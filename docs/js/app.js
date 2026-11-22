/**
 * Hedge Fund Position Predictor v6.5 — Institutional Quant Dashboard Controller
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
    shortIntelligence: [],
    activistFilings: [],
  },
  state: {
    activeTab: "tab-predictions",
    chartType: "capital",
    posSideFilter: "all",
    topHoldingsFilter: "all",
    shortRiskFilter: "all",
    heatmapStrategy: "all",
    searchQuery: "",
  },
  sortState: {},
  macroChart: null,
  toastTimer: null,

  esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  },

  formatMoneyM(valM) {
    const n = Number(valM) || 0;
    if (Math.abs(n) >= 1000) {
      return `$${(n / 1000).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}B`;
    }
    return `$${Math.round(n).toLocaleString()}M`;
  },

  formatQuarter(dateStr) {
    if (!dateStr) return "Latest 13F";
    const m = /^(\d{4})-(\d{2})/.exec(dateStr);
    if (!m) return dateStr;
    const year = m[1];
    const q = Math.ceil(parseInt(m[2], 10) / 3);
    return `Q${q} ${year}`;
  },

  async init() {
    this.bindEvents();
    await this.loadAllData();
    this.renderHeaderMetrics();
    this.populateStrategySelectors();
    this.restoreHashState();
    this.populateFundSelector();
    this.renderMacroChart();
    this.renderFundPredictions();
    this.renderTopHoldings();
    this.renderShortIntelligence();
    this.renderActivistFilings();
    this.renderConvictionMatrix();
    this.renderSectorHeatmap();
    this.renderCFTCMacro();
    if (typeof lucide !== "undefined") lucide.createIcons();
  },

  bindEvents() {
    // Chart view toggles
    document.querySelectorAll(".chart-toggle-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".chart-toggle-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.state.chartType = btn.getAttribute("data-chart");
        this.renderMacroChart();
      });
    });

    // Tabs
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        this.switchTab(btn.getAttribute("data-tab"));
      });
    });

    // Fund Position selectors
    const stratSelect = document.getElementById("strategySelect");
    if (stratSelect) {
      stratSelect.addEventListener("change", () => {
        this.populateFundSelector();
        this.renderFundPredictions();
        this.applyGlobalSearch();
      });
    }

    const fundSelect = document.getElementById("fundSelect");
    if (fundSelect) {
      fundSelect.addEventListener("change", () => {
        this.renderFundPredictions();
        this.updateHashState();
        this.applyGlobalSearch();
      });
    }

    // Fund Position Side filter pills
    document.querySelectorAll("#posSideFilters .filter-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        document.querySelectorAll("#posSideFilters .filter-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        this.state.posSideFilter = pill.getAttribute("data-side");
        this.renderFundPredictions();
        this.applyGlobalSearch();
      });
    });

    // Top Holdings filter pills
    document.querySelectorAll("#topHoldingsFilters .filter-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        document.querySelectorAll("#topHoldingsFilters .filter-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        this.state.topHoldingsFilter = pill.getAttribute("data-th-filter");
        this.renderTopHoldings();
        this.applyGlobalSearch();
      });
    });

    // Short Risk filter pills
    document.querySelectorAll("#shortRiskFilters .filter-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        document.querySelectorAll("#shortRiskFilters .filter-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        this.state.shortRiskFilter = pill.getAttribute("data-risk");
        this.renderShortIntelligence();
        this.applyGlobalSearch();
      });
    });

    // Heatmap strategy filter
    const heatStrat = document.getElementById("heatmapStrategyFilter");
    if (heatStrat) {
      heatStrat.addEventListener("change", () => {
        this.state.heatmapStrategy = heatStrat.value;
        this.renderSectorHeatmap();
        this.applyGlobalSearch();
      });
    }

    // Global Search + Clear button
    const searchInput = document.getElementById("searchInput");
    const clearBtn = document.getElementById("searchClearBtn");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.state.searchQuery = e.target.value;
        if (clearBtn) clearBtn.classList.toggle("hidden", !this.state.searchQuery.trim());
        this.applyGlobalSearch();
      });
    }
    if (clearBtn && searchInput) {
      clearBtn.addEventListener("click", () => {
        searchInput.value = "";
        this.state.searchQuery = "";
        clearBtn.classList.add("hidden");
        this.applyGlobalSearch();
        searchInput.focus();
      });
    }

    // Quick inspect ticker chips
    document.querySelectorAll(".quick-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const ticker = chip.getAttribute("data-inspect");
        if (ticker) this.openTickerModal(ticker);
      });
    });

    // Table sorting
    document.querySelectorAll("th[data-sort]").forEach((th) => {
      th.addEventListener("click", () => this.handleSort(th));
    });

    // Event delegation for ticker deep-dive & fund jump links across all tables & modal
    document.addEventListener("click", (e) => {
      const tickerBtn = e.target.closest("[data-open-ticker]");
      if (tickerBtn) {
        e.preventDefault();
        this.openTickerModal(tickerBtn.getAttribute("data-open-ticker"));
        return;
      }
      const fundBtn = e.target.closest("[data-jump-fund]");
      if (fundBtn) {
        e.preventDefault();
        this.jumpToFund(fundBtn.getAttribute("data-jump-fund"));
        return;
      }
    });

    // Modal close handlers
    const modal = document.getElementById("tickerModal");
    const closeBtn = document.getElementById("modalCloseBtn");
    if (closeBtn) closeBtn.addEventListener("click", () => this.closeTickerModal());
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) this.closeTickerModal();
      });
    }

    // Keyboard shortcuts: "/" to search, "Esc" to close modal or clear search
    document.addEventListener("keydown", (e) => {
      const modalOpen = modal && !modal.classList.contains("hidden");
      if (e.key === "Escape") {
        if (modalOpen) {
          this.closeTickerModal();
        } else if (searchInput && (document.activeElement === searchInput || this.state.searchQuery)) {
          searchInput.value = "";
          this.state.searchQuery = "";
          if (clearBtn) clearBtn.classList.add("hidden");
          this.applyGlobalSearch();
          searchInput.blur();
        }
      } else if (e.key === "/" && !modalOpen) {
        const tag = (document.activeElement?.tagName || "").toLowerCase();
        if (tag !== "input" && tag !== "textarea" && tag !== "select") {
          e.preventDefault();
          searchInput?.focus();
        }
      }
    });
  },

  switchTab(tabId) {
    const target = document.getElementById(tabId);
    if (!target) return;
    this.state.activeTab = tabId;
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
    });
    document.querySelectorAll(".tab-content").forEach((c) => {
      c.classList.toggle("active", c.id === tabId);
    });
    this.updateHashState();
  },

  jumpToFund(fundId) {
    if (!fundId) return;
    this.closeTickerModal();
    const stratSelect = document.getElementById("strategySelect");
    const fundSelect = document.getElementById("fundSelect");
    if (stratSelect && stratSelect.value !== "all") {
      stratSelect.value = "all";
      this.populateFundSelector();
    }
    if (fundSelect && this.data.universe.some((f) => f.id === fundId)) {
      fundSelect.value = fundId;
      this.renderFundPredictions();
    }
    this.switchTab("tab-predictions");
    const bar = document.getElementById("fundExposureBar");
    if (bar) bar.scrollIntoView({ behavior: "smooth", block: "start" });
  },

  restoreHashState() {
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) return;
    const params = new URLSearchParams(hash);
    const tab = params.get("tab");
    const fund = params.get("fund");
    if (tab && document.getElementById(tab)) {
      this.switchTab(tab);
    }
    if (fund) {
      const fundSelect = document.getElementById("fundSelect");
      if (fundSelect) fundSelect.setAttribute("data-prev", fund);
    }
  },

  updateHashState() {
    const fundSelect = document.getElementById("fundSelect");
    const params = new URLSearchParams();
    params.set("tab", this.state.activeTab);
    if (fundSelect && fundSelect.value) params.set("fund", fundSelect.value);
    history.replaceState(null, "", `#${params.toString()}`);
  },

  async loadAllData() {
    const bust = `?v=${Date.now().toString().slice(0, -4)}`;
    try {
      const [univ, pred, heat, conv, cftc, summary, shortIntel, activist] = await Promise.all([
        fetch(`data/hf_universe.json${bust}`).then((r) => r.json()).catch(() => []),
        fetch(`data/predictions.json${bust}`).then((r) => r.json()).catch(() => ({})),
        fetch(`data/sector_heatmap.json${bust}`).then((r) => r.json()).catch(() => []),
        fetch(`data/conviction_matrix.json${bust}`).then((r) => r.json()).catch(() => ({})),
        fetch(`data/cftc_macro.json${bust}`).then((r) => r.json()).catch(() => ({})),
        fetch(`data/meta_summary.json${bust}`).then((r) => r.json()).catch(() => ({})),
        fetch(`data/short_intelligence.json${bust}`).then((r) => r.json()).catch(() => []),
        fetch(`data/activist_filings.json${bust}`).then((r) => r.json()).catch(() => []),
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
      this.showToast("Failed to load some datasets. Please refresh.");
    }
  },

  renderHeaderMetrics() {
    const s = this.data.metaSummary || {};
    const dateObj = s.last_updated ? new Date(s.last_updated) : new Date();
    const dateISO = isNaN(dateObj.getTime()) ? "Live" : dateObj.toISOString().slice(0, 10);

    const diffDays = isNaN(dateObj.getTime())
      ? 0
      : Math.max(0, Math.floor((Date.now() - dateObj.getTime()) / (1000 * 60 * 60 * 24)));

    const isFresh = diffDays <= 7;
    const statusBadge = isFresh
      ? `<span class="status-pill status-pill-ok">✓ Up to Date</span>`
      : `<span class="status-pill status-pill-warn" title="Last updated ${diffDays} days ago (Weekly update recommended)">⚠ Update Needed (${diffDays}d ago)</span>`;

    const pulseDot = document.getElementById("livePulseDot");
    if (pulseDot) pulseDot.classList.toggle("stale", !isFresh);

    const quarterLabel = s.latest_report_date ? this.formatQuarter(s.latest_report_date) : "Latest";

    const sourceText = document.getElementById("dataSourceText");
    if (sourceText) {
      sourceText.innerHTML = `SEC EDGAR ${this.esc(quarterLabel)} • Updated ${this.esc(dateISO)} ${statusBadge}`;
    }

    const heroQ = document.getElementById("heroFilingQuarter");
    if (heroQ) {
      const realCnt = s.funds_with_real_data ?? 0;
      const totCnt = s.funds_count ?? this.data.universe.length;
      heroQ.textContent = `Live SEC EDGAR ${quarterLabel} 13F-HR • ${realCnt}/${totCnt} Funds Verified`;
    }

    const heroSub = document.getElementById("heroSubtitle");
    if (heroSub && s.channels_active && s.engines_active) {
      heroSub.textContent = `100% Free Public Data Pipeline • ${s.channels_active} Information Channels • ${s.engines_active} Quant Analytics Engines • Multi-Timeframe Fusion`;
    }

    const metricFunds = document.getElementById("metricFunds");
    const metricReal = document.getElementById("metricRealCoverage");
    if (metricFunds) metricFunds.textContent = `${s.funds_count || this.data.universe.length} Top Funds`;
    if (metricReal) {
      const realCnt = s.funds_with_real_data ?? 0;
      const totCnt = s.funds_count || this.data.universe.length;
      metricReal.innerHTML = `<span class="text-emerald">${realCnt}/${totCnt} Live SEC 13F-HR</span> • 8 Strategies`;
    }

    const metricAUM = document.getElementById("metricAUM");
    if (metricAUM && s.total_tracked_aum_billions) {
      const b = Number(s.total_tracked_aum_billions);
      metricAUM.textContent = b >= 1000 ? `$${(b / 1000).toFixed(2)}T` : `$${b.toLocaleString()}B`;
    }

    const metricEngines = document.getElementById("metricEngines");
    const metricChannels = document.getElementById("metricChannels");
    if (metricEngines && s.engines_active) metricEngines.textContent = `${s.engines_active} Engines`;
    if (metricChannels && s.channels_active) metricChannels.textContent = `${s.channels_active} Active Data Channels • Fusion`;

    const metricHit = document.getElementById("metricHit");
    if (metricHit && s.metrics?.top3_hit_rate) {
      metricHit.textContent = `${Math.round(s.metrics.top3_hit_rate * 100)}% Hit Rate`;
    }

    const lastUp = document.getElementById("lastUpdated");
    if (lastUp) {
      lastUp.innerHTML = `Updated ${this.esc(dateISO)} ${statusBadge}`;
    }
  },

  populateStrategySelectors() {
    const counts = {};
    this.data.universe.forEach((f) => {
      if (f.strategy) counts[f.strategy] = (counts[f.strategy] || 0) + 1;
    });
    const strategies = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);

    ["strategySelect", "heatmapStrategyFilter"].forEach((id) => {
      const select = document.getElementById(id);
      if (!select) return;
      select.innerHTML = `<option value="all">All Strategies (${this.data.universe.length})</option>`;
      strategies.forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s;
        const label = s.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
        opt.textContent = `${label} (${counts[s]})`;
        select.appendChild(opt);
      });
    });
  },

  populateFundSelector() {
    const select = document.getElementById("fundSelect");
    const stratSelect = document.getElementById("strategySelect");
    if (!select || !this.data.universe.length) return;

    const selectedStrat = stratSelect ? stratSelect.value : "all";
    const prevVal = select.value || select.getAttribute("data-prev");

    select.innerHTML = "";
    const filtered = selectedStrat === "all"
      ? this.data.universe
      : this.data.universe.filter((f) => f.strategy === selectedStrat);

    filtered.forEach((fund) => {
      const opt = document.createElement("option");
      opt.value = fund.id;
      const tag = fund.data_source === "SEC 13F-HR" ? "✓" : "~";
      opt.textContent = `${tag} ${fund.name} (${fund.aum_display})`;
      select.appendChild(opt);
    });

    if (filtered.length > 0) {
      if (prevVal && filtered.some((f) => f.id === prevVal)) {
        select.value = prevVal;
      } else {
        select.value = filtered[0].id;
      }
    }
  },

  getStrategyBadgeHtml(strategy) {
    if (!strategy) return "";
    const display = strategy.replace(/_/g, " ").toUpperCase();
    return `<span class="strat-badge strat-${this.esc(strategy)}">${this.esc(display)}</span>`;
  },

  renderMacroChart() {
    const canvas = document.getElementById("macroAnalyticsChart");
    const subtitle = document.getElementById("chartSubtitle");
    if (!canvas || typeof Chart === "undefined" || !this.data.predictions) return;

    if (this.macroChart) {
      this.macroChart.destroy();
    }

    const type = this.state.chartType || "capital";
    let chartConfig = null;

    const commonPlugins = {
      legend: {
        labels: { color: "#9CA3AF", font: { size: 12, family: "Inter, sans-serif" }, boxWidth: 12, padding: 14 },
      },
      tooltip: {
        backgroundColor: "rgba(13, 17, 23, 0.96)",
        borderColor: "rgba(96, 165, 250, 0.4)",
        borderWidth: 1,
        titleColor: "#F0F6FC",
        bodyColor: "#CBD5E1",
        padding: 10,
      },
    };

    if (type === "capital") {
      if (subtitle) subtitle.textContent = "Top 15 assets by total disclosed institutional capital — Stacked Long Equity/Call (Green) vs. Disclosed 13F PUT Hedges (Rose)";
      const map = {};
      Object.values(this.data.predictions).forEach((positions) => {
        positions.forEach((p) => {
          if (!p.ticker) return;
          if (!map[p.ticker]) map[p.ticker] = { ticker: p.ticker, name: p.name || "", longVal: 0, shortVal: 0 };
          const val = p.value_m || 0;
          if (p.type === "SHORT" || p.putCall === "PUT") map[p.ticker].shortVal += val;
          else map[p.ticker].longVal += val;
        });
      });
      const sorted = Object.values(map)
        .sort((a, b) => (b.longVal + b.shortVal) - (a.longVal + a.shortVal))
        .slice(0, 15);

      chartConfig = {
        type: "bar",
        data: {
          labels: sorted.map((s) => s.ticker),
          datasets: [
            {
              label: "Long Capital ($M)",
              data: sorted.map((s) => Math.round(s.longVal)),
              backgroundColor: "rgba(16, 185, 129, 0.82)",
              borderColor: "#10B981",
              borderWidth: 1,
              borderRadius: 4,
            },
            {
              label: "Short / 13F PUT ($M)",
              data: sorted.map((s) => Math.round(s.shortVal)),
              backgroundColor: "rgba(244, 63, 94, 0.82)",
              borderColor: "#F43F5E",
              borderWidth: 1,
              borderRadius: 4,
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            ...commonPlugins,
            tooltip: {
              ...commonPlugins.tooltip,
              mode: "index",
              intersect: false,
              callbacks: {
                label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.x.toLocaleString()}M`,
              },
            },
          },
          scales: {
            x: {
              stacked: true,
              ticks: { color: "#9CA3AF", callback: (v) => `$${(v / 1000).toFixed(0)}B` },
              grid: { color: "rgba(56, 68, 86, 0.3)" },
            },
            y: {
              stacked: true,
              ticks: { color: "#E5E7EB", autoSkip: false, font: { size: 11, family: "JetBrains Mono, monospace", weight: "600" } },
              grid: { display: false },
            },
          },
        },
      };
    } else if (type === "sector") {
      if (subtitle) subtitle.textContent = "Aggregated capital & percentage share across GICS sectors & asset classes";
      const secMap = {};
      let grandTotal = 0;
      Object.values(this.data.predictions).forEach((positions) => {
        positions.forEach((p) => {
          const s = p.sector || "Other";
          const val = p.value_m || 0;
          secMap[s] = (secMap[s] || 0) + val;
          grandTotal += val;
        });
      });
      const sortedSecs = Object.entries(secMap).sort((a, b) => b[1] - a[1]);
      const palette = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#06B6D4", "#F43F5E", "#EC4899", "#F97316", "#14B8A6", "#A855F7", "#64748B", "#84CC16", "#EAB308"];

      chartConfig = {
        type: "bar",
        data: {
          labels: sortedSecs.map(([sec, val]) => `${sec} (${grandTotal ? ((val / grandTotal) * 100).toFixed(1) : 0}%)`),
          datasets: [{
            label: "Allocated Capital ($B)",
            data: sortedSecs.map(([, val]) => Number((val / 1000).toFixed(1))),
            backgroundColor: sortedSecs.map((_, i) => palette[i % palette.length]),
            borderRadius: 5,
          }],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            ...commonPlugins,
            legend: { display: false },
            tooltip: {
              ...commonPlugins.tooltip,
              callbacks: {
                label: (ctx) => `$${ctx.parsed.x.toLocaleString()}B`,
              },
            },
          },
          scales: {
            x: {
              ticks: { color: "#9CA3AF", callback: (v) => `$${v}B` },
              grid: { color: "rgba(56, 68, 86, 0.3)" },
            },
            y: {
              ticks: { color: "#E5E7EB", autoSkip: false, font: { size: 11 } },
              grid: { display: false },
            },
          },
        },
      };
    } else if (type === "strategy") {
      if (subtitle) subtitle.textContent = "Total disclosed 13F capital ($B) grouped by hedge fund strategy";
      const stratMap = {};
      this.data.universe.forEach((f) => {
        const strat = f.strategy ? f.strategy.replace(/_/g, " ").toUpperCase() : "OTHER";
        stratMap[strat] = (stratMap[strat] || 0) + (f.total_13f_value_m || 0);
      });
      const sortedStrats = Object.entries(stratMap).sort((a, b) => b[1] - a[1]);
      const stratColors = ["#8B5CF6", "#10B981", "#F97316", "#F59E0B", "#F43F5E", "#3B82F6", "#06B6D4", "#EC4899"];

      chartConfig = {
        type: "bar",
        data: {
          labels: sortedStrats.map((s) => s[0]),
          datasets: [{
            label: "Total 13F Capital ($B)",
            data: sortedStrats.map((s) => Number((s[1] / 1000).toFixed(1))),
            backgroundColor: stratColors.slice(0, sortedStrats.length),
            borderRadius: 6,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            ...commonPlugins,
            legend: { display: false },
            tooltip: {
              ...commonPlugins.tooltip,
              callbacks: { label: (ctx) => `$${ctx.parsed.y.toLocaleString()}B` },
            },
          },
          scales: {
            x: { ticks: { color: "#E5E7EB", autoSkip: false, font: { size: 11 } }, grid: { display: false } },
            y: { ticks: { color: "#9CA3AF", callback: (v) => `$${v}B` }, grid: { color: "rgba(56, 68, 86, 0.3)" } },
          },
        },
      };
    } else if (type === "strategy_ls") {
      if (subtitle) subtitle.textContent = "Long Equity/Call vs. Disclosed 13F PUT Hedge capital ($B) across all 8 hedge fund strategies";
      const stratMap = {};
      this.data.universe.forEach((f) => {
        const strat = f.strategy ? f.strategy.replace(/_/g, " ").toUpperCase() : "OTHER";
        if (!stratMap[strat]) stratMap[strat] = { longVal: 0, shortVal: 0 };
        const positions = this.data.predictions[f.id] || [];
        positions.forEach((p) => {
          const v = p.value_m || 0;
          if (p.type === "SHORT" || p.putCall === "PUT") stratMap[strat].shortVal += v;
          else stratMap[strat].longVal += v;
        });
      });
      const sortedStrats = Object.entries(stratMap).sort((a, b) => (b[1].longVal + b[1].shortVal) - (a[1].longVal + a[1].shortVal));

      chartConfig = {
        type: "bar",
        data: {
          labels: sortedStrats.map((s) => s[0]),
          datasets: [
            {
              label: "Top Book Long ($B)",
              data: sortedStrats.map((s) => Number((s[1].longVal / 1000).toFixed(1))),
              backgroundColor: "rgba(16, 185, 129, 0.82)",
              borderRadius: 5,
            },
            {
              label: "Disclosed 13F PUT / Short ($B)",
              data: sortedStrats.map((s) => Number((s[1].shortVal / 1000).toFixed(1))),
              backgroundColor: "rgba(244, 63, 94, 0.82)",
              borderRadius: 5,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            ...commonPlugins,
            tooltip: {
              ...commonPlugins.tooltip,
              mode: "index",
              intersect: false,
              callbacks: { label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.y.toLocaleString()}B` },
            },
          },
          scales: {
            x: { ticks: { color: "#E5E7EB", autoSkip: false, font: { size: 11 } }, grid: { display: false } },
            y: { ticks: { color: "#9CA3AF", callback: (v) => `$${v}B` }, grid: { color: "rgba(56, 68, 86, 0.3)" } },
          },
        },
      };
    }

    if (chartConfig) {
      this.macroChart = new Chart(canvas.getContext("2d"), chartConfig);
    }
  },

  getTypeHtml(type, putCall, instrument) {
    const isShort = type === "SHORT" || (putCall && putCall.toUpperCase() === "PUT");
    const inst = instrument || (putCall ? putCall.toUpperCase() : "EQUITY");
    const instBadge = inst !== "EQUITY" ? `<span class="inst-tag">${this.esc(inst)}</span>` : "";

    if (!isShort) {
      return `<span class="type-indicator type-long"><i data-lucide="trending-up"></i> LONG${instBadge}</span>`;
    }
    return `<span class="type-indicator type-short"><i data-lucide="trending-down"></i> SHORT${instBadge}</span>`;
  },

  renderFundPredictions() {
    const select = document.getElementById("fundSelect");
    const container = document.getElementById("fundPositionsTable");
    if (!select || !container) return;

    const fundId = select.value;
    select.setAttribute("data-prev", fundId);
    const fundObj = this.data.universe.find((f) => f.id === fundId);
    const allPositions = this.data.predictions[fundId] || [];

    // Update fund identity header
    const nameEl = document.getElementById("selectedFundName");
    const stratEl = document.getElementById("selectedFundStratBadge");
    const srcEl = document.getElementById("selectedFundSourceBadge");
    const repEl = document.getElementById("selectedFundReportDate");
    const cntEl = document.getElementById("selectedFundTotalPositions");
    const pvEl = document.getElementById("portfolioValue");
    const secLink = document.getElementById("fundSecLink");

    if (nameEl) nameEl.textContent = fundObj ? fundObj.name : fundId;
    if (stratEl) stratEl.innerHTML = fundObj ? this.getStrategyBadgeHtml(fundObj.strategy) : "";
    if (srcEl && fundObj) {
      const isReal = fundObj.data_source === "SEC 13F-HR";
      srcEl.textContent = isReal ? "✓ Live SEC 13F-HR" : "Model Estimate";
      srcEl.classList.toggle("estimated", !isReal);
    }
    if (repEl) {
      repEl.textContent = fundObj?.report_date
        ? `${this.formatQuarter(fundObj.report_date)} (${fundObj.report_date})`
        : "Model Est.";
    }
    if (cntEl) {
      cntEl.textContent = fundObj?.positions_count
        ? `${fundObj.positions_count.toLocaleString()} Total 13F Lines`
        : `${allPositions.length} Positions`;
    }
    if (pvEl) pvEl.textContent = fundObj?.aum_display || "N/A";
    if (secLink && fundObj?.sec_url) secLink.href = fundObj.sec_url;

    // Exposure calculation over all positions of this fund
    let longVal = 0, shortVal = 0, longWeight = 0, shortWeight = 0;
    allPositions.forEach((p) => {
      const isShort = p.type === "SHORT" || p.putCall === "PUT";
      if (isShort) {
        shortVal += p.value_m || 0;
        shortWeight += p.weight || 0;
      } else {
        longVal += p.value_m || 0;
        longWeight += p.weight || 0;
      }
    });

    const expLong = document.getElementById("expLong");
    const expShort = document.getElementById("expShort");
    const expNet = document.getElementById("expNet");
    const expGross = document.getElementById("expGross");
    const splitLong = document.getElementById("expSplitLong");
    const splitShort = document.getElementById("expSplitShort");

    if (expLong) expLong.textContent = `${this.formatMoneyM(longVal)} (${(longWeight * 100).toFixed(1)}%)`;
    if (expShort) expShort.textContent = `${this.formatMoneyM(shortVal)} (${(shortWeight * 100).toFixed(1)}%)`;
    if (expNet) expNet.textContent = `${((longWeight - shortWeight) * 100).toFixed(1)}%`;
    if (expGross) expGross.textContent = `${((longWeight + shortWeight) * 100).toFixed(1)}%`;

    const totLS = longVal + shortVal;
    const longShare = totLS > 0 ? (longVal / totLS) * 100 : 100;
    if (splitLong) splitLong.style.width = `${longShare.toFixed(1)}%`;
    if (splitShort) splitShort.style.width = `${(100 - longShare).toFixed(1)}%`;

    // Apply position side filter
    const side = this.state.posSideFilter;
    const filtered = allPositions.filter((p) => {
      if (side === "all") return true;
      const isShort = p.type === "SHORT" || p.putCall === "PUT";
      return side === "SHORT" ? isShort : !isShort;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<tr class="empty-row"><td colspan="8" style="text-align:center; padding: 28px; color: var(--text-muted);">No ${side === "SHORT" ? "disclosed 13F PUT / Short" : ""} positions for this manager.</td></tr>`;
      return;
    }

    const maxWeight = Math.max(...filtered.map((p) => p.weight || 0), 0.01);

    container.innerHTML = filtered
      .map((p) => {
        const isShort = p.type === "SHORT" || p.putCall === "PUT";
        const badgeClass = `badge-${(p.rating || "low").toLowerCase()}`;
        const wPct = (p.weight || 0) * 100;
        const barW = Math.min(100, (p.weight / maxWeight) * 100);
        const tickerCls = isShort ? "ticker-btn ticker-short" : "ticker-btn";
        const valM = p.value_m || 0;

        return `<tr>
          <td data-sort-val="${this.esc(p.ticker)}">
            <button class="${tickerCls}" data-open-ticker="${this.esc(p.ticker)}" title="Inspect ${this.esc(p.ticker)} across all 50 funds">${this.esc(p.ticker)}</button>
          </td>
          <td>${this.esc(p.name || "-")}</td>
          <td style="color: var(--text-secondary);">${this.esc(p.sector || "-")}</td>
          <td data-sort-val="${isShort ? "SHORT" : "LONG"}">${this.getTypeHtml(p.type, p.putCall, p.instrument)}</td>
          <td class="num-col" data-sort-val="${valM}"><strong>${this.formatMoneyM(valM)}</strong></td>
          <td class="num-col" data-sort-val="${wPct}">
            <div class="bar-cell">
              <strong>${wPct.toFixed(2)}%</strong>
              <div class="micro-bar-track"><div class="micro-bar-fill ${isShort ? "fill-rose" : "fill-emerald"}" style="width:${barW.toFixed(1)}%"></div></div>
            </div>
          </td>
          <td class="num-col" data-sort-val="${p.confidence || 0}">${(p.confidence || 0).toFixed(0)}%</td>
          <td><span class="badge ${badgeClass}">${this.esc(p.rating || "-")}</span></td>
        </tr>`;
      })
      .join("");

    if (typeof lucide !== "undefined") lucide.createIcons();
  },

  renderTopHoldings() {
    const container = document.getElementById("topHoldingsTable");
    if (!container || !this.data.predictions) return;

    const holdingsMap = {};
    Object.entries(this.data.predictions).forEach(([fundId, positions]) => {
      positions.forEach((p) => {
        if (!p.ticker) return;
        if (!holdingsMap[p.ticker]) {
          holdingsMap[p.ticker] = {
            ticker: p.ticker,
            name: p.name || "-",
            sector: p.sector || "-",
            fundsSet: new Set(),
            longFunds: new Set(),
            shortFunds: new Set(),
            totalWeight: 0,
            entries: 0,
            totalValue: 0,
            longValue: 0,
            shortValue: 0,
          };
        }
        const h = holdingsMap[p.ticker];
        const isShort = p.type === "SHORT" || p.putCall === "PUT";
        const val = p.value_m || 0;
        h.fundsSet.add(fundId);
        h.entries += 1;
        h.totalWeight += p.weight || 0;
        h.totalValue += val;
        if (isShort) {
          h.shortFunds.add(fundId);
          h.shortValue += val;
        } else {
          h.longFunds.add(fundId);
          h.longValue += val;
        }
      });
    });

    let list = Object.values(holdingsMap).map((h) => ({
      ...h,
      count: h.fundsSet.size,
      longCount: h.longFunds.size,
      shortCount: h.shortFunds.size,
    }));

    const mode = this.state.topHoldingsFilter;
    if (mode === "long") list = list.filter((h) => h.shortCount === 0);
    else if (mode === "hedged") list = list.filter((h) => h.longCount > 0 && h.shortCount > 0);
    else if (mode === "short") list = list.filter((h) => h.shortValue > h.longValue || h.longCount === 0);

    list.sort((a, b) => b.totalValue - a.totalValue);
    const topHoldings = list.slice(0, 60);

    if (topHoldings.length === 0) {
      container.innerHTML = `<tr class="empty-row"><td colspan="8" style="text-align:center; padding: 28px; color: var(--text-muted);">No matching holdings for this filter.</td></tr>`;
      return;
    }

    container.innerHTML = topHoldings
      .map((h) => {
        const avgWeight = (h.totalWeight / Math.max(1, h.entries)) * 100;
        const longPct = h.totalValue > 0 ? (h.longValue / h.totalValue) * 100 : 100;
        const shortPct = 100 - longPct;

        let biasLabel = "";
        if (h.shortCount === 0) {
          biasLabel = `<span class="type-indicator type-long">LONG ${h.longCount}</span>`;
        } else if (h.longCount === 0) {
          biasLabel = `<span class="type-indicator type-short">SHORT ${h.shortCount}</span>`;
        } else {
          biasLabel = `<span class="type-indicator type-long">L:${h.longCount}</span> <span style="color:var(--text-muted)">/</span> <span class="type-indicator type-short">S:${h.shortCount}</span>`;
        }

        const netBias = (h.longValue - h.shortValue) / Math.max(1, h.totalValue);
        const intensity = Math.max(10, Math.min(100, Math.round(h.count * 2.2 + avgWeight * 6 + netBias * 18)));
        const intColor = intensity >= 75 ? "var(--accent-emerald)" : intensity >= 50 ? "var(--accent-cyan)" : "var(--accent-amber)";

        return `<tr>
          <td data-sort-val="${this.esc(h.ticker)}">
            <button class="ticker-btn ticker-emerald" data-open-ticker="${this.esc(h.ticker)}">${this.esc(h.ticker)}</button>
          </td>
          <td>${this.esc(h.name)}</td>
          <td class="num-col" data-sort-val="${h.count}"><strong>${h.count}</strong> <span class="text-muted">funds</span></td>
          <td data-sort-val="${longPct}">
            <div class="bar-cell">
              <div>${biasLabel}</div>
              <div class="micro-bar-track" title="Long ${longPct.toFixed(0)}% / Short ${shortPct.toFixed(0)}%">
                <div class="micro-bar-fill fill-emerald" style="width:${longPct.toFixed(1)}%"></div>
                <div class="micro-bar-fill fill-rose" style="width:${shortPct.toFixed(1)}%"></div>
              </div>
            </div>
          </td>
          <td class="num-col" data-sort-val="${h.totalValue}"><strong>${this.formatMoneyM(h.totalValue)}</strong></td>
          <td class="num-col" data-sort-val="${avgWeight}">${avgWeight.toFixed(2)}%</td>
          <td class="num-col" data-sort-val="${intensity}"><span style="color:${intColor}; font-weight:700;">${intensity}%</span></td>
          <td style="color: var(--text-secondary);">${this.esc(h.sector)}</td>
        </tr>`;
      })
      .join("");

    if (typeof lucide !== "undefined") lucide.createIcons();
  },

  renderShortIntelligence() {
    const container = document.getElementById("shortIntelTable");
    if (!container) return;
    const allData = this.data.shortIntelligence || [];

    // Update KPI strip
    const elTot = document.getElementById("kpiShortTotal");
    const elHigh = document.getElementById("kpiShortHigh");
    const elHtb = document.getElementById("kpiShortHTB");
    const elPuts = document.getElementById("kpiShortPuts");

    if (elTot) elTot.textContent = allData.length;
    if (elHigh) elHigh.textContent = allData.filter((x) => x.squeeze_risk === "HIGH").length;
    if (elHtb) elHtb.textContent = allData.filter((x) => (x.borrow_status || "").includes("HTB")).length;
    if (elPuts) elPuts.textContent = allData.filter((x) => (x.put_funds_count || 0) > 0).length;

    const filter = this.state.shortRiskFilter;
    const data = allData.filter((item) => {
      if (filter === "all") return true;
      if (filter === "PUTS") return (item.put_funds_count || 0) > 0;
      return item.squeeze_risk === filter;
    });

    if (!data.length) {
      container.innerHTML = `<tr class="empty-row"><td colspan="7" style="text-align:center; padding: 28px; color:var(--text-muted);">No short intelligence targets match this filter.</td></tr>`;
      return;
    }

    container.innerHTML = data
      .map((item) => {
        const si = Number(item.short_interest_pct || 0);
        const days = Number(item.days_to_cover || 0);
        const fee = Number(item.borrow_fee_pct || 0);
        const putsCnt = Number(item.put_funds_count || 0);
        const putsM = Number(item.put_total_m || 0);

        const siColor = si > 20 ? "var(--accent-red)" : si > 10 ? "var(--accent-amber)" : "var(--text-secondary)";
        const squeezeClass = item.squeeze_risk === "HIGH" ? "rating-badge bg-red" : item.squeeze_risk === "MODERATE" ? "rating-badge bg-amber" : "rating-badge bg-dim";
        const daysColor = days > 5 ? "var(--accent-red)" : days > 3 ? "var(--accent-amber)" : "var(--text-secondary)";
        const isHTB = (item.borrow_status || "").includes("HTB");
        const feeColor = fee > 5 ? "var(--accent-red)" : "var(--text-secondary)";

        const putsCell = putsCnt > 0
          ? `<span class="text-rose" style="font-weight:700;">${putsCnt} funds</span> <span class="text-muted">(${this.formatMoneyM(putsM)})</span>`
          : `<span class="text-muted">—</span>`;

        return `<tr>
          <td data-sort-val="${this.esc(item.ticker)}">
            <button class="ticker-btn ticker-short" data-open-ticker="${this.esc(item.ticker)}">${this.esc(item.ticker)}</button>
          </td>
          <td class="num-col" data-sort-val="${si}" style="color:${siColor}; font-weight:700;">${si.toFixed(1)}%</td>
          <td class="num-col" data-sort-val="${days}" style="color:${daysColor};">${days.toFixed(1)}d</td>
          <td class="num-col" data-sort-val="${fee}" style="color:${feeColor}; font-weight:600;">
            ${fee.toFixed(1)}% <span class="badge ${isHTB ? "bg-red" : "bg-dim"}" style="margin-left:4px;">${isHTB ? "HTB" : "ETB"}</span>
          </td>
          <td class="num-col" data-sort-val="${putsM}">${putsCell}</td>
          <td><span class="${squeezeClass}">${this.esc(item.squeeze_risk)}</span></td>
          <td style="font-size:0.82rem; color:var(--text-secondary); max-width:340px;">${this.esc(item.thesis)}</td>
        </tr>`;
      })
      .join("");
  },

  renderActivistFilings() {
    const container = document.getElementById("activistTable");
    if (!container) return;
    const data = this.data.activistFilings || [];

    // Update Activist KPI strip
    const elCnt = document.getElementById("kpiActCount");
    const elCap = document.getElementById("kpiActCapital");
    const elOwn = document.getElementById("kpiActAvgOwn");
    const elConf = document.getElementById("kpiActConf");

    if (elCnt) elCnt.textContent = data.length;
    if (elCap) {
      const sumM = data.reduce((s, i) => s + (i.value_m || 0), 0);
      elCap.textContent = this.formatMoneyM(sumM);
    }
    if (elOwn && data.length) {
      const avgOwn = data.reduce((s, i) => s + (i.ownership_pct || 0), 0) / data.length;
      elOwn.textContent = `${avgOwn.toFixed(1)}%`;
    }
    if (elConf && data.length) {
      const avgC = data.reduce((s, i) => s + (i.confidence || 0), 0) / data.length;
      elConf.textContent = `${avgC.toFixed(0)}%`;
    }

    if (!data.length) {
      container.innerHTML = `<tr class="empty-row"><td colspan="8" style="text-align:center; padding: 28px; color:var(--text-muted);">No activist filing data available.</td></tr>`;
      return;
    }

    container.innerHTML = data
      .map((item) => {
        const matchedFund = this.data.universe.find(
          (f) => f.name.toLowerCase().includes(item.fund.toLowerCase()) || item.fund.toLowerCase().includes(f.id.replace(/_/g, " "))
        );
        const fundCell = matchedFund
          ? `<button class="fund-link-btn" data-jump-fund="${this.esc(matchedFund.id)}">${this.esc(item.fund)}</button>`
          : `<strong>${this.esc(item.fund)}</strong>`;

        const actionColor = item.action === "ACTIVIST" ? "var(--accent-red)" : item.action === "CONTROL" ? "#C084FC" : "var(--accent-emerald)";
        const actionBadge = item.action === "ACTIVIST" ? "rating-badge bg-red" : item.action === "CONTROL" ? "rating-badge bg-purple" : "rating-badge bg-emerald";
        const confColor = item.confidence >= 95 ? "var(--accent-emerald)" : "var(--accent-amber)";

        return `<tr>
          <td>${fundCell}</td>
          <td data-sort-val="${this.esc(item.ticker)}">
            <button class="ticker-btn" data-open-ticker="${this.esc(item.ticker)}">${this.esc(item.ticker)}</button>
          </td>
          <td>${this.esc(item.company)}</td>
          <td class="num-col" data-sort-val="${item.ownership_pct}" style="color:${actionColor}; font-weight:700;">${Number(item.ownership_pct).toFixed(1)}%</td>
          <td class="num-col" data-sort-val="${item.value_m}"><strong>${this.formatMoneyM(item.value_m)}</strong></td>
          <td class="mono-num" style="color:var(--text-secondary); font-size:0.82rem;">${this.esc(item.date || "—")}</td>
          <td><span class="${actionBadge}">${this.esc(item.action)}</span></td>
          <td class="num-col" data-sort-val="${item.confidence}" style="color:${confColor}; font-weight:700;">${Number(item.confidence).toFixed(0)}%</td>
        </tr>`;
      })
      .join("");
  },

  renderConvictionMatrix() {
    const hiddenContainer = document.getElementById("hiddenAlphaTable");
    const crowdContainer = document.getElementById("crowdingRiskTable");
    const m = this.data.convictionMatrix || {};

    if (hiddenContainer) {
      const hidden = m.hidden_alpha || [];
      if (!hidden.length) {
        hiddenContainer.innerHTML = `<tr class="empty-row"><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No hidden alpha signals detected.</td></tr>`;
      } else {
        hiddenContainer.innerHTML = hidden
          .map((item) => {
            const wNum = parseFloat(String(item.conviction_weight || "0").replace("%", "")) || 0;
            const fundCell = item.conviction_fund_id
              ? `<button class="fund-link-btn" data-jump-fund="${this.esc(item.conviction_fund_id)}">${this.esc(item.conviction_fund)}</button>`
              : this.esc(item.conviction_fund);
            return `<tr>
              <td data-sort-val="${this.esc(item.ticker)}">
                <button class="ticker-btn ticker-emerald" data-open-ticker="${this.esc(item.ticker)}">${this.esc(item.ticker)}</button>
              </td>
              <td>${this.esc(item.name)}</td>
              <td>${fundCell}</td>
              <td class="num-col" data-sort-val="${wNum}"><strong>${this.esc(item.conviction_weight)}</strong></td>
              <td style="font-size:0.82rem; color:var(--text-secondary);">${this.esc(item.rationale)}</td>
            </tr>`;
          })
          .join("");
      }
    }

    if (crowdContainer) {
      const crowd = m.crowding_risk || [];
      if (!crowd.length) {
        crowdContainer.innerHTML = `<tr class="empty-row"><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No crowding risk alerts.</td></tr>`;
      } else {
        crowdContainer.innerHTML = crowd
          .map((item) => {
            const riskCls = item.risk === "HIGH" ? "badge-low" : "badge-moderate";
            return `<tr>
              <td data-sort-val="${this.esc(item.ticker)}">
                <button class="ticker-btn ticker-short" data-open-ticker="${this.esc(item.ticker)}">${this.esc(item.ticker)}</button>
              </td>
              <td>${this.esc(item.name)}</td>
              <td class="num-col" data-sort-val="${item.holders_count}"><strong>${item.holders_count}</strong> Funds</td>
              <td><span class="badge ${riskCls}">${this.esc(item.risk)} RISK</span></td>
              <td style="font-size:0.82rem; color:var(--text-secondary);">${this.esc(item.rationale)}</td>
            </tr>`;
          })
          .join("");
      }
    }
  },

  renderSectorHeatmap() {
    const container = document.getElementById("sectorHeatmapTable");
    if (!container) return;

    const allRows = this.data.sectorHeatmap || [];
    const stratFilter = this.state.heatmapStrategy || "all";
    const rows = stratFilter === "all"
      ? allRows
      : allRows.filter((row) => {
          const strat = row.strategy || this.data.universe.find((f) => f.id === row.fund_id)?.strategy;
          return strat === stratFilter;
        });

    if (!rows.length) {
      container.innerHTML = `<tr class="empty-row"><td colspan="12" style="text-align:center; padding: 28px; color:var(--text-muted);">No sector heatmap data.</td></tr>`;
      return;
    }

    const sectors = [
      "Information Technology", "Financials", "Health Care", "Consumer Discretionary",
      "Communication Services", "Industrials", "Energy", "Materials",
      "Real Estate", "Consumer Staples", "Utilities",
    ];

    container.innerHTML = rows
      .map((row) => {
        const fundObj = this.data.universe.find((f) => f.id === row.fund_id || f.name === row.fund_name);
        const strat = row.strategy || fundObj?.strategy || "";
        const stratBadge = this.getStrategyBadgeHtml(strat);
        const fid = row.fund_id || fundObj?.id || "";

        const cells = sectors
          .map((sec) => {
            const val = Number(row[sec] || 0);
            let bg = "transparent";
            let txtColor = "var(--text-muted)";
            if (val >= 35) { bg = "rgba(59, 130, 246, 0.72)"; txtColor = "#FFFFFF"; }
            else if (val >= 22) { bg = "rgba(59, 130, 246, 0.48)"; txtColor = "#F0F6FC"; }
            else if (val >= 10) { bg = "rgba(59, 130, 246, 0.28)"; txtColor = "#E5E7EB"; }
            else if (val > 0) { bg = "rgba(59, 130, 246, 0.12)"; txtColor = "#CBD5E1"; }

            return `<td class="heat-cell" data-sort-val="${val}" style="background:${bg}; color:${txtColor};">${val > 0 ? val.toFixed(1) + "%" : "—"}</td>`;
          })
          .join("");

        return `<tr>
          <td data-sort-val="${this.esc(row.fund_name)}">
            <button class="fund-link-btn" data-jump-fund="${this.esc(fid)}">${this.esc(row.fund_name)}</button>
            <div style="margin-top:4px;">${stratBadge}</div>
          </td>
          ${cells}
        </tr>`;
      })
      .join("");
  },

  renderCFTCMacro() {
    const container = document.getElementById("cftcTable");
    const tiltsGrid = document.getElementById("cftcSectorTiltsGrid");
    const repDate = document.getElementById("cftcReportDate");
    const c = this.data.cftcMacro || {};

    if (repDate && c.report_date) {
      repDate.textContent = `CFTC Leveraged Funds Futures Positioning & Implied GICS Sector Tilts (Report: ${c.report_date})`;
    }

    if (tiltsGrid && c.sector_tilts) {
      tiltsGrid.innerHTML = c.sector_tilts
        .map((t) => {
          const isShort = String(t.direction).includes("SHORT");
          const color = isShort ? "var(--accent-rose)" : "var(--accent-emerald)";
          const badgeCls = isShort ? "badge-low" : "badge-confirmed";
          return `<div class="tilt-card glass">
            <div class="tilt-card-top">
              <span class="tilt-sector">${this.esc(t.sector)}</span>
              <span class="badge ${badgeCls}">${this.esc(t.direction)}</span>
            </div>
            <div class="tilt-val" style="color:${color};">${this.esc(t.tilt)}</div>
          </div>`;
        })
        .join("");
    }

    if (container && c.contracts) {
      container.innerHTML = c.contracts
        .map((item) => {
          const z = Number(item.z_score || 0);
          const isBull = z >= 0;
          const color = isBull ? "var(--accent-emerald)" : "var(--accent-rose)";
          const numPos = parseFloat(String(item.net_position).replace(/[^0-9.\-]/g, "")) || 0;
          const pct = Math.min(50, (Math.abs(z) / 2.5) * 50);
          const fillStyle = isBull
            ? `left:50%; width:${pct.toFixed(1)}%; background:var(--accent-emerald);`
            : `right:50%; width:${pct.toFixed(1)}%; background:var(--accent-rose);`;

          return `<tr>
            <td><strong>${this.esc(item.name)}</strong></td>
            <td style="color:var(--text-secondary);">${this.esc(item.category)}</td>
            <td class="num-col" data-sort-val="${numPos}"><strong>${this.esc(item.net_position)}</strong></td>
            <td class="num-col" data-sort-val="${z}">
              <div class="zscore-wrap">
                <span style="color:${color}; font-weight:700; min-width:52px;">${z > 0 ? "+" : ""}${z.toFixed(2)}σ</span>
                <div class="zscore-bar"><div class="zscore-bar-fill" style="${fillStyle}"></div></div>
              </div>
            </td>
            <td><span class="badge ${isBull ? "badge-confirmed" : "badge-low"}">${this.esc(item.sentiment)}</span></td>
          </tr>`;
        })
        .join("");
    }
  },

  /* ========================================================================
     Cross-Fund Ticker Deep-Dive Modal
     ======================================================================== */
  openTickerModal(rawTicker) {
    const ticker = String(rawTicker || "").replace(/\s*\(PUT\)\s*/i, "").trim().toUpperCase();
    const modal = document.getElementById("tickerModal");
    if (!modal || !ticker) return;

    const fundMap = Object.fromEntries(this.data.universe.map((f) => [f.id, f]));
    const holders = [];
    let companyName = ticker;
    let sector = "Equity / Security";

    Object.entries(this.data.predictions).forEach(([fid, positions]) => {
      positions.forEach((p) => {
        const cleanT = String(p.ticker || "").replace(/\s*\(PUT\)\s*/i, "").trim().toUpperCase();
        if (cleanT === ticker) {
          if (companyName === ticker && p.name) companyName = p.name;
          if (sector === "Equity / Security" && p.sector) sector = p.sector;
          holders.push({
            fundId: fid,
            fundName: fundMap[fid]?.name || fid,
            strategy: fundMap[fid]?.strategy || "",
            type: p.type === "SHORT" || p.putCall === "PUT" ? "SHORT" : "LONG",
            instrument: p.instrument || (p.putCall ? p.putCall : "EQUITY"),
            value_m: p.value_m || 0,
            weight: p.weight || 0,
            confidence: p.confidence || 0,
          });
        }
      });
    });

    holders.sort((a, b) => b.value_m - a.value_m);

    const longHolders = holders.filter((h) => h.type === "LONG");
    const shortHolders = holders.filter((h) => h.type === "SHORT");
    const longCap = longHolders.reduce((s, h) => s + h.value_m, 0);
    const shortCap = shortHolders.reduce((s, h) => s + h.value_m, 0);

    const shortInfo = (this.data.shortIntelligence || []).find((x) => x.ticker.toUpperCase() === ticker);
    const activistMatches = (this.data.activistFilings || []).filter((x) => x.ticker.toUpperCase() === ticker);

    document.getElementById("modalTickerBadge").textContent = ticker;
    document.getElementById("modalTickerTitle").textContent = companyName;
    document.getElementById("modalTickerSector").textContent = `${sector} • Found across ${new Set(holders.map((h) => h.fundId)).size} tracked hedge funds`;
    document.getElementById("modalYahooLink").href = `https://finance.yahoo.com/quote/${encodeURIComponent(ticker)}`;
    document.getElementById("modalSecLink").href = `https://www.sec.gov/edgar/search/#/q=${encodeURIComponent(ticker)}`;

    let html = `
      <div class="modal-kpi-row">
        <div class="modal-kpi">
          <div class="modal-kpi-label">Long Capital</div>
          <div class="modal-kpi-val text-emerald">${this.formatMoneyM(longCap)}</div>
        </div>
        <div class="modal-kpi">
          <div class="modal-kpi-label">Short / PUT Capital</div>
          <div class="modal-kpi-val text-rose">${this.formatMoneyM(shortCap)}</div>
        </div>
        <div class="modal-kpi">
          <div class="modal-kpi-label">Long / Short Funds</div>
          <div class="modal-kpi-val">${longHolders.length}L / ${shortHolders.length}S</div>
        </div>
        <div class="modal-kpi">
          <div class="modal-kpi-label">FINRA Short Interest</div>
          <div class="modal-kpi-val ${shortInfo && shortInfo.short_interest_pct > 15 ? "text-rose" : "text-cyan"}">${shortInfo ? shortInfo.short_interest_pct.toFixed(1) + "%" : "N/A"}</div>
        </div>
      </div>
    `;

    if (shortInfo) {
      html += `<div class="modal-alert-box modal-alert-short">
        <strong>Short Intelligence (${this.esc(shortInfo.squeeze_risk)} Squeeze Risk):</strong>
        Short Interest ${shortInfo.short_interest_pct.toFixed(1)}% • Days to Cover ${shortInfo.days_to_cover.toFixed(1)}d • Est. Borrow Fee ${shortInfo.borrow_fee_pct?.toFixed(1) || "N/A"}% (${this.esc(shortInfo.borrow_status || "")}) — ${this.esc(shortInfo.thesis)}
      </div>`;
    }

    if (activistMatches.length) {
      html += `<div class="modal-alert-box modal-alert-activist">
        <strong>SEC Schedule 13D Activist Filing${activistMatches.length > 1 ? "s" : ""}:</strong>
        ${activistMatches.map((a) => `${this.esc(a.fund)} (${a.ownership_pct.toFixed(1)}% stake, ${this.formatMoneyM(a.value_m)}, ${this.esc(a.action)})`).join(" • ")}
      </div>`;
    }

    if (holders.length) {
      html += `
        <div class="table-container glass-table">
          <table>
            <thead>
              <tr>
                <th>Hedge Fund Manager</th>
                <th>Strategy</th>
                <th>Position</th>
                <th class="num-col">Capital ($M)</th>
                <th class="num-col">Weight</th>
              </tr>
            </thead>
            <tbody>
              ${holders
                .map(
                  (h) => `<tr>
                    <td><button class="fund-link-btn" data-jump-fund="${this.esc(h.fundId)}">${this.esc(h.fundName)}</button></td>
                    <td>${this.getStrategyBadgeHtml(h.strategy)}</td>
                    <td>${this.getTypeHtml(h.type, h.instrument === "PUT" ? "PUT" : null, h.instrument)}</td>
                    <td class="num-col"><strong>${this.formatMoneyM(h.value_m)}</strong></td>
                    <td class="num-col">${(h.weight * 100).toFixed(2)}%</td>
                  </tr>`
                )
                .join("")}
            </tbody>
          </table>
        </div>
      `;
    } else {
      html += `<p style="text-align:center; color:var(--text-muted); padding:20px;">Not present in top disclosed 13F positions across the 50 funds (tracked via Short Intelligence or 13D module).</p>`;
    }

    document.getElementById("modalBodyContent").innerHTML = html;
    modal.classList.remove("hidden");
    if (typeof lucide !== "undefined") lucide.createIcons();
  },

  closeTickerModal() {
    const modal = document.getElementById("tickerModal");
    if (modal) modal.classList.add("hidden");
  },

  /* ========================================================================
     Global Search with Live Per-Tab Match Count Badges
     ======================================================================== */
  applyGlobalSearch() {
    const q = (this.state.searchQuery || "").toLowerCase().trim();

    const tabTables = {
      "tab-predictions": ["fundPositionsTable"],
      "tab-top-holdings": ["topHoldingsTable"],
      "tab-short-intel": ["shortIntelTable"],
      "tab-activist": ["activistTable"],
      "tab-conviction": ["hiddenAlphaTable", "crowdingRiskTable"],
      "tab-heatmap": ["sectorHeatmapTable"],
      "tab-macro": ["cftcTable"],
    };

    Object.entries(tabTables).forEach(([tabId, tableIds]) => {
      let tabMatches = 0;
      tableIds.forEach((tableId) => {
        const rows = document.querySelectorAll(`#${tableId} tr:not(.empty-row)`);
        rows.forEach((row) => {
          const match = !q || row.innerText.toLowerCase().includes(q);
          row.style.display = match ? "" : "none";
          if (match) tabMatches += 1;
        });
      });

      const badge = document.querySelector(`[data-badge-for="${tabId}"]`);
      if (badge) {
        if (!q) {
          badge.classList.add("hidden");
        } else {
          badge.textContent = tabMatches;
          badge.classList.remove("hidden");
          badge.classList.toggle("has-matches", tabMatches > 0);
        }
      }
    });
  },

  /* ========================================================================
     CSV Export (Visible Filtered Rows Only) & Toast
     ======================================================================== */
  exportTableCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = Array.from(table.querySelectorAll("tr")).filter((row) => {
      return row.style.display !== "none" && !row.classList.contains("empty-row");
    });

    const csvContent = rows
      .map((row) => {
        const cols = Array.from(row.querySelectorAll("th, td"));
        return cols
          .map((c) => `"${c.innerText.replace(/\s+/g, " ").replace(/"/g, '""').trim()}"`)
          .join(",");
      })
      .join("\n");

    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename || "export.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    this.showToast(`Exported ${Math.max(0, rows.length - 1)} rows to ${filename}`);
  },

  showToast(msg) {
    const el = document.getElementById("toastNotification");
    if (!el) return;
    el.textContent = msg;
    el.classList.remove("hidden");
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => el.classList.add("hidden"), 2600);
  },

  /* ========================================================================
     Rock-Solid Table Sorting (uses data-sort-val, safe on empty rows)
     ======================================================================== */
  handleSort(th) {
    const table = th.closest("table");
    if (!table) return;
    const tbody = table.querySelector("tbody");
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll("tr:not(.empty-row)"));
    if (rows.length <= 1) return;

    const tableKey = table.id || "table";
    const sortKey = th.getAttribute("data-sort");
    const index = Array.from(th.parentNode.children).indexOf(th);

    const prev = this.sortState[tableKey] || { col: null, asc: true };
    const isAsc = prev.col === sortKey ? !prev.asc : false; // Default descending for numbers on first click
    this.sortState[tableKey] = { col: sortKey, asc: isAsc };

    // Highlight active column header
    table.querySelectorAll("th[data-sort]").forEach((h) => h.classList.remove("sort-active"));
    th.classList.add("sort-active");

    rows.sort((a, b) => {
      const cellA = a.children[index];
      const cellB = b.children[index];
      if (!cellA || !cellB) return 0;

      const rawA = cellA.hasAttribute("data-sort-val") ? cellA.getAttribute("data-sort-val") : cellA.innerText.trim();
      const rawB = cellB.hasAttribute("data-sort-val") ? cellB.getAttribute("data-sort-val") : cellB.innerText.trim();

      const numA = Number(rawA);
      const numB = Number(rawB);
      if (rawA !== "" && rawB !== "" && !Number.isNaN(numA) && !Number.isNaN(numB)) {
        return isAsc ? numA - numB : numB - numA;
      }

      return isAsc
        ? String(rawA).localeCompare(String(rawB))
        : String(rawB).localeCompare(String(rawA));
    });

    const frag = document.createDocumentFragment();
    rows.forEach((r) => frag.appendChild(r));
    tbody.appendChild(frag);
  },
};
