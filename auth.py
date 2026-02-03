"""
Yahoo Fantasy API Authentication

First run: Opens browser for Yahoo authorization
Subsequent runs: Uses saved tokens (auto-refreshes if expired)
"""
import json
from pathlib import Path
from yahoo_oauth import OAuth2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

PROJECT_DIR = Path(__file__).parent
TOKEN_FILE = PROJECT_DIR / "oauth2.json"


def setup_oauth_file():
    """Create the OAuth2 credentials file from environment variables."""
    client_id = os.getenv("YAHOO_CLIENT_ID")
    client_secret = os.getenv("YAHOO_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Missing YAHOO_CLIENT_ID or YAHOO_CLIENT_SECRET in .env file")

    credentials = {
        "consumer_key": client_id,
        "consumer_secret": client_secret
    }

    with open(TOKEN_FILE, "w") as f:
        json.dump(credentials, f, indent=2)

    print(f"Created {TOKEN_FILE}")
    return TOKEN_FILE


def get_oauth_session():
    """
    Get an authenticated OAuth2 session for Yahoo Fantasy API.

    Returns:
        OAuth2 session object
    """
    # Create credentials file if it doesn't exist
    if not TOKEN_FILE.exists():
        setup_oauth_file()

    # Check if we only have credentials (no tokens yet)
    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)

    if "access_token" not in data:
        print("\nNo access token found. Starting OAuth flow...")
        print("A browser window will open for Yahoo authorization.\n")

    # Create OAuth2 session
    oauth = OAuth2(None, None, from_file=str(TOKEN_FILE))

    if not oauth.token_is_valid():
        oauth.refresh_access_token()

    return oauth


def test_connection():
    """Test the Yahoo API connection by fetching user's leagues."""
    print("=" * 50)
    print("Yahoo Fantasy API Connection Test")
    print("=" * 50)

    try:
        oauth = get_oauth_session()

        # Test API call - get user's MLB leagues
        print("\nFetching your MLB fantasy leagues...")
        url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_codes=mlb/leagues"
        response = oauth.session.get(url, params={"format": "json"})

        if response.status_code == 200:
            print("\n[OK] Connection successful!")
            data = response.json()

            # Try to extract league info
            try:
                users = data.get("fantasy_content", {}).get("users", {})
                if users:
                    print("\nYour MLB Fantasy Leagues:")
                    print("-" * 30)
                    # Parse the nested structure
                    print(json.dumps(data, indent=2)[:1500])
            except Exception as e:
                print(f"Could not parse leagues: {e}")
                print("\nRaw response (truncated):")
                print(json.dumps(data, indent=2)[:1000])

            return True
        else:
            print(f"\n[FAIL] Connection failed: HTTP {response.status_code}")
            print(response.text[:500])
            return False

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        return False


if __name__ == "__main__":
    test_connection()
