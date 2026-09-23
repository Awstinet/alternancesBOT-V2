import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datas.databaseHandler import getRevivalDates, getUserApplications, changeStatus, getAllFilters
from scrapers.linkedin import Linkedin

from utils.getShortkLink import getShortLink

from config import config

import datetime


idSalon = config.DISCORD_CHANNEL_ID
idServeur = config.DISCORD_GUILD_ID

COLOR_JOBS = 0x0A66C2

_scrapingStarted = False


EMBED_MAX_FIELDS = 25


def _buildOffersEmbeds(keyword: str, offers: list) -> list:
    """Construit un embed par tranche de 25 offres (limite Discord), pour que
    tous les résultats soient envoyés quel que soit SCRAPING_MAX_RESULTS."""
    if not offers:
        embed = discord.Embed(title=f'Nouvelles offres LinkedIn — "{keyword}"', color=COLOR_JOBS)
        embed.description = "Aucune offre trouvée pour ce mot-clef."
        return [embed]

    chunks = [offers[i:i + config.SCRAPING_MAX_RESULTS] for i in range(0, len(offers), config.SCRAPING_MAX_RESULTS)]

    embeds = []
    for page, chunk in enumerate(chunks, start=1):
        title = f'Nouvelles offres LinkedIn — "{keyword}"'
        if len(chunks) > 1:
            title += f" ({page}/{len(chunks)})"
        embed = discord.Embed(title=title, color=COLOR_JOBS)

        for offer in chunk:
            lines = [part for part in (offer["company"], offer["location"]) if part]
            if offer["link"]:
                lines.append(f"[Voir l'offre]({getShortLink(offer['link'])})")
            embed.add_field(
                name=(offer["title"] or "(Titre indisponible)")[:256],
                value="\n".join(lines) or "—",
                inline=False,
            )

        embed.set_footer(text=f"{len(offers)} offre(s) — actualisé toutes les {config.SCRAPING_INTERVAL_MINUTES} min")
        embeds.append(embed)

    return embeds


async def _scrapingLoop(bot: commands.Bot):
    await bot.wait_until_ready()
    scraper = Linkedin(
        "https://www.linkedin.com/jobs/search/",
        config.LINKEDIN_LOGIN,
        config.LINKEDIN_PASSWORD,
    )

    try:
        while True:
            if config.TOGGLE_SCRAPING and "linkedin" in config.ENABLED_WEBSITES:
                channel = bot.get_channel(idSalon)
                if channel is None:
                    try:
                        channel = await bot.fetch_channel(idSalon)
                    except discord.DiscordException as e:
                        channel = None
                        print(f"[Scraping LinkedIn] Salon Discord introuvable pour l'id {idSalon} : {e}")

                if channel is not None:
                    keywords = list(getAllFilters().values()) or ["alternance"]

                    for keyword in keywords:
                        try:
                            offers = await asyncio.to_thread(
                                scraper.searchJobs, keyword, config.SCRAPING_MAX_RESULTS
                            )
                        except Exception as e:
                            print(f"[Scraping LinkedIn] Erreur sur '{keyword}' : {e}")
                            await asyncio.to_thread(scraper.close)
                            continue

                        for embed in _buildOffersEmbeds(keyword, offers):
                            await channel.send(embed=embed)

            await asyncio.sleep(config.SCRAPING_INTERVAL_MINUTES * 60)
    finally:
        await asyncio.to_thread(scraper.close)

#Permissions du bot
intents = discord.Intents().all() 
intents.message_content = True
intents.guilds = True
intents.members= True 
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(command_prefix= ".",intents = intents)

#Pour les commandes /
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

#Au moment où le bot se lance
@bot.event
async def on_ready():

    await bot.load_extension("cogs.filters")
    await bot.load_extension("cogs.applications")

    #Syncrhonisation des commandes /
    try:
        guild = discord.Object(id=idServeur)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synchronisation de {len(synced)} commandes")
    except Exception as e:
        print(e)

    global _scrapingStarted
    if not _scrapingStarted:
        _scrapingStarted = True
        bot.loop.create_task(_scrapingLoop(bot))

    while True:
        
        revivalDates = getRevivalDates().values
        for i in revivalDates:
            if i[1] == datetime.date.today().strftime("%d/%m/%Y"):

                applications = getUserApplications(i[0]).values

                for j in applications:
                    if j[5] == datetime.date.today().strftime("%d/%m/%Y")  and j[6] != "revived":
                        changeStatus(j[0], "revived")
                        await bot.get_channel(idSalon).send(f"<@{i[0]}>, vous avez une relance à faire auprès de `{j[2]}` pour le poste de `{j[3]}`")
                

        await asyncio.sleep(3600*24) #Action réitérée tous les jours



@bot.tree.command(guild=discord.Object(id=idServeur), name="test", description="Faudra trouver une description")
async def test(interaction : discord.Interaction):

    await interaction.response.send_message("C'est OK")



bot.run(config.DISCORD_BOT_TOKEN)