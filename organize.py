#!/usr/bin/env python3
"""
Codeforces Repository Organizer & Challenge Tracker.

Automatically:
  1. Matches new solution files (.cpp, .cc, .rs) to official Codeforces metadata
     (difficulty rating, tags, contest ID, problem link).
  2. Moves source files into canonical difficulty folders under `ratings/<rating>/`.
  3. Builds `tags/<tag-slug>/` folders across all 37 official Codeforces tags with
     difficulty-prefixed symlinks so problems are sorted by difficulty inside each tag.
  4. Generates `README.md` dashboards (root, `ratings/`, `tags/`, and per-tag) highlighting
     skill gaps, unpracticed tags, difficulty progression, and next-step challenges.

Usage:
  python3 organize.py                        # Organize new solutions & update READMEs
  python3 organize.py --refresh              # Force refresh Codeforces problemset cache
  python3 organize.py --set file.cpp=2193D   # Explicitly map a filename to a CF problem ID
  python3 organize.py --challenge            # Print personalized challenge suggestions in CLI
  python3 organize.py --challenge --tag dp   # Print challenge suggestions for a specific tag
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
RATINGS_DIR = REPO_ROOT / "ratings"
TAGS_DIR = REPO_ROOT / "tags"
MANIFEST_PATH = REPO_ROOT / "problems.json"
CACHE_PATH = REPO_ROOT / ".cache" / "cf_problemset.json"
CF_API_URL = "https://codeforces.com/api/problemset.problems"
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours

SOLUTION_EXTENSIONS = {".cpp", ".cc", ".rs"}

# All 37 standard Codeforces topic tags (excluding '*special').
ALL_CF_TAGS = [
    "2-sat",
    "binary search",
    "bitmasks",
    "brute force",
    "chinese remainder theorem",
    "combinatorics",
    "communication",
    "constructive algorithms",
    "data structures",
    "dfs and similar",
    "divide and conquer",
    "dp",
    "dsu",
    "expression parsing",
    "fft",
    "flows",
    "games",
    "geometry",
    "graph matchings",
    "graphs",
    "greedy",
    "hashing",
    "implementation",
    "interactive",
    "math",
    "matrices",
    "meet-in-the-middle",
    "number theory",
    "probabilities",
    "schedules",
    "shortest paths",
    "sortings",
    "string suffix structures",
    "strings",
    "ternary search",
    "trees",
    "two pointers",
]

# Fallback core tags (common <= 1500) if running completely offline without API cache.
FALLBACK_CORE_TAGS = {
    "implementation",
    "greedy",
    "math",
    "brute force",
    "constructive algorithms",
    "sortings",
    "strings",
    "dp",
    "number theory",
    "binary search",
    "data structures",
    "two pointers",
    "bitmasks",
    "dfs and similar",
    "graphs",
    "games",
    "combinatorics",
    "geometry",
    "dsu",
    "trees",
}


def tag_to_slug(tag: str) -> str:
    return tag.strip().lower().replace(" ", "-")


def normalize_title(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def strip_leading_article(text: str) -> str:
    cleaned = re.sub(r"^(the|an|a)\s+", "", text.strip(), flags=re.IGNORECASE)
    return normalize_title(cleaned)


def split_camel_or_snake(stem: str) -> str:
    s = re.sub(r"[_-]+", " ", stem)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    return s.strip()


def format_rating_dir(rating: int | None) -> str:
    if rating is None:
        return "unrated"
    return f"{rating:04d}"


def problem_url(contest_id: int, index: str) -> str:
    return f"https://codeforces.com/contest/{contest_id}/problem/{index}"


def load_cf_dataset(force_refresh: bool = False) -> dict[str, Any] | None:
    """Load Codeforces problemset from cache or fetch from official API."""
    if not force_refresh and CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            try:
                return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass

    try:
        req = urllib.request.Request(
            CF_API_URL,
            headers={"User-Agent": "codeforces-repo-organizer/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if payload.get("status") == "OK":
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CACHE_PATH.write_text(json.dumps(payload["result"]), encoding="utf-8")
            return payload["result"]
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        if CACHE_PATH.exists():
            print(f"[warn] Could not reach Codeforces API ({exc}); using cached dataset.")
            try:
                return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        else:
            print(f"[warn] Offline and no local cache available ({exc}). Using problems.json metadata.")
    return None


class ProblemIndex:
    """Fast lookup and recommendation engine over Codeforces problemset."""

    def __init__(self, raw_result: dict[str, Any] | None) -> None:
        self.available = raw_result is not None
        self.by_id: dict[str, dict[str, Any]] = {}
        self.by_norm_name: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
        self.by_article_stripped: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
        self.solved_counts: dict[str, int] = {}
        self.all_problems: list[dict[str, Any]] = []
        self.tag_counts_under_cap: dict[int, collections.Counter[str]] = {}

        if not raw_result:
            return

        for stat in raw_result.get("problemStatistics", []):
            cid = stat.get("contestId")
            idx = stat.get("index")
            if cid is not None and idx:
                self.solved_counts[f"{cid}{idx}".upper()] = int(stat.get("solvedCount", 0))

        for prob in raw_result.get("problems", []):
            cid = prob.get("contestId")
            idx = prob.get("index")
            name = prob.get("name", "")
            if cid is None or not idx or not name:
                continue
            pid = f"{cid}{idx}".upper()
            entry = {
                "id": pid,
                "contestId": int(cid),
                "index": str(idx),
                "name": name,
                "rating": prob.get("rating"),
                "tags": [t for t in prob.get("tags", []) if t != "*special"],
                "is_special": "*special" in prob.get("tags", []),
                "solvedCount": self.solved_counts.get(pid, 0),
            }
            self.by_id[pid] = entry
            self.all_problems.append(entry)

            norm = normalize_title(name)
            if norm:
                self.by_norm_name[norm].append(entry)

            stripped = strip_leading_article(name)
            if stripped and stripped != norm:
                self.by_article_stripped[stripped].append(entry)

    def count_tag_up_to_rating(self, max_rating: int) -> collections.Counter[str]:
        if max_rating not in self.tag_counts_under_cap:
            counter: collections.Counter[str] = collections.Counter()
            for p in self.all_problems:
                if p["is_special"] or p["rating"] is None:
                    continue
                if p["rating"] <= max_rating:
                    for t in p["tags"]:
                        counter[t] += 1
            self.tag_counts_under_cap[max_rating] = counter
        return self.tag_counts_under_cap[max_rating]

    def _dedupe_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(candidates) <= 1:
            return candidates

        # Prefer non-special rated problems when available
        non_special = [c for c in candidates if not c["is_special"]]
        if non_special:
            candidates = non_special
        rated = [c for c in candidates if c["rating"] is not None]
        if rated:
            candidates = rated

        # Sort by solvedCount desc, contestId desc
        candidates = sorted(
            candidates,
            key=lambda c: (c["solvedCount"], c["contestId"]),
            reverse=True,
        )

        # Collapse parallel Div.1/Div.2 twin entries (adjacent contestId, identical name)
        deduped: list[dict[str, Any]] = []
        for cand in candidates:
            is_twin = any(
                abs(cand["contestId"] - prev["contestId"]) <= 1
                and normalize_title(cand["name"]) == normalize_title(prev["name"])
                for prev in deduped
            )
            if not is_twin:
                deduped.append(cand)
        return deduped

    def match_file(
        self,
        file_path: Path,
        override_id: str | None = None,
        interactive: bool = True,
    ) -> dict[str, Any] | None:
        if not self.available:
            return None

        # 1. Explicit CLI override
        if override_id:
            pid = override_id.strip().upper()
            if pid in self.by_id:
                return self.by_id[pid]
            print(f"[error] Override ID '{pid}' not found in Codeforces problemset.")
            return None

        # 2. Check top comments for URL or Problem ID
        try:
            head_lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:20]
        except OSError:
            head_lines = []

        for line in head_lines:
            url_match = re.search(
                r"codeforces\.com/(?:contest|problemset/problem)/(\d+)/(?:problem/)?([A-Za-z]\d?)\b",
                line,
                flags=re.IGNORECASE,
            )
            if url_match:
                pid = f"{url_match.group(1)}{url_match.group(2)}".upper()
                if pid in self.by_id:
                    return self.by_id[pid]

            tag_match = re.search(
                r"(?:://|//|#|\*)\s*(?:CF|Problem|ID)?\s*:?\s*\b(\d{1,4}[A-Za-z]\d?)\b",
                line,
                flags=re.IGNORECASE,
            )
            if tag_match:
                pid = tag_match.group(1).upper()
                if pid in self.by_id:
                    return self.by_id[pid]

        # 3. Check filename stem for Problem ID prefix/suffix (e.g. 2193D.cpp, 2193D_monsterGame.cpp)
        stem = file_path.stem
        # Strip leading rating prefix if someone placed 1200_2193D_foo.cpp
        clean_stem = re.sub(r"^\d{3,4}_", "", stem)
        for pattern in (
            r"^(\d{1,4}[A-Za-z]\d?)(?:[_-].*)?$",
            r"^.*[_-](\d{1,4}[A-Za-z]\d?)$",
        ):
            m = re.match(pattern, clean_stem)
            if m:
                pid = m.group(1).upper()
                if pid in self.by_id:
                    return self.by_id[pid]

        # 4. Normalized title match (including leading 'The '/'A '/'An ' fallback)
        spaced = split_camel_or_snake(clean_stem)
        norm = normalize_title(spaced)
        stripped = strip_leading_article(spaced)

        candidates = list(self.by_norm_name.get(norm, []))
        if not candidates and stripped:
            candidates = list(self.by_article_stripped.get(stripped, []))
        if not candidates and norm:
            candidates = list(self.by_article_stripped.get(norm, []))

        candidates = self._dedupe_candidates(candidates)
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        if interactive and sys.stdin.isatty():
            print(f"\nMultiple Codeforces problems match '{file_path.name}':")
            for idx, c in enumerate(candidates[:8], start=1):
                r_str = c["rating"] if c["rating"] is not None else "unrated"
                tags_str = ", ".join(c["tags"])
                print(f"  [{idx}] {c['id']} - {c['name']} (Rating: {r_str}, Tags: {tags_str})")
            choice = input(f"Select [1-{min(8, len(candidates))}] (Enter for 1): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= min(8, len(candidates)):
                return candidates[int(choice) - 1]
            return candidates[0]

        chosen = candidates[0]
        print(
            f"[info] Multiple matches for '{file_path.name}'; selected {chosen['id']} ({chosen['name']}). "
            f"Use `--set {file_path.name}=<ID>` to override."
        )
        return chosen

    def recommend(
        self,
        solved_ids: set[str],
        *,
        tag: str | None = None,
        min_rating: int = 800,
        max_rating: int = 1400,
        limit: int = 4,
        exclude_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        if not self.available:
            return []

        blocked = solved_ids | (exclude_ids or set())

        def collect(modern_only: bool, r_min: int, r_max: int) -> list[dict[str, Any]]:
            matches = []
            for p in self.all_problems:
                if p["id"] in blocked or p["is_special"] or p["rating"] is None:
                    continue
                if not (r_min <= p["rating"] <= r_max):
                    continue
                if tag and tag not in p["tags"]:
                    continue
                if modern_only and p["contestId"] < 1650:
                    continue
                matches.append(p)
            matches.sort(key=lambda x: (x["solvedCount"], x["contestId"]), reverse=True)
            return matches

        results = collect(True, min_rating, max_rating)
        if len(results) < limit:
            results = collect(False, min_rating, max_rating)
        if len(results) < limit:
            # Widen rating window for advanced/rare tags (like fft, flows, 2-sat)
            results = collect(False, min_rating, 3500)
            results.sort(key=lambda x: (x["rating"], -x["solvedCount"]))

        return results[:limit]


def extract_completion_date(file_path: Path, fallback: str | None = None) -> str:
    """Extract completion date from top comments of solution file, normalized to YYYY-MM-DD."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:10]
    except OSError:
        lines = []

    for line in lines:
        if not line.strip().startswith(("//", "/*", "*", "#")):
            continue
        iso = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", line)
        if iso:
            y, m, d = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
            try:
                return dt.date(y, m, d).isoformat()
            except ValueError:
                pass

        us = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", line)
        if us:
            m, d, y = int(us.group(1)), int(us.group(2)), int(us.group(3))
            if y < 100:
                y += 2000
            try:
                return dt.date(y, m, d).isoformat()
            except ValueError:
                pass

    if fallback:
        return fallback

    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(file_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        git_date = res.stdout.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", git_date):
            return git_date
    except OSError:
        pass

    return dt.date.today().isoformat()


def discover_solution_files() -> list[Path]:
    """Find all real solution files in repo root and `ratings/`."""
    found: list[Path] = []
    for child in sorted(REPO_ROOT.iterdir()):
        if child.is_file() and not child.is_symlink() and child.suffix in SOLUTION_EXTENSIONS:
            found.append(child)

    if RATINGS_DIR.exists():
        for path in sorted(RATINGS_DIR.rglob("*")):
            if path.is_file() and not path.is_symlink() and path.suffix in SOLUTION_EXTENSIONS:
                found.append(path)
    return found


def load_manifest() -> dict[str, dict[str, Any]]:
    """Load existing problems.json keyed by filename."""
    if not MANIFEST_PATH.exists():
        return {}
    try:
        items = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if isinstance(items, list):
            return {item["file"]: item for item in items if "file" in item}
    except Exception as exc:
        print(f"[warn] Failed to parse problems.json ({exc}); rebuilding.")
    return {}


def save_manifest(records: list[dict[str, Any]]) -> None:
    ordered = sorted(
        records,
        key=lambda r: (
            r["rating"] if r["rating"] is not None else 9999,
            r["id"],
            r["file"],
        ),
    )
    MANIFEST_PATH.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")


def progress_bar(count: int, scale: int = 8) -> str:
    filled = min(scale, count)
    return "█" * filled + "░" * (scale - filled)


def compute_comfort_and_target(records: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Return (comfort_rating, stretch_low, stretch_high)."""
    ratings = sorted(r["rating"] for r in records if r["rating"] is not None)
    if not ratings:
        return (800, 800, 1000)
    median_r = int(round(statistics.median(ratings) / 100.0) * 100)
    max_r = max(ratings)
    # If user already has >= 2 solves at max_r and max_r >= median_r, push ceiling!
    at_max = sum(1 for r in ratings if r == max_r)
    comfort = max(800, median_r)
    stretch_low = max(comfort + 100, max_r if at_max < 3 else max_r + 100)
    stretch_high = min(3500, stretch_low + 100)
    return (comfort, stretch_low, stretch_high)


def classify_tags(
    index: ProblemIndex,
    comfort_rating: int,
    all_tags: list[str],
) -> tuple[set[str], set[str]]:
    """Split tags into (core_for_current_level, advanced_topics)."""
    cap = max(1500, comfort_rating + 300)
    if index.available:
        counts = index.count_tag_up_to_rating(cap)
        core = {t for t in all_tags if counts[t] >= 40}
    else:
        core = set(FALLBACK_CORE_TAGS)
    advanced = set(all_tags) - core
    return core, advanced


def rebuild_tags_directory(records: list[dict[str, Any]], index: ProblemIndex) -> None:
    """Create all 37 tag folders, populate difficulty-sorted symlinks, and write per-tag READMEs."""
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    solved_ids = {r["id"] for r in records}
    comfort, stretch_low, stretch_high = compute_comfort_and_target(records)

    extra_tags = {t for r in records for t in r["tags"]} - set(ALL_CF_TAGS)
    all_tags = sorted(set(ALL_CF_TAGS) | extra_tags)

    by_tag: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in records:
        for t in rec["tags"]:
            by_tag[t].append(rec)

    for tag in all_tags:
        slug = tag_to_slug(tag)
        tag_dir = TAGS_DIR / slug
        tag_dir.mkdir(parents=True, exist_ok=True)

        # Remove existing symlinks inside tag_dir before recreating fresh ones
        for existing in tag_dir.iterdir():
            if existing.is_symlink():
                existing.unlink()

        tag_records = sorted(
            by_tag.get(tag, []),
            key=lambda r: (r["rating"] if r["rating"] is not None else 9999, r["id"], r["file"]),
        )

        for rec in tag_records:
            r_dir = format_rating_dir(rec["rating"])
            fname = rec["file"]
            if fname.upper().startswith(rec["id"].upper()):
                link_name = f"{r_dir}_{fname}"
            else:
                link_name = f"{r_dir}_{rec['id']}_{fname}"
            link_path = tag_dir / link_name
            rel_target = Path("..") / ".." / "ratings" / r_dir / fname
            link_path.symlink_to(rel_target)

        # Determine appropriate recommendation band for this specific tag
        tag_ratings = [r["rating"] for r in tag_records if r["rating"] is not None]
        if tag_ratings:
            rec_min = max(comfort, max(tag_ratings))
            rec_max = rec_min + 200
        else:
            rec_min = max(800, comfort - 100)
            rec_max = stretch_high

        suggestions = index.recommend(
            solved_ids,
            tag=tag,
            min_rating=rec_min,
            max_rating=rec_max,
            limit=4,
        )

        lines = [
            f"# Tag: `{tag}`",
            "",
            "[← All Tags](../README.md) · [← Main Dashboard](../../README.md)",
            "",
        ]

        if tag_records:
            r_vals = [r["rating"] for r in tag_records if r["rating"] is not None]
            r_span = f"{min(r_vals)}–{max(r_vals)}" if r_vals else "unrated"
            lines.extend(
                [
                    f"**Solved:** `{len(tag_records)}` &nbsp;|&nbsp; **Difficulty Range:** `{r_span}`",
                    "",
                    "## Solved Problems (Sorted by Difficulty)",
                    "",
                    "| Difficulty | Problem | Solution | Other Tags | Completed |",
                    "| :---: | :--- | :--- | :--- | :---: |",
                ]
            )
            for rec in tag_records:
                r_disp = f"`{rec['rating']}`" if rec["rating"] is not None else "`unrated`"
                p_link = f"[{rec['id']} - {rec['name']}]({problem_url(rec['contestId'], rec['index'])})"
                r_dir = format_rating_dir(rec["rating"])
                s_link = f"[`{rec['file']}`](../../ratings/{r_dir}/{rec['file']})"
                other_tags = ", ".join(
                    f"[`{t}`](../{tag_to_slug(t)}/)" for t in rec["tags"] if t != tag
                ) or "—"
                lines.append(f"| {r_disp} | {p_link} | {s_link} | {other_tags} | {rec['completed']} |")
            lines.append("")
        else:
            lines.extend(
                [
                    "> **0 problems solved in `" + tag + "` so far!** Pick one of the starter challenges below to unlock this topic.",
                    "",
                ]
            )

        if suggestions:
            heading = (
                f"## Next Challenges in `{tag}`"
                if tag_records
                else f"## Starter Challenges to Unlock `{tag}`"
            )
            lines.extend(
                [
                    heading,
                    "",
                    "| Difficulty | Problem | All Tags |",
                    "| :---: | :--- | :--- |",
                ]
            )
            for s in suggestions:
                s_link = f"[{s['id']} - {s['name']}]({problem_url(s['contestId'], s['index'])})"
                s_tags = ", ".join(f"`{t}`" for t in s["tags"])
                lines.append(f"| `{s['rating']}` | {s_link} | {s_tags} |")
            lines.append("")

        (tag_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_ratings_readme(records: list[dict[str, Any]]) -> None:
    RATINGS_DIR.mkdir(parents=True, exist_ok=True)
    by_rating: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in records:
        by_rating[format_rating_dir(rec["rating"])].append(rec)

    lines = [
        "# Solutions by Difficulty Rating",
        "",
        "[← Back to Main Dashboard](../README.md) · [Browse by Topic Tag →](../tags/README.md)",
        "",
        "| Folder | Rating | Solved | Problems |",
        "| :--- | :---: | :---: | :--- |",
    ]

    for r_dir in sorted(by_rating.keys()):
        items = sorted(by_rating[r_dir], key=lambda x: (x["id"], x["file"]))
        r_label = f"`{items[0]['rating']}`" if items[0]["rating"] is not None else "`unrated`"
        prob_links = ", ".join(f"[`{it['file']}`](./{r_dir}/{it['file']})" for it in items)
        lines.append(f"| [`{r_dir}/`](./{r_dir}/) | {r_label} | **{len(items)}** | {prob_links} |")

    lines.extend(["", "## Full List (Easiest → Hardest)", ""])
    lines.extend(
        [
            "| Difficulty | Problem | Solution | Tags | Completed |",
            "| :---: | :--- | :--- | :--- | :---: |",
        ]
    )
    for rec in sorted(
        records,
        key=lambda r: (r["rating"] if r["rating"] is not None else 9999, r["id"], r["file"]),
    ):
        r_dir = format_rating_dir(rec["rating"])
        r_disp = f"`{rec['rating']}`" if rec["rating"] is not None else "`unrated`"
        p_link = f"[{rec['id']} - {rec['name']}]({problem_url(rec['contestId'], rec['index'])})"
        s_link = f"[`{rec['file']}`](./{r_dir}/{rec['file']})"
        t_links = ", ".join(f"[`{t}`](../tags/{tag_to_slug(t)}/)" for t in rec["tags"])
        lines.append(f"| {r_disp} | {p_link} | {s_link} | {t_links} | {rec['completed']} |")

    lines.append("")
    (RATINGS_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_tags_readme(records: list[dict[str, Any]], index: ProblemIndex) -> None:
    comfort, _, _ = compute_comfort_and_target(records)
    extra_tags = {t for r in records for t in r["tags"]} - set(ALL_CF_TAGS)
    all_tags = sorted(set(ALL_CF_TAGS) | extra_tags)
    core_tags, _ = classify_tags(index, comfort, all_tags)
    cap = max(1500, comfort + 300)
    cf_counts = index.count_tag_up_to_rating(cap) if index.available else collections.Counter()

    by_tag: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in records:
        for t in rec["tags"]:
            by_tag[t].append(rec)

    practiced = [t for t in all_tags if by_tag[t]]
    practiced.sort(key=lambda t: (-len(by_tag[t]), t))
    unpracticed_core = sorted(
        [t for t in all_tags if not by_tag[t] and t in core_tags],
        key=lambda t: (-cf_counts[t], t),
    )
    unpracticed_adv = sorted(
        [t for t in all_tags if not by_tag[t] and t not in core_tags],
        key=lambda t: (-cf_counts[t], t),
    )

    lines = [
        "# Solutions by Codeforces Topic Tag",
        "",
        "[← Back to Main Dashboard](../README.md) · [Browse by Difficulty →](../ratings/README.md)",
        "",
        f"**Practiced Tags:** `{len(practiced)} / {len(all_tags)}` &nbsp;|&nbsp; "
        f"**Core Unpracticed (`0` solved):** `{len(unpracticed_core)}` &nbsp;|&nbsp; "
        f"**Advanced Unpracticed (`0` solved):** `{len(unpracticed_adv)}`",
        "",
        "## Practiced Tags",
        "",
        "| Tag Folder | Solved | Progress | Difficulty Range | Solutions |",
        "| :--- | :---: | :--- | :---: | :--- |",
    ]

    for t in practiced:
        slug = tag_to_slug(t)
        items = sorted(
            by_tag[t],
            key=lambda r: (r["rating"] if r["rating"] is not None else 9999, r["id"]),
        )
        r_vals = [r["rating"] for r in items if r["rating"] is not None]
        r_span = f"`{min(r_vals)}–{max(r_vals)}`" if len(set(r_vals)) > 1 else (
            f"`{r_vals[0]}`" if r_vals else "`unrated`"
        )
        sols = ", ".join(
            f"[`{it['file']}`](../ratings/{format_rating_dir(it['rating'])}/{it['file']})"
            for it in items
        )
        lines.append(
            f"| [`{t}`](./{slug}/) | **{len(items)}** | `{progress_bar(len(items))}` | {r_span} | {sols} |"
        )

    lines.extend(
        [
            "",
            f"## Core Topics Not Yet Practiced (`0` Solved — High Priority `<= {cap}`)",
            "",
            "Click into any folder below for starter problem recommendations at your level:",
            "",
            "| Tag Folder | Solved | CF Problems `<= " + str(cap) + "` | Status |",
            "| :--- | :---: | :---: | :--- |",
        ]
    )
    for t in unpracticed_core:
        slug = tag_to_slug(t)
        cnt = cf_counts[t] if index.available else "—"
        lines.append(f"| [`{t}`](./{slug}/) | `0` | {cnt} | Open folder for starter challenges |")

    if unpracticed_adv:
        lines.extend(
            [
                "",
                "## Advanced / Specialized Topics (`0` Solved — Mostly `1600+`)",
                "",
                "| Tag Folder | Solved | CF Problems `<= " + str(cap) + "` |",
                "| :--- | :---: | :---: |",
            ]
        )
        for t in unpracticed_adv:
            slug = tag_to_slug(t)
            cnt = cf_counts[t] if index.available else "—"
            lines.append(f"| [`{t}`](./{slug}/) | `0` | {cnt} |")

    lines.append("")
    (TAGS_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_root_readme(records: list[dict[str, Any]], index: ProblemIndex) -> None:
    solved_ids = {r["id"] for r in records}
    comfort, stretch_low, stretch_high = compute_comfort_and_target(records)
    extra_tags = {t for r in records for t in r["tags"]} - set(ALL_CF_TAGS)
    all_tags = sorted(set(ALL_CF_TAGS) | extra_tags)
    core_tags, _ = classify_tags(index, comfort, all_tags)
    cap = max(1500, comfort + 300)
    cf_counts = index.count_tag_up_to_rating(cap) if index.available else collections.Counter()

    by_tag: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in records:
        for t in rec["tags"]:
            by_tag[t].append(rec)

    by_rating: dict[int, list[dict[str, Any]]] = collections.defaultdict(list)
    unrated_recs: list[dict[str, Any]] = []
    for rec in records:
        if rec["rating"] is None:
            unrated_recs.append(rec)
        else:
            by_rating[rec["rating"]].append(rec)

    ratings_only = sorted(by_rating.keys())
    min_r = min(ratings_only) if ratings_only else 800
    max_r = max(ratings_only) if ratings_only else 800

    practiced = sorted([t for t in all_tags if by_tag[t]], key=lambda t: (-len(by_tag[t]), t))
    lightly_practiced = [t for t in practiced if len(by_tag[t]) <= 2 and t in core_tags]
    unpracticed_core = sorted(
        [t for t in all_tags if not by_tag[t] and t in core_tags],
        key=lambda t: (-cf_counts[t], t),
    )
    unpracticed_adv = sorted(
        [t for t in all_tags if not by_tag[t] and t not in core_tags],
        key=lambda t: (-cf_counts[t], t),
    )

    lines = [
        "# Codeforces Solutions & Progress Tracker",
        "",
        "Organized both by **difficulty rating** ([`ratings/`](./ratings/)) and across **all 37 official Codeforces topic tags** ([`tags/`](./tags/)).",
        "",
        "| Total Solved | Solved Rating Span | Current Comfort Zone | Next Stretch Target | Tags Unlocked |",
        "| :---: | :---: | :---: | :---: | :---: |",
        f"| **{len(records)}** | `{min_r} – {max_r}` | **`{comfort}`** | **`{stretch_low} – {stretch_high}`** | **`{len(practiced)} / {len(all_tags)}`** |",
        "",
        "---",
        "",
        "## What to Work On Next",
        "",
        "### 1. Difficulty Ladder — Push Ceiling to `"
        + f"{stretch_low}–{stretch_high}"
        + "`",
        "",
        "| Rating | Solved | Distribution | Folder / Status |",
        "| :---: | :---: | :--- | :--- |",
    ]

    ladder_top = max(1500, max_r + 200)
    for r in range(800, ladder_top + 100, 100):
        cnt = len(by_rating.get(r, []))
        bar = "█" * cnt + ("░" if cnt == 0 else "")
        r_dir = format_rating_dir(r)
        if cnt > 0:
            note = f"[`ratings/{r_dir}/`](./ratings/{r_dir}/)"
            if r == comfort:
                note += " *(comfort zone)*"
            elif r == max_r:
                note += " *(current ceiling)*"
        else:
            if stretch_low <= r <= stretch_high:
                note = "**Next milestone — target this band!**"
            else:
                note = "—"
        lines.append(f"| `{r}` | **{cnt}** | `{bar}` | {note} |")

    if unrated_recs:
        lines.append(
            f"| `unrated` | **{len(unrated_recs)}** | `{'█' * len(unrated_recs)}` | [`ratings/unrated/`](./ratings/unrated/) |"
        )

    shown_ids: set[str] = set()

    # Stretch difficulty problem picks (balanced across stretch_low and stretch_high)
    if stretch_low < stretch_high:
        low_picks = index.recommend(
            solved_ids,
            min_rating=stretch_low,
            max_rating=stretch_low,
            limit=2,
            exclude_ids=shown_ids,
        )
        shown_ids.update(p["id"] for p in low_picks)
        high_picks = index.recommend(
            solved_ids,
            min_rating=stretch_high,
            max_rating=stretch_high,
            limit=2,
            exclude_ids=shown_ids,
        )
        shown_ids.update(p["id"] for p in high_picks)
        stretch_picks = low_picks + high_picks
    else:
        stretch_picks = index.recommend(
            solved_ids,
            min_rating=stretch_low,
            max_rating=stretch_high,
            limit=4,
            exclude_ids=shown_ids,
        )
        shown_ids.update(p["id"] for p in stretch_picks)

    if stretch_picks:
        lines.extend(
            [
                "",
                f"**Recommended `{stretch_low}–{stretch_high}` Stretch Problems:**",
                "",
                "| Rating | Problem | Tags |",
                "| :---: | :--- | :--- |",
            ]
        )
        for p in stretch_picks:
            p_link = f"[{p['id']} - {p['name']}]({problem_url(p['contestId'], p['index'])})"
            p_tags = ", ".join(f"[`{t}`](./tags/{tag_to_slug(t)}/)" for t in p["tags"])
            lines.append(f"| `{p['rating']}` | {p_link} | {p_tags} |")

    # Core 0-solved blind spots with 1 unique entry challenge each
    if unpracticed_core:
        lines.extend(
            [
                "",
                "### 2. Core Topic Blind Spots (`0` Solved)",
                "",
                "These fundamental competitive programming tags appear frequently at your target rating, and you currently have **`0` solutions** in them:",
                "",
                "| Unpracticed Core Tag | Starter Challenge to Break the Ice | Rating |",
                "| :--- | :--- | :---: |",
            ]
        )
        for t in unpracticed_core[:8]:
            slug = tag_to_slug(t)
            picks = index.recommend(
                solved_ids,
                tag=t,
                min_rating=max(800, comfort - 100),
                max_rating=stretch_high,
                limit=1,
                exclude_ids=shown_ids,
            )
            if picks:
                p = picks[0]
                shown_ids.add(p["id"])
                pick_cell = f"[{p['id']} - {p['name']}]({problem_url(p['contestId'], p['index'])})"
                r_cell = f"`{p['rating']}`"
            else:
                pick_cell = f"See [`tags/{slug}/`](./tags/{slug}/)"
                r_cell = "—"
            lines.append(f"| [`{t}`](./tags/{slug}/) | {pick_cell} | {r_cell} |")

    # Lightly practiced core tags (1-2 solved)
    if lightly_practiced:
        lines.extend(
            [
                "",
                "### 3. Lightly Practiced Topics (`1–2` Solved — Build Consistency)",
                "",
                "| Tag | Solved | Highest Solved | Suggested Next Step |",
                "| :--- | :---: | :---: | :--- |",
            ]
        )
        for t in lightly_practiced:
            slug = tag_to_slug(t)
            r_vals = [r["rating"] for r in by_tag[t] if r["rating"] is not None]
            max_t = max(r_vals) if r_vals else comfort
            next_min = max(comfort, max_t + 100 if len(by_tag[t]) >= 2 else max_t)
            picks = index.recommend(
                solved_ids,
                tag=t,
                min_rating=next_min,
                max_rating=max(stretch_high, next_min + 100),
                limit=1,
                exclude_ids=shown_ids,
            )
            if picks:
                shown_ids.add(picks[0]["id"])
            next_cell = (
                f"[{picks[0]['id']} - {picks[0]['name']}]({problem_url(picks[0]['contestId'], picks[0]['index'])}) (`{picks[0]['rating']}`)"
                if picks
                else f"[`tags/{slug}/`](./tags/{slug}/)"
            )
            lines.append(
                f"| [`{t}`](./tags/{slug}/) | `{len(by_tag[t])}` | `{max_t}` | {next_cell} |"
            )

    # Full Tag Coverage Matrix
    lines.extend(
        [
            "",
            "---",
            "",
            "## Topic Tag Coverage (All 37 Codeforces Tags)",
            "",
            "### Practiced Tags",
            "",
            "| Tag | Solved | Bar | Rating Span | Folder |",
            "| :--- | :---: | :--- | :---: | :--- |",
        ]
    )
    for t in practiced:
        slug = tag_to_slug(t)
        items = by_tag[t]
        r_vals = [r["rating"] for r in items if r["rating"] is not None]
        span = (
            f"`{min(r_vals)}–{max(r_vals)}`"
            if len(set(r_vals)) > 1
            else (f"`{r_vals[0]}`" if r_vals else "`unrated`")
        )
        lines.append(
            f"| [`{t}`](./tags/{slug}/) | **{len(items)}** | `{progress_bar(len(items))}` | {span} | [`tags/{slug}/`](./tags/{slug}/) |"
        )

    if unpracticed_core:
        core_links = " · ".join(f"[`{t}`](./tags/{tag_to_slug(t)}/)" for t in unpracticed_core)
        lines.extend(
            [
                "",
                f"**Unpracticed Core Tags (`0` solved):** {core_links}",
            ]
        )

    if unpracticed_adv:
        adv_links = " · ".join(f"[`{t}`](./tags/{tag_to_slug(t)}/)" for t in unpracticed_adv)
        lines.extend(
            [
                "",
                "<details>",
                f"<summary><strong>Unpracticed Advanced / Specialized Tags ({len(unpracticed_adv)} tags, typically 1600+)</strong></summary>",
                "",
                adv_links,
                "",
                "</details>",
            ]
        )

    # All Solved Problems Sorted by Difficulty
    lines.extend(
        [
            "",
            "---",
            "",
            "## Solved Problems (Sorted by Difficulty)",
            "",
            "| Difficulty | Problem | Solution | Tags | Completed |",
            "| :---: | :--- | :--- | :--- | :---: |",
        ]
    )
    for rec in sorted(
        records,
        key=lambda r: (r["rating"] if r["rating"] is not None else 9999, r["id"], r["file"]),
    ):
        r_dir = format_rating_dir(rec["rating"])
        r_disp = f"`{rec['rating']}`" if rec["rating"] is not None else "`unrated`"
        p_link = f"[{rec['id']} - {rec['name']}]({problem_url(rec['contestId'], rec['index'])})"
        s_link = f"[`{rec['file']}`](./ratings/{r_dir}/{rec['file']})"
        t_links = ", ".join(f"[`{t}`](./tags/{tag_to_slug(t)}/)" for t in rec["tags"])
        lines.append(f"| {r_disp} | {p_link} | {s_link} | {t_links} | {rec['completed']} |")

    # Collapsible Problems Grouped by Tag
    lines.extend(
        [
            "",
            "<details>",
            "<summary><strong>View Solved Problems Grouped by Tag</strong></summary>",
            "",
        ]
    )
    for t in practiced:
        slug = tag_to_slug(t)
        items = sorted(
            by_tag[t],
            key=lambda r: (r["rating"] if r["rating"] is not None else 9999, r["id"]),
        )
        lines.append(f"### [`{t}`](./tags/{slug}/) ({len(items)})")
        lines.append("")
        for it in items:
            r_dir = format_rating_dir(it["rating"])
            r_str = it["rating"] if it["rating"] is not None else "unrated"
            lines.append(
                f"- `{r_str}` — [{it['id']}: {it['name']}]({problem_url(it['contestId'], it['index'])}) "
                f"([`{it['file']}`](./ratings/{r_dir}/{it['file']}))"
            )
        lines.append("")
    lines.extend(["</details>", ""])

    # Workflow guide
    lines.extend(
        [
            "---",
            "",
            "## Adding New Solutions",
            "",
            "You never need to manually create folders or symlinks:",
            "",
            "1. Save your new solution right in the repo root (e.g., `problemName.cpp` or `2193D.cpp` — or add `// CF: 2193D` on line 1).",
            "2. Run the organizer (or simply push to `main` and let GitHub Actions run it for you):",
            "",
            "```bash",
            "python3 organize.py",
            "```",
            "",
            "### Useful Commands",
            "",
            "```bash",
            "python3 organize.py --challenge              # Get next challenge suggestions in terminal",
            "python3 organize.py --challenge --tag graphs # Get starter/next problems for a specific tag",
            "python3 organize.py --set mySol.cpp=2193D    # Explicitly link a custom filename to a CF ID",
            "python3 organize.py --refresh                # Force refresh Codeforces problemset cache",
            "```",
            "",
        ]
    )

    (REPO_ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def print_challenge_cli(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    filter_tag: str | None,
    filter_rating: int | None,
) -> None:
    if not index.available:
        print("[error] Codeforces problemset cache unavailable; connect to the internet and run `--refresh`.")
        return

    solved_ids = {r["id"] for r in records}
    comfort, stretch_low, stretch_high = compute_comfort_and_target(records)
    print(f"Solved: {len(records)} | Comfort Rating: {comfort} | Stretch Target: {stretch_low}-{stretch_high}\n")

    if filter_tag:
        norm_tag = filter_tag.strip().lower().replace("-", " ")
        r_lo = filter_rating if filter_rating else max(800, comfort - 100)
        r_hi = filter_rating if filter_rating else stretch_high
        picks = index.recommend(solved_ids, tag=norm_tag, min_rating=r_lo, max_rating=r_hi, limit=6)
        print(f"Recommended '{norm_tag}' problems ({r_lo}-{r_hi}):")
        for p in picks:
            print(f"  [{p['rating']}] {p['id']:6s} {p['name']} -> {problem_url(p['contestId'], p['index'])}")
        return

    shown_ids: set[str] = set()
    r_lo = filter_rating if filter_rating else stretch_low
    r_hi = filter_rating if filter_rating else stretch_high
    print(f"1) Stretch Difficulty Challenges ({r_lo}-{r_hi}):")
    if r_lo < r_hi:
        cli_stretch = index.recommend(solved_ids, min_rating=r_lo, max_rating=r_lo, limit=2, exclude_ids=shown_ids)
        shown_ids.update(p["id"] for p in cli_stretch)
        cli_high = index.recommend(solved_ids, min_rating=r_hi, max_rating=r_hi, limit=2, exclude_ids=shown_ids)
        shown_ids.update(p["id"] for p in cli_high)
        cli_stretch.extend(cli_high)
    else:
        cli_stretch = index.recommend(solved_ids, min_rating=r_lo, max_rating=r_hi, limit=4, exclude_ids=shown_ids)
        shown_ids.update(p["id"] for p in cli_stretch)

    for p in cli_stretch:
        print(
            f"  [{p['rating']}] {p['id']:6s} {p['name']} ({', '.join(p['tags'])})\n"
            f"         {problem_url(p['contestId'], p['index'])}"
        )

    practiced_tags = {t for r in records for t in r["tags"]}
    core_tags, _ = classify_tags(index, comfort, ALL_CF_TAGS)
    cap = max(1500, comfort + 300)
    cf_counts = index.count_tag_up_to_rating(cap)
    unpracticed_core = sorted(core_tags - practiced_tags, key=lambda t: (-cf_counts[t], t))

    if unpracticed_core:
        print("\n2) Unlock Unpracticed Core Topics (0 solved so far):")
        for t in unpracticed_core[:5]:
            picks = index.recommend(
                solved_ids,
                tag=t,
                min_rating=max(800, comfort - 100),
                max_rating=stretch_high,
                limit=1,
                exclude_ids=shown_ids,
            )
            if picks:
                p = picks[0]
                shown_ids.add(p["id"])
                print(
                    f"  • {t:20s} -> [{p['rating']}] {p['id']} - {p['name']} "
                    f"({problem_url(p['contestId'], p['index'])})"
                )


def parse_overrides(raw_overrides: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in raw_overrides:
        if "=" not in item:
            print(f"[warn] Ignoring invalid --set '{item}' (expected filename=1234A).")
            continue
        fname, pid = item.split("=", 1)
        mapping[Path(fname.strip()).name] = pid.strip().upper()
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Organize Codeforces solutions by difficulty and tags.")
    parser.add_argument("--refresh", action="store_true", help="Force refresh Codeforces API cache.")
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="FILE=ID",
        help="Explicitly map a solution filename to a Codeforces ID (e.g. sol.cpp=2193D).",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt on ambiguous matches (for CI/GitHub Actions).",
    )
    parser.add_argument(
        "--challenge",
        action="store_true",
        help="Print personalized next-challenge problem suggestions and exit.",
    )
    parser.add_argument("--tag", type=str, default=None, help="Filter `--challenge` by topic tag.")
    parser.add_argument("--rating", type=int, default=None, help="Filter `--challenge` by difficulty rating.")
    args = parser.parse_args()

    raw_cf = load_cf_dataset(force_refresh=args.refresh)
    index = ProblemIndex(raw_cf)
    manifest = load_manifest()

    if args.challenge:
        print_challenge_cli(list(manifest.values()), index, args.tag, args.rating)
        return 0

    overrides = parse_overrides(args.overrides)
    files = discover_solution_files()

    records: list[dict[str, Any]] = []
    moved_summary: list[str] = []
    unresolved: list[Path] = []

    for fpath in files:
        fname = fpath.name
        override_id = overrides.get(fname)
        existing = manifest.get(fname)

        matched: dict[str, Any] | None = None
        if override_id:
            matched = index.match_file(fpath, override_id=override_id, interactive=not args.non_interactive)
        elif existing:
            # Refresh rating/tags from API if previously unrated or --refresh requested
            pid = existing["id"].upper()
            if index.available and pid in index.by_id:
                api_entry = index.by_id[pid]
                matched = api_entry
            else:
                matched = {
                    "id": existing["id"],
                    "contestId": existing["contestId"],
                    "index": existing["index"],
                    "name": existing["name"],
                    "rating": existing.get("rating"),
                    "tags": existing.get("tags", []),
                }
        else:
            matched = index.match_file(fpath, interactive=not args.non_interactive)

        if not matched:
            unresolved.append(fpath)
            continue

        completed = extract_completion_date(fpath, fallback=existing.get("completed") if existing else None)
        dest_dir = RATINGS_DIR / format_rating_dir(matched["rating"])
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / fname

        if fpath.resolve() != dest_path.resolve():
            shutil.move(str(fpath), str(dest_path))
            moved_summary.append(
                f"  • {fname} -> ratings/{format_rating_dir(matched['rating'])}/{fname} "
                f"({matched['id']}: {matched['name']}, rating={matched['rating']})"
            )

        records.append(
            {
                "id": matched["id"],
                "contestId": matched["contestId"],
                "index": matched["index"],
                "name": matched["name"],
                "rating": matched["rating"],
                "tags": matched["tags"],
                "file": fname,
                "completed": completed,
            }
        )

    # Clean up any empty subdirectories inside ratings/
    if RATINGS_DIR.exists():
        for sub in sorted(RATINGS_DIR.iterdir()):
            if sub.is_dir() and not any(sub.iterdir()):
                sub.rmdir()

    save_manifest(records)
    rebuild_tags_directory(records, index)
    write_ratings_readme(records)
    write_tags_readme(records, index)
    write_root_readme(records, index)

    print(f"Organized {len(records)} solution(s) across ratings/ and 37 tags/ folders.")
    if moved_summary:
        print("\nMoved files:")
        for line in moved_summary:
            print(line)

    if unresolved:
        print("\n[warn] Could not match the following file(s) to a Codeforces problem:")
        for u in unresolved:
            print(
                f"  • {u.relative_to(REPO_ROOT)} "
                f"(add `// CF: 1234A` on line 1 or run `python3 organize.py --set {u.name}=1234A`)"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
