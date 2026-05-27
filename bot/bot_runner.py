# bot/bot_runner.py
import sys
import os

# ── UTF-8 stdout/stderr untuk Windows ─────────────────────────────────────
# Gunakan reconfigure() jika tersedia (Python 3.7+),
# jangan buat TextIOWrapper baru karena parent process bisa sudah redirect stdout.
def _ensure_utf8(stream):
    try:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        elif hasattr(stream, "buffer"):
            import io
            return io.TextIOWrapper(stream.buffer, encoding="utf-8",
                                    errors="replace", line_buffering=True)
    except Exception:
        pass
    return stream

sys.stdout = _ensure_utf8(sys.stdout)
sys.stderr = _ensure_utf8(sys.stderr)

# ── Path ───────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.bot import run_bot

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else input("Masukkan token: ")
    try:
        run_bot(token)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback
        print(f"FATAL ERROR: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)