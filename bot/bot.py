# bot/bot.py
import discord
from discord.ext import commands
import asyncio
import sys
import traceback
from pathlib import Path

from .game_data import game, ROLES
from .utils import check_image_folder, reset_game, IMAGE_FOLDER

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
bot_initialized = False


@bot.event
async def on_ready():
    global bot_initialized
    await bot.tree.sync()
    print(f"[OK] Bot {bot.user} online!")
    print(f"[FOLDER] PIC: {'[FOUND]' if IMAGE_FOLDER.exists() else '[NOT FOUND]'}")
    print("=" * 50)
    print("[READY] GAME WEREWOLF READY!")
    print("[WARNING] WAJIB pilih moderator dengan /setmod terlebih dahulu!")
    print("Commands: /setmod, /start, /night, /kill, /terawang, /heal, /witch_status, /endnight, /vote, /end, /status, /guide")
    print("[SEER] Seer: /terawang (pilih target dari dropdown)")
    print("[WEREWOLF] Werewolf: /kill (pilih target dari dropdown)")
    print("[WITCH] Witch: /heal @pemain (selamatkan korban), /witch_status (cek status ramuan)")
    print("=" * 50)
    bot_initialized = True


def run_bot(token):
    global bot_initialized
    try:
        from .commands import setup_commands
        import importlib
        
        if bot_initialized:
            importlib.reload(sys.modules['.commands'])
        
        setup_commands(bot)
        bot.run(token, reconnect=True)
        
    except Exception as e:
        print(f"[ERROR] Bot error: {e}")
        print(traceback.format_exc())
        raise