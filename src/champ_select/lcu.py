from lcu import push
from pathlib import Path
from lcu_driver import Connector
from lcu_driver.connection import Connection
from services import champion_service, spells_service
from lcu_driver.events.responses import WebsocketEventResponse

in_game = False

def register(connector: Connector):
    @connector.ws.register("/lol-champ-select/v1/session", event_types=("CREATE", ))
    async def on_champ_select_create(conn: Connection, event: WebsocketEventResponse):
        push(open(Path("src/champ_select/index.html"), encoding="utf-8").read())
        await on_champ_select_update(conn, event)

    @connector.ws.register("/lol-champ-select/v1/session", event_types=("UPDATE", ))
    async def on_champ_select_update(conn: Connection, event: WebsocketEventResponse):
        await update_teams(conn, event)
        await update_bans(conn, event)
        await update_aram_bench(conn, event)

    @connector.ws.register("/lol-champ-select/v1/session", event_types=("DELETE", ))
    async def on_champ_select_delete(conn: Connection, event: WebsocketEventResponse):
        # im not sure how to implement redirects prompted by the server so im just rending the container
        # hmlt and stay on the same url
        push(open(Path("src/lobby/index.html"), encoding="utf-8").read())


async def create_my_team_player(conn: Connection, player_info) -> str:
    champ_id = player_info["championId"] or player_info["championPickIntent"]
    champ_icon = await champion_service.get_icon(conn, champ_id)
    spell1 = spells_service.get_icon(player_info["spell1Id"])
    spell2 = spells_service.get_icon(player_info["spell2Id"])
    return f'<div class="player-lobby-info"><img src="{champ_icon}" class="player-champ-icon"><div><b style="font-size: 1rem;">{player_info.get("gameName", "Hidden")}</b><div><img src="{spell1}" class="player-summoner"><img src="{spell2}" class="player-summoner"></div></div></div>'

async def create_my_team_panel(conn: Connection, team_data) -> str:
    return "".join([await create_my_team_player(conn, player) for player in team_data])

async def create_their_team_player(conn: Connection, player_info) -> str:
    champ_id = player_info["championId"]
    champ_icon = await champion_service.get_icon(conn, champ_id)
    counter_ids = await champion_service.get_counter_ids(champ_id)
    counters = "".join([f'<img src="{await champion_service.get_icon(conn, c_id)}" class="player-summoner">' for c_id in counter_ids])
    return f'<div class="player-lobby-info"><div><b style="font-size: 1rem;">Counters</b><div>{counters}</div></div><img src="{champ_icon}" class="player-champ-icon"></div>'

async def create_their_team_panel(conn: Connection, team_data) -> str:
    return "".join([await create_their_team_player(conn, player) for player in team_data])

async def update_teams(conn: Connection, event: WebsocketEventResponse):
    push(f'<div id="my-team" hx-swap-oob="true">{await create_my_team_panel(conn, event.data["myTeam"])}</div>')
    push(f'<div id="their-team" hx-swap-oob="true">{await create_their_team_panel(conn, event.data["theirTeam"])}</div>')

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
    return "".join([f'<img src="{await champion_service.get_icon(conn, ban_id)}" class="bench-champ-icon">' for ban_id in team_data])

async def update_bans(conn: Connection, event: WebsocketEventResponse):
    my_team_bans, their_team_bans = gather_bans_from_actions(event.data["actions"])
    push(f'<div id="my-team-bans" hx-swap-oob="true">{await create_team_bans_panel(conn, my_team_bans)}</div>')
    push(f'<div id="their-team-bans" hx-swap-oob="true">{await create_team_bans_panel(conn, their_team_bans)}</div>')

async def update_aram_bench(conn: Connection, event: WebsocketEventResponse):
    if not event.data["benchEnabled"]:
        return

    result = "".join([f'<img src="{await champion_service.get_icon(conn, champ["championId"])}" hx-trigger="click" hx-post="/champ-select/bench/swap/{champ["championId"]}" hx-swap="none" class="bench-champ-icon">' for champ in event.data["benchChampions"]])
    push(f'<div id="aram-bench" hx-swap-oob="true">{result}</div>')

# /lol-lobby-team-builder/champ-select/v1/subset-champion-list