"""
Helpers de formatage du temps pour les sous-titres et les logs.
"""

from __future__ import annotations


def ms_to_ass_time(ms: int) -> str:
    """
    Convertit des millisecondes en format ASS : H:MM:SS.cc
    Exemple : 3750 -> 0:00:03.75
    """
    total_seconds, centis = divmod(ms, 1000)
    centis = centis // 10
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{seconds:02}.{centis:02}"


def ms_to_srt_time(ms: int) -> str:
    """
    Convertit des millisecondes en format SRT : HH:MM:SS,mmm
    Exemple : 3750 -> 00:00:03,750
    """
    total_seconds, millis = divmod(ms, 1000)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def seconds_to_ms(seconds: float) -> int:
    return int(seconds * 1000)


def format_duration(seconds: float) -> str:
    """Affichage lisible : '1m 32s' ou '28s'."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes:
        return f"{minutes}m {secs:02}s"
    return f"{secs}s"
