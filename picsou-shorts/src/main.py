"""
Point d'entree CLI — picsou-shorts.

Usage :
    python -m src.main --prompt "Explique pourquoi il ne faut jamais prêter d'argent"
    python -m src.main --prompt "..." --voice fable
"""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from src import pipeline

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def generate(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Sujet du monologue"),
) -> None:
    """Genere une video Shorts Picsou a partir d'un prompt."""
    console.rule("[bold gold1]Picsou Shorts Generator[/]")

    ctx = pipeline.run(
        prompt=prompt,
    )

    # console.print()
    # console.rule("[bold green]Pipeline terminé[/]")

    # if ctx.script:
    #     console.print(f"[bold]Script[/]  {ctx.script.word_count} mots · mood={ctx.script.mood}")
    # if ctx.voice:
    #     console.print(f"[bold]Voice[/]   {ctx.voice.audio_path}")
    # if ctx.timestamps:
    #     console.print(f"[bold]Timestamps[/]  {len(ctx.timestamps.words)} mots alignes")


if __name__ == "__main__":
    app()
