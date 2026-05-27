# gui/components.py
"""
Komponen UI untuk Werewolf Bot GUI.
Semua komponen menggunakan flat tk widgets — tidak ada ttk kecuali Combobox —
agar performa konsisten di semua OS dan theme system tidak ikut campur.
"""
import tkinter as tk
from .styles import Colors


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _darken(hex_color: str, amount: int = 25) -> str:
    r = max(0, int(hex_color[1:3], 16) - amount)
    g = max(0, int(hex_color[3:5], 16) - amount)
    b = max(0, int(hex_color[5:7], 16) - amount)
    return f'#{r:02x}{g:02x}{b:02x}'


def _card(parent, **kw) -> tk.Frame:
    """Buat frame kartu dengan border tipis."""
    return tk.Frame(
        parent,
        bg=kw.pop("bg", Colors.BG_CARD),
        highlightthickness=1,
        highlightbackground=Colors.BORDER,
        **kw
    )


def _card_header(parent, text, fonts) -> tk.Frame:
    """Strip header kartu dengan label."""
    hdr = tk.Frame(parent, bg=Colors.BG_CARD_HEADER, height=32)
    hdr.pack(fill=tk.X)
    hdr.pack_propagate(False)

    # accent bar kiri
    tk.Frame(hdr, bg=Colors.BORDER_ACCENT, width=3).pack(side=tk.LEFT, fill=tk.Y)

    tk.Label(
        hdr, text=text,
        font=fonts.label,
        bg=Colors.BG_CARD_HEADER,
        fg=Colors.TEXT_WHITE,
        padx=10,
    ).pack(side=tk.LEFT, pady=0)

    return hdr


# ─────────────────────────────────────────────────────────────────────────────
# ModernButton
# ─────────────────────────────────────────────────────────────────────────────

class ModernButton(tk.Button):
    """Tombol dengan hover effect dan disabled state yang jelas."""

    def __init__(self, parent, text, color, hover_color, command,
                 state=tk.NORMAL, **kwargs):
        super().__init__(
            parent,
            text=text,
            bg=color if state == tk.NORMAL else Colors.BTN_SECONDARY,
            fg=Colors.TEXT_WHITE if state == tk.NORMAL else Colors.TEXT_GRAY_LIGHT,
            activebackground=hover_color,
            activeforeground=Colors.TEXT_WHITE,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=7,
            cursor='hand2' if state == tk.NORMAL else 'arrow',
            command=command,
            state=state,
            font=kwargs.pop("font", ("Segoe UI", 9, "bold")),
            highlightthickness=1,
            highlightbackground=_darken(color, 40) if state == tk.NORMAL else Colors.BORDER,
            **kwargs,
        )
        self._active_color  = color
        self._active_hover  = hover_color
        self._active_hl     = _darken(color, 40)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    # Override config agar state bisa diubah dan tampilan ikut berubah
    def config(self, **kw):
        if "state" in kw:
            new_state = kw["state"]
            if new_state == tk.DISABLED:
                kw.setdefault("bg", Colors.BTN_SECONDARY)
                kw.setdefault("fg", Colors.TEXT_GRAY_LIGHT)
                kw.setdefault("highlightbackground", Colors.BORDER)
                kw.setdefault("cursor", "arrow")
            elif new_state == tk.NORMAL:
                kw.setdefault("bg", self._active_color)
                kw.setdefault("fg", Colors.TEXT_WHITE)
                kw.setdefault("highlightbackground", self._active_hl)
                kw.setdefault("cursor", "hand2")
        super().config(**kw)

    def _on_enter(self, _e):
        if str(self["state"]) != tk.DISABLED:
            self.config(bg=self._active_hover)

    def _on_leave(self, _e):
        if str(self["state"]) != tk.DISABLED:
            self.config(bg=self._active_color)


# ─────────────────────────────────────────────────────────────────────────────
# TokenCard
# ─────────────────────────────────────────────────────────────────────────────

class TokenCard(tk.Frame):
    def __init__(self, parent, colors, fonts, lang_manager,
                 show_token_var, toggle_token_cmd):
        super().__init__(parent, bg=Colors.BG_CARD,
                         highlightthickness=1, highlightbackground=Colors.BORDER)
        self.colors = colors
        self.fonts  = fonts
        self.lang   = lang_manager
        self.show_token_var    = show_token_var
        self.toggle_token_cmd  = toggle_token_cmd
        self.token_entry       = None
        self._build()

    def _build(self):
        self._hdr = _card_header(self, self.lang.get("bot_config"), self.fonts)

        body = tk.Frame(self, bg=Colors.BG_CARD, padx=12, pady=10)
        body.pack(fill=tk.X)

        self._token_lbl = tk.Label(
            body, text=self.lang.get("token_label"),
            font=self.fonts.mono_sm, bg=Colors.BG_CARD, fg=Colors.TEXT_GRAY,
            anchor="w",
        )
        self._token_lbl.pack(fill=tk.X)

        # Entry dengan highlight border
        entry_wrap = tk.Frame(
            body, bg=Colors.BORDER_ACCENT,
            highlightthickness=0, pady=1, padx=1,
        )
        entry_wrap.pack(fill=tk.X, pady=(4, 6))

        self.token_entry = tk.Entry(
            entry_wrap,
            font=("Consolas", 10),
            bg=Colors.BG_INPUT,
            fg=Colors.TEXT_WHITE,
            insertbackground=Colors.STATUS_ONLINE,
            relief=tk.FLAT,
            bd=0,
            show="*",
        )
        self.token_entry.pack(fill=tk.X, ipady=7, padx=1, pady=1)

        # Show token + warning baris
        bottom = tk.Frame(body, bg=Colors.BG_CARD)
        bottom.pack(fill=tk.X)

        self._show_cb = tk.Checkbutton(
            bottom,
            text=self.lang.get("show_token"),
            variable=self.show_token_var,
            command=self.toggle_visibility,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_GRAY,
            selectcolor=Colors.BG_CARD_HEADER,
            activebackground=Colors.BG_CARD,
            activeforeground=Colors.TEXT_GRAY,
            cursor="hand2",
            font=self.fonts.subtitle,
        )
        self._show_cb.pack(side=tk.LEFT)

        self._warn_lbl = tk.Label(
            bottom,
            text=self.lang.get("warning_text"),
            font=self.fonts.subtitle,
            bg=Colors.BG_CARD,
            fg=Colors.STATUS_WARNING,
        )
        self._warn_lbl.pack(side=tk.RIGHT)

        self._help_lbl = tk.Label(
            body,
            text=self.lang.get("help_text"),
            font=self.fonts.subtitle,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_GRAY_LIGHT,
            anchor="w",
        )
        self._help_lbl.pack(fill=tk.X, pady=(4, 0))

    # ── public API ───────────────────────────────────────────────

    def update_language(self):
        for child in self._hdr.winfo_children():
            if isinstance(child, tk.Label):
                child.config(text=self.lang.get("bot_config"))
                break
        self._token_lbl.config(text=self.lang.get("token_label"))
        self._show_cb.config(text=self.lang.get("show_token"))
        self._warn_lbl.config(text=self.lang.get("warning_text"))
        self._help_lbl.config(text=self.lang.get("help_text"))

    def toggle_visibility(self):
        if self.token_entry:
            self.token_entry.config(show="" if self.show_token_var.get() else "*")

    def get_token(self) -> str:
        return self.token_entry.get().strip() if self.token_entry else ""

    def set_disabled(self, disabled: bool):
        if self.token_entry:
            self.token_entry.config(state=tk.DISABLED if disabled else tk.NORMAL)


# ─────────────────────────────────────────────────────────────────────────────
# StatusCard
# ─────────────────────────────────────────────────────────────────────────────

class StatusCard(tk.Frame):
    _STATES = {
        "online":  ("STATUS_ONLINE",  "status_online",  "detail_running"),
        "offline": ("STATUS_OFFLINE", "status_offline", "detail_not_running"),
        "error":   ("STATUS_WARNING", "status_error",   "detail_error"),
    }

    def __init__(self, parent, colors, fonts, lang_manager):
        super().__init__(parent, bg=Colors.BG_CARD,
                         highlightthickness=1, highlightbackground=Colors.BORDER)
        self.colors = colors
        self.fonts  = fonts
        self.lang   = lang_manager
        self._state = "offline"
        self._build()

    def _build(self):
        self._hdr = _card_header(self, self.lang.get("system_status"), self.fonts)

        body = tk.Frame(self, bg=Colors.BG_CARD, padx=12, pady=10)
        body.pack(fill=tk.X)

        row = tk.Frame(body, bg=Colors.BG_CARD)
        row.pack(anchor="w")

        # Dot canvas
        self._cv = tk.Canvas(row, width=10, height=10,
                             bg=Colors.BG_CARD, highlightthickness=0)
        self._cv.pack(side=tk.LEFT, padx=(0, 8))
        self._dot = self._cv.create_oval(1, 1, 9, 9,
                                         fill=Colors.STATUS_OFFLINE, outline="")

        self._status_lbl = tk.Label(
            row, text=self.lang.get("status_offline"),
            font=self.fonts.status, bg=Colors.BG_CARD, fg=Colors.STATUS_OFFLINE,
        )
        self._status_lbl.pack(side=tk.LEFT)

        self._detail_lbl = tk.Label(
            body, text=self.lang.get("detail_not_running"),
            font=self.fonts.subtitle, bg=Colors.BG_CARD, fg=Colors.TEXT_GRAY_LIGHT,
        )
        self._detail_lbl.pack(anchor="w", pady=(4, 0))

    def _apply(self, state: str):
        self._state = state
        color_key, status_key, detail_key = self._STATES[state]
        color = getattr(Colors, color_key)
        self._cv.itemconfig(self._dot, fill=color)
        self._status_lbl.config(text=self.lang.get(status_key), fg=color)
        self._detail_lbl.config(text=self.lang.get(detail_key))

    def set_online(self):  self._apply("online")
    def set_offline(self): self._apply("offline")
    def set_error(self):   self._apply("error")

    def update_language(self):
        for child in self._hdr.winfo_children():
            if isinstance(child, tk.Label):
                child.config(text=self.lang.get("system_status"))
                break
        self._apply(self._state)


# ─────────────────────────────────────────────────────────────────────────────
# NetworkStatusCard
# ─────────────────────────────────────────────────────────────────────────────

class NetworkStatusCard(tk.Frame):
    def __init__(self, parent, colors, fonts, lang_manager):
        super().__init__(parent, bg=Colors.BG_CARD,
                         highlightthickness=1, highlightbackground=Colors.BORDER)
        self.colors = colors
        self.fonts  = fonts
        self.lang   = lang_manager
        self.auto_monitor_var = tk.BooleanVar(value=True)
        self._current_status  = None
        self._build()

    def _build(self):
        self._hdr = _card_header(self, self.lang.get("network_status"), self.fonts)

        body = tk.Frame(self, bg=Colors.BG_CARD, padx=12, pady=10)
        body.pack(fill=tk.X)

        # Status row
        row = tk.Frame(body, bg=Colors.BG_CARD)
        row.pack(fill=tk.X, pady=(0, 4))

        self._cv = tk.Canvas(row, width=10, height=10,
                             bg=Colors.BG_CARD, highlightthickness=0)
        self._cv.pack(side=tk.LEFT, padx=(0, 8))
        self._dot = self._cv.create_oval(1, 1, 9, 9,
                                         fill=Colors.STATUS_OFFLINE, outline="")

        self._lbl = tk.Label(
            row, text=self.lang.get("checking"),
            font=self.fonts.subtitle, bg=Colors.BG_CARD, fg=Colors.TEXT_GRAY_LIGHT,
        )
        self._lbl.pack(side=tk.LEFT)

        self._detail = tk.Label(
            body, text="",
            font=self.fonts.subtitle, bg=Colors.BG_CARD, fg=Colors.TEXT_GRAY_LIGHT,
        )
        self._detail.pack(anchor="w", pady=(0, 6))

        # Bottom row: check btn + auto monitor
        btn_row = tk.Frame(body, bg=Colors.BG_CARD)
        btn_row.pack(fill=tk.X)

        self.check_btn = tk.Button(
            btn_row,
            text=self.lang.get("check_connection"),
            bg=Colors.BTN_SECONDARY, fg=Colors.TEXT_WHITE,
            activebackground=Colors.BTN_SEC_HV, activeforeground=Colors.TEXT_WHITE,
            relief=tk.FLAT, bd=0, padx=10, pady=4,
            font=self.fonts.subtitle, cursor="hand2",
            highlightthickness=1, highlightbackground=Colors.BORDER,
        )
        self.check_btn.pack(side=tk.LEFT)
        self.check_btn.bind("<Enter>", lambda _: self.check_btn.config(bg=Colors.BTN_SEC_HV))
        self.check_btn.bind("<Leave>", lambda _: self.check_btn.config(bg=Colors.BTN_SECONDARY))

        self._auto_cb = tk.Checkbutton(
            btn_row,
            text=self.lang.get("auto_monitor"),
            variable=self.auto_monitor_var,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_GRAY,
            selectcolor=Colors.BG_CARD_HEADER,
            activebackground=Colors.BG_CARD,
            activeforeground=Colors.TEXT_GRAY,
            cursor="hand2",
            font=self.fonts.subtitle,
        )
        self._auto_cb.pack(side=tk.LEFT, padx=8)

    def update_status(self, status):
        self._current_status = status
        if status["internet"]:
            self._cv.itemconfig(self._dot, fill=Colors.STATUS_ONLINE)
            self._lbl.config(text=self.lang.get("internet_online"), fg=Colors.STATUS_ONLINE)
            self._detail.config(text=self.lang.get("internet_connected"), fg=Colors.STATUS_ONLINE)
        else:
            self._cv.itemconfig(self._dot, fill=Colors.STATUS_OFFLINE)
            self._lbl.config(text=self.lang.get("internet_offline"), fg=Colors.STATUS_OFFLINE)
            self._detail.config(text=self.lang.get("internet_disconnected"), fg=Colors.STATUS_OFFLINE)

    def update_language(self):
        for child in self._hdr.winfo_children():
            if isinstance(child, tk.Label):
                child.config(text=self.lang.get("network_status"))
                break
        self.check_btn.config(text=self.lang.get("check_connection"))
        self._auto_cb.config(text=self.lang.get("auto_monitor"))
        if self._current_status is not None:
            self.update_status(self._current_status)
        else:
            self._lbl.config(text=self.lang.get("checking"))