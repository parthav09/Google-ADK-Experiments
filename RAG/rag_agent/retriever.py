import os
import re
from pathlib import Path

from google.adk.tools import ToolContext

DATA_DIR = Path(__file__).resolve().parent / "data"
LAST_SEARCH_QUERY_KEY = "last_search_query"
SEARCH_HISTORY_KEY = "search_history"

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def tokenize(text):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {word for word in words if len(word) > 2}

def chunk_text(text, chunk_size = 500, overlap = 100):
    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)
        
        start += chunk_size - overlap
    return chunks

def load_documents():
    documents = []


    for file_path in DATA_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):
            documents.append(
                {
                    "source": file_path.name,
                    "chunk_id": index,
                    "text": chunk
                }
            )
    return documents

def search_docs(query: str, tool_context: ToolContext):
    """
    Search local documents for relevant context.

    Args:
        query: The user's search query.
    """

    search_history = list(tool_context.state.get(SEARCH_HISTORY_KEY, []))
    search_history.append(query)
    tool_context.state[LAST_SEARCH_QUERY_KEY] = query
    tool_context.state[SEARCH_HISTORY_KEY] = search_history
    documents = load_documents()

    if not documents:
        return "No documents found"
    
    query_tokens = tokenize(query)
    scored_results = []

    for doc in documents:
        chunk_tokens = tokenize(doc["text"])
        score = len(query_tokens & chunk_tokens)
        if score > 0:
            scored_results.append((score, doc))
        
    scored_results.sort(reverse = True, key = lambda item: item[0])
    top_results = scored_results[:3]

    if not top_results:
        return "No relevant context found in local documents"
    
    context_parts = []

    for score, doc in top_results:
        context_parts.append(f"Source: {doc['source']}, Chunk ID: {doc['chunk_id']}\n{doc['text']}\n")
    
    return "\n".join(context_parts)

def get_last_search(tool_context: ToolContext):
    """Get the previous document search queries."""
    last_query = tool_context.state.get(LAST_SEARCH_QUERY_KEY)
    search_history = tool_context.state.get(SEARCH_HISTORY_KEY, [])

    if not last_query:
        return {
            "status": "empty",
            "message": "No previous search query found"
        }
    
    else:
        return {
            "status": "success",
            "message": f"Last search query: {last_query}",
            "queries": search_history,
        }