import lcu
import logging
from lobby import lcu as lcu_l
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register(app: FastAPI):
    @app.post("/post-game/again")
    async def queue_start():
        try:
            await lcu.request("post", "/lol-lobby/v2/play-again")
        except Exception:
            logger.exception("Exception on /lobby/queue/start")
