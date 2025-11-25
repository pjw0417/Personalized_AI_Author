# rag_store.py
from pathlib import Path
from typing import Dict, Optional

from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from llm_config import embeddings, VECTOR_DB_DIR

def build_vectorstore_from_texts(book_texts: Dict[str, str]) -> None:
    """
    book_texts: dict {title: full_text}
    Splits into chunks, embeds, and persists a Chroma DB.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    docs = []
    for title, text in book_texts.items():
        chunks = splitter.split_text(text)
        for chunk in chunks:
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={"title": title}
                )
            )

    db = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR,
    )
    db.persist()
    print(f"✅ Built vector DB at: {VECTOR_DB_DIR}")

def get_vectorstore() -> Optional[Chroma]:
    """
    Loads the existing Chroma DB if present.
    Returns None if it doesn't exist yet.
    """
    path = Path(VECTOR_DB_DIR)
    if not path.exists():
        print(f"⚠️  Vector DB dir '{VECTOR_DB_DIR}' not found. Run build_rag_db.py first.")
        return None

    db = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings,
    )
    return db
