from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from app.core.config import get_settings
from app.services.llm_client import chat_json
from app.services.parsing import ParsedSignals

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AICompanyEnrichment:
    name: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    tags: Optional[List[str]] = None
    prospect_type: Optional[str] = None
    score: Optional[float] = None
    reasons: Optional[str] = None


def _normalize_tags(raw_tags: object) -> List[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, list):
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]
        return tags
    if isinstance(raw_tags, str):
        return [t.strip() for t in raw_tags.split(",") if t.strip()]
    return []


def enrich_company_with_llm(
    root_url: str,
    text: str,
    signals: ParsedSignals,
) -> Optional[AICompanyEnrichment]:
    """
    Utilise un LLM (ChatGPT API) pour enrichir les infos société et
    affiner la classification prospect.
    Retourne None si l'IA est désactivée ou en cas d'erreur.
    """
    if not settings.OPENAI_ENABLE:
        return None
    if not settings.OPENAI_MODEL:
        logger.warning("OPENAI_MODEL not configured; skipping LLM enrichment")
        return None

    if not text:
        return None

    snippet = text[: settings.LLM_MAX_CHARS]

    system_prompt = (
        "You are a senior B2B lead analyst working for a software development "
        "and AI agency. You receive noisy text scraped from a company's public "
        "website (marketing pages, careers, blog, etc.). "
        "Your job is to summarize the company and evaluate how interesting it is "
        "as a potential client.\n\n"
        "You MUST output a single valid JSON object and nothing else."
    )

    user_prompt = f"""
    Website root URL: {root_url}

    The following text was extracted from multiple pages of the same website.
    It is noisy (cookies banners, legal mentions, etc.) but you must infer the
    most likely business information:

    \"\"\"{snippet}\"\"\"

    Pre-detected heuristic signals (booleans):

    - has_it_jobs: {signals.has_it_jobs}
    - hiring_language: {signals.hiring_language}
    - offers_it_services: {signals.offers_it_services}

    Based on all this, infer:

    1) A concise company profile.
    2) A prospect classification for a software / AI development agency.

    Return a JSON object with EXACTLY this structure:

    {{
    "company": {{
        "name": string | null,
        "description": string | null,
        "country": string | null,
        "city": string | null,
        "industry": string | null,
        "size": string | null,         // staff size like "1-10", "11-50", "51-200", "200+"
        "tags": [string, ...]          // 3-8 very short tags, may be empty list
    }},
    "prospect": {{
        "type": "project" | "staffing" | "both" | "unknown",
        "score": number,               // 0-100 (0 = not interesting, 100 = ideal target)
        "reasons": string              // 1-3 sentences explaining the score
    }}
    }}

    Rules:
    - Be realistic and conservative with the score.
    - If information is not clearly present, return null or "unknown" instead of guessing wildly.
    - Do NOT include any fields outside this JSON schema.
    """

    try:
        data = chat_json(
            model=settings.OPENAI_MODEL,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )
    except Exception:
        logger.warning("LLM enrichment failed; falling back to heuristics", exc_info=True)
        return None

    company_data = data.get("company") or {}
    prospect_data = data.get("prospect") or {}

    tags = _normalize_tags(company_data.get("tags"))

    # Prospect type
    prospect_type = prospect_data.get("type")
    if prospect_type not in ("project", "staffing", "both", "unknown"):
        prospect_type = None

    # Score
    score_val = prospect_data.get("score")
    score: Optional[float]
    try:
        score = float(score_val) if score_val is not None else None
    except (TypeError, ValueError):
        score = None

    enrichment = AICompanyEnrichment(
        name=company_data.get("name"),
        description=company_data.get("description"),
        country=company_data.get("country"),
        city=company_data.get("city"),
        industry=company_data.get("industry"),
        size=company_data.get("size"),
        tags=tags,
        prospect_type=prospect_type,
        score=score,
        reasons=prospect_data.get("reasons"),
    )

    logger.info(
        "LLM enrichment for %s -> type=%s score=%s",
        root_url,
        enrichment.prospect_type,
        enrichment.score,
    )

    return enrichment
