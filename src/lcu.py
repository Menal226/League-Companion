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
auto_accept = False

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

def toggle_autoaccept():
    global auto_accept
    auto_accept = not auto_accept


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

def _champion_icon(champion_id: int) -> str:
    CD_ICONS = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/"
    if champion_id <= 0:
        return f"{CD_ICONS}-1.png"
    return f"{CD_ICONS}{champion_id}.png"

async def _process_team(conn: Connection, team_data):
    rows = ""
    for player in team_data:
        champ_id = player["championId"] or player["championPickIntent"]
        label = "Locked in" if champ_id == player["championId"] else "Hovering"
        rows += f"<tr><td>{player.get("gameName", "Hidden")}</td><td>{_champion_name(champ_id)}</td><td>{label}</td></tr>"
        print(player)

    return rows

async def update_teams(conn: Connection, event: WebsocketEventResponse):
    if event.data["timer"]["phase"] != "BAN_PICK" and event.data["timer"]["phase"] != "PLANNING":
        return

    push(f'<tbody id="myteam-body" hx-swap-oob="true">{await _process_team(conn, event.data["myTeam"])}</tbody>')
    push(f'<tbody id="theirteam-body" hx-swap-oob="true">{await _process_team(conn, event.data["theirTeam"])}</tbody>')

def update_aram_bench(event: WebsocketEventResponse):
    if not event.data["benchEnabled"]:
        return
    
    result = ""
    for champ in event.data["benchChampions"]:
        result += f'<img src="{_champion_icon(champ["championId"])}" hx-trigger="click" hx-post="/lobby/bench/swap/{champ["championId"]}" hx-swap="none">'


    push(f'<div id="bench-champs" hx-swap-oob="true">{result}</div>')
    

@connector.ws.register("/lol-champ-select/v1/session", event_types=("CREATE", "UPDATE"))
async def on_champ_select(conn: Connection, event: WebsocketEventResponse):
    await update_teams(conn, event)
    update_aram_bench(event)


@connector.ws.register("/lol-champ-select/v1/session", event_types=("DELETE", ))
async def on_champ_select_exit(conn: Connection, event: WebsocketEventResponse):
    push('<tbody id="myteam-body" hx-swap-oob="true"><tr><td colspan="3" class="empty">Waiting for champ select…</td></tr></tbody>')
    push('<tbody id="theirteam-body" hx-swap-oob="true"><tr><td colspan="3" class="empty">Waiting for champ select…</td></tr></tbody>')
    push('<div id="bench-champs" hx-swap-oob="true"></div>')

@connector.ws.register("/lol-matchmaking/v1/search", event_types=("CREATE", "UPDATE"))
async def on_queue(conn: Connection, event: WebsocketEventResponse):
    push(f'<b id="queue_timer" hx-swap-oob="true"> Time: {event.data["timeInQueue"]}s</b>')

@connector.ws.register("/lol-matchmaking/v1/search", event_types=("DELETE", ))
async def on_queue_exit(conn: Connection, event: WebsocketEventResponse):
    push('<b id="queue_timer" hx-swap-oob="true">Not in queue</b>')

@connector.ws.register("/lol-matchmaking/v1/ready-check", event_types=("UPDATE",))
async def on_queue_pop(conn: Connection, event: WebsocketEventResponse):
    if event.data["playerResponse"] != "None" or not auto_accept:
        return
    
    await conn.request("POST", "/lol-matchmaking/v1/ready-check/accept")