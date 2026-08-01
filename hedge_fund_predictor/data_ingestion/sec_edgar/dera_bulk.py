import logging
import requests
import time
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from hedge_fund_predictor.config.settings import SEC_USER_AGENT, DATA_DIR
from hedge_fund_predictor.storage.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DERABulkLoader:
    """Loader for SEC DERA Form 13F bulk datasets."""
    
    BASE_URL = "https://www.sec.gov/files/dera/data/form-13f-data-sets"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": SEC_USER_AGENT})
        
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        
        self.data_dir = Path(DATA_DIR) / "sec_dera"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def _download_file(self, filename: str) -> Path:
        """Download a file with SEC rate limiting (max 10 req/sec)."""
        url = f"{self.BASE_URL}/{filename}"
        local_path = self.data_dir / filename
        
        if local_path.exists():
            logger.info(f"File {filename} already exists at {local_path}")
            return local_path
            
        logger.info(f"Downloading {url}")
        time.sleep(0.15)  # Respect SEC limit of 10 requests/second
        
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return local_path

    def load_quarter(self, year: int, quarter: int):
        """Download and load data for a specific year and quarter."""
        base_name = f"13f{year}q{quarter}"
        
        files = {
            "infotable": f"{base_name}_infotable.csv",
            "submission": f"{base_name}_submission.tsv",
            "coverpage": f"{base_name}_coverpage.tsv"
        }
        
        try:
            infotable_path = self._download_file(files["infotable"])
            sub_path = self._download_file(files["submission"])
            cov_path = self._download_file(files["coverpage"])
            
            df_info = pd.read_csv(infotable_path, sep="\t" if infotable_path.suffix == ".tsv" else ",")
            df_sub = pd.read_csv(sub_path, sep="\t")
            df_cov = pd.read_csv(cov_path, sep="\t")
            
            if df_info.empty:
                logger.warning(f"No data found in {files['infotable']}")
                return

            logger.info(f"Loaded data for {year} Q{quarter}")
            
            # In a full implementation, we map these DataFrames to our schema
            # and use DatabaseManager to insert.
            with DatabaseManager() as db:
                # db.upsert_holdings(mapped_holdings_df)
                # db.bulk_insert('filings_metadata', mapped_metadata_df)
                pass
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download data for {year} Q{quarter}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing data for {year} Q{quarter}: {e}")
            raise

    def load_recent_quarters(self, n: int = 8):
        """Load data for the last n quarters."""
        import datetime
        now = datetime.datetime.now()
        current_year = now.year
        current_quarter = (now.month - 1) // 3 + 1
        
        quarters_to_load = []
        for _ in range(n):
            current_quarter -= 1
            if current_quarter == 0:
                current_quarter = 4
                current_year -= 1
            quarters_to_load.append((current_year, current_quarter))
            
        for y, q in tqdm(quarters_to_load, desc="Loading quarters"):
            self.load_quarter(y, q)
