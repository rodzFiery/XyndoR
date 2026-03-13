import discord
from discord.ext import commands
import random
import time

class LevelingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cooldown to prevent XP spam (1 message every 30 seconds)
        self.xp_cooldowns = {} 

    def get_daily_cog(self):
        """Helper to access the central data storage."""
        return self.bot.get_cog("DailyRewards")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and commands
        if message.author.bot or message.content.startswith('!'):
            return

        daily_cog = self.get_daily_cog()
        if not daily_cog:
            return

        user_id = str(message.author.id)
        current_time = time.time()

        # Initialize config in user_data if it doesn't exist (Global Settings)
        if "config" not in daily_cog.user_data:
            daily_cog.user_data["config"] = {"selfie_channels": [], "post_channels": []}

        # XP Cooldown check
        last_xp_time = self.xp_cooldowns.get(user_id, 0)
        if current_time - last_xp_time < 15:
            return

        # Initialize User if needed
        if user_id not in daily_cog.user_data:
            daily_cog.user_data[user_id] = {"balance": 0, "xp": 0, "class": "none", "streaks": {}}

        # Logic for Different XP Gains
        xp_to_add = random.randint(15, 25) # Base XP for regular chatting
        
        # Multiplier from Classes
        user_class = daily_cog.user_data[user_id].get("class", "none")
        multiplier = 1.0
        if user_class == "submissive": multiplier = 1.5
        elif user_class == "switch": multiplier = 1.3
        elif user_class == "dominant": multiplier = 1.2
        
        # Check for Special Channels (Selfies/Posts)
        channel_id = message.channel.id
        if channel_id in daily_cog.user_data["config"].get("selfie_channels", []):
            if message.attachments: # Must have an image
                xp_to_add += 50 # Bonus for selfies
        elif channel_id in daily_cog.user_data["config"].get("post_channels", []):
            xp_to_add += 30 # Bonus for specific post channels

        # Apply XP
        final_xp = int(xp_to_add * multiplier)
        old_level = (daily_cog.user_data[user_id].get("xp", 0) // 1000) + 1
        daily_cog.user_data[user_id]["xp"] = daily_cog.user_data[user_id].get("xp", 0) + final_xp
        new_level = (daily_cog.user_data[user_id]["xp"] // 1000) + 1

        # Level Up Notification
        if new_level > old_level:
            await message.channel.send(f"🎊 **Level Up!** {message.author.mention} is now Level **{new_level}**!")

        self.xp_cooldowns[user_id] = current_time
        daily_cog.save_data()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot: return
        daily_cog = self.get_daily_cog()
        if not daily_cog: return

        user_id = str(user.id)
        if user_id not in daily_cog.user_data: return
        
        # Small XP reward for being active with reactions
        daily_cog.user_data[user_id]["xp"] += 2
        daily_cog.save_data()

    # --- ADMIN COMMANDS TO SET CHANNELS ---

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setselfie(self, ctx, channel: discord.TextChannel):
        """Sets a channel where posting images gives bonus XP."""
        daily_cog = self.get_daily_cog()
        if "config" not in daily_cog.user_data:
            daily_cog.user_data["config"] = {"selfie_channels": [], "post_channels": []}
        
        if channel.id not in daily_cog.user_data["config"]["selfie_channels"]:
            daily_cog.user_data["config"]["selfie_channels"].append(channel.id)
            daily_cog.save_data()
            await ctx.send(f"✅ {channel.mention} is now a **Selfie Channel** (Bonus XP).")
        else:
            await ctx.send("This channel is already set.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setpost(self, ctx, channel: discord.TextChannel):
        """Sets a channel where regular posts give extra XP."""
        daily_cog = self.get_daily_cog()
        if "config" not in daily_cog.user_data:
            daily_cog.user_data["config"] = {"selfie_channels": [], "post_channels": []}
            
        if channel.id not in daily_cog.user_data["config"]["post_channels"]:
            daily_cog.user_data["config"]["post_channels"].append(channel.id)
            daily_cog.save_data()
            await ctx.send(f"✅ {channel.mention} is now a **Post Channel** (Extra XP).")
        else:
            await ctx.send("This channel is already set.")

async def setup(bot):
    await bot.add_cog(LevelingSystem(bot))
