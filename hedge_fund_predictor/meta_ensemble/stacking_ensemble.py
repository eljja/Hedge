"""
Meta-Ensemble Stacking Model & Confidence Scorer.

Meta-layer of the predictor architecture:
  - Takes base outputs from all 11 Engines.
  - Fits a Ridge regression meta-model (or LightGBM fallback) to produce final position & sector estimates.
  - Computes final 0-100 Confidence Score based on:
      * Recency score
      * Event verification boost
      * Network herding strength
      * Restatement Return Gap skill bonus
      * Multi-timeframe consistency
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Computes final 0-100 confidence score for position predictions."""

    @staticmethod
    def calculate_confidence(
        recency_days: int,
        has_13d_or_event: bool = False,
        herding_prob: float = 0.0,
        skill_multiplier: float = 1.0,
        multi_channel_count: int = 1,
    ) -> float:
        """Calculate composite 0-100 confidence score based on v6 formula.

        Score = w1*S_recency + w2*S_signal + w3*S_turnover + w4*S_consensus + w5*S_calib + w6*S_skill + w7*S_multi
        """
        # 1. Recency (0.15)
        s_recency = 100.0 if recency_days <= 45 else (60.0 if recency_days <= 90 else 20.0)

        # 2. Signal (0.25)
        s_signal = 100.0 if has_13d_or_event else 30.0

        # 3. Network (0.15)
        s_network = max(0.0, min(100.0, herding_prob * 100.0))

        # 4. Skill (0.15)
        s_skill = max(20.0, min(100.0, skill_multiplier * 50.0))

        # 5. Multi-channel consistency (0.30)
        s_multi = 90.0 if multi_channel_count >= 3 else (60.0 if multi_channel_count == 2 else 30.0)

        composite = (
            0.15 * s_recency +
            0.25 * s_signal +
            0.15 * s_network +
            0.15 * s_skill +
            0.30 * s_multi
        )

        return round(float(np.clip(composite, 0.0, 100.0)), 1)


class StackingMetaEnsemble:
    """Meta-layer Stacking Model for combining all 11 Engines."""

    def __init__(self, db_manager=None, alpha: float = 1.0):
        self.db = db_manager
        self.meta_model = Ridge(alpha=alpha, positive=True)
        self.is_fitted = False

    def predict_final_weights(
        self,
        engine_predictions_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Combine predictions from multiple engines into final sector/stock weights.

        Parameters
        ----------
        engine_predictions_df : pd.DataFrame
            Columns: [target, E1_weight, E2_weight, E3_weight, E4_weight, E7_weight, E9_weight, ...]

        Returns
        -------
        pd.DataFrame
            Columns: [target, final_weight, confidence_score, display_rating]
        """
        if engine_predictions_df.empty:
            return pd.DataFrame()

        df = engine_predictions_df.copy()

        # Identify feature columns (engine weights)
        feature_cols = [c for c in df.columns if c.startswith("E") and "weight" in c]

        if not feature_cols:
            # Fallback if unformatted: take mean of numeric columns
            df["final_weight"] = df.select_dtypes(include=[np.number]).mean(axis=1)
        else:
            if not self.is_fitted:
                # Default equal weighting across engines
                df["final_weight"] = df[feature_cols].mean(axis=1)
            else:
                X = df[feature_cols].fillna(0.0).values
                df["final_weight"] = self.meta_model.predict(X)

        # Normalize weights to sum to 1.0
        tot = df["final_weight"].sum()
        if tot > 0:
            df["final_weight"] = df["final_weight"] / tot

        # Compute confidence & ratings
        conf_scorer = ConfidenceScorer()
        confidences = []
        ratings = []

        for _, row in df.iterrows():
            has_event = bool(row.get("E3_weight", 0) > 0.5)
            herding = float(row.get("E9_weight", 0.0) or 0.0)
            skill = float(row.get("skill_mult", 1.0) or 1.0)
            n_ch = int(row.get("n_channels", 1) or 1)

            conf = conf_scorer.calculate_confidence(
                recency_days=45,
                has_13d_or_event=has_event,
                herding_prob=herding,
                skill_multiplier=skill,
                multi_channel_count=n_ch,
            )

            confidences.append(conf)

            if conf >= 90.0:
                rating = "CONFIRMED"
            elif conf >= 70.0:
                rating = "HIGH"
            elif conf >= 50.0:
                rating = "MODERATE"
            else:
                rating = "LOW"

            ratings.append(rating)

        df["confidence_score"] = confidences
        df["display_rating"] = ratings

        logger.info("Meta-Ensemble produced final weights for %d targets", len(df))
        return df.sort_values("final_weight", ascending=False)
