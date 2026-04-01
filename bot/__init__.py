# bot/__init__.py
"""
Werewolf Bot Package
"""

from .game_data import game, ROLES
from .bot import run_bot

__all__ = ['game', 'ROLES', 'run_bot']