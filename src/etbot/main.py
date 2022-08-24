import getopt
import json
import logging
import os
import sys

from disnake.ext import commands

from vars import channels, emojis, roles, messages, warnings

with open("config.json", 'r') as config_file:
    json_config = json.load(config_file)
    token = json_config["token"]
    test_guilds = json_config["test_guilds"]

bot = commands.Bot(
    command_prefix='&',
    sync_commands_debug=True,
    test_guilds=test_guilds
)

testing = False


@bot.event
async def on_ready() -> None:
    # must initialize vars after starting bot (especially channels)
    # TODO check if this can be improved with using bot.start()
    if testing:
        channels.initialize_testing_channels(bot)
        emojis.initialize_testing_emojis(bot)
        roles.initialize_testing_roles(bot)
        messages.initialize_testing_messages()
    else:
        channels.initialize_channels(bot)
        emojis.initialize_emojis(bot)
        roles.initialize_roles(bot)
        messages.initialize_messages()

    await warnings.init_warnings(bot)

    print(f"Anwesend {bot.user.name}")


def load_extensions() -> None:
    for filename in os.listdir("./src/etbot/cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            bot.load_extension(f"cogs.{filename[:-3]}")


def parse_args(argv: list[str]) -> None:
    try:
        opts, args = getopt.getopt(argv, "ht")
    except getopt.GetoptError:
        print("Invalid argument")
        sys.exit(2)

    global testing

    for opt, arg in opts:
        if opt == 'h':
            print("main.py -h -> Help\n"
                  "main.py -t -> Loads the Testing Channels and sets the logging level to DEBUG")
        elif opt == '-t':
            testing = True
            print("Testing...")


def main(argv: list[str] or None = None) -> None:
    if argv:
        parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if testing else logging.INFO)

    load_extensions()

    bot.run(token)


if __name__ == "__main__":
    main(sys.argv[1:])
