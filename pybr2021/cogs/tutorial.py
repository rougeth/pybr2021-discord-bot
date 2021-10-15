import asyncio
import json
import os
import pickle
import time
from base64 import b64encode
from datetime import datetime, timedelta
from functools import wraps
from random import shuffle

import discord
import httpx
from bot_msg import (auth_already_confirmed, auth_email_not_found,
                     auth_instructions, auth_welcome)
from decouple import config
from discord import message
from discord.enums import ChannelType
from discord.ext import commands, tasks
from discord_setup import get_or_create_channel
from invite_tracker import InviteTracker
from loguru import logger

EVENTBRITE_TOKEN = config("EVENTBRITE_TOKEN")
DISCORD_GUILD_ID = config("DISCORD_GUILD_ID")
DISCORD_LOG_CHANNEL_ID = config("DISCORD_LOG_CHANNEL_ID")
DISCORD_GENERAL_INVITE = config("DISCORD_GENERAL_INVITE")

ROLE_INVITE_MAP = [
    ("Ministrantes", ["zuNYMG4jud"]),
    ("Voluntariado", ["j9YH9BqU"]),
    ("Patrocinadoras", ["DfgQhYnVxK"]),
]


def only_log_exceptions(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except:
            logger.exception(f"Error while calling {function!r}")
    return wrapper


async def logchannel(bot, message):
    channel = await bot.fetch_channel(DISCORD_LOG_CHANNEL_ID)
    await channel.send(message)


# async def http_get_json(semaphore, client, url, params, retry=3):
#     async with semaphore:
#         try:
#             response = await client.get(url, params=params)
#         except httpx.ReadTimeout:
#             if retry > 0:
#                 await asyncio.sleep(20)
#                 return await http_get_json(semaphore, client, url, params, retry - 1)
#             logger.exception("Erro")

#         return response.json()


# async def load_attendees(updated_at: datetime = None):
#     default_params = {
#         "token": EVENTBRITE_TOKEN,
#         "status": "attending",
#     }
#     if updated_at:
#         updated_at = updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
#         default_params["changed_since"] = updated_at

#     url = "https://www.eventbriteapi.com/v3/events/169078058023/attendees/"
#     semaphore = asyncio.BoundedSemaphore(10)
#     async with httpx.AsyncClient() as client:
#         response = await http_get_json(semaphore, client, url, default_params)
#         if not updated_at:
#             logger.info(
#                 "Attendees load initialized. attendees={attendees}, pages={pages}".format(
#                     attendees=response["pagination"]["object_count"],
#                     pages=response["pagination"]["page_count"],
#                 )
#             )

#         attendees = []
#         attendees.extend(response["attendees"])

#         tasks = []
#         page_count = response["pagination"]["page_count"]
#         for page_number in range(1, page_count + 1):
#             # I'm not proud of this, but Eventbrite is the one to blame
#             next_page = json.dumps({"page": page_number})

#             params = default_params.copy()
#             params["continuation"] = b64encode(next_page.encode("utf-8")).decode(
#                 "utf-8"
#             )
#             tasks.append(http_get_json(semaphore, client, url, params))

#         if tasks:
#             results = await asyncio.gather(*tasks)
#             attendees.extend(
#                 [attendees for result in results for attendees in result["attendees"]]
#             )

#     return attendees


# def create_index(attendees):
#     index = {}
#     for attendee in attendees:
#         profile = attendee["profile"]
#         index[attendee["order_id"]] = profile
#         index[profile["email"].lower()] = profile
#     return index


MSG="""Tutorial {channel}"""
TUTORIAIS = [
    {"nome": "Desenhando com Python: programação criativa ao alcance de todas as pessoas", "data_hora": "dia 17/10/2021 às 10h", "vagas": "25", "ministrantes": ["Alexandre Villares"]},
    {"nome": "Análise de Datasets Científicos usando Python", "data_hora": "dia 16/10/2021 às 10h", "vagas": "100", "ministrantes": ["Bruno dos Santos Almeida"]},
    {"nome": "1-Djavue - criando uma aplicação web do zero com Django e Vue.js", "data_hora": "dia 16/10/2021 às 10h", "vagas": "80", "ministrantes": ["Buser (facilitadora: Renzo Nuccitelli)"]},
    {"nome": "2-Djavue - criando uma aplicação web do zero com Django e Vue.js", "data_hora": "dia 16/10/2021 às 15h", "vagas": "80", "ministrantes": ["Buser (facilitadora: Renzo Nuccitelli)"]},
    {"nome": "Desenvolvimento orientado a testes com Django", "data_hora": "dia 17/10/2021 às 15h", "vagas": "20", "ministrantes": ["Carta (facilitador: Gabriel Saldanha)"]},
    {"nome": "Como o dinheiro viaja internacionalmente?", "data_hora": "dia 16/10/2021 às 10h", "vagas": "80", "ministrantes": ["Ebury (facilitador: Gustavo Di Domenico)"]},
    {"nome": "Acelerando a exploração de dados multidimensionais com Xarray", "data_hora": "dia 17/10/2021 às 15h", "vagas": "60", "ministrantes": ["Felipe Schuch"]},
    {"nome": "Python para microcontroladores com MicroPython", "data_hora": "dia 17/10/2021às 10h", "vagas": "10", "ministrantes": ["Gabriel Aragão"]},
    {"nome": "Python Geoespacial: automatizando processos de GIS e Sensoriamento Remoto com pacotes abertos em python", "data_hora": "dia 17/10/2021 às 15h", "vagas": "15", "ministrantes": ["Guilherme Iablonovski"]},
    {"nome": "Viajando por uma API protegida: Implementando uma API com Flask", "data_hora": "dia 16/10/2021 às 10h", "vagas": "30", "ministrantes": ["Jessica Temporal"]},
    {"nome": "Expectativas nem sempre machucam - Criando expectativas para os seus dados com Great Expectations.", "data_hora": "dia 16/10/2021 às 15h", "vagas": "20", "ministrantes": ["Joamila Brito"]},
    {"nome": "Analisando 250GB em segundos usando Python e a Base dos Dados", "data_hora": "dia 16/10/2021 às 10h", "vagas": "10", "ministrantes": ["João Carabetta"]},
    {"nome": "Criando um jogo de plataforma com Pygame do zero", "data_hora": "dia 16/10/2021 às 10h", "vagas": "12", "ministrantes": ["João JS Bueno"]},
    {"nome": "Python para Dashboards", "data_hora": "dia 17/10/2021 às 15h", "vagas": "30", "ministrantes": ["Jose Edivaldo da Silva Junior"]},
    {"nome": "Airflow na Pratica", "data_hora": "dia 16 às 10h", "vagas": "40", "ministrantes": ["JusBrasil (facilitador: Tarsis)"]},
    {"nome": "Anatomia de um interpretador Lisp em Python", "data_hora": "dia/10/2021 16 às 15h", "vagas": "30", "ministrantes": ["Luciano Ramalho"]},
    {"nome": "Construindo API's robustas utilizando Python", "data_hora": "dia 16/10/2021 às 15h", "vagas": "30", "ministrantes": ["Luizalabs (facilitador: Cassio Botaro)"]},
    {"nome": "As luas de Jupyter: widgets e outras ferramentas que o orbitam", "data_hora": "dia 17/10/2021 às 10h", "vagas": "20", "ministrantes": ["Mariana Meireles", "Marcos Pantuza", "Laysa Ucho"]},
    {"nome": "Qual produto é o melhor para mim? Comparando produtos usando a API de MELI", "data_hora": "dia 17/10/2021 às 10h", "vagas": "15", "ministrantes": ["Mercado Livre (facilitador: Giovanni Almeida)"]},
    {"nome": "Desvendando o código genético com Biopython", "data_hora": "dia 17/10/2021 às 10h", "vagas": "30", "ministrantes": ["Pâmella Araújo Balcaçar"]},
    {"nome": "Manipulando Imagens da webCam com python", "data_hora": "dia 17/10/2021 às 15h", "vagas": "40", "ministrantes": ["Ramon Domingos Duarte Oliveira"]},
]

class Tutorial(commands.Cog):
    AUTH_CHANNEL_ID = config("DISCORD_AUTH_CHANNEL_ID", cast=int)
    AUTH_START_EMOJI = "👍"
    ATTENDEES_ROLE_NAME = "Participantes"

    def __init__(self, bot):
        self.bot = bot
        self._guild = None
        self._allowtouser= False

    async def save_list(self,tutorial):
        os.makedirs("./pickles",exist_ok=True)
        with open(f"./pickles/{tutorial['file_name']}", 'wb') as f:
            pickle.dump(tutorial, f)

    async def load_list(self,tutorial):
        if os.path.isfile(f"./pickles/{tutorial['file_name']}"):
            with open(f"./pickles/{tutorial['file_name']}", 'rb') as f:
                tutorial=pickle.load(f)
        else:
            tutorial['userinscritos']=[]
            tutorial['inscritos']=0
            await self.save_list(tutorial)
        

    #@commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        """Quando o usuário reagir será inscrito
        """
        if (
            user.bot
            or reaction.message.channel.id != self.AUTH_CHANNEL_ID
        ):
            return

        if reaction.emoji != self.AUTH_START_EMOJI:
            await reaction.clear()
            return

        if len(user.roles) == 1:
            await user.send(auth_instructions.format(name=user.name))

    async def get_attendee_role(self, guild: discord.Guild) -> discord.Role:
        """Retorna cargo de participante"""
        if not self._atteendee_role:
            guild = await self.get_guild()
            roles = await guild.fetch_roles()
            self._atteendee_role = discord.utils.get(roles, name=self.ATTENDEES_ROLE_NAME)
        return self._atteendee_role

    async def get_guild(self):
        if not self._guild:
            self._guild = await self.bot.fetch_guild(config("DISCORD_GUILD_ID"))
        return self._guild

    @commands.command(name="tutoriais-relauch",brief="")
    async def on_ready(self, ctx):
        self._allowtouser=False
        await self.on_ready(True)

    @commands.Cog.listener()
    async def on_ready(self,force_clean=False):
        logger.info("Criando Canais")

        self._guild = await self.bot.fetch_guild(config("DISCORD_GUILD_ID"))

        overwrites = {
        self._guild.default_role: discord.PermissionOverwrite(read_messages=False)}
        organizacao_cat = await get_or_create_channel(
            "TUTORIAIS",
            self._guild,
            type=discord.ChannelType.category,
            overwrites=overwrites,
            position=0,
        )

        if force_clean:
            for guilds in self.bot.guilds:
                for cat in guilds.categories:
                    if cat.name == "TUTORIAIS":
                        for c  in cat.channels:
                            await c.delete()

        for index,tutorial in enumerate(TUTORIAIS):
            tutorial["file_name"]=f"tutorial_{index}_file.pkl"
            await self.load_list(tutorial)
            await logchannel(self.bot, f"Carregando tutorial-{index}:{tutorial.get('nome')[:20]}")
            tutorial["channel"] = await get_or_create_channel(f"tutorial-{index}-chat", self._guild, position=99, category=organizacao_cat)
            tutorial["voice"] = await get_or_create_channel(f"tutorial-{index}-voice", self._guild, position=99, category=organizacao_cat,type=discord.ChannelType.voice)
            await self.clear(tutorial["channel"])
            tutorial["inscritos_msg"] = await self.lista(tutorial,True)
        
        self._allowtouser=True
        logger.info("Canais criados com sucesso")
        

    async def clear(self,channel):
        messages = await channel.history().flatten()
        for msg in messages:
            await msg.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        
        if message.author.bot or message.channel.type == discord.ChannelType.private or not self._allowtouser:
            return

        if not self._allowtouser:
            await message.delete()
            return

        for index,tutorial in enumerate(TUTORIAIS):
            if message.channel.id == tutorial["channel"]:
                if message.content.lower() == "entrar":
                    if message.author.id in tutorial["userinscritos"]:
                        await message.delete()
                        await self.lista(tutorial)
                        return  

                    tutorial['inscritos']+=1
                    tutorial["userinscritos"].append(message.author.id)
                    await self.save_list(tutorial)

                if message.content.lower() == "sair":
                
                    if message.author.id in tutorial["userinscritos"]:
                        tutorial['inscritos']-=1
                        tutorial["userinscritos"].remove(message.author.id)
                        await self.save_list(tutorial)

                await message.delete()
                await self.lista(tutorial)

    async def lista(self,tutorial,init=False):
        msg = f"{MSG.format(channel=tutorial['nome'])}"
        msg+= f"\nDia e Hora: {tutorial['data_hora']}"
        for ministrante in tutorial['ministrantes']:
            msg+=f"\nMinistrante: {ministrante}"

        msg+= f"\nLista de Inscritos {tutorial['inscritos']}/{tutorial['vagas']}"
        for item in tutorial['userinscritos']:
            msg+=f"\n<@{item}>"
        
        if tutorial['inscritos'] == tutorial['vagas']:
            msg+="\nTutorial Lotado !!- Envie << sair >> para remover sua inscrição"
        else:
            msg+="\nVagas Abertas !! - Envie << entrar >> para  sua inscrição ou << sair >> para remover sua inscrição"
        if not init: 
            await tutorial["inscritos_msg"].edit(content=msg) 
            return
        logger.info(msg)
        return await tutorial['channel'].send(msg)

           
            #await message.channel.send(f"comandos aceitos:entrar,sair,lista")

            #await message.channel.send(f"comandos aceitos:entrar,sair,lista")
        # profile = self.search_attendee(message.content)
        # if not profile:
        #     logger.info(
        #         f"User not found on index. user_id={message.author.id}, content={message.content!r}"
        #     )
        #     await message.add_reaction("❌")
        #     await message.author.send(auth_email_not_found.format(query=message.content))
        #     await logchannel(self.bot, (
        #         f"❌\nInscrição não encontrada - {message.author.mention}"
        #         f"\n`{message.content}`"
        #     ))
        #     return

        # role = await self.get_attendee_role(message.guild)

        # await member.add_roles(role)
        # await message.add_reaction("✅")
        # await member.send(DISCORD_GENERAL_INVITE)
        # await logchannel(self.bot, f"✅\n{member.mention}  confirmou sua inscrição")
        # logger.info(f"User authenticated. user={message.author.name}")

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     # Invite Tracker
    #     guild = await self.get_guild()
    #     self.invite_tracker = InviteTracker(self.bot, guild, ROLE_INVITE_MAP)
    #     await self.invite_tracker.sync()
    #     logger.info(f"Invite tracker synced. invites={self.invite_tracker.invites!r}")

    # #@commands.command(name="confirmar",brief="")
    # async def confirm_eventbrite(self, ctx, value):
    #     if len(ctx.author.roles) != 1:
    #         await ctx.message.add_reaction("❌")
    #         return

    #     profile = self.search_attendee(value)
    #     if not profile:
    #         await ctx.message.add_reaction("❌")
    #         return

    #     role = await self.get_attendee_role(ctx.guild)
    #     await ctx.author.add_roles(role)
    #     await ctx.message.delete()
    #     await logchannel(self.bot, f"Usuário confirmou inscrição com commando. {ctx.author.mention}")

    # #@commands.command(name="check-eventbrite",brief="Check if user has eventbrite [email or tickeid]")
    # async def check_eventbrite(self, ctx, value):
    #     profile = self.search_attendee(value)
    #     if profile:
    #         message = f"`{value}` encotrado.\n```{profile!r}```"
    #     else:
    #         message = f"`{value}` não encotrado."

    #     await ctx.channel.send(message)
