"""
SEC EDGAR real-time poller for 13D/13G/Form 4 filings.

Data Channel ② from v6 architecture — monitors SEC EDGAR for new
activist filings (13D), passive large-holder filings (13G), and
insider transaction reports (Form 4) for funds in our universe.

Also serves Engine 10 (Insider Correlation): detects when corporate
insiders buy/sell alongside hedge fund activity.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Form types we monitor
MONITORED_FORMS = {
    "SC 13D",
    "SC 13D/A",
    "SC 13G",
    "SC 13G/A",
    "4",        # Form 4 insider trading
    "3",        # Form 3 initial insider holdings
}


class SECRealtimePoller:
    """Poll SEC EDGAR for new 13D/13G/Form 4 filings.

    Uses the SEC's submissions JSON endpoint:
        https://data.sec.gov/submissions/CIK{cik}.json

    Rate limited to 10 requests/second per SEC policy.
    """

    def __init__(self, db_manager=None):
        from hedge_fund_predictor.config.settings import (
            SEC_BASE_URL,
            SEC_USER_AGENT,
            SEC_RATE_LIMIT,
        )

        self.base_url = SEC_BASE_URL
        self.headers = {"User-Agent": SEC_USER_AGENT}
        self.rate_limit_delay = 1.0 / SEC_RATE_LIMIT
        self.db = db_manager
        self._last_request_time = 0.0

    # -- public API ---------------------------------------------------------

    def poll_fund_filings(
        self,
        ciks: list[str],
        lookback_days: int = 7,
        form_types: Optional[set[str]] = None,
    ) -> pd.DataFrame:
        """Check each CIK for recent filings of interest.

        Parameters
        ----------
        ciks : list[str]
            Zero-padded 10-digit CIK numbers.
        lookback_days : int
            Only return filings from the last N days.
        form_types : set[str]
            Forms to watch for. Default: 13D, 13G, Form 4.

        Returns
        -------
        pd.DataFrame
            Columns: cik, event_type, event_date, accession_number,
            primary_doc, form_description
        """
        if form_types is None:
            form_types = MONITORED_FORMS

        cutoff = datetime.now() - timedelta(days=lookback_days)
        all_events: list[dict] = []

        for cik in ciks:
            events = self._check_cik(cik, cutoff, form_types)
            all_events.extend(events)

        df = pd.DataFrame(all_events)
        if not df.empty:
            logger.info(
                "Found %d new filings across %d CIKs", len(df), len(ciks)
            )
            if self.db is not None:
                self._store_events(df)

        return df

    def poll_insider_trades(
        self,
        tickers_or_ciks: list[str],
        lookback_days: int = 90,
    ) -> pd.DataFrame:
        """Poll Form 4 insider transactions for specific companies.

        Used by Engine 10 (Insider Correlation) to find CEO/CFO buys
        that coincide with hedge fund accumulation.

        Parameters
        ----------
        tickers_or_ciks : list[str]
            Company CIKs to check for insider trades.
        lookback_days : int
            Lookback window for recent insider activity.
        """
        cutoff = datetime.now() - timedelta(days=lookback_days)
        all_trades: list[dict] = []

        for cik in tickers_or_ciks:
            events = self._check_cik(cik, cutoff, {"4", "3"})
            all_trades.extend(events)

        return pd.DataFrame(all_trades)

    # -- internal -----------------------------------------------------------

    def _check_cik(
        self, cik: str, cutoff: datetime, form_types: set[str]
    ) -> list[dict]:
        """Fetch recent filings for a single CIK."""
        self._rate_limit()

        url = f"{self.base_url}/submissions/CIK{cik}.json"
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.debug("Failed to fetch %s: %s", cik, exc)
            return []

        try:
            data = resp.json()
        except json.JSONDecodeError:
            return []

        recent = data.get("filings", {}).get("recent", {})
        if not recent:
            return []

        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        events: list[dict] = []
        for i, form in enumerate(forms):
            if form not in form_types:
                continue

            filing_date_str = dates[i] if i < len(dates) else None
            if filing_date_str is None:
                continue

            try:
                filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            except ValueError:
                continue

            if filing_date < cutoff:
                continue  # too old

            events.append(
                {
                    "cik": cik,
                    "event_type": _classify_form(form),
                    "form_type": form,
                    "event_date": filing_date.date(),
                    "accession_number": accessions[i] if i < len(accessions) else None,
                    "primary_doc": primary_docs[i] if i < len(primary_docs) else None,
                    "ticker": None,  # resolved later
                    "cusip": None,
                    "shares": None,
                    "value_thousands": None,
                    "direction": _infer_direction(form),
                    "raw_json": None,
                }
            )

        return events

    def _store_events(self, df: pd.DataFrame) -> None:
        """Store discovered events in the database."""
        if self.db is None:
            return

        store_df = df[
            [
                "cik", "event_type", "event_date", "ticker",
                "cusip", "shares", "value_thousands", "direction",
                "raw_json",
            ]
        ].copy()

        self.db.bulk_insert("events_realtime", store_df)
        logger.info("Stored %d events in DB", len(store_df))

    def _rate_limit(self) -> None:
        """Enforce SEC's 10 requests/second policy."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()


# ---------------------------------------------------------------------------
# SC 13D/G detail parser (for extracting shares and target info)
# ---------------------------------------------------------------------------

class SC13DParser:
    """Parse SC 13D/G filing details to extract:
    - Subject company (target)
    - Shares acquired
    - Percent of class
    - Purpose of transaction
    """

    def __init__(self):
        from hedge_fund_predictor.config.settings import SEC_USER_AGENT
        self.headers = {"User-Agent": SEC_USER_AGENT}

    def parse_filing(self, accession_number: str, cik: str) -> dict:
        """Download and parse a 13D/G filing for key data points.

        Returns
        -------
        dict with keys: subject_company, cusip, shares, percent_class,
        purpose, acquisition_date
        """
        # Construct EDGAR filing URL
        acc_no_clean = accession_number.replace("-", "")
        url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{int(cik)}/{acc_no_clean}/{accession_number}.txt"
        )

        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            return self._extract_13d_fields(resp.text)
        except Exception as exc:
            logger.debug("13D parse failed for %s: %s", accession_number, exc)
            return {}

    def _extract_13d_fields(self, text: str) -> dict:
        """Simple regex/text extraction from 13D filing text."""
        import re

        result = {}

        # CUSIP
        cusip_match = re.search(r"CUSIP\s*(?:No\.?\s*)?:?\s*([A-Z0-9]{6,9})", text, re.IGNORECASE)
        if cusip_match:
            result["cusip"] = cusip_match.group(1).strip()

        # Percent of class
        pct_match = re.search(
            r"PERCENT\s+OF\s+CLASS.*?:\s*([\d.]+)\s*%",
            text,
            re.IGNORECASE,
        )
        if pct_match:
            result["percent_class"] = float(pct_match.group(1))

        # Number of shares
        shares_match = re.search(
            r"(?:AGGREGATE\s+AMOUNT|NUMBER\s+OF\s+SHARES).*?:\s*([\d,]+)",
            text,
            re.IGNORECASE,
        )
        if shares_match:
            result["shares"] = int(shares_match.group(1).replace(",", ""))

        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_form(form: str) -> str:
    """Map SEC form type to our event classification."""
    form_upper = form.upper().strip()
    if "13D" in form_upper:
        return "13D"
    elif "13G" in form_upper:
        return "13G"
    elif form_upper in ("4", "3"):
        return "FORM4_INSIDER"
    return "OTHER"


def _infer_direction(form: str) -> str:
    """Infer likely direction from form type.
    13D = acquisition (buy), Form 4 = unknown until parsed.
    """
    if "13D" in form.upper():
        return "BUY"  # 13D is always about acquisitions > 5%
    return "UNKNOWN"
