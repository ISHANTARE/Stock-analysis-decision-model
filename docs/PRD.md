# Product Requirements Document (PRD)
## Project: Quantamental Stock Analysis & Decision Model
### Powered by TypeSafe AI (Jev System One)

**Status:** Approved for Implementation  
**Target Markets:** Indian Stock Market (NSE & BSE) & Global Markets (US / NASDAQ / NYSE / EU)  
**Version:** 1.0.0  
**Author:** Pair Programming Team (Antigravity + User)

---

## 1. Executive Summary & Vision

The **Quantamental Stock Analysis & Decision Engine** is an institutional-grade investment evaluation system that synthesizes **quantitative financial modeling** with **qualitative semantic intelligence**. 

By combining deterministic Python valuation algorithms with **TypeSafe AI's flagship System One model (Jev)**, the system eliminates traditional LLM hallucinations, prompt-parsing failures, and arbitrary price target guesses. Instead, it grounds every recommendation in:
1. **Mathematical Multi-Scenario Modeling** (Bull, Base, Bear scenario targets computed deterministically).
2. **Calibrated Probabilities** ($P(\text{Bull})$, $P(\text{Base})$, $P(\text{Bear})$ determined by Jev from semantic fundamental disclosures).
3. **Forensic Governance Vetoes** (Guarding against fraud, high promoter share pledging in India, or accounting manipulation).
4. **Confidence-Gated Execution** (Action thresholds that scale strictly with model certainty).

---

## 2. Target Markets & Market-Specific Nuances

### 2.1 Indian Stock Market (NSE / BSE) - Primary Focus
- **Tickers:** NSE symbols (`RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY.NS`, `ZOMATO.NS`) and BSE (`.BO`).
- **Denominations:** Indian Rupees (₹ INR), formatted in **Crores** ($1\text{ Cr} = 10^7\text{ INR}$) and **Lakhs** ($10^5\text{ INR}$).
- **Key Domestic Indicators:**
  - **Promoter Share Pledging:** A critical corporate governance metric in India. Promoters borrowing against shares can trigger forced margin liquidations in market downturns.
  - **FII / DII Flows:** Foreign Institutional Investors vs. Domestic Institutional Investors (Mutual Funds, LIC).
  - **Policy Tailwinds:** Government Capex, PLI (Production Linked Incentive) schemes, Make in India, Defence indigenization.
  - **Corporate Filings:** Concall (Conference Call) transcripts submitted to BSE/NSE, MCA/ROC filings, quarterly SEBI disclosures.

### 2.2 Global Stock Markets (US / NYSE / NASDAQ / European Exchanges)
- **Tickers:** Standard global symbols (`AAPL`, `NVDA`, `MSFT`, `TSLA`, `ASML`).
- **Denominations:** USD ($) / EUR (€) in Billions and Millions.
- **Key Global Indicators:**
  - **SEC Disclosures:** 10-K, 10-Q (MD&A sections and Item 1A Risk Factors), 8-K material event filings.
  - **Capital Allocation:** Share buyback yield vs. Stock-Based Compensation (SBC) dilution.
  - **Macro Factors:** Federal Reserve interest rate cycles, USD currency strength (DXY), global enterprise IT spend.

---

## 3. User Personas

1. **Active Retail / Swing Investor:** Wants clear Buy/Sell/Hold ratings, Expected 12-Month Return %, and immediate identification of whether a stock is overvalued or has broken momentum.
2. **Long-Term Fundamental / Value Investor:** Requires Warren Buffett-style Moat auditing, management conviction vs. evasion analysis, and margin of safety verification.
3. **Risk-Conscious / Forensic Analyst:** Demands hard vetoes on promoter pledging, sudden auditor resignations, related-party transactions, and accounting red flags.

---

## 4. Functional Requirements (FR)

### FR-1: Unified Market Data Ingestion
- Ingest real-time and historical price data, trading volume, valuation multiples, balance sheets, cash flows, and income statements.
- Automatically detect ticker region:
  - If entered as `RELIANCE` or `TCS`, automatically append `.NS` for Indian National Stock Exchange.
  - If entered as `NVDA` or `AAPL`, resolve directly to US exchanges.
- Support manual exchange override (e.g. `--market IN` or `--market US`).

### FR-2: Quantitative Ratio & Health Pre-Computation
- Compute financial health metrics in deterministic code:
  - **Valuation:** Trailing P/E, Forward P/E, EV/EBITDA, Price/FCF, PEG Ratio.
  - **Profitability:** Gross Margin, Operating Margin, ROE, ROCE / ROIC.
  - **Solvency:** Net Debt / EBITDA, Interest Coverage Ratio, Altman Z-Score (bankruptcy risk), Piotroski F-Score (financial strength).
  - **Technicals:** 52-week high/low range, 50-day / 200-day Moving Average positions, RSI (14).

### FR-3: Jev Speculative Fan-Out Evaluation
- Construct a clean, structured `state` JSON containing pre-computed metrics, earnings commentary, concall Q&A, and news.
- Submit a **single batch evaluation request** to Jev (`POST /v1/systemone`) covering 6 parallel dimensions:
  1. `guidance_trajectory` (Choice: Accelerating, Steady, Decelerating).
  2. `management_conviction` (Score: 0 to 3 from Evasive to High Conviction).
  3. `economic_moat` (Score: 0 to 3 from Commodity to Monopoly).
  4. `forensic_governance_risk` (Noul: Binary probability of fraud, pledging risk, or accounting anomalies).
  5. `macro_policy_tailwinds` (Choice: Strong Tailwinds, Neutral/Cyclical, Secular Headwinds).
  6. `valuation_sanity` (Score: 0 to 3 from Extreme Bubble to Deep Margin of Safety).

### FR-4: Scenario Valuation & Expected Return Calculation
- Compute 3 deterministic target prices for a 12-month horizon:
  - **Bull Case ($P_{\text{Bull}}$)**: Upper-quartile historical multiple + accelerated revenue growth.
  - **Base Case ($P_{\text{Base}}$)**: Consensus median multiple + normalized growth.
  - **Bear Case ($P_{\text{Bear}}$)**: Multiple compression / de-rating + decelerated growth.
- Synthesize the **Expected Fair Value**:
  $$E[\text{Price}] = P(\text{Bull}) \cdot P_{\text{Bull}} + P(\text{Base}) \cdot P_{\text{Base}} + P(\text{Bear}) \cdot P_{\text{Bear}}$$
- Calculate the **Expected Return %**:
  $$\text{Expected Return} = \frac{E[\text{Price}] - P_{\text{Current}}}{P_{\text{Current}}} \times 100$$

### FR-5: Decision Matrix & Action Signals
- **Hard Forensic Veto:** If `forensic_governance_risk` probability $> 0.60$, issue `STRONG_SELL_OR_AVOID` regardless of upside.
- **Action Signal Assignment:**
  - `STRONG_BUY`: Expected Return $> +20\%$, Moat Score $\ge 2.0$, Confidence $\ge 0.75$.
  - `BUY`: Expected Return $> +12\%$, Guidance accelerating/steady, Confidence $\ge 0.60$.
  - `HOLD`: Expected Return between $-5\%$ and $+12\%$, or Model Confidence $< 0.50$ (uncertainty / low visibility).
  - `TRIM_OR_SELL`: Expected Return $< -10\%$, or Decelerating guidance.

### FR-6: CLI & Report Output
- Provide a clean CLI command: `python analyze.py --ticker <SYMBOL>`.
- Output an executive dashboard displaying:
  - Header: Ticker, Company Name, Current Price, Exchange, Currency.
  - Core Signal: Color-coded action banner (`STRONG BUY`, `BUY`, `HOLD`, `SELL`, `AVOID`).
  - Valuation Target: Expected 12M Target Price & Expected Return %.
  - Fundamental Scores: Moat Rating, Management Conviction, Governance Safety.
  - Jev Scenario Probabilities: Bull / Base / Bear distribution with model confidence.
  - Detailed Bulleted Investment Thesis & Key Risks.

---

## 5. Non-Functional Requirements (NFR)

- **NFR-1 (Latency):** Complete analysis cycle (data fetch + Jev parallel evaluation + scenario synthesis) must execute in under **5 seconds** per stock.
- **NFR-2 (Cost Efficiency):** By utilizing Jev's **Speculative Fan-out pattern**, all semantic questions must be batched into **one single API call** per stock analysis.
- **NFR-3 (Robustness & Fail-Safe):** In case of market data gaps (e.g. missing forward P/E), the system must degrade gracefully with reasonable historical proxies rather than crashing.
- **NFR-4 (Configurability):** All question rubrics, criteria descriptions, and decision thresholds must live in dedicated configuration files, never hardcoded inside operational scripts.

---

## 6. Success Metrics & KPIs

1. **Calibration Accuracy:** Jev's reported confidence matches actual empirical distribution outcomes.
2. **Forensic Detection:** Zero false negatives on known corporate governance crises (e.g. flagging promoter pledge crises before price collapse).
3. **Execution Simplicity:** 1-command execution for any Indian or Global equity.
