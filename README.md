# Picsou Shorts Generator

Génère automatiquement une vidéo MP4 au format Shorts (1080×1920) à partir d'un simple prompt texte.  
Le personnage Picsou parle en français, animé bouche ouverte/fermée, avec sous-titres dynamiques mot-par-mot.

---

## Prérequis

| Outil | Version minimale | Installation |
|---|---|---|
| Python | 3.10+ | [python.org](https://python.org) |
| FFmpeg | 4.x+ | `apt install ffmpeg` (Linux) · `brew install ffmpeg` (macOS) |
| Clé API OpenAI | — | [platform.openai.com](https://platform.openai.com) |

---

## Installation

```bash
# 1. Cloner le dépôt
git clone git@github.com:taher-software/video-shorts.git
cd video-shorts/picsou-shorts

# 2. Créer et activer un environnement virtuel
python3.10 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Installer les dépendances
pip install -r requirements.txt
```

---

## Configuration



```env
export default OPENAI_API_KEY=sk-..
```

---

## Générer une vidéo

Depuis le dossier `picsou-shorts/` :

```bash
python -m src.main --prompt "Explique pourquoi il ne faut jamais prêter d'argent"
```

La vidéo est générée dans `output/video_YYYYMMDD_HHMMSS.mp4`.

### Options disponibles

```bash
python -m src.main --help
```

| Option | Défaut | Description |
|---|---|---|
| `--prompt` / `-p` | *(requis)* | Sujet du monologue de Picsou |

### Exemple de sortie console

```
────────────── Picsou Shorts Generator ───────────────
[1/5] Generating script...       ✓ 142 mots · mood=sarcastique
[2/5] Generating voice (TTS)...  ✓ voice.mp3
[2/5] Transcribing with Whisper... ✓ 89 word timestamps
[3/5] Preparing visual assets...
[3/5] Checking character images... ✓ reusing existing pair
[3/5] Generating background with DALL-E 3...
[3/5] Analysing audio amplitudes... ✓ 930 frames · 63% mouth-open
[4/5] Generating subtitles...    ✓ 89 entries · 23 blocks
[5/5] Composing video...
[5/5] Rendering 930 frames...
[5/5] Encoding with FFmpeg...
[5/5] Done — output/video_20260417_143022.mp4 (1080×1920, 31.0s)
```

---

## Coût API estimé (par vidéo ~30 s)

| Étape | API | Coût estimé |
|---|---|---|
| Script | GPT-4o | ~$0.003 |
| Voix | OpenAI tts-1 | ~$0.002 |
| Timestamps | Whisper | ~$0.005 |
| Fond | DALL-E 3 | ~$0.040 |
| Personnage | DALL-E 3 × 2 | ~$0.080 (généré **une seule fois**) |
| **Total** | | **~$0.05 / vidéo** (après première génération) |

> Les images du personnage (`picsou_mouth_closed.png`, `picsou_mouth_open.png`) sont générées une seule fois et réutilisées pour toutes les vidéos suivantes.

---

## Architecture du code



## Structure

```
src/
├── main.py               # Point d'entrée CLI (Typer)
├── pipeline.py           # Orchestrateur des 5 étapes
├── settings.py           # Initialisation des clients API (OpenAI)
│
├── steps/                # Une étape = un module, responsabilité unique
│   ├── step01_script.py  # Génération du script via GPT-4o
│   ├── step02_voice.py   # TTS (OpenAI tts-1) + timestamps (Whisper)
│   ├── step03_visuals.py # Assets visuels : personnage + fond DALL-E + analyse audio
│   ├── step04_subtitles.py # Groupage des timestamps en blocs de sous-titres
│   └── step05_compose.py # Rendu Pillow frame-par-frame + encodage FFmpeg
│
├── services/             # Clients et utilitaires réutilisables
│   ├── llm.py            # Client GPT-4o avec retry/cache
│   ├── tts.py            # Client TTS avec retry/cache
│   ├── whisper.py        # Transcription Whisper avec timestamps mot-à-mot
│   ├── image_gen.py      # DALL-E 3 : fond (avec cache URL) + dégradé Pillow
│   ├── audio_analysis.py # RMS par frame, seuil adaptatif, états bouche
│   ├── subtitle_renderer.py # Rendu Pillow des blocs de sous-titres (overlay RGBA)
│   └── ffmpeg.py         # Encodage FFmpeg (frames → MP4) + ffprobe durée
│
├── models/
│   └── pipeline.py       # Dataclasses du contexte partagé entre étapes
│
├── prompts/
│   ├── script_system.txt # System prompt Picsou (personnage, style, format JSON)
│   └── script_user.txt   # Template du user prompt avec {prompt}
│
└── utils/
    ├── audio.py          # Helpers audio (à compléter selon besoins)
    ├── image.py          # Helpers image
    └── time_utils.py     # Formatage de durées
```

---

## Pipeline

Chaque étape reçoit un `PipelineContext`, l'enrichit, et le retourne.

```
Prompt utilisateur
      │
      ▼
┌─────────────┐
│  step 1     │  GPT-4o → script (80-200 mots) + background_description + mood
│  SCRIPT     │  Sortie : ctx.script  |  Fichier : work_dir/script.json
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  step 2     │  OpenAI tts-1 → voice.mp3
│  VOICE      │  Whisper → timestamps mot-à-mot (fallback : estimation uniforme)
└──────┬──────┘  Sortie : ctx.voice + ctx.timestamps  |  Fichiers : voice.mp3, timestamps.json
       │
       ▼
┌─────────────┐
│  step 3     │  DALL-E 3 → fond (1024×1024, basé sur background_description)
│  VISUALS    │  DALL-E 3 → picsou_mouth_closed.png + picsou_mouth_open.png (générés une fois)
└──────┬──────┘  pydub → amplitude RMS par frame à 30 FPS (seuil adaptatif = moy × 0.6)
       │         Sortie : ctx.visuals + ctx.amplitudes_per_frame
       │
       ▼
┌─────────────┐
│  step 4     │  Groupe les timestamps en blocs de 4 mots
│  SUBTITLES  │  Pour chaque mot : SubtitleEntry(text=bloc, highlight_word=mot, start_ms, end_ms)
└──────┬──────┘  Sortie : ctx.subtitles  |  Fichier : work_dir/subtitles.json
       │
       ▼
┌─────────────┐
│  step 5     │  Pour chaque frame (30/s) :
│  COMPOSE    │    • Fond redimensionné en cover 1080×1920
└──────┬──────┘    • Personnage : bouche ouverte si amplitude > seuil, sinon fermée
       │           • Overlay sous-titres Pillow : bloc courant, mot en jaune
       │         FFmpeg encode frames/ + voice.mp3 → output/video_YYYYMMDD_HHMMSS.mp4
       ▼
  output/video.mp4  (H.264, AAC, 1080×1920, 30 FPS)
```

---

## Modèle de données

```python
PipelineContext
├── prompt          : str
├── work_dir        : Path          # tmp/gen_<id>/
├── script          : ScriptResult  # text, background_description, mood, word_count
├── voice           : VoiceResult   # audio_path, duration_seconds
├── timestamps      : TimestampsResult  # words: list[WordTimestamp]
├── visuals         : VisualsResult # background_path, character_frames
├── subtitles       : SubtitlesResult   # entries: list[SubtitleEntry]
├── output          : OutputResult  # video_path, resolution, duration_seconds
└── amplitudes_per_frame : list[float]  # RMS par frame (30/s)
```

---

## Services clés

### `llm.py`
- Appel GPT-4o avec `@backoff` (retry sur `RateLimitError` / `InvalidScriptError`)
- `@lru_cache` : même prompt → pas de second appel API
- Validation du word count (80–200 mots), sinon relance

### `tts.py`
- Appel `tts-1` avec `@backoff` + `@lru_cache`
- Facturation OpenAI au caractère → usage loggué via `len(text)`

### `whisper.py`
- Transcription `verbose_json` avec `timestamp_granularities=["word"]`
- Durée audio loggée (`transcript.duration`) pour estimation du coût

### `image_gen.py`
- `_fetch_background_url` : `@lru_cache` + `@backoff` — même description → pas de double appel DALL-E
- Fallback dégradé doré Pillow si DALL-E non disponible

### `audio_analysis.py`
- Découpe audio en chunks de 33 ms (30 FPS)
- RMS par chunk via pydub
- Seuil adaptatif = `mean(amplitudes) × 0.6`

### `subtitle_renderer.py`
- Rendu Pillow d'un bloc de 4 mots en overlay RGBA transparent
- Mot courant : jaune (#FFD700), taille 80 pt, contour noir 3 px
- Autres mots : blanc, taille 72 pt, contour noir 3 px
- Position : tiers inférieur (78 % du haut), centré horizontalement

---

## Fichiers intermédiaires (`work_dir/`)

| Fichier | Produit par | Contenu |
|---|---|---|
| `script.json` | step 1 | JSON complet retourné par GPT-4o |
| `voice.mp3` | step 2 | Audio TTS |
| `timestamps.json` | step 2 | `[{word, start, end}]` |
| `background.png` | step 3 | Fond DALL-E 3 redimensionné |
| `subtitles.json` | step 4 | `[{text, highlight_word, start_ms, end_ms}]` |
| `frames/frame_NNNN.png` | step 5 | Frames composites 1080×1920 |

Assets persistants (partagés entre toutes les générations) :

| Fichier | Produit par | Contenu |
|---|---|---|
| `assets/picsou_mouth_closed.png` | step 3 | Personnage bouche fermée (généré une fois) |
| `assets/picsou_mouth_open.png` | step 3 | Personnage bouche ouverte (généré une fois) |
