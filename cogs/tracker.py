# cogs/tracker.py

import discord
from discord.ext import commands
import datetime
from db.database import users
from utils.level import LEVEL_THRESHOLDS, calculate_level

active_sessions = {}

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild):
        return discord.utils.get(guild.text_channels, name="bot-log")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        print(f"🎤 VOICE STATE UPDATE: {member.display_name}")

        user_id = member.id
        game = member.activity.name if member.activity else None

        # User joined voice and is playing a game
        if after.channel and game:
            active_sessions[user_id] = {
                "start_time": datetime.datetime.utcnow(),
                "game": game,
                "channel": after.channel.name,
                "guild_id": member.guild.id
            }
            print(f"[+] Tracking started for {member.name} in {game}")

        # User left voice channel
        elif before.channel and not after.channel:
            if user_id in active_sessions:
                session = active_sessions[user_id]
                duration = int((datetime.datetime.utcnow() - session["start_time"]).total_seconds())
                await self.stop_session(member, duration, session["game"], "🔕 Left voice channel")
                del active_sessions[user_id]
            elif user_id not in active_sessions:
                print(f"[WARN] {member.name} left voice but had no active session")
    
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        print(f"🔍 PRESENCE UPDATE: {after.display_name}")

        user_id = after.id

        if not after.activities or all(not act.name for act in after.activities):
            print("   🔸 No activities found.")

            if user_id in active_sessions and active_sessions[user_id]["game"]:
                session = active_sessions[user_id]
                duration = int((datetime.datetime.utcnow() - session["start_time"]).total_seconds())
                await self.stop_session(after, duration, session["game"], "🛑 No activity")
                del active_sessions[user_id]
            return

        for act in after.activities:
            print(f"   🔸 Activity: {act.name} ({type(act).__name__})")

        # Get game name if any (first Game-type or fallback to any name)
        game = None
        for act in after.activities:
            if isinstance(act, discord.Game):
                game = act.name
                break
        if not game:
            game = after.activity.name if after.activity else None

        # Not in voice? skip
        voice_channel = next((vc for vc in after.guild.voice_channels if after in vc.members), None)
        if not voice_channel:
            print("   ⏭️ User not in a voice channel. Ignoring.")
            return

        if not game:
            if user_id in active_sessions and active_sessions[user_id]["game"]:
                session = active_sessions[user_id]
                duration = int((datetime.datetime.utcnow() - session["start_time"]).total_seconds())
                await self.stop_session(after, duration, session["game"], "🛑 No game detected")
                del active_sessions[user_id]
            return

        # Compare with previous session game
        if user_id in active_sessions and active_sessions[user_id]["game"] == game:
            return  # same game, no change

        if user_id in active_sessions and active_sessions[user_id]["game"]:
            session = active_sessions[user_id]
            duration = int((datetime.datetime.utcnow() - session["start_time"]).total_seconds())
            await self.stop_session(after, duration, session["game"], "🔁 Switched game")
            del active_sessions[user_id]

        # Start tracking new game
        active_sessions[user_id] = {
            "start_time": datetime.datetime.utcnow(),
            "game": game,
            "channel": voice_channel.name,
            "guild_id": after.guild.id
        }

        new_msg = f"▶️ **{after.display_name}** started playing **{game}**"
        log_channel = await self.get_log_channel(after.guild)
        if log_channel:
            await log_channel.send(new_msg)
        print(new_msg)
    
    async def stop_session(self, member: discord.Member, duration: int, game: str, reason: str):
        user_id = str(member.id)
        guild_id = str(member.guild.id)

        # Load existing user data
        user_doc = await users.find_one({"user_id": user_id, "guild_id": guild_id}) or {}
        prev_total = user_doc.get("total_time", 0)
        prev_game = user_doc.get("game_time", {}).get(game, 0)
        prev_level = calculate_level(prev_total)

        # New totals
        new_total = prev_total + duration
        new_game = prev_game + duration
        new_level = calculate_level(new_total)

        # Announce level up
        if new_level > prev_level:
            msg = f"🎉 **{member.display_name}** leveled up to **Level {new_level}**!"
            log_channel = await self.get_log_channel(member.guild)
            if log_channel:
                await log_channel.send(msg)
            print(msg)

        # Title role logic
        titles = set(user_doc.get("titles", []))
        log_channel = await self.get_log_channel(member.guild)

        if new_total >= 360000 and "Professional Gamer" not in titles:
            titles.add("Professional Gamer")
            role = discord.utils.get(member.guild.roles, name="Professional Gamer")
            if role:
                await member.add_roles(role)
            if log_channel:
                await log_channel.send(f"🏆 **{member.display_name}** earned the title **Professional Gamer**!")

        if new_game >= 360000:
            game_title = f"{game} Master"
            if game_title not in titles:
                titles.add(game_title)
                role = discord.utils.get(member.guild.roles, name=game_title)
                if role:
                    await member.add_roles(role)
                if log_channel:
                    await log_channel.send(f"🎮 **{member.display_name}** earned the title **{game_title}**!")

        # Format session summary
        time_parts = []
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        if hours:
            time_parts.append(f"{hours} hr{'s' if hours != 1 else ''}")
        if minutes:
            time_parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
        if seconds or not time_parts:
            time_parts.append(f"{seconds} sec{'s' if seconds != 1 else ''}")
        duration_str = ' '.join(time_parts)
        msg = f"🎮 **{member.display_name}** played **{game}** in voice for **{duration_str}**"

        if log_channel:
            await log_channel.send(msg)
        print(f"{reason} → {msg}")

        # Update DB
        await users.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {
                "$inc": {
                    f"game_time.{game}": duration,
                    "total_time": duration
                },
                "$set": {
                    "username": member.display_name,
                    "level": new_level,
                    "titles": list(titles)
                }
            },
            upsert=True
        )




async def setup(bot):
    await bot.add_cog(Tracker(bot))
