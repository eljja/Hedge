"""
Main pipeline: Phase 1 data ingestion and universe building.

Run this script to:
1. Initialize the DuckDB schema
2. Download DERA 13F bulk data for recent quarters
3. Build the hedge fund universe ($1B+ AUM)
4. Download market data (ETF prices, FF5 factors, CFTC COT)
5. Download public HF vehicle NAVs for calibration

Usage:
    python -m hedge_fund_predictor.main_pipeline
"""

import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-40s | %(levelname)-5s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("pipeline")


def run_phase1():
    """Execute the complete Phase 1 data ingestion pipeline."""
    from hedge_fund_predictor.storage.db_manager import DatabaseManager

    logger.info("=" * 70)
    logger.info("HEDGE FUND POSITION PREDICTOR — Phase 1 Pipeline")
    logger.info("=" * 70)

    # ── Step 1: Initialize Database ────────────────────────────────────
    logger.info("Step 1: Initializing DuckDB schema...")
    with DatabaseManager() as db:
        db.init_schema()
        logger.info("✓ Schema initialized")

        # ── Step 2: Load DERA 13F Bulk Data ────────────────────────────
        logger.info("Step 2: Loading DERA 13F bulk data...")
        try:
            from hedge_fund_predictor.data_ingestion.sec_edgar.dera_bulk import (
                DERABulkLoader,
            )

            loader = DERABulkLoader()
            # Start with last 2 quarters for quick testing
            loader.load_recent_quarters(n=2)
            logger.info("✓ DERA 13F data loaded")
        except Exception as exc:
            logger.error("DERA loading failed: %s", exc)
            logger.info("Continuing with remaining steps...")

        # ── Step 3: Build Fund Universe ────────────────────────────────
        logger.info("Step 3: Building hedge fund universe...")
        try:
            from hedge_fund_predictor.fund_universe.universe_builder import (
                UniverseBuilder,
            )

            builder = UniverseBuilder(db_manager=db)
            universe = builder.build()

            if not universe.empty:
                known_hf = universe[universe["is_known_hf"] == True]
                logger.info(
                    "✓ Universe built: %d total filers, %d known HFs",
                    len(universe),
                    len(known_hf),
                )
                # Display top 20 by AUM
                top20 = universe.head(20)[["cik", "fund_name", "estimated_aum", "strategy"]]
                logger.info("Top 20 by AUM:\n%s", top20.to_string(index=False))
            else:
                logger.warning("Universe is empty — DERA data may not have loaded")
        except Exception as exc:
            logger.error("Universe building failed: %s", exc)

        # ── Step 4: Download Market Data ───────────────────────────────
        logger.info("Step 4: Downloading market data...")

        # 4a. Sector/Theme ETF prices
        try:
            from hedge_fund_predictor.data_ingestion.market_data.yfinance_ff import (
                YFinanceClient,
                FamaFrenchClient,
                PublicVehicleNAVCollector,
            )

            yf_client = YFinanceClient(db_manager=db)
            yf_client.download_sector_etf_returns(start="2024-01-01")
            logger.info("✓ Sector ETF returns downloaded")
        except Exception as exc:
            logger.error("ETF download failed: %s", exc)

        # 4b. Fama-French factors
        try:
            ff_client = FamaFrenchClient(db_manager=db)
            ff_client.download(start="2024-01-01")
            logger.info("✓ Fama-French 5 factors downloaded")
        except Exception as exc:
            logger.error("FF5 download failed: %s", exc)

        # 4c. Public HF vehicle NAVs (Kalman calibration)
        try:
            nav_collector = PublicVehicleNAVCollector(db_manager=db)
            nav_collector.download_all(start="2024-01-01")
            logger.info("✓ Public vehicle NAVs downloaded")
        except Exception as exc:
            logger.error("NAV download failed: %s", exc)

        # ── Step 5: Download CFTC COT Data ─────────────────────────────
        logger.info("Step 5: Downloading CFTC COT data...")
        try:
            from hedge_fund_predictor.data_ingestion.market_data.cftc_cot import (
                CFTCCOTLoader,
            )

            cot_loader = CFTCCOTLoader(db_manager=db)
            cot_loader.load_recent_years(n_years=2)
            logger.info("✓ CFTC COT data downloaded")
        except Exception as exc:
            logger.error("CFTC download failed: %s", exc)

        # ── Step 6: Run Basic Engine 1 Test ────────────────────────────
        logger.info("Step 6: Running Engine 1 (Adaptive Drift) test...")
        try:
            from hedge_fund_predictor.analytics_engine.E1_adaptive_drift import (
                AdaptiveDriftEngine,
            )
            from hedge_fund_predictor.config.entity_groups import ENTITY_GROUPS

            engine1 = AdaptiveDriftEngine(db_manager=db)

            # Test with Pershing Square (concentrated, well-known positions)
            if "pershing_square" in ENTITY_GROUPS:
                ps_config = ENTITY_GROUPS["pershing_square"]
                ps_cik = ps_config.hedge_fund_ciks[0]
                positions = engine1.estimate_current_positions(
                    cik=ps_cik, strategy=ps_config.strategy
                )
                if not positions.empty:
                    logger.info(
                        "✓ E1 test (Pershing Square): %d positions, "
                        "top hold: %s (%.1f%%)",
                        len(positions),
                        positions.iloc[0].get("issuer", "?"),
                        positions.iloc[0]["weight_raw"] * 100,
                    )
        except Exception as exc:
            logger.error("Engine 1 test failed: %s", exc)

        # ── Summary ───────────────────────────────────────────────────
        logger.info("=" * 70)
        logger.info("Phase 1 Pipeline Complete!")
        logger.info("Database: %s", db.db_path)

        # Quick DB stats
        try:
            stats = {
                "holdings_13f": db.query("SELECT COUNT(*) as n FROM holdings_13f").iloc[0]["n"],
                "market_prices": db.query("SELECT COUNT(*) as n FROM market_prices").iloc[0]["n"],
                "cftc_cot": db.query("SELECT COUNT(*) as n FROM cftc_cot").iloc[0]["n"],
                "fund_nav": db.query("SELECT COUNT(*) as n FROM fund_nav").iloc[0]["n"],
            }
            for table, count in stats.items():
                logger.info("  %-20s: %s rows", table, f"{count:,}")
        except Exception:
            pass

        logger.info("=" * 70)


if __name__ == "__main__":
    run_phase1()
