"""
Orchestrateur du pipeline de generation de video Shorts.
Chaque etape recoit le contexte, l'enrichit, et le retourne.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from src.models.pipeline import PipelineContext
from src.steps import (
    step01_script,
    step02_voice,
    step03_visuals,
    step04_subtitles,
    step05_compose,
)

logger = logging.getLogger(__name__)

DEFAULT_WORK_BASE = Path("tmp")


def run(
    prompt: str,
    voice: str = "onyx",
    work_base: Path = DEFAULT_WORK_BASE,
) -> PipelineContext:
    """
    Lance le pipeline complet (5 etapes).

    Cree un dossier de travail unique par generation sous work_base/,
    puis execute chaque etape sequentiellement en passant le contexte.
    """
    run_id = uuid.uuid4().hex[:8]
    work_dir = work_base / f"gen_{run_id}"
    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Pipeline started — run_id=%s work_dir=%s", run_id, work_dir)

    ctx = PipelineContext(prompt=prompt, work_dir=work_dir)

    ctx = step01_script.run(ctx)
    ctx = step02_voice.run(ctx, voice=voice)
    ctx = step03_visuals.run(ctx)
    ctx = step04_subtitles.run(ctx)
    ctx = step05_compose.run(ctx)

    logger.info("Pipeline done — run_id=%s", run_id)
    return ctx
