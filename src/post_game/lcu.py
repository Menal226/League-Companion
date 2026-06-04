import logging
from lcu import push
from pathlib import Path

auto_accept = False
logger = logging.getLogger(__name__)


def switch_screen():
    logger.info("Switching to post game screen")
    push(open(Path("src/post_game/index.html"), encoding="utf-8").read())
