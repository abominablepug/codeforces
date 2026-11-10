# Codeforces Solutions

**26** solved · **800–1500** rating · target **1500–1600** · **18 / 37** tags

## [By Difficulty](./ratings/README.md)

| Rating | Solved |
| :--- | :---: |
| [800](./ratings/0800/) | 7 |
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

### [binary search](./tags/binary-search/) — Monotonic Predicate (Search on the Answer) *(Sprint 1 · 0/4)*

Reframe 'find the optimal `X`' into a yes/no threshold check `can(X)` with a single true-to-false cutoff. Start with direct `O(n)` arithmetic checks, then build greedy sweep simulations inside `can(X)` as constraints tighten.

1. [ ] **1300** · [2022B - Kar Salesman](https://codeforces.com/contest/2022/problem/B)
2. [ ] **1400** · [2132C2 - The Cunning Seller (hard version)](https://codeforces.com/contest/2132/problem/C2)
3. [ ] **1500** · [2183C - War Strategy](https://codeforces.com/contest/2183/problem/C)
4. [ ] **1600** · [2232C2 - Seating Arrangement (Hard Version)](https://codeforces.com/contest/2232/problem/C2)

### [strings](./tags/strings/) — Run-Length Blocks, Palindromes & 26-Way Scans *(Sprint 1 · 0/4)*

Compress consecutive identical letters into run-length blocks and leverage the tiny 26-letter alphabet—iterating all 26 target characters often turns a hard string problem into `O(26 · n)`.

1. [ ] **1100** · [1820B - JoJo's Incredible Adventures](https://codeforces.com/contest/1820/problem/B)
2. [ ] **1200** · [2174A - Needle in a Haystack](https://codeforces.com/contest/2174/problem/A)
3. [ ] **1300** · [1821C - Tear It Apart](https://codeforces.com/contest/1821/problem/C)
4. [ ] **1400** · [1748B - Diverse Substrings](https://codeforces.com/contest/1748/problem/B)

### [bitmasks](./tags/bitmasks/) — Bitwise Column Independence (`AND` / `OR` / `XOR`) *(Sprint 1 · 0/4)*

Since bitwise operations never carry across positions, analyze the 30 bit columns independently and lock in decisions from MSB down to LSB. Later steps mix bitwise constraints with sums where carries reappear.

1. [ ] **1200** · [1420B - Rock and Lever](https://codeforces.com/contest/1420/problem/B)
2. [ ] **1300** · [1926D - Vlad and Division](https://codeforces.com/contest/1926/problem/D)
3. [ ] **1400** · [1918C - XOR-distance](https://codeforces.com/contest/1918/problem/C)
4. [ ] **1500** · [2203C - Test Generator](https://codeforces.com/contest/2203/problem/C)

## [All Tags](./tags/README.md)

| Tag | Solved |
| :--- | :---: |
| [greedy](./tags/greedy/) | 12 |
| [implementation](./tags/implementation/) | 9 |
| [math](./tags/math/) | 9 |
| [dp](./tags/dp/) | 7 |
| [binary search](./tags/binary-search/) | 4 |
| [constructive algorithms](./tags/constructive-algorithms/) | 4 |
| [sortings](./tags/sortings/) | 4 |
| [two pointers](./tags/two-pointers/) | 4 |
| [brute force](./tags/brute-force/) | 3 |
| [data structures](./tags/data-structures/) | 2 |
| [dfs and similar](./tags/dfs-and-similar/) | 2 |
| [number theory](./tags/number-theory/) | 2 |
| [bitmasks](./tags/bitmasks/) | 1 |
| [dsu](./tags/dsu/) | 1 |
| [geometry](./tags/geometry/) | 1 |
| [graphs](./tags/graphs/) | 1 |
| [hashing](./tags/hashing/) | 1 |
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
| [graph matchings](./tags/graph-matchings/) | 0 |
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
