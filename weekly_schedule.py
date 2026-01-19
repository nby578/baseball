"""
Weekly Schedule Scanner for BLJ X

Scans the week's MLB schedule to identify:
- All pitching matchups day by day
- Two-start pitchers
- Matchup quality for each start
"""
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from mlb_api import get_todays_games
from streaming import calculate_streaming_score, PARK_HR_FACTORS, TEAM_HR_RATE, TEAM_K_RATE


@dataclass
class PitchingStart:
    """A single pitching start."""
    pitcher_name: str
    pitcher_id: Optional[int]
    team: str
    opponent: str
    game_date: date
    is_home: bool
    game_time: Optional[str] = None
    venue: str = ""

    # Calculated matchup quality
    streaming_score: float = 0.0
    factors: dict = field(default_factory=dict)

    # Flags
    is_two_start: bool = False  # Part of a 2-start week
    start_number: int = 1       # 1st or 2nd start of week

    def matchup_summary(self) -> str:
        """Short matchup description."""
        loc = "vs" if self.is_home else "@"
        return f"{self.pitcher_name} ({self.team}) {loc} {self.opponent}"

    def full_summary(self) -> str:
        """Detailed matchup info."""
        loc = "vs" if self.is_home else "@"
        two_start = " [2-START]" if self.is_two_start else ""
        return (f"{self.game_date.strftime('%a %m/%d')}: "
                f"{self.pitcher_name} ({self.team}) {loc} {self.opponent} "
                f"- Score: {self.streaming_score:.1f}{two_start}")


@dataclass
class WeeklySchedule:
    """A week's worth of pitching matchups."""
    week_start: date
    week_end: date
    starts: list = field(default_factory=list)

    # Organized views
    by_date: dict = field(default_factory=dict)      # date -> [starts]
    by_pitcher: dict = field(default_factory=dict)   # pitcher_name -> [starts]
    two_start_pitchers: list = field(default_factory=list)

    def add_start(self, start: PitchingStart):
        """Add a start to the schedule."""
        self.starts.append(start)

        # Index by date
        if start.game_date not in self.by_date:
            self.by_date[start.game_date] = []
        self.by_date[start.game_date].append(start)

        # Index by pitcher
        if start.pitcher_name not in self.by_pitcher:
            self.by_pitcher[start.pitcher_name] = []
        self.by_pitcher[start.pitcher_name].append(start)

    def identify_two_start_pitchers(self):
        """Find pitchers with 2+ starts this week."""
        self.two_start_pitchers = []
        for pitcher, starts in self.by_pitcher.items():
            if len(starts) >= 2:
                self.two_start_pitchers.append(pitcher)
                # Mark the starts
                for i, start in enumerate(starts):
                    start.is_two_start = True
                    start.start_number = i + 1

    def get_day_starts(self, target_date: date) -> list:
        """Get all starts for a specific date."""
        return self.by_date.get(target_date, [])

    def get_pitcher_starts(self, pitcher_name: str) -> list:
        """Get all starts for a specific pitcher."""
        return self.by_pitcher.get(pitcher_name, [])

    def get_best_streams(self, target_date: date, top_n: int = 10) -> list:
        """Get best streaming options for a date."""
        day_starts = self.get_day_starts(target_date)
        sorted_starts = sorted(day_starts, key=lambda x: x.streaming_score, reverse=True)
        return sorted_starts[:top_n]

    def get_two_start_analysis(self) -> list:
        """Analyze two-start pitchers for the week."""
        analysis = []
        for pitcher in self.two_start_pitchers:
            starts = self.get_pitcher_starts(pitcher)
            total_score = sum(s.streaming_score for s in starts)
            avg_score = total_score / len(starts)

            # Determine recommendation
            scores = [s.streaming_score for s in starts]
            if min(scores) >= 50:
                rec = "START BOTH"
            elif min(scores) >= 35:
                rec = "START BOTH (one risky)"
            elif max(scores) >= 50 and min(scores) < 35:
                rec = "START ONE (skip bad matchup)"
            else:
                rec = "CONSIDER SKIPPING"

            analysis.append({
                "pitcher": pitcher,
                "starts": starts,
                "total_score": total_score,
                "avg_score": avg_score,
                "min_score": min(scores),
                "max_score": max(scores),
                "recommendation": rec,
            })

        return sorted(analysis, key=lambda x: x["total_score"], reverse=True)

    def summary(self) -> str:
        """Print weekly summary."""
        lines = [
            f"=== WEEKLY SCHEDULE ===",
            f"{self.week_start.strftime('%m/%d')} - {self.week_end.strftime('%m/%d')}",
            f"Total Starts: {len(self.starts)}",
            f"Two-Start Pitchers: {len(self.two_start_pitchers)}",
            "",
        ]

        # Day by day
        current = self.week_start
        while current <= self.week_end:
            day_starts = self.get_day_starts(current)
            lines.append(f"\n{current.strftime('%A %m/%d')} ({len(day_starts)} starts):")

            if day_starts:
                # Top 5 streams for the day
                top = sorted(day_starts, key=lambda x: x.streaming_score, reverse=True)[:5]
                for s in top:
                    two = " **2-START**" if s.is_two_start else ""
                    loc = "vs" if s.is_home else "@"
                    lines.append(f"  {s.streaming_score:5.1f} - {s.pitcher_name} ({s.team}) {loc} {s.opponent}{two}")

            current += timedelta(days=1)

        # Two-start analysis
        if self.two_start_pitchers:
            lines.append("\n" + "=" * 50)
            lines.append("TWO-START PITCHER ANALYSIS:")
            for analysis in self.get_two_start_analysis():
                lines.append(f"\n{analysis['pitcher']}:")
                for s in analysis['starts']:
                    loc = "vs" if s.is_home else "@"
                    lines.append(f"  {s.game_date.strftime('%a')}: {loc} {s.opponent} ({s.streaming_score:.1f})")
                lines.append(f"  Total: {analysis['total_score']:.1f} | Rec: {analysis['recommendation']}")

        return "\n".join(lines)


def fetch_week_schedule(start_date: Optional[date] = None) -> WeeklySchedule:
    """
    Fetch the week's pitching schedule from MLB API.

    Args:
        start_date: Monday of the week (defaults to current week's Monday)

    Returns:
        WeeklySchedule with all starts
    """
    if start_date is None:
        # Get this week's Monday
        today = date.today()
        start_date = today - timedelta(days=today.weekday())

    week_end = start_date + timedelta(days=6)

    schedule = WeeklySchedule(week_start=start_date, week_end=week_end)

    # Fetch each day
    current = start_date
    while current <= week_end:
        date_str = current.strftime("%Y-%m-%d")
        try:
            games = get_todays_games(date_str)
        except Exception as e:
            print(f"Error fetching {date_str}: {e}")
            games = []

        for game in games:
            # Skip non-scheduled games
            if game.get("status") not in ["Scheduled", "Pre-Game", "Warmup", None]:
                # During season, include in-progress/final for historical
                if game.get("status") in ["In Progress", "Final"]:
                    pass
                else:
                    continue

            # Home pitcher
            if game.get("home_pitcher") and game["home_pitcher"] != "TBD":
                score, factors = calculate_streaming_score(
                    opponent=game["away_abbrev"],
                    is_home=True
                )
                start = PitchingStart(
                    pitcher_name=game["home_pitcher"],
                    pitcher_id=game.get("home_pitcher_id"),
                    team=game["home_abbrev"],
                    opponent=game["away_abbrev"],
                    game_date=current,
                    is_home=True,
                    game_time=game.get("game_time"),
                    venue=game.get("venue", ""),
                    streaming_score=score,
                    factors=factors,
                )
                schedule.add_start(start)

            # Away pitcher
            if game.get("away_pitcher") and game["away_pitcher"] != "TBD":
                score, factors = calculate_streaming_score(
                    opponent=game["home_abbrev"],
                    is_home=False
                )
                start = PitchingStart(
                    pitcher_name=game["away_pitcher"],
                    pitcher_id=game.get("away_pitcher_id"),
                    team=game["away_abbrev"],
                    opponent=game["home_abbrev"],
                    game_date=current,
                    is_home=False,
                    game_time=game.get("game_time"),
                    venue=game.get("venue", ""),
                    streaming_score=score,
                    factors=factors,
                )
                schedule.add_start(start)

        current += timedelta(days=1)

    # Identify two-start pitchers
    schedule.identify_two_start_pitchers()

    return schedule


def get_streaming_calendar(weeks: int = 2) -> str:
    """
    Get a streaming calendar for the next N weeks.

    Shows best streaming days and two-start opportunities.
    """
    lines = ["=== STREAMING CALENDAR ===\n"]

    today = date.today()
    current_monday = today - timedelta(days=today.weekday())

    for week in range(weeks):
        week_start = current_monday + timedelta(weeks=week)
        schedule = fetch_week_schedule(week_start)

        lines.append(f"\nWEEK OF {week_start.strftime('%m/%d')}:")
        lines.append("-" * 40)

        # Best streaming days (by avg score of top 5)
        day_scores = []
        current = week_start
        while current <= schedule.week_end:
            day_starts = schedule.get_day_starts(current)
            if day_starts:
                top_5 = sorted(day_starts, key=lambda x: x.streaming_score, reverse=True)[:5]
                avg = sum(s.streaming_score for s in top_5) / len(top_5)
                day_scores.append((current, avg, len(day_starts)))
            current += timedelta(days=1)

        if day_scores:
            lines.append("\nBest Streaming Days:")
            for d, avg, count in sorted(day_scores, key=lambda x: x[1], reverse=True)[:3]:
                lines.append(f"  {d.strftime('%a %m/%d')}: {avg:.1f} avg ({count} starts)")

        # Two-start pitchers
        if schedule.two_start_pitchers:
            lines.append(f"\nTwo-Start Pitchers ({len(schedule.two_start_pitchers)}):")
            for analysis in schedule.get_two_start_analysis()[:5]:
                lines.append(f"  {analysis['pitcher']}: {analysis['total_score']:.1f} total ({analysis['recommendation']})")

    return "\n".join(lines)


if __name__ == "__main__":
    print("Fetching this week's schedule...")
    print("(Note: May show limited data in offseason)\n")

    schedule = fetch_week_schedule()
    print(schedule.summary())

    print("\n" + "=" * 60)
    print(get_streaming_calendar(weeks=1))
