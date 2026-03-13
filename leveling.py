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
        """Helper to access the central data storage from DailyRewards."""
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

        # Initialize global config if it doesn't exist
        if "config" not in daily_cog.user_data:
            daily_cog.user_data["config"] = {
                "selfie_channels": [], 
                "post_channels": [],
                "level_up_channel": None
            }

        # XP Cooldown check (prevent spamming)
        last_xp_time = self.xp_cooldowns.get(user_id, 0)
        if current_time - last_xp_time < 30:
            return

        # Ensure User data structure exists
        if user_id not in daily_cog.user_data:
            daily_cog.user_data[user_id] = {
                "balance": 0, 
                "xp": 0, 
                "class": "none", 
                "streaks": {"daily": 0, "weekly": 0, "monthly": 0},
                "last_claim": {}
            }

        # --- XP Calculation Logic ---
        xp_to_add = random.randint(15, 25) # Base XP for regular chatting
        
        # Multiplier based on Classes from classes.py
        user_class = daily_cog.user_data[user_id].get("class", "none")
        multiplier = 1.0
        if user_class == "submissive": 
            multiplier = 1.5
        elif user_class == "switch": 
            multiplier = 1.3
        elif user_class == "dominant": 
            multiplier = 1.2
        
        # Check for Special Channels (Selfies/Posts)
        channel_id = message.channel.id
        config = daily_cog.user_data["config"]
        
        if channel_id in config.get("selfie_channels", []):
            if message.attachments: # Bonus only if an image/file is attached
                xp_to_add += 50 
        elif channel_id in config.get("post_channels", []):
            xp_to_add += 30 

        # Apply final XP
        final_xp = int(xp_to_add * multiplier)
        old_xp = daily_cog.user_data[user_id].get("xp", 0)
        old_level = (old_xp // 1000) + 1
        
        daily_cog.user_data[user_id]["xp"] = old_xp + final_xp
        new_level = (daily_cog.user_data[user_id]["xp"] // 1000) + 1

        # --- Level Up Notification Logic ---
        if new_level > old_level:
            level_channel_id = config.get("level_up_channel")
            target_channel = self.bot.get_channel(level_channel_id) if level_channel_id else message.channel

            embed = discord.Embed(
                title="🎊 Level Up!",
                description=f"Congratulations {message.author.mention}!\nYou have reached **Level {new_level}**.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Keep active to earn more XP!")
            
            try:
                await target_channel.send(embed=embed)
            except:
                # Fallback to current channel if target channel is missing/no permissions
                await message.channel.send(f"🎊 **Level Up!** {message.author.mention} is now Level **{new_level}**!")

        # Update cooldown and save to Railway Volume
        self.xp_cooldowns[user_id] = current_time
        daily_cog.save_data()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Give a tiny bit of XP for reacting to messages."""
        if user.bot: 
            return
            
        daily_cog = self.get_daily_cog()
        if not daily_cog: 
            return

        user_id = str(user.id)
        if user_id in daily_cog.user_data:
            daily_cog.user_data[user_id]["xp"] = daily_cog.user_data[user_id].get("xp", 0) + 2
            daily_cog.save_data()

    # --- ADMIN CONFIGURATION COMMANDS ---

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setselfie(self, ctx, channel: discord.TextChannel):
        """Sets a channel where posting images gives bonus XP."""
        daily_cog = self.get_daily_cog()
        if "config" not in daily_cog.user_data:
            daily_cog.user_data["config"] = {"selfie_channels": [], "post_channels": [], "level_up_channel": None}
        
        if channel.id not in daily_cog.user_data["config"]["selfie_channels"]:
            daily_cog.user_data["config"]["selfie_channels"].append(channel.id)
            daily_cog.save_data()
            await ctx.send(f"✅ {channel.mention} is now a **Selfie Channel** (Bonus XP for images).")
        else:
            await ctx.send("This channel is already a selfie channel.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setpost(self, ctx, channel: discord.TextChannel):
        """Sets a channel where regular posts give extra XP."""
        daily_cog = self.get_daily_cog()
        if "config" not in daily_cog.user_data:
            daily_cog.user_data["config"] = {"selfie_channels": [], "post_channels": [], "level_up_channel": None}
            
        if channel.id not in daily_cog.user_data["config"]["post_channels"]:
            daily_cog.user_data["config"]["post_channels"].append(channel.id)
            daily_cog.save_data()
            await ctx.send(f"✅ {channel.mention} is now a **Post Channel** (Extra XP).")
        else:
            await ctx.send("This channel is already a post channel.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlevelchannel(self, ctx, channel: discord.TextChannel):
        """Sets the channel where level-up messages are sent."""
        daily_cog = self.get_daily_cog()
        if "config" not in daily_cog.user_data:
            daily_cog.user_data["config"] = {"selfie_channels": [], "post_channels": [], "level_up_channel": None}
        
        daily_cog.user_data["config"]["level_up_channel"] = channel.id
        daily_cog.save_data()
        await ctx.send(f"✅ Level-up announcements will now be sent in {channel.mention}.")

async def setup(bot):
    await bot.add_cog(LevelingSystem(bot))
