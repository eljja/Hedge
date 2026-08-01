"""Hedge Fund Entity Group configurations.

Maps top hedge fund managers to SEC EDGAR CIK numbers (10-digit zero-padded),
strategy categorizations, public fund vehicles, CFTC trader categories, and EU short position registry names.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

STRATEGIES: List[str] = [
    "concentrated_activist",
    "equity_long_short",
    "multi_strategy",
    "global_macro",
    "quant_systematic",
    "event_driven",
    "credit",
    "tiger_cub",
]


@dataclass
class EntityGroupConfig:
    """Configuration mapping for a hedge fund management entity group."""

    hedge_fund_ciks: List[str]
    exclude_ciks: List[str] = field(default_factory=list)
    strategy: str = "multi_strategy"
    public_vehicle: Optional[str] = None
    cftc_trader_category: Optional[str] = "leveraged_funds"
    eu_short_name: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate strategy and format CIKs as zero-padded 10-digit strings."""
        if self.strategy not in STRATEGIES:
            raise ValueError(
                f"Invalid strategy '{self.strategy}'. Must be one of {STRATEGIES}"
            )
        self.hedge_fund_ciks = [cik.zfill(10) for cik in self.hedge_fund_ciks]
        self.exclude_ciks = [cik.zfill(10) for cik in self.exclude_ciks]


ENTITY_GROUPS: Dict[str, EntityGroupConfig] = {
    "bridgewater": EntityGroupConfig(
        hedge_fund_ciks=["0001350694"],  # Bridgewater Associates, LP
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Bridgewater Associates",
    ),
    "citadel": EntityGroupConfig(
        hedge_fund_ciks=["0001423053"],  # Citadel Advisors LLC
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Citadel Advisors",
    ),
    "de_shaw": EntityGroupConfig(
        hedge_fund_ciks=["0001009258"],  # D. E. Shaw & Co., L.P.
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="D. E. Shaw",
    ),
    "two_sigma": EntityGroupConfig(
        hedge_fund_ciks=["0001179392"],  # Two Sigma Investments, LP
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Two Sigma Investments",
    ),
    "renaissance": EntityGroupConfig(
        hedge_fund_ciks=["0001037389"],  # Renaissance Technologies LLC
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Renaissance Technologies",
    ),
    "millennium": EntityGroupConfig(
        hedge_fund_ciks=["0001273087"],  # Millennium Management LLC
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Millennium Capital",
    ),
    "point72": EntityGroupConfig(
        hedge_fund_ciks=["0001603466"],  # Point72 Asset Management, L.P.
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Point72 Asset Management",
    ),
    "elliott": EntityGroupConfig(
        hedge_fund_ciks=["0001048445"],  # Elliott Investment Management L.P.
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Elliott Management",
    ),
    "third_point": EntityGroupConfig(
        hedge_fund_ciks=["0001040273"],  # Third Point LLC
        strategy="concentrated_activist",
        public_vehicle="TPOU",  # Third Point Offshore Investors Ltd
        cftc_trader_category="leveraged_funds",
        eu_short_name="Third Point",
    ),
    "pershing_square": EntityGroupConfig(
        hedge_fund_ciks=["0001336528"],  # Pershing Square Capital Management, L.P.
        strategy="concentrated_activist",
        public_vehicle="PSH",  # Pershing Square Holdings Ltd
        cftc_trader_category="leveraged_funds",
        eu_short_name="Pershing Square",
    ),
    "tci": EntityGroupConfig(
        hedge_fund_ciks=["0001334978"],  # TCI Fund Management Ltd
        strategy="concentrated_activist",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="TCI Fund Management",
    ),
    "viking": EntityGroupConfig(
        hedge_fund_ciks=["0001103804"],  # Viking Global Investors LP
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Viking Global",
    ),
    "lone_pine": EntityGroupConfig(
        hedge_fund_ciks=["0001061165"],  # Lone Pine Capital LLC
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Lone Pine Capital",
    ),
    "tiger_global": EntityGroupConfig(
        hedge_fund_ciks=["0001167483"],  # Tiger Global Management LLC
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Tiger Global",
    ),
    "coatue": EntityGroupConfig(
        hedge_fund_ciks=["0001166559"],  # Coatue Management LLC
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Coatue Management",
    ),
    "baupost": EntityGroupConfig(
        hedge_fund_ciks=["0001061700"],  # Baupost Group LLC /MA/
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category=None,
        eu_short_name="Baupost Group",
    ),
    "appaloosa": EntityGroupConfig(
        hedge_fund_ciks=["0001006438"],  # Appaloosa Management LP
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Appaloosa Management",
    ),
    "greenlight": EntityGroupConfig(
        hedge_fund_ciks=["0001079114"],  # Greenlight Capital Inc
        strategy="equity_long_short",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Greenlight Capital",
    ),
    "aqr": EntityGroupConfig(
        hedge_fund_ciks=["0001167557"],  # AQR Capital Management LLC
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="AQR Capital",
    ),
    "man_group": EntityGroupConfig(
        hedge_fund_ciks=["0001416753"],  # Man Group plc
        strategy="quant_systematic",
        public_vehicle="EMG",
        cftc_trader_category="leveraged_funds",
        eu_short_name="Man Group",
    ),
    "balyasny": EntityGroupConfig(
        hedge_fund_ciks=["0001264873"],  # Balyasny Asset Management L.P.
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Balyasny Asset Management",
    ),
    "exoduspoint": EntityGroupConfig(
        hedge_fund_ciks=["0001740286"],  # ExodusPoint Capital Management, LP
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="ExodusPoint",
    ),
    "marshall_wace": EntityGroupConfig(
        hedge_fund_ciks=["0001383749"],  # Marshall Wace LLP
        strategy="equity_long_short",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Marshall Wace",
    ),
    "farallon": EntityGroupConfig(
        hedge_fund_ciks=["0001089748"],  # Farallon Capital Management LLC
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Farallon Capital",
    ),
    "canyon_partners": EntityGroupConfig(
        hedge_fund_ciks=["0001086208"],  # Canyon Capital Advisors LLC
        strategy="credit",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Canyon Capital",
    ),
    "sculptor": EntityGroupConfig(
        hedge_fund_ciks=["0001403256"],  # Sculptor Capital Management, Inc. (Och-Ziff)
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Sculptor Capital",
    ),
    "tudor": EntityGroupConfig(
        hedge_fund_ciks=["0000927702"],  # Tudor Investment Corp Et Al
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Tudor Capital",
    ),
    "soros": EntityGroupConfig(
        hedge_fund_ciks=["0001029160"],  # Soros Fund Management LLC
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Soros Fund Management",
    ),
    "duquesne": EntityGroupConfig(
        hedge_fund_ciks=["0001534643"],  # Duquesne Family Office LLC
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Duquesne",
    ),
    "anchorage": EntityGroupConfig(
        hedge_fund_ciks=["0001275022"],  # Anchorage Capital Group, L.L.C.
        strategy="credit",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Anchorage Capital",
    ),
}
