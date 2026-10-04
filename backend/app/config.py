from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Diretório raiz do backend (um nível acima de app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Ollama
    ollama_model: str = "gemma3:1b"
    ollama_base_url: str = "http://localhost:11434"

    # Embeddings
    embeddings_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # Caminhos (relativos ao BASE_DIR)
    pdf_path: str = "data/Calendario_Academico_da_UFPA_2026.pdf"
    chroma_path: str = "chroma_db"
    chroma_collection: str = "calendario_2026"

    # Retriever
    retriever_k: int = 4

    # Google Calendar
    google_calendar_id: str = "primary"
    google_credentials_path: str = "credentials/secretaria-virtual-famed-60fadc63eb4f.json"
    google_calendar_days_ahead: int = 14

    @property
    def absolute_pdf_path(self) -> Path:
        return BASE_DIR / self.pdf_path

    @property
    def absolute_chroma_path(self) -> Path:
        return BASE_DIR / self.chroma_path


settings = Settings()
