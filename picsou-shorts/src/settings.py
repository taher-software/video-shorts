"""
Configuration et initialisation des clients partagés.
"""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    Retourne le client OpenAI partage.
    Instancie une seule fois grace a lru_cache.
    Lit OPENAI_API_KEY depuis l'environnement (ou .env).
    """
    from dotenv import load_dotenv
    load_dotenv()
    return OpenAI()
