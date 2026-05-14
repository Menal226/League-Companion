import lcu
from fastapi import FastAPI


def register(app: FastAPI):
    @app.post("/champ-select/bench/swap/{champion_id}")
    async def swap_champ_from_bench(champion_id: int):
        await lcu.request(
            "POST", f"/lol-champ-select/v1/session/bench/swap/{champion_id}"
        )

    @app.post("/champ-select/pick/{champion_id}")
    async def select_aram_champion(champion_id: int):
        session_resp = await lcu.request("GET", "/lol-champ-select/v1/session")
        session = await session_resp.json()
        my_cell_id = session["localPlayerCellId"]

        action = next(
            a
            for group in session["actions"]
            for a in group
            if a["actorCellId"] == my_cell_id and not a["completed"]
        )

        await lcu.request(
            "PATCH",
            f"/lol-champ-select/v1/session/actions/{action['id']}",
            json={
                "championId": champion_id,
                "completed": True,
            },
        )

        lcu.push(
            '<div id="aram-picks" hx-swap-oob="true" style="display: none;"></div>'
        )
