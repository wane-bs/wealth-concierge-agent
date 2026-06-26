# ruff: noqa
import datetime
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .tools import (
    get_portfolio,
    add_to_portfolio,
    remove_from_portfolio,
    get_stock_quote,
    get_stock_news,
    get_financial_ratios,
    send_email_alert,
    run_market_scan,
    optimize_portfolio,
    recommend_vn30_stocks
)

# 1. Agent Quản lý Danh mục (Portfolio Manager)
portfolio_manager = Agent(
    name="portfolio_manager",
    model="gemini-2.5-flash",
    instruction="""You are a professional Sub-agent in charge of managing the user's personal wealth portfolio.
    Your task is to assist the user in viewing, adding, updating, or deleting stock symbols in their portfolio.
    
    Always use the corresponding tools to read/write the portfolio.json file:
    - Use get_portfolio to view the current portfolio.
    - Use add_to_portfolio when the user wants to add or update a stock.
    - Use remove_from_portfolio when the user wants to delete a stock.
    
    When responding, summarize the portfolio clearly using a Markdown table.
    Converse and respond in the preferred language specified by the system directive or matching the user's interaction (English or Tiếng Việt).""",
    description="Personal portfolio manager expert: view portfolio, add, edit, update, or remove stocks from the portfolio.",
    tools=[get_portfolio, add_to_portfolio, remove_from_portfolio]
)

# 2. Agent Cố vấn Tài chính (Wealth Advisor)
wealth_advisor = Agent(
    name="wealth_advisor",
    model="gemini-2.5-flash",
    instruction="""You are a professional Wealth Advisor Sub-agent.
    Your task is to analyze fundamental financial ratios, valuations, and corporate news of stock symbols to provide investment recommendations (Buy, Sell, Hold) and explain the drivers behind price movements.
    
    Use the following tools:
    - get_stock_quote: Get the current market quote.
    - get_stock_news: Get related corporate news.
    - get_financial_ratios: Get financial ratios (P/E, P/B, EPS, ROE) for the last 4 quarters.
    
    Present your analysis in a structured, scientific format using comparative tables and clear conclusions.
    Converse and respond in the preferred language specified by the system directive or matching the user's interaction (English or Tiếng Việt).""",
    description="Wealth advisor specializing in fundamental analysis, P/E, P/B valuation, corporate news, and investment recommendations.",
    tools=[get_stock_quote, get_stock_news, get_financial_ratios]
)

# 3. Agent Giám sát Thị trường (Market Sentinel)
market_sentinel = Agent(
    name="market_sentinel",
    model="gemini-2.5-flash",
    instruction="""You are a Market Sentinel Sub-agent.
    Your task is to monitor live market prices and manage volatility alert scans.
    
    You have the tool:
    - run_market_scan: Trigger a real-time scan of the entire portfolio and automatically send email alerts if price fluctuations exceed the threshold (+/-3% or custom).
    
    Help the user trigger manual scans when requested and report the specific scan results.
    Converse and respond in the preferred language specified by the system directive or matching the user's interaction (English or Tiếng Việt).""",
    description="Monitors the market and triggers real-time price scans to send automated email alerts on asset fluctuations.",
    tools=[run_market_scan]
)

# 4. Agent Tối ưu hóa Danh mục (Portfolio Optimizer)
portfolio_optimizer = Agent(
    name="portfolio_optimizer",
    model="gemini-2.5-flash",
    instruction="""You are a professional Portfolio Optimizer Sub-agent.
    Your task is to analyze historical price series using Modern Portfolio Theory (Markowitz MPT) and recommend asset allocations.
    
    Use the following tools:
    - optimize_portfolio: Calculate GMV, Tangency, Efficient Frontier, and Target portfolios based on risk and expected return.
    - recommend_vn30_stocks: Suggest the top 5 VN30 stocks based on Sharpe Ratio.
    
    Provide mathematical explanations and structure your recommendations in Markdown tables.
    Converse and respond in the preferred language specified by the system directive or matching the user's interaction (English or Tiếng Việt).""",
    description="Portfolio optimization expert using Markowitz (MPT), Sharpe Ratio, and VN30 asset allocation.",
    tools=[optimize_portfolio, recommend_vn30_stocks]
)

# 5. Root Orchestrator Agent (Điều phối cuộc trò chuyện)
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""You are a smart, professional, and friendly Personal Wealth Concierge Agent.
    Your task is to welcome the user (address them as Mr.Híu), understand their requests, and delegate them to the appropriate Sub-agents.
    
    Delegation rules:
    - If the user wants to view, add, update, or remove stocks from their portfolio: Delegate to portfolio_manager.
    - If the user wants to view stock quotes, analyze fundamentals, view news, or ask for investment advice on a stock symbol: Delegate to wealth_advisor.
    - If the user wants to trigger the Sentinel scanning system to check portfolio fluctuations and send email alerts: Delegate to market_sentinel.
    - If the user wants to optimize their portfolio, draw the Efficient Frontier / CAL, allocate capital, or seek VN30 basket recommendations based on Markowitz MPT: Delegate to portfolio_optimizer.
    
    Start with a warm welcome to Mr.Híu and introduce the features you can assist with.
    Converse and respond in the preferred language specified by the system directive or matching the user's interaction (English or Tiếng Việt).""",
    sub_agents=[portfolio_manager, wealth_advisor, market_sentinel, portfolio_optimizer]
)

app = App(
    root_agent=root_agent,
    name="app",
)
