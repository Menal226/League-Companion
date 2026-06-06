import lcu
import logging
from enum import Enum
from typing import Any

SETTING_SLUG = "Menal-League-Companion"
logger = logging.getLogger(__name__)


class Setting(Enum):
    AUTO_ACCEPT_QUEUE = "autoAcceptQueue"
    SKIP_POST_GAME_HONOR = "skipPostGameHonor"
    AUTO_HONOR_LOBBY_POST_GAME = "autoHonorLobbyPostGame"

    def __str__(self) -> str:
        return self.value


async def get_setting(setting: Setting) -> None | Any:
    try:
        resp = await lcu.request("get", f"/lol-settings/v1/local/{SETTING_SLUG}")
        if resp.status != 200:
            logger.warning(f"Cannot get value for setting {setting}")
            return None
        data = await resp.json()
        return data["data"].get(str(setting), None)
    except Exception:
        logger.exception(f"Exception trying to get value for setting {setting}")
        return None


async def set_setting(setting: Setting, value: Any) -> bool:
    try:
        await lcu.request(
            "patch",
            f"/lol-settings/v1/local/{SETTING_SLUG}",
            json={"schemaVersion": 1, "data": {str(setting): value}},
        )
        return True
    except Exception:
        logger.exception(f"Exception trying to set value for {setting}")
        return False
