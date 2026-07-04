from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "voice_agent_kb"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class RAGRetriever:
    def __init__(self):
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # We load the embedding model once
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        Retrieves the top_k most relevant snippets from the knowledge base for a given query.
        Returns a formatted string of the snippets.
        """
        query_vector = self.model.encode(query).tolist()
        
        search_result = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )
        
        if not search_result:
            return "No relevant information found in the knowledge base."
            
        context_snippets = []
        for scored_point in search_result:
            payload = scored_point.payload
            if payload and "text" in payload:
                source = payload.get("source", "Unknown Source")
                text = payload.get("text", "")
                context_snippets.append(f"[{source}]: {text}")
                
        return "\n\n".join(context_snippets)

# Global singleton to be used in FastAPI endpoints
rag_retriever = RAGRetriever()
