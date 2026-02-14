'''
This script demonstrates a basic financial analysis agent using LangChain, OpenAI, and Finnhub.
The agent can fetch real-time stock quotes and recent company news for a given list of tickers
and generate a summary report.
'''

import os
import json
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Load environment variables from a .env file for secure key management.
load_dotenv()

# --- CONFIGURATION ---
# API key for OpenRouter, which provides access to various language models.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# API key for Finnhub, used to fetch stock market data.
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Specifies the language model to be used for the agent.
MODEL_NAME = "deepseek/deepseek-chat-v3-0324"

# --- USER QUERY ---
# This more advanced query asks the agent to compare stocks for a specific investment decision,
# requiring it to synthesize data rather than just listing it.
USER_QUERY = "I'm considering investing in the tech sector, but I'm torn between hardware and software. Can you compare Apple (AAPL) and Microsoft (MSFT), giving me a summary of their recent stock performance and any critical news that could help me decide?"


# --- TOOL DEFINITION ---
@tool
def get_stock_market_data(stock_ticker: str) -> Dict[str, Any]:
    """
    Fetches the latest trading data and recent company news for a given stock ticker.

    This function retrieves real-time price quotes (current price, percent change, high, and low)
    and the top 3 news headlines from the last 7 days.

    Args:
        stock_ticker: The stock symbol to look up (e.g., "AAPL", "MSFT").

    Returns:
        A dictionary containing the stock's quote and a list of the latest news articles.
        Returns an error message if the API key is missing or if the request fails.
    """
    print(f"--- TOOL INFO: Fetching all market data for '{stock_ticker}'... ---")
    if not FINNHUB_API_KEY:
        return {"error": "Finnhub API key is not configured."}

    # 1. Fetch Real-Time Price Quote
    quote_data = {}
    try:
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={stock_ticker}&token={FINNHUB_API_KEY}"
        quote_response = requests.get(quote_url)
        quote_response.raise_for_status()  # Raise an exception for bad status codes
        q_data = quote_response.json()
        quote_data = {
            "current_price": f"${q_data.get('c', 0):.2f}",
            "percent_change": f"{q_data.get('dp', 0):.2f}%",
            "high_today": f"${q_data.get('h', 0):.2f}",
            "low_today": f"${q_data.get('l', 0):.2f}",
        }
        print(f"--- TOOL INFO: Fetched quote for {stock_ticker}: {quote_data}")
    except requests.exceptions.RequestException as e:
        print(f"--- TOOL ERROR (Quote): {e} ---")
        quote_data = {"error": f"Failed to fetch price quote: {e}"}

    # 2. Fetch Recent News (Last 7 Days)
    news_data = []
    try:
        # Calculate the date range for the last 7 days to get fresh news.
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)
        date_from = seven_days_ago.strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        
        news_url = f"https://finnhub.io/api/v1/company-news?symbol={stock_ticker}&from={date_from}&to={date_to}&token={FINNHUB_API_KEY}"
        news_response = requests.get(news_url)
        news_response.raise_for_status()
        news_items = news_response.json()
        
        # Extract the top 3 news headlines and their URLs.
        news_data = [{"headline": item["headline"], "url": item["url"]} for item in news_items[:3]]
        
        if not news_data:
            news_data = [{"info": "No news found in the last 7 days."}]
        print(f"--- TOOL INFO: Found {len(news_data)} recent news items for {stock_ticker}.")
        
    except requests.exceptions.RequestException as e:
        print(f"--- TOOL ERROR (News): {e} ---")
        news_data = [{"error": f"Failed to fetch news: {e}"}]

    # 3. Combine into a single structured result
    return {"quote": quote_data, "latest_news": news_data}


def run_langchain_demo():
    """
    Initializes and runs the LangChain agent.

    This function sets up the language model, defines the tools available to the agent,
    creates the prompt template, and executes the agent with the user's query.
    The final analysis from the agent is then printed to the console.
    """
    # Ensure API keys are available before proceeding.
    if not OPENROUTER_API_KEY or not FINNHUB_API_KEY:
        print("CRITICAL ERROR: API keys for OpenRouter and/or Finnhub not found. Ensure they are in your .env file.")
        return

    # Initialize the language model with the specified configuration.
    llm = ChatOpenAI(
        model=MODEL_NAME,
        openai_api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,  # Set to 0 for deterministic, factual outputs.
    )
    
    # Define the list of tools the agent can use.
    tools = [get_stock_market_data]

    # Create the prompt template that guides the agent's behavior.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert financial analyst. Your goal is to provide a comprehensive summary of a stock's current situation. For each company requested, use your tool to fetch its latest price data and recent news. Then, synthesize both the quantitative price action and the qualitative news headlines into a clear, concise report."),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"), # Placeholder for the agent's intermediate steps.
    ])

    # Create the agent by combining the language model, tools, and prompt.
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # The AgentExecutor runs the agent and manages the tool calls.
    # NEW: Added handle_parsing_errors=True to allow the agent to self-correct
    # if the model produces a malformed tool call.
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True
    )

    # --- EXECUTION ---
    print("\n" + "="*50)
    print(f"Executing Agent with query: '{USER_QUERY}'")
    print("="*50 + "\n")
    
    # Invoke the agent with the user's query and get the response.
    response = agent_executor.invoke({"input": USER_QUERY})
    
    # --- FINAL OUTPUT ---
    print("\n" + "="*50)
    print("Final Analysis & Recommendation:")
    print("="*50 + "\n")
    print(response["output"])

if __name__ == "__main__":
    run_langchain_demo()