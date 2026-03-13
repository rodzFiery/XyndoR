import discord
from discord.ext import commands
from datetime import datetime

class UserProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_level(self, xp):
        """Calculates level based on XP. Every 1000 XP = 1 Level."""
        return (xp // 1000) + 1

    @commands.command(name="me")
    async def profile(self, ctx):
        """Displays the user's full economy profile and stats."""
        # 1. Get the DailyRewards Cog to access the central data
        daily_cog = self.bot.get_cog("DailyRewards")
        
        if not daily_cog:
            return await ctx.send("❌ Economy system (daily.py) not found.")

        user_id = str(ctx.author.id)
        
        # 2. Check if user exists, otherwise initialize them
        if user_id not in daily_cog.user_data:
            daily_cog.user_data[user_id] = {
                "balance": 0, 
                "last_claim": {}, 
                "streaks": {"daily": 0, "weekly": 0, "monthly": 0},
                "xp": 0,
                "class": "none"
            }
            daily_cog.save_data()

        # 3. Extract data for the embed
        data = daily_cog.user_data[user_id]
        balance = data.get("balance", 0)
        xp = data.get("xp", 0)
        user_class = data.get("class", "none").capitalize()
        streaks = data.get("streaks", {"daily": 0, "weekly": 0, "monthly": 0})
        
        # Level Calculation logic
        level = self.get_level(xp)
        xp_to_next = 1000 - (xp % 1000)
        progress = (xp % 1000) / 1000
        bar_length = 10
        filled = int(progress * bar_length)
        bar = "▰" * filled + "▱" * (bar_length - filled)

        # Determine color based on class
        embed_color = discord.Color.light_grey()
        if user_class.lower() == "dominant":
            embed_color = discord.Color.red()
        elif user_class.lower() == "submissive":
            embed_color = discord.Color.blue()
        elif user_class.lower() == "switch":
            embed_color = discord.Color.purple()

        # 4. Create the Profile Embed
        embed = discord.Embed(
            title=f"👤 {ctx.author.name}'s Profile",
            description=f"Level **{level}** {user_class}\n`{bar}` {int(progress*100)}%\nNext level in **{xp_to_next}** XP",
            color=embed_color,
            timestamp=datetime.now()
        )
        
        # Add Fields
        embed.add_field(name="💰 Wallet", value=f"{balance:,} MoonStars", inline=True)
        embed.add_field(name="✨ Total XP", value=f"{xp:,} XP", inline=True)
        
        streak_text = (
            f"📅 **Daily:** {streaks.get('daily', 0)}\n"
            f"🗓️ **Weekly:** {streaks.get('weekly', 0)}\n"
            f"🌙 **Monthly:** {streaks.get('monthly', 0)}"
        )
        embed.add_field(name="🔥 Streaks", value=streak_text, inline=False)

        # Set image/thumbnail logic
        # Note: Make sure xyndorlogo.jpeg is in your root folder on Railway
        try:
            logo_file = discord.File("xyndorlogo.jpeg", filename="xyndorlogo.jpeg")
            embed.set_thumbnail(url="attachment://xyndorlogo.jpeg")
            await ctx.send(file=logo_file, embed=embed)
        except Exception:
            # Fallback if the image file is missing
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserProfile(bot))
