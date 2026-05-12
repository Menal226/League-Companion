import asyncio
import threading
from pathlib import Path
from lcu_driver import Connector
from aiohttp import ClientResponse
from lcu_driver.connection import Connection

connector = Connector()
connection: Connection | None = None
connector_loop: asyncio.AbstractEventLoop | None = None

event_queue: asyncio.Queue = asyncio.Queue()
main_loop: asyncio.AbstractEventLoop | None = None

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
    lcu_cs.register(connector)
    lcu_l.register(connector)
    # force existing pages to reset
    event_queue.put_nowait(open(Path("src/lobby/index.html"), encoding="utf-8").read())
    thread = threading.Thread(target=connector.start, daemon=True)
    thread.start()


@connector.ready
async def on_connect(conn: Connection):
    global connection, connector_loop
    connection = conn
    connector_loop = asyncio.get_event_loop()


@connector.close
async def on_disconnect(_):
    global connection, connector_loop
    connection = None
    connector_loop = None
