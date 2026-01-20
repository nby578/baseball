"""
Big League Jew X (2025) - Draft Results
League ID: 89318
Draft Type: Snake Draft, 25 Rounds, 12 Teams

This is STATE 0 - Initial roster state after draft.
Combined with transactions, we can reconstruct any team at any point.

Note: Keepers are included in draft picks (typically later rounds for good players)
      Look for elite players in late rounds = likely keepers
"""

# Team mapping (draft order -> team name)
TEAMS = {
    1: "THE UNCLE NOAH",
    2: "Schanuel And...",  # Full name truncated in source
    3: "Place Your B...",
    4: "Japanese Nat...",
    5: "Melech ha Ba...",
    6: "OJ Simpson",
    7: "carlosc's Sw...",
    8: "Bach & Veovaldi",
    9: "Skene'd Alive",
    10: "Vlad The Imp...",  # USER'S TEAM
    11: "Sasaki Bohms",
    12: "A-A-Ron",
}

# Snake draft order helper
def get_pick_team(round_num: int, pick_in_round: int) -> int:
    """Returns team number (1-12) for a given round and pick."""
    if round_num % 2 == 1:  # Odd rounds: 1-12
        return pick_in_round
    else:  # Even rounds: 12-1
        return 13 - pick_in_round


# Complete draft results: (round, pick, player_name, team_name)
DRAFT_PICKS = [
    # Round 1
    (1, 1, "Jackson Chourio", "THE UNCLE NOAH"),
    (1, 2, "Manny Machado", "Schanuel And..."),
    (1, 3, "Bryce Harper", "Place Your B..."),
    (1, 4, "Corey Seager", "Japanese Nat..."),
    (1, 5, "Jackson Merrill", "Melech ha Ba..."),
    (1, 6, "Jacob deGrom", "OJ Simpson"),
    (1, 7, "Rafael Devers", "carlosc's Sw..."),
    (1, 8, "Ketel Marte", "Bach & Veovaldi"),
    (1, 9, "Kyle Schwarber", "Skene'd Alive"),
    (1, 10, "Oneil Cruz", "Vlad The Imp..."),
    (1, 11, "Aaron Nola", "Sasaki Bohms"),
    (1, 12, "Pete Alonso", "A-A-Ron"),

    # Round 2
    (2, 1, "Ronald Acuña Jr.", "A-A-Ron"),
    (2, 2, "CJ Abrams", "Sasaki Bohms"),
    (2, 3, "Brent Rooker", "Vlad The Imp..."),
    (2, 4, "Marcell Ozuna", "Skene'd Alive"),
    (2, 5, "Anthony Santander", "Bach & Veovaldi"),
    (2, 6, "Michael Harris II", "carlosc's Sw..."),
    (2, 7, "Teoscar Hernández", "OJ Simpson"),
    (2, 8, "Shota Imanaga", "Melech ha Ba..."),
    (2, 9, "Edwin Díaz", "Japanese Nat..."),
    (2, 10, "Wyatt Langford", "Place Your B..."),
    (2, 11, "Josh Hader", "Schanuel And..."),
    (2, 12, "Jose Altuve", "THE UNCLE NOAH"),

    # Round 3
    (3, 1, "Mason Miller", "THE UNCLE NOAH"),
    (3, 2, "James Wood", "Schanuel And..."),
    (3, 3, "Brenton Doyle", "Place Your B..."),
    (3, 4, "Josh Naylor", "Japanese Nat..."),
    (3, 5, "Raisel Iglesias", "Melech ha Ba..."),
    (3, 6, "Cody Bellinger", "OJ Simpson"),
    (3, 7, "Ryan Helsley", "carlosc's Sw..."),
    (3, 8, "Alex Bregman", "Bach & Veovaldi"),
    (3, 9, "Sonny Gray", "Skene'd Alive"),
    (3, 10, "Adley Rutschman", "Vlad The Imp..."),
    (3, 11, "Roki Sasaki", "Sasaki Bohms"),
    (3, 12, "Lawrence Butler", "A-A-Ron"),

    # Round 4
    (4, 1, "Luis Castillo", "A-A-Ron"),
    (4, 2, "Matt McLain", "Sasaki Bohms"),
    (4, 3, "Willy Adames", "Vlad The Imp..."),
    (4, 4, "Spencer Strider", "Skene'd Alive"),
    (4, 5, "Ezequiel Tovar", "Bach & Veovaldi"),
    (4, 6, "Bailey Ober", "carlosc's Sw..."),
    (4, 7, "Hunter Brown", "OJ Simpson"),
    (4, 8, "Tanner Bibee", "Melech ha Ba..."),
    (4, 9, "Bryan Reynolds", "Japanese Nat..."),
    (4, 10, "Ryan Walker", "Place Your B..."),
    (4, 11, "Zac Gallen", "Schanuel And..."),
    (4, 12, "Mark Vientos", "THE UNCLE NOAH"),

    # Round 5
    (5, 1, "Christian Walker", "THE UNCLE NOAH"),
    (5, 2, "Triston Casas", "Schanuel And..."),
    (5, 3, "Joe Ryan", "Place Your B..."),
    (5, 4, "Seiya Suzuki", "Japanese Nat..."),
    (5, 5, "Bo Bichette", "Melech ha Ba..."),
    (5, 6, "Willson Contreras", "OJ Simpson"),
    (5, 7, "Junior Caminero", "carlosc's Sw..."),
    (5, 8, "Cristopher Sánchez", "Bach & Veovaldi"),
    (5, 9, "Justin Steele", "Skene'd Alive"),
    (5, 10, "Félix Bautista", "Vlad The Imp..."),
    (5, 11, "Jake Burger", "Sasaki Bohms"),
    (5, 12, "Jordan Westburg", "A-A-Ron"),

    # Round 6
    (6, 1, "Riley Greene", "A-A-Ron"),
    (6, 2, "Jhoan Duran", "Sasaki Bohms"),
    (6, 3, "Luis Robert Jr.", "Vlad The Imp..."),
    (6, 4, "Matt Chapman", "Skene'd Alive"),
    (6, 5, "Seth Lugo", "Bach & Veovaldi"),
    (6, 6, "Salvador Perez", "carlosc's Sw..."),
    (6, 7, "Mike Trout", "OJ Simpson"),
    (6, 8, "Cal Raleigh", "Melech ha Ba..."),
    (6, 9, "George Kirby", "Japanese Nat..."),
    (6, 10, "Vinnie Pasquantino", "Place Your B..."),
    (6, 11, "Will Smith", "Schanuel And..."),
    (6, 12, "Hunter Greene", "THE UNCLE NOAH"),

    # Round 7
    (7, 1, "Shane McClanahan", "THE UNCLE NOAH"),
    (7, 2, "Xander Bogaerts", "Schanuel And..."),
    (7, 3, "Tanner Scott", "Place Your B..."),
    (7, 4, "Kevin Gausman", "Japanese Nat..."),
    (7, 5, "Randy Arozarena", "Melech ha Ba..."),
    (7, 6, "Anthony Volpe", "OJ Simpson"),
    (7, 7, "Xavier Edwards", "carlosc's Sw..."),
    (7, 8, "Tanner Houck", "Bach & Veovaldi"),
    (7, 9, "Ian Happ", "Skene'd Alive"),
    (7, 10, "Yainer Diaz", "Vlad The Imp..."),
    (7, 11, "Alec Bohm", "Sasaki Bohms"),
    (7, 12, "Sandy Alcantara", "A-A-Ron"),

    # Round 8
    (8, 1, "Clay Holmes", "A-A-Ron"),
    (8, 2, "Jeff Hoffman", "Sasaki Bohms"),
    (8, 3, "Royce Lewis", "Vlad The Imp..."),
    (8, 4, "Jack Flaherty", "Skene'd Alive"),
    (8, 5, "Taylor Ward", "Bach & Veovaldi"),
    (8, 6, "Steven Kwan", "carlosc's Sw..."),
    (8, 7, "Kodai Senga", "OJ Simpson"),
    (8, 8, "Brandon Nimmo", "Melech ha Ba..."),
    (8, 9, "Ryan Pressly", "Japanese Nat..."),
    (8, 10, "Bryan Woo", "Place Your B..."),
    (8, 11, "Nick Pivetta", "Schanuel And..."),
    (8, 12, "Dylan Crews", "THE UNCLE NOAH"),

    # Round 9
    (9, 1, "Christian Yelich", "THE UNCLE NOAH"),
    (9, 2, "Trevor Megill", "Schanuel And..."),
    (9, 3, "Adolis García", "Place Your B..."),
    (9, 4, "Luis Arraez", "Japanese Nat..."),
    (9, 5, "Luis García Jr.", "Melech ha Ba..."),
    (9, 6, "Eugenio Suárez", "OJ Simpson"),
    (9, 7, "Carlos Rodón", "carlosc's Sw..."),
    (9, 8, "Reynaldo López", "Bach & Veovaldi"),
    (9, 9, "Brandon Pfaadt", "Skene'd Alive"),
    (9, 10, "Robbie Ray", "Vlad The Imp..."),
    (9, 11, "Zach Eflin", "Sasaki Bohms"),
    (9, 12, "Isaac Paredes", "A-A-Ron"),

    # Round 10
    (10, 1, "Shea Langeliers", "A-A-Ron"),
    (10, 2, "Austin Wells", "Sasaki Bohms"),
    (10, 3, "Nick Castellanos", "Vlad The Imp..."),
    (10, 4, "Jurickson Profar", "Skene'd Alive"),
    (10, 5, "Jorge Soler", "Bach & Veovaldi"),
    (10, 6, "J.T. Realmuto", "carlosc's Sw..."),
    (10, 7, "Pete Crow-Armstrong", "OJ Simpson"),
    (10, 8, "Josh Lowe", "Melech ha Ba..."),
    (10, 9, "David Bednar", "Japanese Nat..."),
    (10, 10, "Dansby Swanson", "Place Your B..."),
    (10, 11, "Paul Goldschmidt", "Schanuel And..."),
    (10, 12, "Masyn Winn", "THE UNCLE NOAH"),

    # Round 11
    (11, 1, "Nico Hoerner", "THE UNCLE NOAH"),
    (11, 2, "Yusei Kikuchi", "Schanuel And..."),
    (11, 3, "Jasson Domínguez", "Place Your B..."),
    (11, 4, "Logan O'Hoppe", "Japanese Nat..."),
    (11, 5, "Colton Cowser", "Melech ha Ba..."),
    (11, 6, "Jeremy Peña", "OJ Simpson"),
    (11, 7, "Brice Turang", "carlosc's Sw..."),
    (11, 8, "Yandy Díaz", "Bach & Veovaldi"),
    (11, 9, "Michael Toglia", "Skene'd Alive"),
    (11, 10, "Carlos Estévez", "Vlad The Imp..."),
    (11, 11, "Lane Thomas", "Sasaki Bohms"),
    (11, 12, "José Berríos", "A-A-Ron"),

    # Round 12
    (12, 1, "Jordan Romano", "A-A-Ron"),
    (12, 2, "Kenley Jansen", "Sasaki Bohms"),
    (12, 3, "Andrés Giménez", "Vlad The Imp..."),
    (12, 4, "MacKenzie Gore", "Skene'd Alive"),
    (12, 5, "Nathan Eovaldi", "Bach & Veovaldi"),
    (12, 6, "Pete Fairbanks", "carlosc's Sw..."),
    (12, 7, "Tommy Edman", "OJ Simpson"),
    (12, 8, "Spencer Steer", "Melech ha Ba..."),
    (12, 9, "Lourdes Gurriel Jr.", "Japanese Nat..."),
    (12, 10, "Ryan Pepiot", "Place Your B..."),
    (12, 11, "Gleyber Torres", "Schanuel And..."),
    (12, 12, "Gabriel Moreno", "THE UNCLE NOAH"),

    # Round 13
    (13, 1, "Jared Jones", "THE UNCLE NOAH"),
    (13, 2, "Heliot Ramos", "Schanuel And..."),
    (13, 3, "Nolan Arenado", "Place Your B..."),
    (13, 4, "Kerry Carpenter", "Japanese Nat..."),
    (13, 5, "Tyler O'Neill", "Melech ha Ba..."),
    (13, 6, "Kyle Finnegan", "OJ Simpson"),
    (13, 7, "Nick Lodolo", "carlosc's Sw..."),
    (13, 8, "Mitch Keller", "Bach & Veovaldi"),
    (13, 9, "Spencer Arrighetti", "Skene'd Alive"),
    (13, 10, "Kirby Yates", "Vlad The Imp..."),
    (13, 11, "Cedric Mullins", "Sasaki Bohms"),
    (13, 12, "Zach Neto", "A-A-Ron"),

    # Round 14
    (14, 1, "Alexis Díaz", "A-A-Ron"),
    (14, 2, "Max Muncy", "Sasaki Bohms"),
    (14, 3, "Michael Wacha", "Vlad The Imp..."),
    (14, 4, "Matt Shaw", "Skene'd Alive"),
    (14, 5, "Carlos Correa", "Bach & Veovaldi"),
    (14, 6, "Bowden Francis", "carlosc's Sw..."),
    (14, 7, "Bryson Stott", "OJ Simpson"),
    (14, 8, "Alec Burleson", "Melech ha Ba..."),
    (14, 9, "TJ Friedl", "Japanese Nat..."),
    (14, 10, "Ivan Herrera", "Place Your B..."),
    (14, 11, "Justin Martinez", "Schanuel And..."),
    (14, 12, "Aroldis Chapman", "THE UNCLE NOAH"),

    # Round 15
    (15, 1, "Jackson Jobe", "THE UNCLE NOAH"),
    (15, 2, "Max Scherzer", "Schanuel And..."),
    (15, 3, "Lucas Erceg", "Place Your B..."),
    (15, 4, "Merrill Kelly", "Japanese Nat..."),
    (15, 5, "Gavin Williams", "Melech ha Ba..."),
    (15, 6, "Ryan Mountcastle", "OJ Simpson"),
    (15, 7, "Jonathan India", "carlosc's Sw..."),
    (15, 8, "Erick Fedde", "Bach & Veovaldi"),
    (15, 9, "Jackson Holliday", "Skene'd Alive"),
    (15, 10, "Drew Rasmussen", "Vlad The Imp..."),
    (15, 11, "Jesús Luzardo", "Sasaki Bohms"),
    (15, 12, "Nathaniel Lowe", "A-A-Ron"),

    # Round 16
    (16, 1, "Shane Baz", "A-A-Ron"),
    (16, 2, "Taj Bradley", "Sasaki Bohms"),
    (16, 3, "A.J. Puk", "Vlad The Imp..."),
    (16, 4, "Ryan Jeffers", "Skene'd Alive"),
    (16, 5, "Nestor Cortes", "Bach & Veovaldi"),
    (16, 6, "Josh Jung", "carlosc's Sw..."),
    (16, 7, "Tyler Stephenson", "OJ Simpson"),
    (16, 8, "Ceddanne Rafaela", "Melech ha Ba..."),
    (16, 9, "Reese Olson", "Japanese Nat..."),
    (16, 10, "Jake McCarthy", "Place Your B..."),
    (16, 11, "Willi Castro", "Schanuel And..."),
    (16, 12, "George Springer", "THE UNCLE NOAH"),

    # Round 17
    (17, 1, "Rhys Hoskins", "THE UNCLE NOAH"),
    (17, 2, "Nolan Jones", "Schanuel And..."),
    (17, 3, "Victor Robles", "Place Your B..."),
    (17, 4, "Shohei Ohtani (Pitcher)", "Japanese Nat..."),
    (17, 5, "Brandon Lowe", "Melech ha Ba..."),
    (17, 6, "Michael Conforto", "OJ Simpson"),
    (17, 7, "Christian Encarnacion-Strand", "carlosc's Sw..."),
    (17, 8, "Joc Pederson", "Bach & Veovaldi"),
    (17, 9, "Grant Holmes", "Skene'd Alive"),
    (17, 10, "Ronel Blanco", "Vlad The Imp..."),
    (17, 11, "Michael Busch", "Sasaki Bohms"),
    (17, 12, "JJ Bleday", "A-A-Ron"),

    # Round 18
    (18, 1, "Brendan Donovan", "A-A-Ron"),
    (18, 2, "Clarke Schmidt", "Sasaki Bohms"),
    (18, 3, "Sean Manaea", "Vlad The Imp..."),
    (18, 4, "Brandon Woodruff", "Skene'd Alive"),
    (18, 5, "Jason Foley", "Bach & Veovaldi"),
    (18, 6, "Thairo Estrada", "carlosc's Sw..."),
    (18, 7, "Jason Adam", "OJ Simpson"),
    (18, 8, "Byron Buxton", "Melech ha Ba..."),
    (18, 9, "Luis Rengifo", "Japanese Nat..."),
    (18, 10, "Trevor Story", "Place Your B..."),
    (18, 11, "Chris Martin", "Schanuel And..."),
    (18, 12, "Parker Meadows", "THE UNCLE NOAH"),

    # Round 19
    (19, 1, "Tyler Fitzgerald", "THE UNCLE NOAH"),
    (19, 2, "Patrick Bailey", "Schanuel And..."),
    (19, 3, "Tyler Soderstrom", "Place Your B..."),
    (19, 4, "Andrew Vaughn", "Japanese Nat..."),
    (19, 5, "Yu Darvish", "Melech ha Ba..."),
    (19, 6, "Walker Buehler", "OJ Simpson"),
    (19, 7, "Garrett Mitchell", "carlosc's Sw..."),
    (19, 8, "Calvin Faucher", "Bach & Veovaldi"),
    (19, 9, "Grayson Rodriguez", "Skene'd Alive"),
    (19, 10, "Beau Brieske", "Vlad The Imp..."),
    (19, 11, "Hayden Birdsong", "Sasaki Bohms"),
    (19, 12, "Jung Hoo Lee", "A-A-Ron"),

    # Round 20
    (20, 1, "Colson Montgomery", "A-A-Ron"),
    (20, 2, "Jacob Misiorowski", "Sasaki Bohms"),
    (20, 3, "Braxton Ashcraft", "Vlad The Imp..."),
    (20, 4, "Kristian Campbell", "Skene'd Alive"),
    (20, 5, "Bryan Abreu", "Bach & Veovaldi"),
    (20, 6, "Joey Bart", "carlosc's Sw..."),
    (20, 7, "Justin Verlander", "OJ Simpson"),
    (20, 8, "Ben Joyce", "Melech ha Ba..."),
    (20, 9, "Ryan McMahon", "Japanese Nat..."),
    (20, 10, "Zack Gelof", "Place Your B..."),
    (20, 11, "Nolan Schanuel", "Schanuel And..."),
    (20, 12, "Connor Norby", "THE UNCLE NOAH"),

    # Round 21 - KEEPER ROUND (elite players appearing = keepers)
    (21, 1, "Maikel Garcia", "THE UNCLE NOAH"),
    (21, 2, "Max Fried", "Schanuel And..."),
    (21, 3, "Ranger Suárez", "Place Your B..."),
    (21, 4, "Garrett Crochet", "Japanese Nat..."),
    (21, 5, "Andrés Muñoz", "Melech ha Ba..."),
    (21, 6, "Robert Suarez", "OJ Simpson"),
    (21, 7, "Tyler Glasnow", "carlosc's Sw..."),
    (21, 8, "Spencer Schwellenbach", "Bach & Veovaldi"),
    (21, 9, "Elly De La Cruz", "Skene'd Alive"),
    (21, 10, "Zack Wheeler", "Vlad The Imp..."),  # KEEPER!
    (21, 11, "Bryce Miller", "Sasaki Bohms"),
    (21, 12, "J.T. Ginn", "A-A-Ron"),

    # Round 22 - KEEPER ROUND
    (22, 1, "Pablo López", "A-A-Ron"),
    (22, 2, "Logan Webb", "Sasaki Bohms"),
    (22, 3, "Cole Ragans", "Vlad The Imp..."),  # KEEPER!
    (22, 4, "Cade Horton", "Skene'd Alive"),
    (22, 5, "Framber Valdez", "Bach & Veovaldi"),
    (22, 6, "Emmanuel Clase", "carlosc's Sw..."),
    (22, 7, "Blake Snell", "OJ Simpson"),
    (22, 8, "Corbin Burnes", "Melech ha Ba..."),
    (22, 9, "Andrew Painter", "Japanese Nat..."),
    (22, 10, "Dylan Cease", "Place Your B..."),
    (22, 11, "Logan Gilbert", "Schanuel And..."),
    (22, 12, "Freddy Peralta", "THE UNCLE NOAH"),

    # Round 23 - KEEPER ROUND
    (23, 1, "Devin Williams", "THE UNCLE NOAH"),
    (23, 2, "Roman Anthony", "Schanuel And..."),
    (23, 3, "Chris Sale", "Place Your B..."),
    (23, 4, "Yoshinobu Yamamoto", "Japanese Nat..."),
    (23, 5, "Samuel Basallo", "Melech ha Ba..."),
    (23, 6, "Miguel Bleis", "OJ Simpson"),
    (23, 7, "Chase DeLauter", "carlosc's Sw..."),
    (23, 8, "Marcelo Mayer", "Bach & Veovaldi"),
    (23, 9, "Paul Skenes", "Skene'd Alive"),
    (23, 10, "Matt Olson", "Vlad The Imp..."),  # KEEPER!
    (23, 11, "Diego Cartaya", "Sasaki Bohms"),
    (23, 12, "Michael King", "A-A-Ron"),

    # Round 24 - KEEPER ROUND (most elite players here)
    (24, 1, "Gunnar Henderson", "A-A-Ron"),
    (24, 2, "Jarren Duran", "Sasaki Bohms"),
    (24, 3, "Jordan Lawlar", "Vlad The Imp..."),  # KEEPER!
    (24, 4, "Tarik Skubal", "Skene'd Alive"),
    (24, 5, "William Contreras", "Bach & Veovaldi"),
    (24, 6, "Yordan Alvarez", "carlosc's Sw..."),
    (24, 7, "Ozzie Albies", "OJ Simpson"),
    (24, 8, "Austin Riley", "Melech ha Ba..."),
    (24, 9, "Marcus Semien", "Japanese Nat..."),
    (24, 10, "Mookie Betts", "Place Your B..."),
    (24, 11, "Julio Rodríguez", "Schanuel And..."),
    (24, 12, "Kyle Tucker", "THE UNCLE NOAH"),

    # Round 25 - KEEPER ROUND (elite players = keepers)
    (25, 1, "José Ramírez", "THE UNCLE NOAH"),
    (25, 2, "Francisco Lindor", "Schanuel And..."),
    (25, 3, "Bobby Witt Jr.", "Place Your B..."),
    (25, 4, "Jazz Chisholm Jr.", "Japanese Nat..."),
    (25, 5, "Trea Turner", "Melech ha Ba..."),
    (25, 6, "Shohei Ohtani (Batter)", "OJ Simpson"),
    (25, 7, "Fernando Tatis Jr.", "carlosc's Sw..."),
    (25, 8, "Freddie Freeman", "Bach & Veovaldi"),
    (25, 9, "Corbin Carroll", "Skene'd Alive"),
    (25, 10, "Vladimir Guerrero Jr.", "Vlad The Imp..."),  # KEEPER!
    (25, 11, "Juan Soto", "Sasaki Bohms"),
    (25, 12, "Aaron Judge", "A-A-Ron"),
]


def get_team_roster(team_name: str) -> list:
    """Get initial roster for a team after draft."""
    return [(r, p, player) for r, p, player, team in DRAFT_PICKS if team == team_name]


def get_user_team_roster() -> list:
    """Get Vlad The Impaler's initial roster."""
    return get_team_roster("Vlad The Imp...")


# Likely keepers for Vlad The Impaler (elite players in late rounds):
# - Round 21: Zack Wheeler (ace pitcher)
# - Round 22: Cole Ragans (breakout pitcher)
# - Round 23: Matt Olson (elite 1B)
# - Round 24: Jordan Lawlar (top prospect)
# - Round 25: Vladimir Guerrero Jr. (elite 1B)

VLAD_KEEPERS = {
    "batters": ["Vladimir Guerrero Jr.", "Matt Olson"],  # 2 batter keepers
    "pitchers": ["Zack Wheeler", "Cole Ragans"],  # 2 pitcher keepers
}


if __name__ == "__main__":
    print("=" * 60)
    print("BIG LEAGUE JEW X (2025) - DRAFT RESULTS")
    print("=" * 60)

    print("\n12 TEAMS:")
    for num, name in TEAMS.items():
        marker = " <-- USER'S TEAM" if num == 10 else ""
        print(f"  {num:2}. {name}{marker}")

    print("\n" + "=" * 60)
    print("VLAD THE IMPALER - INITIAL ROSTER (25 players)")
    print("=" * 60)

    roster = get_user_team_roster()
    for round_num, pick, player in roster:
        keeper_mark = " *** KEEPER" if player in VLAD_KEEPERS["batters"] + VLAD_KEEPERS["pitchers"] else ""
        print(f"  Round {round_num:2}, Pick {pick:2}: {player}{keeper_mark}")

    print(f"\nTotal players: {len(roster)}")
    print(f"\nLikely Keepers:")
    print(f"  Batters: {VLAD_KEEPERS['batters']}")
    print(f"  Pitchers: {VLAD_KEEPERS['pitchers']}")
