"""
Quantitative Engine for Fantasy Baseball

Implements the mathematical methods from research:
- BudgetedLinUCB (Bandits with Knapsacks)
- Bayesian projection updates
- Ledoit-Wolf shrinkage for correlations
- Risk-adaptive utility
- Declining thresholds
- Urgency scoring

This is the brain of the optimization system.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from datetime import date, timedelta
from scipy import stats
from sklearn.covariance import LedoitWolf


# =============================================================================
# BUDGETED LinUCB - Core Algorithm
# =============================================================================

class BudgetedLinUCB:
    """
    Contextual bandit with budget constraints.

    This is THE algorithm for our problem - directly from Badanidiyuru et al. (2018).

    Each "arm" is a potential streaming pickup.
    Context includes: matchup quality, park factors, pitcher stats, etc.
    Budget = 5 adds per week.
    """

    def __init__(
        self,
        n_features: int,
        budget: int = 5,
        time_horizon: int = 7,
        alpha: float = 1.0,
        lambda_reg: float = 1.0,
    ):
        """
        Args:
            n_features: Dimension of context vector
            budget: Total adds allowed (5 for BLJ X)
            time_horizon: Days in period (7 for weekly)
            alpha: Exploration parameter (higher = more exploration)
            lambda_reg: Regularization for ridge regression
        """
        self.d = n_features
        self.budget = budget
        self.budget_remaining = budget
        self.time_horizon = time_horizon
        self.time_remaining = time_horizon
        self.alpha = alpha
        self.lambda_reg = lambda_reg

        # LinUCB parameters (shared across arms)
        # A = d x d matrix, b = d x 1 vector
        self.A = lambda_reg * np.eye(n_features)
        self.b = np.zeros(n_features)

        # Track history for analysis
        self.history: List[Dict] = []

    def get_ucb(self, context: np.ndarray, deadline_days: Optional[int] = None) -> Tuple[float, float, float]:
        """
        Calculate UCB value for a context.

        Args:
            context: Feature vector for this arm
            deadline_days: Days until this option expires (for urgency bonus)

        Returns:
            (ucb_value, mean_estimate, confidence_bonus)
        """
        # Solve for theta: A * theta = b
        A_inv = np.linalg.inv(self.A)
        theta = A_inv @ self.b

        # Mean estimate
        mean = context @ theta

        # Confidence bonus (uncertainty)
        confidence = self.alpha * np.sqrt(context @ A_inv @ context)

        # Adjust exploration based on budget/time ratio
        # When budget is tight relative to time, exploit more
        budget_ratio = self.budget_remaining / max(self.budget, 1)
        time_ratio = self.time_remaining / max(self.time_horizon, 1)

        if time_ratio > 0:
            adjustment = budget_ratio / time_ratio
        else:
            adjustment = 0.1  # End of horizon, minimal exploration

        adjusted_confidence = confidence * min(adjustment, 2.0)

        # Urgency bonus for expiring options
        urgency_bonus = 0.0
        if deadline_days is not None and deadline_days > 0:
            # Options expiring soon get a bonus
            urgency_bonus = 5.0 / deadline_days  # +5 pts if expires tomorrow

        ucb = mean + adjusted_confidence + urgency_bonus

        return ucb, mean, adjusted_confidence

    def select_arm(
        self,
        contexts: Dict[str, np.ndarray],
        deadlines: Optional[Dict[str, int]] = None,
    ) -> Optional[Tuple[str, float]]:
        """
        Select the best arm to pull (player to add).

        Args:
            contexts: Dict mapping arm_id -> context vector
            deadlines: Dict mapping arm_id -> days until unavailable

        Returns:
            (best_arm_id, ucb_value) or None if budget exhausted
        """
        if self.budget_remaining <= 0:
            return None

        if not contexts:
            return None

        best_arm = None
        best_ucb = -float('inf')

        for arm_id, context in contexts.items():
            deadline = deadlines.get(arm_id) if deadlines else None
            ucb, _, _ = self.get_ucb(context, deadline)

            if ucb > best_ucb:
                best_ucb = ucb
                best_arm = arm_id

        return (best_arm, best_ucb) if best_arm else None

    def update(self, context: np.ndarray, reward: float):
        """
        Update model after observing reward.

        Args:
            context: Feature vector of selected arm
            reward: Observed fantasy points
        """
        self.A += np.outer(context, context)
        self.b += reward * context
        self.budget_remaining -= 1

        self.history.append({
            'context': context.copy(),
            'reward': reward,
            'budget_remaining': self.budget_remaining,
            'time_remaining': self.time_remaining,
        })

    def advance_time(self):
        """Call at end of each day."""
        self.time_remaining -= 1

    def reset_week(self):
        """Reset for new week."""
        self.budget_remaining = self.budget
        self.time_remaining = self.time_horizon
        # Keep learned parameters (A, b) for continuity


# =============================================================================
# CONTEXT BUILDER - Feature Engineering
# =============================================================================

@dataclass
class StreamingContext:
    """Context features for a streaming option."""

    # Player quality
    era: float = 4.00
    k_per_9: float = 8.0
    bb_per_9: float = 3.0
    hr_per_9: float = 1.2
    gb_rate: float = 0.45

    # Matchup
    opp_wrc_plus: float = 100.0
    opp_k_rate: float = 0.22
    opp_hr_rate: float = 0.028

    # Park/situational
    park_hr_factor: float = 100.0
    is_home: bool = True

    # Schedule
    is_two_start: bool = False
    days_until_start: int = 1
    days_until_unavailable: int = 7

    # Extras
    catcher_framing_runs: float = 0.0
    weather_hrfi: float = 5.0  # 1-10 scale, 5 = neutral

    def to_vector(self) -> np.ndarray:
        """Convert to feature vector for LinUCB."""
        return np.array([
            # Normalize features to similar scales
            (4.50 - self.era) / 1.5,  # Lower ERA = higher value
            (self.k_per_9 - 7.0) / 3.0,  # Higher K = higher value
            (3.5 - self.bb_per_9) / 1.5,  # Lower BB = higher value
            (1.3 - self.hr_per_9) / 0.5,  # Lower HR = higher value
            (self.gb_rate - 0.40) / 0.15,  # Higher GB = higher value
            (100 - self.opp_wrc_plus) / 30,  # Lower opp offense = higher value
            (self.opp_k_rate - 0.20) / 0.05,  # Higher opp K rate = higher value
            (0.030 - self.opp_hr_rate) / 0.010,  # Lower opp HR rate = higher value
            (100 - self.park_hr_factor) / 20,  # Lower park factor = higher value
            1.0 if self.is_home else 0.0,
            1.0 if self.is_two_start else 0.0,  # Two-start bonus
            self.catcher_framing_runs / 10,
            (5 - self.weather_hrfi) / 4,  # Lower HRFI = higher value
        ])

    @staticmethod
    def n_features() -> int:
        return 13


def build_context(
    pitcher_stats: Dict,
    opponent_stats: Dict,
    park_factor: float,
    is_home: bool,
    is_two_start: bool = False,
    catcher_framing: float = 0.0,
    weather_hrfi: float = 5.0,
) -> StreamingContext:
    """Build context from raw stats."""
    return StreamingContext(
        era=pitcher_stats.get('era', 4.00),
        k_per_9=pitcher_stats.get('k_per_9', 8.0),
        bb_per_9=pitcher_stats.get('bb_per_9', 3.0),
        hr_per_9=pitcher_stats.get('hr_per_9', 1.2),
        gb_rate=pitcher_stats.get('gb_rate', 0.45),
        opp_wrc_plus=opponent_stats.get('wrc_plus', 100),
        opp_k_rate=opponent_stats.get('k_rate', 0.22),
        opp_hr_rate=opponent_stats.get('hr_rate', 0.028),
        park_hr_factor=park_factor,
        is_home=is_home,
        is_two_start=is_two_start,
        catcher_framing_runs=catcher_framing,
        weather_hrfi=weather_hrfi,
    )


# =============================================================================
# BAYESIAN PROJECTION UPDATES
# =============================================================================

@dataclass
class BayesianProjection:
    """
    Bayesian projection that updates with observed performance.

    Uses Normal-Normal conjugate prior for fantasy points.
    """
    prior_mean: float
    prior_std: float
    observed_mean: float = 0.0
    observed_std: float = 10.0  # Typical game-to-game variance
    n_observations: int = 0

    @property
    def posterior_mean(self) -> float:
        """Weighted average of prior and observed."""
        if self.n_observations == 0:
            return self.prior_mean

        prior_precision = 1 / (self.prior_std ** 2)
        obs_precision = self.n_observations / (self.observed_std ** 2)

        total_precision = prior_precision + obs_precision
        return (prior_precision * self.prior_mean +
                obs_precision * self.observed_mean) / total_precision

    @property
    def posterior_std(self) -> float:
        """Uncertainty after observations."""
        if self.n_observations == 0:
            return self.prior_std

        prior_precision = 1 / (self.prior_std ** 2)
        obs_precision = self.n_observations / (self.observed_std ** 2)

        return np.sqrt(1 / (prior_precision + obs_precision))

    def update(self, observed_points: float):
        """Update with a new observation."""
        self.n_observations += 1
        # Running mean update
        self.observed_mean += (observed_points - self.observed_mean) / self.n_observations

    def sample(self) -> float:
        """Sample from posterior (for Thompson Sampling)."""
        return np.random.normal(self.posterior_mean, self.posterior_std)

    def confidence_interval(self, level: float = 0.9) -> Tuple[float, float]:
        """Get confidence interval."""
        z = stats.norm.ppf((1 + level) / 2)
        return (
            self.posterior_mean - z * self.posterior_std,
            self.posterior_mean + z * self.posterior_std,
        )


class ProjectionManager:
    """Manages Bayesian projections for all players."""

    def __init__(self):
        self.projections: Dict[str, BayesianProjection] = {}

    def add_player(self, player_name: str, prior_mean: float, prior_std: float = 5.0):
        """Add a player with prior projection."""
        self.projections[player_name] = BayesianProjection(
            prior_mean=prior_mean,
            prior_std=prior_std,
        )

    def update_player(self, player_name: str, observed_points: float):
        """Update player projection with observed performance."""
        if player_name in self.projections:
            self.projections[player_name].update(observed_points)

    def get_projection(self, player_name: str) -> Optional[BayesianProjection]:
        """Get current projection for player."""
        return self.projections.get(player_name)

    def get_all_posteriors(self) -> Dict[str, Tuple[float, float]]:
        """Get all posterior means and stds."""
        return {
            name: (proj.posterior_mean, proj.posterior_std)
            for name, proj in self.projections.items()
        }


# =============================================================================
# CORRELATION ESTIMATION (Ledoit-Wolf Shrinkage)
# =============================================================================

class CorrelationEstimator:
    """
    Estimates player correlations using Ledoit-Wolf shrinkage.

    Critical for portfolio optimization - raw sample correlation
    is unreliable with small samples.
    """

    def __init__(self, shrinkage_target: str = 'identity'):
        """
        Args:
            shrinkage_target: 'identity' or 'constant_correlation'
        """
        self.shrinkage_target = shrinkage_target
        self.lw = LedoitWolf()
        self.fitted = False
        self.player_names: List[str] = []

    def fit(self, performance_matrix: np.ndarray, player_names: List[str]):
        """
        Fit on historical performance data.

        Args:
            performance_matrix: Shape (n_games, n_players)
            player_names: List of player names matching columns
        """
        if performance_matrix.shape[0] < 3:
            # Not enough data
            return

        self.lw.fit(performance_matrix)
        self.player_names = player_names
        self.fitted = True

    @property
    def covariance(self) -> np.ndarray:
        """Get shrunk covariance matrix."""
        if not self.fitted:
            return np.eye(len(self.player_names))
        return self.lw.covariance_

    @property
    def correlation(self) -> np.ndarray:
        """Get correlation matrix from covariance."""
        cov = self.covariance
        std = np.sqrt(np.diag(cov))
        std[std == 0] = 1  # Avoid division by zero
        return cov / np.outer(std, std)

    @property
    def shrinkage_amount(self) -> float:
        """How much shrinkage was applied (0-1)."""
        if not self.fitted:
            return 1.0
        return self.lw.shrinkage_

    def get_correlation(self, player1: str, player2: str) -> float:
        """Get correlation between two players."""
        if not self.fitted:
            return 0.0

        try:
            i = self.player_names.index(player1)
            j = self.player_names.index(player2)
            return self.correlation[i, j]
        except (ValueError, IndexError):
            return 0.0


# =============================================================================
# RISK-ADAPTIVE UTILITY
# =============================================================================

class RiskAdaptiveUtility:
    """
    Adjusts risk tolerance based on matchup score differential.

    From research: Risk-sensitive Bellman equation with exponential utility.
    theta > 0: risk-averse (protect lead)
    theta < 0: risk-seeking (need variance to catch up)
    """

    def __init__(self):
        self.score_differential: float = 0.0
        self.days_remaining: int = 7

    def update_state(self, my_score: float, opp_score: float, days_remaining: int):
        """Update game state."""
        self.score_differential = my_score - opp_score
        self.days_remaining = days_remaining

    @property
    def risk_parameter(self) -> float:
        """
        Get risk parameter theta.

        Positive = risk-averse (protect lead)
        Negative = risk-seeking (need variance)
        Zero = risk-neutral
        """
        if self.days_remaining <= 1:
            # End of week - extreme positions
            if self.score_differential > 30:
                return 3.0  # Very conservative
            elif self.score_differential < -30:
                return -3.0  # Very aggressive

        if self.score_differential > 30:
            return 2.0  # Risk-averse: protect large lead
        elif self.score_differential > 10:
            return 0.5  # Mildly risk-averse
        elif self.score_differential > -10:
            return 0.0  # Risk-neutral (close game)
        elif self.score_differential > -30:
            return -1.0  # Risk-seeking
        else:
            return -2.0  # Very risk-seeking: need variance

    def adjust_value(self, mean: float, std: float) -> float:
        """
        Adjust expected value based on risk preference.

        Args:
            mean: Expected points
            std: Standard deviation of points

        Returns:
            Risk-adjusted value
        """
        theta = self.risk_parameter

        if theta == 0:
            return mean
        elif theta > 0:
            # Risk-averse: penalize variance (prefer floor)
            return mean - 0.5 * theta * std
        else:
            # Risk-seeking: bonus for variance (prefer ceiling)
            return mean - 0.5 * theta * std  # Note: theta < 0, so this adds


# =============================================================================
# THRESHOLD CALCULATOR
# =============================================================================

class ThresholdCalculator:
    """
    Calculates declining thresholds for add decisions.

    From research: Monday threshold = 90th percentile, Saturday = 50th.
    Option value decays as week progresses.
    """

    def __init__(
        self,
        historical_values: Optional[List[float]] = None,
        base_threshold: float = 40.0,
    ):
        """
        Args:
            historical_values: Past streaming pickup values for percentile calc
            base_threshold: Default threshold if no history
        """
        self.historical_values = historical_values or []
        self.base_threshold = base_threshold

    def add_observation(self, value: float):
        """Add an observed streaming value."""
        self.historical_values.append(value)

    def get_threshold(self, day_of_week: int, adds_remaining: int) -> float:
        """
        Get threshold for current situation.

        Args:
            day_of_week: 0=Monday, 6=Sunday
            adds_remaining: How many adds left

        Returns:
            Minimum expected value to make an add
        """
        if not self.historical_values:
            # No history - use declining base threshold
            decline_factor = 1.0 - (day_of_week / 10)  # 1.0 on Mon, 0.4 on Sun
            return self.base_threshold * decline_factor

        # Calculate percentile threshold
        # Monday: 90th percentile, Sunday: 50th percentile
        percentile = 90 - (day_of_week * 40 / 6)  # 90 -> 50 over week
        threshold = np.percentile(self.historical_values, percentile)

        # Adjust for adds remaining
        # Fewer adds = higher bar (more precious)
        if adds_remaining <= 1:
            threshold *= 1.2
        elif adds_remaining >= 4:
            threshold *= 0.9

        return threshold

    def get_option_value(self, day_of_week: int, adds_remaining: int) -> float:
        """
        Calculate option value of waiting.

        From research: E[future_best] * (adds_remaining - 1) / adds_remaining
        """
        if adds_remaining <= 1 or day_of_week >= 6:
            return 0.0  # No option value at end

        days_left = 6 - day_of_week

        if not self.historical_values:
            future_expected = self.base_threshold
        else:
            # Expected value of best future option
            future_expected = np.percentile(self.historical_values, 75)

        # Option value formula
        option_value = future_expected * (adds_remaining - 1) / adds_remaining

        # Decay by days remaining
        option_value *= days_left / 6

        return option_value


# =============================================================================
# URGENCY SCORER
# =============================================================================

class UrgencyScorer:
    """
    Scores urgency of streaming options.

    From research: urgency = projected_value / days_until_unavailable
    """

    @staticmethod
    def score(
        projected_value: float,
        days_until_unavailable: int,
        is_two_start: bool = False,
    ) -> float:
        """
        Calculate urgency-adjusted score.

        Args:
            projected_value: Expected fantasy points
            days_until_unavailable: Days until option expires
            is_two_start: Is this a two-start pitcher?

        Returns:
            Urgency-adjusted score
        """
        if days_until_unavailable <= 0:
            return 0.0  # Already unavailable

        # Base urgency
        urgency = projected_value / days_until_unavailable

        # Two-start bonus (efficiency)
        if is_two_start:
            urgency *= 1.5  # 50% bonus for 2-for-1 efficiency

        return urgency

    @staticmethod
    def rank_options(
        options: List[Dict],
    ) -> List[Dict]:
        """
        Rank options by urgency-adjusted score.

        Args:
            options: List of dicts with 'value', 'deadline', 'two_start' keys

        Returns:
            Sorted list (highest urgency first)
        """
        for opt in options:
            opt['urgency_score'] = UrgencyScorer.score(
                projected_value=opt.get('value', 0),
                days_until_unavailable=opt.get('deadline', 7),
                is_two_start=opt.get('two_start', False),
            )

        return sorted(options, key=lambda x: x['urgency_score'], reverse=True)


# =============================================================================
# NEWSVENDOR RESERVE CALCULATOR
# =============================================================================

class NewsvendorReserve:
    """
    Calculates optimal reserve adds using newsvendor model.

    From research: Q* = F^{-1}(Cu / (Cu + Co))
    Cu = cost of underage (missing important activation)
    Co = cost of overage (wasting an add)
    """

    def __init__(
        self,
        cost_underage: float = 15.0,  # Missing a key IL activation
        cost_overage: float = 5.0,    # Wasting an add
        emergency_rate: float = 0.3,  # P(needing emergency add)
    ):
        self.cost_underage = cost_underage
        self.cost_overage = cost_overage
        self.emergency_rate = emergency_rate

    @property
    def critical_fractile(self) -> float:
        """Optimal service level."""
        return self.cost_underage / (self.cost_underage + self.cost_overage)

    def optimal_reserve(
        self,
        n_il_players: int = 0,
        n_dtd_players: int = 0,
        days_remaining: int = 7,
    ) -> int:
        """
        Calculate optimal adds to reserve.

        Args:
            n_il_players: Players on IL who might return
            n_dtd_players: Players who are day-to-day
            days_remaining: Days left in week

        Returns:
            Number of adds to reserve (0-2)
        """
        # Estimate emergency probability
        p_emergency = min(0.9, (
            self.emergency_rate +
            n_il_players * 0.15 +  # Each IL player adds 15% chance
            n_dtd_players * 0.20   # Each DTD player adds 20% chance
        ))

        # Poisson model for number of emergencies
        # Reserve at critical fractile
        if p_emergency < 0.3:
            return 0
        elif p_emergency < 0.6:
            return 1
        else:
            return 2

    def should_use_add(
        self,
        add_value: float,
        adds_remaining: int,
        days_remaining: int,
        reserve_target: int,
    ) -> Tuple[bool, str]:
        """
        Decide whether to use an add or reserve it.

        Returns:
            (should_use, reason)
        """
        buffer = adds_remaining - reserve_target

        if buffer <= 0:
            # At or below reserve - need strong value
            threshold = self.cost_underage
            if add_value > threshold:
                return True, f"Value {add_value:.1f} exceeds reserve threshold {threshold:.1f}"
            else:
                return False, f"Reserving add (value {add_value:.1f} < {threshold:.1f})"

        # Have buffer - use normal decision
        return True, f"Buffer available ({buffer} above reserve)"


# =============================================================================
# INTEGRATED DECISION ENGINE
# =============================================================================

class QuantEngine:
    """
    Integrated quantitative decision engine.

    Combines all components for optimal add decisions.
    """

    def __init__(self, budget: int = 5, time_horizon: int = 7):
        # Core algorithm
        self.bandit = BudgetedLinUCB(
            n_features=StreamingContext.n_features(),
            budget=budget,
            time_horizon=time_horizon,
        )

        # Supporting components
        self.projections = ProjectionManager()
        self.correlations = CorrelationEstimator()
        self.risk_utility = RiskAdaptiveUtility()
        self.thresholds = ThresholdCalculator()
        self.urgency = UrgencyScorer()
        self.reserve = NewsvendorReserve()

        # State
        self.budget = budget
        self.time_horizon = time_horizon
        self.current_day = 0

    def should_add(
        self,
        context: StreamingContext,
        player_name: str,
        my_score: float = 0,
        opp_score: float = 0,
        n_il_players: int = 0,
        n_dtd_players: int = 0,
    ) -> Tuple[bool, float, str]:
        """
        Decide whether to make an add.

        Args:
            context: Streaming context for the player
            player_name: Name of player to add
            my_score: Current matchup score
            opp_score: Opponent's score
            n_il_players: IL players who might return
            n_dtd_players: DTD players

        Returns:
            (should_add, expected_value, reason)
        """
        # Update risk state
        self.risk_utility.update_state(my_score, opp_score, self.time_horizon - self.current_day)

        # Get UCB value
        ucb, mean, conf = self.bandit.get_ucb(
            context.to_vector(),
            deadline_days=context.days_until_unavailable,
        )

        # Get projection if available
        proj = self.projections.get_projection(player_name)
        if proj:
            # Use Bayesian posterior
            expected = proj.posterior_mean
            std = proj.posterior_std
        else:
            # Use UCB estimate
            expected = mean
            std = conf / self.bandit.alpha  # Rough estimate

        # Risk-adjust value
        risk_adjusted = self.risk_utility.adjust_value(expected, std)

        # Calculate threshold
        threshold = self.thresholds.get_threshold(
            day_of_week=self.current_day,
            adds_remaining=self.bandit.budget_remaining,
        )

        # Calculate option value of waiting
        option_value = self.thresholds.get_option_value(
            day_of_week=self.current_day,
            adds_remaining=self.bandit.budget_remaining,
        )

        # Check reserve requirements
        reserve_target = self.reserve.optimal_reserve(
            n_il_players=n_il_players,
            n_dtd_players=n_dtd_players,
            days_remaining=self.time_horizon - self.current_day,
        )

        should_use, reserve_reason = self.reserve.should_use_add(
            add_value=risk_adjusted,
            adds_remaining=self.bandit.budget_remaining,
            days_remaining=self.time_horizon - self.current_day,
            reserve_target=reserve_target,
        )

        if not should_use:
            return False, risk_adjusted, reserve_reason

        # Final decision: value > threshold + option_value?
        decision_threshold = threshold + option_value

        if risk_adjusted > decision_threshold:
            reason = (f"Value {risk_adjusted:.1f} > threshold {threshold:.1f} + "
                     f"option {option_value:.1f} = {decision_threshold:.1f}")
            return True, risk_adjusted, reason
        else:
            reason = (f"Value {risk_adjusted:.1f} < threshold {decision_threshold:.1f}. "
                     f"Wait for better option.")
            return False, risk_adjusted, reason

    def rank_options(
        self,
        options: List[Tuple[str, StreamingContext]],
    ) -> List[Tuple[str, float, str]]:
        """
        Rank multiple streaming options.

        Args:
            options: List of (player_name, context) tuples

        Returns:
            Sorted list of (player_name, score, reason)
        """
        scored = []

        for player_name, context in options:
            ucb, mean, conf = self.bandit.get_ucb(
                context.to_vector(),
                deadline_days=context.days_until_unavailable,
            )

            # Urgency adjustment
            urgency_score = self.urgency.score(
                projected_value=ucb,
                days_until_unavailable=context.days_until_unavailable,
                is_two_start=context.is_two_start,
            )

            reason = f"UCB={ucb:.1f}, urgency={urgency_score:.1f}"
            if context.is_two_start:
                reason += " [2-START]"

            scored.append((player_name, urgency_score, reason))

        return sorted(scored, key=lambda x: x[1], reverse=True)

    def update_with_result(self, context: StreamingContext, player_name: str, points: float):
        """Update model after observing result."""
        # Update bandit
        self.bandit.update(context.to_vector(), points)

        # Update Bayesian projection
        self.projections.update_player(player_name, points)

        # Update threshold history
        self.thresholds.add_observation(points)

    def advance_day(self):
        """Move to next day."""
        self.current_day += 1
        self.bandit.advance_time()

    def new_week(self):
        """Start a new week."""
        self.current_day = 0
        self.bandit.reset_week()


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("QUANT ENGINE DEMO")
    print("=" * 60)

    # Initialize engine
    engine = QuantEngine(budget=5, time_horizon=7)

    # Add some prior projections
    engine.projections.add_player("Pablo Lopez", prior_mean=45.0, prior_std=8.0)
    engine.projections.add_player("Reese Olson", prior_mean=38.0, prior_std=10.0)
    engine.projections.add_player("Mitchell Parker", prior_mean=35.0, prior_std=12.0)

    # Create sample contexts
    options = [
        ("Pablo Lopez", StreamingContext(
            era=3.50, k_per_9=9.0, gb_rate=0.48,
            opp_wrc_plus=85, opp_k_rate=0.25,
            park_hr_factor=95, is_home=True,
            is_two_start=True, days_until_unavailable=5,
        )),
        ("Reese Olson", StreamingContext(
            era=4.00, k_per_9=8.5, gb_rate=0.45,
            opp_wrc_plus=75, opp_k_rate=0.27,
            park_hr_factor=90, is_home=True,
            is_two_start=False, days_until_unavailable=2,
        )),
        ("Mitchell Parker", StreamingContext(
            era=4.20, k_per_9=7.5, gb_rate=0.42,
            opp_wrc_plus=90, opp_k_rate=0.23,
            park_hr_factor=100, is_home=False,
            is_two_start=False, days_until_unavailable=4,
        )),
    ]

    # Rank options
    print("\nSTREAMING OPTIONS (ranked):")
    print("-" * 50)
    ranked = engine.rank_options(options)
    for i, (name, score, reason) in enumerate(ranked, 1):
        print(f"{i}. {name}: {score:.1f}")
        print(f"   {reason}")

    # Test decision making
    print("\n" + "=" * 50)
    print("DECISION TEST (Monday, 5 adds remaining):")
    print("-" * 50)

    for name, context in options:
        should, value, reason = engine.should_add(
            context=context,
            player_name=name,
            my_score=0,
            opp_score=0,
            n_il_players=1,
            n_dtd_players=0,
        )
        decision = "ADD" if should else "WAIT"
        print(f"\n{name}: {decision}")
        print(f"  Value: {value:.1f}")
        print(f"  Reason: {reason}")

    # Test risk adaptation
    print("\n" + "=" * 50)
    print("RISK ADAPTATION TEST:")
    print("-" * 50)

    scenarios = [
        (100, 50, "Leading by 50"),
        (75, 80, "Trailing by 5"),
        (60, 100, "Trailing by 40"),
    ]

    for my_score, opp_score, desc in scenarios:
        engine.risk_utility.update_state(my_score, opp_score, 3)
        theta = engine.risk_utility.risk_parameter

        # Risk-adjust a player with mean=40, std=15
        adjusted = engine.risk_utility.adjust_value(40, 15)

        print(f"\n{desc}:")
        print(f"  Risk parameter theta = {theta:.1f}")
        print(f"  Mean=40, Std=15 -> Risk-adjusted = {adjusted:.1f}")
