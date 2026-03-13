import discord
from discord.ext import commands
import os

# 1. Define Intents (Required for modern Discord bots)
intents = discord.Intents.default()
intents.message_content = True  # Allows the bot to read message content

# 2. Initialize the Bot
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

# --- UPDATED LOAD COGS LOGIC ---
async def load_extensions():
    """
    Automatically loads both daily.py and classes.py.
    This logic will also load any future .py files you add!
    """
    for filename in os.listdir('./'):
        if filename.endswith('.py') and filename != 'main.py':
            try:
                # This loads 'daily', 'classes', etc.
                await bot.load_extension(filename[:-3])
                print(f'Successfully loaded: {filename}')
            except Exception as e:
                print(f'Failed to load {filename}: {e}')

# We override the setup_hook to run our loader
@bot.event
async def setup_hook():
    await load_extensions()
# ------------------------------

# 5. Run the Bot using the Railway environment variable
if __name__ == "__main__":
    # Ensure you added 'DISCORD_TOKEN' in Railway's Variables tab
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
