"""
Weekly Streaming Planner for Fantasy Baseball

Creates a day-by-day streaming plan based on:
- Probable starting pitchers schedule (from MLB Stats API)
- Available free agents in your league
- Matchup quality (opponent K%, ISO, park factors)
- Your current roster/drop candidates

Outputs ranked recommendations for each day of the week.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backtesting"))

from backtesting.yahoo_fetcher import YahooFetcher
from backtesting.stats_as_of import CumulativeStatsCalculator, TeamStatsCalculator
from backtesting.game_results import GameResultsFetcher

# Import our MLB schedule fetcher
from schedule_fetcher import MLBScheduleFetcher, ProbableStarter

# Park factors from matchup_evaluator
PARK_HR_FACTORS = {
    'LAD': 127, 'CIN': 123, 'NYY': 119, 'PHI': 114, 'LAA': 113,
    'COL': 106, 'BAL': 105, 'TEX': 104, 'TOR': 103, 'CHC': 101,
    'ATL': 100, 'MIL': 100, 'ARI': 99, 'HOU': 98, 'NYM': 97,
    'MIN': 96, 'WSH': 95, 'STL': 94, 'BOS': 93, 'CHW': 92,
    'DET': 91, 'TB': 90, 'KC': 89, 'SEA': 89, 'CLE': 88,
    'SD': 87, 'MIA': 85, 'SF': 84, 'OAK': 82, 'PIT': 76,
}


@dataclass
class StreamingOption:
    """A potential streaming pickup."""
    player_name: str
    player_key: str
    mlb_team: str
    position: str

    # Matchup details
    game_date: str
    opponent: str
    park: str
    is_home: bool

    # Stats
    k_bb_pct: Optional[float] = None
    gb_pct: Optional[float] = None
    ip_sample: Optional[float] = None

    # Recent form (last 5 starts)
    recent_avg_points: Optional[float] = None
    recent_trend: Optional[str] = None  # "hot", "cold", "neutral"
    recent_disaster_rate: Optional[float] = None

    # Opponent stats
    opp_k_pct: Optional[float] = None
    opp_iso: Optional[float] = None

    # Park factor
    park_hr_factor: int = 100

    # Scores
    pitcher_score: float = 0.0
    matchup_score: float = 0.0
    form_score: float = 0.0
    total_score: float = 0.0
    risk_tier: str = "UNKNOWN"
    expected_points: float = 0.0


@dataclass
class DailyPlan:
    """Streaming plan for a single day."""
    date: str
    day_name: str
    top_options: List[StreamingOption] = field(default_factory=list)
    games_count: int = 0


@dataclass
class WeeklyPlan:
    """Complete streaming plan for the week."""
    week_start: str
    week_end: str
    generated_at: str
    my_team: str
    daily_plans: List[DailyPlan] = field(default_factory=list)
    overall_top_targets: List[StreamingOption] = field(default_factory=list)


class StreamingPlanner:
    """Plan weekly streaming pickups."""

    def __init__(self, season: int = 2025, league_id: int = 89318):
        self.season = season
        self.league_id = league_id

        print(f"Initializing Streaming Planner for {season}...")

        # Initialize data fetchers
        self.yahoo = YahooFetcher(season)
        self.stats_calc = CumulativeStatsCalculator(season)
        self.team_stats = TeamStatsCalculator(season)
        self.schedule_fetcher = MLBScheduleFetcher(season)
        self.game_fetcher = GameResultsFetcher(season)

        # Cache
        self._rostered_players: Optional[set] = None
        self._my_team_key: Optional[str] = None
        self._schedule_cache: Dict[str, List] = {}

    def get_rostered_players(self) -> set:
        """Get all currently rostered player keys across the league."""
        if self._rostered_players is not None:
            return self._rostered_players

        print("  Fetching current rosters...")
        rosters = self.yahoo.get_all_rosters()

        rostered = set()
        for team_key, players in rosters.items():
            for player in players:
                if player.get('player_key'):
                    rostered.add(player['player_key'])

        self._rostered_players = rostered
        print(f"    {len(rostered)} players currently rostered")
        return rostered

    def get_my_team_roster(self) -> Tuple[str, List[Dict]]:
        """Get my team's current roster."""
        # Find my team key (team 7 in BLJ X)
        team_keys = self.yahoo.get_all_team_keys()
        my_team_key = None

        for tk in team_keys:
            if tk.endswith('.t.7'):  # Vlad The Impaler
                my_team_key = tk
                break

        if not my_team_key:
            my_team_key = team_keys[0] if team_keys else None

        self._my_team_key = my_team_key

        if my_team_key:
            roster_data = self.yahoo.get_team_roster(my_team_key)
            if roster_data:
                return my_team_key, self.yahoo._parse_roster(roster_data)

        return my_team_key, []

    def score_streaming_option(self, option: StreamingOption) -> StreamingOption:
        """
        Score a streaming option using VALIDATED model v4 (Jan 2026).

        Based on 415-pick backtest:
        - IP sample (80%): r=0.295, BEST predictor - experience is EVERYTHING
        - Recent form: Included in experience weighting
        - Matchup (10%): Opponent + park explain only ~1 pt difference

        CRITICAL FINDINGS:
        - PROVEN (120+ IP): 10.8 pts avg, 4.9 IP/start - can absorb HR
        - DEVELOPING (80-120): 8.0 pts avg
        - UNPROVEN (<80): 5.7 pts avg - NEVER STREAM (hard filter)

        Matchup only matters as tiebreaker between same-experience pitchers.
        """
        # === HARD FILTER: IP < 80 = NO-GO ===
        ip = option.ip_sample or 30
        if ip < 80:
            option.total_score = 0
            option.expected_points = 5.7  # Historical avg for unproven
            option.risk_tier = "NO_GO"
            option.form_score = 0
            option.matchup_score = 0
            return option

        # === EXPERIENCE SCORE (80% weight) ===
        # Only reaches here if IP >= 80 (passed hard filter)
        if ip < 100:
            experience_score = 50 + (ip - 80) * 1.5  # 80 IP = 50, 100 IP = 80
        elif ip < 120:
            experience_score = 80 + (ip - 100) * 0.5  # 100 IP = 80, 120 IP = 90
        elif ip < 150:
            experience_score = 90 + (ip - 120) * 0.33  # 120 IP = 90, 150 IP = 100
        else:
            experience_score = 100

        # === RECENT FORM (45% weight) - SECOND BEST ===
        recent_avg = option.recent_avg_points
        recent_trend = option.recent_trend
        disaster_rate = option.recent_disaster_rate

        if recent_avg is not None:
            option.form_score = min(100, max(0, recent_avg * 5))

            # Trend bonus/penalty
            if recent_trend == "hot":
                option.form_score = min(100, option.form_score + 12)
            elif recent_trend == "cold":
                option.form_score = max(0, option.form_score - 8)

            # Disaster rate adjustment
            if disaster_rate and disaster_rate > 0.4:
                option.form_score = max(0, option.form_score - 15)
            elif disaster_rate and disaster_rate < 0.2:
                option.form_score = min(100, option.form_score + 8)
        else:
            option.form_score = min(70, 30 + ip * 0.3) if ip else 40

        # === MATCHUP FACTORS (10% weight) - Small but real effect ===
        # Easy opps (PIT/OAK) = 9.4 pts, Hard opps (LAD/NYY) = 8.1 pts
        opp_k = option.opp_k_pct or 0.22
        option.matchup_score = min(100, max(0, (opp_k - 0.18) * 500))

        hr_factor = option.park_hr_factor or 100
        park_score = min(100, max(0, (130 - hr_factor) * 1.5))

        minor_score = (option.matchup_score * 0.5 + park_score * 0.5)

        # === COMBINED SCORE (Validated weights Jan 2026) ===
        # Experience is king (70%), recent form matters (20%), matchup is tiebreaker (10%)
        option.total_score = (
            experience_score * 0.70 +
            option.form_score * 0.20 +
            minor_score * 0.10
        )

        # === EXPECTED POINTS ===
        option.expected_points = round(1 + (option.total_score * 0.12), 1)

        # === RISK TIER (Validated Decision Matrix Jan 2026) ===
        # Based on 415-pick backtest showing IP sample is the key factor
        is_hot = recent_trend == "hot"
        low_disaster = disaster_rate is not None and disaster_rate < 0.2
        high_disaster = disaster_rate is not None and disaster_rate >= 0.4

        # Check opponent difficulty for developing pitchers
        hard_opponents = {'LAD', 'NYY', 'HOU', 'ATL', 'PHI'}
        vs_hard = option.opponent in hard_opponents if option.opponent else False

        # Decision matrix based on IP tiers
        if ip >= 120:
            # PROVEN: Always stream (10.8 pts avg)
            if option.total_score >= 70 and low_disaster:
                option.risk_tier = "ELITE"
            elif option.total_score >= 55:
                option.risk_tier = "STRONG"
            else:
                option.risk_tier = "MODERATE"
        elif ip >= 100:
            # HIGH-DEVELOPING: Good vs any opponent
            if vs_hard:
                option.risk_tier = "MODERATE"
            elif option.total_score >= 60:
                option.risk_tier = "STRONG"
            else:
                option.risk_tier = "MODERATE"
        else:  # 80-100 IP
            # DEVELOPING: Only vs easy opponents
            if vs_hard:
                option.risk_tier = "AVOID"  # Can't handle hard matchups
            elif high_disaster:
                option.risk_tier = "RISKY"
            elif option.total_score >= 50:
                option.risk_tier = "MODERATE"
            else:
                option.risk_tier = "RISKY"

        return option

    def get_week_schedule(self, start_date: str = None, days: int = 7) -> List[Dict]:
        """
        Get probable starters for the week from MLB API.

        Args:
            start_date: Start date (YYYY-MM-DD), defaults to today
            days: Number of days to fetch

        Returns:
            List of pitcher dicts ready for scoring
        """
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")

        # Check cache
        cache_key = f"{start_date}_{days}"
        if cache_key in self._schedule_cache:
            return self._schedule_cache[cache_key]

        print(f"  Fetching probable starters from MLB API...")
        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days-1)).strftime("%Y-%m-%d")

        # Get all probable starters
        starters = self.schedule_fetcher.get_all_starters(start_date, end_date)

        # Convert to dict format for scoring
        pitchers = []
        for sp in starters:
            if sp.pitcher_name and sp.pitcher_name != "TBD":
                pitchers.append({
                    "name": sp.pitcher_name,
                    "team": sp.team,
                    "position": "SP",
                    "game_date": sp.game_date,
                    "opponent": sp.opponent,
                    "park": sp.park,
                    "is_home": sp.home_away == "home",
                    "pitcher_id": sp.pitcher_id,
                })

        print(f"    Found {len(pitchers)} probable starters ({len(starters) - len(pitchers)} TBD)")

        self._schedule_cache[cache_key] = pitchers
        return pitchers

    def create_weekly_plan(
        self,
        available_pitchers: List[Dict] = None,
        days_ahead: int = 7,
        start_date: str = None,
        fetch_from_mlb: bool = True
    ) -> WeeklyPlan:
        """
        Create a full weekly streaming plan.

        Args:
            available_pitchers: List of available pitcher dicts (name, team, etc.)
                               If None and fetch_from_mlb=True, fetches from MLB API
            days_ahead: Number of days to plan
            start_date: Start date (YYYY-MM-DD), defaults to today
            fetch_from_mlb: If True and no pitchers provided, fetch from MLB API

        Returns:
            WeeklyPlan with daily recommendations
        """
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")

        now = datetime.strptime(start_date, "%Y-%m-%d")
        week_start = start_date
        week_end = (now + timedelta(days=days_ahead-1)).strftime("%Y-%m-%d")

        # Get my team info
        my_team_key, my_roster = self.get_my_team_roster()
        my_team_name = "Vlad The Impaler" if my_team_key else "Unknown"

        plan = WeeklyPlan(
            week_start=week_start,
            week_end=week_end,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            my_team=my_team_name,
        )

        # Fetch from MLB API if no pitchers provided
        if not available_pitchers and fetch_from_mlb:
            print("\n  Fetching probable starters from MLB API...")
            available_pitchers = self.get_week_schedule(start_date, days_ahead)

        if not available_pitchers:
            print("\n  Note: No pitcher schedule available.")
            return plan

        # Get rostered players to filter out
        rostered = self.get_rostered_players()

        # Process each day
        all_options = []
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        for day_offset in range(days_ahead):
            day = start_dt + timedelta(days=day_offset)
            day_str = day.strftime("%Y-%m-%d")
            day_name = day.strftime("%A")

            daily = DailyPlan(date=day_str, day_name=day_name)

            # Filter pitchers scheduled for this day
            day_pitchers = [
                p for p in available_pitchers
                if p.get('game_date') == day_str
            ]

            daily.games_count = len(day_pitchers)

            # Score each pitcher
            for p in day_pitchers:
                # Skip if already rostered
                if p.get('player_key') in rostered:
                    continue

                # Get pitcher stats
                stats = self.stats_calc.get_pitcher_stats_through(
                    p.get('name', ''),
                    day_str,
                    use_game_logs=False
                )

                # Get opponent stats
                opp_stats = None
                if p.get('opponent'):
                    opp_stats = self.team_stats.get_team_stats_as_of(p['opponent'])

                # Get recent form (last 5 starts)
                recent_form = self.game_fetcher.get_recent_form(
                    p.get('name', ''),
                    day_str,
                    num_starts=5
                )

                option = StreamingOption(
                    player_name=p.get('name', ''),
                    player_key=p.get('player_key', ''),
                    mlb_team=p.get('team', ''),
                    position=p.get('position', 'SP'),
                    game_date=day_str,
                    opponent=p.get('opponent', ''),
                    park=p.get('park', ''),
                    is_home=p.get('is_home', True),
                    k_bb_pct=stats.get('k_bb_pct') if stats else None,
                    gb_pct=stats.get('gb_pct') if stats else None,
                    ip_sample=stats.get('ip') if stats else None,
                    recent_avg_points=recent_form.get('avg_points') if recent_form else None,
                    recent_trend=recent_form.get('trend') if recent_form else None,
                    recent_disaster_rate=recent_form.get('disaster_rate') if recent_form else None,
                    opp_k_pct=opp_stats.get('k_pct') if opp_stats else None,
                    opp_iso=opp_stats.get('iso') if opp_stats else None,
                    park_hr_factor=PARK_HR_FACTORS.get(p.get('park', '').upper(), 100),
                )

                option = self.score_streaming_option(option)
                daily.top_options.append(option)
                all_options.append(option)

            # Sort by score
            daily.top_options.sort(key=lambda x: -x.total_score)
            daily.top_options = daily.top_options[:5]  # Top 5 per day

            plan.daily_plans.append(daily)

        # Overall top targets (across the week)
        all_options.sort(key=lambda x: -x.total_score)
        plan.overall_top_targets = all_options[:10]

        return plan

    def print_plan(self, plan: WeeklyPlan):
        """Print formatted weekly plan."""
        print("\n" + "=" * 70)
        print(f"WEEKLY STREAMING PLAN - {plan.my_team}")
        print(f"Week: {plan.week_start} to {plan.week_end}")
        print(f"Generated: {plan.generated_at}")
        print("=" * 70)

        if plan.overall_top_targets:
            print("\nTOP STREAMING TARGETS THIS WEEK:")
            print("-" * 85)
            print(f"{'Rank':<5} {'Pitcher':<20} {'Day':<6} {'vs':<5} {'@':<5} {'Score':>6} {'Tier':<10} {'E[Pts]':>7} {'Form':>8}")
            print("-" * 85)

            for i, opt in enumerate(plan.overall_top_targets[:10], 1):
                day_abbr = datetime.strptime(opt.game_date, "%Y-%m-%d").strftime("%a")
                # Show trend indicator
                if opt.recent_trend == "hot":
                    form_str = f"{opt.recent_avg_points:.0f} HOT" if opt.recent_avg_points else "HOT"
                elif opt.recent_trend == "cold":
                    form_str = f"{opt.recent_avg_points:.0f} COLD" if opt.recent_avg_points else "COLD"
                elif opt.recent_avg_points:
                    form_str = f"{opt.recent_avg_points:.0f}"
                else:
                    form_str = "-"
                print(f"{i:<5} {opt.player_name:<20} {day_abbr:<6} {opt.opponent:<5} {opt.park:<5} {opt.total_score:>6.1f} {opt.risk_tier:<10} {opt.expected_points:>7.1f} {form_str:>8}")

        if plan.daily_plans:
            print("\nDAY-BY-DAY BREAKDOWN:")
            for daily in plan.daily_plans:
                if daily.top_options:
                    print(f"\n{daily.day_name} ({daily.date}) - {daily.games_count} games:")
                    for i, opt in enumerate(daily.top_options[:3], 1):
                        print(f"  {i}. {opt.player_name} vs {opt.opponent} @ {opt.park} [{opt.risk_tier}] E[{opt.expected_points}]")

        print("\n" + "=" * 70)

    def save_plan(self, plan: WeeklyPlan, filepath: Path = None):
        """Save plan to JSON file."""
        if filepath is None:
            filepath = Path(__file__).parent / "plans" / f"streaming_plan_{plan.week_start}.json"

        filepath.parent.mkdir(exist_ok=True)

        # Convert to dict
        plan_dict = {
            "week_start": plan.week_start,
            "week_end": plan.week_end,
            "generated_at": plan.generated_at,
            "my_team": plan.my_team,
            "overall_top_targets": [
                {
                    "name": o.player_name,
                    "team": o.mlb_team,
                    "date": o.game_date,
                    "opponent": o.opponent,
                    "park": o.park,
                    "score": o.total_score,
                    "tier": o.risk_tier,
                    "expected_points": o.expected_points,
                }
                for o in plan.overall_top_targets
            ],
            "daily_plans": [
                {
                    "date": d.date,
                    "day": d.day_name,
                    "games": d.games_count,
                    "options": [
                        {
                            "name": o.player_name,
                            "opponent": o.opponent,
                            "tier": o.risk_tier,
                            "expected_points": o.expected_points,
                        }
                        for o in d.top_options
                    ]
                }
                for d in plan.daily_plans
            ]
        }

        with open(filepath, "w") as f:
            json.dump(plan_dict, f, indent=2)

        print(f"\nPlan saved to: {filepath}")


def demo_streaming_planner():
    """Demo the streaming planner with real MLB API data."""
    print("=" * 70)
    print("STREAMING PLANNER - LIVE MODE")
    print("=" * 70)

    # Create planner
    planner = StreamingPlanner(season=2025)

    # Check if we're in the offseason
    today = datetime.now()
    if today.month < 3 or (today.month == 3 and today.day < 20):
        # Use Opening Day 2025 for demo
        start_date = "2025-03-27"
        print(f"\nNote: MLB season hasn't started. Using Opening Week {start_date} for demo.")
    else:
        start_date = today.strftime("%Y-%m-%d")

    # Create plan using REAL MLB API data
    # fetch_from_mlb=True means it will automatically fetch probable starters
    plan = planner.create_weekly_plan(
        days_ahead=7,
        start_date=start_date,
        fetch_from_mlb=True
    )

    # Print results
    planner.print_plan(plan)

    # Save plan
    planner.save_plan(plan)


def demo_with_sample_data():
    """Demo with hardcoded sample data (no API calls)."""
    print("=" * 70)
    print("STREAMING PLANNER DEMO (Sample Data)")
    print("=" * 70)

    planner = StreamingPlanner(season=2025)

    today = datetime.now()
    sample_pitchers = [
        {"name": "Bailey Falter", "team": "PIT", "position": "SP",
         "game_date": (today + timedelta(days=0)).strftime("%Y-%m-%d"),
         "opponent": "CIN", "park": "PIT", "is_home": True},
        {"name": "Colin Rea", "team": "MIL", "position": "SP",
         "game_date": (today + timedelta(days=0)).strftime("%Y-%m-%d"),
         "opponent": "CHC", "park": "MIL", "is_home": True},
        {"name": "Zack Littell", "team": "TB", "position": "SP",
         "game_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
         "opponent": "OAK", "park": "TB", "is_home": True},
        {"name": "Kumar Rocker", "team": "TEX", "position": "SP",
         "game_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
         "opponent": "SEA", "park": "SEA", "is_home": False},
    ]

    plan = planner.create_weekly_plan(sample_pitchers, days_ahead=2, fetch_from_mlb=False)
    planner.print_plan(plan)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        demo_with_sample_data()
    else:
        demo_streaming_planner()
