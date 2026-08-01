/**
 * Hedge Fund Position Predictor v6 — Premium Static Web Dashboard
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
  currentSort: { column: null, asc: true },

  async init() {
    this.bindEvents();
    await this.loadAllData();
    this.renderHeaderMetrics();
    this.populateStrategySelector();
    this.populateFundSelector();
    this.renderFundPredictions();
    this.renderTopHoldings();
    this.renderConvictionMatrix();
    this.renderSectorHeatmap();
    this.renderCFTCMacro();
  },

  bindEvents() {
    // Tabs
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

    // Selectors
    const stratSelect = document.getElementById("strategySelect");
    if (stratSelect) {
      stratSelect.addEventListener("change", () => {
        this.populateFundSelector();
        this.renderFundPredictions();
      });
    }

    const fundSelect = document.getElementById("fundSelect");
    if (fundSelect) {
      fundSelect.addEventListener("change", () => this.renderFundPredictions());
    }

    // Global Search
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => this.globalSearch(e.target.value));
    }

    // Table Sorting
    document.querySelectorAll("th[data-sort]").forEach(th => {
      th.addEventListener("click", () => this.handleSort(th));
    });
  },

  async loadAllData() {
    try {
      const [univ, pred, heat, conv, cftc, summary] = await Promise.all([
        fetch("data/hf_universe.json").then((r) => r.json()).catch(() => []),
        fetch("data/predictions.json").then((r) => r.json()).catch(() => ({})),
        fetch("data/sector_heatmap.json").then((r) => r.json()).catch(() => []),
        fetch("data/conviction_matrix.json").then((r) => r.json()).catch(() => ({})),
        fetch("data/cftc_macro.json").then((r) => r.json()).catch(() => ({})),
        fetch("data/meta_summary.json").then((r) => r.json()).catch(() => ({})),
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
      // Use meta_summary.json date, fallback to live
      let dateText = s.last_updated ? new Date(s.last_updated).toLocaleDateString() : 'Live';
      
      const sourceText = document.getElementById("dataSourceText");
      if (sourceText) {
          sourceText.innerText = `SEC EDGAR 13F (Updated: ${dateText})`;
      }

      if (lastUp) lastUp.innerText = `Last Updated: ${dateText}`;

      const icMetric = document.getElementById("metricIC");
      if (icMetric) icMetric.innerText = `+${s.metrics.spearman_ic}`;

      const brierMetric = document.getElementById("metricBrier");
      if (brierMetric) brierMetric.innerText = s.metrics.brier_score;

      const hitMetric = document.getElementById("metricHit");
      if (hitMetric) hitMetric.innerText = `${Math.round(s.metrics.top3_hit_rate * 100)}%`;
    }
  },

  populateStrategySelector() {
    const select = document.getElementById("strategySelect");
    if (!select || !this.data.universe.length) return;

    const strategies = [...new Set(this.data.universe.map(f => f.strategy))].filter(Boolean);
    strategies.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
      select.appendChild(opt);
    });
  },

  populateFundSelector() {
    const select = document.getElementById("fundSelect");
    const stratSelect = document.getElementById("strategySelect");
    if (!select || !this.data.universe.length) return;

    const selectedStrat = stratSelect ? stratSelect.value : "all";
    
    select.innerHTML = "";
    
    let filteredUniverse = this.data.universe;
    if (selectedStrat !== "all") {
        filteredUniverse = this.data.universe.filter(f => f.strategy === selectedStrat);
    }

    filteredUniverse.forEach((fund) => {
      const opt = document.createElement("option");
      opt.value = fund.id;
      opt.textContent = fund.name;
      select.appendChild(opt);
    });

    if (filteredUniverse.length > 0) {
        // Try to keep selection if valid
        const prevVal = select.getAttribute("data-prev");
        if (prevVal && filteredUniverse.find(f => f.id === prevVal)) {
            select.value = prevVal;
        } else {
            select.value = filteredUniverse[0].id;
        }
    }
  },

  getStrategyBadgeHtml(strategy) {
      if (!strategy) return "";
      const display = strategy.replace(/_/g, " ").toUpperCase();
      return `<span class="strat-badge strat-${strategy}">${display}</span>`;
  },

  getTypeHtml(type, putCall) {
      let isLong = true;
      if (type && type.toLowerCase() === 'short') isLong = false;
      if (putCall && putCall.toLowerCase() === 'put') isLong = false;
      
      if (isLong) {
          return `<span class="type-indicator type-long"><i data-lucide="trending-up"></i> LONG</span>`;
      } else {
          return `<span class="type-indicator type-short"><i data-lucide="trending-down"></i> SHORT</span>`;
      }
  },

  renderFundPredictions() {
    const select = document.getElementById("fundSelect");
    const container = document.getElementById("fundPositionsTable");
    const pvDisplay = document.getElementById("portfolioValue");
    if (!select || !container) return;

    const fundId = select.value;
    select.setAttribute("data-prev", fundId); // remember
    
    // Set PV
    const fundObj = this.data.universe.find(f => f.id === fundId);
    if (pvDisplay && fundObj && fundObj.aum_display) {
        pvDisplay.textContent = fundObj.aum_display;
    } else if (pvDisplay) {
        pvDisplay.textContent = "N/A";
    }

    const positions = this.data.predictions[fundId] || [];

    if (positions.length === 0) {
      container.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-muted);">No estimated positions available for this manager.</td></tr>`;
      lucide.createIcons();
      return;
    }

    let html = "";
    positions.forEach((p) => {
      const badgeClass = `badge-${p.rating ? p.rating.toLowerCase() : 'low'}`;
      html += `
        <tr>
          <td><strong style="color: var(--accent-blue);">${p.ticker || '-'}</strong></td>
          <td>${p.name || '-'}</td>
          <td>${p.sector || '-'}</td>
          <td>${this.getTypeHtml(p.type, p.putCall)}</td>
          <td><strong>${p.weight ? (p.weight * 100).toFixed(2) : '0.00'}%</strong></td>
          <td>${p.confidence ? p.confidence.toFixed(1) : '0.0'}%</td>
          <td><span class="badge ${badgeClass}">${p.rating || '-'}</span></td>
        </tr>
      `;
    });

    container.innerHTML = html;
    lucide.createIcons();
  },

  renderTopHoldings() {
      const container = document.getElementById("topHoldingsTable");
      if (!container || !this.data.predictions) return;

      const holdingsMap = {};
      
      // Aggregate across all funds
      Object.values(this.data.predictions).forEach(positions => {
          positions.forEach(p => {
              if (!p.ticker) return;
              if (!holdingsMap[p.ticker]) {
                  holdingsMap[p.ticker] = {
                      ticker: p.ticker,
                      name: p.name || '-',
                      sector: p.sector || '-',
                      count: 0,
                      longCount: 0,
                      shortCount: 0,
                      totalWeight: 0
                  };
              }
              holdingsMap[p.ticker].count += 1;
              if (p.type === 'SHORT' || p.putCall === 'PUT') {
                  holdingsMap[p.ticker].shortCount += 1;
              } else {
                  holdingsMap[p.ticker].longCount += 1;
              }
              holdingsMap[p.ticker].totalWeight += (p.weight || 0);
          });
      });

      const holdingsList = Object.values(holdingsMap);
      holdingsList.sort((a, b) => b.count - a.count); // sort by count desc

      const topHoldings = holdingsList.slice(0, 50); // top 50

      if (topHoldings.length === 0) {
          container.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted);">No holdings data.</td></tr>`;
          return;
      }

      let html = "";
      topHoldings.forEach(h => {
          const avgWeight = (h.totalWeight / h.count) * 100;
          let biasBadge = "";
          if (h.shortCount === 0) {
              biasBadge = `<span class="type-indicator type-long"><i data-lucide="trending-up"></i> LONG (100%)</span>`;
          } else if (h.longCount === 0) {
              biasBadge = `<span class="type-indicator type-short"><i data-lucide="trending-down"></i> SHORT (100%)</span>`;
          } else {
              biasBadge = `<span class="type-indicator type-long">LONG (${h.longCount})</span> / <span class="type-indicator type-short">SHORT (${h.shortCount})</span>`;
          }
          html += `
            <tr>
              <td><strong style="color: var(--accent-emerald);">${h.ticker}</strong></td>
              <td>${h.name}</td>
              <td><strong>${h.count}</strong> Funds</td>
              <td>${biasBadge}</td>
              <td>${avgWeight.toFixed(2)}%</td>
              <td>${h.sector}</td>
            </tr>
          `;
      });

      container.innerHTML = html;
      lucide.createIcons();
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
    if (!data || data.length === 0) return;

    // ALL 11 GICS Sectors
    const sectors = [
        "Information Technology", "Financials", "Health Care", "Consumer Discretionary", 
        "Communication Services", "Industrials", "Energy", "Materials", 
        "Real Estate", "Consumer Staples", "Utilities"
    ];

    let html = "";
    // Render ALL funds instead of slice(0,15)
    data.forEach((row) => {
      // Find strategy to add badge
      const fundObj = this.data.universe.find(f => f.name === row.fund_name || f.id === row.fund_id);
      const stratBadge = fundObj ? this.getStrategyBadgeHtml(fundObj.strategy) : "";

      html += `<tr><td><strong>${row.fund_name}</strong> <br> ${stratBadge}</td>`;
      sectors.forEach((sec) => {
        const val = row[sec] || 0;
        let bg = "transparent";
        if (val > 30) bg = "rgba(59, 130, 246, 0.5)";
        else if (val > 20) bg = "rgba(59, 130, 246, 0.35)";
        else if (val > 10) bg = "rgba(59, 130, 246, 0.2)";
        else if (val > 2) bg = "rgba(59, 130, 246, 0.08)";

        html += `<td class="heat-cell" style="background: ${bg};">${val > 0 ? val.toFixed(1) + '%' : '-'}</td>`;
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
  },

  globalSearch(query) {
    const q = query.toLowerCase().trim();
    
    // Search across all tab tables
    const tables = ["fundPositionsTable", "topHoldingsTable", "hiddenAlphaTable", "crowdingRiskTable", "sectorHeatmapTable", "cftcTable"];
    
    tables.forEach(tableId => {
        const rows = document.querySelectorAll(`#${tableId} tr`);
        rows.forEach((row) => {
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(q) ? "" : "none";
        });
    });
  },

  handleSort(th) {
      const table = th.closest('table');
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const sortType = th.getAttribute('data-sort');
      const index = Array.from(th.parentNode.children).indexOf(th);
      
      const isAsc = this.currentSort.column === sortType ? !this.currentSort.asc : true;
      this.currentSort = { column: sortType, asc: isAsc };

      rows.sort((a, b) => {
          const aCol = a.children[index].innerText;
          const bCol = b.children[index].innerText;
          
          let aVal = aCol.replace(/[^0-9.\-]/g, '');
          let bVal = bCol.replace(/[^0-9.\-]/g, '');
          
          if (!isNaN(parseFloat(aVal)) && !isNaN(parseFloat(bVal))) {
              return isAsc ? parseFloat(aVal) - parseFloat(bVal) : parseFloat(bVal) - parseFloat(aVal);
          }
          
          return isAsc ? aCol.localeCompare(bCol) : bCol.localeCompare(aCol);
      });

      tbody.innerHTML = '';
      rows.forEach(r => tbody.appendChild(r));
  }
};
