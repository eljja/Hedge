"""
Engine 7: CFTC Futures & Commodity Macro Positioning Mapping.

Channel ⑧ / Engine 7 in v6 architecture.

Converts CFTC Commitments of Traders (COT) Leveraged Funds & Managed Money
weekly Z-scores into sector/asset class exposure adjustments for Global Macro
and Systematic CTA hedge funds (Bridgewater, AQR, Man Group, etc.).
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Strategy sensitivity to COT macro positioning
STRATEGY_COT_WEIGHTS = {
    "global_macro": 0.8,
    "quant_systematic": 0.7,
    "multi_strategy": 0.4,
    "equity_long_short": 0.2,
    "concentrated_activist": 0.0,
}


class CFTCPositioningEngine:
    """Engine 7: Macro Futures & Commodities Exposure Mapper."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def get_latest_macro_signals(self) -> pd.DataFrame:
        """Fetch latest COT Z-scores for all tracked contracts from database."""
        if self.db is None:
            logger.error("No database connection for CFTC Positioning Engine")
            return pd.DataFrame()

        sql = """
            SELECT report_date, market_name, contract_type, lev_net, mm_net, z_score
            FROM cftc_cot
            WHERE report_date = (SELECT MAX(report_date) FROM cftc_cot)
            ORDER BY z_score DESC
        """
        return self.db.query(sql)

    def compute_fund_macro_bias(
        self,
        fund_strategy: str = "global_macro",
    ) -> dict[str, float]:
        """Compute estimated macro asset class biases (Z-scores weighted by strategy sensitivity).

        Returns
        -------
        dict
            Mapping of asset/contract name -> tilt score (-3.0 to +3.0)
        """
        cot_df = self.get_latest_macro_signals()
        sensitivity = STRATEGY_COT_WEIGHTS.get(fund_strategy, 0.3)

        if cot_df.empty or sensitivity == 0.0:
            return {}

        biases = {}
        for _, row in cot_df.iterrows():
            market = row["market_name"]
            z = float(row.get("z_score", 0.0) or 0.0)
            biases[market] = round(z * sensitivity, 3)

        logger.info(
            "E7 Macro Bias computed for %s: %d contracts mapped (sensitivity=%.2f)",
            fund_strategy,
            len(biases),
            sensitivity,
        )

        return biases

    def map_cot_to_gics_sectors(
        self,
        fund_strategy: str = "global_macro",
    ) -> pd.DataFrame:
        """Map futures Z-scores to GICS sector tilts.

        E.g. S&P 500 / Nasdaq net long -> XLK, XLY tilt
             Crude oil net long        -> XLE tilt
             Treasury 10Y net short    -> XLF tilt (higher yields)
        """
        biases = self.compute_fund_macro_bias(fund_strategy)
        if not biases:
            return pd.DataFrame()

        sector_tilts = {
            "Information Technology": biases.get("nasdaq", 0.0) * 0.6 + biases.get("sp500", 0.0) * 0.4,
            "Financials": biases.get("sp500", 0.0) * 0.3 - biases.get("treasury_10y", 0.0) * 0.4,
            "Energy": biases.get("crude_oil", 0.0) * 0.8,
            "Materials": biases.get("copper", 0.0) * 0.5 + biases.get("gold", 0.0) * 0.3,
            "Consumer Discretionary": biases.get("sp500", 0.0) * 0.5,
        }

        records = [
            {
                "sector": sec,
                "macro_tilt_zscore": round(val, 3),
                "direction": "LONG" if val > 0.5 else ("SHORT" if val < -0.5 else "NEUTRAL"),
                "engine": "E7_cftc_positioning",
            }
            for sec, val in sector_tilts.items()
        ]

        return pd.DataFrame(records).sort_values("macro_tilt_zscore", ascending=False)
