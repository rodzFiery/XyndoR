import discord
from discord.ext import commands
import random
import json
import os
from datetime import datetime, timedelta

class DailyRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "daily_data.json"
        self.user_data = self.load_data()

    def load_data(self):
        """Loads user data from the JSON file."""
        if not os.path.exists(self.data_file):
            return {}
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If the file is empty or corrupted, return an empty dict
            return {}

    def save_data(self):
        """Saves current user data to the JSON file."""
        with open(self.data_file, "w") as f:
            json.dump(self.user_data, f, indent=4)

    def create_reward_embed(self, title, description, color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url="attachment://xyndorlogo.jpeg")
        embed.set_footer(text="Xyndor Economy System")
        return embed

    def check_cooldown(self, user_id, reward_type, days):
        """Checks if the user is on cooldown and ensures data structure exists."""
        user_id = str(user_id)
        
        # Initialize user if they don't exist in the JSON yet
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "balance": 0, 
                "last_claim": {}, 
                "streaks": {"daily": 0, "weekly": 0, "monthly": 0}
            }
            self.save_data() # Save immediately so the structure persists
        
        # Ensure 'streaks' key exists for older data entries
        if "streaks" not in self.user_data[user_id]:
            self.user_data[user_id]["streaks"] = {"daily": 0, "weekly": 0, "monthly": 0}
            self.save_data()

        last_claim_str = self.user_data[user_id]["last_claim"].get(reward_type)
        
        if last_claim_str:
            # Convert the ISO string from JSON back into a Python datetime object
            last_time = datetime.fromisoformat(last_claim_str)
            now = datetime.now()
            
            # If current time is less than the required wait time, return the remaining time
            if now < last_time + timedelta(days=days):
                return (last_time + timedelta(days=days)) - now
                
        return None

    async def give_reward(self, ctx, reward_type, min_amt, max_amt, days):
        user_id = str(ctx.author.id)
        wait_time = self.check_cooldown(user_id, reward_type, days)
        logo_file = discord.File("xyndorlogo.jpeg", filename="xyndorlogo.jpeg")

        if wait_time:
            # Calculate hours and minutes for the error message
            total_seconds = int(wait_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            current_streak = self.user_data[user_id]["streaks"].get(reward_type, 0)
            embed = self.create_reward_embed(
                "❌ | Cooldown Active", 
                f"Too soon! You can claim your **{reward_type}** in **{hours}h {minutes}m**.\n"
                f"🔥 **Current Streak:** {current_streak}",
                discord.Color.red()
            )
            return await ctx.send(file=logo_file, embed=embed)

        # Logic for processing a successful claim
        # 1. Update Streak
        self.user_data[user_id]["streaks"][reward_type] = self.user_data[user_id]["streaks"].get(reward_type, 0) + 1
        streak_count = self.user_data[user_id]["streaks"][reward_type]

        # 2. Calculate Payout
        base_amount = random.randint(min_amt, max_amt)
        bonus = int(base_amount * (streak_count * 0.05)) 
        total_amount = base_amount + bonus

        # 3. Update Balance and Timestamp
        self.user_data[user_id]["balance"] += total_amount
        self.user_data[user_id]["last_claim"][reward_type] = datetime.now().isoformat()
        
        # 4. Save to daily_data.json IMMEDIATELY before sending the Discord message
        # This prevents "re-roll" exploits if the bot crashes right after claiming
        self.save_data()

        embed = self.create_reward_embed(
            f"✨ | {reward_type.capitalize()} Reward Claimed!",
            f"Congratulations **{ctx.author.name}**!\n\n"
            f"💰 **Base:** {base_amount:,}\n"
            f"🔥 **Streak Bonus:** +{bonus:,} ({streak_count}x)\n"
            f"🎁 **Total Earned:** {total_amount:,} MoonStars\n"
            f"🏦 **New Balance:** {self.user_data[user_id]['balance']:,} MoonStars",
            discord.Color.gold()
        )
        
        await ctx.send(file=logo_file, embed=embed)

    @commands.command()
    async def daily(self, ctx):
        await self.give_reward(ctx, "daily", 1000, 3000, 1)

    @commands.command()
    async def weekly(self, ctx):
        await self.give_reward(ctx, "weekly", 7000, 10000, 7)

    @commands.command()
    async def monthly(self, ctx):
        await self.give_reward(ctx, "monthly", 28000, 35000, 30)

    @commands.command()
    async def balance(self, ctx):
        user_id = str(ctx.author.id)
        # Handle cases where balance is called before any claims
        if user_id not in self.user_data:
            self.user_data[user_id] = {"balance": 0, "last_claim": {}, "streaks": {"daily": 0, "weekly": 0, "monthly": 0}}
            self.save_data()
            
        amt = self.user_data[user_id]["balance"]
        streaks = self.user_data[user_id].get("streaks", {"daily": 0, "weekly": 0, "monthly": 0})
        
        logo_file = discord.File("xyndorlogo.jpeg", filename="xyndorlogo.jpeg")
        embed = self.create_reward_embed(
            "💰 Account Balance",
            f"**User:** {ctx.author.mention}\n"
            f"**Total:** {amt:,} MoonStars\n\n"
            f"**Streaks:**\n"
            f"📅 Daily: {streaks.get('daily', 0)}\n"
            f"🗓️ Weekly: {streaks.get('weekly', 0)}\n"
            f"🌙 Monthly: {streaks.get('monthly', 0)}",
            discord.Color.blue()
        )
        
        await ctx.send(file=logo_file, embed=embed)

    @commands.command(name="dailylb")
    async def dailylb(self, ctx):
        user_id = str(ctx.author.id)
        data = self.user_data.get(user_id, {})
        streaks = data.get("streaks", {"daily": 0, "weekly": 0, "monthly": 0})
        balance = data.get("balance", 0)

        stats_description = (
            f"Hello **{ctx.author.name}**! Here is your global progress:\n\n"
            f"🔥 **Daily Streak:** {streaks.get('daily', 0)} days\n"
            f"⚡ **Weekly Streak:** {streaks.get('weekly', 0)} weeks\n"
            f"💎 **Monthly Streak:** {streaks.get('monthly', 0)} months\n\n"
            f"💰 **Total Balance:** {balance:,} MoonStars\n"
            f"🌍 *These stats are linked to your ID across all servers.*"
        )

        logo_file = discord.File("xyndorlogo.jpeg", filename="xyndorlogo.jpeg")
        embed = self.create_reward_embed(
            "📊 Your Personal Streak Statistics",
            stats_description,
            discord.Color.purple()
        )
        await ctx.send(file=logo_file, embed=embed)

async def setup(bot):
    await bot.add_cog(DailyRewards(bot))
async def setup(bot):
    await bot.add_cog(DailyRewards(bot))
