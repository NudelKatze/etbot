import datetime
import json
import uuid

from disnake import User, Member
from disnake.ext import commands

_warnings: dict = {}
_old_warnings: dict = {}


class DiscordWarning:
    """
    A warning.
    """

    def __init__(self, user: User | Member, reason: str, moderator: User | Member, given: datetime.datetime,
                 expires: datetime.datetime, id: uuid.UUID = None):
        self.id = uuid.uuid4() if id is None else id
        self.user: User = user
        self.reason: str = reason
        self.moderator: User = moderator
        self.given: datetime.datetime = given
        self.expires: datetime.datetime = expires

    def __str__(self):
        return f"ID: **{self.id}**" \
               f"\nUser: **{self.user.name}**" \
               f"\nExpires: **{self.expires.strftime('%Y-%m-%d %H:%M')}**" \
               f"\n{self.reason} - {self.given.strftime('%Y-%m-%d %H:%M')}"

    def to_json(self) -> dict:
        return {
            "id": str(self.id),
            "user": str(self.user.id),
            "reason": self.reason,
            "moderator": str(self.moderator.id),
            "given": self.given.strftime('%Y-%m-%d %H:%M'),
            "expires": self.expires.strftime('%Y-%m-%d %H:%M')
        }

    def edit(self, reason: str | None = None, expires: datetime.datetime | None = None):
        if reason is not None:
            self.reason = reason
        if expires is not None:
            self.expires = expires


def generate_expiration(user: User) -> datetime.datetime:
    """
    Generates the expiration date of the next warning of a user.
    """
    update_warnings()

    if user.id not in _warnings:
        _warnings[user.id] = []

    user_warnings: list[DiscordWarning] = get_warnings_by_user(user)

    match len(user_warnings):
        case 0:
            return datetime.datetime.utcnow() + datetime.timedelta(days=30)
        case 1:
            return user_warnings[-1].expires + datetime.timedelta(days=90)
        case 2:
            return user_warnings[-1].expires + datetime.timedelta(days=1)
        case _:
            raise Exception(f"User {user.name} has more than 2, or negative warnings.")


def add_warning(warning: DiscordWarning) -> int:
    """
    Adds a warning. Returns the number of warnings of the user.
    """
    _warnings[warning.user.id].append(warning)
    write_warnings()
    return len(_warnings[warning.user.id])


def delete_warning(warning: DiscordWarning) -> None:
    """
    Removes a warning.
    """
    _warnings[warning.user.id].remove(warning)
    write_warnings()


def get_warnings_by_user(user: User) -> list[DiscordWarning] | None:
    """
    Returns all warnings of a user.
    """
    update_warnings()

    try:
        return _warnings[user.id]
    except KeyError:
        return None


def get_warnings_by_moderator(moderator: User) -> list[DiscordWarning]:
    """
    Returns all warnings of a moderator.
    """
    update_warnings()

    warnings: list[DiscordWarning] = []
    for key, value in _warnings.items():
        for warning in value:
            if warning.moderator == moderator:
                warnings.append(warning)

    return warnings


def get_all_warnings() -> list[DiscordWarning]:
    """
    Returns all warnings.
    """
    update_warnings()

    warnings: list[DiscordWarning] = []
    for value in _warnings.values():
        warnings.extend(value)

    return warnings


def get_warning(id: uuid.UUID) -> DiscordWarning:
    """
    Gets a warning.
    """
    update_warnings()

    for key, value in _warnings.items():
        for warning in value:
            if warning.id == id:
                return warning

    raise Exception(f"Warning with UUID {id} not found.")


def update_warnings() -> None:
    """
    Updates the warnings file.
    """
    for key, value in _warnings.items():
        for warning in value:
            if warning.expires < datetime.datetime.utcnow():
                if key not in _old_warnings:
                    _old_warnings[key] = []
                _old_warnings[key].append(warning)
                _warnings[key].remove(warning)


async def from_json(json_data: dict, bot: commands.Bot) -> DiscordWarning:
    id: uuid.UUID = uuid.UUID(json_data["id"])
    user: User = await bot.getch_user(int(json_data["user"]))
    reason: str = json_data["reason"]
    moderator: User = await bot.getch_user(int(json_data["moderator"]))
    given: datetime.datetime = datetime.datetime.fromisoformat(json_data["given"])
    expires: datetime.datetime = datetime.datetime.fromisoformat(json_data["expires"])

    return DiscordWarning(user, reason, moderator, given, expires, id)


def write_warnings() -> None:
    """
    Writes the warnings to the file.
    """
    old_warnings_json: dict = {}
    for key, value in _old_warnings.items():
        old_warnings_json[key] = []
        for warning in value:
            old_warnings_json[key].append(warning.to_json())

    with open("old_warnings.json", "w", encoding="utf-8") as file:
        json.dump(old_warnings_json, file, indent=4)

    warnings_json: dict = {}
    for key, value in _warnings.items():
        warnings_json[key] = []
        for warning in value:
            warnings_json[key].append(warning.to_json())

    with open("warnings.json", "w", encoding="utf-8") as file:
        json.dump(warnings_json, file, indent=4)


async def init_warnings(bot: commands.Bot) -> None:
    """
    Reads the warnings from the file.
    """
    with open("old_warnings.json", "r", encoding="utf-8") as file:
        old_warnings_json = json.load(file)
    with open("warnings.json", "r", encoding="utf-8") as file:
        warnings_json = json.load(file)

    global _warnings, _old_warnings

    for key, value in old_warnings_json.items():
        _old_warnings[int(key)] = []
        for warning_json in value:
            warning: DiscordWarning = await from_json(warning_json, bot)
            _old_warnings[int(key)].append(warning)

    for key, value in warnings_json.items():
        _warnings[int(key)] = []
        for warning_json in value:
            warning: DiscordWarning = await from_json(warning_json, bot)
            _warnings[int(key)].append(warning)
