"""
Rendu des sous-titres avec Pillow.

Style viral Shorts :
  - Bloc de 3-5 mots affiches en bas de l'image
  - Mot courant en JAUNE (legerement agrandi)
  - Autres mots en BLANC
  - Contour noir sur chaque mot pour lisibilite sur tout fond
  - Police grande, centree horizontalement dans le tiers inferieur
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Polices systeme (priorite decroissante)
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]

# Taille de base et taille du mot surligne
FONT_SIZE_NORMAL = 72
FONT_SIZE_HIGHLIGHT = 80

# Position verticale : tiers inferieur (78 % du haut)
SUBTITLE_Y_RATIO = 0.78

# Largeur max du bloc (85 % de la largeur de la video)
MAX_WIDTH_RATIO = 0.85

# Epaisseur du contour noir
OUTLINE_RADIUS = 3

# Couleurs
COLOR_NORMAL = (255, 255, 255, 255)      # blanc
COLOR_HIGHLIGHT = (255, 215, 0, 255)     # or/jaune
COLOR_OUTLINE = (0, 0, 0, 255)           # noir


@lru_cache(maxsize=8)
def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Charge la meilleure police disponible a la taille demandee."""
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    logger.warning("No TTF font found — falling back to Pillow default")
    return ImageFont.load_default()


def _draw_word_with_outline(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    word: str,
    font: ImageFont.FreeTypeFont,
    color: tuple[int, int, int, int],
    outline_radius: int = OUTLINE_RADIUS,
) -> None:
    """Dessine un mot avec un contour noir pour le rendre lisible sur tout fond."""
    for dx in range(-outline_radius, outline_radius + 1):
        for dy in range(-outline_radius, outline_radius + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), word, font=font, fill=COLOR_OUTLINE)
    draw.text((x, y), word, font=font, fill=color)


def render_subtitle_block(
    block_text: str,
    highlight_word: Optional[str],
    frame_width: int = 1080,
    frame_height: int = 1920,
) -> Image.Image:
    """
    Retourne une image RGBA (meme taille que la frame video) avec le bloc
    de sous-titres dessine, transparent partout sauf le texte.

    Le mot `highlight_word` est affiche en jaune et legerement agrandi.
    Les autres mots sont en blanc.
    Tous les mots ont un contour noir.
    """
    overlay = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_normal = _load_font(FONT_SIZE_NORMAL)
    font_highlight = _load_font(FONT_SIZE_HIGHLIGHT)

    words = block_text.split()
    max_line_px = int(frame_width * MAX_WIDTH_RATIO)

    # Trouver l'index du mot surligne (premiere occurrence)
    highlight_idx: Optional[int] = None
    if highlight_word:
        clean = highlight_word.strip()
        for i, w in enumerate(words):
            if w.strip() == clean:
                highlight_idx = i
                break

    # Disposition des mots en lignes
    Line = list[tuple[str, bool]]  # (word, is_highlighted)
    lines: list[Line] = []
    current_line: Line = []
    current_px = 0

    for i, word in enumerate(words):
        is_hl = i == highlight_idx
        font = font_highlight if is_hl else font_normal
        word_px = draw.textlength(word + " ", font=font)

        if current_px + word_px > max_line_px and current_line:
            lines.append(current_line)
            current_line = [(word, is_hl)]
            current_px = word_px
        else:
            current_line.append((word, is_hl))
            current_px += word_px

    if current_line:
        lines.append(current_line)

    # Hauteur d'une ligne = taille de la plus grande police + interligne
    line_height = FONT_SIZE_HIGHLIGHT + 16
    total_h = len(lines) * line_height
    base_y = int(frame_height * SUBTITLE_Y_RATIO) - total_h // 2

    for line_idx, line in enumerate(lines):
        # Largeur totale de la ligne pour centrage
        line_px = sum(
            draw.textlength(w + " ", font=(font_highlight if hl else font_normal))
            for w, hl in line
        )
        x = (frame_width - line_px) / 2
        y = base_y + line_idx * line_height

        for word, is_hl in line:
            font = font_highlight if is_hl else font_normal
            color = COLOR_HIGHLIGHT if is_hl else COLOR_NORMAL
            _draw_word_with_outline(draw, x, y, word, font, color)
            x += draw.textlength(word + " ", font=font)

    return overlay


def get_subtitle_entry_at(
    entries: list,
    time_ms: int,
) -> Optional[object]:
    """
    Retourne le SubtitleEntry actif au temps `time_ms`,
    ou None si aucun sous-titre n'est actif.
    """
    for entry in entries:
        if entry.start_ms <= time_ms < entry.end_ms:
            return entry
    return None
