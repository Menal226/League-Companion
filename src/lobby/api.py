import lcu
import logging
from lobby import lcu as lcu_l
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register(app: FastAPI):
    @app.post("/lobby/queue/start")
    async def queue_start():
        try:
            await lcu.request("post", "/lol-lobby/v2/lobby/matchmaking/search")
        except Exception:
            logger.exception("Exception on /lobby/queue/start")

    @app.post("/lobby/queue/stop")
    async def queue_stop():
        try:
            await lcu.request("delete", "/lol-lobby/v2/lobby/matchmaking/search")
        except Exception:
            logger.exception("Exception on /lobby/queue/stop")

    @app.post("/lobby/queue/toggle-accept")
    async def queue_aa_toggle():
        lcu_l.toggle_autoaccept()

    @app.post("/lobby/queue/toggle-honor-skip")
    async def queue_aa_toggle():
        lcu_l.toggle_honor_skip()

    @app.post("/lobby/queue/toggle-honor-lobby")
    async def queue_aa_toggle():
        lcu_l.toggle_honor_lobby()

    @app.post("/lobby/create/{queueId}")
    async def create_lobby(queueId: int):
        try:
            await lcu.request("delete", "/lol-lobby/v2/lobby")
            await lcu.request("post", "/lol-lobby/v2/lobby", json={"queueId": queueId})
        except Exception:
            logger.exception(f"Exception on /lobby/create/{queueId}")
