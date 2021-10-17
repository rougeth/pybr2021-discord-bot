
import asyncio
import json
import os
import shutil
from base64 import b64encode
from collections import defaultdict
from datetime import datetime
from functools import wraps

import discord
import httpx
from decouple import config
from discord import message
from discord.enums import ChannelType
from discord.ext import commands, tasks
from discord_setup import get_or_create_channel
from invite_tracker import InviteTracker
from loguru import logger
from pytz import timezone

DISCORD_GUILD_ID = config("DISCORD_GUILD_ID")
DISCORD_LOG_CHANNEL_ID = config("DISCORD_LOG_CHANNEL_ID")

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

CALENDAR_URL = config("CALENDAR_URL")
CALENDER_TIMEZONE= config('CALENDER_TIMEZONE','UTC')
DISPPLAY_TIMEZONE= config('DISPPLAY_TIMEZONE','UTC')

SPRINTS_CATEGORIES= config('SPRINTS_CATEGORIES','SPRINTS')


MSG="""Tutorial {channel}"""

TUTORIAIS = [
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Desenhando com Python: programação criativa ao alcance de todas as pessoas", "data_hora":"2021-10-17 10:00:00", "vagas": "25", "ministrantes": ["Alexandre Villares"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Análise de Datasets Científicos usando Python", "data_hora":"2021-10-16 10:00:00", "vagas": "100", "ministrantes": ["Bruno dos Santos Almeida"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "1-Djavue - criando uma aplicação web do zero com Django e Vue.js", "data_hora":"2021-10-16 10:00:00", "vagas": "80", "ministrantes": ["Buser (facilitadora: Renzo Nuccitelli)"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "2-Djavue - criando uma aplicação web do zero com Django e Vue.js", "data_hora":"2021-10-16 15:00:00", "vagas": "80", "ministrantes": ["Buser (facilitadora: Renzo Nuccitelli)"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Desenvolvimento orientado a testes com Django", "data_hora":"2021-10-17 15:00:00", "vagas": "20", "ministrantes": ["Carta (facilitador: Gabriel Saldanha)"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Como o dinheiro viaja internacionalmente?", "data_hora":"2021-10-16 10:00:00", "vagas": "80", "ministrantes": ["Ebury (facilitador: Gustavo Di Domenico)"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Acelerando a exploração de dados multidimensionais com Xarray", "data_hora":"2021-10-17 15:00:00", "vagas": "60", "ministrantes": ["Felipe Schuc:00:00"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Python para microcontroladores com MicroPython", "data_hora":"2021-10-17 10:00:00", "vagas": "10", "ministrantes": ["Gabriel Aragão"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Python Geoespacial: automatizando processos de GIS e Sensoriamento Remoto com pacotes abertos em python", "data_hora":"2021-10-17 15:00:00", "vagas": "15", "ministrantes": ["Guilherme Iablonovski"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Viajando por uma API protegida: Implementando uma API com Flask", "data_hora":"2021-10-16 10:00:00", "vagas": "30", "ministrantes": ["Jessica Temporal"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Expectativas nem sempre machucam - Criando expectativas para os seus dados com Great Expectations.", "data_hora":"2021-10-16 15:00:00", "vagas": "20", "ministrantes": ["Joamila Brito"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Analisando 250GB em segundos usando Python e a Base dos Dados", "data_hora":"2021-10-16 10:00:00", "vagas": "10", "ministrantes": ["João Carabetta"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Criando um jogo de plataforma com Pygame do zero", "data_hora":"2021-10-16 10:00:00", "vagas": "12", "ministrantes": ["João JS Bueno"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Python para Dashboards", "data_hora":"2021-10-17 15:00:00", "vagas": "30", "ministrantes": ["Jose Edivaldo da Silva Junior"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Airflow na Pratica", "data_hora":"2021-10-16 10:00:00", "vagas": "40", "ministrantes": ["JusBrasil (facilitador: Tarsis)"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Anatomia de um interpretador Lisp em Python", "data_hora": "2011-10-16 15:00:00", "vagas": "30", "ministrantes": ["Luciano Ramalho"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Construindo API's robustas utilizando Python", "data_hora":"2021-10-16 15:00:00", "vagas": "30", "ministrantes": ["Luizalabs (facilitador: Cassio Botaro)"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "As luas de Jupyter: widgets e outras ferramentas que o orbitam", "data_hora":"2021-10-17 10:00:00", "vagas": "20", "ministrantes": ["Mariana Meireles", "Marcos Pantuza", "Laysa Ucho"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Qual produto é o melhor para mim? Comparando produtos usando a API de MELI", "data_hora":"2021-10-17 10:00:00", "vagas": "15", "ministrantes": ["Mercado Livre (facilitador: Giovanni Almeida)"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Desvendando o código genético com Biopython", "data_hora":"2021-10-17 10:00:00", "vagas": "30", "ministrantes": ["Pâmella Araújo Balcaçar"]},
    {"channel":None,"voice":None,"userinscritos":[],"inscritos":0,"nome": "Manipulando Imagens da webCam com python", "data_hora":"2021-10-17 15:00:00", "vagas": "40", "ministrantes": ["Ramon Domingos Duarte Oliveira"]},
]

class Tutorial(commands.Cog):
    SPRINTS_FILE_PATH = config("SPRINTS_FILE_PATH",'./files')
    TUTORIALS_FILE_PATH = config("TUTORIALS_FILE_PATHS",'./files')

    #TO DO SPRINT AND TUTORIALS ROLES
    #ATTENDEES_ROLE_NAME = "Participantes"

    def __init__(self, bot):
        self._bot = bot
        self._guild = None
        self._tutorial_channel = None
        self._sprint_channel = None
        self.alerts_type = ['tutorial','sprint']
        #self.message = None
        self.check_messages = False
        self.sprints_json = self.load_sprints()
        self._allow_mgs= False
        self._tutorials = []
        self._sprints=[]
        self.index = {}

    async def get_guild(self):
        if not self._guild:
            self._guild = await self._bot.fetch_guild(config("DISCORD_GUILD_ID"))
        return self._guild

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Tutorias module has started")
        await self.get_guild()

    async def load_events(self):
        logger.info("Loading calendar events.")
        url = CALENDAR_URL
        semaphore = asyncio.BoundedSemaphore(10)
        async with httpx.AsyncClient() as client:
            response = await self.http_get_json(semaphore, client, url)

        logger.info("Parsing events")
        self._events = await self.parse_events(response)
        self.index = self.create_index(self._events)
        logger.info("Calendar finished load")

    async def parse_events(self,response):
        events=[]
        for item in response.get("items"):
            if item.get('extendedProperties').get('private').get('type') in self.alerts_type:
                events.append(
                    {
                        'start': datetime.strptime(item.get('start').get('dateTime'),'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone(CALENDER_TIMEZONE)),
                        'timezone':item.get('start').get('timeZone'),
                        'location':item.get('location'),
                        'title':item.get('extendedProperties').get('private').get('title'),
                        'author':item.get('extendedProperties').get('private').get('author'),
                        'discord_channel':item.get('extendedProperties').get('private').get('discord_channel'),
                        'type':item.get('extendedProperties').get('private').get('type'),
                        'youtube_channel':item.get('extendedProperties').get('private').get('youtube_channel'),
                        'seats_limits':item.get('extendedProperties').get('private').get('seats_limits'),
                    }
            )
        return events

    def create_index(self,events):
        index = defaultdict(list)
        for event in events:
            index[event["start"].date()].append(event)

    def load_sprints(self):
        if self.SPRINTS_FILE_PATH:
            return json.loads(open(self.SPRINTS_FILE_PATH, "r").read()) 
        return None

    async def _save_files(self):
        os.makedirs("./json",exist_ok=True)
        with open(f"./json/{self._tutorials['file_name']}", 'w') as f:
            json.dump(object, f)
        return object

    async def _save_files(self):
        if os.path.isfile(f"./json/{self._tutorials['file_name']}"):
            with open(f"./json/{self._tutorials['file_name']}", 'rb') as f:
                return json.load(f)
        else:
            self._tutorials['userinscritos']=[]
            self._tutorials['inscritos']=0
            return await self.save_list()

    async def _remove_files(self):
        shutil.rmtree("./json/")

    @commands.command(name="reset-tutorial",brief="reset all tutorials ")
    async def reset(self, ctx):
        logger.info("Reseting Tutoriais")
        self._allow_mgs=False
        await self._remove_files()
        await self.on_ready(True)
        await logchannel(self._bot,"Reseting Tutoriais")
    
    @commands.command(name="open-tutorial",brief="open dsds on tutorials")
    async def open_tutorial(self, ctx):
        self._allow_mgs=True
        #TO DO To function
        for tutorial in self._tutoriais:
            await self.lista(tutorial)
        await self.show_tutoriais()
        logger.info("Inscrições abertas")
        await logchannel(self._bot,"Inscrições abertas")

    @commands.command(name="close-tutorial",brief="warnig on use that!!")
    async def close(self, ctx):
        self._allow_mgs=False
        for tutorial in self._tutoriais:
            await self.lista(tutorial)
        await self.show_tutoriais()
        logger.info("Inscrições fechadas")
        await logchannel(self._bot,"Inscrições fechadas")

    @commands.command(name="create-sprints")
    async def create_sprints(self, ctx):
        
        overwrites = {self._guild.default_role: discord.PermissionOverwrite(read_messages=False)}
        
        organizacao_cat = await get_or_create_channel(
            SPRINTS_CATEGORIES,
            self._guild,
            type=discord.ChannelType.category,
            overwrites=overwrites,
            position=0,
        )

        self._sprint_channel = await get_or_create_channel(f"sprints-info", self._guild, position=0, category=organizacao_cat)
        
        full_msg = []
        for index,sprint in enumerate(self.sprints_json):
            channel = await get_or_create_channel(f"sprint-{index}-chat", self._guild, position=99, category=organizacao_cat)
            voice=  await get_or_create_channel(f"sprint-{index}-voice", self._guild, position=99, category=organizacao_cat,type=discord.ChannelType.voice)
            
            await self.clear(channel.id)
            await channel.send(f"\nCanal da sprint {sprint['titulo']}")
            await channel.send(f"\nDias e Horas {sprint['horarios']}")
            await channel.send(f"\nMinistrante {sprint['nome']}")
            await channel.send(f"\nRepositório {sprint['repo']}")
            await channel.send(f"\nPúblico {sprint['publico']}")
            await channel.send(f"\nConhecimento {sprint['conhecimento']}")
            await channel.send(f"\nDescrição {sprint['descrição']}")
            await channel.send(f"\nCanal de voz {voice.name}")

            full_msg.append(f"\n<#{channel.id}> Canal da sprint {sprint['titulo']}")
            logger.info(index)


        await self.clear(self.channel.id)
        logger.info(full_msg)
        for msg in full_msg:
            await self.channel.send(msg)

    @commands.command(name="tutorial-users")
    async def tutorial_users(self, ctx):
        logger.info("full_msg")

        self._tutoriais = TUTORIAIS
        out=[]
        for index,tutorial in enumerate(self._tutoriais):
            tutorial["file_name"]=f"tutorial_{index}_file.json"
            tutorial_ =await self.load_list(tutorial)
            tutorial_["data_hora"] =  tutorial["data_hora"]
            tutorial = tutorial_    
            channel = self.bot.get_channel(tutorial["channel"])
            canal =  f"<#{channel.id}>" if channel else ''
            data = f"{tutorial['nome']} - {canal} - {datetime.strptime(tutorial['data_hora'],'%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')}"
            insc=[]
            for inscritos in tutorial.get("userinscritos"):
                inscrito = discord.utils.get(self._bot.get_all_members(), id=inscritos)
                if inscrito:
                    insc.append(f"{inscrito.name} - <@{inscrito.id}>")
                    #await logchannel(self.bot,f"======   {inscrito.name} - <@{inscrito.id}>")
            out.append(dict(data=data,inscritos=insc))
        
        logger.info(out)
        os.makedirs("./json",exist_ok=True)
        with open(f"./json/inscritos.json", 'w') as f:
            json.dump(out, f)


    @commands.command(name="create-tutoriais",brief="create tutorias structures")
    async def create_tutoriai(self,force_clean=False):
        logger.info("Creating tutorials structures")
        
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
            pass
            # for guilds in self.bot.guilds:
            #     for cat in guilds.categories:
            #         if cat.name == "TUTORIAIS-TESTES":
            #             for c  in cat.channels:
            #                 logger.info(f"Apagando {c.name}")
            #                 await c.delete()

        self.channel = await get_or_create_channel(f"tutorial-info", self._guild, position=0, category=organizacao_cat)
        self.voice=  await get_or_create_channel(f"tutorial-ajuda", self._guild, position=0, category=organizacao_cat,type=discord.ChannelType.voice)

        self._tutoriais = TUTORIAIS

        for index,tutorial in enumerate(self._tutoriais):
            tutorial["file_name"]=f"tutorial_{index}_file.json"
            tutorial_ =await self.load_list(tutorial)
            tutorial_["data_hora"] =  tutorial["data_hora"]
            tutorial = tutorial_
            await logchannel(self.bot, f"Carregando tutorial-{index}:{tutorial.get('nome')[:20]}")
            channel = await get_or_create_channel(f"tutorial-{index}-chat", self._guild, position=99, category=organizacao_cat)
            voice=  await get_or_create_channel(f"tutorial-{index}-voice", self._guild, position=99, category=organizacao_cat,type=discord.ChannelType.voice)
            tutorial["channel"] = int(channel.id)
            tutorial["voice"] = int(voice.id)
            #await self.clear(tutorial["channel"])
            logger.info(tutorial)
            msg= await self.lista(tutorial,True)
            tutorial["inscritos_msg"] = int(msg.id)

            self._tutoriais[index] = tutorial

        await self.show_tutoriais()
        logger.info("Canais criados com sucesso")
        self.check_messages=True
        await logchannel(self.bot,"Canais criados com sucesso")

    async def show_tutoriais(self):

        await self.clear(self.channel.id)
        msg=""
        msg+="\n:exclamation::exclamation: AQUI ESTÃO OS TUTORIAIS DA PYTHON BRASIL 2021 :exclamation::exclamation:"
        msg+="\n:exclamation::exclamation: MAIS INFORMAÇÕES CLICANDO NO LINK DE CADA CANAL :exclamation::exclamation:"
        msg+="\n:exclamation::exclamation: APENAS 1 INSCRIÇÃO POR PESSOA NO MESMO HORÁRIO (SERÃO VALIDADAS PELO ORG!!) :exclamation::exclamation:"
        msg+="\n:red_circle: INSCRIÇÕES FECHADAS :red_circle:\n\n\n" if not self._allow_mgs else "\n:green_circle: INSCRIÇÕES ABERTAS :green_circle:\n\n\n"
        msg+=""
        await self.channel.send(msg)

        tutorias_msg=":diamond_shape_with_a_dot_inside: {nome}\n     :writing_hand_tone4: <#{canal}> :calendar: {data}"
        for tutorial  in self._tutoriais:
            canal = self.bot.get_channel(tutorial["channel"])
            nome = tutorial["nome"]
            i= tutorial['inscritos']
            total = tutorial['vagas']
            data = datetime.strptime(tutorial['data_hora'],'%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y-%H:%M')
            await self.channel.send(tutorias_msg.format(nome=nome,data=data,canal=canal.id,i=i,total=total))


    async def clear(self,channel):
        channel_msg = self.bot.get_channel(channel)
        messages = await channel_msg.history().flatten()
        for msg in messages:
            await msg.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        logger.info("Validando mensagem")
        if message.author.bot or message.channel.type == discord.ChannelType.private:
            return
        if not self.check_messages:
            return
        for index,tutorial in enumerate(self._tutoriais):
            channel = self.bot.get_channel(tutorial["channel"])
            # if channel is None:
            #     continue
            if message.channel.id == channel.id:
                logger.info(f"Mensagem dentro de canal {message.channel.name}")
                if message.content.lower() == "entrar":
                    if message.author.id in tutorial["userinscritos"]:
                        logger.info(f"Usuário já cadastrado {message.author.name}")
                        #await message.delete()
                        await self.lista(tutorial)
                        return  

                    if not self._allow_mgs:
                        #await message.delete()
                        await message.channel.send(":red_circle: INSCRIÇÕES FECHADAS :red_circle:")
                        return

                    logger.info(f"Cadastrando usuário {message.author.name}")
                    await logchannel(self.bot,f"Cadastrando usuário {message.author.name} em {tutorial['nome']}")
                    tutorial['inscritos']+=1
                    tutorial["userinscritos"].append(message.author.id)
                    logger.info(tutorial)
                    await self.save_list(tutorial)
                    self._tutoriais[index] = tutorial
                    await self.lista(tutorial)

                if message.content.lower() == "sair":
                
                    if message.author.id in tutorial["userinscritos"]:
                        logger.info(f"Removendo usuário {message.author.name}")
                        await logchannel(self.bot,f"Removendo usuário {message.author.name} em {tutorial['nome']}")
                        tutorial['inscritos']-=1
                        tutorial["userinscritos"].remove(message.author.id)
                        await self.save_list(tutorial)
                        self._tutoriais[index] = tutorial
                        await self.lista(tutorial)

                #await message.delete()
                #await self.lista(tutorial)
                #await self.show_tutoriais()

    async def lista(self,tutorial,init=False):
        channel = self.bot.get_channel(tutorial["channel"])

        msg=""
        msg+=":red_circle: INSCRIÇÕES FECHADAS :red_circle:" if not self._allow_mgs else ":green_circle: INSCRIÇÕES ABERTAS :green_circle:\n:keyboard: DIGITE a palavra 'entrar' para sua inscrição ou 'sair' para remover sua inscrição :keyboard:"
        msg+= f"\n:diamond_shape_with_a_dot_inside: {MSG.format(channel=tutorial['nome'])}"
        msg+= f"\n:calendar: Dia e Hora: {datetime.strptime(tutorial['data_hora'],'%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')}"  
        for ministrante in tutorial['ministrantes']:
            msg+=f"\n:teacher_tone5: Ministrante: {ministrante}"

        msg+= f"\n:student_tone5: Lista de Inscritos {tutorial['inscritos']}/{tutorial['vagas']}"
        for item in tutorial['userinscritos']:
            msg+=f"\n<@{item}>"
        
        if tutorial['inscritos'] == tutorial['vagas']:
            msg+="\n:octagonal_sign:  TUTORIAL **LOTADO** :octagonal_sign:"
        else:
            msg+="\n:grey_exclamation: COM VAGAS :grey_exclamation: "

        # if not init: 
        #     message= await channel.fetch_message(tutorial["inscritos_msg"])
        #     await message.edit(content=msg) 
        #     return
        return await channel.send(msg)
