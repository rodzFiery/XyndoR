import discord
from discord.ext import commands

class UserClasses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Multiplier data for easy reference
        self.class_info = {
            "dominant": {"bonus": 0.10, "xp_mult": 1.2, "color": discord.Color.red()},
            "submissive": {"bonus": 0.05, "xp_mult": 1.5, "color": discord.Color.blue()},
            "switch": {"bonus": 0.08, "xp_mult": 1.3, "color": discord.Color.purple()}
        }

    @commands.command(name="setclass")
    async def set_class(self, ctx, choice: str):
        """Pick a class: Dominant, Submissive, or Switch"""
        choice = choice.lower()
        if choice not in self.class_info:
            return await ctx.send("❌ Invalid choice! Please use: `!setclass Dominant`, `Submissive`, or `Switch`.")

        daily_cog = self.bot.get_cog("DailyRewards")
        if not daily_cog:
            return await ctx.send("❌ Economy system not found.")

        user_id = str(ctx.author.id)
        
        # Ensure user structure exists
        if user_id not in daily_cog.user_data:
            daily_cog.user_data[user_id] = {
                "balance": 0, 
                "last_claim": {}, 
                "streaks": {"daily": 0, "weekly": 0, "monthly": 0},
                "xp": 0
            }

        # Set the class
        daily_cog.user_data[user_id]["class"] = choice
        daily_cog.save_data()

        embed = discord.Embed(
            title="🎭 Class Selected",
            description=f"Welcome, **{ctx.author.name}**. You are now recognized as **{choice.capitalize()}**.\n\n"
                        f"💰 **Bonus:** +{int(self.class_info[choice]['bonus']*100)}% MoonStars\n"
                        f"✨ **XP Multiplier:** {self.class_info[choice]['xp_mult']}x",
            color=self.class_info[choice]["color"]
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserClasses(bot))
