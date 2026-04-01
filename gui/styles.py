# gui/styles.py
from tkinter import font

class Colors:
    """Warna-warna untuk GUI"""
    # Background colors
    BG_DARK = '#1a1e2c'
    BG_DARKER = '#0f1119'
    BG_CARD = '#242a3e'
    BG_CARD_HEADER = '#2a3148'
    BG_CONSOLE = '#0d1117'
    
    # Text colors
    TEXT_WHITE = '#ffffff'
    TEXT_GRAY = '#c9d1d9'
    TEXT_GRAY_LIGHT = '#8a8f9e'
    TEXT_GRAY_DARK = '#5a5f73'
    
    # Status colors
    STATUS_ONLINE = '#43b581'
    STATUS_OFFLINE = '#f04747'
    STATUS_WARNING = '#faa61a'
    STATUS_INFO = '#61afef'
    
    # Button colors
    BTN_SUCCESS = '#43b581'
    BTN_DANGER = '#f04747'
    BTN_WARNING = '#faa61a'
    BTN_SECONDARY = '#4a5568'


class Fonts:
    """Font untuk GUI"""
    def __init__(self, root):
        self.title = font.Font(family="Segoe UI", size=22, weight="bold")
        self.subtitle = font.Font(family="Segoe UI", size=10)
        self.button = font.Font(family="Segoe UI", size=11, weight="bold")
        self.label = font.Font(family="Segoe UI", size=10)
        self.status = font.Font(family="Segoe UI", size=12, weight="bold")
        self.console = font.Font(family="Consolas", size=9)