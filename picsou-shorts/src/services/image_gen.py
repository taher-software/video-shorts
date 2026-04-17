"""
Generation d'images — DALL-E 3 (OpenAI) ou fond degrade Pillow.

Le fond degrade est le comportement par defaut (sans appel API).
DALL-E 3 est active si USE_DALLE_BACKGROUND=true dans .env.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
from PIL import Image

from src.settings import get_openai_client

logger = logging.getLogger(__name__)


def generate_background_dalle(
    description: str,
    output_path: Path,
) -> Path:
    """
    Genere un fond via DALL-E 3 a partir de la description du LLM.
    Cout : ~$0.040 par image.
    """
    client = get_openai_client()
    prompt = (
        "Illustration style cartoon, fond pour video courte verticale 9:16."
        f" Ambiance : {description}."
        " Pas de personnages, pas de texte. Style simple et lisible."
    )
    logger.info("DALL-E 3: generating background — %s", description)

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    assert image_url is not None, "DALL-E returned no URL"

    image_data = httpx.get(image_url).content
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_data)
    logger.info("DALL-E 3: background saved to %s", output_path)
    return output_path


def generate_background_gradient(
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    """
    Genere un fond degrade dore (or -> brun dore) sans appel API.
    Fallback par defaut.
    """
    logger.info("Pillow: generating golden gradient background")
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    assert pixels is not None

    top = (255, 215, 0)       # or vif
    bottom = (139, 69, 0)     # brun dore fonce

    for y in range(height):
        ratio = y / (height - 1)
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        for x in range(width):
            pixels[x, y] = (r, g, b)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path))
    logger.info("Pillow: background saved to %s", output_path)
    return output_path
