# Data Formats & Schemas Specification
## Project: Quantamental Stock Analysis & Decision Model

This document specifies the exact JSON schemas, field definitions, and data contracts used across every layer of the system:
1. **Raw Market Data Ingestion Contract**
2. **Unified State Schema** (Compiled for Jev input)
3. **Jev Evaluation Request & Response Schemas**
4. **Scenario Valuation Model Contract**
5. **Final Output Decision Report Contract**

---

## 1. Unified State Schema (`StockState`)

This is the exact JSON structure passed to Jev's `state` field. It encapsulates both quantitative ratios and qualitative disclosures, normalized for Indian and Global stocks.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StockState",
  "type": "object",
  "required": [
    "ticker",
    "company_name",
    "market",
    "currency",
    "current_price",
    "market_cap",
    "financial_metrics",
    "qualitative_commentary"
  ],
  "properties": {
    "ticker": { "type": "string", "example": "RELIANCE.NS" },
    "company_name": { "type": "string", "example": "Reliance Industries Limited" },
    "market": { "type": "string", "enum": ["IN", "GLOBAL"], "example": "IN" },
    "exchange": { "type": "string", "enum": ["NSE", "BSE", "NASDAQ", "NYSE", "OTHER"], "example": "NSE" },
    "currency": { "type": "string", "enum": ["INR", "USD", "EUR", "GBP"], "example": "INR" },
    "current_price": { "type": "number", "example": 1226.40 },
    "market_cap_formatted": { "type": "string", "example": "₹16.59 Lakh Cr" },
    
    "financial_metrics": {
      "type": "object",
      "required": ["pe_trailing", "pe_forward", "revenue_growth_yoy", "operating_margin"],
      "properties": {
        "pe_trailing": { "type": "number", "example": 22.5 },
        "pe_forward": { "type": "number", "example": 17.2 },
        "ev_to_ebitda": { "type": "number", "example": 14.8 },
        "price_to_book": { "type": "number", "example": 2.1 },
        "price_to_free_cash_flow": { "type": "number", "example": 19.4 },
        "peg_ratio": { "type": ["number", "null"], "example": 1.35 },
        "dividend_yield_pct": { "type": "number", "example": 0.8 },
        "revenue_growth_yoy": { "type": "number", "example": 0.115 },
        "gross_margin": { "type": "number", "example": 0.42 },
        "operating_margin": { "type": "number", "example": 0.168 },
        "net_profit_margin": { "type": "number", "example": 0.088 },
        "roe": { "type": "number", "example": 0.124 },
        "roce_or_roic": { "type": "number", "example": 0.118 },
        "net_debt_to_ebitda": { "type": "number", "example": 1.2 },
        "current_ratio": { "type": "number", "example": 1.3 },
        "altman_z_score": { "type": ["number", "null"], "example": 3.8 },
        "piotroski_f_score": { "type": ["integer", "null"], "example": 7 },
        "rsi_14": { "type": ["number", "null"], "example": 48.6 }
      }
    },

    "market_specific_data": {
      "type": "object",
      "description": "Region-specific indicators for Indian or Global stocks",
      "properties": {
        "india_metrics": {
          "type": "object",
          "properties": {
            "promoter_holding_pct": { "type": "number", "example": 50.3 },
            "promoter_pledge_pct": { "type": "number", "example": 0.0 },
            "fii_holding_pct": { "type": "number", "example": 21.8 },
            "dii_holding_pct": { "type": "number", "example": 16.5 },
            "public_holding_pct": { "type": "number", "example": 11.4 },
            "pli_scheme_beneficiary": { "type": "boolean", "example": true }
          }
        },
        "global_metrics": {
          "type": "object",
          "properties": {
            "institutional_ownership_pct": { "type": "number", "example": 68.2 },
            "insider_ownership_pct": { "type": "number", "example": 8.4 },
            "sbc_dilution_pct": { "type": "number", "example": 0.012 },
            "buyback_yield_pct": { "type": "number", "example": 0.024 }
          }
        }
      }
    },

    "qualitative_commentary": {
      "type": "object",
      "required": ["management_guidance", "recent_developments", "risk_factors"],
      "properties": {
        "management_guidance": {
          "type": "string",
          "description": "Executive outlook from concalls, press releases, or guidance notes"
        },
        "concall_qa_highlights": {
          "type": "string",
          "description": "Transcript excerpts of management answers to analyst questions"
        },
        "recent_developments": {
          "type": "string",
          "description": "Latest 3-5 news events, contract wins, or product launches"
        },
        "risk_factors": {
          "type": "string",
          "description": "Key concerns (e.g. debt covenants, raw material inflation, regulatory scrutiny)"
        }
      }
    }
  }
}
```

---

## 2. Jev System One Request & Response Schema

### 2.1 Request Schema (`POST https://api.typesafe.ai/v1/systemone`)
```json
{
  "state": "<StockState JSON Object>",
  "model": "jev-latest",
  "questions": {
    "guidance_trajectory": {
      "type": "choice",
      "instructions": "What is the trajectory of forward guidance in `qualitative_commentary.management_guidance`?",
      "criteria": {
        "accelerating": "Explicitly guides higher growth or expanding margins",
        "steady": "Reaffirms consensus growth rate without disruption",
        "decelerating": "Lowers guidance or cites mounting headwinds"
      }
    },
    "management_conviction": {
      "type": "score",
      "instructions": "Rate management's conviction in `qualitative_commentary.concall_qa_highlights`.",
      "criteria": [
        "Evasive or defensive",
        "Cautious with limited visibility",
        "Pragmatic with clear execution data",
        "High conviction with unambiguous tailwinds"
      ]
    },
    "economic_moat": {
      "type": "score",
      "instructions": "Rate the pricing power and customer switching costs in `state`.",
      "criteria": [
        "Commodity price-taker",
        "Narrow moat with competitor parity",
        "Wide moat with captive customer base",
        "Near-monopoly pricing power"
      ]
    },
    "forensic_governance_risk": {
      "type": "noul",
      "instructions": "Are there material corporate governance, promoter pledge, or accounting red flags?",
      "criteria": {
        "true": "High promoter pledge (>15%), auditor issues, or accounting manipulation",
        "false": "Clean corporate governance and audited disclosures"
      }
    },
    "macro_policy_tailwinds": {
      "type": "choice",
      "instructions": "Does the company enjoy structural macro or policy tailwinds?",
      "criteria": {
        "strong_tailwinds": "Major beneficiary of government capex, PLI, or secular trend",
        "neutral_cyclical": "Standard cyclical exposure without distinctive incentives",
        "secular_headwinds": "Disrupted by technology or adverse regulatory policy"
      }
    },
    "valuation_sanity": {
      "type": "score",
      "instructions": "Contextualizing `financial_metrics` against growth, rate the valuation margin of safety.",
      "criteria": [
        "Extreme bubble / severe multiple compression risk",
        "Richly valued with low room for error",
        "Fairly valued relative to peers and growth",
        "Deeply undervalued with high margin of safety"
      ]
    }
  }
}
```

### 2.2 Response Schema
```json
{
  "model": "jev-1.13.0",
  "answers": {
    "guidance_trajectory": {
      "type": "choice",
      "choice": "accelerating",
      "confidence": 0.84,
      "probabilities": {
        "accelerating": 0.72,
        "steady": 0.22,
        "decelerating": 0.06
      }
    },
    "management_conviction": {
      "type": "score",
      "score": 2.35,
      "confidence": 0.79,
      "legend": { "0": "Evasive", "1": "Cautious", "2": "Pragmatic", "3": "High conviction" },
      "probabilities": { "0": 0.01, "1": 0.08, "2": 0.46, "3": 0.45 }
    },
    "economic_moat": {
      "type": "score",
      "score": 2.10,
      "confidence": 0.81,
      "legend": { "0": "Commodity", "1": "Narrow", "2": "Wide", "3": "Monopoly" },
      "probabilities": { "0": 0.02, "1": 0.16, "2": 0.52, "3": 0.30 }
    },
    "forensic_governance_risk": {
      "type": "noul",
      "noul": 0.04
    },
    "macro_policy_tailwinds": {
      "type": "choice",
      "choice": "strong_tailwinds",
      "confidence": 0.76,
      "probabilities": {
        "strong_tailwinds": 0.68,
        "neutral_cyclical": 0.28,
        "secular_headwinds": 0.04
      }
    },
    "valuation_sanity": {
      "type": "score",
      "score": 1.95,
      "confidence": 0.70,
      "legend": { "0": "Bubble", "1": "Rich", "2": "Fair", "3": "Undervalued" },
      "probabilities": { "0": 0.04, "1": 0.22, "2": 0.49, "3": 0.25 }
    }
  },
  "usage": {
    "input_tokens": 812,
    "output_tokens": 128
  }
}
```

---

## 3. Scenario Valuation & Synthesis Schema

```json
{
  "ticker": "RELIANCE.NS",
  "current_price": 1226.40,
  "currency": "INR",
  
  "valuation_scenarios": {
    "bull_case": {
      "scenario_name": "Bull",
      "target_price": 1550.00,
      "upside_pct": 26.39,
      "assumptions": "Accelerating retail/Jio telecom growth + multiple expansion to 26x P/E",
      "probability": 0.72
    },
    "base_case": {
      "scenario_name": "Base",
      "target_price": 1340.00,
      "upside_pct": 9.26,
      "assumptions": "Consensus 12% revenue growth + 20x forward P/E",
      "probability": 0.22
    },
    "bear_case": {
      "scenario_name": "Bear",
      "target_price": 1050.00,
      "upside_pct": -14.38,
      "assumptions": "Oil-to-chemicals margin slowdown + multiple de-rating to 16x P/E",
      "probability": 0.06
    }
  },

  "synthesis": {
    "expected_target_price": 1473.80,
    "expected_return_pct": 20.17,
    "expected_horizon_months": 12,
    "overall_confidence": 0.84,
    
    "governance_audit": {
      "is_vetoed": false,
      "forensic_risk_score": 0.04,
      "promoter_pledge_flag": "Safe (0.0% Pledged)"
    },
    
    "fundamental_grades": {
      "moat_rating": "Wide Moat (Score: 2.10/3.0)",
      "management_conviction": "High Conviction (Score: 2.35/3.0)",
      "macro_tailwind": "Strong Policy & Capex Tailwinds (P=0.68)",
      "valuation_grade": "Fair to Attractive (Score: 1.95/3.0)"
    },
    
    "recommendation": {
      "action": "STRONG_BUY",
      "conviction_tier": "HIGH_CONVICTION",
      "recommended_action_summary": "Attractive risk/reward with 20.2% expected 12-month return backed by wide moat and accelerating guidance.",
      "key_catalysts": [
        "Accelerating forward guidance in high-margin segments",
        "Clean balance sheet with negligible debt risk",
        "High management operational conviction during concall"
      ],
      "primary_risks": [
        "Global crude/energy refining crack spread volatility",
        "Macro demand headwinds in retail discretionary spend"
      ]
    }
  }
}
```
