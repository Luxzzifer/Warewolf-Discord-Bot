# gui/main_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import traceback
from io import StringIO
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

# Add parent directory to path for bot imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


class TextRedirector:
    """
    Redirects stdout to a tkinter Text widget.
    
    This class captures all print statements and redirects them
    to the console output area in the GUI.
    """
    def __init__(self, text_widget):
        """Initialize the redirector with the target text widget."""
        self.text_widget = text_widget
        self.buffer = StringIO()

    def write(self, string):
        """Write string to the text widget."""
        try:
            self.buffer.write(string)
            self.text_widget.insert(tk.END, string)
            self.text_widget.see(tk.END)
            self.text_widget.update_idletasks()
        except Exception:
            pass

    def flush(self):
        """Flush the buffer."""
        try:
            self.buffer.flush()
        except Exception:
            pass


class WindowConfig:
    """
    Manages window size and position persistence.
    
    This class handles saving and loading the window configuration
    to/from a JSON file, preserving the user's preferred window size,
    position, and maximized state across sessions.
    """
    CONFIG_FILE = Path(__file__).parent.parent / "window_config.json"
    
    @classmethod
    def load(cls):
        """
        Load window configuration from file.
        
        Returns:
            dict: Window configuration with width, height, x, y, and maximized state.
        """
        default_config = {
            "width": 1100,
            "height": 750,
            "x": None,
            "y": None,
            "maximized": False
        }
        
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with default for any missing keys
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            except Exception:
                pass
        
        return default_config
    
    @classmethod
    def save(cls, width, height, x, y, maximized=False):
        """
        Save window configuration to file.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            x: X position on screen
            y: Y position on screen
            maximized: Whether window is maximized
        """
        try:
            config = {
                "width": width,
                "height": height,
                "x": x,
                "y": y,
                "maximized": maximized
            }
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass


class WerewolfBotGUI:
    """
    Main GUI class for Werewolf Discord Bot.
    
    This class creates and manages the main window of the application,
    including all UI components, bot control, and network monitoring.
    """
    def __init__(self, root):
        """Initialize the main GUI window and components."""
        self.root = root
        self.lang = LanguageManager()
        
        # Load saved window configuration
        self.window_config = WindowConfig.load()
        
        # Set window size and position
        self._setup_window()
        self.root.title("🐺 WAREWOLF DISCORD BOT")
        
        # Set window icon (optional)
        try:
            self.root.iconphoto(False, tk.PhotoImage())
        except Exception:
            pass
        
        self.root.configure(bg=Colors.BG_DARK)

        # Bot state variables
        self.bot_running = False
        self.bot_process = None
        self.retry_count = 0
        self.max_retries = 3
        
        # UI state variables
        self.auto_scroll = tk.BooleanVar(value=True)
        self.network_check_running = False
        self.show_token = tk.BooleanVar()
        self.auto_reconnect = tk.BooleanVar(value=True)
        self.output_queue = queue.Queue()
        
        # Bind window events for configuration persistence
        self.root.bind("<Configure>", self._on_window_configure)
        self.root.bind("<Map>", self._on_window_map)

        # Initialize UI
        self.setup_fonts()
        self.setup_ui()
        sys.excepthook = self.handle_uncaught_exception

        # Start background processes
        self.root.after(100, self.start_network_monitoring)
        self.root.after(200, self.process_output_queue)
        self.root.after(500, self._fix_layout)

    # ==================== WINDOW MANAGEMENT ====================
    
    def _setup_window(self):
        """Setup window size, position, and center on first run."""
        width = self.window_config.get("width", 1100)
        height = self.window_config.get("height", 750)
        x = self.window_config.get("x")
        y = self.window_config.get("y")
        maximized = self.window_config.get("maximized", False)

        # If position not saved, center the window
        if x is None or y is None:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = int((screen_width / 2) - (width / 2))
            y = int((screen_height / 2) - (height / 2))

        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Set minimum window size
        self.root.minsize(900, 650)
        
        # Allow window resizing
        self.root.resizable(True, True)

        # Restore maximized state if it was saved
        if maximized:
            self.root.after(100, lambda: self.root.state('zoomed'))
    
    def _on_window_configure(self, event):
        """Save window configuration when window is resized or moved."""
        if event.widget == self.root:
            try:
                if self.root.state() == 'normal':
                    self._save_window_state()
                elif self.root.state() == 'zoomed':
                    self._save_window_state()
            except Exception:
                pass
    
    def _on_window_map(self, event):
        """Handle window mapping (when window becomes visible)."""
        if event.widget == self.root:
            self._save_window_state()
    
    def _save_window_state(self):
        """Save current window state to config file."""
        try:
            state = self.root.state()
            if state == 'normal':
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                WindowConfig.save(width, height, x, y, maximized=False)
            elif state == 'zoomed':
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                WindowConfig.save(width, height, x, y, maximized=True)
        except Exception:
            pass

    # ==================== UI SETUP ====================
    
    def setup_fonts(self):
        """Initialize fonts for the GUI."""
        self.fonts = Fonts(self.root)

    def setup_ui(self):
        """Create the main UI structure."""
        main_frame = tk.Frame(self.root, bg=Colors.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights for responsive layout
        main_frame.grid_rowconfigure(0, weight=0)  # Header
        main_frame.grid_rowconfigure(1, weight=1)  # Content
        main_frame.grid_rowconfigure(2, weight=0)  # Footer
        main_frame.grid_columnconfigure(0, weight=1)

        self.setup_header(main_frame)
        self.setup_content(main_frame)
        self.setup_footer(main_frame)

        self.root.update_idletasks()

    def setup_header(self, parent):
        """
        Create the header area with title, subtitle, and language selector.
        
        Args:
            parent: Parent widget to attach the header to.
        """
        header_frame = tk.Frame(parent, bg=Colors.BG_DARKER, height=80)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_propagate(False)

        # Title label
        title_label = tk.Label(
            header_frame,
            text=self.lang.get("app_title"),
            font=self.fonts.title,
            bg=Colors.BG_DARKER,
            fg=Colors.TEXT_WHITE
        )
        title_label.pack(expand=True, pady=(15, 5))

        # Subtitle label
        self.subtitle_label = tk.Label(
            header_frame,
            text=self.lang.get("subtitle"),
            font=self.fonts.subtitle,
            bg=Colors.BG_DARKER,
            fg=Colors.TEXT_GRAY_LIGHT
        )
        self.subtitle_label.pack()

        # Language selector dropdown
        lang_frame = tk.Frame(header_frame, bg=Colors.BG_DARKER)
        lang_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        tk.Label(
            lang_frame,
            text=self.lang.get("language"),
            bg=Colors.BG_DARKER,
            fg=Colors.TEXT_GRAY_LIGHT
        ).pack(side=tk.LEFT)
        
        self.lang_combo = ttk.Combobox(
            lang_frame,
            values=["ID", "ENG"],
            state="readonly",
            width=5
        )
        self.lang_combo.set(self.lang.current_lang)
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        self.lang_combo.pack(side=tk.LEFT, padx=5)

    def on_language_change(self, event):
        """Handle language selection change and update all UI texts."""
        new_lang = self.lang_combo.get()
        self.lang.set_language(new_lang)

        # Update window title
        self.root.title(self.lang.get("app_title"))
        self.subtitle_label.config(text=self.lang.get("subtitle"))

        # Update all cards
        self.token_card.update_language()
        self.status_card.update_language()
        self.network_card.update_language()

        # Update footer
        self.footer_label.config(text=self.lang.get("copyright"))

        # Update buttons
        self.start_btn.config(text=self.lang.get("start_bot"))
        self.stop_btn.config(text=self.lang.get("stop_bot"))
        self.restart_btn.config(text=self.lang.get("restart_bot"))

        # Update console header
        self.console_header_label.config(text=self.lang.get("console_output"))

        # Update toolbar buttons
        self.clear_btn.config(text=self.lang.get("clear_log"))
        self.save_btn.config(text=self.lang.get("save_log"))
        self.auto_scroll_cb.config(text=self.lang.get("auto_scroll"))

        # Update auto reconnect checkbox
        self.auto_reconnect_cb.config(text=self.lang.get("auto_reconnect"))

    def setup_content(self, parent):
        """
        Create the main content area with left (configuration) and right (console) panels.
        
        Args:
            parent: Parent widget to attach the content to.
        """
        # Create PanedWindow for split view
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Left panel with scrollbar
        left_container = tk.Frame(paned, bg=Colors.BG_DARK)
        paned.add(left_container, weight=40)

        # Create canvas and scrollbar for left panel
        left_canvas = tk.Canvas(
            left_container,
            bg=Colors.BG_DARK,
            highlightthickness=0
        )
        left_scrollbar = tk.Scrollbar(
            left_container,
            orient="vertical",
            command=left_canvas.yview
        )
        left_scrollable = tk.Frame(left_canvas, bg=Colors.BG_DARK)

        left_scrollable.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        
        canvas_window = left_canvas.create_window(
            (0, 0),
            window=left_scrollable,
            anchor="nw",
            width=left_canvas.winfo_width()
        )
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")

        self.left_canvas = left_canvas
        self.canvas_window = canvas_window

        # Update canvas window width when canvas is resized
        def on_canvas_configure(e):
            self.left_canvas.itemconfig(self.canvas_window, width=e.width)
        left_canvas.bind("<Configure>", on_canvas_configure)

        # Add all left panel widgets
        self.token_card = TokenCard(
            left_scrollable, Colors, self.fonts, self.lang,
            self.show_token, self.toggle_token
        )
        self.token_card.pack(fill=tk.X, pady=(0, 15), padx=5)

        self.status_card = StatusCard(left_scrollable, Colors, self.fonts, self.lang)
        self.status_card.pack(fill=tk.X, pady=(0, 15), padx=5)

        self.network_card = NetworkStatusCard(left_scrollable, Colors, self.fonts, self.lang)
        self.network_card.pack(fill=tk.X, pady=(0, 15), padx=5)
        self.network_card.check_btn.config(command=self.check_network_manual)

        self.setup_buttons(left_scrollable)

        left_scrollable.update_idletasks()
        left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        # Right panel (console)
        right_frame = tk.Frame(paned, bg=Colors.BG_DARK)
        paned.add(right_frame, weight=60)
        self.setup_console(right_frame)

    def setup_buttons(self, parent):
        """
        Create the control buttons (START, STOP, RESTART).
        
        Args:
            parent: Parent widget to attach the buttons to.
        """
        btn_frame = tk.Frame(parent, bg=Colors.BG_DARK)
        btn_frame.pack(fill=tk.X, pady=10, padx=5)

        # Get button texts
        start_text = self.lang.get("start_bot")
        stop_text = self.lang.get("stop_bot")
        restart_text = self.lang.get("restart_bot")

        # Calculate minimum button width based on text length
        max_text_len = max(len(start_text), len(stop_text), len(restart_text))
        min_button_width = max(100, max_text_len * 9)

        # Configure grid columns for equal distribution
        btn_frame.grid_columnconfigure(0, weight=1, minsize=min_button_width)
        btn_frame.grid_columnconfigure(1, weight=1, minsize=min_button_width)
        btn_frame.grid_columnconfigure(2, weight=1, minsize=min_button_width)
        
        # Ensure row height is sufficient
        btn_frame.grid_rowconfigure(0, weight=1, minsize=40)

        # Create START button
        self.start_btn = ModernButton(
            btn_frame,
            start_text,
            Colors.BTN_SUCCESS,
            self.start_bot
        )
        self.start_btn.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Create STOP button
        self.stop_btn = ModernButton(
            btn_frame,
            stop_text,
            Colors.BTN_DANGER,
            self.stop_bot,
            state=tk.DISABLED
        )
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Create RESTART button
        self.restart_btn = ModernButton(
            btn_frame,
            restart_text,
            Colors.BTN_WARNING,
            self.restart_bot,
            state=tk.DISABLED
        )
        self.restart_btn.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        btn_frame.update_idletasks()

        # Update scrollable area
        if hasattr(self, 'left_canvas'):
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def setup_console(self, parent):
        """
        Create the console output area.
        
        Args:
            parent: Parent widget to attach the console to.
        """
        console_card = tk.Frame(parent, bg=Colors.BG_CARD, relief=tk.RAISED, bd=1)
        console_card.pack(fill=tk.BOTH, expand=True)

        # Console header with toolbar
        header = tk.Frame(console_card, bg=Colors.BG_CARD_HEADER, height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        self.console_header_label = tk.Label(
            header,
            text=self.lang.get("console_output"),
            font=self.fonts.label,
            bg=Colors.BG_CARD_HEADER,
            fg=Colors.TEXT_WHITE
        )
        self.console_header_label.pack(side=tk.LEFT, padx=15)

        # Toolbar buttons
        toolbar = tk.Frame(header, bg=Colors.BG_CARD_HEADER)
        toolbar.pack(side=tk.RIGHT, padx=10)

        self.clear_btn = tk.Button(
            toolbar,
            text=self.lang.get("clear_log"),
            command=self.clear_log,
            bg=Colors.BTN_SECONDARY,
            fg='white',
            font=("Segoe UI", 8),
            padx=8,
            cursor='hand2'
        )
        self.clear_btn.pack(side=tk.LEFT, padx=2)

        self.save_btn = tk.Button(
            toolbar,
            text=self.lang.get("save_log"),
            command=self.save_log,
            bg=Colors.BTN_SECONDARY,
            fg='white',
            font=("Segoe UI", 8),
            padx=8,
            cursor='hand2'
        )
        self.save_btn.pack(side=tk.LEFT, padx=2)

        self.auto_scroll_cb = tk.Checkbutton(
            toolbar,
            text=self.lang.get("auto_scroll"),
            variable=self.auto_scroll,
            bg=Colors.BG_CARD_HEADER,
            fg=Colors.TEXT_GRAY_LIGHT,
            cursor='hand2'
        )
        self.auto_scroll_cb.pack(side=tk.LEFT, padx=5)

        # Console text widget
        self.log_text = scrolledtext.ScrolledText(
            console_card,
            bg=Colors.BG_CONSOLE,
            fg=Colors.TEXT_GRAY,
            font=self.fonts.console,
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Configure text tags for colored output
        self.log_text.tag_config("error", foreground=Colors.STATUS_OFFLINE)
        self.log_text.tag_config("success", foreground=Colors.STATUS_ONLINE)
        self.log_text.tag_config("info", foreground=Colors.STATUS_INFO)
        self.log_text.tag_config("warning", foreground=Colors.STATUS_WARNING)

    def setup_footer(self, parent):
        """
        Create the footer area with copyright and connection indicator.
        
        Args:
            parent: Parent widget to attach the footer to.
        """
        footer = tk.Frame(parent, bg=Colors.BG_DARKER, height=35)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        # Left side - copyright text
        left_footer = tk.Frame(footer, bg=Colors.BG_DARKER)
        left_footer.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.footer_label = tk.Label(
            left_footer,
            text=self.lang.get("copyright"),
            bg=Colors.BG_DARKER,
            fg=Colors.TEXT_GRAY_DARK,
            font=self.fonts.subtitle
        )
        self.footer_label.pack(side=tk.LEFT)

        # Right side - connection indicator and auto reconnect checkbox
        right_footer = tk.Frame(footer, bg=Colors.BG_DARKER)
        right_footer.pack(side=tk.RIGHT, padx=20, pady=5)

        self.conn_indicator = tk.Canvas(
            right_footer,
            width=8,
            height=8,
            bg=Colors.BG_DARKER,
            highlightthickness=0
        )
        self.conn_indicator.pack(side=tk.LEFT, padx=5)
        self.conn_dot = self.conn_indicator.create_oval(
            2, 2, 6, 6,
            fill=Colors.STATUS_OFFLINE,
            outline=''
        )

        self.auto_reconnect_cb = tk.Checkbutton(
            right_footer,
            text=self.lang.get("auto_reconnect"),
            variable=self.auto_reconnect,
            bg=Colors.BG_DARKER,
            fg=Colors.TEXT_GRAY_LIGHT,
            cursor='hand2'
        )
        self.auto_reconnect_cb.pack(side=tk.LEFT, padx=5)

    # ==================== LAYOUT HELPERS ====================
    
    def _fix_layout(self):
        """Ensure scrollable area has correct width after window resizes."""
        if hasattr(self, 'left_canvas') and hasattr(self, 'canvas_window'):
            self.left_canvas.itemconfig(self.canvas_window, width=self.left_canvas.winfo_width())
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    # ==================== BOT CONTROL METHODS ====================
    
    def toggle_token(self):
        """Toggle token visibility in the entry field."""
        if hasattr(self, 'token_card'):
            self.token_card.toggle_visibility()

    def get_token(self):
        """Get token value from token card."""
        return self.token_card.get_token() if hasattr(self, 'token_card') else ""

    # ==================== LOGGING METHODS ====================
    
    def clear_log(self):
        """Clear console output."""
        self.log_text.delete(1.0, tk.END)
        self.log_info("Log cleared", "success")

    def save_log(self):
        """Save console output to file."""
        filename = f"werewolf_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.log_text.get(1.0, tk.END))
        messagebox.showinfo("Success", f"Log saved to {filename}")

    def log_error(self, msg):
        """Log error message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"\n[{timestamp}] ERROR: {msg}\n", "error")
        if self.auto_scroll.get():
            self.log_text.see(tk.END)
        self.root.update_idletasks()

    def log_info(self, msg, tag="info"):
        """Log informational message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"\n[{timestamp}] INFO: {msg}\n", tag)
        if self.auto_scroll.get():
            self.log_text.see(tk.END)
        self.root.update_idletasks()

    def log_warning(self, msg):
        """Log warning message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"\n[{timestamp}] WARNING: {msg}\n", "warning")
        if self.auto_scroll.get():
            self.log_text.see(tk.END)
        self.root.update_idletasks()

    def handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions and log them."""
        error = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.log_error(f"Uncaught: {error}")

    # ==================== NETWORK METHODS ====================
    
    def check_network_manual(self):
        """Manually check network connection."""
        status = NetworkChecker.get_network_status()
        self.network_card.update_status(status)
        return status

    def update_network_status(self, status):
        """Update network status display."""
        self.network_card.update_status(status)
        if not status["internet"]:
            self.log_error("TIDAK ADA KONEKSI INTERNET!")

    def start_network_monitoring(self):
        """Start network monitoring thread."""
        def monitor():
            while self.network_check_running:
                try:
                    if self.network_card.auto_monitor_var.get():
                        status = NetworkChecker.get_network_status()
                        self.root.after(0, lambda: self.update_network_status(status))
                    time.sleep(15)
                except Exception:
                    pass

        self.network_check_running = True
        self.network_thread = threading.Thread(target=monitor, daemon=True)
        self.network_thread.start()
        self.root.after(500, lambda: self.check_network_manual())

    def check_network_before_start(self):
        """Check internet connection before starting bot."""
        status = NetworkChecker.get_network_status()
        if not status["internet"]:
            messagebox.showerror(
                "Error",
                "TIDAK ADA KONEKSI INTERNET!\n\nBot tidak dapat dijalankan."
            )
            self.log_error("GAGAL START: Tidak ada koneksi internet!")
            return False
        return True

    # ==================== BOT START/STOP METHODS ====================
    
    def start_bot(self):
        """Start the bot process."""
        if self.bot_running:
            return

        if not self.check_network_before_start():
            return

        token = self.get_token()
        if not token:
            messagebox.showerror("Error", "Token tidak boleh kosong!")
            return

        if len(token) < 50:
            messagebox.showerror("Error", "Token terlalu pendek, pastikan token benar!")
            return

        self.bot_running = True
        self.retry_count = 0

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.restart_btn.config(state=tk.NORMAL)
        self.status_card.set_online()
        self.token_card.set_disabled(True)
        self.conn_indicator.itemconfig(self.conn_dot, fill=Colors.STATUS_ONLINE)

        self.log_info("=" * 50)
        self.log_info("WEREWOLF BOT - STARTING", "success")
        self.log_info(f"Token: {token[:20]}...{token[-10:]}")
        self.log_info("=" * 50)

        self._run_bot_process(token)

    def _run_bot_process(self, token):
        """Launch bot as a subprocess."""
        try:
            bot_runner = Path(__file__).parent.parent / "bot" / "bot_runner.py"

            # Set environment for UTF-8 output
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'

            self.bot_process = subprocess.Popen(
                [sys.executable, str(bot_runner), token],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            self._read_output()

        except Exception as e:
            self.log_error(f"Failed to start bot: {e}")
            self.bot_error()

    def _read_output(self):
        """Read output from bot process in a separate thread."""
        def read():
            if self.bot_process and self.bot_process.stdout:
                for line in iter(self.bot_process.stdout.readline, ''):
                    if line:
                        self.output_queue.put(line.strip())
                    if self.bot_process.poll() is not None:
                        break
                self.output_queue.put(None)  # Signal end of output

        threading.Thread(target=read, daemon=True).start()

    def process_output_queue(self):
        """Process queued output lines in the GUI thread."""
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line is None:
                    if self.bot_running:
                        self.root.after(0, self.bot_error)
                    break
                if line:
                    self.log_info(line, "info")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_output_queue)

    def bot_error(self):
        """Handle bot error and auto-reconnect if enabled."""
        if not self.bot_running:
            return

        if self.auto_reconnect.get() and self.retry_count < self.max_retries:
            self.retry_count += 1
            self.log_warning(
                f"Bot mati, auto-reconnect ({self.retry_count}/{self.max_retries})..."
            )
            self.root.after(3000, self._reconnect_bot)
        else:
            self._do_stop()
            self.status_card.set_error()
            self.log_error("Bot mati, silakan restart manual.")

    def _reconnect_bot(self):
        """Reconnect bot."""
        if self.bot_running:
            self._do_stop()
            self.root.after(1000, self.start_bot)

    def restart_bot(self):
        """Restart the bot."""
        if not self.bot_running:
            self.start_bot()
            return

        self.log_warning("Restarting bot...")
        self._do_stop()
        self.root.after(1000, self.start_bot)

    def _do_stop(self):
        """Stop the bot process and clean up."""
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

        # Clear output queue
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.NORMAL)
        self.status_card.set_offline()
        if hasattr(self, 'token_card'):
            self.token_card.set_disabled(False)
        self.conn_indicator.itemconfig(self.conn_dot, fill=Colors.STATUS_OFFLINE)

        self.log_info("BOT STOPPED", "error")

    def stop_bot(self):
        """Stop the bot."""
        if not self.bot_running:
            return
        self._do_stop()

    # ==================== WINDOW CLOSING ====================
    
    def on_closing(self):
        """Handle window closing event."""
        self._save_window_state()
        self.network_check_running = False
        if self.bot_running:
            if messagebox.askokcancel("Konfirmasi", "Bot sedang berjalan. Yakin ingin keluar?"):
                self._do_stop()
                self.root.destroy()
        else:
            self.root.destroy()