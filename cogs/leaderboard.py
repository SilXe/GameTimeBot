import discord
from discord.ext import commands
from db.database import users
from utils.game_aliases import GAME_ALIASES

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx, *, game: str = None):
        guild_id = str(ctx.guild.id)
        top_n = 5

        if game:
            game = game.lower()
            game = GAME_ALIASES.get(game, game.title())

            query = {
                "guild_id": guild_id,
                f"game_time.{game}": {"$exists": True}
            }
            cursor = users.find(query).sort([(f"game_time.{game}", -1)]).limit(top_n)
            title = f"Top {top_n} Players in {game}"
        else:
            query = { "guild_id": guild_id }
            cursor = users.find(query).sort([("total_time", -1)]).limit(top_n)
            title = f"Top {top_n} Players (All Games Combined)"

        leaderboard_data = await cursor.to_list(length=top_n)

        if not leaderboard_data:
            await ctx.send("❌ No data found for leaderboard.")
            return

        embed = discord.Embed(title=title, color=discord.Color.blurple())

        medals = ["🥇", "🥈", "🥉", "🎖", "🎖"]
        for idx, user in enumerate(leaderboard_data):
            name = user.get("username", "Unknown")
            time_played = (
                user.get("game_time", {}).get(game, 0) if game
                else user.get("total_time", 0)
            )
            duration = format_duration(time_played)
            embed.add_field(
                name=f"{medals[idx]} {idx+1}. {name}",
                value=f"**{duration}**",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
