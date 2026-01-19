"""
Streaming Pitcher Ranker

Ranks available pitchers by matchup quality for streaming.
Factors: opponent wRC+, park factor, recent form, handedness splits.
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from mlb_api import get_todays_games, TEAM_IDS


@dataclass
class StreamingCandidate:
    """A pitcher available for streaming."""
    name: str
    team: str
    opponent: str
    is_home: bool
    score: float = 0.0
    factors: dict = None


# Team offensive rankings (lower = easier matchup)
# Based on typical wRC+ - update with real data during season
TEAM_OFFENSE_RANK = {
    # Elite offenses (avoid)
    "LAD": 95, "ATL": 93, "TEX": 90, "PHI": 88, "BAL": 87,
    # Good offenses
    "NYY": 85, "TB": 84, "HOU": 83, "MIN": 82, "TOR": 81,
    "ARI": 80, "SEA": 79, "SD": 78, "MIL": 77, "CIN": 76,
    # Average offenses
    "SF": 75, "BOS": 74, "STL": 73, "CLE": 72, "KC": 71,
    "NYM": 70, "CHC": 69, "DET": 68, "LAA": 67, "MIA": 66,
    # Weak offenses (target)
    "PIT": 60, "WSH": 58, "COL": 55, "OAK": 50, "CHW": 45,
}

# Park factors for RUNS (100 = neutral, >100 = hitter friendly)
# Note: For BLJ X, we care more about HR factor than run factor
PARK_FACTORS = {
    "COL": 128,  # Coors - HIGH runs but HR factor only 106!
    "CIN": 108, "PHI": 109, "TEX": 105, "BOS": 104,
    "MIL": 103, "ATL": 102, "NYY": 113, "CHC": 101,
    # Neutral
    "BAL": 100, "ARI": 100, "KC": 100, "MIN": 100, "STL": 100,
    "TOR": 99, "HOU": 99, "CLE": 99, "DET": 98,
    # Pitcher friendly
    "LAD": 105, "SD": 96, "NYM": 96, "TB": 95,
    "SEA": 94, "SF": 92, "MIA": 92, "OAK": 91,
    "LAA": 95, "CHW": 98, "PIT": 97, "WSH": 98,
}

# HR-specific park factors - THIS IS WHAT MATTERS FOR BLJ X (-13 per HR!)
# Source: Baseball Savant 2023-2025 rolling average
PARK_HR_FACTORS = {
    # HR DANGER ZONES (avoid streaming here)
    "LAD": 127,  # Dodger Stadium - worst for HRs!
    "NYY": 119,  # Yankee Stadium - short porch
    "MIA": 118,  # loanDepot park
    "PHI": 114,  # Citizens Bank
    "LAA": 113,  # Angel Stadium
    "CIN": 112,  # Great American
    "TEX": 110,  # Globe Life
    # NEUTRAL
    "COL": 106,  # Coors - SURPRISINGLY SAFE! Big outfield
    "CHC": 105, "ATL": 104, "BAL": 103, "MIL": 102,
    "ARI": 101, "KC": 100, "MIN": 100, "HOU": 99,
    "TOR": 98, "DET": 97, "WSH": 96, "TB": 95,
    # HR SAFE ZONES (target for streaming)
    "BOS": 94,   # Fenway - wall robs HRs
    "SEA": 92,   # T-Mobile
    "NYM": 90,   # Citi Field
    "SD": 88,    # Petco
    "STL": 87,   # Busch
    "CHW": 86,   # Guaranteed Rate
    "CLE": 85,   # Progressive
    "SF": 82,    # Oracle - pitcher's park
    "OAK": 80,   # Coliseum - deep fences
    "PIT": 76,   # PNC Park - safest!
}

# Team HR rate (HR/PA) - CRITICAL for BLJ X scoring (-13 per HR!)
# Lower = safer to stream against
TEAM_HR_RATE = {
    # High HR teams (AVOID - they'll crush you with -13 per HR)
    "NYY": 0.042, "LAD": 0.040, "ATL": 0.039, "BAL": 0.038, "PHI": 0.037,
    "TEX": 0.036, "HOU": 0.035, "SEA": 0.034, "ARI": 0.033, "TOR": 0.032,
    # Average HR teams
    "MIN": 0.031, "CIN": 0.030, "TB": 0.030, "SD": 0.029, "MIL": 0.029,
    "SF": 0.028, "BOS": 0.028, "STL": 0.027, "CLE": 0.027, "KC": 0.026,
    # Low HR teams (TARGET - safer for your -13 HR penalty)
    "NYM": 0.025, "CHC": 0.025, "DET": 0.024, "LAA": 0.024, "MIA": 0.023,
    "PIT": 0.022, "WSH": 0.021, "COL": 0.028, "OAK": 0.019, "CHW": 0.018,
}

# Team K rate (K/PA) - Higher = more points from Ks
TEAM_K_RATE = {
    # High K teams (TARGET - extra K points)
    "OAK": 0.27, "CHW": 0.26, "DET": 0.25, "ARI": 0.25, "MIA": 0.24,
    "PIT": 0.24, "TEX": 0.24, "TB": 0.23, "SEA": 0.23, "LAA": 0.23,
    # Average K teams
    "CIN": 0.22, "CHC": 0.22, "BAL": 0.22, "MIL": 0.22, "STL": 0.22,
    "BOS": 0.21, "TOR": 0.21, "MIN": 0.21, "WSH": 0.21, "PHI": 0.21,
    # Low K teams (less K upside)
    "NYM": 0.20, "SF": 0.20, "HOU": 0.20, "CLE": 0.19, "SD": 0.19,
    "KC": 0.19, "NYY": 0.18, "LAD": 0.18, "ATL": 0.18, "COL": 0.20,
}


def calculate_streaming_score(
    opponent: str,
    is_home: bool,
    pitcher_era: float = 4.00,
    pitcher_k_rate: float = 0.22,
    blj_scoring: bool = True,
) -> tuple[float, dict]:
    """
    Calculate streaming score for a matchup.

    Higher score = better streaming option.
    Optimized for BLJ X scoring: -13 per HR, +2 per K

    Args:
        opponent: Opponent team abbreviation
        is_home: Whether pitcher is at home
        pitcher_era: Pitcher's ERA (lower = better)
        pitcher_k_rate: Pitcher's K rate (higher = better)
        blj_scoring: Use BLJ X scoring weights (HR/K emphasis)

    Returns:
        (score, factors_dict)
    """
    factors = {}

    # Opponent offense factor (0-20 points)
    opp_rank = TEAM_OFFENSE_RANK.get(opponent, 70)
    opp_factor = max(0, 20 - (opp_rank - 45) * 0.4)
    factors['opponent'] = f"{opponent} offense: {opp_factor:.1f}/20"

    # HR Park factor (0-15 points) - USE HR FACTOR, NOT RUN FACTOR!
    park_hr = PARK_HR_FACTORS.get(opponent, 100)
    # Scale: 76 (PNC, safest) -> 15 pts, 127 (LAD, worst) -> 0 pts
    park_factor = max(0, 15 - (park_hr - 76) * 0.29)
    factors['park'] = f"HR Park ({park_hr}): {park_factor:.1f}/15"

    # Home advantage (0-5 points)
    home_factor = 5 if is_home else 0
    factors['home'] = f"Home: {home_factor}/5"

    if blj_scoring:
        # HR RATE FACTOR (0-25 points) - CRITICAL for -13 HR penalty!
        # Lower HR rate = much safer stream
        hr_rate = TEAM_HR_RATE.get(opponent, 0.028)
        # Scale: 0.018 (best) -> 25 pts, 0.042 (worst) -> 0 pts
        hr_factor = max(0, 25 - (hr_rate - 0.018) * 1000)
        factors['hr_safety'] = f"HR safety ({hr_rate:.1%}): {hr_factor:.1f}/25"

        # K RATE FACTOR (0-15 points) - Bonus for high-K opponents
        k_rate = TEAM_K_RATE.get(opponent, 0.22)
        # Scale: 0.27 (best) -> 15 pts, 0.18 (worst) -> 0 pts
        k_upside = max(0, (k_rate - 0.18) * 167)
        factors['k_upside'] = f"K upside ({k_rate:.0%}): {k_upside:.1f}/15"

        # Pitcher quality (0-20 points)
        era_factor = max(0, 10 - (pitcher_era - 3.0) * 2.5)
        pitcher_k = min(10, pitcher_k_rate * 35)
        pitcher_factor = era_factor + pitcher_k
        factors['pitcher'] = f"Pitcher: {pitcher_factor:.1f}/20"

        # Total score (max 100)
        total = opp_factor + park_factor + home_factor + hr_factor + k_upside + pitcher_factor
        factors['total'] = f"Total: {total:.1f}/100"
    else:
        # Standard scoring (old formula)
        era_factor = max(0, 15 - (pitcher_era - 3.0) * 3)
        k_factor = min(10, pitcher_k_rate * 40)
        pitcher_factor = era_factor + k_factor
        factors['pitcher'] = f"Quality: {pitcher_factor:.1f}/25"

        total = opp_factor + park_factor + home_factor + pitcher_factor
        factors['total'] = f"Total: {total:.1f}/65"

    return total, factors


def get_streaming_targets(
    available_pitchers: list[dict] = None,
    min_score: float = 40.0,
) -> list[StreamingCandidate]:
    """
    Get ranked streaming targets for today.

    Args:
        available_pitchers: List of available pitchers with stats
                          [{"name": str, "team": str, "era": float, "k_rate": float}]
        min_score: Minimum score to include

    Returns:
        Sorted list of StreamingCandidate
    """
    todays_games = get_todays_games()

    candidates = []

    for game in todays_games:
        if game['status'] not in ['Scheduled', 'Pre-Game', 'Warmup']:
            continue

        # Home pitcher vs away team
        if game['home_pitcher'] != 'TBD':
            score, factors = calculate_streaming_score(
                opponent=game['away_abbrev'],
                is_home=True,
            )
            if score >= min_score:
                candidates.append(StreamingCandidate(
                    name=game['home_pitcher'],
                    team=game['home_abbrev'],
                    opponent=f"vs {game['away_abbrev']}",
                    is_home=True,
                    score=score,
                    factors=factors,
                ))

        # Away pitcher vs home team
        if game['away_pitcher'] != 'TBD':
            score, factors = calculate_streaming_score(
                opponent=game['home_abbrev'],
                is_home=False,
            )
            if score >= min_score:
                candidates.append(StreamingCandidate(
                    name=game['away_pitcher'],
                    team=game['away_abbrev'],
                    opponent=f"@ {game['home_abbrev']}",
                    is_home=False,
                    score=score,
                    factors=factors,
                ))

    # Sort by score descending
    candidates.sort(key=lambda x: x.score, reverse=True)

    return candidates


def rank_opponents_for_week(start_date: str = None) -> list[tuple[str, float]]:
    """
    Rank opponents by ease of matchup for the week.

    Returns:
        List of (team_abbrev, average_score) sorted best to worst
    """
    scores = []
    for team, offense in TEAM_OFFENSE_RANK.items():
        park = PARK_FACTORS.get(team, 100)
        # Simple score: prioritize weak offense + pitcher park
        score = (100 - offense) + (110 - park)
        scores.append((team, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


if __name__ == "__main__":
    print("=== Streaming Pitcher Ranker ===\n")

    # Test scoring
    print("Matchup Score Examples:")
    print("-" * 50)

    test_matchups = [
        ("vs OAK", "OAK", True),
        ("vs CHW", "CHW", True),
        ("@ COL", "COL", False),  # Coors - bad
        ("vs LAD", "LAD", True),  # Good offense - bad
        ("@ MIA", "MIA", False),  # Pitcher park - good
    ]

    for label, opp, is_home in test_matchups:
        score, factors = calculate_streaming_score(opp, is_home)
        print(f"\n{label}:")
        for k, v in factors.items():
            print(f"  {v}")

    print("\n" + "=" * 50)
    print("\nBest Opponents to Stream Against (all season):")
    print("-" * 50)

    ranked = rank_opponents_for_week()
    for i, (team, score) in enumerate(ranked[:10], 1):
        offense = TEAM_OFFENSE_RANK.get(team, 70)
        park = PARK_FACTORS.get(team, 100)
        print(f"  {i:2}. {team} (Offense: {offense}, Park: {park}) - Score: {score:.0f}")

    print("\n" + "=" * 50)
    print("\nWorst Opponents (avoid streaming):")
    print("-" * 50)

    for team, score in ranked[-5:]:
        offense = TEAM_OFFENSE_RANK.get(team, 70)
        park = PARK_FACTORS.get(team, 100)
        print(f"  {team} (Offense: {offense}, Park: {park}) - Score: {score:.0f}")

    print("\n" + "=" * 50)
    print("\nChecking Today's Streaming Options...")
    print("-" * 50)

    candidates = get_streaming_targets(min_score=30.0)
    if candidates:
        print(f"\nFound {len(candidates)} streaming candidates:\n")
        for i, c in enumerate(candidates[:10], 1):
            print(f"  {i:2}. {c.name} ({c.team}) {c.opponent}")
            print(f"      Score: {c.score:.1f}")
    else:
        print("  No games found (offseason or no scheduled games)")
