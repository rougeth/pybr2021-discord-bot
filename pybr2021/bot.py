import asyncio
import os
from typing import Dict


import discord
from decouple import config
from discord.ext import commands
from loguru import logger

from discord_setup import get_or_create_channel, get_or_create_role

DISCORD_TOKEN = config("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="pybr!", intents=discord.Intents.all())


@bot.group(name="config", invoke_without_command=True)
async def config_group(ctx, *args):
    await ctx.channel.send(
        "Comandos disponíveis:\n"
        "**roles**\n - Cria todos os roles necessários\n"
        "**canais**\n"
    )


@config_group.command(name="roles")
async def config_roles(ctx: commands.Context):
    logger.info("Configurando roles")
    tracking_message = await ctx.channel.send(
        "1️⃣ Conferindo *roles* existentes\n"
        "2️⃣ Criando novos *roles*\n"
        "3️⃣ Configurando permissões\n"
    )
    roles = await ctx.guild.fetch_roles()
    roles = {role.name: role for role in roles}
    logger.info(f"{len(roles)} roles encontrados. roles={','.join(roles.keys())!r}")
    await tracking_message.edit(
        content=(
            "✅ Conferindo roles já existem\n"
            "2️⃣ Criando novos *roles*\n"
            "3️⃣ Configurando permissões\n"
        )
    )

    # Novos roles
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
            "✅ Conferindo roles já existem\n"
            "✅ Criando novos *roles*\n"
            "3️⃣ Configurando permissões\n"
        )
    )

    # Configurando permissões
    positions = {roles[name]: position for name, _, position in new_roles}
    positions[ctx.guild.me.top_role] = 999
    await ctx.guild.edit_role_positions(positions)

    await tracking_message.edit(
        content=(
            "✅ Conferindo roles já existem\n"
            "✅ Criando novos *roles*\n"
            "✅ Configurando permissões\n"
        )
    )


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


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
