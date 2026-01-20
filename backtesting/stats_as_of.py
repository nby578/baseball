"""
Cumulative Stats Calculator - "As Of Date" Stats

Calculates pitcher and team stats cumulative through a specific date,
not just season totals. Critical for accurate backtesting.

Uses pybaseball to fetch game logs and aggregate to cumulative stats.
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from pybaseball import (
    pitching_stats,
    batting_stats,
    team_batting,
    playerid_lookup,
    statcast_pitcher,
)

# Cache directory
CACHE_DIR = Path(__file__).parent / "data" / "stats_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class PitcherGameLog:
    """Fetch and cache pitcher game logs."""

    def __init__(self, season: int):
        self.season = season
        self._game_logs: Dict[int, pd.DataFrame] = {}  # mlbam_id -> game log
        self._player_id_cache: Dict[str, Dict] = {}

    def lookup_player_id(self, name: str) -> Optional[Dict]:
        """Look up MLBAM player ID by name."""
        if name in self._player_id_cache:
            return self._player_id_cache[name]

        try:
            parts = name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = " ".join(parts[1:])
                result = playerid_lookup(last, first)
                if not result.empty:
                    # Find most recent player (highest mlbam_id usually)
                    row = result.sort_values('key_mlbam', ascending=False).iloc[0]
                    player_ids = {
                        "name": name,
                        "mlbam_id": int(row.get("key_mlbam", 0)) if pd.notna(row.get("key_mlbam")) else None,
                        "fangraphs_id": int(row.get("key_fangraphs", 0)) if pd.notna(row.get("key_fangraphs")) else None,
                    }
                    self._player_id_cache[name] = player_ids
                    return player_ids
        except Exception as e:
            print(f"  Warning: Could not look up {name}: {e}")

        self._player_id_cache[name] = None
        return None

    def get_game_log(self, mlbam_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get pitcher game log from Statcast.

        Args:
            mlbam_id: MLB Advanced Media player ID
            start_date: Start of date range (YYYY-MM-DD)
            end_date: End of date range (YYYY-MM-DD)

        Returns:
            DataFrame with pitch-level data
        """
        # Default to full season
        if not start_date:
            start_date = f"{self.season}-03-01"
        if not end_date:
            end_date = f"{self.season}-10-15"

        cache_key = f"statcast_{mlbam_id}_{self.season}"
        cache_file = CACHE_DIR / f"{cache_key}.parquet"

        if cache_file.exists():
            return pd.read_parquet(cache_file)

        print(f"  Fetching Statcast for pitcher {mlbam_id}...")
        try:
            df = statcast_pitcher(start_date, end_date, mlbam_id)
            if not df.empty:
                df.to_parquet(cache_file)
            return df
        except Exception as e:
            print(f"  Error fetching Statcast: {e}")
            return pd.DataFrame()

    def aggregate_to_games(self, statcast_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate pitch-level Statcast data to game summaries.

        Returns DataFrame with: game_date, opponent, IP, K, BB, H, HR, ER
        """
        if statcast_df.empty:
            return pd.DataFrame()

        # Group by game date
        games = []

        for game_date, game_data in statcast_df.groupby('game_date'):
            # Basic counting stats
            pitches = len(game_data)
            strikeouts = len(game_data[game_data['events'] == 'strikeout'])
            walks = len(game_data[game_data['events'].isin(['walk', 'hit_by_pitch'])])
            hits = len(game_data[game_data['events'].isin(['single', 'double', 'triple', 'home_run'])])
            home_runs = len(game_data[game_data['events'] == 'home_run'])

            # Estimate IP from outs recorded
            outs = len(game_data[game_data['events'].isin([
                'strikeout', 'field_out', 'grounded_into_double_play',
                'force_out', 'sac_fly', 'sac_bunt', 'fielders_choice_out',
                'double_play', 'triple_play', 'caught_stealing_2b',
                'caught_stealing_3b', 'caught_stealing_home'
            ])])

            # Approximate IP (outs / 3)
            ip = round(outs / 3, 1)

            # Get opponent from 'home_team' or 'away_team'
            if not game_data.empty:
                row = game_data.iloc[0]
                pitcher_team = row.get('pitcher_team', '')
                home_team = row.get('home_team', '')
                away_team = row.get('away_team', '')
                opponent = away_team if pitcher_team == home_team else home_team
            else:
                opponent = ""

            games.append({
                'game_date': game_date,
                'opponent': opponent,
                'pitches': pitches,
                'ip': ip,
                'k': strikeouts,
                'bb': walks,
                'h': hits,
                'hr': home_runs,
            })

        return pd.DataFrame(games).sort_values('game_date')


class CumulativeStatsCalculator:
    """Calculate cumulative stats through a specific date."""

    def __init__(self, season: int):
        self.season = season
        self.game_log_fetcher = PitcherGameLog(season)
        self._season_stats_cache: Dict[int, pd.DataFrame] = {}

    def get_season_pitcher_stats(self, qual: int = 1) -> pd.DataFrame:
        """Get all pitcher stats for the season."""
        cache_key = f"pitchers_{self.season}_{qual}"

        if cache_key in self._season_stats_cache:
            return self._season_stats_cache[cache_key]

        cache_file = CACHE_DIR / f"{cache_key}.parquet"
        if cache_file.exists():
            df = pd.read_parquet(cache_file)
            self._season_stats_cache[cache_key] = df
            return df

        print(f"Fetching pitcher stats for {self.season}...")
        df = pitching_stats(self.season, qual=qual)

        if "K-BB%" not in df.columns and "K%" in df.columns and "BB%" in df.columns:
            df["K-BB%"] = df["K%"] - df["BB%"]

        df.to_parquet(cache_file)
        self._season_stats_cache[cache_key] = df
        return df

    def get_pitcher_stats_through(
        self,
        pitcher_name: str,
        through_date: str,
        use_game_logs: bool = False
    ) -> Optional[Dict]:
        """
        Get pitcher stats cumulative through a specific date.

        Args:
            pitcher_name: Full name of pitcher
            through_date: Date in YYYY-MM-DD format
            use_game_logs: If True, aggregate game logs. If False, use season stats (approximation)

        Returns:
            Dict with k_pct, bb_pct, k_bb_pct, gb_pct, era, ip, etc.
        """
        if use_game_logs:
            return self._get_stats_from_game_logs(pitcher_name, through_date)
        else:
            # For now, return season stats as approximation
            # This is faster but less accurate for early-season adds
            return self._get_season_stats_approximation(pitcher_name)

    def _get_season_stats_approximation(self, pitcher_name: str) -> Optional[Dict]:
        """Get season stats as approximation (fast but not date-specific)."""
        all_pitchers = self.get_season_pitcher_stats(qual=1)

        # Fuzzy match by last name
        name_lower = pitcher_name.lower()
        last_name = name_lower.split()[-1] if name_lower else ""

        matches = all_pitchers[
            all_pitchers["Name"].str.lower().str.contains(last_name, regex=False)
        ]

        if matches.empty:
            return None

        # Get best match (highest IP if multiple)
        row = matches.sort_values("IP", ascending=False).iloc[0]

        return {
            "name": row.get("Name"),
            "team": row.get("Team"),
            "ip": float(row.get("IP", 0)),
            "era": float(row.get("ERA", 0)),
            "fip": float(row.get("FIP", 0)),
            "k_pct": float(row.get("K%", 0)),
            "bb_pct": float(row.get("BB%", 0)),
            "k_bb_pct": float(row.get("K-BB%", row.get("K%", 0) - row.get("BB%", 0))),
            "gb_pct": float(row.get("GB%", 0)),
            "hr_per_9": float(row.get("HR/9", 0)),
            "whip": float(row.get("WHIP", 0)),
            "war": float(row.get("WAR", 0)),
            "source": "season_total",
        }

    def _get_stats_from_game_logs(self, pitcher_name: str, through_date: str) -> Optional[Dict]:
        """Get cumulative stats from actual game logs through date."""
        # Look up player ID
        player_ids = self.game_log_fetcher.lookup_player_id(pitcher_name)
        if not player_ids or not player_ids.get("mlbam_id"):
            return None

        mlbam_id = player_ids["mlbam_id"]

        # Get game log
        start_date = f"{self.season}-03-01"
        statcast_df = self.game_log_fetcher.get_game_log(mlbam_id, start_date, through_date)

        if statcast_df.empty:
            return None

        # Filter to games before through_date
        statcast_df['game_date'] = pd.to_datetime(statcast_df['game_date'])
        through_dt = pd.to_datetime(through_date)
        filtered = statcast_df[statcast_df['game_date'] < through_dt]

        if filtered.empty:
            return None

        # Aggregate to games
        games = self.game_log_fetcher.aggregate_to_games(filtered)

        if games.empty:
            return None

        # Calculate cumulative stats
        total_ip = games['ip'].sum()
        total_k = games['k'].sum()
        total_bb = games['bb'].sum()
        total_hr = games['hr'].sum()
        total_h = games['h'].sum()

        # Calculate rates
        # Note: These are approximations since we don't have exact PA/TBF
        k_pct = total_k / (total_ip * 3 + total_h + total_bb) if total_ip > 0 else 0
        bb_pct = total_bb / (total_ip * 3 + total_h + total_bb) if total_ip > 0 else 0

        return {
            "name": pitcher_name,
            "mlbam_id": mlbam_id,
            "games": len(games),
            "ip": float(total_ip),
            "k": int(total_k),
            "bb": int(total_bb),
            "hr": int(total_hr),
            "h": int(total_h),
            "k_pct": float(k_pct),
            "bb_pct": float(bb_pct),
            "k_bb_pct": float(k_pct - bb_pct),
            "through_date": through_date,
            "source": "game_logs",
        }


class TeamStatsCalculator:
    """Calculate team batting stats."""

    def __init__(self, season: int):
        self.season = season
        self._team_stats_cache = None

    def get_team_stats(self) -> pd.DataFrame:
        """Get all team batting stats for the season."""
        if self._team_stats_cache is not None:
            return self._team_stats_cache

        cache_file = CACHE_DIR / f"team_batting_{self.season}.parquet"
        if cache_file.exists():
            self._team_stats_cache = pd.read_parquet(cache_file)
            return self._team_stats_cache

        print(f"Fetching team batting stats for {self.season}...")
        df = team_batting(self.season)
        df.to_parquet(cache_file)
        self._team_stats_cache = df
        return df

    def get_team_stats_as_of(self, team: str, through_date: str = None) -> Optional[Dict]:
        """
        Get team batting stats.

        Note: pybaseball only provides season totals, not date-specific.
        For accurate "as of date" stats, would need game-by-game data.
        """
        all_teams = self.get_team_stats()

        # Normalize team abbreviation
        team_upper = team.upper()
        team_map = {
            "ARI": "ARI", "ATL": "ATL", "BAL": "BAL", "BOS": "BOS",
            "CHC": "CHC", "CHW": "CHW", "CWS": "CHW", "CIN": "CIN",
            "CLE": "CLE", "COL": "COL", "DET": "DET", "HOU": "HOU",
            "KC": "KCR", "KCR": "KCR", "LAA": "LAA", "LAD": "LAD",
            "MIA": "MIA", "MIL": "MIL", "MIN": "MIN", "NYM": "NYM",
            "NYY": "NYY", "OAK": "OAK", "PHI": "PHI", "PIT": "PIT",
            "SD": "SDP", "SDP": "SDP", "SF": "SFG", "SFG": "SFG",
            "SEA": "SEA", "STL": "STL", "TB": "TBR", "TBR": "TBR",
            "TEX": "TEX", "TOR": "TOR", "WAS": "WSN", "WSH": "WSN", "WSN": "WSN",
        }
        normalized = team_map.get(team_upper, team_upper)

        # Find team
        matches = all_teams[all_teams["Team"].str.upper() == normalized]

        if matches.empty:
            # Try partial match
            matches = all_teams[all_teams["Team"].str.contains(team, case=False)]

        if matches.empty:
            return None

        row = matches.iloc[0]

        return {
            "team": row.get("Team"),
            "k_pct": float(row.get("K%", 0)),
            "bb_pct": float(row.get("BB%", 0)),
            "iso": float(row.get("ISO", 0)),
            "woba": float(row.get("wOBA", 0)),
            "wrc_plus": float(row.get("wRC+", 100)),
            "ops": float(row.get("OPS", 0)),
            "avg": float(row.get("AVG", 0)),
            "source": "season_total",
        }


def test_stats_calculator():
    """Test the stats calculators."""
    print("=" * 60)
    print("CUMULATIVE STATS CALCULATOR TEST")
    print("=" * 60)

    calc = CumulativeStatsCalculator(2024)
    team_calc = TeamStatsCalculator(2024)

    # Test pitcher lookup
    print("\n1. Testing pitcher stats (season approximation):")
    for name in ["Zack Wheeler", "Jose A. Ferrer", "Bailey Falter"]:
        stats = calc.get_pitcher_stats_through(name, "2024-06-15", use_game_logs=False)
        if stats:
            print(f"   {name}:")
            print(f"     K-BB%: {stats['k_bb_pct']:.1%}, GB%: {stats.get('gb_pct', 0):.1%}, IP: {stats['ip']}")
        else:
            print(f"   {name}: Not found")

    # Test team stats
    print("\n2. Testing team batting stats:")
    for team in ["OAK", "NYY", "LAD"]:
        stats = team_calc.get_team_stats_as_of(team)
        if stats:
            print(f"   {team}: K%={stats['k_pct']:.1%}, ISO={stats['iso']:.3f}, wOBA={stats['woba']:.3f}")
        else:
            print(f"   {team}: Not found")

    print("\n" + "=" * 60)
    print("STATS CALCULATOR TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_stats_calculator()
