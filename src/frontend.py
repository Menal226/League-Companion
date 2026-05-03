from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
import lcu

def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(open("index.html", encoding="utf-8").read())

    @app.get("/sse")
    async def sse(request: Request) -> EventSourceResponse:
        async def generator():
            while not await request.is_disconnected():
                html = await lcu.event_queue.get()
                yield {"data": html}
        return EventSourceResponse(generator())

    @app.post("/queue/start", response_class=HTMLResponse)
    async def queue_start() -> str:
        try:
            await lcu.request("post", "/lol-lobby/v2/lobby/matchmaking/search")
            return '<span class="toast">Queue started</span>'
        except RuntimeError as e:
            return f'<span class="toast error">{e}</span>'

    @app.post("/queue/stop", response_class=HTMLResponse)
    async def queue_stop() -> str:
        try:
            await lcu.request("delete", "/lol-lobby/v2/lobby/matchmaking/search")
            return '<span class="toast">Queue stopped</span>'
        except RuntimeError as e:
            return f'<span class="toast error">{e}</span>'

    return app