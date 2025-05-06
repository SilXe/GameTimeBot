import discord
from discord.ext import commands
from db.database import users
import matplotlib.pyplot as plt
import io

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="profile")
    async def profile(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)

        # Fetch user doc
        user = await users.find_one({"user_id": user_id, "guild_id": guild_id})
        if not user:
            await ctx.send("❌ No data found for you yet.")
            return

        total_seconds = user.get("total_time", 0)
        game_time = user.get("game_time", {})
        titles = user.get("titles", [])
        level = user.get("level", 0)

        # Format time
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        total_str = f"{hours}h {minutes}m"

        # Sort top games
        top_games = sorted(game_time.items(), key=lambda x: x[1], reverse=True)[:5]

        # Create figure
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#2C2F33')
        ax.axis('off')

        y = 0.9
        ax.text(0.05, y, f"User: {member.display_name}", fontsize=14, color='white', weight='bold')
        y -= 0.1
        ax.text(0.05, y, f"Level: {level}", fontsize=12, color='white')
        y -= 0.08
        ax.text(0.05, y, f"Total Time: {total_str}", fontsize=12, color='white')
        y -= 0.12

        if top_games:
            ax.text(0.05, y, "Top Games Played:", fontsize=12, color='cyan')
            y -= 0.08
            for game, sec in top_games:
                h = sec // 3600
                m = (sec % 3600) // 60
                ax.text(0.07, y, f"- {game}: {h}h {m}m", fontsize=11, color='white')
                y -= 0.06

        y -= 0.04
        ax.text(0.05, y, "Titles Earned:", fontsize=12, color='yellow')
        y -= 0.08

        if titles:
            for title in titles:
                ax.text(0.07, y, f"- {title}", fontsize=11, color='white')
                y -= 0.05
        else:
            ax.text(0.07, y, "You have no titles earned yet.", fontsize=11, color='gray')

        # Export image to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()

        await ctx.send(file=discord.File(fp=buf, filename="profile.png"))

async def setup(bot):
    await bot.add_cog(Profile(bot))