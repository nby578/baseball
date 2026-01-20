# Fantasy Baseball Bot Project

## Quick Context
Building an AI-powered Yahoo Fantasy Baseball automation system. **Hybrid approach required** - Yahoo deprecated API Write access in Oct 2025, so we use API for monitoring + Claude for Chrome for executing moves.

## Project Status: API WORKING ✓

### Completed
- [x] Project structure created at `FBB/fantasy-bot/`
- [x] Python 3.14.2 confirmed installed
- [x] Yahoo API documentation saved to `fantasy-bot/docs/`
- [x] Discovered Yahoo removed Write API access (Oct 2025) - [yfpy Issue #79](https://github.com/uberfastman/yfpy/issues/79)
- [x] Yahoo Developer app registered (App ID: 6yF3a0Ly)
- [x] OAuth2 authentication working (tokens saved in oauth2.json)
- [x] Read API connection tested successfully (Jan 18, 2026)

### Next Steps
1. Build roster monitoring module (IL/NA detection)
2. Build Chrome automation for roster moves
3. Create alerting system (Discord webhooks)
4. Set up scheduled checks (GitHub Actions or local cron)

---

## Architecture Decision

```
┌─────────────────────────────────────────────────────────┐
│                    HYBRID APPROACH                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Yahoo Fantasy API (Read-Only)     Claude for Chrome    │
│  ─────────────────────────────     ─────────────────    │
│  • Get roster status               • Make lineup changes│
│  • Check IL/NA status              • Add/drop players   │
│  • Monitor free agents             • Submit waivers     │
│  • Get player stats                • Execute trades     │
│  • League standings                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Why Hybrid?** Yahoo removed Write API access for new apps (Oct 2025). Existing apps grandfathered in, but new apps are Read-only. Chrome automation is the workaround.

---

## Critical Discovery: Yahoo API Write Access Removed

**Date Found**: Jan 2026
**Source**: https://github.com/uberfastman/yfpy/issues/79

- New apps can only get `fspt-r` (Read) scope
- `fspt-w` (Write) scope no longer available for new registrations
- Existing apps with Write access still work
- Likely related to Yahoo Fantasy Plus paid service push

---

## Project Files

```
FBB/
├── CLAUDE.md                          # This file - project state
├── Yahoo API Documentation.txt        # Full official Yahoo API docs
├── fantasy_baseball_dashboard.tsx     # 2022 season dashboard
├── fantasy-baseball-wave-chart.tsx    # 2025 wave chart
├── jumpoff research.md                # AI fantasy baseball research
├── Original Dashboard Context.txt     # Dashboard dev history
├── Wave Context.txt                   # Wave chart context
├── Jump Off Context.txt               # Automation project context
│
└── fantasy-bot/                       # Main bot project
    ├── auth.py                        # Yahoo OAuth module
    ├── config.py                      # Configuration
    ├── requirements.txt               # Python dependencies
    ├── .env.example                   # Credential template
    ├── .gitignore
    ├── README.md
    └── docs/
        ├── yahoo_api_reference.md     # API method reference
        └── yahoo_official_docs.txt    # Full Yahoo docs copy
```

---

## Yahoo App Registration

**URL**: https://developer.yahoo.com/apps/

**Settings to use**:
| Field | Value |
|-------|-------|
| Application Name | Fantasy Baseball Bot |
| Application Type | Confidential Client |
| Redirect URI | `https://localhost` |
| API Permissions | Fantasy Sports (Read only - Write no longer available) |

**After creation, save**:
- Client ID → `.env` as `YAHOO_CLIENT_ID`
- Client Secret → `.env` as `YAHOO_CLIENT_SECRET`

---

## User's League Info

- **Platform**: Yahoo Fantasy Baseball
- **Yahoo GUID**: 5MRVOCCT5RVXXX3WGKEXBHA624
- **Known League**: "Big League Jew V" (2019: `388.l.121268`)
- **Strategy**: Heavy streaming, crowd picks + stats + double starts + opponent quality
- **Track record**: Medals almost every year, usually 2nd place
- **Season**: 2026 starts ~April (league key TBD once created)

---

## Key API Endpoints (Read-Only)

```python
# Get my roster
team.roster()  # Returns players with status (IL, DTD, NA, etc.)

# Get free agents
league.free_agents('SP')  # By position

# Get league info
league.standings()
league.current_week()
league.matchups()

# Player stats
league.player_stats(player_ids, 'season')
```

---

## Bot Goals

1. **Never miss IL/NA activations** - Alert when player returns from IL
2. **Never start injured players** - Detect DTD/IL status
3. **Streaming recommendations** - Find best pitcher matchups
4. **Waiver wire alerts** - Hot free agents
5. **Schedule optimization** - Track double-start weeks

---

## Tech Stack (Free)

| Component | Tool | Cost |
|-----------|------|------|
| Compute | GitHub Actions / Local | $0 |
| API | yahoo_fantasy_api | $0 |
| Data | FanGraphs, MLB Stats API | $0 |
| Browser | Claude for Chrome | $0 |
| Alerts | Discord webhooks | $0 |

---

## Related Conversations

- **Dashboard building**: See `Original Dashboard Context.txt`
- **Wave analysis**: See `Wave Context.txt`
- **Automation research**: See `Jump Off Context.txt`, `jumpoff research.md`

---

## Commands to Resume

```bash
# Navigate to project
cd C:\Users\NoahYaffe\Documents\GitHub\Claude_Projects\FBB\fantasy-bot

# Activate venv (once created)
venv\Scripts\activate

# Test auth (once credentials set)
python auth.py
```

---

## Chrome Automation Paths

### Key URLs (Direct Navigation)
```
# Fantasy Baseball Home
https://baseball.fantasysports.yahoo.com/

# Your Fantasy Profile (shows all leagues)
https://profiles.sports.yahoo.com/

# Specific League (replace LEAGUE_KEY)
https://baseball.fantasysports.yahoo.com/b1/{league_id}

# Your Team in a League
https://baseball.fantasysports.yahoo.com/b1/{league_id}/team/{team_id}

# Roster/Lineup Page
https://baseball.fantasysports.yahoo.com/b1/{league_id}/team/{team_id}/roster

# Free Agents
https://baseball.fantasysports.yahoo.com/b1/{league_id}/players
```

### Known League Info
| Year | League | League ID | Team ID | Team Name |
|------|--------|-----------|---------|-----------|
| 2025 | Big League Jew X | **89318** | **7** | Vlad The Impaler |
| 2024 | Big League Jew IX | TBD | TBD | Vlad The Impaler |
| 2021 | Big League Jew VI | TBD | TBD | I'd Like To Thank Guerrero (🏆 1st) |
| 2019 | Big League Jew V | 121268 | TBD | NGU NEVER VERLANDER! |

### Direct URLs (2025 Season - use as template)
```
# League home
https://baseball.fantasysports.yahoo.com/2025/b1/89318

# My Team (roster view)
https://baseball.fantasysports.yahoo.com/2025/b1/89318/7

# Free Agents
https://baseball.fantasysports.yahoo.com/2025/b1/89318/players
```

### Roster Positions (Big League Jew X)
**Batters:** C, 1B, 2B, 3B, SS, OF, OF, OF, Util, Util, Util
**Pitchers:** SP, SP, RP, RP, RP, P, P, P
**Bench:** ~6 BN slots
**IL:** 2 slots (one batter, one pitcher observed)

### Navigation Flow (Chrome)
```
1. Start: https://baseball.fantasysports.yahoo.com/
2. If not logged in: Click "Sign In" (top right)
3. Profile: Click "Fantasy Baseball" dropdown → "Profile"
4. Or direct: https://profiles.sports.yahoo.com/
5. Filter: Click "Baseball" button
6. History: Click "History" tab
7. Click league name to enter specific league
```

### Element References (may change between sessions)
```
# Profile page tabs
History tab: button containing text "History"
Baseball filter: button containing text "Baseball"

# League page elements (to document when we explore)
- Roster link: TBD
- Add/Drop button: TBD
- IL slot: TBD
- Start/Bench toggle: TBD
```

### Automation Checklist (Daily)
```
□ Check roster for IL/DTD status changes
□ Verify no injured players in starting lineup
□ Check for IL returns (players healthy but in IL slot)
□ Review streaming pitcher options
□ Check waiver wire for hot pickups
```

---

## User's League History (Baseball)

| Year | Team Name | League | Finish |
|------|-----------|--------|--------|
| 2025 | Vlad The Impaler | Big League Jew X | 🥈 2nd/12 |
| 2024 | Vlad The Impaler | Big League Jew IX | 🥈 2nd/12 |
| 2024 | Noah's Nifty Team | Big League New II | 4th/6 |
| 2023 | Noah's Nifty Team | Big League New | 7th/8 |
| 2023 | Vlad The Infielder | Big League Jew VIII | 🥈 2nd/12 |
| 2022 | Kirby's DreamYand | Big League Jew VII | 6th/12 |
| 2021 | I'd Like To Thank Guerrero | Big League Jew VI | 🏆 **1st/12** |
| 2019 | NGU NEVER VERLANDER! | Big League Jew V | 🥈 2nd/10 |

**Pattern**: 4 silvers, 1 gold, 1 down year in 8 seasons. Goal: More golds!

---

---

## Backtesting System (Jan 2026)

### What's Built
Complete backtesting infrastructure to validate streaming pitcher predictions against historical results.

**Core Files:**
```
backtesting/
├── backtester.py          # Main backtest runner
├── yahoo_fetcher.py       # Yahoo API + transaction history
├── mlb_fetcher.py         # pybaseball wrapper (pitcher/team stats)
├── game_results.py        # Actual pitcher game results
├── results/               # Backtest output JSON files
└── data/                  # Cached stats (parquet files)
    ├── game_results_cache/   # 300+ pitcher game logs
    ├── stats_cache/          # Season pitching/batting stats
    └── transactions/         # Yahoo transaction history
```

### Historical Data Available

**League Transactions (4,313 total across 7 seasons):**
| Season | League | Adds | Game Key |
|--------|--------|------|----------|
| 2019 | Big League Jew V | ~400 | 388 |
| 2020 | Big League Jew V | ~300 | 398 |
| 2021 | Big League Jew VI | 100 | 404 |
| 2022 | Big League Jew VII | 84 | 412 |
| 2023 | Big League Jew VIII | 100 | 422 |
| 2024 | Big League Jew IX | 50 | 431 |
| 2025 | Big League Jew X | 89 | 458 |
| 2026 | Big League Jew XI | TBD | 469 |

**Backtest Results (423 records with predictions):**
| Season | Records | MAE | Bias | R² |
|--------|---------|-----|------|-----|
| 2021 | 83 | 7.44 | -3.83 | -0.25 |
| 2022 | 61 | 7.21 | -3.91 | -0.09 |
| 2023 | 78 | 6.82 | -3.12 | -0.11 |
| 2024 | 46 | 4.62 | +1.54 | +0.02 |
| 2025 | 155 | 7.89 | -5.42 | -0.04 |

### Calibrated Prediction Model v2 (Jan 2026)

**Formula:** `predicted_points = 2 + (total_score * 0.10)`

**Scoring Weights:**
| Factor | Weight | Notes |
|--------|--------|-------|
| K-BB% | 30% | Strikeout ability |
| Experience (IP) | 25% | Season track record |
| **Recent Form** | 25% | Last 5 starts - HOT pitchers stay hot! |
| Opponent K% | 10% | Inverse - low K% easier |
| Park Factor | 10% | HR park factor |

**Recent Form Tracking:**
- `avg_points`: Average fantasy points in last 5 starts
- `trend`: "hot" (improving), "cold" (declining), "neutral"
- `disaster_rate`: % of starts under 5 pts (consistency indicator)

**Removed Factors (bad correlations):**
- GB% (r=-0.243) - negative correlation, counterintuitive
- Opponent ISO (r=0.038) - near-zero, no predictive value

**Risk Tiers:**
| Tier | Criteria | Historical Avg |
|------|----------|----------------|
| ELITE | score >= 65 AND IP >= 100 AND low disaster rate | 10.7 pts |
| STRONG | score >= 60 OR (score >= 55 AND hot streak) | 9.6 pts |
| MODERATE | score >= 50 AND not cold | 7.4 pts |
| RISKY | score >= 40 OR cold | 6.5 pts |
| AVOID | score < 40 | ~5 pts |

---

## Live Streaming Tools (Jan 2026)

**Core Files:**
```
live/
├── streaming_planner.py      # Weekly streaming recommendations
├── streaming_bot.py          # Main orchestrator
├── live_roster_monitor.py    # IL/injury detection
├── schedule_fetcher.py       # MLB probable starters API
└── scheduled_monitor.py      # Local scheduler
```

### Running the Streaming Planner
```bash
cd C:\Users\NoahYaffe\Documents\GitHub\baseball\live
python streaming_planner.py
```

**Output:** Ranked list of streaming options with:
- Pitcher stats (K-BB%, IP sample)
- Opponent matchup (team K%, park factor)
- Expected points and risk tier
- Upcoming start dates

### MLB Stats API (Free, No Auth)
```python
# Probable starters
GET https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=YYYY-MM-DD&hydrate=probablePitcher

# Team roster
GET https://statsapi.mlb.com/api/v1/teams/{team_id}/roster
```

---

## Commands Quick Reference

```bash
# Run backtest for a season
cd C:\Users\NoahYaffe\Documents\GitHub\baseball\backtesting
python backtester.py 2024 100

# Run streaming planner
cd C:\Users\NoahYaffe\Documents\GitHub\baseball\live
python streaming_planner.py

# Test Yahoo auth
cd C:\Users\NoahYaffe\Documents\GitHub\Claude_Projects\FBB\fantasy-bot
python auth.py
```

---

*Last updated: Jan 19, 2026*
