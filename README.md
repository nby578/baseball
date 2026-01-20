# Fantasy Baseball Optimization System

**League:** Big League Jew X (BLJ X)
**Format:** Head-to-Head Points, 12 teams, Keeper
**Key Scoring:** -13 HR allowed, +9 holds, +3 walks, -1 AB

An AI-powered system for optimizing weekly streaming decisions using quantitative methods from finance, operations research, and machine learning.

---

## Quick Start

```bash
# Run the bot
python fantasy_bot.py daily     # Morning run: generate weekly plan
python fantasy_bot.py streams   # Get streaming recommendations
python fantasy_bot.py prelock   # Pre-midnight verification
python fantasy_bot.py status    # Quick status check
```

---

## Project Structure

### Core System (Optimization Engine)

| File | Purpose |
|------|---------|
| `fantasy_bot.py` | **Main orchestrator** - ties everything together, plugin architecture |
| `quant_engine.py` | **Quantitative decision engine** - BudgetedLinUCB, Bayesian updates, thresholds |
| `quant_plugin.py` | Integration layer connecting quant engine to fantasy bot |
| `risk_analysis.py` | **Risk module** - floor/ceiling, disaster probability, hard filters |
| `matchup_analyzer.py` | **Game theory module** - opponent modeling, situational strategy, win probability |
| `slot_scheduler.py` | **Slot optimization** - exact solver for streaming selection, snipe risk, contingencies |
| `weekly_optimizer.py` | Maximizes value of 5 weekly adds |
| `points_projector.py` | Expected points calculator using BLJ X scoring |
| `weekly_schedule.py` | MLB schedule scanner, 2-start pitcher detection |
| `roster_manager.py` | Roster tracking, exclusion lists, drop tiers |
| `transaction_manager.py` | Drop analysis, IL monitoring, lock timing |
| `streaming.py` | Park factors, matchup quality scoring |

### Quantitative Methods (quant_engine.py)

| Component | Purpose |
|-----------|---------|
| `BudgetedLinUCB` | Contextual bandit with budget constraints for add allocation |
| `BayesianProjection` | Normal-Normal conjugate prior for mid-season projection updates |
| `CorrelationEstimator` | Ledoit-Wolf shrinkage for small-sample correlation |
| `RiskAdaptiveUtility` | Adjusts risk tolerance based on matchup score (leading/trailing) |
| `ThresholdCalculator` | Declining thresholds by day (options pricing analogue) |
| `UrgencyScorer` | Two-start bonus, deadline proximity scoring |
| `NewsvendorReserve` | Optimal add reserve for IL/DTD contingencies |

### Risk Analysis (risk_analysis.py)

| Component | Purpose |
|-----------|---------|
| `RiskCalculator` | Floor/ceiling projections, disaster probability via Poisson |
| `SimpleBaseline` | Heuristic baseline for comparison (weak opp + safe park + GB pitcher) |
| `RiskAwareRanker` | Combines quant + risk for final rankings |
| Risk Tiers | ELITE / SAFE / MODERATE / RISKY / DANGEROUS / NO_GO |

### Matchup Analyzer (matchup_analyzer.py)

| Component | Purpose |
|-----------|---------|
| `Glicko2Calculator` | Skill rating with confidence intervals for opponent strength |
| `SecretaryProblem` | Optimal streaming thresholds by day (don't use best option on Monday) |
| `WinProbabilityCalculator` | Normal approximation for weekly win probability |
| `MatchupStateAnalyzer` | Classify state: DESPERATE / TRAILING / CLOSE / COMFORTABLE / BLOWOUT |
| `OpponentPredictor` | Predict opponent behavior, time zone advantages, activity patterns |
| `ActionRecommender` | Situational recommendations with next-week lookahead |
| `OpponentProfile` | Full opponent model: rating, type (Tight/Loose x Active/Passive), sophistication (L0-L3) |

### Matchup Evaluator (matchup_evaluator.py)

| Component | Purpose |
|-----------|---------|
| `PitcherProfile` | Pitcher metrics: K-BB%, Stuff+, GB%, Barrel% with grade classifications |
| `OpponentProfile` | Team metrics: K%, ISO, wOBA with matchup quality scoring |
| `ParkContext` | Park HR/K factors, weather (HRFI), umpire, catcher framing |
| `MatchupEvaluator` | **Core engine** - combines all factors with validated weights (60/20/15/5) |
| `StreamingRanker` | Ranks candidates by E[Pts], floor, ceiling, or risk-adjusted |

**Key Insight:** Uses validated park factors - Coors (106) is SAFER than Dodger Stadium (127)!

### Slot Scheduler (slot_scheduler.py)

| Component | Purpose |
|-----------|---------|
| `SlotOptimizer` | **Exact solver** using OR-Tools CP-SAT (or brute force fallback) - <1ms solve time |
| `SnipeRiskCalculator` | Survival process model: P(available at t) = exp(-lambda * t) |
| `ContingencyPlanner` | Pre-compute "If X sniped, switch to Y" backup plans |
| `RollingHorizonManager` | Daily re-optimization as week progresses |
| `SlotScheduler` | Main interface combining all components |

**Key insight:** Problem is trivially small (5 adds, 7 days, ~20 candidates). Exact optimal solution in milliseconds - no heuristics needed.

### Trade Analyzer (trade_analyzer.py)

| Component | Purpose |
|-----------|---------|
| `SurplusDetector` | Identifies dying assets (3rd+ best at position) and team needs |
| `TradeFinder` | Finds Pareto-improving bilateral trades (1-for-1, 2-for-1) |
| `CycleFinder` | Multi-party trade cycles using Johnson's algorithm (A->B->C->A) |
| `TradeScorer` | Ranks trades by value, fairness, urgency, simplicity |
| `NegotiationFramer` | Behavioral tactics: anchoring, endowment counter, deadline pressure |

**Key insight:** Keeper leagues are inefficient markets. Surplus players ("dying assets") are worth $0 to current owner but full value to receiver. Find where your surplus fills someone's need!

### Research & Strategy

| File | Purpose |
|------|---------|
| `league_settings.py` | BLJ X scoring config and calculator |
| `fantasy_myths.py` | 8 myths debunked with data |
| `advanced_stats.py` | Obscure stat edges (O-Swing%, xwOBA, K-BB%, etc.) |
| `hidden_edges.py` | Weather, catcher framing, umpires, fatigue |

### Data Sources

| File | Purpose |
|------|---------|
| `mlb_api.py` | MLB Stats API integration (free, no auth) |
| `auth.py` | Yahoo OAuth authentication |
| `config.py` | Configuration settings |

### Utilities

| File | Purpose |
|------|---------|
| `notifications.py` | Discord webhook alerts |
| `roster_monitor.py` | IL/DTD status monitoring |
| `daily_check.py` | Scheduled daily checks |

---

## Research Documents

All deep research is in the `docs/` folder:

| Document | Contents |
|----------|----------|
| **[Streaming Pitcher Optimization](docs/Streaming%20Pitcher%20Optimization.md)** | **NEW** - Min-Cost Max-Flow, OR-Tools CP-SAT, snipe risk survival process, two-stage stochastic programming, rolling horizon re-optimization |
| **[Competitive Edges for H2H Fantasy Baseball](docs/Competitive%20Edges%20for%20Head-to-Head%20Fantasy%20Baseball.md)** | Colonel Blotto game theory, Secretary Problem thresholds, ICM variance adjustment, FAAB bid shading (20-40%), behavioral exploitation, Thompson Sampling, Level-K opponent modeling |
| **[Hidden Edges in Points League Fantasy Baseball](docs/Hidden%20Edges%20in%20Points%20League%20Fantasy%20Baseball.md)** | Catcher framing (+1-4 pts/start), weather/HRFI (86% HR swing), reliever fatigue (2 mph drop on 3rd day), umpire zones (22% K variation), platoon splits, setup men value |
| **[Optimization Frameworks Research](docs/Optimization%20Frameworks%20Research.md)** | Portfolio theory, multi-armed bandits, dynamic programming, Kelly criterion, options pricing analogues, DFS literature - conceptual frameworks |
| **[Quantitative Methods for Sequential Resource Allocation](docs/Quantitative%20Methods%20for%20Sequential%20Resource%20Allocation%20Under%20Uncertainty.md)** | **THE FORMULAS** - K-secretary thresholds, Bellman equations, Bandits with Knapsacks (BwK), BudgetedLinUCB algorithm, Ledoit-Wolf shrinkage, Bayesian updates, newsvendor reserve |

---

## Key Insights (TL;DR)

### Scoring Edges

| Insight | Value |
|---------|-------|
| Walks = 65% of singles | Target high-OBP, low-BA hitters |
| HR allowed = -13 pts | One HR erases 2.5 innings |
| Holds = 82% of saves | Elite setup men are undervalued |
| Ground ball pitchers | Best HR suppression |
| Coors HR factor = 106 | Dodger Stadium = 127 (worse!) |

### Optimization Rules

| Rule | Source |
|------|--------|
| Save 2+ adds for Thu-Sun | Dynamic Programming |
| Two-start pitchers = 1.8x value | Portfolio Theory |
| Urgency = value / days_remaining | Operations Research |
| Leading? Stream floor. Trailing? Stream ceiling. | Kelly Criterion / ICM |
| Reserve 1-2 adds for contingencies | Newsvendor Formula |
| Monday threshold = 90th percentile, Saturday = 50th | Secretary Problem |
| FAAB bid shading = 20-40% below valuation | Auction Theory |
| Way ahead? Prepare for next week | Game Theory |
| Opponent L1-L2: anticipate obvious moves only | Level-K Thinking |
| PT timezone = +3hr edge vs ET opponents | Platform Arbitrage |

### The Core Algorithm

```python
# Bandits with Knapsacks - the exact framework for our problem
# Add player if:
E[Points] > threshold + (adds_remaining / days_remaining) * sigma_opportunity
```

### Risk-Adjusted Streaming

The **-13 HR penalty** creates catastrophic downside risk. A 3-HR blowup can cost -40 points.

```
Tier        Disaster%    Action
─────────────────────────────────
ELITE       <5%          Strong add
SAFE        5-10%        Good add
MODERATE    10-15%       Acceptable
RISKY       15-25%       Caution
DANGEROUS   >25%         Avoid
NO_GO       Hard filter  Never stream
```

**Disaster factors:** Fly ball pitcher + elite offense (LAD/NYY) + HR park = danger

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

**Insight:** With 4 slots on Wednesday, only stream if option is top 25% of expected weekly options.

---

## BLJ X Scoring Reference

### Batters
| Stat | Points |
|------|--------|
| AB | -1 |
| H | +5.6 |
| 2B | +2.9 (bonus) |
| 3B | +5.7 (bonus) |
| HR | +9.4 (bonus) |
| BB | +3 |
| SB | +1.9 |
| CS | -2.8 |

### Pitchers
| Stat | Points |
|------|--------|
| IP | +5 |
| K | +2 |
| BB | -3 |
| HR | **-13** |
| SV | +11 |
| HLD | +9 |

---

## Setup

### Prerequisites
- Python 3.10+
- Yahoo Developer App (for roster data)

### Installation
```bash
git clone https://github.com/nby578/baseball.git
cd baseball
pip install -r requirements.txt
cp .env.example .env
# Edit .env with Yahoo credentials
python auth.py  # First-time OAuth
```

### Daily Usage
```bash
# Morning
python fantasy_bot.py daily

# Before midnight (check availability)
python fantasy_bot.py prelock

# Anytime
python fantasy_bot.py streams   # Today's best streams
python fantasy_bot.py plan      # Full week optimization
```

---

## Roadmap

### Completed
- [x] Research: myths, advanced stats, hidden edges
- [x] Research: optimization frameworks (finance, OR, ML)
- [x] Research: quantitative methods with formulas
- [x] Research: **competitive edges** - game theory, opponent modeling, behavioral exploitation
- [x] Core system: weekly optimizer, projector, scheduler
- [x] **BudgetedLinUCB algorithm** (quant_engine.py)
- [x] **Bayesian projection updates** (Normal-Normal conjugate)
- [x] **Ledoit-Wolf shrinkage** for correlation estimation
- [x] **Risk-adaptive utility** (leading vs trailing)
- [x] **Declining thresholds** (options pricing analogue)
- [x] **Risk analysis module** - floor/ceiling, disaster probability
- [x] **Simple baseline tracker** for quant vs heuristic comparison
- [x] **Matchup analyzer** - Glicko-2 ratings, Secretary Problem, ICM variance
- [x] **Opponent modeling** - activity patterns, sophistication levels, time zone edges
- [x] **Slot scheduler** - exact optimization, snipe risk, contingency planning, rolling horizon

### In Progress
- [ ] Season testing & counterfactual comparison
- [ ] Weather API integration (HRFI)
- [ ] Umpire assignment integration
- [ ] Thompson Sampling implementation (may outperform UCB)

### Future
- [ ] Yahoo API roster sync
- [ ] Discord notifications
- [ ] GitHub Actions scheduled runs
- [ ] Chrome automation for roster moves
- [ ] FAAB bid optimizer (auction theory)

---

## Resources

### Free Data Sources
- [MLB Stats API](https://statsapi.mlb.com) - Schedules, rosters, injuries
- [homerunforecast.com](http://homerunforecast.com) - HRFI weather index
- [umpscorecards.com](http://umpscorecards.com) - Umpire tendencies
- [Baseball Savant](https://baseballsavant.mlb.com) - Statcast data
- [FanGraphs](https://fangraphs.com) - Projections, advanced stats

### Key Papers
- Badanidiyuru et al. (2018) "Bandits with Knapsacks"
- Kleinberg (2005) "A Multiple-Choice Secretary Algorithm"
- Ledoit & Wolf (2004) "Shrinkage Estimator for Covariance Matrices"
- Hunter, Vielma, Zaman (2016) "Picking Winners in Daily Fantasy Sports"
- Ferguson (1989) "Who Solved the Secretary Problem?" - Statistical Science
- Glickman (2012) "Example of the Glicko-2 system" - glicko.net
- Camerer, Ho & Chong (2004) "A Cognitive Hierarchy Model" - QJE (Level-K)
- Roberson (2006) "The Colonel Blotto Game" - Economic Theory
- Russo et al. (2018) "A Tutorial on Thompson Sampling" - Foundations & Trends

---

*Built with Claude Code*
