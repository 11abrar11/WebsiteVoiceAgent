import asyncio
from app.rag.retriever import rag_retriever

async def test_retrieval():
    query = "What are your services?"
    print(f"Querying: {query}")
    context = rag_retriever.retrieve(query, top_k=5)
    print("--- RETRIEVED CONTEXT ---")
    print(context)
    print("-------------------------")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
