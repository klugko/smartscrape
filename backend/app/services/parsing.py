import re
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup

CONTACT_PAGE_KEYWORDS = [
    "contact",
    "contacts",
    "contactez",
    "nous contacter",
]

ABOUT_PAGE_KEYWORDS = [
    "about",
    "à propos",
    "qui sommes-nous",
    "notre histoire",
]

TEAM_PAGE_KEYWORDS = [
    "team",
    "équipe",
    "leadership",
    "management",
]

JOBS_PAGE_KEYWORDS = [
    "jobs",
    "careers",
    "carrières",
    "recrute",
    "offres",
    "emplois",
]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"\+?\d[\d\-\s\(\)]{6,}")


@dataclass
class ParsedCompanyInfo:
    name: Optional[str]
    description: Optional[str]
    country: Optional[str]
    city: Optional[str]
    industry: Optional[str]
    size: Optional[str]


@dataclass
class ParsedContactInfo:
    full_name: Optional[str]
    role_title: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]


@dataclass
class ParsedSignals:
    has_it_jobs: bool
    hiring_language: bool
    offers_it_services: bool


def is_page_type(url: str, keywords: list[str]) -> bool:
    lowered = url.lower()
    return any(k in lowered for k in keywords)


def extract_emails(text: str) -> List[str]:
    """
    Retourne une liste d'emails uniques trouvés dans le texte.
    """
    return list(set(EMAIL_REGEX.findall(text)))


def extract_phones(text: str) -> List[str]:
    """
    Extrait des numéros de téléphone, les normalise (en gardant seulement chiffres et '+'),
    déduplique et filtre les numéros trop courts.
    """
    phones = PHONE_REGEX.findall(text)
    cleaned: List[str] = []
    seen = set()
    for p in phones:
        normalized = re.sub(r"[^\d+]", "", p)
        if len(normalized) < 7:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)
    return cleaned


def extract_company_info_from_pages(pages_html: list[str]) -> ParsedCompanyInfo:
    """
    Heuristique MVP : on prend le premier <title> non vide comme nom,
    et le premier <p> non vide comme description.
    """
    description: Optional[str] = None
    name: Optional[str] = None

    for html in pages_html:
        soup = BeautifulSoup(html, "lxml")

        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            if not name and title_text:
                name = title_text[:255]

        if not description:
            p = soup.find("p")
            if p and p.get_text(strip=True):
                description = p.get_text(strip=True)[:1024]

        if name and description:
            break

    return ParsedCompanyInfo(
        name=name,
        description=description,
        country=None,
        city=None,
        industry=None,
        size=None,
    )


def detect_signals_from_text(text: str) -> ParsedSignals:
    """
    Détecte des signaux simples dans le texte :
    - présence d'offres d'emploi IT,
    - langage de recrutement,
    - offre de services IT / logiciels.
    """
    lower = text.lower()

    it_jobs_keywords = [
        "développeur",
        "developer",
        "devops",
        "data scientist",
        "data engineer",
        "software engineer",
        "full stack",
        "backend",
        "frontend",
        "machine learning engineer",
    ]
    hiring_keywords = [
        "nous recrutons",
        "we are hiring",
        "rejoignez-nous",
        "join our team",
        "postulez",
        "apply now",
    ]
    it_services_keywords = [
        "développement web",
        "development",
        "logiciel",
        "software",
        "application mobile",
        "mobile app",
        "intelligence artificielle",
        "ai",
        "machine learning",
        "data",
        "cloud",
        "consulting",
    ]

    has_it_jobs = any(k in lower for k in it_jobs_keywords)
    hiring_language = any(k in lower for k in hiring_keywords)
    offers_it_services = any(k in lower for k in it_services_keywords)

    return ParsedSignals(
        has_it_jobs=has_it_jobs,
        hiring_language=hiring_language,
        offers_it_services=offers_it_services,
    )


def extract_contacts_from_page(url: str, html: str) -> List[ParsedContactInfo]:
    """
    Extrait des contacts potentiels à partir d'une page :
    - emails
    - numéros de téléphone
    - URLs LinkedIn
    On crée des ParsedContactInfo en associant grossièrement les téléphones/LinkedIn
    aux emails par index (MVP).
    """
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    emails = extract_emails(text)
    phones = extract_phones(text)

    anchors = soup.find_all("a", href=True)
    linkedin_urls = [
        a["href"]
        for a in anchors
        if "linkedin.com/in" in a["href"] or "linkedin.com/profile" in a["href"]
    ]

    contacts: List[ParsedContactInfo] = []

    for idx, email in enumerate(emails):
        phone = phones[idx] if idx < len(phones) else None
        linkedin_url = linkedin_urls[idx] if idx < len(linkedin_urls) else None
        contacts.append(
            ParsedContactInfo(
                full_name=None,
                role_title=None,
                email=email,
                phone=phone,
                linkedin_url=linkedin_url,
            )
        )

    return contacts
