# GameTimeBot
GameTimeBot is a Discord bot that tracks how long users play specific games while in voice channels.  
It awards XP, levels, and custom titles based on playtime. Fully integrated with MongoDB and designed with a gamified, social experience in mind.

### Features
- Tracks time spent playing games in voice channels

- Detects when users switch games without leaving voice

- Logs session durations (e.g. “1 hr 4 mins 33 secs”)

- Stores all data in MongoDB (per-user, per-game, total)

- !stats command shows game time history as a bar chart

- !profile displays:

  - User level and total playtime

  - Top 5 games

  - Titles earned (e.g., League Master, Professional Gamer)

  - XP progress bar to next level

- !leaderboard for top players (global and per-game)

- XP and Leveling system (Level 1 = 5 min → Level 10 = 100 hrs)

- Auto-assigns role titles (e.g., VALORANT Master) at 100 hours

- Game alias support (lol, r6, mc, etc.)

### Tech Stack
- Python 3

- discord.py (Bot framework)

- Motor (MongoDB async driver)

- matplotlib (for charts and profile cards)

- MongoDB Atlas (for cloud database)

### Getting Started

#### 1. Clone the repo
      git clone https://github.com/yourusername/GameTimeBot.git  
      cd GameTimeBot

#### 2. Install dependencies
Make sure you have Python 3.9+ and venv  
<pre>python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt </pre>

#### 3. Configure environment
Create a .env file based on .env.template
<pre>DISCORD_TOKEN=your_bot_token_here
MONGO_URI=your_mongodb_connection_uri</pre>

#### 4. Run the bot locally
<pre> python bot.py #OR py bot.py
</pre>

### Bot Commands
<pre>
| Command               | Description                          |
|-----------------------|--------------------------------------|
| `!profile`            | View your own profile card           |
| `!profile @user`      | View someone else's profile          |
| `!stats`              | View your playtime history as a chart|
| `!leaderboard`        | Top 5 players by total time          |
| `!leaderboard <game>`       | Top 5 players for that game          |
</pre>

#### Contributions
Pull requests are welcome. If you’d like to add game icon support, fuzzy matching, or a web dashboard, feel free to fork and open an issue!
