# Optimization Frameworks for Fantasy Baseball Streaming

Research on Wall Street algorithms, investing theory, and scientific literature that applies to weekly streaming optimization.

## The Core Problem

- 5 "adds" (trades) per week to maximize total value
- Each add has opportunity cost (using one today = one less for weekend)
- Sequential decision making under uncertainty
- Must consider constraints (roster spots, timing, who can be dropped)
- Two-start pitchers = one add for two games (leverage)
- Need to reserve resources for contingencies (IL returns)
- Information updates daily (availability, matchups, weather)
- Decisions lock at specific times (can't change after midnight)

---

## 1. Portfolio Optimization & Modern Portfolio Theory

### Core Concept
Markowitz mean-variance optimization finds the portfolio allocation that maximizes expected return for a given level of risk. The key insight: **correlation between assets matters** - you can reduce portfolio volatility by combining uncorrelated assets.

### Mapping to Fantasy Baseball
- **Assets** = Available players to stream
- **Returns** = Expected fantasy points
- **Risk** = Variance in player performance
- **Correlation** = Players facing same pitchers, same weather systems

Don't just pick the 5 highest-projected players. Pick players whose performances are **uncorrelated** so a bad day from one doesn't sink your week.

### Transaction Cost Modeling
Your "cost" isn't monetary; it's opportunity cost. Key insight from Almgren-Chriss optimal execution: **front-load safer bets and back-load higher-variance plays.** If safe plays hit, you can afford to take risks. If they miss, you need the variance to catch up.

### Key Resource
- DeMiguel et al. (2009) "Optimal Versus Naive Diversification" - shows simple 1/N allocation often beats complex optimization

---

## 2. Multi-Armed Bandit Problems

### Core Concept
You have K slot machines (arms), each with unknown payout distributions. The **exploration-exploitation tradeoff**: do you pull the arm you think is best, or try others to learn more?

### Mapping to Fantasy Baseball
- **Arms** = Streaming options each day
- **Pulls** = Using an add
- **Exploration** = Picking up an unproven player
- **Exploitation** = Going with the known quantity

### Thompson Sampling Approach
Maintain a probability distribution for each player, not just point estimates. Sample from distributions to decide - this naturally balances exploration/exploitation.

### Contextual Bandits (Most Relevant)
Player value depends on context (opponent, park, weather). LinUCB algorithm learns:
```
value = θ · context_features
context_features = [opponent_wOBA, park_factor, rest_days, ...]
```

### Key Insight
**Your adds early in the week should be higher variance than late-week adds.** Early adds give you information to make better late decisions. If you're winning by Thursday, exploit. If you're losing, explore.

### Key Resource
- Lattimore & Szepesvári "Bandit Algorithms" (free online)

---

## 3. Dynamic Programming & Bellman Equations

### Core Concept
Break a sequential decision problem into stages. Work **backwards** from the end to determine optimal policy:
```
V(state, time) = max_action [ reward(state, action) + E[V(next_state, time+1)] ]
```

### Mapping to Fantasy Baseball
- **State** = (adds_remaining, current_roster, day_of_week, score_vs_opponent)
- **Action** = (which player to add, which to drop, or hold)
- **Reward** = Expected points from today's games

### The "Option Value" of Waiting
Key DP insight: **an unused add has option value.** Using it now means you can't use it if something better appears.

On Monday, if your best available add projects for 8 points, but historically Thursday/Friday adds average 10 points (better matchups, more info), **wait**.

### Optimal Stopping (Secretary Problem)
Calculate a **threshold** for each day. Add only if expected value exceeds threshold. Thresholds decrease as week progresses.

### Key Resource
- "Optimal Stopping and Applications" by Ferguson (free online)

---

## 4. Knapsack Problems

### Core Concept
Select items to maximize value subject to capacity constraint.

### Time-Indexed Knapsack
Players have availability windows:
- Player A: Available Mon-Wed only
- Player B: Available all week
- Player C: Only available Thu-Sun

Players with shorter windows are more "urgent" - if you want them, you must act.

### Key Insight
**Prioritize two-start pitchers.** If a one-start SP is worth `v`, a two-start SP is worth approximately `2v - correlation_discount`. Calculate **value per add** for each option.

### Key Resource
- Kellerer et al. "Knapsack Problems"

---

## 5. Stochastic Optimization

### Two-Stage Stochastic Programming
- **Stage 1 (Monday)**: Make initial adds with partial information
- **Uncertainty**: Games played out, injuries revealed, weather updates
- **Stage 2 (Mid-week)**: Recourse actions with updated info

### Scenario-Based Optimization
- Scenario 1 (30%): Your SP1 gets injured, must stream replacement
- Scenario 2 (50%): Normal week
- Scenario 3 (20%): Opponent's key player injured, you're ahead

### Robust Optimization
If you're in a playoff race, optimize **worst case** - don't stream volatile players even if EV is higher.

### Key Insight
**Reserve 1-2 adds for contingency.** The expected value of perfect information (EVPI) is high in fantasy because mid-week news dramatically changes optimal decisions.

---

## 6. Reinforcement Learning for Trading

### Q-Learning Approach
Learn Q(state, action) = expected cumulative reward from taking action in state.

Train by simulating thousands of fantasy weeks. The learned Q-function tells you: "In this exact situation, adding Player X is worth Y points in expectation."

### Key Patterns RL Can Learn
- "When leading by 20+ points on Thursday, hold remaining adds for contingencies"
- "When behind on Saturday, stream high-upside closers over safe starters"
- "Two-start pitchers facing weak teams are worth using adds early"

### Key Resource
- Sutton & Barto "Reinforcement Learning: An Introduction" (free online)

---

## 7. Kelly Criterion & Bet Sizing

### Core Concept
Optimal bet size to maximize long-term wealth growth:
```
f* = (p*b - q) / b
```
Kelly says: **bet proportionally to your edge.**

### Mapping to Fantasy Baseball
High-confidence adds (2-start ace vs weak teams) deserve priority. Speculative adds (unproven call-up) should be made only when you have "bankroll" to spare.

### Application to Matchup Context
- **Leading**: Reduce variance (safe streaming)
- **Trailing**: Increase variance (boom-or-bust plays)

### Practical Insight
Calculate your "edge" for each potential add:
```
edge = (projected_points - replacement_level) / replacement_level
```
- >30%: Strong add, prioritize
- 10-30%: Moderate, consider alternatives
- <10%: Marginal, save the add

---

## 8. Options Pricing Analogues

### Core Concept
An option gives the right (not obligation) to buy/sell an asset. Its value comes from **uncertainty**.

### Mapping to Fantasy Baseball
**Unused adds are call options:**
- **Strike price** = Replacement-level production
- **Expiration** = End of fantasy week
- **Underlying** = Best available player when you decide
- **Volatility** = Uncertainty in player availability/value

### Time Decay (Theta)
Options lose value as expiration approaches:
- Monday add "option" is worth more than Saturday add "option"
- By Sunday, unused adds are worthless

### Key Insight
Only exercise (use the add) when intrinsic value exceeds time value. Early in week, time value is high. Late in week, time value collapses.

---

## 9. Sports Analytics Literature

### DFS Optimization Findings
- Correlation matters - players from same team have correlated outcomes
- Optimal portfolios are NOT just "best projected players"
- Recent performance is overweighted in projections

### Player Projection Systems (PECOTA, ZiPS, Steamer)
- Aging curves: Players peak at ~27, decline after
- Regression to mean: Extreme performances regress
- Platoon splits: Huge value vs opposite-hand pitchers
- Park factors: Can swing projections 10-15%

### Market Efficiency
Sports betting markets are NOT efficient - biases exist. If you find systematic biases in consensus projections, exploit them.

---

## 10. Operations Research Parallels

### Vehicle Routing Problem with Time Windows
**Key insight: prioritize tight time windows.** If a player is only available Monday, prioritize that decision over players available all week.

### Priority Dispatching Rules
1. **Earliest Due Date (EDD)**: Prioritize players whose availability expires soonest
2. **Weighted Shortest Job First (WSJF)**: Prioritize by value/urgency ratio

```
priority_score(player) = projected_value / days_remaining_to_add
```

---

## Synthesized Quant Framework

### Decision Engine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  1. PROJECTION LAYER (Inputs)                               │
│     - Composite projections (PECOTA, ZiPS, Steamer)         │
│     - Uncertainty estimates (projection variance)           │
│     - Correlation matrix (players facing same pitching)     │
│     - Context features (matchup, park, weather)             │
├─────────────────────────────────────────────────────────────┤
│  2. OPTION VALUE LAYER                                      │
│     - Time value of unused adds (decreases daily)           │
│     - Information value (what we'll learn by waiting)       │
│     - Availability windows (player-specific urgency)        │
├─────────────────────────────────────────────────────────────┤
│  3. PORTFOLIO OPTIMIZATION                                  │
│     - Mean-variance optimization across adds                │
│     - Correlation-adjusted diversification                  │
│     - Position constraints as linear constraints            │
├─────────────────────────────────────────────────────────────┤
│  4. DYNAMIC STRATEGY ADJUSTMENT                             │
│     - Current standing vs opponent                          │
│     - Risk tolerance (leading = conservative, trailing =    │
│       aggressive)                                           │
│     - Bayesian update on player distributions               │
├─────────────────────────────────────────────────────────────┤
│  5. EXECUTION                                               │
│     - Priority queue: value / urgency ratio                 │
│     - Reserve buffer for contingencies (1-2 adds)           │
│     - Threshold rules for acting vs waiting                 │
└─────────────────────────────────────────────────────────────┘
```

### Daily Decision Algorithm

```python
def daily_streaming_decision(state):
    # 1. Calculate option value of waiting
    days_left = 6 - state.day_of_week
    E_future_best = estimate_future_best_add(days_left, state)
    option_value = E_future_best * (state.adds_remaining - 1) / state.adds_remaining

    # 2. Evaluate each available player
    candidates = []
    for player in state.available_players:
        proj = get_composite_projection(player)
        urgency = 1.0 / player.availability_window

        # Adjust for game situation
        if state.score_differential > 20:
            adj_value = proj.mean - 0.5 * proj.std  # Leading: prefer floor
        elif state.score_differential < -20:
            adj_value = proj.mean + 0.5 * proj.std  # Trailing: prefer ceiling
        else:
            adj_value = proj.mean  # Close: expected value

        priority = adj_value * urgency
        candidates.append((player, adj_value, priority))

    # 3. Find best candidate
    best = max(candidates, key=lambda x: x[2])

    # 4. Compare to option value of waiting
    if best[1] > option_value:
        return ("ADD", best[0])
    else:
        return ("HOLD", None)
```

---

## Practical Heuristics (Derived from Theory)

1. **Two-Start Pitcher Priority**: Value per add is ~1.8x, not 2x (correlation discount). Still prioritize.

2. **Monday/Tuesday Rule**: Save at least 2 adds for Thu-Sun. Information value is highest early week.

3. **Urgency Scoring**:
   ```
   urgency = projected_value / days_until_unavailable
   ```

4. **Risk Matching**: If ahead by >15%, stream floor plays. If behind by >15%, stream ceiling plays.

5. **Contingency Reserve**: Keep 1 add in reserve until Saturday for IL activations / emergencies.

6. **Threshold Declining**: Monday threshold = 90th percentile projection. By Saturday, threshold = 50th percentile.

7. **Correlation Avoidance**: Don't stream two pitchers facing the same offense. If one blows up, both likely do.

8. **Hot Hand Discount**: "Hot" players are +10-15% to projections, but projections already capture some. Add ~5% max.

---

## Summary Table

| Framework | Key Insight for Fantasy | Practical Takeaway |
|-----------|------------------------|-------------------|
| Portfolio Theory | Correlation reduces diversification benefit | Don't stream correlated players |
| Multi-Armed Bandit | Exploration has value | Early-week adds can be speculative |
| Dynamic Programming | Future flexibility has value | Don't use all adds Monday |
| Knapsack | Efficiency = value / cost | Prioritize two-start pitchers |
| Stochastic Optimization | Reserve for uncertainty | Keep 1-2 adds for contingencies |
| Reinforcement Learning | Patterns can be learned | Position-dependent risk tolerance |
| Kelly Criterion | Bet proportional to edge | Large edge = commit early |
| Options Theory | Time value decays | Thresholds should decrease daily |
| Sports Analytics | Projections are noisy | Use composite, not single source |
| Operations Research | Urgency-weighted scheduling | Tight windows get priority |

---

## Key Insight

**Unused adds have option value, and that value decays as the week progresses.**

This transforms fantasy baseball from "gut feel + projections" into a systematic optimization problem with quantified tradeoffs.
