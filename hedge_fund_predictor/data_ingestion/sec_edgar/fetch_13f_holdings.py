"""
Fetch actual 13F holdings from SEC EDGAR for a given CIK.

Uses the SEC EDGAR EFTS JSON API to find the latest 13F-HR filing,
then downloads and parses the XML INFOTABLE to extract holdings.

SEC EDGAR API is free and requires only a User-Agent header.
Rate limit: 10 requests/second.
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

SEC_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HedgeFundPredictor/1.0 (contact: admin@hedgepredictor.org)"
SEC_RATE_LIMIT_DELAY = 0.2  # ~5 req/sec


class SECEdgar13FFetcher:
    """Fetches 13F holdings from SEC EDGAR for a given CIK."""

    def __init__(self, user_agent: str = SEC_USER_AGENT):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        })
        retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def _throttled_get(self, url: str, **kwargs) -> requests.Response:
        """GET with rate limiting."""
        time.sleep(SEC_RATE_LIMIT_DELAY)
        resp = self.session.get(url, timeout=15, **kwargs)
        return resp

    def get_latest_13f_accession(self, cik: str) -> Optional[str]:
        """Find the most recent 13F-HR filing accession number for a CIK.

        Uses: https://data.sec.gov/submissions/CIK{cik}.json
        """
        cik_padded = cik.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

        try:
            resp = self._throttled_get(url)
            if resp.status_code != 200:
                logger.warning("SEC EDGAR CIK %s returned status %d", cik, resp.status_code)
                return None
            data = resp.json()

            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])

            for i, form in enumerate(forms):
                if form in ("13F-HR", "13F-HR/A"):
                    return accessions[i]

            logger.warning("No 13F-HR filing found for CIK %s", cik)
            return None

        except Exception as e:
            logger.error("Failed to get filing index for CIK %s: %s", cik, e)
            return None

    def get_13f_holdings(self, cik: str) -> Optional[pd.DataFrame]:
        """Fetch and parse the latest 13F holdings for a CIK.

        Returns a DataFrame with columns:
        - nameOfIssuer: Company name
        - titleOfClass: Security class
        - cusip: CUSIP identifier
        - value: Position value in $1000s
        - shrsOrPrnAmt: Number of shares/principal
        - putCall: PUT/CALL/None
        - investmentDiscretion: SOLE/DEFINED/OTHER
        """
        cik_padded = cik.zfill(10)
        accession = self.get_latest_13f_accession(cik)
        if not accession:
            return None

        # Format accession for URL (remove dashes)
        acc_no_dash = accession.replace("-", "")

        # Get filing index to find the infotable XML file
        index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_dash}/index.json"

        try:
            resp = self._throttled_get(index_url)
            index_data = resp.json()

            # Find the infotable XML file
            infotable_url = None
            directory = index_data.get("directory", {})
            items = directory.get("item", [])

            for item in items:
                name = item.get("name", "").lower()
                if "infotable" in name and name.endswith(".xml"):
                    infotable_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_dash}/{item['name']}"
                    break

            if not infotable_url:
                # Try alternative: look for primary_doc.xml
                for item in items:
                    name = item.get("name", "").lower()
                    if name.endswith(".xml") and "primary" not in name:
                        infotable_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_dash}/{item['name']}"
                        break

            if not infotable_url:
                logger.warning("No infotable XML found for CIK %s, accession %s", cik, accession)
                return None

            # Download and parse the infotable XML
            xml_resp = self._throttled_get(infotable_url)
            return self._parse_infotable_xml(xml_resp.text, cik, accession)

        except Exception as e:
            logger.error("Failed to fetch 13F holdings for CIK %s: %s", cik, e)
            return None

    def _parse_infotable_xml(self, xml_text: str, cik: str, accession: str) -> pd.DataFrame:
        """Parse 13F infotable XML into a DataFrame."""
        # Remove namespace for easier parsing
        xml_text = xml_text.replace('xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable"', '')
        xml_text = xml_text.replace('xmlns:ns1="http://www.sec.gov/edgar/document/thirteenf/informationtable"', '')

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error("XML parse error for CIK %s: %s", cik, e)
            return pd.DataFrame()

        holdings = []

        # Find all infoTable entries (handle different tag patterns)
        for entry in root.iter():
            if "infoTable" in entry.tag:
                holding = {
                    "cik": cik,
                    "accession": accession,
                }

                for child in entry:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                    if tag == "nameOfIssuer":
                        holding["nameOfIssuer"] = child.text or ""
                    elif tag == "titleOfClass":
                        holding["titleOfClass"] = child.text or ""
                    elif tag == "cusip":
                        holding["cusip"] = child.text or ""
                    elif tag == "value":
                        try:
                            holding["value"] = int(child.text or 0)
                        except ValueError:
                            holding["value"] = 0
                    elif tag == "shrsOrPrnAmt":
                        for sub in child:
                            sub_tag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                            if sub_tag == "sshPrnamt":
                                try:
                                    holding["shrsOrPrnAmt"] = int(sub.text or 0)
                                except ValueError:
                                    holding["shrsOrPrnAmt"] = 0
                            elif sub_tag == "sshPrnamtType":
                                holding["sshPrnamtType"] = sub.text or ""
                    elif tag == "putCall":
                        holding["putCall"] = child.text
                    elif tag == "investmentDiscretion":
                        holding["investmentDiscretion"] = child.text or ""

                if "nameOfIssuer" in holding:
                    holdings.append(holding)

        if not holdings:
            logger.warning("No holdings parsed from infotable for CIK %s", cik)
            return pd.DataFrame()

        df = pd.DataFrame(holdings)
        logger.info("Parsed %d holdings for CIK %s (accession: %s)",
                     len(df), cik, accession)
        return df


def fetch_all_fund_holdings(entity_groups: dict) -> dict:
    """Fetch latest 13F holdings for all funds in entity_groups.

    Args:
        entity_groups: dict mapping fund_id -> EntityGroupConfig

    Returns:
        dict mapping fund_id -> pd.DataFrame of holdings
    """
    fetcher = SECEdgar13FFetcher()
    all_holdings = {}

    for fund_id, config in entity_groups.items():
        cik = config.hedge_fund_ciks[0]
        logger.info("Fetching 13F for %s (CIK: %s)...", fund_id, cik)

        df = fetcher.get_13f_holdings(cik)
        if df is not None and not df.empty:
            all_holdings[fund_id] = df
            logger.info("  → %d positions, total value: $%sK",
                        len(df), f"{df['value'].sum():,.0f}" if 'value' in df.columns else "N/A")
        else:
            logger.warning("  → No data for %s", fund_id)

    return all_holdings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    # Quick test: fetch Pershing Square (well-known concentrated portfolio)
    fetcher = SECEdgar13FFetcher()
    df = fetcher.get_13f_holdings("1336528")

    if df is not None and not df.empty:
        print(f"\n=== Pershing Square Latest 13F ({len(df)} holdings) ===")
        # Sort by value descending
        df_sorted = df.sort_values("value", ascending=False)
        for _, row in df_sorted.head(10).iterrows():
            val_m = row.get("value", 0) / 1000  # $1000s -> $M
            print(f"  {row['nameOfIssuer'][:35]:<35s} ${val_m:>10,.1f}M  CUSIP:{row.get('cusip','')}")
    else:
        print("No data retrieved")
