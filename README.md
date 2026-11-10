# Codeforces Solutions

**21** solved · **800–1500** rating · target **1500–1600** · **16 / 37** tags

## [By Difficulty](./ratings/README.md)

| Rating | Solved |
| :--- | :---: |
| [800](./ratings/0800/) | 2 |
| [900](./ratings/0900/) | 1 |
| [1100](./ratings/1100/) | 5 |
| [1200](./ratings/1200/) | 6 |
| [1300](./ratings/1300/) | 4 |
| [1400](./ratings/1400/) | 1 |
| [1500](./ratings/1500/) | 2 |
| **1600** *(goal)* | 0 |

## Suggested Challenges

| Problem | Rating |
| :--- | :---: |
| [1917B - Erase First or Second Letter](https://codeforces.com/contest/1917/problem/B) | 1100 |
| [1800D - Remove Two Letters](https://codeforces.com/contest/1800/problem/D) | 1200 |
| [1931E - Anna and the Valentine's Day Gift](https://codeforces.com/contest/1931/problem/E) | 1400 |
| [1915F - Greetings](https://codeforces.com/contest/1915/problem/F) | 1500 |
| [1920C - Partitioning the Array](https://codeforces.com/contest/1920/problem/C) | 1600 |

## Suggested Sprints

Ordered progressions focusing on a specific subtopic or algorithm. Submitting solutions checks off steps automatically; finishing a sprint unlocks a new one in that tag. *(All 37 tag sprints in [All Tags](./tags/README.md).)*

### [dp](./tags/dp/) — Linear States & Decision Boundaries *(Sprint 1 · 3/4)*

Define `dp[i]` around the minimal state needed at position `i` and isolate the exact boundary choice (skip, extend, or jump). Early steps use direct `O(1)` transitions; later problems require prefix extremes or refactoring states to drop an inner loop.

1. [x] **1300** · [189A - Cut Ribbon](https://codeforces.com/contest/189/problem/A) — [cutRibbon.cpp](./ratings/1300/cutRibbon.cpp)
2. [x] **1400** · [698A - Vacations](https://codeforces.com/contest/698/problem/A) — [vacations.cpp](./ratings/1400/vacations.cpp)
3. [x] **1500** · [1842C - Tenzing and Balls](https://codeforces.com/contest/1842/problem/C) — [tenzingAndBalls.cpp](./ratings/1500/tenzingAndBalls.cpp)
4. [ ] **1600** · [1875D - Jellyfish and Mex](https://codeforces.com/contest/1875/problem/D)

### [constructive algorithms](./tags/constructive-algorithms/) — Permutations, Interleaving & Parity Checks *(Sprint 1 · 0/4)*

Test canonical templates first—interleaving `[1, n, 2, n-1, …]`, cyclic shifts, or adjacent `(2i-1, 2i)` swaps—and check parity/sum invariants early for `-1` cases. Harder steps tune a custom prefix before filling the tail monotonically.

1. [ ] **1200** · [1822D - Super-Permutation](https://codeforces.com/contest/1822/problem/D)
2. [ ] **1300** · [2023A - Concatenation of Arrays](https://codeforces.com/contest/2023/problem/A)
3. [ ] **1400** · [1927E - Klever Permutation](https://codeforces.com/contest/1927/problem/E)
4. [ ] **1500** · [1809C - Sum on Subarrays](https://codeforces.com/contest/1809/problem/C)

### [strings](./tags/strings/) — Run-Length Blocks, Palindromes & 26-Way Scans *(Sprint 1 · 0/4)*

Compress consecutive identical letters into run-length blocks and leverage the tiny 26-letter alphabet—iterating all 26 target characters often turns a hard string problem into `O(26 · n)`.

1. [ ] **1100** · [1820B - JoJo's Incredible Adventures](https://codeforces.com/contest/1820/problem/B)
2. [ ] **1200** · [2174A - Needle in a Haystack](https://codeforces.com/contest/2174/problem/A)
3. [ ] **1300** · [1821C - Tear It Apart](https://codeforces.com/contest/1821/problem/C)
4. [ ] **1400** · [1748B - Diverse Substrings](https://codeforces.com/contest/1748/problem/B)

### [data structures](./tags/data-structures/) — Ordered Sets, Frequency Maps & Heaps *(Sprint 1 · 0/4)*

Maintain dynamic min/max, predecessor/successor (`set` / `multiset`), or active counts (`map` / `priority_queue`) during a single pass. Later steps pair greedy heap eviction with running prefix balances.

1. [ ] **1100** · [1800C2 - Powering the Hero (hard version)](https://codeforces.com/contest/1800/problem/C2)
2. [ ] **1200** · [1790D - Matryoshkas](https://codeforces.com/contest/1790/problem/D)
3. [ ] **1300** · [1915E - Romantic Glasses](https://codeforces.com/contest/1915/problem/E)
4. [ ] **1400** · [2014D - Robert Hood and Mrs Hood](https://codeforces.com/contest/2014/problem/D)

## [All Tags](./tags/README.md)

| Tag | Solved |
| :--- | :---: |
| [greedy](./tags/greedy/) | 11 |
| [dp](./tags/dp/) | 6 |
| [implementation](./tags/implementation/) | 6 |
| [math](./tags/math/) | 6 |
| [binary search](./tags/binary-search/) | 4 |
| [sortings](./tags/sortings/) | 4 |
| [two pointers](./tags/two-pointers/) | 4 |
| [brute force](./tags/brute-force/) | 3 |
| [constructive algorithms](./tags/constructive-algorithms/) | 3 |
| [number theory](./tags/number-theory/) | 2 |
| [bitmasks](./tags/bitmasks/) | 1 |
| [data structures](./tags/data-structures/) | 1 |
| [dfs and similar](./tags/dfs-and-similar/) | 1 |
| [dsu](./tags/dsu/) | 1 |
| [graphs](./tags/graphs/) | 1 |
| [strings](./tags/strings/) | 1 |
| [2-sat](./tags/2-sat/) | 0 |
| [chinese remainder theorem](./tags/chinese-remainder-theorem/) | 0 |
| [combinatorics](./tags/combinatorics/) | 0 |
| [communication](./tags/communication/) | 0 |
| [divide and conquer](./tags/divide-and-conquer/) | 0 |
| [expression parsing](./tags/expression-parsing/) | 0 |
| [fft](./tags/fft/) | 0 |
| [flows](./tags/flows/) | 0 |
| [games](./tags/games/) | 0 |
| [geometry](./tags/geometry/) | 0 |
| [graph matchings](./tags/graph-matchings/) | 0 |
| [hashing](./tags/hashing/) | 0 |
| [interactive](./tags/interactive/) | 0 |
| [matrices](./tags/matrices/) | 0 |
| [meet-in-the-middle](./tags/meet-in-the-middle/) | 0 |
| [probabilities](./tags/probabilities/) | 0 |
| [schedules](./tags/schedules/) | 0 |
| [shortest paths](./tags/shortest-paths/) | 0 |
| [string suffix structures](./tags/string-suffix-structures/) | 0 |
| [ternary search](./tags/ternary-search/) | 0 |
| [trees](./tags/trees/) | 0 |

---

Add new solutions to the repo root and run `python3 organize.py` (or push to `main`). Run `python3 organize.py --challenge` for spoiler-free picks or `python3 organize.py --sprint` for active topic sprints.
