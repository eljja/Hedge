"""Global configuration settings for Hedge Fund Position Predictor.

Provides centralized path management, API endpoints, rate limits, and modeling
parameters for SEC EDGAR, CFTC CoT, FRED macro data, and DuckDB storage.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# SEC EDGAR Settings
SEC_USER_AGENT: str = os.getenv(
    "SEC_USER_AGENT", "HedgeFundPredictor admin@example.com"
)
SEC_BASE_URL: str = "https://data.sec.gov"
SEC_DERA_BASE_URL: str = "https://www.sec.gov/files/dera/data"
SEC_RATE_LIMIT: int = 10  # Maximum requests per second permitted by SEC EDGAR guidelines

# Default File Paths (using pathlib.Path throughout)
DEFAULT_BASE_DIR: Path = Path(r"D:\Code\Hedge")
DEFAULT_DATA_DIR: Path = DEFAULT_BASE_DIR / "data" / "raw"
DEFAULT_DB_PATH: Path = DEFAULT_BASE_DIR / "data" / "hedge_fund.duckdb"

DATA_DIR: Path = Path(os.getenv("HEDGE_DATA_DIR", str(DEFAULT_DATA_DIR)))
DB_PATH: Path = Path(os.getenv("HEDGE_DB_PATH", str(DEFAULT_DB_PATH)))

# Data Category Sub-directories
RAW_SEC_DIR: Path = DATA_DIR / "sec"
RAW_CFTC_DIR: Path = DATA_DIR / "cftc"
RAW_FRED_DIR: Path = DATA_DIR / "fred"
RAW_EU_DIR: Path = DATA_DIR / "eu"

# Federal Reserve Economic Data (FRED) API Key
FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")

# Quantitative Model & Data Threshold Parameters
LOOKBACK_QUARTERS: int = 8  # Past quarters window for position predictor models
MIN_AUM_THRESHOLD: int = 1_000_000  # Minimum AUM threshold in $1,000 units ($1,000,000k = $1 Billion)


def ensure_directories_exist() -> None:
    """Create data storage directories and database parent directory if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_SEC_DIR.mkdir(parents=True, exist_ok=True)
    RAW_CFTC_DIR.mkdir(parents=True, exist_ok=True)
    RAW_FRED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_EU_DIR.mkdir(parents=True, exist_ok=True)


# Automatically ensure directory structure exists on module load
ensure_directories_exist()


@dataclass
class Settings:
    """Dataclass encapsulating global application settings."""

    sec_user_agent: str = SEC_USER_AGENT
    sec_base_url: str = SEC_BASE_URL
    sec_dera_base_url: str = SEC_DERA_BASE_URL
    sec_rate_limit: int = SEC_RATE_LIMIT
    db_path: Path = DB_PATH
    data_dir: Path = DATA_DIR
    raw_sec_dir: Path = RAW_SEC_DIR
    raw_cftc_dir: Path = RAW_CFTC_DIR
    raw_fred_dir: Path = RAW_FRED_DIR
    raw_eu_dir: Path = RAW_EU_DIR
    fred_api_key: str = FRED_API_KEY
    lookback_quarters: int = LOOKBACK_QUARTERS
    min_aum_threshold: int = MIN_AUM_THRESHOLD

    def __post_init__(self) -> None:
        """Validate and resolve path objects, ensuring target directories exist."""
        self.db_path = Path(self.db_path)
        self.data_dir = Path(self.data_dir)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Default settings instance
settings = Settings()
