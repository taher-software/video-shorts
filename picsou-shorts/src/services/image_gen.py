"""
Generation d'images — DALL-E 3 (OpenAI) ou fond degrade Pillow.

Le fond degrade est le comportement par defaut (sans appel API).
DALL-E 3 est active si USE_DALLE_BACKGROUND=true dans .env.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import backoff
import httpx
import openai
from PIL import Image

from src.settings import get_openai_client

logger = logging.getLogger(__name__)


@lru_cache(maxsize=64)
@backoff.on_exception(
    backoff.expo,
    (openai.RateLimitError, openai.APIConnectionError),
    max_tries=3,
    logger=logger,
)
def _fetch_background_url(description: str) -> str:
    """
    Appelle DALL-E 3 et retourne l'URL de l'image generee.

    Mis en cache par description : une meme ambiance ne declenche
    pas de second appel API. Retry automatique sur erreurs reseau/rate-limit.
    """
    prompt = (
        "Illustration style cartoon, fond pour video courte verticale 9:16."
        f" Ambiance : {description}."
        " Pas de personnages, pas de texte. Style simple et lisible."
    )
    logger.info("DALL-E 3: generating background — %s", description)

    response = get_openai_client().images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    assert image_url is not None, "DALL-E returned no URL"
    return image_url


def generate_background_dalle(
    description: str,
    output_path: Path,
) -> Path:
    """
    Genere un fond via DALL-E 3 a partir de la description du LLM.
    Cout : ~$0.040 par image.
    """
    image_url = _fetch_background_url(description)

    image_data = httpx.get(image_url).content
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_data)
    logger.info("DALL-E 3: background saved to %s", output_path)
    return output_path



