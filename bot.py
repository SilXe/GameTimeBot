# venv\Scripts\activate to start venv
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.voice_states = True
intents.guilds = True  # Required to access guild and channels
intents.message_content = True # For command inputs in chat


bot = commands.Bot(command_prefix="!", intents=intents)

async def ensure_bot_log_channel(guild: discord.Guild):
    log_channel = discord.utils.get(guild.text_channels, name="bot-log")

    if not log_channel:
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True)
            }
            log_channel = await guild.create_text_channel("bot-log", overwrites=overwrites)
            print(f"Created 'bot-log' in {guild.name}")
        except discord.Forbidden:
            print(f"❌ Missing permissions to create 'bot-log' in {guild.name}")
        except Exception as e:
            print(f"⚠️ Error creating 'bot-log' in {guild.name}: {e}")
    return log_channel

@bot.event
async def on_ready():
    print(f"{bot.user} is now online!")

    for guild in bot.guilds:
        log_channel = await ensure_bot_log_channel(guild)
        if log_channel:
            await log_channel.send(f"✅ **{bot.user.name} is now online and tracking game sessions!**")

# Load extensions
async def load_extensions():
    try:
        await bot.load_extension("cogs.tracker")
        print("[+] Loaded: tracker")
    except Exception as e:
        print(f"[!] Failed to load tracker: {e}")

    try:
        await bot.load_extension("cogs.stats")
        print("[+] Loaded: stats")
    except Exception as e:
        print(f"[!] Failed to load stats: {e}")
    
    try:
        await bot.load_extension("cogs.profile")
        print("[+] Loaded: profile")
    except Exception as e:
        print(f"[!] Failed to load profile: {e}")

    try:
        await bot.load_extension("cogs.leaderboard")
        print("[+] Loaded: leaderboard")
    except Exception as e:
        print(f"[!] Failed to load leaderboard: {e}")


# Start bot
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())
