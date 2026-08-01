"""Configuration package for Hedge Fund Predictor."""

from hedge_fund_predictor.config.cftc_contracts import (
    COMMODITY_FUTURES,
    COT_URLS,
    DISAGGREGATED_CATEGORIES,
    FINANCIAL_FUTURES,
    TFF_CATEGORIES,
    TRADER_CATEGORIES,
)
from hedge_fund_predictor.config.entity_groups import (
    ENTITY_GROUPS,
    STRATEGIES,
    EntityGroupConfig,
)
from hedge_fund_predictor.config.sector_etfs import (
    ALL_FACTOR_ETFS,
    GICS_SECTOR_ETFS,
    SECTOR_NAMES,
    STYLE_FACTOR_ETFS,
    THEME_ETFS,
)
from hedge_fund_predictor.config.settings import (
    DATA_DIR,
    DB_PATH,
    FRED_API_KEY,
    LOOKBACK_QUARTERS,
    MIN_AUM_THRESHOLD,
    RAW_CFTC_DIR,
    RAW_EU_DIR,
    RAW_FRED_DIR,
    RAW_SEC_DIR,
    SEC_BASE_URL,
    SEC_DERA_BASE_URL,
    SEC_RATE_LIMIT,
    SEC_USER_AGENT,
    Settings,
    settings,
)

__all__ = [
    # Settings
    "SEC_USER_AGENT",
    "SEC_BASE_URL",
    "SEC_DERA_BASE_URL",
    "SEC_RATE_LIMIT",
    "DB_PATH",
    "DATA_DIR",
    "RAW_SEC_DIR",
    "RAW_CFTC_DIR",
    "RAW_FRED_DIR",
    "RAW_EU_DIR",
    "FRED_API_KEY",
    "LOOKBACK_QUARTERS",
    "MIN_AUM_THRESHOLD",
    "Settings",
    "settings",
    # Entity Groups
    "STRATEGIES",
    "EntityGroupConfig",
    "ENTITY_GROUPS",
    # Sector ETFs
    "GICS_SECTOR_ETFS",
    "THEME_ETFS",
    "STYLE_FACTOR_ETFS",
    "ALL_FACTOR_ETFS",
    "SECTOR_NAMES",
    # CFTC Contracts
    "FINANCIAL_FUTURES",
    "COMMODITY_FUTURES",
    "COT_URLS",
    "TRADER_CATEGORIES",
    "TFF_CATEGORIES",
    "DISAGGREGATED_CATEGORIES",
]
