"""
Roster Monitor

Checks your Yahoo Fantasy roster for issues:
- Injured players in starting lineup
- Healthy players stuck in IL slot
- Empty roster spots
- Players not playing today
"""
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
from dotenv import load_dotenv

from mlb_api import get_injuries, get_todays_games
from notifications import alert_lineup_issue, alert_il_activation

load_dotenv()

PROJECT_DIR = Path(__file__).parent
TOKEN_FILE = PROJECT_DIR / "oauth2.json"


class RosterMonitor:
    """Monitor Yahoo Fantasy roster for issues."""

    def __init__(self, league_id: str, year: int = 2025):
        """
        Initialize monitor.

        Args:
            league_id: Yahoo league ID (e.g., "89318")
            year: Season year
        """
        self.league_id = league_id
        self.year = year
        self.oauth = None
        self.league = None
        self.team = None

    def connect(self) -> bool:
        """Connect to Yahoo Fantasy API."""
        try:
            self.oauth = OAuth2(None, None, from_file=str(TOKEN_FILE))
            if not self.oauth.token_is_valid():
                self.oauth.refresh_access_token()

            gm = yfa.Game(self.oauth, 'mlb')
            # Build league key
            game_id = gm.game_id()
            league_key = f"{game_id}.l.{self.league_id}"

            self.league = gm.to_league(league_key)
            self.team = self.league.to_team(self.league.team_key())

            print(f"Connected to league: {league_key}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def get_roster(self, day: Optional[datetime] = None) -> list:
        """
        Get current roster.

        Args:
            day: Specific date, defaults to today

        Returns:
            List of player dicts
        """
        if not self.team:
            raise RuntimeError("Not connected. Call connect() first.")

        roster = self.team.roster(day=day)
        return roster

    def check_for_issues(self, roster: list = None) -> list:
        """
        Check roster for common issues.

        Args:
            roster: Roster to check, or fetch current

        Returns:
            List of issue descriptions
        """
        if roster is None:
            roster = self.get_roster()

        issues = []

        # Get today's games and injuries
        todays_games = get_todays_games()
        playing_teams = set()
        for game in todays_games:
            playing_teams.add(game['home_abbrev'])
            playing_teams.add(game['away_abbrev'])

        mlb_injuries = {inj['player_name'].lower(): inj for inj in get_injuries()}

        for player in roster:
            name = player.get('name', 'Unknown')
            position = player.get('selected_position', '')
            status = player.get('status', '')
            eligible = player.get('eligible_positions', [])

            # Check 1: Injured player in starting lineup (not BN or IL)
            if status in ['IL', 'IL+', 'DTD'] and position not in ['BN', 'IL', 'IL+']:
                issues.append(f"⚠️ {name} is {status} but starting at {position}")

            # Check 2: Healthy player in IL slot
            if position in ['IL', 'IL+'] and status == '':
                issues.append(f"🔄 {name} is healthy but still in {position} slot")

            # Check 3: Player's team not playing today (for starters)
            # Would need team info from Yahoo API

        # Check 4: Empty roster spots
        # Would need to check position counts

        return issues

    def find_il_candidates(self, roster: list = None) -> dict:
        """
        Find players who should be moved to/from IL.

        Args:
            roster: Roster to check

        Returns:
            Dict with 'to_il' and 'from_il' lists
        """
        if roster is None:
            roster = self.get_roster()

        results = {
            'to_il': [],    # Injured players not in IL slot
            'from_il': [],  # Healthy players in IL slot
        }

        for player in roster:
            name = player.get('name', 'Unknown')
            position = player.get('selected_position', '')
            status = player.get('status', '')

            if status in ['IL', 'IL+'] and position not in ['IL', 'IL+']:
                results['to_il'].append({
                    'name': name,
                    'current_position': position,
                    'status': status,
                })

            if position in ['IL', 'IL+'] and status == '':
                results['from_il'].append({
                    'name': name,
                    'current_position': position,
                })

        return results

    def get_starting_pitchers_today(self, roster: list = None) -> list:
        """
        Find which of your pitchers are starting today.

        Args:
            roster: Roster to check

        Returns:
            List of pitcher names with starts
        """
        if roster is None:
            roster = self.get_roster()

        todays_games = get_todays_games()

        # Build set of today's probable pitchers
        probable_pitchers = set()
        for game in todays_games:
            if game['home_pitcher']:
                probable_pitchers.add(game['home_pitcher'].lower())
            if game['away_pitcher']:
                probable_pitchers.add(game['away_pitcher'].lower())

        # Check your roster
        your_starters = []
        for player in roster:
            pos_type = player.get('position_type', '')
            if pos_type == 'P':
                name = player.get('name', '')
                if name.lower() in probable_pitchers:
                    your_starters.append(name)

        return your_starters

    def run_daily_check(self) -> dict:
        """
        Run all daily checks.

        Returns:
            Dict with all check results
        """
        roster = self.get_roster()

        results = {
            'timestamp': datetime.now().isoformat(),
            'issues': self.check_for_issues(roster),
            'il_moves': self.find_il_candidates(roster),
            'starters_today': self.get_starting_pitchers_today(roster),
            'roster_count': len(roster),
        }

        # Send alerts if issues found
        if results['issues']:
            alert_lineup_issue(results['issues'])

        return results


def demo_with_sample_data():
    """Demo the monitor with sample data (no API needed)."""
    print("=== Roster Monitor Demo ===\n")

    # Sample roster data (like what Yahoo returns)
    sample_roster = [
        {'name': 'Mike Trout', 'selected_position': 'OF', 'status': 'IL', 'position_type': 'B'},
        {'name': 'Shohei Ohtani', 'selected_position': 'Util', 'status': '', 'position_type': 'B'},
        {'name': 'Freddie Freeman', 'selected_position': 'IL', 'status': '', 'position_type': 'B'},
        {'name': 'Clayton Kershaw', 'selected_position': 'SP', 'status': 'DTD', 'position_type': 'P'},
        {'name': 'Zack Wheeler', 'selected_position': 'IL+', 'status': 'IL+', 'position_type': 'P'},
    ]

    print("Sample Roster:")
    print("-" * 50)
    for p in sample_roster:
        status_str = f"[{p['status']}]" if p['status'] else ""
        print(f"  {p['selected_position']:5} | {p['name']:20} {status_str}")

    print("\n" + "=" * 50)
    print("\nIssues Found:")
    print("-" * 50)

    # Check for issues
    monitor = RosterMonitor("89318")  # Won't connect, just for logic

    for player in sample_roster:
        name = player.get('name', 'Unknown')
        position = player.get('selected_position', '')
        status = player.get('status', '')

        if status in ['IL', 'IL+', 'DTD'] and position not in ['BN', 'IL', 'IL+']:
            print(f"  ⚠️  {name} is {status} but starting at {position}")

        if position in ['IL', 'IL+'] and status == '':
            print(f"  🔄 {name} is healthy but still in {position} slot")

    print("\n" + "=" * 50)
    print("\nRecommended Actions:")
    print("-" * 50)
    print("  1. Move Mike Trout to IL slot (injured)")
    print("  2. Activate Freddie Freeman from IL (healthy)")
    print("  3. Bench Clayton Kershaw (DTD)")


if __name__ == "__main__":
    demo_with_sample_data()
