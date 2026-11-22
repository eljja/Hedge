"""Hedge Fund Entity Group configurations.

Maps top 50 global hedge fund managers to verified SEC EDGAR 13F-HR CIK numbers
(10-digit zero-padded), human-readable display names, strategy categorizations,
public fund vehicles, CFTC trader categories, and EU short position registry names.
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
    display_name: str = ""
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
        display_name="Bridgewater Associates",
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Bridgewater Associates",
    ),
    "citadel": EntityGroupConfig(
        hedge_fund_ciks=["0001423053"],  # Citadel Advisors LLC
        display_name="Citadel Advisors",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Citadel Advisors",
    ),
    "de_shaw": EntityGroupConfig(
        hedge_fund_ciks=["0001009207"],  # D. E. Shaw & Co., Inc.
        display_name="D.E. Shaw & Co.",
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="D. E. Shaw",
    ),
    "two_sigma": EntityGroupConfig(
        hedge_fund_ciks=["0001179392"],  # Two Sigma Investments, LP
        display_name="Two Sigma Investments",
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Two Sigma Investments",
    ),
    "renaissance": EntityGroupConfig(
        hedge_fund_ciks=["0001037389"],  # Renaissance Technologies LLC
        display_name="Renaissance Technologies",
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Renaissance Technologies",
    ),
    "millennium": EntityGroupConfig(
        hedge_fund_ciks=["0001273087"],  # Millennium Management LLC
        display_name="Millennium Management",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Millennium Capital",
    ),
    "point72": EntityGroupConfig(
        hedge_fund_ciks=["0001603466"],  # Point72 Asset Management, L.P.
        display_name="Point72 Asset Management",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Point72 Asset Management",
    ),
    "elliott": EntityGroupConfig(
        hedge_fund_ciks=["0001791786"],  # Elliott Investment Management L.P.
        display_name="Elliott Investment Management",
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Elliott Management",
    ),
    "third_point": EntityGroupConfig(
        hedge_fund_ciks=["0001040273"],  # Third Point LLC
        display_name="Third Point",
        strategy="concentrated_activist",
        public_vehicle="TPOU",
        cftc_trader_category="leveraged_funds",
        eu_short_name="Third Point",
    ),
    "pershing_square": EntityGroupConfig(
        hedge_fund_ciks=["0002026053", "0001336528"],  # Pershing Square Inc. (parent) / Capital Mgmt
        display_name="Pershing Square",
        strategy="concentrated_activist",
        public_vehicle="PSH",
        cftc_trader_category="leveraged_funds",
        eu_short_name="Pershing Square",
    ),
    "tci": EntityGroupConfig(
        hedge_fund_ciks=["0001647251"],  # TCI Fund Management Ltd
        display_name="TCI Fund Management",
        strategy="concentrated_activist",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="TCI Fund Management",
    ),
    "viking": EntityGroupConfig(
        hedge_fund_ciks=["0001103804"],  # Viking Global Investors LP
        display_name="Viking Global Investors",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Viking Global",
    ),
    "lone_pine": EntityGroupConfig(
        hedge_fund_ciks=["0001061165"],  # Lone Pine Capital LLC
        display_name="Lone Pine Capital",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Lone Pine Capital",
    ),
    "tiger_global": EntityGroupConfig(
        hedge_fund_ciks=["0001167483"],  # Tiger Global Management LLC
        display_name="Tiger Global Management",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Tiger Global",
    ),
    "coatue": EntityGroupConfig(
        hedge_fund_ciks=["0001135730"],  # Coatue Management LLC
        display_name="Coatue Management",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Coatue Management",
    ),
    "baupost": EntityGroupConfig(
        hedge_fund_ciks=["0001061768"],  # Baupost Group LLC/MA
        display_name="Baupost Group",
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category=None,
        eu_short_name="Baupost Group",
    ),
    "appaloosa": EntityGroupConfig(
        hedge_fund_ciks=["0001656456"],  # Appaloosa LP
        display_name="Appaloosa Management",
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Appaloosa Management",
    ),
    "greenlight": EntityGroupConfig(
        hedge_fund_ciks=["0001489933"],  # DME Capital Management, LP (Greenlight)
        display_name="Greenlight Capital (DME)",
        strategy="equity_long_short",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Greenlight Capital",
    ),
    "aqr": EntityGroupConfig(
        hedge_fund_ciks=["0001167557"],  # AQR Capital Management LLC
        display_name="AQR Capital Management",
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="AQR Capital",
    ),
    "man_group": EntityGroupConfig(
        hedge_fund_ciks=["0001637460"],  # Man Group plc
        display_name="Man Group",
        strategy="quant_systematic",
        public_vehicle="EMG",
        cftc_trader_category="leveraged_funds",
        eu_short_name="Man Group",
    ),
    "balyasny": EntityGroupConfig(
        hedge_fund_ciks=["0001218710"],  # Balyasny Asset Management L.P.
        display_name="Balyasny Asset Management",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Balyasny Asset Management",
    ),
    "exoduspoint": EntityGroupConfig(
        hedge_fund_ciks=["0001736225"],  # ExodusPoint Capital Management, LP
        display_name="ExodusPoint Capital",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="ExodusPoint",
    ),
    "marshall_wace": EntityGroupConfig(
        hedge_fund_ciks=["0001318757"],  # Marshall Wace, LLP
        display_name="Marshall Wace",
        strategy="equity_long_short",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Marshall Wace",
    ),
    "farallon": EntityGroupConfig(
        hedge_fund_ciks=["0000909661"],  # Farallon Capital Management, L.L.C.
        display_name="Farallon Capital",
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Farallon Capital",
    ),
    "canyon_partners": EntityGroupConfig(
        hedge_fund_ciks=["0001074034"],  # Canyon Capital Advisors LLC
        display_name="Canyon Partners",
        strategy="credit",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Canyon Capital",
    ),
    "sculptor": EntityGroupConfig(
        hedge_fund_ciks=["0001054587"],  # Sculptor Capital LP
        display_name="Sculptor Capital",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Sculptor Capital",
    ),
    "tudor": EntityGroupConfig(
        hedge_fund_ciks=["0000923093"],  # Tudor Investment Corp Et Al
        display_name="Tudor Investment Corp",
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Tudor Capital",
    ),
    "soros": EntityGroupConfig(
        hedge_fund_ciks=["0001029160"],  # Soros Fund Management LLC
        display_name="Soros Fund Management",
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Soros Fund Management",
    ),
    "duquesne": EntityGroupConfig(
        hedge_fund_ciks=["0001536411"],  # Duquesne Family Office LLC
        display_name="Duquesne Family Office",
        strategy="global_macro",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Duquesne",
    ),
    "anchorage": EntityGroupConfig(
        hedge_fund_ciks=["0001300714"],  # Anchorage Capital Group, L.L.C.
        display_name="Anchorage Capital",
        strategy="credit",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Anchorage Capital",
    ),
    "schonfeld": EntityGroupConfig(
        hedge_fund_ciks=["0001665241"],  # Schonfeld Strategic Advisors LLC
        display_name="Schonfeld Strategic Advisors",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Schonfeld Strategic Advisors",
    ),
    "verition": EntityGroupConfig(
        hedge_fund_ciks=["0001454027"],  # Verition Fund Management LLC
        display_name="Verition Fund Management",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Verition Fund Management",
    ),
    "walleye": EntityGroupConfig(
        hedge_fund_ciks=["0001758720"],  # Walleye Capital LLC
        display_name="Walleye Capital",
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Walleye Capital",
    ),
    "hudson_bay": EntityGroupConfig(
        hedge_fund_ciks=["0001393825"],  # Hudson Bay Capital Management LP
        display_name="Hudson Bay Capital",
        strategy="multi_strategy",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Hudson Bay Capital Management",
    ),
    "magnetar": EntityGroupConfig(
        hedge_fund_ciks=["0001352851"],  # Magnetar Financial LLC
        display_name="Magnetar Financial",
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Magnetar Financial",
    ),
    "maverick": EntityGroupConfig(
        hedge_fund_ciks=["0000934639"],  # Maverick Capital Ltd
        display_name="Maverick Capital",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Maverick Capital",
    ),
    "whale_rock": EntityGroupConfig(
        hedge_fund_ciks=["0001387322"],  # Whale Rock Capital Management LLC
        display_name="Whale Rock Capital",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Whale Rock Capital Management",
    ),
    "d1_capital": EntityGroupConfig(
        hedge_fund_ciks=["0001747057"],  # D1 Capital Partners L.P.
        display_name="D1 Capital Partners",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="D1 Capital Partners",
    ),
    "matrix_capital": EntityGroupConfig(
        hedge_fund_ciks=["0001410830"],  # Matrix Capital Management Company, LP
        display_name="Matrix Capital Management",
        strategy="tiger_cub",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Matrix Capital Management",
    ),
    "steadfast": EntityGroupConfig(
        hedge_fund_ciks=["0001214822"],  # Steadfast Capital Management LP
        display_name="Steadfast Capital",
        strategy="equity_long_short",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Steadfast Capital Management",
    ),
    "glenview": EntityGroupConfig(
        hedge_fund_ciks=["0001138995"],  # Glenview Capital Management, LLC
        display_name="Glenview Capital",
        strategy="equity_long_short",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Glenview Capital Management",
    ),
    "icahn": EntityGroupConfig(
        hedge_fund_ciks=["0000921669"],  # Icahn Carl C
        display_name="Icahn Capital",
        strategy="concentrated_activist",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Icahn Capital Management",
    ),
    "valueact": EntityGroupConfig(
        hedge_fund_ciks=["0001418814"],  # ValueAct Holdings, L.P.
        display_name="ValueAct Capital",
        strategy="concentrated_activist",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="ValueAct Capital Management",
    ),
    "jana_partners": EntityGroupConfig(
        hedge_fund_ciks=["0001998597"],  # JANA Partners Management, LP
        display_name="JANA Partners",
        strategy="event_driven",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="JANA Partners",
    ),
    "starboard": EntityGroupConfig(
        hedge_fund_ciks=["0001517137"],  # Starboard Value LP
        display_name="Starboard Value",
        strategy="concentrated_activist",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Starboard Value",
    ),
    "winton": EntityGroupConfig(
        hedge_fund_ciks=["0001612063"],  # Winton Group Ltd
        display_name="Winton Group",
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Winton Capital Management",
    ),
    "worldquant": EntityGroupConfig(
        hedge_fund_ciks=["0001745981"],  # WorldQuant Millennium Advisors LLC
        display_name="WorldQuant",
        strategy="quant_systematic",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="WorldQuant",
    ),
    "king_street": EntityGroupConfig(
        hedge_fund_ciks=["0001218199"],  # King Street Capital Management, L.P.
        display_name="King Street Capital",
        strategy="credit",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="King Street Capital Management",
    ),
    "cerberus": EntityGroupConfig(
        hedge_fund_ciks=["0001525907"],  # Cerberus Capital Management, L.P.
        display_name="Cerberus Capital",
        strategy="credit",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Cerberus Capital Management",
    ),
    "egerton": EntityGroupConfig(
        hedge_fund_ciks=["0001581811"],  # Egerton Capital (UK) LLP
        display_name="Egerton Capital",
        strategy="equity_long_short",
        public_vehicle=None,
        cftc_trader_category="leveraged_funds",
        eu_short_name="Egerton Capital",
    ),
}
