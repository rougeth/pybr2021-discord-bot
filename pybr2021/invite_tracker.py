import discord
from loguru import logger


def generate_role_index(roles):
    index = {}
    for role, invite_codes in roles:
        index.update({code: role for code in invite_codes})

    return index


class InviteTracker:
    def __init__(self, client, guild, role_invite_map):
        self.client = client
        self.guild = guild
        self.old_invites = {}
        self.invites = {}
        self.invite_codes = {}
        self.role_invite_map = role_invite_map

    async def fetch_roles(self):
        # Available roles
        roles = await self.guild.fetch_roles()
        roles = {role.name: role.id for role in roles}

        # Fetch role ID from role name
        invite_codes = generate_role_index(self.role_invite_map)
        code_role_ids = {}

        for code, role_name in invite_codes.items():
            code_role_ids[code] = roles[role_name]

        return code_role_ids

    async def get_invites(self):
        invites = await self.guild.invites()
        return {invite.code: invite.uses for invite in invites}

    async def sync(self):
        invites = await self.get_invites()
        self.old_invites = self.invites
        self.invites = invites

    def diff(self):
        diff = {}
        for code, uses in self.invites.items():
            old_uses = self.old_invites.get(code, 0)
            if uses > old_uses:
                diff[code] = uses - old_uses
                logger.info(f"Invite code used. code={code}, before={old_uses}, after={uses}")

        return diff

    async def check_new_user(self, member):
        if not self.invite_codes:
            self.invite_codes = await self.fetch_roles()

        await self.sync()
        invite_diff = self.diff()

        for code, uses in invite_diff.items():
            try:
                new_role = discord.Object(self.invite_codes.get(code))
            except TypeError:
                return None

            if new_role and uses == 1:
                logger.info(
                    f"Added role to member. member={member.display_name}, role={new_role}"
                )
                await member.add_roles(new_role)
                return new_role
            elif uses > 1:
                logger.warning(
                    "Two or more users joined server between invite tracker updates."
                )

        return None
