# Codeforces Solutions

**33** solved · **800–1500** rating · target **1500–1600** · **20 / 37** tags

## [By Difficulty](./ratings/README.md)

| Rating | Solved |
| :--- | :---: |
| [800](./ratings/0800/) | 10 |
| [900](./ratings/0900/) | 2 |
| [1000](./ratings/1000/) | 1 |
| [1100](./ratings/1100/) | 5 |
| [1200](./ratings/1200/) | 7 |
| [1300](./ratings/1300/) | 4 |
| [1400](./ratings/1400/) | 1 |
| [1500](./ratings/1500/) | 2 |
| **1600** *(goal)* | 0 |
| [unrated](./ratings/unrated/) | 1 |

## Suggested Challenges

| Problem | Rating |
| :--- | :---: |
| [1676G - White-Black Balanced Subtrees](https://codeforces.com/contest/1676/problem/G) | 1300 |
| [1857D - Strong Vertices](https://codeforces.com/contest/1857/problem/D) | 1300 |
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

### [bitmasks](./tags/bitmasks/) — Bitwise Column Independence (`AND` / `OR` / `XOR`) *(Sprint 1 · 1/4)*

Since bitwise operations never carry across positions, analyze the 30 bit columns independently and lock in decisions from MSB down to LSB. Later steps mix bitwise constraints with sums where carries reappear.

1. [x] **1200** · [1420B - Rock and Lever](https://codeforces.com/contest/1420/problem/B) — [rockAndLever.cpp](./ratings/1200/rockAndLever.cpp)
2. [ ] **1300** · [1926D - Vlad and Division](https://codeforces.com/contest/1926/problem/D)
3. [ ] **1400** · [1918C - XOR-distance](https://codeforces.com/contest/1918/problem/C)
4. [ ] **1500** · [2203C - Test Generator](https://codeforces.com/contest/2203/problem/C)

### [strings](./tags/strings/) — Run-Length Blocks, Palindromes & 26-Way Scans *(Sprint 1 · 0/4)*

Compress consecutive identical letters into run-length blocks and leverage the tiny 26-letter alphabet—iterating all 26 target characters often turns a hard string problem into `O(26 · n)`.

1. [ ] **1100** · [1820B - JoJo's Incredible Adventures](https://codeforces.com/contest/1820/problem/B)
2. [ ] **1200** · [2174A - Needle in a Haystack](https://codeforces.com/contest/2174/problem/A)
3. [ ] **1300** · [1821C - Tear It Apart](https://codeforces.com/contest/1821/problem/C)
4. [ ] **1400** · [1748B - Diverse Substrings](https://codeforces.com/contest/1748/problem/B)

### [graphs](./tags/graphs/) — Connected Components, Degrees & Traversal *(Sprint 1 · 0/4)*

Inspect vertex degrees (`deg = 1` leaves, `deg = 2` chains/cycles) and component summaries first—many graph problems resolve directly from component sizes and edge counts.

1. [ ] **1200** · [129B - Students and Shoelaces](https://codeforces.com/contest/129/problem/B)
2. [ ] **1300** · [1829F - Forever Winter](https://codeforces.com/contest/1829/problem/F)
3. [ ] **1400** · [1761C - Set Construction](https://codeforces.com/contest/1761/problem/C)
4. [ ] **1500** · [2060E - Graph Composition](https://codeforces.com/contest/2060/problem/E)

## [All Tags](./tags/README.md)

| Tag | Solved |
| :--- | :---: |
| [greedy](./tags/greedy/) | 15 |
| [math](./tags/math/) | 13 |
| [implementation](./tags/implementation/) | 10 |
| [dp](./tags/dp/) | 7 |
| [constructive algorithms](./tags/constructive-algorithms/) | 5 |
| [two pointers](./tags/two-pointers/) | 5 |
| [binary search](./tags/binary-search/) | 4 |
| [sortings](./tags/sortings/) | 4 |
| [brute force](./tags/brute-force/) | 3 |
| [strings](./tags/strings/) | 3 |
| [bitmasks](./tags/bitmasks/) | 2 |
| [data structures](./tags/data-structures/) | 2 |
| [dfs and similar](./tags/dfs-and-similar/) | 2 |
| [number theory](./tags/number-theory/) | 2 |
| [combinatorics](./tags/combinatorics/) | 1 |
| [dsu](./tags/dsu/) | 1 |
| [games](./tags/games/) | 1 |
| [geometry](./tags/geometry/) | 1 |
| [graphs](./tags/graphs/) | 1 |
| [hashing](./tags/hashing/) | 1 |
| [2-sat](./tags/2-sat/) | 0 |
| [chinese remainder theorem](./tags/chinese-remainder-theorem/) | 0 |
| [communication](./tags/communication/) | 0 |
| [divide and conquer](./tags/divide-and-conquer/) | 0 |
| [expression parsing](./tags/expression-parsing/) | 0 |
| [fft](./tags/fft/) | 0 |
| [flows](./tags/flows/) | 0 |
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
