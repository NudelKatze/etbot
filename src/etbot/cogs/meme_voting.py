import logging
from warnings import catch_warnings

from disnake import Message
from disnake.ext import commands

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
    await message.add_reaction(emojis.question)


async def remove_votes_on_meme(message: Message):
    if not utils.has_embed_or_attachment(message):
        logging.debug(f"No embed or attachment found in message with ID {message.id}")
        return

    await message.clear_reaction(emojis.yes_vote)
    await message.clear_reaction(emojis.no_vote)
    await message.clear_reaction(emojis.recycle)
    await message.clear_reaction(emojis.ear_with_hearing_aid)
    await message.clear_reaction(emojis.question)


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

        meme_channels = []
        delete_noise_channels = []
        try:
            meme_channels = [channels.get_memes(), channels.get_religious_memes()]
            delete_noise_channels = [channels.get_out_of_context_screenshots()]
        except Exception as e:
            logging.exception(e)

        # meme voting
        if message.channel in meme_channels:
            await vote_on_meme(message)
        # delete noise
        if message.channel in delete_noise_channels:
            await delete_noise(message)

    @commands.command(name="meme", aliases=["Meme"],
                      brief="Adds the meme voting reactions to the referenced message.",
                      help="Adds the meme voting reactions to the referenced message.")
    async def meme(self, ctx: commands.Context):
        # deletes meme command
        await ctx.message.delete()

        # variable set up
        msg: Message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

        # add reactions
        await vote_on_meme(msg)

    @commands.command(name="unmeme", aliases=["Unmeme"],
                      brief="From the meme voting reactions from the referenced message.",
                      help="Removes the meme voting reactions from the referenced message.")
    async def unmeme(self, ctx: commands.Context):
        # deletes meme command
        await ctx.message.delete()

        # variable set up
        msg: Message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

        # add reactions
        await remove_votes_on_meme(msg)

    @commands.command(name="vote", aliases=["Vote"],
                      brief="Assembles a vote with the given text.",
                      help="Assembles a vote with the given text. \n"
                           "Including adding the reactions in the correct order.")
    async def vote(self, ctx: commands.Context):
        # deletes vote command
        await ctx.message.delete()

        # variable set up
        msg: Message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

        # add reactions
        await msg.add_reaction(emojis.yes_vote)
        await msg.add_reaction(emojis.no_vote)
        await msg.add_reaction(emojis.abstain_vote)
