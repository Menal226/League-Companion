import lcu
import uvicorn
import asyncio
import threading
import time
import webview
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from lobby.api import register as register_l
from default.api import register as register_def
from champ_select.api import register as register_cs


@asynccontextmanager
async def lifespan(app: FastAPI):
    lcu.set_main_loop(asyncio.get_running_loop())
    lcu.start()
    yield


def create_app() -> FastAPI:
    api = FastAPI()
    api.mount("/static", StaticFiles(directory="src/default"), name="static")
    api.mount("/assets", StaticFiles(directory="src/assets"), name="assets")
    register_cs(api)
    register_def(api)
    register_l(api)
    return api


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)


app = create_app()
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(1.5)
    window = webview.create_window(
        title="League Companion", url="http://127.0.0.1:8000", width=1280, height=800
    )
    webview.start()
