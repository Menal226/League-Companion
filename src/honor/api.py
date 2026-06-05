import lcu
from fastapi import FastAPI


def register(app: FastAPI):
    @app.post("/honor/{game_id}/{puuid}/{summonerId}")
    async def honor_champ(game_id: int, puuid: str, summonerId: int):
        await lcu.request(
            "POST",
            "/lol-honor-v2/v1/honor-player",
            json={
                "summonerId": summonerId,
                "puuid": puuid,
                "honorType": "HEART",
                "gameId": game_id,
            },
        )
