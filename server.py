"""
FastAPI Server for Quantamental Stock Analysis & Decision Dashboard.
Provides real-time market data, interactive charting, live news, and Jev semantic evaluation.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.market_data import (
    fetch_stock_state,
    fetch_chart_data,
    fetch_market_indices,
    normalize_ticker,
    INDIAN_BLUECHIPS
)
from src.financial_engine import compute_health_metrics, compute_valuation_scenarios
from src.jev_evaluator import JevEvaluator
from src.decision_engine import synthesize_decision


app = FastAPI(
    title="Quantamental Stock Analysis & Decision Dashboard",
    description="Real-time Indian (NSE/BSE) and Global stock market analysis powered by TypeSafe AI (Jev)",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Popular search directory for quick autocomplete
POPULAR_STOCKS = [
    # Indian Bluechips
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "market": "IN", "exchange": "NSE", "keywords": "oil retail jio telecom"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "market": "IN", "exchange": "NSE", "keywords": "it tech software tata"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "market": "IN", "exchange": "NSE", "keywords": "banking finance private bank"},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "market": "IN", "exchange": "NSE", "keywords": "it tech cloud consulting"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "market": "IN", "exchange": "NSE", "keywords": "banking private finance"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "market": "IN", "exchange": "NSE", "keywords": "auto cars ev commercial vehicles jlr"},
    {"symbol": "ZOMATO.NS", "name": "Zomato Ltd (Eternal)", "market": "IN", "exchange": "NSE", "keywords": "food delivery blinkit quick commerce"},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "market": "IN", "exchange": "NSE", "keywords": "fmcg tobacco hotels paper packaging"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "market": "IN", "exchange": "NSE", "keywords": "telecom 5g airtel africa"},
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics Ltd", "market": "IN", "exchange": "NSE", "keywords": "defense aerospace fighter jets pli"},
    {"symbol": "BEL.NS", "name": "Bharat Electronics Ltd", "market": "IN", "exchange": "NSE", "keywords": "defense radar electronics navratna"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises Ltd", "market": "IN", "exchange": "NSE", "keywords": "infrastructure energy airports mining"},
    # Global Tech Giants
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "market": "GLOBAL", "exchange": "NASDAQ", "keywords": "ai gpu semiconductors data center chips"},
    {"symbol": "AAPL", "name": "Apple Inc.", "market": "GLOBAL", "exchange": "NASDAQ", "keywords": "iphone mac services consumer tech"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "GLOBAL", "exchange": "NASDAQ", "keywords": "cloud azure ai windows office software"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "market": "GLOBAL", "exchange": "NASDAQ", "keywords": "electric vehicles ev energy autonomous fsd"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "market": "GLOBAL", "exchange": "NASDAQ", "keywords": "search youtube google cloud ai gemini"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "market": "GLOBAL", "exchange": "NASDAQ", "keywords": "ecommerce aws cloud retail logistics"},
    {"symbol": "ASML", "name": "ASML Holding N.V.", "market": "GLOBAL", "exchange": "NASDAQ", "keywords": "semiconductor lithography euv monopoly"},
]


# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------

@app.get("/api/indices")
async def get_indices() -> List[Dict[str, Any]]:
    """Live ticker tape index quotes (NIFTY 50, SENSEX, S&P 500, NASDAQ, etc.)."""
    try:
        return fetch_market_indices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_stocks(q: str = Query(..., min_length=1)) -> List[Dict[str, Any]]:
    """Autocomplete search for Indian and Global stocks."""
    query = q.strip().upper()
    matches = []

    # Match in popular list
    for item in POPULAR_STOCKS:
        if (
            query in item["symbol"].upper()
            or query in item["name"].upper()
            or query.lower() in item["keywords"].lower()
        ):
            matches.append(item)

    # If no match and looks like a valid symbol, provide as direct custom option
    if not matches and len(query) >= 2:
        meta = normalize_ticker(query)
        matches.append({
            "symbol": meta["symbol"],
            "name": f"Search '{meta['symbol']}'",
            "market": meta["market"],
            "exchange": meta["exchange"],
            "keywords": "custom ticker"
        })

    return matches[:10]


@app.get("/api/stock")
async def get_stock_data(ticker: str = Query(..., description="Stock symbol (e.g. 'RELIANCE', 'NVDA')")):
    """Fetch live quote, ratios, and news."""
    try:
        state = fetch_stock_state(ticker)
        health = compute_health_metrics(state["financial_metrics"])
        scenarios = compute_valuation_scenarios(state)
        return {
            "stock_state": state,
            "health_metrics": health,
            "valuation_scenarios": scenarios
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/chart")
async def get_chart_data(
    ticker: str = Query(...),
    period: str = Query("1mo", pattern="^(1d|5d|1mo|6mo|1y)$")
):
    """Fetch historical candles for interactive charting."""
    try:
        return fetch_chart_data(ticker=ticker, period=period)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/analyze")
async def run_full_analysis(
    ticker: str = Query(..., description="Ticker symbol to analyze"),
    model: str = Query("jev-latest", description="TypeSafe model alias")
):
    """
    Executes end-to-end Quantamental evaluation:
    1. Data Ingestion & Live Quote
    2. Health Ratios & Scenarios
    3. Jev Parallel Speculative Fan-out Evaluation
    4. Decision Synthesis & Action Recommendation
    """
    try:
        # Step 1: Ingest Live Data
        state = fetch_stock_state(ticker)
        health = compute_health_metrics(state["financial_metrics"])
        scenarios = compute_valuation_scenarios(state)

        # Step 2: Jev Parallel Evaluation
        evaluator = JevEvaluator(model=model)
        jev_eval = evaluator.evaluate_stock(state)

        # Step 3: Decision Synthesis
        decision = synthesize_decision(
            stock_state=state,
            health_metrics=health,
            valuation_scenarios=scenarios,
            jev_eval=jev_eval
        )

        return {
            "success": True,
            "stock_state": state,
            "health_metrics": health,
            "valuation_scenarios": scenarios,
            "jev_evaluation": jev_eval,
            "decision": decision
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------------------
# Static Files & Dashboard UI Mounting
# -------------------------------------------------------------------------
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_dashboard():
    """Serves the main single-page web dashboard."""
    index_file = static_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard index.html not yet built.")
    return FileResponse(index_file)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\nStarting Quantamental Stock Dashboard on http://127.0.0.1:{port} ...")
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=False)
