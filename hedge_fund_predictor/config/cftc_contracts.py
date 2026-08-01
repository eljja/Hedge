"""CFTC Commitments of Traders (COT) market and contract configurations.

Maps financial and commodity futures contracts to official CFTC report market names,
provides historical download URLs for TFF (Traders in Financial Futures) and
Disaggregated reports, and defines standardized trader category classifications.
"""

from typing import Dict, List

# Financial Futures Mapping (TFF Report Market Names)
FINANCIAL_FUTURES: Dict[str, str] = {
    "S&P 500 E-mini": "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
    "Nasdaq 100 E-mini": "NASDAQ-100 STOCK INDEX MINI - CHICAGO MERCANTILE EXCHANGE",
    "Dow Jones E-mini": "DJIA Consolidated - CHICAGO BOARD OF TRADE",
    "Russell 2000 E-mini": "RUSSELL 2000 E-MINI - CHICAGO MERCANTILE EXCHANGE",
    "10Y Treasury Note": "10-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE",
    "2Y Treasury Note": "2-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE",
    "5Y Treasury Note": "5-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE",
    "30Y Treasury Bond": "U.S. TREASURY BONDS - CHICAGO BOARD OF TRADE",
    "Euro FX": "EURO FX - CHICAGO MERCANTILE EXCHANGE",
    "Japanese Yen": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
    "British Pound": "BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE",
    "Canadian Dollar": "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "Australian Dollar": "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "Swiss Franc": "SWISS FRANC - CHICAGO MERCANTILE EXCHANGE",
    "VIX Futures": "VIX FUTURES - CBOE FUTURES EXCHANGE",
}

# Commodity Futures Mapping (Disaggregated Report Market Names)
COMMODITY_FUTURES: Dict[str, str] = {
    "Crude Oil": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE",
    "Gold": "GOLD - COMMODITY EXCHANGE INC.",
    "Silver": "SILVER - COMMODITY EXCHANGE INC.",
    "Natural Gas": "NATURAL GAS - NEW YORK MERCANTILE EXCHANGE",
    "Copper": "COPPER #1 - COMMODITY EXCHANGE INC.",
    "Corn": "CORN - CHICAGO BOARD OF TRADE",
    "Soybeans": "SOYBEANS - CHICAGO BOARD OF TRADE",
    "Wheat": "WHEAT - CHICAGO BOARD OF TRADE",
    "Brent Crude": "ICE BRENT CRUDE - ICE FUTURES EUROPE",
}

# Official CFTC Historical Bulk Data Download URLs
COT_URLS: Dict[str, str] = {
    "tff": "https://www.cftc.gov/files/dea/history/fin_com_txt.zip",
    "tff_futures_only": "https://www.cftc.gov/files/dea/history/fut_fin_txt.zip",
    "disaggregated": "https://www.cftc.gov/files/dea/history/fut_disagg_txt.zip",
    "disaggregated_combined": "https://www.cftc.gov/files/dea/history/com_disagg_txt.zip",
    "legacy": "https://www.cftc.gov/files/dea/history/deahistfo.zip",
}

# Relevant COT Trader Categories across TFF and Disaggregated Reports
TRADER_CATEGORIES: List[str] = [
    "dealer_intermediary",
    "asset_mgr_institutional",
    "leveraged_funds",
    "managed_money",
    "producer_merchant_processor_user",
    "swap_dealers",
    "other_reportables",
    "nonreportable_positions",
]

# TFF-specific Trader Categories
TFF_CATEGORIES: List[str] = [
    "dealer_intermediary",
    "asset_mgr_institutional",
    "leveraged_funds",
    "other_reportables",
    "nonreportable_positions",
]

# Disaggregated-specific Trader Categories
DISAGGREGATED_CATEGORIES: List[str] = [
    "producer_merchant_processor_user",
    "swap_dealers",
    "managed_money",
    "other_reportables",
    "nonreportable_positions",
]
