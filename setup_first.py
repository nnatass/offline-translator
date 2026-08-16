#!/usr/bin/env python3
"""
Run this ONCE to download all AI models (~3.5 GB total).
Needs internet. After this, the translator works fully offline.

  - NLLB-200 translation model (distilled 600M, CTranslate2)  ~2.4 GB
  - Piper TTS voices          (Arabic, French, English)      ~200 MB
  - Whisper small model       (speech recognition)           ~900 MB
"""

import sys
import os
from pathlib import Path

BASE_DIR  = Path(__file__).parent
MODELS    = BASE_DIR / "models"
PIPER_DIR = MODELS / "piper"
WSP_DIR   = MODELS / "whisper"

for d in (MODELS, PIPER_DIR, WSP_DIR):
    d.mkdir(parents=True, exist_ok=True)

PIPER_VOICES = [
    ("ar_JO-kareem-medium", "Arabic  — Kareem (male, Jordan)"),
    ("fr_FR-siwis-medium",  "French  — Siwis  (female, France)"),
    ("en_US-amy-medium",    "English — Amy    (female, US)"),
]

BAR = "─" * 56


def step(n, total, title):
    print(f"\n[{n}/{total}]  {title}")
    print(BAR)


def ok(msg):    print(f"  ✓  {msg}")
def info(msg):  print(f"  ·  {msg}")
def warn(msg):  print(f"  !  {msg}")
def fail(msg):  print(f"  ✗  {msg}")


def check_import(pkg, install_name=None):
    """Return True if importable, else warn and return False."""
    try:
        __import__(pkg)
        return True
    except ImportError:
        install_name = install_name or pkg
        warn(f"'{install_name}' not installed — run install.bat first")
        return False


# ── 1. Argos Translate ────────────────────────────────────────────────────────

def setup_argos():
    step(1, 3, "Translation model  (NLLB-200 — high quality, ~2.4 GB)")
    if not check_import("huggingface_hub", "huggingface_hub"):
        return

    from huggingface_hub import snapshot_download

    nllb_dir = MODELS / "nllb"
    nllb_dir.mkdir(parents=True, exist_ok=True)

    if (nllb_dir / "model.bin").exists():
        ok("NLLB-200 model already downloaded")
        return

    info("Downloading NLLB-200 (distilled 600M, CTranslate2) …")
    info("This is the big one — several minutes on a normal connection.")
    try:
        snapshot_download(
            repo_id="entai2965/nllb-200-distilled-600M-ctranslate2",
            local_dir=str(nllb_dir),
        )
        ok("NLLB-200 model ready — direct AR/FR/EN in all directions")
    except Exception as e:
        fail(f"Download failed: {e}")
        warn("Check your internet connection and try again.")


# ── 2. Piper TTS voices ───────────────────────────────────────────────────────

def setup_piper():
    step(2, 3, "TTS voice models  (Piper — neural, natural-sounding)")
    if not check_import("piper", "piper-tts"):
        warn("Fallback: system TTS will be used (less natural)")
        return

    try:
        from piper.download_voices import download_voice
    except Exception as e:
        warn(f"piper.download_voices not available: {e}")
        return

    for name, label in PIPER_VOICES:
        onnx = PIPER_DIR / f"{name}.onnx"
        if onnx.exists():
            ok(f"{label}  already downloaded")
            continue
        print(f"  ↓  {label} …", end=" ", flush=True)
        try:
            download_voice(name, PIPER_DIR)
            print("done")
        except Exception as e:
            print(f"FAILED  ({e})")


# ── 3. Whisper speech recognition ────────────────────────────────────────────

def setup_whisper():
    step(3, 3, "Speech recognition  (Whisper small — ~900 MB)")
    if not check_import("faster_whisper", "faster-whisper"):
        return

    from faster_whisper import WhisperModel

    # Check if already cached (Hugging Face cache structure)
    cached = list(WSP_DIR.glob("models--Systran*"))
    if cached:
        ok("Whisper 'small' model already downloaded")
        return

    info("Downloading … this may take several minutes on slow connections")
    try:
        WhisperModel("small", device="cpu", compute_type="int8",
                     download_root=str(WSP_DIR))
        ok("Whisper model ready")
    except Exception as e:
        fail(f"Download failed: {e}")
        warn("Make sure you have enough disk space (~1 GB free) and internet access.")


# ── Verify everything is ready ────────────────────────────────────────────────

def verify():
    print(f"\n{BAR}")
    print("  Verification")
    print(BAR)

    issues = []

    # NLLB model
    if (MODELS / "nllb" / "model.bin").exists():
        ok("NLLB-200 translation model: found")
    else:
        issues.append("NLLB-200 model not found")

    # Piper voices
    try:
        found_voices = []
        for name, label in PIPER_VOICES:
            onnx = PIPER_DIR / f"{name}.onnx"
            if onnx.exists():
                found_voices.append(name.split("-")[0])
            else:
                issues.append(f"Missing Piper voice: {name}")
        if found_voices:
            ok(f"Piper voices found: {', '.join(found_voices)}")
    except Exception as e:
        issues.append(f"Piper check failed: {e}")

    # Whisper
    cached = list(WSP_DIR.glob("models--Systran*"))
    if cached:
        ok("Whisper model: found")
    else:
        issues.append("Whisper model not found")

    print()
    if issues:
        for issue in issues:
            warn(issue)
        print("\n  Re-run this script to retry any failed downloads.")
    else:
        print("  Everything is ready!")

    return len(issues) == 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("   Offline Translator — First-Time Setup")
    print("=" * 56)
    print()
    print("  This downloads ~2 GB of AI model files (one time).")
    print("  After this, the app works with NO internet required.")
    print()

    try:
        setup_argos()
        setup_piper()
        setup_whisper()
        all_ok = verify()
    except KeyboardInterrupt:
        print("\n\n  Setup interrupted. Re-run setup_first.py to continue.")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        sys.exit(1)

    print(f"\n{'=' * 56}")
    if all_ok:
        print("  Setup complete!  Run translator.py to start.")
    else:
        print("  Setup finished with some issues — see above.")
    print(f"{'=' * 56}\n")
