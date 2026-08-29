# 🏛️ Hedge Fund Position Predictor v6 (Quant & Short Analytics Edition)

[![Live Web Dashboard](https://img.shields.io/badge/Live%20Dashboard-eljja.github.io%2FHedge-06B6D4?style=for-the-badge&logo=github)](https://eljja.github.io/Hedge)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-10B981?style=for-the-badge&logo=python)](https://python.org)

> 🌐 **Live Web Dashboard**: [https://eljja.github.io/Hedge](https://eljja.github.io/Hedge)  
> 📦 **GitHub Repository**: [https://github.com/eljja/Hedge](https://github.com/eljja/Hedge)

An institutional-grade hedge fund position estimation and short intelligence engine. Track **50+ top global hedge funds** (over $1.25T AUM), featuring **16 data channels**, **13 quantitative analytics engines**, **FINRA short interest analytics**, **SEC 13D/G activist stake tracking**, and **interactive Chart.js visual analytics**.

---

## 🌟 Key Features

### 1. 🌐 50 Top Global Hedge Funds Universe (8 Strategy Groups)
- **Multi-Strategy (9)**: Citadel, Millennium, Point72, Schonfeld, Verition, Hudson Bay, Balyasny, ExodusPoint, Walleye
- **Quant & Systematic (8)**: Renaissance Technologies, Two Sigma, D.E. Shaw, AQR, WorldQuant, Winton, Man Group, Matrix Capital
- **Tiger Cubs & Tech L/S (8)**: Viking Global, Lone Pine, Tiger Global, Coatue, D1 Capital, Whale Rock, Maverick, Egerton
- **Concentrated & Activists (6)**: Pershing Square, Third Point, TCI Fund, Icahn Enterprises, ValueAct, Starboard Value
- **Event-Driven (6)**: Elliott Management, Baupost Group, Appaloosa, Farallon, Magnetar, JANA Partners
- **Equity Long/Short (5)**: Greenlight Capital, Marshall Wace, Glenview, Steadfast, Sculptor
- **Credit & Distressed (4)**: Canyon Partners, Anchorage Capital, King Street, Cerberus
- **Global Macro (4)**: Bridgewater Associates, Soros Fund Management, Tudor Investment, Duquesne Family Office

### 2. 📊 16 Data Channels & 13 Quantitative Engines
- **SEC EDGAR 13F-HR & 13F-NT**: Quarterly institutional long holdings, call options, and put options.
- **SEC Schedule 13D/G Activist Tracker**: Mandatory 5%+ ownership disclosures with 98%+ confidence ratings.
- **FINRA Short Interest & Reg SHO**: Bi-monthly short interest %, Days-to-Cover, and Short Squeeze Risk ratings (HIGH, MODERATE, LOW).
- **CFTC Commitments of Traders (CoT)**: Leveraged funds futures positioning mapped to macro tilts.
- **Hidden Short Intelligence**: Pair-trade shorts (e.g., Uber Long vs Lyft Short), tail-risk index hedges (SPY/QQQ/IWM PUTs), overvaluation shorts (TSLA, RIVN, CVNA, BYND), and credit/CRE distress shorts (HYG, IYR).
- **Multi-Timeframe Fusion Engine**: Stacking ensemble combining delayed 13F filings with near-real-time 13D, FINRA, and CFTC signals.

### 3. 🖥️ Interactive Web Dashboard (8 Specialized Tabs)
1. **📊 Fund Positions**: Individual fund position estimates with capital amount ($M), weight (%), confidence (%), rating, and real-time **Exposure Summary Bar** (Long Capital, Short Capital, Net Exposure %, Gross Exposure %).
2. **📈 Top Holdings**: Top 50 most held assets aggregated across 50 funds with total capital ($M), position bias (Long vs Short), and **Conviction Intensity Score (🔥)**.
3. **🔴 Short Intelligence**: FINRA short interest %, Days-to-Cover, Squeeze Risk ratings, and fundamental short theses.
4. **⚡ Activist Tracker**: SEC 13D/G 5%+ confirmed stake disclosures with ownership %, action type (ACTIVIST, CONTROL, PASSIVE), and value ($M).
5. **🌐 Conviction & Crowding**: 2×2 matrix separating *Hidden Alpha Opportunities* from *Crowding Risk*.
6. **🔥 Sector Heatmap**: Interactive 11 GICS sector exposure matrix across all 50 funds.
7. **🔮 Macro Futures**: CFTC futures tilts across equities, fixed income, commodities, and FX.
8. **🧪 System Architecture**: Multi-layer engine pipeline diagram and information flow.

---

## 🏗️ Architecture & Data Pipeline

```
[ Data Ingestion Layer ] ──> [ Quant Engines Layer ] ──> [ Multi-Timeframe Fusion ] ──> [ GitHub Pages Dashboard ]
 • SEC EDGAR (13F, 13D/G)     • E1 Adaptive Price Drift   • Stacking Meta-Ensemble    • Interactive HTML/CSS/JS
 • FINRA Short Interest       • E2 Kalman Filter RBSA     • Exposure Metrics Engine   • Chart.js Visualizer
 • SEC Reg SHO List           • E3 Bayesian Event Jump    • Conviction Intensity      • Weekly Status Indicator
 • CFTC CoT Futures           • E4 Delta Conversion       • Hidden Alpha / Crowding   • SEO & Schema.org Metadata
 • Form 4 Insider Trades      • E5 Short Thesis Model     • Static JSON Exporter      • Apache 2.0 Open Source
```

---

## 🔄 Weekly Update Workflow

Data updates are designed to run on a **Weekly Cycle** (recommended: weekends or Monday market pre-open).

### Automatic Status Indicator
The dashboard automatically calculates the difference between the page load date and the `last_updated` date in `meta_summary.json`:
- **≤ 7 days**: Displays `✓ Up to Date`
- **> 7 days**: Displays `⚠️ Update Needed (X days ago)`

### Weekly Data Update Prompt
To run a full update cycle, pass the following master prompt to the agent:

```text
전체 50개 주요 헤지펀드 유니버스에 대해 16개 데이터 수집 채널과 13개 정량 분석 엔진을 전면 재가동하고, 공시로 드러나지 않은 숨은 숏(Short) 포지션과 매크로 헤지까지 역추적 및 예측하여 github.io 웹사이트의 모든 데이터를 최신 상태로 갱신해줘.

1. python -m hedge_fund_predictor.export_static 실행을 통해 docs/data/ 내의 모든 JSON 파일(predictions.json, sector_heatmap.json, conviction_matrix.json, cftc_macro.json, short_intelligence.json, activist_filings.json, hf_universe.json 등)을 새로 빌드해줘.
2. meta_summary.json의 last_updated 타임스탬프를 현재 시점으로 업데이트해줘.
3. 변경된 JSON 데이터와 웹 프론트엔드 파일(docs/index.html, app.js, style.css)을 Git 커밋하고 origin main 브랜치에 push하여 https://eljja.github.io/Hedge 웹사이트에 반영해줘.
```

---

## 💻 Local Development

### Installation

```bash
git clone https://github.com/eljja/Hedge.git
cd Hedge
pip install -r requirements.txt
```

### Run Static Site Data Exporter

```bash
python -m hedge_fund_predictor.export_static
```

### Local Web Preview

```bash
python -m http.server 8000 --directory docs
```

Navigate to `http://localhost:8000` in your web browser.

---

## 🔍 Search Engine Optimization (SEO) & Web Standards

- **Google Site Verification**: Google Search Console verification meta tag included.
- **Sitemap & Robots**: `docs/sitemap.xml` and `docs/robots.txt` configured for search indexing.
- **Open Graph & Twitter Cards**: Full social sharing card support with rich metadata.
- **JSON-LD Schema.org**: WebApplication structured data schema for Google Rich Snippets.

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
