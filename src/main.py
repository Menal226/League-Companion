import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
import lcu
from frontend import create_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    lcu.set_main_loop(asyncio.get_running_loop())
    lcu.start()
    yield

app = create_app()
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)