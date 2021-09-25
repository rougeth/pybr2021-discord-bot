from datetime import datetime
import asyncio
import time

import discord
import httpx
from discord.ext import commands, tasks
from discord_setup import get_or_create_channel
from loguru import logger
from decouple import config


EVENTBRITE_TOKEN = config("EVENTBRITE_TOKEN")


async def http_get_json(client, url, params):
    response = await client.get(url, params=params)
    return response.json()


async def load_attendees(updated_at: datetime = None):
    params = {
        "token": EVENTBRITE_TOKEN,
        "status": "attending",
    }
    if updated_at:
        updated_at = updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"Loading attendees after timestamp. updated_at={updated_at}")
        params["changed_since"] = updated_at

    url = "https://www.eventbriteapi.com/v3/events/169078058023/attendees/"
    async with httpx.AsyncClient() as client:
        response = await http_get_json(client, url, params)

        attendees = []
        attendees.extend(response["attendees"])

        tasks = []
        page_count = response["pagination"]["page_count"]
        for page_number in range(1, page_count + 1):
            params["page"] = page_number
            tasks.append(http_get_json(client, url, params))

        results = await asyncio.gather(*tasks)
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
    def __init__(self, bot):
        self.bot = bot
        self._attendees = []
        self._attendees_updated_at = None
        self._category = None
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

    def default_permissions_overwrite():
        return {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False, read_messages=False
            ),
        }

    async def get_category(self, guild: discord.Guild) -> discord.CategoryChannel:
        if not self._category:
            overwrites = self.default_permissions_overwrite()
            self._category = await get_or_create_channel(
                "Credenciamento",
                guild,
                discord.ChannelType.category,
                overwrites=overwrites,
            )
        return self._category

    async def send_greetings_message(
        self, channel: discord.TextChannel, member: discord.Member
    ):
        await channel.send(
            f"**Boas vindas ao credenciamento da Python Brasil 2021!**\n{member.mention} Instruções"
        )

    async def create_user_auth_channel(
        self, member: discord.Member, category: discord.CategoryChannel
    ):
        overwrites = self.default_permissions_overwrite()
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

        await self.send_greetings_message(channel, member)
