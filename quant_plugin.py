"""
Quant Plugin for Fantasy Bot

Integrates the quantitative decision engine with the fantasy bot.
Provides intelligent streaming decisions using:
- BudgetedLinUCB for optimal add allocation
- Bayesian projection updates
- Risk-adaptive utility
- Declining thresholds
- Floor/ceiling risk analysis
- Disaster probability estimation
"""
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple

from fantasy_bot import Plugin, FantasyBot
from quant_engine import (
    QuantEngine, StreamingContext, build_context,
    BayesianProjection, UrgencyScorer
)
from streaming import (
    TEAM_OFFENSE_RANK, TEAM_HR_RATE, TEAM_K_RATE,
    PARK_HR_FACTORS, calculate_streaming_score
)
from points_projector import project_starter
from hidden_edges import CATCHER_FRAMING
from risk_analysis import (
    RiskCalculator, RiskAwareRanker, SimpleBaseline,
    PitcherProfile, MatchupContext, RiskTier
)


class QuantPlugin(Plugin):
    """
    Quantitative decision-making plugin.

    Uses mathematical optimization for streaming decisions.
    Includes risk analysis for floor/ceiling and disaster probability.
    """

    name = "quant"
    description = "Mathematical optimization for streaming (BwK, Bayesian, risk-adaptive, floor/ceiling)"
    version = "1.1"

    def __init__(self, risk_aversion: float = 1.0):
        self.engine: Optional[QuantEngine] = None
        self.bot: Optional[FantasyBot] = None
        self.risk_calculator = RiskCalculator(risk_aversion)
        self.baseline = SimpleBaseline()
        self.risk_aversion = risk_aversion

    def initialize(self, bot: FantasyBot):
        """Initialize with bot reference."""
        self.bot = bot
        self.engine = QuantEngine(
            budget=bot.config.adds_per_week,
            time_horizon=7,
        )
        print(f"Quant plugin initialized (budget={bot.config.adds_per_week}, risk_aversion={self.risk_aversion})")

    def on_daily_run(self, bot: FantasyBot) -> str:
        """Run quant analysis during daily check."""
        if not self.engine:
            return "Quant engine not initialized"

        lines = ["", "=== QUANT ANALYSIS ==="]

        # Get current state
        adds_remaining = bot.roster.adds_remaining()
        today = date.today()
        day_of_week = today.weekday()

        lines.append(f"Day: {today.strftime('%A')} (day {day_of_week})")
        lines.append(f"Adds remaining: {adds_remaining}/{bot.config.adds_per_week}")

        # Calculate threshold for today
        threshold = self.engine.thresholds.get_threshold(day_of_week, adds_remaining)
        option_value = self.engine.thresholds.get_option_value(day_of_week, adds_remaining)

        lines.append(f"Today's threshold: {threshold:.1f}")
        lines.append(f"Option value of waiting: {option_value:.1f}")

        # Risk state
        risk_param = self.engine.risk_utility.risk_parameter
        if risk_param > 0:
            risk_stance = "CONSERVATIVE (protecting lead)"
        elif risk_param < 0:
            risk_stance = "AGGRESSIVE (need variance)"
        else:
            risk_stance = "NEUTRAL"
        lines.append(f"Risk stance: {risk_stance} (theta={risk_param:.1f})")

        # Reserve recommendation
        n_il = len(bot.roster.get_il_players())
        n_dtd = len(bot.roster.get_dtd_players())
        reserve = self.engine.reserve.optimal_reserve(n_il, n_dtd, 7 - day_of_week)
        lines.append(f"Reserve recommendation: {reserve} add(s) for contingencies")

        # Decision rule summary
        effective_threshold = threshold + option_value
        lines.append(f"\nDECISION RULE: Add if expected value > {effective_threshold:.1f}")

        return "\n".join(lines)

    def on_pre_lock(self, bot: FantasyBot, game_date: date):
        """Pre-lock quant check."""
        if not self.engine:
            return

        print("\n=== QUANT PRE-LOCK CHECK ===")

        # Get best options for tomorrow
        try:
            tomorrow_starts = bot.schedule.get_day_starts(game_date)
            if not tomorrow_starts:
                print("No starts found for tomorrow")
                return

            # Build contexts and rank
            options = []
            for start in tomorrow_starts[:20]:  # Top 20
                context = self._build_context_from_start(start)
                options.append((start.pitcher_name, context))

            ranked = self.engine.rank_options(options)

            print(f"\nTop streaming options for {game_date.strftime('%A')}:")
            for i, (name, score, reason) in enumerate(ranked[:5], 1):
                print(f"  {i}. {name}: {score:.1f}")
                print(f"     {reason}")

        except Exception as e:
            print(f"Error in pre-lock check: {e}")

    def adjust_projection(self, projection: dict) -> dict:
        """Apply quant adjustments to projections."""
        if not self.engine:
            return projection

        player_name = projection.get('player_name', '')

        # Check for Bayesian posterior
        bayes_proj = self.engine.projections.get_projection(player_name)
        if bayes_proj:
            projection['bayesian_mean'] = bayes_proj.posterior_mean
            projection['bayesian_std'] = bayes_proj.posterior_std
            projection['n_observations'] = bayes_proj.n_observations

            # Risk-adjust
            risk_adjusted = self.engine.risk_utility.adjust_value(
                bayes_proj.posterior_mean,
                bayes_proj.posterior_std
            )
            projection['risk_adjusted_value'] = risk_adjusted

        return projection

    def get_alerts(self) -> List[str]:
        """Get quant-based alerts."""
        alerts = []

        if not self.engine:
            return alerts

        # Check if we should be more aggressive or conservative
        theta = self.engine.risk_utility.risk_parameter
        if theta < -1.5:
            alerts.append("QUANT: Behind significantly - stream high-ceiling players")
        elif theta > 1.5:
            alerts.append("QUANT: Large lead - prioritize safe floor over upside")

        # Check if running low on adds
        if self.engine.bandit.budget_remaining <= 2:
            reserve = self.engine.reserve.optimal_reserve(0, 0, self.engine.bandit.time_remaining)
            if self.engine.bandit.budget_remaining <= reserve:
                alerts.append(f"QUANT: Only {self.engine.bandit.budget_remaining} adds left - reserve mode")

        return alerts

    def _build_context_from_start(self, start) -> StreamingContext:
        """Build context from a PitchingStart object."""
        # Get opponent stats
        opp = start.opponent
        opp_wrc = TEAM_OFFENSE_RANK.get(opp, 70)
        opp_hr = TEAM_HR_RATE.get(opp, 0.028)
        opp_k = TEAM_K_RATE.get(opp, 0.22)

        # Get park factor
        park = start.opponent if not start.is_home else start.team
        park_hr = PARK_HR_FACTORS.get(park, 100)

        # Check catcher framing (simplified - would need team roster data)
        framing = 0.0
        # TODO: Look up actual catcher

        return StreamingContext(
            era=4.00,  # Would need actual pitcher stats
            k_per_9=8.0,
            bb_per_9=3.0,
            hr_per_9=1.2,
            gb_rate=0.45,
            opp_wrc_plus=opp_wrc,
            opp_k_rate=opp_k,
            opp_hr_rate=opp_hr,
            park_hr_factor=park_hr,
            is_home=start.is_home,
            is_two_start=start.is_two_start,
            days_until_unavailable=7,  # Would calculate from schedule
            catcher_framing_runs=framing,
        )

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def evaluate_add(
        self,
        player_name: str,
        opponent: str,
        is_home: bool = True,
        is_two_start: bool = False,
        pitcher_stats: Dict = None,
        my_score: float = 0,
        opp_score: float = 0,
    ) -> Tuple[bool, float, str]:
        """
        Evaluate whether to make a specific add.

        Args:
            player_name: Player to evaluate
            opponent: Opponent team abbreviation
            is_home: Is pitcher at home?
            is_two_start: Is this a two-start pitcher?
            pitcher_stats: Optional dict with era, k_per_9, etc.
            my_score: Current matchup score
            opp_score: Opponent's score

        Returns:
            (should_add, expected_value, reason)
        """
        if not self.engine:
            return False, 0.0, "Quant engine not initialized"

        # Build context
        pitcher_stats = pitcher_stats or {}
        opp_stats = {
            'wrc_plus': TEAM_OFFENSE_RANK.get(opponent, 70),
            'k_rate': TEAM_K_RATE.get(opponent, 0.22),
            'hr_rate': TEAM_HR_RATE.get(opponent, 0.028),
        }

        park = opponent if not is_home else ""  # Simplified
        park_hr = PARK_HR_FACTORS.get(park, 100)

        context = build_context(
            pitcher_stats=pitcher_stats,
            opponent_stats=opp_stats,
            park_factor=park_hr,
            is_home=is_home,
            is_two_start=is_two_start,
        )

        # Get decision
        n_il = len(self.bot.roster.get_il_players()) if self.bot else 0
        n_dtd = len(self.bot.roster.get_dtd_players()) if self.bot else 0

        return self.engine.should_add(
            context=context,
            player_name=player_name,
            my_score=my_score,
            opp_score=opp_score,
            n_il_players=n_il,
            n_dtd_players=n_dtd,
        )

    def rank_streaming_options(
        self,
        options: List[Dict],
        include_risk: bool = True,
    ) -> List[Dict]:
        """
        Rank streaming options using quant methods + risk analysis.

        Args:
            options: List of dicts with keys:
                - name: Player name
                - opponent: Opponent abbreviation
                - is_home: Boolean
                - is_two_start: Boolean
                - pitcher_stats: Optional dict (era, k_per_9, bb_per_9, hr_per_9, gb_rate, fb_rate)
            include_risk: Whether to add risk metrics (floor, ceiling, disaster_prob)

        Returns:
            Sorted list with added quant_score, risk metrics, and recommendations
        """
        if not self.engine:
            return options

        contexts = []
        for opt in options:
            opp = opt.get('opponent', '')
            opp_stats = {
                'wrc_plus': TEAM_OFFENSE_RANK.get(opp, 70),
                'k_rate': TEAM_K_RATE.get(opp, 0.22),
                'hr_rate': TEAM_HR_RATE.get(opp, 0.028),
            }
            park_hr = PARK_HR_FACTORS.get(opp if not opt.get('is_home') else '', 100)

            context = build_context(
                pitcher_stats=opt.get('pitcher_stats', {}),
                opponent_stats=opp_stats,
                park_factor=park_hr,
                is_home=opt.get('is_home', True),
                is_two_start=opt.get('is_two_start', False),
            )
            contexts.append((opt.get('name', ''), context))

        # Rank using quant engine
        ranked = self.engine.rank_options(contexts)

        # Merge back
        name_to_result = {name: (score, reason) for name, score, reason in ranked}
        for opt in options:
            name = opt.get('name', '')
            if name in name_to_result:
                opt['quant_score'], opt['quant_reason'] = name_to_result[name]
            else:
                opt['quant_score'] = 0
                opt['quant_reason'] = 'Not evaluated'

            # Add risk analysis
            if include_risk:
                risk_info = self._assess_risk(opt)
                opt.update(risk_info)

        # Sort by risk-adjusted value if available, else quant_score
        return sorted(
            options,
            key=lambda x: (
                x.get('risk_tier') != 'no_go',  # NO_GO last
                x.get('risk_adjusted', x.get('quant_score', 0))
            ),
            reverse=True
        )

    def _assess_risk(self, opt: Dict) -> Dict:
        """
        Assess risk for a single streaming option.

        Returns dict with floor, ceiling, disaster_prob, risk_tier, etc.
        """
        pitcher_stats = opt.get('pitcher_stats', {})
        opp = opt.get('opponent', '')
        park = opp if not opt.get('is_home', True) else opt.get('park', opp)
        is_two_start = opt.get('is_two_start', False)

        # Build pitcher profile
        pitcher = PitcherProfile(
            name=opt.get('name', 'Unknown'),
            era=pitcher_stats.get('era', 4.00),
            k_per_9=pitcher_stats.get('k_per_9', 8.5),
            bb_per_9=pitcher_stats.get('bb_per_9', 3.0),
            hr_per_9=pitcher_stats.get('hr_per_9', 1.2),
            gb_rate=pitcher_stats.get('gb_rate', 0.43),
            fb_rate=pitcher_stats.get('fb_rate', 0.35),
        )

        # Build matchup context
        context = MatchupContext(
            pitcher=pitcher,
            opponent=opp,
            park=park,
            is_home=opt.get('is_home', True),
            expected_ip=5.5 * (1.8 if is_two_start else 1.0),
        )

        # Get risk assessment
        assessment = self.risk_calculator.assess_matchup(context)

        # Also get simple baseline
        baseline = self.baseline.evaluate(pitcher, opp, park, is_two_start)

        return {
            'expected_pts': assessment.expected_points,
            'floor': assessment.floor_points,
            'ceiling': assessment.ceiling_points,
            'disaster_prob': assessment.disaster_prob,
            'blowup_prob': assessment.blowup_prob,
            'risk_adjusted': assessment.risk_adjusted_value,
            'risk_tier': assessment.risk_tier.value,
            'risk_score': assessment.risk_score,
            'recommendation': assessment.recommendation,
            'warnings': assessment.warnings,
            'simple_score': baseline.simple_score,
            'simple_rec': baseline.simple_recommendation,
        }

    def get_full_analysis(self, options: List[Dict]) -> str:
        """
        Get formatted full analysis for streaming options.

        Returns human-readable string with all metrics.
        """
        ranked = self.rank_streaming_options(options, include_risk=True)

        lines = ["", "=" * 60, "STREAMING ANALYSIS (Quant + Risk)", "=" * 60]

        for i, opt in enumerate(ranked, 1):
            name = opt.get('name', 'Unknown')
            opp = opt.get('opponent', '???')
            two_start = " [2-START]" if opt.get('is_two_start') else ""
            tier = opt.get('risk_tier', 'unknown').upper()

            lines.append(f"\n{i}. {name} vs {opp}{two_start}")
            lines.append("-" * 40)

            # Point projections
            exp = opt.get('expected_pts', 0)
            floor = opt.get('floor', 0)
            ceiling = opt.get('ceiling', 0)
            lines.append(f"   Points: {exp:.0f} expected [{floor:.0f} floor / {ceiling:.0f} ceiling]")

            # Risk metrics
            disaster = opt.get('disaster_prob', 0)
            blowup = opt.get('blowup_prob', 0)
            risk_adj = opt.get('risk_adjusted', 0)
            lines.append(f"   Risk: {disaster:.0%} disaster (3+ HR), {blowup:.0%} blowup (neg pts)")
            lines.append(f"   Risk-Adjusted Value: {risk_adj:.1f}")

            # Tier and recommendation
            lines.append(f"   Tier: {tier}")
            lines.append(f"   --> {opt.get('recommendation', 'N/A')}")

            # Warnings
            warnings = opt.get('warnings', [])
            if warnings:
                lines.append(f"   Warnings: {'; '.join(warnings[:2])}")

            # Simple baseline comparison
            simple = opt.get('simple_score', 0)
            simple_rec = opt.get('simple_rec', '')
            lines.append(f"   Simple Baseline: {simple:.0f} ({simple_rec})")

        return "\n".join(lines)

    def update_matchup_state(self, my_score: float, opp_score: float):
        """Update matchup state for risk calculations."""
        if self.engine:
            days_remaining = 7 - date.today().weekday()
            self.engine.risk_utility.update_state(my_score, opp_score, days_remaining)

    def record_result(self, player_name: str, points: float, context: StreamingContext = None):
        """Record streaming result for learning."""
        if not self.engine:
            return

        # Update Bayesian projection
        self.engine.projections.update_player(player_name, points)

        # Update threshold history
        self.engine.thresholds.add_observation(points)

        # Update bandit if we have context
        if context:
            self.engine.update_with_result(context, player_name, points)

    def advance_day(self):
        """Call at end of each day."""
        if self.engine:
            self.engine.advance_day()

    def new_week(self):
        """Call at start of new week."""
        if self.engine:
            self.engine.new_week()


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def create_quant_bot(exclusion_list: List[str] = None):
    """Create a bot with quant plugin enabled."""
    from fantasy_bot import FantasyBot, BotConfig

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
    bot.register_plugin(QuantPlugin())

    return bot


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("QUANT PLUGIN DEMO")
    print("=" * 60)

    # Create bot with quant plugin
    bot = create_quant_bot()

    # Get the quant plugin
    quant = bot.plugins.plugins.get('quant')

    if quant:
        # Test evaluation
        print("\nTesting add evaluation...")
        print("-" * 40)

        test_cases = [
            ("Pablo Lopez", "OAK", True, True),   # vs weak team, 2-start
            ("Reese Olson", "NYY", False, False), # @ strong team
            ("Mitchell Parker", "MIA", True, False),  # vs weak team
        ]

        for name, opp, is_home, two_start in test_cases:
            should, value, reason = quant.evaluate_add(
                player_name=name,
                opponent=opp,
                is_home=is_home,
                is_two_start=two_start,
            )

            decision = "ADD" if should else "WAIT"
            loc = "vs" if is_home else "@"
            two = " [2-START]" if two_start else ""

            print(f"\n{name} {loc} {opp}{two}")
            print(f"  Decision: {decision}")
            print(f"  Value: {value:.1f}")
            print(f"  Reason: {reason}")

        # Test ranking with risk analysis
        print("\n" + "=" * 50)
        print("Testing ranking with RISK ANALYSIS...")
        print("-" * 40)

        # Options with pitcher stats for risk calculation
        options = [
            {
                'name': 'Logan Webb',
                'opponent': 'OAK',
                'is_home': True,
                'is_two_start': False,
                'pitcher_stats': {'era': 3.20, 'k_per_9': 7.5, 'hr_per_9': 0.8, 'gb_rate': 0.52, 'fb_rate': 0.28}
            },
            {
                'name': 'Garrett Crochet',
                'opponent': 'OAK',
                'is_home': True,
                'is_two_start': True,
                'pitcher_stats': {'era': 3.50, 'k_per_9': 11.5, 'hr_per_9': 1.0, 'gb_rate': 0.38, 'fb_rate': 0.42}
            },
            {
                'name': 'Streamer X',
                'opponent': 'LAD',
                'is_home': False,
                'is_two_start': False,
                'pitcher_stats': {'era': 4.50, 'k_per_9': 8.0, 'hr_per_9': 1.4, 'gb_rate': 0.40, 'fb_rate': 0.38}
            },
            {
                'name': 'Crochet Risky',
                'opponent': 'NYY',
                'is_home': False,
                'is_two_start': False,
                'pitcher_stats': {'era': 3.50, 'k_per_9': 11.5, 'hr_per_9': 1.0, 'gb_rate': 0.38, 'fb_rate': 0.42}
            },
        ]

        # Get full analysis with risk
        print(quant.get_full_analysis(options))

    # Run daily analysis
    print("\n" + "=" * 50)
    print("Running daily analysis...")
    print("-" * 40)
    print(bot.daily_run())
