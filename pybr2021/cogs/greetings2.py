import asyncio
import json
import time
from base64 import b64encode
from datetime import datetime, timedelta
from functools import wraps
from random import shuffle

import discord
import httpx
from bot_msg import (
    auth_instructions,
    auth_already_confirmed,
    auth_email_not_found,
    auth_welcome,
)
from decouple import config
from discord import message
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


async def http_get_json(semaphore, client, url, params, retry=3):
    async with semaphore:
        try:
            response = await client.get(url, params=params)
        except httpx.ReadTimeout:
            if retry > 0:
                await asyncio.sleep(20)
                return await http_get_json(semaphore, client, url, params, retry - 1)
            logger.exception("Erro")

        return response.json()


async def load_attendees(updated_at: datetime = None):
    default_params = {
        "token": EVENTBRITE_TOKEN,
        "status": "attending",
    }
    if updated_at:
        updated_at = updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        default_params["changed_since"] = updated_at

    url = "https://www.eventbriteapi.com/v3/events/169078058023/attendees/"
    semaphore = asyncio.BoundedSemaphore(10)
    async with httpx.AsyncClient() as client:
        response = await http_get_json(semaphore, client, url, default_params)
        if not updated_at:
            logger.info(
                "Attendees load initialized. attendees={attendees}, pages={pages}".format(
                    attendees=response["pagination"]["object_count"],
                    pages=response["pagination"]["page_count"],
                )
            )

        attendees = []
        attendees.extend(response["attendees"])

        tasks = []
        page_count = response["pagination"]["page_count"]
        for page_number in range(1, page_count + 1):
            # I'm not proud of this, but Eventbrite is the one to blame
            next_page = json.dumps({"page": page_number})

            params = default_params.copy()
            params["continuation"] = b64encode(next_page.encode("utf-8")).decode(
                "utf-8"
            )
            tasks.append(http_get_json(semaphore, client, url, params))

        if tasks:
            results = await asyncio.gather(*tasks)
            attendees.extend(
                [attendees for result in results for attendees in result["attendees"]]
            )

    return attendees


def create_index(attendees):
    index = {}
    for attendee in attendees:
        profile = attendee["profile"]
        index[attendee["order_id"]] = profile
        index[profile["email"].lower()] = profile
    return index


class Greetings2(commands.Cog):
    AUTH_CHANNEL_ID = config("DISCORD_AUTH_CHANNEL_ID", cast=int)
    AUTH_START_EMOJI = "👍"
    ATTENDEES_ROLE_NAME = "Participantes"

    def __init__(self, bot):
        self.bot = bot
        self._guild = None

        # Attendees from Eventbrite
        self._index = {}
        self._index_updated_at = None
        self._atteendee_role = None
        self._attendees = []
        #self.load_indexes.start()


    #@tasks.loop(minutes=1)
    @only_log_exceptions
    async def load_indexes(self):
        new_attendees = await load_attendees(self._index_updated_at)
        if len(new_attendees) != 0:
            logger.info(f"New attendees found. total={len(new_attendees)}")

        self._attendees.extend(new_attendees)
        self._index = create_index(self._attendees)
        self._index_updated_at = datetime.utcnow()

        logger.info(
            "Attendees index updated. total={}, updated_at={}".format(
                len(self._attendees),
                self._index_updated_at,
            )
        )

    def search_attendee(self, query):
        return self._index.get(query.strip().lower())

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        joined_with_invite_code = await self.invite_tracker.check_new_user(member)
        if joined_with_invite_code:
            return

        role = await self.get_attendee_role(member.guild)
        await member.add_roles(role)
        await logchannel(self.bot, f"✅ atribuí cargo de participante para {member.mention} ")


    #@commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        """Quando usuário reagir a mensagem no canal de texto #credencimento, o bot enviará
        uma mensagem diretamente para o usuário pedindo email para confirmação.
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

    #@commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.type != discord.ChannelType.private:
            return

        guild = await self.get_guild()
        member = await guild.fetch_member(message.author.id)
        if not member:
            logger.info(
                f"User not in Python Brasil server. user={message.author.name}, content={message.content}"
            )
            return

        if len(member.roles) != 1:
            await message.author.send(auth_already_confirmed)
            logger.info(
                f"User already authenticated. user={message.author.name}, content={message.content}"
            )
            return



        logger.info(
            f"Authenticating user. user={message.author.name}, id={message.author.id}, content={message.content}"
        )

        profile = self.search_attendee(message.content)
        if not profile:
            logger.info(
                f"User not found on index. user_id={message.author.id}, content={message.content!r}"
            )
            await message.add_reaction("❌")
            await message.author.send(auth_email_not_found.format(query=message.content))
            await logchannel(self.bot, (
                f"❌\nInscrição não encontrada - {message.author.mention}"
                f"\n`{message.content}`"
            ))
            return

        role = await self.get_attendee_role(message.guild)

        await member.add_roles(role)
        await message.add_reaction("✅")
        await member.send(DISCORD_GENERAL_INVITE)
        await logchannel(self.bot, f"✅\n{member.mention}  confirmou sua inscrição")
        logger.info(f"User authenticated. user={message.author.name}")

    @commands.Cog.listener()
    async def on_ready(self):
        # Invite Tracker
        guild = await self.get_guild()
        self.invite_tracker = InviteTracker(self.bot, guild, ROLE_INVITE_MAP)
        await self.invite_tracker.sync()
        logger.info(f"Invite tracker synced. invites={self.invite_tracker.invites!r}")

    #@commands.command(name="confirmar",brief="")
    async def confirm_eventbrite(self, ctx, value):
        if len(ctx.author.roles) != 1:
            await ctx.message.add_reaction("❌")
            return

        profile = self.search_attendee(value)
        if not profile:
            await ctx.message.add_reaction("❌")
            return

        role = await self.get_attendee_role(ctx.guild)
        await ctx.author.add_roles(role)
        await ctx.message.delete()
        await logchannel(self.bot, f"Usuário confirmou inscrição com commando. {ctx.author.mention}")

    #@commands.command(name="check-eventbrite",brief="Check if user has eventbrite [email or tickeid]")
    async def check_eventbrite(self, ctx, value):
        profile = self.search_attendee(value)
        if profile:
            message = f"`{value}` encotrado.\n```{profile!r}```"
        else:
            message = f"`{value}` não encotrado."

        await ctx.channel.send(message)
