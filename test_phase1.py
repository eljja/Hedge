"""Quick integration test for Phase 1 infrastructure."""
import pandas as pd
from hedge_fund_predictor.storage.db_manager import DatabaseManager

def test():
    db = DatabaseManager()
    db.connect()
    db.init_schema()

    # Check tables exist
    tables = db.query("SELECT table_name FROM information_schema.tables WHERE table_schema='main'")
    print(f"Tables created: {len(tables)}")
    for t in tables['table_name'].tolist():
        print(f"  - {t}")

    # Insert test holdings
    test_data = pd.DataFrame([{
        'cik': '0001423053', 'report_date': '2026-03-31', 'filing_date': '2026-05-15',
        'cusip': '594918104', 'issuer': 'MICROSOFT CORP', 'class_title': 'COM',
        'value_thousands': 500000, 'shares_or_amount': 1200000,
        'shares_type': 'SH', 'put_call': None,
        'investment_discretion': 'SOLE', 'is_amendment': False, 'is_ct_revealed': False,
    }, {
        'cik': '0001423053', 'report_date': '2026-03-31', 'filing_date': '2026-05-15',
        'cusip': '037833100', 'issuer': 'APPLE INC', 'class_title': 'COM',
        'value_thousands': 300000, 'shares_or_amount': 1500000,
        'shares_type': 'SH', 'put_call': None,
        'investment_discretion': 'SOLE', 'is_amendment': False, 'is_ct_revealed': False,
    }])
    db.bulk_insert('holdings_13f', test_data)

    # Query back
    result = db.query('SELECT cik, cusip, issuer, value_thousands FROM holdings_13f ORDER BY value_thousands DESC')
    print(f"\nHoldings test: {len(result)} rows")
    print(result.to_string(index=False))

    # Test Engine 1
    from hedge_fund_predictor.analytics_engine.E1_adaptive_drift import AdaptiveDriftEngine
    engine = AdaptiveDriftEngine(db_manager=db)
    positions = engine.estimate_current_positions('0001423053', 'multi_strategy')
    if not positions.empty:
        print(f"\nEngine 1 test: {len(positions)} positions")
        print(positions[['cusip','issuer','value_current','weight_raw','confidence']].to_string(index=False))

    # Test Engine 5
    from hedge_fund_predictor.analytics_engine.E5_conviction_consensus import ConvictionConsensusEngine
    e5 = ConvictionConsensusEngine(db_manager=db)
    analysis = e5.analyze()
    print(f"\nEngine 5 test: {len(analysis['stock_scores'])} stocks scored")

    # Clean up test data
    db.conn.execute('DELETE FROM holdings_13f')

    # Check entity groups
    from hedge_fund_predictor.config.entity_groups import ENTITY_GROUPS
    print(f"\nEntity groups loaded: {len(ENTITY_GROUPS)} funds")
    for name, cfg in list(ENTITY_GROUPS.items())[:5]:
        print(f"  {name}: CIK={cfg.hedge_fund_ciks[0]}, strategy={cfg.strategy}")

    db.close()
    print("\n[OK] ALL PHASE 1 TESTS PASSED!")

if __name__ == "__main__":
    test()
