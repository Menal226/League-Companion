from opgg import OPGG
from lcu_driver.connection import Connection

CD_ADDR = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/"
opgg = OPGG()

def get_icon(champion_id: int) -> str:
    if champion_id <= 0:
        return f"{CD_ADDR}-1.png"
    return f"{CD_ADDR}{champion_id}.png"

async def get_name(conn: Connection, champion_id: int) -> str:
    if champion_id == 0:
        return "None"
    resp = await conn.request("get", f"/lol-champ-select/v1/grid-champions/{champion_id}")
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