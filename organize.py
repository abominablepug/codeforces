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
     skill gaps, unpracticed tags, difficulty progression, next-step challenges, and
     auto-renewing progressive topic sprints (`sprints.json`).

Usage:
  python3 organize.py                        # Organize new solutions & update READMEs
  python3 organize.py --refresh              # Force refresh Codeforces problemset cache
  python3 organize.py --set file.cpp=2193D   # Explicitly map a filename to a CF problem ID
  python3 organize.py --challenge            # Print personalized challenge suggestions in CLI
  python3 organize.py --challenge --tag dp   # Print challenge suggestions for a specific tag
  python3 organize.py --sprint               # Print active topic sprints in CLI
  python3 organize.py --sprint --tag dp      # Print active sprint for a specific tag
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
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
SPRINTS_PATH = REPO_ROOT / "sprints.json"
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

# Multi-track progressive curriculum across all 37 official Codeforces tags.
# Each track focuses on a distinct subtopic, algorithm, or perspective within that tag.
SPRINT_CURRICULUM: dict[str, list[dict[str, Any]]] = {
    "2-sat": [
        {
            "slug": "implication-graphs",
            "title": "Implication Graphs & Forced Choices",
            "description": (
                "Model each binary decision as `x` vs. `¬x` and turn every 'cannot pick both' rule into "
                "directed edges `a → ¬b` and `b → ¬a`. Start by spotting 2-choice constraints, then use "
                "SCC topological order to reconstruct valid assignments."
            ),
            "min_rating": 1500,
            "prefer_tags": ("graphs", "dfs and similar"),
            "avoid_tags": ("flows", "string suffix structures"),
        },
        {
            "slug": "2sat-thresholds-bitmasks",
            "title": "2-SAT with Binary Search & Bitwise Clauses",
            "description": (
                "Pair a monotonic threshold or independent bit columns with a 2-SAT check so each candidate "
                "answer reduces to boolean satisfiability. Harder steps compress dense clause ranges with "
                "prefix auxiliary variables."
            ),
            "min_rating": 1700,
            "prefer_tags": ("binary search", "bitmasks", "data structures", "constructive algorithms"),
            "avoid_tags": (),
        },
    ],
    "binary search": [
        {
            "slug": "monotonic-predicate",
            "title": "Monotonic Predicate (Search on the Answer)",
            "description": (
                "Reframe 'find the optimal `X`' into a yes/no threshold check `can(X)` with a single "
                "true-to-false cutoff. Start with direct `O(n)` arithmetic checks, then build greedy sweep "
                "simulations inside `can(X)` as constraints tighten."
            ),
            "min_rating": 1000,
            "prefer_tags": ("greedy", "math"),
            "avoid_tags": ("trees", "graphs", "dp", "data structures", "dsu"),
        },
        {
            "slug": "sorted-prefix-bounds",
            "title": "Sorted Prefix Queries & `lower_bound`",
            "description": (
                "Pre-sort or build prefix sums/maxima so each query jumps straight to the cutoff index in "
                "`O(log n)` instead of scanning. Later steps require rearranging two-index inequalities so "
                "`i` and `j` separate cleanly before searching."
            ),
            "min_rating": 1100,
            "require_any": ("sortings", "two pointers"),
            "avoid_tags": ("trees", "graphs", "dp", "dsu"),
        },
        {
            "slug": "parametric-math-cutoffs",
            "title": "Parametric Formulas & Overflow-Safe Roots",
            "description": (
                "Exploit monotonicity in closed-form equations, integer roots, or geometric bounds while "
                "guarding against 64-bit multiplication overflow inside midpoint checks. Harder steps layer "
                "multiple interacting bounds into one feasibility test."
            ),
            "min_rating": 1100,
            "require_any": ("math", "geometry", "number theory"),
            "avoid_tags": ("data structures", "trees", "graphs", "sortings", "dp"),
        },
        {
            "slug": "minimax-ds-predicates",
            "title": "Minimax & Data-Structure-Backed Predicates",
            "description": (
                "Tackle bottleneck objectives where validating `can(X)` itself needs a sliding window, "
                "ordered set, DP, or graph traversal in `O(n)` or `O(n log n)`. Focus on what simplifies "
                "once the threshold `X` is fixed."
            ),
            "min_rating": 1400,
            "require_any": ("data structures", "dp", "trees", "graphs"),
            "avoid_tags": (),
        },
    ],
    "bitmasks": [
        {
            "slug": "bitwise-column-greedy",
            "title": "Bitwise Column Independence (`AND` / `OR` / `XOR`)",
            "description": (
                "Since bitwise operations never carry across positions, analyze the 30 bit columns "
                "independently and lock in decisions from MSB down to LSB. Later steps mix bitwise "
                "constraints with sums where carries reappear."
            ),
            "min_rating": 1100,
            "require_any": ("greedy", "math"),
            "avoid_tags": ("dp", "brute force", "trees", "graphs"),
            "keywords": ("and", "or", "xor", "bit"),
        },
        {
            "slug": "subset-enumeration",
            "title": "Subset Enumeration (`2^k` Search)",
            "description": (
                "Spot a small parameter (`k ≤ 20`) hidden in the constraints and iterate masks "
                "`0 .. (1 << k) - 1` to fix those choices before solving the remaining subproblem greedily. "
                "Advanced steps iterate submasks `(s - 1) & mask`."
            ),
            "min_rating": 1000,
            "require_any": ("brute force",),
            "avoid_tags": ("dp", "trees"),
        },
        {
            "slug": "prefix-xor-basis",
            "title": "Prefix XORs & Linear Basis Ideas",
            "description": (
                "Use `x ^ x = 0` to turn subarray XORs into prefix pairs `pref[R] ^ pref[L - 1]`. Progress "
                "from frequency-map prefix lookups to maintaining independent XOR basis vectors that span "
                "all achievable values."
            ),
            "min_rating": 1200,
            "require_any": ("constructive algorithms", "data structures"),
            "avoid_tags": ("dp", "brute force"),
            "keywords": ("xor", "basis", "bit"),
        },
        {
            "slug": "bitmask-dp",
            "title": "Bitmask DP & Profile Compression",
            "description": (
                "Compress visited items or active profiles into `dp[mask]` and transition by toggling one "
                "bit at a time in `O(n · 2^n)` or `O(n^2 · 2^n)`. Look for redundant state dimensions that "
                "can be derived directly from `popcount(mask)`."
            ),
            "min_rating": 1500,
            "require_any": ("dp",),
            "avoid_tags": (),
        },
    ],
    "brute force": [
        {
            "slug": "fix-one-variable",
            "title": "Fixing One Variable & Bounded Search",
            "description": (
                "Pin down one discrete parameter by brute force so the remaining degrees of freedom "
                "collapse into an `O(1)` or `O(n)` check. As ratings climb, prove tight upper bounds that "
                "shrink a huge-looking loop to a few dozen steps."
            ),
            "min_rating": 1000,
            "prefer_tags": ("math", "implementation"),
            "avoid_tags": ("dp", "graphs", "trees", "bitmasks", "data structures", "dsu"),
        },
        {
            "slug": "harmonic-divisor-loops",
            "title": "Harmonic Series & Divisor Iteration",
            "description": (
                "Lean on `1 + n/2 + n/3 + … ≈ n ln n` and `O(√n)` divisor enumeration—strided multiple "
                "loops are dramatically faster than `O(n^2)`. Later steps combine divisor striding with "
                "value-frequency tables."
            ),
            "min_rating": 1100,
            "require_any": ("number theory",),
            "avoid_tags": ("dp", "graphs", "trees"),
        },
        {
            "slug": "backtracking-pruning",
            "title": "Backtracking, Subsets & Symmetry Pruning",
            "description": (
                "Explore branching choices recursively while pruning hopeless partial states early via "
                "upper bounds or canonical ordering. Harder problems blend small-depth search with bitmasks "
                "or graph connectivity."
            ),
            "min_rating": 1200,
            "require_any": ("bitmasks", "dfs and similar", "combinatorics"),
            "avoid_tags": ("dp",),
        },
    ],
    "chinese remainder theorem": [
        {
            "slug": "simultaneous-congruences",
            "title": "Simultaneous Congruences & Modular Cycles",
            "description": (
                "Merge `x ≡ r_i (mod m_i)` constraints step-by-step via `lcm` periodicity, checking "
                "`r_1 ≡ r_2 (mod gcd(m_1, m_2))` whenever moduli share factors. Later problems disguise "
                "congruences inside cyclic grid or array shifts."
            ),
            "min_rating": 1300,
            "prefer_tags": ("number theory", "math"),
            "avoid_tags": (),
        },
        {
            "slug": "prime-power-residues",
            "title": "Prime-Power Moduli & Residue Obstructions",
            "description": (
                "Factor composite moduli into prime powers `p^k` so residue classes decouple cleanly, and "
                "check small-prime pigeonhole obstructions before building global solutions."
            ),
            "min_rating": 1700,
            "prefer_tags": ("number theory", "constructive algorithms", "math"),
            "avoid_tags": (),
        },
    ],
    "combinatorics": [
        {
            "slug": "product-rule-complements",
            "title": "Rule of Product, Complements & Pair Contributions",
            "description": (
                "Count invalid cases via the complement or sum how many valid configurations each "
                "individual element/pair contributes to. Later problems sort first so valid partner counts "
                "reduce to clean index arithmetic."
            ),
            "min_rating": 1100,
            "prefer_tags": ("math", "sortings"),
            "avoid_tags": ("dp", "fft", "matrices", "trees", "graphs"),
        },
        {
            "slug": "binomials-modular-inverses",
            "title": "Binomial Coefficients & Stars-and-Bars",
            "description": (
                "Precompute factorials and Fermat modular inverses in `O(N)` so `C(n, k)` queries take "
                "`O(1)`. Progress from direct multiset/partition formulas to summing binomial terms across "
                "fixed boundary positions."
            ),
            "min_rating": 1300,
            "require_any": ("number theory", "constructive algorithms"),
            "avoid_tags": ("dp", "fft", "graphs"),
        },
        {
            "slug": "inclusion-exclusion",
            "title": "Inclusion-Exclusion & Parity Sieves",
            "description": (
                "Turn 'none of these bad properties occur' into an alternating sum `(-1)^|S|` over "
                "intersections of bad sets. Start with 2–4 intersecting conditions before scaling to "
                "bitmasks or prime-divisor Mobius sieves."
            ),
            "min_rating": 1500,
            "require_any": ("bitmasks", "number theory", "brute force"),
            "avoid_tags": ("dp", "trees"),
        },
        {
            "slug": "combinatorial-dp",
            "title": "Counting DP & Canonical Recurrences",
            "description": (
                "Count valid structures incrementally while ensuring every valid object has a unique "
                "canonical construction path to prevent double-counting. Later steps collapse `O(n)` "
                "transition loops with running prefix sums."
            ),
            "min_rating": 1400,
            "require_any": ("dp",),
            "avoid_tags": (),
        },
    ],
    "communication": [
        {
            "slug": "compact-encoding",
            "title": "Compact State Encoding & Bit-Budget Protocols",
            "description": (
                "Compare total distinct hidden states against the message bit budget, using modular "
                "checksums, XOR parities, or bipartite colorings so the receiver decodes uniquely."
            ),
            "min_rating": 2000,
            "prefer_tags": ("interactive", "constructive algorithms", "bitmasks"),
            "avoid_tags": (),
        },
        {
            "slug": "resilient-reconstruction",
            "title": "Adversarial Channels & Structural Reconstruction",
            "description": (
                "Exploit neighborhood XOR invariants, tree/graph degree encodings, or redundant parity "
                "blocks to recover full information even when signals are unordered or partially lost."
            ),
            "min_rating": 2200,
            "prefer_tags": ("trees", "graphs", "number theory", "interactive"),
            "avoid_tags": (),
        },
    ],
    "constructive algorithms": [
        {
            "slug": "permutations-extremal-layouts",
            "title": "Permutations, Interleaving & Parity Checks",
            "description": (
                "Test canonical templates first—interleaving `[1, n, 2, n-1, …]`, cyclic shifts, or "
                "adjacent `(2i-1, 2i)` swaps—and check parity/sum invariants early for `-1` cases. Harder "
                "steps tune a custom prefix before filling the tail monotonically."
            ),
            "min_rating": 1000,
            "prefer_tags": ("math", "sortings"),
            "avoid_tags": ("graphs", "trees", "dp", "bitmasks", "strings", "dsu"),
            "keywords": ("permutation", "array", "sequence"),
        },
        {
            "slug": "greedy-invariant-swaps",
            "title": "Greedy Invariants & Incremental Reductions",
            "description": (
                "Build the output one operation at a time while preserving a simple invariant, picking "
                "moves that strictly shrink an imbalance or lock one boundary element into place."
            ),
            "min_rating": 1100,
            "require_any": ("greedy",),
            "avoid_tags": ("graphs", "trees", "dp", "strings", "dsu"),
        },
        {
            "slug": "bitwise-string-constructions",
            "title": "Bitwise, String & Grid Constructions",
            "description": (
                "Decompose the target into independent bit columns, periodic string blocks, or `2 × 2` "
                "grid tiles so fixing the next piece never breaks earlier pieces."
            ),
            "min_rating": 1200,
            "require_any": ("strings", "bitmasks"),
            "avoid_tags": ("graphs", "trees", "dp"),
        },
        {
            "slug": "constructive-trees-graphs",
            "title": "Constructive Trees & Graph Topologies",
            "description": (
                "Anchor your intuition on extremal shapes—stars, paths, combs, and cycles—and graft leaves "
                "onto a spine of chosen length to hit exact diameter, degree, or distance targets."
            ),
            "min_rating": 1300,
            "require_any": ("graphs", "trees", "dfs and similar"),
            "avoid_tags": (),
        },
    ],
    "data structures": [
        {
            "slug": "sets-maps-heaps",
            "title": "Ordered Sets, Frequency Maps & Heaps",
            "description": (
                "Maintain dynamic min/max, predecessor/successor (`set` / `multiset`), or active counts "
                "(`map` / `priority_queue`) during a single pass. Later steps pair greedy heap eviction "
                "with running prefix balances."
            ),
            "min_rating": 1100,
            "require_any": ("greedy", "sortings"),
            "avoid_tags": ("trees", "graphs", "dp", "divide and conquer", "bitmasks", "dsu"),
        },
        {
            "slug": "monotonic-stacks-deques",
            "title": "Prefix Tricks, Monotonic Stacks & Deques",
            "description": (
                "Pop dominated elements from a stack or deque so every element enters and leaves at most "
                "once in `O(n)`. Progress from sliding-window extremes to counting how many subarrays each "
                "element dominates."
            ),
            "min_rating": 1200,
            "require_any": ("two pointers", "implementation"),
            "avoid_tags": ("trees", "graphs", "dp", "divide and conquer", "dsu"),
        },
        {
            "slug": "fenwick-segment-trees",
            "title": "Fenwick / Segment Trees & Range Queries",
            "description": (
                "Coordinate-compress values and maintain prefix or interval aggregates in `O(log n)` per "
                "update. Start with inversion/range-count queries, then build custom associative "
                "segment-tree node merges."
            ),
            "min_rating": 1500,
            "require_any": ("binary search", "divide and conquer", "bitmasks"),
            "avoid_tags": ("strings",),
        },
        {
            "slug": "ds-accelerated-dp",
            "title": "Data-Structure-Accelerated DP & Offline Queries",
            "description": (
                "Write the clean `O(n^2)` DP transition or range query first, sort queries/states by "
                "endpoint, and replace the inner scan with a Fenwick or segment tree lookup."
            ),
            "min_rating": 1600,
            "require_any": ("dp", "trees", "dsu"),
            "avoid_tags": (),
        },
    ],
    "dfs and similar": [
        {
            "slug": "components-flood-fill",
            "title": "Connected Components & Implicit Flood Fill",
            "description": (
                "Aggregate sizes, boundary touches, or values across each connected component in `O(V + E)`, "
                "marking visited states immediately on entry. Later problems build implicit graphs over "
                "grid states or value transitions."
            ),
            "min_rating": 1000,
            "prefer_tags": ("graphs", "implementation", "dsu"),
            "avoid_tags": ("trees", "dp", "shortest paths", "2-sat", "flows"),
        },
        {
            "slug": "tree-dfs-propagation",
            "title": "Tree Traversals & Leaf-to-Root Aggregation",
            "description": (
                "Root the tree at `1` and pass parent `p` so DFS computes depths downward and subtree "
                "summaries upward cleanly. Harder steps propagate edge constraints or directional flips in "
                "a single traversal."
            ),
            "min_rating": 1100,
            "require_any": ("trees",),
            "avoid_tags": ("data structures", "divide and conquer"),
        },
        {
            "slug": "cycles-bipartite-coloring",
            "title": "Cycles, Bipartite 2-Coloring & Functional Graphs",
            "description": (
                "Use 2-coloring parity to test odd-cycle conflicts and 3-color recursion stacks to isolate "
                "directed cycles. On out-degree-1 functional graphs, decompose each component into its "
                "unique cycle plus incoming trees."
            ),
            "min_rating": 1200,
            "require_any": ("graphs",),
            "prefer_tags": ("constructive algorithms", "dsu"),
            "avoid_tags": ("trees", "dp", "flows"),
        },
        {
            "slug": "dfs-memo-subtrees",
            "title": "Subtree States & DAG Memoization",
            "description": (
                "Flatten subtrees via entry/exit timestamps `[tin[u], tout[u]]` or memoize recursive DAG "
                "states so repeated path computations collapse to `O(V + E)`."
            ),
            "min_rating": 1400,
            "require_any": ("dp",),
            "avoid_tags": (),
        },
    ],
    "divide and conquer": [
        {
            "slug": "recursive-halving",
            "title": "Recursive Halving & Cross-Boundary Counting",
            "description": (
                "Split the array or range at its midpoint or extremum, solve left and right recursively, "
                "and count cross-boundary pairs in linear time. Start with structural splits before "
                "inversion-style merges."
            ),
            "min_rating": 1200,
            "prefer_tags": ("sortings", "greedy", "constructive algorithms"),
            "avoid_tags": ("fft", "trees", "dp"),
        },
        {
            "slug": "segment-split-merges",
            "title": "Associative Range Summaries & Segment Splitting",
            "description": (
                "Maintain composable half-interval summaries (like prefix/suffix bests or frequency merges) "
                "so combining two subproblems across a split point stays fast."
            ),
            "min_rating": 1500,
            "require_any": ("data structures",),
            "avoid_tags": ("fft", "trees"),
        },
        {
            "slug": "dnc-dp-centroids",
            "title": "D&C DP Optimization & Centroid Splitting",
            "description": (
                "Exploit monotone split points `opt[i] ≤ opt[i+1]` in layered DP or recursively split trees "
                "at centroids so every path crosses a centroid within `O(log n)` recursion depth."
            ),
            "min_rating": 1700,
            "require_any": ("dp", "trees"),
            "avoid_tags": (),
        },
    ],
    "dp": [
        {
            "slug": "linear-states",
            "title": "Linear States & Decision Boundaries",
            "description": (
                "Define `dp[i]` around the minimal state needed at position `i` and isolate the exact "
                "boundary choice (skip, extend, or jump). Early steps use direct `O(1)` transitions; later "
                "problems require prefix extremes or refactoring states to drop an inner loop."
            ),
            "min_rating": 1100,
            "prefer_tags": (),
            "avoid_tags": (
                "trees",
                "graphs",
                "bitmasks",
                "strings",
                "combinatorics",
                "games",
                "geometry",
                "matrices",
                "fft",
                "flows",
                "greedy",
                "dsu",
            ),
        },
        {
            "slug": "string-subsequence-dp",
            "title": "Strings, Palindromes & Subsequence DP",
            "description": (
                "Track pattern progress in a compact auxiliary state (matched prefix length `0..k`, "
                "character class, or interval endpoints) while scanning the string. Harder steps fold "
                "character frequencies or deletions into the recurrence."
            ),
            "min_rating": 1100,
            "require_any": ("strings",),
            "avoid_tags": ("trees", "graphs", "bitmasks"),
        },
        {
            "slug": "combinatorial-counting-dp",
            "title": "Combinatorial & Modular Counting DP",
            "description": (
                "Swap `min`/`max` for modular addition while ensuring every valid configuration is "
                "produced by a unique transition path. Watch for inner summation loops that telescope into "
                "`O(1)` running prefix sums."
            ),
            "min_rating": 1300,
            "require_any": ("combinatorics", "number theory"),
            "avoid_tags": ("trees", "bitmasks", "graphs"),
        },
        {
            "slug": "tree-dag-dp",
            "title": "Trees, Subtrees & DAG Transitions",
            "description": (
                "Compute `dp[u]` post-order from children `dp[v]`, merging child subtrees one edge at a "
                "time. Later problems add top-down rerooting or topological ordering on directed graphs."
            ),
            "min_rating": 1300,
            "require_any": ("trees", "dfs and similar", "graphs"),
            "avoid_tags": ("bitmasks", "strings"),
        },
        {
            "slug": "bitmask-profile-dp",
            "title": "Bitmask & Subset State Compression",
            "description": (
                "Encode small subsets of used items or column profiles in `mask ∈ [0, 2^k)`, iterating "
                "masks in numeric order so smaller submasks are always finalized before larger ones."
            ),
            "min_rating": 1500,
            "require_any": ("bitmasks",),
            "avoid_tags": (),
        },
    ],
    "dsu": [
        {
            "slug": "components-cycles",
            "title": "Connected Components & Cycle Detection",
            "description": (
                "Maintain union-by-size with path compression, storing component aggregates at each root "
                "and catching the exact moment an edge links two vertices already in the same set."
            ),
            "min_rating": 1100,
            "require_any": ("graphs", "dfs and similar"),
            "avoid_tags": ("trees", "binary search", "two pointers"),
        },
        {
            "slug": "offline-kruskal-thresholds",
            "title": "Edge Sorting, Offline Queries & Kruskal MST",
            "description": (
                "Sort edges and queries by weight so incremental unions answer threshold connectivity in "
                "`O(α(n))`, and remember edge deletions become standard unions when processed in reverse."
            ),
            "min_rating": 1300,
            "require_any": ("sortings", "greedy", "trees"),
            "avoid_tags": ("two pointers",),
        },
        {
            "slug": "potentials-component-metadata",
            "title": "Parity Potentials & Rich Component Metadata",
            "description": (
                "Track XOR/parity offsets from each node to its DSU parent for dynamic bipartiteness "
                "checks, or merge maps/sets small-to-large across union operations."
            ),
            "min_rating": 1500,
            "require_any": ("data structures", "constructive algorithms", "dp"),
            "avoid_tags": (),
        },
    ],
    "expression parsing": [
        {
            "slug": "tokenizing-brackets",
            "title": "Tokenization, Delimiters & Bracket Nesting",
            "description": (
                "Separate clean lexing (splitting tokens and delimiters) from evaluation, using a depth "
                "counter or explicit stack to pair nested brackets without messy index arithmetic."
            ),
            "min_rating": 1000,
            "prefer_tags": ("strings", "implementation"),
            "avoid_tags": ("dp", "trees"),
        },
        {
            "slug": "precedence-syntax-trees",
            "title": "Operator Precedence & Recursive-Descent Trees",
            "description": (
                "Write one function per precedence level (`expr → term → factor`) or materialize the parse "
                "tree explicitly so DP or greedy optimization can run bottom-up on operator nodes."
            ),
            "min_rating": 1500,
            "prefer_tags": ("dp", "data structures", "trees", "dfs and similar"),
            "avoid_tags": (),
        },
    ],
    "fft": [
        {
            "slug": "polynomial-convolutions",
            "title": "Polynomial Multiplication & Sumset Convolutions",
            "description": (
                "Spot pairwise sum patterns `c[i + j] += a[i] · b[j]` (and reverse one array to handle "
                "fixed differences `i - j`) so FFT/NTT computes all convolution buckets simultaneously in "
                "`O(N log N)`."
            ),
            "min_rating": 1900,
            "prefer_tags": ("math", "combinatorics"),
            "avoid_tags": ("string suffix structures",),
        },
        {
            "slug": "dnc-ntt-matching",
            "title": "Divide-and-Conquer NTT & Wildcard Matching",
            "description": (
                "Pair binary-tree polynomial multiplication `∏(1 + x^{w_i})` or squared-difference string "
                "encodings with NTT to turn quadratic bottlenecks into `O(N log^2 N)`."
            ),
            "min_rating": 2100,
            "require_any": ("dp", "divide and conquer", "strings", "bitmasks"),
            "avoid_tags": (),
        },
    ],
    "flows": [
        {
            "slug": "maxflow-capacity-networks",
            "title": "Max-Flow Modeling & Capacity Networks",
            "description": (
                "Encode supplies, demands, and compatibility rules as directed capacities from source to "
                "sink and run Dinic's algorithm. Keep intermediate layer vertices compact so edge counts "
                "stay sharp."
            ),
            "min_rating": 1600,
            "require_any": ("graphs", "graph matchings"),
            "avoid_tags": ("dp",),
        },
        {
            "slug": "mincut-selection",
            "title": "Minimum Cut & Project-Selection Duals",
            "description": (
                "Invoke `max-flow = min-cut` when balancing conflicting rewards and penalties: design "
                "capacities so every finite `S-T` cut corresponds one-to-one with a valid set of choices."
            ),
            "min_rating": 1800,
            "prefer_tags": ("graphs", "constructive algorithms", "dfs and similar"),
            "avoid_tags": (),
        },
        {
            "slug": "mcmf-circulations",
            "title": "Min-Cost Max-Flow & Optimal Routing",
            "description": (
                "Attach per-unit edge weights and augment along shortest potential-adjusted paths whenever "
                "matching or routing must optimize cost alongside flow volume."
            ),
            "min_rating": 2000,
            "prefer_tags": ("shortest paths", "graphs", "data structures"),
            "avoid_tags": (),
        },
    ],
    "games": [
        {
            "slug": "parity-symmetry-invariants",
            "title": "Parity, Symmetry & First-Move Control",
            "description": (
                "Test small cases (`n ≤ 5`) by hand to spot an invariant—total move parity, mirror "
                "copying, or an immediate winning grab—instead of simulating turns when the outcome is "
                "predetermined."
            ),
            "min_rating": 1000,
            "prefer_tags": ("math",),
            "avoid_tags": ("dp", "trees", "graphs", "data structures"),
        },
        {
            "slug": "turn-order-greedy",
            "title": "Optimal Turn Greedy & Shared-Resource Valuation",
            "description": (
                "When two rational players pick from common items, score each move by my gain plus denied "
                "opponent gain (`a_i + b_i`) and sort descending to trace alternating optimal play."
            ),
            "min_rating": 1200,
            "require_any": ("greedy", "sortings", "constructive algorithms"),
            "avoid_tags": ("dp", "trees"),
        },
        {
            "slug": "backward-induction-grundy",
            "title": "Winning/Losing State DP & Grundy (`mex`) Numbers",
            "description": (
                "Classify states backward (Winning iff `≥ 1` move leads to Losing); for independent "
                "parallel subgames, compute Grundy values via `mex` and XOR them together."
            ),
            "min_rating": 1400,
            "require_any": ("dp", "bitmasks", "trees", "graphs"),
            "avoid_tags": (),
        },
    ],
    "geometry": [
        {
            "slug": "projections-slopes-bounds",
            "title": "Bounding Boxes, Exact Slopes & Squared Distances",
            "description": (
                "Stay in exact 64-bit integers whenever possible—compare `d^2` instead of `sqrt`, reduce "
                "direction vectors by `gcd(dx, dy)`, and check whether `x` and `y` coordinates decouple."
            ),
            "min_rating": 1000,
            "prefer_tags": ("math", "implementation"),
            "avoid_tags": ("binary search", "data structures", "dp", "sortings"),
        },
        {
            "slug": "parametric-search-geometry",
            "title": "Parametric Geometry & Binary/Ternary Search",
            "description": (
                "Fix a candidate radius, angle, or cut line so 2D feasibility reduces to 1D interval "
                "overlaps, using fixed-iteration binary/ternary search for clean floating-point precision."
            ),
            "min_rating": 1200,
            "require_any": ("binary search", "ternary search"),
            "avoid_tags": (),
        },
        {
            "slug": "cross-products-convex-hulls",
            "title": "Cross Products, Angular Sweeps & Convex Hulls",
            "description": (
                "Use 2D cross products `(B - A) × (C - A)` for orientation, collinearity, and twice-area "
                "without trig, then sort by angle or `x`-coordinate to sweep rays and hulls."
            ),
            "min_rating": 1500,
            "require_any": ("sortings", "data structures", "dp"),
            "avoid_tags": (),
        },
    ],
    "graph matchings": [
        {
            "slug": "greedy-tree-pairings",
            "title": "Tree & Degree-Bounded Pairing Invariants",
            "description": (
                "Match tree leaves greedily with their parents from the bottom up, and use parity or Hall "
                "neighborhood bottlenecks to bound maximum pairings without heavy flow code."
            ),
            "min_rating": 1200,
            "prefer_tags": ("greedy", "trees", "graphs", "constructive algorithms"),
            "avoid_tags": ("flows",),
        },
        {
            "slug": "bipartite-konig-hopcroft",
            "title": "Augmenting Paths, König Duals & Hopcroft-Karp",
            "description": (
                "Apply bipartite dualities (`min vertex cover = max matching`, `max independent set = V - "
                "max matching`) and unit-network Dinic `O(E √V)` to extract covers and path partitions."
            ),
            "min_rating": 1700,
            "require_any": ("flows", "graphs", "dfs and similar"),
            "avoid_tags": (),
        },
    ],
    "graphs": [
        {
            "slug": "components-degrees-traversal",
            "title": "Connected Components, Degrees & Traversal",
            "description": (
                "Inspect vertex degrees (`deg = 1` leaves, `deg = 2` chains/cycles) and component "
                "summaries first—many graph problems resolve directly from component sizes and edge counts."
            ),
            "min_rating": 1100,
            "require_any": ("dfs and similar", "dsu"),
            "avoid_tags": ("trees", "dp", "shortest paths", "flows", "2-sat"),
        },
        {
            "slug": "cycles-bipartite-constructions",
            "title": "Cycles, Bipartite Coloring & Edge Orientations",
            "description": (
                "Test 2-coloring whenever edges forbid equal labels, and recall any component with `E ≥ V` "
                "contains a cycle. Later steps orient or construct edges to satisfy parity and degree rules."
            ),
            "min_rating": 1200,
            "require_any": ("constructive algorithms", "greedy"),
            "avoid_tags": ("trees", "shortest paths", "flows", "dp"),
        },
        {
            "slug": "state-space-shortest-paths",
            "title": "BFS Layers & State-Space Shortest Paths",
            "description": (
                "When transitions depend on parity, remaining budget, or recent direction, embed that "
                "extra context into the node `(u, state)` and run BFS, 0-1 BFS, or Dijkstra."
            ),
            "min_rating": 1300,
            "require_any": ("shortest paths",),
            "avoid_tags": ("flows",),
        },
        {
            "slug": "dag-condensation-dp",
            "title": "DAGs, SCC Condensation & Topological DP",
            "description": (
                "Collapse strongly connected components into a DAG of supernodes so cycles disappear, then "
                "propagate optimal path values along topological order."
            ),
            "min_rating": 1400,
            "require_any": ("dp",),
            "avoid_tags": ("trees",),
        },
    ],
    "greedy": [
        {
            "slug": "sorting-exchange-arguments",
            "title": "Sorting & Exchange Arguments",
            "description": (
                "Compare swapping two adjacent items `i` and `j` to derive the exact sort comparator "
                "mathematically. Start with single-key sorts, then progress to custom `a_i + b_i` or ratio "
                "orderings."
            ),
            "min_rating": 1100,
            "require_any": ("sortings",),
            "avoid_tags": ("dp", "trees", "graphs", "data structures", "two pointers", "binary search"),
        },
        {
            "slug": "prefix-suffix-invariants",
            "title": "Prefix/Suffix Extremes & Global Bounds",
            "description": (
                "Precompute prefix and suffix aggregates so you can score every split point or single "
                "modification globally in `O(n)` rather than trusting myopic local choices."
            ),
            "min_rating": 1100,
            "require_any": ("math",),
            "avoid_tags": ("sortings", "dp", "trees", "graphs", "data structures", "bitmasks", "number theory"),
        },
        {
            "slug": "heaps-regret-greedy",
            "title": "Priority Queues & Regret Greedy",
            "description": (
                "Take choices optimistically as you sweep left-to-right while storing their costs in a "
                "heap—whenever a constraint overflows, revoke the worst past pick in `O(log n)`."
            ),
            "min_rating": 1300,
            "require_any": ("data structures", "two pointers"),
            "avoid_tags": ("dp", "trees", "graphs"),
        },
        {
            "slug": "constructive-bottlenecks",
            "title": "Bottleneck Peeling & Constructive Greedy",
            "description": (
                "Resolve the most constrained elements first (endpoints, extremes, forced leaves) where "
                "only one valid decision exists, shrinking the problem inductively."
            ),
            "min_rating": 1200,
            "require_any": ("constructive algorithms",),
            "avoid_tags": ("dp", "trees", "graphs", "sortings"),
        },
    ],
    "hashing": [
        {
            "slug": "rolling-substring-hashes",
            "title": "Polynomial Rolling Hashes & Substring Equality",
            "description": (
                "Precompute prefix hashes and base powers modulo two primes (or random base mod `2^61 - 1`) "
                "so arbitrary substrings—even stitched across deletions—compare in `O(1)`."
            ),
            "min_rating": 1300,
            "require_any": ("strings",),
            "avoid_tags": ("trees", "graphs"),
        },
        {
            "slug": "xor-multiset-fingerprints",
            "title": "Randomized XOR & Multiset Fingerprints",
            "description": (
                "Map each distinct value to a random 64-bit integer (`mt19937_64`): XORing detects "
                "odd-count mismatches, while 64-bit sums fingerprint multisets in `O(1)` per prefix."
            ),
            "min_rating": 1400,
            "prefer_tags": ("data structures", "math", "bitmasks"),
            "avoid_tags": ("strings", "string suffix structures"),
        },
        {
            "slug": "hash-binary-search-lcp",
            "title": "Hashing + Binary Search for LCP & Palindromes",
            "description": (
                "Pair `O(1)` hash equality with `O(log n)` binary search on match length to pinpoint the "
                "first differing character or longest valid palindrome."
            ),
            "min_rating": 1600,
            "require_any": ("binary search", "string suffix structures", "dp"),
            "avoid_tags": (),
        },
    ],
    "implementation": [
        {
            "slug": "state-simulation-invariants",
            "title": "Clean State Simulation & Boundary Discipline",
            "description": (
                "Normalize inputs early (0-indexing, sentinels, canonical orientation) to keep your main "
                "loop flat and bug-free, double-checking `n = 1` and all-equal edge cases."
            ),
            "min_rating": 1000,
            "prefer_tags": ("math",),
            "avoid_tags": ("dp", "graphs", "trees", "data structures", "binary search", "number theory", "greedy"),
        },
        {
            "slug": "grid-walks-periodicity",
            "title": "2D Grids, Direction Vectors & Cycle Shortcuts",
            "description": (
                "Drive grid traversals with `dx/dy` tables and helper rotations; when simulation counts "
                "are huge (`K ≤ 10^9`), jump over full periods instead of stepping one-by-one."
            ),
            "min_rating": 1100,
            "require_any": ("brute force", "constructive algorithms", "matrices", "geometry"),
            "avoid_tags": ("dp", "graphs", "trees"),
        },
        {
            "slug": "event-bookkeeping-deltas",
            "title": "Delta Arrays & Active-Set Bookkeeping",
            "description": (
                "Replace repeated range scans with difference arrays or ordered index sets so each update "
                "only touches elements whose state genuinely changes."
            ),
            "min_rating": 1200,
            "require_any": ("data structures", "sortings", "strings"),
            "avoid_tags": ("dp", "trees", "graphs"),
        },
    ],
    "interactive": [
        {
            "slug": "binary-search-queries",
            "title": "Query-Budget Halving & Binary Search",
            "description": (
                "Let the query cap guide your algorithm (`~30–60` queries means `O(log n)` halving): "
                "design a probe whose answer splits the remaining candidate interval cleanly, and flush "
                "every output."
            ),
            "min_rating": 1200,
            "require_any": ("binary search",),
            "avoid_tags": ("trees", "graphs"),
        },
        {
            "slug": "algebraic-bitwise-probing",
            "title": "Bitwise & Algebraic Invariant Probing",
            "description": (
                "Design structured queries (pairwise XORs, GCDs, or prefix sums) whose responses form an "
                "invertible system that pinpoints hidden values without wasted probes."
            ),
            "min_rating": 1400,
            "require_any": ("math", "bitmasks", "constructive algorithms"),
            "avoid_tags": ("binary search", "trees"),
        },
        {
            "slug": "interactive-trees-graphs",
            "title": "Interactive Tree & Graph Discovery",
            "description": (
                "Stratify vertices by root distance or query subtree/centroid splits so every question "
                "eliminates a guaranteed fraction of candidate edges or hidden nodes."
            ),
            "min_rating": 1600,
            "require_any": ("trees", "graphs", "dfs and similar"),
            "avoid_tags": (),
        },
    ],
    "math": [
        {
            "slug": "parity-ceilings-bounds",
            "title": "Parity, Ceilings & Closed-Form Bounds",
            "description": (
                "Check sum parity, modular invariants, and integer ceilings `(a + b - 1) / b` before "
                "simulating—multi-round processes often collapse into `max(ceil(sum / k), max_a)`."
            ),
            "min_rating": 1000,
            "prefer_tags": ("implementation",),
            "avoid_tags": (
                "number theory",
                "combinatorics",
                "geometry",
                "matrices",
                "probabilities",
                "dp",
                "graphs",
                "trees",
                "bitmasks",
                "binary search",
            ),
        },
        {
            "slug": "divisibility-modular-buckets",
            "title": "Remainders, Divisibility & Residue Buckets",
            "description": (
                "Group elements by `a[i] mod m` so pairwise or prefix divisibility reduces to matching "
                "complementary buckets `r` and `(m - r) mod m`."
            ),
            "min_rating": 1100,
            "require_any": ("number theory",),
            "avoid_tags": ("dp", "combinatorics", "graphs", "trees"),
        },
        {
            "slug": "algebraic-index-separation",
            "title": "Algebraic Rearrangement & Series Counting",
            "description": (
                "Rewrite coupled two-index equations (like `a[i] - i = a[j] - j`) so `i` and `j` isolate "
                "on opposite sides, collapsing `O(n^2)` pair checks into a single map pass."
            ),
            "min_rating": 1200,
            "require_any": ("combinatorics", "data structures", "sortings"),
            "avoid_tags": ("dp", "fft", "graphs", "trees", "number theory"),
        },
        {
            "slug": "monotonic-convex-bounds",
            "title": "Convexity, Extremal Splits & Monotone Equations",
            "description": (
                "Recall equal splits maximize products while extreme splits maximize convex sums; pair "
                "algebraic simplification with binary search when equations lack closed-form inverses."
            ),
            "min_rating": 1300,
            "require_any": ("binary search", "constructive algorithms"),
            "avoid_tags": ("graphs", "trees", "dp", "number theory"),
        },
    ],
    "matrices": [
        {
            "slug": "grid-submatrix-invariants",
            "title": "2D Grid Parity, Submatrices & Layer Scans",
            "description": (
                "Check `(r + c) mod 2` chessboard invariants, 2D prefix sums, and whether row and column "
                "operations decouple before treating all `R × C` cells as entangled."
            ),
            "min_rating": 1100,
            "prefer_tags": ("implementation", "constructive algorithms", "greedy"),
            "avoid_tags": ("dp",),
        },
        {
            "slug": "matrix-exponentiation",
            "title": "Matrix Exponentiation & Fast Recurrences",
            "description": (
                "When a small-state DP (`k ≤ 100`) applies the same linear transition `N ≤ 10^18` times, "
                "pack the coefficients into a `k × k` matrix and compute `M^N` in `O(k^3 log N)`."
            ),
            "min_rating": 1700,
            "require_any": ("dp", "math"),
            "avoid_tags": ("implementation",),
        },
        {
            "slug": "gaussian-dynamic-matrices",
            "title": "Gaussian Elimination & Segment Matrix Products",
            "description": (
                "Row-reduce linear or `GF(2)` XOR systems in `O(k^3 / w)`, or store tiny transition "
                "matrices inside segment-tree nodes to support dynamic point updates."
            ),
            "min_rating": 1900,
            "require_any": ("data structures", "bitmasks", "probabilities", "combinatorics"),
            "avoid_tags": (),
        },
    ],
    "meet-in-the-middle": [
        {
            "slug": "split-half-lookup",
            "title": "Split-in-Half Enumeration & Sorted Lookup",
            "description": (
                "When `n ≈ 36–44` makes `2^n` impossible, split into two `n/2` halves (`2^20 ≈ 10^6`), "
                "sort all left-half outcomes, and binary-search or two-pointer each right-half state "
                "against them."
            ),
            "min_rating": 1400,
            "prefer_tags": ("brute force", "binary search", "sortings", "bitmasks"),
            "avoid_tags": ("graphs", "trees"),
        },
        {
            "slug": "bidirectional-state-merge",
            "title": "Bidirectional Search & Hash-Merged Halves",
            "description": (
                "Expand `k/2` steps forward from the start and `k/2` steps backward from the goal, "
                "intersecting canonical state signatures in the middle to square-root the search space."
            ),
            "min_rating": 1700,
            "prefer_tags": ("dp", "math", "hashing", "data structures", "number theory"),
            "avoid_tags": (),
        },
    ],
    "number theory": [
        {
            "slug": "gcd-lcm-invariants",
            "title": "GCD, LCM & Difference Invariance",
            "description": (
                "Use `gcd(a, b) = gcd(a, |a - b|)` whenever constants shift an array, and remember prefix "
                "GCDs can change at most `log2(V)` times because each drop divides by at least `2`."
            ),
            "min_rating": 1100,
            "prefer_tags": ("math",),
            "avoid_tags": ("combinatorics", "dp", "trees", "graphs", "brute force", "greedy"),
            "keywords": ("gcd", "lcm", "coprime", "divis", "mod", "multiple"),
        },
        {
            "slug": "divisors-prime-factorization",
            "title": "Trial Division (`O(√n)`), Prime Exponents & Sieves",
            "description": (
                "Factor values up to `√x` or precompute smallest prime factors `spf[x]` with a sieve so "
                "product and divisibility constraints reduce to per-prime exponent rules."
            ),
            "min_rating": 1100,
            "require_any": ("brute force", "data structures", "sortings"),
            "avoid_tags": ("combinatorics", "dp", "trees", "graphs"),
            "keywords": ("divis", "prime", "factor", "multiply", "equalize"),
        },
        {
            "slug": "modular-constructive",
            "title": "Modular Arithmetic & Constructive Remainders",
            "description": (
                "Probe small moduli (`2, 3, 4, 2^k`) first to expose universal patterns, then scale up "
                "with modular exponentiation and coprime constructions."
            ),
            "min_rating": 1200,
            "require_any": ("constructive algorithms", "bitmasks"),
            "avoid_tags": ("dp",),
        },
        {
            "slug": "divisor-sieve-dp",
            "title": "Harmonic Multiples & Exact-GCD Counting",
            "description": (
                "Iterate multiples `m = d, 2d, 3d, …` from `M` down to `1` to turn 'divisible by `d`' "
                "counts into 'gcd equals `d` exactly' via `f(d) - ∑_{k≥2} exact[k·d]` in `O(M log M)`."
            ),
            "min_rating": 1400,
            "require_any": ("dp", "combinatorics"),
            "avoid_tags": (),
        },
    ],
    "probabilities": [
        {
            "slug": "linearity-of-expectation",
            "title": "Linearity of Expectation & Indicator Events",
            "description": (
                "`E[∑ X_i] = ∑ E[X_i]` holds even when events are strongly dependent. Decompose total "
                "score/size into 0/1 indicator variables ('does item `i` contribute?') and sum their "
                "individual probabilities."
            ),
            "min_rating": 1200,
            "prefer_tags": ("math", "combinatorics", "trees"),
            "avoid_tags": ("dp", "matrices", "fft"),
        },
        {
            "slug": "expected-value-dp",
            "title": "Expected-Value DP & Self-Loop Algebra",
            "description": (
                "Work backward from terminal states (`E[done] = 0`); when state `s` loops back to itself "
                "with probability `p`, move `p · E[s]` to the left-hand side and divide by `(1 - p)`."
            ),
            "min_rating": 1500,
            "require_any": ("dp",),
            "avoid_tags": ("matrices",),
        },
        {
            "slug": "markov-chains-random-walks",
            "title": "Markov Chains, Games & Absorption Probabilities",
            "description": (
                "Raise transition matrices to high powers for long random walks or eliminate cyclic states "
                "systematically when transitions lack a DAG order."
            ),
            "min_rating": 1800,
            "require_any": ("matrices", "games", "bitmasks"),
            "avoid_tags": (),
        },
    ],
    "schedules": [
        {
            "slug": "deadline-exchange-order",
            "title": "Deadlines, Bottlenecks & Exchange Ordering",
            "description": (
                "Compare executing job `A` then `B` vs. `B` then `A` to establish the optimal processing "
                "order (earliest deadline or Smith's ratio), then simulate or DP along that sorted sequence."
            ),
            "min_rating": 1000,
            "prefer_tags": ("greedy", "sortings", "binary search", "dp"),
            "avoid_tags": (),
        },
        {
            "slug": "multistage-regret-scheduling",
            "title": "Regret Heaps & Multi-Stage Scheduling",
            "description": (
                "Sweep deadlines in order while keeping accepted durations in a max-heap—if the current "
                "job misses its deadline, swap out the longest accepted job whenever doing so saves time."
            ),
            "min_rating": 1500,
            "prefer_tags": ("greedy", "data structures", "math"),
            "avoid_tags": (),
        },
    ],
    "shortest paths": [
        {
            "slug": "bfs-01bfs-multisource",
            "title": "Multi-Source BFS & 0-1 Deque Layers",
            "description": (
                "Seed the queue with all starting sources at distance `0` simultaneously, and reach for a "
                "0-1 deque (`0`-edges to front, `1`-edges to back) in `O(V + E)` before heavier heaps."
            ),
            "min_rating": 1200,
            "require_any": ("dfs and similar", "implementation", "constructive algorithms"),
            "avoid_tags": ("data structures", "flows", "dp"),
        },
        {
            "slug": "dijkstra-relaxations",
            "title": "Dijkstra's Algorithm & Virtual Hub Nodes",
            "description": (
                "Discard outdated heap entries (`if d > dist[u]`) and compress dense clique/teleport "
                "transitions through virtual intermediate nodes so edge counts stay near-linear."
            ),
            "min_rating": 1400,
            "require_any": ("graphs", "data structures", "greedy"),
            "avoid_tags": ("flows", "dp"),
        },
        {
            "slug": "state-graphs-floyd-warshall",
            "title": "Augmented State Graphs & Floyd-Warshall",
            "description": (
                "Clone vertices as `(u, state)` to track discounts, parities, or vehicle switches inside "
                "Dijkstra, or leverage Floyd-Warshall's outer `k`-loop to introduce vertices one-by-one."
            ),
            "min_rating": 1600,
            "require_any": ("dp",),
            "avoid_tags": (),
        },
    ],
    "sortings": [
        {
            "slug": "medians-extremal-pairs",
            "title": "Medians, Order Statistics & Adjacent Gaps",
            "description": (
                "Recall the median minimizes `∑|a_i - x|` and closest values always become neighbors after "
                "sorting. Check whether pairing extremes `(a[i], a[n-1-i])` or adjacent items wins."
            ),
            "min_rating": 1000,
            "prefer_tags": ("math", "implementation"),
            "avoid_tags": ("data structures", "two pointers", "binary search", "dp", "graphs", "trees", "greedy"),
        },
        {
            "slug": "custom-comparators-greedy",
            "title": "Custom Comparators & Interval Ordering",
            "description": (
                "Sort intervals by right endpoint for maximum non-overlapping picks or left endpoint for "
                "coverage, ensuring your custom comparator defines a strict weak order (`<`, never `<=`)."
            ),
            "min_rating": 1100,
            "require_any": ("greedy",),
            "avoid_tags": ("data structures", "two pointers", "binary search", "dp", "trees", "graphs"),
        },
        {
            "slug": "sweepline-compression",
            "title": "Sweep Line Events & Coordinate Compression",
            "description": (
                "Convert intervals `[L, R]` into sorted `+1/-1` boundary events (tying endpoints "
                "carefully) or compress sparse `10^9` coordinates into compact `0..n-1` ranks."
            ),
            "min_rating": 1300,
            "require_any": ("data structures", "binary search", "two pointers"),
            "avoid_tags": ("trees", "graphs"),
        },
    ],
    "string suffix structures": [
        {
            "slug": "kmp-z-borders",
            "title": "Prefix Function (KMP), Z-Array & Periodicity",
            "description": (
                "Compute `pi[i]` or `Z[i]` in `O(n)` to enumerate all prefix-suffix borders and minimal "
                "periods `n - pi[n-1]`. Join `pattern + '#' + text` to turn matching into array scans."
            ),
            "min_rating": 1500,
            "require_any": ("strings",),
            "prefer_tags": ("hashing", "dp", "two pointers"),
            "avoid_tags": ("trees", "flows"),
        },
        {
            "slug": "suffix-array-automaton",
            "title": "Suffix Arrays, LCP Ranges & Suffix Automata",
            "description": (
                "Pair sorted suffixes with adjacent LCP heights (and RMQ / monotonic stacks) or SAM link "
                "trees to count distinct substrings and multi-occurrence factors in `O(n log n)` or `O(n)`."
            ),
            "min_rating": 1900,
            "require_any": ("data structures", "binary search", "divide and conquer", "dp"),
            "avoid_tags": (),
        },
    ],
    "strings": [
        {
            "slug": "frequencies-rle-scans",
            "title": "Run-Length Blocks, Palindromes & 26-Way Scans",
            "description": (
                "Compress consecutive identical letters into run-length blocks and leverage the tiny "
                "26-letter alphabet—iterating all 26 target characters often turns a hard string problem "
                "into `O(26 · n)`."
            ),
            "min_rating": 1100,
            "prefer_tags": ("two pointers", "implementation"),
            "avoid_tags": (
                "dp",
                "hashing",
                "string suffix structures",
                "trees",
                "graphs",
                "constructive algorithms",
                "sortings",
            ),
        },
        {
            "slug": "lexicographical-greedy",
            "title": "Lexicographical Greedy & Constructive Edits",
            "description": (
                "Lexicographical order is decided at the very first differing index: spend operations "
                "greedily to minimize the earliest possible character before optimizing later positions."
            ),
            "min_rating": 1100,
            "require_any": ("constructive algorithms", "sortings", "greedy"),
            "avoid_tags": ("dp", "hashing", "string suffix structures", "trees", "graphs"),
        },
        {
            "slug": "string-partition-dp",
            "title": "Subsequence Automaton & String DP",
            "description": (
                "Precompute `next_pos[i][c]` jumps or track small pattern/character states in DP so "
                "subsequence matching, deletions, and string partitions run cleanly in linear time."
            ),
            "min_rating": 1200,
            "require_any": ("dp",),
            "avoid_tags": ("string suffix structures", "trees"),
        },
        {
            "slug": "rolling-hash-borders",
            "title": "Rolling Hashes, Prefix Borders & Periodicity",
            "description": (
                "Move beyond character-by-character scans with `O(1)` substring hashes or KMP/Z border "
                "arrays to detect cyclic rotations, tandem repeats, and stitched palindromes."
            ),
            "min_rating": 1400,
            "require_any": ("hashing", "string suffix structures", "binary search"),
            "avoid_tags": (),
        },
    ],
    "ternary search": [
        {
            "slug": "unimodal-integer-valleys",
            "title": "Unimodal Valleys & Discrete Derivative Search",
            "description": (
                "When total cost is a sum of convex U-shaped terms, binary-search where the discrete slope "
                "`f(x + 1) - f(x)` crosses `0` to dodge flat-plateau pitfalls on integers."
            ),
            "min_rating": 1200,
            "prefer_tags": ("math", "binary search", "greedy"),
            "avoid_tags": ("geometry", "trees"),
        },
        {
            "slug": "continuous-geometric-minimax",
            "title": "Continuous Minimax & Nested Convex Search",
            "description": (
                "Recall that the maximum of convex functions (such as `max_i dist(p, p_i)`) stays "
                "convex—run 80–100 fixed iterations on real coordinates for rock-solid precision."
            ),
            "min_rating": 1500,
            "prefer_tags": ("geometry", "data structures", "dp", "implementation"),
            "avoid_tags": (),
        },
    ],
    "trees": [
        {
            "slug": "subtree-dfs-depths",
            "title": "Subtree Sizes, Depths & Post-Order DFS",
            "description": (
                "Root at node `1` and compute `sz[u]` and `dep[u]` in one DFS—remember removing any single "
                "tree edge splits the vertices cleanly into `sz[v]` inside vs. `n - sz[v]` outside."
            ),
            "min_rating": 1100,
            "require_any": ("dfs and similar",),
            "avoid_tags": ("data structures", "divide and conquer", "binary search", "flows"),
        },
        {
            "slug": "leaves-diameter-greedy",
            "title": "Leaves, Diameter & Greedy Tree Operations",
            "description": (
                "Count degree-1 leaves and find the diameter with two BFS/DFS sweeps (`1 → A → B`): many "
                "tree operation bounds depend purely on leaf count or diameter radius."
            ),
            "min_rating": 1100,
            "require_any": ("greedy", "constructive algorithms"),
            "avoid_tags": ("dp", "data structures", "divide and conquer"),
        },
        {
            "slug": "subtree-dp-rerooting",
            "title": "Subtree DP & All-Roots Rerooting",
            "description": (
                "Combine child DP states bottom-up first; when answers are needed for every vertex as "
                "root, pass the 'outside subtree `u`' summary downward in a second `O(n)` pass."
            ),
            "min_rating": 1400,
            "require_any": ("dp",),
            "avoid_tags": ("divide and conquer", "data structures"),
        },
        {
            "slug": "lca-euler-tour-ds",
            "title": "Euler Tour (`tin`/`tout`), Binary Lifting & LCA",
            "description": (
                "Jump `2^k` ancestors for `O(log n)` LCA and path lengths `dep[u] + dep[v] - 2·dep[lca]`, "
                "or flatten subtrees into `[tin[u], tout[u]]` ranges for Fenwick/segment tree queries."
            ),
            "min_rating": 1500,
            "require_any": ("data structures", "binary search", "dsu"),
            "avoid_tags": (),
        },
    ],
    "two pointers": [
        {
            "slug": "sliding-window-monotonic",
            "title": "Sliding Window & Monotonic Subarray Validity",
            "description": (
                "Verify window monotonicity first (shrinking `L` preserves validity); then advance `R` one "
                "step at a time and pull `L` forward in a `while` loop for `O(n)` total work."
            ),
            "min_rating": 1100,
            "prefer_tags": ("greedy", "implementation"),
            "avoid_tags": ("sortings", "trees", "graphs", "dsu", "data structures", "binary search"),
        },
        {
            "slug": "sorted-opposite-ends",
            "title": "Sorted Opposite-End Pointers & Pair Matching",
            "description": (
                "Sort first and place `L = 0, R = n - 1`: comparing `a[L] + a[R]` against the target "
                "eliminates either `L` or `R` at every step while counting whole blocks of valid partners."
            ),
            "min_rating": 1100,
            "require_any": ("sortings",),
            "avoid_tags": ("data structures", "dp", "trees", "graphs", "dsu"),
        },
        {
            "slug": "window-maps-deques",
            "title": "Stateful Windows with Maps, Sets & Deques",
            "description": (
                "When validity depends on distinct-value counts or `max - min ≤ K` rather than a simple "
                "sum, maintain window state incrementally inside a frequency map, `multiset`, or monotonic deque."
            ),
            "min_rating": 1200,
            "require_any": ("data structures",),
            "avoid_tags": ("trees", "graphs", "dsu"),
        },
        {
            "slug": "two-pointer-dp-counting",
            "title": "Valid-Endpoint Counting & Two-Pointer DP",
            "description": (
                "Once you maintain the furthest valid left bound `L(R)` for each right endpoint `R`, "
                "immediately count all `R - L(R) + 1` valid subarrays or sum DP transitions across `[L(R), R]`."
            ),
            "min_rating": 1300,
            "require_any": ("dp", "combinatorics"),
            "avoid_tags": (),
        },
    ],
}


def base_problem_title(name: str) -> str:
    cleaned = re.sub(
        r"\((?:easy|hard|medium|simple|extreme)\s*version\)",
        "",
        name,
        flags=re.IGNORECASE,
    )
    return re.sub(r"[^a-z0-9]", "", cleaned.lower())


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


def match_sprint_solution(
    prob: dict[str, Any],
    records: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the solved record matching a sprint problem (including Div.1/Div.2 twins or hard versions)."""
    pid = prob["id"].upper()
    if pid in by_id:
        return by_id[pid]

    prob_norm = normalize_title(prob["name"])
    prob_base = base_problem_title(prob["name"])
    prob_cid = int(prob["contestId"])
    prob_rating = prob.get("rating") or 0

    for rec in records:
        if abs(int(rec["contestId"]) - prob_cid) <= 1 and normalize_title(rec["name"]) == prob_norm:
            return rec
        if (
            int(rec["contestId"]) == prob_cid
            and prob_base
            and base_problem_title(rec["name"]) == prob_base
            and (rec.get("rating") or 0) >= prob_rating
        ):
            return rec
    return None


def compute_sprint_start_rating(
    tag: str,
    records: list[dict[str, Any]],
    completed_sprints: list[dict[str, Any]],
) -> int:
    """Determine progressive starting rating for the next sprint in `tag`."""
    comfort, _, _ = compute_comfort_and_target(records)
    tag_ratings = sorted(r["rating"] for r in records if tag in r["tags"] and r["rating"] is not None)

    if completed_sprints:
        last_probs = completed_sprints[-1].get("problems", [])
        if last_probs and last_probs[0].get("rating") is not None:
            return min(3200, max(comfort, int(last_probs[0]["rating"]) + 100))

    if not tag_ratings:
        base = max(800, comfort - 100)
    elif len(tag_ratings) == 1:
        base = max(800, comfort - 100, tag_ratings[0] - 100)
    else:
        tag_med = int(round(statistics.median(tag_ratings) / 100.0) * 100)
        top1 = tag_ratings[-1]
        bump = 100 if (top1 >= tag_med + 200 or len(tag_ratings) >= 4) else 0
        base = max(comfort, tag_med + bump)

    return int(round(base / 100.0) * 100)


def build_tag_sprint(
    tag: str,
    sprint_num: int,
    records: list[dict[str, Any]],
    completed_sprints: list[dict[str, Any]],
    index: ProblemIndex,
    claimed_ids: set[str],
) -> dict[str, Any] | None:
    """Construct a progressive 4-problem sprint teaching a specific subtopic/algorithm of `tag`."""
    if not index.available:
        return None

    tracks = SPRINT_CURRICULUM.get(tag) or [
        {
            "slug": "core-progression",
            "title": f"{tag.title()} Progression",
            "description": (
                f"Build fluency in `{tag}` from direct applications up to multi-step contest syntheses."
            ),
            "min_rating": 1000,
            "prefer_tags": (),
            "avoid_tags": (),
        }
    ]
    track = tracks[(sprint_num - 1) % len(tracks)]
    base_r = max(track.get("min_rating", 800), compute_sprint_start_rating(tag, records, completed_sprints))

    solved_ids = {r["id"].upper() for r in records}
    solved_bases = {base_problem_title(r["name"]) for r in records if base_problem_title(r["name"])}
    prior_ids = {p["id"].upper() for sp in completed_sprints for p in sp.get("problems", [])}
    blocked_ids = solved_ids | prior_ids

    pool = [
        p
        for p in index.all_problems
        if not p["is_special"]
        and p["rating"] is not None
        and p["name"].isascii()
        and tag in p["tags"]
        and p["id"] not in blocked_ids
        and base_problem_title(p["name"]) not in solved_bases
    ]
    if not pool:
        pool = [
            p
            for p in index.all_problems
            if not p["is_special"]
            and p["rating"] is not None
            and p["name"].isascii()
            and tag in p["tags"]
            and p["id"] not in solved_ids
        ]
    if not pool:
        return None

    target_len = 3 if 4 <= len(pool) <= 6 else min(4, len(pool))
    req_any = set(track.get("require_any", ()))
    prefer = set(track.get("prefer_tags", ()))
    avoid = set(track.get("avoid_tags", ()))
    if tag not in ("interactive", "communication"):
        avoid = avoid | {"interactive", "communication"}
    keywords = tuple(k.lower() for k in track.get("keywords", ()))

    def score_candidate(p: dict[str, Any], step_idx: int, strict: bool) -> float | None:
        ptags = set(p["tags"])
        if strict:
            if req_any and not (ptags & req_any):
                return None
            if avoid and (ptags & avoid):
                return None
            if len(ptags) > 5:
                return None

        sc = math.log1p(max(1, p["solvedCount"])) * 10.0
        if p["contestId"] >= 1750:
            sc += 16.0
        elif p["contestId"] >= 1500:
            sc += 9.0
        elif p["contestId"] >= 1200:
            sc += 4.0

        if req_any and (ptags & req_any):
            sc += 30.0
        sc += 12.0 * len(ptags & prefer)
        sc -= 30.0 * len(ptags & avoid)

        if keywords:
            lower_name = p["name"].lower()
            if any(kw in lower_name for kw in keywords):
                sc += 15.0

        unrelated = len(ptags - {tag} - req_any - prefer)
        if step_idx == 0:
            sc -= 9.0 * unrelated
        elif step_idx == 1:
            sc -= 7.0 * unrelated
        else:
            sc -= 5.0 * max(0, unrelated - 1)
            if len(ptags) >= 6:
                sc -= 15.0

        return sc

    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()
    chosen_bases: set[str] = set()

    avail_ge = sorted({p["rating"] for p in pool if p["rating"] >= base_r})
    curr_target = avail_ge[0] if avail_ge else min(p["rating"] for p in pool)

    for step_idx in range(target_len):
        min_allowed = curr_target if step_idx == 0 else (chosen[-1]["rating"] + 100)
        best: dict[str, Any] | None = None

        windows: list[tuple[int, int, bool, bool]] = [
            (min_allowed, min_allowed, True, True),
            (min_allowed, min_allowed + 100, True, True),
            (min_allowed, min_allowed + 200, True, True),
            (min_allowed, min_allowed + 100, True, False),
            (min_allowed, min_allowed + 100, False, True),
            (min_allowed, min_allowed + 400, True, True),
            (min_allowed, 3500, True, True),
            (min_allowed, 3500, False, True),
            (min_allowed, 3500, False, False),
        ]
        if step_idx > 0:
            same_r = chosen[-1]["rating"]
            windows.append((same_r, same_r, True, False))
            windows.append((same_r, same_r, False, False))

        for r_lo, r_hi, strict, respect_claimed in windows:
            cands: list[tuple[float, dict[str, Any]]] = []
            for p in pool:
                p_base = base_problem_title(p["name"])
                if p["id"] in chosen_ids or (p_base and p_base in chosen_bases):
                    continue
                if respect_claimed and p["id"] in claimed_ids:
                    continue
                if not (r_lo <= p["rating"] <= r_hi):
                    continue
                s = score_candidate(p, step_idx, strict)
                if s is None:
                    continue
                dist_pen = ((p["rating"] - min_allowed) // 100) * 14.0
                cands.append((s - dist_pen, p))
            if cands:
                cands.sort(key=lambda item: (item[0], item[1]["solvedCount"], item[1]["contestId"]), reverse=True)
                best = cands[0][1]
                break

        if best is None:
            rem = [p for p in pool if p["id"] not in chosen_ids]
            if not rem:
                break
            prev_r = chosen[-1]["rating"] if chosen else 0
            ge = [p for p in rem if p["rating"] >= prev_r]
            pick_pool = ge if ge else rem
            pick_pool.sort(key=lambda p: (p["rating"], -p["solvedCount"]))
            best = pick_pool[0]

        chosen.append(best)
        chosen_ids.add(best["id"])
        b_title = base_problem_title(best["name"])
        if b_title:
            chosen_bases.add(b_title)

    chosen.sort(key=lambda p: (p["rating"], p["id"]))
    return {
        "sprint": sprint_num,
        "track_slug": track["slug"],
        "title": track["title"],
        "description": track["description"],
        "problems": [
            {
                "id": p["id"],
                "contestId": p["contestId"],
                "index": p["index"],
                "name": p["name"],
                "rating": p["rating"],
            }
            for p in chosen
        ],
    }


def load_sprints_state() -> dict[str, Any]:
    if not SPRINTS_PATH.exists():
        return {"seq": 0, "tags": {}}
    try:
        raw = json.loads(SPRINTS_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("tags"), dict):
            return {"seq": int(raw.get("seq", 0)), "tags": raw["tags"]}
    except Exception as exc:
        print(f"[warn] Failed to parse sprints.json ({exc}); rebuilding.")
    return {"seq": 0, "tags": {}}


def save_sprints_state(state: dict[str, Any]) -> None:
    ordered_tags = {k: state["tags"][k] for k in sorted(state["tags"])}
    payload = {"seq": int(state.get("seq", 0)), "tags": ordered_tags}
    SPRINTS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def sync_sprints(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Update sprint progress from solved records and auto-generate a new sprint whenever one finishes."""
    state = load_sprints_state()
    seq = int(state.get("seq", 0))
    tags_map: dict[str, dict[str, Any]] = state["tags"]

    extra_tags = {t for r in records for t in r["tags"]} - set(ALL_CF_TAGS)
    all_tags = sorted(set(ALL_CF_TAGS) | extra_tags)
    by_id = {r["id"].upper(): r for r in records}

    claimed_ids: set[str] = set()

    # Pass 1: Check completion of existing active sprints and lock in ongoing ones.
    for tag in all_tags:
        t_entry = tags_map.setdefault(tag, {"active": None, "completed": []})
        active = t_entry.get("active")
        if not active or not active.get("problems"):
            t_entry["active"] = None
            continue

        probs = active["problems"]
        matched = [match_sprint_solution(p, records, by_id) for p in probs]
        if all(m is not None for m in matched):
            if index.available:
                seq += 1
                done_dates = [m["completed"] for m in matched if m and m.get("completed")]
                completed_at = max(done_dates) if done_dates else dt.date.today().isoformat()
                archived = dict(active)
                archived["completed_at"] = completed_at
                archived["completed_seq"] = seq
                t_entry.setdefault("completed", []).append(archived)
                t_entry["active"] = None
            else:
                for p in probs:
                    claimed_ids.add(p["id"].upper())
        else:
            for p in probs:
                claimed_ids.add(p["id"].upper())

    # Pass 2: Generate a fresh progressive sprint for any tag without an active sprint.
    # Order core/practiced tags first so they get first pick of unclaimed problems.
    comfort, _, _ = compute_comfort_and_target(records)
    core_tags, _ = classify_tags(index, comfort, all_tags)
    by_tag_cnt = collections.Counter(t for r in records for t in r["tags"])
    gen_order = sorted(
        all_tags,
        key=lambda t: (0 if t in core_tags else 1, -by_tag_cnt[t], t),
    )

    if index.available:
        for tag in gen_order:
            t_entry = tags_map[tag]
            if t_entry.get("active") is None:
                completed_list = t_entry.get("completed", [])
                next_num = len(completed_list) + 1
                new_sprint = build_tag_sprint(tag, next_num, records, completed_list, index, claimed_ids)
                t_entry["active"] = new_sprint
                if new_sprint:
                    for p in new_sprint["problems"]:
                        claimed_ids.add(p["id"].upper())

    state["seq"] = seq
    if persist:
        save_sprints_state(state)
    return state


def sprint_progress(
    sprint: dict[str, Any] | None,
    records: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> tuple[int, int, list[dict[str, Any] | None]]:
    if not sprint or not sprint.get("problems"):
        return (0, 0, [])
    matches = [match_sprint_solution(p, records, by_id) for p in sprint["problems"]]
    done = sum(1 for m in matches if m is not None)
    return (done, len(matches), matches)


def format_sprint_markdown(
    sprint: dict[str, Any],
    records: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    *,
    heading: str,
    ratings_rel_prefix: str,
) -> list[str]:
    """Render a sprint heading, brief coaching push, and progressive checklist."""
    _, _, matches = sprint_progress(sprint, records, by_id)
    out = [
        heading,
        "",
        sprint["description"],
        "",
    ]
    for idx, (prob, sol) in enumerate(zip(sprint["problems"], matches), start=1):
        p_link = f"[{prob['id']} - {prob['name']}]({problem_url(prob['contestId'], prob['index'])})"
        r_str = f"**{prob['rating']}**" if prob.get("rating") is not None else "**unrated**"
        if sol is not None:
            r_dir = format_rating_dir(sol["rating"])
            s_link = f"[{sol['file']}]({ratings_rel_prefix}/{r_dir}/{sol['file']})"
            out.append(f"{idx}. [x] {r_str} · {p_link} — {s_link}")
        else:
            out.append(f"{idx}. [ ] {r_str} · {p_link}")
    return out


def select_featured_sprint_tags(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    sprints_state: dict[str, Any],
    *,
    limit: int = 4,
) -> list[str]:
    """Choose featured tag sprints for the root README (pinning in-progress & newly unlocked sprints)."""
    tags_map = sprints_state.get("tags", {})
    extra_tags = {t for r in records for t in r["tags"]} - set(ALL_CF_TAGS)
    all_tags = sorted(set(ALL_CF_TAGS) | extra_tags)
    available_tags = [t for t in all_tags if tags_map.get(t, {}).get("active")]
    if not available_tags:
        return []

    by_id = {r["id"].upper(): r for r in records}
    comfort, _, _ = compute_comfort_and_target(records)
    core_tags, _ = classify_tags(index, comfort, all_tags)
    cap = max(1500, comfort + 300)
    cf_counts = index.count_tag_up_to_rating(cap) if index.available else collections.Counter()

    by_tag: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in records:
        for t in rec["tags"]:
            by_tag[t].append(rec)

    featured: list[str] = []

    def add_pick(tag: str) -> None:
        if tag in available_tags and tag not in featured and len(featured) < limit:
            featured.append(tag)

    # 1. Always pin sprints currently in progress (1..N-1 solved) so progress shows right on main README.
    in_progress: list[tuple[float, int, str]] = []
    for t in available_tags:
        done, total, _ = sprint_progress(tags_map[t]["active"], records, by_id)
        if 0 < done < total:
            in_progress.append((done / total, done, t))
    in_progress.sort(key=lambda x: (-x[0], -x[1], x[2]))
    for _, _, t in in_progress:
        add_pick(t)

    # 2. Showcase tags that most recently completed a sprint so the newly created sprint is visible.
    recently_rolled: list[tuple[int, str]] = []
    for t in available_tags:
        comp = tags_map[t].get("completed", [])
        if comp:
            last_seq = max(int(c.get("completed_seq", 0)) for c in comp)
            recently_rolled.append((last_seq, t))
    recently_rolled.sort(key=lambda x: (-x[0], x[1]))
    for _, t in recently_rolled:
        add_pick(t)

    # 3. Fill remaining slots with a balanced mix: practiced algorithmic, lightly practiced, and blind spot.
    broad_generic = {"implementation", "math", "brute force"}
    practiced_algo = sorted(
        [t for t in available_tags if len(by_tag[t]) >= 3 and t in core_tags],
        key=lambda t: (1 if t in broad_generic else 0, len(by_tag[t]), t),
    )
    lightly_core = sorted(
        [t for t in available_tags if 1 <= len(by_tag[t]) <= 2 and t in core_tags],
        key=lambda t: (len(by_tag[t]), -cf_counts[t], t),
    )
    blind_core = sorted(
        [t for t in available_tags if not by_tag[t] and t in core_tags],
        key=lambda t: (-cf_counts[t], t),
    )

    for bucket, quota in ((practiced_algo, 1), (lightly_core, 2), (blind_core, 1)):
        added = 0
        for t in bucket:
            if t not in featured and len(featured) < limit:
                featured.append(t)
                added += 1
                if added >= quota:
                    break

    for t in practiced_algo + lightly_core + blind_core + available_tags:
        add_pick(t)

    return featured


def rebuild_tags_directory(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    sprints_state: dict[str, Any],
) -> None:
    """Create all 37 tag folders, populate difficulty-sorted symlinks, and write per-tag READMEs."""
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {r["id"].upper(): r for r in records}
    tags_map = sprints_state.get("tags", {})

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

        t_sprint_info = tags_map.get(tag, {})
        active_sprint = t_sprint_info.get("active")
        completed_sprints = t_sprint_info.get("completed", [])

        lines = [
            f"# {tag}",
            "",
            "[← All Tags](../README.md) · [← Dashboard](../../README.md)",
            "",
        ]

        sprint_badge = (
            f" · **{len(completed_sprints)}** sprint{'s' if len(completed_sprints) != 1 else ''} completed"
            if completed_sprints
            else ""
        )

        if tag_records:
            r_vals = [r["rating"] for r in tag_records if r["rating"] is not None]
            r_span = (
                f"{min(r_vals)}–{max(r_vals)}"
                if len(set(r_vals)) > 1
                else (str(r_vals[0]) if r_vals else "unrated")
            )
            lines.extend(
                [
                    f"**{len(tag_records)}** solved · rating **{r_span}**{sprint_badge}",
                    "",
                    "| Rating | Problem | Solution |",
                    "| :---: | :--- | :--- |",
                ]
            )
            for rec in tag_records:
                r_disp = str(rec["rating"]) if rec["rating"] is not None else "unrated"
                p_link = f"[{rec['id']} - {rec['name']}]({problem_url(rec['contestId'], rec['index'])})"
                r_dir = format_rating_dir(rec["rating"])
                s_link = f"[{rec['file']}](../../ratings/{r_dir}/{rec['file']})"
                lines.append(f"| {r_disp} | {p_link} | {s_link} |")
            lines.append("")
        else:
            lines.extend([f"*0 solved so far.*{sprint_badge}", ""])

        if active_sprint and active_sprint.get("problems"):
            done_cnt, total_cnt, _ = sprint_progress(active_sprint, records, by_id)
            s_num = active_sprint.get("sprint", len(completed_sprints) + 1)
            heading = f"## Suggested Sprint — {active_sprint['title']} *(Sprint {s_num} · {done_cnt}/{total_cnt})*"
            lines.extend(
                format_sprint_markdown(
                    active_sprint,
                    records,
                    by_id,
                    heading=heading,
                    ratings_rel_prefix="../../ratings",
                )
            )
            lines.append("")

        if completed_sprints:
            lines.extend(
                [
                    "<details>",
                    f"<summary>Completed Sprints ({len(completed_sprints)})</summary>",
                    "",
                ]
            )
            for comp in completed_sprints:
                c_links = ", ".join(
                    f"[{p['id']}]({problem_url(p['contestId'], p['index'])}) ({p['rating']})"
                    for p in comp.get("problems", [])
                )
                c_date = f" — *{comp['completed_at']}*" if comp.get("completed_at") else ""
                lines.append(f"- **Sprint {comp.get('sprint', '?')}: {comp['title']}** ({c_links}){c_date}")
            lines.extend(["", "</details>", ""])

        (tag_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_ratings_readme(records: list[dict[str, Any]]) -> None:
    RATINGS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# By Difficulty",
        "",
        "[← Dashboard](../README.md) · [By Tag →](../tags/README.md)",
        "",
        "| Rating | Problem | Solution | Completed |",
        "| :---: | :--- | :--- | :---: |",
    ]
    for rec in sorted(
        records,
        key=lambda r: (r["rating"] if r["rating"] is not None else 9999, r["id"], r["file"]),
    ):
        r_dir = format_rating_dir(rec["rating"])
        r_label = str(rec["rating"]) if rec["rating"] is not None else "unrated"
        r_link = f"[{r_label}](./{r_dir}/)"
        p_link = f"[{rec['id']} - {rec['name']}]({problem_url(rec['contestId'], rec['index'])})"
        s_link = f"[{rec['file']}](./{r_dir}/{rec['file']})"
        lines.append(f"| {r_link} | {p_link} | {s_link} | {rec['completed']} |")

    lines.append("")
    (RATINGS_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def format_tag_sprint_cell(
    tag: str,
    slug: str,
    tags_map: dict[str, Any],
    records: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> str:
    t_info = tags_map.get(tag, {})
    active = t_info.get("active")
    if not active or not active.get("problems"):
        return "—"
    done, total, _ = sprint_progress(active, records, by_id)
    prog = f"**{done}/{total}**" if done > 0 else f"{done}/{total}"
    return f"[{active['title']}](./{slug}/) ({prog})"


def write_tags_readme(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    sprints_state: dict[str, Any],
) -> None:
    comfort, _, _ = compute_comfort_and_target(records)
    extra_tags = {t for r in records for t in r["tags"]} - set(ALL_CF_TAGS)
    all_tags = sorted(set(ALL_CF_TAGS) | extra_tags)
    core_tags, _ = classify_tags(index, comfort, all_tags)
    cap = max(1500, comfort + 300)
    cf_counts = index.count_tag_up_to_rating(cap) if index.available else collections.Counter()
    by_id = {r["id"].upper(): r for r in records}
    tags_map = sprints_state.get("tags", {})

    by_tag: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in records:
        for t in rec["tags"]:
            by_tag[t].append(rec)

    solid = sorted([t for t in all_tags if len(by_tag[t]) >= 3], key=lambda t: (-len(by_tag[t]), t))
    lightly_practiced = sorted(
        [t for t in all_tags if 1 <= len(by_tag[t]) <= 2],
        key=lambda t: (-len(by_tag[t]), t),
    )
    unpracticed_core = sorted(
        [t for t in all_tags if not by_tag[t] and t in core_tags],
        key=lambda t: (-cf_counts[t], t),
    )
    unpracticed_adv = sorted(
        [t for t in all_tags if not by_tag[t] and t not in core_tags],
        key=lambda t: (-cf_counts[t], t),
    )

    practiced_total = len(solid) + len(lightly_practiced)
    total_completed_sprints = sum(len(tags_map.get(t, {}).get("completed", [])) for t in all_tags)
    sprint_stat = (
        f" · **{total_completed_sprints}** sprint{'s' if total_completed_sprints != 1 else ''} completed"
        if total_completed_sprints
        else ""
    )

    lines = [
        "# By Topic Tag",
        "",
        "[← Dashboard](../README.md) · [By Difficulty →](../ratings/README.md)",
        "",
        f"**{practiced_total} / {len(all_tags)}** practiced · **{len(lightly_practiced)}** lightly practiced · **{len(unpracticed_core)}** core blind spots{sprint_stat}",
    ]

    if unpracticed_core:
        lines.extend(
            [
                "",
                "## Core Topic Blind Spots (0 Solved)",
                "",
                f"| Tag | CF Problems <= {cap} | Current Sprint |",
                "| :--- | :---: | :--- |",
            ]
        )
        for t in unpracticed_core:
            slug = tag_to_slug(t)
            cnt = cf_counts[t] if index.available else "—"
            s_cell = format_tag_sprint_cell(t, slug, tags_map, records, by_id)
            lines.append(f"| [{t}](./{slug}/) | {cnt} | {s_cell} |")

    if lightly_practiced:
        lines.extend(
            [
                "",
                "## Lightly Practiced Topics (1–2 Solved)",
                "",
                "| Tag | Solved | Highest Rating | Current Sprint |",
                "| :--- | :---: | :---: | :--- |",
            ]
        )
        for t in lightly_practiced:
            slug = tag_to_slug(t)
            r_vals = [r["rating"] for r in by_tag[t] if r["rating"] is not None]
            max_r = str(max(r_vals)) if r_vals else "unrated"
            s_cell = format_tag_sprint_cell(t, slug, tags_map, records, by_id)
            lines.append(f"| [{t}](./{slug}/) | {len(by_tag[t])} | {max_r} | {s_cell} |")

    if solid:
        lines.extend(
            [
                "",
                "## Practiced Topics (3+ Solved)",
                "",
                "| Tag | Solved | Rating Range | Current Sprint |",
                "| :--- | :---: | :---: | :--- |",
            ]
        )
        for t in solid:
            slug = tag_to_slug(t)
            r_vals = [r["rating"] for r in by_tag[t] if r["rating"] is not None]
            r_span = (
                f"{min(r_vals)}–{max(r_vals)}"
                if len(set(r_vals)) > 1
                else (str(r_vals[0]) if r_vals else "unrated")
            )
            s_cell = format_tag_sprint_cell(t, slug, tags_map, records, by_id)
            lines.append(f"| [{t}](./{slug}/) | {len(by_tag[t])} | {r_span} | {s_cell} |")

    if unpracticed_adv:
        adv_links = " · ".join(f"[{t}](./{tag_to_slug(t)}/)" for t in unpracticed_adv)
        lines.extend(
            [
                "",
                "<details>",
                f"<summary>Advanced / 1600+ Topics ({len(unpracticed_adv)} unpracticed — each has a starter sprint inside)</summary>",
                "",
                adv_links,
                "",
                "</details>",
            ]
        )

    lines.append("")
    (TAGS_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def select_blind_challenges(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    *,
    extra_exclude_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Pick 5 balanced challenge problems (stretch difficulty + weak/unpracticed topics) without spoiling tags."""
    if not index.available:
        return []

    solved_ids = {r["id"] for r in records}
    comfort, stretch_low, stretch_high = compute_comfort_and_target(records)
    core_tags, _ = classify_tags(index, comfort, ALL_CF_TAGS)
    cap = max(1500, comfort + 300)
    cf_counts = index.count_tag_up_to_rating(cap)

    by_tag: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rec in records:
        for t in rec["tags"]:
            by_tag[t].append(rec)

    lightly_practiced = sorted(
        [t for t in core_tags if 1 <= len(by_tag[t]) <= 2],
        key=lambda t: (len(by_tag[t]), -cf_counts[t], t),
    )
    unpracticed_core = sorted(
        [t for t in core_tags if not by_tag[t]],
        key=lambda t: (-cf_counts[t], t),
    )

    shown_ids: set[str] = set(extra_exclude_ids or set())
    picks_out: list[dict[str, Any]] = []

    p_low = index.recommend(
        solved_ids, min_rating=stretch_low, max_rating=stretch_low, limit=1, exclude_ids=shown_ids
    )
    if p_low:
        shown_ids.add(p_low[0]["id"])
        picks_out.append(p_low[0])

    if stretch_high > stretch_low:
        p_high = index.recommend(
            solved_ids,
            min_rating=stretch_high,
            max_rating=stretch_high,
            limit=1,
            exclude_ids=shown_ids,
        )
        if p_high:
            shown_ids.add(p_high[0]["id"])
            picks_out.append(p_high[0])

    for t in unpracticed_core[:2]:
        cand = index.recommend(
            solved_ids,
            tag=t,
            min_rating=max(800, comfort - 100),
            max_rating=stretch_high,
            limit=1,
            exclude_ids=shown_ids,
        )
        if cand:
            shown_ids.add(cand[0]["id"])
            picks_out.append(cand[0])

    for t in lightly_practiced[:1]:
        r_vals = [r["rating"] for r in by_tag[t] if r["rating"] is not None]
        max_t = max(r_vals) if r_vals else comfort
        next_min = max(comfort, max_t + 100 if len(by_tag[t]) >= 2 else max_t)
        cand = index.recommend(
            solved_ids,
            tag=t,
            min_rating=next_min,
            max_rating=max(stretch_high, next_min + 100),
            limit=1,
            exclude_ids=shown_ids,
        )
        if cand:
            shown_ids.add(cand[0]["id"])
            picks_out.append(cand[0])

    # Sort purely by rating then ID so order doesn't hint which row came from which bucket
    picks_out.sort(key=lambda p: (p["rating"] or 9999, p["id"]))
    return picks_out


def write_root_readme(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    sprints_state: dict[str, Any],
) -> None:
    _, stretch_low, stretch_high = compute_comfort_and_target(records)
    extra_tags = {t for r in records for t in r["tags"]} - set(ALL_CF_TAGS)
    all_tags = sorted(set(ALL_CF_TAGS) | extra_tags)
    by_id = {r["id"].upper(): r for r in records}
    tags_map = sprints_state.get("tags", {})

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
    practiced_count = sum(1 for t in all_tags if by_tag[t])
    total_completed_sprints = sum(len(tags_map.get(t, {}).get("completed", [])) for t in all_tags)
    sprint_stat = (
        f" · **{total_completed_sprints}** sprint{'s' if total_completed_sprints != 1 else ''} done"
        if total_completed_sprints
        else ""
    )

    lines = [
        "# Codeforces Solutions",
        "",
        f"**{len(records)}** solved · **{min_r}–{max_r}** rating · target **{stretch_low}–{stretch_high}** · **{practiced_count} / {len(all_tags)}** tags{sprint_stat}",
        "",
        "## [By Difficulty](./ratings/README.md)",
        "",
        "| Rating | Solved |",
        "| :--- | :---: |",
    ]

    for r in sorted(set(ratings_only) | {stretch_high}):
        cnt = len(by_rating.get(r, []))
        r_dir = format_rating_dir(r)
        label = f"[{r}](./ratings/{r_dir}/)" if cnt > 0 else f"**{r}** *(goal)*"
        lines.append(f"| {label} | {cnt} |")

    if unrated_recs:
        lines.append(f"| [unrated](./ratings/unrated/) | {len(unrated_recs)} |")

    featured_sprint_tags = select_featured_sprint_tags(records, index, sprints_state, limit=4)
    featured_problem_ids = {
        p["id"]
        for t in featured_sprint_tags
        for p in tags_map.get(t, {}).get("active", {}).get("problems", [])
    }

    challenges = select_blind_challenges(records, index, extra_exclude_ids=featured_problem_ids)
    if challenges:
        lines.extend(
            [
                "",
                "## Suggested Challenges",
                "",
                "| Problem | Rating |",
                "| :--- | :---: |",
            ]
        )
        for p in challenges:
            p_link = f"[{p['id']} - {p['name']}]({problem_url(p['contestId'], p['index'])})"
            lines.append(f"| {p_link} | {p['rating']} |")

    if featured_sprint_tags:
        lines.extend(
            [
                "",
                "## Suggested Sprints",
                "",
                "Ordered progressions focusing on a specific subtopic or algorithm. Submitting solutions checks off steps automatically; finishing a sprint unlocks a new one in that tag. *(All 37 tag sprints in [All Tags](./tags/README.md).)*",
            ]
        )
        for t in featured_sprint_tags:
            slug = tag_to_slug(t)
            active = tags_map[t]["active"]
            done_cnt, total_cnt, _ = sprint_progress(active, records, by_id)
            s_num = active.get("sprint", len(tags_map[t].get("completed", [])) + 1)
            heading = f"### [{t}](./tags/{slug}/) — {active['title']} *(Sprint {s_num} · {done_cnt}/{total_cnt})*"
            lines.append("")
            lines.extend(
                format_sprint_markdown(
                    active,
                    records,
                    by_id,
                    heading=heading,
                    ratings_rel_prefix="./ratings",
                )
            )

    ordered_tags = sorted(all_tags, key=lambda t: (-len(by_tag[t]), t))
    lines.extend(
        [
            "",
            "## [All Tags](./tags/README.md)",
            "",
            "| Tag | Solved |",
            "| :--- | :---: |",
        ]
    )
    for t in ordered_tags:
        slug = tag_to_slug(t)
        lines.append(f"| [{t}](./tags/{slug}/) | {len(by_tag[t])} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "Add new solutions to the repo root and run `python3 organize.py` (or push to `main`). Run `python3 organize.py --challenge` for spoiler-free picks or `python3 organize.py --sprint` for active topic sprints.",
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

    if filter_rating:
        picks = index.recommend(solved_ids, min_rating=filter_rating, max_rating=filter_rating, limit=6)
    else:
        picks = select_blind_challenges(records, index)

    print("Suggested Challenges (spoiler-free):")
    for p in picks:
        print(f"  [{p['rating']}] {p['id']:6s} {p['name']} -> {problem_url(p['contestId'], p['index'])}")


def print_sprint_cli(
    records: list[dict[str, Any]],
    index: ProblemIndex,
    filter_tag: str | None,
) -> None:
    sprints_state = sync_sprints(records, index, persist=False)
    tags_map = sprints_state.get("tags", {})
    by_id = {r["id"].upper(): r for r in records}

    if filter_tag:
        norm_tag = filter_tag.strip().lower().replace("-", " ")
        if norm_tag not in tags_map or not tags_map[norm_tag].get("active"):
            # Fallback match by slug
            for candidate in tags_map:
                if tag_to_slug(candidate) == tag_to_slug(filter_tag):
                    norm_tag = candidate
                    break
        t_info = tags_map.get(norm_tag)
        if not t_info or not t_info.get("active"):
            print(f"[error] No active sprint found for tag '{filter_tag}'.")
            return
        targets = [norm_tag]
    else:
        targets = select_featured_sprint_tags(records, index, sprints_state, limit=4)

    for idx_t, t in enumerate(targets):
        if idx_t > 0:
            print()
        active = tags_map[t]["active"]
        done, total, matches = sprint_progress(active, records, by_id)
        s_num = active.get("sprint", len(tags_map[t].get("completed", [])) + 1)
        print(f"[{t}] Sprint {s_num}: {active['title']} ({done}/{total})")
        print(f"  {active['description']}")
        for step_i, (prob, sol) in enumerate(zip(active["problems"], matches), start=1):
            mark = "x" if sol is not None else " "
            sol_note = f" (solved: {sol['file']})" if sol is not None else ""
            print(
                f"  {step_i}. [{mark}] [{prob['rating']}] {prob['id']:6s} {prob['name']} -> "
                f"{problem_url(prob['contestId'], prob['index'])}{sol_note}"
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
    parser.add_argument(
        "--sprint",
        action="store_true",
        help="Print active progressive topic sprints and exit.",
    )
    parser.add_argument("--tag", type=str, default=None, help="Filter `--challenge` or `--sprint` by topic tag.")
    parser.add_argument("--rating", type=int, default=None, help="Filter `--challenge` by difficulty rating.")
    args = parser.parse_args()

    raw_cf = load_cf_dataset(force_refresh=args.refresh)
    index = ProblemIndex(raw_cf)
    manifest = load_manifest()

    if args.sprint:
        print_sprint_cli(list(manifest.values()), index, args.tag)
        return 0

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
    sprints_state = sync_sprints(records, index, persist=True)
    rebuild_tags_directory(records, index, sprints_state)
    write_ratings_readme(records)
    write_tags_readme(records, index, sprints_state)
    write_root_readme(records, index, sprints_state)

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
