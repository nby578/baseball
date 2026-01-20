# Data Sources Reference

**Purpose:** Central reference for all external data sources with URLs, current values, and update schedules.

**Last Updated:** January 2026

---

## 1. Park Factors (HR)

**Source:** [Baseball Savant Statcast Park Factors](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors)

**Update Frequency:** Monthly during season (weekly if tracking specific parks)

**Methodology:** 3-year rolling, 100 = average, controlled by batter/pitcher handedness

### Current Values (2023-2025 Rolling)

| Park | HR Factor | Streaming Verdict |
|------|-----------|-------------------|
| **Dodger Stadium** | **127** | **AVOID - WORST** |
| Great American Ball Park | 123 | AVOID |
| Yankee Stadium | 119 | AVOID |
| Citizens Bank Park | 114 | Risky |
| Angel Stadium | 113 | Risky |
| **Coors Field** | **106** | **OK (myth debunked!)** |
| Oriole Park | 105 | Moderate |
| Wrigley Field | 101 | Moderate (check wind!) |
| Truist Park | 100 | Neutral |
| T-Mobile Park | 89 | Good |
| Fenway Park | 89 | Good |
| Kauffman Stadium | 88 | Good |
| Tropicana Field | 87 | Good |
| Progressive Field | 85 | Good |
| Oracle Park | 82 | Excellent |
| **PNC Park** | **76** | **SAFEST** |

---

## 2. Weather/HRFI (Home Run Forecast Index)

**Source:** [Home Run Forecast](http://homerunforecast.com)

**Update Frequency:** Game-day (check 2-4 hours before first pitch)

**Scale:** 1-10 (1 = pitcher-friendly, 10 = hitter-friendly)

### Reference Values

| HRFI | HR/Game | Runs/Game | Streaming Action |
|------|---------|-----------|------------------|
| 1-2 | 1.40 | 7.51 | Boost projection +1-2 pts |
| 3-4 | 1.65 | 8.10 | Slight positive |
| 5-6 | 2.00 | 8.80 | Neutral |
| 7-8 | 2.35 | 9.50 | Slight negative |
| 9-10 | 2.61 | 10.04 | Reduce projection -1-2 pts |

**Key Insight:** HRFI 1-2 vs 9-10 = **86% more HR**. Only act on extremes (≤3 or ≥8).

### Special Parks (Always Check Wind)

| Park | Special Factor |
|------|----------------|
| **Wrigley Field** | Wind direction critical: out = +77% HR/FB, in = -25-40% |
| Kauffman Stadium | Wind off fountain affects carry |
| Coors Field | Despite thin air, HRFI often moderate due to humidor |

**Wind Resource:** [Winds Blowing Out](http://windsblowingout.com) - Wrigley-specific

---

## 3. Umpire Zones

**Source:** [Ump Scorecards](https://umpscorecards.com)

**Update Frequency:** Check when lineup posted (1-3 hours pre-game)

**Limitation:** Assignments often post AFTER fantasy lineups lock - use as tiebreaker only

### Reference Values (K/BB Impact)

| Zone Type | Zone Size | K Change | BB Change | Net Pts |
|-----------|-----------|----------|-----------|---------|
| Largest (Eddings, Miller) | 3.65 sq ft | +0.5-1.0 | -0.3-0.5 | **+2-3.5** |
| Average | 3.25 sq ft | 0 | 0 | 0 |
| Smallest (Davis, Márquez) | 2.85 sq ft | -0.5-1.0 | +0.3-0.5 | **-2-3.5** |

**Crew Rotation:** HP→1B→2B→3B→HP (predictable within series)

### Extreme Umpires (Top/Bottom 5)

**Large Zones (Pitcher-Friendly):**
- Doug Eddings
- Bill Miller
- Marvin Hudson
- Lance Barksdale
- Ted Barrett

**Small Zones (Hitter-Friendly):**
- Gerry Davis
- Alfonso Márquez
- Pat Hoberg
- Ángel Hernández
- CB Bucknor

---

## 4. Catcher Framing

**Source:** [Baseball Savant Catcher Framing](https://baseballsavant.mlb.com/catcher_framing)

**Update Frequency:** Weekly during season

**Metric:** Framing Runs (positive = pitcher-friendly)

### Current Tiers (Update at Season Start)

**Elite Framers (+1-4 pts per start):**
| Catcher | Team | Notes |
|---------|------|-------|
| Patrick Bailey | SF | Elite |
| Cal Raleigh | SEA | Elite |
| Austin Wells | NYY | Elite |
| Jose Trevino | CIN | Good |
| Alejandro Kirk | TOR | Good |

**Avoid Catching (-1-2 pts per start):**
| Catcher | Team | Notes |
|---------|------|-------|
| Edgar Quero | CHW | Poor framer |
| Riley Adams | WSH | Poor framer |

**Impact:** ~0.52-0.77 year-to-year correlation (stable skill)

---

## 5. Team K% (Opponent Weakness)

**Source:** [FanGraphs Team Stats](https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=8&season=2025&month=0&season1=2025&ind=0&team=0,ts&rost=0&age=0&filter=&players=0)

**Update Frequency:** Weekly during season

**Metric:** K% (higher = more exploitable)

### Current Tiers (Update at Season Start)

**Best Matchups (High K%):**
| Team | K% | Notes |
|------|-----|-------|
| OAK | ~27% | Weak offense overall |
| CHW | ~26% | Weak offense overall |
| MIA | ~25% | Rebuilding |
| WSH | ~25% | Rebuilding |
| PIT | ~24% | Young team |

**Worst Matchups (Low K%):**
| Team | K% | Notes |
|------|-----|-------|
| LAD | ~18% | Elite contact + power |
| NYY | ~19% | Power + contact |
| ATL | ~19% | Elite offense |
| HOU | ~20% | Excellent plate discipline |

**Impact:** Each 1% K% difference ≈ +0.25 K per 25 batters faced ≈ +0.5 pts

---

## 6. Team ISO (Power/HR Risk)

**Source:** [FanGraphs Team Stats](https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=8&season=2025&month=0&season1=2025&ind=0&team=0,ts&rost=0&age=0&filter=&players=0) (sort by ISO)

**Update Frequency:** Weekly during season

**Metric:** ISO (Isolated Power) = SLG - AVG

### Current Tiers (Update at Season Start)

**High-Risk (Avoid if FB pitcher):**
| Team | ISO | Notes |
|------|-----|-------|
| LAD | .200+ | Elite power |
| NYY | .195+ | Judge effect |
| ATL | .185+ | Deep lineup |
| PHI | .180+ | Power-heavy |

**Low-Risk (Safer matchups):**
| Team | ISO | Notes |
|------|-----|-------|
| OAK | .130- | Weak power |
| CHW | .135- | Rebuilding |
| MIA | .140- | Young |
| PIT | .145- | Contact-oriented |

**Impact with -13 HR scoring:** High-ISO team = +0.2-0.3 HR per start ≈ -2.5 to -4 pts

---

## 7. Pitcher Metrics

**Source:** [FanGraphs Pitching Leaderboard](https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=y&type=1&season=2025&month=0&season1=2025&ind=0&team=0&rost=0&age=0&filter=&players=0)

**Update Frequency:** Weekly during season (daily for streaming candidates)

### Key Metrics

| Metric | Source | Target | Avoid | Stabilization |
|--------|--------|--------|-------|---------------|
| **K-BB%** | FanGraphs | >15% | <10% | 150 PA |
| **Stuff+** | FanGraphs | >105 | <95 | 80 pitches |
| **GB%** | FanGraphs | >45% | <35% | 100 BIP |
| **Barrel%** | Savant | <7% | >10% | 100 BBE |

---

## 8. Probable Pitchers Schedule

**Source:** [FanGraphs Probables Grid](https://www.fangraphs.com/roster-resource/probables-grid)

**Update Frequency:** Daily (probables known 1-1.5 weeks ahead)

**Alternative:** [MLB.com Probable Pitchers](https://www.mlb.com/probable-pitchers)

---

## Early Season Strategy (April-May)

When current-year data is insufficient:

| Data Type | Fallback Source |
|-----------|-----------------|
| Park Factors | 3-year Statcast rolling (current source) |
| Team K%/ISO | Prior year + projection (Steamer, ZiPS) |
| Catcher Framing | Prior year (0.52-0.77 YoY correlation) |
| Umpire Zones | Prior year (relatively stable) |
| Weather/HRFI | Game-day forecast (always current) |

**Switch to current-year data:** By June 1st (adequate sample size)

---

## Quick Links Summary

| Data | URL | Check Frequency |
|------|-----|-----------------|
| Park Factors | baseballsavant.mlb.com/leaderboard/statcast-park-factors | Monthly |
| HRFI Weather | homerunforecast.com | Game-day |
| Umpire Zones | umpscorecards.com | Pre-game (if available) |
| Catcher Framing | baseballsavant.mlb.com/catcher_framing | Weekly |
| Team Stats | fangraphs.com/leaders | Weekly |
| Probable Pitchers | fangraphs.com/roster-resource/probables-grid | Daily |
| Wrigley Wind | windsblowingout.com | Game-day (Wrigley only) |
