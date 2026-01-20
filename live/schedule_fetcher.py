"""
MLB Schedule Fetcher for Fantasy Baseball Streaming

Fetches upcoming MLB games and probable starters from multiple sources:
- MLB Stats API (free, official)
- pybaseball schedule data

Provides day-by-day schedule with pitching matchups for streaming decisions.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backtesting"))

from stats_as_of import CumulativeStatsCalculator, TeamStatsCalculator


# Team abbreviation mappings (MLB API uses different codes)
MLB_API_TO_STANDARD = {
    "AZ": "ARI", "ARI": "ARI",
    "ATL": "ATL",
    "BAL": "BAL",
    "BOS": "BOS",
    "CHC": "CHC", "CHN": "CHC",
    "CWS": "CHW", "CHA": "CHW", "CHW": "CHW",
    "CIN": "CIN",
    "CLE": "CLE",
    "COL": "COL",
    "DET": "DET",
    "HOU": "HOU",
    "KC": "KC", "KCA": "KC",
    "LAA": "LAA", "ANA": "LAA",
    "LAD": "LAD", "LAN": "LAD",
    "MIA": "MIA", "FLA": "MIA",
    "MIL": "MIL",
    "MIN": "MIN",
    "NYM": "NYM", "NYN": "NYM",
    "NYY": "NYY", "NYA": "NYY",
    "OAK": "OAK", "ATH": "OAK",
    "PHI": "PHI",
    "PIT": "PIT",
    "SD": "SD", "SDP": "SD",
    "SF": "SF", "SFG": "SF", "SFN": "SF",
    "SEA": "SEA",
    "STL": "STL", "SLN": "STL",
    "TB": "TB", "TBR": "TB", "TBA": "TB",
    "TEX": "TEX",
    "TOR": "TOR",
    "WSH": "WAS", "WAS": "WAS", "WSN": "WAS",
}

# MLB API team IDs
MLB_TEAM_IDS = {
    "ARI": 109, "ATL": 144, "BAL": 110, "BOS": 111, "CHC": 112,
    "CHW": 145, "CIN": 113, "CLE": 114, "COL": 115, "DET": 116,
    "HOU": 117, "KC": 118, "LAA": 108, "LAD": 119, "MIA": 146,
    "MIL": 158, "MIN": 142, "NYM": 121, "NYY": 147, "OAK": 133,
    "PHI": 143, "PIT": 134, "SD": 135, "SF": 137, "SEA": 136,
    "STL": 138, "TB": 139, "TEX": 140, "TOR": 141, "WAS": 120,
}

# Reverse lookup
TEAM_ID_TO_ABBREV = {v: k for k, v in MLB_TEAM_IDS.items()}


@dataclass
class ProbableStarter:
    """A probable starting pitcher for a game."""
    pitcher_name: str
    pitcher_id: Optional[int] = None  # MLB player ID
    team: str = ""
    opponent: str = ""
    game_date: str = ""
    game_time: str = ""
    home_away: str = ""  # "home" or "away"
    park: str = ""  # Where game is played

    # Stats (filled in later)
    k_bb_pct: Optional[float] = None
    era: Optional[float] = None
    ip: Optional[float] = None


@dataclass
class ScheduledGame:
    """A scheduled MLB game with both probable starters."""
    game_id: int
    game_date: str
    game_time: str
    home_team: str
    away_team: str
    venue: str
    home_starter: Optional[ProbableStarter] = None
    away_starter: Optional[ProbableStarter] = None
    game_status: str = "scheduled"  # scheduled, in_progress, final


class MLBScheduleFetcher:
    """
    Fetches MLB schedule and probable starters from MLB Stats API.

    MLB Stats API is free and doesn't require authentication.
    Base URL: https://statsapi.mlb.com/api/v1/
    """

    BASE_URL = "https://statsapi.mlb.com/api/v1"

    def __init__(self, season: int = 2025):
        self.season = season
        self._cache_dir = Path(__file__).parent / "cache"
        self._cache_dir.mkdir(exist_ok=True)

    def get_schedule(self, start_date: str, end_date: str = None) -> List[ScheduledGame]:
        """
        Get MLB schedule with probable starters for date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to start_date

        Returns:
            List of ScheduledGame objects
        """
        if end_date is None:
            end_date = start_date

        url = f"{self.BASE_URL}/schedule"
        params = {
            "sportId": 1,  # MLB
            "startDate": start_date,
            "endDate": end_date,
            "hydrate": "probablePitcher,venue,team",
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []

        games = []
        for date_entry in data.get("dates", []):
            game_date = date_entry.get("date", "")

            for game_data in date_entry.get("games", []):
                game = self._parse_game(game_data, game_date)
                if game:
                    games.append(game)

        return games

    def _parse_game(self, game_data: Dict, game_date: str) -> Optional[ScheduledGame]:
        """Parse a single game from MLB API response."""
        try:
            game_id = game_data.get("gamePk", 0)

            # Get teams
            teams = game_data.get("teams", {})
            home_data = teams.get("home", {})
            away_data = teams.get("away", {})

            home_team_data = home_data.get("team", {})
            away_team_data = away_data.get("team", {})

            home_abbrev = home_team_data.get("abbreviation", "")
            away_abbrev = away_team_data.get("abbreviation", "")

            # Normalize abbreviations
            home_team = MLB_API_TO_STANDARD.get(home_abbrev, home_abbrev)
            away_team = MLB_API_TO_STANDARD.get(away_abbrev, away_abbrev)

            # Get venue
            venue_data = game_data.get("venue", {})
            venue = venue_data.get("name", "")

            # Get game time
            game_datetime = game_data.get("gameDate", "")
            game_time = ""
            if game_datetime:
                try:
                    dt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00"))
                    game_time = dt.strftime("%I:%M %p")
                except:
                    pass

            # Get status
            status_data = game_data.get("status", {})
            status = status_data.get("abstractGameState", "scheduled").lower()

            # Create game
            game = ScheduledGame(
                game_id=game_id,
                game_date=game_date,
                game_time=game_time,
                home_team=home_team,
                away_team=away_team,
                venue=venue,
                game_status=status,
            )

            # Get probable starters
            home_pitcher_data = home_data.get("probablePitcher", {})
            away_pitcher_data = away_data.get("probablePitcher", {})

            if home_pitcher_data:
                game.home_starter = ProbableStarter(
                    pitcher_name=home_pitcher_data.get("fullName", "TBD"),
                    pitcher_id=home_pitcher_data.get("id"),
                    team=home_team,
                    opponent=away_team,
                    game_date=game_date,
                    game_time=game_time,
                    home_away="home",
                    park=home_team,  # Home team's park
                )

            if away_pitcher_data:
                game.away_starter = ProbableStarter(
                    pitcher_name=away_pitcher_data.get("fullName", "TBD"),
                    pitcher_id=away_pitcher_data.get("id"),
                    team=away_team,
                    opponent=home_team,
                    game_date=game_date,
                    game_time=game_time,
                    home_away="away",
                    park=home_team,  # Games played at home team's park
                )

            return game

        except Exception as e:
            print(f"Error parsing game: {e}")
            return None

    def get_week_schedule(self, start_date: str = None) -> Dict[str, List[ScheduledGame]]:
        """
        Get full week of games starting from date.

        Args:
            start_date: Start of week (YYYY-MM-DD), defaults to today

        Returns:
            Dict mapping date strings to list of games
        """
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")

        # Parse start date
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=6)
        end_date = end.strftime("%Y-%m-%d")

        # Fetch all games for the week
        all_games = self.get_schedule(start_date, end_date)

        # Group by date
        schedule_by_date = {}
        for game in all_games:
            date_key = game.game_date
            if date_key not in schedule_by_date:
                schedule_by_date[date_key] = []
            schedule_by_date[date_key].append(game)

        return schedule_by_date

    def get_all_starters(self, start_date: str, end_date: str = None) -> List[ProbableStarter]:
        """
        Get all probable starters for date range as flat list.

        Useful for streaming decisions - shows all pitching options.
        """
        games = self.get_schedule(start_date, end_date)

        starters = []
        for game in games:
            if game.home_starter:
                starters.append(game.home_starter)
            if game.away_starter:
                starters.append(game.away_starter)

        return starters

    def get_team_schedule(self, team: str, start_date: str, end_date: str = None) -> List[ScheduledGame]:
        """Get schedule for a specific team."""
        games = self.get_schedule(start_date, end_date)

        team = MLB_API_TO_STANDARD.get(team, team)
        team_games = [g for g in games if g.home_team == team or g.away_team == team]

        return team_games

    def enrich_starters_with_stats(
        self,
        starters: List[ProbableStarter],
        stats_calculator: CumulativeStatsCalculator = None
    ) -> List[ProbableStarter]:
        """
        Add season stats to probable starters.

        Args:
            starters: List of ProbableStarter objects
            stats_calculator: Optional stats calculator (creates one if not provided)

        Returns:
            Same starters with stats filled in
        """
        if stats_calculator is None:
            stats_calculator = CumulativeStatsCalculator(self.season)

        for starter in starters:
            if starter.pitcher_name and starter.pitcher_name != "TBD":
                stats = stats_calculator.get_pitcher_stats_through(
                    starter.pitcher_name,
                    starter.game_date,
                    use_game_logs=False  # Use season stats for speed
                )
                if stats:
                    starter.k_bb_pct = stats.get("k_bb_pct")
                    starter.era = stats.get("era")
                    starter.ip = stats.get("ip")

        return starters

    def print_schedule(self, games: List[ScheduledGame]):
        """Pretty print schedule."""
        if not games:
            print("No games found.")
            return

        current_date = None
        for game in sorted(games, key=lambda g: (g.game_date, g.game_time)):
            if game.game_date != current_date:
                current_date = game.game_date
                print(f"\n{'='*60}")
                print(f"  {current_date}")
                print(f"{'='*60}")

            home_sp = game.home_starter.pitcher_name if game.home_starter else "TBD"
            away_sp = game.away_starter.pitcher_name if game.away_starter else "TBD"

            print(f"\n  {game.away_team} @ {game.home_team} ({game.game_time})")
            print(f"    Away: {away_sp}")
            print(f"    Home: {home_sp}")
            print(f"    Venue: {game.venue}")


def demo():
    """Demo the schedule fetcher."""
    fetcher = MLBScheduleFetcher(season=2025)

    # Get this week's schedule
    today = datetime.now()

    # If it's offseason, use a date during the season for demo
    # 2025 season starts ~late March
    if today.month < 3 or (today.month == 3 and today.day < 20):
        print("Note: MLB season hasn't started. Using sample schedule from Opening Day.")
        start_date = "2025-03-27"  # Approximate Opening Day 2025
    else:
        start_date = today.strftime("%Y-%m-%d")

    print(f"\nFetching MLB schedule starting {start_date}...")

    # Get week of games
    week_schedule = fetcher.get_week_schedule(start_date)

    total_games = sum(len(games) for games in week_schedule.values())
    print(f"Found {total_games} games across {len(week_schedule)} days")

    # Print schedule
    all_games = []
    for date, games in sorted(week_schedule.items()):
        all_games.extend(games)

    fetcher.print_schedule(all_games[:20])  # Show first 20 games

    # Get all starters
    print(f"\n\n{'='*60}")
    print("ALL PROBABLE STARTERS THIS WEEK")
    print(f"{'='*60}")

    end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
    starters = fetcher.get_all_starters(start_date, end_date)

    # Count by team
    team_counts = {}
    tbd_count = 0
    for sp in starters:
        if sp.pitcher_name == "TBD":
            tbd_count += 1
        else:
            team_counts[sp.team] = team_counts.get(sp.team, 0) + 1

    print(f"\nProbable starters by team:")
    for team in sorted(team_counts.keys()):
        print(f"  {team}: {team_counts[team]} starts")

    print(f"\n  TBD: {tbd_count} starts")
    print(f"  Total: {len(starters)} starts")


if __name__ == "__main__":
    demo()
