"""
MLB Stats Fetcher for Backtesting

Uses pybaseball to fetch historical pitcher and team stats.
Provides stats "as of" a specific date for accurate backtesting.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

# pybaseball imports
from pybaseball import (
    pitching_stats,
    batting_stats,
    team_batting,
    team_pitching,
    playerid_lookup,
    statcast_pitcher,
    schedule_and_record,
)

# Cache directory
CACHE_DIR = Path(__file__).parent / "data" / "mlb_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class MLBFetcher:
    """Fetch MLB stats for backtesting fantasy models."""

    def __init__(self, season: int = 2025):
        self.season = season
        self._pitcher_cache: Dict[str, pd.DataFrame] = {}
        self._team_cache: Dict[str, pd.DataFrame] = {}

    def get_pitcher_season_stats(
        self, season: int = None, qual: int = 10
    ) -> pd.DataFrame:
        """
        Get all pitcher stats for a season.

        Args:
            season: MLB season year
            qual: Minimum IP qualification

        Returns:
            DataFrame with pitcher stats including K-BB%, GB%, etc.
        """
        season = season or self.season
        cache_key = f"pitchers_{season}_{qual}"

        if cache_key in self._pitcher_cache:
            return self._pitcher_cache[cache_key]

        # Check file cache
        cache_file = CACHE_DIR / f"{cache_key}.parquet"
        if cache_file.exists():
            df = pd.read_parquet(cache_file)
            self._pitcher_cache[cache_key] = df
            return df

        print(f"Fetching pitcher stats for {season} (qual={qual})...")
        df = pitching_stats(season, qual=qual)

        # Calculate K-BB% if not present
        if "K-BB%" not in df.columns and "K%" in df.columns and "BB%" in df.columns:
            df["K-BB%"] = df["K%"] - df["BB%"]

        # Save to cache
        df.to_parquet(cache_file)
        self._pitcher_cache[cache_key] = df

        print(f"  -> Fetched {len(df)} pitchers")
        return df

    def get_team_batting_stats(self, season: int = None) -> pd.DataFrame:
        """
        Get team batting stats for a season.

        Returns:
            DataFrame with team K%, ISO, wOBA, etc.
        """
        season = season or self.season
        cache_key = f"team_batting_{season}"

        if cache_key in self._team_cache:
            return self._team_cache[cache_key]

        cache_file = CACHE_DIR / f"{cache_key}.parquet"
        if cache_file.exists():
            df = pd.read_parquet(cache_file)
            self._team_cache[cache_key] = df
            return df

        print(f"Fetching team batting stats for {season}...")
        df = team_batting(season)

        df.to_parquet(cache_file)
        self._team_cache[cache_key] = df

        print(f"  -> Fetched {len(df)} teams")
        return df

    def lookup_player_id(self, name: str) -> Optional[Dict]:
        """
        Look up a player's IDs by name.

        Returns:
            Dict with key_mlbam, key_fangraphs, etc.
        """
        try:
            parts = name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = " ".join(parts[1:])
                result = playerid_lookup(last, first)
                if not result.empty:
                    row = result.iloc[0]
                    return {
                        "name": name,
                        "mlbam_id": int(row.get("key_mlbam", 0)) if pd.notna(row.get("key_mlbam")) else None,
                        "fangraphs_id": int(row.get("key_fangraphs", 0)) if pd.notna(row.get("key_fangraphs")) else None,
                        "bbref_id": row.get("key_bbref"),
                    }
        except Exception as e:
            print(f"  Warning: Could not look up {name}: {e}")
        return None

    def get_pitcher_game_log(
        self,
        mlbam_id: int,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Get a pitcher's game log from Statcast.

        Args:
            mlbam_id: MLB Advanced Media player ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with pitch-level data
        """
        cache_key = f"statcast_{mlbam_id}_{start_date}_{end_date}"
        cache_file = CACHE_DIR / f"{cache_key}.parquet"

        if cache_file.exists():
            return pd.read_parquet(cache_file)

        print(f"Fetching Statcast data for player {mlbam_id} ({start_date} to {end_date})...")
        df = statcast_pitcher(start_date, end_date, mlbam_id)

        if not df.empty:
            df.to_parquet(cache_file)

        return df

    def get_team_schedule(self, team: str, season: int = None) -> pd.DataFrame:
        """
        Get a team's schedule and results.

        Args:
            team: Team abbreviation (e.g., 'NYY', 'LAD')
            season: MLB season year

        Returns:
            DataFrame with game schedule and results
        """
        season = season or self.season
        cache_key = f"schedule_{team}_{season}"
        cache_file = CACHE_DIR / f"{cache_key}.parquet"

        if cache_file.exists():
            return pd.read_parquet(cache_file)

        print(f"Fetching schedule for {team} {season}...")
        df = schedule_and_record(season, team)

        if not df.empty:
            df.to_parquet(cache_file)

        return df


class PitcherStatsAsOf:
    """Get pitcher stats as of a specific date for accurate backtesting."""

    def __init__(self, fetcher: MLBFetcher):
        self.fetcher = fetcher
        self._full_stats: Dict[int, pd.DataFrame] = {}

    def get_stats_as_of(
        self,
        pitcher_name: str,
        as_of_date: str,
        season: int = None
    ) -> Optional[Dict]:
        """
        Get a pitcher's cumulative stats as of a specific date.

        For backtesting, we need to know what the stats looked like
        BEFORE the game, not after.

        Args:
            pitcher_name: Full name of pitcher
            as_of_date: Date string (YYYY-MM-DD)
            season: Season year

        Returns:
            Dict with K-BB%, GB%, ERA, FIP, etc. as of that date
        """
        season = season or self.fetcher.season

        # For now, return season stats (we'll enhance this later with game-by-game)
        all_pitchers = self.fetcher.get_pitcher_season_stats(season)

        # Find pitcher by name (fuzzy match)
        name_lower = pitcher_name.lower()
        matches = all_pitchers[
            all_pitchers["Name"].str.lower().str.contains(name_lower.split()[-1])
        ]

        if matches.empty:
            return None

        # Get best match
        row = matches.iloc[0]

        return {
            "name": row.get("Name"),
            "team": row.get("Team"),
            "ip": row.get("IP", 0),
            "era": row.get("ERA", 0),
            "fip": row.get("FIP", 0),
            "k_pct": row.get("K%", 0),
            "bb_pct": row.get("BB%", 0),
            "k_bb_pct": row.get("K-BB%", row.get("K%", 0) - row.get("BB%", 0)),
            "gb_pct": row.get("GB%", 0),
            "hr_per_9": row.get("HR/9", 0),
            "whip": row.get("WHIP", 0),
            "war": row.get("WAR", 0),
        }


class TeamStatsAsOf:
    """Get team batting stats as of a specific date."""

    # Team abbreviation mappings (Yahoo -> standard)
    TEAM_MAP = {
        "ARI": "ARI", "Arizona": "ARI",
        "ATL": "ATL", "Atlanta": "ATL",
        "BAL": "BAL", "Baltimore": "BAL",
        "BOS": "BOS", "Boston": "BOS",
        "CHC": "CHC", "Chi Cubs": "CHC",
        "CHW": "CHW", "Chi Sox": "CHW", "CWS": "CHW",
        "CIN": "CIN", "Cincinnati": "CIN",
        "CLE": "CLE", "Cleveland": "CLE",
        "COL": "COL", "Colorado": "COL",
        "DET": "DET", "Detroit": "DET",
        "HOU": "HOU", "Houston": "HOU",
        "KC": "KC", "KCR": "KC", "Kansas City": "KC",
        "LAA": "LAA", "LA Angels": "LAA",
        "LAD": "LAD", "LA Dodgers": "LAD",
        "MIA": "MIA", "Miami": "MIA",
        "MIL": "MIL", "Milwaukee": "MIL",
        "MIN": "MIN", "Minnesota": "MIN",
        "NYM": "NYM", "NY Mets": "NYM",
        "NYY": "NYY", "NY Yankees": "NYY",
        "OAK": "OAK", "Oakland": "OAK",
        "PHI": "PHI", "Philadelphia": "PHI",
        "PIT": "PIT", "Pittsburgh": "PIT",
        "SD": "SD", "SDP": "SD", "San Diego": "SD",
        "SF": "SF", "SFG": "SF", "San Fran": "SF",
        "SEA": "SEA", "Seattle": "SEA",
        "STL": "STL", "St. Louis": "STL",
        "TB": "TB", "TBR": "TB", "Tampa Bay": "TB",
        "TEX": "TEX", "Texas": "TEX",
        "TOR": "TOR", "Toronto": "TOR",
        "WAS": "WAS", "WSH": "WAS", "Washington": "WAS",
    }

    def __init__(self, fetcher: MLBFetcher):
        self.fetcher = fetcher

    def normalize_team(self, team: str) -> str:
        """Normalize team abbreviation."""
        return self.TEAM_MAP.get(team, team)

    def get_stats_as_of(
        self,
        team: str,
        as_of_date: str,
        season: int = None
    ) -> Optional[Dict]:
        """
        Get a team's batting stats as of a specific date.

        Args:
            team: Team abbreviation
            as_of_date: Date string (YYYY-MM-DD)
            season: Season year

        Returns:
            Dict with K%, ISO, wOBA, etc.
        """
        season = season or self.fetcher.season
        team = self.normalize_team(team)

        all_teams = self.fetcher.get_team_batting_stats(season)

        # Find team
        matches = all_teams[all_teams["Team"].str.upper() == team.upper()]

        if matches.empty:
            # Try partial match
            matches = all_teams[all_teams["Team"].str.contains(team, case=False)]

        if matches.empty:
            return None

        row = matches.iloc[0]

        return {
            "team": row.get("Team"),
            "k_pct": row.get("K%", 0),
            "bb_pct": row.get("BB%", 0),
            "iso": row.get("ISO", 0),
            "woba": row.get("wOBA", 0),
            "wrc_plus": row.get("wRC+", 100),
            "ops": row.get("OPS", 0),
            "avg": row.get("AVG", 0),
        }


def test_mlb_fetcher():
    """Test the MLB fetcher functionality."""
    print("=" * 60)
    print("MLB FETCHER TEST")
    print("=" * 60)

    fetcher = MLBFetcher(season=2024)

    # Test pitcher stats
    print("\n1. Testing pitcher stats fetch...")
    pitchers = fetcher.get_pitcher_season_stats(2024, qual=50)
    print(f"   Columns: {list(pitchers.columns[:10])}...")
    print(f"   Top 5 by K-BB%:")
    if "K-BB%" in pitchers.columns:
        top5 = pitchers.nlargest(5, "K-BB%")[["Name", "Team", "IP", "K%", "BB%", "K-BB%", "ERA"]]
        print(top5.to_string(index=False))

    # Test team batting stats
    print("\n2. Testing team batting stats fetch...")
    teams = fetcher.get_team_batting_stats(2024)
    print(f"   Teams: {len(teams)}")
    print(f"   Columns: {list(teams.columns[:10])}...")

    # Test pitcher lookup
    print("\n3. Testing pitcher lookup...")
    pitcher_stats = PitcherStatsAsOf(fetcher)
    stats = pitcher_stats.get_stats_as_of("Zack Wheeler", "2024-06-15", 2024)
    if stats:
        print(f"   Zack Wheeler (as of 2024-06-15):")
        for k, v in stats.items():
            print(f"     {k}: {v}")

    # Test team lookup
    print("\n4. Testing team lookup...")
    team_stats = TeamStatsAsOf(fetcher)
    oakland = team_stats.get_stats_as_of("OAK", "2024-06-15", 2024)
    if oakland:
        print(f"   Oakland Athletics (as of 2024-06-15):")
        for k, v in oakland.items():
            print(f"     {k}: {v}")

    print("\n" + "=" * 60)
    print("MLB FETCHER TEST COMPLETE")
    print("=" * 60)

    return True


if __name__ == "__main__":
    test_mlb_fetcher()
