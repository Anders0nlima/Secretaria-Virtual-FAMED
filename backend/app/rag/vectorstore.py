"""
Gerencia o banco vetorial ChromaDB e a busca híbrida (Vetorial + BM25 via RRF):
- Indexação: processa os documentos curados e persiste os vetores em disco.
- Busca híbrida: combina similaridade semântica (ChromaDB) com busca léxica exata (BM25)
  usando Reciprocal Rank Fusion (RRF), garantindo alta precisão tanto para siglas exatas
  (TEA, TDAH, SAPE, TCC, 2026.4) quanto para perguntas em linguagem natural.
"""
from collections import Counter
from functools import lru_cache
import math
import re
import unicodedata
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.rag.embeddings import get_embeddings
from app.rag.loader import load_and_split


# ---------------------------------------------------------------------------
# Tokenização e BM25 em Português (leve, sem dependências externas)
# ---------------------------------------------------------------------------

_BM25_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "para", "por", "pelo", "pela", "pelos", "pelas", "com", "sem", "sob", "sobre",
    "e", "ou", "mas", "se", "que", "qual", "quais", "como", "onde", "quando", "quem",
    "ao", "aos", "a", "as", "eu", "voce", "meu", "minha", "meus", "minhas",
    "tenho", "quero", "saber", "fazer", "posso", "pode", "podem", "devo", "deve",
    "esta", "estao", "estou", "sao", "ser", "foi", "ter", "tem", "mais", "muito",
    "tambem", "isso", "isto", "esse", "essa", "este", "esta", "esses", "essas",
    "aqui", "la", "ja", "nao", "sim", "favor", "ola", "oi", "bom", "boa",
}

# Siglas de 2 letras relevantes na FAMED/UFPA que não devem ser descartadas
_SHORT_ACADEMIC_TOKENS = {"sf", "hm", "cr", "ch", "ia"}


def _tokenize_pt(text: str) -> list[str]:
    """Normaliza acentos, preserva códigos como '2026.4' e siglas como 'tea', 'tcc', 'sape'."""
    if not text:
        return []
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8").lower()
    raw_tokens = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", norm)
    tokens = []
    for tok in raw_tokens:
        if tok in _BM25_STOPWORDS:
            continue
        if len(tok) >= 3 or tok in _SHORT_ACADEMIC_TOKENS or tok.isdigit():
            tokens.append(tok)
    return tokens


class _BM25Index:
    """Índice BM25 leve em memória construído diretamente a partir dos chunks do ChromaDB."""

    def __init__(self, docs: list[Document], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1 = k1
        self.b = b
        self.doc_freqs: list[Counter] = []
        self.doc_lens: list[int] = []
        self.df: Counter = Counter()

        for doc in docs:
            toks = _tokenize_pt(doc.page_content)
            counts = Counter(toks)
            self.doc_freqs.append(counts)
            self.doc_lens.append(len(toks))
            for term in counts:
                self.df[term] += 1

        self.n_docs = len(docs)
        self.avgdl = (sum(self.doc_lens) / self.n_docs) if self.n_docs else 1.0

    def search(self, query: str, k: int = 10) -> list[tuple[Document, float]]:
        q_tokens = _tokenize_pt(query)
        if not q_tokens or not self.n_docs:
            return []

        scores: list[tuple[int, float]] = []
        for idx, counts in enumerate(self.doc_freqs):
            dl = self.doc_lens[idx]
            score = 0.0
            for term in q_tokens:
                tf = counts.get(term, 0)
                if tf == 0:
                    continue
                df = self.df.get(term, 0)
                idf = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / self.avgdl))
                score += idf * (tf * (self.k1 + 1.0)) / denom
            if score > 0.0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self.docs[idx], sc) for idx, sc in scores[:k]]


# ---------------------------------------------------------------------------
# Indexação e Acesso ao VectorStore
# ---------------------------------------------------------------------------

def index_documents() -> Chroma:
    """
    Cria (ou recria) o banco vetorial a partir dos documentos curados.
    Deve ser chamado manualmente via script quando os documentos forem atualizados.
    """
    import shutil
    embeddings = get_embeddings()
    chunks = load_and_split(settings.absolute_pdf_path)

    chroma_dir = settings.absolute_chroma_path
    if chroma_dir.exists():
        try:
            shutil.rmtree(str(chroma_dir))
            print(f"[VectorStore] Banco anterior removido em {chroma_dir}")
        except Exception as e:
            print(f"[VectorStore] Aviso ao limpar banco anterior: {e}")
    import chromadb
    client = chromadb.PersistentClient(path=str(settings.absolute_chroma_path))
    try:
        client.delete_collection(settings.chroma_collection)
        print(f"[VectorStore] Coleção '{settings.chroma_collection}' anterior removida.")
    except Exception as e:
        print(f"[VectorStore] Aviso ao remover coleção: {e}")

    print(f"[VectorStore] Indexando {len(chunks)} chunks em {settings.absolute_chroma_path} ...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=settings.chroma_collection,
        persist_directory=str(settings.absolute_chroma_path),
    )
    get_vectorstore.cache_clear()
    get_bm25_index.cache_clear()
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
            "Execute 'python -m app.rag.vectorstore' para indexar os documentos."
        )

    print(f"[VectorStore] Carregando banco de: {chroma_path}")
    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=get_embeddings(),
        persist_directory=str(chroma_path),
    )


@lru_cache(maxsize=1)
def get_bm25_index() -> _BM25Index:
    """Constrói (uma única vez) o índice BM25 sincronizado com os chunks do ChromaDB."""
    vectorstore = get_vectorstore()
    raw = vectorstore.get(include=["documents", "metadatas"])
    documents = raw.get("documents") or []
    metadatas = raw.get("metadatas") or [{} for _ in documents]
    docs = [
        Document(page_content=content, metadata=meta or {})
        for content, meta in zip(documents, metadatas)
        if content
    ]
    print(f"[VectorStore] Índice BM25 construído com {len(docs)} chunks.")
    return _BM25Index(docs)


def get_retriever():
    """Retorna um retriever vetorial padrão configurado com k chunks."""
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_k},
    )


def hybrid_retrieve(query: str, k: int | None = None) -> list[Document]:
    """
    Busca híbrida (ChromaDB Semântico + BM25 Léxico) combinada por
    Reciprocal Rank Fusion (RRF), com filtro de ruído semântico.

    Resolve falhas típicas da busca puramente vetorial:
    - Siglas curtas como TEA, TDAH, SAPE, TCC, TAE, 2026.4 não são soterradas.
    - Chunks irrelevantes (distância alta e sem match lexical) são descartados,
      evitando que o LLM compacto (gemma3:4b) misture assuntos distintos.
    """
    top_k = k or settings.retriever_k
    candidate_k = max(top_k * 2, 10)

    vectorstore = get_vectorstore()
    bm25 = get_bm25_index()

    # 1. Busca semântica com score de distância (menor distância = mais parecido)
    vec_hits = vectorstore.similarity_search_with_score(query, k=candidate_k)
    # 2. Busca lexical exata (BM25)
    bm25_hits = bm25.search(query, k=candidate_k)

    rrf_k = 60
    fused_scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    # Peso vetorial (filtra chunks semanticamente muito distantes quando já temos hits melhores)
    best_vec_dist = vec_hits[0][1] if vec_hits else 2.0
    max_allowed_dist = min(1.35, best_vec_dist + 0.45)

    for rank, (doc, dist) in enumerate(vec_hits, start=1):
        if rank > 2 and dist > max_allowed_dist:
            continue
        key = doc.page_content
        doc_map[key] = doc
        fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (rrf_k + rank))

    # Peso BM25 ligeiramente superior para dar precisão a siglas e termos oficiais
    for rank, (doc, bm25_score) in enumerate(bm25_hits, start=1):
        if bm25_score <= 0.0:
            continue
        key = doc.page_content
        doc_map[key] = doc
        fused_scores[key] = fused_scores.get(key, 0.0) + (1.15 / (rrf_k + rank))

    ranked_keys = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
    return [doc_map[key] for key in ranked_keys[:top_k]]


# Permite executar a indexação diretamente:
# python -m app.rag.vectorstore
if __name__ == "__main__":
    index_documents()
    print("Pronto! Banco vetorial criado com sucesso.")
