# FIX: Python 3.13 compatibility shim for audioop
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        import sys
        sys.modules['audioop'] = audioop
    except ImportError:
        pass 

import discord
from discord.ext import commands, tasks
import random
import os
import asyncio
import json
import traceback
import sys
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
import io
import aiohttp

# Importação do Lexicon para as frases de efeito
from lexicon import FieryLexicon

class LobbyView(discord.ui.View):
    def __init__(self, owner, edition):
        super().__init__(timeout=None)
        self.owner = owner
        self.edition = edition
        self.participants = []
        self.active = True 

    @discord.ui.button(label="Enter the Red room", style=discord.ButtonStyle.success, emoji="🔞", custom_id="fiery_join_button")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.active:
            return await interaction.response.send_message("❌ **The gates are locked.** The session has already begun.", ephemeral=True)

        if interaction.user.id in self.participants:
            return await interaction.response.send_message("🫦 **You are already chained in the Red Room.**", ephemeral=True)
        
        self.participants.append(interaction.user.id)
        
        try:
            embed = interaction.message.embeds[0]
            embed.set_field_at(0, name=f"🧙‍♂️ {len(self.participants)} Sinners Ready", value="*Final checks on chains, collars, and control..*", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send("🔞 **The chains lock in place.** You have entered the Red Room.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("The Master acknowledges your signin. You are joined!", ephemeral=True)

    @discord.ui.button(label="Turn off the lights and start", style=discord.ButtonStyle.danger, emoji="😈", custom_id="fiery_start_button")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        main = sys.modules['__main__']
        data = main.load_data()
        
        # Check for admin role in JSON settings
        gid = str(interaction.guild.id)
        ignis_admin_role_id = data.get("guild_settings", {}).get(gid, {}).get("ignis_admin_role")

        is_staff = any(role.name in ["Staff", "Admin", "Moderator"] or role.id == ignis_admin_role_id for role in getattr(interaction.user, 'roles', []))
        owner_id = getattr(self.owner, 'id', None)
        
        if owner_id and interaction.user.id != owner_id and not is_staff:
            return await interaction.response.send_message("Only the Masters or Staff start the games!", ephemeral=True)
        
        if len(self.participants) < 2:
            return await interaction.response.send_message("Need at least 2 souls!", ephemeral=True)
        
        engine = interaction.client.get_cog("IgnisEngine")
        if engine: 
            self.active = False
            await interaction.response.defer(ephemeral=True)
            await interaction.channel.send("🔞 **THE LIGHTS GO OUT... ECHO HANGRYGAMES HAS BEGUN!**")
            asyncio.create_task(engine.start_battle(interaction.channel, list(self.participants), self.edition))
            self.stop()

class IgnisEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = set()
        self.current_lobbies = {}
        self.current_survivors = {}
        self.last_winner_id = None
        self.flash_sentences = [
            "Strip for me, toy. Let the whole dungeon see your shame.",
            "I want to see everything. Drop the fabric and obey.",
            "Your body belongs to the winner now. Flash us.",
            "Toys don't wear clothes. Drop them."
        ]

    def sync_user_data(self, user_id, **kwargs):
        """JSON Sync Bridge: Updates the main daily_data.json"""
        main = sys.modules['__main__']
        data = main.load_data()
        uid = str(user_id)
        
        if uid not in data["users"]:
            data["users"][uid] = {"balance": 0, "xp": 0, "kills": 0, "deaths": 0, "wins": 0, "current_win_streak": 0}
        
        user = data["users"][uid]
        user["balance"] = user.get("balance", 0) + kwargs.get("amount", 0)
        user["xp"] = user.get("xp", 0) + kwargs.get("xp_gain", 0)
        user["kills"] = user.get("kills", 0) + kwargs.get("kills", 0)
        user["deaths"] = user.get("deaths", 0) + kwargs.get("deaths", 0)
        user["wins"] = user.get("wins", 0) + kwargs.get("wins", 0)
        
        if kwargs.get("deaths", 0) > 0:
            user["current_win_streak"] = 0
            
        main.save_data(data)
        return user

    async def create_arena_image(self, winner_url, loser_url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(winner_url) as r1, session.get(loser_url) as r2:
                    p1_data = io.BytesIO(await r1.read())
                    p2_data = io.BytesIO(await r2.read())
            
            bg = Image.new("RGBA", (1000, 500), (40, 0, 0, 255))
            av_winner = Image.open(p1_data).convert("RGBA").resize((400, 400))
            av_loser = ImageOps.grayscale(Image.open(p2_data).convert("RGBA")).convert("RGBA").resize((400, 400))
            
            # Apply Red Tint to loser
            red_overlay = Image.new("RGBA", (400, 400), (255, 0, 0, 100))
            av_loser = Image.alpha_composite(av_loser, red_overlay)

            bg.paste(av_winner, (50, 50), av_winner)
            bg.paste(av_loser, (550, 50), av_loser)
            
            buf = io.BytesIO()
            bg.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except:
            return None

    async def start_battle(self, channel, participants, edition):
        main = sys.modules['__main__']
        self.active_battles.add(channel.id)
        self.current_survivors[channel.id] = list(participants)
        
        fighters = []
        for p_id in participants:
            m = channel.guild.get_member(p_id) or await channel.guild.fetch_member(p_id)
            fighters.append({"id": p_id, "name": m.display_name, "avatar": m.display_avatar.url})

        await channel.send(FieryLexicon.get_intro())
        await asyncio.sleep(3)

        while len(fighters) > 1:
            p1 = fighters.pop(random.randrange(len(fighters)))
            p2 = fighters.pop(random.randrange(len(fighters)))
            
            winner, loser = (p1, p2) if random.random() > 0.5 else (p2, p1)
            fighters.append(winner)
            self.current_survivors[channel.id].remove(loser['id'])
            
            # Update JSON stats
            self.sync_user_data(winner['id'], kills=1, xp_gain=500)
            self.sync_user_data(loser['id'], deaths=1)

            img_buf = await self.create_arena_image(winner['avatar'], loser['avatar'])
            embed = main.fiery_embed(f"⚔️ {winner['name']} vs {loser['name']}", FieryLexicon.get_kill(winner['name'], loser['name']))
            
            if img_buf:
                file = discord.File(img_buf, filename="arena.png")
                embed.set_image(url="attachment://arena.png")
                await channel.send(file=file, embed=embed)
            else:
                await channel.send(embed=embed)
            
            await asyncio.sleep(5)

        # Final Winner
        winner_final = fighters[0]
        self.last_winner_id = winner_final['id']
        self.sync_user_data(winner_final['id'], amount=25000, xp_gain=5000, wins=1)

        win_embed = main.fiery_embed("🏆 SUPREME VICTOR", f"{winner_member.mention} has conquered Edition #{edition}!")
        win_embed.set_image(url=winner_final['avatar'])
        await channel.send(embed=win_embed)
        
        self.active_battles.remove(channel.id)

class EngineControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echostart(self, ctx):
        main = sys.modules['__main__']
        data = main.load_data()
        
        edition = data.get("game_edition", 1)
        view = LobbyView(ctx.author, edition)
        
        embed = main.fiery_embed(f"Echo's Hangrygames Edition #{edition}", "Step into the Red Room and sign your soul away.")
        embed.add_field(name="🧙‍♂️ 0 Sinners Ready", value="The air is thick with anticipation.", inline=False)
        
        await ctx.send(embed=embed, view=view)
        
        data["game_edition"] = edition + 1
        main.save_data(data)

async def setup(bot):
    await bot.add_cog(IgnisEngine(bot))
    await bot.add_cog(EngineControl(bot))
