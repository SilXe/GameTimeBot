# cogs/tracker.py

import discord
from discord.ext import commands
import datetime
from db.database import users, sessions
from utils.level import LEVEL_THRESHOLDS, calculate_level

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild):
        return discord.utils.get(guild.text_channels, name="bot-log")

    async def start_session(self, member: discord.Member, game: str):
        print(f"[DEBUG] Calling start_session for {member.display_name} | Game: {game}")
        try:
            await sessions.update_one(
                {"user_id": str(member.id), "guild_id": str(member.guild.id)},
                {
                    "$set": {
                        "user_id": str(member.id),
                        "guild_id": str(member.guild.id),
                        "game": game,
                        "start_time": datetime.datetime.utcnow(),
                        "channel": member.voice.channel.name if member.voice else "unknown"
                    }
                },
                upsert=True
            )
            print(f"[+] Session started for {member.display_name} in {game}")
        except Exception as e:
            print(f"[ERROR] stop_session failed: {e}")
        

    async def end_session(self, member: discord.Member, reason: str):
        print(f"[DEBUG] Calling end_session for {member.display_name}")
        doc = await sessions.find_one({
            "user_id": str(member.id),
            "guild_id": str(member.guild.id)
        })
        if not doc:
            print(f"[WARN] No session found for {member.display_name}")
            return

        duration = int((datetime.datetime.utcnow() - doc["start_time"]).total_seconds())
        await self.stop_session(member, duration, doc["game"], reason)
        await sessions.delete_one({"_id": doc["_id"]})

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        print(f"🎤 VOICE STATE UPDATE: {member.display_name}")
        game = member.activity.name if member.activity else None
        print(f"[DEBUG] member.activity: {member.activity}")

        if after.channel and game:
            await self.start_session(member, game)
        elif before.channel and not after.channel:
            await self.end_session(member, "🔕 Left voice channel")

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        print(f"🔍 PRESENCE UPDATE: {after.display_name}")

        if not after.activities or all(not act.name for act in after.activities):
            print("   🔸 No activities found.")
            await self.end_session(after, "🚩 No activity")
            return

        game = None
        for act in after.activities:
            if isinstance(act, discord.Game):
                game = act.name
                break
        if not game:
            game = after.activity.name if after.activity else None

        voice_channel = next((vc for vc in after.guild.voice_channels if after in vc.members), None)
        if not voice_channel:
            print("   ⏭️ User not in a voice channel. Ignoring.")
            return

        existing = await sessions.find_one({"user_id": str(after.id), "guild_id": str(after.guild.id)})
        if existing and existing.get("game") == game:
            return

        if existing:
            await self.end_session(after, "🔁 Switched game")

        if game:
            await self.start_session(after, game)
            msg = f"▶️ **{after.display_name}** started playing **{game}**"
            log_channel = await self.get_log_channel(after.guild)
            if log_channel:
                await log_channel.send(msg)
            print(msg)

    async def stop_session(self, member: discord.Member, duration: int, game: str, reason: str):
        try:
            user_id = str(member.id)
            guild_id = str(member.guild.id)

            user_doc = await users.find_one({"user_id": user_id, "guild_id": guild_id}) or {}
            prev_total = user_doc.get("total_time", 0)
            prev_game = user_doc.get("game_time", {}).get(game, 0)
            prev_level = calculate_level(prev_total)

            new_total = prev_total + duration
            new_game = prev_game + duration
            new_level = calculate_level(new_total)

            if new_level > prev_level:
                msg = f"🎉 **{member.display_name}** leveled up to **Level {new_level}**!"
                log_channel = await self.get_log_channel(member.guild)
                if log_channel:
                    await log_channel.send(msg)
                print(msg)

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
        except Exception as e:
            print(f"[ERROR] stop_session failed: {e}")

async def setup(bot):
    await bot.add_cog(Tracker(bot))
