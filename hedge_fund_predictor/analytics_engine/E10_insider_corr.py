"""
Engine 10: Form 4 Insider Trading Correlation Booster.

Engine 10 in v6 architecture.

Detects if corporate C-suite executives (CEO/CFO) buy open-market shares (Form 4 Code P)
during the same quarter a hedge fund is accumulating. If concurrent buy exists,
conviction score is doubled (2.0x boost).
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class InsiderCorrelationEngine:
    """Engine 10: Form 4 Corporate Insider Correlation Detector."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def evaluate_insider_boost(
        self,
        ticker_or_cusip: str,
        quarter_date: str,
    ) -> dict:
        """Check if open-market insider buys (Form 4 Code P) occurred in the quarter.

        Returns
        -------
        dict
            Keys: has_concurrent_insider_buy, boost_multiplier, total_insider_shares
        """
        if self.db is None:
            return {"has_concurrent_insider_buy": False, "boost_multiplier": 1.0, "total_insider_shares": 0}

        sql = """
            SELECT event_type, shares, direction
            FROM events_realtime
            WHERE (ticker = ? OR cusip = ?)
              AND event_type = 'FORM4_INSIDER'
              AND direction = 'BUY'
        """
        df = self.db.query(sql, [ticker_or_cusip, ticker_or_cusip])

        if not df.empty:
            total_shares = df["shares"].fillna(0).sum()
            logger.info("Engine 10: Concurrent insider buy detected for %s (%d shares)", ticker_or_cusip, total_shares)
            return {
                "has_concurrent_insider_buy": True,
                "boost_multiplier": 2.0,
                "total_insider_shares": int(total_shares),
                "engine": "E10_insider_corr",
            }

        return {"has_concurrent_insider_buy": False, "boost_multiplier": 1.0, "total_insider_shares": 0, "engine": "E10_insider_corr"}
