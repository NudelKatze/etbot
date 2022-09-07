import json

from disnake import ApplicationCommandInteraction, Message
from disnake.ext import commands
from disnake.ext.commands import Cog, slash_command
from mcstatus import JavaServer
from mcstatus.pinger import PingResponse
from requests import Session, Response

from vars import roles, messages

email, password = "", ""


def setup(bot):
    bot.add_cog(Minecraft(bot))
    with open("config.json", 'r') as config_file:
        json_config = json.load(config_file)
        global email, password
        email = json_config["email"]
        password = json_config["password"]
    print("Loaded Minecraft Cog.")


def get_status() -> PingResponse | None:
    server = JavaServer.lookup("ETMC.mchost.pro")
    try:
        status = server.status()
    except ConnectionRefusedError:
        status = None
    return status


def is_online() -> bool:
    status = get_status()
    return True if status is not None else False


def get_session() -> Session:
    payload = {
        "email": email,
        "password": password,
        "stay": "1"
    }
    session = Session()
    session.get("https://www.minecraft-hosting.pro/login")
    session.post("https://www.minecraft-hosting.pro/~bG9naW4=", data=payload)
    return session


class Minecraft(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @slash_command(name="mc")
    async def mc(self, inter: ApplicationCommandInteraction) -> None:
        pass

    @mc.sub_command(name="info", description="Responds with the Minecraft server information.")
    async def info(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        msg: Message = await messages.get_minecraft_info()
        await inter.send(msg.content)

    @mc.sub_command(name="status", description="Responds with the Minecraft server status.")
    async def status(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()

        status = get_status()
        if status is None:
            await inter.send("The Minecraft server is offline.")
        else:
            await inter.send(f"The server has {status.players.online} players and replied in {int(status.latency)} ms.")

    @mc.sub_command(name="start", description="Starts the Minecraft server.")
    async def start(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        response: Response

        if is_online():
            await inter.send("The Minecraft server is already online.")
            return

        with get_session() as s:
            payload = {
                "action": "start",
                "order": "271630"
            }
            response = s.post("https://www.minecraft-hosting.pro/~ZXhlY3V0ZQ==", data=payload)

        if response.status_code == 200:
            await inter.send("Starting Minecraft server...")
        else:
            await inter.send("Failed to start Minecraft server.")

    @mc.sub_command(name="stop", description="Stops the Minecraft server.")
    @commands.check(roles.check_is_staff)
    async def stop(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        response: Response

        if not is_online():
            await inter.send("The Minecraft server is already offline.")
            return

        with get_session() as s:
            payload = {
                "action": "stop",
                "order": "271630"
            }
            response = s.post("https://www.minecraft-hosting.pro/~ZXhlY3V0ZQ==", data=payload)

        if response.status_code == 200:
            await inter.send("Stopping Minecraft server...")
        else:
            await inter.send("Failed to stop Minecraft server.")

    @mc.sub_command(name="restart", description="Restarts the Minecraft server.")
    @commands.check(roles.check_is_staff)
    async def restart(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        response: Response

        with get_session() as s:
            payload = {
                "action": "restart",
                "order": "271630"
            }
            response = s.post("https://www.minecraft-hosting.pro/~ZXhlY3V0ZQ==", data=payload)

        if response.status_code == 200:
            await inter.send("Restarting Minecraft server...")
        else:
            await inter.send("Failed to restart Minecraft server.")
