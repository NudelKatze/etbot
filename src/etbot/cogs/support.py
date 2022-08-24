from disnake import Message, ApplicationCommandInteraction
from disnake.ext import commands

from vars import messages


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Support(bot))
    print("Loaded Support Cog.")


class Support(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name="support",
                            description="Responds with the support FAQ.")
    async def support(self, inter: ApplicationCommandInteraction) -> None:
        msg: Message = await messages.get_support()
        await inter.send(msg.content)
