"""
Constants, Question Prompts, Option Rubrics, and Thresholds for TypeSafe AI Stock Engine.
"""

from typing import Dict, Any

# -------------------------------------------------------------------------
# INDIAN POPULAR BLUECHIP TICKER AUTO-RESOLVER
# -------------------------------------------------------------------------
INDIAN_BLUECHIPS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "LT": "LT.NS",
    "AXISBANK": "AXISBANK.NS",
    "ASIANPAINT": "ASIANPAINT.NS",
    "MARUTI": "MARUTI.NS",
    "TITAN": "TITAN.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS",
    "WIPRO": "WIPRO.NS",
    "ZOMATO": "ZOMATO.NS",
    "TATASTEEL": "TATASTEEL.NS",
    "POWERGRID": "POWERGRID.NS",
    "NTPC": "NTPC.NS",
    "ONGC": "ONGC.NS",
    "COALINDIA": "COALINDIA.NS",
    "ADANIENT": "ADANIENT.NS",
    "ADANIPORTS": "ADANIPORTS.NS",
    "HAL": "HAL.NS",
    "BEL": "BEL.NS",
}

# -------------------------------------------------------------------------
# DECISION & RISK THRESHOLDS
# -------------------------------------------------------------------------
FORENSIC_VETO_NOUL_THRESHOLD = 0.60       # If noul > 0.60 -> Immediate STRONG_SELL_OR_AVOID
MAX_SAFE_PROMOTER_PLEDGE_PCT = 15.0      # India: promoter pledge > 15% flags caution; > 25% flags danger
MIN_SAFE_ALTMAN_Z_SCORE = 1.81           # Below 1.81 indicates distress zone

STRONG_BUY_RETURN_THRESHOLD = 0.20        # Expected 12M return >= +20%
BUY_RETURN_THRESHOLD = 0.12               # Expected 12M return >= +12%
HOLD_LOWER_RETURN_THRESHOLD = -0.05       # Expected 12M return between -5% and +12%
SELL_RETURN_THRESHOLD = -0.10             # Expected 12M return < -10%

HIGH_CONFIDENCE_THRESHOLD = 0.75          # Required for Strong Buy
MIN_CONFIDENCE_THRESHOLD = 0.50           # Below 0.50 -> Model flags UNCERTAIN -> Defaults to HOLD
MIN_MOAT_SCORE_STRONG_BUY = 2.0           # Required moat score for Strong Buy (out of 3.0)


# -------------------------------------------------------------------------
# CENTRALIZED JEV SPECULATIVE FAN-OUT QUESTIONS
# -------------------------------------------------------------------------
JEV_STOCK_QUESTIONS: Dict[str, Dict[str, Any]] = {
    # 1. Forward Guidance & Growth Trajectory
    "guidance_trajectory": {
        "type": "choice",
        "instructions": (
            "Evaluate management's forward guidance in `qualitative_commentary.management_guidance`. "
            "What is the expected trajectory of revenue growth and operating margin over the next 12 months?"
        ),
        "criteria": {
            "accelerating": "Explicitly increases forward revenue growth rate, raises margin guidance, or details strong order backlog expansion.",
            "steady": "Reaffirms consensus targets; business operates in-line with historical baseline without material slowdown.",
            "decelerating": "Lowers forward guidance, cites demand softness, margin contraction, elongated sales cycles, or inventory glut."
        }
    },

    # 2. Management Conviction vs Evasion (Q&A / Disclosures)
    "management_conviction": {
        "type": "score",
        "instructions": (
            "Based on executive commentary and disclosures in `qualitative_commentary.concall_qa_highlights`, "
            "rate management's conviction and operational transparency."
        ),
        "criteria": [
            "Evasive: Giving non-answers, redirecting questions, defensive tone, or shifting blame to macro.",
            "Cautious: Acknowledging severe headwinds, emphasizing limited forward visibility, conservative posture.",
            "Pragmatic: Balanced and measured tone backed by concrete operational figures, customer metrics, and steady milestones.",
            "High Conviction: Unambiguous forward optimism, firm multi-quarter visibility, robust capacity utilization, and clear pricing power."
        ]
    },

    # 3. Structural Economic Moat & Pricing Power
    "economic_moat": {
        "type": "score",
        "instructions": (
            "Rate the structural economic moat, pricing power, and customer switching costs of `company_name` "
            "based on its margins and competitive position in `state`."
        ),
        "criteria": [
            "Commodity / Zero Pricing Power: Pure price-taker, fierce competition, cyclical margin swings, zero switching costs.",
            "Narrow Moat: Moderate brand recall or mild switching costs; competitors can match offerings with capital investment.",
            "Wide Moat: Dominant market share, mission-critical ecosystem lock-in, proprietary IP, and persistent pricing power.",
            "Monopoly / Unassailable Advantage: Near-monopoly control, insurmountable network effects or regulatory barriers, captive customer base."
        ]
    },

    # 4. Forensic Accounting & Corporate Governance Red Flag Veto
    "forensic_governance_risk": {
        "type": "noul",
        "instructions": (
            "Are there material corporate governance, promoter pledging, accounting red flags, or insolvency risks indicated in `state`?"
        ),
        "criteria": {
            "true": "Promoter pledge exceeds 15% (India), sudden mid-tenure auditor resignations, severe related-party transactions, unverified receivables surges, or aggressive restatements.",
            "false": "Standard institutional governance, negligible promoter pledge, verified statutory auditor signatures, and transparent reporting."
        }
    },

    # 5. Macro, Policy & Industrial Tailwinds
    "macro_policy_tailwinds": {
        "type": "choice",
        "instructions": (
            "Does `company_name` benefit from structural government policy or secular macroeconomic tailwinds?"
        ),
        "criteria": {
            "strong_tailwinds": "Direct beneficiary of Indian government Capex, PLI schemes, Make in India, Defence indigenization, or global AI/cloud secular transitions.",
            "neutral_cyclical": "Standard macroeconomic exposure with no distinctive policy subsidies or secular accelerators.",
            "secular_headwinds": "Disrupted by technology, adverse taxation/tariff changes, carbon transition penalties, or aggressive regulatory price caps."
        }
    },

    # 6. Valuation Sanity & Margin of Safety
    "valuation_sanity": {
        "type": "score",
        "instructions": (
            "Contextualizing `financial_metrics.pe_forward` and `financial_metrics.peg_ratio` against the company's growth rate and moat, "
            "rate the valuation attractiveness and margin of safety."
        ),
        "criteria": [
            "Extreme Bubble / Hyper-Speculative: Absurd valuation multiples pricing in decades of flawless growth; severe multiple compression inevitable.",
            "Rich / Priced to Perfection: Trading at substantial premium to peers and historical average; leaves little margin for operational error.",
            "Fair / Growth-Justified: Reasonable multiple supported by return on equity and sustainable cash flow growth.",
            "Deep Value / High Margin of Safety: Significantly undervalued relative to intrinsic cash flow generation and durable moat; compelling risk/reward."
        ]
    }
}
