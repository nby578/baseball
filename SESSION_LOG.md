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

### ~~Validated Streaming Weights~~ **SUPERSEDED - See Below**
```
OLD WEIGHTS (WRONG - from early analysis):
  60% Pitcher quality (K-BB%, GB%, Stuff+)
  20% Opponent weakness (Team K%, Team ISO)
  15% Park factor (HR factor)
   5% Weather/Umpire/Catcher

NEW WEIGHTS (VALIDATED by 415-pick backtest):
  80% Pitcher EXPERIENCE (IP sample)
  10% Pitcher quality (K-BB%)
  10% Matchup (opponent + park)
```

### ~~Top Pitcher Metrics~~ **REVISED PRIORITY**
| Rank | Metric | Why | Target |
|------|--------|-----|--------|
| **#1** | **IP Sample** | Best predictor (r=0.295) | >=120 proven, >=80 minimum |
| #2 | K-BB% | Tiebreaker only | >15% good, <10% avoid |
| #3 | Stuff+ | Marginal impact | >105 elite |
| #4 | GB% | HR suppression | >45% safe, <40% risky |

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

**Note**: All code consolidated in `baseball/` repo (FBB directory deleted Jan 2026)

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
2. ~~Historical backtest: How did our algorithm perform vs actual streaming results?~~ **ANSWERED BELOW**
3. Do high-HR teams correlate with pitchers getting pulled early (fewer IP)?

---

## OPPORTUNITY COST ANALYSIS (Jan 20, 2026) - CRITICAL FINDINGS

### The Problem: Massive Underperformance
| Metric | User Picks | Pool Average | Gap |
|--------|------------|--------------|-----|
| **Avg Points** | 8.4 | 20.7 | **-12.3** |
| **Jackpot Rate (>30 pts)** | 0.7% | 28.8% | **-28.1%** |
| **Total Picks** | 415 | - | - |
| **Missed Jackpots** | 117 | - | HUGE |
| **Total Opportunity Cost** | 5,109 pts | - | - |

### User Pick Outcome Distribution
```
Jackpots (>30):      3 ( 0.7%)   <- Should be ~120!
Great (15-30):      83 (20.0%)
Decent (5-15):     178 (42.9%)
Meh (-5 to 5):     141 (34.0%)
Bad (<-5):          10 ( 2.4%)
```

### ROOT CAUSE: Pitcher Experience (IP Sample)
| IP Sample | # Picks | % of Total | Avg Pts | Jackpots |
|-----------|---------|------------|---------|----------|
| **< 80** | 161 | 38.8% | **5.7** | 1 |
| 80-120 | 61 | 14.7% | 8.0 | 1 |
| **>= 120** | 193 | 46.5% | **10.8** | 1 |

**KEY INSIGHT: 38.8% of picks were unproven pitchers scoring only 5.7 pts avg!**

### Secondary Factors (Less Important Than Expected)
| Factor | Low Tier Avg | High Tier Avg | Impact |
|--------|--------------|---------------|--------|
| K-BB% | 8.3 pts | 8.3 pts | ~0 pts |
| Easy vs Hard Opponent | 8.1 pts | 9.2 pts | ~1 pt |

**Matchup (opponent/park) only explains ~1 pt difference!**

### Combined Filter Analysis
| Filter | # Picks | Avg Pts |
|--------|---------|---------|
| "Safe" (IP>=100, K-BB%>=12%) | 150 | **10.4** |
| "Risky" (IP<80 OR K-BB%<10%) | 212 | **6.6** |

### REVISED ALGORITHM WEIGHTS
```
OLD (WRONG):
  60% Pitcher quality
  20% Opponent weakness
  15% Park factor
   5% Weather/Umpire

NEW (CORRECTED):
  80% Pitcher EXPERIENCE (IP sample)
  10% Pitcher quality (K-BB%)
  10% Matchup (opponent + park)
```

### HARD FILTERS TO IMPLEMENT
1. **MINIMUM 80 IP sample** - Eliminates 38.8% of worst picks
2. **MINIMUM 10% K-BB%** - Eliminates worst disasters
3. **PREFER 120+ IP** when multiple options available

### Why Pool Average (20.7) Is So High
- Pool includes ACES (Alcantara, Snell, etc.) who score 30-50 pts
- Streamers (replacement level) are inherently lower ceiling
- Goal: Find streamers with ACE-like upside characteristics
- Predictive power is LIMITED (r=0.175) - luck matters!

### The Real Opportunity
| If Algorithm Had... | Impact |
|---------------------|--------|
| Filtered IP < 80 | +3.1 pts per pick |
| Preferred IP >= 120 | +2.2 pts additional |
| Perfect prediction | +12.3 pts (theoretical max) |

**Realistic target: 10-11 pts avg (up from 8.4) by fixing IP filter alone.**

---

## STREAMER POOL CORRECTION & NON-LINEAR ANALYSIS (Jan 20, 2026)

### Pool Correction (Removing Aces)
- Original pool avg: 20.7 pts (included aces you can't stream)
- **Actual streamer pool avg: ~18.4 pts** (bottom 80% of starters)
- **Revised gap: 10.0 pts** (was 12.3)

### Non-Linear Hypothesis: TESTED AND ANSWERED

**Question**: Lower pitcher vs Pirates OR Higher pitcher vs Yankees?

**Answer**: ALWAYS pick the higher IP pitcher.
```
IP 120+ vs Yankees/Dodgers: 13.8 pts
IP <80 vs Pirates/Athletics:  6.4 pts
Gap: 7.4 pts in favor of EXPERIENCE
```

### The Matchup Effect Is SMALLER Than Expected
| Pitcher Tier | Matchup Effect (Easy - Hard) |
|--------------|------------------------------|
| Very Low (<50 IP) | +0.6 pts |
| Low (50-80 IP) | +3.6 pts |
| Mid-High (120-150 IP) | -1.2 pts |
| High (150+ IP) | -1.6 pts |

**Key insight**: Matchup helps LOW pitchers more (+3.6 pts) but they still suck (7.5 pts vs 3.8 pts). HIGH pitchers don't need matchup help - they perform regardless.

### DECISION MATRIX (Final)
| Pitcher IP | vs Easy | vs Mid | vs Hard | Action |
|------------|---------|--------|---------|--------|
| **< 80** | AVOID | AVOID | AVOID | Never stream |
| **80-100** | OK | CAUTION | AVOID | Only vs easy |
| **100-120** | GOOD | OK | OK | Prefer easy |
| **120+** | GREAT | GOOD | GOOD | Always stream |

### Tie-Breaker Rules
1. **Different IP tiers?** → Pick higher IP, ignore matchup
2. **Same IP tier?** → Pick better matchup (~2-3 pts edge)
3. **Never** take unproven arm (IP<80) for matchup alone

---

## How to Use This File
1. **Check this file first** when resuming FBB work
2. Update findings as we work
3. Copy key results here before ending session

---

---

## FORMULA UPDATES IMPLEMENTED (Jan 20, 2026)

### Changes to `matchup_evaluator.py`

**1. Added IP Sample to PitcherProfile**
```python
ip_sample: float = 0.0  # Season IP - MOST IMPORTANT METRIC
```

**2. New Experience Tier System**
```python
@property
def experience_tier(self) -> str:
    if self.ip_sample >= 120: return "PROVEN"    # 10.8 pts avg
    elif self.ip_sample >= 80: return "DEVELOPING"  # 8.0 pts avg
    else: return "UNPROVEN"  # 5.7 pts avg - AVOID
```

**3. Experience-Based IP Projection (HR Mitigation)**
```python
@property
def expected_game_ip(self) -> float:
    if self.ip_sample >= 120: return 4.9  # Can absorb HR
    elif self.ip_sample >= 100: return 4.5
    elif self.ip_sample >= 80: return 4.0
    elif self.ip_sample >= 50: return 3.4
    else: return 2.8  # One bad inning = done
```

**4. Updated Weights**
```python
# OLD (WRONG):
PITCHER_WEIGHT = 0.60
OPPONENT_WEIGHT = 0.20
PARK_WEIGHT = 0.15
ENVIRONMENT_WEIGHT = 0.05

# NEW (CORRECT):
PITCHER_WEIGHT = 0.80   # Mostly EXPERIENCE
OPPONENT_WEIGHT = 0.10  # Tiebreaker only
PARK_WEIGHT = 0.05      # Marginal
ENVIRONMENT_WEIGHT = 0.05
```

**5. New Pitcher Score Formula**
```python
@property
def pitcher_score(self) -> float:
    # 80% experience, 20% quality (was 100% quality)
    return (self.experience_score * 0.80 +
            self.quality_score * 0.20)
```

**6. Hard Filters Added**
```python
def _check_no_go(self, result) -> bool:
    # HARD FILTER #1: IP < 80 = ALWAYS NO-GO
    if pitcher.ip_sample < 80:
        return True

    # HARD FILTER #2: 80-100 IP vs hard opponent
    hard_opponents = {'LAD', 'NYY', 'HOU', 'ATL', 'PHI'}
    if 80 <= pitcher.ip_sample < 100 and opponent.team in hard_opponents:
        return True
    # ... other filters
```

### Test Results
```
Proven (150 IP) vs NYY:    14.4 pts, MODERATE ✓
Unproven (50 IP) vs PIT:   NO-GO (blocked) ✓
Developing (95 IP) vs OAK: 19.9 pts, ELITE ✓
Developing (95 IP) vs NYY: NO-GO (blocked) ✓
```

---

## BACKTEST VALIDATION (Jan 20, 2026)

### Experience Tiers Confirmed
| Tier | Picks | Avg Pts | Predicted |
|------|-------|---------|-----------|
| PROVEN (120+ IP) | 193 | **10.8** | 10.8 ✓ |
| DEVELOPING (80-120) | 61 | **8.0** | 8.0 ✓ |
| UNPROVEN (<80) | 161 | **5.7** | 5.7 ✓ |

### Formula Performance
| Metric | Old Formula | New Formula |
|--------|-------------|-------------|
| Picks allowed | 415 | 247 |
| Picks blocked | 0 | **168** |
| Avg pts/pick | 8.4 | **10.2** |
| **Improvement** | - | **+1.8 pts/pick** |

### Blocked Picks Analysis
- 168 picks blocked (40% of total)
- Blocked picks averaged only **5.8 pts**
- 161 were unproven (IP < 80)
- 7 were developing vs hard opponents

### Total Value
```
If blocked picks replaced with avg quality streamers:
  GAIN: +733 total points (+21%)
```

---

*Last updated: 2026-01-20 16:00*
