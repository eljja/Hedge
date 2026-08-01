"""
Ground-truth calibration module for Engine 2 (Kalman RBSA).

Uses listed hedge fund vehicles (Pershing Square - PSH.AS, Third Point - TPNT.L)
whose NAVs are published weekly to optimize measurement noise (R) and
process noise (Q) parameters.
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from hedge_fund_predictor.analytics_engine.E2_kalman_rbsa import KalmanRBSAEngine

logger = logging.getLogger(__name__)


class GroundTruthCalibrator:
    """Calibrates Kalman Filter noise parameters R and Q against public vehicle NAVs."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def calibrate_fund(
        self,
        fund_group: str = "Pershing Square",
        vehicle_ticker: str = "PSH.AS",
    ) -> Tuple[float, float]:
        """Find optimal (R, Q) variance values that minimize 1-step ahead prediction error.

        Returns
        -------
        Tuple[float, float]
            (optimal_R, optimal_Q)
        """
        if self.db is None:
            logger.error("No database manager provided for calibration")
            return 1e-4, 1e-5

        # Fetch NAV & Factor data
        nav_df = self.db.query(
            "SELECT date, nav FROM fund_nav WHERE fund_group = ? ORDER BY date",
            [fund_group],
        )

        etf_df = self.db.query("SELECT * FROM sector_etf_returns ORDER BY date")

        if nav_df.empty or etf_df.empty or len(nav_df) < 15:
            logger.warning("Insufficient data for calibration of %s, using defaults", fund_group)
            return 1e-4, 1e-5

        nav_df["date"] = pd.to_datetime(nav_df["date"])
        etf_df["date"] = pd.to_datetime(etf_df["date"])

        merged = pd.merge(nav_df, etf_df, on="date").sort_values("date").dropna()
        if len(merged) < 15:
            return 1e-4, 1e-5

        fund_returns = merged["nav"].pct_change().dropna()
        factor_returns = merged.drop(columns=["date", "nav", "fund_group"], errors="ignore").iloc[1:]

        # Objective function: Root Mean Squared Error (RMSE) of 1-step ahead prediction
        def objective(params):
            log_r, log_q = params
            r_val = 10**log_r
            q_val = 10**log_q

            engine = KalmanRBSAEngine(r_variance=r_val, q_variance=q_val)
            betas = engine.estimate_exposures(fund_returns, factor_returns)

            if betas.empty:
                return 1e6

            # Compute predicted vs actual returns
            factors = factor_returns.values
            actuals = fund_returns.values

            pred_returns = np.sum(betas.drop(columns=["engine"]).values * factors, axis=1)
            rmse = np.sqrt(np.mean((actuals - pred_returns) ** 2))
            return rmse

        res = minimize(
            objective,
            x0=[-4.0, -5.0],  # R=1e-4, Q=1e-5
            bounds=[(-6.0, -1.0), (-7.0, -2.0)],
            method="L-BFGS-B",
        )

        opt_r = float(10 ** res.x[0])
        opt_q = float(10 ** res.x[1])

        logger.info(
            "Calibration successful for %s (%s): optimal R=%.2e, Q=%.2e (RMSE=%.4f)",
            fund_group,
            vehicle_ticker,
            opt_r,
            opt_q,
            res.fun,
        )

        return opt_r, opt_q
