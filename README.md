# 🏛️ Hedge Fund Position Predictor

[![Live Web Dashboard](https://img.shields.io/badge/Live%20Dashboard-eljja.github.io%2FHedge-06B6D4?style=for-the-badge&logo=github)](https://eljja.github.io/Hedge)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-10B981?style=for-the-badge&logo=python)](https://python.org)

> 🌐 **Live Web Dashboard**: [https://eljja.github.io/Hedge](https://eljja.github.io/Hedge)  
> 📦 **GitHub Repository**: [https://github.com/eljja/Hedge](https://github.com/eljja/Hedge)

An institutional-grade hedge fund portfolio analytics and visualization platform tracking **50 global hedge funds** across 8 strategy categories.

---

## 🖥️ Dashboard Overview

1. **📊 Fund Positions**: Portfolio holdings, exposure summaries, and confidence tiers across 50 tracked managers.
2. **📈 Top Holdings**: Most widely held assets and capital concentration across the institutional universe.
3. **🔴 Short Intelligence**: Short interest metrics, borrow conditions, squeeze risk ratings, and institutional hedge signals.
4. **⚡ Activist 13D**: Confirmed SEC Schedule 13D/G ownership disclosures.
5. **🌐 Alpha & Crowding**: High-conviction low-overlap opportunities vs. crowded institutional positions.
6. **🔥 Sector Heatmap**: 11 GICS sector weight allocation matrix across all 50 funds.
7. **🔮 Macro Futures**: CFTC Commitments of Traders (COT) positioning and implied sector tilts.
8. **🧪 System Architecture**: High-level pipeline overview.

---

## 💻 Local Setup

```bash
git clone https://github.com/eljja/Hedge.git
cd Hedge
pip install -r requirements.txt
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000` in your browser.

---

## 📄 License

Licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
