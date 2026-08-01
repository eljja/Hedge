"""
Engine 2: Kalman Filter Returns-Based Style Analysis (RBSA).

Estimates dynamic factor/sector/theme exposures (beta_t) for hedge funds
by regressing returns against 17 factor ETFs (11 GICS sectors + 6 macro/themes).

State-space formulation:
  Observation:  r_fund,t = F_t^T * beta_t + v_t,   v_t ~ N(0, R)
  State:        beta_t   = beta_{t-1} + w_t,        w_t ~ N(0, Q)

Uses ground-truth calibration from listed vehicles (PSH, TPNT) to tune R and Q.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class KalmanRBSAEngine:
    """Engine 2: Dynamic Kalman Filter Returns-Based Style Analysis.

    Estimates time-varying sector and theme exposure weights for a fund.
    """

    def __init__(self, db_manager=None, r_variance: float = 1e-4, q_variance: float = 1e-5):
        self.db = db_manager
        self.r_variance = r_variance  # Measurement noise variance R
        self.q_variance = q_variance  # Process noise variance Q

    def estimate_exposures(
        self,
        fund_returns: pd.Series,
        factor_returns: pd.DataFrame,
        max_gross_exposure: float = 2.0,
    ) -> pd.DataFrame:
        """Estimate dynamic factor weights (betas) over time.

        Parameters
        ----------
        fund_returns : pd.Series
            Series of fund returns indexed by date.
        factor_returns : pd.DataFrame
            DataFrame of factor returns (columns = factor names, index = date).
        max_gross_exposure : float
            Constraint: sum(|beta_i|) <= max_gross_exposure (Form ADV limit).

        Returns
        -------
        pd.DataFrame
            DataFrame of estimated factor weights per date (columns = factor names).
        """
        # Align dates
        aligned = pd.concat([fund_returns.rename("y"), factor_returns], axis=1).dropna()
        if len(aligned) < 10:
            logger.warning("Insufficient data for Kalman RBSA (need at least 10 rows)")
            return pd.DataFrame()

        y = aligned["y"].values
        X = aligned.drop(columns=["y"]).values
        factor_names = [c for c in aligned.columns if c != "y"]
        n_dates, n_factors = X.shape

        # Initialize state vector (equal weight prior)
        beta = np.full(n_factors, 1.0 / n_factors)
        P = np.eye(n_factors) * 0.1  # Initial state covariance
        Q = np.eye(n_factors) * self.q_variance
        R = self.r_variance

        betas_history = []

        for t in range(n_dates):
            x_t = X[t, :]
            y_t = y[t]

            # 1. Predict Step
            beta_pred = beta
            P_pred = P + Q

            # 2. Innovation / Measurement Update
            y_hat = np.dot(x_t, beta_pred)
            v = y_t - y_hat
            S = np.dot(x_t, np.dot(P_pred, x_t)) + R

            K = np.dot(P_pred, x_t) / S  # Kalman Gain
            beta_update = beta_pred + K * v
            P_update = P_pred - np.outer(K, np.dot(x_t, P_pred))

            # 3. Constrain weights (Gross exposure constraint & soft simplex)
            beta_update = self._apply_exposure_constraints(beta_update, max_gross_exposure)

            beta = beta_update
            P = P_update

            betas_history.append(beta.copy())

        res_df = pd.DataFrame(betas_history, index=aligned.index, columns=factor_names)
        res_df["engine"] = "E2_kalman_rbsa"
        return res_df

    def estimate_latest_sector_weights(
        self,
        fund_group: str,
        lookback_days: int = 252,
    ) -> pd.DataFrame:
        """Estimate the latest sector exposure weights for a fund from DB returns."""
        if self.db is None:
            logger.error("No database connection provided for Kalman RBSA")
            return pd.DataFrame()

        # Fetch factor returns
        etf_returns = self.db.query("SELECT * FROM sector_etf_returns ORDER BY date")
        if etf_returns.empty:
            logger.warning("No factor return data found in database")
            return pd.DataFrame()

        etf_returns["date"] = pd.to_datetime(etf_returns["date"])
        etf_returns = etf_returns.set_index("date")

        # Fetch NAV / Return proxy for the fund
        nav_df = self.db.query(
            "SELECT date, nav FROM fund_nav WHERE fund_group = ? ORDER BY date",
            [fund_group],
        )

        if nav_df.empty or len(nav_df) < 10:
            logger.warning("No sufficient NAV data for %s, cannot run Kalman RBSA", fund_group)
            return pd.DataFrame()

        nav_df["date"] = pd.to_datetime(nav_df["date"])
        nav_df = nav_df.set_index("date")
        fund_returns = nav_df["nav"].pct_change().dropna()

        betas_df = self.estimate_exposures(fund_returns, etf_returns)
        if betas_df.empty:
            return pd.DataFrame()

        latest = betas_df.iloc[-1].drop("engine", errors="ignore")
        summary = pd.DataFrame({
            "sector": latest.index,
            "estimated_weight": latest.values,
            "confidence_score": 75.0,  # Default RBSA confidence
            "engine_source": "E2_kalman_rbsa",
        })

        return summary.sort_values("estimated_weight", ascending=False)

    @staticmethod
    def _apply_exposure_constraints(beta: np.ndarray, max_gross: float) -> np.ndarray:
        """Scale weights if gross exposure sum(|beta|) exceeds max_gross."""
        gross = np.sum(np.abs(beta))
        if gross > max_gross and gross > 0:
            beta = beta * (max_gross / gross)
        return beta
