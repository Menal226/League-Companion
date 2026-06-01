import base64
import logging
from opgg import OPGG
from lcu_driver.connection import Connection
from services.summoner_service import get_current_id

opgg = OPGG()
logger = logging.getLogger(__name__)


async def get_icon(conn: Connection, champion_id: int) -> str:
    try:
        if champion_id <= 0:
            logger.warning(f"Trying to get icon for invalid champion {champion_id}")
            champion_id = -1
        resp = await conn.request(
            "get", f"/lol-game-data/assets/v1/champion-icons/{champion_id}.png"
        )
        if resp.status != 200:
            logger.warning(
                f"Responce status code {resp.status} when getting champion {champion_id} icon"
            )
            return ""
        data = await resp.read()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        logger.exception(f"Exception when getting champion {champion_id} icon")


async def get_name(conn: Connection, champion_id: int) -> str:
    try:
        if champion_id <= 0:
            logger.warning(f"Trying to get name for invalid champion {champion_id}")
            return "None"
        resp = await conn.request(
            "get", f"/lol-champ-select/v1/grid-champions/{champion_id}"
        )
        if resp.status != 200:
            logger.warning(
                f"Responce status {resp.status} when getting champion {champion_id} name"
            )
            return "Unknown"

        possible_name = (await resp.json()).get("name", "Unknown")
        if possible_name == "Unknown":
            logger.warning(f"Champion {champion_id} name doesnt exist")

        return possible_name
    except Exception:
        logger.exception(f"Exception when getting champion {champion_id} name")


async def get_counter_ids(champion_id: int) -> list[int]:
    try:
        # this should be cached most of the time (i think)
        data = await opgg.get_champion_stats_async()
        # for some reason this returns a list that is in arbitrary order
        # so i cant index into it by the champion id and have to iterate over it
        for champ in data:
            if champ["id"] != champion_id:
                continue
            return [
                counter["champion_id"] for counter in champ["positions"][0]["counters"]
            ]

        return []
    except Exception:
        logger.exception(f"Exception when getting counters for {champion_id}")


async def get_portrait(conn: Connection, champion_id: int) -> str:
    try:
        if champion_id <= 0:
            logger.warning(f"Invalid id for champion {champion_id}")
            return ""
        summ_id = await get_current_id(conn)

        champ_info_resp = await conn.request(
            "get", f"/lol-champions/v1/inventories/{summ_id}/champions/{champion_id}"
        )

        if champ_info_resp.status != 200:
            logger.warning(
                f"Responce status code {resp.status} when getting info about chamption {champion_id}"
            )
            return ""

        champ_info = await champ_info_resp.json()

        resp = await conn.request(
            "get",
            champ_info.get("baseLoadScreenPath", ""),
        )
        if resp.status != 200:
            logger.warning(
                f"Responce status code {resp.status} when getting portait for {champion_id}"
            )
            return ""
        data = await resp.read()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        logger.exception(f"Exception when getting portrait for {champion_id}")


async def get_skin_splash(conn: Connection, champ_id: int, skin_id: int) -> str:
    try:
        summ_id = await get_current_id(conn)
        skin_info_resp = await conn.request(
            "get",
            f"/lol-champions/v1/inventories/{summ_id}/champions/{champ_id}/skins/{skin_id}",
        )

        if skin_info_resp.status != 200:
            logger.warning(
                f"Responce status code {skin_info_resp.status} when getting skin info for {champ_id} and {skin_id}"
            )
            return ""

        skin_info = await skin_info_resp.json()

        resp = await conn.request("get", skin_info.get("splashPath", ""))
        if resp.status != 200:
            logger.warning(
                f"Responce status code {resp.status} when getting splash art for {champ_id} and {skin_id}"
            )
            return ""

        data = await resp.read()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        logger.exception(
            f"Exception when getting splash art for {champ_id} and {skin_id}"
        )
