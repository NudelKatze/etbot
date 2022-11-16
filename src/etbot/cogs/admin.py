from urllib import request

from disnake import ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import ExtensionNotFound, ExtensionAlreadyLoaded, ExtensionFailed, NoEntryPointError, \
    ExtensionNotLoaded

from vars import roles


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Admin(bot))
    print("Loaded Admin Cog.")


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name="cogs",
                            description="Replies with a list of all the loaded cogs. (Staff Only)")
    async def cogs(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer(ephermal=True)
        if not roles.check_is_extended_staff(inter):
            await inter.followup.send("You do not have permission to use this command.")
            return

        cogs: str = str(list(self.bot.cogs.keys()))
        await inter.send(cogs)

    @commands.slash_command(name="load",
                            description="Loads a cog. (Staff Only)")
    async def load(self, inter: ApplicationCommandInteraction, cog: str) -> None:
        await inter.response.defer()
        if not roles.check_is_extended_staff(inter):
            await inter.followup.send("You do not have permission to use this command.")
            return

        try:
            self.bot.load_extension(cog)
        except (ExtensionNotFound, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed) as e:
            await inter.send(e)
            return
        await inter.send(f"{cog} loaded.")

    @commands.slash_command(name="unload",
                            description="Unloads a cog. (Staff Only)")
    async def unload(self, inter: ApplicationCommandInteraction, cog: str) -> None:
        await inter.response.defer(ephemeral=True)
        if not roles.check_is_extended_staff(inter):
            await inter.followup.send("You do not have permission to use this command.")
            return

        try:
            self.bot.unload_extension(cog)
        except (ExtensionNotFound, ExtensionNotLoaded) as e:
            await inter.send(e)
            return
        await inter.send(f"{cog} unloaded.")

    @commands.slash_command(name="reload",
                            description="Reloads a cog. (Staff Only)")
    async def reload(self, inter: ApplicationCommandInteraction, cog: str) -> None:
        await inter.response.defer(ephemeral=True)
        if not roles.check_is_extended_staff(inter):
            await inter.followup.send("You do not have permission to use this command.")
            return

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except (ExtensionNotFound, ExtensionNotLoaded, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed) as e:
            await inter.send(e)
            return
        await inter.send(f"{cog} reloaded.")

    @commands.slash_command(name="ip",
                            description="Replies with the server's IP. (Staff Only)")
    async def ip(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        if not roles.check_is_extended_staff(inter):
            await inter.followup.send("You do not have permission to use this command.")
            return

        ipv4: str
        ipv6: str
        ipv4 = request.urlopen('https://v4.ident.me').read().decode('utf8')
        if ipv4 != "":
            await inter.send(ipv4)
            return
        ipv6 = request.urlopen('https://v6.ident.me').read().decode('utf8')
        if ipv6 != "":
            await inter.send(ipv6)
            return
        await inter.send("Could not get IP.", ephemeral=True)
