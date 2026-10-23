"""
Router de feedback: expõe o endpoint POST /feedback para registro de avaliação de respostas.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback", tags=["feedback"])

# Caminho para armazenamento persistente dos feedbacks em formato JSONL
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FEEDBACK_FILE = DATA_DIR / "feedback.jsonl"


class FeedbackRequest(BaseModel):
    helpful: bool = Field(..., description="True se a resposta ajudou (Sim), False se não ajudou (Não)")
    question: str | None = Field(default=None, description="Pergunta realizada pelo usuário")
    answer: str | None = Field(default=None, description="Resposta gerada pelo assistente")
    comment: str | None = Field(default=None, max_length=500, description="Comentário opcional")


@router.post("")
async def submit_feedback(request: FeedbackRequest):
    """
    Registra a avaliação de utilidade da resposta para melhoria contínua e avaliação da IA.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "helpful": request.helpful,
            "rating": "sim" if request.helpful else "nao",
            "question": request.question,
            "answer": request.answer,
            "comment": request.comment,
        }
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return {"status": "success", "message": "Feedback registrado com sucesso"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar feedback: {exc}") from exc

