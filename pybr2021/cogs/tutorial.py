
import json
import os
import shutil
from base64 import b64encode
from datetime import datetime
from functools import wraps

import discord
from decouple import config
from discord import message
from discord.enums import ChannelType
from discord.ext import commands, tasks
from discord_setup import get_or_create_channel
from invite_tracker import InviteTracker
from loguru import logger

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
    AUTH_CHANNEL_ID = config("DISCORD_AUTH_CHANNEL_ID", cast=int)
    AUTH_START_EMOJI = "👍"
    ATTENDEES_ROLE_NAME = "Participantes"

    def __init__(self, bot):
        self.bot = bot
        self._guild = None
        self.channel = None
        self.message = None
        self.voice = None
        self._allowtouser= False
        self._tutoriais = []

    async def save_list(self,tutorial):
        os.makedirs("./json",exist_ok=True)
        with open(f"./json/{tutorial['file_name']}", 'w') as f:
            json.dump(tutorial, f)
        return tutorial
        

    async def load_list(self,tutorial):
        if os.path.isfile(f"./json/{tutorial['file_name']}"):
            with open(f"./json/{tutorial['file_name']}", 'rb') as f:
                return json.load(f)
        else:
            tutorial['userinscritos']=[]
            tutorial['inscritos']=0
            return await self.save_list(tutorial)

    async def remove_files(self):
        shutil.rmtree("./json/")

    async def get_guild(self):
        if not self._guild:
            self._guild = await self.bot.fetch_guild(config("DISCORD_GUILD_ID"))
        return self._guild

    @commands.command(name="reset",brief="warnig on use that!!")
    async def reset(self, ctx):
        logger.info("Resetando Tutoriais")
        self._allowtouser=False
        await self.remove_files()
        await self.on_ready(True)
        await logchannel(self.bot,"Resetanto Tutoriais")
    
    @commands.command(name="open",brief="warnig on use that!!")
    async def open(self, ctx):
        self._allowtouser=True
        for tutorial in self._tutoriais:
            await self.lista(tutorial)
        await self.show_tutoriais()
        logger.info("Inscrições abertas")
        await logchannel(self.bot,"Inscrições abertas")

    @commands.command(name="close",brief="warnig on use that!!")
    async def close(self, ctx):
        self._allowtouser=False
        for tutorial in self._tutoriais:
            await self.lista(tutorial)
        await self.show_tutoriais()
        logger.info("Inscrições fechadas")
        await logchannel(self.bot,"Inscrições fechadas")

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
                            logger.info(f"Apagando {c.name}")
                            await c.delete()

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
            await self.clear(tutorial["channel"])
            logger.info(tutorial)
            msg= await self.lista(tutorial,True)
            tutorial["inscritos_msg"] = int(msg.id)

            self._tutoriais[index] = tutorial

        await self.show_tutoriais()
        logger.info("Canais criados com sucesso")
        await logchannel(self.bot,"Canais criados com sucesso")

    async def show_tutoriais(self):

        await self.clear(self.channel.id)
        msg=""
        msg+="\n:exclamation::exclamation: AQUI ESTÃO OS TUTORIAIS DA PYTHON BRASIL 2021 :exclamation::exclamation:"
        msg+="\n:exclamation::exclamation: MAIS INFORMAÇÕES CLICANDO NO LINK DE CADA CANAL :exclamation::exclamation:"
        msg+="\n:exclamation::exclamation: APENAS 1 INSCRIÇÃO POR PESSOA NO MESMO HORÁRIO (SERÃO VALIDADAS PELO ORG!!) :exclamation::exclamation:"
        msg+="\n:red_circle: INSCRIÇÕES FECHADAS :red_circle:\n\n\n" if not self._allowtouser else "\n:green_circle: INSCRIÇÕES ABERTAS :green_circle:\n\n\n"
        msg+=""
        await self.channel.send(msg)

        tutorias_msg=":diamond_shape_with_a_dot_inside: {nome}\n     :writing_hand_tone4: <#{canal}> :calendar: {data} :school: {i}/{total}"
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

        for index,tutorial in enumerate(self._tutoriais):
            channel = self.bot.get_channel(tutorial["channel"])
            if message.channel.id == channel.id and channel.id:
                if not self._allowtouser:
                    await message.delete()
                    return
                logger.info(f"Mensagem dentro de canal {message.channel.name}")
                if message.content.lower() == "entrar":
                    if message.author.id in tutorial["userinscritos"]:
                        logger.info(f"Usuário já cadastrado {message.author.name}")
                        await message.delete()
                        await self.lista(tutorial)
                        return  

                    logger.info(f"Cadastrando usuário {message.author.name}")
                    await logchannel(self.bot,f"Cadastrando usuário {message.author.name} em {tutorial['nome']}")
                    tutorial['inscritos']+=1
                    tutorial["userinscritos"].append(message.author.id)
                    logger.info(tutorial)
                    await self.save_list(tutorial)
                    self._tutoriais[index] = tutorial

                if message.content.lower() == "sair":
                
                    if message.author.id in tutorial["userinscritos"]:
                        logger.info(f"Removendo usuário {message.author.name}")
                        await logchannel(self.bot,f"Removendo usuário {message.author.name} em {tutorial['nome']}")
                        tutorial['inscritos']-=1
                        tutorial["userinscritos"].remove(message.author.id)
                        await self.save_list(tutorial)
                        self._tutoriais[index] = tutorial

                await message.delete()
                await self.lista(tutorial)
                await self.show_tutoriais()

    async def lista(self,tutorial,init=False):
        channel = self.bot.get_channel(tutorial["channel"])

        msg=""
        msg+=":red_circle: INSCRIÇÕES FECHADAS :red_circle:" if not self._allowtouser else ":green_circle: INSCRIÇÕES ABERTAS :green_circle:\n:keyboard DIGITE a palavra 'entrar' para sua inscrição ou 'sair' para remover sua inscrição :keyboard:"
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

        if not init: 
            message= await channel.fetch_message(tutorial["inscritos_msg"])
            await message.edit(content=msg) 
            return
        return await channel.send(msg)
