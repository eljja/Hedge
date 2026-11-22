"""
Fetch actual 13F holdings from SEC EDGAR for a given CIK.

Uses the SEC EDGAR Submissions JSON API to find the latest 13F-HR filing
(strictly ordered by reportDate to avoid grabbing partial old-quarter 13F-HR/A
amendments), then downloads and parses the XML INFOTABLE to extract holdings.

SEC EDGAR API is free and requires only a compliant User-Agent header.
Rate limit: 10 requests/second (we throttle to ~7 req/sec).
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

SEC_USER_AGENT = "HedgeFundPredictor/2.0 (contact: research@hedgepredictor.org)"
SEC_RATE_LIMIT_DELAY = 0.14  # ~7 req/sec (safely under SEC's 10 req/sec limit)


class SECEdgar13FFetcher:
    """Fetches 13F holdings from SEC EDGAR for a given CIK."""

    def __init__(self, user_agent: str = SEC_USER_AGENT):
        self.session = requests.Session()
        # IMPORTANT: Do NOT hardcode a Host header on the session, because
        # submissions live on data.sec.gov while archives live on www.sec.gov.
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json, application/xml, text/xml, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
        })
        retries = Retry(
            total=3,
            backoff_factor=0.6,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def _throttled_get(self, url: str, **kwargs) -> requests.Response:
        """GET with SEC-compliant rate limiting."""
        time.sleep(SEC_RATE_LIMIT_DELAY)
        return self.session.get(url, timeout=20, **kwargs)

    def get_latest_13f_candidates(self, cik: str, limit: int = 3) -> list[dict]:
        """Return up to `limit` most recent 13F-HR (then 13F-HR/A) filings ordered by reportDate desc."""
        cik_padded = cik.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

        try:
            resp = self._throttled_get(url)
            if resp.status_code != 200:
                logger.warning("SEC EDGAR CIK %s returned status %d", cik, resp.status_code)
                return []
            data = resp.json()
            entity_name = data.get("name", "")

            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            report_dates = recent.get("reportDate", [])
            filing_dates = recent.get("filingDate", [])

            hr_list = []
            amend_list = []

            for i, form in enumerate(forms):
                if form not in ("13F-HR", "13F-HR/A"):
                    continue
                rdate = report_dates[i] if i < len(report_dates) else ""
                fdate = filing_dates[i] if i < len(filing_dates) else ""
                candidate = {
                    "cik": cik_padded,
                    "entity_name": entity_name,
                    "form": form,
                    "accession": accessions[i],
                    "report_date": rdate,
                    "filing_date": fdate,
                }
                if form == "13F-HR":
                    hr_list.append(candidate)
                else:
                    amend_list.append(candidate)

            hr_list.sort(key=lambda x: (x["report_date"], x["filing_date"]), reverse=True)
            amend_list.sort(key=lambda x: (x["report_date"], x["filing_date"]), reverse=True)
            candidates = (hr_list + amend_list)[:limit]
            if not candidates:
                logger.warning("No 13F-HR filing found for CIK %s (%s)", cik, entity_name)
            return candidates

        except Exception as e:
            logger.error("Failed to get filing index for CIK %s: %s", cik, e)
            return []

    def get_latest_13f_metadata(self, cik: str) -> Optional[dict]:
        """Find the most recent full 13F-HR filing metadata for a CIK."""
        candidates = self.get_latest_13f_candidates(cik, limit=1)
        return candidates[0] if candidates else None

    def get_latest_13f_accession(self, cik: str) -> Optional[str]:
        """Backward-compatible wrapper returning only the accession number."""
        meta = self.get_latest_13f_metadata(cik)
        return meta["accession"] if meta else None

    def get_13f_holdings(self, cik: str) -> Optional[pd.DataFrame]:
        """Fetch and parse the latest non-empty 13F holdings for a CIK."""
        candidates = self.get_latest_13f_candidates(cik, limit=3)
        if not candidates:
            return None

        cik_int = int(cik)

        for meta in candidates:
            accession = meta["accession"]
            acc_no_dash = accession.replace("-", "")
            index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no_dash}/index.json"

            try:
                resp = self._throttled_get(index_url)
                if resp.status_code != 200:
                    continue
                index_data = resp.json()

                items = index_data.get("directory", {}).get("item", [])
                infotable_url = self._select_infotable_xml(items, cik_int, acc_no_dash)
                if not infotable_url:
                    continue

                xml_resp = self._throttled_get(infotable_url)
                if xml_resp.status_code != 200:
                    continue

                df = self._parse_infotable_xml(xml_resp.text, cik, accession, meta.get("report_date", ""))
                if df is not None and not df.empty:
                    df.attrs["report_date"] = meta.get("report_date", "")
                    df.attrs["filing_date"] = meta.get("filing_date", "")
                    df.attrs["accession"] = accession
                    df.attrs["entity_name"] = meta.get("entity_name", "")
                    df.attrs["cik"] = meta.get("cik", cik.zfill(10))
                    return df
            except Exception as e:
                logger.error("Failed to fetch 13F holdings for CIK %s (%s): %s", cik, accession, e)

        return None

    @staticmethod
    def _select_infotable_xml(items: list[dict], cik_int: int, acc_no_dash: str) -> Optional[str]:
        """Select the best 13F infotable XML file from an EDGAR filing directory."""
        xml_candidates = []
        for item in items:
            name = item.get("name", "")
            low = name.lower()
            if not low.endswith(".xml"):
                continue
            if "primary" in low or low.startswith("r") and low[1:-4].isdigit():
                continue
            size = int(item.get("size") or 0)
            priority = 0
            if "infotable" in low or "informationtable" in low:
                priority = 3
            elif "13f" in low or "table" in low or "holding" in low:
                priority = 2
            else:
                priority = 1
            xml_candidates.append((priority, size, name))

        if not xml_candidates:
            return None

        xml_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_name = xml_candidates[0][2]
        return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no_dash}/{best_name}"

    def _parse_infotable_xml(
        self, xml_text: str, cik: str, accession: str, report_date: str = ""
    ) -> pd.DataFrame:
        """Parse 13F infotable XML into a DataFrame with value normalized to exact USD."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error("XML parse error for CIK %s: %s", cik, e)
            return pd.DataFrame()

        holdings = []
        for entry in root.iter():
            local_tag = entry.tag.split("}")[-1] if "}" in entry.tag else entry.tag
            if local_tag != "infoTable":
                continue

            holding = {
                "cik": cik.zfill(10),
                "accession": accession,
            }

            for child in entry:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                if tag == "nameOfIssuer":
                    holding["nameOfIssuer"] = (child.text or "").strip()
                elif tag == "titleOfClass":
                    holding["titleOfClass"] = (child.text or "").strip()
                elif tag == "cusip":
                    holding["cusip"] = (child.text or "").strip().upper()
                elif tag == "value":
                    try:
                        holding["value"] = int(float((child.text or "0").replace(",", "").strip()))
                    except ValueError:
                        holding["value"] = 0
                elif tag == "shrsOrPrnAmt":
                    for sub in child:
                        sub_tag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                        if sub_tag == "sshPrnamt":
                            try:
                                holding["shrsOrPrnAmt"] = int(float((sub.text or "0").replace(",", "").strip()))
                            except ValueError:
                                holding["shrsOrPrnAmt"] = 0
                        elif sub_tag == "sshPrnamtType":
                            holding["sshPrnamtType"] = (sub.text or "").strip()
                elif tag == "putCall":
                    val = (child.text or "").strip().upper()
                    holding["putCall"] = val if val in ("PUT", "CALL") else None
                elif tag == "investmentDiscretion":
                    holding["investmentDiscretion"] = (child.text or "").strip()

            if holding.get("nameOfIssuer") and holding.get("value", 0) > 0:
                holdings.append(holding)

        if not holdings:
            logger.warning("No holdings parsed from infotable for CIK %s", cik)
            return pd.DataFrame()

        df = pd.DataFrame(holdings)

        # Normalize <value> to exact USD:
        # SEC Form 13F XML switched from $1,000s to exact nearest dollar starting 2023-01-03.
        # Double-check with median implied share price (for SH equity rows) so edge cases are handled safely.
        is_pre_2023 = bool(report_date and report_date < "2023-01-01")
        if not is_pre_2023 and "shrsOrPrnAmt" in df.columns:
            sh_mask = (
                (df.get("sshPrnamtType", "SH") == "SH")
                & (df["shrsOrPrnAmt"] > 0)
                & (df["value"] > 0)
                & (df.get("putCall").isna() if "putCall" in df.columns else True)
            )
            if sh_mask.any():
                implied_prices = df.loc[sh_mask, "value"] / df.loc[sh_mask, "shrsOrPrnAmt"]
                median_price = float(implied_prices.median())
                # If median implied price is < $0.50, the filer reported in $1,000s
                if median_price < 0.50:
                    is_pre_2023 = True

        if is_pre_2023:
            df["value"] = df["value"] * 1000

        logger.info(
            "Parsed %d holdings for CIK %s (reportDate=%s, total=$%.1fM)",
            len(df),
            cik,
            report_date or "N/A",
            df["value"].sum() / 1_000_000,
        )
        return df


def fetch_all_fund_holdings(entity_groups: dict) -> dict:
    """Fetch latest 13F holdings for all funds in entity_groups."""
    fetcher = SECEdgar13FFetcher()
    all_holdings = {}

    for fund_id, config in entity_groups.items():
        for cik in config.hedge_fund_ciks:
            logger.info("Fetching 13F for %s (CIK: %s)...", fund_id, cik)
            df = fetcher.get_13f_holdings(cik)
            if df is not None and not df.empty:
                all_holdings[fund_id] = df
                logger.info(
                    "  → %d positions, total value: $%.1fM",
                    len(df),
                    df["value"].sum() / 1_000_000 if "value" in df.columns else 0,
                )
                break
        if fund_id not in all_holdings:
            logger.warning("  → No data for %s", fund_id)

    return all_holdings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    fetcher = SECEdgar13FFetcher()
    df = fetcher.get_13f_holdings("0002026053")

    if df is not None and not df.empty:
        print(f"\n=== Pershing Square Latest 13F ({len(df)} holdings, report={df.attrs.get('report_date')}) ===")
        df_sorted = df.sort_values("value", ascending=False)
        for _, row in df_sorted.head(10).iterrows():
            val_m = row.get("value", 0) / 1_000_000
            print(f"  {row['nameOfIssuer'][:35]:<35s} ${val_m:>10,.1f}M  CUSIP:{row.get('cusip','')}")
    else:
        print("No data retrieved")
