"""
Analyse audio — amplitude RMS par frame pour l'animation du personnage.

Approche :
1. Charger le fichier MP3 via pydub
2. Decouper en frames de 1/fps secondes
3. Calculer l'amplitude RMS de chaque frame
4. Le seuil = moyenne * 0.6 (adaptatif, recommande par le sujet)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def get_amplitude_per_frame(
    audio_path: Path,
    fps: int = 30,
) -> list[float]:
    """
    Retourne l'amplitude RMS pour chaque frame video.
    Une valeur haute = voix active = bouche ouverte.
    """
    audio = AudioSegment.from_file(str(audio_path))
    audio = audio.set_channels(1)  # mono

    frame_duration_ms = int(1000 / fps)
    total_ms = len(audio)
    amplitudes: list[float] = []

    for start_ms in range(0, total_ms, frame_duration_ms):
        chunk = audio[start_ms: start_ms + frame_duration_ms]
        samples = np.array(chunk.get_array_of_samples(), dtype=np.float32)
        rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0
        amplitudes.append(rms)

    logger.debug("Audio: %d frames at %d fps", len(amplitudes), fps)
    return amplitudes


def compute_adaptive_threshold(amplitudes: list[float]) -> float:
    """
    Seuil adaptatif = moyenne des amplitudes * 0.6.
    S'adapte aux voix plus ou moins fortes.
    """
    if not amplitudes:
        return 0.0
    mean = sum(amplitudes) / len(amplitudes)
    return mean * 0.6


def is_mouth_open(amplitude: float, threshold: float) -> bool:
    return amplitude > threshold
