"""
Configuration for Fantasy Baseball Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Yahoo API credentials
YAHOO_CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
YAHOO_CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
YAHOO_LEAGUE_ID = os.getenv("YAHOO_LEAGUE_ID")

# Sport and game settings
SPORT = "mlb"
GAME_CODE = "mlb"

# Notification settings
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Schedule settings (times in ET)
LINEUP_CHECK_TIMES = ["07:00", "14:00", "18:00"]  # 7 AM, 2 PM, 6 PM
INJURY_CHECK_INTERVAL_HOURS = 4
WAIVER_CHECK_TIMES = ["08:00", "22:00"]  # 8 AM, 10 PM
