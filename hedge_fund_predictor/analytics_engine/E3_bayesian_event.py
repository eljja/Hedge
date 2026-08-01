"""
Engine 3: Bayesian Discrete Event Jump Engine.

Updates position probabilities upon receiving real-time or discrete events:
  - 13D (Activist > 5% acquisition) -> Likelihood = 0.95
  - 13G (Passive > 5% acquisition)  -> Likelihood = 0.85
  - Form 4 (Insider Buy)            -> Likelihood = 0.60
  - 13F/A CT Release (Confidential) -> Likelihood = 0.90
  - N-PX Against Vote (Activism)    -> Likelihood = 0.70
  - EU Short Register (Short < 0%)  -> Likelihood = 0.80

Bayes Rule:
  P(Hold | Event) = [ P(Event | Hold) * P(Hold) ] / P(Event)
"""

import logging
from datetime import date
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Event likelihood priors P(Event | Hold)
EVENT_LIKELIHOODS = {
    "13D": 0.95,
    "13D/A": 0.95,
    "13G": 0.85,
    "13G/A": 0.85,
    "13F_CT_REVEAL": 0.90,
    "FORM4_INSIDER_BUY": 0.65,
    "NPX_AGAINST_VOTE": 0.70,
    "EU_SHORT_DISCLOSURE": 0.80,
}

EVENT_BASE_RATES = {
    "13D": 0.05,
    "13G": 0.10,
    "13F_CT_REVEAL": 0.02,
    "FORM4_INSIDER_BUY": 0.15,
    "NPX_AGAINST_VOTE": 0.10,
    "EU_SHORT_DISCLOSURE": 0.05,
}


class BayesianEventEngine:
    """Engine 3: Bayesian Posterior Updating for Realtime Events."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def update_posterior_probability(
        self,
        prior_prob: float,
        event_type: str,
    ) -> float:
        """Apply Bayes' Rule to update holding probability given a discrete event.

        Parameters
        ----------
        prior_prob : float
            Prior probability of position holding (0.0 to 1.0).
        event_type : str
            Event code from EVENT_LIKELIHOODS.

        Returns
        -------
        float
            Updated posterior probability.
        """
        p_event_given_hold = EVENT_LIKELIHOODS.get(event_type, 0.50)
        p_event_given_not_hold = EVENT_BASE_RATES.get(event_type, 0.05)

        prior_prob = max(0.01, min(0.99, prior_prob))

        # P(Event) = P(Event|Hold)*P(Hold) + P(Event|~Hold)*P(~Hold)
        p_event = (p_event_given_hold * prior_prob) + (p_event_given_not_hold * (1.0 - prior_prob))

        posterior = (p_event_given_hold * prior_prob) / p_event
        return round(float(posterior), 4)

    def process_realtime_events(
        self,
        cik: Optional[str] = None,
        lookback_days: int = 30,
    ) -> pd.DataFrame:
        """Fetch realtime events from DB and return updated position posteriors."""
        if self.db is None:
            logger.error("No database connection for Bayesian Event Engine")
            return pd.DataFrame()

        sql = """
            SELECT cik, event_type, event_date, ticker, cusip, shares, direction
            FROM events_realtime
            WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        params = []
        if cik:
            sql += " AND cik = ?"
            params.append(cik)

        sql += " ORDER BY event_date DESC"

        events_df = self.db.query(sql, params)
        if events_df.empty:
            return pd.DataFrame()

        updates = []
        for _, row in events_df.iterrows():
            ev = row["event_type"]
            prior = 0.50  # Default uninformative prior
            post = self.update_posterior_probability(prior, ev)

            updates.append({
                "cik": row["cik"],
                "cusip": row["cusip"],
                "ticker": row["ticker"],
                "event_type": ev,
                "event_date": row["event_date"],
                "prior_prob": prior,
                "posterior_prob": post,
                "confidence_boost": round((post - prior) * 100, 1),
                "engine": "E3_bayesian_event",
            })

        res = pd.DataFrame(updates)
        logger.info("Processed %d events in Bayesian Engine", len(res))
        return res
