/**
 * Hedge Fund Position Predictor v6 — Static Web Dashboard App
 * Target: GitHub Pages (https://eljja.github.io/Hedge)
 */

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});

const App = {
  data: {
    universe: [],
    predictions: {},
    sectorHeatmap: [],
    convictionMatrix: {},
    cftcMacro: {},
    metaSummary: {},
  },

  async init() {
    this.bindTabEvents();
    await this.loadAllData();
    this.renderHeaderMetrics();
    this.populateFundSelector();
    this.renderFundPredictions();
    this.renderConvictionMatrix();
    this.renderSectorHeatmap();
    this.renderCFTCMacro();
  },

  bindTabEvents() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");

        tabBtns.forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

        btn.classList.add("active");
        document.getElementById(targetTab).classList.add("active");
      });
    });

    const fundSelect = document.getElementById("fundSelect");
    if (fundSelect) {
      fundSelect.addEventListener("change", () => this.renderFundPredictions());
    }

    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => this.filterFundPositions(e.target.value));
    }
  },

  async loadAllData() {
    try {
      const [univ, pred, heat, conv, cftc, summary] = await Promise.all([
        fetch("data/hf_universe.json").then((r) => r.json()),
        fetch("data/predictions.json").then((r) => r.json()),
        fetch("data/sector_heatmap.json").then((r) => r.json()),
        fetch("data/conviction_matrix.json").then((r) => r.json()),
        fetch("data/cftc_macro.json").then((r) => r.json()),
        fetch("data/meta_summary.json").then((r) => r.json()),
      ]);

      this.data.universe = univ;
      this.data.predictions = pred;
      this.data.sectorHeatmap = heat;
      this.data.convictionMatrix = conv;
      this.data.cftcMacro = cftc;
      this.data.metaSummary = summary;
    } catch (err) {
      console.error("Error loading JSON data:", err);
    }
  },

  renderHeaderMetrics() {
    const s = this.data.metaSummary;
    if (s.metrics) {
      const lastUp = document.getElementById("lastUpdated");
      if (lastUp) lastUp.innerText = `Last Updated: ${s.last_updated ? s.last_updated.substring(0, 10) : 'Live'}`;

      const icMetric = document.getElementById("metricIC");
      if (icMetric) icMetric.innerText = `+${s.metrics.spearman_ic}`;

      const brierMetric = document.getElementById("metricBrier");
      if (brierMetric) brierMetric.innerText = s.metrics.brier_score;

      const hitMetric = document.getElementById("metricHit");
      if (hitMetric) hitMetric.innerText = `${Math.round(s.metrics.top3_hit_rate * 100)}%`;
    }
  },

  populateFundSelector() {
    const select = document.getElementById("fundSelect");
    if (!select) return;

    select.innerHTML = "";
    this.data.universe.forEach((fund) => {
      const opt = document.createElement("option");
      opt.value = fund.id;
      opt.textContent = `${fund.name} (${fund.strategy.replace("_", " ").toUpperCase()})`;
      select.appendChild(opt);
    });

    if (this.data.universe.length > 0) {
      select.value = "pershing_square"; // default highlight
    }
  },

  renderFundPredictions() {
    const select = document.getElementById("fundSelect");
    const container = document.getElementById("fundPositionsTable");
    if (!select || !container) return;

    const fundId = select.value;
    const positions = this.data.predictions[fundId] || [];

    if (positions.length === 0) {
      container.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted);">No estimated positions available for this manager.</td></tr>`;
      return;
    }

    let html = "";
    positions.forEach((p) => {
      const badgeClass = `badge-${p.rating.toLowerCase()}`;
      html += `
        <tr>
          <td><strong style="color: var(--accent-blue);">${p.ticker}</strong></td>
          <td>${p.name}</td>
          <td>${p.sector}</td>
          <td><strong>${(p.weight * 100).toFixed(1)}%</strong></td>
          <td>${p.confidence.toFixed(1)}%</td>
          <td><span class="badge ${badgeClass}">${p.rating}</span></td>
        </tr>
      `;
    });

    container.innerHTML = html;
  },

  filterFundPositions(query) {
    const q = query.toLowerCase().strip ? query.toLowerCase().strip() : query.toLowerCase();
    const rows = document.querySelectorAll("#fundPositionsTable tr");
    rows.forEach((row) => {
      const text = row.innerText.toLowerCase();
      row.style.display = text.includes(q) ? "" : "none";
    });
  },

  renderConvictionMatrix() {
    const hiddenContainer = document.getElementById("hiddenAlphaTable");
    const crowdContainer = document.getElementById("crowdingRiskTable");
    const m = this.data.convictionMatrix;

    if (hiddenContainer && m.hidden_alpha) {
      let html = "";
      m.hidden_alpha.forEach((item) => {
        html += `
          <tr>
            <td><strong style="color: var(--accent-emerald);">${item.ticker}</strong></td>
            <td>${item.name}</td>
            <td>${item.conviction_fund} (${item.conviction_weight})</td>
            <td>${item.confidence}%</td>
            <td style="font-size: 0.85rem; color: var(--text-secondary);">${item.rationale}</td>
          </tr>
        `;
      });
      hiddenContainer.innerHTML = html;
    }

    if (crowdContainer && m.crowding_risk) {
      let html = "";
      m.crowding_risk.forEach((item) => {
        html += `
          <tr>
            <td><strong style="color: var(--accent-rose);">${item.ticker}</strong></td>
            <td>${item.name}</td>
            <td>${item.holders_count} Funds</td>
            <td><span class="badge badge-low">${item.risk} RISK</span></td>
            <td style="font-size: 0.85rem; color: var(--text-secondary);">${item.rationale}</td>
          </tr>
        `;
      });
      crowdContainer.innerHTML = html;
    }
  },

  renderSectorHeatmap() {
    const container = document.getElementById("sectorHeatmapTable");
    if (!container) return;

    const data = this.data.sectorHeatmap;
    if (data.length === 0) return;

    const sectors = ["Information Technology", "Financials", "Health Care", "Consumer Discretionary", "Communication Services", "Industrials", "Energy"];

    let html = "";
    data.slice(0, 15).forEach((row) => {
      html += `<tr><td><strong>${row.fund_name}</strong></td>`;
      sectors.forEach((sec) => {
        const val = row[sec] || 0;
        let bg = "transparent";
        if (val > 25) bg = "rgba(59, 130, 246, 0.4)";
        else if (val > 15) bg = "rgba(59, 130, 246, 0.25)";
        else if (val > 5) bg = "rgba(59, 130, 246, 0.1)";

        html += `<td style="background: ${bg};">${val}%</td>`;
      });
      html += `</tr>`;
    });

    container.innerHTML = html;
  },

  renderCFTCMacro() {
    const container = document.getElementById("cftcTable");
    if (!container) return;

    const c = this.data.cftcMacro;
    if (!c.contracts) return;

    let html = "";
    c.contracts.forEach((item) => {
      const isBull = item.z_score > 0;
      const color = isBull ? "var(--accent-emerald)" : "var(--accent-rose)";
      html += `
        <tr>
          <td><strong>${item.name}</strong></td>
          <td>${item.category}</td>
          <td>${item.net_position}</td>
          <td style="color: ${color}; font-weight: 700;">${item.z_score > 0 ? '+' : ''}${item.z_score}σ</td>
          <td><span class="badge ${isBull ? 'badge-confirmed' : 'badge-low'}">${item.sentiment}</span></td>
        </tr>
      `;
    });

    container.innerHTML = html;
  }
};
