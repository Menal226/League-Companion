from lcu_driver.connection import Connection


async def get_current_id(conn: Connection) -> int:
    resp = await conn.request("GET", "/lol-summoner/v1/current-summoner")
    return (await resp.json()).get("summonerId", 0)
