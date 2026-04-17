"""
Wrapper FFmpeg pour l'encodage final de la video.
Utilise subprocess — plus lisible que ffmpeg-python
pour des commandes avec filter_complex.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def check_ffmpeg() -> None:
    """Verifie que ffmpeg est installe et accessible dans le PATH."""
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError(
            "ffmpeg introuvable dans le PATH. "
            "Linux : apt install ffmpeg | macOS : brew install ffmpeg"
        )


def assemble_video(
    frames_dir: Path,
    audio_path: Path,
    output_path: Path,
    fps: int = 30,
) -> Path:
    """
    Encode les frames pre-composees + audio en video MP4 finale.
    Les frames (fond + personnage + sous-titres) sont generees
    en amont par l'etape 5.
    """
    check_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    logger.info("FFmpeg: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")

    logger.info("FFmpeg: video saved to %s", output_path)
    return output_path


def get_audio_duration(audio_path: Path) -> float:
    """Retourne la duree de l'audio en secondes via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())
