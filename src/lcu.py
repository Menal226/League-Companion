import asyncio
import threading
from aiohttp import ClientResponse
from lcu_driver import Connector
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
    if main_loop:
        main_loop.call_soon_threadsafe(event_queue.put_nowait, html)

async def request(method: str, path: str) -> ClientResponse:
    if connection is None or connector_loop is None:
        raise RuntimeError("Not connected to League")
    future = asyncio.run_coroutine_threadsafe(
        connection.request(method, path),
        connector_loop,
    )

    return await asyncio.get_event_loop().run_in_executor(None, future.result)

def start():
    from champ_select import lcu_champ_select
    from lobby import lcu_lobby
    lcu_champ_select.register(connector)
    lcu_lobby.register(connector)
    thread = threading.Thread(target=connector.start, daemon=True)
    thread.start()


@connector.ready
async def on_connect(conn: Connection):
    global connection, connector_loop
    connection = conn
    connector_loop = asyncio.get_event_loop()
    push('<span id="status" hx-swap-oob="true">● Connected</span>')

@connector.close
async def on_disconnect(_):
    global connection, connector_loop
    connection = None
    connector_loop = None
    push('<span id="status" hx-swap-oob="true">○ Disconnected</span>')
