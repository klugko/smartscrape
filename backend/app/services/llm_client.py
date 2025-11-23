import json
import logging
from typing import Any, Dict

from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """
    Retourne un client OpenAI singleton.
    Utilise la clé définie dans la configuration (OPENAI_API_KEY).
    """
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set; LLM enrichment will be disabled")
            raise RuntimeError("OPENAI_API_KEY is not configured")

        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def chat_json(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> Dict[str, Any]:
    """
    Appelle l'API Chat Completions en mode JSON strict.
    Soulève une exception si l'appel échoue ou si le JSON est invalide.
    """
    client = get_openai_client()

    try:
        completion = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.exception("OpenAI chat.completions.create failed: %s", exc)
        raise

    content = completion.choices[0].message.content
    if not content:
        raise ValueError("Empty content from OpenAI")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.exception("Failed to parse OpenAI JSON content: %s", exc)
        raise
