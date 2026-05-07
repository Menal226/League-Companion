from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
import lcu

def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(open(r"C:\Users\micha\Desktop\League Companion\src\index.html", encoding="utf-8").read())

    @app.get("/sse")
    async def sse(request: Request) -> EventSourceResponse:
        async def generator():
            while not await request.is_disconnected():
                html = await lcu.event_queue.get()
                yield {"data": html}
        return EventSourceResponse(generator())

    @app.post("/queue/start")
    async def queue_start():
        await lcu.request("post", "/lol-lobby/v2/lobby/matchmaking/search")

    @app.post("/queue/stop")
    async def queue_stop():
        await lcu.request("delete", "/lol-lobby/v2/lobby/matchmaking/search")
    
    @app.post("/queue/toggle")
    async def queue_aa_toggle():
        lcu.toggle_autoaccept()

    return app