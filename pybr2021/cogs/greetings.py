import asyncio
import json
import time
from base64 import b64encode
from datetime import datetime

import discord
import httpx
from discord.ext import commands, tasks
from loguru import logger
from decouple import config

from discord_setup import get_or_create_channel
from bot_msg import auth_instructions, auth_user_not_found, auth_order_not_found


EVENTBRITE_TOKEN = config("EVENTBRITE_TOKEN")


async def http_get_json(semaphore, client, url, params, retry=3):
    async with semaphore:
        try:
            response = await client.get(url, params=params)
            return response.json()
        except httpx.ReadTimeout:
            logger.exception()
            if retry > 0:
                await asyncio.sleep(5)
                return await http_get_json(semaphore, client, url, params, retry-1)



async def load_attendees(updated_at: datetime = None):
    default_params = {
        "token": EVENTBRITE_TOKEN,
        "status": "attending",
    }
    if updated_at:
        updated_at = updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"Loading attendees after timestamp. updated_at={updated_at}")
        default_params["changed_since"] = updated_at

    url = "https://www.eventbriteapi.com/v3/events/169078058023/attendees/"
    semaphore = asyncio.BoundedSemaphore(2)
    async with httpx.AsyncClient() as client:
        response = await http_get_json(semaphore, client, url, default_params)
        if not updated_at:
            logger.info("Attendees load initialized. attendees={attendees}, pages={pages}".format(
                attendees=response["pagination"]["object_count"],
                pages=response["pagination"]["page_count"],
            ))

        attendees = []
        attendees.extend(response["attendees"])

        tasks = []
        page_count = response["pagination"]["page_count"]
        for page_number in range(1, page_count + 1):
            # I'm not proud of this, but Eventbrite is the one to blame
            next_page = json.dumps({"page": page_number})

            params = default_params.copy()
            params["continuation"] = b64encode(next_page.encode("utf-8")).decode('utf-8')
            tasks.append(http_get_json(semaphore, client, url, params))

        if tasks:
            results = await asyncio.gather(*tasks)
            logger.info(f"Result from querying Eventbrite API. total_results={len(results)}")

            attendees.extend(
                [attendees for result in results for attendees in result["attendees"]]
            )

    return attendees


def create_email_index(attendees):
    index = {}
    for attendee in attendees:
        profile = attendee["profile"]
        index[profile["email"]] = profile
    return index


def create_order_index(attendees):
    index = {}
    for attendee in attendees:
        profile = attendee["profile"]
        index[attendee["order_id"]] = profile
    return index


class Greetings(commands.Cog):
    CATEGORY_NAME = "Credenciamento"
    WELCOME_CHANNEL_NAME = "boas-vindas"
    ATTENDEES_ROLE_NAME = "inscritos"
    ORG_ROLE_NAME = "organização"

    def __init__(self, bot):
        self.bot = bot
        self._attendees = []
        self._attendees_updated_at = None
        self._category = None
        self._welcome_channel = None
        self.order_index = {}
        self.email_index = {}
        self.load_indexes.start()

    @tasks.loop(minutes=1)
    async def load_indexes(self):
        new_attendees = await load_attendees(self._attendees_updated_at)
        logger.info(
            f"Attendees loaded. attendees={len(self._attendees)}, new_attendees={len(new_attendees)}"
        )
        self._attendees.extend(new_attendees)
        self._attendees_updated_at = datetime.utcnow()

        self.email_index = create_email_index(self._attendees)
        self.order_index = create_order_index(self._attendees)

    def default_permissions_overwrite(self, guild):
        return {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False, read_messages=False
            ),
        }

    async def get_attendee_role(self, guild: discord.Guild) -> discord.Role:
        roles = await guild.fetch_roles()
        return discord.utils.get(roles, name="inscritos")

    async def get_org_role(self, guild: discord.Guild) -> discord.Role:
        members = await guild.fetch_roles()
        return discord.utils.get(members, name=self.ORG_ROLE_NAME)

    async def get_member(self, guild: discord.Guild, name: str) -> discord.Role:
        members = await guild.fetch_members().flatten()
        return discord.utils.get(members, name=name)

    async def get_category(self, guild: discord.Guild) -> discord.CategoryChannel:
        if not self._category:
            overwrites = self.default_permissions_overwrite(guild)
            self._category = await get_or_create_channel(
                self.CATEGORY_NAME,
                guild,
                discord.ChannelType.category,
                overwrites=overwrites,
            )
        return self._category

    async def send_auth_instructions(
        self, channel: discord.TextChannel, member: discord.Member
    ):
        await channel.send(auth_instructions.format(name=member.mention))

    async def send_greetings_message(
            self, guild: discord.Guild, member: discord.Member
    ):

        if not self._welcome_channel:
            channels = await guild.fetch_channels()
            self._welcome_channel = discord.utils(channels, name=self.WELCOME_CHANNEL_NAME)

        await self._welcome_channel.send(auth_welcome.format(name=member.mention))

    async def create_user_auth_channel(
        self, member: discord.Member, category: discord.CategoryChannel
    ):
        overwrites = self.default_permissions_overwrite(member.guild)
        overwrites[member] = discord.PermissionOverwrite(read_messages=True)

        return await get_or_create_channel(
            member.name,
            member.guild,
            category=category,
            overwrites=overwrites,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        category = await self.get_category(member.guild)
        channel = await self.create_user_auth_channel(member, category)

        await self.send_auth_instructions(channel, member)

    @commands.command(name="confirmar")
    async def auth(self, ctx: commands.Context, value: str):
        logger.info(f"Authenticating user. user={ctx.author.name}, value={value}")
        if not ctx.channel.category or ctx.channel.category.name != self.CATEGORY_NAME:
            message = f"❌ Ops! Eu só consigo validar inscrições em canais na category {self.CATEGORY_NAME}"
            await ctx.channel.send(content=message)
            return

        # TODO validar se usuário já está inscrito

        profile = self.order_index.get(value) or self.email_index.get(value)

        if not profile:
            role = await self.get_org_role(ctx.guild)
            await ctx.channel.send(content=auth_order_not_found.format(role=role.mention))
            return

        member = await self.get_member(ctx.guild, ctx.channel.name)
        if not member:
            logger.warning(f"Member no found. name={ctx.channel.name}")
            await ctx.channel.send(content=auth_user_not_found.format(name=ctx.channel.name))
            return

        role = await self.get_attendee_role(ctx.guild)
        await member.add_roles(role)
        await ctx.channel.delete()
        #await self.send_greetings_message(ctx.guild, member)
