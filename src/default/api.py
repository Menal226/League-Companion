import lcu
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

def register(app: FastAPI):
    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(open(Path("src/default/index.html"), encoding="utf-8").read())

    @app.get("/sse")
    async def sse(request: Request) -> EventSourceResponse:
        async def generator():
            while not await request.is_disconnected():
                html = await lcu.event_queue.get()
                yield {"data": html}
        
        lcu.event_queue.put_nowait(open(Path("src/lobby/index.html"), encoding="utf-8").read())
        return EventSourceResponse(generator())