"""
Complete Backtester for Fantasy Baseball Streaming Models

Validates matchup_evaluator predictions against actual historical results.
Uses:
- state_reconstructor: League state at any date
- stats_as_of: Pitcher/team stats cumulative through date
- game_results: Actual pitcher performance

Outputs accuracy metrics and validation report.
"""

import json
import sys
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Local imports
from state_reconstructor import StateReconstructor
from stats_as_of import CumulativeStatsCalculator, TeamStatsCalculator
from game_results import GameResultsFetcher, PitcherStart

# Data directories
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# Park factors (HR factor, from Baseball Savant 2023-2025)
PARK_HR_FACTORS = {
    "LAD": 127, "CIN": 123, "NYY": 119, "PHI": 116, "CHC": 115,
    "BOS": 114, "BAL": 112, "TEX": 111, "COL": 106, "TOR": 105,
    "MIL": 104, "ATL": 103, "MIN": 102, "ARI": 101, "HOU": 100,
    "TB": 99, "KC": 98, "CLE": 97, "STL": 96, "CHW": 95,
    "DET": 94, "WAS": 93, "NYM": 92, "SF": 91, "SEA": 89,
    "SD": 88, "MIA": 86, "LAA": 85, "OAK": 82, "PIT": 76,
}


@dataclass
class BacktestRecord:
    """Complete record of one streaming add backtest."""
    # Add info
    transaction_id: str
    add_date: str
    pitcher_name: str
    pitcher_team: str
    fantasy_team: str

    # Pre-add stats (as of date)
    pitcher_k_bb_pct: Optional[float] = None
    pitcher_gb_pct: Optional[float] = None
    pitcher_ip_sample: Optional[float] = None

    # Recent form (last 5 starts before add date)
    recent_starts: Optional[int] = None
    recent_avg_points: Optional[float] = None
    recent_disaster_rate: Optional[float] = None
    recent_trend: Optional[str] = None  # "hot", "cold", "neutral"

    # Matchup info (for next start)
    opponent: Optional[str] = None
    opponent_k_pct: Optional[float] = None
    opponent_iso: Optional[float] = None
    park: Optional[str] = None
    park_hr_factor: Optional[int] = None

    # Model prediction
    predicted_score: Optional[float] = None
    risk_tier: Optional[str] = None

    # Actual results
    actual_game_date: Optional[str] = None
    actual_ip: Optional[float] = None
    actual_k: Optional[int] = None
    actual_bb: Optional[int] = None
    actual_hr: Optional[int] = None
    actual_points: Optional[float] = None

    # Comparison
    error: Optional[float] = None  # actual - predicted
    error_msg: Optional[str] = None


class StreamingBacktester:
    """Full backtesting pipeline for streaming model validation."""

    def __init__(self, season: int = 2024):
        self.season = season
        print(f"Initializing backtester for {season}...")

        # Initialize components
        self.state_reconstructor = StateReconstructor(season)
        self.stats_calculator = CumulativeStatsCalculator(season)
        self.team_stats_calculator = TeamStatsCalculator(season)
        self.game_fetcher = GameResultsFetcher(season)

        # Results storage
        self.records: List[BacktestRecord] = []

    def run(self, limit: int = None, verbose: bool = True) -> List[BacktestRecord]:
        """
        Run full backtest on all streaming pitcher adds.

        Args:
            limit: Max number of adds to process (for testing)
            verbose: Print progress updates

        Returns:
            List of BacktestRecord objects
        """
        # Get all streaming adds
        adds = self.state_reconstructor.get_streaming_adds()
        if verbose:
            print(f"\nFound {len(adds)} streaming pitcher adds")

        if limit:
            adds = adds[:limit]
            if verbose:
                print(f"Processing first {limit}...")

        print("\n" + "=" * 60)
        print("RUNNING BACKTEST")
        print("=" * 60)

        for i, add in enumerate(adds):
            if verbose and i % 25 == 0:
                print(f"  Processing {i+1}/{len(adds)}...")

            record = self._process_add(add)
            self.records.append(record)

        return self.records

    def _process_add(self, add: Dict) -> BacktestRecord:
        """Process a single streaming add."""
        record = BacktestRecord(
            transaction_id=add.get('transaction_id', ''),
            add_date=add.get('date', ''),
            pitcher_name=add.get('player_name', ''),
            pitcher_team=add.get('player_team', ''),
            fantasy_team=add.get('fantasy_team_name', ''),
        )

        try:
            # 1. Get pitcher stats as of add date
            pitcher_stats = self.stats_calculator.get_pitcher_stats_through(
                record.pitcher_name,
                record.add_date,
                use_game_logs=False  # Use season stats for speed
            )

            if pitcher_stats:
                record.pitcher_k_bb_pct = pitcher_stats.get('k_bb_pct')
                record.pitcher_gb_pct = pitcher_stats.get('gb_pct')
                record.pitcher_ip_sample = pitcher_stats.get('ip')

            # 2. Get recent form (last 5 starts before add date)
            recent_form = self.game_fetcher.get_recent_form(
                record.pitcher_name,
                record.add_date,
                num_starts=5
            )

            if recent_form:
                record.recent_starts = recent_form.get('starts')
                record.recent_avg_points = recent_form.get('avg_points')
                record.recent_disaster_rate = recent_form.get('disaster_rate')
                record.recent_trend = recent_form.get('trend')

            # 3. Get actual next start
            start = self.game_fetcher.find_next_start(
                record.pitcher_name,
                record.add_date,
                record.pitcher_team
            )

            if start:
                record.actual_game_date = start.game_date
                record.opponent = start.opponent
                record.park = start.park
                record.actual_ip = start.ip
                record.actual_k = start.k
                record.actual_bb = start.bb
                record.actual_hr = start.hr
                record.actual_points = start.fantasy_points

                # Get opponent stats
                if start.opponent:
                    opp_stats = self.team_stats_calculator.get_team_stats_as_of(start.opponent)
                    if opp_stats:
                        record.opponent_k_pct = opp_stats.get('k_pct')
                        record.opponent_iso = opp_stats.get('iso')

                # Get park factor
                if start.park:
                    record.park_hr_factor = PARK_HR_FACTORS.get(start.park.upper(), 100)

            # 3. Calculate model prediction
            if record.pitcher_k_bb_pct is not None:
                record.predicted_score, record.risk_tier = self._calculate_prediction(record)

            # 4. Calculate error
            if record.predicted_score is not None and record.actual_points is not None:
                record.error = record.actual_points - record.predicted_score

        except Exception as e:
            record.error_msg = str(e)

        return record

    def _calculate_prediction(self, record: BacktestRecord) -> Tuple[float, str]:
        """
        Calculate model prediction based on available data.

        CALIBRATED MODEL v2 (Jan 2026):
        - Pitcher K-BB% (30%): Strikeout ability
        - IP sample/experience (25%): Season track record
        - Recent form (25%): Last 5 starts - HOT pitchers stay hot!
        - Opponent K% (10%): Matchup difficulty
        - Park factor (10%): HR environment

        Note: GB% REMOVED - had negative correlation
        Note: Opponent ISO REMOVED - near-zero correlation

        Returns: (predicted_points, risk_tier)
        """
        # === PITCHER QUALITY (30% weight) ===
        k_bb = record.pitcher_k_bb_pct or 0
        pitcher_score = min(100, max(0, k_bb * 500))

        # === EXPERIENCE/RELIABILITY (25% weight) ===
        ip = record.pitcher_ip_sample or 30

        if ip < 30:
            experience_score = 20
        elif ip < 50:
            experience_score = 20 + (ip - 30) * 1.5
        elif ip < 150:
            experience_score = 50 + (ip - 50) * 0.5
        else:
            experience_score = 100

        # === RECENT FORM (25% weight) - NEW! ===
        # Hot pitchers stay hot, cold pitchers should be avoided
        recent_avg = record.recent_avg_points
        recent_trend = record.recent_trend
        disaster_rate = record.recent_disaster_rate

        if recent_avg is not None:
            # Recent avg points -> score (5 pts = 25, 10 pts = 50, 15 pts = 75, 20 pts = 100)
            form_score = min(100, max(0, recent_avg * 5))

            # Trend adjustment
            if recent_trend == "hot":
                form_score = min(100, form_score + 15)
            elif recent_trend == "cold":
                form_score = max(0, form_score - 15)

            # Disaster rate penalty (high disaster rate = unreliable)
            if disaster_rate and disaster_rate > 0.4:
                form_score = max(0, form_score - 20)
        else:
            # No recent form data - use neutral score
            form_score = 50

        # === OPPONENT MATCHUP (10% weight) ===
        opp_k = record.opponent_k_pct or 0.22
        opponent_score = min(100, max(0, (0.26 - opp_k) * 1250))

        # === PARK FACTOR (10% weight) ===
        hr_factor = record.park_hr_factor or 100
        park_score = min(100, max(0, (130 - hr_factor) * 1.85))

        # === COMBINED SCORE ===
        total_score = (
            pitcher_score * 0.30 +
            experience_score * 0.25 +
            form_score * 0.25 +
            opponent_score * 0.10 +
            park_score * 0.10
        )

        # === CONVERT TO FANTASY POINTS ===
        predicted_points = 2 + (total_score * 0.10)

        # === RISK TIER ===
        # Factor in recent form for tier assignment
        is_hot = recent_trend == "hot"
        is_cold = recent_trend == "cold"
        low_disaster = disaster_rate is not None and disaster_rate < 0.2

        if total_score >= 65 and ip >= 100 and low_disaster:
            risk_tier = "ELITE"      # High score + proven + consistent
        elif total_score >= 60 or (total_score >= 55 and is_hot):
            risk_tier = "STRONG"     # High score or hot streak
        elif total_score >= 50 and not is_cold:
            risk_tier = "MODERATE"   # Mid-tier, not trending down
        elif total_score >= 40 or is_cold:
            risk_tier = "RISKY"      # Below avg or cold
        else:
            risk_tier = "AVOID"      # Low score, high risk

        return round(predicted_points, 1), risk_tier

    def generate_report(self) -> Dict:
        """Generate comprehensive validation report."""
        valid_records = [r for r in self.records if r.actual_points is not None]
        predicted_records = [r for r in valid_records if r.predicted_score is not None]

        report = {
            "season": self.season,
            "total_adds": len(self.records),
            "with_actual_results": len(valid_records),
            "with_predictions": len(predicted_records),
            "metrics": {},
            "by_tier": {},
            "by_team": {},
            "correlation": None,
        }

        if not predicted_records:
            return report

        # Overall accuracy metrics
        predictions = [r.predicted_score for r in predicted_records]
        actuals = [r.actual_points for r in predicted_records]
        errors = [r.error for r in predicted_records if r.error is not None]

        if errors:
            report["metrics"]["mean_absolute_error"] = round(statistics.mean([abs(e) for e in errors]), 2)
            report["metrics"]["mean_error"] = round(statistics.mean(errors), 2)
            report["metrics"]["std_error"] = round(statistics.stdev(errors), 2) if len(errors) > 1 else 0

        # Calculate R² correlation
        if len(predictions) > 1:
            try:
                mean_pred = statistics.mean(predictions)
                mean_act = statistics.mean(actuals)

                ss_tot = sum((a - mean_act) ** 2 for a in actuals)
                ss_res = sum((a - p) ** 2 for a, p in zip(actuals, predictions))

                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                report["correlation"] = {
                    "r_squared": round(r_squared, 4),
                    "sample_size": len(predictions),
                }
            except Exception:
                pass

        # Stats by risk tier
        tier_order = ["ELITE", "STRONG", "MODERATE", "RISKY", "AVOID"]
        for tier in tier_order:
            tier_records = [r for r in predicted_records if r.risk_tier == tier]
            if tier_records:
                tier_actuals = [r.actual_points for r in tier_records if r.actual_points]
                report["by_tier"][tier] = {
                    "count": len(tier_records),
                    "avg_actual_points": round(statistics.mean(tier_actuals), 1) if tier_actuals else 0,
                    "min_points": round(min(tier_actuals), 1) if tier_actuals else 0,
                    "max_points": round(max(tier_actuals), 1) if tier_actuals else 0,
                }

        # Stats by fantasy team
        teams = set(r.fantasy_team for r in predicted_records if r.fantasy_team)
        for team in sorted(teams):
            team_records = [r for r in predicted_records if r.fantasy_team == team]
            team_actuals = [r.actual_points for r in team_records if r.actual_points]
            if team_actuals:
                report["by_team"][team] = {
                    "adds": len(team_records),
                    "avg_points": round(statistics.mean(team_actuals), 1),
                }

        return report

    def print_report(self, report: Dict = None):
        """Print formatted validation report."""
        if report is None:
            report = self.generate_report()

        print("\n" + "=" * 60)
        print(f"STREAMING MODEL VALIDATION - {report['season']} SEASON")
        print("=" * 60)

        print(f"\nData Coverage:")
        print(f"  Total streaming adds: {report['total_adds']}")
        print(f"  With actual game results: {report['with_actual_results']}")
        print(f"  With predictions: {report['with_predictions']}")

        if report.get("metrics"):
            print(f"\nPrediction Accuracy:")
            print(f"  Mean Absolute Error: {report['metrics'].get('mean_absolute_error', 'N/A')} pts")
            print(f"  Mean Error (bias): {report['metrics'].get('mean_error', 'N/A')} pts")
            print(f"  Std Deviation: {report['metrics'].get('std_error', 'N/A')} pts")

        if report.get("correlation"):
            print(f"\nCorrelation:")
            print(f"  R-squared: {report['correlation']['r_squared']}")
            print(f"  Sample size: {report['correlation']['sample_size']}")

        if report.get("by_tier"):
            print(f"\nActual Results by Risk Tier:")
            print(f"  {'Tier':<12} {'Count':>6} {'Avg Pts':>8} {'Range':>15}")
            print(f"  {'-'*12} {'-'*6} {'-'*8} {'-'*15}")
            for tier in ["ELITE", "SAFE", "MODERATE", "RISKY", "DANGEROUS"]:
                if tier in report["by_tier"]:
                    data = report["by_tier"][tier]
                    range_str = f"{data['min_points']:.0f} - {data['max_points']:.0f}"
                    print(f"  {tier:<12} {data['count']:>6} {data['avg_actual_points']:>8.1f} {range_str:>15}")

        # Check tier separation
        if "ELITE" in report.get("by_tier", {}) and "RISKY" in report.get("by_tier", {}):
            elite_avg = report["by_tier"]["ELITE"]["avg_actual_points"]
            risky_avg = report["by_tier"]["RISKY"]["avg_actual_points"]
            separation = elite_avg - risky_avg
            print(f"\n  Tier Separation (ELITE - RISKY): {separation:+.1f} pts")
            if separation > 0:
                print(f"  [OK] ELITE tier outperforms RISKY tier")
            else:
                print(f"  [!!] Warning: RISKY tier outperforms ELITE tier")

        if report.get("by_team"):
            print(f"\nTop Streamers by Fantasy Team:")
            sorted_teams = sorted(report["by_team"].items(), key=lambda x: -x[1]["adds"])[:5]
            for team, data in sorted_teams:
                print(f"  {team[:30]:<30} {data['adds']:>3} adds, {data['avg_points']:>5.1f} avg pts")

        print("\n" + "=" * 60)

    def save_results(self):
        """Save results to JSON files."""
        # Save full records
        records_file = RESULTS_DIR / f"backtest_records_{self.season}.json"
        records_data = [asdict(r) for r in self.records]
        with open(records_file, "w") as f:
            json.dump(records_data, f, indent=2, default=str)

        # Save report
        report = self.generate_report()
        report_file = RESULTS_DIR / f"backtest_report_{self.season}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nResults saved to:")
        print(f"  {records_file}")
        print(f"  {report_file}")


def run_backtest(season: int = 2024, limit: int = None):
    """Run full backtest for a season."""
    backtester = StreamingBacktester(season)
    backtester.run(limit=limit)
    backtester.print_report()
    backtester.save_results()
    return backtester


if __name__ == "__main__":
    import sys

    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100  # Default to 100 for testing

    run_backtest(season, limit)
