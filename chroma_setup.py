import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os


client = chromadb.Client(Settings(persist_directory="./chroma_db"))


collection = client.get_or_create_collection("documents")


def embed_texts(texts):
    ef = embedding_functions.DefaultEmbeddingFunction()
    embeddings = ef(texts)  
    embeddings = [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]
    return embeddings


def add_document(doc_id, text):
    embedding = embed_texts([text])[0]
    collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding]
    )


def query_similar(text, n_results=3):
    embedding = embed_texts([text])[0]
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    return results

