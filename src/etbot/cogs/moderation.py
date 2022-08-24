import datetime
import uuid

from disnake import Message, Member, User, Guild, Thread, File, NotFound, ApplicationCommandInteraction, Permissions
from disnake.abc import GuildChannel
from disnake.ext import commands

from vars import channels, roles, warnings


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))
    print("Loaded Moderation Cog.")


async def make_message_writeable(message: Message) -> str:
    """
    Makes a message writeable.
    """
    txt: str = f"Author: {message.author.name}#{message.author.discriminator}\n" \
               f"Created at: {message.created_at}\n"

    if message.reference is not None:
        try:
            txt += f"Replying to: {(await message.channel.fetch_message(message.reference.message_id)).clean_content}\n"
        except NotFound:
            txt += f"Replying to: {message.reference.message_id}\n"

    if len(message.attachments) > 0:
        txt += f"Attachments: {message.attachments}\n"
    txt += f"Content: \n" \
           f"{message.clean_content}\n\n\n"

    return txt


async def messages_by_user_in_guild(guild: Guild, user: User | Member) -> int:
    """
    Returns a list of messages sent by a user in a guild.
    """
    counter = 0
    for channel in guild.text_channels:
        counter += await messages_by_user_in_channel(channel, user)

    return counter


async def messages_by_user_in_channel(channel: GuildChannel | Thread, user: User | Member) -> int:
    """
    Returns the number of messages sent by a user in a channel.
    """
    counter = 0
    with open(f"{user.name}.txt", "a", encoding="utf8") as file:
        history = await channel.history(limit=100).flatten()
        for message in history:
            if message.author == user:
                counter += 1
                file.write(f"{message.id}\n{message.created_at}\n{message.clean_content}\n\n\n")
        while not len(history) < 100:
            history = await channel.history(limit=100, before=history[-1]).flatten()
            for message in history:
                if message.author == user:
                    counter += 1
                    file.write(f"{message.id}\n{message.created_at}\n{message.clean_content}\n\n\n")

    return counter


class Moderation(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name="save",
        description="Saves all the messages sent by the given user.",
        default_member_permissions=Permissions(administrator=True)
    )
    async def save_messages(self, inter: ApplicationCommandInteraction, user: User | Member) -> None:
        """
        Saves all messages from a user on a server.
        """
        await inter.response.defer()

        if user is None:
            await inter.send("User not found.")
            return

        with open(f"transcripts/{user.name}.txt", "w", encoding="utf8") as file:
            file.write(f"{user.name}'s messages as of {datetime.datetime.utcnow()}:\n\n")

        counter = await messages_by_user_in_guild(inter.guild, user)

        await inter.send(f"Saved {counter} messages.")

    @commands.slash_command(
        name="purge",
        description="Purges the amount of messages specified",
        default_member_permissions=Permissions(manage_messages=True)
    )
    async def purge_messages(self, inter: ApplicationCommandInteraction, amount: commands.Range[1, ...]) -> None:
        """
        Purges the amount of messages specified.
        """
        await inter.response.defer()

        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")
            async for message in inter.channel.history(limit=amount):
                counter += 1
                file.write(await make_message_writeable(message))

        await inter.channel.purge(limit=counter)  # TODO check if purging and then writing to file works
        await inter.send(f"Purged {counter} messages.", ephemeral=True)
        await channels.get_bot_log().send(f"Purged {counter} messages from {inter.channel.name}.", file=File(filename))
        # os.remove(filename)

    @commands.slash_command(
        name="purgeafter",
        description="Purges the amount of messages (no amount -> all) after the referenced message.",
        default_member_permissions=Permissions(manage_messages=True)
    )
    async def purge_after(self, inter: ApplicationCommandInteraction, reference: Message,
                          amount: commands.Range[1, ...] | None = None) -> None:
        """
        Purges all messages after the referenced message.
        """
        await inter.response.defer()

        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")

            history = await inter.channel.history(limit=100 if amount is None else amount, after=reference).flatten()
            for message in history:
                counter += 1
                file.write(await make_message_writeable(message))

            while len(history) == 100 and amount is None:
                history = await inter.channel.history(limit=100, before=history[-1], after=reference).flatten()
                for message in history:
                    counter += 1
                    file.write(await make_message_writeable(message))

        await inter.channel.purge(limit=counter, after=reference, oldest_first=True)
        await inter.send(f"Purged {counter} messages.", ephemeral=True)
        await channels.get_bot_log().send(f"Purged {counter} messages from {inter.channel.name}.", file=File(filename))
        # os.remove(filename)

    @commands.slash_command(
        name="purgebefore",
        description="Purges the amount of messages specified",
        default_member_permissions=Permissions(manage_messages=True)
    )
    async def purge_before(self, inter: ApplicationCommandInteraction, amount: commands.Range[1, ...],
                           reference: Message) -> None:
        """
        Purges the amount of messages specified before the referenced message.
        """
        await inter.response.defer()

        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")

            async for message in inter.channel.history(limit=amount, before=reference):
                counter += 1
                file.write(await make_message_writeable(message))

        await inter.channel.purge(limit=counter, before=reference)
        await inter.send(f"Purged {counter} messages.", ephemeral=True)
        await channels.get_bot_log().send(f"Purged {counter} messages from {inter.channel.name}.", file=File(filename))
        # os.remove(filename)

    @commands.slash_command(
        name="warn",
        description="Warns a user.",
        default_member_permissions=Permissions(ban_members=True)
    )
    async def warn(self, inter: ApplicationCommandInteraction, user: User | Member, reason: str) -> None:
        """
        Warns a user.
        """
        await inter.response.defer()

        given: datetime.datetime = datetime.datetime.utcnow()
        expires: datetime.datetime = warnings.generate_expiration(user)
        warning: warnings.DiscordWarning = warnings.DiscordWarning(user, reason, inter.author, given, expires)
        warning_amount: int = warnings.add_warning(warning)

        await user.send(f"You have been warned in {inter.guild.name} for: "
                        f"\n{reason}")
        await inter.send(f"Warned {user.name}.")
        await channels.get_moderation_log().send(f"{user.name} has been warned for {reason}."
                                                 f"\nWarnings: {warning_amount} {roles.palatine.mention if warning_amount >= 3 else ''}")

    @commands.slash_command(
        name="delwarn",
        description="Deletes a warning.",
        default_member_permissions=Permissions(ban_members=True)
    )
    async def delwarn(self, inter: ApplicationCommandInteraction, id: str) -> None:
        """
        Deletes a warning.
        """
        await inter.response.defer()

        id: uuid.UUID = uuid.UUID(id)

        try:
            warning: warnings.DiscordWarning = warnings.get_warning(id)
        except Exception:
            await inter.send(f"Warning with ID \"{id}\" not found.")
            return

        if warning.user == inter.author:
            await inter.send("You cannot delete your own warning.")
            return

        warnings.delete_warning(warning)
        await inter.send("Warning deleted.")

    # TODO make warnings and my_warnings into subcommands
    @commands.slash_command(
        name="warnings",
        description="Returns all warnings for the user.",
        default_member_permissions=Permissions(ban_members=True)
    )
    async def warnings(self, inter: ApplicationCommandInteraction, user: User | Member) -> None:
        """
        Returns all warnings for a user
        """
        await inter.response.defer()

        user_warnings = warnings.get_warnings_by_user(user)

        if not user_warnings:
            await inter.send(f"{user.name} has no warnings.")
            return

        warnings_message: str = f"{user.name} has {len(user_warnings)} warnings:"
        for warning in user_warnings:
            warnings_message += f"\n{warning}" \
                                f"\n**--------------------------------------------------**"

        await inter.send(warnings_message)

    @commands.slash_command(
        name="allwarnings",
        description="Returns all warnings.",
        default_member_permissions=Permissions(ban_members=True)
    )
    async def all_warnings(self, inter: ApplicationCommandInteraction) -> None:
        """
        Returns all warnings.
        """
        await inter.response.defer()

        warnings_message: str = "All warnings:"
        for warning in warnings.get_all_warnings():
            warnings_message += f"\n{warning}" \
                                f"\n**--------------------------------------------------**"

        await inter.send(warnings_message)

    @commands.slash_command(
        name="mywarnings",
        description="Returns all of your warnings."
    )
    async def my_warnings(self, inter: ApplicationCommandInteraction) -> None:
        """
        Returns all warnings for the user.
        """
        await inter.response.defer()

        user_warnings = warnings.get_warnings_by_user(inter.author)

        if not user_warnings:
            await inter.send(f"You has no warnings.")
            return

        warnings_message: str = f"{inter.author.name} has {len(user_warnings)} warnings:"
        for warning in user_warnings:
            warnings_message += f"\n{warning}" \
                                f"\n**--------------------------------------------------**"

        await inter.send(warnings_message, ephemeral=True)
