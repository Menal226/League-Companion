import base64
import logging
from lcu import push
from pathlib import Path
from lcu_driver import Connector
from lcu_driver.connection import Connection
from lcu_driver.events.responses import WebsocketEventResponse

auto_accept = False
logger = logging.getLogger(__name__)


def register(connector: Connector):
    @connector.ws.register(
        "/lol-matchmaking/v1/search", event_types=("CREATE", "UPDATE")
    )
    async def on_queue(conn: Connection, event: WebsocketEventResponse):
        logger.info("CREATE/UPDATE /lol-matchmaking/v1/search")
        push(
            f'<b id="queue_timer" hx-swap-oob="true"> Time: {event.data["timeInQueue"]}s (est. {int(event.data["estimatedQueueTime"])}s)</b>'
        )

    @connector.ws.register("/lol-matchmaking/v1/search", event_types=("DELETE",))
    async def on_queue_exit(conn: Connection, event: WebsocketEventResponse):
        logger.info("DELETE /lol-matchmaking/v1/search")
        push('<b id="queue_timer" hx-swap-oob="true">Not in queue</b>')

    @connector.ws.register("/lol-matchmaking/v1/ready-check", event_types=("UPDATE",))
    async def on_queue_pop(conn: Connection, event: WebsocketEventResponse):
        if event.data["playerResponse"] != "None" or not auto_accept:
            return

        logger.info("UPDATE /lol-matchmaking/v1/ready-check")
        await conn.request("POST", "/lol-matchmaking/v1/ready-check/accept")


async def extract_background(conn: Connection, event: WebsocketEventResponse) -> str:
    try:
        event_data = event.data or {}
        map_data = event_data.get("map") or {}
        assets_data = map_data.get("assets") or {}
        bg_url = assets_data.get("gameflow-background", "")
        if bg_url == "":
            logger.warning("No lobby background image found")
            return ""
        resp = await conn.request("GET", f"/{bg_url}")
        if resp.status != 200:
            logger.warning(
                f"Responce status code {resp.status} getting lobby background image"
            )
            return ""
        data = await resp.read()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        logger.exception("Exception getting lobby background")
        return ""


async def update_background(conn: Connection, event: WebsocketEventResponse):
    push(
        f'<img id="lobby-bg" hx-swap-oob="true" style="display: block;" src="{await extract_background(conn, event)}">'
    )


def toggle_autoaccept():
    global auto_accept
    auto_accept = not auto_accept
    logger.info(f"Autoaccept set to {auto_accept}")


def switch_screen():
    logger.info("Switching to lobby")
    push(open(Path("src/lobby/index.html"), encoding="utf-8").read())
    if auto_accept:
        push(
            '<input hx-post="/lobby/queue/toggle" hx-swap-oob="true" hx-swap="none" type="checkbox" id="auto-accept-switch" checked>'
        )
