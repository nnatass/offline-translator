# Offline Translator — Arabic / French / English

A fully **offline** translator with high-quality neural translation, natural (non-robotic) text-to-speech, and voice input. No internet needed after the one-time model download. Runs as a local web app in your browser.

## Features

- **Translate** between Arabic, French, and English — any direction
- **High-quality translation** via [NLLB-200](https://ai.meta.com/research/no-language-left-behind/) (Meta's neural model)
  - Direct Arabic ↔ French (no English detour)
  - Handles technical text and full paragraphs
- **Natural neural voices** via [Piper TTS](https://github.com/rhasspy/piper):
  - Arabic — Kareem (male)
  - French — Siwis (female)
  - English — Amy (female)
- **Voice input** (microphone) via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) speech recognition
- Copy button, language swap, auto-translate, keyboard shortcuts
- **100% offline** after setup

## Requirements

- Windows (tested on Windows 11)
- [Python 3.9+](https://www.python.org/downloads/) with `pip`
- ~4 GB free disk space (for the AI models)
- A microphone (optional, for voice input)

## Install

```bash
# 1. Install the Python packages
pip install -r requirements.txt

# 2. Download the AI models (~3.5 GB, one time, needs internet)
python setup_first.py

# 3. Run the app
python app.py
```

The app opens automatically at **http://localhost:5757**.

> On Windows you can also use the included `install.bat`, `setup_first.bat`, and `run.bat` if you have a bundled `python\` folder. If you cloned this repo, use the `pip` / `python` commands above instead.

## Usage

| Button | Action |
|---|---|
| **Translate** | Translate the input text |
| **Record / Stop** | Speak into your mic; it transcribes to the input box |
| **Speak Input** | Read the input aloud |
| **Speak Translation** | Read the translation aloud |
| **Clear** | Empty both boxes |
| **⇄** | Swap the two languages |

**Shortcuts:** `Ctrl+Enter` = Translate · `Ctrl+Shift+C` = Copy

## How it works

| Component | Model |
|---|---|
| Translation | NLLB-200 distilled 600M (CTranslate2, int8, CPU) |
| Text-to-speech | Piper neural voices (ONNX) |
| Speech recognition | Whisper small (CTranslate2, int8, CPU) |
| UI | Flask + a single-page browser front-end |

The AI models are **not** stored in this repository (they're large). `setup_first.py` downloads them into a local `models/` folder, which is git-ignored.

## Project layout

```
app.py            The application (Flask server + web UI)
setup_first.py    Downloads the AI models
requirements.txt  Python dependencies
models/           AI models — downloaded by setup, git-ignored
```

## License

Provided as-is for personal use. The bundled models carry their own licenses
(NLLB: CC-BY-NC 4.0 · Piper: MIT · Whisper: MIT).
