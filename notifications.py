"""
Discord Webhook Notifications

Free, unlimited messages.
Setup: Create a webhook in Discord server settings.
"""
import requests
import json
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_discord_message(
    content: str,
    username: str = "Fantasy Baseball Bot",
    embed: Optional[dict] = None
) -> bool:
    """
    Send a message to Discord webhook.

    Args:
        content: Message text
        username: Bot display name
        embed: Optional rich embed dict

    Returns:
        True if successful
    """
    if not DISCORD_WEBHOOK_URL:
        print("Warning: DISCORD_WEBHOOK_URL not set in .env")
        return False

    payload = {
        "username": username,
        "content": content,
    }

    if embed:
        payload["embeds"] = [embed]

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    return response.status_code == 204


def send_alert(
    title: str,
    message: str,
    alert_type: str = "info",
    fields: Optional[list] = None
) -> bool:
    """
    Send a formatted alert to Discord.

    Args:
        title: Alert title
        message: Alert description
        alert_type: "info", "warning", "error", "success"
        fields: List of {"name": str, "value": str, "inline": bool}

    Returns:
        True if successful
    """
    colors = {
        "info": 3447003,      # Blue
        "warning": 16776960,  # Yellow
        "error": 15158332,    # Red
        "success": 3066993,   # Green
    }

    embed = {
        "title": title,
        "description": message,
        "color": colors.get(alert_type, colors["info"]),
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Fantasy Baseball Bot"}
    }

    if fields:
        embed["fields"] = fields

    return send_discord_message("", embed=embed)


def alert_il_activation(player_name: str, team: str, action: str) -> bool:
    """
    Alert when a player's IL status changes.

    Args:
        player_name: Player name
        team: Team abbreviation
        action: "activated" or "placed_on_il"
    """
    if action == "activated":
        title = "🟢 IL Activation"
        message = f"**{player_name}** ({team}) has been activated from the IL!"
        alert_type = "success"
    else:
        title = "🔴 Placed on IL"
        message = f"**{player_name}** ({team}) has been placed on the IL."
        alert_type = "warning"

    return send_alert(title, message, alert_type)


def alert_lineup_issue(issues: list) -> bool:
    """
    Alert about lineup problems (injured starter, empty slot, etc.)

    Args:
        issues: List of issue descriptions
    """
    fields = [{"name": f"Issue {i+1}", "value": issue, "inline": False}
              for i, issue in enumerate(issues)]

    return send_alert(
        "⚠️ Lineup Issues Detected",
        "The following problems were found with your roster:",
        "warning",
        fields
    )


def alert_streaming_recommendation(pitchers: list) -> bool:
    """
    Send streaming pitcher recommendations.

    Args:
        pitchers: List of {"name", "team", "opponent", "score"} dicts
    """
    fields = []
    for i, p in enumerate(pitchers[:5], 1):
        fields.append({
            "name": f"#{i} - {p['name']} ({p['team']})",
            "value": f"vs {p['opponent']} | Score: {p['score']:.1f}",
            "inline": False
        })

    return send_alert(
        "📊 Streaming Pitcher Recommendations",
        "Top available pitchers for today:",
        "info",
        fields
    )


def alert_waiver_target(player_name: str, reason: str, owned_pct: float) -> bool:
    """
    Alert about a waiver wire target.

    Args:
        player_name: Player to target
        reason: Why they're recommended
        owned_pct: Current ownership percentage
    """
    return send_alert(
        "🎯 Waiver Wire Target",
        f"**{player_name}** ({owned_pct:.0f}% owned)\n\n{reason}",
        "info"
    )


def daily_summary(
    lineup_status: str,
    games_today: int,
    pitchers_starting: list,
    alerts: list
) -> bool:
    """
    Send daily morning summary.

    Args:
        lineup_status: "OK" or description of issues
        games_today: Number of games
        pitchers_starting: List of your pitchers with starts today
        alerts: List of important notes
    """
    fields = [
        {"name": "📋 Lineup Status", "value": lineup_status, "inline": True},
        {"name": "🏟️ Games Today", "value": str(games_today), "inline": True},
    ]

    if pitchers_starting:
        fields.append({
            "name": "⚾ Your Starters",
            "value": "\n".join(pitchers_starting) or "None",
            "inline": False
        })

    if alerts:
        fields.append({
            "name": "⚠️ Alerts",
            "value": "\n".join(alerts) or "None",
            "inline": False
        })

    return send_alert(
        "☀️ Daily Fantasy Baseball Summary",
        f"Good morning! Here's your fantasy update for {datetime.now().strftime('%A, %B %d')}",
        "info",
        fields
    )


if __name__ == "__main__":
    print("=== Discord Notification Test ===\n")

    if not DISCORD_WEBHOOK_URL:
        print("Set DISCORD_WEBHOOK_URL in .env to test notifications")
        print("\nTo create a webhook:")
        print("1. Go to Discord server settings")
        print("2. Integrations -> Webhooks -> New Webhook")
        print("3. Copy webhook URL to .env file")
    else:
        print("Sending test message...")
        success = send_alert(
            "🧪 Test Alert",
            "Fantasy Baseball Bot is connected!",
            "success"
        )
        print(f"Result: {'Success!' if success else 'Failed'}")
