import lcu
import uvicorn
import asyncio
import threading
import time
import webview
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
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
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)


def setup_logging() -> None:
    logs_dir = Path("logging")
    logs_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    formatter = logging.Formatter(
        fmt="[%(asctime)s] - %(levelname)-8s: %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        logs_dir / "companion.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Companion...")
    app = create_app()
    app.router.lifespan_context = lifespan
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(1.5)
    window = webview.create_window(
        title="League Companion", url="http://127.0.0.1:8000", width=1280, height=800
    )
    logger.info("Companion Started!")
    webview.start()
