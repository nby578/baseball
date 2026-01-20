"""
Scheduled Monitoring Script for Fantasy Baseball Streaming

Run this script to start automated monitoring that:
1. Checks roster changes every N minutes
2. Alerts when watched players get picked up
3. Logs activity to file
4. Optionally sends Discord webhooks

Usage:
    python scheduled_monitor.py              # Run once
    python scheduled_monitor.py --continuous # Run continuously (every 5 min)
    python scheduled_monitor.py --interval 10 # Custom interval (minutes)

For Windows Task Scheduler:
    1. Open Task Scheduler
    2. Create Basic Task
    3. Trigger: Daily, repeat every 30 minutes
    4. Action: Start a program
       Program: python
       Arguments: "C:\\Users\\NoahYaffe\\Documents\\GitHub\\baseball\\live\\scheduled_monitor.py"
       Start in: C:\\Users\\NoahYaffe\\Documents\\GitHub\\baseball\\live
"""

import sys
import os
import json
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backtesting"))

# Set up logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def send_discord_alert(message: str, webhook_url: str = None):
    """Send alert to Discord webhook."""
    if not webhook_url:
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        logger.debug("No Discord webhook configured")
        return

    try:
        import requests
        response = requests.post(
            webhook_url,
            json={"content": message},
            timeout=10
        )
        if response.status_code == 204:
            logger.info("Discord alert sent")
        else:
            logger.warning(f"Discord alert failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Discord alert error: {e}")


def run_check():
    """Run a single monitoring check."""
    logger.info("=" * 50)
    logger.info("Starting roster check...")

    try:
        from live_roster_monitor import RosterMonitor

        monitor = RosterMonitor(season=2025)
        changes = monitor.check_for_changes()

        if changes:
            logger.info(f"Detected {len(changes)} roster changes!")

            # Log each change
            for c in changes:
                logger.info(f"  {c.change_type.upper()}: {c.fantasy_team} - {c.player_name}")

            # Check for watched players
            watched = monitor._state.watched_players if monitor._state else set()
            watched_changes = [c for c in changes if c.player_name in watched]

            if watched_changes:
                alert_msg = "STREAMING ALERT!\n\n"
                for c in watched_changes:
                    alert_msg += f"  {c.player_name} was {c.change_type}ed by {c.fantasy_team}\n"

                logger.warning(alert_msg)
                send_discord_alert(alert_msg)

            # Print changes
            monitor.print_changes(changes)
        else:
            logger.info("No roster changes detected")

        # Get watched player status
        status = monitor.get_watched_player_status()
        available = [p for p, s in status.items() if s == "Available"]

        if available:
            logger.info(f"Available targets: {', '.join(available[:5])}")

        return changes

    except Exception as e:
        logger.error(f"Check failed: {e}", exc_info=True)
        return []


def run_continuous(interval_minutes: int = 5):
    """Run monitoring continuously."""
    logger.info(f"Starting continuous monitoring (every {interval_minutes} min)")
    logger.info("Press Ctrl+C to stop")

    while True:
        try:
            run_check()
            logger.info(f"Next check in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(60)  # Wait 1 min on error


def main():
    parser = argparse.ArgumentParser(description="Fantasy Baseball Streaming Monitor")
    parser.add_argument(
        "--continuous", "-c",
        action="store_true",
        help="Run continuously"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=5,
        help="Check interval in minutes (default: 5)"
    )
    parser.add_argument(
        "--discord",
        type=str,
        help="Discord webhook URL for alerts"
    )

    args = parser.parse_args()

    if args.discord:
        os.environ["DISCORD_WEBHOOK_URL"] = args.discord

    if args.continuous:
        run_continuous(args.interval)
    else:
        run_check()


if __name__ == "__main__":
    main()
