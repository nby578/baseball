# Yahoo Fantasy API Reference

Compiled from official Yahoo documentation and yahoo_fantasy_api library.

## Authentication

- Uses **OAuth 2.0** (library handles OAuth 1.0 internally)
- Register app at https://developer.yahoo.com/apps/
- Select "Installed Application" with Fantasy Sports permissions
- Redirect URI: `oob` (out of band)

## Base URL

```
https://fantasysports.yahooapis.com/fantasy/v2/
```

## Key Formats

| Resource | Format | Example |
|----------|--------|---------|
| Game Key | `{game_code}` or `{game_id}` | `mlb` or `422` |
| League Key | `{game_key}.l.{league_id}` | `422.l.12345` |
| Team Key | `{game_key}.l.{league_id}.t.{team_id}` | `422.l.12345.t.3` |
| Player Key | `{game_key}.p.{player_id}` | `422.p.10660` |

---

## Game Class

**Constructor:** `Game(sc, code)`
- `sc`: OAuth2 session context
- `code`: Sport code (`mlb`, `nfl`, `nba`, `nhl`)

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `game_id()` | str | Yahoo Game ID |
| `league_ids(year=None)` | list | League IDs for current user |
| `to_league(league_id)` | League | Construct League object |

---

## League Class

**Constructor:** `League(sc, league_id)`

### Roster & Teams

| Method | Returns | Description |
|--------|---------|-------------|
| `positions()` | dict | Positions used in league with counts |
| `standings()` | list | Ordered standings (1st place first) |
| `teams()` | dict | All teams, keyed by team_key |
| `to_team(team_key)` | Team | Construct Team object |
| `team_key()` | str | Logged-in user's team key |
| `settings()` | dict | Full league configuration |

### Schedule & Timing

| Method | Returns | Description |
|--------|---------|-------------|
| `current_week()` | int | Current week number |
| `end_week()` | int | Final week of season |
| `edit_date()` | date | Next editable lineup date |
| `week_date_range(week)` | tuple | (start_date, end_date) for week |
| `matchups(week=None)` | dict | Matchup data for week |

### Players & Stats

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `player_details(player)` | str/int/list | list(dict) | Search by name, ID, or list of IDs |
| `player_stats(player_ids, req_type, ...)` | IDs, type, optional date/week | list(dict) | Stats for players |
| `stat_categories()` | - | list(dict) | League scoring categories |

**`player_stats` req_type options:**
- `'season'` - Full season stats
- `'average_season'` - Season averages
- `'lastweek'` - Previous week
- `'lastmonth'` - Previous month
- `'date'` - Specific date (pass `date=datetime.date`)
- `'week'` - Specific week (pass `week=int`)

### Free Agents & Waivers

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `free_agents(position)` | position code | list(dict) | Available players by position |
| `waivers()` | - | list(dict) | Players currently on waivers |
| `ownership(player_ids)` | list(int) | dict | Ownership info |
| `percent_owned(player_ids)` | list(int) | list(dict) | Ownership percentages |
| `taken_players()` | - | list(dict) | All rostered players |

**Position codes:** `'C'`, `'1B'`, `'2B'`, `'3B'`, `'SS'`, `'LF'`, `'CF'`, `'RF'`, `'OF'`, `'Util'`, `'SP'`, `'RP'`, `'P'`, `'BN'`, `'IL'`, `'IL+'`, `'NA'`

### Transactions & Draft

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `draft_results()` | - | list | Draft picks with pick, round, cost, team_key, player_id |
| `transactions(tran_types, count)` | types str, count int | list | Transaction history |

**Transaction types:** `'add'`, `'drop'`, `'trade'`, `'commish'`

---

## Team Class

**Constructor:** `Team(sc, team_key)`

### Roster Management

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `roster(week=None, day=None)` | optional week/day | list | Players with positions and status |
| `details()` | - | dict | Team info (name, managers, etc.) |
| `matchup(week)` | int | str | Opponent team_key for week |

**Roster response includes per player:**
- `player_id` - Unique ID
- `name` - Player name
- `position_type` - `'B'` (batter) or `'P'` (pitcher)
- `eligible_positions` - List of valid positions
- `selected_position` - Current assigned position
- `status` - `'IL'`, `'IL+'`, `'DTD'`, `'NA'`, or empty

### Lineup Changes

```python
team.change_positions(time_frame, modified_lineup)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `time_frame` | date or int | Specific date or week number |
| `modified_lineup` | list(dict) | `[{'player_id': 12345, 'selected_position': 'LF'}, ...]` |

Raises `RuntimeError` on Yahoo communication errors.

### Add/Drop Players

| Method | Parameters | Description |
|--------|------------|-------------|
| `add_player(player_id)` | int | Add free agent |
| `drop_player(player_id)` | int | Drop player |
| `add_and_drop_players(add_id, drop_id)` | int, int | Single transaction add+drop |

### Waiver Claims

| Method | Parameters | Description |
|--------|------------|-------------|
| `claim_player(player_id, faab=None)` | int, optional int | Claim player (with FAAB bid) |
| `claim_and_drop_players(add_id, drop_id, faab=None)` | int, int, optional int | Claim + drop |

### Trades

| Method | Parameters | Description |
|--------|------------|-------------|
| `propose_trade(tradee_team_key, players, note='')` | str, list(dict), str | Propose trade |
| `proposed_trades()` | - | Get pending trade proposals |
| `accept_trade(transaction_key, note='')` | str, str | Accept trade |
| `reject_trade(transaction_key, note='')` | str, str | Reject trade |

**Trade players format:**
```python
players = [
    {'player_key': '422.p.12345', 'source_team_key': 'my_key', 'destination_team_key': 'their_key'},
    {'player_key': '422.p.67890', 'source_team_key': 'their_key', 'destination_team_key': 'my_key'}
]
```

---

## Common Patterns

### Get My Roster

```python
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

sc = OAuth2(None, None, from_file='oauth2.json')
gm = yfa.Game(sc, 'mlb')
lg = gm.to_league(gm.league_ids(year=2025)[0])
tm = lg.to_team(lg.team_key())
roster = tm.roster()
```

### Find IL-Eligible Players Not on IL

```python
roster = tm.roster()
il_candidates = [p for p in roster
                 if p['status'] in ['IL', 'IL+']
                 and p['selected_position'] != 'IL'
                 and p['selected_position'] != 'IL+']
```

### Stream a Pitcher

```python
# Get free agent pitchers
fa_pitchers = lg.free_agents('SP')

# Add best option, drop worst roster player
tm.add_and_drop_players(
    add_player_id=fa_pitchers[0]['player_id'],
    drop_player_id=drop_candidate_id
)
```

### Change Lineup

```python
import datetime

# Move player to different position for tomorrow
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
tm.change_positions(tomorrow, [
    {'player_id': 12345, 'selected_position': 'Util'},
    {'player_id': 67890, 'selected_position': 'BN'}
])
```

---

## Rate Limits

- Unofficial limit: ~900-1000 requests/hour
- Add 100ms delay between rapid sequential calls
- Use batch endpoints where possible

## Error Handling

- Token expiration: Library auto-refreshes
- Rate limiting: Exponential backoff recommended
- Invalid operations: Raises `RuntimeError` with Yahoo error message
