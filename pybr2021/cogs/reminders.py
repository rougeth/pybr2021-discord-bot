import discord
from discord.ext import commands, tasks
from decouple import config


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.weekly_meeting_points.start()

    async def _send_reminder(self, reminder: str):
        guild_id = config("DISCORD_GUILD_ID")
        guild = await self.bot.fetch_guild(guild_id)

        channels = await guild.fetch_channels()
        category = discord.utils.get(
            channels, name="Organização", type=discord.ChannelType.category
        )
        channel = discord.utils.get(channels, name="geral", category_id=category.id)

        roles = await guild.fetch_roles()
        role = discord.utils.get(roles, name="Organização")

        message = (
            f"📆 Lembrete: {role.mention}\n"
            f"**{reminder}**\n\n"
            "<https://github.com/pythonbrasil/pybr2021-org/issues?q=is%3Aissue+is%3Aopen+label%3AReunião>"
        )
        await channel.send(content=message)

    # @tasks.loop(hours=96)
    async def weekly_meeting_points(self):
        await self._send_reminder(
            "Comentar issue da próxima reunião com items que precisam ser discutidos"
        )

    # @weekly_meeting_points.before_loop
    async def before_weekly_meeting_points(self):
        await self.bot.wait_until_ready()
