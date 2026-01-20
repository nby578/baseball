"""
Matchup Analyzer for H2H Fantasy Baseball
==========================================
Game-theoretic opponent modeling and situational strategy optimization.

Key concepts implemented:
- Glicko-2 skill rating for opponent strength estimation
- Level-K thinking for opponent sophistication modeling
- ICM-style variance adjustment (poker tournament theory)
- Secretary Problem thresholds for optimal streaming timing
- Temporal activity patterns for opponent behavior prediction
- Next-week lookahead for add allocation decisions

References:
- Ferguson (1989) "Who Solved the Secretary Problem?" - Statistical Science
- Glickman (2012) "Example of the Glicko-2 system" - glicko.net
- Camerer, Ho & Chong (2004) "A Cognitive Hierarchy Model" - QJE
- ICM theory from poker tournament mathematics
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import math


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class MatchupState(Enum):
    """Current state of weekly matchup - determines strategy profile."""
    BLOWOUT_LEAD = "blowout_lead"    # Way ahead, protect and prepare next week
    COMFORTABLE = "comfortable"       # Ahead, minimize variance
    CLOSE = "close"                   # Normal optimization
    TRAILING = "trailing"             # Behind but catchable, favor upside
    DESPERATE = "desperate"           # Way behind, swing for fences


class OpponentType(Enum):
    """Poker-style opponent classification (2x2 matrix)."""
    TIGHT_PASSIVE = "tight_passive"   # Set-and-forget, minimal moves
    TIGHT_ACTIVE = "tight_active"     # Few but high-quality moves
    LOOSE_PASSIVE = "loose_passive"   # Random changes, no strategy
    LOOSE_ACTIVE = "loose_active"     # Heavy streamer, constantly churning


class SophisticationLevel(Enum):
    """Level-K thinking - opponent strategic depth."""
    L0 = 0  # Random/naive - sets lineup, never checks
    L1 = 1  # Basic optimization - reacts to obvious news
    L2 = 2  # Anticipates your moves, tries to block
    L3 = 3  # Strategic counter-moves, game theory aware


class ActionType(Enum):
    """Recommended action types."""
    STREAM_PITCHER = "stream_pitcher"
    STREAM_BATTER = "stream_batter"
    UPGRADE_BATTING = "upgrade_batting"
    PREPARE_NEXT_WEEK = "prepare_next_week"
    HOLD = "hold"                     # Don't use add
    DEFENSIVE_ADD = "defensive_add"   # Block opponent from pickup


class TimeZone(Enum):
    """Opponent time zone for activity prediction."""
    EAST = "ET"      # 3 AM cutoff for next-day moves
    CENTRAL = "CT"   # 2 AM cutoff
    MOUNTAIN = "MT"  # 1 AM cutoff
    WEST = "PT"      # 12 AM cutoff (user's zone)


# Scoring constants for BLJ X league
HR_ALLOWED_PENALTY = -13
DISASTER_HR_THRESHOLD = 3  # 3+ HR = disaster


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Glicko2Rating:
    """
    Glicko-2 rating with uncertainty tracking.

    mu: Rating (default 1500)
    phi: Rating deviation - uncertainty (default 350)
    sigma: Volatility - expected fluctuation (default 0.06)
    """
    mu: float = 1500.0
    phi: float = 350.0
    sigma: float = 0.06

    @property
    def confidence_interval(self) -> Tuple[float, float]:
        """95% confidence interval for true skill."""
        return (self.mu - 2 * self.phi, self.mu + 2 * self.phi)

    @property
    def display_rating(self) -> int:
        """Conservative display rating (mu - 2*phi)."""
        return int(self.mu - 2 * self.phi)


@dataclass
class ActivityPattern:
    """Temporal patterns of opponent activity."""
    typical_hour_utc: Optional[int] = None  # Most common hour for moves
    days_active: List[int] = field(default_factory=list)  # 0=Mon, 6=Sun
    avg_adds_per_week: float = 0.0
    late_week_bias: float = 0.5  # 0=front-loaded, 1=back-loaded
    response_time_hours: float = 24.0  # How fast they react to news
    timezone: TimeZone = TimeZone.EAST


@dataclass
class OpponentProfile:
    """Complete opponent model for prediction."""
    team_id: str
    team_name: str
    manager_name: str

    # Skill rating
    rating: Glicko2Rating = field(default_factory=Glicko2Rating)

    # Classification
    opponent_type: OpponentType = OpponentType.TIGHT_PASSIVE
    sophistication: SophisticationLevel = SophisticationLevel.L1

    # Historical performance
    wins: int = 0
    losses: int = 0
    points_for: float = 0.0
    points_against: float = 0.0
    current_standing: int = 6  # 1-12

    # Behavioral patterns
    activity: ActivityPattern = field(default_factory=ActivityPattern)

    # Resource state
    adds_used_this_week: int = 0
    adds_remaining_this_week: int = 7
    adds_used_season: int = 0

    # Roster state
    empty_roster_slots: int = 0
    droppable_players: int = 0  # Players clearly worse than FA
    il_slots_used: int = 0

    @property
    def win_rate(self) -> float:
        """Historical win percentage."""
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.5

    @property
    def avg_points(self) -> float:
        """Average weekly points scored."""
        total = self.wins + self.losses
        return self.points_for / total if total > 0 else 0.0

    @property
    def is_active_manager(self) -> bool:
        """Does this manager actively manage their team?"""
        return self.activity.avg_adds_per_week >= 2.0

    @property
    def likely_to_stream(self) -> bool:
        """Will they likely use streaming this week?"""
        return (self.opponent_type in [OpponentType.LOOSE_ACTIVE, OpponentType.TIGHT_ACTIVE]
                and self.adds_remaining_this_week >= 2)


@dataclass
class MatchupContext:
    """Current state of a weekly matchup."""
    week_number: int
    day_of_week: int  # 0=Monday, 6=Sunday

    # Scores
    my_score: float
    opponent_score: float

    # Projections for remainder of week
    my_projected_remaining: float
    opponent_projected_remaining: float
    my_projection_stdev: float
    opponent_projection_stdev: float

    # Resources
    my_adds_remaining: int
    opponent_adds_remaining: int

    # Streaming options quality (0-100 scale)
    best_streamer_score: float = 50.0
    avg_streamer_score: float = 30.0

    # Batting upgrade available?
    batting_upgrade_available: bool = False
    batting_upgrade_value: float = 0.0

    @property
    def score_differential(self) -> float:
        """Current score gap (positive = winning)."""
        return self.my_score - self.opponent_score

    @property
    def projected_final_differential(self) -> float:
        """Projected final score gap."""
        return (self.score_differential +
                self.my_projected_remaining -
                self.opponent_projected_remaining)

    @property
    def days_remaining(self) -> int:
        """Days left in matchup week (Sunday = 0)."""
        return 6 - self.day_of_week

    @property
    def is_late_week(self) -> bool:
        """Friday-Sunday = late week."""
        return self.day_of_week >= 4


@dataclass
class WeekPreview:
    """Preview of next week's matchup for lookahead decisions."""
    opponent: OpponentProfile
    opponent_projected_strength: float  # 0-100 scale
    two_start_pitchers_available: int
    quality_streamers_early_week: int

    @property
    def is_tough_matchup(self) -> bool:
        """Is next week's opponent strong?"""
        return self.opponent_projected_strength >= 65 or self.opponent.current_standing <= 3

    @property
    def setup_value(self) -> float:
        """Value of using an add now for next week setup."""
        base_value = self.two_start_pitchers_available * 15
        if self.is_tough_matchup:
            base_value *= 1.5
        return base_value


@dataclass
class ActionRecommendation:
    """Specific recommended action with reasoning."""
    action_type: ActionType
    target_player: Optional[str] = None
    drop_player: Optional[str] = None

    expected_value: float = 0.0
    risk_level: str = "moderate"
    confidence: float = 0.5

    reasoning: str = ""
    alternative_actions: List[str] = field(default_factory=list)


# =============================================================================
# GLICKO-2 RATING SYSTEM
# =============================================================================

class Glicko2Calculator:
    """
    Glicko-2 rating system implementation.
    Better than Elo for fantasy because it tracks confidence.

    Reference: Glickman (2012) "Example of the Glicko-2 system"
    """

    TAU = 0.5  # System constant constraining volatility change
    EPSILON = 0.000001  # Convergence tolerance

    @staticmethod
    def expected_score(my_rating: Glicko2Rating, opp_rating: Glicko2Rating) -> float:
        """
        Calculate expected win probability against opponent.

        Returns probability from 0 to 1.
        """
        # Convert to Glicko-2 scale
        mu = (my_rating.mu - 1500) / 173.7178
        mu_j = (opp_rating.mu - 1500) / 173.7178
        phi_j = opp_rating.phi / 173.7178

        # g function - reduces impact of uncertain opponents
        g_phi_j = 1 / math.sqrt(1 + 3 * phi_j**2 / math.pi**2)

        # Expected score (logistic function)
        exponent = -g_phi_j * (mu - mu_j)
        return 1 / (1 + math.exp(exponent))

    @classmethod
    def update_rating(cls, rating: Glicko2Rating,
                      opponents: List[Glicko2Rating],
                      scores: List[float]) -> Glicko2Rating:
        """
        Update rating after a set of games.

        scores: List of outcomes (1=win, 0.5=draw, 0=loss)
        """
        if not opponents:
            # No games - increase uncertainty
            new_phi = math.sqrt(rating.phi**2 + rating.sigma**2)
            return Glicko2Rating(rating.mu, min(new_phi, 350), rating.sigma)

        # Convert to Glicko-2 scale
        mu = (rating.mu - 1500) / 173.7178
        phi = rating.phi / 173.7178

        # Calculate v (estimated variance) and delta
        v_sum = 0
        delta_sum = 0

        for opp, score in zip(opponents, scores):
            mu_j = (opp.mu - 1500) / 173.7178
            phi_j = opp.phi / 173.7178

            g_j = 1 / math.sqrt(1 + 3 * phi_j**2 / math.pi**2)
            E_j = 1 / (1 + math.exp(-g_j * (mu - mu_j)))

            v_sum += g_j**2 * E_j * (1 - E_j)
            delta_sum += g_j * (score - E_j)

        v = 1 / v_sum
        delta = v * delta_sum

        # Update volatility (simplified - full algorithm is iterative)
        a = math.log(rating.sigma**2)
        new_sigma = math.exp(a / 2)  # Simplified

        # Update phi
        phi_star = math.sqrt(phi**2 + new_sigma**2)
        new_phi = 1 / math.sqrt(1/phi_star**2 + 1/v)

        # Update mu
        new_mu = mu + new_phi**2 * delta_sum

        # Convert back to Glicko scale
        return Glicko2Rating(
            mu=new_mu * 173.7178 + 1500,
            phi=new_phi * 173.7178,
            sigma=new_sigma
        )


# =============================================================================
# SECRETARY PROBLEM - STREAMING THRESHOLDS
# =============================================================================

class SecretaryProblem:
    """
    Multi-selection secretary problem for optimal streaming timing.

    The insight: Don't use your best streamer on Monday if better
    options might emerge Thursday-Sunday.

    Reference: Ferguson (1989), Grau Ribas (2022)
    """

    @staticmethod
    def optimal_threshold(slots_remaining: int,
                          opportunities_remaining: int,
                          opportunities_total: int) -> float:
        """
        Calculate the percentile threshold for accepting a streamer.

        Early in week: Only accept top-tier options
        Late in week: Accept anything above average

        Returns: Percentile threshold (0-1). Accept streamers above this.

        Formula: threshold = 1 - k/(n-t+k)
        where k = slots remaining, t = opportunities used, n = total opportunities
        """
        if opportunities_remaining <= 0:
            return 0.0  # Accept anything

        if slots_remaining <= 0:
            return 1.0  # Can't accept anything

        k = slots_remaining
        n = opportunities_total
        t = n - opportunities_remaining

        # Avoid division by zero
        denominator = n - t + k
        if denominator <= 0:
            return 0.0

        threshold = 1 - k / denominator
        return max(0.0, min(1.0, threshold))

    @staticmethod
    def should_stream(streamer_percentile: float,
                      slots_remaining: int,
                      day_of_week: int,
                      streamers_per_day: float = 3.0) -> Tuple[bool, str]:
        """
        Decide whether to stream a pitcher based on secretary problem.

        streamer_percentile: How good is this streamer (0-1, 1=best)
        slots_remaining: Add slots left
        day_of_week: 0=Monday, 6=Sunday
        streamers_per_day: Expected streaming options per day

        Returns: (should_stream, reasoning)
        """
        days_remaining = 6 - day_of_week
        opportunities_remaining = int(days_remaining * streamers_per_day)
        opportunities_total = int(7 * streamers_per_day)

        threshold = SecretaryProblem.optimal_threshold(
            slots_remaining, opportunities_remaining, opportunities_total
        )

        should = streamer_percentile >= threshold

        if should:
            reasoning = (f"Stream: {streamer_percentile:.0%} > threshold {threshold:.0%}. "
                        f"With {slots_remaining} slots and {days_remaining} days left, "
                        f"this meets the quality bar.")
        else:
            reasoning = (f"Wait: {streamer_percentile:.0%} < threshold {threshold:.0%}. "
                        f"Better options likely in remaining {days_remaining} days. "
                        f"Save the add for a higher-quality stream.")

        return should, reasoning


# =============================================================================
# WIN PROBABILITY CALCULATOR
# =============================================================================

class WinProbabilityCalculator:
    """
    Calculate win probability for weekly matchup.

    Uses normal approximation for point differentials.
    """

    @staticmethod
    def calculate(context: MatchupContext) -> float:
        """
        Calculate probability of winning the current matchup.

        Uses projected final scores with uncertainty.
        """
        # Projected final differential
        mean_diff = context.projected_final_differential

        # Combined standard deviation
        combined_stdev = math.sqrt(
            context.my_projection_stdev**2 +
            context.opponent_projection_stdev**2
        )

        if combined_stdev == 0:
            return 1.0 if mean_diff > 0 else (0.5 if mean_diff == 0 else 0.0)

        # Z-score for win probability
        z = mean_diff / combined_stdev

        # Normal CDF approximation
        return WinProbabilityCalculator._normal_cdf(z)

    @staticmethod
    def _normal_cdf(z: float) -> float:
        """Approximate standard normal CDF."""
        # Abramowitz and Stegun approximation
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1 if z >= 0 else -1
        z = abs(z) / math.sqrt(2)

        t = 1.0 / (1.0 + p * z)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z * z)

        return 0.5 * (1.0 + sign * y)

    @staticmethod
    def pythagorean_expectation(points_for: float,
                                  points_against: float,
                                  exponent: float = 3.5) -> float:
        """
        Baseball-style pythagorean win expectation.

        Useful for estimating opponent strength from historical data.
        """
        if points_for + points_against == 0:
            return 0.5

        return points_for**exponent / (points_for**exponent + points_against**exponent)


# =============================================================================
# MATCHUP STATE DETERMINATION
# =============================================================================

class MatchupStateAnalyzer:
    """
    Determine current matchup state for strategy selection.

    Thresholds calibrated for typical H2H fantasy baseball variance.
    """

    # Thresholds in standard deviations
    BLOWOUT_THRESHOLD = 2.0      # >2 stdev ahead
    COMFORTABLE_THRESHOLD = 1.0  # 1-2 stdev ahead
    CLOSE_THRESHOLD = 0.5        # Within 0.5 stdev
    TRAILING_THRESHOLD = 1.0     # 0.5-1 stdev behind
    # Below trailing = desperate

    @classmethod
    def determine_state(cls, context: MatchupContext) -> MatchupState:
        """Determine matchup state from current context."""

        # Calculate z-score of current differential
        combined_stdev = math.sqrt(
            context.my_projection_stdev**2 +
            context.opponent_projection_stdev**2
        )

        if combined_stdev == 0:
            combined_stdev = 50  # Default if no projection data

        z_score = context.projected_final_differential / combined_stdev

        # Late week adjustments - less time to recover
        if context.is_late_week:
            z_score *= 1.5  # Amplify the state

        # Determine state
        if z_score >= cls.BLOWOUT_THRESHOLD:
            return MatchupState.BLOWOUT_LEAD
        elif z_score >= cls.COMFORTABLE_THRESHOLD:
            return MatchupState.COMFORTABLE
        elif z_score >= -cls.CLOSE_THRESHOLD:
            return MatchupState.CLOSE
        elif z_score >= -cls.TRAILING_THRESHOLD:
            return MatchupState.TRAILING
        else:
            return MatchupState.DESPERATE

    @classmethod
    def get_variance_preference(cls, state: MatchupState) -> float:
        """
        ICM-style variance preference.

        Returns multiplier for variance:
        - >1.0 = seek variance (take risks)
        - 1.0 = neutral
        - <1.0 = avoid variance (play safe)
        """
        preferences = {
            MatchupState.BLOWOUT_LEAD: 0.3,   # Strongly avoid variance
            MatchupState.COMFORTABLE: 0.6,    # Prefer safety
            MatchupState.CLOSE: 1.0,          # Neutral
            MatchupState.TRAILING: 1.3,       # Seek some variance
            MatchupState.DESPERATE: 2.0,      # Maximum variance
        }
        return preferences.get(state, 1.0)


# =============================================================================
# OPPONENT BEHAVIOR PREDICTOR
# =============================================================================

class OpponentPredictor:
    """
    Predict opponent actions based on profile and context.
    """

    @staticmethod
    def will_make_move_today(opponent: OpponentProfile,
                             current_hour_utc: int,
                             matchup_state_for_them: MatchupState) -> float:
        """
        Probability opponent makes a roster move today.

        Returns probability 0-1.
        """
        base_prob = opponent.activity.avg_adds_per_week / 7.0

        # Adjust for time of day
        if opponent.activity.typical_hour_utc is not None:
            hours_until_typical = (opponent.activity.typical_hour_utc - current_hour_utc) % 24
            if hours_until_typical > 12:
                base_prob *= 0.5  # Unlikely before their typical time

        # Adjust for their matchup state
        state_multipliers = {
            MatchupState.DESPERATE: 1.5,     # Likely to make moves when desperate
            MatchupState.TRAILING: 1.2,
            MatchupState.CLOSE: 1.0,
            MatchupState.COMFORTABLE: 0.7,   # Less likely when ahead
            MatchupState.BLOWOUT_LEAD: 0.5,
        }
        base_prob *= state_multipliers.get(matchup_state_for_them, 1.0)

        # Adjust for manager type
        if opponent.opponent_type == OpponentType.TIGHT_PASSIVE:
            base_prob *= 0.3
        elif opponent.opponent_type == OpponentType.LOOSE_ACTIVE:
            base_prob *= 1.5

        # Adjust for resources
        if opponent.adds_remaining_this_week == 0:
            base_prob = 0.0

        return min(1.0, base_prob)

    @staticmethod
    def predict_streaming_targets(opponent: OpponentProfile,
                                  available_streamers: List[str],
                                  context: MatchupContext) -> List[str]:
        """
        Predict which streamers opponent might target.

        Useful for defensive adds (blocking) or avoiding bidding wars.
        """
        if not opponent.likely_to_stream:
            return []

        # L0 opponents: Won't target anyone strategically
        if opponent.sophistication == SophisticationLevel.L0:
            return []

        # L1 opponents: Will target obvious top options
        if opponent.sophistication == SophisticationLevel.L1:
            return available_streamers[:2]  # Top 2 by ranking

        # L2+ opponents: May try to block your targets
        # For now, return top options
        return available_streamers[:3]

    @staticmethod
    def is_opponent_awake(opponent: OpponentProfile,
                          current_hour_local: int) -> bool:
        """
        Estimate if opponent is likely awake and able to make moves.

        Key insight: East Coast managers unlikely to make moves at 3 AM local.
        """
        # Assume awake hours are 7 AM - 1 AM local
        return 7 <= current_hour_local <= 25  # 25 = 1 AM next day

    @staticmethod
    def late_night_advantage(my_timezone: TimeZone,
                             opponent_timezone: TimeZone) -> float:
        """
        Calculate late-night transaction advantage.

        West Coast has 3-hour advantage over East Coast for
        midnight PT deadline moves.

        Returns hours of advantage (can be negative).
        """
        tz_offsets = {
            TimeZone.EAST: -3,      # 3 AM local when deadline hits
            TimeZone.CENTRAL: -2,   # 2 AM local
            TimeZone.MOUNTAIN: -1,  # 1 AM local
            TimeZone.WEST: 0,       # Midnight local (baseline)
        }

        my_offset = tz_offsets.get(my_timezone, 0)
        opp_offset = tz_offsets.get(opponent_timezone, 0)

        # Positive = I have advantage (ET opponent = +3 hours for PT user)
        return my_offset - opp_offset


# =============================================================================
# ACTION RECOMMENDER
# =============================================================================

class ActionRecommender:
    """
    Generate specific action recommendations based on matchup analysis.
    """

    def __init__(self, secretary: SecretaryProblem = None):
        self.secretary = secretary or SecretaryProblem()

    def recommend(self,
                  context: MatchupContext,
                  opponent: OpponentProfile,
                  next_week: Optional[WeekPreview],
                  streamer_options: List[Dict]) -> ActionRecommendation:
        """
        Generate recommended action for current situation.

        Considers:
        - Current matchup state
        - Opponent behavior prediction
        - Next week's opponent
        - Quality of available options
        """
        state = MatchupStateAnalyzer.determine_state(context)
        win_prob = WinProbabilityCalculator.calculate(context)

        # Special case: Matchup effectively decided
        if state == MatchupState.BLOWOUT_LEAD:
            return self._recommend_when_winning_big(
                context, next_week, streamer_options
            )

        if state == MatchupState.DESPERATE and context.is_late_week:
            return self._recommend_when_desperate(
                context, opponent, streamer_options
            )

        # Normal optimization with secretary problem thresholds
        return self._recommend_standard(
            context, state, streamer_options
        )

    def _recommend_when_winning_big(self,
                                     context: MatchupContext,
                                     next_week: Optional[WeekPreview],
                                     streamers: List[Dict]) -> ActionRecommendation:
        """When way ahead - consider next week or skip add."""

        # Option 1: Prepare for next week
        if next_week and next_week.is_tough_matchup:
            if next_week.two_start_pitchers_available > 0:
                return ActionRecommendation(
                    action_type=ActionType.PREPARE_NEXT_WEEK,
                    reasoning=(f"Matchup decided. Next week vs {next_week.opponent.team_name} "
                              f"(#{next_week.opponent.current_standing}) is tough. "
                              f"Add a 2-start pitcher for Monday/Tuesday head start."),
                    expected_value=next_week.setup_value,
                    risk_level="low",
                    confidence=0.8
                )

        # Option 2: Batting upgrade if available
        if context.batting_upgrade_available:
            return ActionRecommendation(
                action_type=ActionType.UPGRADE_BATTING,
                reasoning=("Matchup decided, streamers add unnecessary risk. "
                          "Use add to improve batting lineup for long-term value."),
                expected_value=context.batting_upgrade_value,
                risk_level="low",
                confidence=0.7
            )

        # Option 3: Don't use the add
        best_streamer = streamers[0] if streamers else {}
        if best_streamer.get('disaster_prob', 0) > 0.15:
            return ActionRecommendation(
                action_type=ActionType.HOLD,
                reasoning=("Way ahead, available streamers are risky. "
                          "Don't add for the sake of adding - "
                          "a blowup could make this close."),
                expected_value=0,
                risk_level="none",
                confidence=0.85,
                alternative_actions=["Stream if elite option emerges"]
            )

        # Default: Still stream if option is elite/safe
        return ActionRecommendation(
            action_type=ActionType.STREAM_PITCHER,
            target_player=best_streamer.get('name'),
            reasoning="Way ahead but safe streaming option available.",
            expected_value=best_streamer.get('expected_points', 0),
            risk_level="low",
            confidence=0.6
        )

    def _recommend_when_desperate(self,
                                   context: MatchupContext,
                                   opponent: OpponentProfile,
                                   streamers: List[Dict]) -> ActionRecommendation:
        """When way behind late in week - maximize variance."""

        if not streamers:
            return ActionRecommendation(
                action_type=ActionType.HOLD,
                reasoning="No streaming options available.",
                confidence=1.0
            )

        # Find highest-ceiling streamer, ignore floor
        best_ceiling = max(streamers, key=lambda s: s.get('ceiling', 0))

        return ActionRecommendation(
            action_type=ActionType.STREAM_PITCHER,
            target_player=best_ceiling.get('name'),
            reasoning=(f"Desperate mode: {context.score_differential:.0f} pts behind "
                      f"on day {context.day_of_week+1}. "
                      f"Ignoring floor, maximizing ceiling. "
                      f"{best_ceiling.get('name')} has {best_ceiling.get('ceiling', 0):.0f}pt ceiling."),
            expected_value=best_ceiling.get('ceiling', 0),
            risk_level="high",
            confidence=0.7,
            alternative_actions=[
                "Consider stacking batters from same lineup for correlated upside"
            ]
        )

    def _recommend_standard(self,
                            context: MatchupContext,
                            state: MatchupState,
                            streamers: List[Dict]) -> ActionRecommendation:
        """Standard recommendation with secretary problem thresholds."""

        if not streamers:
            return ActionRecommendation(
                action_type=ActionType.HOLD,
                reasoning="No streaming options meet minimum quality threshold.",
                confidence=1.0
            )

        best_streamer = streamers[0]
        percentile = best_streamer.get('percentile', 0.5)

        should_stream, reasoning = SecretaryProblem.should_stream(
            percentile,
            context.my_adds_remaining,
            context.day_of_week
        )

        if not should_stream:
            return ActionRecommendation(
                action_type=ActionType.HOLD,
                reasoning=reasoning,
                expected_value=0,
                confidence=0.7,
                alternative_actions=[f"Wait for better option than {best_streamer.get('name')}"]
            )

        # Adjust expected value for matchup state (ICM)
        variance_pref = MatchupStateAnalyzer.get_variance_preference(state)

        # Risk-adjusted value
        ev = best_streamer.get('expected_points', 0)
        stdev = best_streamer.get('stdev', 20)
        adjusted_ev = ev + (variance_pref - 1) * stdev * 0.5

        risk_level = "low" if state == MatchupState.COMFORTABLE else (
            "high" if state in [MatchupState.TRAILING, MatchupState.DESPERATE] else "moderate"
        )

        return ActionRecommendation(
            action_type=ActionType.STREAM_PITCHER,
            target_player=best_streamer.get('name'),
            reasoning=reasoning,
            expected_value=adjusted_ev,
            risk_level=risk_level,
            confidence=0.75
        )


# =============================================================================
# MAIN ANALYZER CLASS
# =============================================================================

class MatchupAnalyzer:
    """
    Main interface for matchup analysis and opponent modeling.

    Combines all components:
    - Glicko-2 skill ratings
    - Secretary problem thresholds
    - ICM variance adjustment
    - Opponent behavior prediction
    - Action recommendations
    """

    def __init__(self):
        self.glicko = Glicko2Calculator()
        self.secretary = SecretaryProblem()
        self.recommender = ActionRecommender(self.secretary)

        # Cache opponent profiles
        self.opponents: Dict[str, OpponentProfile] = {}

    def analyze_matchup(self,
                        context: MatchupContext,
                        opponent_id: str,
                        next_week: Optional[WeekPreview] = None,
                        streamer_options: List[Dict] = None) -> Dict:
        """
        Full matchup analysis with recommendations.

        Returns comprehensive analysis dict.
        """
        opponent = self.opponents.get(opponent_id, OpponentProfile(
            team_id=opponent_id, team_name="Unknown", manager_name="Unknown"
        ))

        state = MatchupStateAnalyzer.determine_state(context)
        win_prob = WinProbabilityCalculator.calculate(context)
        variance_pref = MatchupStateAnalyzer.get_variance_preference(state)

        recommendation = self.recommender.recommend(
            context, opponent, next_week, streamer_options or []
        )

        return {
            'matchup_state': state.value,
            'win_probability': win_prob,
            'variance_preference': variance_pref,
            'score_differential': context.score_differential,
            'projected_final_diff': context.projected_final_differential,
            'days_remaining': context.days_remaining,
            'opponent': {
                'name': opponent.team_name,
                'manager': opponent.manager_name,
                'rating': opponent.rating.mu,
                'rating_confidence': opponent.rating.phi,
                'win_rate': opponent.win_rate,
                'type': opponent.opponent_type.value,
                'sophistication': opponent.sophistication.value,
                'likely_to_stream': opponent.likely_to_stream,
                'adds_remaining': opponent.adds_remaining_this_week,
            },
            'recommendation': {
                'action': recommendation.action_type.value,
                'target': recommendation.target_player,
                'drop': recommendation.drop_player,
                'expected_value': recommendation.expected_value,
                'risk_level': recommendation.risk_level,
                'confidence': recommendation.confidence,
                'reasoning': recommendation.reasoning,
                'alternatives': recommendation.alternative_actions,
            },
            'next_week': {
                'opponent': next_week.opponent.team_name if next_week else None,
                'is_tough': next_week.is_tough_matchup if next_week else None,
                'setup_value': next_week.setup_value if next_week else 0,
            } if next_week else None
        }

    def update_opponent_rating(self,
                                opponent_id: str,
                                result: float,
                                opponent_strength: float = 1500):
        """
        Update opponent's Glicko-2 rating after a matchup.

        result: 1=they won, 0=they lost
        """
        if opponent_id not in self.opponents:
            self.opponents[opponent_id] = OpponentProfile(
                team_id=opponent_id, team_name="Unknown", manager_name="Unknown"
            )

        opponent = self.opponents[opponent_id]
        their_opp = Glicko2Rating(mu=opponent_strength)

        new_rating = self.glicko.update_rating(
            opponent.rating, [their_opp], [result]
        )
        opponent.rating = new_rating

        # Update W/L record
        if result == 1:
            opponent.wins += 1
        else:
            opponent.losses += 1

    def register_opponent(self, profile: OpponentProfile):
        """Register or update an opponent profile."""
        self.opponents[profile.team_id] = profile

    def get_streaming_threshold(self,
                                 slots_remaining: int,
                                 day_of_week: int) -> float:
        """Get minimum percentile threshold for streaming today."""
        return SecretaryProblem.optimal_threshold(
            slots_remaining,
            (6 - day_of_week) * 3,  # ~3 options per day
            21  # ~21 options per week
        )


# =============================================================================
# DEMO / TESTING
# =============================================================================

def demo():
    """Demonstrate matchup analyzer capabilities."""

    print("=" * 70)
    print("MATCHUP ANALYZER DEMO")
    print("=" * 70)

    analyzer = MatchupAnalyzer()

    # Register an opponent
    opponent = OpponentProfile(
        team_id="team_3",
        team_name="The Streamers",
        manager_name="Mike",
        rating=Glicko2Rating(mu=1580, phi=150),
        opponent_type=OpponentType.LOOSE_ACTIVE,
        sophistication=SophisticationLevel.L2,
        wins=8,
        losses=4,
        points_for=1200,
        points_against=1050,
        current_standing=2,
        activity=ActivityPattern(
            typical_hour_utc=3,  # 10 PM ET
            avg_adds_per_week=5.5,
            late_week_bias=0.7,
            timezone=TimeZone.EAST
        ),
        adds_remaining_this_week=4,
    )
    analyzer.register_opponent(opponent)

    # Scenario 1: Close matchup, mid-week
    print("\n--- SCENARIO 1: Close Matchup (Wednesday) ---")
    context1 = MatchupContext(
        week_number=10,
        day_of_week=2,  # Wednesday
        my_score=180,
        opponent_score=175,
        my_projected_remaining=120,
        opponent_projected_remaining=125,
        my_projection_stdev=35,
        opponent_projection_stdev=40,
        my_adds_remaining=4,
        opponent_adds_remaining=4,
        best_streamer_score=72,
        avg_streamer_score=45,
    )

    streamers1 = [
        {'name': 'Garrett Crochet', 'expected_points': 45, 'ceiling': 65,
         'floor': 15, 'percentile': 0.85, 'stdev': 18, 'disaster_prob': 0.04},
        {'name': 'Chris Sale', 'expected_points': 38, 'ceiling': 58,
         'floor': 10, 'percentile': 0.70, 'stdev': 20, 'disaster_prob': 0.08},
    ]

    result1 = analyzer.analyze_matchup(context1, "team_3", streamer_options=streamers1)
    print(f"State: {result1['matchup_state']}")
    print(f"Win Probability: {result1['win_probability']:.1%}")
    print(f"Variance Preference: {result1['variance_preference']:.2f}x")
    print(f"Opponent: {result1['opponent']['name']} (Rating: {result1['opponent']['rating']:.0f})")
    print(f"Opponent Type: {result1['opponent']['type']}, L{result1['opponent']['sophistication']}")
    print(f"\nRecommendation: {result1['recommendation']['action']}")
    print(f"Target: {result1['recommendation']['target']}")
    print(f"Reasoning: {result1['recommendation']['reasoning']}")

    # Scenario 2: Way ahead, late week
    print("\n--- SCENARIO 2: Blowout Lead (Saturday) ---")
    context2 = MatchupContext(
        week_number=10,
        day_of_week=5,  # Saturday
        my_score=350,
        opponent_score=220,
        my_projected_remaining=40,
        opponent_projected_remaining=60,
        my_projection_stdev=15,
        opponent_projection_stdev=25,
        my_adds_remaining=2,
        opponent_adds_remaining=1,
        batting_upgrade_available=True,
        batting_upgrade_value=8,
    )

    next_week = WeekPreview(
        opponent=OpponentProfile(
            team_id="team_1", team_name="First Place FC", manager_name="Sarah",
            current_standing=1,
            rating=Glicko2Rating(mu=1650)
        ),
        opponent_projected_strength=78,
        two_start_pitchers_available=2,
        quality_streamers_early_week=3,
    )

    streamers2 = [
        {'name': 'Risky Rick', 'expected_points': 25, 'ceiling': 55,
         'floor': -20, 'percentile': 0.55, 'stdev': 30, 'disaster_prob': 0.18},
    ]

    result2 = analyzer.analyze_matchup(context2, "team_3", next_week, streamers2)
    print(f"State: {result2['matchup_state']}")
    print(f"Win Probability: {result2['win_probability']:.1%}")
    print(f"Next Week: vs {result2['next_week']['opponent']} (Tough: {result2['next_week']['is_tough']})")
    print(f"\nRecommendation: {result2['recommendation']['action']}")
    print(f"Reasoning: {result2['recommendation']['reasoning']}")

    # Scenario 3: Desperate, Sunday
    print("\n--- SCENARIO 3: Desperate (Sunday) ---")
    context3 = MatchupContext(
        week_number=10,
        day_of_week=6,  # Sunday
        my_score=200,
        opponent_score=320,
        my_projected_remaining=25,
        opponent_projected_remaining=30,
        my_projection_stdev=12,
        opponent_projection_stdev=15,
        my_adds_remaining=1,
        opponent_adds_remaining=0,
    )

    streamers3 = [
        {'name': 'Boom or Bust Bob', 'expected_points': 20, 'ceiling': 70,
         'floor': -30, 'percentile': 0.45, 'stdev': 35, 'disaster_prob': 0.22},
        {'name': 'Safe Sam', 'expected_points': 28, 'ceiling': 40,
         'floor': 10, 'percentile': 0.60, 'stdev': 12, 'disaster_prob': 0.05},
    ]

    result3 = analyzer.analyze_matchup(context3, "team_3", streamer_options=streamers3)
    print(f"State: {result3['matchup_state']}")
    print(f"Win Probability: {result3['win_probability']:.1%}")
    print(f"Variance Preference: {result3['variance_preference']:.2f}x (seeking variance!)")
    print(f"\nRecommendation: {result3['recommendation']['action']}")
    print(f"Target: {result3['recommendation']['target']}")
    print(f"Reasoning: {result3['recommendation']['reasoning']}")

    # Secretary Problem Demo
    print("\n--- SECRETARY PROBLEM THRESHOLDS ---")
    print("Minimum percentile to stream based on day and slots remaining:")
    print()
    print("        | Mon   Tue   Wed   Thu   Fri   Sat   Sun")
    print("--------|" + "-" * 42)
    for slots in [5, 4, 3, 2, 1]:
        row = f"{slots} slots |"
        for day in range(7):
            threshold = analyzer.get_streaming_threshold(slots, day)
            row += f" {threshold:.0%}  "
        print(row)

    # Time zone advantage
    print("\n--- TIME ZONE ADVANTAGE ---")
    for opp_tz in TimeZone:
        advantage = OpponentPredictor.late_night_advantage(TimeZone.WEST, opp_tz)
        print(f"You (PT) vs Opponent ({opp_tz.value}): {advantage:+.0f} hour advantage")

    print("\n" + "=" * 70)
    print("Demo complete!")


if __name__ == "__main__":
    demo()
