"""
Fantasy Baseball Streaming Bot

Main orchestrator for the streaming automation system.
Integrates:
- Weekly streaming planner (schedule + rankings)
- MLB schedule fetcher (probable starters)
- Roster monitor (track league changes)
- Chrome automation guide (execute moves)

Usage:
    python streaming_bot.py plan      # Generate weekly streaming plan
    python streaming_bot.py monitor   # Start roster monitoring
    python streaming_bot.py status    # Show current status
    python streaming_bot.py recommend # Get top available streamers
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add paths for imports (live directory first to avoid conflicts)
sys.path.insert(0, str(Path(__file__).parent))  # live/ directory first
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backtesting"))

# Import from local live/ directory
from streaming_planner import StreamingPlanner
from live_roster_monitor import RosterMonitor  # Renamed to avoid path conflicts
from schedule_fetcher import MLBScheduleFetcher
from yahoo_chrome import YahooAutomationGuide, BLJ_X, print_automation_guide


class StreamingBot:
    """
    Main bot orchestrating all streaming functionality.

    Provides:
    - Weekly plan generation
    - Roster monitoring
    - Streaming recommendations
    - Transaction execution guides
    """

    def __init__(self, season: int = 2025):
        self.season = season
        self.plans_dir = Path(__file__).parent / "plans"
        self.plans_dir.mkdir(exist_ok=True)

        print("=" * 60)
        print(f"STREAMING BOT - Season {season}")
        print("=" * 60)

        # Initialize components
        self.planner = StreamingPlanner(season)
        self.monitor = RosterMonitor(season)
        self.schedule_fetcher = MLBScheduleFetcher(season)
        self.automation = YahooAutomationGuide()

    def generate_weekly_plan(self, start_date: str = None, days: int = 7) -> Dict:
        """
        Generate a fresh weekly streaming plan.

        Args:
            start_date: Start date (YYYY-MM-DD), defaults to today
            days: Number of days to plan

        Returns:
            Plan summary dict
        """
        print("\n[1/3] Generating weekly streaming plan...")

        # Create plan
        plan = self.planner.create_weekly_plan(
            days_ahead=days,
            start_date=start_date,
            fetch_from_mlb=True
        )

        # Print and save
        self.planner.print_plan(plan)
        self.planner.save_plan(plan)

        # Load targets into monitor
        print("\n[2/3] Loading targets into roster monitor...")
        plan_file = self.plans_dir / f"streaming_plan_{plan.week_start}.json"
        if plan_file.exists():
            self.monitor.watch_players_from_plan(plan_file)

        # Check availability
        print("\n[3/3] Checking target availability...")
        status = self.monitor.get_watched_player_status()

        available = [p for p, s in status.items() if s == "Available"]
        taken = [(p, s) for p, s in status.items() if s != "Available"]

        print("\nTARGET AVAILABILITY:")
        print("-" * 40)
        if available:
            print("  AVAILABLE:")
            for p in available:
                print(f"    [OK] {p}")
        if taken:
            print("  ALREADY ROSTERED:")
            for p, s in taken[:5]:
                team = s.replace("Rostered by ", "")
                print(f"    [X] {p} ({team})")

        return {
            "week_start": plan.week_start,
            "targets": len(plan.overall_top_targets),
            "available": available,
            "taken": [p for p, _ in taken],
        }

    def get_recommendations(self, limit: int = 5) -> List[Dict]:
        """
        Get current top streaming recommendations.

        Filters out already-rostered players.

        Returns:
            List of recommendation dicts
        """
        print("\nFetching current recommendations...")

        # Get latest plan
        plan_files = sorted(self.plans_dir.glob("streaming_plan_*.json"), reverse=True)
        if not plan_files:
            print("  No plan found. Run 'plan' first.")
            return []

        with open(plan_files[0]) as f:
            plan = json.load(f)

        # Check roster status
        status = self.monitor.get_watched_player_status()

        # Filter to available
        recommendations = []
        for target in plan.get("overall_top_targets", []):
            name = target.get("name", "")
            player_status = status.get(name, "Unknown")

            if player_status == "Available":
                recommendations.append({
                    **target,
                    "status": "AVAILABLE",
                })
            elif "Rostered by" in player_status:
                recommendations.append({
                    **target,
                    "status": player_status,
                })

        # Sort: available first, then by score
        recommendations.sort(key=lambda x: (x["status"] != "AVAILABLE", -x.get("score", 0)))

        return recommendations[:limit]

    def print_recommendations(self):
        """Print current recommendations with availability."""
        recs = self.get_recommendations(limit=10)

        print("\n" + "=" * 60)
        print("TOP STREAMING RECOMMENDATIONS")
        print("=" * 60)

        if not recs:
            print("No recommendations available. Run 'plan' first.")
            return

        print(f"\n{'Rank':<5} {'Pitcher':<20} {'vs':<5} {'Score':>6} {'Status':<20}")
        print("-" * 60)

        for i, rec in enumerate(recs, 1):
            status = rec.get("status", "Unknown")
            if status == "AVAILABLE":
                status_display = "[AVAILABLE]"
            else:
                status_display = status.replace("Rostered by ", "")[:15]

            print(f"{i:<5} {rec.get('name', ''):<20} {rec.get('opponent', ''):<5} {rec.get('score', 0):>6.1f} {status_display:<20}")

        # Show top available
        available = [r for r in recs if r.get("status") == "AVAILABLE"]
        if available:
            print(f"\n  Top available: {available[0].get('name', '')} ({available[0].get('score', 0):.1f})")

    def prepare_add_drop(self, add_player: str, drop_player: str) -> Dict:
        """
        Prepare an add/drop transaction.

        Returns workflow for Chrome automation.
        """
        workflow = self.automation.get_streaming_workflow(
            add_player=add_player,
            drop_player=drop_player,
        )

        print_automation_guide(workflow)

        return workflow

    def show_status(self):
        """Show current bot status."""
        print("\n" + "=" * 60)
        print("STREAMING BOT STATUS")
        print("=" * 60)

        # Check for latest plan
        plan_files = sorted(self.plans_dir.glob("streaming_plan_*.json"), reverse=True)
        if plan_files:
            latest = plan_files[0]
            with open(latest) as f:
                plan = json.load(f)
            print(f"\nLatest Plan: {latest.name}")
            print(f"  Week: {plan.get('week_start', '?')} to {plan.get('week_end', '?')}")
            print(f"  Generated: {plan.get('generated_at', '?')}")
            print(f"  Targets: {len(plan.get('overall_top_targets', []))}")
        else:
            print("\nNo plans found. Run: python streaming_bot.py plan")

        # Check monitor state
        print("\nRoster Monitor:")
        changes = self.monitor.check_for_changes()
        if changes:
            print(f"  {len(changes)} new changes detected!")
            self.monitor.print_changes(changes)
        else:
            print(f"  Last check: {self.monitor._state.last_check if self.monitor._state else 'Never'}")
            print(f"  Watching: {len(self.monitor._state.watched_players) if self.monitor._state else 0} players")

        # Quick recommendations
        print("\nTop Available Streamers:")
        recs = self.get_recommendations(limit=3)
        available = [r for r in recs if r.get("status") == "AVAILABLE"]
        if available:
            for r in available:
                print(f"  [OK] {r.get('name', '')} vs {r.get('opponent', '')} ({r.get('score', 0):.1f})")
        else:
            print("  No available streamers in current plan")

        print("\n" + "=" * 60)


def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print("Usage: python streaming_bot.py <command>")
        print("\nCommands:")
        print("  plan      - Generate weekly streaming plan")
        print("  monitor   - Start continuous roster monitoring")
        print("  status    - Show current status")
        print("  recommend - Show top recommendations")
        print("  add       - Prepare add/drop workflow")
        return

    command = sys.argv[1].lower()

    bot = StreamingBot(season=2025)

    if command == "plan":
        # Allow optional start date
        start_date = sys.argv[2] if len(sys.argv) > 2 else None
        bot.generate_weekly_plan(start_date=start_date)

    elif command == "monitor":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        bot.monitor.run_continuous(check_interval=interval)

    elif command == "status":
        bot.show_status()

    elif command == "recommend":
        bot.print_recommendations()

    elif command == "add":
        if len(sys.argv) < 4:
            print("Usage: python streaming_bot.py add <player_to_add> <player_to_drop>")
            return
        add_player = sys.argv[2]
        drop_player = sys.argv[3]
        bot.prepare_add_drop(add_player, drop_player)

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
