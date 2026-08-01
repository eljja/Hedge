"""
Engine 5: Conviction-Consensus Cross-Fund Network Analysis.

Analyzes the overlap between hedge fund portfolios to identify:
1. "Hidden Alpha" — stocks with high conviction by few skilled funds
2. "Crowding Risk" — stocks held by too many funds (forced-selling risk)
3. "Herding Propagation" — when fund A buys, similar fund B likely follows

Uses the 2×2 Conviction-Consensus framework:
  - High Conviction + Low Consensus = Hidden Alpha (buy signal)
  - High Conviction + High Consensus = Crowding (risk signal)
  - Low Conviction + Low Consensus = Noise (ignore)
  - Low Conviction + High Consensus = Index-like (sector only)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine

logger = logging.getLogger(__name__)

# Thresholds
CONVICTION_THRESHOLD = 0.075  # 7.5% of portfolio → "Top Conviction"
CONSENSUS_HIGH_THRESHOLD = 0.15  # 15% of funds hold → "High Consensus"


class ConvictionConsensusEngine:
    """Engine 5: Cross-fund conviction and crowding analysis.

    For each stock in the universe, compute:
    - Conviction(i, f) = portfolio weight of stock i in fund f
    - Consensus(i)     = fraction of funds where stock i is top-conviction
    """

    def __init__(self, db_manager=None):
        self.db = db_manager

    def analyze(
        self,
        quarter_date: Optional[str] = None,
        conviction_threshold: float = CONVICTION_THRESHOLD,
        consensus_high_pct: float = CONSENSUS_HIGH_THRESHOLD,
    ) -> dict:
        """Run full conviction-consensus analysis.

        Returns
        -------
        dict with keys:
            - 'stock_scores': DataFrame with conviction/consensus per stock
            - 'fund_similarity': DataFrame with pairwise fund cosine similarity
            - 'crowding_alerts': DataFrame of stocks with high crowding risk
            - 'hidden_alpha': DataFrame of high-conviction, low-consensus stocks
        """
        holdings = self._get_all_holdings(quarter_date)
        if holdings.empty:
            return {"stock_scores": pd.DataFrame(), "fund_similarity": pd.DataFrame(),
                    "crowding_alerts": pd.DataFrame(), "hidden_alpha": pd.DataFrame()}

        # Step 1: Compute portfolio weights per fund
        fund_weights = self._compute_fund_weights(holdings)

        # Step 2: Compute conviction per (stock, fund)
        conviction = self._compute_conviction(fund_weights)

        # Step 3: Compute consensus per stock
        stock_scores = self._compute_consensus(
            conviction, conviction_threshold, consensus_high_pct
        )

        # Step 4: Classify into 2×2 matrix
        stock_scores = self._classify_stocks(stock_scores)

        # Step 5: Compute pairwise fund similarity (cosine)
        fund_similarity = self._compute_fund_similarity(fund_weights)

        # Extract alerts
        crowding = stock_scores[stock_scores["classification"] == "CROWDING"]
        hidden = stock_scores[stock_scores["classification"] == "HIDDEN_ALPHA"]

        logger.info(
            "E5 Analysis: %d stocks scored, %d crowding alerts, %d hidden alpha",
            len(stock_scores), len(crowding), len(hidden),
        )

        return {
            "stock_scores": stock_scores,
            "fund_similarity": fund_similarity,
            "crowding_alerts": crowding,
            "hidden_alpha": hidden,
        }

    def propagate_herding(
        self,
        fund_similarity: pd.DataFrame,
        source_fund: str,
        target_stock: str,
        delta_probability: float,
        alpha: float = 0.5,
    ) -> pd.DataFrame:
        """Propagate a position change signal from one fund to similar funds.

        If fund A buys stock X (confirmed via 13D), estimate the probability
        that fund B (which is similar to A) also bought stock X.

        P_B(X) += α × cos(w_A, w_B) × ΔP_A(X)

        Parameters
        ----------
        fund_similarity : pd.DataFrame
            Pairwise cosine similarity matrix (from analyze()).
        source_fund : str
            CIK of the fund that triggered the signal.
        target_stock : str
            CUSIP or ticker of the stock.
        delta_probability : float
            Change in probability for the source fund (e.g., 0.95 for 13D).
        alpha : float
            Propagation strength (0 = no propagation, 1 = full transfer).

        Returns
        -------
        pd.DataFrame
            Columns: neighbor_fund, propagated_probability, similarity
        """
        if source_fund not in fund_similarity.index:
            return pd.DataFrame()

        similarities = fund_similarity.loc[source_fund].drop(
            source_fund, errors="ignore"
        )

        propagated = pd.DataFrame(
            {
                "neighbor_fund": similarities.index,
                "similarity": similarities.values,
                "propagated_probability": alpha * similarities.values * delta_probability,
            }
        )

        # Only keep meaningful propagation (similarity > 0.3)
        propagated = propagated[propagated["similarity"] > 0.3]
        propagated = propagated.sort_values(
            "propagated_probability", ascending=False
        )

        return propagated

    # -- internal helpers ---------------------------------------------------

    def _get_all_holdings(self, quarter_date: Optional[str]) -> pd.DataFrame:
        """Get all fund holdings for the specified quarter."""
        if self.db is None:
            return pd.DataFrame()

        if quarter_date:
            sql = """
                SELECT cik, cusip, issuer, value_thousands, shares_or_amount, put_call
                FROM holdings_13f
                WHERE report_date = ?
            """
            return self.db.query(sql, [quarter_date])
        else:
            sql = """
                SELECT cik, cusip, issuer, value_thousands, shares_or_amount, put_call
                FROM holdings_13f
                WHERE report_date = (SELECT MAX(report_date) FROM holdings_13f)
            """
            return self.db.query(sql)

    @staticmethod
    def _compute_fund_weights(holdings: pd.DataFrame) -> pd.DataFrame:
        """Compute portfolio weight of each stock within each fund."""
        total_by_fund = holdings.groupby("cik")["value_thousands"].sum()
        holdings = holdings.merge(
            total_by_fund.rename("fund_total"),
            left_on="cik",
            right_index=True,
        )
        holdings["weight"] = holdings["value_thousands"] / holdings["fund_total"]
        return holdings

    @staticmethod
    def _compute_conviction(fund_weights: pd.DataFrame) -> pd.DataFrame:
        """Compute conviction = weight of stock in fund's portfolio."""
        return fund_weights[["cik", "cusip", "issuer", "weight"]].copy()

    @staticmethod
    def _compute_consensus(
        conviction: pd.DataFrame,
        conviction_threshold: float,
        consensus_high_pct: float,
    ) -> pd.DataFrame:
        """Compute consensus: what fraction of funds hold this stock
        at conviction level."""
        n_funds = conviction["cik"].nunique()

        # Flag top-conviction positions
        conviction["is_top_conviction"] = conviction["weight"] >= conviction_threshold

        # Per stock: count funds, count top-conviction funds
        stock_stats = (
            conviction.groupby(["cusip", "issuer"])
            .agg(
                n_holders=("cik", "nunique"),
                n_top_conviction=("is_top_conviction", "sum"),
                avg_weight=("weight", "mean"),
                max_weight=("weight", "max"),
                total_value=("weight", "count"),
            )
            .reset_index()
        )

        stock_stats["consensus"] = stock_stats["n_holders"] / n_funds
        stock_stats["conviction_ratio"] = (
            stock_stats["n_top_conviction"] / stock_stats["n_holders"]
        ).fillna(0)

        # Boolean flags
        stock_stats["is_high_conviction"] = stock_stats["max_weight"] >= conviction_threshold
        stock_stats["is_high_consensus"] = stock_stats["consensus"] >= consensus_high_pct

        return stock_stats

    @staticmethod
    def _classify_stocks(scores: pd.DataFrame) -> pd.DataFrame:
        """Classify stocks into the 2×2 matrix."""
        conditions = [
            scores["is_high_conviction"] & ~scores["is_high_consensus"],
            scores["is_high_conviction"] & scores["is_high_consensus"],
            ~scores["is_high_conviction"] & scores["is_high_consensus"],
            ~scores["is_high_conviction"] & ~scores["is_high_consensus"],
        ]
        choices = ["HIDDEN_ALPHA", "CROWDING", "INDEX_LIKE", "NOISE"]
        scores["classification"] = np.select(conditions, choices, default="NOISE")
        return scores

    @staticmethod
    def _compute_fund_similarity(fund_weights: pd.DataFrame) -> pd.DataFrame:
        """Compute pairwise cosine similarity between fund portfolios.

        Creates a wide matrix (funds × stocks) of weights, then computes
        cosine similarity for every fund pair.
        """
        # Pivot: rows = CIK, columns = CUSIP, values = weight
        pivot = fund_weights.pivot_table(
            index="cik", columns="cusip", values="weight", fill_value=0
        )

        n_funds = len(pivot)
        fund_ids = pivot.index.tolist()
        sim_matrix = np.zeros((n_funds, n_funds))

        for i in range(n_funds):
            for j in range(i, n_funds):
                if i == j:
                    sim_matrix[i][j] = 1.0
                else:
                    sim = 1 - cosine(pivot.iloc[i].values, pivot.iloc[j].values)
                    sim_matrix[i][j] = sim
                    sim_matrix[j][i] = sim

        return pd.DataFrame(sim_matrix, index=fund_ids, columns=fund_ids)
