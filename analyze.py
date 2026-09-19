#!/usr/bin/env python3
"""
Quantamental Stock Analysis & Decision Engine CLI.
Analyzes Indian (NSE/BSE) and Global (US/EU) stocks using TypeSafe AI (Jev).
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.market_data import fetch_stock_state
from src.financial_engine import compute_health_metrics, compute_valuation_scenarios
from src.jev_evaluator import JevEvaluator
from src.decision_engine import synthesize_decision


# ANSI Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner(text: str, color: str = CYAN):
    border = "═" * 78
    print(f"\n{color}{BOLD}{border}{RESET}")
    print(f"{color}{BOLD}  {text}{RESET}")
    print(f"{color}{BOLD}{border}{RESET}")


def format_action_banner(action: str) -> str:
    if action == "STRONG_BUY":
        return f"{GREEN}{BOLD}██  [ STRONG BUY ] - HIGH CONVICTION ALLOCATION  ██{RESET}"
    elif action == "BUY":
        return f"{GREEN}{BOLD}██  [ BUY ] - ATTRACTIVE ACCUMULATION SETUP     ██{RESET}"
    elif action == "HOLD":
        return f"{YELLOW}{BOLD}██  [ HOLD ] - BALANCED / WAIT FOR MARGIN OF SAFETY ██{RESET}"
    elif action == "TRIM_OR_SELL":
        return f"{RED}{BOLD}██  [ TRIM / SELL ] - CAPITAL PRESERVATION PRIORITY ██{RESET}"
    else:  # STRONG_SELL_OR_AVOID
        return f"{RED}{BOLD}██  [ STRONG SELL / AVOID ] - HARD GOVERNANCE VETO  ██{RESET}"


def run_analysis(ticker: str, market: str = None, model: str = "jev-latest", as_json: bool = False):
    """
    Executes the end-to-end quantamental analysis pipeline.
    """
    if not as_json:
        print(f"\n{DIM}Fetching real-time market data & disclosures for '{ticker}'...{RESET}")

    # 1. Ingest Data & Normalize
    try:
        stock_state = fetch_stock_state(ticker=ticker, preferred_market=market)
    except Exception as e:
        print(f"{RED}{BOLD}Error fetching market data:{RESET} {e}")
        sys.exit(1)

    # 2. Compute Health & Quantitative Valuation Scenarios
    health_metrics = compute_health_metrics(stock_state["financial_metrics"])
    valuation_scenarios = compute_valuation_scenarios(stock_state)

    if not as_json:
        print(f"{DIM}Running Jev System One Speculative Fan-out evaluation ({model})...{RESET}")

    # 3. Jev Parallel Semantic Evaluation
    try:
        evaluator = JevEvaluator(model=model)
        jev_eval = evaluator.evaluate_stock(stock_state)
    except Exception as e:
        print(f"{RED}{BOLD}Error during Jev evaluation:{RESET} {e}")
        sys.exit(1)

    # 4. Synthesize Decision & Expected Return
    decision = synthesize_decision(
        stock_state=stock_state,
        health_metrics=health_metrics,
        valuation_scenarios=valuation_scenarios,
        jev_eval=jev_eval
    )

    if as_json:
        full_output = {
            "stock_state": stock_state,
            "health_metrics": health_metrics,
            "valuation_scenarios": valuation_scenarios,
            "jev_evaluation": jev_eval,
            "decision": decision
        }
        print(json.dumps(full_output, indent=2))
        return

    # ---------------------------------------------------------------------
    # RENDER TERMINAL DASHBOARD
    # ---------------------------------------------------------------------
    sym = stock_state["ticker"]
    name = stock_state["company_name"]
    mkt = stock_state["market"]
    exch = stock_state["exchange"]
    curr = stock_state["currency"]
    p0 = stock_state["current_price"]
    mcap = stock_state["market_cap_formatted"]

    print_banner(f"QUANTAMENTAL REPORT: {name} ({sym}) | {exch} ({mkt})", CYAN)

    print(f"\n  {BOLD}Current Price:{RESET} {curr} {p0:,.2f}  │  {BOLD}Market Cap:{RESET} {mcap}  │  {BOLD}P/E (Fwd):{RESET} {stock_state['financial_metrics']['pe_forward'] or 'N/A'}")
    print(f"  {BOLD}P/E (Trailing):{RESET} {stock_state['financial_metrics']['pe_trailing'] or 'N/A'}  │  {BOLD}EV/EBITDA:{RESET} {stock_state['financial_metrics']['ev_to_ebitda'] or 'N/A'}  │  {BOLD}Revenue YoY:{RESET} {stock_state['financial_metrics']['revenue_growth_yoy'] * 100:+.1f}%")

    print("\n" + "─" * 78)
    print("  " + format_action_banner(decision["action"]))
    print("─" * 78)

    # Expected Return Summary
    exp_price = decision["expected_target_price"]
    exp_return = decision["expected_return_pct"]
    conf = decision["overall_confidence"]
    return_color = GREEN if exp_return > 0 else RED

    print(f"\n  {BOLD}Expected 12M Target Price:{RESET} {curr} {exp_price:,.2f}  ({return_color}{exp_return:+.2f}% Expected Return{RESET})")
    print(f"  {BOLD}Model Confidence:{RESET}          {conf:.2f} / 1.00  ({decision['conviction_tier']})")
    print(f"  {BOLD}Summary:{RESET}                   {decision['action_summary']}")

    # Scenario Breakdown Table
    print(f"\n{BOLD}┌── VALUATION SCENARIOS (Weighted by Jev Calibrated Probabilities) ──────┐{RESET}")
    print(f"│  Scenario │ Target Price   │ Upside / Downside │ Jev Probability   │ Weight   │")
    print(f"├───────────┼────────────────┼───────────────────┼───────────────────┼──────────┤")

    scenarios = decision["scenarios_breakdown"]
    for sc_key, sc_name, sc_color in [
        ("bull", "Bull Case", GREEN),
        ("base", "Base Case", CYAN),
        ("bear", "Bear Case", RED)
    ]:
        data = scenarios[sc_key]
        tgt = f"{curr} {data['target']:,.2f}"
        ups = f"{data['upside_pct']:+.1f}%"
        prob = f"{data['probability'] * 100:.1f}%"
        print(f"│  {sc_color}{sc_name:<9}{RESET} │ {tgt:<14} │ {ups:<17} │ {prob:<17} │ {data['probability']:<8.2f} │")
    print(f"└───────────┴────────────────┴───────────────────┴───────────────────┴──────────┘")

    # Jev Semantic Scorecard
    scores = decision["fundamental_scores"]
    moat = scores["economic_moat"]
    conv = scores["management_conviction"]
    guidance = scores["guidance_trajectory"]
    forensic = scores["forensic_risk_noul"]
    tailwind = scores["macro_tailwinds"]
    z_score = scores["altman_z_score"]

    forensic_status = f"{RED}{BOLD}FLAGGED ({forensic:.2f}){RESET}" if forensic > 0.40 else f"{GREEN}SAFE ({forensic:.2f}){RESET}"
    z_status = f"{GREEN}Healthy ({z_score}){RESET}" if z_score >= 2.9 else (f"{YELLOW}Grey Zone ({z_score}){RESET}" if z_score >= 1.8 else f"{RED}Distress ({z_score}){RESET}")

    print(f"\n{BOLD}├── JEV SYSTEM ONE SEMANTIC SCORECARD ───────────────────────────────────┤{RESET}")
    print(f"│  • {BOLD}Economic Moat Rating:{RESET}         {moat:.2f} / 3.00  ({scores_to_moat_label(moat)})")
    print(f"│  • {BOLD}Management Conviction:{RESET}        {conv:.2f} / 3.00  ({scores_to_conv_label(conv)})")
    print(f"│  • {BOLD}Forward Guidance:{RESET}              {guidance.upper()}")
    print(f"│  • {BOLD}Macro & Policy Tailwind:{RESET}       {tailwind.upper()}")
    print(f"│  • {BOLD}Forensic Governance Risk:{RESET}     {forensic_status}")
    print(f"│  • {BOLD}Balance Sheet Solvency:{RESET}       {z_status}")
    print(f"└────────────────────────────────────────────────────────────────────────┘")

    # Key Catalysts
    print(f"\n{BOLD}{GREEN}▲ KEY INVESTMENT CATALYSTS:{RESET}")
    for cat in decision["key_catalysts"]:
        print(f"  {GREEN}✔{RESET} {cat}")

    # Primary Risks
    print(f"\n{BOLD}{RED}▼ PRIMARY INVESTMENT RISKS:{RESET}")
    for risk in decision["primary_risks"]:
        print(f"  {RED}✖{RESET} {risk}")

    if decision.get("is_vetoed"):
        print(f"\n{RED}{BOLD}⚠ CRITICAL GOVERNANCE VETO WARNING:{RESET} {decision.get('veto_reason')}")

    print("\n" + "═" * 78 + "\n")


def scores_to_moat_label(score: float) -> str:
    if score >= 2.5:
        return "Wide Moat / Near Monopoly"
    elif score >= 1.8:
        return "Wide Moat"
    elif score >= 1.0:
        return "Narrow Moat"
    return "Commodity / Weak Moat"


def scores_to_conv_label(score: float) -> str:
    if score >= 2.5:
        return "High Conviction"
    elif score >= 1.8:
        return "Pragmatic / Execution Oriented"
    elif score >= 1.0:
        return "Cautious"
    return "Evasive / Defensive"


def main():
    parser = argparse.ArgumentParser(
        description="Quantamental Stock Analysis & Decision Engine using TypeSafe AI (Jev System One)"
    )
    parser.add_argument(
        "--ticker", "-t",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g. 'RELIANCE.NS', 'TCS', 'NVDA', 'AAPL')"
    )
    parser.add_argument(
        "--market", "-m",
        type=str,
        choices=["IN", "GLOBAL", "US", "NSE"],
        default=None,
        help="Optional market override ('IN' for India/NSE, 'GLOBAL' for US/World)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="jev-latest",
        help="TypeSafe model alias (default: 'jev-latest')"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full raw JSON instead of dashboard"
    )

    args = parser.parse_args()
    run_analysis(
        ticker=args.ticker,
        market=args.market,
        model=args.model,
        as_json=args.json
    )


if __name__ == "__main__":
    main()
