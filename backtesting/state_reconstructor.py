"""
Historical State Reconstructor for Fantasy Baseball Backtesting

Reconstructs the exact state of the fantasy league at any historical date:
- Team rosters (who owned which players)
- Free agent pool (who was available to add)
- Lineup decisions (who was started vs benched)

Uses draft data + transaction history to compute state at any date.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

# Data directory
DATA_DIR = Path(__file__).parent / "data"


@dataclass
class Player:
    """A player in the fantasy league."""
    player_key: str
    name: str = ""
    team: str = ""  # MLB team abbreviation
    position: str = ""
    fantasy_team_key: Optional[str] = None
    fantasy_team_name: Optional[str] = None


@dataclass
class Transaction:
    """A parsed transaction."""
    transaction_id: str
    trans_type: str  # add, drop, add/drop, trade
    timestamp: int
    date: str  # YYYY-MM-DD
    adds: List[Dict] = field(default_factory=list)  # {player_key, name, team, position, dest_team_key, dest_team_name}
    drops: List[Dict] = field(default_factory=list)  # {player_key, name, team, position, source_team_key, source_team_name}


@dataclass
class LeagueState:
    """Complete state of the league at a point in time."""
    date: str
    rosters: Dict[str, List[Player]]  # team_key -> list of players
    all_rostered_player_keys: Set[str]

    def get_roster(self, team_key: str) -> List[Player]:
        """Get roster for a specific team."""
        return self.rosters.get(team_key, [])

    def is_rostered(self, player_key: str) -> bool:
        """Check if a player is rostered by any team."""
        return player_key in self.all_rostered_player_keys


class StateReconstructor:
    """Reconstruct league state at any historical date."""

    def __init__(self, season: int, league_name: str = "Big_League_Jew"):
        self.season = season
        self.league_name = league_name
        self.draft_picks: List[Dict] = []  # Initial state from draft
        self.transactions: List[Transaction] = []
        self.teams: Dict[str, str] = {}  # team_key -> team_name
        self.player_info: Dict[str, Dict] = {}  # player_key -> {name, team, position}

        self._load_data()

    def _load_data(self):
        """Load draft, transactions, and team data."""
        # Find data files
        draft_files = list(DATA_DIR.glob(f"draft_raw_{self.season}_{self.league_name}*.json"))
        trans_files = list(DATA_DIR.glob(f"transactions_parsed_{self.season}_{self.league_name}*.json"))
        teams_files = list(DATA_DIR.glob(f"teams_raw_{self.season}_{self.league_name}*.json"))

        if draft_files:
            self._load_draft(draft_files[0])
        if trans_files:
            self._load_transactions(trans_files[0])
        if teams_files:
            self._load_teams(teams_files[0])

        print(f"Loaded: {len(self.draft_picks)} draft picks, {len(self.transactions)} transactions, {len(self.teams)} teams")

    def _load_draft(self, filepath: Path):
        """Load and parse draft results."""
        with open(filepath) as f:
            data = json.load(f)

        try:
            content = data.get("fantasy_content", {})
            league = content.get("league", [])

            if len(league) > 1:
                draft_results = league[1].get("draft_results", {})

                for key, value in draft_results.items():
                    if key == "count":
                        continue

                    pick = value.get("draft_result", {})
                    self.draft_picks.append({
                        "pick": pick.get("pick"),
                        "round": pick.get("round"),
                        "team_key": pick.get("team_key"),
                        "player_key": pick.get("player_key"),
                    })

        except Exception as e:
            print(f"Error parsing draft: {e}")

        # Sort by pick number
        self.draft_picks.sort(key=lambda x: x.get("pick", 0))

    def _load_transactions(self, filepath: Path):
        """Load parsed transactions."""
        with open(filepath) as f:
            data = json.load(f)

        for trans in data:
            timestamp = int(trans.get("timestamp", 0))
            date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

            parsed = Transaction(
                transaction_id=trans.get("transaction_id"),
                trans_type=trans.get("type"),
                timestamp=timestamp,
                date=date,
            )

            for player in trans.get("players", []):
                player_data = {
                    "player_key": player.get("player_key"),
                    "name": player.get("name"),
                    "team": player.get("team"),
                    "position": player.get("position"),
                }

                # Store player info
                if player.get("player_key"):
                    self.player_info[player["player_key"]] = {
                        "name": player.get("name"),
                        "team": player.get("team"),
                        "position": player.get("position"),
                    }

                if player.get("type") == "add":
                    player_data["dest_team_key"] = player.get("destination_team_key")
                    player_data["dest_team_name"] = player.get("destination_team_name")
                    parsed.adds.append(player_data)
                elif player.get("type") == "drop":
                    player_data["source_team_key"] = player.get("source_team_key")
                    player_data["source_team_name"] = player.get("source_team_name")
                    parsed.drops.append(player_data)

            self.transactions.append(parsed)

        # Sort by timestamp (oldest first for forward replay)
        self.transactions.sort(key=lambda x: x.timestamp)

    def _load_teams(self, filepath: Path):
        """Load team information."""
        with open(filepath) as f:
            data = json.load(f)

        try:
            content = data.get("fantasy_content", {})
            league = content.get("league", [])

            if len(league) > 1:
                teams_data = league[1].get("teams", {})

                for key, value in teams_data.items():
                    if key == "count":
                        continue

                    team_info = value.get("team", [[]])
                    if team_info and isinstance(team_info[0], list):
                        team_key = None
                        team_name = None
                        for item in team_info[0]:
                            if isinstance(item, dict):
                                if "team_key" in item:
                                    team_key = item["team_key"]
                                if "name" in item:
                                    team_name = item["name"]

                        if team_key:
                            self.teams[team_key] = team_name or "Unknown"

        except Exception as e:
            print(f"Error parsing teams: {e}")

    def get_initial_state(self) -> LeagueState:
        """Get the league state immediately after the draft (State 0)."""
        rosters: Dict[str, List[Player]] = {team_key: [] for team_key in self.teams}
        all_rostered = set()

        for pick in self.draft_picks:
            team_key = pick.get("team_key")
            player_key = pick.get("player_key")

            if team_key and player_key:
                # Get player info if available
                info = self.player_info.get(player_key, {})

                player = Player(
                    player_key=player_key,
                    name=info.get("name", f"Player {player_key}"),
                    team=info.get("team", ""),
                    position=info.get("position", ""),
                    fantasy_team_key=team_key,
                    fantasy_team_name=self.teams.get(team_key, "Unknown"),
                )

                if team_key in rosters:
                    rosters[team_key].append(player)
                all_rostered.add(player_key)

        # Get draft date from first transaction or use default
        draft_date = "2024-03-20"  # Default
        if self.transactions:
            # Find earliest transaction date
            draft_date = min(t.date for t in self.transactions)

        return LeagueState(
            date=draft_date,
            rosters=rosters,
            all_rostered_player_keys=all_rostered,
        )

    def get_state_at_date(self, target_date: str) -> LeagueState:
        """
        Reconstruct league state at a specific date.

        Args:
            target_date: YYYY-MM-DD format

        Returns:
            LeagueState with rosters as of that date
        """
        # Start with draft state
        state = self.get_initial_state()

        # Apply all transactions up to and including target_date
        for trans in self.transactions:
            if trans.date > target_date:
                break

            # Process drops first (player leaves team)
            for drop in trans.drops:
                player_key = drop.get("player_key")
                source_team = drop.get("source_team_key")

                if source_team and source_team in state.rosters:
                    state.rosters[source_team] = [
                        p for p in state.rosters[source_team]
                        if p.player_key != player_key
                    ]
                    state.all_rostered_player_keys.discard(player_key)

            # Process adds (player joins team)
            for add in trans.adds:
                player_key = add.get("player_key")
                dest_team = add.get("dest_team_key")

                if dest_team and dest_team in state.rosters:
                    # Get player info
                    info = self.player_info.get(player_key, {})

                    player = Player(
                        player_key=player_key,
                        name=add.get("name") or info.get("name", f"Player {player_key}"),
                        team=add.get("team") or info.get("team", ""),
                        position=add.get("position") or info.get("position", ""),
                        fantasy_team_key=dest_team,
                        fantasy_team_name=add.get("dest_team_name") or self.teams.get(dest_team, "Unknown"),
                    )

                    state.rosters[dest_team].append(player)
                    state.all_rostered_player_keys.add(player_key)

        state.date = target_date
        return state

    def get_free_agents(self, target_date: str, all_mlb_pitchers: Set[str]) -> List[str]:
        """
        Get available free agents (pitchers) at a specific date.

        Args:
            target_date: YYYY-MM-DD format
            all_mlb_pitchers: Set of all MLB pitcher player_keys

        Returns:
            List of player_keys that are free agents
        """
        state = self.get_state_at_date(target_date)
        return [pk for pk in all_mlb_pitchers if pk not in state.all_rostered_player_keys]

    def get_transactions_on_date(self, target_date: str) -> List[Transaction]:
        """Get all transactions that occurred on a specific date."""
        return [t for t in self.transactions if t.date == target_date]

    def get_streaming_adds(self, position_filter: str = "SP,RP,P") -> List[Dict]:
        """
        Get all streaming adds (pitcher adds from free agents).

        Returns:
            List of dicts with add details and context
        """
        streaming_adds = []
        positions = set(position_filter.split(","))

        for trans in self.transactions:
            for add in trans.adds:
                # Check if it's a pitcher
                player_pos = add.get("position", "")
                if not any(pos in player_pos for pos in positions):
                    continue

                streaming_adds.append({
                    "transaction_id": trans.transaction_id,
                    "date": trans.date,
                    "timestamp": trans.timestamp,
                    "player_key": add.get("player_key"),
                    "player_name": add.get("name"),
                    "player_team": add.get("team"),
                    "position": add.get("position"),
                    "fantasy_team_key": add.get("dest_team_key"),
                    "fantasy_team_name": add.get("dest_team_name"),
                })

        return streaming_adds


def parse_teams(teams_data: dict) -> Dict[str, str]:
    """Parse teams API response into team_key -> team_name mapping."""
    teams = {}
    try:
        content = teams_data.get("fantasy_content", {})
        league = content.get("league", [])

        if len(league) > 1:
            teams_section = league[1].get("teams", {})

            for key, value in teams_section.items():
                if key == "count":
                    continue

                team_info = value.get("team", [[]])
                if team_info and isinstance(team_info[0], list):
                    team_key = None
                    team_name = None
                    for item in team_info[0]:
                        if isinstance(item, dict):
                            if "team_key" in item:
                                team_key = item["team_key"]
                            if "name" in item:
                                team_name = item["name"]

                    if team_key:
                        teams[team_key] = team_name or "Unknown"

    except Exception as e:
        print(f"Error parsing teams: {e}")

    return teams


def test_state_reconstructor():
    """Test the state reconstructor."""
    print("=" * 60)
    print("STATE RECONSTRUCTOR TEST")
    print("=" * 60)

    # Test with 2024 data
    reconstructor = StateReconstructor(2024)

    # Get initial state (after draft)
    print("\n1. Initial state (after draft):")
    initial_state = reconstructor.get_initial_state()
    print(f"   Date: {initial_state.date}")
    print(f"   Teams: {len(initial_state.rosters)}")
    print(f"   Total rostered players: {len(initial_state.all_rostered_player_keys)}")

    # Show one team's roster
    if initial_state.rosters:
        first_team = list(initial_state.rosters.keys())[0]
        roster = initial_state.rosters[first_team]
        team_name = reconstructor.teams.get(first_team, "Unknown")
        print(f"\n   {team_name} roster ({len(roster)} players):")
        for p in roster[:5]:
            print(f"     - {p.name or p.player_key} ({p.position})")
        if len(roster) > 5:
            print(f"     ... and {len(roster) - 5} more")

    # Get state at mid-season
    print("\n2. State at mid-season (June 15):")
    mid_state = reconstructor.get_state_at_date("2024-06-15")
    print(f"   Total rostered players: {len(mid_state.all_rostered_player_keys)}")

    # Get state at end of season
    print("\n3. State at end of season (Sept 15):")
    end_state = reconstructor.get_state_at_date("2024-09-15")
    print(f"   Total rostered players: {len(end_state.all_rostered_player_keys)}")

    # Get streaming adds
    print("\n4. Streaming pitcher adds:")
    adds = reconstructor.get_streaming_adds()
    print(f"   Total streaming pitcher adds: {len(adds)}")
    if adds:
        print("\n   Sample adds:")
        for add in adds[:5]:
            print(f"     {add['date']}: {add['player_name']} ({add['player_team']}) -> {add['fantasy_team_name']}")

    print("\n" + "=" * 60)
    print("STATE RECONSTRUCTOR TEST COMPLETE")
    print("=" * 60)

    return reconstructor


if __name__ == "__main__":
    test_state_reconstructor()
