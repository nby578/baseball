"""
Weekly Add Optimizer for BLJ X

Maximizes the value of 5 weekly adds considering:
- All streaming opportunities throughout the week
- Roster constraints (who can be dropped, when)
- Two-start pitcher decisions
- IL return situations (save an add?)
- Timing (moves lock at midnight)

Goal: Maximize total expected points from all 5 adds.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
from enum import Enum
import itertools

from roster_manager import Roster, Player, DropTier, ILStatus
from weekly_schedule import WeeklySchedule, PitchingStart, fetch_week_schedule
from points_projector import project_starter, quick_stream_score


class AddType(Enum):
    STREAMER = "streamer"      # Streaming pitcher
    BATTER = "batter"          # Position player pickup
    IL_ACTIVATION = "il"       # Activating player from IL
    TWO_START = "two_start"    # Two-start pitcher


@dataclass
class StreamingOption:
    """A potential streaming add."""
    pitcher_name: str
    team: str
    opponent: str
    game_date: date
    is_home: bool

    # Projection
    expected_points: float = 0.0
    streaming_score: float = 0.0  # From matchup quality

    # Two-start info
    is_two_start: bool = False
    second_start_date: Optional[date] = None
    second_opponent: Optional[str] = None
    second_expected_points: float = 0.0
    total_two_start_points: float = 0.0

    # Constraints
    drop_deadline: Optional[datetime] = None  # When must you drop to add this?
    available: bool = True  # Still on waivers?

    def total_points(self) -> float:
        """Total points if you roster this player."""
        if self.is_two_start:
            return self.total_two_start_points
        return self.expected_points


@dataclass
class AddRecommendation:
    """A recommended add for the week."""
    day: date
    add_type: AddType
    player_name: str
    opponent: str
    expected_points: float
    drop_candidate: Optional[str] = None
    notes: str = ""
    priority: int = 1  # 1 = highest

    def summary(self) -> str:
        day_str = self.day.strftime("%a %m/%d")
        drop_str = f" (drop {self.drop_candidate})" if self.drop_candidate else ""
        return f"{day_str}: ADD {self.player_name} vs {self.opponent} ({self.expected_points:.1f} pts){drop_str}"


@dataclass
class WeeklyPlan:
    """Optimized plan for the week's adds."""
    week_start: date
    adds_available: int = 5
    il_reserves: int = 0  # Adds to save for IL returns

    recommendations: list = field(default_factory=list)
    total_expected_points: float = 0.0

    # What we're giving up
    opportunity_cost: list = field(default_factory=list)  # Streams we're skipping

    # Warnings
    warnings: list = field(default_factory=list)

    def add_recommendation(self, rec: AddRecommendation):
        self.recommendations.append(rec)
        self.total_expected_points += rec.expected_points

    def summary(self) -> str:
        lines = [
            f"=== WEEKLY ADD PLAN ===",
            f"Week of {self.week_start.strftime('%m/%d')}",
            f"",
            f"ADDS TO MAKE ({len(self.recommendations)}/{self.adds_available}):",
        ]

        for i, rec in enumerate(sorted(self.recommendations, key=lambda x: x.day), 1):
            lines.append(f"  {i}. {rec.summary()}")
            if rec.notes:
                lines.append(f"     Note: {rec.notes}")

        lines.append(f"\nTOTAL EXPECTED POINTS: {self.total_expected_points:.1f}")

        if self.il_reserves > 0:
            lines.append(f"\nRESERVED FOR IL: {self.il_reserves} add(s)")

        if self.warnings:
            lines.append(f"\nWARNINGS:")
            for w in self.warnings:
                lines.append(f"  ! {w}")

        if self.opportunity_cost:
            lines.append(f"\nSKIPPED OPTIONS (opportunity cost):")
            for opt in self.opportunity_cost[:5]:
                lines.append(f"  - {opt}")

        return "\n".join(lines)


class WeeklyOptimizer:
    """
    Optimizes weekly adds to maximize fantasy points.
    """

    def __init__(self, roster: Roster, schedule: WeeklySchedule):
        self.roster = roster
        self.schedule = schedule
        self.streaming_options: list[StreamingOption] = []

    def load_streaming_options(self, available_pitchers: list[str] = None):
        """
        Load all streaming options for the week.

        Args:
            available_pitchers: List of available pitcher names (from waivers)
                               If None, uses all pitchers from schedule
        """
        self.streaming_options = []

        # Group starts by pitcher
        pitcher_starts = {}
        for start in self.schedule.starts:
            if available_pitchers and start.pitcher_name not in available_pitchers:
                continue

            if start.pitcher_name not in pitcher_starts:
                pitcher_starts[start.pitcher_name] = []
            pitcher_starts[start.pitcher_name].append(start)

        # Create streaming options
        for pitcher, starts in pitcher_starts.items():
            # Sort by date
            starts = sorted(starts, key=lambda x: x.game_date)

            if len(starts) >= 2:
                # Two-start pitcher
                opt = StreamingOption(
                    pitcher_name=pitcher,
                    team=starts[0].team,
                    opponent=starts[0].opponent,
                    game_date=starts[0].game_date,
                    is_home=starts[0].is_home,
                    expected_points=starts[0].streaming_score,
                    streaming_score=starts[0].streaming_score,
                    is_two_start=True,
                    second_start_date=starts[1].game_date,
                    second_opponent=starts[1].opponent,
                    second_expected_points=starts[1].streaming_score,
                    total_two_start_points=starts[0].streaming_score + starts[1].streaming_score,
                )
                self.streaming_options.append(opt)

                # Also add individual starts as separate options
                for start in starts:
                    single_opt = StreamingOption(
                        pitcher_name=pitcher,
                        team=start.team,
                        opponent=start.opponent,
                        game_date=start.game_date,
                        is_home=start.is_home,
                        expected_points=start.streaming_score,
                        streaming_score=start.streaming_score,
                    )
                    self.streaming_options.append(single_opt)
            else:
                # Single start
                start = starts[0]
                opt = StreamingOption(
                    pitcher_name=pitcher,
                    team=start.team,
                    opponent=start.opponent,
                    game_date=start.game_date,
                    is_home=start.is_home,
                    expected_points=start.streaming_score,
                    streaming_score=start.streaming_score,
                )
                self.streaming_options.append(opt)

    def get_droppable_for_day(self, target_date: date) -> list[Player]:
        """
        Get players that can be dropped for an add on target_date.

        Constraint: Can't drop a pitcher who starts the next day.
        """
        next_day = target_date + timedelta(days=1)
        droppable = []

        for player in self.roster.get_droppable_players(for_streamer=True):
            # Check if pitcher starts next day
            if player.is_pitcher and player.next_start == next_day:
                continue
            droppable.append(player)

        return droppable

    def should_reserve_for_il(self) -> int:
        """
        Determine how many adds to reserve for IL returns.

        Returns number of adds to reserve (0-2).
        """
        reserves = 0

        # Check for imminent IL returns
        returning = self.roster.get_returning_soon(days=7)
        for player, days_until in returning:
            if player.drop_tier.value <= DropTier.HOLD.value:
                # Important player returning, reserve an add
                reserves += 1
                if reserves >= 2:
                    break

        # Check for DTD players who might need IL
        dtd = self.roster.get_dtd_players()
        if len(dtd) >= 2:
            # Multiple DTD players, might need emergency add
            reserves = max(reserves, 1)

        return min(reserves, 2)

    def optimize_week(self, reserve_for_il: bool = True) -> WeeklyPlan:
        """
        Generate optimized add plan for the week.

        Strategy:
        1. Score all streaming options
        2. Identify two-start pitchers worth rostering full week
        3. Fill remaining adds with best single-day streams
        4. Consider roster constraints and drop timing
        """
        plan = WeeklyPlan(
            week_start=self.schedule.week_start,
            adds_available=self.roster.adds_remaining(),
        )

        if reserve_for_il:
            plan.il_reserves = self.should_reserve_for_il()
            if plan.il_reserves > 0:
                plan.warnings.append(
                    f"Reserving {plan.il_reserves} add(s) for potential IL activation"
                )

        effective_adds = plan.adds_available - plan.il_reserves
        if effective_adds <= 0:
            plan.warnings.append("No adds available after IL reserves!")
            return plan

        # Sort all options by value
        all_options = sorted(
            self.streaming_options,
            key=lambda x: x.total_points(),
            reverse=True
        )

        # Track used adds and days
        adds_used = 0
        used_days = set()  # Days we've committed to
        selected = []

        # First pass: Look for elite two-start pitchers (1 add for 2 games)
        for opt in all_options:
            if adds_used >= effective_adds:
                break

            if opt.is_two_start and opt.total_two_start_points >= 100:
                # Elite two-start: worth the roster spot
                # Check if we can drop someone
                droppable = self.get_droppable_for_day(opt.game_date)
                if droppable:
                    rec = AddRecommendation(
                        day=opt.game_date,
                        add_type=AddType.TWO_START,
                        player_name=opt.pitcher_name,
                        opponent=f"{opt.opponent} & {opt.second_opponent}",
                        expected_points=opt.total_two_start_points,
                        drop_candidate=droppable[0].name,
                        notes=f"Two-start: {opt.game_date.strftime('%a')} & {opt.second_start_date.strftime('%a')}",
                        priority=1,
                    )
                    plan.add_recommendation(rec)
                    adds_used += 1
                    used_days.add(opt.game_date)
                    used_days.add(opt.second_start_date)
                    selected.append(opt.pitcher_name)

        # Second pass: Fill with best remaining single-day streams
        for opt in all_options:
            if adds_used >= effective_adds:
                break

            # Skip already selected or two-starts we didn't take
            if opt.pitcher_name in selected:
                continue
            if opt.is_two_start:
                continue

            # Skip if we already have a stream that day
            if opt.game_date in used_days:
                # Add to opportunity cost
                plan.opportunity_cost.append(
                    f"{opt.pitcher_name} vs {opt.opponent} on {opt.game_date.strftime('%a')} ({opt.expected_points:.1f} pts)"
                )
                continue

            # Check drop availability
            droppable = self.get_droppable_for_day(opt.game_date)
            if not droppable:
                plan.warnings.append(
                    f"No one to drop for {opt.pitcher_name} on {opt.game_date.strftime('%a')}"
                )
                continue

            rec = AddRecommendation(
                day=opt.game_date,
                add_type=AddType.STREAMER,
                player_name=opt.pitcher_name,
                opponent=opt.opponent,
                expected_points=opt.expected_points,
                drop_candidate=droppable[0].name,
                priority=adds_used + 2,
            )
            plan.add_recommendation(rec)
            adds_used += 1
            used_days.add(opt.game_date)
            selected.append(opt.pitcher_name)

        # Add remaining good options to opportunity cost
        for opt in all_options:
            if opt.pitcher_name not in selected and not opt.is_two_start:
                if opt.expected_points >= 40:
                    plan.opportunity_cost.append(
                        f"{opt.pitcher_name} vs {opt.opponent} on {opt.game_date.strftime('%a')} ({opt.expected_points:.1f} pts)"
                    )

        return plan

    def get_best_add_for_day(self, target_date: date) -> Optional[StreamingOption]:
        """Get the single best streaming option for a specific day."""
        day_options = [
            opt for opt in self.streaming_options
            if opt.game_date == target_date and not opt.is_two_start
        ]
        if not day_options:
            return None
        return max(day_options, key=lambda x: x.expected_points)


def generate_weekly_plan(roster: Roster = None) -> WeeklyPlan:
    """
    Convenience function to generate a weekly plan.

    Args:
        roster: Your roster (uses example if None)

    Returns:
        WeeklyPlan with recommendations
    """
    from roster_manager import create_example_roster

    if roster is None:
        roster = create_example_roster()

    # Fetch this week's schedule
    schedule = fetch_week_schedule()

    # Create optimizer
    optimizer = WeeklyOptimizer(roster, schedule)
    optimizer.load_streaming_options()

    # Generate plan
    plan = optimizer.optimize_week()

    return plan


if __name__ == "__main__":
    print("=== WEEKLY ADD OPTIMIZER ===\n")
    print("Fetching schedule and generating plan...\n")

    try:
        plan = generate_weekly_plan()
        print(plan.summary())
    except Exception as e:
        print(f"Error generating plan: {e}")
        print("\n(This may happen in offseason when no games are scheduled)")

        # Demo with fake data
        print("\n" + "=" * 50)
        print("DEMO MODE (sample output):\n")

        demo_plan = WeeklyPlan(
            week_start=date.today(),
            adds_available=5,
        )

        demo_plan.add_recommendation(AddRecommendation(
            day=date.today() + timedelta(days=1),
            add_type=AddType.TWO_START,
            player_name="Pablo Lopez",
            opponent="OAK & CHW",
            expected_points=95.5,
            drop_candidate="Some Streamer",
            notes="Two-start: Tue & Sun",
            priority=1,
        ))

        demo_plan.add_recommendation(AddRecommendation(
            day=date.today() + timedelta(days=3),
            add_type=AddType.STREAMER,
            player_name="Reese Olson",
            opponent="PIT",
            expected_points=52.3,
            drop_candidate="Another Streamer",
            priority=2,
        ))

        demo_plan.add_recommendation(AddRecommendation(
            day=date.today() + timedelta(days=5),
            add_type=AddType.STREAMER,
            player_name="Mitchell Parker",
            opponent="MIA",
            expected_points=48.1,
            drop_candidate="Bench Bat 1",
            priority=3,
        ))

        demo_plan.il_reserves = 1
        demo_plan.warnings.append("Reserving 1 add for potential IL activation (Acuna returning)")
        demo_plan.opportunity_cost = [
            "Bowden Francis vs COL on Wed (45.2 pts) - no drop available",
            "Kyle Gibson vs OAK on Sat (43.8 pts) - day already filled",
        ]

        print(demo_plan.summary())
