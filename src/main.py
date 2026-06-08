import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datas.databaseHandler import getRevivalDates, getUserApplications, changeStatus

from config import config

import datetime


idSalon = config.DISCORD_CHANNEL_ID
idServeur = config.DISCORD_GUILD_ID

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