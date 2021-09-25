import time

import discord
from discord.ext import commands
from discord_setup import get_or_create_channel


class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._category = None

    def default_permissions_overwrite():
        return {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
        }

    async def get_category(self, guild: discord.Guild) -> discord.CategoryChannel:
        if not self._category:
            overwrites = self.default_permissions_overwrite()
            self._category = await get_or_create_channel(
                "Credenciamento",
                guild,
                discord.ChannelType.category,
                overwrites=overwrites
            )
        return self._category

    async def send_greetings_message(self, channel: discord.TextChannel, member: discord.Member):
        await channel.send(f"**Boas vindas ao credenciamento da Python Brasil 2021!**\n{member.mention} Instruções")

    async def create_user_auth_channel(self, member: discord.Member, category: discord.CategoryChannel):
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
