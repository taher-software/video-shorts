"""
Etape 5 — Assemblage final de la video.

Entree  : ctx.visuals, ctx.voice, ctx.subtitles, ctx.amplitudes_per_frame
Sortie  : OutputResult (chemin du MP4 final)

Deux phases :
  A. Pillow — generation des frames composites PNG
       Pour chaque frame (30/s) :
         1. Fond (background) redimensionne en 1080x1920
         2. Personnage : bouche fermee ou ouverte selon l'amplitude audio
         3. Overlay sous-titres : bloc actif mis en evidence mot par mot
  B. FFmpeg — encodage frames + audio -> MP4 H.264/AAC 1080x1920
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from PIL import Image

from src.models.pipeline import OutputResult, PipelineContext
from src.services import audio_analysis, ffmpeg
from src.services.subtitle_renderer import (
    get_subtitle_entry_at,
    render_subtitle_block,
)

logger = logging.getLogger(__name__)

# --- Constantes de composition ---
FRAME_W, FRAME_H = 1080, 1920
FPS = 30
CHARACTER_HEIGHT = 900      # hauteur cible du personnage en px
CHARACTER_Y = 280           # position verticale du haut du personnage

OUTPUT_DIR = Path("output")


# ---------------------------------------------------------------------------
# Chargement et preparation des assets
# ---------------------------------------------------------------------------

def _fit_background(bg_path: Path) -> Image.Image:
    """
    Redimensionne le fond pour couvrir exactement 1080x1920 (cover + crop centre).
    """
    img = Image.open(bg_path).convert("RGB")
    w, h = img.size
    scale = max(FRAME_W / w, FRAME_H / h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - FRAME_W) // 2
    top = (new_h - FRAME_H) // 2
    return img.crop((left, top, left + FRAME_W, top + FRAME_H))


def _scale_character(char_path: Path) -> Image.Image:
    """Redimensionne le personnage a CHARACTER_HEIGHT en conservant le ratio."""
    img = Image.open(char_path).convert("RGBA")
    w, h = img.size
    scale = CHARACTER_HEIGHT / h
    new_w = int(w * scale)
    return img.resize((new_w, CHARACTER_HEIGHT), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Composition d'une frame
# ---------------------------------------------------------------------------

def _composite_frame(
    background: Image.Image,
    char_img: Image.Image,
    char_x: int,
    subtitle_overlay: Image.Image,
) -> Image.Image:
    """
    Assemble une frame complete :
      1. Copie du fond (RGB)
      2. Colle le personnage avec transparence alpha
      3. Applique l'overlay sous-titres (RGBA -> alpha composite)
    """
    frame = background.copy().convert("RGBA")

    # Personnage centre horizontalement
    frame.paste(char_img, (char_x, CHARACTER_Y), char_img)

    # Sous-titres (overlay transparent)
    frame = Image.alpha_composite(frame, subtitle_overlay)

    return frame.convert("RGB")


# ---------------------------------------------------------------------------
# Generation des frames
# ---------------------------------------------------------------------------

def _generate_frames(
    ctx: PipelineContext,
    frames_dir: Path,
    background: Image.Image,
    char_closed: Image.Image,
    char_open: Image.Image,
    mouth_open: list[bool],
) -> int:
    """
    Genere toutes les frames PNG dans frames_dir.
    Retourne le nombre total de frames generees.
    """
    assert ctx.subtitles is not None

    frames_dir.mkdir(parents=True, exist_ok=True)
    entries = ctx.subtitles.entries

    char_x = (FRAME_W - char_closed.width) // 2  # centrage horizontal

    # Cache des overlays sous-titres pour eviter de re-rendre le meme bloc
    _subtitle_cache: dict[tuple[str, str | None], Image.Image] = {}

    n_frames = len(mouth_open)

    for i, is_open in enumerate(mouth_open):
        time_ms = int(i * 1000 / FPS)

        # Choix du personnage selon l'amplitude
        char_img = char_open if is_open else char_closed

        # Sous-titre actif
        entry = get_subtitle_entry_at(entries, time_ms)
        if entry is not None:
            cache_key = (entry.text, entry.highlight_word)
            if cache_key not in _subtitle_cache:
                _subtitle_cache[cache_key] = render_subtitle_block(
                    entry.text,
                    entry.highlight_word,
                    frame_width=FRAME_W,
                    frame_height=FRAME_H,
                )
            subtitle_overlay = _subtitle_cache[cache_key]
        else:
            # Frame sans sous-titre (debut/fin de l'audio)
            subtitle_overlay = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))

        frame = _composite_frame(background, char_img, char_x, subtitle_overlay)
        frame.save(str(frames_dir / f"frame_{i + 1:04d}.png"))

        if (i + 1) % FPS == 0:
            logger.info(
                "[5/5] Frames: %d/%d (%.0f s)",
                i + 1,
                n_frames,
                (i + 1) / FPS,
            )

    return n_frames


# ---------------------------------------------------------------------------
# Orchestration de l'etape
# ---------------------------------------------------------------------------

def run(ctx: PipelineContext) -> PipelineContext:
    """Execute l'etape 5 : rendu des frames Pillow + encodage FFmpeg."""
    assert ctx.visuals is not None, "Step 3 must run before step 5"
    assert ctx.subtitles is not None, "Step 4 must run before step 5"
    assert ctx.voice is not None, "Step 2 must run before step 5"
    assert ctx.amplitudes_per_frame, "Step 3 must compute amplitudes before step 5"

    logger.info("[5/5] Composing video...")

    # --- Calcul du seuil adaptatif ---
    threshold = audio_analysis.adaptive_threshold(ctx.amplitudes_per_frame)
    mouth_open = audio_analysis.mouth_open_per_frame(
        ctx.amplitudes_per_frame, threshold
    )

    # --- Chargement des assets ---
    logger.info("[5/5] Loading assets...")
    background = _fit_background(ctx.visuals.background_path)
    char_closed = _scale_character(ctx.visuals.character_frames.mouth_closed)
    char_open_img = _scale_character(ctx.visuals.character_frames.mouth_open)

    # --- Generation des frames ---
    frames_dir = ctx.work_dir / "frames"
    logger.info("[5/5] Rendering %d frames...", len(mouth_open))

    n_frames = _generate_frames(
        ctx,
        frames_dir,
        background,
        char_closed,
        char_open_img,
        mouth_open,
    )

    # --- Encodage FFmpeg ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"video_{timestamp}.mp4"

    logger.info("[5/5] Encoding with FFmpeg...")
    ffmpeg.assemble_video(
        frames_dir=frames_dir,
        audio_path=ctx.voice.audio_path,
        output_path=output_path,
        fps=FPS,
    )

    ctx.output = OutputResult(
        video_path=output_path,
        resolution=f"{FRAME_W}x{FRAME_H}",
        duration_seconds=ctx.voice.duration_seconds,
    )

    logger.info(
        "[5/5] Done — %s (%dx%d, %.1fs, %d frames)",
        output_path,
        FRAME_W,
        FRAME_H,
        ctx.voice.duration_seconds,
        n_frames,
    )
    return ctx
