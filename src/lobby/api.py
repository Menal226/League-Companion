import lcu
from lobby import lcu as lcu_l
from fastapi import FastAPI


def register(app: FastAPI):
    @app.post("/lobby/queue/start")
    async def queue_start():
        await lcu.request("post", "/lol-lobby/v2/lobby/matchmaking/search")

    @app.post("/lobby/queue/stop")
    async def queue_stop():
        await lcu.request("delete", "/lol-lobby/v2/lobby/matchmaking/search")

    @app.post("/lobby/queue/toggle")
    async def queue_aa_toggle():
        lcu_l.toggle_autoaccept()

    @app.post("/lobby/create/{queueId}")
    async def create_lobby(queueId: int):
        await lcu.request("delete", "/lol-lobby/v2/lobby")
        await lcu.request("post", "/lol-lobby/v2/lobby", json={"queueId": queueId})
