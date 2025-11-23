from typing import Tuple
from app.services.parsing import ParsedSignals

def classify_prospect(signals: ParsedSignals) -> Tuple[str, float]:
    """
    Retourne (prospect_type, score) basé uniquement sur les signaux heuristiques.
    prospect_type: "project", "staffing", "both", "unknown"
    """
    score = 0.0
    project = False
    staffing = False

    if signals.offers_it_services:
        project = True
        score += 30.0

    if signals.has_it_jobs:
        staffing = True
        score += 30.0

    if signals.hiring_language:
        staffing = True
        score += 10.0

    if project and staffing:
        ptype = "both"
    elif project:
        ptype = "project"
    elif staffing:
        ptype = "staffing"
    else:
        ptype = "unknown"

    return ptype, score
