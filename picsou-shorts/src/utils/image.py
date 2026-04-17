"""
Manipulation d'images via Pillow — composition des frames video.

Chaque frame composite = fond + personnage centre + sous-titre.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
_FONTS_DIR = _ASSETS_DIR / "fonts"


def load_image(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    img = Image.open(str(path)).convert("RGBA")
    if size:
        img = img.resize(size, Image.LANCZOS)
    return img


def compose_frame(
    background: Image.Image,
    character: Image.Image,
    subtitle_text: str,
    highlight_word: str | None = None,
    canvas_size: tuple[int, int] = (1080, 1920),
) -> Image.Image:
    """
    Compose une frame complete :
      - fond plein ecran
      - personnage centre horizontalement, positionne au tiers inferieur
      - sous-titre en bas avec mot en surbrillance jaune
    """
    frame = background.copy().convert("RGBA")

    # Personnage : centre horizontal, base a 75% de la hauteur
    char_w, char_h = character.size
    char_x = (canvas_size[0] - char_w) // 2
    char_y = int(canvas_size[1] * 0.40)
    frame.paste(character, (char_x, char_y), character)

    # Sous-titres
    if subtitle_text:
        frame = _draw_subtitle(
            frame, subtitle_text, highlight_word, canvas_size
        )

    return frame.convert("RGB")


def _draw_subtitle(
    frame: Image.Image,
    text: str,
    highlight_word: str | None,
    canvas_size: tuple[int, int],
) -> Image.Image:
    """
    Dessine le sous-titre en bas de la frame.
    Le mot en cours est affiche en jaune, les autres en blanc.
    Contour noir pour lisibilite sur tout fond.
    """
    draw = ImageDraw.Draw(frame)

    font_path = _FONTS_DIR / "Montserrat-Bold.ttf"
    font_size = 72
    try:
        font = ImageFont.truetype(str(font_path), font_size)
    except OSError:
        font = ImageFont.load_default()
        logger.warning("Font not found, using default")

    words = text.split()
    x = canvas_size[0] // 2
    y = int(canvas_size[1] * 0.82)

    # Mesure la largeur totale pour centrer
    total_width = sum(
        draw.textlength(w + " ", font=font) for w in words
    )
    cursor_x = x - int(total_width / 2)

    for word in words:
        color = (255, 215, 0) if word == highlight_word else (255, 255, 255)
        word_w = int(draw.textlength(word + " ", font=font))

        # Contour noir (4 directions)
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            draw.text(
                (cursor_x + dx, y + dy),
                word,
                font=font,
                fill=(0, 0, 0),
            )
        draw.text((cursor_x, y), word, font=font, fill=color)
        cursor_x += word_w

    return frame


def save_frame(frame: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.save(str(output_path))
