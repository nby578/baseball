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

# Park factors (100 = neutral, >100 = hitter friendly)
PARK_FACTORS = {
    "COL": 115,  # Coors - avoid
    "CIN": 108, "PHI": 106, "TEX": 105, "BOS": 104,
    "MIL": 103, "ATL": 102, "NYY": 102, "CHC": 101,
    # Neutral
    "BAL": 100, "ARI": 100, "KC": 100, "MIN": 100, "STL": 100,
    "TOR": 99, "HOU": 99, "CLE": 99, "DET": 98,
    # Pitcher friendly (target)
    "LAD": 97, "SD": 96, "NYM": 96, "TB": 95,
    "SEA": 94, "SF": 93, "MIA": 92, "OAK": 91,
    "LAA": 95, "CHW": 98, "PIT": 97, "WSH": 98,
}


def calculate_streaming_score(
    opponent: str,
    is_home: bool,
    pitcher_era: float = 4.00,
    pitcher_k_rate: float = 0.22,
) -> tuple[float, dict]:
    """
    Calculate streaming score for a matchup.

    Higher score = better streaming option.

    Args:
        opponent: Opponent team abbreviation
        is_home: Whether pitcher is at home
        pitcher_era: Pitcher's ERA (lower = better)
        pitcher_k_rate: Pitcher's K rate (higher = better)

    Returns:
        (score, factors_dict)
    """
    factors = {}

    # Opponent offense factor (0-30 points)
    # Lower offensive rank = more points
    opp_rank = TEAM_OFFENSE_RANK.get(opponent, 70)
    opp_factor = max(0, 30 - (opp_rank - 45) * 0.5)
    factors['opponent'] = f"{opponent} offense: {opp_factor:.1f}/30"

    # Park factor (0-20 points)
    # Lower park factor = more points (pitcher friendly)
    park = PARK_FACTORS.get(opponent, 100)
    park_factor = max(0, 20 - (park - 90) * 0.8)
    factors['park'] = f"Park factor ({park}): {park_factor:.1f}/20"

    # Home advantage (0-5 points)
    home_factor = 5 if is_home else 0
    factors['home'] = f"Home: {home_factor}/5"

    # Pitcher quality (0-25 points)
    era_factor = max(0, 15 - (pitcher_era - 3.0) * 3)
    k_factor = min(10, pitcher_k_rate * 40)
    pitcher_factor = era_factor + k_factor
    factors['pitcher'] = f"Quality (ERA {pitcher_era}, K {pitcher_k_rate:.0%}): {pitcher_factor:.1f}/25"

    # Total score
    total = opp_factor + park_factor + home_factor + pitcher_factor
    factors['total'] = f"Total: {total:.1f}/80"

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
