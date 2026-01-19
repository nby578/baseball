# Fantasy Baseball Bot

AI-powered automation for Yahoo Fantasy Baseball.

## Features (Planned)
- [ ] Never miss IL/NA activations
- [ ] Auto-optimize daily lineups
- [ ] Smart pitcher streaming recommendations
- [ ] Waiver wire monitoring
- [ ] Discord notifications for important moves

## Setup

### 1. Create Yahoo Developer App

1. Go to https://developer.yahoo.com/apps/
2. Click "Create an App"
3. Fill in:
   - **Application Name**: Fantasy Baseball Bot (or whatever)
   - **Application Type**: Installed Application
   - **Description**: Personal fantasy baseball automation
   - **Home Page URL**: (leave blank or use github)
   - **Redirect URI(s)**: `oob` (out of band)
   - **API Permissions**: Check "Fantasy Sports"
4. Click "Create App"
5. Copy your **Client ID** and **Client Secret**

### 2. Configure Environment

```bash
cd fantasy-bot
cp .env.example .env
# Edit .env with your credentials
```

### 3. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 4. First Run (Authorization)

```bash
python auth.py
```

This will:
1. Open a browser window to Yahoo
2. Ask you to authorize the app
3. Give you a verification code
4. Paste the code back in the terminal
5. Save tokens for future use (auto-refresh)

## Usage

```bash
# Test connection
python auth.py

# Run the bot (coming soon)
python bot.py
```

## Project Structure

```
fantasy-bot/
├── auth.py           # Yahoo OAuth authentication
├── config.py         # Configuration settings
├── bot.py            # Main bot logic (coming soon)
├── roster.py         # Roster management (coming soon)
├── streaming.py      # Pitcher streaming logic (coming soon)
├── notifications.py  # Discord/alerts (coming soon)
├── requirements.txt  # Python dependencies
├── .env              # Your credentials (not in git)
└── oauth2.json       # OAuth tokens (not in git)
```
