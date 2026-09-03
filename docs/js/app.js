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
  macroChart: null,
  currentChartType: "capital",

  async init() {
    this.bindEvents();
    await this.loadAllData();
    this.renderHeaderMetrics();
    this.populateStrategySelector();
    this.populateFundSelector();
    this.renderMacroChart();
    this.renderFundPredictions();
    this.renderTopHoldings();
    this.renderShortIntelligence();
    this.renderActivistFilings();
    this.renderConvictionMatrix();
    this.renderSectorHeatmap();
    this.renderCFTCMacro();
  },

  bindEvents() {
    // Chart toggle buttons
    const chartBtns = document.querySelectorAll(".chart-toggle-btn");
    chartBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        chartBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.currentChartType = btn.getAttribute("data-chart");
        this.renderMacroChart();
      });
    });

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
      const [univ, pred, heat, conv, cftc, summary, shortIntel, activist] = await Promise.all([
        fetch("data/hf_universe.json").then((r) => r.json()).catch(() => []),
        fetch("data/predictions.json").then((r) => r.json()).catch(() => ({})),
        fetch("data/sector_heatmap.json").then((r) => r.json()).catch(() => []),
        fetch("data/conviction_matrix.json").then((r) => r.json()).catch(() => ({})),
        fetch("data/cftc_macro.json").then((r) => r.json()).catch(() => ({})),
        fetch("data/meta_summary.json").then((r) => r.json()).catch(() => ({})),
        fetch("data/short_intelligence.json").then((r) => r.json()).catch(() => []),
        fetch("data/activist_filings.json").then((r) => r.json()).catch(() => []),
      ]);

      this.data.universe = univ;
      this.data.predictions = pred;
      this.data.sectorHeatmap = heat;
      this.data.convictionMatrix = conv;
      this.data.cftcMacro = cftc;
      this.data.metaSummary = summary;
      this.data.shortIntelligence = shortIntel;
      this.data.activistFilings = activist;
    } catch (err) {
      console.error("Error loading JSON data:", err);
    }
  },

  renderHeaderMetrics() {
    const s = this.data.metaSummary;
    if (s.metrics) {
      const lastUp = document.getElementById("lastUpdated");
      let dateObj = s.last_updated ? new Date(s.last_updated) : new Date();
      let dateText = dateObj.toLocaleDateString();
      
      // Calculate days difference from current client load time (Weekly cycle: 7 days)
      const now = new Date();
      const diffMs = now - dateObj;
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      let statusBadge = "";
      if (diffDays <= 7) {
        statusBadge = `<span style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); border: 1px solid rgba(16, 185, 129, 0.4); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; margin-left: 8px;">✓ Up to Date</span>`;
      } else {
        statusBadge = `<span style="background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; margin-left: 8px; cursor: pointer;" title="Last updated ${diffDays} days ago (Weekly Update Recommended)">⚠️ Update Needed (${diffDays}d ago)</span>`;
      }

      const sourceText = document.getElementById("dataSourceText");
      if (sourceText) {
        sourceText.innerHTML = `SEC EDGAR 13F (Updated: ${dateText}) ${statusBadge}`;
      }

      if (lastUp) lastUp.innerHTML = `Last Updated: ${dateText} ${statusBadge}`;

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

  renderMacroChart() {
    const canvas = document.getElementById("macroAnalyticsChart");
    if (!canvas || typeof Chart === "undefined" || !this.data.predictions) return;

    if (this.macroChart) {
      this.macroChart.destroy();
    }

    const type = this.currentChartType || "capital";
    let chartData = { labels: [], datasets: [] };
    let chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#8B949E", font: { size: 12 } } },
        tooltip: { mode: "index", intersect: false }
      },
      scales: {
        x: { ticks: { color: "#8B949E", autoSkip: false }, grid: { color: "rgba(48, 54, 61, 0.4)" } },
        y: { ticks: { color: "#8B949E", autoSkip: false, font: { size: 11 } }, grid: { color: "rgba(48, 54, 61, 0.4)" } }
      }
    };

    if (type === "capital") {
      // Top 15 Assets Capital ($M) Horizontal Bar
      const map = {};
      Object.values(this.data.predictions).forEach(positions => {
        positions.forEach(p => {
          if (!p.ticker) return;
          if (!map[p.ticker]) map[p.ticker] = { ticker: p.ticker, val: 0, isShort: (p.type === 'SHORT' || p.putCall === 'PUT') };
          map[p.ticker].val += (p.value_m || 0);
        });
      });
      const sorted = Object.values(map).sort((a, b) => b.val - a.val).slice(0, 15);
      chartData = {
        labels: sorted.map(s => s.ticker),
        datasets: [{
          label: "Total Est. Capital ($M)",
          data: sorted.map(s => Math.round(s.val)),
          backgroundColor: sorted.map(s => s.isShort ? "rgba(244, 63, 94, 0.8)" : "rgba(16, 185, 129, 0.8)"),
          borderColor: sorted.map(s => s.isShort ? "#F43F5E" : "#10B981"),
          borderWidth: 1,
          borderRadius: 6,
        }]
      };
      chartOptions.indexAxis = "y";

    } else if (type === "sector") {
      // Sector Capital ($M) across all funds
      const secMap = {};
      Object.values(this.data.predictions).forEach(positions => {
        positions.forEach(p => {
          const s = p.sector || "Other";
          if (!secMap[s]) secMap[s] = 0;
          secMap[s] += (p.value_m || 0);
        });
      });
      const sortedSecs = Object.entries(secMap).sort((a, b) => b[1] - a[1]);
      const colors = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#06B6D4", "#F43F5E", "#EC4899", "#F97316", "#64748B", "#14B8A6", "#A855F7"];
      chartData = {
        labels: sortedSecs.map(s => s[0]),
        datasets: [{
          label: "Capital Allocated ($M)",
          data: sortedSecs.map(s => Math.round(s[1])),
          backgroundColor: colors.slice(0, sortedSecs.length),
          borderRadius: 6
        }]
      };

    } else if (type === "strategy") {
      // AUM per Strategy ($M)
      const stratMap = {};
      this.data.universe.forEach(f => {
        const strat = f.strategy ? f.strategy.replace(/_/g, " ").toUpperCase() : "OTHER";
        const positions = this.data.predictions[f.id] || [];
        const totalVal = positions.reduce((sum, p) => sum + (p.value_m || 0), 0);
        stratMap[strat] = (stratMap[strat] || 0) + totalVal;
      });
      const sortedStrats = Object.entries(stratMap).sort((a, b) => b[1] - a[1]);
      const stratColors = ["#8B5CF6", "#10B981", "#F97316", "#F59E0B", "#F43F5E", "#3B82F6", "#06B6D4", "#EC4899"];
      chartData = {
        labels: sortedStrats.map(s => s[0]),
        datasets: [{
          label: "Total Strategy Capital ($M)",
          data: sortedStrats.map(s => Math.round(s[1])),
          backgroundColor: stratColors.slice(0, sortedStrats.length),
          borderRadius: 6
        }]
      };
    }

    const ctx = canvas.getContext("2d");
    this.macroChart = new Chart(ctx, {
      type: "bar",
      data: chartData,
      options: chartOptions
    });
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
      container.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--text-muted);">No estimated positions available for this manager.</td></tr>`;
      lucide.createIcons();
      return;
    }

    // Calculate Exposure
    let longVal = 0, shortVal = 0, longWeight = 0, shortWeight = 0;
    positions.forEach(p => {
      const isShort = (p.type === 'SHORT' || p.putCall === 'PUT');
      const val = p.value_m || 0;
      const w = p.weight || 0;
      if (isShort) {
        shortVal += val;
        shortWeight += w;
      } else {
        longVal += val;
        longWeight += w;
      }
    });

    const expLong = document.getElementById("expLong");
    const expShort = document.getElementById("expShort");
    const expNet = document.getElementById("expNet");
    const expGross = document.getElementById("expGross");

    if (expLong) expLong.textContent = `$${Math.round(longVal).toLocaleString()}M (${(longWeight * 100).toFixed(1)}%)`;
    if (expShort) expShort.textContent = `$${Math.round(shortVal).toLocaleString()}M (${(shortWeight * 100).toFixed(1)}%)`;
    if (expNet) expNet.textContent = `${((longWeight - shortWeight) * 100).toFixed(1)}%`;
    if (expGross) expGross.textContent = `${((longWeight + shortWeight) * 100).toFixed(1)}%`;

    let html = "";
    positions.forEach((p) => {
      const badgeClass = `badge-${p.rating ? p.rating.toLowerCase() : 'low'}`;
      const valDisplay = p.value_m ? `$${Math.round(p.value_m).toLocaleString()}M` : '-';
      html += `
        <tr>
          <td><strong style="color: var(--accent-blue);">${p.ticker || '-'}</strong></td>
          <td>${p.name || '-'}</td>
          <td>${p.sector || '-'}</td>
          <td>${this.getTypeHtml(p.type, p.putCall)}</td>
          <td><strong>${valDisplay}</strong></td>
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
                      totalWeight: 0,
                      totalValue: 0,
                      longValue: 0,
                      shortValue: 0,
                  };
              }
              const isShort = (p.type === 'SHORT' || p.putCall === 'PUT');
              const val = p.value_m || 0;
              holdingsMap[p.ticker].count += 1;
              holdingsMap[p.ticker].totalWeight += (p.weight || 0);
              holdingsMap[p.ticker].totalValue += val;
              if (isShort) {
                  holdingsMap[p.ticker].shortCount += 1;
                  holdingsMap[p.ticker].shortValue += val;
              } else {
                  holdingsMap[p.ticker].longCount += 1;
                  holdingsMap[p.ticker].longValue += val;
              }
          });
      });

      const holdingsList = Object.values(holdingsMap);
      holdingsList.sort((a, b) => b.totalValue - a.totalValue); // sort by total capital desc

      const topHoldings = holdingsList.slice(0, 50); // top 50

      if (topHoldings.length === 0) {
          container.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--text-muted);">No holdings data.</td></tr>`;
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

          // Conviction Intensity (0-100%)
          const netBiasRatio = (h.longCount - h.shortCount) / h.count;
          const intensityScore = Math.min(100, Math.round((h.count * 2) + (avgWeight * 8) + (netBiasRatio * 20)));
          const intensityColor = intensityScore > 75 ? 'var(--accent-emerald)' : (intensityScore > 50 ? 'var(--accent-cyan)' : 'var(--accent-amber)');

          html += `
            <tr>
              <td><strong style="color: var(--accent-emerald);">${h.ticker}</strong></td>
              <td>${h.name}</td>
              <td><strong>${h.count}</strong> Funds</td>
              <td>${biasBadge}</td>
              <td><strong>$${Math.round(h.totalValue).toLocaleString()}M</strong></td>
              <td>${avgWeight.toFixed(2)}%</td>
              <td><span style="color: ${intensityColor}; font-weight: 700;">🔥 ${intensityScore}%</span></td>
              <td>${h.sector}</td>
            </tr>
          `;
      });

      container.innerHTML = html;
      lucide.createIcons();
  },

  renderShortIntelligence() {
    const container = document.getElementById("shortIntelTable");
    if (!container) return;
    const data = this.data.shortIntelligence || [];
    if (!data.length) { container.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No short intelligence data available</td></tr>`; return; }

    container.innerHTML = data.map(item => {
      const siColor = item.short_interest_pct > 20 ? "var(--accent-red)" : (item.short_interest_pct > 10 ? "#f0ad4e" : "var(--text-muted)");
      const squeezeClass = item.squeeze_risk === "HIGH" ? "rating-badge bg-red" : (item.squeeze_risk === "MODERATE" ? "rating-badge bg-amber" : "rating-badge bg-dim");
      const daysColor = item.days_to_cover > 5 ? "var(--accent-red)" : (item.days_to_cover > 3 ? "#f0ad4e" : "var(--text-secondary)");
      const feeDisplay = item.borrow_fee_pct ? `${item.borrow_fee_pct.toFixed(1)}% (${item.borrow_status || 'HTB'})` : 'N/A';
      const feeColor = (item.borrow_fee_pct && item.borrow_fee_pct > 5) ? "var(--accent-red)" : "var(--text-secondary)";
      return `<tr>
        <td><strong style="color:var(--accent-red);">${item.ticker}</strong></td>
        <td style="color:${siColor};font-weight:700;">${item.short_interest_pct.toFixed(1)}%</td>
        <td style="color:${daysColor};">${item.days_to_cover.toFixed(1)}</td>
        <td style="color:${feeColor};font-size:0.85rem;font-weight:600;">${feeDisplay}</td>
        <td><span class="${squeezeClass}">${item.squeeze_risk}</span></td>
        <td style="font-size:0.82rem;color:var(--text-secondary);max-width:350px;">${item.thesis}</td>
      </tr>`;
    }).join("");
    if (typeof lucide !== "undefined") lucide.createIcons();
  },

  renderActivistFilings() {
    const container = document.getElementById("activistTable");
    if (!container) return;
    const data = this.data.activistFilings || [];
    if (!data.length) { container.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No activist filing data available</td></tr>`; return; }

    container.innerHTML = data.map(item => {
      const actionColor = item.action === "ACTIVIST" ? "var(--accent-red)" : (item.action === "CONTROL" ? "#a855f7" : "var(--accent-emerald)");
      const actionBadge = item.action === "ACTIVIST" ? "rating-badge bg-red" : (item.action === "CONTROL" ? "rating-badge bg-purple" : "rating-badge bg-emerald");
      const confColor = item.confidence >= 95 ? "var(--accent-emerald)" : "#f0ad4e";
      return `<tr>
        <td><strong>${item.fund}</strong></td>
        <td style="color:var(--accent-cyan);font-weight:600;">${item.ticker}</td>
        <td>${item.company}</td>
        <td style="color:${actionColor};font-weight:700;">${item.ownership_pct.toFixed(1)}%</td>
        <td style="font-weight:600;">$${item.value_m.toLocaleString()}M</td>
        <td><span class="${actionBadge}">${item.action}</span></td>
        <td style="color:${confColor};font-weight:600;">${item.confidence.toFixed(0)}%</td>
      </tr>`;
    }).join("");
    if (typeof lucide !== "undefined") lucide.createIcons();
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
    
    // Search across all 8 tab tables
    const tables = ["fundPositionsTable", "topHoldingsTable", "shortIntelTable", "activistTable", "hiddenAlphaTable", "crowdingRiskTable", "sectorHeatmapTable", "cftcTable"];
    
    tables.forEach(tableId => {
        const rows = document.querySelectorAll(`#${tableId} tr`);
        rows.forEach((row) => {
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(q) ? "" : "none";
        });
    });
  },

  exportTableCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = Array.from(table.querySelectorAll('tr'));
    const csvContent = rows.map(row => {
      const cols = Array.from(row.querySelectorAll('th, td'));
      return cols.map(c => `"${c.innerText.replace(/"/g, '""').trim()}"`).join(',');
    }).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
