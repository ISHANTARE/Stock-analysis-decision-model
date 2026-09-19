# Jev Questions Catalog & Decision Constants
## Project: Quantamental Stock Analysis & Decision Model

> **Design Principle (from TypeSafe AI Guidelines):**  
> *"Put the constants (questions, options, and thresholds) in a single place so they're easy to review without spelunking."*

This document serves as the authoritative single source of truth for all Jev prompts, choice rubrics, score criteria, noul definitions, and decision thresholds.

---

## 1. The Speculative Fan-Out Questions Catalog

All 6 questions below are executed together in a single API request against the unified `StockState`.

### Question 1: `guidance_trajectory`
- **Type:** `choice`
- **Target Field:** `qualitative_commentary.management_guidance`
- **Instructions:**
  ```text
  Evaluate management's forward guidance in `qualitative_commentary.management_guidance`.
  What is the expected trajectory of revenue growth and operating margin over the next 12 months?
  ```
- **Criteria Rubric:**
  | Option | Description |
  | :--- | :--- |
  | `accelerating` | Explicitly increases forward revenue growth rate, raises margin guidance, or details strong order backlog expansion. |
  | `steady` | Reaffirms consensus targets; business operates in-line with historical baseline without material slowdown. |
  | `decelerating` | Lowers forward guidance, cites demand softness, margin contraction, elongated sales cycles, or inventory glut. |

---

### Question 2: `management_conviction`
- **Type:** `score`
- **Target Field:** `qualitative_commentary.concall_qa_highlights`
- **Instructions:**
  ```text
  Based on executive answers to analyst questions in `qualitative_commentary.concall_qa_highlights`,
  rate management's conviction and operational transparency.
  ```
- **Criteria Levels (0 to 3):**
  - **Level 0 (Evasive / Defensive):**
    `Non-answers to hard questions, changing topics, blaming external factors without operational ownership, defensive tone.`
  - **Level 1 (Cautious / Limited Visibility):**
    `Acknowledges significant macroeconomic or sector headwinds; emphasizes lack of forward visibility; conservative outlook.`
  - **Level 2 (Pragmatic / Balanced Execution):**
    `Measured, balanced tone backed by concrete operational figures, customer metrics, and steady execution milestones.`
  - **Level 3 (High Conviction / Catalysts):**
    `Unambiguous forward optimism, firm multi-quarter visibility, robust capacity utilization, and demonstrable pricing power.`

---

### Question 3: `economic_moat`
- **Type:** `score`
- **Target Field:** `state` (incorporating `financial_metrics.gross_margin` and `qualitative_commentary`)
- **Instructions:**
  ```text
  Rate the structural economic moat, pricing power, and customer switching costs of `company_name`.
  ```
- **Criteria Levels (0 to 3):**
  - **Level 0 (Commodity / Pure Price-Taker):**
    `Zero pricing power, fierce undifferentiated competition, cyclical margin swings, low customer switching costs.`
  - **Level 1 (Narrow Moat):**
    `Moderate brand recall or mild switching costs; competitors can match offerings with capital investment.`
  - **Level 2 (Wide Moat):**
    `Dominant market position, mission-critical ecosystem lock-in, proprietary IP/technology, and consistent pricing power.`
  - **Level 3 (Monopoly / Insuperable Advantage):**
    `Near-monopolistic market control, insurmountable network effects or regulatory barriers, captive customer base.`

---

### Question 4: `forensic_governance_risk`
- **Type:** `noul` (Binary Probability: 0.0 to 1.0)
- **Target Field:** `market_specific_data`, `qualitative_commentary.risk_factors`, `financial_metrics`
- **Instructions:**
  ```text
  Are there material corporate governance, promoter pledging, accounting red flags, or insolvency risks indicated in `state`?
  ```
- **Criteria Rubric:**
  - **`true` (High Risk / Fraud / Distress):**
    `Promoter pledge exceeds 15% (India), sudden mid-tenure auditor resignations, severe related-party transactions, unverified receivables surges, or aggressive restatements.`
  - **`false` (Clean / Audit Verified):**
    `Standard institutional governance, negligible promoter pledge, verified statutory auditor signatures, and transparent reporting.`

---

### Question 5: `macro_policy_tailwinds`
- **Type:** `choice`
- **Target Field:** `market_specific_data`, `qualitative_commentary.recent_developments`
- **Instructions:**
  ```text
  Does `company_name` benefit from structural government policy or secular macroeconomic tailwinds?
  ```
- **Criteria Rubric:**
  | Option | Description |
  | :--- | :--- |
  | `strong_tailwinds` | Direct beneficiary of Indian government Capex, PLI schemes, Make in India, Defence indigenization, or global AI/cloud secular transitions. |
  | `neutral_cyclical` | Standard macroeconomic exposure with no distinctive policy subsidies or secular accelerators. |
  | `secular_headwinds` | Disrupted by technology, adverse taxation/tariff changes, carbon transition penalties, or aggressive regulatory price caps. |

---

### Question 6: `valuation_sanity`
- **Type:** `score`
- **Target Field:** `financial_metrics` (P/E, PEG, EV/EBITDA, FCF Yield)
- **Instructions:**
  ```text
  Contextualizing `financial_metrics.pe_forward` and `financial_metrics.peg_ratio` against the company's growth rate and moat,
  rate the valuation attractiveness and margin of safety.
  ```
- **Criteria Levels (0 to 3):**
  - **Level 0 (Extreme Bubble / Hyper-Speculative):**
    `Absurd valuation multiples pricing in decades of flawless growth; severe multiple compression inevitable on the slightest miss.`
  - **Level 1 (Rich / Priced to Perfection):**
    `Trading at substantial premium to peers and historical average; leaves little margin for operational error.`
  - **Level 2 (Fair / Growth-Justified):**
    `Reasonable multiple supported by return on equity and sustainable cash flow growth.`
  - **Level 3 (Deep Value / High Margin of Safety):**
    `Significantly undervalued relative to intrinsic cash flow generation and durable moat; compelling risk/reward.`

---

## 2. Quantitative & Synthesis Threshold Constants

These constants govern the decision logic in `decision_engine.py`:

```python
# -------------------------------------------------------------------------
# FORENSIC & GOVERNANCE VETO
# -------------------------------------------------------------------------
FORENSIC_VETO_NOUL_THRESHOLD = 0.60       # If noul > 0.60 -> Immediate STRONG_SELL_OR_AVOID
MAX_SAFE_PROMOTER_PLEDGE_PCT = 15.0      # India: promoter pledge > 15% flags caution; > 25% flags fatal risk
MIN_SAFE_ALTMAN_Z_SCORE = 1.81           # Below 1.81 indicates distress zone

# -------------------------------------------------------------------------
# EXPECTED RETURN THRESHOLDS (12-Month Horizon)
# -------------------------------------------------------------------------
STRONG_BUY_RETURN_THRESHOLD = 0.20        # Expected return >= +20%
BUY_RETURN_THRESHOLD = 0.12               # Expected return >= +12%
HOLD_LOWER_RETURN_THRESHOLD = -0.05       # Expected return between -5% and +12%
SELL_RETURN_THRESHOLD = -0.10             # Expected return < -10%

# -------------------------------------------------------------------------
# CONFIDENCE & MOAT FILTERS
# -------------------------------------------------------------------------
HIGH_CONFIDENCE_THRESHOLD = 0.75          # Required for Strong Buy
MIN_CONFIDENCE_THRESHOLD = 0.50           # Below 0.50 -> Model flags UNCERTAIN / LOW VISIBILITY -> Defaults to HOLD
MIN_MOAT_SCORE_STRONG_BUY = 2.0           # Wide moat requirement (>= 2.0 / 3.0)
MIN_MANAGEMENT_CONVICTION = 1.8           # Required management conviction score

# -------------------------------------------------------------------------
# SCENARIO PROBABILITY WEIGHTING FORMULA
# -------------------------------------------------------------------------
# P(Bull) = Jev['guidance_trajectory']['probabilities']['accelerating']
# P(Base) = Jev['guidance_trajectory']['probabilities']['steady']
# P(Bear) = Jev['guidance_trajectory']['probabilities']['decelerating']
# Expected Target Price = (P_Bull * Bull_Target) + (P_Base * Base_Target) + (P_Bear * Bear_Target)
```
