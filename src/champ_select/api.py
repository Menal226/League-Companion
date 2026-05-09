import lcu
from fastapi import FastAPI

def register(app: FastAPI):
    @app.post("/champ-select/bench/swap/{champion_id}")
    async def swap_champ_from_bench(champion_id: int):
        await lcu.request("POST", f"/lol-champ-select/v1/session/bench/swap/{champion_id}")
