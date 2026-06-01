# /lol-game-data/assets/DATA/Spells/Icons2D/

import logging

CD_ADDR = "https://raw.communitydragon.org/latest/game/data/spells/icons2d/"
spell_names = {
    21: "summonerbarrier.png",
    1: "summoner_boost.png",
    14: "summonerignite.png",
    3: "summoner_exhaust.png",
    4: "summoner_flash.png",
    6: "summoner_haste.png",
    7: "summoner_heal.png",
    13: "summonermana.png",
    11: "summoner_smite.png",
    32: "summoner_mark.png",
    12: "summoner_teleport_new.png",
}

logger = logging.getLogger(__name__)


def get_spell_icon(spell_id: int):
    spell_path = spell_names.get(spell_id, "terrify.png")
    if spell_path == "terrify.png":
        logger.warning(f"Invalid spell id {spell_id}")

    return CD_ADDR + spell_path


def get_position_icon_path(position_name: str, disabled: bool = False):
    if position_name == "":
        logger.warning(f"Invalid position {position_name}")
        position_name = "none"
    return (
        f"/assets/positions/icon-{position_name}{"-disabled" if disabled else ""}.png"
    )
