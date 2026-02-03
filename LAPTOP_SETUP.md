# Baseball Automation Laptop Setup

This machine's job: run OpenClaw + Chrome to fully automate Yahoo Fantasy Baseball — monitoring, decisions, and roster moves.

## What This Machine Does

```
This Laptop (always on)
├── OpenClaw (Telegram bot <-> Claude Code API)
│   └── Drives Chrome for Yahoo roster moves
├── Chrome (logged into Yahoo Fantasy)
├── Baseball bot scripts (monitoring + analysis)
├── Windows Task Scheduler (triggers checks on schedule)
└── Telegram notifications to Noah's phone
```

## Why This Exists

Yahoo removed Write API access for new apps (Oct 2025). Reading roster data works via API, but actual roster moves (add/drop, lineup changes, waiver claims) require browser automation. This machine provides always-on Chrome + AI to handle that automatically.

---

## Step 1: Software to Install

| Software | Purpose | Install |
|----------|---------|---------|
| Python 3.12+ | Run baseball scripts | python.org or Windows Store |
| Node.js 22+ | Run OpenClaw | nodejs.org |
| Chrome | Browser automation target | google.com/chrome |
| Git | Clone repos | git-scm.com |
| OpenClaw | AI assistant + Telegram bridge | `npm install -g openclaw@latest` |

## Step 2: Clone the Baseball Repo

```bash
git clone https://github.com/NoahYaffe/baseball.git
cd baseball
```

Copy these files from Noah's main machine (not in git):
- `.env` — Yahoo API credentials + league ID
- `oauth2.json` — Yahoo OAuth tokens (auto-refresh)

### .env contents needed:
```
YAHOO_CLIENT_ID=dj0yJmk9NXl6djlIQWFrTHFmJmQ9WVdrOU5ubEdNMkV3VEhrbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTll
YAHOO_CLIENT_SECRET=c660585f3ed780781b8881d848360465cb2a525b
YAHOO_LEAGUE_ID=89318
DISCORD_WEBHOOK_URL=
```

League ID 89318 = Big League Jew X (2025). Update to 2026 league ID once created (game key 469).

### Python dependencies:
```bash
pip install yahoo_fantasy_api yahoo_oauth requests python-dotenv numpy scipy scikit-learn pandas pybaseball
```

## Step 3: Log Chrome into Yahoo

1. Open Chrome manually
2. Go to https://baseball.fantasysports.yahoo.com/
3. Sign in as Noah
4. Leave the session active (stay logged in)

This is needed for browser automation to work — OpenClaw/Claude will drive this Chrome instance.

## Step 4: Set Up OpenClaw

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

During onboard:
- Auth: Anthropic OAuth token (Noah has Max x5 subscription)
- Telegram: Connect to a bot (or create a new one via @BotFather for baseball-specific alerts)
- Workspace: Point to the baseball repo directory

### OpenClaw Key Concepts

- **Gateway**: WebSocket server (default port 18789) that coordinates messaging + agent runtime
- **Heartbeat**: Periodic check-in (set to 5 min during baseball season for timely cron jobs)
- **Cron jobs**: Built-in scheduler in `/path/to/.openclaw/cron/jobs.json` — can be created by telling the bot in Telegram
- **Skills**: Extensible plugins in `/path/to/.openclaw/skills/` described by SKILL.md files
- **Sessions**: Each conversation is a session; "main" is the DM session

### Important Config Settings

In `openclaw.json`, ensure:
```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "5m",
        "activeHours": {
          "start": "06:00",
          "end": "02:00",
          "timezone": "America/New_York"
        }
      }
    }
  }
}
```

---

## Step 5: Create a Baseball Skill

Create a skill directory and SKILL.md so OpenClaw knows about baseball capabilities. The skill should be able to:
- Run `daily_check.py` for roster/injury monitoring
- Run `live/streaming_planner.py` for pitcher recommendations
- Drive Chrome to Yahoo Fantasy to make roster moves
- Send results via Telegram

---

## VPS Access (Existing Infrastructure)

Noah has a Hetzner VPS running related services.

```bash
ssh root@5.78.89.136
```

Key-only auth (no passwords). SSH key must be added via Hetzner console.

### Services on VPS

| Service | Port | What It Does |
|---------|------|-------------|
| Snowflake Proxy | 8000 | Read-only Snowflake queries via `sf.noahyaffe.com` |
| NoashyBot (OpenClaw) | 18789 | General AI assistant on Telegram (@NoashyBot) |
| FlakeBot (OpenClaw) | 18790 | Snowflake data analyst on Telegram (@SnowyflakeyBot) |
| nginx | 80/443 | Reverse proxy for all services |

### VPS OpenClaw Config Paths

| What | Path |
|------|------|
| NoashyBot config | `/root/.openclaw/openclaw.json` |
| NoashyBot skills | `/root/.openclaw/skills/` |
| FlakeBot config | `/root/.openclaw-flakebot/openclaw.json` |
| FlakeBot skills | `/root/.openclaw-flakebot/skills/` |
| Cron jobs | `/root/.openclaw/cron/jobs.json` |

### VPS Service Commands

```bash
# Status check
systemctl --user is-active openclaw-gateway    # NoashyBot
systemctl --user is-active openclaw-flakebot   # FlakeBot
systemctl is-active snowflake-proxy

# Restart
systemctl --user restart openclaw-gateway
systemctl --user restart openclaw-flakebot

# Logs
journalctl --user -u openclaw-gateway -f
journalctl --user -u openclaw-flakebot -f
```

### Snowflake Proxy (for data queries without IP whitelisting)

```bash
curl -s -X POST https://sf.noahyaffe.com/query \
  -H "Authorization: Bearer 3S4lnmoPnoXF03fRtJxtouceVCo-ZM_fftKEQeKfplsx5se2dNJ1p9raRf_NUAcv" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT CURRENT_DATE()"}'
```

---

## Yahoo Fantasy API (Already Working)

The API is read-only but functional. Tokens auto-refresh.

### Test Connection
```bash
cd baseball
python auth.py
```

### Key API Capabilities (Read-Only)
- Roster status (IL, DTD, NA detection)
- Free agent search by position
- League standings and matchups
- Player stats (season and weekly)

### Key URLs for Chrome Automation
```
# League home (2025 — update for 2026)
https://baseball.fantasysports.yahoo.com/2025/b1/89318

# My team roster
https://baseball.fantasysports.yahoo.com/2025/b1/89318/7

# Free agents
https://baseball.fantasysports.yahoo.com/2025/b1/89318/players
```

### Roster Positions (Big League Jew)
- Batters: C, 1B, 2B, 3B, SS, OF, OF, OF, Util, Util, Util
- Pitchers: SP, SP, RP, RP, RP, P, P, P
- Bench: ~6 BN slots
- IL: 2 slots

---

## Automation Schedule (Target)

| Time (ET) | Action | Method |
|-----------|--------|--------|
| 7:00 AM | Check lineup, IL returns, injuries | API + Telegram alert |
| 11:00 AM | Streaming pitcher recommendations | API + analysis scripts |
| 2:00 PM | Pre-game roster verification | API + Chrome if moves needed |
| 6:00 PM | Final lineup check before games | API + Chrome |
| 11:55 PM | Queue waiver claims | Chrome automation |
| Every 4 hrs | Injury scan | API + Telegram alert |

---

## Security Notes

- This machine should use a **dedicated Windows user account** with only baseball-related files
- OpenClaw has full filesystem + shell access as the running user — treat this like giving an AI root on this account
- Don't store sensitive non-baseball credentials on this machine
- Yahoo OAuth tokens and Claude API key are the most sensitive items
- The VPS has hardened security (key-only SSH, loopback-only gateways, rate limiting)

---

## Noah's Telegram Chat ID

`8500251154` — use for direct Telegram Bot API notifications if needed.

NoashyBot token: see VPS config at `/root/.openclaw/openclaw.json`

---

## Key Project Files (Baseball Repo)

```
baseball/
├── auth.py                  # Yahoo OAuth2 authentication
├── config.py                # Configuration variables
├── daily_check.py           # Daily roster check runner
├── mlb_api.py               # MLB Stats API (free, no auth)
├── streaming.py             # Basic streaming ranker
├── points_projector.py      # Points projection engine
├── weekly_optimizer.py      # Weekly roster optimization
├── roster_manager.py        # Roster management logic
├── transaction_manager.py   # Add/drop transaction logic
├── advanced_stats.py        # Advanced statistics
├── hidden_edges.py          # Scoring system exploits
├── fantasy_bot.py           # Main bot orchestrator
├── notifications.py         # Discord/notification webhooks
├── live/
│   ├── streaming_planner.py # Weekly streaming recommendations
│   └── streaming_bot.py     # Streaming orchestrator
├── backtesting/
│   ├── backtester.py        # Historical validation
│   └── mlb_fetcher.py       # pybaseball data fetcher
└── docs/
    ├── Draft.md             # Draft strategy guide
    └── Hidden Edges in Points League Fantasy Baseball.md
```
