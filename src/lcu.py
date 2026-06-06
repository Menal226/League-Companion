import asyncio
import threading
import logging
from pathlib import Path
from lcu_driver import Connector
from aiohttp import ClientResponse
from lcu_driver.connection import Connection
from lcu_driver.events.responses import WebsocketEventResponse

connector = Connector()
connection: Connection | None = None
connector_loop: asyncio.AbstractEventLoop | None = None

event_queue: asyncio.Queue = asyncio.Queue()
main_loop: asyncio.AbstractEventLoop | None = None
logger = logging.getLogger(__name__)

current_state = ""


def set_main_loop(loop: asyncio.AbstractEventLoop):
    global main_loop
    main_loop = loop


def push(html: str):
    if main_loop and len(html) > 0:
        main_loop.call_soon_threadsafe(event_queue.put_nowait, html)


async def request(method: str, path: str, **kwargs) -> ClientResponse:
    if connection is None or connector_loop is None:
        raise RuntimeError("Not connected to League")
    future = asyncio.run_coroutine_threadsafe(
        connection.request(method, path, **kwargs),
        connector_loop,
    )

    return await asyncio.get_event_loop().run_in_executor(None, future.result)


def start():
    # prevent circular import
    from champ_select import lcu as lcu_cs
    from lobby import lcu as lcu_l
    from honor import lcu as lcu_h

    lcu_cs.register(connector)
    lcu_l.register(connector)
    lcu_h.register(connector)
    thread = threading.Thread(target=connector.start, daemon=True)
    thread.start()


@connector.ready
async def on_connect(conn: Connection):
    global connection, connector_loop
    connection = conn
    connector_loop = asyncio.get_event_loop()
    logger.info("Lcu driver started")
    # maybe add pushing of setting here aswell


@connector.close
async def on_disconnect(_):
    global connection, connector_loop
    connection = None
    connector_loop = None
    logger.info("Lcu driver closed")


@connector.ws.register("/lol-gameflow/v1/session", event_types=("CREATE", "UPDATE"))
async def screen_update(conn: Connection, event: WebsocketEventResponse):
    try:
        from champ_select import lcu as lcu_cs
        from lobby import lcu as lcu_l
        from in_game import lcu as lcu_ig
        from post_game import lcu as lcu_pg
        from honor import lcu as lcu_h

        logger.info("CREATE/UPDATE /lol-gameflow/v1/session")
        global current_state
        state = event.data.get("phase", "")

        if state == "ChampSelect":
            if current_state != state:
                lcu_cs.switch_screen()
        elif state == "Lobby":
            if current_state != state:
                await lcu_l.switch_screen()
            await lcu_l.update_background(conn, event)
        elif state == "InProgress":
            if current_state != state:
                lcu_ig.switch_screen()
        elif state == "EndOfGame":
            if current_state != state:
                lcu_pg.switch_screen()
        elif state == "PreEndOfGame":
            if current_state != state:
                lcu_h.switch_screen()
        elif state == "WaitingForStats":
            logger.info("Waiting for stats")
            await asyncio.sleep(5)
            resp = await conn.request("GET", "/lol-gameflow/v1/gameflow-phase")
            if resp.status != 200:
                await conn.request("POST", "/lol-end-of-game/v1/state/dismiss-stats")
                logger.info("Skipped waiting for stats")
            else:
                data = await resp.json()
                if data == "WaitingForStats":
                    await conn.request(
                        "POST", "/lol-end-of-game/v1/state/dismiss-stats"
                    )
                    logger.info("Skipped waiting for stats")
        else:
            return
        current_state = state
    except Exception:
        logger.exception("Exception when switching screens")
