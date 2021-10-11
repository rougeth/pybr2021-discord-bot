import asyncio
import os
import sys
from typing import Dict

import discord
import sentry_sdk
import toml
from decouple import config
from discord import channel, message
from discord.ext import commands
from loguru import logger

import bot_msg
import cogs
from discord_setup import get_or_create_channel, get_or_create_role

SENTRY_TOKEN = config("SENTRY_TOKEN", default=None)
if SENTRY_TOKEN:
    sentry_sdk.init(SENTRY_TOKEN, traces_sample_rate=1.0)

DISCORD_TOKEN = config("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="pybr!", intents=discord.Intents.all())
bot.add_cog(cogs.Reminders(bot))
bot.add_cog(cogs.Greetings(bot))
bot.add_cog(cogs.Schedules(bot))

config_file = toml.load("./config.toml")
DEFAULT_CHANNEL_MSG = '859819206584959007'


@bot.event
async def on_error(event, *args, **kwargs):
    """Don't ignore the error, causing Sentry to capture it."""
    logger.exception("Exception while handling event. event={event!r}, args={args!r}, kwargs={kwargs!r}")
    if SENTRY_TOKEN:
        _, e, traceback = sys.exc_info()
        sentry_sdk.capture_exception(e)
        logger.info(f"Exception sent to Sentry. e={e!r}")


@bot.event
async def on_message(message):
    if not message.author.bot and message.content.lower() == "galvão?":
        await message.channel.send("Fala Tino!")

    await bot.process_commands(message)


@bot.group(name="config", invoke_without_command=True)
async def config_group(ctx, *args):
    await ctx.channel.send(
        "Comandos disponíveis:\n"
        "**roles**\n - Cria todos os roles necessários\n"
        "**canais**\n"
    )


@config_group.command()
async def info(ctx: commands.Context):
    await ctx.channel.send(
        content=(f"Guild ID: `{ctx.guild.id}`\nChannel ID: `{ctx.channel.id}`\n")
    )


@config_group.command(name="roles")
async def config_roles(ctx: commands.Context):
    logger.info("Configurando roles")
    tracking_message = await ctx.channel.send(
        bot_msg.roles.format(bot_msg.emo01, bot_msg.emo02, bot_msg.emo03)
    )
    roles = await ctx.guild.fetch_roles()
    roles = {role.name: role for role in roles}
    logger.info(f"{len(roles)} roles encontrados. roles={','.join(roles.keys())!r}")
    await tracking_message.edit(
        content=(bot_msg.roles.format(bot_msg.emo_check, bot_msg.emo02, bot_msg.emo03))
    )

    # Organization Roles
    org_permissions = discord.Permissions.all()
    org_permissions.administrator = False

    new_roles = [
        ("root", discord.Permissions.all(), 90),
        ("Organização", org_permissions, 80),
        ("Voluntariado", None, 70),
    ]

    for name, permissions, _ in new_roles:
        roles[name] = await get_or_create_role(name, ctx.guild, permissions=permissions)

    await tracking_message.edit(
        content=(
            bot_msg.roles.format(bot_msg.emo_check, bot_msg.emo_check, bot_msg.emo03)
        )
    )

    # Configurando permissões
    positions = {roles[name]: position for name, _, position in new_roles}
    positions[ctx.guild.me.top_role] = 999
    await ctx.guild.edit_role_positions(positions)

    await tracking_message.edit(
        content=(
            bot_msg.roles.format(
                bot_msg.emo_check, bot_msg.emo_check, bot_msg.emo_check
            )
        )
    )


@config_group.command(name="canais_toml")
async def config_channels2(ctx: commands.Context):

    track_message = await ctx.channel.send(
        """{} Criando Categorias e Canais""".format("⌛")
    )

    # Load categories and channels from config
    for categorie in config_file.get("categories"):
        cat_name = categorie.get("name")
        cat_pos = categorie.get("position")
        restrict_access = categorie.get("restict_access", False)

        track_message_cat = await ctx.channel.send(
            """{}----Categoria {}""".format("⌛", cat_name)
        )

        if cat_name != "default":
            overwrites = (
                {
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                }
                if restrict_access
                else None
            )

            # Create Category
            discord_cat = await get_or_create_channel(
                cat_name,
                ctx.guild,
                type=discord.ChannelType.category,
                overwrites=overwrites,
                position=cat_pos,
            )

        for channel in categorie.get("channels"):

            channel_name = channel.get("name")
            channel_pos = channel.get("position")

            track_message_channel = await ctx.channel.send(
                """{}|--------Canal {}""".format("⌛", channel_name)
            )

            channel_param = {
                "name": channel_name,
                "guild": ctx.guild,
                "type": discord.ChannelType.voice
                if channel.get("voice", False)
                else discord.ChannelType.text,
                "position": channel_pos,
            }

            if cat_name != "default":
                channel_param["category"] = discord_cat

            await get_or_create_channel(**channel_param)

            await track_message_channel.edit(
                content=("""{}|--------Canal {}""".format("✅", channel_name))
            )

        await track_message_cat.edit(
            content=("""{}----Categoria {}""".format("✅", cat_name))
        )

    await track_message.edit(content=("""{} Criando Categorias e Canais""".format("✅")))


@config_group.command(name="canais")
async def config_channels(ctx: commands.Context):
    logger.info("Configurando canais")
    tracking_message = await ctx.channel.send(
        "1️⃣ Canais: Gerais\n" "2️⃣ Canais: Organização\n" "3️⃣ Canais: Voluntariado\n"
    )

    # Canais: Gerais
    await get_or_create_channel("boas-vindas", ctx.guild)
    await tracking_message.edit(
        content=(
            "✅ Canais: Gerais\n"
            "2️⃣ Canais: Organização\n"
            "3️⃣ Canais: Voluntariado\n"
        )
    )

    # Canais: Organização
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }

    organizacao_cat = await get_or_create_channel(
        "Organização",
        ctx.guild,
        type=discord.ChannelType.category,
        overwrites=overwrites,
        position=0,
    )
    await get_or_create_channel(
        "geral", ctx.guild, position=0, category=organizacao_cat
    )
    await get_or_create_channel(
        "dev-null", ctx.guild, position=1, category=organizacao_cat
    )
    await get_or_create_channel(
        "reuniões",
        ctx.guild,
        type=discord.ChannelType.voice,
        position=2,
        category=organizacao_cat,
    )

    await tracking_message.edit(
        content=("✅ Canais: Gerais\n✅ Canais: Organização\n3️⃣ Canais: Voluntariado\n")
    )

    # Canais: Voluntariado
    voluntariado_cat = await get_or_create_channel(
        "Voluntariado",
        ctx.guild,
        type=discord.ChannelType.category,
        overwrites=overwrites,
        position=1,
    )
    await get_or_create_channel(
        "america-latina-es", ctx.guild, position=0, category=voluntariado_cat
    )
    await get_or_create_channel(
        "pt-es-enquete-encuesta", ctx.guild, position=1, category=voluntariado_cat
    )

    await tracking_message.edit(
        content=("✅ Canais: Gerais\n✅ Canais: Organização\n✅ Canais: Voluntariado\n")
    )

@bot.command(name="boteco",brief="Send a remember to use buteco")
async def boteco(ctx):
    await sender(bot_msg.buteco)

@bot.command(name="msg",brief="Send a msg to a channel [#channel] [msg]")
async def sendmsg(ctx, *args):
    if len(args) < 2:
        logger.warning("missing destination message and message")
        return

    if args[0].startswith("<#"):
        channel_id = int(args[0][2:-1])
        destination = discord.utils.get(ctx.guild.channels, id=channel_id)
    elif args[0].startswith("<@"):
        member_id = int(args[0][2:-1])
        destination = discord.utils.get(ctx.guild.members, id=member_id)
    else:
        logger.warning(f"Not a channel or user. args={args}")
        await ctx.channel.send(
            f"Uhmm, não encontrei o canal/membro **{args[0]}** para enviar a mensagem"
        )
        return

    if not destination:
        logger.warning(
            f"Destination not found. destination={destination!r}, args={args!r}"
        )
        return

    message = " ".join(args[1:])
    logger.info(f"message sent. destination={destination}, message={message}")
    await destination.send(message)
        
async def reset(guild: discord.Guild):
    channels = await guild.fetch_channels()
    await asyncio.gather(*[channel.delete() for channel in channels])

    roles = await guild.fetch_roles()
    roles = [
        role.delete()
        for role in roles
        if not any([role.is_default(), role.is_bot_managed(), role.is_integration()])
    ]
    await asyncio.gather(*roles)

async def sender(message):
    channel = await bot.fetch_channel(DEFAULT_CHANNEL_MSG)
    await channel.send(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
