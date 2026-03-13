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
    print('Bot is online and ready to process commands!')

# 4. Add a Basic Command
@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# --- DYNAMIC COG LOADER ---
async def load_extensions():
    """
    This loop automatically finds and loads:
    - daily.py
    - classes.py
    - profile.py
    - Any other .py files you add in the future!
    """
    for filename in os.listdir('./'):
        # We only load .py files, and we ignore main.py itself
        if filename.endswith('.py') and filename != 'main.py':
            try:
                # filename[:-3] removes the '.py' extension
                await bot.load_extension(filename[:-3])
                print(f'✅ Successfully loaded extension: {filename}')
            except Exception as e:
                print(f'❌ Failed to load extension {filename}: {e}')

# We use the setup_hook to run our loader before the bot starts
@bot.event
async def setup_hook():
    print('Starting extension loading process...')
    await load_extensions()
# ------------------------------

# 5. Run the Bot
if __name__ == "__main__":
    # Ensure 'DISCORD_TOKEN' is set in your Railway 'Variables' tab
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("CRITICAL ERROR: DISCORD_TOKEN not found in environment variables.")
