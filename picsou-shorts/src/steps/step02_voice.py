"""
Etape 2 — Generation de la voix (TTS) + timestamps Whisper.

Entree  : ctx.script.text
Sortie  : VoiceResult + TimestampsResult ajoutes au contexte
Fichiers: work_dir/voice.mp3, work_dir/timestamps.json
"""

from __future__ import annotations

import json
import logging

from src.services import tts, whisper
from src.services.ffmpeg import get_audio_duration
from src.types.pipeline import (
    PipelineContext,
    TimestampsResult,
    VoiceResult,
    WordTimestamp,
)
from src.utils.time_utils import format_duration

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext, voice: str = "onyx") -> PipelineContext:
    assert ctx.script is not None, "Step 1 must run before step 2"

    logger.info("[2/5] Generating voice (TTS)...")

    audio_path = ctx.work_dir / "voice.mp3"
    tts.generate_voice(ctx.script.text, audio_path, voice=voice)

    duration = get_audio_duration(audio_path)
    ctx.voice = VoiceResult(audio_path=audio_path, duration_seconds=duration)

    # Timestamps via Whisper (avec fallback estimation)
    logger.info("[2/5] Transcribing with Whisper for timestamps...")
    try:
        raw_words = whisper.transcribe_with_timestamps(audio_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Whisper failed (%s), using estimation", exc)
        raw_words = whisper.estimate_timestamps(
            ctx.script.text, duration
        )

    ctx.timestamps = TimestampsResult(
        words=[
            WordTimestamp(word=w["word"], start=w["start"], end=w["end"])
            for w in raw_words
        ]
    )

    ts_path = ctx.work_dir / "timestamps.json"
    ts_path.write_text(
        json.dumps(raw_words, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "[2/5] Voice OK — %s, %d word timestamps",
        format_duration(duration),
        len(ctx.timestamps.words),
    )
    return ctx
