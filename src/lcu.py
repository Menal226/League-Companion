import asyncio
import threading
from aiohttp import ClientResponse
from lcu_driver import Connector
from lcu_driver.connection import Connection
from lcu_driver.events.responses import WebsocketEventResponse

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

async def _champion_name(conn: Connection, champion_id: int) -> str:
    if champion_id == 0:
        return "None"
    resp = await conn.request("get", f"/lol-champ-select/v1/grid-champions/{champion_id}")
    if resp.status != 200:
        return "Unknown"
    return (await resp.json()).get("name", "Unknown")

async def _process_team(conn: Connection, team_data):
    team = []
    for mate in team_data:
        champ_id = mate["championId"] or mate["championPickIntent"]
        team.append({
            "name": mate.get("gameName", "Hidden"),
            "champion": await _champion_name(conn, champ_id),
            "locked": mate["championId"] != 0,
        })

    rows = ""
    for p in team:
        label = "Locked in" if p["locked"] else "Hovering"
        rows += f"<tr><td>{p['name']}</td><td>{p['champion']}</td><td>{label}</td></tr>"

    return rows

@connector.ws.register("/lol-champ-select/v1/session", event_types=("CREATE", "UPDATE"))
async def on_champ_select(conn: Connection, event: WebsocketEventResponse):
    if event.data["timer"]["phase"] != "BAN_PICK":
        return

    push(f'<tbody id="myteam-body" hx-swap-oob="true">{await _process_team(conn, event.data["myTeam"])}</tbody>')
    push(f'<tbody id="theirteam-body" hx-swap-oob="true">{await _process_team(conn, event.data["theirTeam"])}</tbody>')