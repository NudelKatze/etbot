from disnake import Message, ApplicationCommandInteraction
from disnake.abc import User
from disnake.ext.commands import Context

import main


def is_me(ctx: Context | Message | ApplicationCommandInteraction): return ctx.author == main.bot.user


def user_is_me(usr: User): return usr == main.bot.user


def is_not_me(ctx: Context | Message | ApplicationCommandInteraction): return not ctx.author == main.bot.user


def user_is_not_me(usr: User): return not usr == main.bot.user


def has_embed_or_attachment(msg: Message): return True if len(msg.embeds) > 0 or len(msg.attachments) > 0 else False
