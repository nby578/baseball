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

## Security: Hyper-V VM Setup (Recommended)

OpenClaw has full filesystem + shell access as the running user. To isolate it, run everything inside a Hyper-V VM. Noah already has this working on his main machine for Snowflake — same process here.

### Prerequisites
- Windows 10/11 Pro (Home doesn't have Hyper-V)
- Enable Hyper-V if not already on:
  ```powershell
  # Run as Administrator
  Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All
  # Reboot when prompted
  ```

### Create the VM (Hyper-V Manager)

1. Open **Hyper-V Manager** (type it in Start menu)
2. **New** → **Virtual Machine**
3. Settings:
   - **Name**: `Baseball-Bot`
   - **Generation**: 2
   - **Memory**: 6144–8192 MB (dynamic memory ON)
   - **Network**: Default Switch
   - **Virtual Hard Disk**: 50–127 GB (grows as needed)
   - **Installation**: ISO file → browse to `ubuntu-24.04.x-desktop-amd64.iso`
     - Download from: https://ubuntu.com/download/desktop
4. Before first boot, go to **Settings**:
   - **Security** → **Uncheck "Enable Secure Boot"** (critical — Ubuntu won't boot without this)
   - **Firmware** → Make sure **DVD Drive is #1** in boot order
5. **Start** the VM → Install Ubuntu:
   - Choose **Install Ubuntu** (NOT "Try")
   - Erase disk and install (only erases the virtual disk)
   - Set username/password
   - Wait for install → click **Restart Now**
6. After reboot, **immediately**:
   - Settings → **DVD Drive** → Eject the ISO (set to None)
   - Settings → **Firmware** → Move **Hard Drive to #1** in boot order
7. Boot the VM → black screen with X cursor → press Enter → type password → desktop appears

### Known Issues (from Noah's experience)
- **PXE boot loop**: Hard Drive must be #1 in Firmware boot order, DVD ejected
- **Enhanced Session grayed out**: Don't bother — it never worked with Ubuntu 24.04. Use xrandr instead for resolution
- **Resolution fix** (run inside VM after login):
  ```bash
  xrandr --output Virtual-1 --mode 1920x1080 --rate 60
  ```
  Make permanent:
  ```bash
  crontab -e
  # Add this line at bottom:
  @reboot sleep 10 && xrandr --output Virtual-1 --mode "1920x1080_60.00"
  ```
- **Integration Services**: In VM Settings → Integration Services → check all boxes (enables clipboard between host and VM)

### Install Software Inside the VM

```bash
# Update
sudo apt update && sudo apt upgrade -y

# Install basics
sudo apt install -y git curl wget build-essential

# Install Chrome (needed for Yahoo roster moves)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y

# Install Node.js 22+ (for OpenClaw)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.12+ (should already be there on Ubuntu 24.04)
python3 --version
sudo apt install -y python3-pip python3-venv

# Install OpenClaw
sudo npm install -g openclaw@latest

# Clone baseball repo
git clone https://github.com/nby578/baseball.git
cd baseball

# Install Python dependencies
pip3 install yahoo_fantasy_api yahoo_oauth requests python-dotenv numpy scipy scikit-learn pandas pybaseball
```

### Copy Credentials Into the VM

These files need to be manually created inside the VM (they're not in git):

**`.env`** in the baseball repo directory:
```
YAHOO_CLIENT_ID=dj0yJmk9NXl6djlIQWFrTHFmJmQ9WVdrOU5ubEdNMkV3VEhrbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTll
YAHOO_CLIENT_SECRET=c660585f3ed780781b8881d848360465cb2a525b
YAHOO_LEAGUE_ID=89318
DISCORD_WEBHOOK_URL=
```

**`oauth2.json`** — copy the full contents from Noah's main machine. Tokens auto-refresh so this only needs to be done once.

### Set Up OpenClaw Inside the VM

```bash
openclaw onboard --install-daemon
```

During onboard:
- Auth: Anthropic OAuth token (Max x5 subscription)
- Telegram: Connect to @NoashyBot or create a new baseball-specific bot
- Workspace: `/home/<user>/baseball`

### Log Chrome Into Yahoo

1. Open Chrome inside the VM
2. Go to https://baseball.fantasysports.yahoo.com/
3. Sign in as Noah
4. Stay logged in

### Security Benefit of the VM

| Threat | Protection |
|--------|-----------|
| OpenClaw reads personal files | VM has no access to Windows host filesystem |
| OpenClaw modifies system files | Only the VM is affected — nuke and rebuild from checkpoint |
| Credential theft | Only Yahoo OAuth + Claude API key in the VM, nothing else |
| VM escape | Hyper-V hypervisor enforced — guest cannot modify VM settings even with root |
| Social engineering | Human reviews Telegram alerts before approving destructive actions |

**Take a checkpoint** after setup is complete: Hyper-V Manager → right-click VM → Checkpoint → name it "Baseball Bot - Clean". Roll back to this any time.

### Alternative: No VM (Dedicated User Account)

If the laptop is truly dedicated to baseball only and has nothing sensitive:
- Create a `baseball` Windows user account
- Install everything directly (no VM overhead)
- Simpler but weaker isolation — acceptable if machine has no other purpose

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
