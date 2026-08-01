"""
Engine 11: SEC Comment Letter Regulatory Scrutiny Scanner.

Engine 11 in v6 architecture.

Parses SEC comment letters (UPLOAD/CORRESP) to detect accounting scrutiny,
fee transparency issues, or regulatory inquiries targeting specific funds or portfolio companies.
"""

import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

SCRUTINY_KEYWORDS = [
    "accounting treatment", "revenue recognition", "valuation method",
    "fee disclosure", "conflict of interest", "custody", "internal control",
    "material weakness", "restatement", "investigation", "subpoena"
]


class SECScrutinyEngine:
    """Engine 11: SEC Comment Letter Risk Scanner."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def scan_comment_letter(self, letter_text: str) -> dict:
        """Scan text of SEC UPLOAD/CORRESP letter for regulatory red flags.

        Returns
        -------
        dict
            Keys: scrutiny_score (0.0 to 1.0), flag_count, matched_terms, penalty_multiplier
        """
        if not letter_text:
            return {"scrutiny_score": 0.0, "flag_count": 0, "matched_terms": [], "penalty_multiplier": 1.0}

        text_lower = letter_text.lower()
        matched = []

        for kw in SCRUTINY_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                matched.append(kw)

        flag_count = len(matched)
        score = min(1.0, flag_count / 5.0)

        # High scrutiny -> penalty multiplier reduces estimation confidence
        penalty = round(max(0.4, 1.0 - (score * 0.5)), 2)

        return {
            "scrutiny_score": round(score, 2),
            "flag_count": flag_count,
            "matched_terms": matched,
            "penalty_multiplier": penalty,
            "engine": "E11_sec_scrutiny",
        }
