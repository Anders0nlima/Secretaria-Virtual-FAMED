"""
Carrega o PDF do Calendário Acadêmico e divide em chunks de texto.
"""
from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_split(pdf_path: Path) -> list:
    """
    Carrega o PDF e retorna uma lista de Documents (chunks).

    Args:
        pdf_path: Caminho absoluto para o arquivo PDF.

    Returns:
        Lista de LangChain Documents com texto e metadados.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    loader = PyMuPDFLoader(str(pdf_path))
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    print(f"[Loader] {len(documents)} páginas → {len(chunks)} chunks")
    return chunks
