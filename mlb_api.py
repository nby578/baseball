"""
MLB Stats API Integration

Free, no authentication required.
Provides: injuries, lineups, schedules, game status
Docs: https://statsapi.mlb.com
"""
import requests
from datetime import datetime, timedelta
from typing import Optional

BASE_URL = "https://statsapi.mlb.com/api/v1"


def get_todays_games(date: Optional[str] = None) -> list:
    """
    Get all MLB games for a given date.

    Args:
        date: YYYY-MM-DD format, defaults to today

    Returns:
        List of game dicts with teams, time, status
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/schedule"
    params = {
        "sportId": 1,  # MLB
        "date": date,
        "hydrate": "team,probablePitcher"
    }

    response = requests.get(url, params=params)
    data = response.json()

    games = []
    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            game_info = {
                "game_id": game["gamePk"],
                "status": game["status"]["detailedState"],
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_abbrev": game["teams"]["home"]["team"].get("abbreviation", ""),
                "away_abbrev": game["teams"]["away"]["team"].get("abbreviation", ""),
                "game_time": game.get("gameDate"),
                "venue": game.get("venue", {}).get("name", ""),
            }

            # Probable pitchers
            home_pitcher = game["teams"]["home"].get("probablePitcher", {})
            away_pitcher = game["teams"]["away"].get("probablePitcher", {})
            game_info["home_pitcher"] = home_pitcher.get("fullName", "TBD")
            game_info["away_pitcher"] = away_pitcher.get("fullName", "TBD")
            game_info["home_pitcher_id"] = home_pitcher.get("id")
            game_info["away_pitcher_id"] = away_pitcher.get("id")

            games.append(game_info)

    return games


def get_injuries() -> list:
    """
    Get current MLB injury list.

    Returns:
        List of injured players with status
    """
    url = f"{BASE_URL}/injuries"
    params = {"sportId": 1}

    response = requests.get(url, params=params)
    data = response.json()

    injuries = []
    for player in data.get("injuries", []):
        injuries.append({
            "player_id": player.get("playerId"),
            "player_name": player.get("playerName", "Unknown"),
            "team": player.get("team", {}).get("name", "Unknown"),
            "team_abbrev": player.get("team", {}).get("abbreviation", ""),
            "injury_type": player.get("description", "Unknown"),
            "status": player.get("status", "Unknown"),
            "date": player.get("date"),
        })

    return injuries


def get_player_info(player_id: int) -> dict:
    """
    Get detailed info for a specific player.

    Args:
        player_id: MLB player ID

    Returns:
        Player info dict
    """
    url = f"{BASE_URL}/people/{player_id}"
    params = {"hydrate": "stats(group=[hitting,pitching],type=season)"}

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("people"):
        return data["people"][0]
    return {}


def get_team_roster(team_id: int) -> list:
    """
    Get current roster for a team.

    Args:
        team_id: MLB team ID

    Returns:
        List of players on roster
    """
    url = f"{BASE_URL}/teams/{team_id}/roster"
    params = {"rosterType": "active"}

    response = requests.get(url, params=params)
    data = response.json()

    players = []
    for player in data.get("roster", []):
        players.append({
            "player_id": player["person"]["id"],
            "name": player["person"]["fullName"],
            "position": player.get("position", {}).get("abbreviation", ""),
            "status": player.get("status", {}).get("description", "Active"),
        })

    return players


def get_standings() -> dict:
    """
    Get current MLB standings.

    Returns:
        Dict with division standings
    """
    url = f"{BASE_URL}/standings"
    params = {
        "leagueId": "103,104",  # AL and NL
        "season": datetime.now().year,
        "standingsTypes": "regularSeason"
    }

    response = requests.get(url, params=params)
    return response.json()


def search_player(name: str, active_only: bool = True) -> list:
    """
    Search for a player by name.

    Args:
        name: Player name to search (case-insensitive partial match)
        active_only: Only return players on active rosters

    Returns:
        List of matching players
    """
    # Use the people/search endpoint for better results
    url = f"{BASE_URL}/people/search"
    params = {
        "names": name,
        "sportIds": 1,
        "hydrate": "currentTeam"
    }

    response = requests.get(url, params=params)
    data = response.json()

    players = []
    search_lower = name.lower()

    for player in data.get("people", []):
        player_name = player.get("fullName", "")
        # Filter to players whose name contains the search term
        if search_lower in player_name.lower():
            team = player.get("currentTeam", {})
            if active_only and not team:
                continue
            players.append({
                "player_id": player["id"],
                "name": player_name,
                "team": team.get("name", "Free Agent"),
                "team_abbrev": team.get("abbreviation", ""),
                "position": player.get("primaryPosition", {}).get("abbreviation", ""),
                "active": player.get("active", False),
            })

    return players[:20]  # Limit results


# Team ID mapping (for convenience)
TEAM_IDS = {
    "ARI": 109, "ATL": 144, "BAL": 110, "BOS": 111, "CHC": 112,
    "CHW": 145, "CIN": 113, "CLE": 114, "COL": 115, "DET": 116,
    "HOU": 117, "KC": 118, "LAA": 108, "LAD": 119, "MIA": 146,
    "MIL": 158, "MIN": 142, "NYM": 121, "NYY": 147, "OAK": 133,
    "PHI": 143, "PIT": 134, "SD": 135, "SF": 137, "SEA": 136,
    "STL": 138, "TB": 139, "TEX": 140, "TOR": 141, "WSH": 120,
}


if __name__ == "__main__":
    print("=== MLB Stats API Test ===\n")

    # Test: Today's games
    print("Today's Games:")
    print("-" * 40)
    games = get_todays_games()
    if games:
        for g in games[:5]:  # Show first 5
            print(f"  {g['away_team']} @ {g['home_team']} - {g['status']}")
            print(f"    Pitchers: {g['away_pitcher']} vs {g['home_pitcher']}")
    else:
        print("  No games today (offseason)")

    print("\n" + "=" * 40)
    print("\nInjury List (first 10):")
    print("-" * 40)
    injuries = get_injuries()
    for inj in injuries[:10]:
        print(f"  {inj['player_name']} ({inj['team_abbrev']}) - {inj['status']}")
        print(f"    {inj['injury_type']}")

    print("\n" + "=" * 40)
    print("\nPlayer Search: 'Ohtani'")
    print("-" * 40)
    results = search_player("Ohtani")
    for p in results:
        print(f"  {p['name']} - {p['team']} ({p['position']})")
