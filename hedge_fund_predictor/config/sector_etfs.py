"""Sector and Thematic ETF configurations for position modeling and feature engineering.

Defines GICS sector ETFs, thematic ETFs, composite factor ETF lists, and standard
sector/theme names used across portfolio risk modeling and feature extraction.
"""

from typing import Dict, List

# 11 Standard GICS Sector SPDR ETFs
GICS_SECTOR_ETFS: Dict[str, str] = {
    "Information Technology": "XLK",
    "Financials": "XLF",
    "Health Care": "XLV",
    "Consumer Discretionary": "XLY",
    "Communication Services": "XLC",
    "Industrials": "XLI",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
}

# Thematic, Commodity, Macro, and Innovation ETFs
THEME_ETFS: Dict[str, str] = {
    "AI / Semiconductors": "SMH",
    "Clean Energy": "ICLN",
    "Crypto / Digital Assets": "BITO",
    "Treasury Bonds": "TLT",
    "Gold": "GLD",
    "US Dollar": "UUP",
    "Innovation": "ARKK",
    "Biotech": "IBB",
}

# Additional Style Factor ETFs used in quantitative risk models
STYLE_FACTOR_ETFS: List[str] = [
    "MTUM",  # Momentum
    "QUAL",  # Quality
    "USMV",  # Min Volatility
    "VLUE",  # Value
    "IWM",   # Small Cap (Russell 2000)
    "SPY",   # Broad Market (S&P 500)
    "QQQ",   # Tech Heavy (Nasdaq 100)
]

# Complete deduplicated list of all factor, sector, and thematic ETF tickers
ALL_FACTOR_ETFS: List[str] = list(
    dict.fromkeys(
        list(GICS_SECTOR_ETFS.values())
        + list(THEME_ETFS.values())
        + STYLE_FACTOR_ETFS
    )
)

# Ordered list of all sector and thematic names
SECTOR_NAMES: List[str] = list(GICS_SECTOR_ETFS.keys()) + list(THEME_ETFS.keys())
