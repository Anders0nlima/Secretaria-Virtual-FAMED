"""
Carrega o arquivo Markdown curado do Calendario Academico e divide em chunks
respeitando a estrutura de cabecalhos (##, ###) do documento.

Usa MarkdownHeaderTextSplitter para garantir que cada secao (###) vire seu
proprio chunk, evitando que secoes com temas diferentes sejam mescladas.
"""
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CURATED_MD_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "calendario_2026_curado.md"

# Sub-splitter para secoes muito longas (ex: lista de feriados municipais)
SUB_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=50,
    separators=["\n", ". ", " "],
)

# Cabecalhos que definem os limites de cada chunk
HEADERS_TO_SPLIT = [
    ("##", "secao"),
    ("###", "subsecao"),
]


def load_and_split(pdf_path: Path = None) -> list:
    """
    Carrega o Markdown curado e retorna uma lista de Documents (chunks),
    cada um correspondendo a uma secao ### do documento.

    Secoes maiores que 800 chars sao sub-divididas para manter
    a qualidade dos embeddings.
    """
    if not CURATED_MD_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo curado nao encontrado: {CURATED_MD_PATH}\n"
            "Certifique-se de que o arquivo 'calendario_2026_curado.md' "
            "existe em backend/data/"
        )

    with open(CURATED_MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Passo 1: Dividir pelo Markdown headers (## e ###)
    # Cada secao ### vira seu proprio documento
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT,
        strip_headers=False,
    )
    md_docs = md_splitter.split_text(content)

    # Passo 2: Sub-dividir secoes muito longas (ex: 23 feriados municipais)
    final_chunks = []
    for doc in md_docs:
        if len(doc.page_content) > 800:
            sub_chunks = SUB_SPLITTER.split_documents([doc])
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(doc)

    print(f"[Loader] Arquivo curado carregado: {len(final_chunks)} chunks gerados")
    return final_chunks