import logging
import duckdb
import pandas as pd
from pathlib import Path
from hedge_fund_predictor.config.settings import DB_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages DuckDB connection and common operations."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def connect(self):
        """Establish connection to DuckDB."""
        if self.conn is None:
            # Create directory if it doesn't exist
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to DuckDB at {self.db_path}")
            
    def close(self):
        """Close connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            logger.info("Closed DuckDB connection")
            
    def init_schema(self, schema_path: str = "D:/Code/Hedge/hedge_fund_predictor/storage/schema.sql"):
        """Initialize database schema from SQL file."""
        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            self.conn.execute(schema_sql)
            logger.info(f"Successfully initialized schema from {schema_path}")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
            
    def bulk_insert(self, table: str, df: pd.DataFrame):
        """Bulk insert a pandas DataFrame into a table."""
        if df.empty:
            logger.warning(f"Attempted to insert empty DataFrame into {table}")
            return
            
        try:
            self.conn.register('temp_df', df)
            columns = ", ".join(df.columns)
            self.conn.execute(f"INSERT INTO {table} ({columns}) SELECT * FROM temp_df")
            self.conn.unregister('temp_df')
            logger.info(f"Inserted {len(df)} rows into {table}")
        except Exception as e:
            logger.error(f"Failed to bulk insert into {table}: {e}")
            raise
            
    def query(self, sql: str, params: tuple = None) -> pd.DataFrame:
        """Execute a query and return results as a pandas DataFrame."""
        try:
            if params:
                return self.conn.execute(sql, params).df()
            return self.conn.execute(sql).df()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
            
    def get_latest_filing_date(self, cik: str) -> str:
        """Get the most recent filing date for a given CIK."""
        sql = "SELECT MAX(filing_date) as latest_date FROM filings_metadata WHERE cik = ?"
        df = self.query(sql, (cik,))
        if not df.empty and pd.notnull(df.iloc[0]['latest_date']):
            return str(df.iloc[0]['latest_date'])
        return None
        
    def get_fund_holdings(self, cik: str, quarter_date: str) -> pd.DataFrame:
        """Get holdings for a specific fund and quarter."""
        sql = "SELECT * FROM holdings_13f WHERE cik = ? AND report_date = ?"
        return self.query(sql, (cik, quarter_date))
        
    def upsert_holdings(self, df: pd.DataFrame):
        """Upsert holdings, handling duplicates based on primary key."""
        if df.empty:
            return
            
        try:
            self.conn.register('temp_holdings', df)
            
            sql = """
            INSERT INTO holdings_13f
            SELECT * FROM temp_holdings
            ON CONFLICT (cik, report_date, cusip, put_call) DO UPDATE SET
                filing_date = excluded.filing_date,
                issuer = excluded.issuer,
                class_title = excluded.class_title,
                value_thousands = excluded.value_thousands,
                shares_or_amount = excluded.shares_or_amount,
                shares_type = excluded.shares_type,
                investment_discretion = excluded.investment_discretion,
                is_amendment = excluded.is_amendment,
                is_ct_revealed = excluded.is_ct_revealed;
            """
            self.conn.execute(sql)
            self.conn.unregister('temp_holdings')
            logger.info(f"Upserted {len(df)} rows into holdings_13f")
        except Exception as e:
            logger.error(f"Failed to upsert holdings: {e}")
            raise
