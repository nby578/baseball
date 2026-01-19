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
| `weekly_optimizer.py` | Maximizes value of 5 weekly adds |
| `points_projector.py` | Expected points calculator using BLJ X scoring |
| `weekly_schedule.py` | MLB schedule scanner, 2-start pitcher detection |
| `roster_manager.py` | Roster tracking, exclusion lists, drop tiers |
| `transaction_manager.py` | Drop analysis, IL monitoring, lock timing |
| `streaming.py` | Park factors, matchup quality scoring |

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
| Leading? Stream floor. Trailing? Stream ceiling. | Kelly Criterion |
| Reserve 1-2 adds for contingencies | Newsvendor Formula |
| Monday threshold = 90th percentile, Saturday = 50th | Options Theory |

### The Core Algorithm

```python
# Bandits with Knapsacks - the exact framework for our problem
# Add player if:
E[Points] > threshold + (adds_remaining / days_remaining) * sigma_opportunity
```

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

- [x] Research: myths, advanced stats, hidden edges
- [x] Research: optimization frameworks (finance, OR, ML)
- [x] Research: quantitative methods with formulas
- [x] Core system: weekly optimizer, projector, scheduler
- [ ] Implement BudgetedLinUCB algorithm
- [ ] Bayesian projection updates mid-season
- [ ] Weather API integration (HRFI)
- [ ] Umpire assignment integration
- [ ] Yahoo API roster sync
- [ ] Discord notifications
- [ ] GitHub Actions scheduled runs

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

---

*Built with Claude Code*
