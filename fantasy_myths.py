"""
Fantasy Baseball: Myths vs Reality

Compiled research on what conventional wisdom gets WRONG.
Use these edges against your leaguemates.

Optimized for BLJ X scoring (-1 AB, +3 BB, -13 HR allowed, +2 K)
"""

# =============================================================================
# MYTH #1: COORS FIELD IS A HR DEATH TRAP
# =============================================================================
COORS_MYTH = """
MYTH: "Never stream at Coors Field - it's a launching pad"

REALITY:
- Coors HR park factor: 106 (barely above average!)
- Dodger Stadium HR factor: 127 (WORST in MLB)
- Yankee Stadium HR factor: 119 (short porch)

WHY: Coors has the LARGEST outfield in MLB (116,729 sq ft)
- Thin air helps ball carry, but huge outfield catches them
- Would-be HRs become doubles/triples instead
- For BLJ X (-13 per HR), doubles don't hurt you!

EDGE: Stream at Coors while others avoid it. Avoid LAD/NYY.
"""

# =============================================================================
# MYTH #2: HOT STREAKS ARE PREDICTIVE
# =============================================================================
HOT_STREAK_MYTH = """
MYTH: "This guy is hot, ride the streak!"

REALITY:
- Correlation between "hot" performance and next game: -0.00064
- That's effectively ZERO predictive power
- Hot streakers: .587 wOBA during streak -> .369 after (their normal)
- Even extreme streaks only predict ~5 points of wOBA

WHY: Small sample size noise dominates
- A player can go 8-for-15 purely by chance
- Doesn't mean anything changed about their ability
- Regression to mean is inevitable

EDGE: BUY players after cold streaks when others panic-sell.
Don't chase hot players at inflated prices.
"""

# =============================================================================
# MYTH #3: DRAFT CATCHERS/2B EARLY (POSITION SCARCITY)
# =============================================================================
POSITION_SCARCITY_MYTH = """
MYTH: "Catcher and 2B are so shallow, grab one early!"

REALITY:
- Panicking on C/2B leads to bypassing better overall talent
- You're sacrificing total points for positional "security"
- The drop-off at C isn't as bad as people think
- Streaming catchers is viable

WHY: Points leagues care about TOTAL POINTS, not categories
- A catcher hitting .240 with 15 HR gives you fewer points
  than a 3B hitting .280 with 25 HR
- Position is just roster construction, not value

EDGE: Let others panic-draft catchers early.
Take better hitters, fill C later with Yainer Diaz types.
"""

# =============================================================================
# MYTH #4: BABIP REGRESSION HAPPENS QUICKLY
# =============================================================================
BABIP_MYTH = """
MYTH: "His BABIP is .380, he'll crash any day now"

REALITY:
- BABIP takes 800+ balls in play to stabilize for hitters
- For pitchers, it's 2,000+ balls in play (multiple seasons!)
- A hot April doesn't mean May will be cold

WHY: Personal baseline matters more than league average
- Fast players legitimately run higher BABIP (.320+)
- Fly ball hitters run lower BABIP
- Compare to CAREER BABIP, not league average .300

EDGE: Don't sell players just because of high BABIP.
Check their career baseline first.

KEY INSIGHT FOR BLJ X:
Your scoring penalizes AB (-1), not BABIP directly.
A .350 BABIP guy with walks is BETTER than
a .280 BABIP guy who strikes out.
"""

# =============================================================================
# MYTH #5: STOLEN BASES ARE VALUABLE (EARLY DRAFT)
# =============================================================================
STOLEN_BASE_MYTH = """
MYTH: "I need to draft a speed guy early for SBs"

REALITY:
- Breakeven success rate: 70% (below that = negative value)
- BLJ X scoring: SB = 1.9 pts, CS = -2.8 pts
- You need 60%+ success rate just to break even!
- SB leaders are volatile year-to-year

WHY: Steals are high variance, low reward
- HR leaders are predictable (same guys every year)
- SB leaders change constantly
- Late-round speedsters emerge on waivers

EDGE: Don't pay for speed early.
Target everyday players who chip in 10-15 SBs later.
The elite speed guys will bust or the unknown ones will emerge.

BLJ X SPECIFIC: At 1.9 pts per SB, a stolen base is worth
less than a walk (3 pts). Prioritize OBP over speed.
"""

# =============================================================================
# MYTH #6: CLOSERS ARE WORTH PAYING FOR
# =============================================================================
CLOSER_MYTH = """
MYTH: "I need elite closers for saves"

REALITY:
- Top 10 ADP closers: Only 4 returned top-20 value in 2024
- Closer is the MOST VOLATILE position in fantasy
- Role changes, injuries, blown saves, trades = chaos
- Ryan Helsley got 49 saves on a 83-win team (unsustainable)

WHY: Saves are team-dependent and role-dependent
- Good pitcher on bad team = no save chances
- Manager decisions change everything
- Injuries are rampant

BLJ X SPECIFIC:
- SV = 11 pts, HLD = 9 pts (holds are almost as good!)
- A setup man with 25 holds = 225 pts
- A closer with 30 saves = 330 pts
- But the setup man has NO role volatility

EDGE: Draft elite setup men (holds), stream closers.
Target guys like Devin Williams, Evan Phillips types.
"""

# =============================================================================
# MYTH #7: PLATOON SPLITS = SIT YOUR LEFTY VS LHP
# =============================================================================
PLATOON_MYTH = """
MYTH: "Always bench lefty hitters against lefty pitchers"

REALITY:
- 84% of RHH show platoon splits (real but expected)
- 92% of LHH show platoon splits (slightly more)
- BUT: The split is only ~70-115 OPS points
- Daily lineup decisions don't matter much

WHY: Platoon disadvantage is overrated in daily decisions
- Your LHH vs LHP is still probably better than your bench bat
- Plus they might face the bullpen (RHP) later
- Starting lineup =/= only ABs

EXCEPTIONS MATTER:
- Some hitters have REVERSE splits (hit same-hand better)
- Check the individual player, not just handedness

EDGE: Don't overthink daily platoon decisions.
Start your best hitters. Period.
"""

# =============================================================================
# MYTH #8: BATTING AVERAGE MATTERS IN POINTS LEAGUES
# =============================================================================
BATTING_AVG_MYTH = """
MYTH: "I need high-average hitters"

REALITY (for BLJ X specifically):
- Walk = 3 pts (no AB penalty)
- Single = 4.6 pts (5.6 H - 1 AB)
- Strikeout = -1 pt (just AB penalty)

This means:
- A walk is 65% as valuable as a single
- Kyle Schwarber (.199 BA, .357 OBP) is ELITE in your format
- A guy who goes 0-3 with 2 BB scores 6 pts
- A guy who goes 1-4 with 0 BB scores 4.6 pts

THE WALK GUY WON.

WHY: OBP > BA in any points league with walk scoring
- BA doesn't account for walks
- OBP does
- Your league rewards walks almost like hits

EDGE: Target low-BA, high-OBP guys that others undervalue.
Schwarber, Santana, Soto, anyone with .380+ OBP.
"""

# =============================================================================
# SUMMARY: EDGES FOR BLJ X
# =============================================================================
BLJ_X_EDGES = """
=== QUICK REFERENCE: BLJ X MARKET INEFFICIENCIES ===

DRAFTING:
1. TARGET high-OBP, low-BA hitters (walks = 3 pts)
2. AVOID paying for stolen bases (1.9 pts, volatile)
3. WAIT on catchers (don't panic-draft)
4. DRAFT elite setup men over mid-tier closers
5. IGNORE "position scarcity" panic

IN-SEASON:
6. BUY after cold streaks (no predictive value)
7. SELL after hot streaks if you can get value
8. STREAM pitchers at Coors (it's not that bad)
9. AVOID streaming at Yankee/Dodger Stadium
10. DON'T bench good hitters for platoon reasons

PITCHING:
11. HR ALLOWED IS DEATH (-13 pts)
12. Target ground ball pitchers
13. Avoid fly ball pitchers in HR-happy parks
14. Ks are valuable (+2 each)
15. Holds are almost as good as saves (9 vs 11)
"""

if __name__ == "__main__":
    print("=" * 60)
    print("FANTASY BASEBALL: MYTHS VS REALITY")
    print("=" * 60)

    myths = [
        ("COORS FIELD", COORS_MYTH),
        ("HOT STREAKS", HOT_STREAK_MYTH),
        ("POSITION SCARCITY", POSITION_SCARCITY_MYTH),
        ("BABIP REGRESSION", BABIP_MYTH),
        ("STOLEN BASES", STOLEN_BASE_MYTH),
        ("CLOSERS", CLOSER_MYTH),
        ("PLATOON SPLITS", PLATOON_MYTH),
        ("BATTING AVERAGE", BATTING_AVG_MYTH),
    ]

    for name, content in myths:
        print(f"\n{'='*60}")
        print(f"MYTH: {name}")
        print("=" * 60)
        print(content)

    print("\n" + "=" * 60)
    print(BLJ_X_EDGES)
