"""
Hidden Edges for BLJ X

Research-backed inefficiencies that most fantasy managers miss.
Focused on exploiting the -13 HR penalty, +9 holds, and +3 walk scoring.

Source: Deep research on platoons, weather, catchers, umpires, and more.
"""

# =============================================================================
# CATCHER FRAMING - FREE POINTS
# =============================================================================
CATCHER_FRAMING = """
=== CATCHER FRAMING ===

WHAT IT IS:
- Elite framers steal 2 extra strikes per game
- Gap between best and worst: 38 runs per season
- Highly stable year-to-year (0.52-0.77 correlation)

BLJ X IMPACT:
- Each stolen strike that becomes K vs BB = 5 pt swing (+2 vs -3)
- Elite framer vs average = +1-2 pts per start
- Elite framer vs worst = +2-4 pts per start

ELITE FRAMERS (target pitchers throwing to these):
| Catcher        | Team     | Framing Runs |
|----------------|----------|--------------|
| Patrick Bailey | Giants   | +16          |
| Cal Raleigh    | Mariners | +13          |
| Austin Wells   | Yankees  | +12          |
| Jose Trevino   | Reds     | +10          |
| Alejandro Kirk | Blue Jays| +9           |

AVOID (negative framers):
| Catcher        | Team     | Framing Runs |
|----------------|----------|--------------|
| Edgar Quero    | White Sox| -13          |
| Riley Adams    | Nationals| -10          |

EDGE: Use framing as tiebreaker between similar streaming options.
A mediocre pitcher to Bailey > good pitcher to Quero.
"""

# =============================================================================
# WEATHER EFFECTS - MASSIVE HR SWINGS
# =============================================================================
WEATHER_EFFECTS = """
=== WEATHER & HOME RUN FORECAST ===

THE NUMBERS:
- 4 feet of additional carry per 10 degrees F
- 63% more HRs in extreme heat vs cold
- 5 mph wind out = 18-20 extra feet on fly balls

HRFI (Home Run Forecast Index) IMPACT:
| HRFI Score | Avg HR/Game | Avg Runs |
|------------|-------------|----------|
| 1-2 (cold) | 1.40        | 7.51     |
| 9-10 (hot) | 2.61        | 10.04    |

That's 86% MORE home runs in favorable conditions.

WIND-SENSITIVE PARKS:
- Wrigley Field: 23% HR/FB wind out vs 13% wind in (77% swing!)
- Oracle Park: 18 mph avg wind, 1 in 3 games wind-affected
- Kauffman: 67 wind-prevented HRs per season

BLJ X APPLICATION:
With -13 HR penalty, weather streaming is HIGH LEVERAGE.
- HRFI 1-3: START your pitchers (cold, wind in)
- HRFI 8+: BENCH your pitchers (hot, wind out)
- Wrigley/Coors with HRFI 8+: AVOID at all costs

RESOURCE: homerunforecast.com (free, updated hourly)

EDGE: Most managers don't check weather. You should.
"""

# =============================================================================
# RELIEVER FATIGUE - PREDICTABLE DECLINE
# =============================================================================
RELIEVER_FATIGUE = """
=== RELIEVER FATIGUE PATTERNS ===

VELOCITY DROP BY USAGE:
| Days Worked     | Fastball Velo |
|-----------------|---------------|
| 1 day rest      | 91.6 mph      |
| Back-to-back    | 91.0 mph      |
| 3 straight days | 89.2 mph      |

That's nearly 2 MPH drop on 3 consecutive days.

"TIRED RELIEVER" FLAGS:
- 25+ pitches previous day
- 35+ pitches over last 3 days
- Appearances in both prior 2 days

TRAVEL FATIGUE:
- Eastward travel = lose entire 4% home field advantage
- Pitchers allow ~0.1-0.2 more runs after flying east
- Monday games after West Coast trips = target

BLJ X APPLICATION:
- NEVER start relievers on 3rd consecutive day
- Target pitchers facing teams just back from West Coast
- Check Monday/Thursday off-days for rested bullpens

EDGE: Fatigue is predictable. Exploit it.
"""

# =============================================================================
# UMPIRE TENDENCIES - 22% K RATE VARIATION
# =============================================================================
UMPIRE_ZONES = """
=== UMPIRE ZONE VARIATION ===

THE NUMBERS:
- 22% variation in K rates between extreme umps
- Only 81% accuracy on borderline pitches
- 9% of all called pitches are incorrect

PITCHER-FRIENDLY UMPS (+22% K rate):
- Doug Eddings
- D.J. Reyburn
- Check current assignments

HITTER-FRIENDLY UMPS (-12% K rate):
- Marvin Hudson
- Chris Guccione

2025 RULE CHANGE:
- Buffer zone shrunk from 2" to 0.75"
- Effectively smaller called strike zone
- Fewer edge strikes = more walks

BLJ X IMPACT:
- K: +2, BB: -3 = 5 pt swing per extra strike
- Pitcher-friendly ump = 1-4 extra pts per start

RESOURCES:
- umpscorecards.com
- evanalytics.com
Check 1-3 hours before gametime

EDGE: Use as tiebreaker for streaming decisions.
"""

# =============================================================================
# PLATOON SPLITS - MOSTLY NOISE
# =============================================================================
PLATOON_SPLITS = """
=== PLATOON SPLITS: REAL BUT OVERRATED ===

LEAGUE-WIDE ADVANTAGES:
| Matchup      | wOBA Gain | Sample to Stabilize |
|--------------|-----------|---------------------|
| LHH vs RHP   | +43 pts   | 1,000 PA            |
| RHH vs LHP   | +32 pts   | 2,200 PA            |

KEY INSIGHT: Individual splits need MASSIVE samples.
Most "extreme split" players are experiencing noise.

WHAT'S ACTUALLY STICKY:
- K% and BB% differential (not power)
- Hitters walk more vs opposite hand
- With +3 walk scoring, this matters

PITCH TYPE MATTERS MORE:
- Sinkers/sliders: Big platoon effect
- Curveballs/changeups: REVERSE splits
- Don't stack lefties vs RHP curveball specialists
  (McCullers, Morton, etc.)

BLJ X APPLICATION:
- Use league-average platoon advantages for stacking
- LHH vs RHP = ~8.6% wOBA boost (reliable)
- Don't chase individual player splits under 500 PA
- The walk boost is what matters in your format

EDGE: Everyone overthinks platoons.
Use league averages, ignore small sample "data."
"""

# =============================================================================
# SETUP MEN - MASSIVELY UNDERVALUED
# =============================================================================
SETUP_MEN = """
=== ELITE SETUP MEN ===

THE MATH (your scoring):
- Saves: +11 pts
- Holds: +9 pts (82% of save value!)
- League produces 52% MORE holds than saves
- 100+ pitchers get 10+ holds vs only 39 get 10+ saves

EXAMPLE - ELITE SETUP MAN:
- 25 holds x 9 = 225 pts
- 70 IP x 5 = 350 pts
- 85 K x 2 = 170 pts
- TOTAL: 745+ pts

VS MID-TIER CLOSER:
- 30 saves x 11 = 330 pts
- 55 IP x 5 = 275 pts
- 60 K x 2 = 120 pts
- TOTAL: 725 pts

Setup man WINS and costs 50-100 picks less.

TARGET SETUP MEN:
| Name             | Team    | Holds | K's | Notes           |
|------------------|---------|-------|-----|-----------------|
| Bryan Abreu      | Astros  | 21    | 105 | Elite K rate    |
| Jeremiah Estrada | Padres  | 23    | 108 | K monster       |
| Griffin Jax      | Rays    | 24    | 99  | Versatile       |
| Garrett Whitlock | Red Sox | 22    | 91  | Steady          |
| Jason Adam       | Padres  | 22    | 70  | Low ERA         |

CLOSERS-IN-WAITING (stash):
- Porter Hodge (Cubs - Pressly aging)
- Orion Kerkering (Phillies)
- Justin Martinez (D-backs - 5 year extension at 23)
- Lucas Erceg (Royals)
- Cade Smith (Guardians - 47% closer probability)

TEAMS TO MONITOR FOR CLOSER CHANGES:
- Cubs (Pressly aging out)
- Reds (Pagan vulnerable)
- Cardinals (Helsley trade candidate)

EDGE: Don't overpay for closers. Target high-gmLI (>1.4)
relievers on winning teams. Holds are almost saves.
"""

# =============================================================================
# GROUND BALL RATE - HR SUPPRESSION KING
# =============================================================================
GROUND_BALL_PITCHERS = """
=== GROUND BALL RATE: YOUR -13 HR INSURANCE ===

THE RESEARCH:
- Fly ball pitchers allow 25% more HRs than ground ballers
- Dallas Keuchel (19.3% FB): 1 HR per 73 batters
- Jered Weaver (47.9% FB): 1 HR per 33 batters
- Same K%, same HR/FB% - just trajectory difference

MYTH BUSTED:
"Ground ballers have higher HR/FB because fly balls are mistakes"
REALITY: Correlation between GB% and HR/FB is -0.05 (none)

MYTH BUSTED:
"High-spin fastballs prevent HRs"
REALITY: Scherzer/Verlander have elite spin, allow lots of HRs.
High spin suppresses BA (.192 vs .259) but NOT HRs.

GB% THRESHOLDS:
| Classification | GB%   | HR Risk     |
|----------------|-------|-------------|
| Extreme GB     | >50%  | LOWEST      |
| Ground Baller  | 45-50%| Low         |
| Neutral        | 40-45%| Average     |
| Fly Ball       | <40%  | AVOID       |

ALSO CHECK:
- Barrel Rate Allowed: <7% = strong HR suppression
- Sinker usage: Higher = more grounders

MODEL TARGETS:
- Framber Valdez (elite GB%)
- Logan Webb (sinker heavy)
- Alex Cobb (ground ball machine)

AVOID:
- Four-seam dominant (>60% usage) in hitter parks
- Fly ball pitchers at LAD, NYY, PHI

EDGE: GB% is the simplest HR predictor.
With -13 per HR, this is your #1 pitcher filter.
"""

# =============================================================================
# DAY/NIGHT SPLITS - IGNORE THEM
# =============================================================================
DAY_NIGHT_SPLITS = """
=== DAY/NIGHT SPLITS: COMPLETE NOISE ===

THE RESEARCH:
- Year-to-year correlation: <0.05
- Worse predictor than pitcher BABIP (which is random)
- "Day game guys" don't exist

WHY PEOPLE THINK IT'S REAL:
- Small samples create illusions
- Confirmation bias after a good day game

THE ONE EXPLOITABLE PATTERN:
- Day games AFTER night games = backup catchers, tired players
- Stream PITCHERS in these spots, not hitters

BLJ X APPLICATION:
- Don't make lineup decisions based on day/night
- Don't roster "day game specialists"
- The one edge: stream pitchers vs fatigued lineups

EDGE: Save your mental energy for real edges.
Day/night is noise.
"""

# =============================================================================
# POINTS LEAGUE BIASES
# =============================================================================
POINTS_LEAGUE_BIASES = """
=== POINTS LEAGUE MARKET BIASES ===

WALKS ARE PREMIUM:
- +3 pts with no AB penalty
- Kyle Schwarber's 80 walks = 240 pts = 50+ singles equivalent
- Jonathan India: 80 walks made him 52nd best points hitter
- High-walk guys are discounted for low BA - BUY THEM

SPEED IS OVERRATED:
- SB: +1.9, CS: -2.8 = need 60%+ success to break even
- League CS rate: 21.3% and improving
- Speed peaks at 22, declines ~7 SBs by age 30
- Don't pay for pure speed

WORKHORSE STARTERS DOMINATE:
- Pablo Lopez: Top-20 in points despite 4.08 ERA (200+ IP)
- Michael King, Sonny Gray: Top-10 via 200+ Ks
- IP accumulation > ratios in points leagues

MIDDLE RELIEVERS WITHOUT SAVES = USELESS:
- No reliever with <10 saves finished top-80 in points
- Ratio benefits don't translate without counting stats
- Exception: Elite setup men with holds (your format)

| Common Bias           | Your Correction                    |
|-----------------------|------------------------------------|
| Closers essential     | Setup men with holds = 82% value   |
| Speed premium         | Need 60%+ SB success; avoid pure speed |
| Low-AVG guys bad      | High walks offset; Schwarber elite |
| Draft for ratios      | Draft for volume (IP, PA)          |
| Aging curve at 27-29  | Modern data: decline from arrival  |
"""

# =============================================================================
# QUICK REFERENCE - ACTIONABLE THRESHOLDS
# =============================================================================
ACTIONABLE_THRESHOLDS = """
=== ACTIONABLE THRESHOLDS FOR BLJ X ===

PITCHERS - STREAMING CHECKLIST:
[ ] GB% > 45% (avoid <40%)
[ ] Barrel% allowed < 7%
[ ] HRFI 1-3 (check homerunforecast.com)
[ ] Catcher is elite framer (Bailey, Raleigh, Wells)
[ ] Not 3rd consecutive day (relievers)
[ ] Check umpire 1-3 hrs pre-game

RELIEVERS - HOLD TARGETS:
[ ] gmLI > 1.4 (high leverage)
[ ] On winning team (more hold opps)
[ ] K rate > 25%
[ ] Not fatigued (check usage)

HITTERS - WALK TARGETS:
[ ] BB% > 10%
[ ] O-Swing% < 25%
[ ] Don't care about BA if OBP is high

SPEED - AVOID UNLESS:
[ ] SB success rate > 70%
[ ] Also has other value (power, OBP)
[ ] Don't pay premium for pure speed

WEATHER DECISIONS:
[ ] HRFI 1-3: Start pitchers confidently
[ ] HRFI 4-7: Neutral
[ ] HRFI 8+: Bench pitchers, especially at Wrigley/Coors

FATIGUE CHECKS:
[ ] Reliever on 3rd straight day: BENCH
[ ] Team just flew east: Target their hitters
[ ] Monday after West Coast trip: Stream vs them
"""

# =============================================================================
# RESOURCES
# =============================================================================
RESOURCES = """
=== FREE RESOURCES ===

WEATHER:
- homerunforecast.com (HRFI, updated hourly)

UMPIRES:
- umpscorecards.com (zone tendencies)
- evanalytics.com (daily assignments)

CATCHER FRAMING:
- Baseball Savant (framing runs)
- FanGraphs (historical data)

RELIEVER USAGE:
- ESPN "Tired Reliever" flags
- Roster Resource (bullpen depth charts)

STATCAST:
- Baseball Savant (barrel%, GB%, xwOBA)
- FanGraphs (K-BB%, Stuff+)

CHECK DAILY:
1. Weather/HRFI for streaming decisions
2. Umpire assignments 1-3 hrs pre-game
3. Reliever usage (3-day fatigue)
4. Lineup announcements (backup catcher days)
"""

if __name__ == "__main__":
    print("=" * 60)
    print("HIDDEN EDGES FOR BLJ X")
    print("=" * 60)

    sections = [
        ("CATCHER FRAMING", CATCHER_FRAMING),
        ("WEATHER EFFECTS", WEATHER_EFFECTS),
        ("RELIEVER FATIGUE", RELIEVER_FATIGUE),
        ("UMPIRE ZONES", UMPIRE_ZONES),
        ("PLATOON SPLITS", PLATOON_SPLITS),
        ("SETUP MEN", SETUP_MEN),
        ("GROUND BALL PITCHERS", GROUND_BALL_PITCHERS),
        ("DAY/NIGHT SPLITS", DAY_NIGHT_SPLITS),
        ("POINTS LEAGUE BIASES", POINTS_LEAGUE_BIASES),
        ("ACTIONABLE THRESHOLDS", ACTIONABLE_THRESHOLDS),
        ("RESOURCES", RESOURCES),
    ]

    for name, content in sections:
        print(f"\n{'='*60}")
        print(name)
        print("=" * 60)
        print(content)
