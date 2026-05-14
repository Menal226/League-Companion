# /lol-game-data/assets/DATA/Spells/Icons2D/

CD_ADDR = "https://raw.communitydragon.org/latest/game/data/spells/icons2d/"
names = {
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


def get_icon(spell_id: int):
    return CD_ADDR + names.get(spell_id, "terrify.png")
