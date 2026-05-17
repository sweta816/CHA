import json
import os
import chromadb
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Free local embedding model
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

# ChromaDB setup
print("Connecting ChromaDB...")
chroma = chromadb.PersistentClient(path="./nutrition_db")

try:
    chroma.delete_collection("nutrimate")
    print("Old collection deleted")
except:
    pass

chroma_collection = chroma.create_collection("nutrimate")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Load all JSON files from data folder
documents = []
for filename in os.listdir("./data"):
    if not filename.endswith(".json"):
        continue
    with open(f"./data/{filename}", "r", encoding="utf-8") as f:
        data = json.load(f)
    for chunk in data["chunks"]:
        doc = Document(
            text=chunk["content"],
            metadata={
                "id": chunk["id"],
                "heading": chunk.get("heading", ""),
                "source": data.get("source", "ICMR-NIN 2024")
            }
        )
        documents.append(doc)
    print(f"Loaded: {filename} — {len(data['chunks'])} chunks")

# Index into ChromaDB
print("Indexing into ChromaDB...")
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context
)

print(f"\nDone! {len(documents)} chunks indexed.")
print("Now run: python main.py")