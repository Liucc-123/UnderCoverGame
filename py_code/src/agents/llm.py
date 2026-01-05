"""
File: llm.py
Created Time: 2026-01-05
Author: falcon (liuc47810@gmail.com)
"""
import os, dotenv
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_BASE_URL"] = os.getenv("OPENAI_BASE_URL")
llm = ChatOpenAI(model="gpt-5-mini")

