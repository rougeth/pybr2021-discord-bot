
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
from discord_setup import get_or_create_channel, get_or_create_role
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
    #SPRINTS_FILE_PATH = config("SPRINTS_FILE_PATH")
    AUTH_CHANNEL_ID = config("DISCORD_AUTH_CHANNEL_ID", cast=int)
    AUTH_START_EMOJI = "👍"
    ATTENDEES_ROLE_NAME = "Participantes"

    def __init__(self, bot):

        #fileObject = open(self.SPRINTS_FILE_PATH, "r")
        #jsonContent = fileObject.read()
        self.bot = bot
        self._guild = None
        self.channel = None
        self.message = None
        self.check_messages = False
        self.voice = None
        # self.sprints_json = json.loads(jsonContent)
        self._allowtouser= False
        self._tutoriais = []
        # logger.info(self.sprints_json)
        # logger.info(type(self.sprints_json))

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


    @commands.command(name="create-sprints")
    async def create_sprints(self, ctx):
        self._guild = await self.bot.fetch_guild(config("DISCORD_GUILD_ID"))

        overwrites = {
        self._guild.default_role: discord.PermissionOverwrite(read_messages=False)}
        organizacao_cat = await get_or_create_channel(
            "SPRINTS",
            self._guild,
            type=discord.ChannelType.category,
            overwrites=overwrites,
            position=0,
        )
        
        x= [{'nome': 'Ana Paula Gomes', 'titulo': 'Análise de dados para cidades', 'repo': 'https://github.com/DadosAbertosDeFeira/', 'publico': 'Intermediário (alguma experiência prévia com um framework, biblioteca ou técnica específica)', 'conhecimento': 'Análise de dados (iniciante), SQL (básico), pandas (iniciante)', 'descrição': 'Vamos utilizar dados abertos para criar análises que sirvam para entender cidades de todo o Brasil.', 'comunidadde': 'O projeto tem o objetivo de desenvolver tecnologias cívicas que sirvam para qualquer cidade de todo o Brasil. A partir da participação nessa sprint, o participante poderá explorar dados da sua cidade e entendê-la melhor. Com sorte, se envolver mais com ela através da programação. :)', 'horarios': 'Sábado - 10h às 13h, Domingo - 10h às 13h'}, {'nome': 'Bruno Messias', 'titulo': 'Helios Network Visualization and Streaming', 'repo': 'https://github.com/fury-gl/helios', 'publico': 'Iniciante (conhecimentos básicos em Python, Orientação a Objetos, Estruturas de Dados, etc.)', 'conhecimento': 'Conhecimento básico sobre grafos e dataviz, conhecimento básico de inglês', 'descrição': 'Esse projeto foi desenvolvido no meu período do google summer of code 2021. Helios é uma ferramente que permite análise de grafos (tais como oriundos de redes sociais) e inspeção visual. Além disso o Helios permite  o compartilhamento da visualização utilizando o protocolo WebRTC.', 'comunidadde': 'O helios sana algumas deficiências dos softwares livres para visualização de grafos. Tais como ser capaz de visualizar grafos com milhões de nós e permitir a interação colaborativa.', 'horarios': 'Sábado - 14h às 17h, Domingo - 15h às 18h'}, {'nome': 'Giulio Carvalho', 'titulo': 'Querido Diário', 'repo': 'https://queridodiario.ok.org.br/', 'publico': 'Intermediário (alguma experiência prévia com um framework, biblioteca ou técnica específica)', 'conhecimento': 'Eu coloquei público intermediário porque contribuições de código necessitam conhecimentos em raspagem de dados, frontend ou api, por exemplo. Como o projeto tem vários repositórios, pessoas que tem conhecimento de frameworks como Scrapy, FastAPI e Angular conseguem contribuir com partes diferentes do projeto (raspadores, API, frontend). Mas também pensamos em fazer muitas melhorias de documentação do projeto, então não seria necessário conhecimento técnico prévio. Se conseguirem passar pras pessoas que qualquer nível é bem vindo, seria ótimo :)', 'descrição': 'O Querido Diário é um projeto para libertar dados de diários oficiais municipais, desde a raspagem dos dados de cada município até a disponibilização do conteúdo processo em formato aberto numa API e numa plataforma de busca. Assim, o projeto tem vários repositórios, cada um dedicado a uma etapa do processo. Com o lançamento oficial da plataforma de busca, queremos dar uma organizada na casa para diminuir as barreiras iniciais de contribuição e também adicionar novas funcionalidades que as pessoas achem legais :) Pensamos inicialmente em melhorar a documentação, melhorar a arquitetura do projeto pra tornar mais fácil de inserir novas funcionalidades, melhorar a interface de uso das usuárias e também construir novos raspadores.', 'comunidadde': 'O projeto tem uma visão clara de libertação de dados onde eles são menos transparentes. Queremos fazer com que informações essenciais de funcionamento de todos os municípios do Brasil estejam acessíveis a qualquer pessoa, técnica ou não, que precisa de uma informação pontual que só está disponível no diário ou que deseja realizar um estudo acadêmico através do conteúdo de anos de diários de várias cidades. Cremos que é possível chegar num ponto onde poderemos utilizar esses dados de forma tão simples que será fácil cruzar informações com outras fontes públicas como as da Receita Federal e do SUS por exemplo. É um projeto de código aberto e muito receptivo a novas contribuições, feito por pessoas muito envolvidas na comunidade e que valorizam demais essa construção colaborativa.', 'horarios': 'Sábado - 10h às 13h, Sábado - 14h às 17h, Domingo - 10h às 13h, Domingo - 15h às 18h'}, {'nome': 'João JS Bueno', 'titulo': 'terminedia', 'repo': 'https://github.com/jsbueno/terminedia', 'publico': 'Iniciante (conhecimentos básicos em Python, Orientação a Objetos, Estruturas de Dados, etc.)', 'conhecimento': 'Python puro, vontade de criar arte na forma de programas ou gostar de jogos vintage', 'descrição': 'O Terminedia é um projeto aberto, sem fins de mercado: é um framework que permite a criação de ASCIIArt ou Unicode Art no terminal, de forma interativa. Ele expõe APIs de desenhos com caracteres, incluindo podendo usar caracteres de bloco  ASCII numa emulação de pixels de alta resolução de texto. Ao longo do desenvolvimento, por não depender de nenhuma lib ou framework externo, ele foi incorporando estruturas de dados e mecanismos que usam a linguagem de forma bastante avançada - por exemplo, decorators que acrescentam parâmetros de cor efundo em um método, de forma transparente, ou subclasses de str para facilitar o uso de emojis. \nHoje o projeto está bastante completo, contando inclusive com widgets de edição de texto e seleção de opções, suporte a mouse, que permitem até o desenvolvimento de apps completas no terminal. \nUm ponto fraco do projeto é a documentação e o fato de que os exemplos existentes (são programas stand-alone instalados junto com o projeto), não cobrem todas as possibilidades existindo no código.\nA sprint pode focar exatamente nos programas de exemplos: tanto evoluir os exemplos existentes para que se tornem aplicativos com utilidade em si mesmos: há o terminedia-plot para plotagem de gráficos no terminal e o terminedia-text para criação de banners de texto usando letras grandes desenhadas com os caracteres de bloco, por exemplo. U  outro é um joguinho de snake que é só uma prova de conceito e pode ser polido até ser um jogo completo, com introdução de fases e níveis de dificuldade. E há funcionalidades inteiras sem exemplos, como os widgets (controles para entrada de texto e seleção), degradês, e os transformers em geral: um mecanismo extremamente poderoso que permite a criação de centenas de efeitos especiais programáticos.', 'comunidadde': 'é um projeto com foco cultural e artístico - então sua contribuição vem na razão direta de existirem usuários usando o mesmo como ferramenta para suas criações. Eventualmente pode ser usado no mercado para enfeitar com efeitos especiais passos feitos no terminal como comandos de git, ou saídas de log e compiladores - da mesma forma que o google cria seus doodles. Outras bibliotecas de Python para o terminal tem um foco mais pragmático tentando ser sérias: o rich foca muito na criação de logs coloridos, e o prompt toolkit foca em permitir a criação de apps de manipulação de dados - a ideia do terminedia é deixar as possibilidades abertas para criação artística. Por exemplo, é possível ter uma área de edição de texto na tela do terminal com escrita na vertical, de baixo pra cima e da esquerda pra direita, com colunas de texto em vez de linhas de texto - e colocar isso numa aplicação', 'horarios': 'Domingo - 10h às 13h, Domingo - 15h às 18h'}, {'nome': 'Pâmella Araújo Balcaçar', 'titulo': 'Rasa Boilerplate', 'repo': 'https://github.com/BOSS-BigOpenSourceSibling/bot-da-boss', 'publico': 'Iniciante (conhecimentos básicos em Python, Orientação a Objetos, Estruturas de Dados, etc.)', 'conhecimento': 'Conhecimentos básicos em Python, sintaxe, e também as tecnologias como RASA, Docker, preferencialmente ambiente linux.', 'descrição': 'O projeto open source Rasa Boilerplate será apresentado junto com conceitos de comunidades open source e o desenvolvimento de chatbots; Entendendo o projeto boilerplate e as tecnologias envolvidas (RASA, Python, Docker);  Conhecerá arquitetura implementada. E por fim, apresentaremos as issues para contribuição.', 'comunidadde': 'Por ser um projeto open source e com parte de sua tecnologia é desenvolvido em python, poderá ser promotor da vivência de contribuição em um projeto assim.', 'horarios': 'Domingo - 15h às 18h'}, {'nome': 'Rafael Ferreira Fontenelle', 'titulo': 'Tradução da documentação do Python', 'repo': 'https://github.com/python/python-docs-pt-br/wiki/Sprint-pybr2021', 'publico': 'Não técnico (isto é, sua atividade não abordará tecnologia diretamente. Ex: Tradução da documentação)', 'conhecimento': 'Inglês', 'descrição': 'Esta sprint busca juntar atuais e potenciais membros da equipe de tradução da documentação do Python em uma frente de ataque às mensagens não traduzidas.', 'comunidadde': 'Incentivar novos membros a participar da tradução da documentação, bem como aumentar o número de mensagens traduzidas.', 'horarios': 'Sábado - 14h às 17h, Domingo - 10h às 13h, Domingo - 15h às 18h'}]

        self.channel = await get_or_create_channel(f"sprints-info", self._guild, position=0, category=organizacao_cat)
        
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

            self._guild = await self.bot.fetch_guild(config("DISCORD_GUILD_ID"))
    
            try:
                role = get_or_create_role(channel.name,self._guild ,None)
            except:
                role = None

            canal =  f"<#{channel.id}>" if channel else ''
            data = f"{tutorial['nome']} - {canal} - {datetime.strptime(tutorial['data_hora'],'%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')}"

            insc=[]

            for inscritos in tutorial.get("userinscritos"):
                inscrito = discord.utils.get(self.bot.get_all_members(), id=inscritos)
                if inscrito:
                    insc.append(f"{inscrito.name} - <@{inscrito.id}>")
                    for role in inscrito.roles:
                        if role.name == channel.name:
                            insc.append(f"{inscrito.name} - <@{inscrito.id}>")
                    #await logchannel(self.bot,f"======   {inscrito.name} - <@{inscrito.id}>")

            insc = list(dict.fromkeys(insc))
            out.append(dict(data=data,inscritos=insc))
        
        logger.info(out)
        os.makedirs("./json",exist_ok=True)
        with open(f"./json/inscritos.json", 'w') as f:
            json.dump(out, f)

        


    @commands.command(name="close",brief="warnig on use that!!")
    async def close(self, ctx):
        self._allowtouser=False
    
        for index,tutorial in enumerate(self._tutoriais):
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
            #await logchannel(self.bot, f"Carregando tutorial-{index}:{tutorial.get('nome')[:20]}")
            channel = await get_or_create_channel(f"tutorial-{index}-chat", self._guild, position=99, category=organizacao_cat)
            voice=  await get_or_create_channel(f"tutorial-{index}-voice", self._guild, position=99, category=organizacao_cat,type=discord.ChannelType.voice)
            tutorial["channel"] = int(channel.id)
            tutorial["voice"] = int(voice.id)
            #await self.clear(tutorial["channel"])
            logger.info(tutorial)
            #msg= await self.lista(tutorial,True)
            #tutorial["inscritos_msg"] = int(msg.id)

            self._tutoriais[index] = tutorial

        #await self.show_tutoriais()
        logger.info("Canais criados com sucesso")
        self.check_messages=True
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

    #@commands.Cog.listener()
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

                    if not self._allowtouser:
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
        msg+=":red_circle: INSCRIÇÕES FECHADAS :red_circle:" if not self._allowtouser else ":green_circle: INSCRIÇÕES ABERTAS :green_circle:\n:keyboard: DIGITE a palavra 'entrar' para sua inscrição ou 'sair' para remover sua inscrição :keyboard:"
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
