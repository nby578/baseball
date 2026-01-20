"""
Risk Analysis Module for Fantasy Baseball Streaming

The key insight: Pitcher downside is CATASTROPHIC (-13 per HR in BLJ X).
A blowup start (3+ HR) can cost -40 to -50 points and erase multiple good starts.

This module provides:
1. Floor/ceiling projections for each start
2. Disaster probability (P of 3+ HR allowed)
3. Risk-adjusted rankings that penalize high-variance pitchers
4. Hard filters for "no-go" matchups
5. Simple baseline tracker for comparing to quant picks

Key factors for pitcher blowup risk:
- Fly ball rate (higher = more HR risk)
- HR/9 rate (direct measure)
- Opponent HR rate (team tendencies)
- Park HR factor (LAD=127, PIT=76)
- Ground ball rate (higher = safer)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math

# Try numpy for stats, fall back to pure Python
try:
    import numpy as np
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# =============================================================================
# LEAGUE SCORING CONSTANTS (BLJ X)
# =============================================================================

POINTS_PER_IP = 5.0
POINTS_PER_K = 2.0
POINTS_PER_BB = -3.0
POINTS_PER_HR = -13.0  # THE KILLER
POINTS_PER_HIT = -1.0  # Approximate

# Typical outing distributions (based on historical data)
TYPICAL_IP = 5.5
TYPICAL_K_PER_9 = 8.5
TYPICAL_BB_PER_9 = 3.0
TYPICAL_HR_PER_9 = 1.2
TYPICAL_H_PER_9 = 8.5


# =============================================================================
# OPPONENT AND PARK DATA
# =============================================================================

# Team HR rates (HR per PA, 2024-2025 data)
TEAM_HR_RATE = {
    'LAD': 0.038, 'NYY': 0.036, 'ATL': 0.034, 'BAL': 0.033, 'PHI': 0.032,
    'HOU': 0.031, 'SEA': 0.030, 'TEX': 0.030, 'MIN': 0.029, 'CLE': 0.029,
    'SD': 0.028, 'TOR': 0.028, 'MIL': 0.028, 'KC': 0.027, 'BOS': 0.027,
    'ARI': 0.027, 'STL': 0.026, 'SF': 0.026, 'NYM': 0.026, 'CIN': 0.026,
    'DET': 0.025, 'TB': 0.025, 'LAA': 0.025, 'COL': 0.024, 'CHC': 0.024,
    'PIT': 0.023, 'WSH': 0.022, 'MIA': 0.021, 'CHW': 0.020, 'OAK': 0.019,
}

# Park HR factors (100 = neutral, higher = more HR)
PARK_HR_FACTOR = {
    'LAD': 127, 'NYY': 119, 'MIA': 118, 'PHI': 114, 'LAA': 113,
    'CIN': 112, 'TEX': 110, 'BAL': 108, 'CHC': 107, 'COL': 106,
    'BOS': 105, 'TOR': 104, 'MIL': 103, 'ATL': 102, 'MIN': 101,
    'ARI': 100, 'HOU': 99, 'NYM': 98, 'WSH': 97, 'KC': 96,
    'STL': 95, 'CHW': 94, 'CLE': 93, 'DET': 92, 'TB': 91,
    'SD': 90, 'SEA': 88, 'SF': 85, 'OAK': 82, 'PIT': 76,
}

# Team K rates (K per PA)
TEAM_K_RATE = {
    'OAK': 0.26, 'CHW': 0.25, 'DET': 0.24, 'ARI': 0.24, 'COL': 0.24,
    'MIA': 0.23, 'PIT': 0.23, 'LAA': 0.23, 'TEX': 0.23, 'TB': 0.22,
    'CIN': 0.22, 'NYM': 0.22, 'WSH': 0.22, 'SF': 0.22, 'MIN': 0.22,
    'CHC': 0.21, 'STL': 0.21, 'TOR': 0.21, 'BAL': 0.21, 'MIL': 0.21,
    'BOS': 0.21, 'ATL': 0.21, 'SEA': 0.20, 'PHI': 0.20, 'SD': 0.20,
    'HOU': 0.20, 'CLE': 0.20, 'KC': 0.19, 'NYY': 0.19, 'LAD': 0.18,
}


# =============================================================================
# RISK TIERS
# =============================================================================

class RiskTier(Enum):
    """Risk classification for streaming decisions."""
    ELITE = "elite"          # <5% disaster prob, high floor
    SAFE = "safe"            # 5-10% disaster prob, solid floor
    MODERATE = "moderate"    # 10-15% disaster prob, acceptable
    RISKY = "risky"          # 15-25% disaster prob, proceed with caution
    DANGEROUS = "dangerous"  # >25% disaster prob, avoid unless desperate
    NO_GO = "no_go"          # Hard filter - never stream


@dataclass
class PitcherProfile:
    """Pitcher's baseline stats for risk calculation."""
    name: str
    era: float = 4.00
    k_per_9: float = 8.5
    bb_per_9: float = 3.0
    hr_per_9: float = 1.2
    gb_rate: float = 0.43      # Ground ball rate (0-1)
    fb_rate: float = 0.35      # Fly ball rate (0-1)
    hard_hit_rate: float = 0.35  # Hard hit allowed rate

    @property
    def is_ground_ball_pitcher(self) -> bool:
        return self.gb_rate >= 0.47

    @property
    def is_fly_ball_pitcher(self) -> bool:
        return self.fb_rate >= 0.40

    @property
    def hr_suppressor(self) -> bool:
        """Elite HR suppression (low HR/9 + high GB)."""
        return self.hr_per_9 < 1.0 and self.gb_rate >= 0.45


@dataclass
class MatchupContext:
    """Context for a specific streaming matchup."""
    pitcher: PitcherProfile
    opponent: str
    park: str
    is_home: bool = True
    expected_ip: float = 5.5

    @property
    def opp_hr_rate(self) -> float:
        return TEAM_HR_RATE.get(self.opponent, 0.027)

    @property
    def opp_k_rate(self) -> float:
        return TEAM_K_RATE.get(self.opponent, 0.22)

    @property
    def park_hr_factor(self) -> float:
        return PARK_HR_FACTOR.get(self.park, 100) / 100.0


@dataclass
class RiskAssessment:
    """Complete risk assessment for a streaming option."""
    pitcher_name: str
    opponent: str

    # Point projections
    expected_points: float
    floor_points: float      # 10th percentile
    ceiling_points: float    # 90th percentile

    # Risk metrics
    disaster_prob: float     # P(3+ HR allowed)
    blowup_prob: float       # P(negative points)
    variance: float

    # Classification
    risk_tier: RiskTier
    risk_score: float        # 0-100, higher = riskier

    # Decision support
    risk_adjusted_value: float
    recommendation: str
    warnings: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"{self.pitcher_name} vs {self.opponent}: "
            f"EV={self.expected_points:.1f} [{self.floor_points:.1f} to {self.ceiling_points:.1f}] "
            f"Disaster={self.disaster_prob:.1%} | {self.risk_tier.value.upper()}"
        )


# =============================================================================
# RISK CALCULATOR
# =============================================================================

class RiskCalculator:
    """
    Calculates floor, ceiling, and disaster probability for streaming pitchers.

    The core insight: HR allowed follows roughly a Poisson distribution.
    We can estimate lambda (expected HR) from:
    - Pitcher's HR/9 rate
    - Expected innings
    - Opponent HR tendency
    - Park factor

    Then P(3+ HR) = 1 - P(0) - P(1) - P(2) under Poisson.
    """

    def __init__(self, risk_aversion: float = 1.0):
        """
        Args:
            risk_aversion: How much to penalize variance (0=neutral, 2=very conservative)
        """
        self.risk_aversion = risk_aversion

        # Hard filter thresholds
        self.max_disaster_prob = 0.30  # Never stream if >30% disaster prob
        self.max_blowup_prob = 0.50    # Never stream if >50% negative points prob

    def assess_matchup(self, context: MatchupContext) -> RiskAssessment:
        """
        Full risk assessment for a streaming matchup.

        Returns floor, ceiling, disaster probability, and recommendation.
        """
        pitcher = context.pitcher

        # Calculate adjusted HR rate for this matchup
        adj_hr_per_9 = self._adjusted_hr_rate(context)

        # Expected HR in this start
        expected_hr = (adj_hr_per_9 / 9.0) * context.expected_ip

        # Disaster probability using Poisson
        disaster_prob = self._poisson_tail(expected_hr, threshold=3)
        blowup_prob = self._estimate_blowup_prob(context, expected_hr)

        # Point distribution
        expected_pts, floor_pts, ceiling_pts, variance = self._point_distribution(
            context, adj_hr_per_9
        )

        # Risk classification
        risk_tier = self._classify_risk(disaster_prob, blowup_prob, context)
        risk_score = self._risk_score(disaster_prob, blowup_prob, variance)

        # Risk-adjusted value
        risk_adjusted = self._risk_adjusted_value(expected_pts, variance, disaster_prob)

        # Warnings and recommendation
        warnings = self._generate_warnings(context, disaster_prob, risk_tier)
        recommendation = self._generate_recommendation(
            risk_tier, expected_pts, risk_adjusted, disaster_prob
        )

        return RiskAssessment(
            pitcher_name=pitcher.name,
            opponent=context.opponent,
            expected_points=expected_pts,
            floor_points=floor_pts,
            ceiling_points=ceiling_pts,
            disaster_prob=disaster_prob,
            blowup_prob=blowup_prob,
            variance=variance,
            risk_tier=risk_tier,
            risk_score=risk_score,
            risk_adjusted_value=risk_adjusted,
            recommendation=recommendation,
            warnings=warnings,
        )

    def _adjusted_hr_rate(self, context: MatchupContext) -> float:
        """
        Adjust pitcher's HR/9 for opponent and park.

        Formula: HR/9_adj = HR/9_base * (opp_hr_rate / lg_avg) * park_factor
        """
        pitcher = context.pitcher
        lg_avg_hr_rate = 0.027  # League average HR/PA

        # Opponent adjustment
        opp_factor = context.opp_hr_rate / lg_avg_hr_rate

        # Park adjustment
        park_factor = context.park_hr_factor

        # Ground ball pitchers get bonus
        gb_adjustment = 1.0
        if pitcher.is_ground_ball_pitcher:
            gb_adjustment = 0.85  # 15% fewer HR for GB pitchers
        elif pitcher.is_fly_ball_pitcher:
            gb_adjustment = 1.15  # 15% more HR for FB pitchers

        adjusted = pitcher.hr_per_9 * opp_factor * park_factor * gb_adjustment

        # Bound to reasonable range
        return max(0.5, min(3.0, adjusted))

    def _poisson_tail(self, lambda_: float, threshold: int) -> float:
        """
        P(X >= threshold) where X ~ Poisson(lambda).

        For disaster probability: P(HR >= 3)
        """
        if HAS_SCIPY:
            return 1 - stats.poisson.cdf(threshold - 1, lambda_)
        else:
            # Pure Python fallback
            cdf = 0
            for k in range(threshold):
                cdf += (lambda_ ** k) * math.exp(-lambda_) / math.factorial(k)
            return 1 - cdf

    def _estimate_blowup_prob(self, context: MatchupContext, expected_hr: float) -> float:
        """
        Estimate probability of negative fantasy points.

        Rough breakeven: ~3 IP with 0 HR, or 5 IP with 1 HR.
        """
        # Simplified model: blowup if HR >= IP/2 roughly
        # More precisely: 5*IP + 2*K - 3*BB - 13*HR - H < 0

        # Expected stats
        pitcher = context.pitcher
        ip = context.expected_ip
        exp_k = (pitcher.k_per_9 / 9.0) * ip * (context.opp_k_rate / 0.22)
        exp_bb = (pitcher.bb_per_9 / 9.0) * ip
        exp_h = 8.5 / 9.0 * ip  # Rough estimate

        expected_pts = (
            POINTS_PER_IP * ip +
            POINTS_PER_K * exp_k +
            POINTS_PER_BB * exp_bb +
            POINTS_PER_HR * expected_hr +
            POINTS_PER_HIT * exp_h
        )

        # Variance is dominated by HR variance
        # Var(HR) ~ lambda for Poisson
        hr_variance = expected_hr
        pts_variance = (POINTS_PER_HR ** 2) * hr_variance + 100  # Plus other variance

        if HAS_SCIPY:
            # P(points < 0) assuming roughly normal
            std = math.sqrt(pts_variance)
            return stats.norm.cdf(0, loc=expected_pts, scale=std)
        else:
            # Rough approximation
            std = math.sqrt(pts_variance)
            z = -expected_pts / std if std > 0 else -10
            # Simple normal approximation
            return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    def _point_distribution(
        self,
        context: MatchupContext,
        adj_hr_per_9: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate expected points, floor (10th pct), ceiling (90th pct), variance.
        """
        pitcher = context.pitcher
        ip = context.expected_ip

        # Adjust K rate for opponent
        lg_avg_k_rate = 0.22
        k_factor = context.opp_k_rate / lg_avg_k_rate
        adj_k_per_9 = pitcher.k_per_9 * k_factor

        # Expected stats
        exp_k = (adj_k_per_9 / 9.0) * ip
        exp_bb = (pitcher.bb_per_9 / 9.0) * ip
        exp_hr = (adj_hr_per_9 / 9.0) * ip
        exp_h = 8.0 / 9.0 * ip  # Approximate

        # Expected points
        expected = (
            POINTS_PER_IP * ip +
            POINTS_PER_K * exp_k +
            POINTS_PER_BB * exp_bb +
            POINTS_PER_HR * exp_hr +
            POINTS_PER_HIT * exp_h
        )

        # Floor: bad outing (short, lots of HR)
        # 10th percentile: ~4 IP, +1 HR over expected, -2 K
        floor_ip = max(2.0, ip - 2.0)
        floor_hr = exp_hr + 1.5
        floor_k = max(0, exp_k - 2)
        floor = (
            POINTS_PER_IP * floor_ip +
            POINTS_PER_K * floor_k +
            POINTS_PER_BB * (exp_bb + 1) +
            POINTS_PER_HR * floor_hr +
            POINTS_PER_HIT * (exp_h + 2)
        )

        # Ceiling: great outing (deep, no HR, lots of K)
        # 90th percentile: +1 IP, 0 HR, +3 K
        ceiling_ip = min(9.0, ip + 1.5)
        ceiling_hr = max(0, exp_hr - 0.8)
        ceiling_k = exp_k + 3
        ceiling = (
            POINTS_PER_IP * ceiling_ip +
            POINTS_PER_K * ceiling_k +
            POINTS_PER_BB * max(0, exp_bb - 1) +
            POINTS_PER_HR * ceiling_hr +
            POINTS_PER_HIT * max(0, exp_h - 2)
        )

        # Variance estimate
        variance = ((ceiling - floor) / 3.3) ** 2  # Rough std from range

        return expected, floor, ceiling, variance

    def _classify_risk(
        self,
        disaster_prob: float,
        blowup_prob: float,
        context: MatchupContext
    ) -> RiskTier:
        """Classify into risk tier based on probabilities."""

        # Hard filters first
        if disaster_prob > self.max_disaster_prob:
            return RiskTier.NO_GO
        if blowup_prob > self.max_blowup_prob:
            return RiskTier.NO_GO

        # Check for dangerous matchups
        dangerous_opponents = {'LAD', 'NYY', 'ATL', 'HOU'}
        dangerous_parks = {'LAD', 'NYY', 'CIN', 'PHI'}

        if (context.opponent in dangerous_opponents and
            context.park in dangerous_parks and
            context.pitcher.fb_rate > 0.38):
            return RiskTier.DANGEROUS

        # Tier by disaster probability
        if disaster_prob < 0.05:
            return RiskTier.ELITE
        elif disaster_prob < 0.10:
            return RiskTier.SAFE
        elif disaster_prob < 0.15:
            return RiskTier.MODERATE
        elif disaster_prob < 0.25:
            return RiskTier.RISKY
        else:
            return RiskTier.DANGEROUS

    def _risk_score(
        self,
        disaster_prob: float,
        blowup_prob: float,
        variance: float
    ) -> float:
        """
        Combined risk score 0-100 (higher = riskier).
        """
        # Weight disaster probability heavily
        disaster_component = disaster_prob * 200  # 0-60 for 0-30%
        blowup_component = blowup_prob * 50       # 0-25 for 0-50%
        variance_component = min(15, variance / 100)  # 0-15

        return min(100, disaster_component + blowup_component + variance_component)

    def _risk_adjusted_value(
        self,
        expected: float,
        variance: float,
        disaster_prob: float
    ) -> float:
        """
        Risk-adjusted expected value.

        Formula: E[V] - risk_aversion * std - disaster_penalty

        The disaster penalty recognizes that a -40 point outing
        is worse than just the EV impact suggests.
        """
        std = math.sqrt(variance)

        # Disaster penalty: expected loss beyond normal variance
        disaster_penalty = disaster_prob * 30  # Extra 30 pt penalty for disasters

        adjusted = expected - self.risk_aversion * std - disaster_penalty

        return adjusted

    def _generate_warnings(
        self,
        context: MatchupContext,
        disaster_prob: float,
        risk_tier: RiskTier
    ) -> List[str]:
        """Generate warning messages for risky matchups."""
        warnings = []
        pitcher = context.pitcher

        if risk_tier == RiskTier.NO_GO:
            warnings.append("HARD FILTER: Do not stream this matchup")

        if context.opponent in {'LAD', 'NYY'}:
            warnings.append(f"Elite offense: {context.opponent}")

        if PARK_HR_FACTOR.get(context.park, 100) >= 115:
            warnings.append(f"HR-friendly park: {context.park} ({PARK_HR_FACTOR[context.park]})")

        if pitcher.is_fly_ball_pitcher:
            warnings.append(f"Fly ball pitcher (FB%={pitcher.fb_rate:.0%}) - HR prone")

        if pitcher.hr_per_9 >= 1.5:
            warnings.append(f"High HR rate: {pitcher.hr_per_9:.2f} HR/9")

        if disaster_prob >= 0.20:
            warnings.append(f"High disaster risk: {disaster_prob:.0%} chance of 3+ HR")

        return warnings

    def _generate_recommendation(
        self,
        risk_tier: RiskTier,
        expected: float,
        risk_adjusted: float,
        disaster_prob: float
    ) -> str:
        """Generate recommendation text."""

        if risk_tier == RiskTier.NO_GO:
            return "AVOID - Risk too high regardless of upside"

        if risk_tier == RiskTier.ELITE:
            return f"STRONG ADD - Safe floor with {expected:.0f} pt upside"

        if risk_tier == RiskTier.SAFE:
            return f"GOOD ADD - Solid {expected:.0f} pt expectation, low risk"

        if risk_tier == RiskTier.MODERATE:
            if risk_adjusted > 20:
                return f"ACCEPTABLE - Worth {risk_adjusted:.0f} risk-adjusted pts"
            else:
                return f"MARGINAL - Only {risk_adjusted:.0f} risk-adjusted pts"

        if risk_tier == RiskTier.RISKY:
            if expected > 35:
                return f"HIGH RISK/REWARD - {expected:.0f} pts but {disaster_prob:.0%} disaster"
            else:
                return f"RISKY - Not enough upside ({expected:.0f} pts) for {disaster_prob:.0%} disaster risk"

        if risk_tier == RiskTier.DANGEROUS:
            return f"DANGEROUS - {disaster_prob:.0%} disaster probability"

        return "EVALUATE FURTHER"


# =============================================================================
# SIMPLE BASELINE TRACKER
# =============================================================================

@dataclass
class BaselineDecision:
    """Track simple heuristic decisions for comparison."""
    pitcher_name: str
    opponent: str

    # Simple heuristics
    weak_opponent: bool      # OAK, CHW, MIA, PIT, WSH
    safe_park: bool          # Park HR factor < 95
    ground_ball_pitcher: bool
    two_start: bool

    # Simple score
    simple_score: float
    simple_recommendation: str

    # For comparison
    quant_score: Optional[float] = None
    actual_points: Optional[float] = None


class SimpleBaseline:
    """
    Simple heuristic baseline for comparison with quant methods.

    Rules:
    1. Stream vs weak opponents (OAK, CHW, MIA, PIT, WSH)
    2. Prefer safe parks (HR factor < 95)
    3. Prefer ground ball pitchers
    4. Two-start = bonus
    5. Avoid strong opponents in HR parks
    """

    WEAK_OPPONENTS = {'OAK', 'CHW', 'MIA', 'PIT', 'WSH'}
    STRONG_OPPONENTS = {'LAD', 'NYY', 'ATL', 'HOU', 'PHI'}
    SAFE_PARKS = {k for k, v in PARK_HR_FACTOR.items() if v < 95}
    DANGER_PARKS = {k for k, v in PARK_HR_FACTOR.items() if v >= 110}

    def __init__(self):
        self.decisions: List[BaselineDecision] = []

    def evaluate(
        self,
        pitcher: PitcherProfile,
        opponent: str,
        park: str,
        is_two_start: bool = False
    ) -> BaselineDecision:
        """Simple heuristic evaluation."""

        weak_opp = opponent in self.WEAK_OPPONENTS
        safe_park = park in self.SAFE_PARKS
        gb_pitcher = pitcher.is_ground_ball_pitcher

        # Simple additive score
        score = 0.0

        # Opponent quality (biggest factor)
        if weak_opp:
            score += 15
        elif opponent in self.STRONG_OPPONENTS:
            score -= 15

        # Park factor
        if safe_park:
            score += 8
        elif park in self.DANGER_PARKS:
            score -= 10

        # Pitcher type
        if gb_pitcher:
            score += 5
        if pitcher.is_fly_ball_pitcher:
            score -= 5

        # Two-start bonus
        if is_two_start:
            score += 10

        # Hard filters
        danger_combo = opponent in self.STRONG_OPPONENTS and park in self.DANGER_PARKS

        if danger_combo and pitcher.is_fly_ball_pitcher:
            recommendation = "AVOID - Bad matchup combo"
        elif score >= 15:
            recommendation = "STREAM - Good matchup"
        elif score >= 5:
            recommendation = "CONSIDER - Decent matchup"
        elif score >= -5:
            recommendation = "MARGINAL - Meh"
        else:
            recommendation = "AVOID - Poor matchup"

        decision = BaselineDecision(
            pitcher_name=pitcher.name,
            opponent=opponent,
            weak_opponent=weak_opp,
            safe_park=safe_park,
            ground_ball_pitcher=gb_pitcher,
            two_start=is_two_start,
            simple_score=score,
            simple_recommendation=recommendation,
        )

        self.decisions.append(decision)
        return decision

    def record_result(self, pitcher_name: str, actual_points: float):
        """Record actual result for comparison."""
        for d in self.decisions:
            if d.pitcher_name == pitcher_name and d.actual_points is None:
                d.actual_points = actual_points
                break

    def compare_performance(self) -> Dict:
        """Compare simple vs quant decisions."""
        completed = [d for d in self.decisions if d.actual_points is not None]

        if not completed:
            return {"message": "No completed decisions to compare"}

        simple_total = sum(d.actual_points for d in completed if d.simple_score >= 5)
        simple_count = sum(1 for d in completed if d.simple_score >= 5)

        quant_total = sum(
            d.actual_points for d in completed
            if d.quant_score is not None and d.quant_score >= 20
        )
        quant_count = sum(
            1 for d in completed
            if d.quant_score is not None and d.quant_score >= 20
        )

        return {
            "simple_avg": simple_total / simple_count if simple_count else 0,
            "simple_count": simple_count,
            "quant_avg": quant_total / quant_count if quant_count else 0,
            "quant_count": quant_count,
            "decisions": len(completed),
        }


# =============================================================================
# INTEGRATED RISK RANKER
# =============================================================================

class RiskAwareRanker:
    """
    Ranks streaming options considering both upside and risk.

    Combines:
    - Expected value
    - Risk-adjusted value
    - Disaster probability
    - Simple baseline check
    """

    def __init__(self, risk_aversion: float = 1.0):
        self.calculator = RiskCalculator(risk_aversion)
        self.baseline = SimpleBaseline()

    def rank_options(
        self,
        options: List[Tuple[PitcherProfile, str, str, bool]]  # pitcher, opp, park, two_start
    ) -> List[Tuple[RiskAssessment, BaselineDecision]]:
        """
        Rank streaming options by risk-adjusted value.

        Returns list of (RiskAssessment, BaselineDecision) tuples, sorted best-first.
        """
        results = []

        for pitcher, opponent, park, is_two_start in options:
            context = MatchupContext(
                pitcher=pitcher,
                opponent=opponent,
                park=opponent if not is_two_start else park,  # Simplified
                is_home=True,
                expected_ip=5.5 * (1.8 if is_two_start else 1.0),
            )

            risk_assessment = self.calculator.assess_matchup(context)
            baseline_decision = self.baseline.evaluate(pitcher, opponent, park, is_two_start)

            # Cross-reference scores
            baseline_decision.quant_score = risk_assessment.risk_adjusted_value

            results.append((risk_assessment, baseline_decision))

        # Sort by risk-adjusted value, filtering out NO_GO
        results.sort(
            key=lambda x: (
                x[0].risk_tier != RiskTier.NO_GO,  # NO_GO last
                x[0].risk_adjusted_value
            ),
            reverse=True
        )

        return results

    def quick_filter(
        self,
        options: List[Tuple[PitcherProfile, str, str, bool]]
    ) -> Tuple[List, List]:
        """
        Quick pass/fail filter.

        Returns (streamable, avoid) lists.
        """
        streamable = []
        avoid = []

        for opt in options:
            pitcher, opponent, park, is_two_start = opt
            context = MatchupContext(
                pitcher=pitcher,
                opponent=opponent,
                park=park,
                expected_ip=5.5,
            )

            assessment = self.calculator.assess_matchup(context)

            if assessment.risk_tier == RiskTier.NO_GO:
                avoid.append((opt, assessment))
            elif assessment.risk_tier == RiskTier.DANGEROUS:
                avoid.append((opt, assessment))
            else:
                streamable.append((opt, assessment))

        return streamable, avoid


# =============================================================================
# CLI DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("RISK ANALYSIS MODULE DEMO")
    print("=" * 70)

    # Create test pitchers
    pitchers = [
        PitcherProfile(
            name="Logan Webb",
            era=3.20, k_per_9=7.5, bb_per_9=2.2, hr_per_9=0.8,
            gb_rate=0.52, fb_rate=0.28
        ),
        PitcherProfile(
            name="Garrett Crochet",
            era=3.50, k_per_9=11.5, bb_per_9=2.8, hr_per_9=1.0,
            gb_rate=0.38, fb_rate=0.42
        ),
        PitcherProfile(
            name="Streamer McGee",
            era=4.50, k_per_9=8.0, bb_per_9=3.5, hr_per_9=1.4,
            gb_rate=0.40, fb_rate=0.38
        ),
    ]

    # Test matchups
    matchups = [
        # (pitcher, opponent, park, is_two_start)
        (pitchers[0], "OAK", "OAK", False),    # Webb vs weak team, safe park
        (pitchers[0], "LAD", "LAD", False),    # Webb vs strong team, HR park
        (pitchers[1], "OAK", "OAK", True),     # Crochet vs weak, 2-start
        (pitchers[1], "NYY", "NYY", False),    # Crochet vs strong, danger park
        (pitchers[2], "MIA", "MIA", False),    # Streamer vs weak
        (pitchers[2], "LAD", "LAD", False),    # Streamer vs strong, danger
    ]

    # Risk calculator
    calc = RiskCalculator(risk_aversion=1.0)

    print("\n" + "=" * 70)
    print("INDIVIDUAL MATCHUP ASSESSMENTS")
    print("=" * 70)

    for pitcher, opp, park, two_start in matchups:
        context = MatchupContext(
            pitcher=pitcher,
            opponent=opp,
            park=park,
            expected_ip=5.5 * (1.8 if two_start else 1.0)
        )

        assessment = calc.assess_matchup(context)

        ts = " [2-START]" if two_start else ""
        print(f"\n{pitcher.name} vs {opp} @ {park}{ts}")
        print("-" * 50)
        print(f"  Expected: {assessment.expected_points:.1f} pts")
        print(f"  Floor:    {assessment.floor_points:.1f} pts (10th pct)")
        print(f"  Ceiling:  {assessment.ceiling_points:.1f} pts (90th pct)")
        print(f"  Disaster: {assessment.disaster_prob:.1%} (3+ HR)")
        print(f"  Blowup:   {assessment.blowup_prob:.1%} (negative pts)")
        print(f"  Risk-Adj: {assessment.risk_adjusted_value:.1f} pts")
        print(f"  Tier:     {assessment.risk_tier.value.upper()}")
        print(f"  --> {assessment.recommendation}")
        if assessment.warnings:
            print(f"  Warnings: {'; '.join(assessment.warnings)}")

    # Ranking comparison
    print("\n" + "=" * 70)
    print("RANKED OPTIONS (Risk-Adjusted)")
    print("=" * 70)

    ranker = RiskAwareRanker(risk_aversion=1.0)
    ranked = ranker.rank_options(matchups)

    for i, (risk_assess, baseline) in enumerate(ranked, 1):
        marker = "X" if risk_assess.risk_tier == RiskTier.NO_GO else " "
        print(f"\n{i}. [{marker}] {risk_assess.pitcher_name} vs {risk_assess.opponent}")
        print(f"   Quant: {risk_assess.risk_adjusted_value:.1f} | Simple: {baseline.simple_score:.0f}")
        print(f"   {risk_assess.risk_tier.value}: {risk_assess.recommendation}")
        print(f"   Simple: {baseline.simple_recommendation}")

    # Quick filter
    print("\n" + "=" * 70)
    print("QUICK FILTER")
    print("=" * 70)

    streamable, avoid = ranker.quick_filter(matchups)

    print(f"\nSTREAMABLE ({len(streamable)}):")
    for (pitcher, opp, park, ts), assess in streamable:
        print(f"  - {pitcher.name} vs {opp}: {assess.risk_tier.value}")

    print(f"\nAVOID ({len(avoid)}):")
    for (pitcher, opp, park, ts), assess in avoid:
        print(f"  - {pitcher.name} vs {opp}: {assess.risk_tier.value}")
        for w in assess.warnings[:2]:
            print(f"    ! {w}")
