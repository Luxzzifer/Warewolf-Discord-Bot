# main.py
import sys
import traceback
import io
from pathlib import Path

# Set stdout to UTF-8 for Windows to handle emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import tkinter as tk
    from gui.main_gui import WerewolfBotGUI
    
    def main():
        root = tk.Tk()
        app = WerewolfBotGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import Error: {e}")
    print("Pastikan semua file sudah lengkap!")
    traceback.print_exc()
    input("Press Enter to exit...")
except Exception as e:
    print(f"Fatal error: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")