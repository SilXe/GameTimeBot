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

async def setup(bot):
    await bot.add_cog(Tracker(bot))
