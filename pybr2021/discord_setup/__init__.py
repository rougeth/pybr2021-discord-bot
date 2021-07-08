import discord


async def get_or_create_role(
    name: str, guild: discord.Guild, permissions: discord.Permissions
):
    existing_roles = await guild.fetch_roles()
    role = discord.utils.get(existing_roles, name=name)
    if not role:
        role = await guild.create_role(name=name, permissions=permissions)

    return role


async def get_or_create_channel(
    name: str,
    guild: discord.Guild,
    type: discord.ChannelType = discord.ChannelType.text,
    **kwargs
):
    methods = {
        discord.ChannelType.category: guild.create_category,
        discord.ChannelType.text: guild.create_text_channel,
        discord.ChannelType.voice: guild.create_voice_channel,
    }
    method = methods.get(type)
    if not method:
        raise Exception("Channel type unknown")

    search_kwargs = {}
    if "category" in kwargs:
        search_kwargs["category_id"] = kwargs["category"].id

    existing_channels = await guild.fetch_channels()
    channel = discord.utils.get(
        existing_channels, name=name, type=type, **search_kwargs
    )
    if not channel:
        channel = await method(name=name, **kwargs)

    return channel
