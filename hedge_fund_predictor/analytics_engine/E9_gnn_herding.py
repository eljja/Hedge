"""
Engine 9: Graph Co-Holding & Director Overlap Herding Simulator.

Engine 9 in v6 architecture.

Constructs a fund-fund graph where edge weights represent portfolio similarity
and director overlap. Simulates message passing: when fund A buys a stock (e.g. 13D),
herding probabilities propagate to connected funds B and C before their 13Fs are published.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class GNNHerdingEngine:
    """Engine 9: Graph Herding Signal Propagation Engine."""

    def __init__(self, db_manager=None, decay_lambda: float = 0.85):
        self.db = db_manager
        self.decay_lambda = decay_lambda

    def propagate_herding_signal(
        self,
        adj_matrix: pd.DataFrame,
        initial_signals: dict[str, float],
        n_steps: int = 2,
    ) -> dict[str, float]:
        """Simulate GNN Message Passing over fund graph.

        Parameters
        ----------
        adj_matrix : pd.DataFrame
            Symmetric N x N matrix of fund similarities (0.0 to 1.0).
        initial_signals : dict
            Mapping of fund_id -> initial buy signal (0.0 to 1.0).
        n_steps : int
            Number of message passing iterations.

        Returns
        -------
        dict
            Mapping of fund_id -> propagated buy probability.
        """
        funds = adj_matrix.index.tolist()
        n = len(funds)
        if n == 0:
            return {}

        # Row-normalize adjacency matrix
        A = adj_matrix.values.copy()
        np.fill_diagonal(A, 0.0)  # No self-loops for propagation
        row_sums = A.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        A_norm = A / row_sums

        # Vectorize initial signals
        h = np.array([initial_signals.get(f, 0.0) for f in funds], dtype=float)

        for step in range(n_steps):
            # Message passing: h_{t+1} = lambda * (A_norm @ h_t) + (1 - lambda) * h_0
            h = self.decay_lambda * (A_norm @ h) + (1.0 - self.decay_lambda) * h

        res = {funds[i]: round(float(h[i]), 4) for i in range(n)}
        logger.info("GNN Herding propagated over %d steps for %d funds", n_steps, n)
        return res
