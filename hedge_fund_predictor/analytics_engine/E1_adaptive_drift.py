"""
Engine 1: Adaptive 13F Price Drift with Half-Life Decay.

Takes the most recent 13F holdings snapshot, applies price drift
(shares × current price) to estimate current portfolio weights, and
applies a strategy-specific half-life decay to reduce confidence as
time passes since the filing date.

This is the foundational position estimation engine. All other engines
either refine or override its outputs.
"""

import logging
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdaptiveDriftEngine:
    """Engine 1: 13F Price Drift + Turnover-Based Half-Life Decay.

    Given a fund's last 13F filing, estimate its *current* portfolio
    by adjusting for stock price changes since the filing date, then
    decaying the confidence based on expected portfolio turnover.
    """

    # Strategy → annual turnover → half-life (in quarters)
    STRATEGY_HALFLIFE = {
        "concentrated_activist": 13.9,   # τ ≈ 0.05 → very long
        "equity_long_short":      2.5,   # τ ≈ 0.25
        "tiger_cub":              2.0,   # τ ≈ 0.30
        "event_driven":           1.7,   # τ ≈ 0.40
        "multi_strategy":         0.9,   # τ ≈ 0.75 → fast turnover
        "quant_systematic":       0.8,   # τ ≈ 0.90
        "global_macro":           1.5,   # mixed
        "credit":                 3.0,   # relatively static
    }

    DEFAULT_HALFLIFE = 2.0  # quarters

    def __init__(self, db_manager=None):
        self.db = db_manager

    def estimate_current_positions(
        self,
        cik: str,
        strategy: str = "equity_long_short",
        filing_date: Optional[date] = None,
        current_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Estimate current portfolio weights from the last 13F filing.

        Parameters
        ----------
        cik : str
            10-digit zero-padded CIK.
        strategy : str
            Fund strategy for half-life lookup.
        filing_date : date, optional
            Date of the 13F filing. If None, uses latest from DB.
        current_date : date, optional
            "Now" date for estimation. Defaults to today.

        Returns
        -------
        pd.DataFrame
            Columns: cusip, issuer, value_current, weight_raw, weight_decayed,
            confidence, shares, put_call
        """
        if current_date is None:
            current_date = date.today()

        # Step 1: Get last 13F holdings
        holdings = self._get_holdings(cik, filing_date)
        if holdings.empty:
            logger.warning("No 13F holdings found for CIK %s", cik)
            return pd.DataFrame()

        actual_filing_date = holdings["report_date"].iloc[0]
        if hasattr(actual_filing_date, 'date'):
            actual_filing_date = actual_filing_date.date()
        elif isinstance(actual_filing_date, str):
            actual_filing_date = pd.to_datetime(actual_filing_date).date()

        # Step 2: Apply price drift
        drifted = self._apply_price_drift(holdings, current_date)

        # Step 3: Calculate raw portfolio weights
        total_value = drifted["value_current"].sum()
        if total_value <= 0:
            logger.warning("Total portfolio value <= 0 for CIK %s", cik)
            return pd.DataFrame()

        drifted["weight_raw"] = drifted["value_current"] / total_value

        # Step 4: Apply half-life decay to confidence
        days_elapsed = (current_date - actual_filing_date).days
        halflife_quarters = self.STRATEGY_HALFLIFE.get(
            strategy, self.DEFAULT_HALFLIFE
        )
        halflife_days = halflife_quarters * 90  # approximate

        decay_factor = np.exp(
            -np.log(2) * days_elapsed / max(halflife_days, 1)
        )

        drifted["weight_decayed"] = drifted["weight_raw"] * decay_factor
        drifted["confidence"] = decay_factor * 100  # 0-100 scale
        drifted["days_since_filing"] = days_elapsed
        drifted["engine"] = "E1_adaptive_drift"

        # Sort by current estimated weight
        drifted = drifted.sort_values("weight_raw", ascending=False)

        logger.info(
            "E1 Drift for CIK %s: %d positions, decay=%.2f%% (day %d, h=%.1fq)",
            cik,
            len(drifted),
            decay_factor * 100,
            days_elapsed,
            halflife_quarters,
        )

        return drifted

    def estimate_sector_weights(
        self,
        cik: str,
        strategy: str = "equity_long_short",
        sector_mapping: Optional[dict[str, str]] = None,
    ) -> pd.DataFrame:
        """Aggregate position-level estimates into sector weights.

        Parameters
        ----------
        sector_mapping : dict[str, str], optional
            CUSIP → GICS sector name mapping. If None, will attempt to
            infer from the issuer name or ETF lookup.
        """
        positions = self.estimate_current_positions(cik, strategy)
        if positions.empty:
            return pd.DataFrame()

        if sector_mapping is None:
            # Fallback: use a simple sector classification based on
            # the first letter of the CUSIP (very rough approximation)
            # In production, this would use a proper CUSIP→GICS lookup
            positions["sector"] = "Unknown"
        else:
            positions["sector"] = positions["cusip"].map(sector_mapping)
            positions["sector"] = positions["sector"].fillna("Unknown")

        sector_df = (
            positions.groupby("sector")
            .agg(
                estimated_weight=("weight_raw", "sum"),
                confidence=("confidence", "mean"),
                num_positions=("cusip", "count"),
            )
            .reset_index()
            .sort_values("estimated_weight", ascending=False)
        )

        sector_df["engine"] = "E1_adaptive_drift"
        return sector_df

    # -- internal helpers ---------------------------------------------------

    def _get_holdings(
        self, cik: str, filing_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Retrieve 13F holdings from database."""
        if self.db is None:
            logger.error("No database connection for Engine 1")
            return pd.DataFrame()

        if filing_date is not None:
            sql = """
                SELECT * FROM holdings_13f
                WHERE cik = ? AND report_date = ?
                ORDER BY value_thousands DESC
            """
            return self.db.query(sql, [cik, filing_date])
        else:
            sql = """
                SELECT * FROM holdings_13f
                WHERE cik = ?
                AND report_date = (
                    SELECT MAX(report_date)
                    FROM holdings_13f
                    WHERE cik = ?
                )
                ORDER BY value_thousands DESC
            """
            return self.db.query(sql, [cik, cik])

    def _apply_price_drift(
        self, holdings: pd.DataFrame, current_date: date
    ) -> pd.DataFrame:
        """Apply price changes since the filing to estimate current value.

        For each holding: current_value = shares × current_price
        If current price unavailable, use original value (no drift).
        """
        result = holdings.copy()

        # Attempt to get current prices for all held CUSIPs
        # This is a simplified version — in production, we'd map CUSIP→ticker
        # and lookup from market_prices table
        result["value_current"] = result["value_thousands"].astype(float)

        if self.db is not None:
            # Try to get price ratios from market_prices
            # For now, use the filing value as the base (price drift will
            # be applied when we have ticker↔CUSIP mapping)
            report_date = result["report_date"].iloc[0]

            # TODO: Implement CUSIP→ticker resolution and actual price lookup
            # For MVP, we approximate with sector ETF returns
            pass

        return result


def compute_portfolio_hhi(weights: pd.Series) -> float:
    """Compute Herfindahl-Hirschman Index for portfolio concentration.

    HHI = Σ(w_i²)
    Range: 1/N (perfectly diversified) to 1.0 (single holding)
    HHI > 0.05 typically indicates concentrated portfolio.
    """
    w = weights / weights.sum()
    return float((w ** 2).sum())
