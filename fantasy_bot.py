"""
Fantasy Baseball Bot - Main Orchestrator

Ties all components together:
- Roster management
- Weekly scheduling
- Points projection
- Add optimization
- Transaction execution

Designed with plugin architecture for future extensions.
"""
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Callable, Optional, Any
from abc import ABC, abstractmethod


# =============================================================================
# PLUGIN ARCHITECTURE
# =============================================================================

class Plugin(ABC):
    """Base class for bot plugins."""

    name: str = "base_plugin"
    description: str = ""
    version: str = "1.0"

    @abstractmethod
    def initialize(self, bot: 'FantasyBot'):
        """Called when plugin is registered."""
        pass

    def on_daily_run(self, bot: 'FantasyBot'):
        """Called during daily bot run."""
        pass

    def on_pre_lock(self, bot: 'FantasyBot', game_date: date):
        """Called before lock deadline."""
        pass

    def adjust_projection(self, projection: dict) -> dict:
        """Modify a player projection. Return adjusted projection."""
        return projection

    def get_alerts(self) -> list[str]:
        """Return any alerts from this plugin."""
        return []


class PluginRegistry:
    """Manages bot plugins."""

    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self.hooks: dict[str, list[Callable]] = {
            "daily_run": [],
            "pre_lock": [],
            "adjust_projection": [],
            "get_alerts": [],
        }

    def register(self, plugin: Plugin, bot: 'FantasyBot'):
        """Register a plugin."""
        self.plugins[plugin.name] = plugin
        plugin.initialize(bot)

        # Register hooks
        if hasattr(plugin, 'on_daily_run'):
            self.hooks["daily_run"].append(plugin.on_daily_run)
        if hasattr(plugin, 'on_pre_lock'):
            self.hooks["pre_lock"].append(plugin.on_pre_lock)
        if hasattr(plugin, 'adjust_projection'):
            self.hooks["adjust_projection"].append(plugin.adjust_projection)
        if hasattr(plugin, 'get_alerts'):
            self.hooks["get_alerts"].append(plugin.get_alerts)

    def run_hook(self, hook_name: str, *args, **kwargs) -> list:
        """Run all registered hooks."""
        results = []
        for hook in self.hooks.get(hook_name, []):
            try:
                result = hook(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                print(f"Plugin hook error ({hook_name}): {e}")
        return results


# =============================================================================
# MAIN BOT
# =============================================================================

@dataclass
class BotConfig:
    """Configuration for the fantasy bot."""
    league_id: str = "89318"
    league_name: str = "Big League Jew X"
    team_id: str = "7"
    team_name: str = "Vlad The Impaler"

    # Weekly limits
    adds_per_week: int = 5
    reserve_adds_for_il: bool = True

    # Thresholds
    min_stream_score: float = 40.0
    elite_two_start_threshold: float = 100.0

    # Notifications
    discord_webhook: Optional[str] = None

    # Exclusion list (never drop)
    exclusion_list: list = field(default_factory=list)


class FantasyBot:
    """
    Main fantasy baseball bot.

    Orchestrates all components and plugins.
    """

    def __init__(self, config: BotConfig = None):
        self.config = config or BotConfig()
        self.plugins = PluginRegistry()

        # Core components (lazy loaded)
        self._roster = None
        self._schedule = None
        self._optimizer = None
        self._transaction_manager = None

        # State
        self.last_run: Optional[datetime] = None
        self.weekly_plan = None
        self.alerts: list[str] = []

    # =========================================================================
    # COMPONENT ACCESS (Lazy Loading)
    # =========================================================================

    @property
    def roster(self):
        """Get roster manager."""
        if self._roster is None:
            from roster_manager import Roster
            self._roster = Roster(
                team_name=self.config.team_name,
                league_id=self.config.league_id,
                adds_per_week=self.config.adds_per_week,
            )
            self._roster.set_exclusion_list(self.config.exclusion_list)
        return self._roster

    @property
    def schedule(self):
        """Get weekly schedule."""
        if self._schedule is None:
            from weekly_schedule import fetch_week_schedule
            self._schedule = fetch_week_schedule()
        return self._schedule

    @property
    def optimizer(self):
        """Get weekly optimizer."""
        if self._optimizer is None:
            from weekly_optimizer import WeeklyOptimizer
            self._optimizer = WeeklyOptimizer(self.roster, self.schedule)
            self._optimizer.load_streaming_options()
        return self._optimizer

    @property
    def transaction_manager(self):
        """Get transaction manager."""
        if self._transaction_manager is None:
            from transaction_manager import TransactionManager
            self._transaction_manager = TransactionManager(self.roster)
        return self._transaction_manager

    def refresh_components(self):
        """Force refresh of all components."""
        self._roster = None
        self._schedule = None
        self._optimizer = None
        self._transaction_manager = None

    # =========================================================================
    # PLUGIN MANAGEMENT
    # =========================================================================

    def register_plugin(self, plugin: Plugin):
        """Register a plugin with the bot."""
        self.plugins.register(plugin, self)
        print(f"Registered plugin: {plugin.name} v{plugin.version}")

    # =========================================================================
    # MAIN OPERATIONS
    # =========================================================================

    def daily_run(self) -> str:
        """
        Run daily bot operations.

        Call this once per day (morning is best).
        """
        self.last_run = datetime.now()
        self.alerts = []
        output = []

        output.append(f"=== FANTASY BOT DAILY RUN ===")
        output.append(f"Time: {self.last_run.strftime('%Y-%m-%d %H:%M')}")
        output.append(f"League: {self.config.league_name}")
        output.append("")

        # 1. Refresh schedule
        try:
            self.refresh_components()
            output.append(f"Schedule loaded: {len(self.schedule.starts)} starts this week")
            output.append(f"Two-start pitchers: {len(self.schedule.two_start_pitchers)}")
        except Exception as e:
            output.append(f"Error loading schedule: {e}")
            self.alerts.append(f"Schedule load failed: {e}")

        # 2. Generate weekly plan
        try:
            self.weekly_plan = self.optimizer.optimize_week(
                reserve_for_il=self.config.reserve_adds_for_il
            )
            output.append(f"\nWeekly plan generated:")
            output.append(f"  Recommended adds: {len(self.weekly_plan.recommendations)}")
            output.append(f"  Expected points: {self.weekly_plan.total_expected_points:.1f}")
        except Exception as e:
            output.append(f"Error generating plan: {e}")
            self.alerts.append(f"Optimizer failed: {e}")

        # 3. Check IL situations
        try:
            il_alerts = self.transaction_manager.il_monitor.get_all_alerts()
            if il_alerts:
                output.append(f"\nIL Alerts ({len(il_alerts)}):")
                for alert in il_alerts[:3]:
                    output.append(f"  - {alert.action_needed}")
                    self.alerts.append(alert.action_needed)
        except Exception as e:
            output.append(f"Error checking IL: {e}")

        # 4. Run plugin hooks
        plugin_results = self.plugins.run_hook("daily_run", self)
        for result in plugin_results:
            if result:
                output.append(f"\nPlugin output: {result}")

        # 5. Collect all alerts
        for get_alerts in self.plugins.hooks["get_alerts"]:
            try:
                plugin_alerts = get_alerts()
                self.alerts.extend(plugin_alerts)
            except:
                pass

        # Summary
        output.append(f"\n{'='*50}")
        output.append(f"ALERTS ({len(self.alerts)}):")
        for alert in self.alerts:
            output.append(f"  ! {alert}")

        return "\n".join(output)

    def pre_lock_check(self, game_date: date = None) -> str:
        """
        Run pre-lock verification.

        Call this ~30 min before midnight.
        """
        if game_date is None:
            game_date = date.today() + timedelta(days=1)

        output = []
        output.append(f"=== PRE-LOCK CHECK ===")
        output.append(f"For: {game_date.strftime('%A %m/%d')}")
        output.append("")

        # Transaction manager's pre-lock check
        try:
            txn_report = self.transaction_manager.pre_lock_check(game_date)
            output.append(txn_report)
        except Exception as e:
            output.append(f"Error: {e}")

        # Run plugin hooks
        self.plugins.run_hook("pre_lock", self, game_date)

        return "\n".join(output)

    def get_streaming_recommendations(self, target_date: date = None) -> str:
        """Get streaming recommendations for a specific date."""
        if target_date is None:
            target_date = date.today() + timedelta(days=1)

        output = []
        output.append(f"=== STREAMING RECOMMENDATIONS ===")
        output.append(f"For: {target_date.strftime('%A %m/%d')}")
        output.append("")

        try:
            best = self.schedule.get_best_streams(target_date, top_n=10)
            if best:
                for i, start in enumerate(best, 1):
                    loc = "vs" if start.is_home else "@"
                    two = " [2-START]" if start.is_two_start else ""
                    output.append(
                        f"{i:2}. {start.streaming_score:5.1f} - "
                        f"{start.pitcher_name} ({start.team}) {loc} {start.opponent}{two}"
                    )
            else:
                output.append("No games scheduled for this date.")
        except Exception as e:
            output.append(f"Error: {e}")

        return "\n".join(output)

    def get_weekly_plan(self) -> str:
        """Get the current weekly plan."""
        if self.weekly_plan is None:
            return "No weekly plan generated. Run daily_run() first."
        return self.weekly_plan.summary()

    def get_roster_status(self) -> str:
        """Get current roster status."""
        return self.roster.summary()

    # =========================================================================
    # QUICK ACTIONS
    # =========================================================================

    def plan_add(self, player_name: str, for_date: date = None,
                 expected_points: float = 0.0) -> str:
        """Plan an add transaction."""
        if for_date is None:
            for_date = date.today() + timedelta(days=1)

        txn = self.transaction_manager.plan_transaction(
            add_player=player_name,
            for_date=for_date,
            expected_points=expected_points,
        )

        if txn:
            return f"Planned: Add {txn.add_player}, Drop {txn.drop_player} for {for_date}"
        return "Could not plan transaction (check adds remaining or drop candidates)"

    def status(self) -> str:
        """Quick status check."""
        lines = [
            f"=== BOT STATUS ===",
            f"Last run: {self.last_run or 'Never'}",
            f"Adds remaining: {self.roster.adds_remaining()}/{self.config.adds_per_week}",
            f"Alerts: {len(self.alerts)}",
            f"Plugins: {len(self.plugins.plugins)}",
        ]

        if self.weekly_plan:
            lines.append(f"Weekly plan: {len(self.weekly_plan.recommendations)} adds planned")
            lines.append(f"Expected points: {self.weekly_plan.total_expected_points:.1f}")

        return "\n".join(lines)


# =============================================================================
# EXAMPLE PLUGINS
# =============================================================================

class WeatherPlugin(Plugin):
    """Plugin for weather-based adjustments."""

    name = "weather"
    description = "Adjusts projections based on weather/HRFI"
    version = "1.0"

    def initialize(self, bot: FantasyBot):
        self.bot = bot
        print(f"Weather plugin initialized")

    def adjust_projection(self, projection: dict) -> dict:
        """Adjust projection based on HRFI."""
        # TODO: Fetch actual HRFI from homerunforecast.com
        # For now, placeholder
        hrfi = projection.get("hrfi", 5)
        if hrfi >= 8:
            projection["hr_adjustment"] = 0.2
            projection["notes"] = projection.get("notes", "") + " [Hot weather +HR risk]"
        elif hrfi <= 2:
            projection["hr_adjustment"] = -0.2
            projection["notes"] = projection.get("notes", "") + " [Cold weather -HR risk]"
        return projection

    def get_alerts(self) -> list[str]:
        # TODO: Check for extreme weather days
        return []


class UmpirePlugin(Plugin):
    """Plugin for umpire-based adjustments."""

    name = "umpire"
    description = "Adjusts projections based on umpire zone tendencies"
    version = "1.0"

    def initialize(self, bot: FantasyBot):
        self.bot = bot

    def adjust_projection(self, projection: dict) -> dict:
        # TODO: Fetch umpire assignments from umpscorecards.com
        return projection


class NewsPlugin(Plugin):
    """Plugin for injury/news monitoring."""

    name = "news"
    description = "Monitors injury news and lineup changes"
    version = "1.0"

    def initialize(self, bot: FantasyBot):
        self.bot = bot

    def on_daily_run(self, bot: FantasyBot):
        # TODO: Fetch latest injury news
        pass

    def get_alerts(self) -> list[str]:
        # TODO: Return breaking news alerts
        return []


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_bot(exclusion_list: list[str] = None) -> FantasyBot:
    """Create a configured bot instance."""
    config = BotConfig(
        exclusion_list=exclusion_list or [
            "Shohei Ohtani",
            "Juan Soto",
            "Bobby Witt Jr.",
            "Gunnar Henderson",
            "Corbin Carroll",
        ]
    )

    bot = FantasyBot(config)

    # Register default plugins
    bot.register_plugin(WeatherPlugin())
    bot.register_plugin(UmpirePlugin())
    bot.register_plugin(NewsPlugin())

    return bot


def quick_status() -> str:
    """Quick status without full bot initialization."""
    bot = create_bot()
    return bot.status()


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main entry point."""
    import sys

    print("=" * 60)
    print("FANTASY BASEBALL BOT - BLJ X")
    print("=" * 60)
    print()

    bot = create_bot()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "daily":
            print(bot.daily_run())
        elif command == "status":
            print(bot.status())
        elif command == "streams":
            print(bot.get_streaming_recommendations())
        elif command == "plan":
            print(bot.get_weekly_plan())
        elif command == "prelock":
            print(bot.pre_lock_check())
        elif command == "roster":
            print(bot.get_roster_status())
        else:
            print(f"Unknown command: {command}")
            print("Commands: daily, status, streams, plan, prelock, roster")
    else:
        # Default: run daily
        print(bot.daily_run())


if __name__ == "__main__":
    main()
