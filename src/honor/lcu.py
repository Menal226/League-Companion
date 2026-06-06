import logging
from lcu import push, request
from pathlib import Path
from lcu_driver import Connector
from lcu_driver.connection import Connection
from lcu_driver.events.responses import WebsocketEventResponse
from services.champion_service import get_portrait

logger = logging.getLogger(__name__)


def register(connector: Connector):
    @connector.ws.register("/lol-honor-v2/v1/ballot", event_types=("CREATE", "UPDATE"))
    async def on_honor_update(conn: Connection, event: WebsocketEventResponse):
        from lobby.lcu import auto_skip_honor, auto_honor_lobby

        if auto_skip_honor:
            await request("DELETE", "/lol-honor-v2/v1/ballot")
            return

        honored = {
            player["recipientPuuid"] for player in event.data.get("honoredPlayers", [])
        }
        allies = [
            (
                f'<img class="honor-portrait{"-disabled" if player["puuid"] in honored else ""}" id="my-honor-possible-{i}" hx-swap-oob="true" src="{await get_portrait(conn, player["championId"])}"'
                f'hx-trigger="click" hx-post="/honor/{event.data["gameId"]}/{player["puuid"]}/{player["summonerId"]}" hx-swap="none">'
                if not player["puuid"] in honored
                else ">"
            )
            for i, player in enumerate(event.data.get("eligibleAllies", []))
        ]
        opponents = [
            (
                f'<img class="honor-portrait{"-disabled" if player["puuid"] in honored else ""}" id="enemy-honor-possible-{i}" hx-swap-oob="true" src="{await get_portrait(conn, player["championId"])}"'
                f'hx-trigger="click" hx-post="/honor/{event.data["gameId"]}/{player["puuid"]}/{player["summonerId"]}" hx-swap="none">'
                if not player["puuid"] in honored
                else ">"
            )
            for i, player in enumerate(event.data.get("eligibleOpponents", []))
        ]
        push("".join(allies))
        push("".join(opponents))


def switch_screen():
    logger.info("Switching to honor screen")
    push(open(Path("src/honor/index.html"), encoding="utf-8").read())
