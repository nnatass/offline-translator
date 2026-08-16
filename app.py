#!/usr/bin/env python3
"""
Offline Translator — Web UI
Run: python app.py  → opens http://localhost:5757
"""

import os, time, wave, io, tempfile, threading, json
import webbrowser
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string

BASE_DIR     = Path(__file__).parent
PIPER_DIR    = BASE_DIR / "models" / "piper"
WSP_DIR      = BASE_DIR / "models" / "whisper"
NLLB_DIR     = BASE_DIR / "models" / "nllb"

PIPER_VOICES = {
    "ar": "ar_JO-kareem-medium",
    "fr": "fr_FR-siwis-medium",
    "en": "en_US-amy-medium",
}

# NLLB-200 language codes
NLLB_LANG = {
    "ar": "arb_Arab",
    "fr": "fra_Latn",
    "en": "eng_Latn",
}

# ── Global state ───────────────────────────────────────────────────────────────
G = {
    "ready":    False,
    "status":   "Loading models…",
    "speaking": False,
    "recording": False,
    "nllb":     None,
    "nllb_tok": None,
    "whisper":  None,
    "piper":    {},
    "rec_chunks": [],
}

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Offline Translator</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0f1117;--panel:#1a1d26;--border:#2a2d3a;
    --accent:#3b82f6;--accent2:#6366f1;
    --text:#e2e8f0;--muted:#64748b;--green:#22c55e;
    --red:#ef4444;--purple:#a855f7;
  }
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',Arial,sans-serif;min-height:100vh}
  h1{font-size:1.6rem;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--accent2));
     -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}

  /* header */
  .header{display:flex;align-items:center;justify-content:space-between;
          padding:18px 28px;border-bottom:1px solid var(--border)}
  .status-dot{width:8px;height:8px;border-radius:50%;background:var(--red);
              display:inline-block;margin-right:6px;transition:.3s}
  .status-dot.ready{background:var(--green)}
  #statusText{font-size:.85rem;color:var(--muted)}

  /* lang bar */
  .langbar{display:flex;align-items:center;gap:12px;padding:14px 28px;
           border-bottom:1px solid var(--border)}
  select{background:var(--panel);color:var(--text);border:1px solid var(--border);
         border-radius:8px;padding:8px 12px;font-size:.95rem;cursor:pointer;outline:none}
  select:focus{border-color:var(--accent)}
  .swap-btn{background:var(--panel);border:1px solid var(--border);color:var(--text);
            width:38px;height:38px;border-radius:8px;font-size:1.2rem;cursor:pointer;
            display:flex;align-items:center;justify-content:center;transition:.15s}
  .swap-btn:hover{border-color:var(--accent);color:var(--accent)}

  /* main area */
  .main{display:grid;grid-template-columns:1fr 1fr;gap:0;flex:1}
  .pane{padding:16px 28px;display:flex;flex-direction:column;gap:8px}
  .pane:first-child{border-right:1px solid var(--border)}
  .pane-header{display:flex;justify-content:space-between;align-items:center}
  .pane-label{font-size:.8rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
  .char-count{font-size:.78rem;color:var(--muted)}
  textarea{background:transparent;border:none;color:var(--text);font-size:1.1rem;
           font-family:'Arial',sans-serif;resize:none;outline:none;flex:1;
           line-height:1.6;min-height:220px}
  textarea::placeholder{color:var(--muted)}
  textarea:read-only{cursor:default}

  /* action bar */
  .actions{display:flex;flex-wrap:wrap;gap:10px;padding:14px 28px;
           border-top:1px solid var(--border)}
  .btn{display:inline-flex;align-items:center;gap:6px;padding:9px 18px;
       border-radius:8px;border:none;font-size:.9rem;font-weight:600;
       cursor:pointer;transition:.15s;color:#fff}
  .btn:disabled{opacity:.4;cursor:not-allowed}
  .btn-blue{background:var(--accent)}
  .btn-blue:hover:not(:disabled){background:#2563eb}
  .btn-green{background:#166534}
  .btn-green:hover:not(:disabled){background:var(--green);color:#000}
  .btn-green.recording{background:var(--red)}
  .btn-purple{background:#4c1d95}
  .btn-purple:hover:not(:disabled){background:var(--purple)}
  .btn-gray{background:#374151}
  .btn-gray:hover:not(:disabled){background:#4b5563}
  .btn-copy{background:var(--panel);border:1px solid var(--border);color:var(--muted);
            padding:5px 12px;font-size:.8rem;border-radius:6px;cursor:pointer}
  .btn-copy:hover{border-color:var(--accent);color:var(--accent)}
  .auto-label{display:flex;align-items:center;gap:6px;font-size:.85rem;color:var(--muted);
              margin-left:auto;cursor:pointer}
  .auto-label input{cursor:pointer}

  /* shortcuts hint */
  .shortcuts{font-size:.75rem;color:#374151;padding:4px 28px 10px;
             border-top:1px solid var(--border)}

  /* toast */
  #toast{position:fixed;bottom:28px;right:28px;background:#1e293b;border:1px solid var(--border);
         color:var(--text);padding:10px 18px;border-radius:10px;font-size:.88rem;
         opacity:0;transition:.3s;pointer-events:none;z-index:99}
  #toast.show{opacity:1}

  /* layout */
  .app{display:flex;flex-direction:column;height:100vh}
  .middle{display:flex;flex:1;overflow:hidden}
  .left,.right{flex:1;display:flex;flex-direction:column;padding:16px 24px;gap:8px}
  .left{border-right:1px solid var(--border)}
  audio{width:100%;margin-top:6px;display:none}
  audio.visible{display:block}
</style>
</head>
<body>
<div class="app">

  <!-- Header -->
  <div class="header">
    <h1>Offline Translator</h1>
    <div style="display:flex;align-items:center;gap:8px">
      <span class="status-dot" id="dot"></span>
      <span id="statusText">Loading models…</span>
    </div>
  </div>

  <!-- Language bar -->
  <div class="langbar">
    <select id="srcLang">
      <option value="ar">🇸🇦 Arabic</option>
      <option value="fr">🇫🇷 French</option>
      <option value="en" selected>🇬🇧 English</option>
    </select>
    <button class="swap-btn" onclick="swapLangs()" title="Swap languages">⇄</button>
    <select id="tgtLang">
      <option value="ar" selected>🇸🇦 Arabic</option>
      <option value="fr">🇫🇷 French</option>
      <option value="en">🇬🇧 English</option>
    </select>
    <span style="margin-left:auto;font-size:.8rem;color:var(--muted)">
      Ctrl+Enter = Translate &nbsp;|&nbsp; Ctrl+Shift+C = Copy
    </span>
  </div>

  <!-- Text area -->
  <div class="middle">
    <div class="left">
      <div class="pane-header">
        <span class="pane-label">Input</span>
        <span class="char-count" id="inCount">0 chars</span>
      </div>
      <textarea id="inputText" placeholder="Type or paste text here… or use Record to speak"
                oninput="onType()" rows="10"></textarea>
    </div>
    <div class="right">
      <div class="pane-header">
        <span class="pane-label">Translation</span>
        <div style="display:flex;gap:6px;align-items:center">
          <span class="char-count" id="outCount">0 chars</span>
          <button class="btn-copy" onclick="copyTranslation()">📋 Copy</button>
        </div>
      </div>
      <textarea id="outputText" readonly placeholder="Translation appears here…" rows="10"></textarea>
      <audio id="ttsAudio" controls></audio>
    </div>
  </div>

  <!-- Actions — no onclick attrs, all wired via addEventListener below -->
  <div class="actions">
    <button class="btn btn-blue"   id="btnTranslate" disabled>⚡ Translate</button>
    <button class="btn btn-green"  id="btnRecord"    disabled>🎤 Record</button>
    <button class="btn btn-purple" id="btnSpeakIn"   disabled>🔊 Speak Input</button>
    <button class="btn btn-purple" id="btnSpeakOut"  disabled>🔊 Speak Translation</button>
    <button class="btn btn-gray"   id="btnClear">✕ Clear</button>
    <label class="auto-label">
      <input type="checkbox" id="autoTranslate"> Auto-translate
    </label>
  </div>

</div>

<div id="toast"></div>

<script>
// ── All state in one object to avoid any scoping surprises ─────────────────
const APP = { recording: false, autoTimer: null };

// ── DOM shortcuts ──────────────────────────────────────────────────────────
const $  = id => document.getElementById(id);
const inputText  = () => $('inputText').value.trim();
const outputText = () => $('outputText').value.trim();
const srcLang    = () => $('srcLang').value;
const tgtLang    = () => $('tgtLang').value;

function setStatus(msg) { $('statusText').textContent = msg; }

function showToast(msg) {
  $('toast').textContent = msg;
  $('toast').className = 'show';
  setTimeout(() => $('toast').className = '', 2400);
}

function updateCounts() {
  $('inCount').textContent  = $('inputText').value.length  + ' chars';
  $('outCount').textContent = $('outputText').value.length + ' chars';
}

function setOutput(text) {
  $('outputText').value = text;
  updateCounts();
}

// ── Status polling ─────────────────────────────────────────────────────────
function pollStatus() {
  fetch('/status')
    .then(r => r.json())
    .then(d => {
      setStatus(d.status);
      $('dot').className = 'status-dot' + (d.ready ? ' ready' : '');
      if (d.ready) {
        ['btnTranslate','btnRecord','btnSpeakIn','btnSpeakOut'].forEach(id => {
          $(id).disabled = false;
        });
      } else {
        setTimeout(pollStatus, 900);
      }
    })
    .catch(() => setTimeout(pollStatus, 2000));
}
pollStatus();

// ── Translation ────────────────────────────────────────────────────────────
async function doTranslate() {
  const text = inputText();
  if (!text) return;
  const src = srcLang(), tgt = tgtLang();
  if (src === tgt) { setOutput(text); return; }
  setStatus('Translating…');
  try {
    const r = await fetch('/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, src, tgt })
    });
    const d = await r.json();
    setOutput(d.result || d.error || '');
    setStatus('Done');
  } catch (e) {
    setStatus('Error: ' + e);
  }
}

// ── TTS ────────────────────────────────────────────────────────────────────
async function doSpeak(which) {
  const text = which === 'input' ? inputText()  : outputText();
  const lang = which === 'input' ? srcLang()    : tgtLang();
  if (!text) { showToast('Nothing to speak'); return; }
  setStatus('Generating audio…');
  try {
    const r = await fetch('/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang })
    });
    if (r.ok) {
      const url = URL.createObjectURL(await r.blob());
      const audio = $('ttsAudio');
      audio.src = url;
      audio.className = 'visible';
      audio.play();
      setStatus('Playing…');
      audio.onended = () => setStatus('Ready');
    } else {
      const d = await r.json();
      setStatus('TTS error: ' + (d.error || 'unknown'));
    }
  } catch (e) {
    setStatus('TTS error: ' + e);
  }
}

// ── STT ────────────────────────────────────────────────────────────────────
async function doToggleRecord() {
  const btn = $('btnRecord');
  if (!APP.recording) {
    const r = await fetch('/record/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lang: srcLang() })
    });
    if (!r.ok) { showToast('Could not start recording'); return; }
    APP.recording = true;
    btn.textContent = '⏹ Stop';
    btn.style.background = 'var(--red)';
    setStatus('Listening… click Stop when done');
  } else {
    APP.recording = false;
    btn.textContent = '🎤 Record';
    btn.style.background = '';
    setStatus('Processing…');
    const r = await fetch('/record/stop', { method: 'POST' });
    const d = await r.json();
    if (d.text) {
      $('inputText').value = d.text;
      updateCounts();
      setStatus('Transcribed — click Translate or press Ctrl+Enter');
    } else {
      setStatus(d.error || 'Nothing captured');
    }
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function doSwap() {
  const sv = $('srcLang').value, tv = $('tgtLang').value;
  $('srcLang').value = tv;
  $('tgtLang').value = sv;
  const si = $('inputText').value, so = $('outputText').value;
  $('inputText').value  = so;
  $('outputText').value = si;
  updateCounts();
}

function doCopy() {
  const text = $('outputText').value;
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => showToast('Copied!'));
}

function doClear() {
  $('inputText').value  = '';
  $('outputText').value = '';
  updateCounts();
  setStatus('Ready');
}

// ── Wire up all buttons via addEventListener (no onclick= attributes) ──────
document.addEventListener('DOMContentLoaded', () => {
  $('btnTranslate').addEventListener('click', doTranslate);
  $('btnRecord')   .addEventListener('click', doToggleRecord);
  $('btnSpeakIn')  .addEventListener('click', () => doSpeak('input'));
  $('btnSpeakOut') .addEventListener('click', () => doSpeak('output'));
  $('btnClear')    .addEventListener('click', doClear);
  document.querySelector('.swap-btn').addEventListener('click', doSwap);
  document.querySelector('.btn-copy').addEventListener('click', doCopy);

  $('inputText').addEventListener('input', () => {
    updateCounts();
    if (!$('autoTranslate').checked) return;
    clearTimeout(APP.autoTimer);
    if ($('inputText').value.trim().length > 2)
      APP.autoTimer = setTimeout(doTranslate, 1400);
  });

  document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); doTranslate(); }
    if (e.ctrlKey && e.shiftKey && e.key === 'C') { e.preventDefault(); doCopy(); }
  });
});
</script>
</body>
</html>
"""


# ── Load models ────────────────────────────────────────────────────────────────

def set_status(msg):
    G["status"] = msg
    print(f"[STATUS] {msg}")


def load_models():
    set_status("Loading translation engine (NLLB-200)…")
    try:
        import ctranslate2
        import transformers
        G["nllb_tok"] = transformers.AutoTokenizer.from_pretrained(str(NLLB_DIR))
        G["nllb"]     = ctranslate2.Translator(str(NLLB_DIR), device="cpu",
                                                compute_type="int8")
    except Exception as e:
        set_status(f"NLLB error — run setup_first.py  ({e})")
        return

    set_status("Loading speech recognition (Whisper)…")
    try:
        from faster_whisper import WhisperModel
        G["whisper"] = WhisperModel("small", device="cpu", compute_type="int8",
                                     download_root=str(WSP_DIR))
    except Exception as e:
        set_status(f"Whisper error — run setup_first.py  ({e})")
        return

    set_status("Loading TTS voices (Piper)…")
    try:
        from piper import PiperVoice
        for code, name in PIPER_VOICES.items():
            onnx = PIPER_DIR / f"{name}.onnx"
            jcfg = PIPER_DIR / f"{name}.onnx.json"
            if not jcfg.exists():
                # config file may be stored without .onnx prefix
                jcfg = PIPER_DIR / f"{name}.json"
            if onnx.exists() and jcfg.exists():
                G["piper"][code] = PiperVoice.load(str(onnx), config_path=str(jcfg))
    except ImportError:
        pass

    voice_names = [PIPER_VOICES[c] for c in G["piper"]] if G["piper"] else ["none (run setup_first.py)"]
    set_status(f"Ready  ·  voices: {', '.join(voice_names)}")
    G["ready"] = True


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/status")
def status():
    return jsonify({"ready": G["ready"], "status": G["status"]})


@app.route("/translate", methods=["POST"])
def translate():
    if not G["ready"]:
        return jsonify({"error": "Models not ready yet"}), 503
    data = request.get_json()
    text = data.get("text", "").strip()
    src  = data.get("src", "en")
    tgt  = data.get("tgt", "ar")
    if not text:
        return jsonify({"result": ""})
    if src == tgt:
        return jsonify({"result": text})
    try:
        result = _do_translate(text, src, tgt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _split_sentences(text):
    """Split text into sentences/lines so NLLB stays under its length limit
    and gives cleaner output. Keeps blank lines as paragraph breaks."""
    import re
    out = []
    for line in text.split("\n"):
        if not line.strip():
            out.append("")  # preserve paragraph break
            continue
        # Split after . ! ? and Arabic ؟ ! while keeping the delimiter
        parts = re.split(r"(?<=[.!?؟])\s+", line.strip())
        out.extend(p for p in parts if p)
    return out


def _do_translate(text, src, tgt):
    tok   = G["nllb_tok"]
    trans = G["nllb"]
    src_code, tgt_code = NLLB_LANG[src], NLLB_LANG[tgt]
    tok.src_lang = src_code

    sentences = _split_sentences(text)
    results = []
    for sent in sentences:
        if not sent:
            results.append("")  # blank line → paragraph break
            continue
        source = tok.convert_ids_to_tokens(tok.encode(sent))
        out = trans.translate_batch(
            [source],
            target_prefix=[[tgt_code]],
            beam_size=4,
            max_decoding_length=512,
        )
        target = out[0].hypotheses[0][1:]  # drop the language token
        results.append(tok.decode(tok.convert_tokens_to_ids(target)))

    # Rejoin: blanks become newlines, sentences joined by space
    text_out, prev_blank = "", False
    for i, r in enumerate(results):
        if r == "":
            text_out += "\n"
            prev_blank = True
        else:
            if text_out and not text_out.endswith("\n"):
                text_out += " "
            text_out += r
            prev_blank = False
    return text_out.strip()


@app.route("/speak", methods=["POST"])
def speak():
    if not G["ready"]:
        return jsonify({"error": "Not ready"}), 503
    data = request.get_json()
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    if not text:
        return jsonify({"error": "No text"}), 400

    voice = G["piper"].get(lang)
    if not voice:
        return jsonify({"error": f"No Piper voice for '{lang}'. Run setup_first.py"}), 503

    try:
        import numpy as np
        import soundfile as sf

        chunks = list(voice.synthesize(text))
        if not chunks:
            return jsonify({"error": "No audio generated"}), 500

        audio = np.concatenate([c.audio_float_array for c in chunks])
        sr    = chunks[0].sample_rate

        # Write to temp WAV file (soundfile handles headers correctly)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        sf.write(tmp.name, audio.astype(np.float32), sr, format="WAV", subtype="PCM_16")

        def remove_tmp():
            try: os.unlink(tmp.name)
            except OSError: pass

        response = send_file(tmp.name, mimetype="audio/wav", as_attachment=False)
        response.call_on_close(remove_tmp)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/record/start", methods=["POST"])
def record_start():
    if G["recording"]:
        return jsonify({"error": "Already recording"}), 400
    G["recording"]   = True
    G["rec_chunks"]  = []
    G["rec_lang"]    = request.get_json(silent=True, force=True).get("lang", "en")
    threading.Thread(target=_do_record, daemon=True).start()
    return jsonify({"ok": True})


def _do_record():
    import sounddevice as sd
    def cb(indata, frames, t, status):
        if G["recording"]:
            G["rec_chunks"].append(indata.copy())
    with sd.InputStream(samplerate=16000, channels=1, dtype="float32", callback=cb):
        while G["recording"]:
            time.sleep(0.05)


@app.route("/record/stop", methods=["POST"])
def record_stop():
    G["recording"] = False
    time.sleep(0.2)  # let last chunk arrive
    import numpy as np
    import soundfile as sf

    chunks = G["rec_chunks"]
    if not chunks:
        return jsonify({"error": "No audio captured"})

    audio = np.concatenate(chunks).flatten()
    tmp   = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, 16000)
    tmp.close()

    try:
        lang = G.get("rec_lang", "en")
        segs, _ = G["whisper"].transcribe(tmp.name, language=lang, beam_size=5)
        text = " ".join(s.text for s in segs).strip()
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 54)
    print("  Offline Translator  —  starting server")
    print("=" * 54)
    threading.Thread(target=load_models, daemon=True).start()
    # Open browser after short delay
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5757")).start()
    print("  Opening http://localhost:5757 in your browser…")
    print("  Press Ctrl+C to stop\n")
    app.run(host="127.0.0.1", port=5757, debug=False)
