"""
Client Whisper — OpenAI /v1/audio/transcriptions avec
timestamp_granularities[]=word pour obtenir les timestamps par mot.

Donne des timestamps reels (pas estimes), ce qui ameliore
la synchronisation des sous-titres.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.settings import get_openai_client

logger = logging.getLogger(__name__)


def transcribe_with_timestamps(
    audio_path: Path,
) -> list[dict[str, Any]]:
    """
    Transcrit l'audio et retourne les timestamps par mot.

    Retourne : [{"word": "Alors", "start": 0.0, "end": 0.35}, ...]
    """
    client = get_openai_client()
    logger.info("Whisper: transcribing %s", audio_path)

    with audio_path.open("rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
            language="fr",
        )
        
    print("Whisper API response:", transcript.usage)
    
    words = transcript.words or []
    result = [
        {"word": w.word, "start": w.start, "end": w.end}
        for w in words
    ]
    logger.info("Whisper: got %d word timestamps", len(result))
    return result


def estimate_timestamps(
    text: str,
    duration_seconds: float,
) -> list[dict[str, Any]]:
    """
    Fallback : repartit uniformement les mots sur la duree audio.
    Utilise si Whisper echoue ou n'est pas disponible.
    """
    words = text.split()
    if not words:
        return []

    step = duration_seconds / len(words)
    return [
        {
            "word": word,
            "start": round(i * step, 3),
            "end": round((i + 1) * step, 3),
        }
        for i, word in enumerate(words)
    ]
