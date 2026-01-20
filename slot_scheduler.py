"""
Slot Scheduler for Fantasy Baseball Streaming
==============================================
Resource-constrained optimization for weekly streaming pitcher selection.

Key insight from research: This problem is TRIVIALLY SMALL for modern solvers.
- 5 adds, 7 days, ~20 candidates = exact solution in <10ms
- No heuristics needed - OR-Tools CP-SAT solves optimally

Resources modeled:
- Consumable: 5 weekly adds (once used, gone)
- Renewable: 1-2 pitcher slots per day (refresh after each day's starts)
- Temporal: Must add before pitch day

Features:
- Exact optimal solution via constraint programming
- Snipe risk modeling (survival process)
- Daily re-optimization (rolling horizon)
- Contingency trees (backup plans if targets sniped)

References:
- Google OR-Tools: https://developers.google.com/optimization
- Research: "Streaming Pitcher Optimization" doc
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
import math

# Try to import OR-Tools, fall back to brute force if not available
try:
    from ortools.sat.python import cp_model
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False
    print("Warning: OR-Tools not installed. Using brute force solver (slower but works).")


# =============================================================================
# CONSTANTS
# =============================================================================

DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DEFAULT_WEEKLY_ADDS = 5
DEFAULT_SLOTS_PER_DAY = 2  # Typical streaming slots available


class SnipeRiskTier(Enum):
    """Snipe risk categories based on player desirability."""
    ELITE = "elite"        # Top 10 adds - 30-50% daily snipe risk
    HIGH = "high"          # Top 11-30 - 20-35% daily
    MODERATE = "moderate"  # Top 31-50 - 10-20% daily
    LOW = "low"            # Below top 50 - 5-10% daily
    MINIMAL = "minimal"    # Deep streamers - <5% daily


# Snipe intensity (lambda) by tier - probability of being taken per day
SNIPE_LAMBDAS = {
    SnipeRiskTier.ELITE: 0.45,     # ~36% daily survival
    SnipeRiskTier.HIGH: 0.28,      # ~76% daily survival
    SnipeRiskTier.MODERATE: 0.15,  # ~86% daily survival
    SnipeRiskTier.LOW: 0.08,       # ~92% daily survival
    SnipeRiskTier.MINIMAL: 0.03,   # ~97% daily survival
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class StreamingCandidate:
    """A pitcher available for streaming."""
    name: str
    team: str
    pitch_days: List[int]  # 0=Mon, 6=Sun

    # Expected points per start
    points_per_start: float

    # Risk metrics (from risk_analysis.py)
    floor: float = 0.0
    ceiling: float = 0.0
    disaster_prob: float = 0.10

    # Snipe risk
    snipe_tier: SnipeRiskTier = SnipeRiskTier.MODERATE
    ownership_pct: float = 0.0  # League ownership if known

    # Opponent info for each start
    opponents: List[str] = field(default_factory=list)

    # Two-start indicator
    @property
    def is_two_start(self) -> bool:
        return len(self.pitch_days) >= 2

    @property
    def total_expected_points(self) -> float:
        return self.points_per_start * len(self.pitch_days)

    @property
    def snipe_lambda(self) -> float:
        """Daily snipe intensity."""
        return SNIPE_LAMBDAS.get(self.snipe_tier, 0.15)

    def survival_prob(self, days: int) -> float:
        """Probability still available after `days` days."""
        return math.exp(-self.snipe_lambda * days)


@dataclass
class RosterSlot:
    """A pitcher slot on the active roster."""
    slot_id: str  # e.g., "SP1", "P2"
    slot_type: str  # "SP", "RP", or "P"

    # Current occupant (None if open for streaming)
    current_player: Optional[str] = None
    is_keeper: bool = False  # If True, don't drop

    # When slot becomes available (day streamer's start completes)
    available_day: int = 0  # 0=Mon available

    @property
    def is_available(self) -> bool:
        return not self.is_keeper and self.current_player is None


@dataclass
class DailySlotConfig:
    """Slot availability for a single day."""
    day: int  # 0=Mon, 6=Sun
    total_slots: int  # How many streamers can pitch this day
    slots_used: int = 0  # Already committed

    @property
    def available(self) -> int:
        return self.total_slots - self.slots_used


@dataclass
class WeeklySchedule:
    """Full week schedule of slot availability."""
    week_start: date
    daily_slots: List[DailySlotConfig]

    # Committed streamers (already added, locked in)
    committed: List[StreamingCandidate] = field(default_factory=list)

    # Adds used so far
    adds_used: int = 0

    @property
    def adds_remaining(self) -> int:
        return DEFAULT_WEEKLY_ADDS - self.adds_used

    def slots_on_day(self, day: int) -> int:
        """Available slots on given day."""
        if 0 <= day < len(self.daily_slots):
            return self.daily_slots[day].available
        return 0


@dataclass
class OptimizationResult:
    """Result of streaming optimization."""
    selected: List[StreamingCandidate]
    total_points: float

    # Schedule: which day to add each streamer
    add_schedule: Dict[str, int] = field(default_factory=dict)  # name -> add_day

    # Contingencies
    backups: List[StreamingCandidate] = field(default_factory=list)

    # Solve metadata
    solve_time_ms: float = 0.0
    is_optimal: bool = True

    def __str__(self) -> str:
        lines = [
            f"=== Optimization Result ===",
            f"Total Expected Points: {self.total_points:.1f}",
            f"Streamers Selected: {len(self.selected)}",
            f"Solve Time: {self.solve_time_ms:.1f}ms",
            f"Optimal: {self.is_optimal}",
            "",
            "Schedule:"
        ]
        for s in sorted(self.selected, key=lambda x: min(x.pitch_days)):
            days_str = ', '.join(DAYS_OF_WEEK[d] for d in s.pitch_days)
            add_day = self.add_schedule.get(s.name, min(s.pitch_days) - 1)
            add_str = DAYS_OF_WEEK[max(0, add_day)]
            lines.append(f"  {s.name}: Add {add_str} -> Pitches {days_str} ({s.total_expected_points:.1f} pts)")

        if self.backups:
            lines.append("")
            lines.append("Backups:")
            for b in self.backups[:3]:
                lines.append(f"  {b.name}: {b.total_expected_points:.1f} pts")

        return '\n'.join(lines)


# =============================================================================
# CORE OPTIMIZER (OR-Tools CP-SAT)
# =============================================================================

class SlotOptimizer:
    """
    Core optimization engine using OR-Tools CP-SAT.

    Solves the streaming selection problem EXACTLY in milliseconds.
    """

    def __init__(self,
                 candidates: List[StreamingCandidate],
                 schedule: WeeklySchedule,
                 budget: Optional[int] = None):
        """
        Initialize optimizer.

        candidates: Available streaming pitchers
        schedule: Weekly slot configuration
        budget: Override for adds remaining (default from schedule)
        """
        self.candidates = candidates
        self.schedule = schedule
        self.budget = budget if budget is not None else schedule.adds_remaining

    def solve(self) -> OptimizationResult:
        """
        Find optimal streaming selection.

        Returns OptimizationResult with selected streamers and schedule.
        """
        import time
        start = time.time()

        if HAS_ORTOOLS:
            result = self._solve_ortools()
        else:
            result = self._solve_brute_force()

        result.solve_time_ms = (time.time() - start) * 1000
        return result

    def _solve_ortools(self) -> OptimizationResult:
        """Solve using OR-Tools CP-SAT (fast, exact)."""
        model = cp_model.CpModel()
        n = len(self.candidates)

        if n == 0:
            return OptimizationResult(selected=[], total_points=0)

        # Binary selection variables
        selected = [model.NewBoolVar(f'select_{i}') for i in range(n)]

        # Budget constraint (consumable resource)
        model.Add(sum(selected) <= self.budget)

        # Daily capacity constraints (renewable resource)
        for day in range(7):
            pitchers_today = []
            for i, cand in enumerate(self.candidates):
                if day in cand.pitch_days:
                    pitchers_today.append(selected[i])

            if pitchers_today:
                daily_cap = self.schedule.slots_on_day(day)
                model.Add(sum(pitchers_today) <= daily_cap)

        # Objective: maximize total expected points
        # Scale to integers for CP-SAT (multiply by 10 for 1 decimal precision)
        total_points = sum(
            selected[i] * int(self.candidates[i].total_expected_points * 10)
            for i in range(n)
        )
        model.Maximize(total_points)

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 1.0  # Should be instant
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            picks = [self.candidates[i] for i in range(n)
                    if solver.Value(selected[i]) == 1]

            # Build add schedule (add day before first pitch)
            add_schedule = {}
            for p in picks:
                first_pitch = min(p.pitch_days)
                add_schedule[p.name] = max(0, first_pitch - 1)

            # Get backups (next best not selected)
            selected_names = {p.name for p in picks}
            backups = [c for c in self.candidates if c.name not in selected_names]
            backups.sort(key=lambda x: x.total_expected_points, reverse=True)

            return OptimizationResult(
                selected=picks,
                total_points=solver.ObjectiveValue() / 10.0,
                add_schedule=add_schedule,
                backups=backups[:5],
                is_optimal=(status == cp_model.OPTIMAL)
            )

        return OptimizationResult(selected=[], total_points=0, is_optimal=False)

    def _solve_brute_force(self) -> OptimizationResult:
        """Fallback brute force solver (works without OR-Tools)."""
        from itertools import combinations

        n = len(self.candidates)
        if n == 0:
            return OptimizationResult(selected=[], total_points=0)

        best_picks = []
        best_points = 0

        # Try all combinations up to budget size
        for k in range(1, min(self.budget + 1, n + 1)):
            for combo in combinations(range(n), k):
                picks = [self.candidates[i] for i in combo]

                # Check daily capacity constraints
                feasible = True
                for day in range(7):
                    pitchers_today = sum(1 for p in picks if day in p.pitch_days)
                    if pitchers_today > self.schedule.slots_on_day(day):
                        feasible = False
                        break

                if feasible:
                    total = sum(p.total_expected_points for p in picks)
                    if total > best_points:
                        best_points = total
                        best_picks = picks

        # Build add schedule
        add_schedule = {}
        for p in best_picks:
            first_pitch = min(p.pitch_days)
            add_schedule[p.name] = max(0, first_pitch - 1)

        # Get backups
        selected_names = {p.name for p in best_picks}
        backups = [c for c in self.candidates if c.name not in selected_names]
        backups.sort(key=lambda x: x.total_expected_points, reverse=True)

        return OptimizationResult(
            selected=best_picks,
            total_points=best_points,
            add_schedule=add_schedule,
            backups=backups[:5],
            is_optimal=True
        )


# =============================================================================
# SNIPE RISK CALCULATOR
# =============================================================================

class SnipeRiskCalculator:
    """
    Model competitor behavior as a stochastic survival process.

    P(player available at time t) = exp(-lambda * t)
    """

    def __init__(self, league_activity: float = 1.0):
        """
        league_activity: Multiplier for snipe rates (1.0 = average league)
        """
        self.league_activity = league_activity

    def survival_probability(self,
                             candidate: StreamingCandidate,
                             days_until_add: int) -> float:
        """
        Probability candidate is still available after `days_until_add` days.
        """
        lambda_ = candidate.snipe_lambda * self.league_activity
        return math.exp(-lambda_ * days_until_add)

    def expected_value_with_snipe_risk(self,
                                        candidate: StreamingCandidate,
                                        days_until_add: int,
                                        backup_value: float = 0) -> float:
        """
        Risk-adjusted expected value accounting for snipe probability.

        EV = P(available) * value + P(sniped) * backup_value
        """
        p_available = self.survival_probability(candidate, days_until_add)
        return (p_available * candidate.total_expected_points +
                (1 - p_available) * backup_value)

    def should_add_now(self,
                       candidate: StreamingCandidate,
                       days_until_needed: int,
                       slot_cost: float = 0) -> Tuple[bool, str]:
        """
        Determine if we should add now vs wait.

        Decision rule: Add immediately when snipe risk > ~25%/day for
        high-value targets.

        slot_cost: Opportunity cost of using slot early (e.g., missing
                   another start we could have gotten)

        Returns: (should_add_now, reasoning)
        """
        daily_snipe_prob = 1 - math.exp(-candidate.snipe_lambda * self.league_activity)
        cumulative_snipe_prob = 1 - self.survival_probability(candidate, days_until_needed)

        value = candidate.total_expected_points
        expected_loss = cumulative_snipe_prob * value

        # Add now if expected loss from snipe > slot opportunity cost
        should_add = expected_loss > slot_cost and cumulative_snipe_prob > 0.20

        if should_add:
            reasoning = (f"ADD NOW: {candidate.name} has {cumulative_snipe_prob:.0%} snipe risk "
                        f"over {days_until_needed} days. Expected loss ${expected_loss:.1f} pts > "
                        f"slot cost {slot_cost:.1f} pts.")
        else:
            reasoning = (f"WAIT: {candidate.name} has only {cumulative_snipe_prob:.0%} snipe risk. "
                        f"Safe to wait until closer to pitch day.")

        return should_add, reasoning

    def rank_by_urgency(self,
                        candidates: List[StreamingCandidate],
                        current_day: int) -> List[Tuple[StreamingCandidate, float, str]]:
        """
        Rank candidates by add urgency (snipe risk adjusted).

        Returns list of (candidate, urgency_score, reasoning).
        Higher urgency = should add sooner.
        """
        results = []

        for cand in candidates:
            if not cand.pitch_days:
                continue

            first_pitch = min(cand.pitch_days)
            days_until_pitch = max(0, first_pitch - current_day)

            # Urgency = value * snipe_risk / days_remaining
            snipe_risk = 1 - self.survival_probability(cand, days_until_pitch)

            if days_until_pitch == 0:
                urgency = cand.total_expected_points * 10  # Must add today!
            else:
                urgency = cand.total_expected_points * snipe_risk / days_until_pitch

            if snipe_risk > 0.30:
                reason = f"HIGH URGENCY: {snipe_risk:.0%} snipe risk"
            elif snipe_risk > 0.15:
                reason = f"MODERATE: {snipe_risk:.0%} snipe risk"
            else:
                reason = f"LOW: Can wait, only {snipe_risk:.0%} snipe risk"

            results.append((cand, urgency, reason))

        results.sort(key=lambda x: x[1], reverse=True)
        return results


# =============================================================================
# CONTINGENCY PLANNER
# =============================================================================

class ContingencyPlanner:
    """
    Pre-compute backup plans for when primary targets get sniped.
    """

    def __init__(self, optimizer: SlotOptimizer):
        self.optimizer = optimizer
        self.contingency_cache: Dict[frozenset, OptimizationResult] = {}

    def generate_contingencies(self,
                                primary_result: OptimizationResult,
                                top_n_scenarios: int = 5) -> Dict[str, OptimizationResult]:
        """
        Generate backup plans for top snipe scenarios.

        Returns dict: sniped_player_name -> new_optimal_result
        """
        contingencies = {}

        # Sort primary picks by snipe risk (highest first)
        risky_picks = sorted(
            primary_result.selected,
            key=lambda x: x.snipe_lambda,
            reverse=True
        )[:top_n_scenarios]

        for sniped in risky_picks:
            # Remove sniped player from candidates
            remaining = [c for c in self.optimizer.candidates if c.name != sniped.name]

            # Re-optimize without this player
            backup_optimizer = SlotOptimizer(
                candidates=remaining,
                schedule=self.optimizer.schedule,
                budget=self.optimizer.budget
            )
            backup_result = backup_optimizer.solve()

            contingencies[sniped.name] = backup_result

        return contingencies

    def get_contingency_tree(self,
                              primary_result: OptimizationResult) -> str:
        """Generate human-readable contingency tree."""
        contingencies = self.generate_contingencies(primary_result)

        lines = ["=== Contingency Tree ===", ""]
        lines.append("Primary Plan:")
        for s in primary_result.selected:
            lines.append(f"  - {s.name} ({s.total_expected_points:.1f} pts)")

        lines.append("")
        lines.append("If sniped, switch to:")

        for sniped_name, backup in contingencies.items():
            # Find the replacement
            primary_names = {s.name for s in primary_result.selected}
            backup_names = {s.name for s in backup.selected}
            new_adds = backup_names - primary_names

            if new_adds:
                replacement = list(new_adds)[0]
                pts_diff = backup.total_points - primary_result.total_points + \
                          next(s.total_expected_points for s in primary_result.selected
                               if s.name == sniped_name)
                lines.append(f"  {sniped_name} sniped -> Add {replacement} "
                           f"(lose {pts_diff:.1f} pts)")
            else:
                lines.append(f"  {sniped_name} sniped -> No good replacement")

        return '\n'.join(lines)


# =============================================================================
# ROLLING HORIZON MANAGER
# =============================================================================

class RollingHorizonManager:
    """
    Manage daily re-optimization as the week progresses.
    """

    def __init__(self):
        self.committed_adds: List[StreamingCandidate] = []
        self.dropped_players: Set[str] = set()
        self.adds_used: int = 0
        self.current_day: int = 0  # 0=Mon

    def advance_day(self, new_day: int):
        """Move to next day, freeing up slots from completed starts."""
        self.current_day = new_day

        # Mark streamers who pitched yesterday as droppable
        yesterday = new_day - 1
        for streamer in self.committed_adds:
            if yesterday in streamer.pitch_days:
                # Check if they have another start this week
                future_starts = [d for d in streamer.pitch_days if d > yesterday]
                if not future_starts:
                    # Can drop this player, slot is now free
                    self.dropped_players.add(streamer.name)

    def commit_add(self, streamer: StreamingCandidate):
        """Lock in a streaming add."""
        self.committed_adds.append(streamer)
        self.adds_used += 1

    def reoptimize(self,
                   all_candidates: List[StreamingCandidate],
                   schedule: WeeklySchedule) -> OptimizationResult:
        """
        Re-solve with current state.

        Fixes committed decisions, excludes dropped players,
        only considers remaining days.
        """
        # Filter to available candidates (not dropped, not already committed)
        committed_names = {s.name for s in self.committed_adds}
        available = [c for c in all_candidates
                    if c.name not in self.dropped_players
                    and c.name not in committed_names]

        # Filter to candidates with remaining pitch days
        available = [c for c in available
                    if any(d >= self.current_day for d in c.pitch_days)]

        # Update pitch days to only include future starts
        for cand in available:
            cand.pitch_days = [d for d in cand.pitch_days if d >= self.current_day]

        # Create updated schedule
        remaining_budget = DEFAULT_WEEKLY_ADDS - self.adds_used

        optimizer = SlotOptimizer(
            candidates=available,
            schedule=schedule,
            budget=remaining_budget
        )

        return optimizer.solve()

    def get_status(self) -> str:
        """Get current status summary."""
        lines = [
            f"=== Day {self.current_day} ({DAYS_OF_WEEK[self.current_day]}) Status ===",
            f"Adds used: {self.adds_used}/{DEFAULT_WEEKLY_ADDS}",
            f"Committed streamers: {len(self.committed_adds)}",
        ]

        for s in self.committed_adds:
            remaining = [DAYS_OF_WEEK[d] for d in s.pitch_days if d >= self.current_day]
            status = f"Starts: {', '.join(remaining)}" if remaining else "DONE"
            lines.append(f"  - {s.name}: {status}")

        if self.dropped_players:
            lines.append(f"Dropped: {', '.join(self.dropped_players)}")

        return '\n'.join(lines)


# =============================================================================
# MAIN SCHEDULER CLASS
# =============================================================================

class SlotScheduler:
    """
    Main interface for streaming slot optimization.

    Combines all components:
    - Core optimizer (OR-Tools)
    - Snipe risk calculator
    - Contingency planner
    - Rolling horizon manager
    """

    def __init__(self, league_activity: float = 1.0):
        """
        league_activity: How active is your league? (1.0 = average)
                        Higher = more snipe risk
        """
        self.snipe_calc = SnipeRiskCalculator(league_activity)
        self.horizon = RollingHorizonManager()

    def create_weekly_schedule(self,
                                slots_per_day: List[int] = None) -> WeeklySchedule:
        """
        Create a new weekly schedule.

        slots_per_day: List of 7 ints for Mon-Sun slot availability.
                      Default is [2,2,2,2,2,2,2]
        """
        if slots_per_day is None:
            slots_per_day = [DEFAULT_SLOTS_PER_DAY] * 7

        daily = [DailySlotConfig(day=i, total_slots=slots_per_day[i])
                for i in range(7)]

        return WeeklySchedule(
            week_start=date.today(),
            daily_slots=daily
        )

    def optimize_week(self,
                      candidates: List[StreamingCandidate],
                      schedule: WeeklySchedule) -> OptimizationResult:
        """
        Run full week optimization.

        Returns optimal streaming selection with schedule.
        """
        optimizer = SlotOptimizer(candidates, schedule)
        result = optimizer.solve()

        # Keep backups as StreamingCandidate objects (already set by optimizer)
        # Contingencies are generated separately when needed

        return result

    def get_daily_recommendation(self,
                                  candidates: List[StreamingCandidate],
                                  schedule: WeeklySchedule,
                                  current_day: int) -> Dict:
        """
        Get today's specific recommendation.

        Returns dict with:
        - add_today: List of streamers to add today
        - rationale: Why these picks
        - urgency_ranking: All candidates by urgency
        - snipe_alerts: High-risk targets to grab ASAP
        """
        self.horizon.current_day = current_day

        # Get optimal solution
        result = self.horizon.reoptimize(candidates, schedule)

        # Which of the optimal picks should be added TODAY?
        add_today = []
        rationale = []

        for streamer in result.selected:
            first_pitch = min(streamer.pitch_days)
            should_add_by = first_pitch - 1  # Day before pitch

            if should_add_by <= current_day:
                add_today.append(streamer)
                rationale.append(f"{streamer.name}: Pitches {DAYS_OF_WEEK[first_pitch]}, must add today")
            else:
                # Check snipe risk
                days_until = first_pitch - current_day
                should_early, reason = self.snipe_calc.should_add_now(streamer, days_until)
                if should_early:
                    add_today.append(streamer)
                    rationale.append(f"{streamer.name}: {reason}")

        # Get urgency ranking for all candidates
        urgency = self.snipe_calc.rank_by_urgency(candidates, current_day)

        # Identify snipe alerts
        snipe_alerts = [(c, u, r) for c, u, r in urgency
                       if c.snipe_tier in [SnipeRiskTier.ELITE, SnipeRiskTier.HIGH]]

        return {
            'add_today': add_today,
            'rationale': rationale,
            'optimal_plan': result,
            'urgency_ranking': urgency[:10],
            'snipe_alerts': snipe_alerts,
            'status': self.horizon.get_status()
        }

    def commit_and_advance(self,
                           added: List[StreamingCandidate],
                           new_day: int):
        """
        Commit today's adds and advance to next day.

        Call after executing the recommended adds.
        """
        for streamer in added:
            self.horizon.commit_add(streamer)
        self.horizon.advance_day(new_day)


# =============================================================================
# DEMO / TESTING
# =============================================================================

def demo():
    """Demonstrate slot scheduler capabilities."""

    print("=" * 70)
    print("SLOT SCHEDULER DEMO")
    print("=" * 70)

    # Create sample candidates
    candidates = [
        StreamingCandidate(
            name="Garrett Crochet", team="CWS",
            pitch_days=[1, 6],  # Tue, Sun (two-start!)
            points_per_start=42,
            floor=15, ceiling=65, disaster_prob=0.04,
            snipe_tier=SnipeRiskTier.ELITE,
            opponents=["OAK", "DET"]
        ),
        StreamingCandidate(
            name="Mitchell Parker", team="WSH",
            pitch_days=[2],  # Wed
            points_per_start=35,
            floor=10, ceiling=55, disaster_prob=0.08,
            snipe_tier=SnipeRiskTier.MODERATE,
            opponents=["MIA"]
        ),
        StreamingCandidate(
            name="Patrick Corbin", team="WSH",
            pitch_days=[4],  # Fri
            points_per_start=28,
            floor=-5, ceiling=50, disaster_prob=0.15,
            snipe_tier=SnipeRiskTier.LOW,
            opponents=["PIT"]
        ),
        StreamingCandidate(
            name="David Festa", team="MIN",
            pitch_days=[3, 6],  # Thu, Sun (two-start!)
            points_per_start=32,
            floor=8, ceiling=52, disaster_prob=0.10,
            snipe_tier=SnipeRiskTier.HIGH,
            opponents=["OAK", "CHW"]
        ),
        StreamingCandidate(
            name="Adam Oller", team="OAK",
            pitch_days=[1],  # Tue
            points_per_start=22,
            floor=-10, ceiling=45, disaster_prob=0.18,
            snipe_tier=SnipeRiskTier.MINIMAL,
            opponents=["CWS"]
        ),
        StreamingCandidate(
            name="Jack Leiter", team="TEX",
            pitch_days=[5],  # Sat
            points_per_start=30,
            floor=5, ceiling=55, disaster_prob=0.12,
            snipe_tier=SnipeRiskTier.MODERATE,
            opponents=["COL"]
        ),
        StreamingCandidate(
            name="Seth Lugo", team="KC",
            pitch_days=[2, 6],  # Wed, Sun (two-start!)
            points_per_start=38,
            floor=12, ceiling=58, disaster_prob=0.06,
            snipe_tier=SnipeRiskTier.HIGH,
            opponents=["DET", "CLE"]
        ),
    ]

    # Create scheduler
    scheduler = SlotScheduler(league_activity=1.2)  # Somewhat active league

    # Create weekly schedule (2 slots most days, 3 on weekend)
    schedule = scheduler.create_weekly_schedule([2, 2, 2, 2, 2, 3, 3])

    # Optimize full week
    print("\n--- FULL WEEK OPTIMIZATION ---")
    result = scheduler.optimize_week(candidates, schedule)
    print(result)

    # Show contingency tree
    print("\n--- CONTINGENCY PLANNING ---")
    optimizer = SlotOptimizer(candidates, schedule)
    planner = ContingencyPlanner(optimizer)
    print(planner.get_contingency_tree(result))

    # Simulate daily recommendations
    print("\n--- MONDAY RECOMMENDATION ---")
    rec = scheduler.get_daily_recommendation(candidates, schedule, current_day=0)

    print("Add today:")
    for s in rec['add_today']:
        print(f"  - {s.name}")
    print()
    print("Rationale:")
    for r in rec['rationale']:
        print(f"  - {r}")

    print("\nSnipe alerts:")
    for cand, urgency, reason in rec['snipe_alerts']:
        print(f"  - {cand.name}: {reason}")

    print("\nUrgency ranking (top 5):")
    for cand, urgency, reason in rec['urgency_ranking'][:5]:
        print(f"  {cand.name}: {urgency:.1f} - {reason}")

    # Snipe risk analysis
    print("\n--- SNIPE RISK ANALYSIS ---")
    snipe_calc = SnipeRiskCalculator(league_activity=1.2)

    for cand in candidates:
        if cand.pitch_days:
            first_pitch = min(cand.pitch_days)
            surv = snipe_calc.survival_probability(cand, first_pitch)
            print(f"{cand.name}: {cand.snipe_tier.value} tier, "
                  f"{surv:.0%} survival to {DAYS_OF_WEEK[first_pitch]}")

    # Solve time demonstration
    print("\n--- SOLVE TIME BENCHMARK ---")
    import time
    times = []
    for _ in range(10):
        start = time.time()
        SlotOptimizer(candidates, schedule).solve()
        times.append((time.time() - start) * 1000)

    avg_time = sum(times) / len(times)
    print(f"Average solve time: {avg_time:.2f}ms (over 10 runs)")
    print(f"Solver: {'OR-Tools CP-SAT' if HAS_ORTOOLS else 'Brute Force'}")

    print("\n" + "=" * 70)
    print("Demo complete!")


if __name__ == "__main__":
    demo()
