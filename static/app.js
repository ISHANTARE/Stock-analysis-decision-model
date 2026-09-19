/**
 * Quantamental Stock Analysis Dashboard - Frontend Application Logic
 * Powered by TypeSafe AI (Jev System One)
 */

let currentTicker = "RELIANCE.NS";
let currentPeriod = "1mo";
let currentReportData = null;
let priceChartInstance = null;
let searchDebounceTimer = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initTickerTape();
  initSearchAndChips();
  initChartTimeframeButtons();
  initExportButton();

  // Load default stock (Reliance Industries)
  runAnalysis(currentTicker);
});

/* ==========================================================================
   1. LIVE TICKER TAPE
   ========================================================================== */
async function initTickerTape() {
  const tapeWrapper = document.getElementById("ticker-tape");

  async function updateTape() {
    try {
      const resp = await fetch("/api/indices");
      if (!resp.ok) return;
      const data = await resp.json();

      if (!data || data.length === 0) return;

      // Duplicate data array to ensure seamless infinite CSS ticker scroll
      const displayItems = [...data, ...data];

      tapeWrapper.innerHTML = displayItems.map(item => {
        const isPos = item.change >= 0;
        const changeClass = isPos ? "positive" : "negative";
        const sign = isPos ? "+" : "";
        return `
          <div class="tape-item">
            <span class="tape-item-name">${item.name}</span>
            <span class="tape-item-price">${item.price.toLocaleString()}</span>
            <span class="tape-item-change ${changeClass}">${sign}${item.change_pct}%</span>
          </div>
        `;
      }).join("");
    } catch (e) {
      console.warn("Ticker tape update error:", e);
    }
  }

  updateTape();
  // Refresh indices every 45 seconds
  setInterval(updateTape, 45000);
}

/* ==========================================================================
   2. SEARCH & AUTOCOMPLETE & CHIPS
   ========================================================================== */
function initSearchAndChips() {
  const searchInput = document.getElementById("ticker-search-input");
  const dropdown = document.getElementById("autocomplete-dropdown");
  const runBtn = document.getElementById("btn-run-analysis");

  // Keyboard shortcut (Cmd/Ctrl + K)
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });

  // Debounced input search
  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchDebounceTimer);
    const query = e.target.value.trim();
    if (!query) {
      dropdown.classList.remove("active");
      return;
    }

    searchDebounceTimer = setTimeout(async () => {
      try {
        const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        if (!resp.ok) return;
        const results = await resp.json();

        if (results.length === 0) {
          dropdown.classList.remove("active");
          return;
        }

        dropdown.innerHTML = results.map(item => `
          <div class="dropdown-item" data-ticker="${item.symbol}">
            <div>
              <span class="item-symbol">${item.symbol}</span>
              <span class="item-name">${item.name}</span>
            </div>
            <span class="item-market-tag ${item.market.toLowerCase()}">${item.exchange}</span>
          </div>
        `).join("");

        dropdown.classList.add("active");

        // Attach click listeners to items
        dropdown.querySelectorAll(".dropdown-item").forEach(el => {
          el.addEventListener("click", () => {
            const sym = el.getAttribute("data-ticker");
            searchInput.value = sym;
            dropdown.classList.remove("active");
            setActiveChip(sym);
            runAnalysis(sym);
          });
        });
      } catch (err) {
        console.warn("Search error:", err);
      }
    }, 250);
  });

  // Close dropdown on outside click
  document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove("active");
    }
  });

  // Enter key initiates search
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      dropdown.classList.remove("active");
      const val = searchInput.value.trim();
      if (val) {
        setActiveChip(val);
        runAnalysis(val);
      }
    }
  });

  // Evaluate Button click
  runBtn.addEventListener("click", () => {
    const val = searchInput.value.trim() || currentTicker;
    setActiveChip(val);
    runAnalysis(val);
  });

  // Quick Chips Click Handlers
  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      const ticker = chip.getAttribute("data-ticker");
      searchInput.value = ticker;
      setActiveChip(ticker);
      runAnalysis(ticker);
    });
  });
}

function setActiveChip(ticker) {
  document.querySelectorAll(".chip-btn").forEach(chip => {
    if (chip.getAttribute("data-ticker") === ticker || chip.getAttribute("data-ticker") === `${ticker}.NS`) {
      chip.classList.add("active");
    } else {
      chip.classList.remove("active");
    }
  });
}

/* ==========================================================================
   3. CHART TIMEFRAMES
   ========================================================================== */
function initChartTimeframeButtons() {
  const buttons = document.querySelectorAll(".btn-timeframe");
  buttons.forEach(btn => {
    btn.addEventListener("click", async () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentPeriod = btn.getAttribute("data-period");
      await updateChart(currentTicker, currentPeriod);
    });
  });
}

/* ==========================================================================
   4. EXPORT BUTTON
   ========================================================================== */
function initExportButton() {
  const btn = document.getElementById("btn-export-json");
  btn.addEventListener("click", () => {
    if (!currentReportData) return;
    const blob = new Blob([JSON.stringify(currentReportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Quantamental_${currentTicker}_Report.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}

/* ==========================================================================
   5. RUN QUANTAMENTAL ANALYSIS PIPELINE
   ========================================================================== */
async function runAnalysis(ticker) {
  currentTicker = ticker;
  const overlay = document.getElementById("loading-overlay");
  const statusText = document.getElementById("loading-status-text");

  overlay.style.display = "flex";
  statusText.innerText = `Fetching real-time market data & disclosures for '${ticker}'...`;

  try {
    const resp = await fetch(`/api/analyze?ticker=${encodeURIComponent(ticker)}`);
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Analysis request failed.");
    }
    const data = await resp.json();
    currentReportData = data;

    // Render Dashboard Sections
    renderSnapshot(data.stock_state);
    renderDecisionCard(data.decision);
    renderScenarios(data.valuation_scenarios, data.decision.scenarios_breakdown, data.stock_state.currency);
    renderScorecard(data.jev_evaluation, data.health_metrics);
    renderThesisAndNews(data.decision, data.stock_state.live_news);
    renderRatiosTable(data.stock_state.financial_metrics);

    // Render / Update Chart
    await updateChart(ticker, currentPeriod, data.valuation_scenarios);

  } catch (err) {
    alert(`Error analyzing stock '${ticker}':\n${err.message}`);
    console.error(err);
  } finally {
    overlay.style.display = "none";
  }
}

/* ==========================================================================
   6. DOM RENDERERS
   ========================================================================== */

function renderSnapshot(state) {
  const curr = state.currency;
  const currSign = curr === "INR" ? "₹" : "$";

  document.getElementById("stock-name").innerText = state.company_name;
  document.getElementById("stock-ticker").innerText = state.ticker;
  document.getElementById("stock-exchange").innerText = `${state.exchange} • ${state.market === 'IN' ? 'INDIA' : 'GLOBAL'}`;
  document.getElementById("stock-currency").innerText = `${curr} (${currSign})`;

  document.getElementById("stock-price").innerText = `${currSign}${state.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

  const changePill = document.getElementById("stock-change-pill");
  const changeAmt = state.change_amount;
  const changePct = state.change_pct;
  const isPos = changeAmt >= 0;

  changePill.className = `price-change-pill ${isPos ? 'positive' : 'negative'}`;
  document.getElementById("stock-change-amt").innerText = `${isPos ? '+' : ''}${currSign}${changeAmt.toFixed(2)}`;
  document.getElementById("stock-change-pct").innerText = `(${isPos ? '+' : ''}${changePct.toFixed(2)}%)`;

  // Day & 52w Ranges
  const dayLow = state.day_low || state.current_price;
  const dayHigh = state.day_high || state.current_price;
  const low52 = state.financial_metrics.fifty_two_week_low || dayLow;
  const high52 = state.financial_metrics.fifty_two_week_high || dayHigh;

  document.getElementById("day-low").innerText = `${currSign}${dayLow.toFixed(2)}`;
  document.getElementById("day-high").innerText = `${currSign}${dayHigh.toFixed(2)}`;
  document.getElementById("fifty-two-low").innerText = `${currSign}${low52.toFixed(2)}`;
  document.getElementById("fifty-two-high").innerText = `${currSign}${high52.toFixed(2)}`;

  // Progress fills
  const dayPct = dayHigh > dayLow ? Math.min(100, Math.max(0, ((state.current_price - dayLow) / (dayHigh - dayLow)) * 100)) : 50;
  const fiftyTwoPct = high52 > low52 ? Math.min(100, Math.max(0, ((state.current_price - low52) / (high52 - low52)) * 100)) : 50;

  document.getElementById("day-range-fill").style.width = `${dayPct}%`;
  document.getElementById("fifty-two-range-fill").style.width = `${fiftyTwoPct}%`;

  // Quick Stats
  document.getElementById("stat-mcap").innerText = state.market_cap_formatted;
  document.getElementById("stat-pe-trailing").innerText = state.financial_metrics.pe_trailing ?? "N/A";
  document.getElementById("stat-pe-forward").innerText = state.financial_metrics.pe_forward ?? "N/A";
  document.getElementById("stat-ev-ebitda").innerText = state.financial_metrics.ev_to_ebitda ?? "N/A";

  const revEl = document.getElementById("stat-rev-growth");
  const revGrowth = state.financial_metrics.revenue_growth_yoy;
  revEl.innerText = `${revGrowth >= 0 ? '+' : ''}${(revGrowth * 100).toFixed(1)}%`;
  revEl.className = `stat-val ${revGrowth >= 0 ? 'positive' : 'negative'}`;

  document.getElementById("stat-div-yield").innerText = `${state.financial_metrics.dividend_yield_pct.toFixed(2)}%`;
}

function renderDecisionCard(decision) {
  const actionBanner = document.getElementById("action-banner");
  const actionText = document.getElementById("action-text");
  const action = decision.action;

  actionText.innerText = action.replace(/_/g, " ");

  if (action === "STRONG_BUY" || action === "BUY") {
    actionBanner.className = "action-banner buy";
  } else if (action === "HOLD") {
    actionBanner.className = "action-banner hold";
  } else if (action === "TRIM_OR_SELL") {
    actionBanner.className = "action-banner sell";
  } else {
    actionBanner.className = "action-banner avoid";
  }

  // Expected Return
  const expReturnEl = document.getElementById("expected-return-val");
  const expReturn = decision.expected_return_pct;
  const isPos = expReturn >= 0;

  expReturnEl.innerText = `${isPos ? '+' : ''}${expReturn.toFixed(2)}%`;
  expReturnEl.className = `expected-return-val ${isPos ? 'positive' : 'negative'}`;

  const currSign = decision.currency === "INR" ? "₹" : "$";
  document.getElementById("expected-target-price").innerText = `${currSign}${decision.expected_target_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

  // Confidence
  const confPct = Math.round(decision.overall_confidence * 100);
  document.getElementById("confidence-value").innerText = `${decision.overall_confidence.toFixed(2)} (${decision.conviction_tier.replace(/_/g, " ")})`;
  document.getElementById("confidence-fill").style.width = `${confPct}%`;

  document.getElementById("decision-summary-text").innerText = decision.action_summary;
}

function renderScenarios(rawScenarios, breakdown, currency) {
  const currSign = currency === "INR" ? "₹" : "$";

  // Bull
  document.getElementById("sc-bull-target").innerText = `${currSign}${breakdown.bull.target.toFixed(2)}`;
  document.getElementById("sc-bull-upside").innerText = `+${breakdown.bull.upside_pct}% Upside`;
  document.getElementById("sc-bull-prob").innerText = `Jev Prob: ${(breakdown.bull.probability * 100).toFixed(0)}%`;
  document.getElementById("sc-bull-fill").style.width = `${breakdown.bull.probability * 100}%`;
  document.getElementById("sc-bull-rationale").innerText = rawScenarios.bull_case.rationale;

  // Base
  document.getElementById("sc-base-target").innerText = `${currSign}${breakdown.base.target.toFixed(2)}`;
  document.getElementById("sc-base-upside").innerText = `+${breakdown.base.upside_pct}% Upside`;
  document.getElementById("sc-base-prob").innerText = `Jev Prob: ${(breakdown.base.probability * 100).toFixed(0)}%`;
  document.getElementById("sc-base-fill").style.width = `${breakdown.base.probability * 100}%`;
  document.getElementById("sc-base-rationale").innerText = rawScenarios.base_case.rationale;

  // Bear
  document.getElementById("sc-bear-target").innerText = `${currSign}${breakdown.bear.target.toFixed(2)}`;
  document.getElementById("sc-bear-upside").innerText = `${breakdown.bear.upside_pct}% Downside`;
  document.getElementById("sc-bear-prob").innerText = `Jev Prob: ${(breakdown.bear.probability * 100).toFixed(0)}%`;
  document.getElementById("sc-bear-fill").style.width = `${breakdown.bear.probability * 100}%`;
  document.getElementById("sc-bear-rationale").innerText = rawScenarios.bear_case.rationale;
}

function renderScorecard(jev, health) {
  // Moat
  const moat = jev.economic_moat.score;
  document.getElementById("moat-score").innerText = moat.toFixed(2);
  document.getElementById("moat-fill").style.width = `${(moat / 3.0) * 100}%`;
  document.getElementById("moat-badge").innerText = moat >= 2.0 ? "Wide Moat" : (moat >= 1.0 ? "Narrow Moat" : "Commodity");

  // Conviction
  const conv = jev.management_conviction.score;
  document.getElementById("conv-score").innerText = conv.toFixed(2);
  document.getElementById("conv-fill").style.width = `${(conv / 3.0) * 100}%`;
  document.getElementById("conv-badge").innerText = conv >= 2.0 ? "High Conviction" : (conv >= 1.2 ? "Pragmatic" : "Evasive");

  // Guidance
  const guideChoice = jev.guidance_trajectory.choice;
  const guideProbs = jev.guidance_trajectory.probabilities;
  document.getElementById("guide-badge").innerText = guideChoice.toUpperCase();
  document.getElementById("guide-p-acc").innerText = `${Math.round((guideProbs.accelerating || 0) * 100)}%`;
  document.getElementById("guide-p-ste").innerText = `${Math.round((guideProbs.steady || 0) * 100)}%`;
  document.getElementById("guide-p-dec").innerText = `${Math.round((guideProbs.decelerating || 0) * 100)}%`;

  // Forensic Risk
  const forensic = jev.forensic_governance_risk.noul;
  document.getElementById("forensic-score").innerText = forensic.toFixed(2);
  const forensicFill = document.getElementById("forensic-fill");
  const forensicBadge = document.getElementById("forensic-badge");
  forensicFill.style.width = `${Math.min(100, forensic * 100)}%`;

  if (forensic >= 0.60) {
    forensicBadge.innerText = "CRITICAL VETO";
    forensicBadge.className = "score-card-badge negative";
    forensicFill.className = "score-fill negative";
  } else if (forensic >= 0.30) {
    forensicBadge.innerText = "MODERATE RISK";
    forensicBadge.className = "score-card-badge hold";
  } else {
    forensicBadge.innerText = "SAFE";
    forensicBadge.className = "score-card-badge safe";
    forensicFill.className = "score-fill safe";
  }

  // Macro
  const tailwind = jev.macro_policy_tailwinds.choice;
  document.getElementById("tailwind-badge").innerText = tailwind.replace(/_/g, " ").toUpperCase();
  document.getElementById("tailwind-tag").innerText = tailwind === "strong_tailwinds" ? "CAPEX / SECULAR BENEFICIARY" : "STANDARD CYCLICAL";

  // Solvency
  const zScore = health.altman_z_score;
  const zStatus = health.health_status;
  document.getElementById("sol-altman").innerText = zScore.toFixed(2);
  document.getElementById("sol-piotroski").innerText = `${health.piotroski_f_score} / 9`;
  document.getElementById("solvency-badge").innerText = zStatus === "HEALTHY_SAFE_ZONE" ? "Healthy" : (zStatus === "MODERATE_GREY_ZONE" ? "Grey Zone" : "Distress Risk");
}

function renderThesisAndNews(decision, newsList) {
  // Catalysts
  const catList = document.getElementById("catalysts-list");
  catList.innerHTML = decision.key_catalysts.map(c => `<li>${c}</li>`).join("");

  // Risks
  const riskList = document.getElementById("risks-list");
  riskList.innerHTML = decision.primary_risks.map(r => `<li>${r}</li>`).join("");

  // News Stream
  const newsContainer = document.getElementById("news-stream");
  if (!newsList || newsList.length === 0) {
    newsContainer.innerHTML = `<div class="news-item"><p class="news-snippet">No recent breaking news articles found for this ticker.</p></div>`;
    return;
  }

  newsContainer.innerHTML = newsList.map(item => {
    // Simple headline sentiment heuristic
    const t = (item.title + " " + item.summary).toLowerCase();
    let sentiment = "neutral";
    let sentLabel = "NEUTRAL";
    if (t.includes("record") || t.includes("beat") || t.includes("growth") || t.includes("tax relief") || t.includes("surge") || t.includes("order win")) {
      sentiment = "positive";
      sentLabel = "BULLISH";
    } else if (t.includes("probe") || t.includes("fine") || t.includes("slump") || t.includes("miss") || t.includes("cut") || t.includes("fraud")) {
      sentiment = "negative";
      sentLabel = "BEARISH";
    }

    return `
      <div class="news-item">
        <div class="news-meta">
          <span class="news-source">${item.provider}</span>
          <span class="news-time">${item.display_time || ''}</span>
          <span class="news-sentiment ${sentiment}">${sentLabel}</span>
        </div>
        <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="news-headline">${item.title}</a>
        ${item.summary ? `<p class="news-snippet">${item.summary}</p>` : ''}
      </div>
    `;
  }).join("");
}

function renderRatiosTable(metrics) {
  document.getElementById("rc-pe-trail").innerText = metrics.pe_trailing ?? "N/A";
  document.getElementById("rc-pe-fwd").innerText = metrics.pe_forward ?? "N/A";
  document.getElementById("rc-ev-ebitda").innerText = metrics.ev_to_ebitda ?? "N/A";
  document.getElementById("rc-pb").innerText = metrics.price_to_book ?? "N/A";
  document.getElementById("rc-peg").innerText = metrics.peg_ratio ?? "N/A";
  document.getElementById("rc-div").innerText = `${metrics.dividend_yield_pct.toFixed(2)}%`;
  document.getElementById("rc-gross-margin").innerText = `${(metrics.gross_margin * 100).toFixed(1)}%`;
  document.getElementById("rc-op-margin").innerText = `${(metrics.operating_margin * 100).toFixed(1)}%`;
  document.getElementById("rc-net-margin").innerText = `${(metrics.net_profit_margin * 100).toFixed(1)}%`;
  document.getElementById("rc-roe").innerText = `${(metrics.roe * 100).toFixed(1)}%`;
  document.getElementById("rc-debt-eq").innerText = metrics.debt_to_equity ? `${metrics.debt_to_equity.toFixed(1)}%` : "N/A";
  document.getElementById("rc-curr-ratio").innerText = metrics.current_ratio ? metrics.current_ratio.toFixed(2) : "N/A";
}

/* ==========================================================================
   7. INTERACTIVE CHART RENDERING (Chart.js)
   ========================================================================== */
async function updateChart(ticker, period, scenarios = null) {
  try {
    const resp = await fetch(`/api/chart?ticker=${encodeURIComponent(ticker)}&period=${period}`);
    if (!resp.ok) return;
    const chartData = await resp.json();

    const ctx = document.getElementById("price-chart").getContext("2d");

    if (priceChartInstance) {
      priceChartInstance.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "rgba(99, 102, 241, 0.35)");
    gradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");

    // Determine target line overlays from scenarios if available
    const lastPrice = chartData.prices[chartData.prices.length - 1];

    priceChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: [{
          label: "Price",
          data: chartData.prices,
          borderColor: "#6366f1",
          borderWidth: 2.2,
          pointRadius: chartData.prices.length > 50 ? 0 : 2,
          pointHoverRadius: 5,
          pointBackgroundColor: "#06b6d4",
          backgroundColor: gradient,
          fill: true,
          tension: 0.2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(13, 18, 28, 0.95)",
            borderColor: "rgba(255, 255, 255, 0.15)",
            borderWidth: 1,
            titleFont: { family: "Inter", size: 12 },
            bodyFont: { family: "JetBrains Mono", size: 13, weight: "bold" },
            padding: 10,
            displayColors: false,
            callbacks: {
              label: (context) => `Price: ${context.parsed.y.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: "rgba(255, 255, 255, 0.04)" },
            ticks: {
              color: "#64748b",
              font: { family: "JetBrains Mono", size: 10 },
              maxTicksLimit: 8
            }
          },
          y: {
            position: "right",
            grid: { color: "rgba(255, 255, 255, 0.04)" },
            ticks: {
              color: "#94a3b8",
              font: { family: "JetBrains Mono", size: 11 },
              callback: (val) => val.toLocaleString()
            }
          }
        }
      }
    });
  } catch (err) {
    console.warn("Chart rendering error:", err);
  }
}
