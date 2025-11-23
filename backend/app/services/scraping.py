from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup
from urllib import robotparser

from app.core.config import get_settings
from app.services.rate_limit import respect_rate_limit

settings = get_settings()

@dataclass
class PageContent:
    url: str
    html: str

def normalize_root_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or parsed.path
    return f"{scheme}://{netloc}"

def is_same_domain(url: str, root: str) -> bool:
    return urlparse(url).netloc == urlparse(root).netloc

def load_robots_txt(root: str) -> robotparser.RobotFileParser:
    parsed = urlparse(root)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception:
        pass
    return rp

def crawl_site(root_url: str) -> List[PageContent]:
    root = normalize_root_url(root_url)
    visited: Set[str] = set()
    pages: List[PageContent] = []

    rp = load_robots_txt(root)
    client = httpx.Client(
        headers={"User-Agent": settings.SCRAPER_USER_AGENT},
        timeout=settings.SCRAPER_REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    )

    queue: deque[Tuple[str, int]] = deque()
    queue.append((root, 0))

    while queue and len(pages) < settings.SCRAPER_MAX_PAGES_PER_DOMAIN:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        if depth > settings.SCRAPER_MAX_DEPTH:
            continue

        if rp.default_entry and not rp.can_fetch(settings.SCRAPER_USER_AGENT, url):
            continue

        respect_rate_limit(urlparse(url).netloc)

        try:
            resp = client.get(url)
            if resp.status_code >= 400:
                continue
            html = resp.text
        except httpx.RequestError:
            continue

        pages.append(PageContent(url=url, html=html))

        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("#"):
                continue
            joined = urljoin(url, href)
            if is_same_domain(joined, root) and joined not in visited:
                queue.append((joined, depth + 1))

    client.close()
    return pages
