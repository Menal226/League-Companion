import lcu
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from services.settings_service import get_setting, Setting


def register(app: FastAPI):
    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(
            open(Path("src/default/index.html"), encoding="utf-8").read()
        )

    @app.get("/sse")
    async def sse(request: Request) -> EventSourceResponse:
        async def generator():
            while not await request.is_disconnected():
                html = await lcu.event_queue.get()
                yield {"data": html}

        if await get_setting(Setting.AUTO_ACCEPT_QUEUE):
            lcu.push(
                '<input hx-post="/lobby/queue/toggle-accept" hx-swap-oob="true" hx-swap="none" type="checkbox" id="auto-accept-switch" checked>'
            )

        if await get_setting(Setting.SKIP_POST_GAME_HONOR):
            lcu.push(
                '<input hx-post="/lobby/queue/toggle-honor-skip" hx-swap-oob="true" hx-swap="none" type="checkbox" id="auto-honor-skip-switch" checked>'
            )

        if await get_setting(Setting.AUTO_HONOR_LOBBY_POST_GAME):
            lcu.push(
                '<input hx-post="/lobby/queue/toggle-honor-lobby" hx-swap-oob="true" hx-swap="none" type="checkbox" id="auto-honor-lobby-switch" checked>'
            )

        return EventSourceResponse(generator())
