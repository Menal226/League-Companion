import logging
from lcu import push
from pathlib import Path

logger = logging.getLogger(__name__)


def switch_screen():
    logger.info("Switching to ingame screen")
    push(open(Path("src/in_game/index.html"), encoding="utf-8").read())
