"""
Live Roster Monitor for Fantasy Baseball

Monitors the Yahoo Fantasy league for roster changes:
- Tracks when other teams add streaming pitchers
- Alerts when targets from our plan get picked up
- Re-ranks available options when landscape changes
- Provides real-time updates on free agent pool

Can be run as a background process or called on-demand.
"""

import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backtesting"))

from backtesting.yahoo_fetcher import YahooFetcher


@dataclass
class RosterChange:
    """A detected roster change."""
    timestamp: str
    fantasy_team: str
    team_key: str
    change_type: str  # "add", "drop", "trade"
    player_name: str
    player_key: str
    player_team: str
    player_position: str
    is_pitcher: bool = False


@dataclass
class MonitorState:
    """Current state of the roster monitor."""
    last_check: str
    rostered_players: Dict[str, Dict]  # player_key -> {player_info, team_key}
    recent_changes: List[RosterChange]
    watched_players: Set[str]  # player_keys we're tracking


class RosterMonitor:
    """
    Monitors league rosters for changes.

    Usage:
        monitor = RosterMonitor(season=2025)
        changes = monitor.check_for_changes()
        if changes:
            print("New roster moves detected!")
    """

    def __init__(self, season: int = 2025, my_team_number: int = 7):
        self.season = season
        self.my_team_number = my_team_number

        print(f"Initializing Roster Monitor for {season}...")

        # Initialize Yahoo API
        self.yahoo = YahooFetcher(season)

        # State
        self._state_file = Path(__file__).parent / "cache" / f"roster_state_{season}.json"
        self._state_file.parent.mkdir(exist_ok=True)

        self._state: Optional[MonitorState] = None
        self._load_state()

        # Team info cache
        self._team_names: Dict[str, str] = {}

    def _load_state(self):
        """Load previous state from disk."""
        if self._state_file.exists():
            try:
                with open(self._state_file) as f:
                    data = json.load(f)

                self._state = MonitorState(
                    last_check=data.get("last_check", ""),
                    rostered_players=data.get("rostered_players", {}),
                    recent_changes=[
                        RosterChange(**c) for c in data.get("recent_changes", [])
                    ],
                    watched_players=set(data.get("watched_players", [])),
                )
                print(f"  Loaded state from {self._state.last_check}")
            except Exception as e:
                print(f"  Could not load state: {e}")
                self._state = None

    def _save_state(self):
        """Save current state to disk."""
        if self._state is None:
            return

        data = {
            "last_check": self._state.last_check,
            "rostered_players": self._state.rostered_players,
            "recent_changes": [asdict(c) for c in self._state.recent_changes[-100:]],  # Keep last 100
            "watched_players": list(self._state.watched_players),
        }

        with open(self._state_file, "w") as f:
            json.dump(data, f, indent=2)

    def _get_team_name(self, team_key: str) -> str:
        """Get team name from key (cached)."""
        if team_key not in self._team_names:
            # Extract team number from key (e.g., "458.l.89318.t.1")
            parts = team_key.split(".")
            if len(parts) >= 5:
                team_num = parts[-1]
                self._team_names[team_key] = f"Team {team_num}"
            else:
                self._team_names[team_key] = team_key
        return self._team_names[team_key]

    def get_current_rosters(self) -> Dict[str, Dict]:
        """
        Get snapshot of all currently rostered players.

        Returns:
            Dict mapping player_key -> {player_info, team_key}
        """
        print("  Fetching all rosters...")
        rosters = self.yahoo.get_all_rosters()

        all_players = {}
        for team_key, players in rosters.items():
            for player in players:
                player_key = player.get("player_key")
                if player_key:
                    all_players[player_key] = {
                        **player,
                        "team_key": team_key,
                        "fantasy_team": self._get_team_name(team_key),
                    }

        print(f"    {len(all_players)} players rostered across {len(rosters)} teams")
        return all_players

    def check_for_changes(self) -> List[RosterChange]:
        """
        Check for roster changes since last check.

        Returns:
            List of RosterChange objects for new changes
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get current state
        current_rosters = self.get_current_rosters()

        # If no previous state, initialize
        if self._state is None or not self._state.rostered_players:
            print("  First run - initializing baseline state")
            self._state = MonitorState(
                last_check=now,
                rostered_players=current_rosters,
                recent_changes=[],
                watched_players=set(),
            )
            self._save_state()
            return []

        # Detect changes
        changes = []

        # Check for new additions
        for player_key, player_info in current_rosters.items():
            if player_key not in self._state.rostered_players:
                # New addition
                change = RosterChange(
                    timestamp=now,
                    fantasy_team=player_info.get("fantasy_team", "Unknown"),
                    team_key=player_info.get("team_key", ""),
                    change_type="add",
                    player_name=player_info.get("name", "Unknown"),
                    player_key=player_key,
                    player_team=player_info.get("team", ""),
                    player_position=player_info.get("eligible_positions", ""),
                    is_pitcher="SP" in player_info.get("eligible_positions", "") or
                              "RP" in player_info.get("eligible_positions", ""),
                )
                changes.append(change)

        # Check for drops
        for player_key, player_info in self._state.rostered_players.items():
            if player_key not in current_rosters:
                # Player dropped
                change = RosterChange(
                    timestamp=now,
                    fantasy_team=player_info.get("fantasy_team", "Unknown"),
                    team_key=player_info.get("team_key", ""),
                    change_type="drop",
                    player_name=player_info.get("name", "Unknown"),
                    player_key=player_key,
                    player_team=player_info.get("team", ""),
                    player_position=player_info.get("eligible_positions", ""),
                    is_pitcher="SP" in player_info.get("eligible_positions", "") or
                              "RP" in player_info.get("eligible_positions", ""),
                )
                changes.append(change)

        # Check for moves between teams (trades/waiver claims)
        for player_key, current_info in current_rosters.items():
            if player_key in self._state.rostered_players:
                prev_info = self._state.rostered_players[player_key]
                if current_info.get("team_key") != prev_info.get("team_key"):
                    # Changed teams
                    change = RosterChange(
                        timestamp=now,
                        fantasy_team=f"{prev_info.get('fantasy_team', '?')} -> {current_info.get('fantasy_team', '?')}",
                        team_key=current_info.get("team_key", ""),
                        change_type="trade",
                        player_name=current_info.get("name", "Unknown"),
                        player_key=player_key,
                        player_team=current_info.get("team", ""),
                        player_position=current_info.get("eligible_positions", ""),
                        is_pitcher="SP" in current_info.get("eligible_positions", "") or
                                  "RP" in current_info.get("eligible_positions", ""),
                    )
                    changes.append(change)

        # Update state
        self._state.last_check = now
        self._state.rostered_players = current_rosters
        self._state.recent_changes.extend(changes)
        self._save_state()

        return changes

    def watch_player(self, player_key: str):
        """Add a player to the watch list."""
        if self._state is None:
            self._state = MonitorState(
                last_check="",
                rostered_players={},
                recent_changes=[],
                watched_players=set(),
            )
        self._state.watched_players.add(player_key)
        self._save_state()

    def watch_players_from_plan(self, plan_file: Path):
        """
        Add all players from a streaming plan to the watch list.

        Args:
            plan_file: Path to streaming plan JSON
        """
        if not plan_file.exists():
            print(f"Plan file not found: {plan_file}")
            return

        with open(plan_file) as f:
            plan = json.load(f)

        # Extract player names from the plan
        targets = plan.get("overall_top_targets", [])
        watched = 0

        for target in targets:
            name = target.get("name", "")
            if name:
                # We'll use name as a pseudo-key since we may not have player_key
                if self._state is None:
                    self._state = MonitorState(
                        last_check="",
                        rostered_players={},
                        recent_changes=[],
                        watched_players=set(),
                    )
                self._state.watched_players.add(name)
                watched += 1

        self._save_state()
        print(f"  Now watching {watched} streaming targets")

    def get_watched_player_status(self) -> Dict[str, str]:
        """
        Check status of watched players.

        Returns:
            Dict mapping player name/key -> status ("available", "taken by X")
        """
        if self._state is None or not self._state.watched_players:
            return {}

        status = {}

        for watched in self._state.watched_players:
            # Check if this player is in current rosters
            found = False
            for player_key, info in self._state.rostered_players.items():
                player_name = info.get("name", "")
                if watched == player_key or watched.lower() == player_name.lower():
                    status[watched] = f"Rostered by {info.get('fantasy_team', 'Unknown')}"
                    found = True
                    break

            if not found:
                status[watched] = "Available"

        return status

    def print_changes(self, changes: List[RosterChange]):
        """Pretty print roster changes."""
        if not changes:
            print("No new roster changes detected.")
            return

        print(f"\n{'='*60}")
        print(f"ROSTER CHANGES DETECTED ({len(changes)} total)")
        print(f"{'='*60}")

        adds = [c for c in changes if c.change_type == "add"]
        drops = [c for c in changes if c.change_type == "drop"]
        trades = [c for c in changes if c.change_type == "trade"]

        if adds:
            print("\n ADDITIONS:")
            for c in adds:
                icon = "[SP]" if c.is_pitcher else "[POS]"
                watched = " [WATCHED!]" if c.player_name in (self._state.watched_players if self._state else set()) else ""
                print(f"  + {c.fantasy_team} added {c.player_name} ({c.player_team}) {icon}{watched}")

        if drops:
            print("\n DROPS:")
            for c in drops:
                icon = "[SP]" if c.is_pitcher else "[POS]"
                print(f"  - {c.fantasy_team} dropped {c.player_name} ({c.player_team}) {icon}")

        if trades:
            print("\n TRADES/WAIVERS:")
            for c in trades:
                print(f"  ~ {c.player_name} moved: {c.fantasy_team}")

        print(f"\n{'='*60}")

    def get_available_streamers(self, all_pitchers: List[Dict]) -> List[Dict]:
        """
        Filter pitcher list to show only available (unrostered) ones.

        Args:
            all_pitchers: List of pitcher dicts from schedule

        Returns:
            Filtered list of available pitchers
        """
        if self._state is None or not self._state.rostered_players:
            return all_pitchers

        # Build set of rostered pitcher names for quick lookup
        rostered_names = set()
        for player_key, info in self._state.rostered_players.items():
            if info.get("name"):
                rostered_names.add(info["name"].lower())

        # Filter
        available = []
        for pitcher in all_pitchers:
            name = pitcher.get("name", "").lower()
            if name and name not in rostered_names:
                available.append(pitcher)

        return available

    def run_continuous(self, check_interval: int = 300):
        """
        Run continuous monitoring (every N seconds).

        Args:
            check_interval: Seconds between checks (default 5 minutes)
        """
        print(f"\nStarting continuous monitoring (every {check_interval}s)...")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                changes = self.check_for_changes()
                if changes:
                    self.print_changes(changes)

                    # Check for watched players
                    watched_changes = [
                        c for c in changes
                        if c.player_name in (self._state.watched_players if self._state else set())
                    ]
                    if watched_changes:
                        print("\n*** ALERT: Watched player status changed! ***")
                        for c in watched_changes:
                            print(f"    {c.player_name}: {c.change_type} by {c.fantasy_team}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No changes")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")


def demo():
    """Demo the roster monitor."""
    print("=" * 60)
    print("ROSTER MONITOR DEMO")
    print("=" * 60)

    monitor = RosterMonitor(season=2025)

    # Check for changes
    print("\nChecking for roster changes...")
    changes = monitor.check_for_changes()
    monitor.print_changes(changes)

    # Show watched player status
    print("\nWatched player status:")
    status = monitor.get_watched_player_status()
    if status:
        for player, st in status.items():
            print(f"  {player}: {st}")
    else:
        print("  No players being watched yet.")

    # Look for recent plan file
    plans_dir = Path(__file__).parent / "plans"
    if plans_dir.exists():
        plan_files = sorted(plans_dir.glob("streaming_plan_*.json"), reverse=True)
        if plan_files:
            latest_plan = plan_files[0]
            print(f"\nLoading targets from {latest_plan.name}...")
            monitor.watch_players_from_plan(latest_plan)

            # Re-check status
            status = monitor.get_watched_player_status()
            print("\nUpdated watched player status:")
            for player, st in list(status.items())[:10]:  # Top 10
                print(f"  {player}: {st}")


if __name__ == "__main__":
    demo()
