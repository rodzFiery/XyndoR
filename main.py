import discord
from discord.ext import commands
import os

# 1. Define Intents (Required for modern Discord bots)
intents = discord.Intents.default()
intents.message_content = True  # Allows the bot to read message content

# 2. Initialize the Bot
# We use commands.Bot for full functionality
bot = commands.Bot(command_prefix='!', intents=intents)

# 3. Add an Event: On Ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

# 4. Add a Basic Command
@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# 5. Run the Bot using the Railway environment variable
if __name__ == "__main__":
    # Ensure you added 'DISCORD_TOKEN' in Railway's Variables tab
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
