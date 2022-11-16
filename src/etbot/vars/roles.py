import sys

from disnake import Role, ApplicationCommandInteraction
from disnake.ext import commands

this = sys.modules[__name__]

senator: Role | None = None
emperor: Role | None = None
viceroy: Role | None = None
palatine: Role | None = None

# not really safe since it could be called before any of the values are assigned
staff_roles: list[Role] = [emperor, viceroy, palatine]


def check_is_staff(inter: ApplicationCommandInteraction) -> bool:
    return any(role in inter.author.roles for role in staff_roles)


def initialize_testing_roles(bot: commands.Bot):
    this.senator = bot.get_guild(867738868181368852).get_role(867863600973742121)
    this.emperor = bot.get_guild(867738868181368852).get_role(942901866021408848)
    this.viceroy = bot.get_guild(867738868181368852).get_role(945664683615092756)
    this.palatine = bot.get_guild(867738868181368852).get_role(945664760869949490)
    this.staff_roles = [emperor, viceroy, palatine]


def initialize_roles(bot: commands.Bot):
    this.senator = bot.get_guild(485360396715425792).get_role(691576535781605417)
    this.emperor = bot.get_guild(485360396715425792).get_role(485512381238083585)
    this.viceroy = bot.get_guild(485360396715425792).get_role(485510055853293579)
    this.palatine = bot.get_guild(485360396715425792).get_role(485515994492698625)
    this.staff_roles = [emperor, viceroy, palatine]
