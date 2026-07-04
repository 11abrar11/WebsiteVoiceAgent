import os
import glob
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownTextSplitter

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "voice_agent_kb"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
KNOWLEDGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../knowledge_base"))

def main():
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    vector_size = model.get_sentence_embedding_dimension()
    
    # Check if collection exists
    collections = [col.name for col in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        print(f"Collection '{COLLECTION_NAME}' already exists. Recreating it to ensure clean state...")
        client.delete_collection(collection_name=COLLECTION_NAME)
        
    print(f"Creating collection '{COLLECTION_NAME}' with vector size {vector_size}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    
    # Setup Text Splitter for Markdown
    # We want reasonable chunks so the LLM gets good context.
    # Increasing chunk size to 1500 to keep lists (like services) together in one chunk.
    splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=150)
    
    md_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.md"))
    if not md_files:
        print(f"Warning: No markdown files found in {KNOWLEDGE_BASE_DIR}")
        return

    total_chunks = 0
    for file_path in md_files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        chunks = splitter.split_text(content)
        
        if not chunks:
            continue
            
        # Create vectors
        embeddings = model.encode(chunks, show_progress_bar=False)
        
        points = []
        for i, chunk in enumerate(chunks):
            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=embeddings[i].tolist(),
                    payload={
                        "source": file_name,
                        "text": chunk
                    }
                )
            )
            
        # Upload to Qdrant
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        total_chunks += len(chunks)
        print(f" -> Inserted {len(chunks)} chunks from {file_name}")

    print(f"\nIngestion Complete! Total chunks inserted: {total_chunks}")

if __name__ == "__main__":
    main()
