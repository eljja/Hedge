"""
Engine 4: 13F Options Black-Scholes Delta Conversion.

Converts 13F-reported option positions (PUT / CALL) into underlying equity-equivalent
delta exposures.

Formula:
  Delta_Call = N(d1)
  Delta_Put  = N(d1) - 1
  d1 = [ln(S/K) + (r + 0.5 * sigma^2)*T] / (sigma * sqrt(T))

When strike K or expiry T are not reported in 13F, applies ATM (At-The-Money: S=K)
and 45-day default expiry assumptions.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import norm

logger = logging.getLogger(__name__)


def bs_delta(
    s: float,
    k: float,
    t: float,
    r: float = 0.04,
    sigma: float = 0.25,
    option_type: str = "call",
) -> float:
    """Calculate Black-Scholes Delta for Call or Put options.

    Parameters
    ----------
    s : float
        Underlying stock price ($).
    k : float
        Option strike price ($).
    t : float
        Time to expiration in years (e.g. 45/365).
    r : float
        Risk-free interest rate (annualized). Default 4.0%.
    sigma : float
        Implied volatility (annualized). Default 25%.
    option_type : str
        'call' or 'put'.

    Returns
    -------
    float
        Delta value between 0 and 1 for call, -1 and 0 for put.
    """
    if t <= 0 or s <= 0 or k <= 0 or sigma <= 0:
        if option_type.lower() == "call":
            return 1.0 if s >= k else 0.0
        else:
            return -1.0 if s < k else 0.0

    d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))

    if option_type.lower() == "call":
        return float(norm.cdf(d1))
    else:
        return float(norm.cdf(d1) - 1.0)


class OptionsDeltaEngine:
    """Engine 4: Option Delta Transformation for 13F Holdings."""

    def __init__(self, db_manager=None, default_days_to_exp: int = 45, default_iv: float = 0.25):
        self.db = db_manager
        self.default_t = default_days_to_exp / 365.0
        self.default_iv = default_iv

    def convert_options_to_delta_equivalent(
        self,
        holdings_df: pd.DataFrame,
        r: float = 0.04,
    ) -> pd.DataFrame:
        """Convert raw 13F options positions to delta-adjusted equity equivalent shares.

        Parameters
        ----------
        holdings_df : pd.DataFrame
            DataFrame containing holdings with columns:
            [cusip, issuer, value_thousands, shares_or_amount, put_call]

        Returns
        -------
        pd.DataFrame
            Original DataFrame with added columns:
            [delta, delta_equivalent_shares, delta_equivalent_value, exposure_type]
        """
        if holdings_df.empty:
            return holdings_df

        df = holdings_df.copy()

        deltas = []
        delta_shares = []
        delta_values = []
        exposure_types = []

        for _, row in df.iterrows():
            put_call = str(row.get("put_call", "NONE")).upper()
            shares = float(row.get("shares_or_amount", 0) or 0)
            val = float(row.get("value_thousands", 0) or 0)

            if put_call == "NONE" or pd.isna(put_call) or put_call == "":
                # Pure equity position
                d = 1.0
                d_share = shares
                d_val = val
                exp_type = "LONG_EQUITY"
            else:
                # ATM Assumption: S = K => ln(S/K) = 0
                opt_type = "call" if "CALL" in put_call else "put"
                d = bs_delta(
                    s=100.0,
                    k=100.0,
                    t=self.default_t,
                    r=r,
                    sigma=self.default_iv,
                    option_type=opt_type,
                )

                d_share = shares * d
                d_val = val * abs(d)
                exp_type = f"OPTION_{opt_type.upper()}_DELTA"

            deltas.append(d)
            delta_shares.append(d_share)
            delta_values.append(d_val)
            exposure_types.append(exp_type)

        df["delta"] = deltas
        df["delta_equivalent_shares"] = delta_shares
        df["delta_equivalent_value"] = delta_values
        df["exposure_type"] = exposure_types
        df["engine"] = "E4_options_delta"

        logger.info(
            "E4 Delta conversion complete: %d rows processed (%d options converted)",
            len(df),
            sum(1 for t in exposure_types if "OPTION" in t),
        )

        return df
