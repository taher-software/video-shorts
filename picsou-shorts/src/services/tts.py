"""
Client TTS — OpenAI TTS-1.

Voix choisie : 'onyx' (grave, autoritaire — evoque bien Picsou).
'fable' est une alternative plus expressive si souhaite.

Note : OpenAI TTS ne fournit pas de timestamps mot-a-mot.
On utilise Whisper (whisper.py) dans l'etape suivante pour les obtenir.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import backoff
import openai

from src.settings import get_openai_client

logger = logging.getLogger(__name__)


@backoff.on_exception(
    backoff.expo,
    (openai.RateLimitError, openai.APIConnectionError),
    max_tries=3,
    logger=logger,
)
def _call_tts(text: str, voice: str, model: str) -> bytes:
    """Appel API TTS avec retry automatique. Retourne les bytes audio."""
    response = get_openai_client().audio.speech.create(
        model=model,
        voice=voice,  # type: ignore[arg-type]
        input=text,
        response_format="mp3",
    )
    print("TTS API response:", response.usage)  
    return response.read()


@lru_cache(maxsize=128)
def generate_voice(
    text: str,
    output_path: Path,
    voice: str = "onyx",
    model: str = "tts-1",
) -> Path:
    """
    Genere l'audio TTS et l'ecrit dans output_path (MP3).
    Le resultat est mis en cache : un meme (text, path, voice, model)
    ne declenchera pas de second appel API.
    """
    logger.info("TTS: generating audio with voice=%s model=%s", voice, model)

    audio_bytes = _call_tts(text, voice, model)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio_bytes)

    logger.info("TTS: audio saved to %s", output_path)
    return output_path
