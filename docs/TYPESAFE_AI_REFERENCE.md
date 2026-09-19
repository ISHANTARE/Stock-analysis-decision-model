# TypeSafe AI & Jev (System One) Comprehensive Reference

This reference documents the complete API specification, design principles, primitives, patterns, known jagged edges, and code recipes for working with **TypeSafe AI** and its flagship System One model, **Jev** (`jev-latest`, `jev-1.13.0`).

---

## 1. System One Architecture & Philosophy

TypeSafe AI models (flagship: **Jev**) are **System One** models built specifically for software:
- **Programmable Common Sense**: Unlike generative LLMs (System Two) that produce free-form text or step-by-step reasoning chains, System One models return **fast, typed decisions and calibrated probabilities** that software can consume and compose directly.
- **Code Owns Control Flow**: The model never chooses its next action or writes unstructured prose. Your application code retains complete control of loops, deterministic calculations, thresholds, arithmetic, state management, and side effects.
- **Calibrated Probabilities**: Answers represent true statistical distributions over discrete choices or continuous score rubrics, not token-generation approximations.
- **Single Ingestion, Parallel Evaluation**: A request sends an application `state` once, along with an arbitrary map of typed `questions`. Jev ingests the state once and evaluates every question in parallel. Adding questions incurs near-zero latency overhead and costs only minimal extra question tokens.

---

## 2. API Specifications & Endpoints

### 2.1 HTTP Endpoint & Authentication

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <TYPESAFE_API_KEY>
Content-Type: application/json
```

- **Default Base URL**: `https://api.typesafe.ai`
- **Model Alias**: `"jev-latest"` (resolves to current stable version, e.g. `"jev-1.13.0"`)
- **Context Budget**: 
  - **64k tokens**: Total request budget (`state` + all `questions` combined).
  - **32k tokens**: Single evaluation budget (`state` + longest single question).

### 2.2 Request Payload Schema

```json
{
  "state": "<string | object | array>",
  "model": "jev-latest",
  "questions": {
    "<question_id>": {
      "type": "noul | choice | score",
      "instructions": "<string | object | array>",
      "criteria": "<criteria_structure_per_type>"
    }
  }
}
```

- `state`: The data being judged. Can be plain text (e.g., news article, earnings transcript) or structured JSON (e.g., balance sheet, order book, customer ticket).
- `questions`: A dictionary mapping custom string keys (`question_id`) to Question objects. The key is an arbitrary routing identifier chosen by your code and is not used in inference.

### 2.3 Response Payload Schema

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "<question_id>": {
      "type": "noul | choice | score",
      "...": "typed answer fields"
    }
  },
  "usage": {
    "input_tokens": 484,
    "output_tokens": 76
  }
}
```

### 2.4 HTTP Status Codes & Error Handling

| Status Code | Meaning | Handling Strategy |
| :--- | :--- | :--- |
| `200 OK` | Successful evaluation | Process typed answers. |
| `401 Unauthorized` | Invalid/missing API key | Check `TYPESAFE_API_KEY` in environment or header. |
| `422 Unprocessable Entity` | Validation error (e.g. invalid question format, empty score criteria) | Fix request payload structure. |
| `429 Too Many Requests` | Rate limit exceeded | Retry with exponential backoff; respect `Retry-After` header. |
| `529 Overloaded` | Server capacity temporarily strained | Retry with exponential backoff. |

---

## 3. The Three Core Primitives (Questions & Answers)

### 3.1 Noul (Binary / Yes-No Judgment)

Evaluates whether a condition is true or false. Returns a single float `noul` between `0.0` (definitive No) and `1.0` (definitive Yes), with `0.5` indicating maximal uncertainty.

#### Request Schema:
```json
{
  "type": "noul",
  "instructions": "Does `financials.guidance` indicate revenue acceleration next quarter?",
  "criteria": {
    "true": "Explicitly guides higher revenue growth rate",
    "false": "Guides lower, flat, or provides no acceleration confirmation"
  }
}
```
*(Note: `criteria` is optional for Noul, but providing explicit `true`/`false` rubrics sharpens precision).*

#### Response Schema:
```json
{
  "type": "noul",
  "noul": 0.88
}
```
*(Note: Noul does not return a separate `confidence` field because `noul` itself is the direct calibrated probability).*

---

### 3.2 Choice (Categorical Selection)

Selects the single best option from a discrete set of alternatives. Returns the winner (`choice`), full probability distribution (`probabilities` summing to 1.0), and certainty metric (`confidence`).

#### Request Schema:
```json
{
  "type": "choice",
  "instructions": "What is management's tone regarding supply chain constraints?",
  "criteria": {
    "improving": "Delays are easing, lead times shortening, costs declining",
    "stable": "No material change, manageable headwinds",
    "deteriorating": "Bottlenecks worsening, severe component shortages",
    "not_mentioned": "No discussion of supply chain or logistical constraints"
  }
}
```
*(Note: `criteria` values can be descriptive rubrics or `null` if the option name is self-explanatory).*

#### Response Schema:
```json
{
  "type": "choice",
  "choice": "improving",
  "confidence": 0.82,
  "probabilities": {
    "improving": 0.85,
    "stable": 0.10,
    "deteriorating": 0.03,
    "not_mentioned": 0.02
  }
}
```

---

### 3.3 Score (Continuous / Ordinal Rating)

Rates the state along an ordered rubric of at least 2 levels (indexed from `0` to `N-1`). Returns a probability-weighted expected score (`score`), full distribution across levels (`probabilities`), and `confidence`.

#### Request Schema:
```json
{
  "type": "score",
  "instructions": "Rate the competitive moat and pricing power demonstrated in `state.business_overview`.",
  "criteria": [
    "No moat: Commodity product, fierce price competition, zero pricing power",
    "Narrow moat: Moderate brand recognition or mild switching costs",
    "Wide moat: Dominant network effect, high switching costs, persistent pricing power",
    "Exceptional monopoly/duopoly: Unassailable barrier to entry with captive customer base"
  ]
}
```

#### Response Schema:
```json
{
  "type": "score",
  "score": 2.15,
  "confidence": 0.74,
  "legend": {
    "0": "No moat: Commodity product...",
    "1": "Narrow moat: Moderate brand...",
    "2": "Wide moat: Dominant network...",
    "3": "Exceptional monopoly/duopoly..."
  },
  "probabilities": {
    "0": 0.02,
    "1": 0.15,
    "2": 0.50,
    "3": 0.33
  }
}
```
- `score`: The mathematical expected value: $\sum (\text{level\_index} \times \text{probability})$. Can land between integer levels (e.g. `2.15`).

---

## 4. State Engineering & Field Referencing

1. **State Formats**: State can be plain text or a structured JSON dictionary.
2. **Deep Field Referencing**: When state is structured JSON, questions should pinpoint relevant data fields using **dot-and-bracket path notation wrapped in backticks**:
   ```json
   {
     "state": {
       "ticker": "AAPL",
       "metrics": {
         "pe_ratio": 28.5,
         "fcf_yield": 0.038
       },
       "transcripts": [
         {"quarter": "Q3", "quote": "Services revenue grew 14% to an all-time record."}
       ]
     },
     "questions": {
       "services_momentum": {
         "type": "noul",
         "instructions": "In `transcripts[0].quote`, does management report double-digit growth in high-margin revenue?"
       }
     }
   }
   ```
3. **Filter Before Ingesting**: Keep state focused. Remove irrelevant boilerplate (e.g., legal safe-harbor disclaimers, cookie banners) before sending, as excessive noise dilutes model attention.

---

## 5. Confidence Mechanics & Decision Gating

- **Probability vs. Confidence**:
  - `probability`: The likelihood of a specific outcome (e.g., $P(\text{bullish}) = 0.65$).
  - `confidence`: The certainty of the distribution shape, normalized from `0.0` to `1.0`. A peaked distribution has high confidence; a flat/uniform distribution has near-zero confidence.
- **Three-Tier Risk Architecture**:
  ```python
  if confidence < 0.50:
      # Model expresses genuine uncertainty / insufficient data
      escalate_to_human_or_fallback()
  elif confidence < 0.80:
      # Moderate confidence: Require user confirmation or secondary validation
      request_confirmation_or_secondary_check()
  else:
      # High confidence (> 0.80 - 0.90): Safe for automated execution
      execute_automated_action()
  ```

---

## 6. Architectural Patterns

### Pattern 1: Speculative Fan-Out
Never send 10 individual requests for 10 questions. Put all questions (even conditional or speculative ones) into a single API call.
- **Why**: Jev processes all questions against the state in a single forward pass.
- **Advantage**: ~10x-12x faster, ~10x cheaper than sequential calls.
- **Usage**: Ask for sentiment, moat, risks, fraud indicators, and executive tone all at once. Your code inspects only the answers relevant to the trade setup.

### Pattern 2: Composite Scoring
Decompose complex, multifaceted judgments into atomic scores, then compute the final decision in code using explicit weights:
```python
final_decision_score = (
    0.35 * fundamental_score +
    0.25 * moat_score +
    0.25 * management_confidence_score -
    0.40 * forensic_accounting_risk_score
)
```
- **Why**: Keeps business logic transparent, debuggable, and editable in code without prompt rewriting.

### Pattern 3: Confidence-Gated Intent & Pipeline Routing
Classify incoming financial signals into execution tracks based on the winner label and its confidence:
- High confidence Buy signal $\rightarrow$ Route to Automated Execution Queue.
- Medium confidence Buy signal $\rightarrow$ Route to Portfolio Manager Watchlist with highlight.
- Low confidence or Mixed $\rightarrow$ Hold / Ignore.

---

## 7. Jev 1.13 Jaggedness & Critical Gotchas

| # | Pitfall / Failure Mode | Why Jev Struggles | What To Do Instead (In Code) |
| :--- | :--- | :--- | :--- |
| **1** | **Math & Arithmetic** | Jev is a semantic judgment model, not an arithmetic engine. It will fail on numeric precision. | **Compute all numbers in Python!** Calculate P/E, EPS surprises, margins, debt ratios in code, pass them into `state`, and ask Jev to judge the semantic meaning. |
| **2** | **Date & Time Comparison** | Complex temporal calculations ("was event A 90 days before B?") are unreliable. | **Calculate elapsed time in code!** Pass `days_since_last_event: 92` into state. |
| **3** | **Literal Reading** | Jev answers what you literally wrote, not implied intent. | Write exact criteria and boundary definitions for each option. Avoid vague metaphors. |
| **4** | **Multi-Hop Indirection** | Chained deduction across multiple distant paragraphs can lose fidelity. | Direct questions to specific fields via backtick paths: `` `earnings.segment_breakdown` ``. |
| **5** | **Noisy / Bloated State** | Sending an entire 150-page 10-K full of boilerplate reduces accuracy. | Pre-process and extract target sections (MD&A, Risk Factors, Financial Footnotes) before calling Jev. |
| **6** | **Structural Invariants** | Demanding that two independent questions maintain mathematical parity. | Ask the question once in one direction; enforce inverses or complementary logic in code. |
| **7** | **Text Generation** | Jev does not write reports, summarize text, or generate markdown. | Use Jev strictly for structured decisions/probabilities. Use generative models (e.g. Gemini) for prose. |

---

## 8. Python SDK & Zero-Dependency Integration

### 8.1 Official SDK (`typesafe-sdk`)

Installation:
```bash
pip install typesafe-sdk
```

Synchronous Example:
```python
from typesafe_sdk import TypeSafeClient, Noul, Choice, Score

client = TypeSafeClient()  # Automatically reads TYPESAFE_API_KEY from environment

response = client.system_one(
    state={"ticker": "MSFT", "headline": "Azure revenue accelerates to 33% growth"},
    questions={
        "is_beat": Noul(instructions="Does the headline indicate accelerating cloud growth?"),
        "sentiment": Choice(
            instructions="Assess market impact",
            criteria={"bullish": "Strong positive surprise", "bearish": "Negative", "neutral": "In-line"}
        ),
        "impact_score": Score(
            instructions="Rate revenue impact magnitude",
            criteria=["Minor", "Moderate", "Significant", "Transformative"]
        )
    }
)

print(response.nouls["is_beat"].noul)             # float 0.0 - 1.0
print(response.choices["sentiment"].choice)        # "bullish"
print(response.choices["sentiment"].confidence)    # float 0.0 - 1.0
print(response.scores["impact_score"].score)       # float 0.0 - 3.0
```

### 8.2 Zero-Dependency Pure Python Client (Built-in `urllib`)

```python
import json
import urllib.request
import os

class TypeSafeDirectClient:
    def __init__(self, api_key: str = None, base_url: str = "https://api.typesafe.ai/v1"):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY")
        if not self.api_key:
            raise ValueError("TYPESAFE_API_KEY must be provided or set in environment.")
        self.endpoint = f"{base_url.rstrip('/')}/systemone"

    def evaluate(self, state, questions: dict, model: str = "jev-latest") -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"state": state, "model": model, "questions": questions}
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
```

---

## 9. Domain-Specific Stock Analysis & Decision Recipes

### Recipe 1: Earnings Call Sentiment & Management Evasion Analysis
```python
questions = {
    "management_confidence": {
        "type": "score",
        "instructions": "Evaluate management's conviction in `transcript.qa_section` when answering analyst concerns.",
        "criteria": [
            "Evasive: Giving non-answers, redirecting questions, defensive tone",
            "Cautious: Acknowledging severe headwinds, uncertain timelines",
            "Pragmatic: Measured confidence backed by clear operating data",
            "High Conviction: Unambiguous forward optimism with concrete catalysts"
        ]
    },
    "guidance_revision_direction": {
        "type": "choice",
        "instructions": "What is the net trajectory of full-year guidance in `report.outlook`?",
        "criteria": {
            "raised": "Explicitly increased revenue or margin forecast",
            "maintained": "Reaffirmed existing full-year targets",
            "lowered": "Cut revenue, EBITDA, or margin targets",
            "withdrawn": "Withdrew forward guidance due to volatility"
        }
    },
    "accounting_red_flag": {
        "type": "noul",
        "instructions": "Does `report.financial_notes` contain any aggressive revenue recognition, sudden DSO surges, or unusual restructuring charges?",
        "criteria": {
            "true": "Clear anomalies in working capital or recurring non-recurring charges",
            "false": "Standard, clean accounting footnotes without material flags"
        }
    }
}
```

### Recipe 2: Warren Buffett / Value Investing Moat Audit
```python
moat_questions = {
    "pricing_power": {
        "type": "score",
        "instructions": "Evaluate the company's ability to raise prices without losing customer volume.",
        "criteria": [
            "Zero pricing power (pure price-taker)",
            "Weak pricing power (loses share if prices rise)",
            "Moderate pricing power (passes inflation with lag)",
            "Strong pricing power (routinely raises prices with expanding margins)"
        ]
    },
    "switching_costs": {
        "type": "choice",
        "instructions": "What level of friction exists if a customer attempts to switch to a competitor?",
        "criteria": {
            "frictionless": "Customer can switch instantly with zero loss or setup cost",
            "moderate": "Requires modest re-training or migration effort",
            "mission_critical": "Deeply embedded in enterprise workflow; replacement is prohibitive"
        }
    },
    "network_effects": {
        "type": "noul",
        "instructions": "Does each additional user or customer inherently increase the platform's value to all other participants?"
    }
}
```

### Recipe 3: Automated Confidence-Gated Decision Engine
```python
def make_stock_decision(result: dict) -> dict:
    answers = result["answers"]
    
    guidance = answers["guidance_revision_direction"]
    confidence = guidance["confidence"]
    evasion = answers["management_confidence"]["score"]
    red_flag_prob = answers["accounting_red_flag"]["noul"]
    
    # 1. Forensic veto
    if red_flag_prob > 0.65:
        return {"action": "AVOID_OR_SHORT", "reason": "High accounting red-flag probability", "confidence": red_flag_prob}
    
    # 2. Confidence filter
    if confidence < 0.60:
        return {"action": "WATCHLIST_HOLD", "reason": "Model uncertain regarding guidance trajectory", "confidence": confidence}
        
    # 3. Bullish synthesis
    if guidance["choice"] == "raised" and evasion >= 2.0:
        return {"action": "ACCUMULATE_BUY", "reason": "Raised guidance + strong management conviction", "confidence": confidence}
        
    # 4. Bearish synthesis
    if guidance["choice"] == "lowered" or evasion < 1.0:
        return {"action": "TRIM_OR_SELL", "reason": "Lowered guidance or high executive evasion", "confidence": confidence}
        
    return {"action": "HOLD_NEUTRAL", "reason": "Mixed or in-line performance", "confidence": confidence}
```

---

## 10. Summary Checklist for Engineering with TypeSafe AI

- [x] **Store constants centrally**: Keep questions, criteria, and decision thresholds in dedicated configuration files.
- [x] **Batch into one call**: Always group related questions on the same state into a single request.
- [x] **Calculate math in code**: Never ask Jev to compute arithmetic ratios or dates; provide computed values in state.
- [x] **Use backtick paths**: Point questions directly to nested state keys: `` `metrics.pe_ratio` ``.
- [x] **Gate on confidence**: Check `confidence` before taking automated action; handle low confidence with human-in-the-loop or fallback paths.
- [x] **Read calibrated probabilities**: For nuanced decisions, inspect `probabilities` rather than just the top `choice` or integer score.
