import sqlite3
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# IDs des salons et rôles
SALON_ID = 1131342196948357175
ROLE_JOUEUR_ID = 1131231592015216723
ROLE_MONSTRE_ID = 1385977719539499079

scheduler = AsyncIOScheduler()

def get_stats():
    conn = sqlite3.connect("stats.db")
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, wins, loses, mvp_count FROM stats")
    data = cursor.fetchall()
    conn.close()

    return [
        {
            "user_id": row[0],
            "wins": row[1],
            "loses": row[2],
            "mvp_count": row[3],
            "winrate": row[1] / (row[1] + row[2]) if (row[1] + row[2]) > 0 else 0
        }
        for row in data
    ]

@scheduler.scheduled_job("cron", day_of_week="sun", hour=12)
async def envoyer_classement():
    stats = get_stats()
    if not stats:
        return

    # Calcul MVP
    top_mvp = max(stats, key=lambda x: x["mvp_count"])

    # Calcul WinRate
    top_winrate = max(stats, key=lambda x: x["winrate"])

    # Récupération du serveur
    guild = discord.utils.get(discord.Client().guilds)  # À adapter selon ton bot

    role_monstre = discord.utils.get(guild.roles, id=ROLE_MONSTRE_ID)
    channel = guild.get_channel(SALON_ID)

    # Retirer le rôle "monstre" à tout le monde
    for member in guild.members:
        if role_monstre in member.roles:
            await member.remove_roles(role_monstre)

    # Ajouter le rôle "monstre" aux deux gagnants
    for user_id in [top_mvp["user_id"], top_winrate["user_id"]]:
        member = guild.get_member(int(user_id))
        if member:
            await member.add_roles(role_monstre)

    # Envoi du message dans le salon
    await channel.send(
        f"<@&{ROLE_JOUEUR_ID}> 🌟 **Classement Final de la Semaine**\n\n"
        f"🥇 **MVP** : <@{top_mvp['user_id']}> ({top_mvp['mvp_count']} mentions !)\n"
        f"🎯 **WinRate** : <@{top_winrate['user_id']}> ({top_winrate['winrate']:.2%})\n\n"
        f"👑 Le rôle **MONSTRE** a été attribué aux deux champions 🔥\n"
        f"🔁 Rendez-vous dimanche prochain à 12h !"
    )

    # Reset des stats pour la nouvelle semaine
    conn = sqlite3.connect("stats.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stats")
    conn.commit()
    conn.close()
