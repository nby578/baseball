#!/usr/bin/env python3
"""
Daily Fantasy Baseball Check

Runs all monitoring checks and sends alerts.
Designed to run via GitHub Actions or local cron.
"""
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from mlb_api import get_todays_games, get_injuries
from notifications import daily_summary, send_alert
from streaming import get_streaming_targets, rank_opponents_for_week

load_dotenv()

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def run_mlb_checks() -> dict:
    """Run MLB API checks (no Yahoo auth needed)."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'games_today': [],
        'injuries': [],
        'streaming_options': [],
    }

    print("Fetching today's games...")
    games = get_todays_games()
    results['games_today'] = games
    print(f"  Found {len(games)} games")

    print("Fetching injury list...")
    injuries = get_injuries()
    results['injuries'] = injuries[:50]  # Limit for storage
    print(f"  Found {len(injuries)} injuries")

    print("Calculating streaming options...")
    streamers = get_streaming_targets(min_score=35.0)
    results['streaming_options'] = [
        {
            'name': s.name,
            'team': s.team,
            'opponent': s.opponent,
            'score': s.score,
        }
        for s in streamers[:15]
    ]
    print(f"  Found {len(streamers)} streaming candidates")

    return results


def run_yahoo_checks() -> dict:
    """Run Yahoo Fantasy API checks (requires auth)."""
    results = {
        'roster_issues': [],
        'il_candidates': {'to_il': [], 'from_il': []},
        'your_starters': [],
    }

    # Check if we have OAuth credentials
    oauth_file = Path(__file__).parent / "oauth2.json"
    if not oauth_file.exists():
        print("Skipping Yahoo checks (no oauth2.json)")
        return results

    try:
        from roster_monitor import RosterMonitor

        league_id = os.getenv("YAHOO_LEAGUE_ID", "89318")
        monitor = RosterMonitor(league_id)

        if monitor.connect():
            print("Running Yahoo roster checks...")
            check_results = monitor.run_daily_check()
            results['roster_issues'] = check_results.get('issues', [])
            results['il_candidates'] = check_results.get('il_moves', {})
            results['your_starters'] = check_results.get('starters_today', [])
        else:
            print("Yahoo connection failed")

    except Exception as e:
        print(f"Yahoo check error: {e}")

    return results


def generate_summary(mlb_results: dict, yahoo_results: dict) -> str:
    """Generate human-readable summary."""
    lines = []
    lines.append("=" * 50)
    lines.append(f"Fantasy Baseball Daily Check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 50)

    # Games today
    games = mlb_results.get('games_today', [])
    lines.append(f"\n[GAMES] Games Today: {len(games)}")

    # Top streaming options
    streamers = mlb_results.get('streaming_options', [])
    if streamers:
        lines.append("\n[STREAM] Top Streaming Pitchers:")
        for i, s in enumerate(streamers[:5], 1):
            lines.append(f"  {i}. {s['name']} ({s['team']}) {s['opponent']} - Score: {s['score']:.1f}")

    # Roster issues
    issues = yahoo_results.get('roster_issues', [])
    if issues:
        lines.append("\n[ALERT] Roster Issues:")
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("\n[OK] No roster issues found")

    # IL moves needed
    il = yahoo_results.get('il_candidates', {})
    if il.get('to_il') or il.get('from_il'):
        lines.append("\n[IL] IL Moves Needed:")
        for p in il.get('to_il', []):
            lines.append(f"  -> Move {p['name']} to IL ({p['status']})")
        for p in il.get('from_il', []):
            lines.append(f"  <- Activate {p['name']} from IL")

    # Your starters today
    starters = yahoo_results.get('your_starters', [])
    if starters:
        lines.append("\n[STARTERS] Your Pitchers Starting Today:")
        for name in starters:
            lines.append(f"  - {name}")

    lines.append("\n" + "=" * 50)

    return "\n".join(lines)


def main():
    """Main entry point."""
    print("Starting daily fantasy baseball check...\n")

    # Run checks
    mlb_results = run_mlb_checks()
    yahoo_results = run_yahoo_checks()

    # Generate summary
    summary = generate_summary(mlb_results, yahoo_results)
    print("\n" + summary)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"check_{timestamp}.json"

    all_results = {
        'timestamp': datetime.now().isoformat(),
        'mlb': mlb_results,
        'yahoo': yahoo_results,
    }

    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nResults saved to: {results_file}")

    # Send Discord notification if configured
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        print("\nSending Discord notification...")
        games_count = len(mlb_results.get('games_today', []))
        issues = yahoo_results.get('roster_issues', [])
        starters = yahoo_results.get('your_starters', [])

        lineup_status = "⚠️ Issues found" if issues else "✅ OK"
        alerts = issues if issues else ["No issues"]

        daily_summary(
            lineup_status=lineup_status,
            games_today=games_count,
            pitchers_starting=starters,
            alerts=alerts
        )
        print("Discord notification sent!")
    else:
        print("\nDiscord webhook not configured, skipping notification")

    print("\nDaily check complete!")


if __name__ == "__main__":
    main()
