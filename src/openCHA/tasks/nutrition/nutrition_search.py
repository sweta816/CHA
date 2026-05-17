from typing import List
import os
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq as LlamaGroq
from openCHA.tasks.task import BaseTask
from dotenv import load_dotenv

load_dotenv()

# Set embedding model — free local
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

# Set LLM — Groq instead of OpenAI
Settings.llm = LlamaGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)

# Connect to ChromaDB
chroma = chromadb.PersistentClient(path="./nutrition_db")
chroma_collection = chroma.get_or_create_collection("nutrimate")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(
    vector_store=vector_store
)
index = VectorStoreIndex.from_vector_store(
    vector_store,
    storage_context=storage_context
)
query_engine = index.as_query_engine(similarity_top_k=3)


class NutritionSearch(BaseTask):

    name: str = "nutrition_search"
    chat_name: str = "NutritionSearch"
    description: str = (
        "Searches verified ICMR-NIN 2024 nutrition knowledge base "
        "for Indian college students. ALWAYS use this task for ANY "
        "question about: fatigue, tiredness, iron deficiency, hair fall, "
        "pale skin, diet plans, hostel food, budget meals, vitamins, "
        "minerals, calcium, Vitamin D, Vitamin B12, protein deficiency, "
        "bone pain, concentration issues, immunity, weight management, "
        "or any nutrition or health symptom. "
        "Always call this before answering any nutrition question."
    )
    dependencies: List = []
    inputs: List = [
        "A search query about nutrition, diet, food, "
        "or health symptoms."
    ]
    outputs: List = [
        "Returns verified nutrition information from "
        "ICMR-NIN 2024 dietary guidelines."
    ]
    output_type: bool = False

    def _execute(self, inputs: List) -> str:
        query = inputs[0]
        try:
            response = query_engine.query(query)
            result = str(response).strip()
            if not result or result == "Empty Response":
                return (
                    "No specific information found in knowledge base. "
                    "Please consult a doctor or dietitian."
                )
            return result
        except Exception as e:
            return f"Search error: {str(e)}"