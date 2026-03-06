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
            return {}

    def save_data(self):
        """Saves current user data to the JSON file."""
        with open(self.data_file, "w") as f:
            json.dump(self.user_data, f, indent=4)

    def check_cooldown(self, user_id, reward_type, days):
        """Checks if the user is on cooldown using stored timestamps."""
        user_id = str(user_id) # JSON keys must be strings
        if user_id not in self.user_data:
            self.user_data[user_id] = {"balance": 0, "last_claim": {}}
        
        last_claim_str = self.user_data[user_id]["last_claim"].get(reward_type)
        
        if last_claim_str:
            last_time = datetime.fromisoformat(last_claim_str)
            if datetime.now() < last_time + timedelta(days=days):
                return (last_time + timedelta(days=days)) - datetime.now()
        return None

    async def give_reward(self, ctx, reward_type, min_amt, max_amt, days):
        user_id = str(ctx.author.id)
        wait_time = self.check_cooldown(user_id, reward_type, days)

        if wait_time:
            hours, remainder = divmod(int(wait_time.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            return await ctx.send(f"❌ | Too soon! You can claim your {reward_type} in **{hours}h {minutes}m**.")

        # Generate MoonStars and update data
        amount = random.randint(min_amt, max_amt)
        self.user_data[user_id]["balance"] += amount
        self.user_data[user_id]["last_claim"][reward_type] = datetime.now().isoformat()
        
        # ADDED: Save immediately after change
        self.save_data()

        await ctx.send(f"✨ | **{ctx.author.name}**, you earned **{amount:,} MoonStars**! Total: **{self.user_data[user_id]['balance']:,}**")

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
        amt = self.user_data.get(user_id, {}).get("balance", 0)
        await ctx.send(f"💰 | **{ctx.author.name}**, your balance is **{amt:,} MoonStars**.")

async def setup(bot):
    await bot.add_cog(DailyRewards(bot))
