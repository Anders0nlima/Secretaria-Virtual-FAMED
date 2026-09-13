"""
Configura e retorna o modelo de embeddings.
Utiliza sentence-transformers multilingual para suporte ao português.
"""
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Instancia o modelo de embeddings uma única vez (singleton via cache).
    O modelo é baixado automaticamente na primeira execução.
    """
    print(f"[Embeddings] Carregando modelo: {settings.embeddings_model}")
    return HuggingFaceEmbeddings(
        model_name=settings.embeddings_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
