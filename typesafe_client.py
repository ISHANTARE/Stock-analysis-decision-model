"""
TypeSafe AI System One Client & Stock Analysis Helper.

Connects to TypeSafe AI's Jev model (POST https://api.typesafe.ai/v1/systemone)
using calibrated probabilities and typed primitives (Noul, Choice, Score).
Zero third-party dependencies required (built on Python standard library).
"""

import os
import json
import urllib.request
import urllib.error
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


def load_env():
    """Load environment variables from .env file if present."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and not os.environ.get(key):
                        os.environ[key] = val
                elif line.startswith("apikey_") and not os.environ.get("TYPESAFE_API_KEY"):
                    # Handle raw key line
                    os.environ["TYPESAFE_API_KEY"] = line


# Load environment variables on import
load_env()


class Noul:
    """Helper to construct a Noul (yes/no) question."""
    def __init__(self, instructions: str, criteria: Optional[Dict[str, str]] = None):
        self.type = "noul"
        self.instructions = instructions
        self.criteria = criteria

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": "noul", "instructions": self.instructions}
        if self.criteria:
            d["criteria"] = self.criteria
        return d


class Choice:
    """Helper to construct a Choice (categorical selection) question."""
    def __init__(self, instructions: str, criteria: Dict[str, Optional[str]]):
        self.type = "choice"
        self.instructions = instructions
        self.criteria = criteria

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "choice",
            "instructions": self.instructions,
            "criteria": self.criteria
        }


class Score:
    """Helper to construct a Score (ordinal/continuous rating) question."""
    def __init__(self, instructions: str, criteria: List[str]):
        if len(criteria) < 2:
            raise ValueError("Score question criteria must contain at least 2 levels.")
        self.type = "score"
        self.instructions = instructions
        self.criteria = criteria

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "score",
            "instructions": self.instructions,
            "criteria": self.criteria
        }


class TypeSafeClient:
    """
    TypeSafe AI System One Client.
    Connects to the TypeSafe evaluation endpoint using the Jev model family.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.typesafe.ai/v1",
        default_model: str = "jev-latest",
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing TypeSafe API key. Set TYPESAFE_API_KEY in your .env or pass api_key to TypeSafeClient."
            )
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/systemone"
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries

    def evaluate(
        self,
        state: Union[str, Dict[str, Any], List[Any]],
        questions: Dict[str, Union[Dict[str, Any], Noul, Choice, Score]],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a state against a map of typed questions in parallel.

        Args:
            state: Text or structured JSON data to evaluate.
            questions: Dictionary mapping question IDs to question definitions.
            model: Model name/alias (defaults to 'jev-latest').

        Returns:
            Dictionary with 'model', 'answers', and 'usage'.
        """
        # Normalize questions to dictionaries
        normalized_questions = {}
        for q_id, q_val in questions.items():
            if hasattr(q_val, "to_dict"):
                normalized_questions[q_id] = q_val.to_dict()
            elif isinstance(q_val, dict):
                normalized_questions[q_id] = q_val
            else:
                raise ValueError(f"Invalid question definition for '{q_id}': {q_val}")

        payload = {
            "state": state,
            "model": model or self.default_model,
            "questions": normalized_questions
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TypeSafe-StockModel/1.0"
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data_bytes, headers=headers)

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_data = resp.read().decode("utf-8")
                    return json.loads(resp_data)
            except urllib.error.HTTPError as e:
                last_error = e
                # Retry on rate limit (429) or temporary server overload (529 / 503)
                if e.code in (429, 503, 529) and attempt < self.max_retries:
                    retry_after = e.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else (2 ** attempt * 1.5)
                    time.sleep(delay)
                    continue
                error_body = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"TypeSafe API Error HTTP {e.code}: {error_body}"
                ) from e
            except urllib.error.URLError as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt * 1.0)
                    continue
                raise RuntimeError(f"TypeSafe Connection Error: {e.reason}") from e

        raise RuntimeError(f"TypeSafe request failed after retries: {last_error}")

    def analyze_stock(
        self,
        ticker: str,
        financial_summary: Dict[str, Any],
        transcript_or_news: str
    ) -> Dict[str, Any]:
        """
        High-level helper executing a Speculative Fan-out stock analysis evaluation.
        """
        state = {
            "ticker": ticker,
            "financial_metrics": financial_summary,
            "commentary": transcript_or_news
        }

        questions = {
            "growth_sustainability": Score(
                instructions="Based on `financial_metrics` and `commentary`, rate the durability of revenue growth.",
                criteria=[
                    "Deteriorating or artificial growth",
                    "Cyclical with imminent slowdown risk",
                    "Steady and defensible growth",
                    "Exceptional structural compounder"
                ]
            ),
            "earnings_sentiment": Choice(
                instructions="Assess the fundamental tone and outlook presented in `commentary`.",
                criteria={
                    "bullish": "Positive surprises, expanding margins, upbeat forward guidance",
                    "neutral": "Mixed results, meeting expectations without clear catalysts",
                    "bearish": "Missed expectations, margin compression, cautious or lowered guidance"
                }
            ),
            "accounting_red_flags": Noul(
                instructions="Are there indicators of aggressive revenue recognition, sudden margin deterioration, or evasiveness?",
                criteria={
                    "true": "Anomalies, warning signs, or unresolved red flags present",
                    "false": "Clean, standard reporting without material forensic concerns"
                }
            ),
            "pricing_power": Score(
                instructions="Rate the pricing power and customer loyalty implied in `state`.",
                criteria=[
                    "Zero pricing power (pure commodity)",
                    "Weak pricing power (vulnerable to inflation)",
                    "Moderate pricing power (can pass through costs)",
                    "High pricing power (commanding premium with expanding margins)"
                ]
            )
        }

        return self.evaluate(state=state, questions=questions)


if __name__ == "__main__":
    print("Initializing TypeSafe Client and running test stock analysis...")
    client = TypeSafeClient()

    sample_metrics = {
        "revenue_growth_yoy": "+12.4%",
        "gross_margin": "44.2%",
        "free_cash_flow_margin": "23.8%",
        "net_debt_to_ebitda": "0.8x",
        "pe_ratio": 24.1
    }

    sample_transcript = (
        "During Q2, enterprise recurring revenue expanded by 18%, driven by robust adoption of our "
        "cloud security modules. We experienced some elongated sales cycles in Europe, but gross margins "
        "expanded 120 bps due to automation efficiencies. Full-year operating margin guidance is reaffirmed."
    )

    result = client.analyze_stock(
        ticker="NVX",
        financial_summary=sample_metrics,
        transcript_or_news=sample_transcript
    )

    print("\n--- Model Response ---")
    print("Model:", result.get("model"))
    print("Token Usage:", result.get("usage"))
    print("\n--- Typed Answers ---")
    for q_id, answer in result.get("answers", {}).items():
        print(f"\n[{q_id.upper()}] (Type: {answer.get('type')})")
        if answer.get("type") == "choice":
            print(f"  Selected Choice : {answer.get('choice')} (Confidence: {answer.get('confidence'):.2f})")
            print(f"  Probabilities   : {answer.get('probabilities')}")
        elif answer.get("type") == "score":
            print(f"  Expected Score  : {answer.get('score'):.2f} (Confidence: {answer.get('confidence'):.2f})")
            print(f"  Level Probabilities: {answer.get('probabilities')}")
        elif answer.get("type") == "noul":
            print(f"  Noul Probability: {answer.get('noul'):.2f}")
