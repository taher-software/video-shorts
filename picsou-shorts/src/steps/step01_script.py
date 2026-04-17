"""
Etape 1 — Generation du script via GPT-4o.

Entree  : prompt utilisateur (str)
Sortie  : ScriptResult ajoute au PipelineContext
Fichier : work_dir/script.json
"""

from __future__ import annotations

import json
import logging

from src.services import llm
from src.types.pipeline import PipelineContext, ScriptResult

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    logger.info("[1/5] Generating script...")

    data = llm.generate_script(ctx.prompt)

    ctx.script = ScriptResult(
        text=data["script"],
        background_description=data.get("background_description", ""),
        mood=data.get("mood", "neutre"),
        word_count=data["word_count"],
    )

    script_path = ctx.work_dir / "script.json"
    script_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "[1/5] Script OK — %d words, mood=%s",
        ctx.script.word_count,
        ctx.script.mood,
    )
    return ctx
