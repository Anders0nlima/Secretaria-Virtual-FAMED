"""
Carrega os documentos curados em Markdown (Calendario Academico e Normas/Regulamentos da FAMED)
e divide em chunks semanticos respeitando a estrutura de cabecalhos (##, ###).

Estrategia:
- Cada secao ### vira seu proprio chunk semantico isolado.
- Os chunks sao prefixados com o nome da fonte para maximizar a precisao da busca vetorial.
- O formato Markdown elimina ruidos de extracao (quebras de linha, notas de rodape e tabelas fragmentadas).
"""
from pathlib import Path
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_core.documents import Document

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
CALENDAR_MD = DATA_DIR / "calendario_2026_curado.md"
CURATED_DOCS_DIR = DATA_DIR / "documentos_curados"

# ---------------------------------------------------------------------------
# Splitters
# ---------------------------------------------------------------------------
HEADERS_TO_SPLIT = [("##", "secao"), ("###", "subsecao")]

MD_SUB_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " "],
)


def extract_title_from_md(content: str, default_name: str) -> str:
    """Extrai o primeiro titulo '# ' do Markdown para usar como fonte legivel."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.replace("# ", "").strip()
    return default_name.replace("_", " ").replace("-", " ").title()


def load_curated_markdowns() -> list:
    """
    Carrega todos os arquivos Markdown curados:
    - calendario_2026_curado.md
    - backend/data/documentos_curados/*.md
    """
    all_md_files = []
    if CALENDAR_MD.exists():
        all_md_files.append(CALENDAR_MD)

    if CURATED_DOCS_DIR.exists():
        curated_files = sorted(CURATED_DOCS_DIR.glob("*.md"))
        all_md_files.extend(curated_files)

    if not all_md_files:
        raise FileNotFoundError(
            f"Nenhum arquivo Markdown encontrado em {DATA_DIR} ou {CURATED_DOCS_DIR}"
        )

    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT,
        strip_headers=False,
    )

    all_chunks = []

    for md_file in all_md_files:
        content = md_file.read_text(encoding="utf-8")
        source_title = extract_title_from_md(content, md_file.stem)

        # Trata caso especial de identificacao amigavel do calendario
        if "calendario" in md_file.name.lower():
            source_title = "Calendario Academico 2026 - UFPA"

        docs = md_splitter.split_text(content)

        chunks_for_file = []
        for doc in docs:
            doc.metadata["source"] = source_title
            doc.metadata["arquivo"] = md_file.name
            doc.metadata["tipo"] = "documento_curado"

            header_prefix = f"[Fonte: {source_title}]\n"
            content_with_source = f"{header_prefix}{doc.page_content}"

            if len(content_with_source) > 1200:
                doc.page_content = content_with_source
                sub = MD_SUB_SPLITTER.split_documents([doc])
                for s in sub:
                    s.metadata = dict(doc.metadata)
                    if not s.page_content.startswith("[Fonte:"):
                        s.page_content = f"{header_prefix}{s.page_content}"
                chunks_for_file.extend(sub)
            else:
                doc.page_content = content_with_source
                chunks_for_file.append(doc)

        print(f"  [OK] {md_file.name} -> {len(chunks_for_file)} chunks ({source_title})")
        all_chunks.extend(chunks_for_file)

    return all_chunks


# ---------------------------------------------------------------------------
# Ponto de entrada principal (chamado pelo vectorstore)
# ---------------------------------------------------------------------------

def load_and_split(pdf_path: Path = None) -> list:
    """
    Carrega todos os documentos curados e retorna lista de Documents para indexacao.
    """
    print("[Loader] Carregando documentos curados...")
    chunks = load_curated_markdowns()
    print(f"[Loader] Total: {len(chunks)} chunks gerados com sucesso.")
    return chunks