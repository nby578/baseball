"""
Transaction Manager for BLJ X

Handles:
- Drop analysis (who can be dropped, when, roster constraints)
- IL monitoring (returns, stash alerts, emergency adds)
- Pre-lock availability checking
- Transaction timing (locks at midnight)

This is the "execution" layer that works with the optimizer.
"""
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, time
from typing import Optional
from enum import Enum

from roster_manager import Roster, Player, DropTier, ILStatus


# =============================================================================
# TRANSACTION TIMING
# =============================================================================

# Yahoo Fantasy locks at midnight ET for the next day
LOCK_TIME = time(0, 0)  # Midnight
TIMEZONE = "America/New_York"


def get_lock_deadline(game_date: date) -> datetime:
    """
    Get the deadline to make a roster move for a game.

    Moves lock at midnight the night before.
    """
    # Lock is midnight before game day
    lock_date = game_date - timedelta(days=1)
    return datetime.combine(lock_date, LOCK_TIME)


def time_until_lock(game_date: date) -> timedelta:
    """Get time remaining until lock for a game date."""
    deadline = get_lock_deadline(game_date)
    now = datetime.now()
    return deadline - now


def is_locked(game_date: date) -> bool:
    """Check if moves are locked for a game date."""
    return time_until_lock(game_date).total_seconds() < 0


# =============================================================================
# DROP ANALYSIS
# =============================================================================

@dataclass
class DropCandidate:
    """A player that could be dropped."""
    player: Player
    drop_tier: DropTier
    can_drop_today: bool
    blocking_reason: Optional[str] = None

    # For pitchers
    next_start: Optional[date] = None
    starts_tomorrow: bool = False

    # Value assessment
    recent_points: float = 0.0
    replacement_value: float = 0.0

    def drop_priority(self) -> int:
        """
        Lower number = should drop first.
        Streamers drop before droppable, etc.
        """
        if self.starts_tomorrow:
            return 100  # Don't drop
        return self.drop_tier.value


class DropAnalyzer:
    """Analyzes roster for drop candidates."""

    def __init__(self, roster: Roster):
        self.roster = roster

    def analyze_all(self, for_date: date = None) -> list[DropCandidate]:
        """
        Analyze all players for drop potential.

        Args:
            for_date: The date we want to add someone for
        """
        if for_date is None:
            for_date = date.today() + timedelta(days=1)

        candidates = []

        for player in self.roster.players:
            # Skip IL players
            if player.is_on_il():
                continue

            # Check if in exclusion list
            if player.name in self.roster.exclusion_list:
                continue

            candidate = DropCandidate(
                player=player,
                drop_tier=player.drop_tier,
                can_drop_today=True,
                next_start=player.next_start,
            )

            # Check if pitcher starts tomorrow
            if player.is_pitcher and player.next_start == for_date:
                candidate.can_drop_today = False
                candidate.starts_tomorrow = True
                candidate.blocking_reason = f"Pitches tomorrow ({for_date})"

            candidates.append(candidate)

        # Sort by drop priority
        return sorted(candidates, key=lambda x: x.drop_priority())

    def get_best_drop(self, for_date: date = None) -> Optional[DropCandidate]:
        """Get the best player to drop for an add."""
        candidates = self.analyze_all(for_date)
        droppable = [c for c in candidates if c.can_drop_today]
        return droppable[0] if droppable else None

    def can_make_add(self, for_date: date = None) -> bool:
        """Check if we can make an add (have someone to drop)."""
        return self.get_best_drop(for_date) is not None

    def drop_report(self, for_date: date = None) -> str:
        """Generate a drop analysis report."""
        if for_date is None:
            for_date = date.today() + timedelta(days=1)

        candidates = self.analyze_all(for_date)

        lines = [
            f"=== DROP ANALYSIS ===",
            f"For adds on: {for_date.strftime('%A %m/%d')}",
            f"",
            f"DROPPABLE NOW:",
        ]

        droppable = [c for c in candidates if c.can_drop_today]
        for c in droppable:
            tier = c.drop_tier.name
            pos = c.player.position if not c.player.is_pitcher else "P"
            lines.append(f"  {c.player.name} ({pos}) - {tier}")

        blocked = [c for c in candidates if not c.can_drop_today]
        if blocked:
            lines.append(f"\nBLOCKED:")
            for c in blocked:
                lines.append(f"  {c.player.name} - {c.blocking_reason}")

        return "\n".join(lines)


# =============================================================================
# IL MONITORING
# =============================================================================

@dataclass
class ILAlert:
    """An alert about an IL situation."""
    player: Player
    alert_type: str  # "returning", "stash", "emergency"
    days_until: Optional[int] = None
    action_needed: str = ""
    priority: int = 1  # 1 = highest


class ILMonitor:
    """Monitors IL situations and generates alerts."""

    def __init__(self, roster: Roster):
        self.roster = roster

    def check_returns(self, days_ahead: int = 7) -> list[ILAlert]:
        """Check for players returning from IL soon."""
        alerts = []
        today = date.today()

        for player in self.roster.get_il_players():
            if player.expected_return:
                days_until = (player.expected_return - today).days

                if days_until <= 0:
                    # Should be activated now!
                    alerts.append(ILAlert(
                        player=player,
                        alert_type="returning",
                        days_until=0,
                        action_needed=f"ACTIVATE {player.name} NOW - expected return passed",
                        priority=1,
                    ))
                elif days_until <= 3:
                    # Returning very soon
                    alerts.append(ILAlert(
                        player=player,
                        alert_type="returning",
                        days_until=days_until,
                        action_needed=f"Plan to activate {player.name} in {days_until} days - save an add",
                        priority=2,
                    ))
                elif days_until <= days_ahead:
                    # Returning this week
                    alerts.append(ILAlert(
                        player=player,
                        alert_type="returning",
                        days_until=days_until,
                        action_needed=f"{player.name} returning in {days_until} days - monitor",
                        priority=3,
                    ))

        return sorted(alerts, key=lambda x: x.priority)

    def check_dtd(self) -> list[ILAlert]:
        """Check for DTD players who might need IL."""
        alerts = []

        for player in self.roster.get_dtd_players():
            # Important players who are DTD
            if player.drop_tier.value <= DropTier.HOLD.value:
                alerts.append(ILAlert(
                    player=player,
                    alert_type="emergency",
                    action_needed=f"{player.name} is DTD - may need IL stint, reserve an add",
                    priority=2,
                ))

        return alerts

    def get_all_alerts(self) -> list[ILAlert]:
        """Get all IL-related alerts."""
        alerts = []
        alerts.extend(self.check_returns())
        alerts.extend(self.check_dtd())
        return sorted(alerts, key=lambda x: x.priority)

    def should_save_add(self) -> tuple[bool, str]:
        """
        Determine if we should save an add for IL situations.

        Returns:
            (should_save, reason)
        """
        alerts = self.get_all_alerts()

        # Priority 1 alerts = definite save
        p1_alerts = [a for a in alerts if a.priority == 1]
        if p1_alerts:
            return True, p1_alerts[0].action_needed

        # Multiple priority 2 alerts = probably save
        p2_alerts = [a for a in alerts if a.priority == 2]
        if len(p2_alerts) >= 2:
            return True, f"Multiple IL situations: {len(p2_alerts)} players"

        # Single important player returning soon
        for alert in p2_alerts:
            if alert.player.drop_tier.value <= DropTier.HOLD.value:
                return True, alert.action_needed

        return False, ""

    def il_report(self) -> str:
        """Generate IL status report."""
        alerts = self.get_all_alerts()

        lines = [
            f"=== IL MONITOR ===",
            f"",
        ]

        if not alerts:
            lines.append("No IL alerts at this time.")
        else:
            for alert in alerts:
                priority_str = "!!!" if alert.priority == 1 else "!" if alert.priority == 2 else ""
                lines.append(f"{priority_str} {alert.action_needed}")

        should_save, reason = self.should_save_add()
        lines.append(f"\nSave an add? {'YES - ' + reason if should_save else 'No'}")

        return "\n".join(lines)


# =============================================================================
# AVAILABILITY CHECKER
# =============================================================================

@dataclass
class AvailabilityCheck:
    """Result of checking player availability."""
    player_name: str
    is_available: bool
    checked_at: datetime
    owner: Optional[str] = None  # If taken, who owns them
    waiver_status: Optional[str] = None  # "FA", "W (Mon)", etc.


class AvailabilityChecker:
    """
    Checks if players are still available before lock.

    Note: This would integrate with Yahoo API in production.
    For now, it's a placeholder structure.
    """

    def __init__(self, league_id: str = "89318"):
        self.league_id = league_id
        self.cache: dict[str, AvailabilityCheck] = {}
        self.cache_duration = timedelta(minutes=5)

    def check_player(self, player_name: str) -> AvailabilityCheck:
        """
        Check if a specific player is available.

        TODO: Integrate with Yahoo API
        """
        # Check cache
        if player_name in self.cache:
            cached = self.cache[player_name]
            if datetime.now() - cached.checked_at < self.cache_duration:
                return cached

        # TODO: Actual Yahoo API call
        # For now, return placeholder
        result = AvailabilityCheck(
            player_name=player_name,
            is_available=True,  # Placeholder
            checked_at=datetime.now(),
            waiver_status="FA",
        )

        self.cache[player_name] = result
        return result

    def check_multiple(self, player_names: list[str]) -> dict[str, AvailabilityCheck]:
        """Check availability for multiple players."""
        results = {}
        for name in player_names:
            results[name] = self.check_player(name)
        return results

    def verify_before_lock(self, targets: list[str], game_date: date) -> list[str]:
        """
        Verify targets are available right before lock.

        Returns list of still-available players.
        """
        if is_locked(game_date):
            print(f"WARNING: Moves already locked for {game_date}")
            return []

        time_left = time_until_lock(game_date)
        print(f"Time until lock: {time_left}")

        available = []
        for name in targets:
            check = self.check_player(name)
            if check.is_available:
                available.append(name)
            else:
                print(f"  {name}: TAKEN by {check.owner or 'unknown'}")

        return available


# =============================================================================
# TRANSACTION EXECUTOR
# =============================================================================

@dataclass
class Transaction:
    """A planned transaction."""
    add_player: str
    drop_player: str
    for_date: date
    expected_points: float
    executed: bool = False
    execution_time: Optional[datetime] = None


class TransactionManager:
    """
    Manages the full transaction workflow.

    Combines drop analysis, IL monitoring, and availability checking.
    """

    def __init__(self, roster: Roster):
        self.roster = roster
        self.drop_analyzer = DropAnalyzer(roster)
        self.il_monitor = ILMonitor(roster)
        self.availability_checker = AvailabilityChecker(roster.league_id)

        self.pending_transactions: list[Transaction] = []
        self.completed_transactions: list[Transaction] = []

    def plan_transaction(self, add_player: str, for_date: date,
                         expected_points: float = 0.0) -> Optional[Transaction]:
        """
        Plan a transaction (add player, auto-select drop).

        Returns Transaction if valid, None if can't execute.
        """
        # Check if we have adds remaining
        if self.roster.adds_remaining() <= 0:
            print("No adds remaining this week!")
            return None

        # Get best drop candidate
        drop_candidate = self.drop_analyzer.get_best_drop(for_date)
        if not drop_candidate:
            print(f"No valid drop candidate for {for_date}")
            return None

        # Check availability
        avail = self.availability_checker.check_player(add_player)
        if not avail.is_available:
            print(f"{add_player} is not available (owned by {avail.owner})")
            return None

        txn = Transaction(
            add_player=add_player,
            drop_player=drop_candidate.player.name,
            for_date=for_date,
            expected_points=expected_points,
        )

        self.pending_transactions.append(txn)
        return txn

    def execute_transaction(self, txn: Transaction) -> bool:
        """
        Execute a planned transaction.

        TODO: Integrate with Yahoo API or Chrome automation.
        """
        # Verify still valid
        if is_locked(txn.for_date):
            print(f"Cannot execute - moves locked for {txn.for_date}")
            return False

        # Verify availability one more time
        avail = self.availability_checker.check_player(txn.add_player)
        if not avail.is_available:
            print(f"{txn.add_player} was claimed!")
            return False

        # TODO: Actual execution via Yahoo API or Chrome
        print(f"EXECUTING: Drop {txn.drop_player}, Add {txn.add_player}")

        # Update roster
        self.roster.remove_player(txn.drop_player)
        self.roster.use_add()

        txn.executed = True
        txn.execution_time = datetime.now()

        self.pending_transactions.remove(txn)
        self.completed_transactions.append(txn)

        return True

    def pre_lock_check(self, for_date: date) -> str:
        """
        Run pre-lock verification for tomorrow's adds.

        Call this ~30 min before midnight.
        """
        lines = [
            f"=== PRE-LOCK CHECK ===",
            f"Game date: {for_date.strftime('%A %m/%d')}",
            f"Time until lock: {time_until_lock(for_date)}",
            f"",
        ]

        # Get pending transactions for this date
        pending = [t for t in self.pending_transactions if t.for_date == for_date]

        if not pending:
            lines.append("No pending transactions for this date.")
        else:
            lines.append(f"PENDING TRANSACTIONS ({len(pending)}):")
            for txn in pending:
                avail = self.availability_checker.check_player(txn.add_player)
                status = "AVAILABLE" if avail.is_available else f"TAKEN by {avail.owner}"
                lines.append(f"  Add {txn.add_player}: {status}")
                lines.append(f"  Drop {txn.drop_player}")
                lines.append(f"  Expected: {txn.expected_points:.1f} pts")
                lines.append("")

        # Drop analysis
        lines.append(self.drop_analyzer.drop_report(for_date))

        # IL alerts
        lines.append("\n" + self.il_monitor.il_report())

        return "\n".join(lines)

    def daily_summary(self) -> str:
        """Generate daily transaction summary."""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        lines = [
            f"=== TRANSACTION SUMMARY ===",
            f"Date: {today.strftime('%A %m/%d')}",
            f"Adds remaining: {self.roster.adds_remaining()}/{self.roster.adds_per_week}",
            f"",
        ]

        # Tomorrow's pending
        tomorrow_txns = [t for t in self.pending_transactions if t.for_date == tomorrow]
        if tomorrow_txns:
            lines.append(f"TOMORROW'S ADDS ({len(tomorrow_txns)}):")
            for txn in tomorrow_txns:
                lines.append(f"  {txn.add_player} (drop {txn.drop_player}) - {txn.expected_points:.1f} pts")
        else:
            lines.append("No adds planned for tomorrow.")

        # This week's completed
        if self.completed_transactions:
            lines.append(f"\nCOMPLETED THIS WEEK ({len(self.completed_transactions)}):")
            for txn in self.completed_transactions:
                lines.append(f"  {txn.for_date.strftime('%a')}: +{txn.add_player} -{txn.drop_player}")

        # IL status
        lines.append("\n" + self.il_monitor.il_report())

        return "\n".join(lines)


if __name__ == "__main__":
    from roster_manager import create_example_roster

    print("=== TRANSACTION MANAGER DEMO ===\n")

    roster = create_example_roster()
    manager = TransactionManager(roster)

    print(manager.daily_summary())

    print("\n" + "=" * 50 + "\n")

    # Demo pre-lock check
    tomorrow = date.today() + timedelta(days=1)
    print(manager.pre_lock_check(tomorrow))
