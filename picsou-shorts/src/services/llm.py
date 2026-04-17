"""
Client LLM — OpenAI GPT-4o.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

import backoff
import openai

from src.settings import get_openai_client

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class InvalidScriptError(Exception):
    """Levee quand le LLM retourne un JSON invalide ou un script hors limites."""


def _load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


@backoff.on_exception(
    backoff.expo,
    (InvalidScriptError, openai.RateLimitError, openai.APIConnectionError),
    max_tries=3,
    logger=logger,
)
def _call_llm(system: str, user: str) -> dict:
    """
    Appel unique au LLM avec validation.
    Leve InvalidScriptError si le JSON est invalide ou le script hors plage.
    backoff relance automatiquement en cas d'erreur.
    """
    response = get_openai_client().chat.completions.create(
        model="gpt-4o",
        temperature=0.8,
        max_tokens=800,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    raw = response.choices[0].message.content or ""
    
    print("LLM raw response:", response.usage) 

    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise InvalidScriptError(f"Invalid JSON: {exc}") from exc

    word_count = len(data.get("script", "").split())
    if not 80 <= word_count <= 200:
        raise InvalidScriptError(
            f"Word count {word_count} out of range [80, 200]"
        )

    data["word_count"] = word_count
    return data


@lru_cache(maxsize=128)
def generate_script(prompt: str) -> dict:
    """
    Genere le script Picsou a partir d'un prompt utilisateur via GPT-4o.
    Retourne le JSON parse avec word_count injecte.
    """
    system = _load_prompt("script_system.txt")
    user = _load_prompt("script_user.txt").format(prompt=prompt)
    return _call_llm(system, user)
