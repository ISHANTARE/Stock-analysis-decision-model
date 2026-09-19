"""
Financial Modeling & Valuation Scenarios Engine.
Deterministically computes quantitative health metrics and 3 valuation target scenarios (Bull, Base, Bear).
"""

from typing import Dict, Any


def compute_health_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes financial health proxies: Altman Z-Score zone, solvency, and balance sheet safety.
    """
    debt_equity = metrics.get("debt_to_equity") or 50.0
    current_ratio = metrics.get("current_ratio") or 1.3
    roe = metrics.get("roe") or 0.12
    operating_margin = metrics.get("operating_margin") or 0.15

    # Altman Z-Score Proxy (Solvency indicator)
    # Z > 2.9: Safe Zone | 1.81 <= Z <= 2.99: Grey Zone | Z < 1.81: Distress Zone
    z_score = 1.5
    if current_ratio >= 1.5:
        z_score += 0.8
    elif current_ratio >= 1.0:
        z_score += 0.4

    if debt_equity < 50.0:  # Conservative debt
        z_score += 1.0
    elif debt_equity < 100.0:
        z_score += 0.4
    else:
        z_score -= 0.5

    if operating_margin > 0.15:
        z_score += 0.7
    if roe > 0.15:
        z_score += 0.5

    z_score = round(max(0.5, min(6.0, z_score)), 2)

    if z_score >= 2.99:
        health_status = "HEALTHY_SAFE_ZONE"
    elif z_score >= 1.81:
        health_status = "MODERATE_GREY_ZONE"
    else:
        health_status = "HIGH_DISTRESS_RISK"

    # Piotroski F-Score estimation (0 to 9 scale)
    f_score = 5
    if roe > 0.12:
        f_score += 1
    if operating_margin > 0.12:
        f_score += 1
    if current_ratio >= 1.2:
        f_score += 1
    if debt_equity < 80.0:
        f_score += 1

    return {
        "altman_z_score": z_score,
        "health_status": health_status,
        "piotroski_f_score": min(9, f_score)
    }


def compute_valuation_scenarios(stock_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates 3 deterministic 12-month valuation targets:
    1. Bull Case: Accelerated growth + Multiple expansion
    2. Base Case: In-line consensus growth + Multiple retention
    3. Bear Case: Growth slowdown + Multiple de-rating
    """
    p0 = stock_state["current_price"]
    metrics = stock_state["financial_metrics"]

    base_growth = metrics.get("revenue_growth_yoy") or 0.10
    # Bound base growth to realistic baseline [-15%, +50%]
    base_growth = max(-0.15, min(0.50, base_growth))

    # --- 1. Bull Case ---
    # Strong operating leverage: growth accelerates by 30%, P/E expands by 15%
    bull_growth = min(0.65, base_growth * 1.30 if base_growth > 0 else 0.10)
    bull_multiple_expansion = 1.15
    bull_price = p0 * (1.0 + bull_growth) * bull_multiple_expansion
    # Cap maximum 12M bull target to +75% of current price for sanity
    bull_price = min(p0 * 1.75, max(p0 * 1.05, bull_price))

    # --- 2. Base Case ---
    # Consensus execution: earnings grow in-line with base growth
    base_price = p0 * (1.0 + base_growth)
    # Bound base case between -10% and +35%
    base_price = min(p0 * 1.35, max(p0 * 0.90, base_price))

    # --- 3. Bear Case ---
    # Downside scenario: growth cuts in half, multiple contracts by 20%
    bear_growth = max(-0.25, base_growth * 0.40 if base_growth > 0 else base_growth * 1.5)
    bear_multiple_compression = 0.80
    bear_price = p0 * (1.0 + bear_growth) * bear_multiple_compression
    # Floor bear case to -45% maximum drawdown
    bear_price = max(p0 * 0.55, min(p0 * 0.95, bear_price))

    bull_upside = round(((bull_price - p0) / p0) * 100.0, 2)
    base_upside = round(((base_price - p0) / p0) * 100.0, 2)
    bear_upside = round(((bear_price - p0) / p0) * 100.0, 2)

    return {
        "current_price": p0,
        "bull_case": {
            "scenario": "Bull",
            "target_price": round(bull_price, 2),
            "upside_pct": bull_upside,
            "rationale": f"Accelerated growth (+{bull_growth * 100:.1f}%) and 15% multiple expansion"
        },
        "base_case": {
            "scenario": "Base",
            "target_price": round(base_price, 2),
            "upside_pct": base_upside,
            "rationale": f"Consensus growth (+{base_growth * 100:.1f}%) and stable valuation multiple"
        },
        "bear_case": {
            "scenario": "Bear",
            "target_price": round(bear_price, 2),
            "upside_pct": bear_upside,
            "rationale": f"Growth slowdown (+{bear_growth * 100:.1f}%) and 20% multiple de-rating"
        }
    }
