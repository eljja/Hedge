"""Phase 2 Integration Test Script."""

import numpy as np
import pandas as pd
from hedge_fund_predictor.storage.db_manager import DatabaseManager
from hedge_fund_predictor.analytics_engine.E2_kalman_rbsa import KalmanRBSAEngine
from hedge_fund_predictor.analytics_engine.E4_options_delta import OptionsDeltaEngine, bs_delta
from hedge_fund_predictor.analytics_engine.E7_cftc_positioning import CFTCPositioningEngine
from hedge_fund_predictor.analytics_engine.E3_bayesian_event import BayesianEventEngine
from hedge_fund_predictor.calibration.ground_truth_calibrator import GroundTruthCalibrator


def test_phase2():
    print("=" * 60)
    print("STARTING PHASE 2 INTEGRATION TESTS")
    print("=" * 60)

    db = DatabaseManager()
    db.connect()
    db.init_schema()

    # -------------------------------------------------------------------
    # Test 1: Engine 4 (Options Delta Conversion)
    # -------------------------------------------------------------------
    print("\n--- Testing Engine 4 (Options Delta Conversion) ---")
    holdings_raw = pd.DataFrame([
        {
            "cusip": "594918104",
            "issuer": "MICROSOFT CORP",
            "value_thousands": 500000,
            "shares_or_amount": 1200000,
            "put_call": "NONE",
        },
        {
            "cusip": "037833100",
            "issuer": "APPLE INC CALL",
            "value_thousands": 50000,
            "shares_or_amount": 250000,
            "put_call": "CALL",
        },
        {
            "cusip": "88160R101",
            "issuer": "TESLA INC PUT",
            "value_thousands": 30000,
            "shares_or_amount": 150000,
            "put_call": "PUT",
        },
    ])

    e4 = OptionsDeltaEngine(db_manager=db)
    delta_df = e4.convert_options_to_delta_equivalent(holdings_raw)

    print("Engine 4 output:")
    print(delta_df[["issuer", "put_call", "delta", "delta_equivalent_shares", "exposure_type"]].to_string(index=False))

    assert len(delta_df) == 3, "Engine 4 should return 3 rows"
    assert round(delta_df.iloc[0]["delta"], 1) == 1.0, "Equity delta should be 1.0"
    assert delta_df.iloc[1]["delta"] > 0.4, "Call delta should be ~0.5"
    assert delta_df.iloc[2]["delta"] < -0.4, "Put delta should be ~ -0.5"
    print("[OK] Engine 4 Passed!")

    # -------------------------------------------------------------------
    # Test 2: Engine 2 (Kalman RBSA Engine)
    # -------------------------------------------------------------------
    print("\n--- Testing Engine 2 (Kalman RBSA Engine) ---")
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=30, freq="W")

    factors = pd.DataFrame({
        "XLK": np.random.normal(0.002, 0.02, 30),
        "XLF": np.random.normal(0.001, 0.015, 30),
        "XLE": np.random.normal(-0.001, 0.025, 30),
    }, index=dates)

    # Synthetic fund returns heavily exposed to XLK
    fund_rets = 0.7 * factors["XLK"] + 0.3 * factors["XLF"] + np.random.normal(0, 0.005, 30)
    fund_rets.name = "fund_ret"

    e2 = KalmanRBSAEngine(r_variance=1e-4, q_variance=1e-5)
    betas = e2.estimate_exposures(fund_rets, factors)

    print("Engine 2 estimated factor weights (latest date):")
    print(betas.iloc[-1].to_string())

    assert not betas.empty, "Engine 2 output should not be empty"
    assert "XLK" in betas.columns, "XLK factor should be in betas"
    assert betas.iloc[-1]["XLK"] > betas.iloc[-1]["XLE"], "XLK weight should exceed XLE"
    print("[OK] Engine 2 Passed!")

    # -------------------------------------------------------------------
    # Test 3: Engine 7 (CFTC Macro Positioning)
    # -------------------------------------------------------------------
    print("\n--- Testing Engine 7 (CFTC Positioning Engine) ---")

    # Insert synthetic COT data
    cot_test = pd.DataFrame([
        {
            "report_date": "2026-03-31",
            "market_name": "sp500",
            "contract_type": "financial",
            "lev_long": 150000,
            "lev_short": 50000,
            "lev_net": 100000,
            "mm_long": 0,
            "mm_short": 0,
            "mm_net": 0,
            "z_score": 1.85,
        },
        {
            "report_date": "2026-03-31",
            "market_name": "crude_oil",
            "contract_type": "commodity",
            "lev_long": 0,
            "lev_short": 0,
            "lev_net": 0,
            "mm_long": 80000,
            "mm_short": 120000,
            "mm_net": -40000,
            "z_score": -1.20,
        },
    ])

    db.bulk_insert("cftc_cot", cot_test)

    e7 = CFTCPositioningEngine(db_manager=db)
    biases = e7.compute_fund_macro_bias("global_macro")
    tilts = e7.map_cot_to_gics_sectors("global_macro")

    print(f"Engine 7 biases: {biases}")
    print("Engine 7 sector tilts:")
    print(tilts.to_string(index=False))

    assert "sp500" in biases, "sp500 bias should be present"
    assert not tilts.empty, "Sector tilts dataframe should not be empty"
    print("[OK] Engine 7 Passed!")

    # -------------------------------------------------------------------
    # Test 4: Engine 3 (Bayesian Discrete Event Jump)
    # -------------------------------------------------------------------
    print("\n--- Testing Engine 3 (Bayesian Event Engine) ---")
    e3 = BayesianEventEngine(db_manager=db)

    prior = 0.50
    post_13d = e3.update_posterior_probability(prior, "13D")
    post_ct = e3.update_posterior_probability(prior, "13F_CT_REVEAL")

    print(f"13D Event: Prior {prior} -> Posterior {post_13d}")
    print(f"13F CT Release: Prior {prior} -> Posterior {post_ct}")

    assert post_13d > 0.85, "13D posterior should be > 0.85"
    assert post_ct > 0.80, "13F CT posterior should be > 0.80"
    print("[OK] Engine 3 Passed!")

    # -------------------------------------------------------------------
    # Test 5: Ground Truth Calibrator
    # -------------------------------------------------------------------
    print("\n--- Testing Ground Truth Calibrator ---")
    calib = GroundTruthCalibrator(db_manager=db)
    r_opt, q_opt = calib.calibrate_fund("Pershing Square", "PSH.AS")
    print(f"Calibrated R: {r_opt:.2e}, Q: {q_opt:.2e}")
    assert r_opt > 0 and q_opt > 0, "Calibrated noise terms must be positive"
    print("[OK] Ground Truth Calibrator Passed!")

    # Clean test tables
    db.conn.execute("DELETE FROM cftc_cot")
    db.close()

    print("\n[OK] ALL PHASE 2 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_phase2()
