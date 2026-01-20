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

### 3. Competitive Edges for H2H Fantasy Baseball
**File:** `Competitive Edges for Head-to-Head Fantasy Baseball.md`

**NEW** - Game theory and opponent modeling research:

| Edge | Impact |
|------|--------|
| **Colonel Blotto** | Category concentration when you're the "weaker" player |
| **Secretary Problem** | Optimal streaming thresholds (10-15% outcome improvement) |
| **ICM Variance** | Minimize variance ahead, maximize when behind (3-8% playoff improvement) |
| **FAAB Bid Shading** | Bid 20-40% below valuation (15-25% FAAB efficiency) |
| **Behavioral Exploitation** | Target tilted managers after bad weeks |
| **Level-K Thinking** | Most managers are L1-L2 sophistication |
| **Time Zone Edge** | PT has 3-hour advantage over ET for midnight adds |

---

### 4. Streaming Pitcher Optimization
**File:** `Streaming Pitcher Optimization.md`

**NEW** - Resource-constrained scheduling research:

| Finding | Impact |
|---------|--------|
| **Problem is trivially small** | Exact solution in <10ms, no heuristics needed |
| **Min-Cost Max-Flow** | Polynomial-time elegant formulation |
| **OR-Tools CP-SAT** | Free solver, <1ms solve time |
| **Snipe risk model** | P(available) = exp(-lambda * t) survival process |
| **Two-stage stochastic** | Primary plan + backup recourse |
| **Rolling horizon** | Re-solve daily with fixed commits |

---

### 5. Quantitative Methods for Sequential Resource Allocation
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

### 6. Park Factor Analysis - Coors Myth Debunked
**File:** `Park Factor Analysis - Coors Myth Debunked.md`

**CRITICAL FINDING:** Conventional wisdom about Coors is WRONG!

| Park | HR Factor | Reality |
|------|-----------|---------|
| **Dodger Stadium** | **127** | **THE WORST - Avoid!** |
| Great American | 123 | Avoid |
| Yankee Stadium | 119 | Avoid |
| **Coors Field** | **106** | **Only 6% above average - OK to stream!** |
| PNC Park | 76 | Safest |

**Data Source:** [Baseball Savant Statcast Park Factors](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors) - Update monthly during season

**Why Coors isn't dangerous:**
- Humidor (since 2002) cut HR factor by 50%
- Deepest outfield in MLB (415ft to center)
- Contrarian edge: lower snipe risk because everyone avoids

---

### 7. META SYNTHESIS - What Actually Matters
**File:** `META SYNTHESIS - What Actually Matters.md`

Reconciliation of ALL research findings ranked by validated impact:

| Tier | Contents |
|------|----------|
| **TIER 1** | K-BB%, Stuff+, GB%, Team K%, TTC algorithm - build into system |
| **TIER 2** | Weather HRFI, catcher framing, umpires - use as tiebreakers |
| **TIER 3** | Coors (debunked!), Secretary Problem (wrong model), hot streaks (myth) |
| **TIER 4** | Humidity, day/night splits - skip (complexity not worth it) |

---

### 8. Algorithmic Trade Optimization
**File:** `Algorithmic Trade Optimization for Keeper Fantasy Baseball.md`

Keeper league trade optimization using kidney exchange theory:

| Concept | Application |
|---------|-------------|
| **Top Trading Cycles (TTC)** | Pareto-efficient multi-party trades |
| **Surplus Detection** | Position-adjusted VAR for "dying assets" |
| **Behavioral Tactics** | Endowment effect (2-3x overvaluation), anchoring |

---

### 9. Data Sources Reference
**File:** `Data Sources Reference.md`

**CENTRAL HUB** for all external data with URLs, current values, and update schedules:

| Data Type | Source | Update Frequency |
|-----------|--------|------------------|
| Park Factors | [Baseball Savant](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors) | Monthly |
| Weather/HRFI | [Home Run Forecast](http://homerunforecast.com) | Game-day |
| Umpire Zones | [Ump Scorecards](https://umpscorecards.com) | Pre-game |
| Catcher Framing | [Baseball Savant](https://baseballsavant.mlb.com/catcher_framing) | Weekly |
| Team K%/ISO | [FanGraphs](https://www.fangraphs.com/leaders) | Weekly |
| Probable Pitchers | [FanGraphs Grid](https://www.fangraphs.com/roster-resource/probables-grid) | Daily |

Includes current reference values for early-season use before current-year data stabilizes.

---

## Implementation Files

The research has been implemented into working Python modules:

### Core Quant Engine

| File | Lines | Contents |
|------|-------|----------|
| `quant_engine.py` | ~1000 | **Full implementation** of BudgetedLinUCB, Bayesian updates, Ledoit-Wolf shrinkage, risk-adaptive utility, declining thresholds, urgency scoring, newsvendor reserve |
| `quant_plugin.py` | ~600 | Integration layer connecting quant engine to fantasy_bot.py |
| `risk_analysis.py` | ~500 | Floor/ceiling projections, disaster probability (Poisson), risk tiers, simple baseline tracker |
| `matchup_analyzer.py` | ~900 | Glicko-2 ratings, Secretary Problem thresholds, ICM variance, opponent modeling, win probability, next-week lookahead |
| `slot_scheduler.py` | ~900 | Exact solver (OR-Tools/brute force), snipe risk survival process, contingency trees, rolling horizon re-optimization |
| `matchup_evaluator.py` | ~850 | Pitcher/opponent/park scoring using Tier 1 validated metrics, StreamingRanker, Coors myth validation |
| `trade_analyzer.py` | ~1200 | **NEW** - Keeper trade optimization: TTC algorithm, surplus detection, multi-party cycles, negotiation framing |

Run the quant engine demos:
```bash
python quant_engine.py       # Full algorithm demo
python quant_plugin.py       # Integration demo with risk analysis
python risk_analysis.py      # Risk module standalone demo
python matchup_analyzer.py   # Matchup analysis + opponent modeling demo
python slot_scheduler.py     # Slot optimization + snipe risk demo
python matchup_evaluator.py  # Matchup evaluation + Coors validation demo
python trade_analyzer.py     # Keeper trade analysis + dying asset economics demo
```

### Research Reference Files

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

### Risk Tiers (from risk_analysis.py)

| Tier | Disaster% | Recommendation |
|------|-----------|----------------|
| **ELITE** | <5% | Strong add - safe floor |
| **SAFE** | 5-10% | Good add - solid option |
| **MODERATE** | 10-15% | Acceptable - worth considering |
| **RISKY** | 15-25% | Caution - only if high upside |
| **DANGEROUS** | >25% | Avoid - too much blowup risk |
| **NO_GO** | Hard filter | Never stream this matchup |

### Disaster Risk Factors
- **Fly ball pitcher** (FB% > 40%) = more HR
- **Elite offense** (LAD, NYY, ATL, HOU) = more HR
- **HR-friendly park** (LAD 127, NYY 119) = more HR
- **High HR/9** (> 1.3) = more HR
- **Ground ball pitcher** (GB% > 47%) = SAFER

### Best Streaming Matchups (Opponents)
1. OAK - Weak offense, high K rate
2. CHW - Weak offense, high K rate
3. PIT - Weak offense, safest HR park (76 factor)
4. MIA - Weak offense
5. WSH - Weak offense

### Worst Streaming Parks (HR Factor) - [Source: Baseball Savant](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors)
1. LAD - 127 (worst!)
2. CIN - 123
3. NYY - 119
4. PHI - 114
5. LAA - 113
6. COL - **106** (NOT as bad as myth says!)

**Note:** Coors Field (106) is safer than 5 other parks! See `Park Factor Analysis - Coors Myth Debunked.md`

### Danger Combos (NO-GO)
- Fly ball pitcher @ LAD vs Dodgers
- Fly ball pitcher @ NYY vs Yankees
- High HR/9 pitcher vs any elite offense in HR park

### Matchup State Strategy (ICM)

| State | Win Prob | Strategy | Variance Pref |
|-------|----------|----------|---------------|
| **BLOWOUT** | >95% | Prepare next week, skip risky adds | 0.3x (avoid) |
| **COMFORTABLE** | 70-95% | Protect lead, favor floor | 0.6x |
| **CLOSE** | 40-70% | Normal optimization | 1.0x |
| **TRAILING** | 20-40% | Chase counting stats, favor ceiling | 1.3x |
| **DESPERATE** | <20% | Swing for fences, max variance | 2.0x (seek) |

### Secretary Problem Thresholds

Minimum streamer percentile to accept (don't use best option too early):

```
        | Mon   Tue   Wed   Thu   Fri   Sat   Sun
--------|------------------------------------------
5 slots | 78%   75%   71%   64%   55%   38%   0%
4 slots | 82%   79%   75%   69%   60%   43%   0%
3 slots | 86%   83%   80%   75%   67%   50%   0%
2 slots | 90%   88%   86%   82%   75%   60%   0%
1 slots | 95%   94%   92%   90%   86%   75%   0%
```

**Insight:** With 4 slots on Wednesday, only stream if option is top 25% of expected options.

### Opponent Classification (Poker-Style)

| Type | Behavior | How to Exploit |
|------|----------|----------------|
| **Tight/Passive** | Set-and-forget, minimal moves | Aggressive streaming, they won't counter |
| **Tight/Active** | Few but quality moves | Respect their adds, don't overbid |
| **Loose/Passive** | Random changes, no strategy | Ignore their noise, optimize normally |
| **Loose/Active** | Heavy streaming, constant churn | May compete for adds, consider defensive bids |

### Level-K Sophistication

| Level | Behavior | % of Managers |
|-------|----------|---------------|
| **L0** | Sets lineup once, never checks | ~15% |
| **L1** | Reacts to obvious news/injuries | ~50% |
| **L2** | Anticipates your moves, may block | ~30% |
| **L3+** | Strategic counter-moves | ~5% |

**Insight:** Don't overthink - most opponents are L1-L2. Focus on your own optimization.

### Time Zone Advantage (PT User)

| Opponent TZ | Your Advantage |
|-------------|----------------|
| ET (East) | +3 hours |
| CT (Central) | +2 hours |
| MT (Mountain) | +1 hour |
| PT (Pacific) | 0 hours |

**Why it matters:** 11:59 PM PT deadline = 3 AM ET. East Coast managers are asleep.

### Snipe Risk Tiers (from slot_scheduler.py)

| Tier | Daily Snipe % | Survival to Day 3 | Action |
|------|---------------|-------------------|--------|
| **ELITE** | 30-50% | ~36% | Add ASAP - high value target |
| **HIGH** | 20-35% | ~51% | Add within 1-2 days |
| **MODERATE** | 10-20% | ~70% | Can wait, but monitor |
| **LOW** | 5-10% | ~86% | Safe to wait |
| **MINIMAL** | <5% | ~97% | Add when convenient |

**Decision rule:** Add immediately when cumulative snipe risk > 25% AND expected loss > slot cost.

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

*Last updated: January 19, 2026*

---

## Change Log

**Jan 19, 2026 (v3)**
- Added `slot_scheduler.py` - exact optimization + snipe risk
- Added "Streaming Pitcher Optimization" research document
- Added Snipe Risk Tiers quick reference

**Jan 19, 2026 (v2)**
- Added `matchup_analyzer.py` - game theory + opponent modeling
- Added "Competitive Edges" research document
- Added quick reference cards: Matchup States, Secretary Problem, Opponent Classification, Level-K, Time Zones
