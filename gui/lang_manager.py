# gui/lang_manager.py
import xml.etree.ElementTree as ET
from pathlib import Path
import sys


def get_base_path():
    """Get base path for PyInstaller one-file build"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent.parent


class LanguageManager:
    def __init__(self):
        base_path = get_base_path()
        self.lang_folder = base_path / "Lang"
        self.current_lang = "ID"
        self.strings = {}
        self.load_language("ID")

    def load_language(self, lang_code):
        """Load language file for given language code (ID or ENG)"""
        if lang_code == "ID":
            file_path = self.lang_folder / "ID" / "id.xml"
        elif lang_code == "ENG":
            file_path = self.lang_folder / "ENG" / "eng.xml"
        else:
            return
        
        if not file_path.exists():
            print(f"Language file not found: {file_path}")
            return
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            self.strings = {}
            for string in root.findall("string"):
                name = string.get("name")
                text = string.text
                if name and text:
                    self.strings[name] = text
            self.current_lang = lang_code
        except Exception as e:
            print(f"Error loading language file: {e}")

    def get(self, key, default=None):
        """Get translation for key"""
        return self.strings.get(key, default)

    def set_language(self, lang_code):
        """Change language and reload"""
        self.load_language(lang_code)