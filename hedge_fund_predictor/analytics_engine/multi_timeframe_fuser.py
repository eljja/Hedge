"""
Multi-Timeframe Signal Fusion Engine.

Fuses signals across 5 time horizons with channel-specific half-life decays:
  1. Realtime (13D/Form4/13G)   -> Half-life: infinity (legal snapshot)
  2. Daily (yfinance/OCC OI)    -> Half-life: 7 days
  3. Weekly (CFTC COT/NAV)      -> Half-life: 14 days
  4. Monthly (N-PORT)           -> Half-life: 60 days
  5. Quarterly (13F DERA)       -> Half-life: turnover-adaptive (90-360 days)
"""

import logging
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default half-lives in days
CHANNEL_HALF_LIVES = {
    "realtime_13d": 3650.0,  # ~infinity (permanent until modified)
    "occ_options": 7.0,
    "cftc_cot": 14.0,
    "nport_monthly": 60.0,
    "13f_quarterly": 90.0,
    "npx_annual": 180.0,
}


class MultiTimeframeFuser:
    """Combines heterogeneous signals across time resolutions."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def fuse_position_estimates(
        self,
        estimates_by_channel: dict[str, pd.DataFrame],
        current_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Fuse sector/stock estimation dataframes from multiple engines.

        Parameters
        ----------
        estimates_by_channel : dict[str, pd.DataFrame]
            Map of channel_name -> DataFrame with columns [sector/ticker, estimated_weight, confidence_score, date]

        Returns
        -------
        pd.DataFrame
            Fused position estimates with decayed, weighted confidence scores.
        """
        if current_date is None:
            current_date = date.today()

        fused_records = []

        for channel, df in estimates_by_channel.items():
            if df.empty:
                continue

            half_life = CHANNEL_HALF_LIVES.get(channel, 30.0)

            for _, row in df.iterrows():
                target = row.get("ticker") or row.get("sector") or "UNKNOWN"
                weight = float(row.get("estimated_weight", 0.0) or 0.0)
                conf = float(row.get("confidence_score", 50.0) or 50.0)

                record_date = row.get("date", current_date)
                if hasattr(record_date, "date"):
                    record_date = record_date.date()
                elif isinstance(record_date, str):
                    record_date = pd.to_datetime(record_date).date()

                days_elapsed = (current_date - record_date).days
                decay_factor = float(np.exp(-np.log(2) * max(0, days_elapsed) / half_life))

                decayed_conf = conf * decay_factor

                fused_records.append({
                    "target": target,
                    "channel": channel,
                    "estimated_weight": weight,
                    "raw_confidence": conf,
                    "decay_factor": round(decay_factor, 3),
                    "decayed_confidence": round(decayed_conf, 2),
                })

        if not fused_records:
            return pd.DataFrame()

        fused_df = pd.DataFrame(fused_records)

        # Aggregate weighted weights per target
        summary = (
            fused_df.groupby("target")
            .apply(
                lambda g: pd.Series({
                    "fused_weight": round(np.average(g["estimated_weight"], weights=np.maximum(1e-3, g["decayed_confidence"])), 4),
                    "total_confidence": round(g["decayed_confidence"].sum(), 2),
                    "n_channels": len(g["channel"].unique()),
                })
            )
            .reset_index()
            .sort_values("fused_weight", ascending=False)
        )

        logger.info("Multi-Timeframe Fuser combined %d signals into %d targets", len(fused_records), len(summary))
        return summary
