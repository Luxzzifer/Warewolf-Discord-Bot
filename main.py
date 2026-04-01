# main.py
import sys
import traceback
import os
from pathlib import Path

# Set base path untuk PyInstaller
def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # Import GUI
        from gui.main_gui import WerewolfBotGUI
        
        root = tk.Tk()
        app = WerewolfBotGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
        
    except Exception as e:
        # Simpan error ke file
        error_msg = f"Error: {e}\n{traceback.format_exc()}"
        
        try:
            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(error_msg)
        except:
            pass
        
        # Tampilkan message box error jika tkinter bisa digunakan
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error", f"Bot gagal dijalankan!\n\n{e}\n\nCek error_log.txt untuk detail.")
            root.destroy()
        except:
            print(error_msg)
        
        raise

if __name__ == "__main__":
    main()