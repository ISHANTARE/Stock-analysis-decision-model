"""
Decision Engine & Expected Return Synthesis.
Combines deterministic valuation scenarios with Jev's calibrated probabilities,
evaluates forensic governance vetoes, and generates the final Buy/Sell/Hold recommendation.
"""

from typing import Dict, Any, List
from src.constants import (
    FORENSIC_VETO_NOUL_THRESHOLD,
    STRONG_BUY_RETURN_THRESHOLD,
    BUY_RETURN_THRESHOLD,
    SELL_RETURN_THRESHOLD,
    MIN_MOAT_SCORE_STRONG_BUY,
    HIGH_CONFIDENCE_THRESHOLD,
    MIN_CONFIDENCE_THRESHOLD
)


def synthesize_decision(
    stock_state: Dict[str, Any],
    health_metrics: Dict[str, Any],
    valuation_scenarios: Dict[str, Any],
    jev_eval: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synthesizes the complete quantitative and semantic analysis into an actionable recommendation.
    """
    p0 = stock_state["current_price"]
    currency = stock_state["currency"]
    ticker = stock_state["ticker"]
    company_name = stock_state["company_name"]
    market = stock_state["market"]

    # ---------------------------------------------------------------------
    # 1. Extract Scenario Targets and Calibrated Probabilities
    # ---------------------------------------------------------------------
    bull_target = valuation_scenarios["bull_case"]["target_price"]
    base_target = valuation_scenarios["base_case"]["target_price"]
    bear_target = valuation_scenarios["bear_case"]["target_price"]

    probs = jev_eval["guidance_trajectory"]["probabilities"]
    p_bull = float(probs.get("accelerating", 0.25))
    p_base = float(probs.get("steady", 0.50))
    p_bear = float(probs.get("decelerating", 0.25))

    # Normalize probabilities to ensure exact sum of 1.0
    total_prob = p_bull + p_base + p_bear
    if total_prob > 0:
        p_bull /= total_prob
        p_base /= total_prob
        p_bear /= total_prob

    # Expected Target Price & Expected 12M Return
    expected_target = (p_bull * bull_target) + (p_base * base_target) + (p_bear * bear_target)
    expected_return_pct = ((expected_target - p0) / p0) * 100.0

    # Key Jev Dimensions
    guidance_choice = jev_eval["guidance_trajectory"]["choice"]
    confidence = jev_eval["overall_confidence"]
    moat_score = jev_eval["economic_moat"]["score"]
    conviction_score = jev_eval["management_conviction"]["score"]
    forensic_noul = jev_eval["forensic_governance_risk"]["noul"]
    tailwind_choice = jev_eval["macro_policy_tailwinds"]["choice"]

    # ---------------------------------------------------------------------
    # 2. Forensic & Governance Hard Veto Check
    # ---------------------------------------------------------------------
    is_vetoed = False
    veto_reason = None

    if forensic_noul >= FORENSIC_VETO_NOUL_THRESHOLD:
        is_vetoed = True
        veto_reason = (
            f"Severe forensic accounting / corporate governance red flags detected "
            f"(Jev Risk Probability = {forensic_noul * 100:.1f}%)."
        )
    elif health_metrics.get("health_status") == "HIGH_DISTRESS_RISK":
        is_vetoed = True
        veto_reason = (
            f"Critical solvency distress risk (Altman Z-Score = {health_metrics['altman_z_score']})."
        )

    # ---------------------------------------------------------------------
    # 3. Decision Matrix & Action Signals
    # ---------------------------------------------------------------------
    if is_vetoed:
        action = "STRONG_SELL_OR_AVOID"
        conviction_tier = "CRITICAL_RISK_VETO"
        action_summary = f"HARD VETO TRIGGERED: {veto_reason} Capital preservation priority overrules upside."
    else:
        # Confidence Filter: If model is not confident, default to cautious HOLD
        if confidence < MIN_CONFIDENCE_THRESHOLD:
            action = "HOLD"
            conviction_tier = "LOW_VISIBILITY"
            action_summary = (
                f"Model confidence ({confidence:.2f}) is below operational threshold (0.50). "
                f"Conflicting disclosures or low visibility dictate a neutral HOLD."
            )
        elif (
            expected_return_pct >= (STRONG_BUY_RETURN_THRESHOLD * 100)
            and moat_score >= MIN_MOAT_SCORE_STRONG_BUY
            and guidance_choice == "accelerating"
            and confidence >= HIGH_CONFIDENCE_THRESHOLD
        ):
            action = "STRONG_BUY"
            conviction_tier = "HIGH_CONVICTION"
            action_summary = (
                f"Exceptional compounder setup: +{expected_return_pct:.1f}% expected return, "
                f"wide moat ({moat_score:.1f}/3.0), and accelerating forward guidance."
            )
        elif expected_return_pct >= (BUY_RETURN_THRESHOLD * 100) and guidance_choice in ("accelerating", "steady"):
            action = "BUY"
            conviction_tier = "MODERATE_CONVICTION"
            action_summary = (
                f"Attractive risk/reward: +{expected_return_pct:.1f}% expected return "
                f"with durable execution and steady guidance."
            )
        elif expected_return_pct <= (SELL_RETURN_THRESHOLD * 100) or guidance_choice == "decelerating":
            action = "TRIM_OR_SELL"
            conviction_tier = "CAPITAL_PRESERVATION"
            action_summary = (
                f"Negative expected return ({expected_return_pct:.1f}%) or decelerating guidance. "
                f"Recommend trimming exposure to avoid multiple compression."
            )
        else:
            action = "HOLD"
            conviction_tier = "BALANCED_FAIR_VALUE"
            action_summary = (
                f"Stock is fairly valued with {expected_return_pct:+.1f}% expected return. "
                f"Maintain existing position; wait for a wider margin of safety."
            )

    # ---------------------------------------------------------------------
    # 4. Synthesize Catalysts & Risks
    # ---------------------------------------------------------------------
    catalysts: List[str] = []
    risks: List[str] = []

    # Catalysts
    if guidance_choice == "accelerating":
        catalysts.append("Forward guidance indicates accelerated revenue growth and operating leverage.")
    if moat_score >= 2.0:
        catalysts.append(f"Durable economic moat (Score: {moat_score}/3.0) provides pricing power.")
    if conviction_score >= 2.0:
        catalysts.append(f"High management execution transparency and operational conviction (Score: {conviction_score}/3.0).")
    if tailwind_choice == "strong_tailwinds":
        market_label = "Indian government Capex / PLI" if market == "IN" else "Secular industry"
        catalysts.append(f"Direct beneficiary of {market_label} tailwinds.")
    if not catalysts:
        catalysts.append("Stable operating cash flow and consensus revenue delivery.")

    # Risks
    if forensic_noul > 0.30:
        risks.append(f"Elevated governance/forensic scrutiny (Noul risk probability: {forensic_noul * 100:.1f}%).")
    if guidance_choice == "decelerating":
        risks.append("Demand deceleration or margin pressure cited in forward disclosures.")
    if moat_score < 1.5:
        risks.append("Vulnerable to competitor price undercutting or commodity input costs.")
    if health_metrics.get("altman_z_score", 3.0) < 2.5:
        risks.append("Leverage or working capital coverage requires monitoring.")
    if not risks:
        risks.append("Broad market macroeconomic fluctuations and sector rotation risk.")

    return {
        "ticker": ticker,
        "company_name": company_name,
        "current_price": p0,
        "currency": currency,
        "market": market,
        "action": action,
        "conviction_tier": conviction_tier,
        "action_summary": action_summary,
        "expected_target_price": round(expected_target, 2),
        "expected_return_pct": round(expected_return_pct, 2),
        "overall_confidence": confidence,
        "scenarios_breakdown": {
            "bull": {
                "target": bull_target,
                "probability": round(p_bull, 2),
                "upside_pct": valuation_scenarios["bull_case"]["upside_pct"]
            },
            "base": {
                "target": base_target,
                "probability": round(p_base, 2),
                "upside_pct": valuation_scenarios["base_case"]["upside_pct"]
            },
            "bear": {
                "target": bear_target,
                "probability": round(p_bear, 2),
                "upside_pct": valuation_scenarios["bear_case"]["upside_pct"]
            }
        },
        "fundamental_scores": {
            "economic_moat": round(moat_score, 2),
            "management_conviction": round(conviction_score, 2),
            "guidance_trajectory": guidance_choice,
            "forensic_risk_noul": forensic_noul,
            "macro_tailwinds": tailwind_choice,
            "altman_z_score": health_metrics.get("altman_z_score")
        },
        "key_catalysts": catalysts,
        "primary_risks": risks,
        "is_vetoed": is_vetoed,
        "veto_reason": veto_reason
    }
