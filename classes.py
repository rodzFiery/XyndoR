import discord
from discord.ext import commands

class UserClasses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Multipliers for MoonStars
        self.class_data = {
            "dominant": {"bonus": 0.10, "xp_mult": 1.2, "color": discord.Color.red()},
            "submissive": {"bonus": 0.05, "xp_mult": 1.5, "color": discord.Color.blue()},
            "switch": {"bonus": 0.08, "xp_mult": 1.3, "color": discord.Color.purple()}
        }

    @commands.command(name="setclass")
    async def set_class(self, ctx, choice: str):
        """Allows a user to choose their class: Dominant, Submissive, or Switch."""
        choice = choice.lower()
        if choice not in self.class_data:
            return await ctx.send("❌ Invalid class! Choose: **Dominant**, **Submissive**, or **Switch**.")

        # Access the shared data from the DailyRewards Cog
        daily_cog = self.bot.get_cog("DailyRewards")
        if not daily_cog:
            return await ctx.send("❌ Economy system not found.")

        user_id = str(ctx.author.id)
        
        # Ensure user exists in data
        if user_id not in daily_cog.user_data:
            daily_cog.user_data[user_id] = {"balance": 0, "last_claim": {}, "streaks": {}}
        
        # Set the class and save
        daily_cog.user_data[user_id]["class"] = choice
        daily_cog.save_data()

        embed = discord.Embed(
            title="🎭 Class Assigned",
            description=f"You are now a **{choice.capitalize()}**!",
            color=self.class_data[choice]["color"]
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserClasses(bot))
