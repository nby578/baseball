"""
Points Projector for BLJ X

Projects expected fantasy points for pitchers based on:
- Base projection (season stats, pitcher quality)
- Matchup adjustment (opponent, park)
- Weather modifier (HRFI when available)
- Catcher framing bonus
- Fatigue/rest considerations

Uses BLJ X scoring:
- IP: +5, K: +2, BB: -3, HBP: -3, HR: -13, SV: +11, HLD: +9
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date

from league_settings import PITCHER_SCORING, calculate_pitcher_points
from streaming import (
    TEAM_OFFENSE_RANK, PARK_HR_FACTORS, TEAM_HR_RATE, TEAM_K_RATE
)


# =============================================================================
# LEAGUE AVERAGE BASELINES (2024 data, adjust for 2026)
# =============================================================================

# Average starter performance per start
LEAGUE_AVG_START = {
    "ip": 5.5,
    "k": 5.0,
    "bb": 2.0,
    "hr": 1.0,
    "hbp": 0.3,
}

# Average reliever performance per appearance
LEAGUE_AVG_RELIEF = {
    "ip": 1.0,
    "k": 1.0,
    "bb": 0.35,
    "hr": 0.12,
    "hbp": 0.05,
}


# =============================================================================
# CATCHER FRAMING ADJUSTMENTS
# =============================================================================

# Framing runs per 120 games -> estimated extra K-BB per game
# Top framers add ~0.15-0.25 K-BB per game
CATCHER_FRAMING = {
    # Elite framers (add K-BB value)
    "Patrick Bailey": 0.25,
    "Cal Raleigh": 0.20,
    "Austin Wells": 0.18,
    "Jose Trevino": 0.15,
    "Alejandro Kirk": 0.15,
    # Good framers
    "William Contreras": 0.10,
    "Adley Rutschman": 0.10,
    "Sean Murphy": 0.08,
    # Neutral (0.0)
    # Bad framers (negative)
    "Edgar Quero": -0.20,
    "Riley Adams": -0.15,
}

# Team -> primary catcher (simplified, would need roster data)
TEAM_CATCHERS = {
    "SF": "Patrick Bailey",
    "SEA": "Cal Raleigh",
    "NYY": "Austin Wells",
    "CIN": "Jose Trevino",
    "TOR": "Alejandro Kirk",
    "ATL": "William Contreras",
    "BAL": "Adley Rutschman",
    "OAK": "Sean Murphy",
    "CHW": "Edgar Quero",
    "WSH": "Riley Adams",
}


# =============================================================================
# PITCHER PROJECTION
# =============================================================================

@dataclass
class PitcherProjection:
    """Projected stats and points for a pitching appearance."""
    pitcher_name: str
    team: str
    opponent: str
    is_home: bool
    game_date: Optional[date] = None

    # Projected stats
    proj_ip: float = 0.0
    proj_k: float = 0.0
    proj_bb: float = 0.0
    proj_hr: float = 0.0
    proj_hbp: float = 0.0

    # For relievers
    proj_sv: float = 0.0
    proj_hld: float = 0.0

    # Final projection
    expected_points: float = 0.0

    # Breakdown
    ip_points: float = 0.0
    k_points: float = 0.0
    bb_points: float = 0.0
    hr_points: float = 0.0
    other_points: float = 0.0

    # Adjustments applied
    adjustments: dict = None

    def __post_init__(self):
        if self.adjustments is None:
            self.adjustments = {}

    def calculate_points(self):
        """Calculate expected points from projected stats."""
        self.ip_points = self.proj_ip * PITCHER_SCORING["IP"]
        self.k_points = self.proj_k * PITCHER_SCORING["K"]
        self.bb_points = self.proj_bb * PITCHER_SCORING["BB"]
        self.hr_points = self.proj_hr * PITCHER_SCORING["HR"]
        self.other_points = (
            self.proj_hbp * PITCHER_SCORING["HBP"] +
            self.proj_sv * PITCHER_SCORING["SV"] +
            self.proj_hld * PITCHER_SCORING["HLD"]
        )

        self.expected_points = (
            self.ip_points + self.k_points + self.bb_points +
            self.hr_points + self.other_points
        )

    def summary(self) -> str:
        """Detailed projection summary."""
        loc = "vs" if self.is_home else "@"
        lines = [
            f"=== {self.pitcher_name} ({self.team}) {loc} {self.opponent} ===",
            f"",
            f"PROJECTED STATS:",
            f"  IP: {self.proj_ip:.1f}  K: {self.proj_k:.1f}  BB: {self.proj_bb:.1f}  HR: {self.proj_hr:.2f}",
            f"",
            f"EXPECTED POINTS: {self.expected_points:.1f}",
            f"  IP:  {self.ip_points:+.1f}",
            f"  K:   {self.k_points:+.1f}",
            f"  BB:  {self.bb_points:+.1f}",
            f"  HR:  {self.hr_points:+.1f}",
            f"  Other: {self.other_points:+.1f}",
            f"",
            f"ADJUSTMENTS APPLIED:",
        ]
        for adj, val in self.adjustments.items():
            lines.append(f"  {adj}: {val:+.2f}")

        return "\n".join(lines)


def project_starter(
    pitcher_name: str,
    team: str,
    opponent: str,
    is_home: bool,
    # Pitcher baseline stats (per start averages)
    base_ip: float = None,
    base_k_per_9: float = None,
    base_bb_per_9: float = None,
    base_hr_per_9: float = None,
    # Optional modifiers
    weather_hrfi: Optional[int] = None,  # 1-10 scale
    days_rest: Optional[int] = None,
    vs_team_k_rate: Optional[float] = None,
    vs_team_hr_rate: Optional[float] = None,
) -> PitcherProjection:
    """
    Project expected points for a starting pitcher.

    Args:
        pitcher_name: Pitcher's name
        team: Pitcher's team abbreviation
        opponent: Opponent team abbreviation
        is_home: Is pitcher at home?
        base_ip: Pitcher's average IP per start (default: league avg)
        base_k_per_9: Pitcher's K/9 rate
        base_bb_per_9: Pitcher's BB/9 rate
        base_hr_per_9: Pitcher's HR/9 rate
        weather_hrfi: Home Run Forecast Index (1-10, higher = more HRs)
        days_rest: Days since last start
        vs_team_k_rate: Override opponent K rate
        vs_team_hr_rate: Override opponent HR rate

    Returns:
        PitcherProjection with expected stats and points
    """
    proj = PitcherProjection(
        pitcher_name=pitcher_name,
        team=team,
        opponent=opponent,
        is_home=is_home,
    )

    # Start with baseline stats
    base_ip = base_ip or LEAGUE_AVG_START["ip"]
    base_k_per_9 = base_k_per_9 or 8.2  # League average
    base_bb_per_9 = base_bb_per_9 or 3.3
    base_hr_per_9 = base_hr_per_9 or 1.3

    # Convert rates to per-start projections
    proj.proj_ip = base_ip
    proj.proj_k = (base_k_per_9 / 9) * base_ip
    proj.proj_bb = (base_bb_per_9 / 9) * base_ip
    proj.proj_hr = (base_hr_per_9 / 9) * base_ip
    proj.proj_hbp = LEAGUE_AVG_START["hbp"]

    # === ADJUSTMENTS ===

    # 1. Opponent K rate adjustment
    opp_k_rate = vs_team_k_rate or TEAM_K_RATE.get(opponent, 0.22)
    league_avg_k = 0.22
    k_mult = opp_k_rate / league_avg_k
    k_adj = proj.proj_k * (k_mult - 1)
    proj.proj_k += k_adj
    proj.adjustments["Opp K Rate"] = k_adj

    # 2. Opponent HR rate adjustment
    opp_hr_rate = vs_team_hr_rate or TEAM_HR_RATE.get(opponent, 0.028)
    league_avg_hr = 0.028
    hr_mult = opp_hr_rate / league_avg_hr
    hr_adj = proj.proj_hr * (hr_mult - 1)
    proj.proj_hr += hr_adj
    proj.adjustments["Opp HR Rate"] = hr_adj * PITCHER_SCORING["HR"]  # Show point impact

    # 3. Park HR factor (for away games, use opponent's park)
    if is_home:
        park = team
    else:
        park = opponent
    park_hr_factor = PARK_HR_FACTORS.get(park, 100)
    park_mult = park_hr_factor / 100
    park_hr_adj = proj.proj_hr * (park_mult - 1)
    proj.proj_hr += park_hr_adj
    proj.adjustments["Park HR Factor"] = park_hr_adj * PITCHER_SCORING["HR"]

    # 4. Home/away adjustment (home pitchers slightly better)
    if is_home:
        proj.proj_ip += 0.2  # Slightly longer at home
        proj.adjustments["Home Advantage"] = 0.2 * PITCHER_SCORING["IP"]

    # 5. Weather adjustment (if provided)
    if weather_hrfi is not None:
        # HRFI 5 = neutral, each point = ~8% HR change
        hr_weather_mult = 1 + (weather_hrfi - 5) * 0.08
        weather_hr_adj = proj.proj_hr * (hr_weather_mult - 1)
        proj.proj_hr += weather_hr_adj
        proj.adjustments["Weather HRFI"] = weather_hr_adj * PITCHER_SCORING["HR"]

    # 6. Catcher framing (if known)
    catcher = TEAM_CATCHERS.get(team)
    if catcher and catcher in CATCHER_FRAMING:
        framing_adj = CATCHER_FRAMING[catcher]
        # Add to K, subtract from BB
        proj.proj_k += framing_adj * 0.5
        proj.proj_bb -= framing_adj * 0.5
        frame_pts = (framing_adj * 0.5 * PITCHER_SCORING["K"] -
                     framing_adj * 0.5 * PITCHER_SCORING["BB"])
        proj.adjustments[f"Catcher ({catcher})"] = frame_pts

    # 7. Days rest adjustment
    if days_rest is not None:
        if days_rest >= 6:
            # Extra rest = slightly better
            proj.proj_k += 0.2
            proj.adjustments["Extra Rest"] = 0.2 * PITCHER_SCORING["K"]
        elif days_rest <= 3:
            # Short rest = worse
            proj.proj_ip -= 0.5
            proj.proj_k -= 0.3
            proj.adjustments["Short Rest"] = -0.5 * PITCHER_SCORING["IP"] - 0.3 * PITCHER_SCORING["K"]

    # Ensure no negative values
    proj.proj_ip = max(0, proj.proj_ip)
    proj.proj_k = max(0, proj.proj_k)
    proj.proj_bb = max(0, proj.proj_bb)
    proj.proj_hr = max(0, proj.proj_hr)

    # Calculate final points
    proj.calculate_points()

    return proj


def project_reliever(
    pitcher_name: str,
    team: str,
    opponent: str,
    is_home: bool,
    # Reliever type
    is_closer: bool = False,
    is_setup: bool = False,
    # Baseline stats
    base_k_per_9: float = None,
    base_bb_per_9: float = None,
    # Save/hold probability
    save_prob: float = 0.0,
    hold_prob: float = 0.0,
    # Fatigue
    consecutive_days: int = 0,
) -> PitcherProjection:
    """
    Project expected points for a reliever.

    Args:
        is_closer: Is this the team's closer?
        is_setup: Is this an elite setup man?
        save_prob: Probability of save opportunity (0-1)
        hold_prob: Probability of hold opportunity (0-1)
        consecutive_days: Days pitched in a row (0, 1, 2, 3+)
    """
    proj = PitcherProjection(
        pitcher_name=pitcher_name,
        team=team,
        opponent=opponent,
        is_home=is_home,
    )

    # Baseline
    base_k_per_9 = base_k_per_9 or 9.5  # Relievers K more
    base_bb_per_9 = base_bb_per_9 or 3.5

    proj.proj_ip = LEAGUE_AVG_RELIEF["ip"]
    proj.proj_k = (base_k_per_9 / 9) * proj.proj_ip
    proj.proj_bb = (base_bb_per_9 / 9) * proj.proj_ip
    proj.proj_hr = LEAGUE_AVG_RELIEF["hr"]
    proj.proj_hbp = LEAGUE_AVG_RELIEF["hbp"]

    # Save/hold expectations
    if is_closer:
        proj.proj_sv = save_prob * 0.85  # 85% conversion
        proj.adjustments["Save Opportunity"] = proj.proj_sv * PITCHER_SCORING["SV"]
    elif is_setup:
        proj.proj_hld = hold_prob * 0.90  # 90% conversion
        proj.adjustments["Hold Opportunity"] = proj.proj_hld * PITCHER_SCORING["HLD"]

    # Fatigue penalty
    if consecutive_days >= 3:
        # 2 mph velocity drop = big performance hit
        proj.proj_k -= 0.3
        proj.proj_hr += 0.05
        proj.adjustments["Fatigue (3+ days)"] = (
            -0.3 * PITCHER_SCORING["K"] + 0.05 * PITCHER_SCORING["HR"]
        )
    elif consecutive_days == 2:
        proj.proj_k -= 0.1
        proj.adjustments["Fatigue (2 days)"] = -0.1 * PITCHER_SCORING["K"]

    # Ensure no negatives
    proj.proj_k = max(0, proj.proj_k)
    proj.proj_hr = max(0, proj.proj_hr)

    proj.calculate_points()
    return proj


def compare_streamers(
    options: list,
    opponent_map: dict = None,
) -> list:
    """
    Compare multiple streaming options.

    Args:
        options: List of dicts with pitcher info
                 [{"name": str, "team": str, "opponent": str, "is_home": bool, ...}]
        opponent_map: Override opponent stats if needed

    Returns:
        Sorted list of projections (best first)
    """
    projections = []

    for opt in options:
        proj = project_starter(
            pitcher_name=opt["name"],
            team=opt["team"],
            opponent=opt["opponent"],
            is_home=opt.get("is_home", True),
            base_ip=opt.get("ip"),
            base_k_per_9=opt.get("k_per_9"),
            base_bb_per_9=opt.get("bb_per_9"),
            base_hr_per_9=opt.get("hr_per_9"),
            weather_hrfi=opt.get("hrfi"),
        )
        projections.append(proj)

    return sorted(projections, key=lambda x: x.expected_points, reverse=True)


# =============================================================================
# QUICK PROJECTION HELPERS
# =============================================================================

def quick_stream_score(opponent: str, is_home: bool = True, park: str = None) -> float:
    """
    Quick expected points estimate for a league-average pitcher.

    Useful for fast comparisons without full pitcher data.
    """
    proj = project_starter(
        pitcher_name="League Average",
        team=park or opponent,
        opponent=opponent,
        is_home=is_home,
    )
    return proj.expected_points


def rank_opponents_by_expected_points() -> list:
    """Rank all opponents by expected points for a league-average pitcher."""
    from streaming import TEAM_IDS

    rankings = []
    for team in TEAM_IDS.keys():
        pts = quick_stream_score(opponent=team, is_home=True)
        rankings.append((team, pts))

    return sorted(rankings, key=lambda x: x[1], reverse=True)


if __name__ == "__main__":
    print("=== BLJ X POINTS PROJECTOR ===\n")

    # Example: Compare streaming options
    print("EXAMPLE PROJECTIONS:\n")

    # Great matchup: vs OAK at home
    proj1 = project_starter(
        pitcher_name="Stream Option A",
        team="SF",  # Gets Patrick Bailey framing bonus
        opponent="OAK",
        is_home=True,
        base_ip=5.5,
        base_k_per_9=8.5,
        base_bb_per_9=3.0,
        base_hr_per_9=1.2,
    )
    print(proj1.summary())

    print("\n" + "=" * 50 + "\n")

    # Risky matchup: @ LAD (HR park)
    proj2 = project_starter(
        pitcher_name="Stream Option B",
        team="COL",
        opponent="LAD",  # Bad HR park
        is_home=False,
        base_ip=5.0,
        base_k_per_9=7.5,
        base_bb_per_9=3.5,
        base_hr_per_9=1.4,
    )
    print(proj2.summary())

    print("\n" + "=" * 50 + "\n")

    # Opponent rankings
    print("OPPONENT RANKINGS (League Avg Pitcher at Home):\n")
    rankings = rank_opponents_by_expected_points()
    print("BEST MATCHUPS:")
    for team, pts in rankings[:5]:
        print(f"  vs {team}: {pts:.1f} expected pts")

    print("\nWORST MATCHUPS:")
    for team, pts in rankings[-5:]:
        print(f"  vs {team}: {pts:.1f} expected pts")
