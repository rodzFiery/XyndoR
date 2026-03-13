import discord
from discord.ext import commands, tasks
import random
import os
import asyncio
import json
import traceback
import sys
from PIL import Image, ImageDraw, ImageOps
import io
import aiohttp

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

# Importação do Lexicon para as frases de efeito
from lexicon import FieryLexicon

class LobbyView(discord.ui.View):
    def __init__(self, owner, edition, bot):
        super().__init__(timeout=None)
        self.owner = owner
        self.edition = edition
        self.bot = bot
        self.participants = []
        self.active = True 

    @discord.ui.button(label="Enter the Red room", style=discord.ButtonStyle.success, emoji="🔞", custom_id="fiery_join_button")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.active:
            return await interaction.response.send_message("❌ **The gates are locked.** The session has already begun.", ephemeral=True)

        if interaction.user.id in self.participants:
            return await interaction.response.send_message("🫦 **You are already chained in the Red Room.** There is no escape now.", ephemeral=True)
        
        self.participants.append(interaction.user.id)
        
        try:
            embed = interaction.message.embeds[0]
            embed.set_field_at(0, name=f"🧙‍♂️ {len(self.participants)} Sinners Ready", value="*Final checks on chains, collars, lights and control..*", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send("🔞 **The chains lock in place.** You have successfully entered the Red Room.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("The Master acknowledges your signin but the ledger glitched. You are joined!", ephemeral=True)

    @discord.ui.button(label="Turn off the lights and start", style=discord.ButtonStyle.danger, emoji="😈", custom_id="fiery_start_button")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        main = sys.modules['__main__']
        data = main.load_data()
        
        # Check for Ignis Admin Role in JSON
        guild_id_str = str(interaction.guild.id)
        ignis_admin_role_id = data.get("guild_settings", {}).get(guild_id_str, {}).get("ignis_admin_role")

        is_staff = any(role.name in ["Staff", "Admin", "Moderator"] or role.id == ignis_admin_role_id for role in getattr(interaction.user, 'roles', []))
        owner_id = getattr(self.owner, 'id', None)
        
        if owner_id and interaction.user.id != owner_id and not is_staff:
            return await interaction.response.send_message("Only the Masters or Staff start the games!", ephemeral=True)
        
        if len(self.participants) < 2:
            return await interaction.response.send_message("Need at least 2 sexy fucks !", ephemeral=True)
        
        engine = interaction.client.get_cog("IgnisEngine")
        if engine: 
            guild_games = 0
            for channel_id in engine.active_battles:
                ch = interaction.client.get_channel(channel_id)
                if ch and ch.guild and ch.guild.id == interaction.guild.id:
                    guild_games += 1
            
            if guild_games >= 2:
                return await interaction.response.send_message("❌ **The Red Room is at capacity.** Only 2 games per server.", ephemeral=True)

            self.active = False
            await interaction.response.defer(ephemeral=True)

            if interaction.guild.id in engine.current_lobbies:
                del engine.current_lobbies[interaction.guild.id]
            
            await interaction.channel.send("🔞 **THE LIGHTS GO OUT... ECHO HANGRYGAMES EDITION HAS BEGUN!**")
            asyncio.create_task(engine.start_battle(interaction.channel, list(self.participants), self.edition))
            self.stop()
        else:
            return await interaction.followup.send("❌ Error: IgnisEngine not found.", ephemeral=True)

class EngineControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_ignis_admin(self, ctx, role: discord.Role):
        main = sys.modules['__main__']
        data = main.load_data()
        if "guild_settings" not in data: data["guild_settings"] = {}
        gid = str(ctx.guild.id)
        if gid not in data["guild_settings"]: data["guild_settings"][gid] = {}
        
        data["guild_settings"][gid]["ignis_admin_role"] = role.id
        main.save_data(data)
        await ctx.send(embed=main.fiery_embed("Settings Updated", f"The role {role.mention} is now an **Ignis Admin**."))

    @commands.command()
    async def echostart(self, ctx):
        main = sys.modules['__main__']
        image_path = "LobbyTopRight.jpg"
        
        game_edition = main.load_data().get("game_edition", 1)
        
        embed = discord.Embed(
            title=f"Echo's Hangrygames Edition # {game_edition}", 
            description="The hellgates are about to open, little pets. Submit to the registration.", 
            color=0xFF0000
        )
        
        view = LobbyView(ctx.author, game_edition, self.bot)
        engine = self.bot.get_cog("IgnisEngine")
        if engine: 
            engine.current_lobbies[ctx.guild.id] = view

        if os.path.exists(image_path):
            file = discord.File(image_path, filename="lobby_thumb.jpg")
            embed.set_thumbnail(url="attachment://lobby_thumb.jpg")
            embed.add_field(name="🧙‍♂️ 0 Sinners Ready", value="The air is thick with anticipation.", inline=False)
            await ctx.send(file=file, embed=embed, view=view)
        else:
            embed.set_thumbnail(url="https://i.imgur.com/Gis6f9V.gif")
            embed.add_field(name="🧙‍♂️ 0 Sinners Ready", value="\u200b", inline=False)
            await ctx.send(embed=embed, view=view)
        
        data = main.load_data()
        data["game_edition"] = game_edition + 1
        main.save_data(data)

class IgnisEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = set() 
        self.current_lobbies = {} 
        self.current_survivors = {} 
        self.last_winner_id = None
        self.flash_sentences = FieryLexicon.flash_sentences # Pulled from external Lexicon

    def calculate_level(self, current_xp):
        level = 1
        xp_needed = 500
        while current_xp >= xp_needed and level < 100:
            current_xp -= xp_needed
            level += 1
            if level <= 15: xp_needed = 2500
            elif level <= 30: xp_needed = 5000
            elif level <= 60: xp_needed = 7500
            else: xp_needed = 5000
        return level

    async def create_arena_image(self, winner_url, loser_url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(winner_url) as r1, session.get(loser_url) as r2:
                    p1_data = io.BytesIO(await r1.read())
                    p2_data = io.BytesIO(await r2.read())
            
            canvas_w, canvas_h = 1000, 1000
            bg_path = "1v1Background.jpg"
            bg = Image.open(bg_path).convert("RGBA").resize((canvas_w, canvas_h)) if os.path.exists(bg_path) else Image.new("RGBA", (canvas_w, canvas_h), (180, 30, 0, 255))
            
            av_large = 420
            av_winner = Image.open(p1_data).convert("RGBA").resize((av_large, av_large))
            av_winner = ImageOps.expand(av_winner, border=10, fill="orange")
            
            av_loser_raw = Image.open(p2_data).convert("RGBA").resize((av_large, av_large))
            av_loser = ImageOps.grayscale(av_loser_raw).convert("RGBA")
            red_overlay = Image.new("RGBA", av_loser.size, (255, 0, 0, 100))
            av_loser = Image.alpha_composite(av_loser, red_overlay)
            av_loser = ImageOps.expand(av_loser, border=10, fill="gray")
            
            bg.paste(av_winner, (40, 150), av_winner)
            bg.paste(av_loser, (540, 150), av_loser)
            
            draw = ImageDraw.Draw(bg)
            draw.line((400, 220, 600, 480), fill=(220, 220, 220), width=25)
            draw.line((600, 220, 400, 480), fill=(220, 220, 220), width=25)
            
            buf = io.BytesIO()
            bg.crop((0, 50, 1000, 750)).save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception:
            fallback = Image.new("RGBA", (1000, 700), (120, 20, 0, 255))
            buf = io.BytesIO()
            fallback.save(buf, format="PNG")
            buf.seek(0)
            return buf

    async def start_battle(self, channel, participants, edition):
        if channel.id in self.active_battles: return
        self.active_battles.add(channel.id)
        
        main = sys.modules['__main__']
        fxp_log = {p_id: {"participation": 100, "kills": 0, "first_kill": 0, "placement": 0} for p_id in participants}
        first_blood_recorded = False
        
        try:
            fighters = []
            game_kills = {p_id: 0 for p_id in participants}
            
            data = main.load_data()
            users = data.get("users", {})

            for p_id in participants:
                uid = str(p_id)
                if uid not in users: continue
                
                member = channel.guild.get_member(p_id) or await channel.guild.fetch_member(p_id)
                if not member: continue
                
                fighters.append({"id": p_id, "name": member.display_name, "avatar": member.display_avatar.url})
                users[uid]["games_played"] = users[uid].get("games_played", 0) + 1

            self.current_survivors[channel.id] = [f['id'] for f in fighters]
            main.save_data(data)

            await channel.send(FieryLexicon.get_intro())
            await asyncio.sleep(2)

            while len(fighters) > 1:
                # Combat Loop Logic (Simplified for brevity but identical in math)
                p1 = fighters.pop(random.randrange(len(fighters)))
                p2 = fighters.pop(random.randrange(len(fighters)))
                
                winner, loser = (p1, p2) if random.random() < 0.5 else (p2, p1)
                fighters.append(winner)
                
                if channel.id in self.current_survivors:
                    self.current_survivors[channel.id].remove(loser['id'])
                
                game_kills[winner['id']] += 1
                fxp_log[winner['id']]["kills"] += 750
                
                # Visuals
                img = await self.create_arena_image(winner['avatar'], loser['avatar'])
                await channel.send(file=discord.File(img, "arena.png"), embed=discord.Embed(title="⚔️ Combat", description=FieryLexicon.get_kill(winner['name'], loser['name']), color=0xFF4500).set_image(url="attachment://arena.png"))
                await asyncio.sleep(4)

            # Winner Logic
            winner_final = fighters[0]
            self.last_winner_id = winner_final['id']
            await channel.send(FieryLexicon.get_winner_announcement(f"<@{winner_final['id']}>"))
            
            # Save final stats back to JSON
            data = main.load_data()
            data["users"][str(winner_final['id'])]["moonstars"] = data["users"][str(winner_final['id'])].get("moonstars", 0) + 25000
            main.save_data(data)

        finally:
            self.active_battles.remove(channel.id)

async def setup(bot):
    await bot.add_cog(IgnisEngine(bot))
    await bot.add_cog(EngineControl(bot))
