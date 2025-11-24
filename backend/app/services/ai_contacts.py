from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.models.contact import Contact
from app.services.llm_client import chat_json

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AIContactEnrichment:
    email: str
    full_name: Optional[str]
    role_title: Optional[str]
    is_decision_maker: Optional[bool]
    linkedin_url: Optional[str]


def _normalize_bool(value: object) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("true", "yes", "y", "1"):
            return True
        if lower in ("false", "no", "n", "0"):
            return False
    return None


def enrich_contacts_for_company(
    root_url: str,
    full_text: str,
    contacts: List[Contact],
) -> Dict[str, AIContactEnrichment]:
    """
    Utilise le LLM pour enrichir les contacts existants d'une société :
    - full_name
    - role_title
    - is_decision_maker (IT / digital)
    - linkedin_url

    Ne crée PAS de nouveaux emails, ne modifie PAS les emails existants.
    Retourne un mapping email -> AIContactEnrichment.
    """
    if not settings.OPENAI_ENABLE:
        return {}
    if not settings.OPENAI_MODEL:
        logger.warning("OPENAI_MODEL not configured; skipping contact enrichment")
        return {}
    if not contacts:
        return {}
    if not full_text:
        return {}

    emails = [c.email for c in contacts if c.email]
    unique_emails = sorted(set(e for e in emails if e))
    if not unique_emails:
        return {}

    snippet = full_text[: settings.LLM_MAX_CHARS]

    emails_block = "\n".join(f"- {email}" for email in unique_emails)

    system_prompt = (
        "You are an assistant that analyzes a company's public website to "
        "identify and enrich B2B contacts for a software / data / AI agency.\n"
        "You must only use information that is very likely to be correct from the website text."
    )

    user_prompt = f"""
    Company website root URL: {root_url}

    We have extracted the following email addresses from this website:
    {emails_block}

    Below is a text corpus built from multiple pages of the same website
    (home, about, team, jobs, contact, etc.):

    \"\"\"{snippet}\"\"\"

    For EACH email in the list, infer:

    - full_name: the person's full name (e.g. "Jane Doe") if you can clearly identify it,
                otherwise null.
    - role_title: their role or job title (e.g. "CTO", "Head of Data", "HR Manager") if identifiable,
                otherwise null.
    - is_decision_maker: true if this person is likely involved in buying decisions for
                        software / IT / data / digital consulting; false if clearly not;
                        null if unknown.
    - linkedin_url: a LinkedIn profile URL explicitly mentioned on the website for this person,
                    otherwise null. Do NOT invent URLs.

    Return a JSON object with EXACTLY this structure:

    {{
    "contacts": [
        {{
        "email": string,          // MUST be one of the input emails
        "full_name": string | null,
        "role_title": string | null,
        "is_decision_maker": boolean | null,
        "linkedin_url": string | null
        }},
        ...
    ]
    }}

    Rules:
    - Do NOT introduce any new emails that are not in the input list.
    - For generic addresses (like contact@company.com, support@, info@),
    full_name and role_title will usually be null.
    - If you are not reasonably confident, leave fields as null.
    """

    try:
        data = chat_json(
            model=settings.OPENAI_MODEL,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=min(settings.OPENAI_MAX_TOKENS, 800),
        )
    except Exception:
        logger.warning(
            "LLM contact enrichment failed for %s; falling back to raw emails",
            root_url,
            exc_info=True,
        )
        return {}

    items = data.get("contacts") or []
    enrichments: Dict[str, AIContactEnrichment] = {}

    for item in items:
        email = item.get("email")
        if not email or email not in unique_emails:
            continue

        full_name = item.get("full_name")
        role_title = item.get("role_title")
        linkedin_url = item.get("linkedin_url")
        is_decision_maker = _normalize_bool(item.get("is_decision_maker"))

        enrichments[email] = AIContactEnrichment(
            email=email,
            full_name=full_name or None,
            role_title=role_title or None,
            is_decision_maker=is_decision_maker,
            linkedin_url=linkedin_url or None,
        )

    logger.info(
        "LLM contact enrichment for %s -> %d contacts enriched",
        root_url,
        len(enrichments),
    )

    return enrichments
