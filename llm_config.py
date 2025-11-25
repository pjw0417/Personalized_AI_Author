# llm_config.py
import os
from dotenv import load_dotenv
from typing import Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load .env so this works in local dev
load_dotenv()

# Model names can be overridden via env
MAIN_MODEL = os.getenv("MAIN_MODEL", "gpt-5-nano")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "vector_db")

def get_llm(model: Optional[str] = None, temperature: float = 0.9) -> ChatOpenAI:
    """
    Returns a ChatOpenAI LLM instance.
    """
    return ChatOpenAI(
        model=model or MAIN_MODEL,
        temperature=temperature,
    )

# Single embedding object reused across RAG
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
