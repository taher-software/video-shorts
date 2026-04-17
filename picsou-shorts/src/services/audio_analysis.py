"""
Analyse audio — amplitude RMS par frame pour l'animation de parole.

Approche niveau 2 : seuil adaptatif
  - Decoupage de l'audio en frames (30 FPS -> 33 ms/frame)
  - RMS de chaque frame via pydub
  - Seuil = moyenne * facteur (0.6 par defaut)
  - Au-dessus du seuil -> bouche ouverte
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from pydub import AudioSegment

logger = logging.getLogger(__name__)

FPS = 30
ADAPTIVE_FACTOR = 0.6


def compute_amplitudes_per_frame(
    audio_path: Path,
    fps: int = FPS,
) -> list[float]:
    """
    Charge l'audio et retourne l'amplitude RMS de chaque frame.

    Retourne une liste de floats (une valeur par frame a fps images/s).
    """
    audio = AudioSegment.from_file(str(audio_path))
    frame_duration_ms = int(1000 / fps)

    amplitudes: list[float] = []
    for start_ms in range(0, len(audio), frame_duration_ms):
        chunk = audio[start_ms : start_ms + frame_duration_ms]
        amplitudes.append(float(chunk.rms))

    logger.info(
        "Audio analysis: %d frames at %d FPS (%.1f s)",
        len(amplitudes),
        fps,
        len(audio) / 1000,
    )
    return amplitudes


def adaptive_threshold(amplitudes: list[float], factor: float = ADAPTIVE_FACTOR) -> float:
    """
    Seuil adaptatif = moyenne des amplitudes * factor.

    S'adapte aux voix plus ou moins fortes sans valeur fixe.
    """
    if not amplitudes:
        return 0.0
    mean = float(np.mean(amplitudes))
    threshold = mean * factor
    logger.info(
        "Adaptive threshold: mean=%.1f factor=%.2f threshold=%.1f",
        mean,
        factor,
        threshold,
    )
    return threshold


def mouth_open_per_frame(amplitudes: list[float], threshold: float) -> list[bool]:
    """Retourne True pour chaque frame ou la bouche doit etre ouverte."""
    return [amp > threshold for amp in amplitudes]
