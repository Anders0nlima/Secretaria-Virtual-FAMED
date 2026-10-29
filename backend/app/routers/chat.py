"""
Router de chat: expõe o endpoint POST /chat.
"""
import re
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

class MessageHistoryItem(BaseModel):
    role: str = Field(..., description="'user' ou 'assistant'")
    content: str = Field(..., description="Conteúdo da mensagem")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Pergunta do usuário")
    history: list[MessageHistoryItem] = Field(default=[], description="Histórico recente da conversa")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Resposta gerada pela IA")
    sources: list[str] = Field(default=[], description="Fontes consultadas")


# ---------------------------------------------------------------------------
# Padrões Rápidos de Cumprimento e Agradecimento
# ---------------------------------------------------------------------------

THANKS_PATTERN = re.compile(
    r"^\s*(obrigad[oa]|valeu|muito obrigad[oa]|agrade[cç]o|tks|thanks)[\s!.,?]*$",
    re.IGNORECASE,
)

GREETING_PATTERN = re.compile(
    r"^\s*(oi+|ol[aá]+|e a[ií]|bom dia|boa tarde|boa noite|tudo bem\??|hello|hi)[\s!.,?]*$",
    re.IGNORECASE,
)

THANKS_ANSWER = (
    "Por nada! Se precisar de mais alguma informação ou tiver outras dúvidas sobre a FAMED/UFPA, estou à disposição."
)

GREETING_ANSWER = (
    "Olá! Sou a Secretaria Virtual da FAMED/UFPA. "
    "Posso ajudar com dúvidas sobre o Calendário Acadêmico, normas, TCC, formulários e agenda. "
    "Qual é a sua dúvida?"
)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Recebe uma pergunta e histórico recente, retornando a resposta baseada
    no Calendário Acadêmico 2026, normas da FAMED/UFPA e Agenda Institucional.
    """
    # Agradecimentos imediatos
    if THANKS_PATTERN.match(request.message):
        return ChatResponse(answer=THANKS_ANSWER, sources=[])

    # Cumprimentos e saudações imediatas
    if GREETING_PATTERN.match(request.message):
        return ChatResponse(answer=GREETING_ANSWER, sources=[])

    try:
        chain = get_chain()
        history_dicts = [item.model_dump() for item in request.history]
        answer = chain.invoke({"question": request.message, "history": history_dicts})
        sources = get_sources(request.message, history=history_dicts)
        return ChatResponse(answer=answer, sources=sources)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar a pergunta: {exc}",
        ) from exc
