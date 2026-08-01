# 🏛️ Hedge Fund Position Predictor v6 (Ultimate Quant Edition)

> **Live GitHub Pages Dashboard**: [https://eljja.github.io/Hedge](https://eljja.github.io/Hedge)  
> **GitHub Repository**: [https://github.com/eljja/Hedge](https://github.com/eljja/Hedge)

An institutional-grade hedge fund position prediction engine powered by **100% free public data channels**, featuring **14 data channels**, **11 prediction engines**, **5-horizon multi-timeframe signal fusion**, and **stacking meta-ensemble models**.

---

## 🌟 Key Features

- **100% Free & Open Source Data**: SEC DERA 13F bulk data, 13D/13G/Form 4 real-time filings, N-PORT, N-PX, EU Short Position Registers, CFTC Commitments of Traders (COT), yfinance, Fama-French 5-Factor, and OCC Options Open Interest.
- **11-Engine Quantitative Ensemble**:
  1. **E1 Adaptive Price Drift**: Stock price drift + turnover-based half-life confidence decay.
  2. **E2 Dynamic Kalman Filter RBSA**: 17-factor sector/theme exposure decomposition calibrated against listed HF vehicles (PSH, TPNT).
  3. **E3 Bayesian Event Jump**: Real-time event probability updating ($P > 0.95$ for 13D acquisitions).
  4. **E4 Options Delta Conversion**: Black-Scholes Delta transformation for 13F options.
  5. **E5 Conviction-Consensus Matrix**: 2×2 classification for *Hidden Alpha* vs *Crowding Risk*.
  6. **E6 Investor Letter NLP**: Sentiment analysis on letters and news feeds.
  7. **E7 CFTC Macro Positioning**: Leveraged Funds futures positioning mapped to sector tilts.
  8. **E8 13F Meta Signals**: Filing delay Z-score & Restatement Return Gap (Cao et al. 2026).
  9. **E9 GNN Herding Simulator**: Graph-based co-holding & director overlap message passing.
  10. **E10 Insider Correlation**: C-Suite Form 4 Code P concurrent buy 2.0x conviction booster.
  11. **E11 SEC Scrutiny Scanner**: Regulatory comment letter risk evaluation.
- **GitHub Pages Ready (`docs/`)**: Interactive, dark-mode web dashboard featuring live fund explorer, sector heatmaps, crowding matrix, and CFTC macro gauges.
- **Automated Daily GitHub Action**: Daily cron updates predictions and deploys to `github.io`.

---

## 🚀 Quick Setup & Deployment to `github.com/eljja/Hedge`

### 1. Push Code to GitHub

Open terminal in `D:\Code\Hedge` and run:

```bash
# Initialize git repository
git init
git branch -M main

# Add remote repository
git remote add origin https://github.com/eljja/Hedge.git

# Stage and commit files
git add .
git commit -m "Initial commit: Hedge Fund Position Predictor v6 & GitHub Pages Dashboard"

# Push to GitHub
git push -u origin main
```

### 2. Enable GitHub Pages on `https://github.com/eljja/Hedge`

1. Go to your repository on GitHub: **`https://github.com/eljja/Hedge/settings/pages`**
2. Under **Source**, select **GitHub Actions** (or `Deploy from a branch` -> `main` branch -> `/docs` folder).
3. Save settings. Your web dashboard will be live at:
   👉 **`https://eljja.github.io/Hedge`**

---

## 💻 Local Development

### Installation

```bash
pip install -r requirements.txt
```

### Run Phase Data Ingestion Pipeline

```bash
python -m hedge_fund_predictor
```

### Run Static Site Data Exporter

```bash
python -m hedge_fund_predictor.export_static
```

### Local Web Preview

Simply open `docs/index.html` in any web browser or use a local HTTP server:

```bash
python -m http.server 8000 --directory docs
```

Navigate to `http://localhost:8000`.

---

## 🧪 Integration Tests

```bash
python test_phase1.py   # Test storage, DuckDB, DERA loader
python test_phase2.py   # Test E1, E2, E3, E4, E7, Calibrator
python test_phase3.py   # Test E5-E11, Multi-Timeframe Fuser, Stacking Ensemble
```

---

## 📄 License

MIT License. Free to use for research and educational purposes.
