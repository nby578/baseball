"""
Matchup Evaluator Module for Fantasy Baseball Streaming

VALIDATED WEIGHTS (Jan 2026 Backtest - 415 picks analyzed):

PITCHER EXPERIENCE (80% weight) - THE #1 FACTOR:
- IP Sample: Best predictor of outcomes (r=0.295)
- High IP (120+): 10.8 pts avg, can absorb HR through volume
- Mid IP (80-120): 8.0 pts avg
- Low IP (<80): 5.7 pts avg - AVOID regardless of matchup
- Experience enables longer outings (4.9 IP vs 2.8 IP) = more cushion

PITCHER QUALITY (10% weight):
- K-BB%: Secondary factor, minimal impact in isolation
- Only matters as tiebreaker between same-experience pitchers

MATCHUP FACTORS (10% weight):
- Opponent + Park combined explain only ~1 pt difference
- Use ONLY as tiebreaker when pitcher experience is equal
- Exception: Hard filter vs elite power (LAD/NYY) at HR parks

KEY FINDINGS:
- IP 120+ vs Yankees: 13.8 pts (proven pitcher dominates)
- IP <80 vs Pirates: 6.4 pts (easy matchup can't save bad pitcher)
- Matchup effect for high IP pitchers: ~0.7 pts (negligible)
- Matchup effect for low IP pitchers: ~2.0 pts (still not enough)

DECISION MATRIX:
| IP Sample  | vs Easy | vs Hard | Action           |
|------------|---------|---------|------------------|
| < 80       | AVOID   | AVOID   | Never stream     |
| 80-100     | OK      | AVOID   | Only vs easy     |
| 100-120    | GOOD    | OK      | Prefer easy      |
| 120+       | GREAT   | GOOD    | Always stream    |

HR MITIGATION EFFECT:
- High IP pitchers give up MORE HR (0.67/start) but still score 8.7 pts
- Extra innings (4.9 vs 2.8) = +10.5 pts baseline cushion
- They survive HR because they've already banked value

Expected Points Formula (BLJ X):
E[Points] = (K × 2) + (IP × 5) - (BB × 3) - (HR × 13)

Data Sources:
- Park Factors: https://baseballsavant.mlb.com/leaderboard/statcast-park-factors
- Team Stats: https://www.fangraphs.com/leaders
- Catcher Framing: https://baseballsavant.mlb.com/catcher_framing
- Weather/HRFI: http://homerunforecast.com
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math

# =============================================================================
# BLJ X SCORING CONSTANTS
# =============================================================================

class Scoring:
    """BLJ X league scoring constants."""
    IP = 5.0
    K = 2.0
    BB = -3.0
    HR = -13.0  # THE KILLER - one HR erases 2.5 clean innings
    HIT = -1.0  # Approximate

    # Batter scoring (for reference)
    AB = -1.0
    H = 5.6
    DOUBLE = 2.9  # Bonus
    TRIPLE = 5.7  # Bonus
    HOME_RUN = 9.4  # Bonus
    WALK = 3.0
    SB = 1.9
    CS = -2.8


# =============================================================================
# VALIDATED PARK FACTORS (2023-2025 Baseball Savant)
# Source: https://baseballsavant.mlb.com/leaderboard/statcast-park-factors
# Last Updated: January 2026
# =============================================================================

PARK_HR_FACTORS = {
    # DANGER ZONE - Avoid for streaming
    'LAD': 127,  # Dodger Stadium - THE WORST
    'CIN': 123,  # Great American Ball Park
    'NYY': 119,  # Yankee Stadium - short RF porch
    'PHI': 114,  # Citizens Bank Park
    'LAA': 113,  # Angel Stadium

    # MODERATE RISK - Acceptable with good matchup
    'COL': 106,  # Coors Field - NOT as bad as myth! Humidor works
    'BAL': 105,  # Oriole Park
    'TEX': 104,  # Globe Life Field (roof helps)
    'TOR': 103,  # Rogers Centre
    'CHC': 101,  # Wrigley - CHECK WIND DAILY
    'ATL': 100,  # Truist Park - Neutral
    'MIL': 100,  # American Family Field
    'ARI': 99,   # Chase Field (humidor installed)
    'HOU': 98,   # Minute Maid Park
    'NYM': 97,   # Citi Field
    'MIN': 96,   # Target Field
    'WSH': 95,   # Nationals Park
    'STL': 94,   # Busch Stadium

    # FAVORABLE - Good for streaming
    'BOS': 93,   # Fenway - tricky dimensions favor doubles
    'CHW': 92,   # Guaranteed Rate Field
    'DET': 91,   # Comerica Park - deep CF
    'TB': 90,    # Tropicana Field - dome
    'KC': 89,    # Kauffman Stadium - deep alleys
    'SEA': 89,   # T-Mobile Park - marine layer
    'CLE': 88,   # Progressive Field
    'SD': 87,    # Petco Park - marine layer
    'MIA': 85,   # loanDepot Park
    'SF': 82,    # Oracle Park - marine layer, triples alley
    'OAK': 80,   # Oakland Coliseum - foul territory
    'PIT': 76,   # PNC Park - SAFEST
}

# Park K factors (affects strikeout expectations)
PARK_K_FACTORS = {
    'SEA': 109, 'MIA': 106, 'SD': 105, 'NYY': 107, 'TB': 104,
    'ARI': 103, 'HOU': 102, 'SF': 101, 'CIN': 101, 'TEX': 100,
    'ATL': 100, 'PHI': 100, 'LAD': 100, 'MIL': 99, 'BAL': 99,
    'BOS': 98, 'NYM': 98, 'TOR': 98, 'MIN': 97, 'STL': 97,
    'WSH': 96, 'CHW': 96, 'DET': 95, 'KC': 95, 'CLE': 94,
    'PIT': 93, 'LAA': 92, 'CHC': 91, 'OAK': 90, 'COL': 89,
}


# =============================================================================
# TEAM OFFENSIVE PROFILES (Update weekly during season)
# Source: https://www.fangraphs.com/leaders
# =============================================================================

# Team K% - Higher = more exploitable (easier to strike out)
TEAM_K_PCT = {
    # BEST MATCHUPS (High K%)
    'OAK': 0.270, 'CHW': 0.265, 'DET': 0.255, 'MIA': 0.250, 'COL': 0.248,
    'ARI': 0.245, 'PIT': 0.242, 'WSH': 0.240, 'LAA': 0.238, 'TEX': 0.235,
    # MODERATE
    'TB': 0.232, 'CIN': 0.230, 'NYM': 0.228, 'SF': 0.225, 'MIN': 0.222,
    'CHC': 0.220, 'STL': 0.218, 'TOR': 0.215, 'BAL': 0.212, 'MIL': 0.210,
    'BOS': 0.208, 'SEA': 0.205, 'ATL': 0.202, 'SD': 0.200, 'KC': 0.198,
    # WORST MATCHUPS (Low K%) - Hard to strike out
    'PHI': 0.195, 'CLE': 0.192, 'HOU': 0.190, 'NYY': 0.188, 'LAD': 0.180,
}

# Team ISO (Isolated Power = SLG - AVG) - Lower = safer
TEAM_ISO = {
    # HIGH RISK - Power-heavy lineups
    'LAD': 0.205, 'NYY': 0.198, 'ATL': 0.190, 'PHI': 0.188, 'BAL': 0.185,
    'HOU': 0.182, 'SEA': 0.180, 'TEX': 0.178, 'SD': 0.175, 'MIN': 0.172,
    # MODERATE
    'CIN': 0.170, 'TOR': 0.168, 'MIL': 0.165, 'KC': 0.162, 'BOS': 0.160,
    'ARI': 0.158, 'STL': 0.155, 'SF': 0.152, 'NYM': 0.150, 'CLE': 0.148,
    'DET': 0.145, 'TB': 0.142, 'CHC': 0.140, 'LAA': 0.138, 'COL': 0.135,
    # LOW RISK - Contact-oriented lineups
    'PIT': 0.132, 'WSH': 0.130, 'MIA': 0.125, 'CHW': 0.120, 'OAK': 0.115,
}

# Team wOBA (overall offensive quality)
TEAM_WOBA = {
    'LAD': 0.345, 'NYY': 0.338, 'ATL': 0.335, 'HOU': 0.332, 'PHI': 0.330,
    'BAL': 0.328, 'SEA': 0.325, 'SD': 0.322, 'MIN': 0.320, 'TEX': 0.318,
    'CIN': 0.315, 'TOR': 0.312, 'MIL': 0.310, 'KC': 0.308, 'BOS': 0.305,
    'ARI': 0.302, 'STL': 0.300, 'SF': 0.298, 'NYM': 0.295, 'CLE': 0.292,
    'DET': 0.290, 'TB': 0.288, 'CHC': 0.285, 'LAA': 0.282, 'COL': 0.280,
    'PIT': 0.278, 'WSH': 0.275, 'MIA': 0.270, 'CHW': 0.265, 'OAK': 0.260,
}

# League averages for normalization
LEAGUE_AVG = {
    'K_PCT': 0.225,
    'ISO': 0.155,
    'WOBA': 0.310,
    'HR_PER_9': 1.25,
    'K_PER_9': 8.8,
    'BB_PER_9': 3.2,
}


# =============================================================================
# CATCHER FRAMING (Update at season start)
# Source: https://baseballsavant.mlb.com/catcher_framing
# =============================================================================

class FramingTier(Enum):
    """Catcher framing quality tiers."""
    ELITE = "elite"      # +2-4 pts per start
    GOOD = "good"        # +1-2 pts per start
    AVERAGE = "average"  # Neutral
    POOR = "poor"        # -1-2 pts per start

# Catcher framing impact (points per start adjustment)
CATCHER_FRAMING = {
    # ELITE FRAMERS
    'Patrick Bailey': (FramingTier.ELITE, 'SF', 3.0),
    'Cal Raleigh': (FramingTier.ELITE, 'SEA', 2.8),
    'Austin Wells': (FramingTier.ELITE, 'NYY', 2.5),
    # GOOD FRAMERS
    'Jose Trevino': (FramingTier.GOOD, 'CIN', 1.5),
    'Alejandro Kirk': (FramingTier.GOOD, 'TOR', 1.2),
    'Adley Rutschman': (FramingTier.GOOD, 'BAL', 1.0),
    'William Contreras': (FramingTier.GOOD, 'MIL', 0.8),
    # POOR FRAMERS
    'Edgar Quero': (FramingTier.POOR, 'CHW', -1.5),
    'Riley Adams': (FramingTier.POOR, 'WSH', -1.2),
}


# =============================================================================
# MATCHUP QUALITY TIERS
# =============================================================================

class MatchupTier(Enum):
    """Overall matchup quality classification."""
    ELITE = "elite"          # Stream confidently, +15-25% boost
    FAVORABLE = "favorable"  # Good matchup, +5-15% boost
    NEUTRAL = "neutral"      # Average matchup
    UNFAVORABLE = "unfavorable"  # Tough matchup, -5-15% penalty
    AVOID = "avoid"          # Don't stream unless desperate


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PitcherProfile:
    """
    Pitcher evaluation using VALIDATED metrics from Jan 2026 backtest.

    PRIMARY METRIC (80% of value):
    - IP Sample: Best predictor of outcomes (r=0.295)
      - 120+ IP: "Proven" - 10.8 pts avg, can absorb HR
      - 80-120 IP: "Developing" - 8.0 pts avg
      - <80 IP: "Unproven" - 5.7 pts avg, AVOID

    SECONDARY METRICS (20% of value, tiebreakers only):
    - K-BB%: Minimal impact in isolation
    - Stuff+, GB%: Marginal effects
    """
    name: str
    team: str

    # PRIMARY: Experience (THE KEY FACTOR)
    ip_sample: float = 0.0       # Season IP - MOST IMPORTANT METRIC

    # Core metrics (secondary importance)
    k_pct: float = 0.22          # Strikeout rate
    bb_pct: float = 0.08         # Walk rate
    k_bb_pct: float = 0.14       # K-BB% (calculated if not provided)

    # Stuff/Quality metrics
    stuff_plus: float = 100.0    # Stuff+ (100 = average)
    pitching_plus: float = 100.0 # Combined stuff/location

    # Batted ball profile
    gb_pct: float = 0.43         # Ground ball rate
    fb_pct: float = 0.35         # Fly ball rate
    hr_per_9: float = 1.25       # HR per 9 innings
    barrel_pct: float = 0.08     # Barrel rate allowed

    # Rate stats
    k_per_9: float = 8.8         # K/9
    bb_per_9: float = 3.2        # BB/9
    era: float = 4.50            # ERA (for reference)

    # Handedness
    throws: str = 'R'            # R or L

    def __post_init__(self):
        """Calculate derived metrics."""
        # Calculate K-BB% if not explicitly set
        if self.k_bb_pct == 0.14 and self.k_pct != 0.22:
            self.k_bb_pct = self.k_pct - self.bb_pct

    @property
    def k_bb_grade(self) -> str:
        """Grade K-BB% (target >15%, avoid <10%)."""
        if self.k_bb_pct >= 0.20:
            return "ELITE"
        elif self.k_bb_pct >= 0.15:
            return "GOOD"
        elif self.k_bb_pct >= 0.10:
            return "AVERAGE"
        else:
            return "POOR"

    @property
    def stuff_grade(self) -> str:
        """Grade Stuff+ (target >105, avoid <95)."""
        if self.stuff_plus >= 110:
            return "ELITE"
        elif self.stuff_plus >= 105:
            return "GOOD"
        elif self.stuff_plus >= 95:
            return "AVERAGE"
        else:
            return "POOR"

    @property
    def gb_grade(self) -> str:
        """Grade GB% (target >45%, avoid <35%)."""
        if self.gb_pct >= 0.50:
            return "ELITE"
        elif self.gb_pct >= 0.45:
            return "GOOD"
        elif self.gb_pct >= 0.38:
            return "AVERAGE"
        else:
            return "FLY_BALL"  # Risky

    @property
    def is_fly_ball_pitcher(self) -> bool:
        """Check if pitcher is fly-ball prone (higher HR risk)."""
        return self.fb_pct > 0.40 or self.gb_pct < 0.38

    @property
    def experience_tier(self) -> str:
        """
        Grade pitcher experience (THE PRIMARY FACTOR).

        Based on Jan 2026 backtest of 415 picks:
        - PROVEN (120+ IP): 10.8 pts avg, 4.9 IP/start, survives HR
        - DEVELOPING (80-120 IP): 8.0 pts avg
        - UNPROVEN (<80 IP): 5.7 pts avg, 2.8 IP/start - AVOID
        """
        if self.ip_sample >= 120:
            return "PROVEN"
        elif self.ip_sample >= 80:
            return "DEVELOPING"
        else:
            return "UNPROVEN"

    @property
    def expected_game_ip(self) -> float:
        """
        Expected innings per start based on experience tier.

        High IP pitchers go deeper (key for HR mitigation):
        - PROVEN: 4.9 IP avg (can absorb HR with volume)
        - DEVELOPING: 4.0 IP avg
        - UNPROVEN: 2.8 IP avg (one bad inning = done)
        """
        if self.ip_sample >= 120:
            return 4.9
        elif self.ip_sample >= 100:
            return 4.5
        elif self.ip_sample >= 80:
            return 4.0
        elif self.ip_sample >= 50:
            return 3.4
        else:
            return 2.8

    @property
    def experience_score(self) -> float:
        """
        Calculate experience score (0-100 scale).

        This is THE PRIMARY FACTOR (80% of total value).
        IP sample has r=0.295 correlation with outcomes.
        """
        # Normalize IP sample: 0 IP = 0, 150+ IP = 100
        return min(100, max(0, self.ip_sample / 1.5))

    @property
    def quality_score(self) -> float:
        """
        Calculate pitcher quality score (0-100 scale).

        SECONDARY factor (only 20% of value, used for tiebreakers).
        K-BB% and Stuff+ matter less than we thought.
        """
        # Normalize each metric to 0-100 scale
        k_bb_score = min(100, max(0, (self.k_bb_pct - 0.05) / 0.20 * 100))
        stuff_score = min(100, max(0, (self.stuff_plus - 85) / 30 * 100))
        gb_score = min(100, max(0, (self.gb_pct - 0.30) / 0.25 * 100))
        barrel_score = min(100, max(0, (0.12 - self.barrel_pct) / 0.08 * 100))

        return (k_bb_score * 0.40 +
                stuff_score * 0.30 +
                gb_score * 0.20 +
                barrel_score * 0.10)

    @property
    def pitcher_score(self) -> float:
        """
        Calculate overall pitcher score (0-100 scale).

        VALIDATED WEIGHTS (Jan 2026 backtest):
        - Experience (IP sample): 80% - THE PRIMARY FACTOR
        - Quality (K-BB%, Stuff+): 20% - Tiebreaker only

        Old weights were 100% quality - THIS WAS WRONG.
        """
        return (self.experience_score * 0.80 +
                self.quality_score * 0.20)


@dataclass
class OpponentProfile:
    """
    Opponent team evaluation.

    Key metrics (from META SYNTHESIS):
    - Team K%: Most exploitable weakness
    - Team ISO: Power/HR risk (critical with -13 HR scoring)
    """
    team: str

    # Core metrics (pulled from constants or provided)
    k_pct: float = None
    iso: float = None
    woba: float = None

    # Lineup-specific (if known)
    lineup_k_pct: float = None   # Today's lineup K%
    lineup_iso: float = None     # Today's lineup ISO

    def __post_init__(self):
        """Fill in team averages if not provided."""
        if self.k_pct is None:
            self.k_pct = TEAM_K_PCT.get(self.team, LEAGUE_AVG['K_PCT'])
        if self.iso is None:
            self.iso = TEAM_ISO.get(self.team, LEAGUE_AVG['ISO'])
        if self.woba is None:
            self.woba = TEAM_WOBA.get(self.team, LEAGUE_AVG['WOBA'])

    @property
    def k_grade(self) -> str:
        """Grade team K% (higher = better for streaming)."""
        if self.k_pct >= 0.26:
            return "ELITE"  # Very exploitable
        elif self.k_pct >= 0.23:
            return "GOOD"
        elif self.k_pct >= 0.20:
            return "AVERAGE"
        else:
            return "TOUGH"  # Hard to strike out

    @property
    def power_grade(self) -> str:
        """Grade team ISO (lower = safer)."""
        if self.iso <= 0.135:
            return "SAFE"  # Low power
        elif self.iso <= 0.155:
            return "MODERATE"
        elif self.iso <= 0.175:
            return "RISKY"
        else:
            return "DANGEROUS"  # High HR risk

    @property
    def opponent_score(self) -> float:
        """
        Calculate opponent matchup score (0-100, higher = better matchup).

        Weights:
        - K%: 50% (most exploitable, +2 pts per K)
        - ISO: 35% (HR risk with -13 scoring)
        - wOBA: 15% (overall quality)
        """
        # Normalize (invert where needed so higher = better matchup)
        k_score = min(100, max(0, (self.k_pct - 0.15) / 0.15 * 100))
        iso_score = min(100, max(0, (0.22 - self.iso) / 0.12 * 100))  # Inverted
        woba_score = min(100, max(0, (0.36 - self.woba) / 0.10 * 100))  # Inverted

        return k_score * 0.50 + iso_score * 0.35 + woba_score * 0.15


@dataclass
class ParkContext:
    """
    Park and environmental context for a start.
    """
    park_team: str  # Team whose park (for lookup)

    # Park factors
    hr_factor: float = None
    k_factor: float = None

    # Weather (optional)
    hrfi: int = None         # Home Run Forecast Index (1-10)
    temperature: float = None
    wind_out: bool = None    # Wrigley-specific

    # Umpire (optional, often unknown at lineup time)
    umpire_name: str = None
    umpire_k_boost: float = 0.0  # +/- K adjustment

    # Catcher (optional)
    catcher_name: str = None
    framing_boost: float = 0.0

    def __post_init__(self):
        """Fill in park factors from constants."""
        if self.hr_factor is None:
            self.hr_factor = PARK_HR_FACTORS.get(self.park_team, 100)
        if self.k_factor is None:
            self.k_factor = PARK_K_FACTORS.get(self.park_team, 100)

        # Lookup catcher framing if provided
        if self.catcher_name and self.catcher_name in CATCHER_FRAMING:
            _, _, boost = CATCHER_FRAMING[self.catcher_name]
            self.framing_boost = boost

    @property
    def park_grade(self) -> str:
        """Grade park HR factor."""
        if self.hr_factor >= 115:
            return "DANGER"
        elif self.hr_factor >= 105:
            return "MODERATE"
        elif self.hr_factor >= 95:
            return "NEUTRAL"
        elif self.hr_factor >= 85:
            return "FAVORABLE"
        else:
            return "EXCELLENT"

    @property
    def weather_adjustment(self) -> float:
        """Calculate points adjustment from weather/HRFI."""
        if self.hrfi is None:
            return 0.0

        # Only act on extremes
        if self.hrfi <= 3:
            return 1.5  # Pitcher-friendly
        elif self.hrfi >= 8:
            return -1.5  # Hitter-friendly
        return 0.0

    @property
    def total_environment_boost(self) -> float:
        """Total environmental adjustment to expected points."""
        return self.weather_adjustment + self.framing_boost + self.umpire_k_boost


# =============================================================================
# MATCHUP EVALUATOR
# =============================================================================

@dataclass
class MatchupResult:
    """Complete matchup evaluation result."""
    pitcher: PitcherProfile
    opponent: OpponentProfile
    park: ParkContext

    # Scores (0-100)
    pitcher_score: float = 0.0
    opponent_score: float = 0.0
    park_score: float = 0.0
    overall_score: float = 0.0

    # Projected stats
    proj_ip: float = 5.5
    proj_k: float = 5.5
    proj_bb: float = 2.0
    proj_hr: float = 0.8

    # Expected points
    expected_points: float = 0.0
    floor_points: float = 0.0
    ceiling_points: float = 0.0

    # Risk assessment
    disaster_prob: float = 0.10  # P(3+ HR)

    # Tier classifications
    matchup_tier: MatchupTier = MatchupTier.NEUTRAL
    risk_tier: str = "MODERATE"

    # Breakdown
    breakdown: Dict[str, Any] = field(default_factory=dict)


class MatchupEvaluator:
    """
    Main matchup evaluation engine.

    VALIDATED WEIGHTS (Jan 2026 backtest - 415 picks):

    OLD WEIGHTS (WRONG):
    - 60% pitcher quality (K-BB%, Stuff+)
    - 20% opponent
    - 15% park
    - 5% weather

    NEW WEIGHTS (CORRECT):
    - 80% pitcher (mostly EXPERIENCE, not quality)
    - 10% opponent
    - 10% park + environment

    KEY INSIGHT: Matchup factors only explain ~1 pt difference.
    Pitcher experience (IP sample) explains ~5 pt difference.
    """

    # VALIDATED weights from Jan 2026 backtest
    PITCHER_WEIGHT = 0.80       # Was 0.60 - EXPERIENCE is key
    OPPONENT_WEIGHT = 0.10      # Was 0.20 - Less important than thought
    PARK_WEIGHT = 0.05          # Was 0.15 - Marginal impact
    ENVIRONMENT_WEIGHT = 0.05   # Same - Weather/catcher as tiebreaker

    # Hard filter thresholds
    MIN_IP_SAMPLE = 80          # NEVER stream below this
    PREFERRED_IP_SAMPLE = 120   # Target this level

    def __init__(self):
        """Initialize evaluator."""
        pass

    def evaluate(self,
                 pitcher: PitcherProfile,
                 opponent: OpponentProfile,
                 park: ParkContext) -> MatchupResult:
        """
        Evaluate a complete matchup.

        Args:
            pitcher: Pitcher profile with metrics
            opponent: Opponent team profile
            park: Park and environmental context

        Returns:
            MatchupResult with scores, projections, and tiers
        """
        result = MatchupResult(
            pitcher=pitcher,
            opponent=opponent,
            park=park
        )

        # Calculate component scores
        result.pitcher_score = pitcher.pitcher_score
        result.opponent_score = opponent.opponent_score
        result.park_score = self._calculate_park_score(park)

        # Weighted overall score
        result.overall_score = (
            result.pitcher_score * self.PITCHER_WEIGHT +
            result.opponent_score * self.OPPONENT_WEIGHT +
            result.park_score * self.PARK_WEIGHT +
            50.0 * self.ENVIRONMENT_WEIGHT  # Environment is 0-centered adjustment
        )

        # Project stats
        self._project_stats(result)

        # Calculate expected points
        self._calculate_points(result)

        # Assess risk
        self._assess_risk(result)

        # Classify tiers
        self._classify_tiers(result)

        # Build breakdown
        result.breakdown = self._build_breakdown(result)

        return result

    def _calculate_park_score(self, park: ParkContext) -> float:
        """Convert park HR factor to 0-100 score (lower HR factor = higher score)."""
        # Invert: lower HR factor is better
        # Range roughly 75-130, center at 100
        return min(100, max(0, (130 - park.hr_factor) / 55 * 100))

    def _project_stats(self, result: MatchupResult):
        """
        Project game stats based on matchup.

        KEY INSIGHT (Jan 2026 backtest):
        - IP projection based on EXPERIENCE, not generic 5.5
        - Proven pitchers (120+ IP): 4.9 IP avg
        - Unproven pitchers (<80 IP): 2.8 IP avg
        - This is the HR MITIGATION effect - more IP = more cushion
        """
        pitcher = result.pitcher
        opponent = result.opponent
        park = result.park

        # CRITICAL: Use experience-based IP projection
        # This is THE key to HR mitigation math
        base_ip = pitcher.expected_game_ip  # Was hardcoded 5.5

        # Base K/BB/HR projections scaled to expected IP
        base_k = pitcher.k_per_9 * base_ip / 9
        base_bb = pitcher.bb_per_9 * base_ip / 9
        base_hr = pitcher.hr_per_9 * base_ip / 9

        # Adjust for opponent K%
        k_multiplier = opponent.k_pct / LEAGUE_AVG['K_PCT']

        # Adjust for opponent ISO (affects HR)
        iso_multiplier = opponent.iso / LEAGUE_AVG['ISO']

        # Adjust for park
        park_hr_mult = park.hr_factor / 100.0
        park_k_mult = park.k_factor / 100.0

        # Apply adjustments
        result.proj_ip = base_ip
        result.proj_k = base_k * k_multiplier * park_k_mult
        result.proj_bb = base_bb
        result.proj_hr = base_hr * iso_multiplier * park_hr_mult

        # Ensure reasonable bounds
        result.proj_k = max(0, min(15, result.proj_k))
        result.proj_hr = max(0, min(4, result.proj_hr))

    def _calculate_points(self, result: MatchupResult):
        """Calculate expected fantasy points."""
        # Base expected points
        base_points = (
            result.proj_ip * Scoring.IP +
            result.proj_k * Scoring.K +
            result.proj_bb * Scoring.BB +
            result.proj_hr * Scoring.HR
        )

        # Add environmental adjustments
        env_adj = result.park.total_environment_boost

        result.expected_points = base_points + env_adj

        # Floor/Ceiling (rough estimates)
        # Floor: -1 IP, -2 K, +1 BB, +1 HR
        result.floor_points = (
            (result.proj_ip - 1) * Scoring.IP +
            (result.proj_k - 2) * Scoring.K +
            (result.proj_bb + 1) * Scoring.BB +
            (result.proj_hr + 1) * Scoring.HR
        ) + env_adj

        # Ceiling: +1 IP, +3 K, -1 BB, -0.5 HR
        result.ceiling_points = (
            (result.proj_ip + 1) * Scoring.IP +
            (result.proj_k + 3) * Scoring.K +
            max(0, result.proj_bb - 1) * Scoring.BB +
            max(0, result.proj_hr - 0.5) * Scoring.HR
        ) + env_adj

    def _assess_risk(self, result: MatchupResult):
        """Assess disaster probability using Poisson model."""
        # Expected HR for this matchup
        lambda_hr = result.proj_hr

        # Adjust for fly ball pitcher
        if result.pitcher.is_fly_ball_pitcher:
            lambda_hr *= 1.25

        # Adjust for high-ISO opponent
        if result.opponent.iso >= 0.18:
            lambda_hr *= 1.15

        # Adjust for HR-friendly park
        if result.park.hr_factor >= 115:
            lambda_hr *= 1.10

        # P(3+ HR) using Poisson
        # P(X >= 3) = 1 - P(0) - P(1) - P(2)
        p_0 = math.exp(-lambda_hr)
        p_1 = lambda_hr * math.exp(-lambda_hr)
        p_2 = (lambda_hr ** 2 / 2) * math.exp(-lambda_hr)

        result.disaster_prob = 1 - p_0 - p_1 - p_2

    def _classify_tiers(self, result: MatchupResult):
        """Classify matchup and risk tiers."""
        # Matchup tier based on overall score
        if result.overall_score >= 70:
            result.matchup_tier = MatchupTier.ELITE
        elif result.overall_score >= 55:
            result.matchup_tier = MatchupTier.FAVORABLE
        elif result.overall_score >= 40:
            result.matchup_tier = MatchupTier.NEUTRAL
        elif result.overall_score >= 25:
            result.matchup_tier = MatchupTier.UNFAVORABLE
        else:
            result.matchup_tier = MatchupTier.AVOID

        # Risk tier based on disaster probability
        if result.disaster_prob < 0.05:
            result.risk_tier = "ELITE"
        elif result.disaster_prob < 0.10:
            result.risk_tier = "SAFE"
        elif result.disaster_prob < 0.15:
            result.risk_tier = "MODERATE"
        elif result.disaster_prob < 0.25:
            result.risk_tier = "RISKY"
        else:
            result.risk_tier = "DANGEROUS"

        # Hard filter: NO-GO conditions
        if self._check_no_go(result):
            result.matchup_tier = MatchupTier.AVOID
            result.risk_tier = "NO_GO"

    def _check_no_go(self, result: MatchupResult) -> bool:
        """
        Check for NO-GO conditions (hard filters).

        VALIDATED HARD FILTERS (Jan 2026 backtest):
        1. IP < 80: ALWAYS NO-GO (5.7 pts avg, not worth it)
        2. IP 80-100 vs HARD opponent: NO-GO (matchup can't save)
        3. FB pitcher vs elite power at HR park: NO-GO
        """
        pitcher = result.pitcher
        opponent = result.opponent
        park = result.park

        # HARD FILTER #1: Unproven pitchers (IP < 80)
        # These averaged only 5.7 pts - NEVER stream regardless of matchup
        if pitcher.ip_sample < self.MIN_IP_SAMPLE:
            return True

        # HARD FILTER #2: Developing pitcher (80-100 IP) vs hard opponent
        # Matchup can't save a developing arm against elite offense
        hard_opponents = {'LAD', 'NYY', 'HOU', 'ATL', 'PHI'}
        if (80 <= pitcher.ip_sample < 100 and
            opponent.team in hard_opponents):
            return True

        # HARD FILTER #3: FB pitcher vs elite power at HR-friendly park
        if (pitcher.is_fly_ball_pitcher and
            opponent.iso >= 0.19 and
            park.hr_factor >= 115):
            return True

        # HARD FILTER #4: Very high disaster probability
        if result.disaster_prob > 0.30:
            return True

        # HARD FILTER #5: Poor quality pitcher vs tough lineup at bad park
        # (Only applies to proven pitchers who passed IP filter)
        if (pitcher.quality_score < 30 and
            opponent.opponent_score < 30 and
            park.hr_factor >= 110):
            return True

        return False

    def _build_breakdown(self, result: MatchupResult) -> Dict[str, Any]:
        """Build detailed breakdown for analysis."""
        return {
            'pitcher': {
                'name': result.pitcher.name,
                'team': result.pitcher.team,
                'score': round(result.pitcher_score, 1),
                # PRIMARY FACTOR: Experience
                'ip_sample': result.pitcher.ip_sample,
                'experience_tier': result.pitcher.experience_tier,
                'experience_score': round(result.pitcher.experience_score, 1),
                'expected_game_ip': result.pitcher.expected_game_ip,
                # Secondary factors
                'quality_score': round(result.pitcher.quality_score, 1),
                'k_bb_pct': f"{result.pitcher.k_bb_pct:.1%}",
                'k_bb_grade': result.pitcher.k_bb_grade,
                'stuff_plus': result.pitcher.stuff_plus,
                'stuff_grade': result.pitcher.stuff_grade,
                'gb_pct': f"{result.pitcher.gb_pct:.1%}",
                'gb_grade': result.pitcher.gb_grade,
                'is_fly_ball': result.pitcher.is_fly_ball_pitcher,
            },
            'opponent': {
                'team': result.opponent.team,
                'score': round(result.opponent_score, 1),
                'k_pct': f"{result.opponent.k_pct:.1%}",
                'k_grade': result.opponent.k_grade,
                'iso': f"{result.opponent.iso:.3f}",
                'power_grade': result.opponent.power_grade,
            },
            'park': {
                'team': result.park.park_team,
                'hr_factor': result.park.hr_factor,
                'park_grade': result.park.park_grade,
                'hrfi': result.park.hrfi,
                'weather_adj': round(result.park.weather_adjustment, 1),
                'catcher': result.park.catcher_name,
                'framing_adj': round(result.park.framing_boost, 1),
            },
            'projections': {
                'ip': round(result.proj_ip, 1),
                'k': round(result.proj_k, 1),
                'bb': round(result.proj_bb, 1),
                'hr': round(result.proj_hr, 2),
            },
            'points': {
                'expected': round(result.expected_points, 1),
                'floor': round(result.floor_points, 1),
                'ceiling': round(result.ceiling_points, 1),
            },
            'risk': {
                'disaster_prob': f"{result.disaster_prob:.1%}",
                'risk_tier': result.risk_tier,
            },
        }


# =============================================================================
# STREAMING RANKER
# =============================================================================

@dataclass
class StreamingCandidate:
    """A streaming candidate with evaluation."""
    pitcher: PitcherProfile
    opponent: OpponentProfile
    park: ParkContext
    pitch_date: str = ""  # YYYY-MM-DD

    # Populated by evaluation
    result: MatchupResult = None

    @property
    def expected_points(self) -> float:
        return self.result.expected_points if self.result else 0.0

    @property
    def matchup_tier(self) -> MatchupTier:
        return self.result.matchup_tier if self.result else MatchupTier.NEUTRAL

    @property
    def risk_tier(self) -> str:
        return self.result.risk_tier if self.result else "MODERATE"


class StreamingRanker:
    """
    Ranks streaming candidates combining matchup quality and risk.
    """

    def __init__(self, evaluator: MatchupEvaluator = None):
        """Initialize ranker."""
        self.evaluator = evaluator or MatchupEvaluator()

    def evaluate_candidates(self,
                           candidates: List[StreamingCandidate]) -> List[StreamingCandidate]:
        """
        Evaluate all candidates and attach results.
        """
        for candidate in candidates:
            candidate.result = self.evaluator.evaluate(
                candidate.pitcher,
                candidate.opponent,
                candidate.park
            )
        return candidates

    def rank_by_expected_points(self,
                                candidates: List[StreamingCandidate],
                                exclude_no_go: bool = True) -> List[StreamingCandidate]:
        """
        Rank candidates by expected points.

        Args:
            candidates: List of evaluated candidates
            exclude_no_go: Whether to filter out NO_GO matchups

        Returns:
            Sorted list (best first)
        """
        filtered = candidates
        if exclude_no_go:
            filtered = [c for c in candidates if c.risk_tier != "NO_GO"]

        return sorted(filtered, key=lambda c: c.expected_points, reverse=True)

    def rank_by_floor(self,
                      candidates: List[StreamingCandidate],
                      exclude_no_go: bool = True) -> List[StreamingCandidate]:
        """
        Rank by floor (conservative, for when leading).
        """
        filtered = candidates
        if exclude_no_go:
            filtered = [c for c in candidates if c.risk_tier != "NO_GO"]

        return sorted(filtered,
                     key=lambda c: c.result.floor_points if c.result else -999,
                     reverse=True)

    def rank_by_ceiling(self,
                        candidates: List[StreamingCandidate],
                        exclude_no_go: bool = True) -> List[StreamingCandidate]:
        """
        Rank by ceiling (aggressive, for when trailing).
        """
        filtered = candidates
        if exclude_no_go:
            filtered = [c for c in candidates if c.risk_tier != "NO_GO"]

        return sorted(filtered,
                     key=lambda c: c.result.ceiling_points if c.result else -999,
                     reverse=True)

    def rank_risk_adjusted(self,
                          candidates: List[StreamingCandidate],
                          risk_tolerance: float = 1.0,
                          exclude_no_go: bool = True) -> List[StreamingCandidate]:
        """
        Rank with risk adjustment.

        Args:
            candidates: List of evaluated candidates
            risk_tolerance: 1.0 = neutral, <1 = risk averse, >1 = risk seeking
            exclude_no_go: Whether to filter out NO_GO matchups

        Returns:
            Sorted list (best first)
        """
        filtered = candidates
        if exclude_no_go:
            filtered = [c for c in candidates if c.risk_tier != "NO_GO"]

        def risk_adjusted_score(c: StreamingCandidate) -> float:
            if not c.result:
                return -999

            # Base: expected points
            base = c.result.expected_points

            # Risk penalty based on disaster probability
            risk_penalty = c.result.disaster_prob * 40  # -40 points max penalty

            # Adjust penalty by tolerance
            adjusted_penalty = risk_penalty / risk_tolerance

            return base - adjusted_penalty

        return sorted(filtered, key=risk_adjusted_score, reverse=True)

    def get_tier_summary(self,
                        candidates: List[StreamingCandidate]) -> Dict[str, List[str]]:
        """
        Group candidates by matchup tier.
        """
        tiers = {tier.value: [] for tier in MatchupTier}

        for c in candidates:
            tier = c.matchup_tier.value if c.result else "neutral"
            tiers[tier].append(
                f"{c.pitcher.name} vs {c.opponent.team} @ {c.park.park_team}"
            )

        return tiers

    def format_rankings(self,
                       candidates: List[StreamingCandidate],
                       top_n: int = 10) -> str:
        """
        Format rankings as readable string.
        """
        lines = ["=" * 70]
        lines.append("STREAMING RANKINGS")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"{'Rank':<5} {'Pitcher':<20} {'vs':<5} {'@':<5} "
                    f"{'E[Pts]':>7} {'Floor':>7} {'Ceil':>7} {'Risk':<10} {'Tier':<12}")
        lines.append("-" * 70)

        for i, c in enumerate(candidates[:top_n], 1):
            if not c.result:
                continue

            r = c.result
            lines.append(
                f"{i:<5} {c.pitcher.name:<20} {c.opponent.team:<5} "
                f"{c.park.park_team:<5} {r.expected_points:>7.1f} "
                f"{r.floor_points:>7.1f} {r.ceiling_points:>7.1f} "
                f"{r.risk_tier:<10} {r.matchup_tier.value:<12}"
            )

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


# =============================================================================
# QUICK LOOKUP FUNCTIONS
# =============================================================================

def get_team_matchup_quality(team: str) -> Dict[str, Any]:
    """
    Quick lookup of a team's matchup characteristics.
    """
    return {
        'team': team,
        'k_pct': TEAM_K_PCT.get(team, LEAGUE_AVG['K_PCT']),
        'k_grade': OpponentProfile(team).k_grade,
        'iso': TEAM_ISO.get(team, LEAGUE_AVG['ISO']),
        'power_grade': OpponentProfile(team).power_grade,
        'woba': TEAM_WOBA.get(team, LEAGUE_AVG['WOBA']),
        'home_park_hr': PARK_HR_FACTORS.get(team, 100),
    }


def get_park_safety(park_team: str) -> Dict[str, Any]:
    """
    Quick lookup of park HR safety.
    """
    hr_factor = PARK_HR_FACTORS.get(park_team, 100)
    park = ParkContext(park_team)

    return {
        'park_team': park_team,
        'hr_factor': hr_factor,
        'grade': park.park_grade,
        'k_factor': PARK_K_FACTORS.get(park_team, 100),
        'streaming_verdict': (
            "AVOID" if hr_factor >= 115 else
            "RISKY" if hr_factor >= 105 else
            "OK" if hr_factor >= 95 else
            "GOOD" if hr_factor >= 85 else
            "EXCELLENT"
        ),
    }


def quick_evaluate(pitcher_name: str,
                   ip_sample: float,
                   k_bb_pct: float,
                   stuff_plus: float,
                   gb_pct: float,
                   vs_team: str,
                   at_park: str) -> MatchupResult:
    """
    Quick evaluation with minimal inputs.

    IMPORTANT: ip_sample is now REQUIRED (it's the #1 factor).
    """
    pitcher = PitcherProfile(
        name=pitcher_name,
        team="",  # Not needed for evaluation
        ip_sample=ip_sample,  # THE KEY FACTOR
        k_bb_pct=k_bb_pct,
        k_pct=k_bb_pct + 0.08,  # Estimate
        bb_pct=0.08,
        stuff_plus=stuff_plus,
        gb_pct=gb_pct,
    )

    opponent = OpponentProfile(team=vs_team)
    park = ParkContext(park_team=at_park)

    evaluator = MatchupEvaluator()
    return evaluator.evaluate(pitcher, opponent, park)


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demonstrate the matchup evaluator."""
    print("=" * 70)
    print("MATCHUP EVALUATOR DEMO")
    print("=" * 70)
    print()

    # Create sample pitchers with IP sample (THE KEY FACTOR)
    pitchers = [
        PitcherProfile(
            name="Corbin Burnes (PROVEN)",
            team="ARI",
            ip_sample=180,  # PROVEN - should dominate
            k_bb_pct=0.22,
            k_pct=0.28,
            bb_pct=0.06,
            stuff_plus=112,
            gb_pct=0.48,
            k_per_9=10.5,
            bb_per_9=2.0,
            hr_per_9=0.9,
            barrel_pct=0.06,
        ),
        PitcherProfile(
            name="Developing Arm (MID)",
            team="TEX",
            ip_sample=95,   # DEVELOPING - OK vs easy matchups
            k_bb_pct=0.12,
            k_pct=0.20,
            bb_pct=0.08,
            stuff_plus=98,
            gb_pct=0.42,
            k_per_9=8.0,
            bb_per_9=3.2,
            hr_per_9=1.3,
            barrel_pct=0.09,
        ),
        PitcherProfile(
            name="Unproven Rookie (LOW)",
            team="PHI",
            ip_sample=45,   # UNPROVEN - should be NO-GO
            k_bb_pct=0.15,
            k_pct=0.23,
            bb_pct=0.08,
            stuff_plus=102,
            gb_pct=0.44,
            k_per_9=9.2,
            bb_per_9=3.2,
            hr_per_9=1.2,
            barrel_pct=0.08,
        ),
    ]

    # Sample matchups
    matchups = [
        ("OAK", "OAK"),   # Great matchup: weak team, safe park
        ("LAD", "LAD"),   # Terrible: elite offense, worst park
        ("COL", "COL"),   # Coors test: park is actually OK!
        ("NYY", "NYY"),   # Bad: elite offense, bad park
        ("PIT", "PIT"),   # Great: weak team, safest park
    ]

    evaluator = MatchupEvaluator()
    candidates = []

    print("INDIVIDUAL MATCHUP EVALUATIONS")
    print("-" * 70)

    for pitcher in pitchers[:2]:  # Test first two pitchers
        for vs_team, at_park in matchups:
            opponent = OpponentProfile(team=vs_team)
            park = ParkContext(park_team=at_park)

            result = evaluator.evaluate(pitcher, opponent, park)

            print(f"\n{pitcher.name} vs {vs_team} @ {at_park}")
            print(f"  Pitcher Score: {result.pitcher_score:.1f}")
            print(f"  Opponent Score: {result.opponent_score:.1f}")
            print(f"  Park Score: {result.park_score:.1f}")
            print(f"  Overall Score: {result.overall_score:.1f}")
            print(f"  Expected Points: {result.expected_points:.1f}")
            print(f"  Floor/Ceiling: {result.floor_points:.1f} / {result.ceiling_points:.1f}")
            print(f"  Disaster Prob: {result.disaster_prob:.1%}")
            print(f"  Matchup Tier: {result.matchup_tier.value.upper()}")
            print(f"  Risk Tier: {result.risk_tier}")

            candidates.append(StreamingCandidate(
                pitcher=pitcher,
                opponent=opponent,
                park=park,
                result=result,
            ))

    # Demo ranker
    print("\n" + "=" * 70)
    print("STREAMING RANKINGS (By Expected Points)")
    print("=" * 70)

    ranker = StreamingRanker(evaluator)
    ranked = ranker.rank_by_expected_points(candidates)
    print(ranker.format_rankings(ranked, top_n=8))

    # Demo COORS VALIDATION
    print("\n" + "=" * 70)
    print("COORS FIELD VALIDATION")
    print("=" * 70)

    coors_info = get_park_safety("COL")
    lad_info = get_park_safety("LAD")

    print(f"\nCoors Field (COL):")
    print(f"  HR Factor: {coors_info['hr_factor']}")
    print(f"  Grade: {coors_info['grade']}")
    print(f"  Streaming Verdict: {coors_info['streaming_verdict']}")

    print(f"\nDodger Stadium (LAD):")
    print(f"  HR Factor: {lad_info['hr_factor']}")
    print(f"  Grade: {lad_info['grade']}")
    print(f"  Streaming Verdict: {lad_info['streaming_verdict']}")

    print(f"\n>>> CONCLUSION: Coors ({coors_info['hr_factor']}) is SAFER than "
          f"Dodger Stadium ({lad_info['hr_factor']})!")
    print(">>> The conventional wisdom 'Never stream at Coors' is WRONG.")

    # Quick lookup demo
    print("\n" + "=" * 70)
    print("QUICK TEAM LOOKUPS")
    print("=" * 70)

    for team in ['LAD', 'OAK', 'COL', 'NYY', 'PIT']:
        info = get_team_matchup_quality(team)
        print(f"\n{team}:")
        print(f"  K%: {info['k_pct']:.1%} ({info['k_grade']})")
        print(f"  ISO: {info['iso']:.3f} ({info['power_grade']})")
        print(f"  Home Park HR: {info['home_park_hr']}")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo()
