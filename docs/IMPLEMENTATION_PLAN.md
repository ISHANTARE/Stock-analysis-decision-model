# Implementation Plan: Quantamental Stock Decision Engine
## Target: Indian (NSE/BSE) & Global (US/EU) Equities via TypeSafe AI (Jev)

This plan outlines the architecture, module breakdown, test strategy, and delivery milestones for building the Quantamental Stock Analysis & Decision Engine.

---

## 1. System Components & Architecture

The project will follow a modular, production-ready structure:

```
Stock-analysis-decision-model/
├── .env                                  # API keys (TYPESAFE_API_KEY)
├── .agents/skills/typesafe-ai/SKILL.md   # Agent skill definition
├── docs/                                 # Complete documentation suite
│   ├── PRD.md                            # Product Requirements Document
│   ├── SCHEMAS_AND_DATA_FORMATS.md       # Input/Output data contracts
│   ├── JEV_QUESTIONS_CATALOG.md          # Centralized Jev questions & constants
│   ├── TYPESAFE_AI_REFERENCE.md          # TypeSafe & Jev technical manual
│   └── IMPLEMENTATION_PLAN.md            # This plan
│
├── src/                                  # Core Python source code
│   ├── __init__.py
│   ├── constants.py                      # Thresholds, rubrics, questions catalog
│   ├── market_data.py                    # Dual Indian/Global data ingestion
│   ├── financial_engine.py               # Deterministic valuation & ratio engine
│   ├── jev_evaluator.py                  # TypeSafe System One client & batch fan-out
│   └── decision_engine.py                # Expected return synthesis & signal generator
│
├── tests/                                # Automated test suite
│   ├── test_market_data.py               # Test NSE/BSE & US ticker fetching
│   ├── test_financial_engine.py          # Test DCF and scenario target calculations
│   ├── test_jev_evaluator.py             # Test Jev batch call & probability parsing
│   └── test_decision_engine.py           # Test vetoes, signals, and expected returns
│
├── analyze.py                            # User-facing CLI entry point
└── typesafe_client.py                    # Standalone zero-dependency TypeSafe wrapper
```

---

## 2. Implementation Milestones

### Milestone 1: Constants & Data Model Layer (`src/constants.py`)
- Define all Jev question dictionaries, criteria maps, and score levels as documented in `docs/JEV_QUESTIONS_CATALOG.md`.
- Define decision threshold constants (`FORENSIC_VETO_NOUL_THRESHOLD`, `STRONG_BUY_RETURN_THRESHOLD`, etc.).
- Define Indian ticker normalization maps (e.g. `RELIANCE` $\rightarrow$ `RELIANCE.NS`).

### Milestone 2: Market Data Ingestion Engine (`src/market_data.py`)
- Build unified `fetch_stock_data(ticker_symbol: str)` using `yfinance`.
- Detect market:
  - If ticker ends with `.NS` or `.BO`, or matches an Indian bluechip, set `market = "IN"`, currency `INR`, format market cap in `₹ Crores`.
  - Otherwise, set `market = "GLOBAL"`, currency `USD`, format in `$ Billions`.
- Extract balance sheet, income statement, operating cash flow, trailing/forward P/E, EV/EBITDA, dividend yield, 52-week range.
- Fetch latest corporate news and executive disclosures to assemble `qualitative_commentary`.
- Assemble clean, validated `StockState` dictionary.

### Milestone 3: Financial & Scenario Valuation Engine (`src/financial_engine.py`)
- Calculate quantitative health metrics:
  - Return on Equity (ROE), Operating Margin trend, Debt-to-Equity, Altman Z-Score, Piotroski F-Score.
- Construct 3 deterministic 12-month valuation scenarios:
  1. **Bull Case ($P_{\text{Bull}}$)**: Higher growth + forward P/E multiple expansion.
  2. **Base Case ($P_{\text{Base}}$)**: Normalized historical growth + median historical P/E.
  3. **Bear Case ($P_{\text{Bear}}$)**: Lower growth + multiple de-rating / margin compression.

### Milestone 4: Jev Semantic Evaluation Layer (`src/jev_evaluator.py`)
- Load `TYPESAFE_API_KEY` securely from `.env`.
- Format the single batch request containing the 6 parallel questions:
  `guidance_trajectory`, `management_conviction`, `economic_moat`, `forensic_governance_risk`, `macro_policy_tailwinds`, `valuation_sanity`.
- Execute `POST https://api.typesafe.ai/v1/systemone` using Jev (`jev-latest`).
- Parse and validate typed responses (`NoulAnswer`, `ChoiceAnswer`, `ScoreAnswer`) and confidence ratings.

### Milestone 5: Synthesis & Decision Engine (`src/decision_engine.py`)
- Combine scenario prices ($P_{\text{Bull}}, P_{\text{Base}}, P_{\text{Bear}}$) with Jev's calibrated probabilities ($P_{\text{accelerating}}, P_{\text{steady}}, P_{\text{decelerating}}$).
- Calculate:
  - $\text{Expected Target Price} = \sum P_i \times \text{Target}_i$
  - $\text{Expected 12M Return (\%)} = \frac{\text{Expected Target Price} - \text{Current Price}}{\text{Current Price}} \times 100$
- Evaluate Governance & Forensic Veto:
  - If `forensic_governance_risk.noul > 0.60` $\rightarrow$ Issue `STRONG_SELL_OR_AVOID`.
- Apply Confidence & Moat Gating:
  - Assign final action: `STRONG BUY`, `BUY`, `HOLD`, `SELL`.
  - Format executive summary, key catalysts, and risks.

### Milestone 6: CLI Application & Interactive Reporting (`analyze.py`)
- Create an intuitive CLI:
  ```bash
  python analyze.py --ticker RELIANCE.NS
  python analyze.py --ticker TCS.NS
  python analyze.py --ticker NVDA
  python analyze.py --ticker AAPL
  ```
- Output a color-coded terminal dashboard displaying:
  - Ticker & Company details (Formatted in ₹ Crores or $ Billions).
  - Prominent Decision Banner (`STRONG BUY` / `BUY` / `HOLD` / `SELL` / `AVOID`).
  - Expected 12-Month Target Price & Return %.
  - Fundamental Scores: Moat (0-3), Management Conviction (0-3), Governance Safety.
  - Scenario Breakdown Table with Jev calibrated probabilities.
  - Key Investment Catalysts & Primary Risks.

---

## 3. Verification & Testing Plan

1. **Unit Tests**:
   - `tests/test_market_data.py`: Test ticker auto-resolution (`TCS` $\rightarrow$ `TCS.NS`, `NVDA` $\rightarrow$ `NVDA`), metric extraction, currency formatting.
   - `tests/test_financial_engine.py`: Test scenario target prices, ensure math never produces negative prices or division by zero.
   - `tests/test_decision_engine.py`: Verify that a high forensic risk triggers a hard veto regardless of upside.
2. **Live Integration Tests**:
   - Test live execution on an Indian stock (e.g. `RELIANCE.NS` or `TCS.NS`).
   - Test live execution on a Global stock (e.g. `AAPL` or `NVDA`).
   - Verify total latency is under 5 seconds and token usage is under 1,000 tokens.
