import logging

from lcu_driver.connection import Connection

logger = logging.getLogger(__name__)


async def get_current_id(conn: Connection) -> int:
    try:
        resp = await conn.request("GET", "/lol-summoner/v1/current-summoner")
        if resp.status != 200:
            logger.warning(
                f"Responce status code {resp.status} when getting summoner id"
            )
            return 0
        possible = (await resp.json()).get("summonerId", 0)
        if possible == 0:
            logger.warning("No summoner id for responce")
        return possible
    except Exception:
        logger.exception("Exception when getting summoner id")
        return 0
