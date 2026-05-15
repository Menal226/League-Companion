import base64
from opgg import OPGG
from lcu_driver.connection import Connection
from services.summoner_service import get_current_id

opgg = OPGG()


async def get_icon(conn: Connection, champion_id: int) -> str:
    if champion_id <= 0:
        champion_id = -1
    resp = await conn.request(
        "get", f"/lol-game-data/assets/v1/champion-icons/{champion_id}.png"
    )
    if resp.status != 200:
        return ""
    data = await resp.read()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{encoded}"


async def get_name(conn: Connection, champion_id: int) -> str:
    if champion_id <= 0:
        return "None"
    resp = await conn.request(
        "get", f"/lol-champ-select/v1/grid-champions/{champion_id}"
    )
    if resp.status != 200:
        return "Unknown"
    return (await resp.json()).get("name", "Unknown")


async def get_counter_ids(champion_id: int) -> list[int]:
    # this should be cached most of the time (i think)
    data = await opgg.get_champion_stats_async()
    # for some reason this returns a list that is in arbitrary order
    # so i cant index into it by the champion id and have to iterate over it
    for champ in data:
        if champ["id"] != champion_id:
            continue
        return [counter["champion_id"] for counter in champ["positions"][0]["counters"]]

    return []


async def get_portrait(conn: Connection, champion_id: int) -> str:
    if champion_id <= 0:
        return ""
    summ_id = await get_current_id(conn)

    champ_info_resp = await conn.request(
        "get", f"/lol-champions/v1/inventories/{summ_id}/champions/{champion_id}"
    )

    champ_info = await champ_info_resp.json()

    resp = await conn.request(
        "get",
        champ_info.get("baseLoadScreenPath", ""),
    )
    if resp.status != 200:
        return ""
    data = await resp.read()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{encoded}"
