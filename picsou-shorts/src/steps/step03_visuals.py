"""
Etape 3 — Preparation des assets visuels.

Entree  : ctx.script.background_description, ctx.voice.audio_path
Sortie  : VisualsResult + ctx.amplitudes_per_frame

Sous-etapes :
  1. Images du personnage (bouche fermee / ouverte)
     - Generees par DALL-E une seule fois dans assets/
     - Reutilisees si les fichiers existent deja
  2. Fond (background)
     - DALL-E 3 base sur background_description de l'etape 1
  3. Analyse audio
     - Amplitude RMS par frame a 30 FPS
     - Seuil adaptatif = moyenne * 0.6
     - Stockee dans ctx.amplitudes_per_frame
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from src.models.pipeline import CharacterFrames, PipelineContext, VisualsResult
from src.services import audio_analysis, image_gen
from src.settings import get_openai_client

logger = logging.getLogger(__name__)

# Dossier assets partage entre toutes les generations
ASSETS_DIR = Path(__file__).parents[2] / "assets"

CHAR_CLOSED = ASSETS_DIR / "picsou_mouth_closed.png"
CHAR_OPEN = ASSETS_DIR / "picsou_mouth_open.png"


# ---------------------------------------------------------------------------
# Personnage — deux appels DALL-E 3 avec style commun ancre
# ---------------------------------------------------------------------------

_CHAR_BASE = (
    "ONE character and ONE character only. Do NOT duplicate the character. "
    "A single 2D cartoon elderly duck, full body, centered on a plain white "
    "background. Black top hat, red jacket and spats, holding a wooden cane. "
    "Facing DIRECTLY forward, front view, looking straight at the camera, "
    "NOT turned left or right. "
    "Flat cel-shading style, no text, no shadow. "
    "There must be exactly one duck in the image, never two or more."
)

_CHARACTER_PROMPTS = {
    "closed": (
        _CHAR_BASE
        + " Bill firmly CLOSED, calm neutral expression,"
        " as if pausing between sentences."
    ),
    "open": (
        _CHAR_BASE
        + " Bill WIDE OPEN, clearly showing the inside of the mouth,"
        " actively speaking a word. Open mouth must be very visible."
    ),
}


def _generate_character_pair() -> None:
    """Genere les deux images du personnage via DALL-E 3."""
    client = get_openai_client()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for which, path in (("closed", CHAR_CLOSED), ("open", CHAR_OPEN)):
        logger.info("DALL-E 3: generating character — mouth_%s", which)
        r = client.images.generate(
            model="dall-e-3",
            prompt=_CHARACTER_PROMPTS[which],
            size="1024x1024",
            quality="standard",
            n=1,
        )
        url = r.data[0].url
        assert url is not None
        path.write_bytes(httpx.get(url).content)
        logger.info("Saved: %s", path.name)


def _ensure_character_images() -> CharacterFrames:
    """
    Retourne les chemins des images du personnage.
    - Les deux existent  -> reutilisation directe.
    - Une seule ou aucune -> supprime et regenere la paire complete.
    """
    closed_ok = CHAR_CLOSED.exists()
    open_ok = CHAR_OPEN.exists()

    if closed_ok and open_ok:
        logger.info("Character images found — reusing existing pair")
    else:
        if closed_ok:
            CHAR_CLOSED.unlink()
            logger.info(
                "Deleted incomplete image: %s", CHAR_CLOSED.name
            )
        if open_ok:
            CHAR_OPEN.unlink()
            logger.info(
                "Deleted incomplete image: %s", CHAR_OPEN.name
            )
        _generate_character_pair()

    return CharacterFrames(mouth_closed=CHAR_CLOSED, mouth_open=CHAR_OPEN)


# ---------------------------------------------------------------------------
# Orchestration de l'etape
# ---------------------------------------------------------------------------


def run(ctx: PipelineContext, fps: int = 30) -> PipelineContext:
    """Execute l'etape 3 : assets visuels + analyse audio."""
    assert ctx.script is not None, "Step 1 must run before step 3"
    assert ctx.voice is not None, "Step 2 must run before step 3"

    logger.info("[3/5] Preparing visual assets...")

    # 1. Images du personnage
    logger.info("[3/5] Checking character images...")
    character_frames = _ensure_character_images()

    # 2. Fond via DALL-E 3
    logger.info("[3/5] Generating background with DALL-E 3...")
    background_path = ctx.work_dir / "background.png"
    image_gen.generate_background_dalle(
        ctx.script.background_description, background_path
    )

    ctx.visuals = VisualsResult(
        background_path=background_path,
        character_frames=character_frames,
    )

    # 3. Analyse audio — amplitude par frame
    logger.info("[3/5] Analysing audio amplitudes...")
    amplitudes = audio_analysis.compute_amplitudes_per_frame(
        ctx.voice.audio_path, fps=fps
    )
    ctx.amplitudes_per_frame = amplitudes

    threshold = audio_analysis.adaptive_threshold(amplitudes)
    open_frames = sum(
        audio_analysis.mouth_open_per_frame(amplitudes, threshold)
    )
    logger.info(
        "[3/5] Visuals OK — %d frames, %.0f%% mouth-open",
        len(amplitudes),
        100 * open_frames / len(amplitudes) if amplitudes else 0,
    )

    return ctx
