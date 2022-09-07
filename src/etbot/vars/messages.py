import sys

from disnake import Message

from vars import channels

this = sys.modules[__name__]

_support_id: int | None = None
_minecraft_info_id: int | None = None


async def get_support() -> Message:
    return await channels.get_support().fetch_message(_support_id)


async def get_minecraft_info() -> Message:
    return await channels.get_minecraft().fetch_message(_minecraft_info_id)


def initialize_testing_messages():
    this._support_id = 941391031184818216
    this._minecraft_info_id = 1017106100350357674


def initialize_messages():
    this._support_id = 556837149924917249
    this._minecraft_info_id = 692403470074118304
