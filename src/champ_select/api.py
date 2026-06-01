import lcu
import logging
from math import floor
from datetime import datetime
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register(app: FastAPI):
    @app.post("/champ-select/bench/swap/{champion_id}")
    async def swap_champ_from_bench(champion_id: int):
        try:
            await lcu.request(
                "POST", f"/lol-champ-select/v1/session/bench/swap/{champion_id}"
            )
        except Exception:
            logger.exception("Exception when swaping to chamption from bench")

    @app.post("/champ-select/pick/{champion_id}")
    async def select_aram_champion(champion_id: int):
        try:
            session_resp = await lcu.request("GET", "/lol-champ-select/v1/session")
            if session_resp.status != 200:
                logger.warning(
                    f"Responce status code {session_resp.status} when getting session info"
                )
                return
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
        except Exception:
            logger.exception(f"Exception when trying to pick chamption {champion_id}")

    @app.get("/champ-select/clock")
    async def get_remaining_time():
        try:
            resp = await lcu.request("GET", "/lol-champ-select/v1/session/timer")

            if resp.status != 200:
                logger.warning(
                    f"Responce status code {resp.status} when getting current clock"
                )
                return ""

            data = await resp.json()
            timer_ms = data.get("adjustedTimeLeftInPhase", 0) - (
                datetime.now().timestamp() * 1000
                - (data.get("internalNowInEpochMs", 0))
            )

            if timer_ms < 0:
                logger.warning(f"Timer is negative {timer_ms}")

            return max(0, floor(timer_ms / 1000))
        except Exception:
            logger.exception("Exception getting clock value")

    @app.post("/champ-select/swap-position/{id}/request")
    async def swap_position(id: int):
        try:
            await lcu.request(
                "POST", f"/lol-champ-select/v1/session/position-swaps/{id}/request"
            )
        except Exception:
            logger.exception(f"Exception when requesting position swap with {id}")

    @app.post("/champ-select/swap-champions/{id}/request")
    async def swap_position(id: int):
        try:
            await lcu.request(
                "POST", f"/lol-champ-select/v1/session/champion-swaps/{id}/request"
            )
        except Exception:
            logger.exception(f"Exception when requesting champion swap with {id}")

    @app.post("/champ-select/swap-order/{id}/request")
    async def swap_position(id: int):
        try:
            await lcu.request(
                "POST", f"/lol-champ-select/v1/session/pick-order-swaps/{id}/request"
            )
        except Exception:
            logger.exception(f"Exception when requesting order swap with {id}")
