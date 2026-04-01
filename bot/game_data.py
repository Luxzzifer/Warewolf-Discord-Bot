# bot/game_data.py
import discord
from typing import List, Dict, Optional

class GameData:
    def __init__(self):
        self.players: List[discord.Member] = []
        self.roles: Dict[int, str] = {}
        self.game_active: bool = False
        self.modal_channel: Optional[discord.TextChannel] = None
        self.moderator_id: Optional[int] = None
        self.moderator_name: Optional[str] = None
        self.votes: Dict[int, int] = {}
        self.vote_message: Optional[discord.Message] = None
        self.vote_ended: bool = False
        self.dead_players: List[int] = []
        self.night_kills: Dict[int, int] = {}
        self.night_phase: bool = False
        self.has_killed_this_night: bool = False
        self.tough_guy_hits: Dict[int, int] = {}
        self.seer_used: Dict[int, bool] = {}
        self.tough_guy_survived: List[int] = []
        
        # Fitur Witch
        self.witch_saved: bool = False  # Apakah ramuan penyelamat sudah digunakan
        self.witch_potion_save: Optional[int] = None  # ID player yang diselamatkan

game = GameData()

ROLES = {
    "warewolf": {
        "name": "🐺 Werewolf",
        "desc": "Dapat membunuh satu pemain setiap malam (hanya 1 Werewolf yang bisa membunuh per malam)",
        "image": "Warewolf.png",
        "alignment": "jahat"
    },
    "seer": {
        "name": "🔮 The Seer", 
        "desc": "Dapat melihat apakah seorang pemain Baik atau Jahat setiap malam",
        "image": "Seer.png",
        "alignment": "baik"
    },
    "tough_guy": {
        "name": "🛡️ Tough Guy",
        "desc": "Memiliki ketahanan ekstra, membutuhkan 2 kali pembunuhan",
        "image": "Tough_Guy.png",
        "alignment": "baik"
    },
    "witch": {
        "name": "🧙 WITCH",
        "desc": "Memiliki ramuan penyelamat (hanya 1 kali)",
        "image": "Witch.png",
        "alignment": "baik"
    },
    "laycan": {
        "name": "🌾 Laycan",
        "desc": "Warga desa biasa, tetapi saat diterawang Seer akan terlihat JAHAT",
        "image": "Laycan.png",
        "alignment": "baik"
    },
    "villager": {
        "name": "🏘️ Villager",
        "desc": "Warga desa biasa yang berusaha bertahan hidup",
        "image": "Villager.png",
        "alignment": "baik"
    }
}