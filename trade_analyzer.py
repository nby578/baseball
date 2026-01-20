"""
Trade Analyzer Module for Keeper Fantasy Baseball

Based on kidney exchange theory (Alvin Roth's Nobel Prize-winning work).

KEY INSIGHT: Keeper leagues are inefficient markets because:
1. Owners fail to detect constraint-driven surplus until deadline pressure
2. Multi-party trades unlock value impossible in bilateral exchanges
3. Surplus flows to need, sometimes through intermediaries

THE CONSTRAINT (BLJ X):
- Each team keeps 2 batters + 2 pitchers
- A team's 3rd-best batter/pitcher is a "dying asset" worth $0 if not traded
- BUT teams don't always keep their literal best - they might trade a keeper
  if they get enough surplus value back from another team's dying assets

TRADE SCENARIOS:
1. Clear surplus: Team has 3+ good at position ->dying asset MUST be traded
2. Upgrade via surplus: Trade your #2 keeper + receive someone's dying assets ->net gain
3. Multi-party: A→B→C→A cycles where no bilateral trade works

ALGORITHMS:
- Top Trading Cycles (TTC) - Pareto-efficient matching
- Johnson's Algorithm - Multi-party cycle enumeration
- Position-adjusted VAR - Value Above Replacement with keeper year discounting

Data Sources for Player Values:
- Projections: https://www.fangraphs.com/projections (Steamer, ZiPS)
- ADP: https://www.fantasypros.com/mlb/adp/overall.php
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import math
from collections import defaultdict

# =============================================================================
# CONSTANTS
# =============================================================================

# Keeper rules (BLJ X)
KEEPER_SLOTS_BATTER = 2
KEEPER_SLOTS_PITCHER = 2
TOTAL_KEEPER_SLOTS = KEEPER_SLOTS_BATTER + KEEPER_SLOTS_PITCHER

# Value allocation (traditional 65-35 split)
BATTER_VALUE_SHARE = 0.65
PITCHER_VALUE_SHARE = 0.35

# Age curves (peak at 26-27 for batters, 26-28 for pitchers)
# Factor applied to future year projections
AGE_FACTORS_BATTER = {
    21: 1.15, 22: 1.12, 23: 1.10, 24: 1.08, 25: 1.05,
    26: 1.02, 27: 1.00, 28: 0.97, 29: 0.94, 30: 0.90,
    31: 0.86, 32: 0.82, 33: 0.78, 34: 0.74, 35: 0.70,
}

AGE_FACTORS_PITCHER = {
    21: 1.12, 22: 1.10, 23: 1.08, 24: 1.06, 25: 1.04,
    26: 1.02, 27: 1.00, 28: 0.98, 29: 0.95, 30: 0.90,
    31: 0.85, 32: 0.80, 33: 0.75, 34: 0.70, 35: 0.65,
}

# Keeper year discount rates
YEAR_DISCOUNT = {
    1: 1.00,  # Current year
    2: 0.80,  # Next year
    3: 0.65,  # Year 3
    4: 0.50,  # Year 4+
}

# Replacement level (approximate rank where value = 0)
# In 12-team league keeping 2 each, replacement ~ rank 25
REPLACEMENT_RANK_BATTER = 25
REPLACEMENT_RANK_PITCHER = 25


# =============================================================================
# ENUMS
# =============================================================================

class Position(Enum):
    """Player position category."""
    BATTER = "batter"
    PITCHER = "pitcher"


class SurplusStatus(Enum):
    """Player's status relative to keeper constraints."""
    CORE_KEEPER = "core_keeper"      # Top 2 at position, definitely keeping
    TRADEABLE_KEEPER = "tradeable"   # Could keep, but tradeable for right price
    DYING_ASSET = "dying_asset"      # Can't keep, must trade or lose value
    REPLACEMENT = "replacement"       # Below keeper threshold


class TradeUrgency(Enum):
    """How urgent is it to trade this player?"""
    CRITICAL = "critical"    # Dying asset, deadline approaching
    HIGH = "high"            # Clear surplus, should trade
    MODERATE = "moderate"    # Tradeable keeper, upgrade possible
    LOW = "low"              # No pressure, trade only if great offer


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Player:
    """A player with keeper value assessment."""
    name: str
    team: str  # MLB team
    position: Position
    age: int

    # Current season projected value (z-score or dollar value)
    current_value: float

    # Keeper years remaining (1 = just this year, 2+ = multi-year)
    keeper_years: int = 1

    # Owner's fantasy team
    fantasy_team: str = ""

    # Calculated fields
    keeper_value: float = 0.0
    surplus_status: SurplusStatus = SurplusStatus.REPLACEMENT
    trade_urgency: TradeUrgency = TradeUrgency.LOW

    def __post_init__(self):
        """Calculate keeper value."""
        self.keeper_value = self._calculate_keeper_value()

    def _calculate_keeper_value(self) -> float:
        """
        Calculate total keeper value across all keeper years.

        Formula: Σ(Year_Value × Year_Discount × Age_Factor)
        """
        total_value = 0.0
        age_factors = AGE_FACTORS_BATTER if self.position == Position.BATTER else AGE_FACTORS_PITCHER

        for year in range(1, self.keeper_years + 1):
            year_discount = YEAR_DISCOUNT.get(year, 0.50)
            future_age = self.age + year - 1
            age_factor = age_factors.get(future_age, 0.70 if future_age < 21 else 0.65)

            # Project value decays with age
            projected_value = self.current_value * age_factor
            discounted_value = projected_value * year_discount

            total_value += discounted_value

        return total_value

    @property
    def is_batter(self) -> bool:
        return self.position == Position.BATTER

    @property
    def is_pitcher(self) -> bool:
        return self.position == Position.PITCHER

    @property
    def is_dying_asset(self) -> bool:
        return self.surplus_status == SurplusStatus.DYING_ASSET

    @property
    def is_tradeable(self) -> bool:
        return self.surplus_status in [SurplusStatus.TRADEABLE_KEEPER, SurplusStatus.DYING_ASSET]


@dataclass
class FantasyTeam:
    """A fantasy team's roster for keeper analysis."""
    name: str
    owner: str
    players: List[Player] = field(default_factory=list)

    # Calculated after analysis
    keeper_batters: List[Player] = field(default_factory=list)
    keeper_pitchers: List[Player] = field(default_factory=list)
    surplus_batters: List[Player] = field(default_factory=list)
    surplus_pitchers: List[Player] = field(default_factory=list)

    # Needs assessment
    batter_need_score: float = 0.0   # Higher = more need
    pitcher_need_score: float = 0.0

    def add_player(self, player: Player):
        """Add a player to the roster."""
        player.fantasy_team = self.name
        self.players.append(player)

    @property
    def batters(self) -> List[Player]:
        return [p for p in self.players if p.is_batter]

    @property
    def pitchers(self) -> List[Player]:
        return [p for p in self.players if p.is_pitcher]

    @property
    def dying_assets(self) -> List[Player]:
        return [p for p in self.players if p.is_dying_asset]

    @property
    def total_keeper_value(self) -> float:
        """Value of optimal keepers."""
        return sum(p.keeper_value for p in self.keeper_batters + self.keeper_pitchers)


@dataclass
class TradePackage:
    """A proposed trade between teams."""
    team_a: str
    team_b: str
    team_a_gives: List[Player]
    team_b_gives: List[Player]

    # Value assessment
    team_a_value_change: float = 0.0
    team_b_value_change: float = 0.0
    total_value_created: float = 0.0
    fairness_ratio: float = 0.0  # min/max, closer to 1 = more fair

    # Trade quality
    is_pareto_improving: bool = False  # Both teams benefit
    urgency_score: float = 0.0
    complexity: int = 2  # Number of teams involved

    def __post_init__(self):
        """Calculate trade metrics."""
        self._evaluate()

    def _evaluate(self):
        """Evaluate trade fairness and value."""
        # Value given by each team
        a_gives_value = sum(p.keeper_value for p in self.team_a_gives)
        b_gives_value = sum(p.keeper_value for p in self.team_b_gives)

        # Value received by each team
        # Key insight: dying assets are worth 0 to current owner but full value to receiver
        a_receives_value = sum(p.keeper_value for p in self.team_b_gives)
        b_receives_value = sum(p.keeper_value for p in self.team_a_gives)

        # Adjust for dying asset status - dying assets cost the giver nothing!
        a_actual_cost = sum(p.keeper_value for p in self.team_a_gives if not p.is_dying_asset)
        b_actual_cost = sum(p.keeper_value for p in self.team_b_gives if not p.is_dying_asset)

        # Net value change considering dying asset discount
        self.team_a_value_change = a_receives_value - a_actual_cost
        self.team_b_value_change = b_receives_value - b_actual_cost

        # Total value created (should be positive for good trades)
        self.total_value_created = self.team_a_value_change + self.team_b_value_change

        # Pareto improving if both benefit
        self.is_pareto_improving = (self.team_a_value_change > 0 and
                                    self.team_b_value_change > 0)

        # Fairness ratio
        if self.team_a_value_change > 0 and self.team_b_value_change > 0:
            self.fairness_ratio = min(self.team_a_value_change, self.team_b_value_change) / \
                                  max(self.team_a_value_change, self.team_b_value_change)
        else:
            self.fairness_ratio = 0.0

        # Urgency based on dying assets involved
        dying_count = sum(1 for p in self.team_a_gives + self.team_b_gives if p.is_dying_asset)
        self.urgency_score = dying_count * 0.25


@dataclass
class TradeCycle:
    """A multi-party trade cycle (A→B→C→A)."""
    teams: List[str]  # Teams in cycle order
    transfers: Dict[str, Tuple[str, List[Player]]]  # team -> (receiving_from, players)

    total_value_created: float = 0.0
    is_pareto_improving: bool = False
    team_benefits: Dict[str, float] = field(default_factory=dict)

    @property
    def cycle_length(self) -> int:
        return len(self.teams)

    @property
    def complexity(self) -> int:
        return self.cycle_length


# =============================================================================
# SURPLUS DETECTOR
# =============================================================================

class SurplusDetector:
    """
    Detects surplus and need across all teams.

    Key insight: A player is a dying asset when they would be a keeper
    but the team has too many good players at that position.
    """

    def __init__(self,
                 keeper_batters: int = KEEPER_SLOTS_BATTER,
                 keeper_pitchers: int = KEEPER_SLOTS_PITCHER):
        self.keeper_batters = keeper_batters
        self.keeper_pitchers = keeper_pitchers

    def analyze_team(self, team: FantasyTeam) -> FantasyTeam:
        """
        Analyze a team's roster for surplus/need.

        Returns the team with updated keeper/surplus lists.
        """
        # Sort by keeper value
        batters = sorted(team.batters, key=lambda p: p.keeper_value, reverse=True)
        pitchers = sorted(team.pitchers, key=lambda p: p.keeper_value, reverse=True)

        # Identify keepers vs surplus for batters
        for i, player in enumerate(batters):
            if i < self.keeper_batters:
                # Top N are keepers
                if i == 0:
                    player.surplus_status = SurplusStatus.CORE_KEEPER
                    player.trade_urgency = TradeUrgency.LOW
                else:
                    # #2 keeper is tradeable for right price
                    player.surplus_status = SurplusStatus.TRADEABLE_KEEPER
                    player.trade_urgency = TradeUrgency.MODERATE
                team.keeper_batters.append(player)
            elif player.keeper_value > 0:
                # Has value but can't keep - dying asset!
                player.surplus_status = SurplusStatus.DYING_ASSET
                player.trade_urgency = TradeUrgency.CRITICAL
                team.surplus_batters.append(player)
            else:
                player.surplus_status = SurplusStatus.REPLACEMENT
                player.trade_urgency = TradeUrgency.LOW

        # Same for pitchers
        for i, player in enumerate(pitchers):
            if i < self.keeper_pitchers:
                if i == 0:
                    player.surplus_status = SurplusStatus.CORE_KEEPER
                    player.trade_urgency = TradeUrgency.LOW
                else:
                    player.surplus_status = SurplusStatus.TRADEABLE_KEEPER
                    player.trade_urgency = TradeUrgency.MODERATE
                team.keeper_pitchers.append(player)
            elif player.keeper_value > 0:
                player.surplus_status = SurplusStatus.DYING_ASSET
                player.trade_urgency = TradeUrgency.CRITICAL
                team.surplus_pitchers.append(player)
            else:
                player.surplus_status = SurplusStatus.REPLACEMENT
                player.trade_urgency = TradeUrgency.LOW

        # Calculate need scores
        # Need = how much upgrading the #2 keeper would help
        if len(team.keeper_batters) >= 2:
            # Gap between #1 and #2 indicates upgrade potential
            gap = team.keeper_batters[0].keeper_value - team.keeper_batters[1].keeper_value
            team.batter_need_score = gap / max(1, team.keeper_batters[0].keeper_value)
        else:
            team.batter_need_score = 1.0  # Desperate need

        if len(team.keeper_pitchers) >= 2:
            gap = team.keeper_pitchers[0].keeper_value - team.keeper_pitchers[1].keeper_value
            team.pitcher_need_score = gap / max(1, team.keeper_pitchers[0].keeper_value)
        else:
            team.pitcher_need_score = 1.0

        return team

    def analyze_league(self, teams: List[FantasyTeam]) -> List[FantasyTeam]:
        """Analyze all teams in the league."""
        return [self.analyze_team(team) for team in teams]

    def get_all_dying_assets(self, teams: List[FantasyTeam]) -> List[Player]:
        """Get all dying assets across the league."""
        dying = []
        for team in teams:
            dying.extend(team.dying_assets)
        return sorted(dying, key=lambda p: p.keeper_value, reverse=True)

    def get_surplus_summary(self, teams: List[FantasyTeam]) -> Dict[str, Dict]:
        """Summarize surplus/need across all teams."""
        summary = {}
        for team in teams:
            summary[team.name] = {
                'surplus_batters': [p.name for p in team.surplus_batters],
                'surplus_pitchers': [p.name for p in team.surplus_pitchers],
                'surplus_batter_value': sum(p.keeper_value for p in team.surplus_batters),
                'surplus_pitcher_value': sum(p.keeper_value for p in team.surplus_pitchers),
                'batter_need': team.batter_need_score,
                'pitcher_need': team.pitcher_need_score,
                'total_dying_value': sum(p.keeper_value for p in team.dying_assets),
            }
        return summary


# =============================================================================
# TRADE FINDER (Bilateral)
# =============================================================================

class TradeFinder:
    """
    Finds mutually beneficial bilateral trades.

    Looks for matches where:
    1. Team A's surplus fills Team B's need
    2. Team B's surplus fills Team A's need
    3. Both teams end up better off
    """

    def __init__(self, min_value_gain: float = 0.5):
        """
        Args:
            min_value_gain: Minimum keeper value gain for trade to be worthwhile
        """
        self.min_value_gain = min_value_gain

    def find_bilateral_trades(self,
                              teams: List[FantasyTeam],
                              include_tradeable_keepers: bool = True) -> List[TradePackage]:
        """
        Find all Pareto-improving bilateral trades.

        Args:
            teams: List of analyzed teams
            include_tradeable_keepers: Whether to consider trading #2 keepers
        """
        trades = []

        for i, team_a in enumerate(teams):
            for team_b in teams[i+1:]:
                # Find trades between these two teams
                team_trades = self._find_trades_between(
                    team_a, team_b, include_tradeable_keepers
                )
                trades.extend(team_trades)

        # Sort by total value created
        trades.sort(key=lambda t: t.total_value_created, reverse=True)

        return trades

    def _find_trades_between(self,
                             team_a: FantasyTeam,
                             team_b: FantasyTeam,
                             include_tradeable: bool) -> List[TradePackage]:
        """Find all beneficial trades between two teams."""
        trades = []

        # Get tradeable players
        a_available = self._get_tradeable_players(team_a, include_tradeable)
        b_available = self._get_tradeable_players(team_b, include_tradeable)

        # Try all 1-for-1 combinations
        for a_player in a_available:
            for b_player in b_available:
                trade = self._evaluate_trade(team_a, team_b, [a_player], [b_player])
                if trade and trade.is_pareto_improving:
                    trades.append(trade)

        # Try 2-for-1 combinations (surplus player + sweetener for star)
        for a_player in a_available:
            for b1 in b_available:
                for b2 in b_available:
                    if b1.name == b2.name:
                        continue
                    trade = self._evaluate_trade(team_a, team_b, [a_player], [b1, b2])
                    if trade and trade.is_pareto_improving:
                        trades.append(trade)

        for b_player in b_available:
            for a1 in a_available:
                for a2 in a_available:
                    if a1.name == a2.name:
                        continue
                    trade = self._evaluate_trade(team_a, team_b, [a1, a2], [b_player])
                    if trade and trade.is_pareto_improving:
                        trades.append(trade)

        return trades

    def _get_tradeable_players(self, team: FantasyTeam, include_tradeable: bool) -> List[Player]:
        """Get players available for trade."""
        available = list(team.surplus_batters) + list(team.surplus_pitchers)

        if include_tradeable:
            # Add #2 keepers (tradeable for right price)
            for keeper in team.keeper_batters + team.keeper_pitchers:
                if keeper.surplus_status == SurplusStatus.TRADEABLE_KEEPER:
                    available.append(keeper)

        return available

    def _evaluate_trade(self,
                        team_a: FantasyTeam,
                        team_b: FantasyTeam,
                        a_gives: List[Player],
                        b_gives: List[Player]) -> Optional[TradePackage]:
        """Evaluate a specific trade."""
        # Check position balance - does this fill needs?
        a_gets_batters = sum(1 for p in b_gives if p.is_batter)
        a_gets_pitchers = sum(1 for p in b_gives if p.is_pitcher)
        b_gets_batters = sum(1 for p in a_gives if p.is_batter)
        b_gets_pitchers = sum(1 for p in a_gives if p.is_pitcher)

        # Create trade package
        trade = TradePackage(
            team_a=team_a.name,
            team_b=team_b.name,
            team_a_gives=a_gives,
            team_b_gives=b_gives,
        )

        # Check if both sides gain enough
        if trade.team_a_value_change < self.min_value_gain:
            return None
        if trade.team_b_value_change < self.min_value_gain:
            return None

        return trade


# =============================================================================
# CYCLE FINDER (Multi-party trades)
# =============================================================================

class CycleFinder:
    """
    Finds multi-party trade cycles using graph algorithms.

    Based on Johnson's algorithm for finding all elementary circuits.

    Example: A has surplus batter, needs pitcher
            B has surplus pitcher, needs catcher (proxy for another position)
            C has surplus "catcher", needs batter
            ->3-way cycle: A→C→B→A (A gives batter to C, C gives to B, B gives pitcher to A)
    """

    def __init__(self, max_cycle_length: int = 4):
        """
        Args:
            max_cycle_length: Maximum teams in a cycle (3-4 recommended)
        """
        self.max_cycle_length = max_cycle_length

    def build_preference_graph(self, teams: List[FantasyTeam]) -> Dict[str, List[str]]:
        """
        Build directed graph where edge A→B means A wants something from B.

        An edge exists if:
        - B has a dying asset that would improve A's keeper value
        - A has something B might want in return
        """
        graph = defaultdict(list)

        for team_a in teams:
            for team_b in teams:
                if team_a.name == team_b.name:
                    continue

                # Does B have a dying asset A wants?
                b_surplus_batters = team_b.surplus_batters
                b_surplus_pitchers = team_b.surplus_pitchers

                # Would A benefit from B's surplus?
                a_wants_batter = (team_a.batter_need_score > 0.2 and
                                  any(p.keeper_value > 5 for p in b_surplus_batters))
                a_wants_pitcher = (team_a.pitcher_need_score > 0.2 and
                                   any(p.keeper_value > 5 for p in b_surplus_pitchers))

                # Does A have something to offer?
                a_has_surplus = (team_a.surplus_batters or team_a.surplus_pitchers or
                                any(p.surplus_status == SurplusStatus.TRADEABLE_KEEPER
                                    for p in team_a.players))

                if (a_wants_batter or a_wants_pitcher) and a_has_surplus:
                    graph[team_a.name].append(team_b.name)

        return dict(graph)

    def find_cycles(self,
                    teams: List[FantasyTeam],
                    graph: Dict[str, List[str]] = None) -> List[List[str]]:
        """
        Find all simple cycles in the preference graph.

        Uses DFS-based cycle enumeration.
        """
        if graph is None:
            graph = self.build_preference_graph(teams)

        all_cycles = []
        team_names = [t.name for t in teams]

        # Find cycles starting from each node
        for start in team_names:
            cycles = self._find_cycles_from(start, graph, team_names)
            all_cycles.extend(cycles)

        # Remove duplicates (same cycle starting from different points)
        unique_cycles = self._deduplicate_cycles(all_cycles)

        return unique_cycles

    def _find_cycles_from(self,
                          start: str,
                          graph: Dict[str, List[str]],
                          all_nodes: List[str]) -> List[List[str]]:
        """Find all cycles starting from a given node."""
        cycles = []

        def dfs(path: List[str], visited: Set[str]):
            current = path[-1]

            if len(path) > self.max_cycle_length:
                return

            for neighbor in graph.get(current, []):
                if neighbor == start and len(path) >= 2:
                    # Found a cycle back to start
                    cycles.append(path.copy())
                elif neighbor not in visited and neighbor > start:
                    # Continue DFS (neighbor > start prevents duplicates)
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(path, visited)
                    path.pop()
                    visited.remove(neighbor)

        dfs([start], {start})
        return cycles

    def _deduplicate_cycles(self, cycles: List[List[str]]) -> List[List[str]]:
        """Remove duplicate cycles (same teams, different starting point)."""
        seen = set()
        unique = []

        for cycle in cycles:
            # Normalize: rotate to start with smallest team name
            min_idx = cycle.index(min(cycle))
            normalized = tuple(cycle[min_idx:] + cycle[:min_idx])

            if normalized not in seen:
                seen.add(normalized)
                unique.append(cycle)

        return unique

    def evaluate_cycle(self,
                       cycle: List[str],
                       teams: List[FantasyTeam]) -> Optional[TradeCycle]:
        """
        Evaluate if a cycle represents a viable multi-party trade.

        For a cycle to work:
        - Each team must give to the next team
        - Each team must receive from the previous team
        - All teams must benefit
        """
        team_map = {t.name: t for t in teams}
        transfers = {}
        team_benefits = {}

        n = len(cycle)

        for i, team_name in enumerate(cycle):
            team = team_map[team_name]
            next_team_name = cycle[(i + 1) % n]
            next_team = team_map[next_team_name]
            prev_team_name = cycle[(i - 1) % n]
            prev_team = team_map[prev_team_name]

            # What does this team give to next team?
            # Give dying assets that next team needs
            gives = self._find_best_gift(team, next_team)

            # What does this team receive from prev team?
            receives = self._find_best_gift(prev_team, team)

            if not gives or not receives:
                return None  # Cycle doesn't work

            transfers[team_name] = (prev_team_name, receives)

            # Calculate benefit
            gives_value = sum(p.keeper_value for p in gives if not p.is_dying_asset)
            receives_value = sum(p.keeper_value for p in receives)
            team_benefits[team_name] = receives_value - gives_value

        # Check if all teams benefit
        if not all(v > 0 for v in team_benefits.values()):
            return None

        total_value = sum(team_benefits.values())

        return TradeCycle(
            teams=cycle,
            transfers=transfers,
            total_value_created=total_value,
            is_pareto_improving=True,
            team_benefits=team_benefits,
        )

    def _find_best_gift(self,
                        giver: FantasyTeam,
                        receiver: FantasyTeam) -> List[Player]:
        """Find the best player(s) giver can give to receiver."""
        # Prefer dying assets (cost giver nothing)
        candidates = []

        # Check if receiver needs batters
        if receiver.batter_need_score > 0.2:
            candidates.extend(giver.surplus_batters)

        # Check if receiver needs pitchers
        if receiver.pitcher_need_score > 0.2:
            candidates.extend(giver.surplus_pitchers)

        if candidates:
            # Return highest value dying asset
            best = max(candidates, key=lambda p: p.keeper_value)
            return [best]

        return []


# =============================================================================
# TRADE SCORER
# =============================================================================

class TradeScorer:
    """
    Scores and ranks trade opportunities.

    Weights from research:
    - Total value created: 35%
    - Fairness between parties: 25%
    - Urgency of dying assets: 15%
    - Trade simplicity: 15%
    - Position fit: 10%
    """

    WEIGHT_VALUE = 0.35
    WEIGHT_FAIRNESS = 0.25
    WEIGHT_URGENCY = 0.15
    WEIGHT_SIMPLICITY = 0.15
    WEIGHT_FIT = 0.10

    def score_trade(self, trade: TradePackage) -> float:
        """Calculate composite trade score."""
        # Value score (normalize to 0-100)
        value_score = min(100, trade.total_value_created * 10)

        # Fairness score (0-100)
        fairness_score = trade.fairness_ratio * 100

        # Urgency score (dying assets involved)
        urgency_score = trade.urgency_score * 100

        # Simplicity score (fewer pieces = better)
        pieces = len(trade.team_a_gives) + len(trade.team_b_gives)
        simplicity_score = max(0, 100 - (pieces - 2) * 25)

        # Position fit score (trades that fill actual needs)
        fit_score = 75  # Default, would need more context to calculate

        composite = (
            value_score * self.WEIGHT_VALUE +
            fairness_score * self.WEIGHT_FAIRNESS +
            urgency_score * self.WEIGHT_URGENCY +
            simplicity_score * self.WEIGHT_SIMPLICITY +
            fit_score * self.WEIGHT_FIT
        )

        return composite

    def rank_trades(self, trades: List[TradePackage]) -> List[Tuple[TradePackage, float]]:
        """Rank trades by composite score."""
        scored = [(trade, self.score_trade(trade)) for trade in trades]
        return sorted(scored, key=lambda x: x[1], reverse=True)


# =============================================================================
# BEHAVIORAL FRAMING
# =============================================================================

class NegotiationFramer:
    """
    Generates negotiation talking points using behavioral insights.

    Key biases to exploit:
    - Endowment effect: People overvalue what they own by 2-3x
    - Loss aversion: Losses feel 2x worse than equivalent gains
    - Anchoring: First offer explains 50-85% of outcome variance
    - Deadline pressure: Increases cooperation when moderate
    """

    @staticmethod
    def frame_proposal(trade: TradePackage,
                       target_team: str,
                       deadline_days: int = 7) -> Dict[str, any]:
        """
        Generate framing for a trade proposal.

        Args:
            trade: The proposed trade
            target_team: Which team you're pitching to
            deadline_days: Days until keeper deadline
        """
        # Determine what target team receives
        if target_team == trade.team_a:
            receives = trade.team_b_gives
            gives = trade.team_a_gives
            gain = trade.team_a_value_change
        else:
            receives = trade.team_a_gives
            gives = trade.team_b_gives
            gain = trade.team_b_value_change

        # Frame emphasizing GAINS not losses
        talking_points = []

        # Lead with what they GET
        for player in receives:
            talking_points.append(
                f"You're acquiring {player.name} - "
                f"projected for {player.current_value:.1f} value with "
                f"{player.keeper_years} keeper years remaining"
            )

        # Minimize what they give
        for player in gives:
            if player.is_dying_asset:
                talking_points.append(
                    f"{player.name} can't make your keeper roster anyway - "
                    f"get value instead of losing them for nothing"
                )
            else:
                talking_points.append(
                    f"{player.name} is a solid piece but you're upgrading overall"
                )

        # Deadline urgency (if dying assets involved)
        if any(p.is_dying_asset for p in gives):
            if deadline_days <= 3:
                urgency = "CRITICAL - deadline approaching, value expires soon"
            elif deadline_days <= 7:
                urgency = "Moderate - should finalize within the week"
            else:
                urgency = "Low - but early action secures best options"
        else:
            urgency = "Flexible timing"

        # Anchoring - suggest slightly better terms for yourself
        anchor_adjustment = 1.15  # Ask for 15% more than fair

        return {
            'target_team': target_team,
            'talking_points': talking_points,
            'value_gain': gain,
            'urgency': urgency,
            'deadline_days': deadline_days,
            'anchor_adjustment': anchor_adjustment,
            'key_message': (
                f"This trade adds {gain:.1f} keeper value to your team. "
                f"You're upgrading your keeper pool while I'm taking on roster depth."
            ),
        }

    @staticmethod
    def counter_endowment_effect(player: Player) -> str:
        """Generate talking points to counter endowment bias."""
        return (
            f"I know {player.name} has been good for you, but the projections "
            f"show {player.current_value:.1f} value. "
            f"That's what the market says - I'm offering fair value."
        )

    @staticmethod
    def deadline_pressure_message(days_remaining: int) -> str:
        """Generate deadline pressure message."""
        if days_remaining <= 2:
            return (
                "The keeper deadline is almost here. After that, any surplus "
                "players are gone for nothing. Let's finalize this today."
            )
        elif days_remaining <= 5:
            return (
                "We have a few days until keepers lock. This is the window "
                "to maximize value before the deadline forces our hands."
            )
        else:
            return (
                "No rush, but early trades give both of us time to evaluate "
                "our improved rosters and maybe make additional moves."
            )


# =============================================================================
# MAIN TRADE ANALYZER
# =============================================================================

class TradeAnalyzer:
    """
    Main interface for trade analysis.

    Combines:
    - Surplus detection
    - Bilateral trade finding
    - Multi-party cycle finding
    - Trade scoring
    - Negotiation framing
    """

    def __init__(self,
                 keeper_batters: int = KEEPER_SLOTS_BATTER,
                 keeper_pitchers: int = KEEPER_SLOTS_PITCHER,
                 max_cycle_length: int = 4):
        self.surplus_detector = SurplusDetector(keeper_batters, keeper_pitchers)
        self.trade_finder = TradeFinder()
        self.cycle_finder = CycleFinder(max_cycle_length)
        self.scorer = TradeScorer()
        self.framer = NegotiationFramer()

    def analyze_league(self, teams: List[FantasyTeam]) -> Dict[str, any]:
        """
        Complete league trade analysis.

        Returns comprehensive analysis including:
        - Surplus/need by team
        - Best bilateral trades
        - Multi-party opportunities
        - Negotiation recommendations
        """
        # Step 1: Analyze each team
        analyzed_teams = self.surplus_detector.analyze_league(teams)

        # Step 2: Find bilateral trades
        bilateral_trades = self.trade_finder.find_bilateral_trades(analyzed_teams)

        # Step 3: Find multi-party cycles
        graph = self.cycle_finder.build_preference_graph(analyzed_teams)
        cycles = self.cycle_finder.find_cycles(analyzed_teams, graph)

        # Evaluate cycles
        viable_cycles = []
        for cycle in cycles:
            evaluated = self.cycle_finder.evaluate_cycle(cycle, analyzed_teams)
            if evaluated:
                viable_cycles.append(evaluated)

        # Step 4: Score and rank trades
        scored_trades = self.scorer.rank_trades(bilateral_trades)

        # Step 5: Generate summary
        dying_assets = self.surplus_detector.get_all_dying_assets(analyzed_teams)
        surplus_summary = self.surplus_detector.get_surplus_summary(analyzed_teams)

        return {
            'teams': analyzed_teams,
            'surplus_summary': surplus_summary,
            'dying_assets': dying_assets,
            'bilateral_trades': scored_trades[:20],  # Top 20
            'multi_party_cycles': viable_cycles,
            'preference_graph': graph,
            'total_dying_value': sum(p.keeper_value for p in dying_assets),
        }

    def recommend_for_team(self,
                           team_name: str,
                           analysis: Dict) -> Dict[str, any]:
        """
        Get trade recommendations for a specific team.
        """
        # Find team
        team = next((t for t in analysis['teams'] if t.name == team_name), None)
        if not team:
            return {'error': f'Team {team_name} not found'}

        # Filter trades involving this team
        relevant_trades = [
            (trade, score) for trade, score in analysis['bilateral_trades']
            if trade.team_a == team_name or trade.team_b == team_name
        ]

        # Filter cycles involving this team
        relevant_cycles = [
            cycle for cycle in analysis['multi_party_cycles']
            if team_name in cycle.teams
        ]

        # Get framing for top trade
        top_trade = None
        framing = None
        if relevant_trades:
            top_trade, score = relevant_trades[0]
            other_team = top_trade.team_b if top_trade.team_a == team_name else top_trade.team_a
            framing = self.framer.frame_proposal(top_trade, other_team)

        return {
            'team': team_name,
            'dying_assets': [p.name for p in team.dying_assets],
            'dying_asset_value': sum(p.keeper_value for p in team.dying_assets),
            'keeper_batters': [p.name for p in team.keeper_batters],
            'keeper_pitchers': [p.name for p in team.keeper_pitchers],
            'batter_need': team.batter_need_score,
            'pitcher_need': team.pitcher_need_score,
            'recommended_trades': relevant_trades[:5],
            'multi_party_options': relevant_cycles,
            'top_trade_framing': framing,
        }

    def format_analysis(self, analysis: Dict) -> str:
        """Format analysis as readable report."""
        lines = []
        lines.append("=" * 70)
        lines.append("KEEPER LEAGUE TRADE ANALYSIS")
        lines.append("=" * 70)
        lines.append("")

        # Dying assets summary
        lines.append("DYING ASSETS (Must trade or lose value)")
        lines.append("-" * 40)
        total_dying = analysis['total_dying_value']
        lines.append(f"Total dying asset value in league: {total_dying:.1f}")
        lines.append("")

        for player in analysis['dying_assets'][:10]:
            lines.append(f"  {player.name} ({player.fantasy_team}) - "
                        f"Value: {player.keeper_value:.1f}, "
                        f"Age: {player.age}, "
                        f"Years: {player.keeper_years}")

        if len(analysis['dying_assets']) > 10:
            lines.append(f"  ... and {len(analysis['dying_assets']) - 10} more")

        lines.append("")

        # Team surplus summary
        lines.append("TEAM SURPLUS/NEED SUMMARY")
        lines.append("-" * 40)

        for team_name, summary in analysis['surplus_summary'].items():
            lines.append(f"\n{team_name}:")
            if summary['surplus_batters']:
                lines.append(f"  Surplus Batters: {', '.join(summary['surplus_batters'])} "
                           f"(value: {summary['surplus_batter_value']:.1f})")
            if summary['surplus_pitchers']:
                lines.append(f"  Surplus Pitchers: {', '.join(summary['surplus_pitchers'])} "
                           f"(value: {summary['surplus_pitcher_value']:.1f})")
            lines.append(f"  Batter Need: {summary['batter_need']:.2f}, "
                        f"Pitcher Need: {summary['pitcher_need']:.2f}")

        lines.append("")

        # Top trades
        lines.append("TOP BILATERAL TRADES")
        lines.append("-" * 40)

        for i, (trade, score) in enumerate(analysis['bilateral_trades'][:10], 1):
            a_gives = ', '.join(p.name for p in trade.team_a_gives)
            b_gives = ', '.join(p.name for p in trade.team_b_gives)
            lines.append(f"\n{i}. {trade.team_a} <-> {trade.team_b} (Score: {score:.1f})")
            lines.append(f"   {trade.team_a} gives: {a_gives}")
            lines.append(f"   {trade.team_b} gives: {b_gives}")
            lines.append(f"   Value created: {trade.total_value_created:.1f}, "
                        f"Fairness: {trade.fairness_ratio:.2f}")

        lines.append("")

        # Multi-party cycles
        if analysis['multi_party_cycles']:
            lines.append("MULTI-PARTY TRADE CYCLES")
            lines.append("-" * 40)

            for i, cycle in enumerate(analysis['multi_party_cycles'][:5], 1):
                cycle_str = ' ->'.join(cycle.teams) + ' ->' + cycle.teams[0]
                lines.append(f"\n{i}. {cycle_str}")
                lines.append(f"   Total value created: {cycle.total_value_created:.1f}")
                for team, benefit in cycle.team_benefits.items():
                    lines.append(f"   {team} gains: {benefit:.1f}")

        lines.append("")
        lines.append("=" * 70)

        return '\n'.join(lines)


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demonstrate the trade analyzer."""
    print("=" * 70)
    print("TRADE ANALYZER DEMO")
    print("=" * 70)
    print()

    # Create sample league
    teams = []

    # Team 1: Has 3 elite batters (surplus batter), weak pitching
    team1 = FantasyTeam(name="Bat Heavy", owner="Owner 1")
    team1.add_player(Player("Elite Batter 1", "NYY", Position.BATTER, 26, 45.0, 3))
    team1.add_player(Player("Elite Batter 2", "LAD", Position.BATTER, 24, 40.0, 4))
    team1.add_player(Player("Elite Batter 3", "ATL", Position.BATTER, 27, 35.0, 2))  # DYING ASSET
    team1.add_player(Player("Decent Pitcher 1", "HOU", Position.PITCHER, 29, 20.0, 2))
    team1.add_player(Player("Weak Pitcher 2", "TEX", Position.PITCHER, 31, 10.0, 1))
    teams.append(team1)

    # Team 2: Has 3 elite pitchers (surplus pitcher), weak batting
    team2 = FantasyTeam(name="Arm Heavy", owner="Owner 2")
    team2.add_player(Player("Decent Batter 1", "BOS", Position.BATTER, 28, 22.0, 2))
    team2.add_player(Player("Weak Batter 2", "TB", Position.BATTER, 30, 12.0, 1))
    team2.add_player(Player("Elite Pitcher 1", "PHI", Position.PITCHER, 25, 42.0, 4))
    team2.add_player(Player("Elite Pitcher 2", "SD", Position.PITCHER, 27, 38.0, 3))
    team2.add_player(Player("Elite Pitcher 3", "SEA", Position.PITCHER, 26, 32.0, 3))  # DYING ASSET
    teams.append(team2)

    # Team 3: Balanced but aging - trade potential
    team3 = FantasyTeam(name="Balanced", owner="Owner 3")
    team3.add_player(Player("Good Batter 1", "CLE", Position.BATTER, 32, 28.0, 2))
    team3.add_player(Player("Good Batter 2", "MIN", Position.BATTER, 25, 25.0, 3))
    team3.add_player(Player("Good Pitcher 1", "MIL", Position.PITCHER, 28, 26.0, 2))
    team3.add_player(Player("Good Pitcher 2", "ARI", Position.PITCHER, 24, 24.0, 4))
    teams.append(team3)

    # Team 4: Young rebuild - needs now, has future
    team4 = FantasyTeam(name="Rebuilder", owner="Owner 4")
    team4.add_player(Player("Young Stud Batter", "DET", Position.BATTER, 22, 30.0, 5))
    team4.add_player(Player("Prospect Batter", "PIT", Position.BATTER, 23, 18.0, 5))
    team4.add_player(Player("Young Arm", "BAL", Position.PITCHER, 23, 28.0, 5))
    team4.add_player(Player("Prospect Pitcher", "KC", Position.PITCHER, 22, 15.0, 5))
    teams.append(team4)

    # Run analysis
    analyzer = TradeAnalyzer()
    analysis = analyzer.analyze_league(teams)

    # Print report
    print(analyzer.format_analysis(analysis))

    # Recommendations for Team 1
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS FOR 'Bat Heavy'")
    print("=" * 70)

    recs = analyzer.recommend_for_team("Bat Heavy", analysis)

    print(f"\nDying Assets: {recs['dying_assets']}")
    print(f"Dying Asset Value: {recs['dying_asset_value']:.1f}")
    print(f"Keeper Batters: {recs['keeper_batters']}")
    print(f"Keeper Pitchers: {recs['keeper_pitchers']}")
    print(f"Batter Need Score: {recs['batter_need']:.2f}")
    print(f"Pitcher Need Score: {recs['pitcher_need']:.2f}")

    if recs['top_trade_framing']:
        print("\nTop Trade Framing:")
        framing = recs['top_trade_framing']
        print(f"  Target: {framing['target_team']}")
        print(f"  Urgency: {framing['urgency']}")
        print(f"  Key Message: {framing['key_message']}")
        print("\n  Talking Points:")
        for point in framing['talking_points']:
            print(f"    - {point}")

    # Test negotiation framing
    print("\n" + "=" * 70)
    print("NEGOTIATION TACTICS")
    print("=" * 70)

    print("\nDeadline Pressure (3 days):")
    print(f"  {NegotiationFramer.deadline_pressure_message(3)}")

    print("\nDeadline Pressure (7 days):")
    print(f"  {NegotiationFramer.deadline_pressure_message(7)}")

    # Show dying asset value insight
    print("\n" + "=" * 70)
    print("KEY INSIGHT: DYING ASSET ECONOMICS")
    print("=" * 70)

    dying = analysis['dying_assets']
    print(f"\nTotal dying asset value in league: {analysis['total_dying_value']:.1f}")
    print("\nThis value will be LOST if not traded before deadline!")
    print("Every team with dying assets is motivated to deal.")
    print("\nYour edge: Identify which teams have surplus at positions you need,")
    print("then propose trades where their dying asset fills your need.")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo()
