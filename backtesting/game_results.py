"""
Game Results Fetcher - Actual Pitcher Performance

Fetches real game results for pitchers after streaming adds.
Links streaming adds to actual games pitched and calculates fantasy points.
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from pybaseball import (
    playerid_lookup,
    statcast_pitcher,
    schedule_and_record,
)

# Cache directory
CACHE_DIR = Path(__file__).parent / "data" / "game_results_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# BLJ Scoring Configuration
# Based on standard head-to-head points league
SCORING_CONFIG = {
    "ip": 3,           # +3 per IP
    "k": 1,            # +1 per K
    "bb": -1,          # -1 per BB
    "h": -1,           # -1 per H
    "hr": -2,          # -2 per HR allowed
    "er": -1,          # -1 per ER
    "win": 5,          # +5 per W
    "loss": -3,        # -3 per L
    "qs": 3,           # +3 per QS (6+ IP, 3 or fewer ER)
    "cg": 5,           # +5 per CG
    "so": 5,           # +5 per SO
    "nh": 10,          # +10 per NH
}


@dataclass
class PitcherStart:
    """A single pitching appearance/start."""
    game_date: str
    pitcher_name: str
    mlbam_id: Optional[int]
    opponent: str
    park: str  # Home team's park
    is_home: bool

    # Game stats
    ip: float
    k: int
    bb: int
    h: int
    hr: int
    er: int
    pitches: int

    # Results (if available)
    win: int = 0
    loss: int = 0
    quality_start: int = 0

    # Calculated
    fantasy_points: float = 0.0


class GameResultsFetcher:
    """Fetch actual game results for pitchers."""

    def __init__(self, season: int, scoring_config: Dict = None):
        self.season = season
        self.scoring = scoring_config or SCORING_CONFIG
        self._player_id_cache: Dict[str, Optional[int]] = {}
        self._game_log_cache: Dict[int, pd.DataFrame] = {}

    def lookup_mlbam_id(self, pitcher_name: str) -> Optional[int]:
        """Look up MLBAM player ID by name."""
        if pitcher_name in self._player_id_cache:
            return self._player_id_cache[pitcher_name]

        try:
            parts = pitcher_name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = " ".join(parts[1:])
                result = playerid_lookup(last, first)
                if not result.empty:
                    row = result.sort_values('key_mlbam', ascending=False).iloc[0]
                    mlbam_id = int(row.get("key_mlbam", 0)) if pd.notna(row.get("key_mlbam")) else None
                    self._player_id_cache[pitcher_name] = mlbam_id
                    return mlbam_id
        except Exception as e:
            pass

        self._player_id_cache[pitcher_name] = None
        return None

    def get_pitcher_game_log(self, mlbam_id: int) -> pd.DataFrame:
        """Get full season game log for a pitcher."""
        if mlbam_id in self._game_log_cache:
            return self._game_log_cache[mlbam_id]

        cache_file = CACHE_DIR / f"pitcher_{mlbam_id}_{self.season}.parquet"
        if cache_file.exists():
            df = pd.read_parquet(cache_file)
            self._game_log_cache[mlbam_id] = df
            return df

        # Fetch from Statcast
        start_date = f"{self.season}-03-01"
        end_date = f"{self.season}-10-15"

        try:
            df = statcast_pitcher(start_date, end_date, mlbam_id)
            if not df.empty:
                df.to_parquet(cache_file)
                self._game_log_cache[mlbam_id] = df
            return df
        except Exception as e:
            print(f"    Error fetching game log for {mlbam_id}: {e}")
            return pd.DataFrame()

    def aggregate_game_stats(self, statcast_df: pd.DataFrame, game_date: str) -> Optional[Dict]:
        """Aggregate pitch-level data to game stats for a specific date."""
        if statcast_df.empty:
            return None

        # Filter to specific game date
        statcast_df['game_date'] = pd.to_datetime(statcast_df['game_date'])
        target_date = pd.to_datetime(game_date)
        game_data = statcast_df[statcast_df['game_date'] == target_date]

        if game_data.empty:
            return None

        # Count stats from events
        pitches = len(game_data)
        strikeouts = len(game_data[game_data['events'] == 'strikeout'])
        walks = len(game_data[game_data['events'].isin(['walk', 'hit_by_pitch'])])
        hits = len(game_data[game_data['events'].isin(['single', 'double', 'triple', 'home_run'])])
        home_runs = len(game_data[game_data['events'] == 'home_run'])

        # Estimate outs recorded
        outs = len(game_data[game_data['events'].isin([
            'strikeout', 'field_out', 'grounded_into_double_play',
            'force_out', 'sac_fly', 'sac_bunt', 'fielders_choice_out',
            'double_play', 'triple_play', 'caught_stealing_2b',
            'caught_stealing_3b', 'caught_stealing_home'
        ])])

        ip = round(outs / 3, 1)

        # Get opponent and park
        row = game_data.iloc[0]
        pitcher_team = row.get('pitcher_team', '') if 'pitcher_team' in row else ''
        home_team = row.get('home_team', '')
        away_team = row.get('away_team', '')

        if pitcher_team:
            is_home = (pitcher_team == home_team)
            opponent = away_team if is_home else home_team
        else:
            is_home = True
            opponent = away_team

        park = home_team

        # Estimate ER (rough: assume 40% of hits score, HRs always score)
        er = int(home_runs + (hits - home_runs) * 0.3)

        return {
            'game_date': game_date,
            'opponent': opponent,
            'park': park,
            'is_home': is_home,
            'pitches': pitches,
            'ip': ip,
            'k': strikeouts,
            'bb': walks,
            'h': hits,
            'hr': home_runs,
            'er': er,
        }

    def find_next_start(
        self,
        pitcher_name: str,
        after_date: str,
        mlb_team: str = None
    ) -> Optional[PitcherStart]:
        """
        Find the pitcher's next start after a given date.

        Args:
            pitcher_name: Full name of pitcher
            after_date: Find start after this date (YYYY-MM-DD)
            mlb_team: MLB team abbreviation (optional, for filtering)

        Returns:
            PitcherStart object with game details
        """
        mlbam_id = self.lookup_mlbam_id(pitcher_name)
        if not mlbam_id:
            return None

        game_log = self.get_pitcher_game_log(mlbam_id)
        if game_log.empty:
            return None

        # Filter to games after the add date
        game_log['game_date'] = pd.to_datetime(game_log['game_date'])
        after_dt = pd.to_datetime(after_date)
        future_games = game_log[game_log['game_date'] > after_dt]

        if future_games.empty:
            return None

        # Get unique game dates
        game_dates = future_games['game_date'].unique()
        game_dates = sorted(game_dates)

        if not len(game_dates):
            return None

        # Get first game after add date
        next_game_date = game_dates[0]
        next_game_str = str(next_game_date)[:10]

        # Aggregate stats for that game
        game_stats = self.aggregate_game_stats(game_log, next_game_str)
        if not game_stats:
            return None

        # Check for quality start (6+ IP, 3 or fewer ER)
        is_qs = 1 if game_stats['ip'] >= 6 and game_stats['er'] <= 3 else 0

        # Calculate fantasy points
        points = self.calculate_fantasy_points(game_stats)

        return PitcherStart(
            game_date=next_game_str,
            pitcher_name=pitcher_name,
            mlbam_id=mlbam_id,
            opponent=game_stats['opponent'],
            park=game_stats['park'],
            is_home=game_stats['is_home'],
            ip=game_stats['ip'],
            k=game_stats['k'],
            bb=game_stats['bb'],
            h=game_stats['h'],
            hr=game_stats['hr'],
            er=game_stats['er'],
            pitches=game_stats['pitches'],
            quality_start=is_qs,
            fantasy_points=points,
        )

    def calculate_fantasy_points(self, game_stats: Dict) -> float:
        """Calculate fantasy points from game stats."""
        points = 0.0

        points += game_stats.get('ip', 0) * self.scoring['ip']
        points += game_stats.get('k', 0) * self.scoring['k']
        points += game_stats.get('bb', 0) * self.scoring['bb']
        points += game_stats.get('h', 0) * self.scoring['h']
        points += game_stats.get('hr', 0) * self.scoring['hr']
        points += game_stats.get('er', 0) * self.scoring['er']

        # Quality start bonus
        if game_stats.get('ip', 0) >= 6 and game_stats.get('er', 0) <= 3:
            points += self.scoring['qs']

        return round(points, 1)

    def get_all_starts_for_adds(
        self,
        streaming_adds: List[Dict],
        limit: int = None
    ) -> List[Tuple[Dict, Optional[PitcherStart]]]:
        """
        Get actual starts for a list of streaming adds.

        Args:
            streaming_adds: List of add dicts with player_name, date, etc.
            limit: Max number to process

        Returns:
            List of (add, PitcherStart or None) tuples
        """
        results = []
        adds = streaming_adds[:limit] if limit else streaming_adds

        print(f"Fetching game results for {len(adds)} streaming adds...")

        for i, add in enumerate(adds):
            if i % 50 == 0:
                print(f"  Processing {i+1}/{len(adds)}...")

            pitcher_name = add.get('player_name')
            add_date = add.get('date')
            mlb_team = add.get('player_team')

            if not pitcher_name or not add_date:
                results.append((add, None))
                continue

            start = self.find_next_start(pitcher_name, add_date, mlb_team)
            results.append((add, start))

        found = sum(1 for _, s in results if s is not None)
        print(f"  Found {found}/{len(adds)} actual game results")

        return results


def test_game_results():
    """Test the game results fetcher."""
    print("=" * 60)
    print("GAME RESULTS FETCHER TEST")
    print("=" * 60)

    fetcher = GameResultsFetcher(2024)

    # Test known streaming adds
    test_adds = [
        {"player_name": "Jose A. Ferrer", "date": "2024-09-14", "player_team": "SEA"},
        {"player_name": "Taj Bradley", "date": "2024-09-14", "player_team": "MIN"},
        {"player_name": "Bailey Falter", "date": "2024-06-15", "player_team": "PIT"},
    ]

    print("\nFetching next starts after streaming adds:")
    for add in test_adds:
        print(f"\n  {add['player_name']} (added {add['date']}):")
        start = fetcher.find_next_start(add['player_name'], add['date'], add['player_team'])
        if start:
            print(f"    Next start: {start.game_date} vs {start.opponent} @ {start.park}")
            print(f"    Line: {start.ip} IP, {start.k} K, {start.bb} BB, {start.hr} HR")
            print(f"    Fantasy points: {start.fantasy_points}")
        else:
            print(f"    No start found")

    print("\n" + "=" * 60)
    print("GAME RESULTS FETCHER TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_game_results()
