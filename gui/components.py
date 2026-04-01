# gui/components.py
import tkinter as tk
from .styles import Colors


class ModernButton(tk.Button):
    """Custom modern button with hover effect"""
    def __init__(self, parent, text, color, command, state=tk.NORMAL, **kwargs):
        super().__init__(
            parent, text=text, bg=color, fg='white', relief=tk.FLAT,
            bd=0, padx=15, pady=8, cursor='hand2', command=command,
            state=state, **kwargs
        )
        self.default_bg = color
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg=self.darken_color(self.default_bg))

    def on_leave(self, e):
        self.config(bg=self.default_bg)

    @staticmethod
    def darken_color(color):
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f'#{max(0, r-30):02x}{max(0, g-30):02x}{max(0, b-30):02x}'
        return color


class NetworkStatusCard(tk.Frame):
    def __init__(self, parent, colors, fonts, lang_manager):
        super().__init__(parent, bg=colors.BG_CARD, relief=tk.RAISED, bd=1)
        self.colors = colors
        self.fonts = fonts
        self.lang = lang_manager
        self.auto_monitor_var = tk.BooleanVar(value=True)
        self._current_status = None
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self, bg=self.colors.BG_CARD_HEADER, height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        self.header_label = tk.Label(header, text=self.lang.get("network_status"),
                                     font=self.fonts.label, bg=self.colors.BG_CARD_HEADER,
                                     fg=self.colors.TEXT_WHITE)
        self.header_label.pack(expand=True, pady=8)

        content = tk.Frame(self, bg=self.colors.BG_CARD, padx=15, pady=10)
        content.pack(fill=tk.X)

        indicator_frame = tk.Frame(content, bg=self.colors.BG_CARD)
        indicator_frame.pack(fill=tk.X, pady=5)

        self.canvas = tk.Canvas(indicator_frame, width=10, height=10,
                                bg=self.colors.BG_CARD, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.dot = self.canvas.create_oval(2, 2, 8, 8, fill=self.colors.STATUS_OFFLINE, outline='')

        self.label = tk.Label(indicator_frame, text=self.lang.get("checking"),
                              font=self.fonts.subtitle, bg=self.colors.BG_CARD,
                              fg=self.colors.TEXT_GRAY_LIGHT)
        self.label.pack(side=tk.LEFT)

        self.detail = tk.Label(content, text="", font=self.fonts.subtitle,
                               bg=self.colors.BG_CARD, fg=self.colors.TEXT_GRAY_LIGHT)
        self.detail.pack(pady=2)

        btn_frame = tk.Frame(content, bg=self.colors.BG_CARD)
        btn_frame.pack(pady=5)

        self.check_btn = tk.Button(btn_frame, text=self.lang.get("check_connection"),
                                   bg=self.colors.BTN_SECONDARY, fg='white',
                                   font=("Segoe UI", 8), padx=10, cursor='hand2')
        self.check_btn.pack(side=tk.LEFT, padx=2)

        self.auto_monitor_cb = tk.Checkbutton(btn_frame, text=self.lang.get("auto_monitor"),
                                              variable=self.auto_monitor_var,
                                              bg=self.colors.BG_CARD, fg=self.colors.TEXT_GRAY_LIGHT,
                                              cursor='hand2')
        self.auto_monitor_cb.pack(side=tk.LEFT, padx=5)

    def update_language(self):
        self.header_label.config(text=self.lang.get("network_status"))
        self.check_btn.config(text=self.lang.get("check_connection"))
        self.auto_monitor_cb.config(text=self.lang.get("auto_monitor"))
        if self._current_status is not None:
            self.update_status(self._current_status)
        else:
            self.label.config(text=self.lang.get("checking"))

    def update_status(self, status):
        self._current_status = status
        if status["internet"]:
            self.canvas.itemconfig(self.dot, fill=self.colors.STATUS_ONLINE)
            self.label.config(text=self.lang.get("internet_online"), fg=self.colors.STATUS_ONLINE)
            self.detail.config(text=self.lang.get("internet_connected"), fg=self.colors.STATUS_ONLINE)
        else:
            self.canvas.itemconfig(self.dot, fill=self.colors.STATUS_OFFLINE)
            self.label.config(text=self.lang.get("internet_offline"), fg=self.colors.STATUS_OFFLINE)
            self.detail.config(text=self.lang.get("internet_disconnected"), fg=self.colors.STATUS_OFFLINE)


class StatusCard(tk.Frame):
    def __init__(self, parent, colors, fonts, lang_manager):
        super().__init__(parent, bg=colors.BG_CARD, relief=tk.RAISED, bd=1)
        self.colors = colors
        self.fonts = fonts
        self.lang = lang_manager
        self._state = "offline"
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self, bg=self.colors.BG_CARD_HEADER, height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        self.header_label = tk.Label(header, text=self.lang.get("system_status"),
                                     font=self.fonts.label, bg=self.colors.BG_CARD_HEADER,
                                     fg=self.colors.TEXT_WHITE)
        self.header_label.pack(expand=True, pady=8)

        content = tk.Frame(self, bg=self.colors.BG_CARD, padx=15, pady=15)
        content.pack(fill=tk.X)

        indicator_frame = tk.Frame(content, bg=self.colors.BG_CARD)
        indicator_frame.pack(pady=5)

        self.canvas = tk.Canvas(indicator_frame, width=12, height=12,
                                bg=self.colors.BG_CARD, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.dot = self.canvas.create_oval(2, 2, 10, 10, fill=self.colors.STATUS_OFFLINE, outline='')

        self.status_label = tk.Label(indicator_frame, text=self.lang.get("status_offline"),
                                     font=self.fonts.status, fg=self.colors.STATUS_OFFLINE,
                                     bg=self.colors.BG_CARD)
        self.status_label.pack(side=tk.LEFT)

        self.detail_label = tk.Label(content, text=self.lang.get("detail_not_running"),
                                     bg=self.colors.BG_CARD, fg=self.colors.TEXT_GRAY_LIGHT,
                                     font=self.fonts.subtitle)
        self.detail_label.pack(pady=5)

    def update_language(self):
        self.header_label.config(text=self.lang.get("system_status"))
        self._update_state()

    def set_online(self):
        self.canvas.itemconfig(self.dot, fill=self.colors.STATUS_ONLINE)
        self.status_label.config(text=self.lang.get("status_online"), fg=self.colors.STATUS_ONLINE)
        self.detail_label.config(text=self.lang.get("detail_running"))
        self._state = "online"

    def set_offline(self):
        self.canvas.itemconfig(self.dot, fill=self.colors.STATUS_OFFLINE)
        self.status_label.config(text=self.lang.get("status_offline"), fg=self.colors.STATUS_OFFLINE)
        self.detail_label.config(text=self.lang.get("detail_not_running"))
        self._state = "offline"

    def set_error(self):
        self.canvas.itemconfig(self.dot, fill=self.colors.STATUS_WARNING)
        self.status_label.config(text=self.lang.get("status_error"), fg=self.colors.STATUS_WARNING)
        self.detail_label.config(text=self.lang.get("detail_error"))
        self._state = "error"

    def _update_state(self):
        if self._state == "online":
            self.set_online()
        elif self._state == "offline":
            self.set_offline()
        elif self._state == "error":
            self.set_error()


class TokenCard(tk.Frame):
    def __init__(self, parent, colors, fonts, lang_manager, show_token_var, toggle_token_cmd):
        super().__init__(parent, bg=colors.BG_CARD, relief=tk.RAISED, bd=1)
        self.colors = colors
        self.fonts = fonts
        self.lang = lang_manager
        self.show_token_var = show_token_var
        self.toggle_token_cmd = toggle_token_cmd
        self.token_entry = None
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self, bg=self.colors.BG_CARD_HEADER, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        self.header_label = tk.Label(header, text=self.lang.get("bot_config"),
                                     font=self.fonts.label, bg=self.colors.BG_CARD_HEADER,
                                     fg=self.colors.TEXT_WHITE)
        self.header_label.pack(expand=True, pady=10)

        content = tk.Frame(self, bg=self.colors.BG_CARD, padx=15, pady=15)
        content.pack(fill=tk.X)

        label_frame = tk.Frame(content, bg=self.colors.BG_CARD)
        label_frame.pack(fill=tk.X, pady=(0, 5))
        self.token_label = tk.Label(label_frame, text=self.lang.get("token_label"),
                                    font=self.fonts.label, bg=self.colors.BG_CARD,
                                    fg=self.colors.TEXT_GRAY)
        self.token_label.pack(anchor=tk.W)

        self.token_entry = tk.Entry(content, font=("Consolas", 11),
                                    bg=self.colors.BG_DARK, fg=self.colors.TEXT_WHITE,
                                    insertbackground=self.colors.STATUS_ONLINE,
                                    relief=tk.FLAT, bd=1, highlightthickness=2,
                                    highlightcolor=self.colors.STATUS_ONLINE)
        self.token_entry.pack(fill=tk.X, pady=(5, 8), ipady=10)

        help_frame = tk.Frame(content, bg=self.colors.BG_CARD)
        help_frame.pack(fill=tk.X, pady=(0, 8))
        self.help_label = tk.Label(help_frame, text=self.lang.get("help_text"),
                                   font=self.fonts.subtitle, bg=self.colors.BG_CARD,
                                   fg=self.colors.TEXT_GRAY_LIGHT)
        self.help_label.pack(anchor=tk.W)

        checkbox_frame = tk.Frame(content, bg=self.colors.BG_CARD)
        checkbox_frame.pack(anchor=tk.W, pady=(0, 5))
        self.show_token_cb = tk.Checkbutton(checkbox_frame, text=self.lang.get("show_token"),
                                            variable=self.show_token_var,
                                            command=self.toggle_visibility,
                                            bg=self.colors.BG_CARD, fg=self.colors.TEXT_GRAY_LIGHT,
                                            selectcolor=self.colors.BG_CARD, cursor='hand2',
                                            font=self.fonts.subtitle)
        self.show_token_cb.pack(side=tk.LEFT)

        warning_frame = tk.Frame(content, bg=self.colors.BG_CARD)
        warning_frame.pack(fill=tk.X, pady=(5, 0))
        self.warning_label = tk.Label(warning_frame, text=self.lang.get("warning_text"),
                                      font=self.fonts.subtitle, bg=self.colors.BG_CARD,
                                      fg=self.colors.STATUS_WARNING)
        self.warning_label.pack(anchor=tk.W)

        separator = tk.Frame(self, bg=self.colors.BG_CARD_HEADER, height=1)
        separator.pack(fill=tk.X, side=tk.BOTTOM)

    def update_language(self):
        self.header_label.config(text=self.lang.get("bot_config"))
        self.token_label.config(text=self.lang.get("token_label"))
        self.help_label.config(text=self.lang.get("help_text"))
        self.show_token_cb.config(text=self.lang.get("show_token"))
        self.warning_label.config(text=self.lang.get("warning_text"))

    def toggle_visibility(self):
        if self.token_entry:
            self.token_entry.config(show="" if self.show_token_var.get() else "*")

    def get_token(self):
        return self.token_entry.get().strip() if self.token_entry else ""

    def set_disabled(self, disabled):
        if self.token_entry:
            self.token_entry.config(state=tk.DISABLED if disabled else tk.NORMAL)