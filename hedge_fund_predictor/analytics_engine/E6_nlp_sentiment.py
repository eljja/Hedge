"""
Engine 6: NLP Sentiment Analyzer for Investor Letters & News RSS.

Channel ⑭ / Engine 6 in v6 architecture.

Extracts sentiment scores for specific tickers or hedge funds from
investor letters, Sohn conference transcripts, and Google News RSS feeds.
"""

import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Basic sentiment dictionary for financial texts
BULLISH_KEYWORDS = [
    "long", "overweight", "buy", "bullish", "conviction", "undervalued",
    "upside", "catalyst", "growth", "outperform", "opportunity", "moat"
]

BEARISH_KEYWORDS = [
    "short", "underweight", "sell", "bearish", "overvalued", "downside",
    "risk", "headwind", "underperform", "deterioration", "impairment", "fraud"
]


class NLPSentimentEngine:
    """Engine 6: Financial NLP Sentiment Extractor."""

    def __init__(self, use_transformer: bool = False):
        self.use_transformer = use_transformer
        self.model = None

    def analyze_text(self, text: str, ticker: Optional[str] = None) -> dict:
        """Analyze sentiment of a snippet or investor letter text.

        Parameters
        ----------
        text : str
            Raw text content.
        ticker : str, optional
            Target ticker symbol if searching for company-specific mentions.

        Returns
        -------
        dict
            Keys: sentiment_score (-1.0 to +1.0), bullish_count, bearish_count, mentions
        """
        if not text:
            return {"sentiment_score": 0.0, "bullish_count": 0, "bearish_count": 0, "mentions": 0}

        text_lower = text.lower()
        mentions = 0
        if ticker:
            ticker_pattern = r"\b" + re.escape(ticker.lower()) + r"\b"
            mentions = len(re.findall(ticker_pattern, text_lower))

        bull_count = sum(len(re.findall(r"\b" + kw + r"\b", text_lower)) for kw in BULLISH_KEYWORDS)
        bear_count = sum(len(re.findall(r"\b" + kw + r"\b", text_lower)) for kw in BEARISH_KEYWORDS)

        total = bull_count + bear_count
        if total == 0:
            score = 0.0
        else:
            score = (bull_count - bear_count) / float(total)

        return {
            "sentiment_score": round(score, 3),
            "bullish_count": bull_count,
            "bearish_count": bear_count,
            "mentions": mentions,
            "engine": "E6_nlp_sentiment",
        }

    def analyze_corpus(self, documents: list[dict]) -> pd.DataFrame:
        """Analyze a collection of documents [{'text': ..., 'ticker': ..., 'fund_group': ...}]."""
        results = []
        for doc in documents:
            res = self.analyze_text(doc.get("text", ""), doc.get("ticker"))
            res["fund_group"] = doc.get("fund_group")
            res["ticker"] = doc.get("ticker")
            results.append(res)

        return pd.DataFrame(results)
