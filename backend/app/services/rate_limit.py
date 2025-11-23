import time
from collections import defaultdict
from typing import Dict

from app.core.config import get_settings

settings = get_settings()

_last_call_per_domain: Dict[str, float] = defaultdict(float)

def respect_rate_limit(domain: str) -> None:
    now = time.time()
    last = _last_call_per_domain[domain]
    delay = settings.SCRAPER_REQUEST_DELAY_SECONDS
    if now - last < delay:
        time.sleep(delay - (now - last))
    _last_call_per_domain[domain] = time.time()
