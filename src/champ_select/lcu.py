from shutil import ExecError

from lcu import push
from pathlib import Path
from lcu_driver import Connector
from lcu_driver.connection import Connection
from services import champion_service, lobby_service
from lcu_driver.events.responses import WebsocketEventResponse
from lobby.lcu import switch_screen as switch_to_lobby

in_game = False
players = [{} for _ in range(10)]
bench = [0 for _ in range(10)]

# autofill, side
# /lol-champ-select/v1/pin-drop-notification

# skins info
# /lol-champions/v1/inventories/{summonerid}/champions

"""
[
  {
    "cellId": 1,
    "id": 32,
    "state": "INVALID"
  },
  {
    "cellId": 2,
    "id": 34,
    "state": "INVALID"
  },
  {
    "cellId": 3,
    "id": 28,
    "state": "INVALID"
  },
  {
    "cellId": 4,
    "id": 30,
    "state": "INVALID"
  }
]"""


def register(connector: Connector):
    @connector.ws.register("/lol-champ-select/v1/session", event_types=("CREATE",))
    async def on_champ_select_create(conn: Connection, event: WebsocketEventResponse):
        switch_screen()
        await on_champ_select_update(conn, event)

    @connector.ws.register("/lol-champ-select/v1/session", event_types=("UPDATE",))
    async def on_champ_select_update(conn: Connection, event: WebsocketEventResponse):
        try:
            await update_aram_bench(conn, event)
            await update_teams(conn, event)
            await update_bans(conn, event)
        except Exception as e:
            print(e)

    @connector.ws.register("/lol-champ-select/v1/session", event_types=("DELETE",))
    async def on_champ_select_delete(conn: Connection, event: WebsocketEventResponse):
        # im not sure how to implement redirects prompted by the server so im just rending the container
        # hmlt and stay on the same url
        global players, bench
        players = [{} for _ in range(10)]
        bench = [0 for _ in range(10)]
        switch_to_lobby()

    @connector.ws.register(
        "/lol-lobby-team-builder/champ-select/v1/subset-champion-list",
        event_types=("CREATE",),
    )
    async def on_aram_champs_create(conn: Connection, event: WebsocketEventResponse):
        push(
            f'<div id="aram-picks" hx-swap-oob="true" style="display: block;">{await create_possible_pick_images(conn, event)}</div>'
        )

    @connector.ws.register(
        "/lol-champ-select/v1/current-champion", event_types=("CREATE",)
    )
    async def on_champ_selected(conn: Connection, event: WebsocketEventResponse):
        push('<div id="aram-picks" hx-swap-oob="true" style="display: none;"></div>')


async def create_possible_pick_images(conn: Connection, event: WebsocketEventResponse):
    return "".join(
        [
            f'<img id="aram-possible-{i}" class="aram-portrait" src="{await champion_service.get_portrait(conn, event.data[i])}" hx-trigger="click" hx-post="/champ-select/pick/{event.data[i]}">'
            for i in range(len(event.data))
        ]
    )


def switch_screen():
    push(open(Path("src/champ_select/index.html"), encoding="utf-8").read())


async def create_my_team_player(conn: Connection, player_info, index: int) -> str:
    global players
    champ_id = player_info["championId"] or player_info["championPickIntent"]
    last_state = players[player_info["cellId"]]
    if (
        champ_id
        == (last_state.get("championId") or last_state.get("championPickIntent"))
        and player_info["spell1Id"] == last_state.get("spell1Id")
        and player_info["spell2Id"] == last_state.get("spell2Id")
        and player_info["cellId"] == last_state.get("cellId")
        and player_info["assignedPosition"] == last_state.get("assignedPosition")
    ):
        return ""

    players[player_info["cellId"]] = player_info
    spell1 = lobby_service.get_spell_icon(player_info["spell1Id"])
    spell2 = lobby_service.get_spell_icon(player_info["spell2Id"])
    champ_icon = await champion_service.get_icon(conn, champ_id)
    name = player_info["gameName"] if player_info["gameName"] != "" else "Unknown"
    swaps = await get_allowed_swaps(conn)
    print()

    return (
        f'<div class="player-lobby-info" hx-swap-oob="true" id="my-player-{index}">'
        '<div class="swap-holder">'
        '<b style="font-size: 1.5rem;">Swap with player</b>'
        "<div>"
        f"{make_position_swap_button(player_info["assignedPosition"], swaps[0][player_info["cellId"]])}"
        f"{make_champion_swap_button(player_info["assignedPosition"], swaps[1][player_info["cellId"]])}"
        f"{make_order_swap_button(player_info["assignedPosition"], swaps[2][player_info["cellId"]])}"
        "</div>"
        "</div>"
        f'<img src="{champ_icon}" class="player-champ-icon">'
        "<div>"
        f'<b style="font-size: 1rem;">{name}</b>'
        "<div>"
        f'<img src="{spell1}" class="player-summoner">'
        f'<img src="{spell2}" class="player-summoner">'
        "</div>"
        "</div>"
        "</div>"
    )


def make_position_swap_button(position: str, id: 0):
    if id == 0:
        return f'<img src="{lobby_service.get_position_icon_path(position, True)}" class="swap-icon" title="Swap Positions (Disabled)">'
    else:
        return (
            f'<img src="{lobby_service.get_position_icon_path(position)}" class="swap-icon" title="Swap Positions" style="cursor: pointer;" '
            f'hx-trigger="click" hx-post="/champ-select/swap-position/{id}/request" hx-swap="none">'
        )


def make_champion_swap_button(position: str, id: 0):
    if id == 0:
        return '<img src="/assets/icon-helmet-disabled.png" class="swap-icon" title="Swap Champions (Disabled)">'
    else:
        return (
            f'<img src="/assets/icon-helmet.png" class="swap-icon" title="Swap Champions" style="cursor: pointer;" '
            f'hx-trigger="click" hx-post="/champ-select/swap-champions/{id}/request" hx-swap="none">'
        )


def make_order_swap_button(position: str, id: 0):
    if id == 0:
        return '<img src="/assets/icon-swap-disabled.png" class="swap-icon" title="Swap Pick Order (Disabled)">'
    else:
        return (
            f'<img src="/assets/icon-swap.png" class="swap-icon" title="Swap Pick Order" style="cursor: pointer;" '
            f'hx-trigger="click" hx-post="/champ-select/swap-order/{id}/request" hx-swap="none">'
        )


async def create_their_team_player(conn: Connection, player_info, index: int) -> str:
    global players
    champ_id = player_info["championId"] or player_info["championPickIntent"]
    last_state = players[player_info["cellId"]]
    if champ_id == (
        last_state.get("championId") or last_state.get("championPickIntent")
    ):
        return ""

    players[player_info["cellId"]] = player_info
    champ_icon = await champion_service.get_icon(conn, champ_id)
    counter_ids = await champion_service.get_counter_ids(champ_id)
    if len(counter_ids) < 3:
        for _ in range(3 - len(counter_ids)):
            counter_ids.append(-1)
    counters = "".join(
        [
            f'<img src="{await champion_service.get_icon(conn, c_id)}" class="player-summoner">'
            for c_id in counter_ids
        ]
    )
    return (
        f'<div class="player-lobby-info" hx-swap-oob="true" id="their-player-{index}">'
        "<div>"
        '<b style="font-size: 1rem;">Counters</b>'
        f"<div>{counters}</div>"
        "</div>"
        f'<img src="{champ_icon}" class="player-champ-icon">'
        "</div>"
    )


async def get_allowed_swaps(conn: Connection) -> list[dict[int, bool]]:
    result = [{i: 0 for i in range(10)} for _ in range(3)]
    endpoints = [
        "/lol-champ-select/v1/session/position-swaps",
        "/lol-champ-select/v1/session/champion-swaps",
        "/lol-champ-select/v1/session/pick-order-swaps",
    ]

    for i, endpoint in enumerate(endpoints):
        resp = await conn.request("GET", endpoint)
        if resp.status == 200:
            data = await resp.json()
            for point in data:
                result[i][point["cellId"]] = (
                    point["id"] if point["state"] == "AVAILABLE" else 0
                )

    return result


async def update_teams(conn: Connection, event: WebsocketEventResponse):
    push(
        "".join(
            [
                await create_my_team_player(conn, player, i)
                for i, player in enumerate(event.data["myTeam"])
            ]
        )
    )
    push(
        "".join(
            [
                await create_their_team_player(conn, player, i)
                for i, player in enumerate(event.data["theirTeam"])
            ]
        )
    )


def gather_bans_from_actions(actions: list[dict]) -> tuple[list[int], list[int]]:
    my_team_bans: list[int] = []
    their_team_bans: list[int] = []

    for action in actions:
        action = action[0]
        if action["type"] != "ban":
            continue
        if action["isAllyAction"]:
            my_team_bans.append(action["championId"])
        else:
            their_team_bans.append(action["championId"])

    return my_team_bans, their_team_bans


async def create_team_bans_panel(conn: Connection, team_data: list[int]) -> str:
    return "".join(
        [
            f'<img src="{await champion_service.get_icon(conn, ban_id)}" class="bench-champ-icon">'
            for ban_id in team_data
        ]
    )


async def update_bans(conn: Connection, event: WebsocketEventResponse):
    if event.data["timer"]["phase"] != "BAN_PICK":
        return
    my_team_bans, their_team_bans = gather_bans_from_actions(event.data["actions"])
    my_bans_html = f'<div id="my-team-bans" hx-swap-oob="true">{await create_team_bans_panel(conn, my_team_bans)}</div>'
    their_bans_html = f'<div id="their-team-bans" hx-swap-oob="true">{await create_team_bans_panel(conn, their_team_bans)}</div>'
    push(my_bans_html)
    push(their_bans_html)


async def update_aram_bench(conn: Connection, event: WebsocketEventResponse):
    if not event.data["benchEnabled"]:
        return

    global bench
    result = ""
    for i, champ in enumerate(event.data["benchChampions"]):
        if bench[i] != champ["championId"]:
            bench[i] = champ["championId"]
            result += (
                f'<img src="{await champion_service.get_icon(conn, champ["championId"])}" class="bench-champ-icon" id="bench-{i}"'
                f'hx-trigger="click" hx-post="/champ-select/bench/swap/{champ["championId"]}" hx-swap-oob="true" hx-swap="none">'
            )
    push(result)


# /lol-lobby-team-builder/champ-select/v1/subset-champion-list
