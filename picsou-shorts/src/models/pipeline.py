"""
Types Pydantic pour le pipeline de generation de video Shorts.
Chaque etape recoit et enrichit un PipelineContext.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ScriptResult:
    text: str
    background_description: str
    mood: str
    word_count: int


@dataclass
class VoiceResult:
    audio_path: Path
    duration_seconds: float


@dataclass
class WordTimestamp:
    word: str
    start: float   # secondes
    end: float     # secondes


@dataclass
class TimestampsResult:
    words: list[WordTimestamp]


@dataclass
class CharacterFrames:
    mouth_closed: Path
    mouth_open: Path


@dataclass
class VisualsResult:
    background_path: Path
    character_frames: CharacterFrames


@dataclass
class SubtitleEntry:
    text: str
    start_ms: int
    end_ms: int
    highlight_word: Optional[str] = None


@dataclass
class SubtitlesResult:
    entries: list[SubtitleEntry]
    ass_file_path: Optional[Path] = None


@dataclass
class OutputResult:
    video_path: Path
    resolution: str          # ex: "1080x1920"
    duration_seconds: float


@dataclass
class PipelineContext:
    """
    Contexte partage entre toutes les etapes du pipeline.
    Chaque etape lit les champs remplis par les etapes precedentes
    et ajoute les siens.
    """

    prompt: str
    work_dir: Path

    # Rempli par etape 1
    script: Optional[ScriptResult] = None

    # Rempli par etape 2
    voice: Optional[VoiceResult] = None
    timestamps: Optional[TimestampsResult] = None

    # Rempli par etape 3
    visuals: Optional[VisualsResult] = None

    # Rempli par etape 4
    subtitles: Optional[SubtitlesResult] = None

    # Rempli par etape 5
    output: Optional[OutputResult] = None

    # Amplitude par frame (rempli pendant l'etape 3/5)
    amplitudes_per_frame: list[float] = field(default_factory=list)
