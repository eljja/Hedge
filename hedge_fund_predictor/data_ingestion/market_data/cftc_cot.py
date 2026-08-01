"""
CFTC Commitments of Traders (COT) weekly data loader.

Data Channel ⑪ from v6 architecture — tracks aggregate futures positioning
of "Leveraged Funds" and "Managed Money" categories to estimate sector/asset
exposure for global-macro and CTA hedge funds.

Sources:
  - Traders in Financial Futures (TFF): https://www.cftc.gov/files/dea/history/
  - Disaggregated: https://www.cftc.gov/files/dea/history/
"""

import io
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL patterns — CFTC publishes annual ZIP archives
# ---------------------------------------------------------------------------

_BASE = "https://www.cftc.gov/files/dea/history"

# TFF = Traders in Financial Futures (equity index, treasury, FX futures)
TFF_URL_TEMPLATE = _BASE + "/fut_fin_txt_{year}.zip"

# Disaggregated = commodity futures (oil, gold, ag, etc.)
DISAGG_URL_TEMPLATE = _BASE + "/fut_disagg_txt_{year}.zip"


# Key contracts we track for hedge-fund macro positioning
FINANCIAL_CONTRACTS = {
    "sp500":       "E-MINI S&P 500",
    "nasdaq":      "NASDAQ-100",
    "russell":     "E-MINI RUSSELL 2000",
    "treasury_10y": "10-YEAR",
    "treasury_2y":  "2-YEAR",
    "treasury_30y": "U.S. TREASURY BONDS",
    "euro_fx":     "EURO FX",
    "yen":         "JAPANESE YEN",
    "gbp":         "BRITISH POUND",
    "cad":         "CANADIAN DOLLAR",
}

COMMODITY_CONTRACTS = {
    "crude_oil":   "CRUDE OIL, LIGHT SWEET",
    "gold":        "GOLD",
    "silver":      "SILVER",
    "natural_gas": "NATURAL GAS",
    "copper":      "COPPER",
    "corn":        "CORN",
    "soybeans":    "SOYBEANS",
}


class CFTCCOTLoader:
    """Download and parse CFTC Commitments of Traders weekly reports.

    Extracts "Leveraged Funds" (TFF) and "Managed Money" (Disaggregated)
    net positioning for key financial and commodity futures contracts.
    """

    def __init__(self, db_manager=None, data_dir: Optional[Path] = None):
        self.db = db_manager
        if data_dir is None:
            from hedge_fund_predictor.config.settings import DATA_DIR
            self.data_dir = DATA_DIR / "cftc"
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # -- public API ---------------------------------------------------------

    def load_recent_years(self, n_years: int = 3) -> pd.DataFrame:
        """Download and process TFF + Disaggregated for the last *n_years*."""
        current_year = datetime.now().year
        years = list(range(current_year - n_years + 1, current_year + 1))

        all_frames: list[pd.DataFrame] = []
        for year in years:
            df_tff = self._download_tff(year)
            df_dis = self._download_disaggregated(year)
            if not df_tff.empty:
                all_frames.append(df_tff)
            if not df_dis.empty:
                all_frames.append(df_dis)

        if not all_frames:
            logger.error("No COT data downloaded")
            return pd.DataFrame()

        result = pd.concat(all_frames, ignore_index=True)
        result = self._compute_z_scores(result)

        if self.db is not None:
            self.db.bulk_insert("cftc_cot", result)
            logger.info("Inserted %d COT rows into DB", len(result))

        return result

    def load_year(self, year: int) -> pd.DataFrame:
        """Load COT data for a single year."""
        return self.load_recent_years(1)  # simplified

    # -- download helpers ---------------------------------------------------

    def _download_tff(self, year: int) -> pd.DataFrame:
        """Download Traders in Financial Futures report for given year."""
        url = TFF_URL_TEMPLATE.format(year=year)
        cache_path = self.data_dir / f"tff_{year}.csv"

        raw_df = self._fetch_zip_csv(url, cache_path)
        if raw_df.empty:
            return raw_df

        # Filter to contracts we care about
        rows: list[dict] = []
        for friendly_name, pattern in FINANCIAL_CONTRACTS.items():
            mask = raw_df["Market_and_Exchange_Names"].str.contains(
                pattern, case=False, na=False
            )
            subset = raw_df[mask].copy()
            if subset.empty:
                continue

            for _, row in subset.iterrows():
                lev_long = _safe_int(row.get("Lev_Money_Positions_Long_All", 0))
                lev_short = _safe_int(row.get("Lev_Money_Positions_Short_All", 0))
                rows.append(
                    {
                        "report_date": _parse_date(row.get("Report_Date_as_YYYY-MM-DD")),
                        "market_name": friendly_name,
                        "contract_type": "financial",
                        "lev_long": lev_long,
                        "lev_short": lev_short,
                        "lev_net": lev_long - lev_short,
                        "mm_long": None,
                        "mm_short": None,
                        "mm_net": None,
                        "z_score": None,  # computed later
                    }
                )

        return pd.DataFrame(rows)

    def _download_disaggregated(self, year: int) -> pd.DataFrame:
        """Download Disaggregated COT report (commodities)."""
        url = DISAGG_URL_TEMPLATE.format(year=year)
        cache_path = self.data_dir / f"disagg_{year}.csv"

        raw_df = self._fetch_zip_csv(url, cache_path)
        if raw_df.empty:
            return raw_df

        rows: list[dict] = []
        for friendly_name, pattern in COMMODITY_CONTRACTS.items():
            mask = raw_df["Market_and_Exchange_Names"].str.contains(
                pattern, case=False, na=False
            )
            subset = raw_df[mask].copy()
            if subset.empty:
                continue

            for _, row in subset.iterrows():
                mm_long = _safe_int(row.get("M_Money_Positions_Long_ALL", 0))
                mm_short = _safe_int(row.get("M_Money_Positions_Short_ALL", 0))
                rows.append(
                    {
                        "report_date": _parse_date(row.get("Report_Date_as_YYYY-MM-DD")),
                        "market_name": friendly_name,
                        "contract_type": "commodity",
                        "lev_long": None,
                        "lev_short": None,
                        "lev_net": None,
                        "mm_long": mm_long,
                        "mm_short": mm_short,
                        "mm_net": mm_long - mm_short,
                        "z_score": None,
                    }
                )

        return pd.DataFrame(rows)

    def _fetch_zip_csv(self, url: str, cache_path: Path) -> pd.DataFrame:
        """Download a CFTC ZIP file, extract the single CSV inside."""
        if cache_path.exists():
            logger.info("Using cached COT file: %s", cache_path.name)
            return pd.read_csv(cache_path, low_memory=False)

        logger.info("Downloading COT from %s", url)
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("COT download failed (%s): %s", url, exc)
            return pd.DataFrame()

        try:
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_names = [n for n in zf.namelist() if n.endswith(".txt") or n.endswith(".csv")]
                if not csv_names:
                    logger.warning("No CSV/TXT found in ZIP: %s", url)
                    return pd.DataFrame()
                with zf.open(csv_names[0]) as f:
                    df = pd.read_csv(f, low_memory=False)
                    # cache
                    df.to_csv(cache_path, index=False)
                    return df
        except Exception as exc:
            logger.error("Error parsing COT ZIP: %s", exc)
            return pd.DataFrame()

    # -- z-score computation ------------------------------------------------

    @staticmethod
    def _compute_z_scores(
        df: pd.DataFrame, lookback_weeks: int = 52
    ) -> pd.DataFrame:
        """Compute rolling Z-score of net positioning per contract.

        Z-score tells us: "How extreme is the current positioning relative
        to the past year?"  Values > 2 or < -2 are significant.
        """
        if df.empty:
            return df

        df = df.sort_values(["market_name", "report_date"]).copy()

        def _zscore_group(g: pd.DataFrame) -> pd.DataFrame:
            # Use lev_net for financial, mm_net for commodity
            net_col = "lev_net" if g["contract_type"].iloc[0] == "financial" else "mm_net"
            net = g[net_col].astype(float)
            rolling_mean = net.rolling(lookback_weeks, min_periods=10).mean()
            rolling_std = net.rolling(lookback_weeks, min_periods=10).std()
            g["z_score"] = (net - rolling_mean) / rolling_std.replace(0, np.nan)
            return g

        df = df.groupby("market_name", group_keys=False).apply(_zscore_group)
        return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(val) -> Optional[object]:
    """Parse CFTC date string to date object."""
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(str(val)).date()
    except Exception:
        return None


def _safe_int(v) -> int:
    try:
        f = float(v)
        return 0 if np.isnan(f) else int(f)
    except (TypeError, ValueError):
        return 0
