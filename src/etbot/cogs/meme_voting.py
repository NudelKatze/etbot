import logging

from disnake import Message, ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import Param

import utils
from vars import channels, emojis


def setup(bot):
    bot.add_cog(MemeVoting(bot))
    print("Loaded MemeVoting Cog.")


async def vote_on_meme(message: Message):
    if not utils.has_embed_or_attachment(message):
        logging.debug(f"No embed or attachment found in message with ID {message.id}")
        return

    await message.add_reaction(emojis.yes_vote)
    await message.add_reaction(emojis.no_vote)
    await message.add_reaction(emojis.recycle)
    await message.add_reaction(emojis.ear_with_hearing_aid)


async def delete_noise(message: Message):
    if utils.has_embed_or_attachment(message):
        logging.debug(f"Embed or attachment found in message with ID {message.id} in channel {message.channel.name}.")
        return

    await message.delete(delay=60 * 60)  # delete message after 1 hour


class MemeVoting(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # no reaction if bot
        if message.author.bot:
            return

        meme_channels = [channels.get_memes(), channels.get_religious_memes()]
        delete_noise_channels = [channels.get_out_of_context_screenshots()]

        # meme voting
        if message.channel in meme_channels:
            await vote_on_meme(message)
        # delete noise
        if message.channel in delete_noise_channels:
            await delete_noise(message)

    @commands.slash_command(name="meme",
                            description="Adds the meme voting reactions to the referenced message.")
    async def meme(self, inter: ApplicationCommandInteraction,
                   message_id: int = Param(gt=0, description="ID of the message to react to")) -> None:
        # deletes meme command
        await inter.response.defer(ephemeral=True)

        # variable set up
        msg: Message = await inter.channel.fetch_message(message_id)

        # add reactions
        await vote_on_meme(msg)

    @commands.slash_command(name="vote",
                            description="Assembles a vote with the given text.")
    async def vote(self, inter: ApplicationCommandInteraction,
                   message_id: int = Param(gt=0, description="ID of the message to react to")) -> None:
        # deletes vote command
        await inter.response.defer()

        # variable set up
        msg: Message = await inter.channel.fetch_message(message_id)

        # add reactions
        await msg.add_reaction(emojis.yes_vote)
        await msg.add_reaction(emojis.no_vote)
        await msg.add_reaction(emojis.abstain_vote)
