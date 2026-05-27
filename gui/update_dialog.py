# gui/update_dialog.py
"""
Dialog popup untuk notifikasi dan progress update.
Dipanggil dari main_gui.py ketika UpdateChecker menemukan versi baru.
"""
import tkinter as tk
from tkinter import ttk
import threading
from .styles import Colors, Fonts


class UpdateDialog(tk.Toplevel):
    """
    Modal dialog yang menampilkan:
      • Info versi baru + release notes
      • Tombol Update Sekarang / Nanti
      • Progress bar + status saat update berjalan
      • Tombol Restart setelah update selesai
    """

    def __init__(self, parent, update_info: dict, fonts: Fonts, apply_fn):
        super().__init__(parent)
        self._info     = update_info
        self._fonts    = fonts
        self._apply_fn = apply_fn   # callable(info, progress_cb) → bool
        self._updating = False

        self.title("Update Tersedia")
        self.resizable(False, False)
        self.configure(bg=Colors.BG_DARK)
        self.grab_set()             # modal
        self.transient(parent)

        # Ukuran & posisi tengah parent
        w, h = 460, 360
        px = parent.winfo_x() + (parent.winfo_width()  - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{px}+{py}")

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Build UI ─────────────────────────────────────────────────

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=Colors.BG_DARKER, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Frame(hdr, bg=Colors.BORDER_ACCENT, width=3).pack(side=tk.LEFT, fill=tk.Y)

        hdr_txt = tk.Frame(hdr, bg=Colors.BG_DARKER)
        hdr_txt.pack(side=tk.LEFT, padx=12, fill=tk.Y)

        tk.Label(
            hdr_txt, text="🔄  Update Tersedia",
            font=self._fonts.label,
            bg=Colors.BG_DARKER, fg=Colors.TEXT_WHITE,
        ).pack(anchor="w", pady=(10, 0))

        tk.Label(
            hdr_txt,
            text=f"Versi baru: {self._info['tag']}  ←  {_get_local_ver()}",
            font=self._fonts.subtitle,
            bg=Colors.BG_DARKER, fg=Colors.TEXT_GRAY_LIGHT,
        ).pack(anchor="w")

        # ── Release notes ──
        notes_frame = tk.Frame(self, bg=Colors.BG_CARD,
                               highlightthickness=1, highlightbackground=Colors.BORDER)
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(12, 6))

        tk.Label(
            notes_frame, text="Release Notes",
            font=self._fonts.mono_sm,
            bg=Colors.BG_CARD_HEADER, fg=Colors.TEXT_GRAY,
            padx=10, pady=4, anchor="w",
        ).pack(fill=tk.X)

        notes_txt = tk.Text(
            notes_frame,
            bg=Colors.BG_CONSOLE, fg=Colors.TEXT_GRAY,
            font=self._fonts.console,
            relief=tk.FLAT, bd=0,
            wrap=tk.WORD, height=6,
            state=tk.NORMAL,
        )
        notes_txt.insert(tk.END, self._info.get("notes") or "Tidak ada catatan rilis.")
        notes_txt.config(state=tk.DISABLED)
        notes_txt.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # ── Progress bar (hidden awalnya) ──
        self._prog_frame = tk.Frame(self, bg=Colors.BG_DARK)
        self._prog_frame.pack(fill=tk.X, padx=14, pady=(0, 4))

        self._prog_lbl = tk.Label(
            self._prog_frame, text="",
            font=self._fonts.subtitle,
            bg=Colors.BG_DARK, fg=Colors.TEXT_GRAY_LIGHT,
            anchor="w",
        )
        self._prog_lbl.pack(fill=tk.X)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor=Colors.BG_CARD,
            background=Colors.STATUS_ONLINE,
            bordercolor=Colors.BORDER,
            lightcolor=Colors.STATUS_ONLINE,
            darkcolor=Colors.STATUS_ONLINE,
        )
        self._progress = ttk.Progressbar(
            self._prog_frame,
            style="Green.Horizontal.TProgressbar",
            orient="horizontal", mode="determinate", length=430,
        )
        # progress bar disembunyikan dulu
        self._prog_frame.pack_forget()

        # ── Tombol ──
        btn_row = tk.Frame(self, bg=Colors.BG_DARK)
        btn_row.pack(fill=tk.X, padx=14, pady=(0, 12))

        _btn = dict(relief=tk.FLAT, bd=0, padx=16, pady=7,
                    font=self._fonts.subtitle, cursor="hand2",
                    highlightthickness=1)

        self._later_btn = tk.Button(
            btn_row, text="Nanti",
            bg=Colors.BTN_SECONDARY, fg=Colors.TEXT_WHITE,
            activebackground=Colors.BTN_SEC_HV,
            highlightbackground=Colors.BORDER,
            command=self._on_close,
            **_btn,
        )
        self._later_btn.pack(side=tk.RIGHT, padx=(4, 0))

        self._update_btn = tk.Button(
            btn_row, text="⬇  Update Sekarang",
            bg=Colors.BTN_SUCCESS, fg=Colors.TEXT_WHITE,
            activebackground=Colors.BTN_SUCCESS_HV,
            highlightbackground=Colors.BTN_SUCCESS,
            command=self._start_update,
            **_btn,
        )
        self._update_btn.pack(side=tk.RIGHT)

        # Hover effects
        for btn, active, normal in (
            (self._later_btn,  Colors.BTN_SEC_HV,    Colors.BTN_SECONDARY),
            (self._update_btn, Colors.BTN_SUCCESS_HV, Colors.BTN_SUCCESS),
        ):
            btn.bind("<Enter>", lambda e, b=btn, c=active:  b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=normal:  b.config(bg=c))

    # ── Update flow ──────────────────────────────────────────────

    def _start_update(self):
        if self._updating:
            return
        self._updating = True
        self._update_btn.config(state=tk.DISABLED, text="Mengupdate...")
        self._later_btn.config(state=tk.DISABLED)

        # Tampilkan progress bar
        self._prog_frame.pack(fill=tk.X, padx=14, pady=(0, 4),
                              before=self._update_btn.master)
        self._progress.pack(fill=tk.X, pady=(2, 0))

        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        def progress_cb(msg: str, pct: int):
            self.after(0, self._set_progress, msg, pct)

        success = self._apply_fn(self._info, progress_cb)
        self.after(0, self._on_update_done, success)

    def _set_progress(self, msg: str, pct: int):
        self._prog_lbl.config(text=msg)
        if pct >= 0:
            self._progress["value"] = pct

    def _on_update_done(self, success: bool):
        if success:
            self._update_btn.config(
                text="✓ Selesai — Restart untuk menerapkan",
                bg=Colors.BTN_SUCCESS,
                state=tk.NORMAL,
                command=self._restart_app,
            )
            self._later_btn.config(state=tk.NORMAL, text="Tutup")
        else:
            self._update_btn.config(
                text="✗ Gagal — Coba lagi",
                bg=Colors.BTN_DANGER,
                state=tk.NORMAL,
                command=self._start_update,
            )
            self._later_btn.config(state=tk.NORMAL)
        self._updating = False

    def _restart_app(self):
        """Restart proses Python saat ini."""
        import subprocess, sys
        self.destroy()
        subprocess.Popen([sys.executable] + sys.argv)
        self.master.after(200, self.master.destroy)

    def _on_close(self):
        if not self._updating:
            self.destroy()


# ── helper ───────────────────────────────────────────────────────────────────

def _get_local_ver() -> str:
    try:
        from updater import get_local_version
        return get_local_version()
    except Exception:
        return "v?"