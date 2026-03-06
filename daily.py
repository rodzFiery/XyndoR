import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta

class DailyRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Temporary storage (In a professional bot, you'd eventually move this to a Database)
        self.user_bank = {} 
        self.last_claim = {} # Stores {user_id: {"daily": timestamp, "weekly": timestamp, "monthly": timestamp}}

    def check_cooldown(self, user_id, reward_type, days):
        """Helper to check if the user is still on cooldown."""
        if user_id not in self.last_claim:
            self.last_claim[user_id] = {}
        
        last_time = self.last_claim[user_id].get(reward_type)
        if last_time:
            if datetime.now() < last_time + timedelta(days=days):
                retry_after = (last_time + timedelta(days=days)) - datetime.now()
                return retry_after
        return None

    async def give_reward(self, ctx, reward_type, min_amt, max_amt, days):
        user_id = ctx.author.id
        wait_time = self.check_cooldown(user_id, reward_type, days)

        if wait_time:
            hours, remainder = divmod(int(wait_time.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return await ctx.send(f"❌ | You already claimed your {reward_type}! Try again in **{hours}h {minutes}m**.")

        # Generate MoonStars
        amount = random.randint(min_amt, max_amt)
        self.user_bank[user_id] = self.user_bank.get(user_id, 0) + amount
        self.last_claim[user_id][reward_type] = datetime.now()

        await ctx.send(f"✨ | **{ctx.author.name}**, you received **{amount:,} MoonStars** from your {reward_type}!")

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
        amt = self.user_bank.get(ctx.author.id, 0)
        await ctx.send(f"💰 | **{ctx.author.name}**, your balance is **{amt:,} MoonStars**.")

# This function is required for main.py to load this file
async def setup(bot):
    await bot.add_cog(DailyRewards(bot))
