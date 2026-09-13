"""
Carrega o arquivo Markdown curado do Calendario Academico e divide em chunks semanticos.

Em vez de usar o PDF bruto (que fragmenta tabelas e listas), usamos um arquivo .md
onde cada informacao foi convertida em uma frase completa e autocontida.
"""
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Caminho do arquivo curado (relativo ao diretorio backend/)
CURATED_MD_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "calendario_2026_curado.md"


def load_and_split(pdf_path: Path = None) -> list:
    """
    Carrega o Markdown curado e retorna uma lista de Documents (chunks).

    O argumento pdf_path e mantido por compatibilidade com o vectorstore,
    mas o loader sempre usa o arquivo curado.

    Returns:
        Lista de LangChain Documents com texto e metadados.
    """
    if not CURATED_MD_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo curado nao encontrado: {CURATED_MD_PATH}\n"
            "Certifique-se de que o arquivo 'calendario_2026_curado.md' "
            "existe em backend/data/"
        )

    loader = TextLoader(str(CURATED_MD_PATH), encoding="utf-8")
    documents = loader.load()

    # chunk_size maior mantem secoes inteiras juntas (ex: lista de matriculas dos 4 periodos)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    print(f"[Loader] Arquivo curado carregado: {len(chunks)} chunks gerados")
    return chunks