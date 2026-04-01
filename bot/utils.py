# bot/utils.py
import discord
import random
from pathlib import Path
from typing import List
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from .game_data import game, ROLES

IMAGE_FOLDER = Path(__file__).parent.parent / "Pic"


def is_moderator(interaction: discord.Interaction) -> bool:
    """Check if user is the game moderator."""
    return game.moderator_id is not None and interaction.user.id == game.moderator_id


def has_moderator() -> bool:
    """Check if a moderator has been selected."""
    return game.moderator_id is not None


def check_moderator_exists(interaction: discord.Interaction) -> bool:
    """Check if moderator exists and send error message if not."""
    if not has_moderator():
        embed = discord.Embed(
            title="⚠️ BELUM ADA MODERATOR",
            description="❌ **Game tidak dapat dimulai tanpa moderator!**\n\nSilakan gunakan `/setmod` terlebih dahulu.",
            color=discord.Color.red()
        )
        return False
    return True


def get_alive_players() -> List[discord.Member]:
    """Get list of alive players."""
    return [p for p in game.players if p.id not in game.dead_players]


def get_werewolves() -> List[discord.Member]:
    """Get list of alive werewolves."""
    return [p for p in get_alive_players() if game.roles.get(p.id) == "warewolf"]


def check_game_active(interaction: discord.Interaction) -> bool:
    """Check if game is active and user is in the game."""
    if not game.game_active:
        return False
    return any(p.id == interaction.user.id for p in game.players)


def get_alignment(role_key: str) -> str:
    """Get alignment of a role (baik/jahat)."""
    return ROLES.get(role_key, {}).get("alignment", "baik")


def check_image_folder():
    """Check image folder and return status."""
    status = {"folder_exists": False, "images": {}}
    
    if IMAGE_FOLDER.exists():
        status["folder_exists"] = True
        for role_key, role_data in ROLES.items():
            image_path = IMAGE_FOLDER / role_data['image']
            status["images"][role_key] = image_path.exists()
    else:
        status["folder_exists"] = False
        
    return status


def generate_roles(player_count: int) -> List[str]:
    """Generate role list based on player count."""
    configs = {
        10: ['warewolf']*2 + ['seer']*1 + ['tough_guy']*1 + ['witch']*1 + ['laycan']*2 + ['villager']*3,
        9: ['warewolf']*2 + ['seer']*1 + ['tough_guy']*1 + ['witch']*1 + ['laycan']*2 + ['villager']*2,
        8: ['warewolf']*2 + ['seer']*1 + ['tough_guy']*1 + ['witch']*1 + ['laycan']*1 + ['villager']*2,
        7: ['warewolf']*2 + ['seer']*1 + ['tough_guy']*1 + ['witch']*1 + ['villager']*2,
        6: ['warewolf']*2 + ['seer']*1 + ['tough_guy']*1 + ['villager']*2,
        5: ['warewolf']*2 + ['seer']*1 + ['villager']*2,
        4: ['warewolf']*2 + ['villager']*2,
        3: ['warewolf']*1 + ['villager']*2
    }
    
    if player_count in configs:
        return configs[player_count]
    
    werewolf_count = max(2, min(4, player_count // 4))
    seer_count = 1 if player_count >= 5 else 0
    tough_guy_count = 1 if player_count >= 6 else 0
    witch_count = 1 if player_count >= 7 else 0
    laycan_count = max(0, (player_count - werewolf_count - seer_count - tough_guy_count - witch_count) // 2)
    villager_count = player_count - werewolf_count - seer_count - tough_guy_count - witch_count - laycan_count
    
    return (['warewolf'] * werewolf_count + ['seer'] * seer_count + 
            ['tough_guy'] * tough_guy_count + ['witch'] * witch_count + 
            ['laycan'] * laycan_count + ['villager'] * villager_count)


async def send_role_dm(player: discord.Member, role_key: str):
    """Send role information to player via DM."""
    role_data = ROLES[role_key]
    embed = discord.Embed(
        title="🎭 ROLE ANDA",
        description=f"Anda adalah **{role_data['name']}**",
        color=discord.Color.green()
    )
    embed.add_field(name="⚔️ KEMAMPUAN", value=role_data['desc'], inline=False)
    
    if role_key == "warewolf":
        embed.add_field(
            name="🐺 COMMAND KHUSUS WEREWOLF", 
            value="Gunakan `/kill` untuk membuka menu pilih target yang akan dibunuh!\n\n⚠️ **CATATAN:**\n• **Hanya SATU Werewolf yang bisa membunuh per malam!**", 
            inline=False
        )
    elif role_key == "seer":
        embed.add_field(
            name="🔮 COMMAND KHUSUS SEER", 
            value="Gunakan `/terawang` untuk membuka menu pilih target yang akan diterawang!\n⚠️ **Hanya bisa digunakan SEKALI per malam!**", 
            inline=False
        )
    elif role_key == "witch":
        embed.add_field(
            name="🧙 COMMAND KHUSUS WITCH", 
            value="Anda memiliki **RAMUAN PENYELAMAT** yang dapat digunakan **SEKALI**!\n\n📝 **CARA MENGGUNAKAN:**\n• Gunakan `/heal @pemain` untuk menyelamatkan pemain yang mati\n• Hanya bisa digunakan **SATU KALI** sepanjang game\n• Hanya bisa digunakan saat **FASE MALAM**\n• Cek status ramuan dengan `/witch_status`\n\n⚠️ **PENTING:** Pilih dengan bijak kapan menggunakan ramuan!", 
            inline=False
        )
    elif role_key == "laycan":
        embed.add_field(
            name="🌾 COMMAND KHUSUS LAYCAN", 
            value="Anda adalah **LAYCAN** - Warga desa biasa.\n\n⚠️ **CATATAN PENTING:**\n• Anda **BUKAN** penghianat\n• Anda adalah warga desa biasa\n• **TAPI** saat diterawang oleh Seer, Anda akan terlihat sebagai **JAHAT**\n• Ini adalah kemampuan khusus Anda untuk melindungi Werewolf\n• Jangan sampai ketahuan oleh warga!", 
            inline=False
        )
    
    embed.set_footer(text="JANGAN BERITAHU ROLE ANDA!")
    
    image_path = IMAGE_FOLDER / role_data['image']
    if image_path.exists():
        file = discord.File(image_path, filename=role_data['image'])
        embed.set_image(url=f"attachment://{role_data['image']}")
        await player.send(file=file, embed=embed)
    else:
        await player.send(embed=embed)


async def reset_game():
    """Reset all game data."""
    game.players.clear()
    game.roles.clear()
    game.game_active = False
    game.modal_channel = None
    game.votes.clear()
    game.vote_message = None
    game.vote_ended = False
    game.dead_players.clear()
    game.night_kills.clear()
    game.night_phase = False
    game.has_killed_this_night = False
    game.tough_guy_hits.clear()
    game.seer_used.clear()
    game.tough_guy_survived.clear()
    game.witch_saved = False
    game.witch_potion_save = None


async def check_winner(interaction: discord.Interaction) -> bool:
    """Check if game has ended and announce winner."""
    alive_players = get_alive_players()
    werewolf_alive = any(game.roles[p.id] == "warewolf" for p in alive_players)
    
    evil_count = len([p for p in alive_players if game.roles.get(p.id) in ["warewolf"]])
    good_count = len(alive_players) - evil_count
    
    if evil_count >= good_count:
        winner_embed = discord.Embed(
            title="🏆 GAME BERAKHIR",
            description="**WEREWOLF MENANG!** Werewolf berhasil menguasai desa!",
            color=discord.Color.dark_red()
        )
        await interaction.channel.send(embed=winner_embed)
        await reset_game()
        return True
    elif not werewolf_alive:
        winner_embed = discord.Embed(
            title="🏆 GAME BERAKHIR",
            description="**WARGA MENANG!** Semua Werewolf telah mati!",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=winner_embed)
        await reset_game()
        return True
    return False