from urllib import request

from disnake import ApplicationCommandInteraction, Permissions
from disnake.ext import commands
from disnake.ext.commands import ExtensionNotFound, ExtensionAlreadyLoaded, ExtensionFailed, NoEntryPointError, \
    ExtensionNotLoaded


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Admin(bot))
    print("Loaded Admin Cog.")


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name="cogs",
                            description="Replies with a list of all the loaded cogs.",
                            default_member_permissions=Permissions(administrator=True))
    async def cogs(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()

        cogs: str = str(list(self.bot.cogs.keys()))
        await inter.send(cogs)

    @commands.slash_command(name="load",
                            description="Loads a cog.",
                            default_member_permissions=Permissions(administrator=True))
    async def load(self, inter: ApplicationCommandInteraction, cog: str) -> None:
        await inter.response.defer()

        try:
            self.bot.load_extension(cog)
        except (ExtensionNotFound, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed) as e:
            await inter.send(e, ephemeral=True)
            return
        await inter.send(f"{cog} loaded.")

    @commands.slash_command(name="unload",
                            description="Unloads a cog.",
                            default_member_permissions=Permissions(administrator=True))
    async def unload(self, inter: ApplicationCommandInteraction, cog: str) -> None:
        try:
            self.bot.unload_extension(cog)
        except (ExtensionNotFound, ExtensionNotLoaded) as e:
            await inter.send(e, ephemeral=True)
            return
        await inter.send(f"{cog} unloaded.")

    @commands.slash_command(name="reload",
                            description="Reloads a cog.",
                            default_member_permissions=Permissions(administrator=True))
    async def reload(self, inter: ApplicationCommandInteraction, cog: str) -> None:
        await inter.response.defer()

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except (ExtensionNotFound, ExtensionNotLoaded, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed) as e:
            await inter.send(e, ephemeral=True)
            return
        await inter.send(f"{cog} reloaded.")

    @commands.slash_command(name="ip",
                            description="Replies with the server's IP.",
                            default_member_permissions=Permissions(administrator=True))
    async def ip(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()

        ipv4: str
        ipv6: str
        ipv4 = request.urlopen('https://v4.ident.me').read().decode('utf8')
        if ipv4 != "":
            await inter.send(ipv4, ephemeral=True)
            return
        ipv6 = request.urlopen('https://v6.ident.me').read().decode('utf8')
        if ipv6 != "":
            await inter.send(ipv6, ephemeral=True)
            return
        await inter.send("Could not get IP.", ephemeral=True)
