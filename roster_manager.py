"""
Roster Manager for BLJ X

Tracks your roster, exclusion list (never drop), and droppable tiers.
Foundation for the weekly add optimizer.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, date


class Position(Enum):
    C = "C"
    FIRST = "1B"
    SECOND = "2B"
    THIRD = "3B"
    SS = "SS"
    OF = "OF"
    UTIL = "Util"
    SP = "SP"
    RP = "RP"
    P = "P"
    BN = "BN"
    IL = "IL"
    NA = "NA"


class DropTier(Enum):
    """How droppable is this player?"""
    UNTOUCHABLE = 0      # Never drop (aces, stars)
    HOLD = 1             # Wouldn't drop for streamers
    RELUCTANT = 2        # Would drop only for great opportunity
    DROPPABLE = 3        # Fine to drop for streamers
    STREAMER = 4         # Actively looking to replace


class ILStatus(Enum):
    ACTIVE = "Active"
    IL10 = "10-Day IL"
    IL60 = "60-Day IL"
    DTD = "Day-to-Day"
    SUSP = "Suspended"
    NA = "NA"            # Minors


@dataclass
class Player:
    """A player on your roster or available."""
    name: str
    player_id: Optional[int] = None  # MLB/Yahoo ID
    team: str = ""
    position: str = ""               # Primary position
    eligible_positions: list = field(default_factory=list)

    # Status
    il_status: ILStatus = ILStatus.ACTIVE
    expected_return: Optional[date] = None

    # Your roster info
    roster_position: Optional[Position] = None  # Where slotted on your team
    drop_tier: DropTier = DropTier.DROPPABLE

    # For pitchers
    is_pitcher: bool = False
    is_starter: bool = False
    next_start: Optional[date] = None
    second_start: Optional[date] = None  # For 2-start weeks

    # Stats (for valuation)
    season_points: float = 0.0
    points_per_game: float = 0.0

    def is_droppable_for_streamer(self) -> bool:
        """Can this player be dropped for a streaming pitcher?"""
        return self.drop_tier.value >= DropTier.DROPPABLE.value

    def is_on_il(self) -> bool:
        """Is player currently on IL?"""
        return self.il_status in [ILStatus.IL10, ILStatus.IL60, ILStatus.NA]

    def is_injured(self) -> bool:
        """Is player injured or IL-eligible?"""
        return self.il_status != ILStatus.ACTIVE


@dataclass
class Roster:
    """Your fantasy roster."""
    team_name: str = "My Team"
    league_id: str = "89318"  # BLJ X

    # Roster slots (BLJ X configuration)
    max_roster: int = 27  # 11 batters + 8 pitchers + 6 bench + 2 IL
    batter_slots: int = 11
    pitcher_slots: int = 8
    bench_slots: int = 6
    il_slots: int = 4
    na_slots: int = 2

    # Weekly limits
    adds_per_week: int = 5
    adds_used: int = 0
    week_start: Optional[date] = None

    # Players
    players: list = field(default_factory=list)

    # Exclusion list (never drop these player names)
    exclusion_list: list = field(default_factory=list)

    def add_player(self, player: Player):
        """Add a player to roster."""
        # Check if in exclusion list
        if player.name in self.exclusion_list:
            player.drop_tier = DropTier.UNTOUCHABLE
        self.players.append(player)

    def remove_player(self, player_name: str) -> Optional[Player]:
        """Remove a player from roster."""
        for i, p in enumerate(self.players):
            if p.name == player_name:
                return self.players.pop(i)
        return None

    def get_player(self, player_name: str) -> Optional[Player]:
        """Get a player by name."""
        for p in self.players:
            if p.name.lower() == player_name.lower():
                return p
        return None

    def get_pitchers(self) -> list:
        """Get all pitchers on roster."""
        return [p for p in self.players if p.is_pitcher]

    def get_batters(self) -> list:
        """Get all batters on roster."""
        return [p for p in self.players if not p.is_pitcher]

    def get_droppable_players(self, for_streamer: bool = True) -> list:
        """Get players that can be dropped."""
        if for_streamer:
            # For streamers, only drop DROPPABLE or STREAMER tier
            return [p for p in self.players
                    if p.drop_tier.value >= DropTier.DROPPABLE.value
                    and not p.is_on_il()]
        else:
            # For regular adds, include RELUCTANT tier
            return [p for p in self.players
                    if p.drop_tier.value >= DropTier.RELUCTANT.value
                    and not p.is_on_il()]

    def get_streamers(self) -> list:
        """Get current streaming pitchers."""
        return [p for p in self.players
                if p.is_pitcher and p.drop_tier == DropTier.STREAMER]

    def get_il_players(self) -> list:
        """Get players on IL."""
        return [p for p in self.players if p.is_on_il()]

    def get_dtd_players(self) -> list:
        """Get day-to-day players (might need IL stint)."""
        return [p for p in self.players if p.il_status == ILStatus.DTD]

    def get_returning_soon(self, days: int = 7) -> list:
        """Get IL players expected back within X days."""
        today = date.today()
        returning = []
        for p in self.get_il_players():
            if p.expected_return:
                days_until = (p.expected_return - today).days
                if 0 <= days_until <= days:
                    returning.append((p, days_until))
        return sorted(returning, key=lambda x: x[1])

    def adds_remaining(self) -> int:
        """How many adds left this week?"""
        return self.adds_per_week - self.adds_used

    def use_add(self):
        """Use one weekly add."""
        self.adds_used += 1

    def reset_weekly_adds(self):
        """Reset adds for new week."""
        self.adds_used = 0
        self.week_start = date.today()

    def can_drop_for_streamer(self, exclude_pitching_tomorrow: bool = True,
                               tomorrow: Optional[date] = None) -> list:
        """
        Get list of players that can be dropped tonight for a streamer.

        Args:
            exclude_pitching_tomorrow: Don't drop pitchers starting tomorrow
            tomorrow: Tomorrow's date (for checking starts)
        """
        droppable = self.get_droppable_players(for_streamer=True)

        if exclude_pitching_tomorrow and tomorrow:
            # Filter out pitchers with starts tomorrow
            droppable = [p for p in droppable
                        if not (p.is_pitcher and p.next_start == tomorrow)]

        return droppable

    def set_exclusion_list(self, player_names: list):
        """Set the never-drop list."""
        self.exclusion_list = player_names
        # Update existing players
        for p in self.players:
            if p.name in self.exclusion_list:
                p.drop_tier = DropTier.UNTOUCHABLE

    def summary(self) -> str:
        """Print roster summary."""
        lines = [
            f"=== {self.team_name} ===",
            f"League: BLJ X ({self.league_id})",
            f"Adds: {self.adds_remaining()}/{self.adds_per_week} remaining",
            "",
            "PITCHERS:",
        ]

        for p in sorted(self.get_pitchers(), key=lambda x: x.drop_tier.value):
            status = f" [{p.il_status.value}]" if p.is_injured() else ""
            tier = f"({p.drop_tier.name})"
            lines.append(f"  {p.name} - {p.team}{status} {tier}")

        lines.append("\nBATTERS:")
        for p in sorted(self.get_batters(), key=lambda x: x.drop_tier.value):
            status = f" [{p.il_status.value}]" if p.is_injured() else ""
            tier = f"({p.drop_tier.name})"
            lines.append(f"  {p.name} - {p.team} ({p.position}){status} {tier}")

        # IL returns
        returning = self.get_returning_soon(7)
        if returning:
            lines.append("\nIL RETURNS (next 7 days):")
            for p, days in returning:
                lines.append(f"  {p.name} - {days} days")

        return "\n".join(lines)


# =============================================================================
# EXAMPLE ROSTER SETUP
# =============================================================================

def create_example_roster() -> Roster:
    """Create an example roster for testing."""
    roster = Roster(team_name="Vlad The Impaler")

    # Set exclusion list (never drop these)
    roster.set_exclusion_list([
        "Shohei Ohtani",
        "Juan Soto",
        "Corbin Carroll",
        "Bobby Witt Jr.",
        "Gunnar Henderson",
    ])

    # Example pitchers
    pitchers = [
        Player(name="Zack Wheeler", team="PHI", is_pitcher=True, is_starter=True,
               drop_tier=DropTier.UNTOUCHABLE),
        Player(name="Logan Webb", team="SF", is_pitcher=True, is_starter=True,
               drop_tier=DropTier.HOLD),
        Player(name="Pablo Lopez", team="MIN", is_pitcher=True, is_starter=True,
               drop_tier=DropTier.HOLD),
        Player(name="Bryan Abreu", team="HOU", is_pitcher=True, is_starter=False,
               drop_tier=DropTier.HOLD),  # Elite setup man
        Player(name="Some Streamer", team="OAK", is_pitcher=True, is_starter=True,
               drop_tier=DropTier.STREAMER),
        Player(name="Another Streamer", team="CHW", is_pitcher=True, is_starter=True,
               drop_tier=DropTier.STREAMER),
    ]

    # Example batters
    batters = [
        Player(name="Shohei Ohtani", team="LAD", position="DH",
               drop_tier=DropTier.UNTOUCHABLE),
        Player(name="Juan Soto", team="NYM", position="OF",
               drop_tier=DropTier.UNTOUCHABLE),
        Player(name="Bobby Witt Jr.", team="KC", position="SS",
               drop_tier=DropTier.UNTOUCHABLE),
        Player(name="Bench Bat 1", team="TBD", position="OF",
               drop_tier=DropTier.DROPPABLE),
        Player(name="Bench Bat 2", team="TBD", position="1B",
               drop_tier=DropTier.DROPPABLE),
    ]

    for p in pitchers + batters:
        roster.add_player(p)

    return roster


if __name__ == "__main__":
    roster = create_example_roster()
    print(roster.summary())

    print("\n" + "=" * 50)
    print("\nDROPPABLE FOR STREAMING:")
    for p in roster.can_drop_for_streamer():
        print(f"  {p.name} ({p.drop_tier.name})")

    print("\n" + "=" * 50)
    print(f"\nADDS REMAINING: {roster.adds_remaining()}")
