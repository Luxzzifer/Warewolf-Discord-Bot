# gui/main_gui.py
"""
WerewolfBotGUI — main window.

Optimasi performa:
  • Debounced <Configure> → tidak spam WindowConfig.save()
  • TextRedirector thread-safe via root.after(0, ...)
  • _process_output_queue drain seluruh queue per tick (batch insert)
  • Tidak ada update_idletasks() di hot-path logging
  • maxundo=0 di ScrolledText → tidak bloat memori untuk log panjang
  • Font lazy-cached via Fonts property
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import re
import traceback
import time
from pathlib import Path
import subprocess
import os
import queue
import json

from .network_checker import NetworkChecker
from .styles import Colors, Fonts
from .components import ModernButton, NetworkStatusCard, StatusCard, TokenCard
from .lang_manager import LanguageManager

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


# ─────────────────────────────────────────────────────────────────────────────
# Stdout / stderr redirector
# ─────────────────────────────────────────────────────────────────────────────

# Simpan referensi stderr asli SEBELUM kita timpa apapun
_REAL_STDERR = sys.stderr

class TextRedirector:
    """
    Thread-safe stdout/stderr → tkinter Text widget.

    • write() aman dipanggil dari thread manapun (pakai root.after)
    • Jika widget/root sudah destroyed (misal saat app closing), fallback ke
      stderr asli sehingga tidak ada 'I/O operation on closed file'
    • tag='error' dipakai jika instance ini menggantikan stderr
    """

    def __init__(self, text_widget, root, tag: str = "info"):
        self._widget  = text_widget
        self._root    = root
        self._tag     = tag
        self._closed  = False

    def write(self, s: str):
        if not s:
            return
        if self._closed:
            try:
                _REAL_STDERR.write(s)
            except Exception:
                pass
            return
        try:
            self._root.after(0, self._insert, str(s))
        except Exception:
            # root sudah destroy — tulis ke stderr asli
            try:
                _REAL_STDERR.write(s)
            except Exception:
                pass

    def _insert(self, s: str):
        try:
            if self._widget.winfo_exists():
                self._widget.insert(tk.END, s, self._tag)
                self._widget.see(tk.END)
        except Exception:
            pass

    def close(self):
        """Dipanggil saat app closing agar write() tidak crash."""
        self._closed = True

    def flush(self):
        pass

    # Supaya io.TextIOWrapper tidak komplain
    @property
    def encoding(self):
        return "utf-8"

    @property
    def errors(self):
        return "replace"


# ─────────────────────────────────────────────────────────────────────────────
# Window config persistence
# ─────────────────────────────────────────────────────────────────────────────

class WindowConfig:
    CONFIG_FILE = Path(__file__).parent.parent / "window_config.json"
    _DEFAULTS   = {"width": 960, "height": 620, "x": None, "y": None, "maximized": False}

    @classmethod
    def load(cls) -> dict:
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return {**cls._DEFAULTS, **json.load(f)}
            except Exception:
                pass
        return dict(cls._DEFAULTS)

    @classmethod
    def save(cls, w, h, x, y, maximized=False):
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"width": w, "height": h, "x": x, "y": y,
                           "maximized": maximized}, f, indent=2)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Main GUI
# ─────────────────────────────────────────────────────────────────────────────

class WerewolfBotGUI:
    VERSION = "v1.0.0"

    def __init__(self, root: tk.Tk):
        self.root          = root
        self.lang          = LanguageManager()
        self.window_config = WindowConfig.load()

        self._setup_window()
        self.root.title(self.lang.get("app_title"))
        self._set_icon()
        self.root.configure(bg=Colors.BG_DARK)

        # ── state ──
        self.bot_running          = False
        self.bot_process          = None
        self.retry_count          = 0
        self.max_retries          = 3
        self.auto_scroll          = tk.BooleanVar(value=True)
        self.network_check_running= False
        self.show_token           = tk.BooleanVar()
        self.auto_reconnect       = tk.BooleanVar(value=True)
        self.output_queue: queue.Queue = queue.Queue()
        self._configure_after_id  = None   # debounce handle

        self.root.bind("<Configure>", self._on_window_configure)
        self.root.bind("<Map>",       self._on_window_map)

        self.fonts = Fonts(self.root)
        self._build_ui()
        sys.excepthook = self._handle_uncaught

        self.root.after(100, self._start_network_monitoring)
        self.root.after(200, self._process_output_queue)
        self.root.after(500, self._fix_layout)

    # ══════════════════════════════════════════════════════════════
    # Window management
    # ══════════════════════════════════════════════════════════════

    def _set_icon(self):
        try:
            p = Path(__file__).parent.parent / "icon.ico"
            if p.exists():
                self.root.iconbitmap(str(p))
        except Exception:
            pass

    def _setup_window(self):
        cfg = self.window_config
        w, h = cfg.get("width", 960), cfg.get("height", 620)
        x, y = cfg.get("x"), cfg.get("y")
        if x is None or y is None:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            x, y   = (sw - w) // 2, (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(820, 540)
        self.root.resizable(True, True)
        if cfg.get("maximized"):
            self.root.after(100, lambda: self.root.state("zoomed"))

    def _on_window_configure(self, event):
        if event.widget is not self.root:
            return
        if self._configure_after_id:
            self.root.after_cancel(self._configure_after_id)
        self._configure_after_id = self.root.after(350, self._save_window_state)

    def _on_window_map(self, event):
        if event.widget is self.root:
            self._save_window_state()

    def _save_window_state(self):
        self._configure_after_id = None
        try:
            state     = self.root.state()
            maximized = state == "zoomed"
            WindowConfig.save(
                self.root.winfo_width(), self.root.winfo_height(),
                self.root.winfo_x(),     self.root.winfo_y(),
                maximized=maximized,
            )
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        # Root uses grid so rows/cols can expand properly
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()

    # ── Header ───────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=Colors.BG_DARKER, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        # Left: title block
        left = tk.Frame(hdr, bg=Colors.BG_DARKER)
        left.pack(side=tk.LEFT, padx=16, pady=0, fill=tk.Y)

        # green accent bar
        tk.Frame(left, bg=Colors.BORDER_ACCENT, width=3).pack(side=tk.LEFT, fill=tk.Y, pady=8)

        title_block = tk.Frame(left, bg=Colors.BG_DARKER)
        title_block.pack(side=tk.LEFT, padx=(8, 0), fill=tk.Y, pady=8)

        self._title_lbl = tk.Label(
            title_block,
            text=self.lang.get("app_title"),
            font=self.fonts.title,
            bg=Colors.BG_DARKER,
            fg=Colors.TEXT_ACCENT,
        )
        self._title_lbl.pack(anchor="w")

        self._subtitle_lbl = tk.Label(
            title_block,
            text=self.lang.get("subtitle"),
            font=self.fonts.subtitle,
            bg=Colors.BG_DARKER,
            fg=Colors.TEXT_GRAY_LIGHT,
        )
        self._subtitle_lbl.pack(anchor="w")

        # Right: version tag + lang selector
        right = tk.Frame(hdr, bg=Colors.BG_DARKER)
        right.pack(side=tk.RIGHT, padx=16, fill=tk.Y)

        ver = tk.Label(
            right, text=self.VERSION,
            font=self.fonts.tag,
            bg=Colors.BG_CARD_HEADER,
            fg=Colors.TEXT_GRAY,
            padx=6, pady=2,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=Colors.BORDER,
        )
        ver.pack(side=tk.RIGHT, pady=16, padx=(6, 0))

        lang_frame = tk.Frame(right, bg=Colors.BG_DARKER)
        lang_frame.pack(side=tk.RIGHT, pady=16)

        tk.Label(lang_frame, text="LANG",
                 font=self.fonts.tag, bg=Colors.BG_DARKER,
                 fg=Colors.TEXT_GRAY_LIGHT).pack(side=tk.LEFT, padx=(0, 4))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TCombobox",
            fieldbackground=Colors.BG_CARD,
            background=Colors.BG_CARD_HEADER,
            foreground=Colors.TEXT_WHITE,
            arrowcolor=Colors.TEXT_GRAY,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.BG_CARD,
            darkcolor=Colors.BG_CARD,
            selectbackground=Colors.BG_CARD_HEADER,
            selectforeground=Colors.TEXT_WHITE,
        )
        self._lang_combo = ttk.Combobox(
            lang_frame, values=["ID", "ENG"],
            state="readonly", width=4,
            style="Dark.TCombobox",
        )
        self._lang_combo.set(self.lang.current_lang)
        self._lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)
        self._lang_combo.pack(side=tk.LEFT)

    # ── Body (paned) ─────────────────────────────────────────────

    def _build_body(self):
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 0))

        # ── Left panel ──
        left_outer = tk.Frame(paned, bg=Colors.BG_DARK)
        paned.add(left_outer, weight=38)

        self._left_canvas   = tk.Canvas(left_outer, bg=Colors.BG_DARK, highlightthickness=0)
        left_sb             = tk.Scrollbar(left_outer, orient="vertical",
                                           command=self._left_canvas.yview,
                                           bg=Colors.BG_DARKER, troughcolor=Colors.BG_DARKER)
        self._left_scroll   = tk.Frame(self._left_canvas, bg=Colors.BG_DARK)

        self._left_scroll.bind(
            "<Configure>",
            lambda _: self._left_canvas.configure(
                scrollregion=self._left_canvas.bbox("all"))
        )
        self._canvas_win = self._left_canvas.create_window(
            (0, 0), window=self._left_scroll, anchor="nw",
            width=self._left_canvas.winfo_width(),
        )
        self._left_canvas.configure(yscrollcommand=left_sb.set)
        self._left_canvas.pack(side="left", fill="both", expand=True)
        left_sb.pack(side="right", fill="y")

        self._left_canvas.bind(
            "<Configure>",
            lambda e: self._left_canvas.itemconfig(self._canvas_win, width=e.width),
        )

        # Mousewheel scroll
        self._left_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._left_canvas.yview_scroll(-1*(e.delta//120), "units"),
        )

        # Cards
        pad = {"fill": tk.X, "pady": (0, 8), "padx": 4}

        self.token_card = TokenCard(
            self._left_scroll, Colors, self.fonts, self.lang,
            self.show_token, self._toggle_token,
        )
        self.token_card.pack(**pad)

        self.status_card = StatusCard(self._left_scroll, Colors, self.fonts, self.lang)
        self.status_card.pack(**pad)

        self.network_card = NetworkStatusCard(self._left_scroll, Colors, self.fonts, self.lang)
        self.network_card.pack(**pad)
        self.network_card.check_btn.config(command=self._check_network_manual)

        self._build_buttons(self._left_scroll)

        # ── Right panel (console) ──
        right_outer = tk.Frame(paned, bg=Colors.BG_DARK)
        paned.add(right_outer, weight=62)
        self._build_console(right_outer)

    def _build_buttons(self, parent):
        frame = tk.Frame(parent, bg=Colors.BG_DARK)
        frame.pack(fill=tk.X, padx=4, pady=(4, 8))

        defs = [
            ("start_bot",   Colors.BTN_SUCCESS, Colors.BTN_SUCCESS_HV, self.start_bot,   tk.NORMAL),
            ("stop_bot",    Colors.BTN_DANGER,  Colors.BTN_DANGER_HV,  self.stop_bot,    tk.DISABLED),
            ("restart_bot", Colors.BTN_WARNING, Colors.BTN_WARNING_HV, self.restart_bot, tk.DISABLED),
        ]

        frame.grid_rowconfigure(0, weight=1, minsize=36)
        for col, (key, color, hover, cmd, state) in enumerate(defs):
            frame.grid_columnconfigure(col, weight=1)
            btn = ModernButton(frame, self.lang.get(key), color, hover, cmd, state=state)
            btn.grid(row=0, column=col, padx=3, sticky="nsew")

            # store refs for later
            if key == "start_bot":   self.start_btn   = btn
            elif key == "stop_bot":  self.stop_btn    = btn
            elif key == "restart_bot": self.restart_btn = btn

    # ── Console ──────────────────────────────────────────────────

    def _build_console(self, parent):
        wrap = tk.Frame(parent, bg=Colors.BG_CARD,
                        highlightthickness=1, highlightbackground=Colors.BORDER)
        wrap.pack(fill=tk.BOTH, expand=True)

        # Header bar
        hdr = tk.Frame(wrap, bg=Colors.BG_CARD_HEADER, height=32)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Frame(hdr, bg=Colors.BORDER_ACCENT, width=3).pack(side=tk.LEFT, fill=tk.Y)

        self._console_lbl = tk.Label(
            hdr, text=self.lang.get("console_output"),
            font=self.fonts.label, bg=Colors.BG_CARD_HEADER, fg=Colors.TEXT_WHITE,
            padx=10,
        )
        self._console_lbl.pack(side=tk.LEFT)

        # Toolbar
        tb = tk.Frame(hdr, bg=Colors.BG_CARD_HEADER)
        tb.pack(side=tk.RIGHT, padx=8)

        _btn = dict(bg=Colors.BTN_SECONDARY, fg=Colors.TEXT_WHITE,
                    activebackground=Colors.BTN_SEC_HV, activeforeground=Colors.TEXT_WHITE,
                    relief=tk.FLAT, bd=0, padx=8, pady=3,
                    font=self.fonts.subtitle, cursor="hand2",
                    highlightthickness=1, highlightbackground=Colors.BORDER)

        self._clear_btn = tk.Button(tb, text=self.lang.get("clear_log"),
                                    command=self.clear_log, **_btn)
        self._clear_btn.pack(side=tk.LEFT, padx=2)

        self._save_btn = tk.Button(tb, text=self.lang.get("save_log"),
                                   command=self.save_log, **_btn)
        self._save_btn.pack(side=tk.LEFT, padx=2)

        for btn_w in (self._clear_btn, self._save_btn):
            btn_w.bind("<Enter>", lambda e, w=btn_w: w.config(bg=Colors.BTN_SEC_HV))
            btn_w.bind("<Leave>", lambda e, w=btn_w: w.config(bg=Colors.BTN_SECONDARY))

        self._auto_scroll_cb = tk.Checkbutton(
            tb, text=self.lang.get("auto_scroll"),
            variable=self.auto_scroll,
            bg=Colors.BG_CARD_HEADER, fg=Colors.TEXT_GRAY,
            selectcolor=Colors.BG_CARD_HEADER,
            activebackground=Colors.BG_CARD_HEADER,
            activeforeground=Colors.TEXT_GRAY,
            cursor="hand2", font=self.fonts.subtitle,
        )
        self._auto_scroll_cb.pack(side=tk.LEFT, padx=6)

        # Log text
        self.log_text = scrolledtext.ScrolledText(
            wrap,
            bg=Colors.BG_CONSOLE, fg=Colors.TEXT_GRAY,
            font=self.fonts.console,
            wrap=tk.WORD, relief=tk.FLAT, bd=0,
            insertbackground=Colors.STATUS_ONLINE,
            selectbackground=Colors.BG_CARD_HEADER,
            maxundo=0,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        for tag, color in (
            ("error",   Colors.STATUS_OFFLINE),
            ("success", Colors.STATUS_ONLINE),
            ("info",    Colors.STATUS_INFO),
            ("warning", Colors.STATUS_WARNING),
            ("dim",     Colors.TEXT_GRAY_LIGHT),
        ):
            self.log_text.tag_config(tag, foreground=color)

        # Redirect stdout + stderr SETELAH widget siap.
        # Simpan instance agar bisa di-.close() saat app keluar.
        self._stdout_redir = TextRedirector(self.log_text, self.root, tag="info")
        self._stderr_redir = TextRedirector(self.log_text, self.root, tag="error")
        sys.stdout = self._stdout_redir
        sys.stderr = self._stderr_redir

    # ── Footer ───────────────────────────────────────────────────

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=Colors.BG_DARKER, height=28)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        # Separator line atas
        tk.Frame(footer, bg=Colors.BORDER, height=1).pack(fill=tk.X, side=tk.TOP)

        inner = tk.Frame(footer, bg=Colors.BG_DARKER)
        inner.pack(fill=tk.BOTH, expand=True)

        self._footer_lbl = tk.Label(
            inner, text=self.lang.get("copyright"),
            font=self.fonts.subtitle, bg=Colors.BG_DARKER, fg=Colors.TEXT_GRAY_DARK,
        )
        self._footer_lbl.pack(side=tk.LEFT, padx=12)

        right = tk.Frame(inner, bg=Colors.BG_DARKER)
        right.pack(side=tk.RIGHT, padx=12)

        self._conn_cv = tk.Canvas(right, width=8, height=8,
                                  bg=Colors.BG_DARKER, highlightthickness=0)
        self._conn_cv.pack(side=tk.LEFT, padx=(0, 4))
        self._conn_dot = self._conn_cv.create_oval(1, 1, 7, 7,
                                                   fill=Colors.STATUS_OFFLINE, outline="")

        self._auto_reconnect_cb = tk.Checkbutton(
            right, text=self.lang.get("auto_reconnect"),
            variable=self.auto_reconnect,
            bg=Colors.BG_DARKER, fg=Colors.TEXT_GRAY,
            selectcolor=Colors.BG_DARKER,
            activebackground=Colors.BG_DARKER,
            activeforeground=Colors.TEXT_GRAY,
            cursor="hand2", font=self.fonts.subtitle,
        )
        self._auto_reconnect_cb.pack(side=tk.LEFT)

    # ══════════════════════════════════════════════════════════════
    # Language
    # ══════════════════════════════════════════════════════════════

    def _on_lang_change(self, _event):
        self.lang.set_language(self._lang_combo.get())
        self.root.title(self.lang.get("app_title"))
        self._title_lbl.config(text=self.lang.get("app_title"))
        self._subtitle_lbl.config(text=self.lang.get("subtitle"))
        for card in (self.token_card, self.status_card, self.network_card):
            card.update_language()
        self._footer_lbl.config(text=self.lang.get("copyright"))
        self.start_btn.config(text=self.lang.get("start_bot"))
        self.stop_btn.config(text=self.lang.get("stop_bot"))
        self.restart_btn.config(text=self.lang.get("restart_bot"))
        self._console_lbl.config(text=self.lang.get("console_output"))
        self._clear_btn.config(text=self.lang.get("clear_log"))
        self._save_btn.config(text=self.lang.get("save_log"))
        self._auto_scroll_cb.config(text=self.lang.get("auto_scroll"))
        self._auto_reconnect_cb.config(text=self.lang.get("auto_reconnect"))

    # ══════════════════════════════════════════════════════════════
    # Layout helpers
    # ══════════════════════════════════════════════════════════════

    def _fix_layout(self):
        if hasattr(self, "_left_canvas"):
            self._left_canvas.itemconfig(self._canvas_win,
                                         width=self._left_canvas.winfo_width())
            self._left_canvas.configure(scrollregion=self._left_canvas.bbox("all"))

    # ══════════════════════════════════════════════════════════════
    # Logging  (single hot-path writer)
    # ══════════════════════════════════════════════════════════════

    def _log(self, msg: str, tag: str = "info"):
        ts     = time.strftime("%H:%M:%S")
        prefix = {"error": "ERR ", "warning": "WARN", "success": "OK  "}.get(tag, "INFO")
        self.log_text.insert(tk.END, f"[{ts}] ", "dim")
        self.log_text.insert(tk.END, f"{prefix}  ", tag)
        self.log_text.insert(tk.END, f"{msg}\n")
        if self.auto_scroll.get():
            self.log_text.see(tk.END)

    def log_error(self, msg):            self._log(msg, "error")
    def log_warning(self, msg):          self._log(msg, "warning")
    def log_info(self, msg, tag="info"): self._log(msg, tag)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self._log("log cleared", "success")

    def save_log(self):
        fname = f"werewolf_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(self.log_text.get(1.0, tk.END))
        messagebox.showinfo("Saved", f"Log disimpan ke {fname}")

    def _handle_uncaught(self, exc_type, exc_value, exc_tb):
        self.log_error("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

    # ══════════════════════════════════════════════════════════════
    # Token
    # ══════════════════════════════════════════════════════════════

    def _toggle_token(self):
        if hasattr(self, "token_card"):
            self.token_card.toggle_visibility()

    def _get_token(self) -> str:
        return self.token_card.get_token() if hasattr(self, "token_card") else ""

    # ══════════════════════════════════════════════════════════════
    # Network
    # ══════════════════════════════════════════════════════════════

    def _check_network_manual(self):
        status = NetworkChecker.get_network_status()
        self.network_card.update_status(status)
        return status

    def _update_network_status(self, status):
        self.network_card.update_status(status)
        if not status["internet"]:
            self.log_error("tidak ada koneksi internet")

    def _start_network_monitoring(self):
        def monitor():
            while self.network_check_running:
                try:
                    if self.network_card.auto_monitor_var.get():
                        s = NetworkChecker.get_network_status()
                        self.root.after(0, self._update_network_status, s)
                except Exception:
                    pass
                time.sleep(15)

        self.network_check_running = True
        threading.Thread(target=monitor, daemon=True).start()
        self.root.after(500, self._check_network_manual)

    def _check_network_before_start(self) -> bool:
        status = NetworkChecker.get_network_status()
        if not status["internet"]:
            messagebox.showerror("Error",
                                 "TIDAK ADA KONEKSI INTERNET!\n\nBot tidak dapat dijalankan.")
            self.log_error("gagal start: tidak ada koneksi internet")
            return False
        return True

    # ══════════════════════════════════════════════════════════════
    # Bot control
    # ══════════════════════════════════════════════════════════════

    def start_bot(self):
        if self.bot_running:
            return
        if not self._check_network_before_start():
            return

        token = self._get_token()
        if not token:
            messagebox.showerror("Error", "Token tidak boleh kosong!")
            return
        if len(token) < 50:
            messagebox.showerror("Error", "Token terlalu pendek!")
            return

        self.bot_running  = True
        self.retry_count  = 0

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.restart_btn.config(state=tk.NORMAL)
        self.status_card.set_online()
        self.token_card.set_disabled(True)
        self._conn_cv.itemconfig(self._conn_dot, fill=Colors.STATUS_ONLINE)

        self._log("─" * 40, "dim")
        self._log("werewolf bot  starting", "success")
        self._log(f"token  {'*' * 20}...{'*' * 8}", "info")
        self._log("─" * 40, "dim")

        self._run_bot_process(token)

    def _run_bot_process(self, token: str):
        try:
            runner = Path(__file__).parent.parent / "bot" / "bot_runner.py"
            env    = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
            self.bot_process = subprocess.Popen(
                [sys.executable, str(runner), token],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,   # terpisah agar warna berbeda di console
                text=True, bufsize=1, universal_newlines=True,
                encoding="utf-8", errors="replace", env=env,
            )
            self._read_output()
        except Exception as e:
            self.log_error(f"gagal start proses: {e}")
            self.bot_error()

    def _read_output(self):
        def _read_pipe(pipe, queue_obj, prefix=""):
            try:
                for line in iter(pipe.readline, ""):
                    if line:
                        queue_obj.put(prefix + line.rstrip())
            except Exception:
                pass

        proc = self.bot_process

        # stdout → queue normal
        threading.Thread(
            target=_read_pipe,
            args=(proc.stdout, self.output_queue),
            daemon=True,
        ).start()

        # stderr → queue dengan prefix "!ERR " agar bisa dibedakan
        threading.Thread(
            target=_read_pipe,
            args=(proc.stderr, self.output_queue, "!ERR "),
            daemon=True,
        ).start()

        # Watcher: kirim sentinel saat proses selesai
        def _watcher():
            proc.wait()
            self.output_queue.put(None)

        threading.Thread(target=_watcher, daemon=True).start()

    # Token pattern: Discord tokens are base64 segments separated by dots
    _TOKEN_RE = re.compile(
        r'[A-Za-z0-9_-]{24,28}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,38}'
    )

    @classmethod
    def _censor(cls, text: str) -> str:
        """Ganti token Discord di teks dengan ****."""
        return cls._TOKEN_RE.sub(lambda m: m.group()[:6] + "****" + m.group()[-4:], text)

    def _process_output_queue(self):
        """Drain seluruh queue dalam satu Tk tick → batch insert."""
        try:
            stdout_lines, stderr_lines, sentinel = [], [], False
            while True:
                item = self.output_queue.get_nowait()
                if item is None:
                    sentinel = True
                    break
                if isinstance(item, str) and item.startswith("!ERR "):
                    stderr_lines.append(self._censor(item[5:]))
                else:
                    stdout_lines.append(self._censor(item))

            if stdout_lines:
                self._log("\n".join(stdout_lines), "info")
            if stderr_lines:
                self._log("\n".join(stderr_lines), "error")
            if sentinel and self.bot_running:
                self.root.after(0, self.bot_error)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_output_queue)

    def bot_error(self):
        if not self.bot_running:
            return
        if self.auto_reconnect.get() and self.retry_count < self.max_retries:
            self.retry_count += 1
            self.log_warning(
                f"bot mati, auto-reconnect ({self.retry_count}/{self.max_retries})..."
            )
            self.root.after(3000, self._reconnect_bot)
        else:
            self._do_stop()
            self.status_card.set_error()
            self.log_error("bot mati  restart manual diperlukan")

    def _reconnect_bot(self):
        if self.bot_running:
            self._do_stop()
            self.root.after(1000, self.start_bot)

    def restart_bot(self):
        self.log_warning("restarting bot...")
        if self.bot_running:
            self._do_stop()
        self.root.after(1000, self.start_bot)

    def _do_stop(self):
        self.bot_running = False

        if self.bot_process:
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=5)
            except Exception:
                try:
                    self.bot_process.kill()
                except Exception:
                    pass
            self.bot_process = None

        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.NORMAL)
        self.status_card.set_offline()
        if hasattr(self, "token_card"):
            self.token_card.set_disabled(False)
        self._conn_cv.itemconfig(self._conn_dot, fill=Colors.STATUS_OFFLINE)
        self._log("bot stopped", "error")

    def stop_bot(self):
        if self.bot_running:
            self._do_stop()

    # ══════════════════════════════════════════════════════════════
    # Closing
    # ══════════════════════════════════════════════════════════════

    def on_closing(self):
        self._save_window_state()
        self.network_check_running = False
        if self.bot_running:
            if messagebox.askokcancel("Konfirmasi",
                                      "Bot sedang berjalan. Yakin ingin keluar?"):
                self._do_stop()
                self._restore_stdio()
                self.root.destroy()
        else:
            self._restore_stdio()
            self.root.destroy()

    def _restore_stdio(self):
        """Tutup redirector dan kembalikan sys.stdout/stderr ke aslinya
        sebelum window di-destroy, agar tidak ada 'I/O on closed file'."""
        for attr in ("_stdout_redir", "_stderr_redir"):
            redir = getattr(self, attr, None)
            if redir:
                redir.close()
        try:
            sys.stdout = _REAL_STDERR   # stderr asli pasti ada
            sys.stderr = _REAL_STDERR
        except Exception:
            pass