# updater.py


import os
import sys
import json
import base64
import hashlib
import shutil
import zipfile
import tempfile
import threading
import requests
from pathlib import Path
from typing import Callable, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Config loader — baca dari _secret.py yang terenkripsi
# ─────────────────────────────────────────────────────────────────────────────

def _derive_key(salt: bytes) -> bytes:
    seed = b"WerewolfBot_2025_" + salt
    return hashlib.sha256(seed).digest()


def _xor_decrypt(enc_b64: str, key: bytes) -> str:
    encrypted  = base64.b64decode(enc_b64.encode("ascii"))
    key_stream = (key * ((len(encrypted) // len(key)) + 1))[:len(encrypted)]
    decrypted  = bytes(a ^ b for a, b in zip(encrypted, key_stream))
    return decrypted.decode("utf-8")


def _load_config() -> tuple:
    """
    Load GITHUB_OWNER dan GITHUB_REPO dari gui/_secret.py.
    Fallback ke env vars jika _secret.py tidak ada (untuk CI/dev).
    """
    try:
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
        secret_path = base / "gui" / "_secret.py"

        if not secret_path.exists():
            secret_path = Path(__file__).parent / "gui" / "_secret.py"

        if secret_path.exists():
            ns = {}
            exec(secret_path.read_text(encoding="utf-8"), ns)

            salt  = base64.b64decode(ns["_SALT"].encode("ascii"))
            key   = _derive_key(salt)
            owner = _xor_decrypt(ns["_ENC_OWNER"], key)
            repo  = _xor_decrypt(ns["_ENC_REPO"],  key)
            return owner, repo
    except Exception:
        pass

    # Fallback: environment variables
    owner = os.environ.get("GH_OWNER", "")
    repo  = os.environ.get("GH_REPO",  "")
    if owner and repo:
        return owner, repo

    raise RuntimeError(
        "Konfigurasi GitHub tidak ditemukan.\n"
        "Jalankan: python tools/encrypt_config.py"
    )


_CONFIG_CACHE = None

def _get_config() -> tuple:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = _load_config()
    return _CONFIG_CACHE


# ─────────────────────────────────────────────────────────────────────────────
# File & path config
# ─────────────────────────────────────────────────────────────────────────────

VERSION_FILE = Path(__file__).parent / "version.json"
BASE_DIR     = Path(__file__).parent

SKIP_PATHS = {
    "window_config.json",
    "version.json",
    "_secret.py",
    ".env",
    "token.txt",
}


# ─────────────────────────────────────────────────────────────────────────────
# Core update logic
# ─────────────────────────────────────────────────────────────────────────────

def get_local_version() -> str:
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("version", "v0.0.0")
        except Exception:
            pass
    return "v0.0.0"


def save_local_version(version: str):
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"version": version}, f, indent=2)
    except Exception:
        pass


def _parse_version(tag: str) -> tuple:
    try:
        return tuple(int(x) for x in tag.lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def check_for_update(timeout: int = 10) -> Optional[dict]:
    try:
        owner, repo = _get_config()
    except RuntimeError:
        return None

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        resp = requests.get(
            url, timeout=timeout,
            headers={"Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    remote_tag = data.get("tag_name", "v0.0.0")
    local_tag  = get_local_version()

    if _parse_version(remote_tag) <= _parse_version(local_tag):
        return None

    assets    = data.get("assets", [])
    zip_asset = next((a for a in assets if a["name"].endswith(".zip")), None)
    if not zip_asset:
        return None

    return {
        "tag":          remote_tag,
        "notes":        data.get("body", ""),
        "download_url": zip_asset["browser_download_url"],
        "asset_name":   zip_asset["name"],
        "size":         zip_asset["size"],
    }


def download_and_apply(update_info: dict, progress_cb=None) -> bool:
    def _prog(msg: str, pct: int = -1):
        if progress_cb:
            progress_cb(msg, pct)

    try:
        _prog("Mendownload update...", 0)
        resp = requests.get(update_info["download_url"], stream=True, timeout=60)
        resp.raise_for_status()

        total      = update_info["size"] or 1
        downloaded = 0
        tmp_zip    = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")

        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                tmp_zip.write(chunk)
                downloaded += len(chunk)
                _prog(f"Mendownload... {downloaded // 1024} KB",
                      int(downloaded / total * 80))

        tmp_zip.close()
        _prog("Mengekstrak...", 82)

        tmp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(tmp_zip.name, "r") as zf:
            zf.extractall(tmp_dir)

        _prog("Menerapkan update...", 88)

        tmp_path = Path(tmp_dir)
        contents = list(tmp_path.iterdir())
        src_root = contents[0] if len(contents) == 1 and contents[0].is_dir() else tmp_path

        _copy_update(src_root, BASE_DIR, _prog)
        save_local_version(update_info["tag"])
        _prog(f"Update {update_info['tag']} berhasil!", 100)

        os.unlink(tmp_zip.name)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return True

    except Exception as e:
        _prog(f"Gagal update: {e}", -1)
        return False


def _copy_update(src: Path, dst: Path, prog_cb):
    dst.mkdir(parents=True, exist_ok=True)
    items = list(src.rglob("*"))
    total = max(len(items), 1)

    for i, item in enumerate(items):
        rel = item.relative_to(src)
        if any(part in SKIP_PATHS for part in rel.parts):
            continue
        if "__pycache__" in rel.parts:
            continue
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(item), str(target))
        prog_cb(f"Menyalin: {rel}", 88 + int(i / total * 10))


# ─────────────────────────────────────────────────────────────────────────────
# Thread wrapper
# ─────────────────────────────────────────────────────────────────────────────

class UpdateChecker:
    def __init__(self, on_update_found=None, on_no_update=None, on_error=None):
        self._on_found = on_update_found or (lambda _: None)
        self._on_none  = on_no_update    or (lambda: None)
        self._on_error = on_error        or (lambda _: None)

    def check_async(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            info = check_for_update()
            if info:
                self._on_found(info)
            else:
                self._on_none()
        except Exception as e:
            self._on_error(str(e))