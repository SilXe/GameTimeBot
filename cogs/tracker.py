# cogs/tracker.py

import discord
from discord.ext import commands
import datetime
from db.database import users

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
                start_time = session["start_time"]
                game = session["game"]
                duration = int((datetime.datetime.utcnow() - start_time).total_seconds())
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60

                # Format log message
                time_parts = []
                if hours:
                    time_parts.append(f"{hours} hr{'s' if hours != 1 else ''}")
                if minutes:
                    time_parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
                if seconds or not time_parts:
                    time_parts.append(f"{seconds} sec{'s' if seconds != 1 else ''}")
                duration_str = ' '.join(time_parts)

                msg = f"🎮 **{member.display_name}** played **{game}** in voice for **{duration_str}**"

                # ✅ Store/update in MongoDB
                await users.update_one(
                    {"user_id": str(member.id), "guild_id": str(member.guild.id)},
                    {
                        "$inc": {
                            f"game_time.{game}": duration,
                            "total_time": duration
                        },
                        "$set": {
                            "username": str(member.display_name)
                        }
                    },
                    upsert=True
                )

                # Log to terminal and Discord
                try:
                    print(f"[-] {msg}")
                except Exception as e:
                    print(f"[-] Session finished but could not print: {e}")

                guild = self.bot.get_guild(session["guild_id"])
                log_channel = await self.get_log_channel(guild)
                if log_channel:
                    await log_channel.send(msg)

                del active_sessions[user_id]
    
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        print(f"🔍 PRESENCE UPDATE: {after.display_name}")

        user_id = after.id

        # 🔍 Log raw activities
        if not after.activities or all(not act.name for act in after.activities):
            print("   🔸 No activities found.")

            # Stop current game if being tracked
            if user_id in active_sessions and active_sessions[user_id]["game"]:
                session = active_sessions[user_id]
                start_time = session["start_time"]
                old_game = session["game"]
                duration = int((datetime.datetime.utcnow() - start_time).total_seconds())

                # Format log message
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

                msg = f"🛑 **{after.display_name}** stopped playing **{old_game}** (Duration: {duration_str})"

                # Log to Discord
                log_channel = await self.get_log_channel(after.guild)
                if log_channel:
                    await log_channel.send(msg)
                print(msg)

                # Store to DB
                await users.update_one(
                    {"user_id": str(after.id), "guild_id": str(after.guild.id)},
                    {
                        "$inc": {
                            f"game_time.{old_game}": duration,
                            "total_time": duration
                        },
                        "$set": {
                            "username": str(after.display_name)
                        }
                    },
                    upsert=True
                )

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

        # If no game active, treat as stopping
        if not game:
            if user_id in active_sessions and active_sessions[user_id]["game"]:
                session = active_sessions[user_id]
                start_time = session["start_time"]
                old_game = session["game"]
                duration = int((datetime.datetime.utcnow() - start_time).total_seconds())

                # Format log message
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

                msg = f"🛑 **{after.display_name}** stopped playing **{old_game}** (Duration: {duration_str})"

                # Log
                log_channel = await self.get_log_channel(after.guild)
                if log_channel:
                    await log_channel.send(msg)
                print(msg)

                # DB store
                await users.update_one(
                    {"user_id": str(after.id), "guild_id": str(after.guild.id)},
                    {
                        "$inc": {
                            f"game_time.{old_game}": duration,
                            "total_time": duration
                        },
                        "$set": {
                            "username": str(after.display_name)
                        }
                    },
                    upsert=True
                )

                del active_sessions[user_id]
            return

        # Compare with previous session game
        if user_id in active_sessions and active_sessions[user_id]["game"] == game:
            return  # same game, no change

        # Stop old session if any
        if user_id in active_sessions and active_sessions[user_id]["game"]:
            old_session = active_sessions[user_id]
            old_game = old_session["game"]
            start_time = old_session["start_time"]
            duration = int((datetime.datetime.utcnow() - start_time).total_seconds())

            # Format message
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

            stop_msg = f"🛑 **{after.display_name}** stopped playing **{old_game}** (Duration: {duration_str})"
            log_channel = await self.get_log_channel(after.guild)
            if log_channel:
                await log_channel.send(stop_msg)
            print(stop_msg)

            await users.update_one(
                {"user_id": str(after.id), "guild_id": str(after.guild.id)},
                {
                    "$inc": {
                        f"game_time.{old_game}": duration,
                        "total_time": duration
                    },
                    "$set": {
                        "username": str(after.display_name)
                    }
                },
                upsert=True
            )

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



async def setup(bot):
    await bot.add_cog(Tracker(bot))
