"""
Market data ingestion: yfinance prices, Fama-French factors, FRED macro series.

Channels ⑨ (yfinance), ⑩ (FF5 + FRED) from the v6 architecture.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# yfinance wrapper
# ---------------------------------------------------------------------------

class YFinanceClient:
    """Download price data for individual tickers, sector/theme ETFs, and
    public hedge-fund vehicles.  Writes results into DuckDB via
    DatabaseManager.
    """

    def __init__(self, db_manager=None):
        self.db = db_manager

    # -- public API ---------------------------------------------------------

    def download_prices(
        self,
        tickers: list[str],
        start: str = "2022-01-01",
        end: Optional[str] = None,
        *,
        batch_size: int = 50,
    ) -> pd.DataFrame:
        """Bulk-download daily adjusted-close prices.

        Parameters
        ----------
        tickers : list[str]
            Yahoo Finance ticker symbols.
        start / end : str
            Date range in 'YYYY-MM-DD' format.
        batch_size : int
            Download tickers in batches to avoid timeouts.

        Returns
        -------
        pd.DataFrame
            Columns: ticker, date, open, high, low, close, adj_close, volume
        """
        import yfinance as yf

        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")

        all_frames: list[pd.DataFrame] = []

        for i in range(0, len(tickers), batch_size):
            batch = tickers[i : i + batch_size]
            logger.info(
                "Downloading prices batch %d/%d (%d tickers)",
                i // batch_size + 1,
                (len(tickers) - 1) // batch_size + 1,
                len(batch),
            )
            try:
                raw = yf.download(
                    batch,
                    start=start,
                    end=end,
                    group_by="ticker",
                    auto_adjust=False,
                    threads=True,
                    progress=False,
                )
                df = self._reshape_yf(raw, batch)
                all_frames.append(df)
            except Exception as exc:
                logger.warning("yfinance batch failed: %s", exc)

        if not all_frames:
            logger.error("No price data downloaded")
            return pd.DataFrame()

        result = pd.concat(all_frames, ignore_index=True)

        if self.db is not None:
            self.db.bulk_insert("market_prices", result)
            logger.info("Inserted %d price rows into DB", len(result))

        return result

    def download_sector_etf_returns(
        self,
        start: str = "2022-01-01",
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Download daily returns for all sector/theme ETFs and pivot into
        the wide format expected by the Kalman RBSA engine.
        """
        from hedge_fund_predictor.config.sector_etfs import ALL_FACTOR_ETFS

        prices = self.download_prices(ALL_FACTOR_ETFS, start=start, end=end)
        if prices.empty:
            return pd.DataFrame()

        # Pivot to wide: date × ticker → adj_close
        wide = prices.pivot_table(
            index="date", columns="ticker", values="adj_close"
        )
        returns = wide.pct_change().dropna(how="all")
        returns = returns.reset_index()

        if self.db is not None:
            self.db.bulk_insert("sector_etf_returns", returns)
            logger.info("Inserted %d ETF-return rows", len(returns))

        return returns

    # -- internal -----------------------------------------------------------

    @staticmethod
    def _reshape_yf(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
        """Reshape yfinance multi-ticker output into long-form rows."""
        rows: list[dict] = []

        if len(tickers) == 1:
            # Single-ticker download: columns are just OHLCV
            ticker = tickers[0]
            for dt, row in raw.iterrows():
                rows.append(
                    {
                        "ticker": ticker,
                        "date": pd.Timestamp(dt).date(),
                        "open": _safe_float(row.get("Open")),
                        "high": _safe_float(row.get("High")),
                        "low": _safe_float(row.get("Low")),
                        "close": _safe_float(row.get("Close")),
                        "adj_close": _safe_float(row.get("Adj Close")),
                        "volume": _safe_int(row.get("Volume")),
                    }
                )
        else:
            for ticker in tickers:
                try:
                    sub = raw[ticker] if ticker in raw.columns.get_level_values(0) else None
                except (KeyError, TypeError):
                    sub = None
                if sub is None or sub.empty:
                    continue
                for dt, row in sub.iterrows():
                    rows.append(
                        {
                            "ticker": ticker,
                            "date": pd.Timestamp(dt).date(),
                            "open": _safe_float(row.get("Open")),
                            "high": _safe_float(row.get("High")),
                            "low": _safe_float(row.get("Low")),
                            "close": _safe_float(row.get("Close")),
                            "adj_close": _safe_float(row.get("Adj Close")),
                            "volume": _safe_int(row.get("Volume")),
                        }
                    )

        return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Fama-French 5-Factor daily
# ---------------------------------------------------------------------------

class FamaFrenchClient:
    """Download Fama-French 5-factor daily returns from Ken French's
    data library via pandas-datareader.
    """

    FF_DATASET = "F-F_Research_Data_5_Factors_2x3_daily"

    def __init__(self, db_manager=None):
        self.db = db_manager

    def download(
        self, start: str = "2022-01-01", end: Optional[str] = None
    ) -> pd.DataFrame:
        """Fetch FF5 daily factors.

        Returns
        -------
        pd.DataFrame
            Columns: date, mkt_rf, smb, hml, rmw, cma, rf (all in decimal)
        """
        import pandas_datareader.data as web

        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")

        logger.info("Downloading Fama-French 5 factors (%s → %s)", start, end)

        try:
            ds = web.DataReader(
                self.FF_DATASET, "famafrench", start=start, end=end
            )
            df = ds[0]  # daily table
        except Exception as exc:
            logger.error("Failed to download FF5: %s", exc)
            return pd.DataFrame()

        # Columns come as 'Mkt-RF', 'SMB', etc.  Values are in percent.
        df = df.rename(
            columns={
                "Mkt-RF": "mkt_rf",
                "SMB": "smb",
                "HML": "hml",
                "RMW": "rmw",
                "CMA": "cma",
                "RF": "rf",
            }
        )
        df = df / 100.0  # percent → decimal
        df.index.name = "date"
        df = df.reset_index()
        df["date"] = pd.to_datetime(df["date"]).dt.date

        if self.db is not None:
            self.db.bulk_insert("ff_factors_daily", df)
            logger.info("Inserted %d FF5 rows", len(df))

        return df


# ---------------------------------------------------------------------------
# FRED macro series
# ---------------------------------------------------------------------------

class FREDClient:
    """Download key macro series from FRED (free API key required)."""

    # Default series used by Engine 2 (Kalman RBSA)
    DEFAULT_SERIES = {
        "DGS10": "treasury_10y",       # 10-Year Treasury yield
        "T10Y2Y": "yield_curve_2s10s", # 2s10s spread
        "VIXCLS": "vix",               # VIX close
        "DTWEXBGS": "usd_index",       # Trade-weighted USD
    }

    def __init__(self, api_key: str = "", db_manager=None):
        self.api_key = api_key
        self.db = db_manager

    def download(
        self,
        series_ids: Optional[dict[str, str]] = None,
        start: str = "2022-01-01",
    ) -> pd.DataFrame:
        """Download multiple FRED series, merge into single DataFrame.

        Parameters
        ----------
        series_ids : dict
            {FRED_ID: friendly_column_name}
        """
        if series_ids is None:
            series_ids = self.DEFAULT_SERIES

        if not self.api_key:
            logger.warning(
                "FRED API key not set – skipping FRED download.  "
                "Set FRED_API_KEY in config/settings.py"
            )
            return pd.DataFrame()

        from fredapi import Fred

        fred = Fred(api_key=self.api_key)
        frames: list[pd.DataFrame] = []

        for series_id, col_name in series_ids.items():
            try:
                s = fred.get_series(series_id, observation_start=start)
                s.name = col_name
                frames.append(s.to_frame())
            except Exception as exc:
                logger.warning("FRED series %s failed: %s", series_id, exc)

        if not frames:
            return pd.DataFrame()

        merged = pd.concat(frames, axis=1)
        merged.index.name = "date"
        merged = merged.reset_index()
        merged["date"] = pd.to_datetime(merged["date"]).dt.date

        logger.info("Downloaded %d FRED rows across %d series", len(merged), len(frames))
        return merged


# ---------------------------------------------------------------------------
# Public hedge-fund vehicle NAV collector
# ---------------------------------------------------------------------------

class PublicVehicleNAVCollector:
    """Download weekly NAV proxies for listed hedge-fund vehicles
    (PSH.AS, TPNT.L, EMG.L, GLRE) using yfinance.

    Used for Kalman filter ground-truth calibration (Engine 2).
    """

    VEHICLES = {
        "Pershing Square": "PSH.AS",
        "Third Point": "TPNT.L",
        "Man Group": "EMG.L",
        "Greenlight Capital": "GLRE",
    }

    def __init__(self, db_manager=None):
        self.db = db_manager

    def download_all(self, start: str = "2022-01-01") -> pd.DataFrame:
        """Download weekly adjusted-close for all public vehicles."""
        import yfinance as yf

        all_rows: list[dict] = []

        for fund_group, ticker in self.VEHICLES.items():
            logger.info("Downloading NAV proxy: %s (%s)", fund_group, ticker)
            try:
                data = yf.download(
                    ticker,
                    start=start,
                    interval="1wk",
                    auto_adjust=True,
                    progress=False,
                )
                if data.empty:
                    logger.warning("No data for %s", ticker)
                    continue

                for dt, row in data.iterrows():
                    all_rows.append(
                        {
                            "fund_group": fund_group,
                            "date": pd.Timestamp(dt).date(),
                            "nav": _safe_float(row.get("Close")),
                            "source": f"yfinance:{ticker}",
                        }
                    )
            except Exception as exc:
                logger.warning("NAV download failed for %s: %s", ticker, exc)

        df = pd.DataFrame(all_rows)

        if self.db is not None and not df.empty:
            self.db.bulk_insert("fund_nav", df)
            logger.info("Inserted %d NAV rows", len(df))

        return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(v) -> Optional[float]:
    """Convert to float, returning None on failure."""
    try:
        f = float(v)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _safe_int(v) -> Optional[int]:
    try:
        f = float(v)
        return None if np.isnan(f) else int(f)
    except (TypeError, ValueError):
        return None
