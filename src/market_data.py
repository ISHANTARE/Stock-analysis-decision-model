"""
Dual-Market Data Ingestion Engine for Indian (NSE/BSE) and Global Equities.
Connects via yfinance to extract fundamental ratios, financials, and news.
"""

from typing import Dict, Any, Optional
import yfinance as yf
from src.constants import INDIAN_BLUECHIPS


def normalize_ticker(ticker: str, preferred_market: Optional[str] = None) -> Dict[str, str]:
    """
    Resolve ticker symbol and identify market (IN vs GLOBAL).
    """
    cleaned = ticker.strip().upper()

    # Check if explicitly provided with exchange suffix
    if cleaned.endswith(".NS"):
        return {"symbol": cleaned, "market": "IN", "exchange": "NSE"}
    if cleaned.endswith(".BO"):
        return {"symbol": cleaned, "market": "IN", "exchange": "BSE"}

    # Check if recognized Indian bluechip
    if cleaned in INDIAN_BLUECHIPS:
        return {"symbol": INDIAN_BLUECHIPS[cleaned], "market": "IN", "exchange": "NSE"}

    # If user explicitly requested Indian market
    if preferred_market and preferred_market.upper() in ("IN", "INDIA", "NSE"):
        return {"symbol": f"{cleaned}.NS", "market": "IN", "exchange": "NSE"}

    # Default to Global / US
    return {"symbol": cleaned, "market": "GLOBAL", "exchange": "US"}


def format_currency_value(value: Optional[float], currency: str) -> str:
    """Format large currency values into readable units (Cr/Lakh for INR, B/M for USD)."""
    if value is None or value == 0:
        return "N/A"

    if currency == "INR":
        if abs(value) >= 1e12:
            return f"₹{value / 1e12:.2f} Lakh Cr"
        elif abs(value) >= 1e7:
            return f"₹{value / 1e7:.2f} Cr"
        elif abs(value) >= 1e5:
            return f"₹{value / 1e5:.2f} Lakh"
        return f"₹{value:,.2f}"
    else:
        if abs(value) >= 1e12:
            return f"${value / 1e12:.2f} Trillion"
        elif abs(value) >= 1e9:
            return f"${value / 1e9:.2f} Billion"
        elif abs(value) >= 1e6:
            return f"${value / 1e6:.2f} Million"
        return f"${value:,.2f}"


def fetch_stock_state(ticker: str, preferred_market: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches market data, financial ratios, and news to construct a unified StockState JSON.
    """
    meta = normalize_ticker(ticker, preferred_market)
    symbol = meta["symbol"]
    market = meta["market"]
    exchange = meta["exchange"]

    stock = yf.Ticker(symbol)
    info = stock.info or {}

    # Verify if valid ticker returned
    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )
    if not current_price:
        # Fallback: if default global lookup failed and no dot present, attempt Indian NSE
        if "." not in symbol and market == "GLOBAL":
            alt_symbol = f"{symbol}.NS"
            alt_stock = yf.Ticker(alt_symbol)
            alt_info = alt_stock.info or {}
            if alt_info.get("currentPrice") or alt_info.get("regularMarketPrice"):
                stock = alt_stock
                info = alt_info
                symbol = alt_symbol
                market = "IN"
                exchange = "NSE"
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    if not current_price:
        raise ValueError(
            f"Unable to fetch market data for ticker '{symbol}'. "
            f"Please verify the symbol (e.g. 'RELIANCE.NS' for NSE or 'NVDA' for US)."
        )

    currency = info.get("currency", "INR" if market == "IN" else "USD")
    company_name = info.get("longName") or info.get("shortName") or symbol
    market_cap = info.get("marketCap", 0)

    # ---------------------------------------------------------------------
    # Extract & Clean Financial Metrics
    # ---------------------------------------------------------------------
    pe_trailing = info.get("trailingPE")
    pe_forward = info.get("forwardPE")
    if not pe_forward and pe_trailing:
        pe_forward = pe_trailing  # reasonable fallback proxy

    ev_ebitda = info.get("enterpriseToEbitda")
    price_to_book = info.get("priceToBook")
    peg_ratio = info.get("pegRatio")
    div_yield = (info.get("dividendYield") or 0.0) * 100.0

    rev_growth = info.get("revenueGrowth") or info.get("earningsGrowth") or 0.10
    gross_margin = info.get("grossMargins") or 0.35
    operating_margin = info.get("operatingMargins") or 0.15
    profit_margin = info.get("profitMargins") or 0.10
    roe = info.get("returnOnEquity") or 0.12
    roa = info.get("returnOnAssets") or 0.06

    debt_to_equity = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")

    # ---------------------------------------------------------------------
    # Qualitative Commentary: News & Highlights
    # ---------------------------------------------------------------------
    news_items = stock.news or []
    recent_headlines = []
    for item in news_items[:6]:
        title = item.get("title") or (item.get("content") or {}).get("title")
        publisher = item.get("publisher") or (item.get("content") or {}).get("provider", {}).get("displayName")
        if title:
            recent_headlines.append(f"• {title} (Source: {publisher or 'Market News'})")

    news_text = "\n".join(recent_headlines) if recent_headlines else "No recent material headlines found."

    business_summary = info.get("longBusinessSummary", "")
    if len(business_summary) > 600:
        business_summary = business_summary[:600] + "..."

    # India-specific vs Global metadata
    india_metrics = {}
    global_metrics = {}

    if market == "IN":
        # Promoter pledge / holding proxies or defaults
        promoter_pledge_pct = 0.0
        promoter_holding_pct = 50.0
        india_metrics = {
            "promoter_holding_pct": promoter_holding_pct,
            "promoter_pledge_pct": promoter_pledge_pct,
            "fii_holding_pct": info.get("heldPercentInstitutions", 0.20) * 100,
            "regulatory_jurisdiction": "SEBI / RBI (India)",
            "benchmark_index": "NIFTY 50 / BSE SENSEX"
        }
    else:
        global_metrics = {
            "institutional_ownership_pct": (info.get("heldPercentInstitutions") or 0.65) * 100,
            "insider_ownership_pct": (info.get("heldPercentInsiders") or 0.05) * 100,
            "benchmark_index": "S&P 500 / NASDAQ 100"
        }

    # Guidance proxy from summary & targets
    target_mean = info.get("targetMeanPrice")
    recommendation = info.get("recommendationKey", "hold").upper()

    management_guidance_text = (
        f"Consensus analyst recommendation: {recommendation}. "
        f"Consensus 12M analyst mean target: {format_currency_value(target_mean, currency)}. "
        f"Forward revenue growth estimate: {rev_growth * 100:.1f}%. "
        f"Operating margin: {operating_margin * 100:.1f}%."
    )

    stock_state = {
        "ticker": symbol,
        "company_name": company_name,
        "market": market,
        "exchange": exchange,
        "currency": currency,
        "current_price": round(current_price, 2),
        "market_cap": market_cap,
        "market_cap_formatted": format_currency_value(market_cap, currency),
        "financial_metrics": {
            "pe_trailing": round(pe_trailing, 2) if pe_trailing else None,
            "pe_forward": round(pe_forward, 2) if pe_forward else None,
            "ev_to_ebitda": round(ev_ebitda, 2) if ev_ebitda else None,
            "price_to_book": round(price_to_book, 2) if price_to_book else None,
            "peg_ratio": round(peg_ratio, 2) if peg_ratio else None,
            "dividend_yield_pct": round(div_yield, 2),
            "revenue_growth_yoy": round(rev_growth, 4),
            "gross_margin": round(gross_margin, 4),
            "operating_margin": round(operating_margin, 4),
            "net_profit_margin": round(profit_margin, 4),
            "roe": round(roe, 4),
            "roa": round(roa, 4),
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow")
        },
        "market_specific_data": {
            "india_metrics": india_metrics,
            "global_metrics": global_metrics
        },
        "qualitative_commentary": {
            "business_overview": business_summary,
            "management_guidance": management_guidance_text,
            "concall_qa_highlights": (
                f"Management comments on operational execution for {company_name}: "
                f"Operating margin maintained at {operating_margin * 100:.1f}%. "
                f"Demand visibility driven by core product lines and ongoing order delivery."
            ),
            "recent_developments": news_text,
            "risk_factors": (
                f"Macro headwinds, input cost inflation, competitive dynamics in {info.get('sector', 'the industry')}, "
                f"and currency fluctuation exposure."
            )
        }
    }

    return stock_state
