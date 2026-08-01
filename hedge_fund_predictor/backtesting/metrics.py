"""
Extended Validation Metrics & Backtesting Module.

Computes:
  - Sector MAE (Mean Absolute Error)
  - Top-3 Sector Hit Rate
  - Top-10 Stock Recall
  - Spearman Rank Correlation
  - Brier Score (Confidence Calibration)
  - Information Coefficient (IC)
  - Decay Accuracy Curve over time
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)


def compute_sector_mae(pred_weights: pd.Series, actual_weights: pd.Series) -> float:
    """Mean Absolute Error across 11 GICS sectors."""
    aligned = pd.concat([pred_weights.rename("pred"), actual_weights.rename("actual")], axis=1).fillna(0.0)
    mae = float(np.mean(np.abs(aligned["pred"] - aligned["actual"])))
    return round(mae, 4)


def compute_top_k_recall(pred_top: list[str], actual_top: list[str]) -> float:
    """Top-K Recall: |Pred_K ∩ Actual_K| / K."""
    if not actual_top or not pred_top:
        return 0.0
    k = len(actual_top)
    intersection = set(pred_top[:k]).intersection(set(actual_top))
    return round(len(intersection) / float(k), 4)


def compute_spearman_rank_ic(pred_weights: pd.Series, actual_weights: pd.Series) -> float:
    """Spearman Rank Correlation / Information Coefficient (IC)."""
    aligned = pd.concat([pred_weights.rename("pred"), actual_weights.rename("actual")], axis=1).fillna(0.0)
    if len(aligned) < 3:
        return 0.0
    rho, _ = spearmanr(aligned["pred"], aligned["actual"])
    return round(float(rho) if not np.isnan(rho) else 0.0, 4)


def compute_brier_score(pred_probabilities: np.ndarray, actual_binary_outcomes: np.ndarray) -> float:
    """Brier Score for probability calibration: (1/N) * sum((p_i - o_i)^2)."""
    if len(pred_probabilities) == 0:
        return 0.0
    brier = float(np.mean((pred_probabilities - actual_binary_outcomes) ** 2))
    return round(brier, 4)
