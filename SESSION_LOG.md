# FBB Session Log

This file tracks analysis work and findings so they survive conversation compaction.

---

## RECOVERED FROM SESSION 6f8e8357-4f50-4176-9163-8fa7264452b7 (Jan 19-20)

### BLJ X League Scoring (Critical)
```
Pitchers:
- IP: +5
- K: +2
- BB: -3
- HBP: -3
- HR allowed: **-13** (devastating!)
- SV: +11, HLD: +9

Key insight: One HR allowed erases 2.5 innings of work!
```

### HR Park Factors (VALIDATED - Not What You'd Expect!)
| Park | HR Factor | Conventional Wisdom | Reality |
|------|-----------|---------------------|---------|
| **Dodger Stadium** | **127** | "Pitcher friendly" | WORST PARK! |
| Yankee Stadium | 119 | "Short porch" | Bad (known) |
| Coors Field | **106** | "NEVER stream" | Actually AVERAGE! |
| Great American (CIN) | 114 | Overlooked | Bad |
| Oracle Park (SF) | 82 | Pitcher park | Safe ✓ |

**Coors Myth Debunked:**
- Humidor installed 2002 cut HR by 50%
- Large outfield (116,729 sq ft) → balls that would be HR become doubles/triples
- Doubles/triples = 0 pts lost in your scoring
- **Contrarian edge**: Lower snipe risk because everyone avoids Coors

### Validated Streaming Weights
```
Matchup Expected Points =
  60% Pitcher quality (K-BB%, GB%, Stuff+)
  20% Opponent weakness (Team K%, Team ISO)
  15% Park factor (HR factor)
   5% Weather/Umpire/Catcher
```

### Top Pitcher Metrics (Tier 1 - High Confidence)
| Metric | Why | Target |
|--------|-----|--------|
| **K-BB%** | Best ERA predictor (R²=0.224) | >15% good, <10% avoid |
| **Stuff+** | Stabilizes in 80 pitches | >105 elite |
| **GB%** | HR suppression | >45% safe, <40% risky |

### Top Opponent Metrics (Ranked for YOUR scoring)
| Rank | Metric | Impact |
|------|--------|--------|
| 1 | **Team K%** | +2 extra K vs high-K team = +4 pts |
| 2 | **Team ISO** | Critical due to -13 HR penalty |
| 3 | **Team wOBA** | Overall offensive quality |
| 4 | **Platoon splits** | LHP vs LHB = 28-pt wOBA disadvantage |

### Best/Worst Teams to Stream Against
**Best (high K%, low ISO):**
- OAK (91.6 score) - 27% K rate, .115 ISO
- CHW (88.8 score) - 26% K rate
- WSH, PIT, MIA

**Worst (low K%, high ISO):**
- LAD (33.0 score) - 18% K rate, .205 ISO
- NYY (34.0 score)
- HOU, ATL

### Risk Tier System (From risk_analysis.py)
```
Tier        Disaster%    Action
─────────────────────────────────────
ELITE       <5%          Strong add
SAFE        5-10%        Good add
MODERATE    10-15%       Acceptable
RISKY       15-25%       Caution
DANGEROUS   >25%         Avoid
NO_GO       Hard filter  Never stream
```

**Disaster = 3+ HR allowed (Poisson model)**

### Example Matchup Analysis
| Pitcher | vs | Expected | Floor | Ceiling | Disaster% | Risk |
|---------|-------|----------|-------|---------|-----------|------|
| Crochet | OAK (2-start) | 51 | 13 | 67 | 4% | ELITE |
| Webb | OAK | 24 | -15 | 46 | 0% | ELITE |
| Crochet | NYY | 15 | -24 | 44 | **10%** | DANGEROUS |
| Streamer | LAD | 5 | -33 | 34 | **20%** | RISKY |

### Python Modules Built
**Location: `C:\Users\NoahYaffe\Documents\GitHub\baseball\`** (separate repo!)

| Module | Size | Purpose |
|--------|------|---------|
| `matchup_evaluator.py` | 40KB | Streaming matchup scoring |
| `trade_analyzer.py` | 47KB | Keeper trade optimization |
| `risk_analysis.py` | 30KB | Floor/ceiling, disaster probability |
| `quant_engine.py` | 33KB | Quantitative decision engine |
| `slot_scheduler.py` | 33KB | Add/drop timing optimization |
| `matchup_analyzer.py` | 42KB | Matchup analysis |
| `hidden_edges.py` | 14KB | Weather, catchers, umps |
| `advanced_stats.py` | 16KB | Obscure stat thresholds |
| `league_settings.py` | 7KB | BLJ X scoring config |
| `fantasy_bot.py` | 17KB | Main bot orchestration |

**Note**: `FBB/fantasy-bot/` has the basic bot, `baseball/` has advanced analysis

### Hidden Edges Found
1. **Catcher framing** - Patrick Bailey, Cal Raleigh, Austin Wells add 1-4 pts per start
2. **Weather** - 86% more HRs in hot/wind-out vs cold/wind-in (check homerunforecast.com)
3. **Reliever fatigue** - 3 consecutive days = 2 mph velocity drop
4. **Umpire zones** - Vary 22%, check umpscorecards.com 1-3 hours before games
5. **Platoon splits** - Need 1,000-2,200 PA to stabilize (most are noise)

---

## Session: 2026-01-20 (Current)

### Working On
- Analyzing HR variance: What % is pitcher vs opposing team vs park?
- Tuning streaming algorithm parameters
- Answering: Do high-HR teams cause more blowouts than pitcher performance?

### New Research (Today)

#### HR Type Distribution (FanGraphs 2006+ data)
| HR Type | Percentage |
|---------|------------|
| Solo HR | 56.9% |
| 2-Run HR | 29.1% |
| 3-Run HR | 11.3% |
| Grand Slam | 2.6% |

**Implication**: 57% of HR are solo shots. Pitcher who gives up HR but limits walks → mostly 1-run damage.

#### Blowout Correlation
- HR-heavy teams = higher variance (can explode OR go cold)
- Contact teams = more consistent, less catastrophic
- **Key**: Walk + HR = multi-run HR. Walk rate is the multiplier!

### Questions Still To Answer
1. What % of pitcher ERA variance is explained by opponent quality?
2. Historical backtest: How did our algorithm perform vs actual streaming results?
3. Do high-HR teams correlate with pitchers getting pulled early (fewer IP)?

---

## How to Use This File
1. **Check this file first** when resuming FBB work
2. Update findings as we work
3. Copy key results here before ending session

---

*Last updated: 2026-01-20 11:30*
