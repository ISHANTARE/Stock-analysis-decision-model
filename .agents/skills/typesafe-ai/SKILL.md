---
name: typesafe-ai
license: MIT
description: >
  Build AI-powered software with TypeSafe: small units of AI intelligence you
  can use like programming primitives. Its System One models, including Jev,
  turn natural language and application state into typed judgments and
  probabilities that code can combine. Use when a feature needs programmable
  common sense, when brainstorming what AI could make possible in an app, or
  when an LLM prompt-and-parse step could become a structured decision.
  Applications include routing, ranking, extraction, verification, financial
  decision modeling, and interactive experiences.
---

# Build with TypeSafe

TypeSafe makes units of AI intelligence usable like programming primitives: small
judgments you can compose into larger capabilities. Its **System One models** return
fast, focused judgments that software can consume directly. **Jev** (`jev-latest`, `jev-1.13.0`)
is TypeSafe's flagship System One model. It understands natural language and returns
typed answers and calibrated probabilities rather than generating text or reasoning explanations.
Code owns the workflow; the model supplies programmable common sense where ordinary code
needs semantic understanding.

## Core Reference Document

A complete, local reference is maintained at:
`docs/TYPESAFE_AI_REFERENCE.md`

## The Three Primitives

| Type | Answer Fields | Usage |
| :--- | :--- | :--- |
| **Noul** | `noul` (0.0 to 1.0) | Yes/No conditions. Probability that statement is true. |
| **Choice** | `choice`, `probabilities`, `confidence` | Discrete classification. Selects top option and returns full distribution. |
| **Score** | `score`, `legend`, `probabilities`, `confidence` | Ordinal/continuous rating across ordered rubric (minimum 2 levels). |

## Key Architectural Rules

1. **Batch Questions (Speculative Fan-out)**:
   Always send multiple questions against the same state in a single request.
   Jev evaluates them in parallel with virtually zero extra latency overhead.
2. **Never Ask Jev to do Math**:
   Jev is a semantic decision model, not an arithmetic engine. Compute ratios, percentages,
   and date comparisons in code; pass the computed values in `state`.
3. **Reference Fields with Backticks**:
   In instructions, use dot-notation wrapped in backticks to point to specific keys in the state:
   e.g. `Does \`financials.revenue\` represent accelerated growth?`
4. **Gate Decisions on Confidence**:
   Use `confidence` as a risk control axis:
   - High (> 0.80): Automatic execution
   - Medium (0.50 - 0.80): Request user confirmation or flag for review
   - Low (< 0.50): Escalate to human or safe fallback
5. **Endpoint & Auth**:
   `POST https://api.typesafe.ai/v1/systemone`
   Header: `Authorization: Bearer <TYPESAFE_API_KEY>`
