import discord
from discord.ext import commands
import sqlite3
import random

from dotenv import load_dotenv
import os

from keep_alive import keep_alive

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Connexion à la base de données
conn = sqlite3.connect("stats.db")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        user_id INTEGER PRIMARY KEY,
        games_played INTEGER DEFAULT 0,
        mvps INTEGER DEFAULT 0,
        victories INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0
    )
""")
conn.commit()

# Rôles autorisés par commande
authorized_roles = {
    "mvp": [1131231591943901296, 1131231591943901300, 1131231591973257250, 1131657543127670854, 1131231592090697769],
    "addgame": [1131231591943901296, 1131231591943901300, 1131231591973257250, 1131657543127670854, 1131231592090697769],
    "lb": [],
    "pg": [],
    "stats": [],
    "roulette": [1131231591943901296, 1131231591943901300, 1131231591973257250, 1131657543127670854, 1131231592090697769],
    "aw": [1131231591943901296, 1131231591943901300, 1131231591973257250, 1131657543127670854, 1131231592090697769],
    "al": [1131231591943901296, 1131231591943901300, 1131231591973257250, 1131657543127670854, 1131231592090697769]
}

# Ajoute la colonne 'losses' si elle n'existe pas
try:
    cur.execute("ALTER TABLE stats ADD COLUMN losses INTEGER DEFAULT 0")
    conn.commit()
except sqlite3.OperationalError:
    pass  # La colonne existe déjà


def has_rank(ctx, command):
    if not authorized_roles.get(command):
        return True
    return any(role.id in authorized_roles[command] for role in ctx.author.roles)

@bot.command()
async def mvp(ctx, member: discord.Member):
    if not has_rank(ctx, "mvp"):
        return await ctx.send("**Tu n'as pas la permission d'exécuter cette commande.**")
    cur.execute("INSERT OR IGNORE INTO stats (user_id) VALUES (?)", (member.id,))
    cur.execute("UPDATE stats SET mvps = mvps + 1 WHERE user_id = ?", (member.id,))
    conn.commit()
    await ctx.send(f"**MVP ajouté pour {member.mention}.**")

@bot.command()
async def addgame(ctx, voice_channel_id: int):
    if not has_rank(ctx, "addgame"):
        return await ctx.send("**Tu n'as pas la permission d'exécuter cette commande.**")
    channel = bot.get_channel(voice_channel_id)
    if not isinstance(channel, discord.VoiceChannel):
        return await ctx.send("ID invalide.")
    for member in channel.members:
        cur.execute("INSERT OR IGNORE INTO stats (user_id) VALUES (?)", (member.id,))
        cur.execute("UPDATE stats SET games_played = games_played + 1 WHERE user_id = ?", (member.id,))
    conn.commit()
    await ctx.send("**Parties ajoutées à tous les membres connectés.**")

@bot.command()
async def aw(ctx, voice_channel_id: int):
    if not has_rank(ctx, "aw"):
        return await ctx.send("**Tu n'as pas la permission d'exécuter cette commande.**")
    channel = bot.get_channel(voice_channel_id)
    if not isinstance(channel, discord.VoiceChannel):
        return await ctx.send("ID de salon vocal invalide.")
    
    for member in channel.members:
        cur.execute("INSERT OR IGNORE INTO stats (user_id) VALUES (?)", (member.id,))
        cur.execute("""
            UPDATE stats SET
                victories = victories + 1,
                games_played = games_played + 1
            WHERE user_id = ?
        """, (member.id,))
    conn.commit()
    await ctx.send("**✅ Victoire + Partie ajoutée à tous les membres du salon.**")

@bot.command()
async def al(ctx, voice_channel_id: int):
    if not has_rank(ctx, "al"):
        return await ctx.send("Tu n'as pas la permission d'exécuter cette commande.")
    channel = bot.get_channel(voice_channel_id)
    if not isinstance(channel, discord.VoiceChannel):
        return await ctx.send("ID de salon vocal invalide.")
    
    for member in channel.members:
        cur.execute("INSERT OR IGNORE INTO stats (user_id) VALUES (?)", (member.id,))
        cur.execute("""
            UPDATE stats SET
                losses = losses + 1,
                games_played = games_played + 1
            WHERE user_id = ?
        """, (member.id,))
    conn.commit()
    await ctx.send("**✅ Défaite + Partie ajoutée à tous les membres du salon.**")


@bot.command()
async def lb(ctx):
    allowed_channels = [1131419095796035624, 1386040436312903691, 1135965417941241866]
    if ctx.channel.id not in allowed_channels:
        return await ctx.send("**❌ Cette commande ne peut être utilisée que dans le salon Commandes.**")

    if not has_rank(ctx, "lb"):
        return await ctx.send("**Tu n'as pas la permission d'exécuter cette commande.**")

    # Récupération Top MVPs
    cur.execute("SELECT user_id, mvps FROM stats ORDER BY mvps DESC LIMIT 10")
    mvp_results = cur.fetchall()

    # Calcul des Winrates
    cur.execute("SELECT user_id, victories, losses FROM stats")
    players = cur.fetchall()

    winrate_list = []
    for user_id, wins, losses in players:
        total = wins + losses
        if total > 0:
            winrate = round((wins / total) * 100, 2)
            winrate_list.append((user_id, winrate, wins, losses))

    top_winrates = sorted(winrate_list, key=lambda x: x[1], reverse=True)[:10]

    # Construction Embed
    embed = discord.Embed(title="**🏆 Classement du Serveur**", color=discord.Color.gold())
    embed.add_field(name="**🥇 Top 10 MVPs**", value="\n".join(
        [f"{i+1}. <@{user_id}> — {mvp} MVPs" for i, (user_id, mvp) in enumerate(mvp_results)]
    ) or "Aucun MVP enregistré", inline=True)

    embed.add_field(name="**📈 Top 10 Winrates**", value="\n".join(
        [f"{i+1}. <@{user_id}> — {rate}% ({wins}W/{losses}L)" for i, (user_id, rate, wins, losses) in enumerate(top_winrates)]
    ) or "Aucune partie jouée", inline=True)

    await ctx.send(embed=embed)


@bot.command()
async def stats(ctx, member: discord.Member = None):
    allowed_channels = [1131419095796035624, 1386040436312903691, 1135965417941241866]  # Remplace par les vrais IDs des salons
    if ctx.channel.id not in allowed_channels:
        return await ctx.send("**❌ Cette commande ne peut être utilisée que dans le salon Commandes.**")

    member = member or ctx.author
    cur.execute("SELECT games_played, mvps, victories, losses FROM stats WHERE user_id = ?", (member.id,))
    data = cur.fetchone()

    if data:
        total_matches = data[2] + data[3]
        winrate = round((data[2] / total_matches) * 100, 2) if total_matches > 0 else 0

        embed = discord.Embed(
            title=f" **{member.display_name}**",
            color=discord.Color.teal()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Parties jouées", value=str(data[0]), inline=True)
        embed.add_field(name="MVPs", value=str(data[1]), inline=True)
        embed.add_field(name="Victoires", value=str(data[2]), inline=True)
        embed.add_field(name="Défaites", value=str(data[3]), inline=True)
        embed.add_field(name="Winrate", value=f"{winrate}%", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"**Aucune donnée trouvée pour {member.mention}.**")


@bot.command()
async def clearstats(ctx, member: discord.Member):
    
    if not has_rank(ctx, "mvp"):
        return await ctx.send("**Tu n'as pas la permission d'exécuter cette commande.**")
    cur.execute("SELECT * FROM stats WHERE user_id = ?", (member.id,))
    if not cur.fetchone():
        return await ctx.send(f"Aucune donnée à réinitialiser pour {member.mention}.")
    cur.execute("""
        UPDATE stats
        SET games_played = 0,
            mvps = 0,
            victories = 0,
            losses = 0
        WHERE user_id = ?
    """, (member.id,))
    conn.commit()
    embed = discord.Embed(
        title="♻️ Statistiques réinitialisées",
        description=f"Les stats de {member.mention} ont été remises à zéro.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)


map_images = {
    "Ascent": "https://static.wikia.nocookie.net/valorant/images/1/1c/Ascent_chargement.png/revision/latest?cb=20240613123615&path-prefix=fr",
    "Bind": "https://gdm-assets.b-cdn.net/images/ncavvykf/siege/7ec3655b17ee937bf56e8a4fcf9dcf3be2801b4c-1280x720.jpg?auto=format&h=405&w=720",
    "Haven": "https://files.bo3.gg/uploads/image/64582/image/webp-aaaa475629b10d73cbe5de879e7033c2.webp",
    "Lotus": "https://cdn.oneesports.gg/cdn-data/2023/01/Valorant_Lotus_Episode6ActI_Map-1024x576.jpg",
    "Sunset": "https://liquipedia.net/commons/images/f/f5/Sunset_Map.png",
    "Icebox": "https://cdn.sanity.io/images/ncavvykf/siege/a651bf9782fd09256b9ceb0adb2c341ceb8e73e1-1280x720.jpg?rect=1,0,1279,720&w=810&h=456&auto=format",
    "Corrode": "https://happygamer.com/wp-content/uploads/2025/06/valorant-s-new-map-corrode-sparks-heated-debate-among-players-768x432.webp"
}

class MapRouletteView(discord.ui.View):
    def __init__(self, ctx, map_pool):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.map_pool = map_pool
        self.votes_cross = set()
        self.chosen_map = random.choice(self.map_pool)
        self.message = None

    async def send(self):
        embed = discord.Embed(
            title=f"Carte sélectionnée : **{self.chosen_map}**",
            color=discord.Color.blurple()
        )
        embed.set_image(url=map_images.get(self.chosen_map, ""))
        self.message = await self.ctx.send(embed=embed, view=self)

    async def reroll(self, interaction: discord.Interaction):
        self.votes_cross.clear()
        self.chosen_map = random.choice(self.map_pool)
        embed = discord.Embed(
            title="♻ Nouvelle carte tirée !",
            description=f"Nouvelle carte : **{self.chosen_map}**",
            color=discord.Color.orange()
        )
        embed.set_image(url=map_images.get(self.chosen_map, ""))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="✅", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes_cross.add(interaction.user.id)
        if len(self.votes_cross) >= 5:
            await self.reroll(interaction)
        else:
            await interaction.response.defer()

@bot.command()
async def roulette(ctx):
    if not has_rank(ctx, "roulette"):
        return await ctx.send("**Tu n’as pas la permission d'exécuter cette commande.**")
    map_pool = list(map_images.keys())
    view = MapRouletteView(ctx, map_pool)
    await view.send()

keep_alive()
bot.run(token)

