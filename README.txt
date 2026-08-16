========================================================
  OFFLINE TRANSLATOR  —  Arabic / French / English
========================================================

Fully offline translator with natural (non-robotic) voices,
voice input, and translation history.

--------------------------------------------------------
  HOW TO USE
--------------------------------------------------------

Just double-click:   run.bat

Your browser opens automatically at http://localhost:5757
Keep the black command window open while using the app.
To stop: close the command window (or press Ctrl+C in it).

--------------------------------------------------------
  FEATURES
--------------------------------------------------------

  * Translate between Arabic, French, English (any direction)
  * High-quality translation via NLLB-200 (Meta's neural model)
    - direct Arabic<->French, no English detour
    - handles technical text and full paragraphs
  * Natural neural voices (Piper TTS):
      - Arabic : Kareem (male)
      - French : Siwis (female)
      - English: Amy (female)
  * Voice input (microphone) via Whisper speech recognition
  * Copy button, language swap, auto-translate
  * 100% offline — no internet needed after setup

--------------------------------------------------------
  BUTTONS
--------------------------------------------------------

  Translate           - translate the input text
  Record / Stop       - speak into your mic, it transcribes
  Speak Input         - read the input aloud
  Speak Translation   - read the translation aloud
  Clear               - empty both boxes
  Swap (arrows)       - swap the two languages

  Shortcuts:  Ctrl+Enter = Translate   Ctrl+Shift+C = Copy

--------------------------------------------------------
  NOTES
--------------------------------------------------------

  - Translation uses NLLB-200, which translates every
    language pair directly (including Arabic <-> French).
  - Everything (Python, packages, AI models) lives inside
    this folder. Nothing is installed system-wide.
  - To re-download models if ever needed: setup_first.bat

--------------------------------------------------------
  FILES
--------------------------------------------------------

  run.bat           - start the app (this is all you need)
  app.py            - the application
  setup_first.bat   - re-download AI models (only if needed)
  install.bat       - re-install packages (only if needed)
  models/           - AI model files (NLLB, Piper, Whisper)
  python/           - bundled Python (self-contained)
