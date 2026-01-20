# Algorithmic Trade Optimization for Keeper Fantasy Baseball

The keeper league trade problem maps directly to **kidney exchange mechanisms**—one of economics' most successful real-world applications of market design theory. Your hypothesis is correct: keeper leagues are inefficient markets primarily because owners fail to detect constraint-driven surplus until deadline pressure forces suboptimal decisions. An AI system that scans all 12 rosters, identifies dying assets, and proposes Pareto-improving trades would have significant edge—not from better player evaluation, but from **superior trade opportunity detection**.

The formal model is an **exchange economy with constrained housing markets**. The Top Trading Cycles (TTC) algorithm, developed by David Gale and formalized by Shapley and Scarf in 1974, provides the mathematical foundation. For multi-party trades, Johnson's cycle enumeration algorithm finds all beneficial trading cycles in O((n+e)(c+1)) time. Combined with position-adjusted surplus value calculations and behavioral exploitation tactics, these algorithms create a complete framework for systematic trade optimization.

---

## The kidney exchange model solves exactly your problem

Kidney paired donation programs face an identical structure to your keeper league. In kidney exchange, patient-donor pairs where the donor cannot give to their own patient seek compatible swaps. The constraint that **each donor can only give one kidney** mirrors your keeper rule that **each team can only keep 2 batters and 2 pitchers**. Both create "dying assets"—resources that lose all value if not exchanged before a deadline.

The Top Trading Cycles algorithm guarantees four essential properties for your system. First, **Pareto efficiency**: no reallocation can make anyone better off without making someone worse off. Second, **core stability**: no coalition can improve by trading among themselves outside the mechanism. Third, **strategy-proofness**: truthful preference reporting is the dominant strategy. Fourth, **individual rationality**: no team ends up worse than their starting position.

The algorithm works by building a directed graph where each team points to their most-preferred available player. Because the graph has finite nodes with outdegree 1, at least one cycle must exist. Cycles represent mutually beneficial trades: in a 3-way cycle A→B→C→A, each team gives to the next and receives from the previous. Executing all trades in a cycle simultaneously ensures no party can renege.

Real kidney exchange networks have achieved remarkable scale. The National Kidney Registry completed a **60-participant chain in 2012** and a 70-participant chain in 2014. Chains of 3+ segments accounted for 68% of successful chain transplants. Your 12-team league is considerably smaller, making exhaustive algorithmic search computationally trivial—all possible trade combinations can be evaluated in under one second.

---

## Surplus detection requires position-specific replacement levels

The core input to any trade optimization system is accurate surplus detection. A player constitutes a "dying asset" when they would provide keeper value but **cannot be kept due to slot constraints**. Detection requires calculating each player's value above replacement within their position category, then comparing against keeper slot capacity.

**Value Above Replacement (VAR)** should be calculated using position-specific baselines. Determine replacement level at each position based on roster construction—for a 12-team league keeping 2 batters each, the replacement batter is approximately the 25th-best available. A player's surplus value equals their projected production minus this replacement threshold. This methodology automatically adjusts for positional scarcity; elite shortstops receive appropriate premium because replacement-level shortstops produce less than replacement-level first basemen.

For cross-position normalization between batters and pitchers, convert both to a common unit using **z-scores or Standings Gain Points (SGP)**. The traditional allocation assigns **65-70% of value to batters and 30-35% to pitchers**. In auction terms, a $260 budget allocates approximately $160-182 to hitters and $78-100 to pitchers. Once normalized, a 2.0 z-score pitcher equals a 2.0 z-score batter in trade value.

Keeper year value requires discounting future production and applying age curves. Research on age-adjusted performance shows hitters peak at **age 26-27 with gradual decline beginning around 28-30**, while pitchers peak around 26-28. For valuation purposes, apply approximately **20% discount for Year 2, 35% for Year 3, and 50% for Year 4+**. A 24-year-old breakout is worth substantially more than a 32-year-old veteran with identical current production because the young player provides more keeper years at higher expected performance.

---

## Multi-party trades unlock value impossible in bilateral exchanges

Three-way and four-way trade cycles often create value that cannot be captured through any sequence of two-party trades. Consider: Team A has surplus batters and needs pitchers, Team B has surplus pitchers and needs catchers, Team C has surplus catchers and needs batters. No two-team trade works, but a triangular A→B→C→A swap makes everyone better off.

Johnson's Algorithm finds all elementary circuits in a directed preference graph with time complexity O((n+e)(c+1)), where n is vertices (teams), e is edges (trade preferences), and c is total cycles found. For 12 teams, this runs instantaneously. The algorithm uses depth-first search with a blocking mechanism to avoid counting duplicates.

The practical implementation involves three steps. First, build a preference graph where an edge from Team A to Team B exists if A wants a surplus player from B. Second, enumerate all simple cycles up to your maximum acceptable trade complexity (typically 3-4 parties). Third, evaluate each cycle for mutual benefit—a cycle is viable only if every participant strictly improves.

Coordination costs increase with cycle length. In kidney exchange, cycles are typically limited to 2-way or 3-way because all surgeries must occur simultaneously to prevent reneging. Fantasy leagues face analogous trust concerns, though the commissioner can process all cycle trades atomically. **Start with 2-way and 3-way cycles** for practical implementation, expanding to 4-way only when shorter cycles leave significant value on the table.

---

## Behavioral exploitation provides negotiation edge

Owners systematically overvalue their own players due to three documented psychological biases. The **endowment effect** causes people to value owned items 2-3× higher than identical unowned items—in classic experiments, sellers demanded approximately $7 for mugs that buyers would only pay $3 to acquire. **Loss aversion** makes losses feel twice as painful as equivalent gains, creating resistance to trades framed as giving something up. **Status quo bias** produces inertia favoring current allocations even when change is objectively beneficial.

Frame all trade proposals to emphasize gains rather than losses. Instead of "You're giving up Player A who could still bounce back," say "You're acquiring Player B who's projected for 25 home runs." Instead of highlighting what they surrender, focus exclusively on what they obtain. Connect acquired players to their specific team needs and stated goals.

The research on first-mover advantage strongly favors making the opening offer. First offers explain **50-85% of variance in final negotiation outcomes** due to anchoring effects. Precise anchors signal competence—$349,999 is more effective than $350,000. When you know more about relative player value than your trading partner, anchor aggressively with your proposed terms.

Deadline pressure increases concessions and cooperation. Counterintuitively, negotiators predict deadlines will hurt them, but research shows moderate deadlines often improve outcomes by creating shared urgency. Target owners with dying assets **2-3 days before the keeper deadline**—urgency peaks but panic hasn't yet set in. Frame the deadline as external constraint: "League rules force this timeline, not me."

---

## Implementation requires integrated valuation and graph algorithms

A complete trade optimization system requires three integrated components. The **surplus detection module** takes all 12 rosters with player values and outputs which teams have dying assets at which positions. The **trade pair finder** takes the surplus/deficit mapping and enumerates all Pareto-improving 2-party trades. The **cycle finder** identifies multi-party trade cycles that improve all participants.

For the valuation engine, use a unified formula combining current production, keeper year multipliers, and age adjustments:

**Keeper Value = Current_Year_VAR × 1.0 + Next_Year_VAR × 0.80 × Age_Factor + Year3_VAR × 0.65 × Age_Factor**

Age factors range from 1.05 for age 24 players to 0.82 for age 34+. Position scarcity automatically enters through position-specific replacement levels.

For trade scoring, weight multiple criteria: **total value created (35%), fairness between parties (25%), urgency of dying assets (15%), trade simplicity (15%), and position fit (10%)**. Fairness is measured as min(benefit)/max(benefit)—a ratio approaching 1.0 indicates balanced mutual gain. Simpler trades with fewer parties receive preference when value creation is equivalent.

Handle incomplete information through conservative estimation. Assume opponents value players at public projection baselines, adjusted upward 20% for positions of need and downward 20% for positions of surplus. When range-based analysis shows even pessimistic scenarios benefit all parties, trades are robustly Pareto-improving and likely to be accepted.

---

## Conclusion: Market design theory validates your approach

Your central hypothesis withstands scrutiny: keeper leagues are inefficient markets exploitable through systematic trade opportunity detection. The inefficiency stems not from poor player evaluation but from **failure to recognize constraint-driven surplus, emotional attachment preventing rational trading, lack of multi-party trade consideration, and inadequate analysis of opponents' situations**.

The kidney exchange literature proves these problems are solvable at scale. Alvin Roth's Nobel Prize-winning work on market design demonstrates that properly structured matching mechanisms create "thick markets" where beneficial exchanges are identified and executed. Your 12-team league is computationally trivial compared to national kidney registries, making exhaustive trade enumeration feasible.

The key insight for implementation: **separate valuation from opportunity detection**. Most fantasy analysis focuses on determining which players are good. Your competitive advantage comes from determining which trades are mutually beneficial—a fundamentally different question requiring graph algorithms, constraint satisfaction, and behavioral tactics rather than projection systems. A team with mediocre player evaluation but superior trade detection will systematically extract value from teams with excellent evaluation but poor trade execution.

Build the system in phases. Start with surplus detection using position-adjusted VAR. Add bilateral trade enumeration using Pareto improvement criteria. Incorporate cycle detection for multi-party trades. Finally, layer behavioral framing tactics for negotiation execution. Each component provides incremental edge; the complete system creates compounding advantage through every preseason trade window.