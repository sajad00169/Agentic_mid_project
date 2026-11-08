"""
Configuration management for the Fee Management Agent.
Loads environment variables and sets defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configurations
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

# LangSmith Tracing
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "student-fee-management-agent")

# Business Logic Defaults
REFERENCE_DATE = os.getenv("REFERENCE_DATE", "2024-11-01")
CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "PKR")
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

os.makedirs(LOGS_DIR, exist_ok=True)
