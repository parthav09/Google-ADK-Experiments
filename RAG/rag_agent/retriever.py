from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge.txt"

def load_chunks():
    text = DATA_PATH.read_text(encoding = "utf-8")
    chunks = text.split("\n")
    return chunks

def search_docs(query):
    chunks = load_chunks()
    query_words = set(query.lower().split())
    scored_chunks = []

    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        score = len(query_words.intersection(chunk_words))

        if score > 0:
            scored_chunks.append((chunk, score))
        
        scored_chunks.sort(reverse = True, key = lambda item: item[0])
        top_chunks = [chunk for _, chunk in scored_chunks[:3]]

        if not top_chunks:
            return "No relevant information found in the knowledge base"
        
        return "\n".join(top_chunks)
