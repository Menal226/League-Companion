import lcu
from math import floor
from datetime import datetime
from fastapi import FastAPI


def register(app: FastAPI):
    @app.post("/champ-select/bench/swap/{champion_id}")
    async def swap_champ_from_bench(champion_id: int):
        await lcu.request(
            "POST", f"/lol-champ-select/v1/session/bench/swap/{champion_id}"
        )

    @app.post("/champ-select/pick/{champion_id}")
    async def select_aram_champion(champion_id: int):
        session_resp = await lcu.request("GET", "/lol-champ-select/v1/session")
        session = await session_resp.json()
        my_cell_id = session["localPlayerCellId"]

        action = next(
            a
            for group in session["actions"]
            for a in group
            if a["actorCellId"] == my_cell_id and not a["completed"]
        )

        await lcu.request(
            "PATCH",
            f"/lol-champ-select/v1/session/actions/{action['id']}",
            json={
                "championId": champion_id,
                "completed": True,
            },
        )

    @app.get("/champ-select/clock")
    async def get_remaining_time():
        resp = await lcu.request("GET", "/lol-champ-select/v1/session/timer")

        if resp.status != 200:
            return ""

        data = await resp.json()
        timer_ms = data.get("adjustedTimeLeftInPhase", 0) - (
            datetime.now().timestamp() * 1000 - (data.get("internalNowInEpochMs", 0))
        )
        return max(0, floor(timer_ms / 1000))
