import datetime
import os
import uuid

from disnake import Message, Member, User, Guild, Thread, File, NotFound, ApplicationCommandInteraction, Permissions, \
    TextChannel, VoiceChannel, SelectOption, Embed
from disnake.abc import GuildChannel
from disnake.ext.commands import Cog, Bot, slash_command, command, Context
from disnake.ui import View, Select, user_select, string_select

from vars import channels, roles, warnings
from vars.warnings import DiscordWarning


def setup(bot: Bot) -> None:
    if not os.path.isdir("transcripts/"):
        os.mkdir("transcripts/")

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


class UserWarningView(View):

    def __init__(self):
        self.users: list[User | Member] = []
        self.options: list[SelectOption] = []
        super().__init__()

    @user_select(placeholder="Select a user", row=0)
    async def select_callback(self, select: Select, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()
        user: User | Member = select.values[0]
        user_warnings: list[DiscordWarning] | None = warnings.get_warnings_by_user(user)

        embed: Embed = Embed(
            title=f"{user.name}#{user.discriminator} has {0 if user_warnings is None or len(user_warnings) == 0 else len(user_warnings)} Warnings",
            color=0x00ff00 if user_warnings is None or len(user_warnings) == 0 else 0xff0000,
            timestamp=interaction.created_at)
        embed.set_author(name=user.name, icon_url=user.avatar.url)

        if user_warnings is not None:
            for warning in user_warnings:
                embed.add_field(name=f"ID: {warning.id}",
                                value=f"{warning.reason}\n"
                                      f"Created at {warning.given}\n"
                                      f"Expires at {warning.expires}",
                                inline=False)

        await interaction.edit_original_message(view=self, embed=embed)


class AllWarningView(View):
    options: list[SelectOption] = [
        SelectOption(label="Warnings", value="warnings", description="List of all Users that currently hold warnings."),
        SelectOption(label="Old Warnings", value="old_warnings",
                     description="[EXPERIMENTAL] List of all Users that have had warnings in the past. [EXPERIMENTAL]"),
    ]

    def __init__(self):
        super().__init__()

    @string_select(placeholder="Warnings", options=options)
    async def select_callback(self, select: Select, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()
        warnings_dict: dict = {}

        if select.values[0] == "warnings":
            warnings_dict = warnings._warnings
        elif select.values[0] == "old_warnings":
            warnings_dict = warnings._old_warnings
        else:
            return

        embed: Embed = Embed(
            title=f"All Warnings" if select.values[0] == "warnings" else f"Old Warnings",
            color=0xff0000 if select.values[0] == "warnings" else 0xff8000,
            timestamp=interaction.created_at)

        for user_id, user_warnings in warnings_dict.items():
            if len(user_warnings) == 0:
                continue
            user: User | Member = await interaction.guild.getch_member(int(user_id))
            embed.add_field(name=f"{user.name}#{user.discriminator}",
                            value=f"{len(user_warnings)} Warnings",
                            inline=False)

        await interaction.edit_original_message(view=self, embed=embed)


class Moderation(Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command(name="save",
                   description="Saves all the messages sent by the given user.",
                   default_member_permissions=Permissions(administrator=True))
    async def save_messages(self, inter: ApplicationCommandInteraction, user: User | Member) -> None:
        """
        Saves all messages from a user on a server.
        """
        await inter.response.defer(ephemeral=True)

        if user is None:
            await inter.send("User not found.")
            return

        with open(f"transcripts/{user.name}.txt", "w", encoding="utf8") as file:
            file.write(f"{user.name}'s messages as of {datetime.datetime.utcnow()}:\n\n")

        counter = await messages_by_user_in_guild(inter.guild, user)

        await inter.send(f"Saved {counter} messages.")

    @command(name="purge",
             description="Purges the amount of messages specified",
             default_member_permissions=Permissions(manage_messages=True))
    async def purge_messages(self, ctx: Context, amount: int) -> None:
        """
        Purges the amount of messages specified.
        """
        await ctx.message.delete()

        if amount < 0:
            await ctx.send("You can't purge negative messages.")
            return

        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")
            async for message in ctx.channel.history(limit=amount):
                counter += 1
                file.write(await make_message_writeable(message))

        await ctx.channel.purge(limit=counter)  # TODO check if purging and then writing to file works
        await ctx.send(f"Purged {counter} messages.")
        await channels.get_bot_log().send(f"Purged {counter} messages from {ctx.channel.name}.", file=File(filename))

    @command(name="purgeafter",
             description="Purges the amount of messages (no amount -> all) after the referenced message.",
             default_member_permissions=Permissions(manage_messages=True))
    async def purge_after(self, ctx: Context, amount: int | None) -> None:
        """
        Purges the amount of messages specified after the referenced message.
        """
        await ctx.message.delete()

        if amount is not None and amount < 0:
            await ctx.send("Amount must be positive.")
            return
        if ctx.message.reference is None:
            await ctx.send("You need to reference a message.")
            return

        reference: Message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")

            history = await ctx.channel.history(limit=100 if amount is None else amount, after=reference).flatten()
            for message in history:
                counter += 1
                file.write(await make_message_writeable(message))

            while len(history) == 100 and amount is None:
                history = await ctx.channel.history(limit=100, before=history[-1], after=reference).flatten()
                for message in history:
                    counter += 1
                    file.write(await make_message_writeable(message))

        await ctx.channel.purge(limit=counter, after=reference, oldest_first=True)
        await ctx.send(f"Purged {counter} messages.")
        await channels.get_bot_log().send(f"Purged {counter} messages from {ctx.channel.name}.", file=File(filename))

    @command(name="purgebefore",
             description="Purges the amount of messages specified before the referenced message",
             default_member_permissions=Permissions(manage_messages=True))
    async def purge_before(self, ctx: Context, amount: int) -> None:
        """
        Purges the amount of messages specified before the referenced message.
        """
        await ctx.message.delete()

        if amount < 0:
            await ctx.send("Amount must be positive.")
            return
        if ctx.message.reference is None:
            await ctx.send("You must reference a message.")
            return

        reference: Message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")

            async for message in ctx.channel.history(limit=amount, before=reference):
                counter += 1
                file.write(await make_message_writeable(message))

        await ctx.channel.purge(limit=counter, before=reference)
        await ctx.send(f"Purged {counter} messages.")
        await channels.get_bot_log().send(f"Purged {counter} messages from {ctx.channel.name}.", file=File(filename))

    @command(name="purgeuserchannel", aliases=["purgeUserChannel"],
             description="Purges the amount of messages specified (no amount -> all) from the given user in this channel.",
             default_member_permissions=Permissions(manage_messages=True))
    async def purge_user_channel(self, ctx: Context, user: User | Member,
                                 amount: int | None = None) -> None:
        """
        Purges the amount of messages specified (no amount -> all) from the given user in this channel.
        """
        await ctx.message.delete()

        if amount is not None and amount < 0:
            await ctx.send("Amount must be positive.")
            return

        if user is None:
            await ctx.send("User not found.")
            return

        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")

            while amount is None or counter < amount:
                async for message in ctx.channel.history(limit=amount):
                    if message.author == user:
                        counter += 1
                        file.write(await make_message_writeable(message))
                    if counter == amount:
                        break
                if amount is None:
                    break

        await ctx.channel.purge(limit=counter, check=lambda m: m.author == user)
        await ctx.send(f"Purged {counter} messages.")
        await channels.get_bot_log().send(f"Purged {counter} messages from {ctx.channel.name}.", file=File(filename))

    @command(name="purgeuserall", aliases=["purgeUserAll"],
             description="Purges all messages from the given user in all channels. VERY SLOW!",
             default_member_permissions=Permissions(manage_messages=True))
    async def purge_user_all(self, ctx: Context, user: User | Member) -> None:
        """
        Purges all messages from the given user in all channels. VERY SLOW!
        """
        await ctx.message.delete()

        if user is None:
            await ctx.send("User not found.")
            return

        counter = 0
        time = f"{datetime.datetime.utcnow()}"
        filename = f"transcripts/{uuid.uuid4()}.txt"

        with open(filename, "w", encoding="utf8") as file:
            file.write(f"{time}:\n\n")

            for channel in ctx.guild.channels:
                if not isinstance(channel, TextChannel | VoiceChannel | Thread):
                    continue
                file.write(f"#{channel.name}:\n")
                async for message in channel.history(limit=None):
                    if message.author == user:
                        counter += 1
                        file.write(await make_message_writeable(message))
                        await message.delete()
                await channel.purge(limit=None, check=lambda m: m.author == user)

        await ctx.send(f"Purged {counter} messages.")
        await channels.get_bot_log().send(f"Purged {counter} messages from {ctx.guild.name}.", file=File(filename))

    @slash_command(name="warn",
                   description="Warns a user.",
                   default_member_permissions=Permissions(ban_members=True))
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

    @slash_command(name="delwarn",
                   description="Deletes a warning.",
                   default_member_permissions=Permissions(ban_members=True))
    async def delwarn(self, inter: ApplicationCommandInteraction, warning_id: str) -> None:
        """
        Deletes a warning.
        """
        await inter.response.defer()

        warning_id: uuid.UUID = uuid.UUID(warning_id)

        try:
            warning: warnings.DiscordWarning = warnings.get_warning(warning_id)
        except Exception:
            await inter.send(f"Warning with ID \"{warning_id}\" not found.")
            return

        if warning.user == inter.author:
            await inter.send("You cannot delete your own warning.")
            return

        warnings.delete_warning(warning)
        await inter.send("Warning deleted.")

    # TODO make warnings and my_warnings into subcommands
    @slash_command(name="warnings",
                   description="Returns all warnings for the user.",
                   default_member_permissions=Permissions(ban_members=True))
    async def warnings(self, inter: ApplicationCommandInteraction) -> None:
        """
        Returns all warnings for a user
        """
        await inter.response.defer()

        warnings_view: UserWarningView = UserWarningView()

        await inter.send(view=warnings_view)

    @slash_command(name="allwarnings",
                   description="Returns all warnings.",
                   default_member_permissions=Permissions(ban_members=True))
    async def all_warnings(self, inter: ApplicationCommandInteraction) -> None:
        """
        Returns all warnings.
        """
        await inter.response.defer()

        users: list[User | Member] = []

        for key, value in warnings._warnings.items():
            if len(value) > 0:
                users.append(await inter.guild.getch_member(int(key)))

        warnings_view: AllWarningView = AllWarningView()

        await inter.send(view=warnings_view)

    @slash_command(name="mywarnings",
                   description="Returns all of your warnings.")
    async def my_warnings(self, inter: ApplicationCommandInteraction) -> None:
        """
        Returns all warnings for the user.
        """
        await inter.response.defer()

        user_warnings = warnings.get_warnings_by_user(inter.author)

        embed: Embed = Embed(
            title=f"{inter.author.name}#{inter.author.discriminator} has {0 if user_warnings is None or len(user_warnings) == 0 else len(user_warnings)} Warnings",
            color=0x00ff00 if user_warnings is None or len(user_warnings) == 0 else 0xff0000,
            timestamp=inter.created_at)
        embed.set_author(name=inter.author.name, icon_url=inter.author.avatar.url)

        if user_warnings is not None:
            for warning in user_warnings:
                embed.add_field(name=f"ID: {warning.id}",
                                value=f"{warning.reason}\n"
                                      f"Created at {warning.given}\n"
                                      f"Expires at {warning.expires}",
                                inline=False)

        await inter.send(embed=embed, ephemeral=True)
