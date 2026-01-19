"""
Advanced Stats Guide for BLJ X

Obscure and underutilized statistics that provide edges in FIP-based points leagues.
Focus: stats that predict walks (+3), avoid HR allowed (-13), and identify K upside (+2).

These are the stats your leaguemates probably aren't using.
"""

# =============================================================================
# BATTER STATS: FINDING HIDDEN OBP VALUE
# =============================================================================

CHASE_RATE = """
=== O-SWING% (CHASE RATE) ===

WHAT IT IS:
- Percentage of pitches outside the zone that a batter swings at
- League average: ~30%
- Lower = more patient = more walks

WHY IT MATTERS FOR BLJ X:
- Walks = 3 pts (65% of a single's value!)
- Low O-Swing% directly correlates with walk rate
- High O-Swing% guys are walk-allergic

THRESHOLDS:
- Elite (<20%): Juan Soto, Kyle Schwarber, Bryce Harper
- Good (20-25%): Quality plate discipline
- Average (25-32%): League norm
- Bad (32-40%): Free swingers, avoid
- Terrible (>40%): Will never walk, major red flag

HOW TO USE:
- Target hitters with O-Swing% under 25%
- Avoid guys over 35% even if they're hitting well
- Low O-Swing% + high BB% = elite BLJ X asset
- Compare to SwStr% (whiff rate) for full picture

EDGE: Most fantasy players look at BA, not O-Swing%.
A .240 hitter with 18% O-Swing% will outearn a .280 hitter with 38% O-Swing%.
"""

EXPECTED_STATS = """
=== xwOBA / xBA / xSLG (EXPECTED STATS) ===

WHAT THEY ARE:
- Statcast measures exit velocity + launch angle on every batted ball
- Calculates what SHOULD have happened based on quality of contact
- Strips out luck, defense, and park factors

xwOBA vs wOBA DIFFERENTIAL:
- Positive (xwOBA > wOBA): Player is UNLUCKY, buy low
- Negative (xwOBA < wOBA): Player is LUCKY, sell high
- Typical regression: ~50% within 2-3 weeks

KEY INSIGHT FOR BLJ X:
- Your scoring rewards OUTCOMES, not expected outcomes
- BUT expected stats predict FUTURE outcomes
- Use for buy/sell decisions, not current lineup choices

THRESHOLDS (xwOBA):
- Elite (>.400): Top 10% of hitters
- Great (.360-.400): All-star caliber
- Above Average (.320-.360): Solid everyday player
- Average (.300-.320): League average
- Below Average (<.300): Replacement level

SPECIFIC USE CASES:
1. Cold streak + high xwOBA = BUY (luck will turn)
2. Hot streak + low xwOBA = SELL (regression coming)
3. Consistent xwOBA = actual skill, trust it

EDGE: xwOBA takes 200+ PA to stabilize.
Early season, look at underlying metrics instead.
"""

BARREL_RATE = """
=== BARREL RATE ===

WHAT IT IS:
- A "barrel" = batted ball with ideal exit velo + launch angle
- Results in .500+ BA and 1.500+ SLG historically
- Basically: how often does the hitter CRUSH the ball?

WHY IT MATTERS FOR BLJ X:
- HR = 14 pts (massive)
- 2B = 7.5 pts (great)
- Barrels = future HRs and XBH
- More predictive of power than actual HR totals

THRESHOLDS:
- Elite (>15%): Premium power (Judge, Acuna, Ohtani)
- Great (10-15%): Plus power
- Average (6-10%): League norm
- Below (4-6%): Gap power, not HR power
- Poor (<4%): No power upside

STABILIZATION: ~150 batted ball events (~300 PA)

COMBO METRICS TO WATCH:
- Barrel% + HardHit% = power profile
- Barrel% + Flyball% = HR projection
- High Barrel% + Low HR = BUY (luck)
- Low Barrel% + High HR = SELL (regression)

EDGE: Barrel rate stabilizes faster than HR totals.
April HR leaders with low Barrel% will regress.
April non-HR hitters with high Barrel% will break out.
"""

HARD_HIT_RATE = """
=== HARD HIT RATE (95+ MPH) ===

WHAT IT IS:
- Percentage of batted balls at 95+ mph exit velocity
- Raw measure of how hard a player hits the ball
- Doesn't account for launch angle

WHY IT MATTERS:
- Hard contact = more XBH = more points
- Very stable metric (200 BBE to stabilize)
- Less noisy than HR or even Barrel Rate

THRESHOLDS:
- Elite (>50%): Exceptional hitter
- Great (45-50%): Plus bat
- Above Average (40-45%): Good
- Average (35-40%): League norm
- Below Average (<35%): Weak contact

BLJ X APPLICATION:
- Hard Hit Rate predicts points better than BA
- A .250 hitter with 48% HardHit > .280 hitter with 32% HardHit
- Look for Hard Hit% + BB% combo for total package

SLEEPER FINDER:
- High HardHit% + Low BABIP = EXTREMELY unlucky, BUY NOW
- Example: .220 BA, 45% HardHit, .240 BABIP = massive regression coming
"""

ZONE_CONTACT = """
=== Z-CONTACT% (ZONE CONTACT RATE) ===

WHAT IT IS:
- How often a batter makes contact on pitches IN the zone
- Different from overall contact rate (includes chases)
- Measures "can they hit pitches they should hit?"

WHY IT MATTERS FOR BLJ X:
- AB penalty (-1) means outs hurt
- High Z-Contact% = fewer Ks = fewer -1 AB outcomes
- But too high can mean weak contact

THRESHOLDS:
- Elite (>92%): Almost never whiffs in zone
- Great (88-92%): Plus contact skills
- Average (84-88%): League norm
- Below (80-84%): Whiff issues
- Poor (<80%): K machine

THE SWEET SPOT:
- Want Z-Contact% around 85-90% WITH power
- Too high (>95%) often means no power (slapping)
- Too low (<80%) means too many Ks

COMBO WITH O-SWING%:
- High Z-Contact% + Low O-Swing% = IDEAL
- Makes contact on good pitches, takes bad ones
- Example: Soto, Freeman, Ramirez
"""

# =============================================================================
# PITCHER STATS: AVOIDING THE -13 HR BOMB
# =============================================================================

HR_FB_RATE = """
=== HR/FB RATE (HR PER FLY BALL) ===

WHAT IT IS:
- Percentage of fly balls that become home runs
- League average: ~11-12%
- Highly volatile and luck-dependent

WHY THIS IS GOLD FOR BLJ X:
- HR allowed = -13 pts (DEVASTATING)
- HR/FB rate regresses HARD to the mean
- Pitchers don't control HR/FB much

REGRESSION PATTERNS:
- HR/FB under 8% = UNSUSTAINABLE, will allow more HRs
- HR/FB over 15% = UNLUCKY, will allow fewer HRs
- Career norms matter more than recent samples

STABILIZATION: 1,200+ batted balls (multiple seasons!)

ACTIONABLE INSIGHT:
1. Pitcher with 4.50 ERA but 18% HR/FB? BUY - ERA will drop
2. Pitcher with 2.80 ERA but 6% HR/FB? SELL - ERA will rise
3. Always check HR/FB before streaming

WARNING SIGNS:
- Low GB% + High FB% + Hitter's park = HR waiting to happen
- High HR/FB + Career norm is lower = regression coming
- But High HR/FB + Career high HR/FB = might be real

EDGE: Most fantasy players see ERA, not HR/FB.
A "bad" pitcher with high HR/FB is a buy.
A "good" pitcher with low HR/FB is a sell.
"""

K_BB_RATE = """
=== K-BB% (STRIKEOUT MINUS WALK RATE) ===

WHAT IT IS:
- K% minus BB%
- Single best predictor of pitcher quality
- Measures what pitchers actually control

WHY IT MATTERS FOR BLJ X:
- K = +2 pts
- BB = -3 pts
- K-BB% captures both in one number
- Correlates strongly with future ERA

THRESHOLDS:
- Elite (>25%): Ace level (Cole, deGrom healthy)
- Great (20-25%): Top 20 starter
- Above Average (15-20%): Quality arm
- Average (10-15%): League norm
- Below Average (5-10%): Fringy
- Poor (<5%): Avoid completely

BLJ X POINTS MATH:
- 15% K-BB% over 6 IP (~24 batters) =
  ~3.6 Ks = +7.2 pts
  ~1.2 BB = -3.6 pts
  Net: +3.6 pts just from K-BB
- 25% K-BB% over same:
  ~6 Ks = +12 pts
  ~1.5 BB = -4.5 pts
  Net: +7.5 pts from K-BB

STABILIZATION: ~150 batters faced (~5-6 starts)

STREAMING RULE:
- Never stream a pitcher with K-BB% under 10%
- Target 15%+ for quality streams
- Elite (20%+) = pay up for these arms
"""

GROUND_BALL_RATE = """
=== GB% (GROUND BALL RATE) ===

WHAT IT IS:
- Percentage of batted balls that are ground balls
- Ground balls rarely become HRs
- But they can become hits

WHY THIS IS CRITICAL FOR BLJ X:
- HR allowed = -13 pts
- Ground balls = almost 0% HR chance
- Fly balls = 11%+ HR chance
- GB pitchers are INSURANCE against -13 bombs

THRESHOLDS:
- Elite (>55%): Extreme grounder (Webb, Bieber)
- Great (50-55%): Plus GB rate
- Average (43-50%): League norm
- Below Average (38-43%): Fly ball tendency
- Fly Ball (<38%): HR risk (unless elite K rate)

THE CALCULATION:
- At 50% GB%, only 50% of balls in play can be HR
- At 35% GB%, 65% of balls can be HR
- Each 5% GB = significant HR reduction

STREAMING PRIORITY:
1. High K-BB% + High GB% = PREMIUM stream
2. High K-BB% + Low GB% = Risky but upside
3. Low K-BB% + High GB% = Safe but low ceiling
4. Low K-BB% + Low GB% = AVOID

PARK FACTOR COMBO:
- GB pitcher at Coors? Actually fine (HR factor only 106)
- FB pitcher at Yankee Stadium? DISASTER (-13 bombs incoming)

EDGE: People fear Coors. They should fear LAD/NYY for FB pitchers.
"""

WHIFF_RATE = """
=== WHIFF RATE (SwStr%) ===

WHAT IT IS:
- Swinging strikes divided by total swings
- Measures a pitcher's ability to miss bats
- Directly translates to strikeouts

WHY IT MATTERS:
- K = +2 pts
- High whiff rate = high K rate = more points
- Very stable, predictive metric

THRESHOLDS:
- Elite (>14%): K machine (Clase, Diaz, Burns)
- Great (12-14%): Plus K ability
- Above Average (10-12%): Good strikeout stuff
- Average (8-10%): League norm
- Below (<8%): Weak K upside

RELATIONSHIP TO K%:
- Whiff Rate * Contact Rate = ~K%
- High whiff + high chase = massive Ks
- Whiff rate more stable than K% early season

STABILIZATION: ~200 pitches (very fast!)

EARLY SEASON USE:
- April K% can be noisy
- Whiff rate stabilizes by 2nd or 3rd start
- Use whiff rate for early season streaming decisions

COMBO METRIC:
- CSW% (Called Strike + Whiff) = total strike generation
- CSW% over 30% = elite
- CSW% + GB% = full pitcher profile
"""

CHASE_RATE_PITCHERS = """
=== O-SWING% INDUCED (PITCHER CHASE RATE) ===

WHAT IT IS:
- How often batters chase pitches outside the zone
- Pitcher skill, not just batter discipline
- Measures deception and stuff quality

WHY IT MATTERS:
- High chase = more Ks on non-strikes
- Efficient pitch counts
- Deeper into games = more IP (+5 per IP)

THRESHOLDS:
- Elite (>35%): Nasty stuff, batters flailing
- Great (32-35%): Plus deception
- Average (28-32%): League norm
- Below (<28%): Hittable stuff

BLJ X APPLICATION:
- High O-Swing% induced + High Whiff = K monster
- High O-Swing% + Low Whiff = Contact on chases (not ideal)
- Combo tells you if chases become Ks or weak contact

STREAMING INSIGHT:
- Target pitchers with 32%+ chase rate
- They generate easy strikes and Ks
- Especially valuable vs high-chase teams (OAK, CHW)
"""

# =============================================================================
# UNDERRATED STATS: DEEP CUTS
# =============================================================================

SPRINT_SPEED = """
=== SPRINT SPEED ===

WHAT IT IS:
- Feet per second on competitive runs
- Measures raw speed, not just SB totals
- Statcast measures every player

WHY IT'S UNDERRATED FOR BLJ X:
- SB only 1.9 pts (not great)
- BUT speed also = higher BABIP, more triples
- Triples = 10.3 pts (huge)
- Fast + high line drive = BABIP monster

THRESHOLDS:
- Elite (>30 ft/s): Burner (Ohtani, Acuna, Witt Jr)
- Great (28-30 ft/s): Plus speed
- Above Average (27-28 ft/s): Can steal
- Average (26-27 ft/s): League norm
- Below (<26 ft/s): Slow, no SB value

HIDDEN VALUE:
- Speed helps BABIP by ~15-20 points
- Speed helps turn doubles into triples
- Speed turns grounders into infield hits

BUT FOR BLJ X:
- Don't DRAFT for speed (SB undervalued)
- DO consider speed as tiebreaker
- Speed is cherry on top, not the sundae
"""

EXTENSION = """
=== PITCHER EXTENSION ===

WHAT IT IS:
- How far toward home plate a pitcher releases the ball
- More extension = less reaction time for hitter
- Measured in feet

WHY IT'S SNEAKY IMPORTANT:
- Average extension: 6.0-6.2 feet
- Elite extension: 6.5+ feet
- Each extra 6 inches = ~1 mph perceived velocity

EFFECT ON STUFF:
- 93 mph + 6.8 ft extension = "feels like" 96 mph
- More whiffs, more Ks
- Especially helps fastballs

SLEEPER FINDER:
- Average velocity + elite extension = hidden K upside
- These guys often have better results than velocity suggests

EXAMPLES:
- Ranger Suarez: 92 mph but elite extension
- Results better than velo suggests
- Undervalued in drafts
"""

STUFF_PLUS = """
=== STUFF+ / LOCATION+ / PITCHING+ ===

WHAT THEY ARE:
- Stuff+: Raw pitch quality (movement, velo, spin)
- Location+: How well they hit spots
- Pitching+: Combined overall grade
- 100 = average, higher = better

WHY THESE MATTER:
- Predictive of future performance
- Context-neutral (not affected by luck)
- Better than ERA for pitcher evaluation

THRESHOLDS (all three):
- Elite (>115): Ace stuff
- Great (105-115): Quality arm
- Average (95-105): League norm
- Below (<95): Fringy

BLJ X APPLICATION:
- High Stuff+ but high ERA = BUY (stuff will win out)
- Low Stuff+ but low ERA = SELL (luck will run out)
- Stuff+ + Pitching+ combo = full picture

HOW TO USE:
- Stuff+ for raw talent assessment
- Location+ for command reliability
- Pitching+ for overall ranking

STABILIZATION: ~300 pitches (2-3 starts)
"""

# =============================================================================
# SUMMARY: STAT PRIORITY FOR BLJ X
# =============================================================================

BLJ_X_STAT_PRIORITY = """
=== STAT PRIORITY FOR BLJ X SCORING ===

BATTERS (in order of importance):
1. O-Swing% - Predicts walks (+3 pts)
2. BB% - Direct walk production
3. Barrel Rate - Predicts power (HR = 14 pts)
4. xwOBA - True talent level
5. Hard Hit% - Contact quality
6. Z-Contact% - Avoids K penalty

PITCHERS (in order of importance):
1. HR/FB Rate - Predicts HR regression (-13 per HR!)
2. K-BB% - Best overall predictor
3. GB% - HR avoidance
4. Whiff Rate - K upside (+2 per K)
5. Stuff+/Pitching+ - True talent
6. O-Swing% Induced - Chase rate

DAILY STREAMING CHECKLIST:
[ ] Opponent team HR rate (avoid high HR teams)
[ ] Park HR factor (avoid LAD, NYY, PHI)
[ ] Pitcher K-BB% (want 15%+)
[ ] Pitcher GB% (prefer 45%+)
[ ] Pitcher HR/FB (beware <8% or >15%)

BUY LOW SIGNALS:
- High xwOBA, low actual wOBA (hitter)
- High HR/FB, career norm is lower (pitcher)
- High Stuff+, high ERA (pitcher)
- Low O-Swing%, few walks so far (hitter)

SELL HIGH SIGNALS:
- Low xwOBA, high actual wOBA (hitter)
- Low HR/FB, career norm is higher (pitcher)
- Low Stuff+, low ERA (pitcher)
- Hot streak with poor underlying metrics
"""

QUICK_REFERENCE = """
=== QUICK REFERENCE: OBSCURE STAT THRESHOLDS ===

BATTERS - TARGET THESE:
- O-Swing% under 25%
- Barrel Rate over 10%
- Hard Hit% over 45%
- xwOBA over .360
- Z-Contact% 85-90% (with power)

BATTERS - AVOID THESE:
- O-Swing% over 35%
- Barrel Rate under 6%
- Hard Hit% under 35%
- xwOBA under .300

PITCHERS - TARGET THESE:
- K-BB% over 15%
- GB% over 50%
- Whiff Rate over 12%
- Stuff+ over 105
- HR/FB 10-13% (league average)

PITCHERS - AVOID THESE:
- K-BB% under 10%
- GB% under 40% (fly ball pitcher)
- Whiff Rate under 8%
- HR/FB under 8% (will regress UP)
- Pitching at LAD, NYY, PHI (HR parks)

REGRESSION ALERTS:
- HR/FB < 8% = More HRs coming
- HR/FB > 15% = Fewer HRs coming
- xwOBA - wOBA > .030 = Unlucky, buy
- xwOBA - wOBA < -.030 = Lucky, sell
- Hot streak + bad barrels = Sell
- Cold streak + good barrels = Buy
"""

if __name__ == "__main__":
    print("=" * 60)
    print("ADVANCED STATS GUIDE FOR BLJ X")
    print("=" * 60)

    sections = [
        ("CHASE RATE (O-Swing%)", CHASE_RATE),
        ("EXPECTED STATS (xwOBA)", EXPECTED_STATS),
        ("BARREL RATE", BARREL_RATE),
        ("HARD HIT RATE", HARD_HIT_RATE),
        ("ZONE CONTACT", ZONE_CONTACT),
        ("HR/FB RATE", HR_FB_RATE),
        ("K-BB%", K_BB_RATE),
        ("GROUND BALL RATE", GROUND_BALL_RATE),
        ("WHIFF RATE", WHIFF_RATE),
        ("PITCHER CHASE RATE", CHASE_RATE_PITCHERS),
        ("SPRINT SPEED", SPRINT_SPEED),
        ("EXTENSION", EXTENSION),
        ("STUFF+", STUFF_PLUS),
    ]

    for name, content in sections:
        print(f"\n{'='*60}")
        print(f"STAT: {name}")
        print("=" * 60)
        print(content)

    print("\n" + "=" * 60)
    print(BLJ_X_STAT_PRIORITY)
    print("\n" + "=" * 60)
    print(QUICK_REFERENCE)
