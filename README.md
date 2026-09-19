# 🚀 Quantamental Stock Analysis & Decision Engine
### Powered by TypeSafe AI (Jev System One) & Quantitative Financial Modeling

[![Model: Jev-Latest](https://img.shields.io/badge/Model-Jev--Latest-blueviolet.svg)](https://docs.typesafe.ai)
[![Markets: India (NSE/BSE) & Global (US/EU)](https://img.shields.io/badge/Markets-India%20(NSE%2FBSE)%20%26%20Global-success.svg)](#supported-markets)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)

An institutional-grade **Quantamental (Quantitative + Fundamental)** stock analysis and decision platform. It combines **deterministic financial scenario valuation** with **TypeSafe AI's flagship System One model (Jev)** to deliver calibrated probability distributions, expected return projections, and confidence-gated Buy/Sell/Hold actions.

Built from the ground up for both the **Indian Stock Market (NSE / BSE)** and **Global Markets (US NASDAQ/NYSE, Europe)**.

---

## ⚡ The Core Philosophy: Why System One (Jev)?

Traditional LLM stock tools attempt to generate prose reports or hallucinate numerical price targets (e.g. *"I think this stock will hit $180"*). 

This platform uses a strict separation of concerns:
> **Python handles the math, accounting, and financial valuation. Jev provides calibrated probabilities, qualitative scoring, and forensic risk judgment.**

```
                           ┌───────────────────────────┐
                           │   USER INPUT / TICKER     │
                           │ e.g. RELIANCE, TCS, NVDA  │
                           └─────────────┬─────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
       [INDIAN MARKET DETECTOR]                    [GLOBAL MARKET DETECTOR]
       • Resolves to .NS (NSE) / .BO (BSE)         • Resolves to NASDAQ / NYSE
       • Formats in ₹ Crores & Lakhs               • Formats in $ Billions / Millions
       • Ingests Promoter Pledge, FII/DII          • Ingests SEC 10-K/10-Q, Buyback/SBC
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ 1. DATA INGESTION & RATIO ENGINE      │
                     │    • Real-time quote & fundamentals   │
                     │    • Trailing/Fwd P/E, EV/EBITDA, ROE │
                     │    • Altman Z, Piotroski F, Margins   │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼  (Unified State JSON)
                     ┌───────────────────────────────────────┐
                     │ 2. JEV SPECULATIVE FAN-OUT (System 1) │
                     │    Single parallel API call (~1.5s):  │
                     │    • Forward Guidance Trajectory      │
                     │    • Management Conviction vs Evasion │
                     │    • Economic Moat & Pricing Power    │
                     │    • Forensic Accounting & Governance │
                     │    • Macro & Policy Tailwinds (PLI)   │
                     │    • Valuation Sanity & Margin Safety │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼  (Calibrated Probabilities & Scores)
                     ┌───────────────────────────────────────┐
                     │ 3. PROBABILISTIC VALUATION & RETURN   │
                     │    E[Price] = Σ P_i × Target_i        │
                     │    Expected Return = (E[P] - P0) / P0 │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ 4. DECISION ENGINE & CONFIDENCE GATING│
                     │    • Forensic Veto (Promoter / Fraud) │
                     │    • Strong Buy / Buy / Hold / Sell   │
                     │    • Action Confidence Filter         │
                     └───────────────────────────────────────┘
```

---

## 🇮🇳 Supported Markets

### 1. Indian Stock Market (NSE & BSE) - *First-Class Support*
- **Automatic Ticker Normalization**: Enter `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ZOMATO` — automatically resolves to `.NS` (National Stock Exchange).
- **Indian Denominations**: Formats market caps and financials natively in **₹ Crores** ($1\text{ Cr} = 10^7\text{ INR}$) and **₹ Lakh Crores**.
- **Domestic Risk Checks**: Evaluates promoter share pledging, FII/DII flows, Concall Q&A transcripts, and Indian government policy tailwinds (PLI schemes, Capex push, Make in India).

### 2. Global Equities (US / NASDAQ / NYSE / EU)
- **Global Tickers**: Native support for `NVDA`, `AAPL`, `MSFT`, `TSLA`, `ASML`, etc.
- **Global Denominations**: Formats in **$ Billions** and **$ Trillions**.
- **SEC Disclosures**: Ingests risk factors, capital allocation (buybacks vs dilution), and global macroeconomic positioning.

---

## 🔬 The 6 Parallel Jev Dimensions (Speculative Fan-Out)

Using Jev's **Speculative Fan-out pattern**, all 6 dimensions below are evaluated simultaneously in **one single API request** against the stock state:

| Dimension | Primitive | Target & Output |
| :--- | :--- | :--- |
| **1. Guidance Trajectory** | `Choice` | `accelerating`, `steady`, `decelerating` with calibrated probabilities summing to 1.0. |
| **2. Management Conviction** | `Score` | Rates executive Q&A on a 0 to 3 scale (`Evasive` $\rightarrow$ `High Conviction`). |
| **3. Economic Moat** | `Score` | Rates structural pricing power and switching costs on a 0 to 3 scale (`Commodity` $\rightarrow$ `Monopoly`). |
| **4. Forensic Governance Risk** | `Noul` | Calibrated probability in `[0.0, 1.0]`. **If $> 0.60$, triggers an automatic hard veto**. |
| **5. Macro & Policy Tailwinds** | `Choice` | `strong_tailwinds` (e.g. PLI scheme, AI capex), `neutral_cyclical`, or `secular_headwinds`. |
| **6. Valuation Sanity** | `Score` | Rates valuation margin of safety on a 0 to 3 scale (`Extreme Bubble` $\rightarrow$ `Deep Value`). |

---

## 📈 How Future Target Price & Expected Return Are Derived

Rather than relying on arbitrary AI price predictions, the system uses mathematical Expected Value:

1. **Python calculates 3 deterministic valuation scenario prices**:
   - **Bull Case Target ($P_{\text{Bull}}$)**: Accelerated growth + Multiple expansion.
   - **Base Case Target ($P_{\text{Base}}$)**: In-line consensus execution + Stable historical multiple.
   - **Bear Case Target ($P_{\text{Bear}}$)**: Slowdown + Multiple de-rating.
2. **Jev determines the scenario probabilities** from fundamental disclosures:
   - $P(\text{Bull}) = P(\text{accelerating})$, $P(\text{Base}) = P(\text{steady})$, $P(\text{Bear}) = P(\text{decelerating})$.
3. **Synthesis Engine computes the 12-Month Expected Return**:
   $$\text{Expected Target Price} = P(\text{Bull}) \cdot P_{\text{Bull}} + P(\text{Base}) \cdot P_{\text{Base}} + P(\text{Bear}) \cdot P_{\text{Bear}}$$
   $$\text{Expected Return (\%)} = \frac{\text{Expected Target Price} - P_{\text{Current}}}{P_{\text{Current}}} \times 100$$

---

## 🚦 Action Signals & Decision Matrix

| Action Signal | Expected Return | Moat Score | Guidance Trajectory | Model Confidence |
| :--- | :--- | :--- | :--- | :--- |
| **STRONG BUY** | $\ge +20\%$ | $\ge 2.0$ / 3.0 | `accelerating` | $\ge 0.75$ |
| **BUY** | $\ge +12\%$ | Any | `accelerating` or `steady` | $\ge 0.50$ |
| **HOLD** | $-5\%$ to $+12\%$ | Any | Mixed | Any (or $< 0.50$ uncertainty) |
| **TRIM / SELL** | $\le -10\%$ | Any | `decelerating` | Any |
| **STRONG SELL / AVOID** | **HARD VETO** | Any | Any | **Forensic Noul $\ge 0.60$** |

---

## 🛠️ Installation & Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/ISHANTARE/Stock-analysis-decision-model.git
cd Stock-analysis-decision-model

# Install market data dependencies
pip install yfinance pandas
```

### 2. Configure API Key
Add your TypeSafe AI API key to [.env](file:///.env):
```env
TYPESAFE_API_KEY=apikey_your_typesafe_key_here
```

---

## 🖥️ Command Line Usage

### Analyze an Indian Stock (NSE/BSE)
```bash
# Using simple symbol (auto-resolves to .NS)
python analyze.py --ticker RELIANCE

# Using full exchange ticker
python analyze.py --ticker TCS.NS
```

### Analyze a Global / US Stock
```bash
python analyze.py --ticker NVDA
python analyze.py --ticker AAPL
```

### Programmatic JSON Output
```bash
python analyze.py --ticker RELIANCE.NS --json
```

---

## 📊 Sample Terminal Output

```text
══════════════════════════════════════════════════════════════════════════════
  QUANTAMENTAL REPORT: Reliance Industries Limited (RELIANCE.NS) | NSE (IN)
══════════════════════════════════════════════════════════════════════════════

  Current Price: INR 1,226.40  │  Market Cap: ₹16.60 Lakh Cr  │  P/E (Fwd): 17.18
  P/E (Trailing): 22.52  │  EV/EBITDA: 10.97  │  Revenue YoY: +29.7%

──────────────────────────────────────────────────────────────────────────────
  ██  [ BUY ] - ATTRACTIVE ACCUMULATION SETUP     ██
──────────────────────────────────────────────────────────────────────────────

  Expected 12M Target Price: INR 1,681.70  (+37.13% Expected Return)
  Model Confidence:          0.75 / 1.00  (MODERATE_CONVICTION)
  Summary:                   Attractive risk/reward: +37.1% expected return with durable execution and steady guidance.

┌── VALUATION SCENARIOS (Weighted by Jev Calibrated Probabilities) ──────┐
│  Scenario │ Target Price   │ Upside / Downside │ Jev Probability   │ Weight   │
├───────────┼────────────────┼───────────────────┼───────────────────┼──────────┤
│  Bull Case │ INR 1,954.90   │ +59.4%            │ 25.0%             │ 0.25     │
│  Base Case │ INR 1,590.64   │ +29.7%            │ 75.0%             │ 0.75     │
│  Bear Case │ INR 1,097.68   │ -10.5%            │ 0.0%              │ 0.00     │
└───────────┴────────────────┴───────────────────┴───────────────────┴──────────┘

├── JEV SYSTEM ONE SEMANTIC SCORECARD ───────────────────────────────────┤
│  • Economic Moat Rating:         1.44 / 3.00  (Narrow Moat)
│  • Management Conviction:        1.97 / 3.00  (Pragmatic / Execution Oriented)
│  • Forward Guidance:              STEADY
│  • Macro & Policy Tailwind:       STRONG_TAILWINDS
│  • Forensic Governance Risk:     SAFE (0.07)
│  • Balance Sheet Solvency:       Healthy (2.9)
└────────────────────────────────────────────────────────────────────────┘

▲ KEY INVESTMENT CATALYSTS:
  ✔ Direct beneficiary of Indian government Capex / PLI tailwinds.

▼ PRIMARY INVESTMENT RISKS:
  ✖ Vulnerable to competitor price undercutting or commodity input costs.
```

---

## 🐍 Python API Usage

You can also use the modules directly inside your own trading algorithms or portfolio management code:

```python
from src.market_data import fetch_stock_state
from src.financial_engine import compute_health_metrics, compute_valuation_scenarios
from src.jev_evaluator import JevEvaluator
from src.decision_engine import synthesize_decision

# 1. Fetch live market data (Indian or Global)
stock_state = fetch_stock_state("RELIANCE.NS")

# 2. Compute quantitative scenarios & health metrics
health = compute_health_metrics(stock_state["financial_metrics"])
scenarios = compute_valuation_scenarios(stock_state)

# 3. Evaluate parallel semantic dimensions via Jev
evaluator = JevEvaluator()
jev_eval = evaluator.evaluate_stock(stock_state)

# 4. Synthesize decision
decision = synthesize_decision(stock_state, health, scenarios, jev_eval)

print(f"Signal: {decision['action']}")
print(f"Target: {stock_state['currency']} {decision['expected_target_price']}")
print(f"Expected Return: {decision['expected_return_pct']:+.1f}%")
```

---

## 📚 Complete Documentation Index

- **[Product Requirements Document (PRD)](docs/PRD.md)**: Product goals, functional specs, user personas.
- **[Data Formats & Schemas Specification](docs/SCHEMAS_AND_DATA_FORMATS.md)**: JSON contracts for `StockState`, Jev API, and Decision Reports.
- **[Jev Questions Catalog & Decision Constants](docs/JEV_QUESTIONS_CATALOG.md)**: Centralized source of truth for all prompts, rubrics, and threshold constants.
- **[TypeSafe AI & Jev Technical Reference](docs/TYPESAFE_AI_REFERENCE.md)**: Comprehensive manual for the System One architecture, primitives, and patterns.
- **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md)**: Architecture roadmap, milestones, and testing strategy.

---

## 🧪 Running Tests

Run the automated test suite:
```bash
python -m unittest tests/test_engine.py
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
