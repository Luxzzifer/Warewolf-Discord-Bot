# gui/styles.py
from tkinter import font


class Colors:
    # ── Backgrounds ──────────────────────────────────────────────
    BG_DARK        = '#0d1117'   # page bg
    BG_DARKER      = '#090c12'   # titlebar / footer
    BG_CARD        = '#161b27'   # card surface
    BG_CARD_HEADER = '#1c2333'   # card header strip
    BG_CONSOLE     = '#090c12'   # console area
    BG_INPUT       = '#0d1117'   # entry bg

    # ── Text ─────────────────────────────────────────────────────
    TEXT_WHITE      = '#e6edf3'
    TEXT_GRAY       = '#8b949e'
    TEXT_GRAY_LIGHT = '#6e7681'
    TEXT_GRAY_DARK  = '#3d444d'
    TEXT_ACCENT     = '#39d353'   # bright green for accent labels

    # ── Status / semantic ────────────────────────────────────────
    STATUS_ONLINE  = '#39d353'   # neon green
    STATUS_OFFLINE = '#f85149'   # vivid red
    STATUS_WARNING = '#e3b341'   # amber
    STATUS_INFO    = '#58a6ff'   # blue

    # ── Buttons ──────────────────────────────────────────────────
    BTN_SUCCESS   = '#238636'
    BTN_SUCCESS_HV= '#2ea043'
    BTN_DANGER    = '#da3633'
    BTN_DANGER_HV = '#f85149'
    BTN_WARNING   = '#9e6a03'
    BTN_WARNING_HV= '#e3b341'
    BTN_SECONDARY = '#21262d'
    BTN_SEC_HV    = '#30363d'

    # ── Borders ──────────────────────────────────────────────────
    BORDER        = '#30363d'
    BORDER_ACCENT = '#39d353'


class Fonts:
    """Lazy-cached font objects."""
    def __init__(self, root):
        self._cache: dict = {}

    def _get(self, key, family, size, weight="normal"):
        if key not in self._cache:
            self._cache[key] = font.Font(family=family, size=size, weight=weight)
        return self._cache[key]

    # Judul pakai Consolas biar feel terminal
    @property
    def title(self):    return self._get("title",    "Consolas",  16, "bold")
    @property
    def subtitle(self): return self._get("subtitle", "Segoe UI",   9)
    @property
    def button(self):   return self._get("button",   "Segoe UI",  10, "bold")
    @property
    def label(self):    return self._get("label",    "Segoe UI",  10, "bold")
    @property
    def status(self):   return self._get("status",   "Consolas",  11, "bold")
    @property
    def console(self):  return self._get("console",  "Consolas",   9)
    @property
    def mono_sm(self):  return self._get("mono_sm",  "Consolas",   8)
    @property
    def tag(self):      return self._get("tag",      "Consolas",   8)