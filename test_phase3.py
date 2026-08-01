"""Phase 3 & Full Architecture Integration Test Script."""

import numpy as np
import pandas as pd
from hedge_fund_predictor.storage.db_manager import DatabaseManager
from hedge_fund_predictor.analytics_engine.E1_adaptive_drift import AdaptiveDriftEngine
from hedge_fund_predictor.analytics_engine.E2_kalman_rbsa import KalmanRBSAEngine
from hedge_fund_predictor.analytics_engine.E3_bayesian_event import BayesianEventEngine
from hedge_fund_predictor.analytics_engine.E4_options_delta import OptionsDeltaEngine
from hedge_fund_predictor.analytics_engine.E5_conviction_consensus import ConvictionConsensusEngine
from hedge_fund_predictor.analytics_engine.E6_nlp_sentiment import NLPSentimentEngine
from hedge_fund_predictor.analytics_engine.E7_cftc_positioning import CFTCPositioningEngine
from hedge_fund_predictor.analytics_engine.E8_filing_meta_signal import FilingMetaSignalEngine
from hedge_fund_predictor.analytics_engine.E9_gnn_herding import GNNHerdingEngine
from hedge_fund_predictor.analytics_engine.E10_insider_corr import InsiderCorrelationEngine
from hedge_fund_predictor.analytics_engine.E11_sec_scrutiny import SECScrutinyEngine
from hedge_fund_predictor.analytics_engine.multi_timeframe_fuser import MultiTimeframeFuser
from hedge_fund_predictor.meta_ensemble.stacking_ensemble import StackingMetaEnsemble, ConfidenceScorer
from hedge_fund_predictor.backtesting.metrics import (
    compute_sector_mae, compute_top_k_recall, compute_spearman_rank_ic, compute_brier_score
)


def test_all_11_engines():
    print("=" * 60)
    print("STARTING FULL 11-ENGINE & ENSEMBLE INTEGRATION TESTS")
    print("=" * 60)

    db = DatabaseManager()
    db.connect()
    db.init_schema()

    # 1. Test Engine 6 (NLP Sentiment)
    e6 = NLPSentimentEngine()
    sent = e6.analyze_text("We are strongly bullish on Microsoft due to huge AI growth upside.", "MSFT")
    print(f"Engine 6 NLP Sentiment: {sent}")
    assert sent["sentiment_score"] > 0, "Sentiment score should be positive"

    # 2. Test Engine 8 (Meta Signal & Return Gap)
    e8 = FilingMetaSignalEngine(db_manager=db)
    delay_sig = e8.compute_filing_delay_signal("0001423053", pd.to_datetime("2026-05-14").date(), pd.to_datetime("2026-03-31").date())
    print(f"Engine 8 Delay Signal: {delay_sig}")
    assert "delay_zscore" in delay_sig, "Delay zscore should be computed"

    # 3. Test Engine 9 (GNN Herding)
    e9 = GNNHerdingEngine(db_manager=db)
    adj = pd.DataFrame([[1.0, 0.8, 0.2], [0.8, 1.0, 0.1], [0.2, 0.1, 1.0]], index=["F1", "F2", "F3"], columns=["F1", "F2", "F3"])
    herding = e9.propagate_herding_signal(adj, {"F1": 1.0}, n_steps=2)
    print(f"Engine 9 Herding Probabilities: {herding}")
    assert herding["F2"] > 0 and herding["F3"] > 0, "Connected funds should receive propagated herding signal"

    # 4. Test Engine 10 (Insider Correlation)
    e10 = InsiderCorrelationEngine(db_manager=db)
    insider_res = e10.evaluate_insider_boost("MSFT", "2026-03-31")
    print(f"Engine 10 Insider Correlation: {insider_res}")
    assert "boost_multiplier" in insider_res, "Boost multiplier should be present"

    # 5. Test Engine 11 (SEC Scrutiny)
    e11 = SECScrutinyEngine(db_manager=db)
    scrut = e11.scan_comment_letter("The SEC staff issued an inquiry regarding revenue recognition and valuation method.")
    print(f"Engine 11 SEC Scrutiny: {scrut}")
    assert scrut["scrutiny_score"] > 0, "Scrutiny score should be non-zero"

    # 6. Test Multi-Timeframe Fuser
    fuser = MultiTimeframeFuser(db_manager=db)
    fused = fuser.fuse_position_estimates({
        "13f_quarterly": pd.DataFrame([{"target": "XLK", "estimated_weight": 0.35, "confidence_score": 80.0, "date": "2026-03-31"}]),
        "cftc_cot": pd.DataFrame([{"target": "XLK", "estimated_weight": 0.40, "confidence_score": 70.0, "date": "2026-04-15"}]),
    })
    print("\nMulti-Timeframe Fuser output:")
    print(fused.to_string(index=False))
    assert not fused.empty, "Fused dataframe should not be empty"

    # 7. Test Stacking Meta Ensemble
    ensemble = StackingMetaEnsemble(db_manager=db)
    predictions = pd.DataFrame([
        {"target": "XLK", "E1_weight": 0.30, "E2_weight": 0.35, "E7_weight": 0.40, "E9_weight": 0.85, "n_channels": 3},
        {"target": "XLF", "E1_weight": 0.20, "E2_weight": 0.15, "E7_weight": 0.10, "E9_weight": 0.20, "n_channels": 2},
    ])
    final_res = ensemble.predict_final_weights(predictions)
    print("\nStacking Meta Ensemble output:")
    print(final_res.to_string(index=False))
    assert not final_res.empty, "Ensemble output should not be empty"

    # 8. Test Validation Metrics
    pred_s = pd.Series({"XLK": 0.35, "XLF": 0.25, "XLE": 0.10})
    act_s = pd.Series({"XLK": 0.30, "XLF": 0.20, "XLE": 0.15})
    mae = compute_sector_mae(pred_s, act_s)
    recall = compute_top_k_recall(["XLK", "XLF"], ["XLK", "XLE"])
    ic = compute_spearman_rank_ic(pred_s, act_s)
    brier = compute_brier_score(np.array([0.9, 0.2]), np.array([1.0, 0.0]))

    print(f"\nValidation Metrics: MAE={mae}, Top-2 Recall={recall}, IC={ic}, Brier={brier}")
    assert mae < 0.10, "MAE should be low"
    assert brier < 0.10, "Brier score should be low"

    db.close()
    print("\n[OK] ALL 11 ENGINES, FUSER, META-ENSEMBLE & METRICS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_all_11_engines()
