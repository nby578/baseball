"""
Yahoo Fantasy API Data Fetcher for Backtesting

Uses existing OAuth setup from fantasy-bot project.
Fetches transactions, draft results, matchups via API.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add fantasy-bot to path for auth
FANTASY_BOT_PATH = Path(r"C:\Users\NoahYaffe\Documents\GitHub\Claude_Projects\FBB\fantasy-bot")
sys.path.insert(0, str(FANTASY_BOT_PATH))

from auth import get_oauth_session

# League info
LEAGUES = {
    2024: {"name": "Big League Jew IX", "id": 95829, "game_key": "422"},
    2025: {"name": "Big League Jew X", "id": 89318, "game_key": "431"},
}

BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2"


class YahooFetcher:
    """Fetch fantasy baseball data from Yahoo API."""

    def __init__(self, year: int = 2024):
        self.year = year
        self.league_info = LEAGUES.get(year)
        if not self.league_info:
            raise ValueError(f"Unknown year: {year}")

        self.league_key = f"{self.league_info['game_key']}.l.{self.league_info['id']}"
        self.oauth = None

    def connect(self):
        """Establish OAuth connection."""
        print(f"Connecting to Yahoo API for {self.league_info['name']} ({self.year})...")
        self.oauth = get_oauth_session()
        print("Connected!")
        return self

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make authenticated GET request."""
        if not self.oauth:
            self.connect()

        url = f"{BASE_URL}{endpoint}"
        default_params = {"format": "json"}
        if params:
            default_params.update(params)

        response = self.oauth.session.get(url, params=default_params)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text[:500]}")
            return None

        return response.json()

    def get_league_info(self) -> dict:
        """Get basic league information."""
        endpoint = f"/league/{self.league_key}"
        return self._get(endpoint)

    def get_transactions(self, trans_type: str = None) -> dict:
        """
        Get all transactions for the league.

        Args:
            trans_type: Filter by type - 'add', 'drop', 'trade', 'add/drop', or None for all
        """
        endpoint = f"/league/{self.league_key}/transactions"
        params = {}
        if trans_type:
            params["type"] = trans_type

        return self._get(endpoint, params)

    def get_draft_results(self) -> dict:
        """Get complete draft results."""
        endpoint = f"/league/{self.league_key}/draftresults"
        return self._get(endpoint)

    def get_teams(self) -> dict:
        """Get all teams in the league."""
        endpoint = f"/league/{self.league_key}/teams"
        return self._get(endpoint)

    def get_standings(self) -> dict:
        """Get league standings."""
        endpoint = f"/league/{self.league_key}/standings"
        return self._get(endpoint)

    def get_matchups(self, week: int = None) -> dict:
        """Get matchup results for a specific week or all weeks."""
        if week:
            endpoint = f"/league/{self.league_key}/scoreboard;week={week}"
        else:
            endpoint = f"/league/{self.league_key}/scoreboard"
        return self._get(endpoint)

    def get_team_roster(self, team_key: str, date: str = None) -> dict:
        """
        Get a team's roster, optionally as of a specific date.

        Args:
            team_key: e.g., "422.l.95829.t.7"
            date: YYYY-MM-DD format
        """
        endpoint = f"/team/{team_key}/roster"
        if date:
            endpoint += f";date={date}"
        return self._get(endpoint)

    def get_player_stats(self, player_keys: list, stat_type: str = "season") -> dict:
        """
        Get stats for specific players.

        Args:
            player_keys: List of player keys
            stat_type: 'season', 'date', 'week', etc.
        """
        player_str = ",".join(player_keys)
        endpoint = f"/players;player_keys={player_str}/stats;type={stat_type}"
        return self._get(endpoint)

    def get_league_settings(self) -> dict:
        """Get league settings including scoring rules."""
        endpoint = f"/league/{self.league_key}/settings"
        return self._get(endpoint)

    def get_all_team_keys(self) -> list:
        """Get all team keys in the league."""
        teams_data = self.get_teams()
        if not teams_data:
            return []

        team_keys = []
        try:
            content = teams_data.get("fantasy_content", {})
            league = content.get("league", [])
            if len(league) > 1:
                teams = league[1].get("teams", {})
                for key, value in teams.items():
                    if key == "count":
                        continue
                    team_info = value.get("team", [[]])
                    if team_info and isinstance(team_info[0], list):
                        for item in team_info[0]:
                            if isinstance(item, dict) and "team_key" in item:
                                team_keys.append(item["team_key"])
                                break
        except Exception as e:
            print(f"Error parsing team keys: {e}")

        return team_keys

    def get_all_rosters(self, date: str = None) -> dict:
        """
        Get all team rosters for a specific date.

        Args:
            date: YYYY-MM-DD format, or None for current

        Returns:
            Dict mapping team_key -> list of player dicts
        """
        team_keys = self.get_all_team_keys()
        rosters = {}

        for team_key in team_keys:
            roster_data = self.get_team_roster(team_key, date)
            if roster_data:
                players = self._parse_roster(roster_data)
                rosters[team_key] = players

        return rosters

    def _parse_roster(self, roster_data: dict) -> list:
        """Parse roster API response into clean player list."""
        players = []
        try:
            content = roster_data.get("fantasy_content", {})
            team_data = content.get("team", [])

            if len(team_data) > 1:
                roster = team_data[1].get("roster", {})
                coverage_type = roster.get("coverage_type", "date")
                players_data = roster.get("0", {}).get("players", {})

                for key, value in players_data.items():
                    if key == "count":
                        continue

                    player_info = value.get("player", [])
                    if len(player_info) >= 2:
                        # Parse player details from nested list
                        info_list = player_info[0]
                        selected_pos = player_info[1].get("selected_position", [{}])
                        position = selected_pos[1].get("position", "BN") if len(selected_pos) > 1 else "BN"

                        player = {}
                        if isinstance(info_list, list):
                            for item in info_list:
                                if isinstance(item, dict):
                                    if "player_key" in item:
                                        player["player_key"] = item["player_key"]
                                    if "name" in item:
                                        name_data = item["name"]
                                        player["name"] = name_data.get("full", str(name_data))
                                    if "editorial_team_abbr" in item:
                                        player["team"] = item["editorial_team_abbr"]
                                    if "display_position" in item:
                                        player["eligible_positions"] = item["display_position"]
                                    if "status" in item:
                                        player["status"] = item["status"]  # IL, DTD, etc.

                        player["selected_position"] = position
                        player["is_starting"] = position not in ("BN", "IL", "IL+", "NA")
                        players.append(player)

        except Exception as e:
            print(f"Error parsing roster: {e}")
            import traceback
            traceback.print_exc()

        return players

    def get_players_info(self, player_keys: list) -> dict:
        """
        Get player information (name, team, position) for player keys.

        Args:
            player_keys: List of player keys

        Returns:
            Dict mapping player_key -> player info dict
        """
        if not player_keys:
            return {}

        # Yahoo API limits to 25 players per request
        all_players = {}
        for i in range(0, len(player_keys), 25):
            batch = player_keys[i:i+25]
            player_str = ",".join(batch)
            endpoint = f"/players;player_keys={player_str}"
            data = self._get(endpoint)

            if data:
                parsed = self._parse_players_info(data)
                all_players.update(parsed)

        return all_players

    def _parse_players_info(self, data: dict) -> dict:
        """Parse players API response."""
        players = {}
        try:
            content = data.get("fantasy_content", {})
            players_data = content.get("players", {})

            for key, value in players_data.items():
                if key == "count":
                    continue

                player_info = value.get("player", [])
                if player_info:
                    info_list = player_info[0] if isinstance(player_info[0], list) else player_info

                    player = {}
                    for item in info_list:
                        if isinstance(item, dict):
                            if "player_key" in item:
                                player["player_key"] = item["player_key"]
                            if "name" in item:
                                name_data = item["name"]
                                player["name"] = name_data.get("full", str(name_data))
                            if "editorial_team_abbr" in item:
                                player["team"] = item["editorial_team_abbr"]
                            if "display_position" in item:
                                player["position"] = item["display_position"]

                    if player.get("player_key"):
                        players[player["player_key"]] = player

        except Exception as e:
            print(f"Error parsing players info: {e}")

        return players


def parse_transactions(data: dict) -> list:
    """Parse transaction data into clean list."""
    transactions = []

    try:
        content = data.get("fantasy_content", {})
        league = content.get("league", [])

        # Navigate nested structure
        if len(league) > 1:
            trans_data = league[1].get("transactions", {})

            for key, value in trans_data.items():
                if key == "count":
                    continue

                trans = value.get("transaction", [])
                if len(trans) >= 2:
                    meta = trans[0]
                    players = trans[1].get("players", {})

                    trans_record = {
                        "transaction_id": meta.get("transaction_id"),
                        "type": meta.get("type"),
                        "timestamp": meta.get("timestamp"),
                        "status": meta.get("status"),
                        "players": []
                    }

                    # Parse players in transaction
                    for pkey, pval in players.items():
                        if pkey == "count":
                            continue
                        player_data = pval.get("player", [])
                        if len(player_data) >= 2:
                            # Player info is in a nested list
                            player_info_list = player_data[0]
                            if isinstance(player_info_list, list):
                                # Flatten the player info
                                player_info = {}
                                for item in player_info_list:
                                    if isinstance(item, dict):
                                        player_info.update(item)

                                # Transaction data is also in a list
                                trans_data_section = player_data[1].get("transaction_data", [])
                                trans_info = {}
                                if isinstance(trans_data_section, list) and trans_data_section:
                                    trans_info = trans_data_section[0] if trans_data_section else {}
                                elif isinstance(trans_data_section, dict):
                                    trans_info = trans_data_section

                                # Get player name
                                name_info = player_info.get("name", {})
                                player_name = name_info.get("full") if isinstance(name_info, dict) else str(name_info)

                                trans_record["players"].append({
                                    "player_key": player_info.get("player_key"),
                                    "name": player_name,
                                    "team": player_info.get("editorial_team_abbr"),
                                    "position": player_info.get("display_position"),
                                    "type": trans_info.get("type"),  # 'add' or 'drop'
                                    "source_type": trans_info.get("source_type"),
                                    "destination_type": trans_info.get("destination_type"),
                                    "destination_team_key": trans_info.get("destination_team_key"),
                                    "destination_team_name": trans_info.get("destination_team_name"),
                                    "source_team_key": trans_info.get("source_team_key"),
                                    "source_team_name": trans_info.get("source_team_name"),
                                })

                    transactions.append(trans_record)

    except Exception as e:
        print(f"Error parsing transactions: {e}")
        import traceback
        traceback.print_exc()

    return transactions


def save_data(data: dict, filename: str):
    """Save data to JSON file."""
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved to {filepath}")
    return filepath


def get_user_leagues(oauth):
    """Get all MLB leagues the user is in to find correct game keys."""
    print("\nFetching user's MLB leagues...")
    url = f"{BASE_URL}/users;use_login=1/games;game_codes=mlb/leagues"
    response = oauth.session.get(url, params={"format": "json"})

    if response.status_code == 200:
        data = response.json()
        save_data(data, "user_leagues_raw.json")

        # Parse to find league keys
        try:
            content = data.get("fantasy_content", {})
            users = content.get("users", {})
            user_data = users.get("0", {}).get("user", [])

            if len(user_data) > 1:
                games = user_data[1].get("games", {})
                leagues_found = []

                for gkey, gval in games.items():
                    if gkey == "count":
                        continue
                    game = gval.get("game", [])
                    if len(game) > 1:
                        game_info = game[0]
                        leagues = game[1].get("leagues", {})

                        for lkey, lval in leagues.items():
                            if lkey == "count":
                                continue
                            league = lval.get("league", [])
                            if league:
                                league_info = league[0]
                                leagues_found.append({
                                    "game_key": game_info.get("game_key"),
                                    "season": game_info.get("season"),
                                    "league_key": league_info.get("league_key"),
                                    "league_id": league_info.get("league_id"),
                                    "name": league_info.get("name"),
                                })

                return leagues_found

        except Exception as e:
            print(f"Error parsing leagues: {e}")

    return []


def test_connection():
    """Test the Yahoo API connection."""
    print("=" * 60)
    print("YAHOO FANTASY API - CONNECTION TEST")
    print("=" * 60)

    try:
        # First, get OAuth session
        from auth import get_oauth_session
        oauth = get_oauth_session()
        print("Connected!")

        # Find user's actual leagues to get correct game keys
        leagues = get_user_leagues(oauth)

        if leagues:
            print(f"\nFound {len(leagues)} MLB leagues:")
            for league in leagues:
                print(f"  {league['season']} - {league['name']}")
                print(f"    League Key: {league['league_key']}")
                print(f"    Game Key: {league['game_key']}")

            save_data(leagues, "user_leagues_parsed.json")

            # Find Big League Jew leagues specifically
            blj_leagues = [l for l in leagues if "Big League Jew" in l['name']]
            print(f"\nBig League Jew leagues: {len(blj_leagues)}")

            # Use the most recent BLJ league
            test_league = blj_leagues[-1] if blj_leagues else leagues[0]
            print(f"\nTesting with league: {test_league['name']} ({test_league['season']})")

            # Try fetching transactions for this league
            endpoint = f"/league/{test_league['league_key']}/transactions"
            url = f"{BASE_URL}{endpoint}"
            response = oauth.session.get(url, params={"format": "json"})

            if response.status_code == 200:
                trans_data = response.json()
                save_data(trans_data, f"transactions_raw_{test_league['season']}.json")
                print(f"\n[OK] Successfully fetched transactions!")

                # Parse
                parsed = parse_transactions(trans_data)
                print(f"Found {len(parsed)} transactions")

                if parsed:
                    save_data(parsed, f"transactions_parsed_{test_league['season']}.json")
                    print("\nFirst 3 transactions:")
                    for t in parsed[:3]:
                        ts = datetime.fromtimestamp(int(t['timestamp']))
                        players = ", ".join([f"{p['name']} ({p['type']})" for p in t['players']])
                        print(f"  {ts.strftime('%Y-%m-%d %H:%M')} - {t['type']}: {players}")

                return True
            else:
                print(f"\n[X] Failed to fetch transactions: {response.status_code}")
                print(response.text[:500])

        else:
            print("\n[X] No leagues found")
            return False

    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def fetch_all_blj_data():
    """Fetch all data from Big League Jew leagues for backtesting."""
    print("=" * 60)
    print("FETCHING ALL BIG LEAGUE JEW DATA")
    print("=" * 60)

    from auth import get_oauth_session
    oauth = get_oauth_session()
    print("Connected!")

    # Get user's leagues
    leagues = get_user_leagues(oauth)
    blj_leagues = [l for l in leagues if "Big League Jew" in l['name']]

    print(f"\nFound {len(blj_leagues)} Big League Jew leagues")

    all_data = {}

    for league in blj_leagues:
        season = league['season']
        name = league['name']
        league_key = league['league_key']

        print(f"\n{'='*40}")
        print(f"Processing: {name} ({season})")
        print(f"League Key: {league_key}")
        print(f"{'='*40}")

        league_data = {
            "info": league,
            "transactions": [],
            "draft": None,
        }

        # Fetch transactions
        print("  Fetching transactions...")
        endpoint = f"/league/{league_key}/transactions"
        url = f"{BASE_URL}{endpoint}"
        response = oauth.session.get(url, params={"format": "json"})

        if response.status_code == 200:
            trans_raw = response.json()
            save_data(trans_raw, f"transactions_raw_{season}_{name.replace(' ', '_')}.json")
            parsed = parse_transactions(trans_raw)
            league_data["transactions"] = parsed
            print(f"  -> Found {len(parsed)} transactions")
            save_data(parsed, f"transactions_parsed_{season}_{name.replace(' ', '_')}.json")
        else:
            print(f"  -> Failed: {response.status_code}")

        # Fetch draft results
        print("  Fetching draft results...")
        endpoint = f"/league/{league_key}/draftresults"
        url = f"{BASE_URL}{endpoint}"
        response = oauth.session.get(url, params={"format": "json"})

        if response.status_code == 200:
            draft_raw = response.json()
            save_data(draft_raw, f"draft_raw_{season}_{name.replace(' ', '_')}.json")
            print(f"  -> Draft data saved")
        else:
            print(f"  -> Failed: {response.status_code}")

        # Fetch teams
        print("  Fetching teams...")
        endpoint = f"/league/{league_key}/teams"
        url = f"{BASE_URL}{endpoint}"
        response = oauth.session.get(url, params={"format": "json"})

        if response.status_code == 200:
            teams_raw = response.json()
            save_data(teams_raw, f"teams_raw_{season}_{name.replace(' ', '_')}.json")
            print(f"  -> Teams data saved")
        else:
            print(f"  -> Failed: {response.status_code}")

        # Fetch standings
        print("  Fetching standings...")
        endpoint = f"/league/{league_key}/standings"
        url = f"{BASE_URL}{endpoint}"
        response = oauth.session.get(url, params={"format": "json"})

        if response.status_code == 200:
            standings_raw = response.json()
            save_data(standings_raw, f"standings_raw_{season}_{name.replace(' ', '_')}.json")
            print(f"  -> Standings data saved")
        else:
            print(f"  -> Failed: {response.status_code}")

        all_data[f"{season}_{name}"] = league_data

    print("\n" + "=" * 60)
    print("DATA FETCH COMPLETE!")
    print("=" * 60)

    # Summary
    total_trans = sum(len(d["transactions"]) for d in all_data.values())
    print(f"\nTotal transactions across all leagues: {total_trans}")

    return all_data


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        fetch_all_blj_data()
    else:
        test_connection()
