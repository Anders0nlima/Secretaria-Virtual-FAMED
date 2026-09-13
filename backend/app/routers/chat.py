"""
Router de chat: expõe o endpoint POST /chat.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.rag.chain import build_chain, get_sources

router = APIRouter(prefix="/chat", tags=["chat"])

# Chain inicializada uma única vez ao importar o módulo
_chain = None


def get_chain():
    global _chain
    if _chain is None:
        _chain = build_chain()
    return _chain


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Pergunta do usuário")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Resposta gerada pela IA")
    sources: list[str] = Field(default=[], description="Fontes consultadas")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Recebe uma pergunta e retorna a resposta baseada no Calendário Acadêmico 2026.
    """
    try:
        chain = get_chain()
        answer = chain.invoke(request.message)
        sources = get_sources(request.message)
        return ChatResponse(answer=answer, sources=sources)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar a pergunta: {exc}",
        ) from exc
