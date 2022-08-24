from disnake import Message, ApplicationCommandInteraction, Permissions
from disnake.ext import commands
from disnake.ext.commands import MessageNotFound

import utils
from vars import channels, roles, emojis, index

_history_limit: int = 100
_bill_text_length_limit: int = 1800


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Senate(bot))
    print("Loaded Senate Cog.")


async def check_bill_concluded(bill: Message) -> bool:
    concluded_emojis = [emojis.bill_closed, emojis.imperial_authority, emojis.void, emojis.withdrawn]
    return any(reaction.emoji in concluded_emojis for reaction in bill.reactions)


def check_senatorial_channels(inter: ApplicationCommandInteraction) -> bool:
    # Add special channel permissions for specific commands by making a special case for it
    allowed_channels: list[channels]
    match inter.application_command.qualified_name:
        case "edit":
            allowed_channels = [channels.get_senate()]
        case "index":
            allowed_channels = [channels.get_staff_bot_commands()]
        case _:
            allowed_channels = [channels.get_senate(),
                                channels.get_senatorial_voting(),
                                channels.get_staff_bot_commands()]
    return inter.channel in allowed_channels


async def find_bill(bot: commands.Bot, bill_number: int, history: list[Message] | None = None) -> Message | None:
    if history is None:
        history = await channels.get_senatorial_voting().history(limit=_history_limit).flatten()

    for msg in history:  # TODO make this not depend on precise spacing.
        if utils.is_me(msg):
            continue
        if roles.senator not in msg.role_mentions:
            continue

        content: list[str] = msg.content.split(' ')
        if len(content) <= 1:
            continue
        if to_int(content[1]) != bill_number:
            continue
        return msg

    if len(history) == _history_limit:
        last: Message = history[_history_limit - 1]
        history = await channels.get_senatorial_voting().history(limit=_history_limit, before=last).flatten()
        return await find_bill(bot, bill_number, history)

    raise MessageNotFound


def count_votes(bill: Message) -> str:
    yes, no = -1, -1
    one, two, three, four, five, six, seven, eight, nine, ten = -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
    abstain: int = -1
    for reaction in bill.reactions:
        match reaction.emoji:
            case emojis.yes_vote:
                yes += reaction.count
            case emojis.no_vote:
                no += reaction.count
            case emojis.one:
                one += reaction.count
            case emojis.two:
                two += reaction.count
            case emojis.three:
                three += reaction.count
            case emojis.four:
                four += reaction.count
            case emojis.five:
                five += reaction.count
            case emojis.six:
                six += reaction.count
            case emojis.seven:
                seven += reaction.count
            case emojis.eight:
                eight += reaction.count
            case emojis.nine:
                nine += reaction.count
            case emojis.ten:
                ten += reaction.count
            case emojis.abstain_vote:
                abstain += reaction.count

    vote_string: str = f"\r\n"
    if yes >= 0:
        vote_string += f"{yes} {emojis.yes_vote}"
    if one >= 0 and two >= 0:
        vote_string += f"{one} {emojis.one} | {two} {emojis.two}"
    if three >= 0:
        vote_string += f" | {three} {emojis.three}"
    if four >= 0:
        vote_string += f" | {four} {emojis.four}"
    if five >= 0:
        vote_string += f" | {five} {emojis.five}"
    if six >= 0:
        vote_string += f" | {six} {emojis.six}"
    vote_string += f" | {no} {emojis.no_vote} | {abstain} {emojis.abstain_vote}"
    return vote_string


def assemble_bill(text: str, bill_index: int, author_mention: str) -> str:
    text = f"**Bill {str(bill_index)}:** " \
           f"\r\n{text} " \
           f"\r\nBill by: {author_mention} " \
           f"\r\n{roles.senator.mention} {roles.tribune.mention}"
    return text


def assemble_amendment(text: str, bill_index: int, bill_number: int, author_mention: str) -> str:
    text = f"**Bill {str(bill_index)}:** Amendment to **Bill {str(bill_number)}** " \
           f"\r\n{text} " \
           f"\r\nBill by: {author_mention} " \
           f"\r\n{roles.senator.mention} {roles.tribune.mention}"
    return text


# removes everything but numbers from a string and converts it to an integer
def to_int(string: str) -> int | None:
    number = ''
    for c in string:
        if c.isdigit():
            number += c

    if number == '':
        return None
    return int(number)


class Senate(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name="bill",
                            description="Assembles a bill with the given text.")
    @commands.has_role("Senator")
    @commands.check(check_senatorial_channels)
    async def bill(self, inter: ApplicationCommandInteraction, text: str) -> None:
        await inter.response.defer(ephemeral=True)

        if len(text) > _bill_text_length_limit:
            await inter.send(f"Bill is too long. Max length is 1800 characters.")
            return

        # variable set up
        author_mention: str = inter.author.mention

        index.increment_index()
        text: str = assemble_bill(text, index.get_index(), author_mention)

        # send bill
        msg: Message = await channels.get_senatorial_voting().send(text)

        # add reactions
        await msg.add_reaction(emojis.yes_vote)
        await msg.add_reaction(emojis.no_vote)
        await msg.add_reaction(emojis.abstain_vote)

        await inter.send(f"Bill assembled and posted. {emojis.yes_vote}", ephemeral=True)

    @commands.slash_command(name="amendment",
                            description="Assembles an amendment with the given text and bill_number.")
    @commands.has_role("Senator")
    @commands.check(check_senatorial_channels)
    async def amendment(self, inter: ApplicationCommandInteraction, bill_number: int, text: str) -> None:
        await inter.response.defer(ephemeral=True)

        if len(text) > _bill_text_length_limit:
            await inter.send(f"Bill is too long. Max length is 1800 characters.")
            return

        # variable set up
        author: str = inter.author.mention
        command: str = f"/amendment {bill_number} {text}"

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found."
                             f"\r\n```{command}```")
            return

        index.increment_index()
        text: str = assemble_amendment(text, index.get_index(), bill_number, author)

        # send amendment
        msg: Message = await bill.reply(text)

        # add reactions
        await msg.add_reaction(emojis.yes_vote)
        await msg.add_reaction(emojis.no_vote)
        await msg.add_reaction(emojis.abstain_vote)

        await inter.send(f"Bill assembled and posted. {emojis.yes_vote}", delete_after=10)

    @commands.slash_command(name="option",
                            description="Assembles an option bill with the given text.")
    @commands.has_role("Senator")
    @commands.check(check_senatorial_channels)
    async def option(self, inter: ApplicationCommandInteraction, options: int, text: str) -> None:
        await inter.response.defer(ephemeral=True)

        if len(text) > _bill_text_length_limit:
            await inter.send(f"Bill is too long. Max length is 1800 characters.")
            return

        # variable set up
        author: str = inter.author.mention
        command: str = f"/amendment {options} {text}"

        # option amount check
        if options < 2:
            await inter.send(f"Too few options given. {author}"
                             f"\r\n```{command}```")
            return
        if options > 10:
            await inter.send(f"Too many options given. {author}"
                             f"\r\n```{command}```")
            return

        index.increment_index()
        text: str = assemble_bill(text, index.get_index(), author)

        msg: Message = await channels.get_senatorial_voting().send(text)

        # add reactions
        for i in range(0, options):
            await msg.add_reaction(emojis.options[i])
        await msg.add_reaction(emojis.no_vote)
        await msg.add_reaction(emojis.abstain_vote)

        await inter.send(f"Bill assembled and posted. {emojis.yes_vote}", delete_after=10)

    @commands.slash_command(name="amendmentoption",
                            description="Assembles an option amendment with the given text and bill.")
    @commands.has_role("Senator")
    @commands.check(check_senatorial_channels)
    async def amendment_option(self, inter: ApplicationCommandInteraction, bill_number: int, options: int,
                               text: str) -> None:
        await inter.response.defer(ephemeral=True)

        if len(text) > _bill_text_length_limit:
            await inter.send(f"Bill is too long. Max length is 1800 characters.")
            return

        # variable set up
        author: str = inter.author.mention
        command: str = f"/amendment {bill_number} {options} {text}"

        # option amount check
        if options < 2:
            await inter.send(f"Too few options given. {author}"
                             f"\r\n```{command}```")
            return
        if options > 10:
            await inter.send(f"Too many options given. {author}"
                             f"\r\n```{command}```")
            return

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author}"
                             f"\r\n```{command}```")
            return

        index.increment_index()
        text: str = assemble_amendment(text, index.get_index(), bill_number, author)

        msg: Message = await bill.reply(text)

        # add reactions
        for i in range(0, options):
            await msg.add_reaction(emojis.options[i])
        await msg.add_reaction(emojis.no_vote)
        await msg.add_reaction(emojis.abstain_vote)

        await inter.send(f"Bill assembled and posted. {emojis.yes_vote}", delete_after=10)

    @commands.slash_command(name="edit",
                            description="Edits the bill with the given number.")
    @commands.has_role("Senator")
    @commands.check(check_senatorial_channels)
    async def edit(self, inter: ApplicationCommandInteraction, bill_index: int, text: str) -> None:
        await inter.response.defer(ephemeral=True)

        if len(text) > _bill_text_length_limit:
            await inter.send(f"Bill is too long. Max length is 1800 characters.")
            return

        # variable set up
        author: str = inter.author.mention
        command: str = f"/amendment {bill_index} {text}"

        # check that bill_number is valid
        if bill_index > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        is_amendment = False

        # search bill by index
        try:
            original: Message | None = await find_bill(self.bot, bill_index)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if await check_bill_concluded(original):
            await inter.send(f"You cannot edit an already closed bill. {author}"
                             f"\r\n```{command}```")
            return

        content: list[str] | None = original.content.split(' ')
        bill_author: str | None = content[len(content) - 3]
        bill_number: str | None = None
        if content[2] == 'Amendment' and content[3] == 'to':
            bill_number = content[5]
            bill_number = bill_number.strip('*')
            is_amendment = True

        # clean changes
        changes = content[:len(content) - 4]
        changes_string: str = ''
        for element in changes:
            changes_string += f"{element} "

        # error message
        if author != bill_author:
            await inter.send(f"This is not your Bill. {author}"
                             f"\r\n```{command}```")
            return

        # assemble new message
        if is_amendment:
            content_string: str = assemble_amendment(text, bill_index, int(bill_number), author)
        else:
            content_string: str = assemble_bill(text, bill_index, author)

        # edit command
        if original is not None:
            await original.edit(content=content_string)
            await channels.get_senate().send(f"Previous wording: "
                                             f"\r\n```{changes_string}```"
                                             f"\r\nSuccess. {author}")
            await inter.send(f"Bill assembled and posted. {emojis.yes_vote}", delete_after=10)
        else:
            await inter.send("A bug seems to have crept itself into the code.", delete_after=10)

    @commands.slash_command(name="index",
                            description="Overrides the saved bill index.",
                            default_member_permissions=Permissions(administrator=True))
    @commands.check(check_senatorial_channels)
    async def set_index(self, inter: ApplicationCommandInteraction, new_index: int):
        index.set_index(new_index)
        await inter.send(f"Index set to {new_index}.", delete_after=60)

    @commands.slash_command(name="pass",
                            description="Passes the bill with the given number.")
    @commands.has_role("Emperor")
    @commands.check(check_senatorial_channels)
    async def pass_bill(self, inter: ApplicationCommandInteraction, bill_number: int, comment: str = '') -> None:
        await inter.response.defer(ephemeral=True)

        # variable set up
        author_mention: str = inter.author.mention
        command: str = f"/pass {bill_number}{(' ' + comment) if comment != '' else ''}"
        if comment != '':
            comment += ' '

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author_mention}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author_mention}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if await check_bill_concluded(bill):
            await inter.send(f"Bill has already been concluded. {author_mention}"
                             f"\r\n```{command}```")
            return

        await bill.add_reaction(emojis.bill_closed)

        content: list[str] = bill.content.split(' ')
        await bill.reply(f"Bill {bill_number} passes."
                         f"\n{comment}{content[len(content) - 3]}")

        # clean changes
        wording: str = ''
        for element in content[:len(content) - 4]:
            wording += f"{element} "

        # count votes
        wording += count_votes(bill)
        await channels.get_passed_bills().send(wording)

        await inter.send(f"Bill marked and posted to {channels.get_passed_bills().mention}.",
                         ephemeral=True,
                         delete_after=10)

    @commands.slash_command(name="fail",
                            description="Fails the bill with the given number.")
    @commands.has_role("Emperor")
    @commands.check(check_senatorial_channels)
    async def fail(self, inter: ApplicationCommandInteraction, bill_number: int, comment: str = '') -> None:
        await inter.response.defer(ephemeral=True)

        # variable set up
        author_mention: str = inter.author.mention
        command: str = f"/fail {bill_number}{(' ' + comment) if comment != '' else ''}"
        if comment != '':
            comment += ' '

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author_mention}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author_mention}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if await check_bill_concluded(bill):
            await inter.send(f"Bill has already been concluded. {author_mention}"
                             f"\r\n```{command}```")
            return

        await bill.add_reaction(emojis.bill_closed)

        content: list[str] = bill.content.split(' ')
        await bill.reply(f"Bill {bill_number} does not pass."
                         f"\n{comment}{content[len(content) - 3]}")

        await inter.send(f"Bill marked as failed.", delete_after=10)

    @commands.slash_command(name="veto",
                            description="Vetoes the bill with the given number.", )
    @commands.has_role("Emperor")
    @commands.check(check_senatorial_channels)
    async def veto(self, inter: ApplicationCommandInteraction, bill_number: int, comment: str = '') -> None:
        await inter.response.defer(ephemeral=True)

        # variable set up
        author: str = inter.author.mention
        command: str = f"/veto {bill_number}{(' ' + comment) if comment != '' else ''}"
        if comment != '':
            comment += ' '

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if await check_bill_concluded(bill):
            await inter.send(f"Bill has already been concluded. {author}"
                             f"\r\n```{command}```")
            return

        await bill.add_reaction(emojis.imperial_authority)

        content: list[str] = bill.content.split(' ')
        await bill.reply(f"Bill {bill_number} is vetoed."
                         f"\r\n{comment}{content[len(content) - 3]}")

        await inter.send(f"Bill marked as vetoed.", delete_after=10)

    @commands.slash_command(name="forcethrough",
                            description="Forces the bill with the given number through.")
    @commands.has_role("Emperor")
    @commands.check(check_senatorial_channels)
    async def forcethrough(self, inter: ApplicationCommandInteraction, bill_number: int, comment: str = '') -> None:
        await inter.response.defer(ephemeral=True)

        # variable set up
        author: str = inter.author.mention
        command: str = f"/forcethrough {bill_number}{(' ' + comment) if comment != '' else ''}"
        if comment != '':
            comment += ' '

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if await check_bill_concluded(bill):
            await inter.send(f"Bill has already been concluded. {author}"
                             f"\r\n```{command}```")
            return

        await bill.add_reaction(emojis.imperial_mandate)

        content: list[str] = bill.content.split(' ')
        await bill.reply(f"Bill {bill_number} is forced through."
                         f"\r\n{comment}{content[len(content) - 3]}")

        await inter.send(f"Bill marked as forced through.", delete_after=10)

    @commands.slash_command(name="void",
                            description="Voids the bill with the given number.")
    @commands.check(roles.check_is_staff)
    @commands.check(check_senatorial_channels)
    async def void(self, inter: ApplicationCommandInteraction, bill_number: int, comment: str = '') -> None:
        await inter.response.defer(ephemeral=True)

        # variable set up
        author: str = inter.author.mention
        command: str = f"/void {bill_number}{(' ' + comment) if comment != '' else ''}"
        if comment != '':
            comment += ' '

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if await check_bill_concluded(bill):
            await inter.send(f"Bill has already been concluded. {author}"
                             f"\r\n```{command}```")
            return

        await bill.add_reaction(emojis.void)

        content: list[str] = bill.content.split(' ')
        await bill.reply(f"Bill {bill_number} is void."
                         f"\r\n{comment} {content[len(content) - 3]}")

        await inter.send(f"Bill marked as void.", delete_after=10)

    @commands.slash_command(name="unvoid",
                            description="Unvoids the bill with the given number.")
    @commands.check(roles.check_is_staff)
    @commands.check(check_senatorial_channels)
    async def unvoid(self, inter: ApplicationCommandInteraction, bill_number: int, comment: str = '') -> None:
        await inter.response.defer(ephemeral=True)

        # variable set up
        author: str = inter.author.mention
        command: str = f"/unvoid {bill_number}{(' ' + comment) if comment != '' else ''}"
        if comment != '':
            comment += ' '

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if not any(reaction.emoji is emojis.void for reaction in bill.reactions):
            await inter.send(f"Bill isn't void. {author}"
                             f"\r\n```{command}```")
            return

        await bill.remove_reaction(emojis.void, self.bot.user)

        content: list[str] = bill.content.split(' ')
        await bill.reply(f"Bill {bill_number} is unvoided."
                         f"\r\n{comment} {content[len(content) - 3]}")

        await inter.send(f"Bill unmarked as void.", delete_after=10)

    @commands.slash_command(name="withdraw",
                            description="Withdraws the bill with the given number.")
    @commands.check(check_senatorial_channels)
    async def withdraw(self, inter: ApplicationCommandInteraction, bill_number: int, comment: str = '') -> None:
        await inter.response.defer(ephemeral=True)

        # variable set up
        author: str = inter.author.mention
        command: str = f"/withdraw {bill_number}{(' ' + comment) if comment != '' else ''}"
        if comment != '':
            comment += ' '

        # check that bill_number is valid
        if bill_number > index.get_index():
            await inter.send(f"No valid bill number was given. {author}"
                             f"\r\n```{command}```")
            return

        try:
            bill = await find_bill(self.bot, bill_number)
        except MessageNotFound:
            await inter.send(f"No bill with that index found. {author}"
                             f"\r\n```{command}```")
            return
        # check that the bill isn't closed already
        if await check_bill_concluded(bill):
            await inter.send(f"Bill has already been concluded. {author}"
                             f"\r\n```{command}```")
            return

        content: list[str] | None = bill.content.split(' ')
        bill_author: str | None = content[len(content) - 3]
        # error message
        if author != bill_author:
            await inter.send(f"This is not your Bill. {author}"
                             f"\r\n```{command}```")
            return

        await bill.add_reaction(emojis.withdrawn)

        content: list[str] = bill.content.split(' ')
        await bill.reply(f"Bill {bill_number} is withdrawn."
                         f"\r\n{comment}{content[len(content) - 3]}")

        await inter.send(f"Bill marked as withdrawn.", delete_after=10)
