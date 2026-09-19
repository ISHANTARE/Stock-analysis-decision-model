"""
TypeSafe AI Semantic Evaluation Layer.
Executes the parallel Speculative Fan-out query across 6 core fundamental dimensions using Jev.
"""

from typing import Dict, Any
from typesafe_client import TypeSafeClient
from src.constants import JEV_STOCK_QUESTIONS


class JevEvaluator:
    """
    Evaluates compiled stock states using TypeSafe's flagship System One model (Jev).
    """
    def __init__(self, api_key: str = None, model: str = "jev-latest"):
        self.client = TypeSafeClient(api_key=api_key)
        self.model = model

    def evaluate_stock(self, stock_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes parallel speculative fan-out evaluation against Jev.
        """
        raw_response = self.client.evaluate(
            state=stock_state,
            questions=JEV_STOCK_QUESTIONS,
            model=self.model
        )

        answers = raw_response.get("answers", {})

        # Extract Guidance Trajectory
        guidance = answers.get("guidance_trajectory", {})
        guidance_choice = guidance.get("choice", "steady")
        guidance_probs = guidance.get("probabilities", {
            "accelerating": 0.25,
            "steady": 0.50,
            "decelerating": 0.25
        })
        guidance_conf = guidance.get("confidence", 0.60)

        # Extract Management Conviction
        conviction = answers.get("management_conviction", {})
        conviction_score = conviction.get("score", 1.8)
        conviction_conf = conviction.get("confidence", 0.60)

        # Extract Economic Moat
        moat = answers.get("economic_moat", {})
        moat_score = moat.get("score", 1.8)
        moat_conf = moat.get("confidence", 0.65)

        # Extract Forensic Governance Risk (Noul)
        forensic = answers.get("forensic_governance_risk", {})
        forensic_risk_noul = forensic.get("noul", 0.05)

        # Extract Macro Tailwinds
        tailwinds = answers.get("macro_policy_tailwinds", {})
        tailwind_choice = tailwinds.get("choice", "neutral_cyclical")
        tailwind_conf = tailwinds.get("confidence", 0.65)
        tailwind_probs = tailwinds.get("probabilities", {})

        # Extract Valuation Sanity
        valuation = answers.get("valuation_sanity", {})
        valuation_score = valuation.get("score", 1.8)
        valuation_conf = valuation.get("confidence", 0.65)

        # Overall average confidence
        overall_confidence = round(
            (guidance_conf + conviction_conf + moat_conf + tailwind_conf + valuation_conf) / 5.0,
            2
        )

        return {
            "model": raw_response.get("model", self.model),
            "usage": raw_response.get("usage", {}),
            "overall_confidence": overall_confidence,
            "guidance_trajectory": {
                "choice": guidance_choice,
                "probabilities": guidance_probs,
                "confidence": guidance_conf
            },
            "management_conviction": {
                "score": round(conviction_score, 2),
                "confidence": conviction_conf
            },
            "economic_moat": {
                "score": round(moat_score, 2),
                "confidence": moat_conf
            },
            "forensic_governance_risk": {
                "noul": round(forensic_risk_noul, 3)
            },
            "macro_policy_tailwinds": {
                "choice": tailwind_choice,
                "confidence": tailwind_conf,
                "probabilities": tailwind_probs
            },
            "valuation_sanity": {
                "score": round(valuation_score, 2),
                "confidence": valuation_conf
            },
            "raw_answers": answers
        }
