import logging
import pandas as pd
from hedge_fund_predictor.storage.db_manager import DatabaseManager
from hedge_fund_predictor.config.settings import MIN_AUM_THRESHOLD
from hedge_fund_predictor.config.entity_groups import KNOWN_HEDGE_FUNDS

logger = logging.getLogger(__name__)

class UniverseBuilder:
    """Builds and maintains the hedge fund universe."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def build(self, quarter_date: str) -> pd.DataFrame:
        """
        Build universe for a specific quarter.
        - Computes AUM per CIK from holdings_13f
        - Filters by MIN_AUM_THRESHOLD
        - Identifies known hedge funds
        - Uses concentration (HHI) to flag potential funds
        """
        query = """
            SELECT cik, SUM(value_thousands) as estimated_aum, 
                   SUM(value_thousands * value_thousands) / (SUM(value_thousands) * SUM(value_thousands)) as hhi
            FROM holdings_13f 
            WHERE report_date = ?
            GROUP BY cik
        """
        df_stats = self.db.query(query, (quarter_date,))
        
        if df_stats.empty:
            logger.warning(f"No holdings data found for {quarter_date}")
            return pd.DataFrame()
            
        df_filtered = df_stats[df_stats['estimated_aum'] >= MIN_AUM_THRESHOLD].copy()
        
        def check_known(cik):
            return cik in KNOWN_HEDGE_FUNDS
            
        df_filtered['is_known_hf'] = df_filtered['cik'].apply(check_known)
        df_filtered['is_high_concentration'] = df_filtered['hhi'] > 0.05
        
        # In a real implementation, join with filings_metadata to get fund name
        df_filtered['fund_name'] = "Unknown Entity" 
        df_filtered['strategy'] = "Unknown"
        
        logger.info(f"Built universe for {quarter_date} with {len(df_filtered)} funds")
        return df_filtered
        
    def get_active_universe(self) -> pd.DataFrame:
        """Return the latest active universe from the database."""
        return self.db.query("SELECT * FROM fund_universe")
