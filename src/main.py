import lcu
import uvicorn
import asyncio
from fastapi import FastAPI
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
    register_cs(api)
    register_def(api)
    register_l(api)
    return api

app = create_app()
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)