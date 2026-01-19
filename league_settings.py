"""
Big League Jew X - League Settings

2025 Season Configuration
League ID: 89318
"""

LEAGUE_INFO = {
    "id": "89318",
    "name": "Big League Jew X",
    "teams": 12,
    "scoring_type": "Head-to-Head Points",
    "draft_date": "Sun Mar 23 8:15pm EDT",
    "keeper_league": True,
    "max_acquisitions_per_week": 5,
    "waiver_time_days": 2,
    "waiver_type": "Continual rolling list",
    "daily_lineup_changes": True,
}

# Roster Positions
ROSTER = {
    "batters": ["C", "1B", "2B", "3B", "SS", "OF", "OF", "OF", "Util", "Util", "Util"],
    "pitchers": ["SP", "SP", "RP", "RP", "RP", "P", "P", "P"],
    "bench": 6,
    "il": 4,
    "na": 2,
}

# Batter Scoring
BATTER_SCORING = {
    "AB": -1,      # At Bats (penalty for outs!)
    "H": 5.6,      # Hits
    "2B": 2.9,     # Doubles (bonus on top of H)
    "3B": 5.7,     # Triples (bonus on top of H)
    "HR": 9.4,     # Home Runs (bonus on top of H)
    "SB": 1.9,     # Stolen Bases
    "CS": -2.8,    # Caught Stealing
    "BB": 3,       # Walks
    "HBP": 3,      # Hit By Pitch
    "A": 0.1,      # Assists
    "E": -0.1,     # Errors
}

# Pitcher Scoring
PITCHER_SCORING = {
    "IP": 5,       # Innings Pitched
    "SV": 11,      # Saves
    "HR": -13,     # Home Runs allowed (big penalty!)
    "BB": -3,      # Walks
    "HBP": -3,     # Hit Batters
    "K": 2,        # Strikeouts
    "HLD": 9,      # Holds (valuable!)
    "PICK": 0.2,   # Pickoffs
}

# Derived point values for common outcomes
POINT_VALUES = {
    # Batter outcomes (including AB penalty where applicable)
    "single": 5.6 - 1,           # 4.6 pts
    "double": 5.6 + 2.9 - 1,     # 7.5 pts
    "triple": 5.6 + 5.7 - 1,     # 10.3 pts
    "home_run": 5.6 + 9.4 - 1,   # 14.0 pts
    "walk": 3,                    # 3.0 pts (no AB)
    "hbp": 3,                     # 3.0 pts (no AB)
    "strikeout": -1,              # -1.0 pts (just AB)
    "groundout": -1,              # -1.0 pts (just AB)
    "flyout": -1,                 # -1.0 pts (just AB)
    "stolen_base": 1.9,           # 1.9 pts
    "caught_stealing": -2.8,      # -2.8 pts

    # Pitcher outcomes
    "clean_inning": 5,            # 5.0 pts (3 outs, no damage)
    "inning_3k": 5 + 6,           # 11.0 pts (3 K inning)
    "hr_allowed": -13,            # -13.0 pts (brutal)
    "walk_allowed": -3,           # -3.0 pts
    "save": 11,                   # 11.0 pts
    "hold": 9,                    # 9.0 pts
}

# Key insights for this scoring system
STRATEGY_NOTES = """
KEY INSIGHTS FOR BLJ X SCORING:

BATTERS:
- OBP is KING: Walks (3 pts) are nearly as valuable as singles (4.6 pts)
- Avoid free swingers: AB penalty (-1) hurts high K guys
- Power is rewarded: HR = 14 pts, 2B = 7.5 pts
- SB not super valuable: Only 1.9 pts, and CS costs 2.8
  -> Need 60%+ success rate for SB to be net positive

PITCHERS:
- AVOID HR-PRONE pitchers: -13 pts per HR is devastating
  -> One HR erases 2.5 innings of work
- Strikeouts very valuable: +2 per K
- Holds almost as good as saves: 9 vs 11 pts
  -> Elite setup men are valuable
- Ground ball pitchers preferred (avoid HRs)

STREAMING STRATEGY:
- Target pitchers facing weak lineups (fewer HR risk)
- Favor pitcher-friendly parks (less HR damage)
- High-K pitchers offset some risk
- Setup men in high-leverage situations = gold
"""


def calculate_batter_points(
    ab: int = 0,
    h: int = 0,
    doubles: int = 0,
    triples: int = 0,
    hr: int = 0,
    bb: int = 0,
    hbp: int = 0,
    sb: int = 0,
    cs: int = 0,
    assists: int = 0,
    errors: int = 0,
) -> float:
    """Calculate fantasy points for a batter's game."""
    points = 0
    points += ab * BATTER_SCORING["AB"]
    points += h * BATTER_SCORING["H"]
    points += doubles * BATTER_SCORING["2B"]
    points += triples * BATTER_SCORING["3B"]
    points += hr * BATTER_SCORING["HR"]
    points += bb * BATTER_SCORING["BB"]
    points += hbp * BATTER_SCORING["HBP"]
    points += sb * BATTER_SCORING["SB"]
    points += cs * BATTER_SCORING["CS"]
    points += assists * BATTER_SCORING["A"]
    points += errors * BATTER_SCORING["E"]
    return points


def calculate_pitcher_points(
    ip: float = 0,
    k: int = 0,
    bb: int = 0,
    hr: int = 0,
    hbp: int = 0,
    sv: int = 0,
    hld: int = 0,
    pick: int = 0,
) -> float:
    """Calculate fantasy points for a pitcher's game."""
    points = 0
    points += ip * PITCHER_SCORING["IP"]
    points += k * PITCHER_SCORING["K"]
    points += bb * PITCHER_SCORING["BB"]
    points += hr * PITCHER_SCORING["HR"]
    points += hbp * PITCHER_SCORING["HBP"]
    points += sv * PITCHER_SCORING["SV"]
    points += hld * PITCHER_SCORING["HLD"]
    points += pick * PITCHER_SCORING["PICK"]
    return points


if __name__ == "__main__":
    print("=== Big League Jew X Scoring Calculator ===\n")

    # Example batter games
    print("BATTER EXAMPLES:")
    print("-" * 40)

    # Great game: 2-4, HR, BB
    pts = calculate_batter_points(ab=4, h=2, hr=1, bb=1)
    print(f"2-4, HR, BB:           {pts:.1f} pts")

    # Good game: 3-5, 2B, SB
    pts = calculate_batter_points(ab=5, h=3, doubles=1, sb=1)
    print(f"3-5, 2B, SB:           {pts:.1f} pts")

    # Patient game: 1-2, 2 BB
    pts = calculate_batter_points(ab=2, h=1, bb=2)
    print(f"1-2, 2 BB:             {pts:.1f} pts")

    # Bad game: 0-4, CS
    pts = calculate_batter_points(ab=4, h=0, cs=1)
    print(f"0-4, CS:               {pts:.1f} pts")

    # Strikeout game: 0-5, 4 K
    pts = calculate_batter_points(ab=5, h=0)
    print(f"0-5 (collar):          {pts:.1f} pts")

    print("\n" + "=" * 40)
    print("\nPITCHER EXAMPLES:")
    print("-" * 40)

    # Quality start: 6 IP, 8 K, 2 BB, 0 HR
    pts = calculate_pitcher_points(ip=6, k=8, bb=2, hr=0)
    print(f"6 IP, 8 K, 2 BB:       {pts:.1f} pts")

    # Great start: 7 IP, 10 K, 1 BB, 0 HR
    pts = calculate_pitcher_points(ip=7, k=10, bb=1, hr=0)
    print(f"7 IP, 10 K, 1 BB:      {pts:.1f} pts")

    # Disaster: 4 IP, 3 K, 3 BB, 3 HR
    pts = calculate_pitcher_points(ip=4, k=3, bb=3, hr=3)
    print(f"4 IP, 3 K, 3 BB, 3 HR: {pts:.1f} pts")

    # Closer save: 1 IP, 2 K, SV
    pts = calculate_pitcher_points(ip=1, k=2, sv=1)
    print(f"1 IP, 2 K, SV:         {pts:.1f} pts")

    # Setup hold: 1 IP, 1 K, HLD
    pts = calculate_pitcher_points(ip=1, k=1, hld=1)
    print(f"1 IP, 1 K, HLD:        {pts:.1f} pts")

    # Blown save: 0.2 IP, 1 BB, 1 HR
    pts = calculate_pitcher_points(ip=0.67, k=0, bb=1, hr=1)
    print(f"0.2 IP, 1 BB, 1 HR:    {pts:.1f} pts")

    print("\n" + "=" * 40)
    print(STRATEGY_NOTES)
