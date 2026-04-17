"""
Etape 4 — Generation des sous-titres dynamiques.

Entree  : ctx.timestamps.words (WordTimestamp[])
Sortie  : SubtitlesResult ajoute au contexte

Logique :
  - Les mots sont regroupes en blocs de WORDS_PER_BLOCK mots.
  - Pour chaque mot d'un bloc, un SubtitleEntry est cree :
      text          = texte complet du bloc (3-5 mots)
      highlight_word = le mot actuellement prononce
      start_ms      = debut de ce mot
      end_ms        = debut du mot suivant (ou fin de l'audio)
  - Cela permet au rendu (etape 5) d'afficher le bloc entier
    en mettant en jaune le mot en cours de prononciation.
"""

from __future__ import annotations

import json
import logging

from src.models.pipeline import (
    PipelineContext,
    SubtitleEntry,
    SubtitlesResult,
    WordTimestamp,
)

logger = logging.getLogger(__name__)

WORDS_PER_BLOCK = 4  # groupes de 4 mots (ajustable entre 3 et 5)


def _group_into_entries(words: list[WordTimestamp]) -> list[SubtitleEntry]:
    """
    Transforme la liste de timestamps mot-a-mot en SubtitleEntry.

    Chaque entry represente l'interval pendant lequel un mot specifique
    est prononce, avec le bloc complet comme contexte.
    """
    entries: list[SubtitleEntry] = []

    for block_start in range(0, len(words), WORDS_PER_BLOCK):
        block = words[block_start : block_start + WORDS_PER_BLOCK]
        block_text = " ".join(w.word for w in block)

        for i, word in enumerate(block):
            # end_ms = debut du mot suivant dans le bloc,
            # ou debut du prochain bloc, ou fin de l'audio.
            global_next = block_start + i + 1
            if global_next < len(words):
                end_ms = int(words[global_next].start * 1000)
            else:
                end_ms = int(word.end * 1000)

            entries.append(
                SubtitleEntry(
                    text=block_text,
                    start_ms=int(word.start * 1000),
                    end_ms=end_ms,
                    highlight_word=word.word,
                )
            )

    return entries


def run(ctx: PipelineContext) -> PipelineContext:
    """Execute l'etape 4 : groupage des timestamps en blocs de sous-titres."""
    assert ctx.timestamps is not None, "Step 2 must run before step 4"

    logger.info("[4/5] Generating subtitles...")

    entries = _group_into_entries(ctx.timestamps.words)

    ctx.subtitles = SubtitlesResult(entries=entries)

    # Sauvegarde pour debug / inspection
    subtitles_path = ctx.work_dir / "subtitles.json"
    subtitles_path.write_text(
        json.dumps(
            [
                {
                    "text": e.text,
                    "highlight_word": e.highlight_word,
                    "start_ms": e.start_ms,
                    "end_ms": e.end_ms,
                }
                for e in entries
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    logger.info(
        "[4/5] Subtitles OK — %d entries, %d blocks",
        len(entries),
        -(-len(ctx.timestamps.words) // WORDS_PER_BLOCK),  # ceiling div
    )
    return ctx
