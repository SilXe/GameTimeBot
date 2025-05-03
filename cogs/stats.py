# cogs/stats.py

import discord
from discord.ext import commands
from db.database import users
import matplotlib.pyplot as plt
import io

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats")
    async def stats(self, ctx):
        print(f"[DEBUG] !stats triggered by {ctx.author}")
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        doc = await users.find_one({"user_id": user_id, "guild_id": guild_id})
        if not doc or "game_time" not in doc:
            await ctx.send("No game data found for you yet!")
            return

        game_times = doc["game_time"]

        # Convert seconds to hours/minutes for readability
        labels = []
        values = []
        for game, seconds in game_times.items():
            mins = seconds // 60
            labels.append(game)
            values.append(mins)

        # Plot bar chart
        plt.figure(figsize=(8, 4))
        bars = plt.bar(labels, values)
        plt.xlabel("Game")
        plt.ylabel("Time (minutes)")
        plt.title(f"Game Time for {ctx.author.display_name}")
        plt.tight_layout()

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        # Send as image
        file = discord.File(buf, filename="stats.png")
        await ctx.send(file=file)

async def setup(bot):
    await bot.add_cog(Stats(bot))
