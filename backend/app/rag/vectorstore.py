"""
Gerencia o banco vetorial ChromaDB:
- Indexação: processa o PDF e persiste os vetores em disco.
- Busca: carrega o banco existente e retorna um retriever.
"""
from functools import lru_cache
from langchain_chroma import Chroma
from app.config import settings
from app.rag.embeddings import get_embeddings
from app.rag.loader import load_and_split


def index_documents() -> Chroma:
    """
    Cria (ou recria) o banco vetorial a partir do PDF.
    Deve ser chamado manualmente via script quando o documento for atualizado.
    """
    embeddings = get_embeddings()
    chunks = load_and_split(settings.absolute_pdf_path)

    print(f"[VectorStore] Indexando {len(chunks)} chunks em {settings.absolute_chroma_path} ...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=settings.chroma_collection,
        persist_directory=str(settings.absolute_chroma_path),
    )
    print("[VectorStore] Indexação concluída.")
    return vectorstore


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    """
    Carrega o banco vetorial existente do disco (singleton via cache).
    Levanta RuntimeError se o banco ainda não foi indexado.
    """
    chroma_path = settings.absolute_chroma_path
    if not chroma_path.exists():
        raise RuntimeError(
            "Banco vetorial não encontrado. "
            "Execute 'python -m app.rag.vectorstore' para indexar o PDF."
        )

    print(f"[VectorStore] Carregando banco de: {chroma_path}")
    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=get_embeddings(),
        persist_directory=str(chroma_path),
    )


def get_retriever():
    """Retorna um retriever configurado com k chunks."""
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_k},
    )


# Permite executar a indexação diretamente:
# python -m app.rag.vectorstore
if __name__ == "__main__":
    index_documents()
    print("Pronto! Banco vetorial criado com sucesso.")
