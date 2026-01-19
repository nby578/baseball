# Research Index

This folder contains deep research on fantasy baseball optimization for BLJ X league.

---

## Documents

### 1. Hidden Edges in Points League Fantasy Baseball
**File:** `Hidden Edges in Points League Fantasy Baseball.md`

Actionable edges most fantasy managers miss:

| Edge | Impact |
|------|--------|
| **Catcher Framing** | +1-4 pts per start (Bailey, Raleigh, Wells = good; Quero = avoid) |
| **Weather/HRFI** | 86% more HRs in hot vs cold games. Check homerunforecast.com |
| **Reliever Fatigue** | 2 mph velocity drop on 3rd consecutive day. Never start fatigued relievers |
| **Umpire Zones** | 22% K rate variation between extreme umps. Check umpscorecards.com |
| **Platoon Splits** | Need 1000+ PA to stabilize. Use league averages, not individual splits |
| **Setup Men** | Holds = 82% of save value. Bryan Abreu > mid-tier closers |
| **Ground Ball Pitchers** | 25% fewer HRs than fly ball pitchers |

---

### 2. Optimization Frameworks Research
**File:** `Optimization Frameworks Research.md`

Conceptual frameworks from finance, OR, and ML:

| Framework | Key Insight |
|-----------|-------------|
| Portfolio Theory | Don't stream correlated players |
| Multi-Armed Bandits | Early-week adds can be speculative |
| Dynamic Programming | Future flexibility has value |
| Knapsack Problems | Two-start pitchers = best efficiency |
| Stochastic Optimization | Reserve 1-2 adds for contingencies |
| Kelly Criterion | Bet proportional to edge |
| Options Theory | Unused adds have time value that decays |

**The 8 Heuristics:**
1. Two-start pitchers = ~1.8x value
2. Save 2+ adds for Thu-Sun
3. Urgency = value / days_remaining
4. Leading? Stream floor. Trailing? Stream ceiling.
5. Reserve 1 add until Saturday
6. Monday threshold = 90th percentile, Saturday = 50th
7. Don't stream 2 pitchers vs same offense
8. Early-week = explore, late-week = exploit

---

### 3. Quantitative Methods for Sequential Resource Allocation
**File:** `Quantitative Methods for Sequential Resource Allocation Under Uncertainty.md`

**THE FORMULAS AND CODE** - This is the implementation guide.

| Method | What You Get |
|--------|--------------|
| **K-Secretary Threshold** | When to pull trigger (achieves 78% of optimal) |
| **Prophet Inequalities** | Single threshold for k=5 selections |
| **Bellman Equations** | Full MDP formulation with risk-sensitive extension |
| **Bandits with Knapsacks** | THE direct model - BudgetedLinUCB algorithm with Python code |
| **Multi-Asset Kelly** | f* = Σ⁻¹μ formula for correlated bets |
| **Ledoit-Wolf Shrinkage** | Correlation estimation from small samples |
| **Bayesian Updates** | Normal-Normal conjugate for mid-season projection updates |
| **Newsvendor Formula** | Critical fractile → reserve 1-2 adds |
| **MCTS** | Monte Carlo Tree Search for sequential decisions |

**Core Decision Rule:**
```python
# Add player if:
E[Points] > threshold + (adds_remaining / days_remaining) * sigma_opportunity
```

**Regret Bound:** ~40 points suboptimality vs omniscient selector for our problem size.

---

## Python Reference Files

These `.py` files in the root folder contain the same research in executable form:

| File | Contents |
|------|----------|
| `fantasy_myths.py` | 8 myths debunked (Coors, hot streaks, position scarcity, etc.) |
| `advanced_stats.py` | Obscure stats guide (O-Swing%, xwOBA, K-BB%, Barrel Rate, etc.) |
| `hidden_edges.py` | Weather, framers, umps, fatigue - same as the MD doc |
| `league_settings.py` | BLJ X scoring with calculator |

Run any of them to print the research:
```bash
python fantasy_myths.py
python advanced_stats.py
python hidden_edges.py
```

---

## Quick Reference Cards

### Best Streaming Matchups (Opponents)
1. OAK - Weak offense, high K rate
2. CHW - Weak offense, high K rate
3. PIT - Weak offense, safest HR park (76 factor)
4. MIA - Weak offense
5. WSH - Weak offense

### Worst Streaming Parks (HR Factor)
1. LAD - 127 (worst!)
2. NYY - 119
3. MIA - 118
4. PHI - 114
5. LAA - 113

### Catcher Framing Tiers
**Elite:** Patrick Bailey (SF), Cal Raleigh (SEA), Austin Wells (NYY)
**Good:** Jose Trevino (CIN), Alejandro Kirk (TOR)
**Avoid:** Edgar Quero (CHW), Riley Adams (WSH)

### Setup Men Targets (Holds League)
- Bryan Abreu (HOU) - 105 K
- Jeremiah Estrada (SD) - 108 K
- Griffin Jax (TB) - versatile
- Garrett Whitlock (BOS) - steady

---

## External Resources

| Resource | URL | Use For |
|----------|-----|---------|
| Home Run Forecast | homerunforecast.com | HRFI weather index (check daily) |
| Ump Scorecards | umpscorecards.com | Umpire assignments (1-3 hrs pre-game) |
| Baseball Savant | baseballsavant.mlb.com | Statcast data (barrel%, GB%, etc.) |
| FanGraphs | fangraphs.com | Projections, K-BB%, Stuff+ |

---

*Last updated: January 2026*
