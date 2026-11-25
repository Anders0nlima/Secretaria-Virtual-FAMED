"""
Pipeline Conversational RAG da Secretaria Virtual FAMED/UFPA:
1. Reescrita de pergunta independente (Query Rewriting) com ChatOllama quando há histórico.
2. Busca híbrida (BM25 + ChromaDB via RRF) + integração inteligente com Google Calendar.
3. Geração estruturada via ChatOllama (SystemMessage + HumanMessage) com contexto limpo,
   evitando contaminação entre perguntas sequenciais e repetição de respostas anteriores.
"""
from datetime import date
from functools import lru_cache
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama
from app.config import settings
from app.integrations.google_calendar import get_calendar_context
from app.rag.context import clean_user_message, rewrite_question_with_llm
from app.rag.intent import is_calendar_query
from app.rag.vectorstore import hybrid_retrieve


# ---------------------------------------------------------------------------
# Auxiliares de data e período
# ---------------------------------------------------------------------------

PERIODS = [
    ("2026.1", date(2026, 1, 5),  date(2026, 3, 6)),
    ("2026.2", date(2026, 3, 23), date(2026, 7, 23)),
    ("2026.3", date(2026, 7, 1),  date(2026, 8, 28)),
    ("2026.4", date(2026, 8, 24), date(2026, 12, 23)),
]


def get_active_period_code(today: date) -> str:
    """Retorna o código do período ativo (ex: '2026.4'), ou string vazia se fora do calendário."""
    active = [name for name, start, end in PERIODS if start <= today <= end]
    if len(active) == 1:
        return active[0]
    if len(active) > 1:
        return active[-1]
    return ""


def get_current_period_description(today: date) -> str:
    """Retorna descrição legível do período ativo para o prompt."""
    active = [name for name, start, end in PERIODS if start <= today <= end]
    if not active:
        return "Nenhum período letivo está ativo nesta data."
    if len(active) == 1:
        return f"O período letivo ativo hoje é o {active[0]}."
    return f"Os períodos letivos ativos hoje são: {', '.join(active)} (sobreposição de períodos)."


def format_date_pt(d: date) -> str:
    """Formata data em português."""
    months = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    ]
    return f"{d.day} de {months[d.month - 1]} de {d.year}"


# ---------------------------------------------------------------------------
# Query Augmentation: enriquece a busca com o período atual
# ---------------------------------------------------------------------------

TEMPORAL_KEYWORDS = [
    "atual", "agora", "esse periodo", "este periodo",
    "esse período", "este período", "hoje", "vigente",
    "corrente", "em curso", "desse periodo", "desse período",
    "deste periodo", "deste período", "desse semestre", "deste semestre",
    "nesse periodo", "nesse período", "neste periodo", "neste período",
    "nesse semestre", "neste semestre",
]


def sanitize_question(q: str) -> str:
    """Mantido por compatibilidade; delega para clean_user_message."""
    return clean_user_message(q)


def augment_query(question: str) -> str:
    """Injeta o período letivo ativo na query caso mencione termos temporais."""
    question_lower = question.lower()
    if any(kw in question_lower for kw in TEMPORAL_KEYWORDS):
        period_code = get_active_period_code(date.today())
        if period_code and period_code not in question_lower:
            return f"{question} {period_code}"
    return question


def get_dynamic_today(_=None) -> str:
    return format_date_pt(date.today())


def get_dynamic_period(_=None) -> str:
    return get_current_period_description(date.today())


# ---------------------------------------------------------------------------
# Prompt de Sistema enxuto e rigoroso (otimizado para gemma3:4b via ChatOllama)
# ---------------------------------------------------------------------------

FALLBACK_ANSWER = (
    "Não encontrei essa informação nos documentos oficiais da FAMED/UFPA. "
    "Para tirar dúvidas específicas ou protocolar um pedido, recomendamos abrir uma solicitação no "
    "SAGITTA (sagitta.ufpa.br), que é o canal oficial de atendimento ao aluno. "
    "Você também pode contatar a Secretaria da FAMED pelo telefone (91) 3201-7067, "
    "pelo e-mail coord-medicina@ufpa.br ou presencialmente na sede da FAMED "
    "(Praça Camilo Salgado, nº 01 - Umarizal / salas no Campus Guamá)."
)

SYSTEM_PROMPT = f"""Você é a Secretaria Virtual da FAMED/UFPA (Faculdade de Medicina da Universidade Federal do Pará).
Sua ÚNICA fonte de informação é o CONTEXTO fornecido pelo usuário.

REGRAS OBRIGATÓRIAS:
1. FIDELIDADE ABSOLUTA: Responda SOMENTE com informações EXPLICITAMENTE escritas no CONTEXTO. NUNCA invente, calcule ou misture regras de assuntos diferentes (por exemplo: não misture regras de revisão de nota com laudo médico de TAE, nem datas de Oferta de Turmas com datas de Fim das Aulas).
2. FOCO ESTRITO NA PERGUNTA: Responda APENAS ao que foi perguntado. Ignore completamente trechos do contexto que tratem de outros assuntos.
3. QUANDO NÃO SOUBER: Se a resposta NÃO estiver claramente no CONTEXTO, responda EXATAMENTE e SOMENTE:
"{FALLBACK_ANSWER}"
4. CALENDÁRIO ACADÊMICO E DATAS:
   - Copie as datas exatamente como aparecem no contexto.
   - Ao citar um período letivo (2026.1, 2026.2, 2026.3 ou 2026.4), informe sempre a data de início e a data de término das aulas.
   - Se a pergunta mencionar "período atual", "esse período" ou "esse semestre", responda somente sobre o período letivo ativo hoje.
   - Em trancamento, diferencie: "Trancamento do Período Letivo Total" (feito pelo discente no SIGAA) vs. "Trancamento Administrativo" (automático pelo CIAC).
5. AGENDA INSTITUCIONAL (GOOGLE AGENDA):
   - Priorize o bloco da Agenda Institucional para dúvidas sobre aulas, salas, horários e eventos.
   - Liste APENAS as atividades da data ou docente solicitado, informando horário, sala e atividade/docente. Nunca atribua a sala de um professor a outro.
6. FORMATAÇÃO:
   - Responda em português do Brasil, de forma clara, objetiva e cordial.
   - Use Markdown limpo: listas com '- ' ou '1. ' em linhas separadas e **negrito** em datas, prazos, locais e sistemas."""


# ---------------------------------------------------------------------------
# Instâncias ChatOllama (cache singleton)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_rewriter_llm() -> ChatOllama:
    """LLM compacto e rápido dedicado exclusivamente à reescrita de pergunta independente."""
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
        num_ctx=4096,
        num_predict=96,
    )


@lru_cache(maxsize=1)
def get_answer_llm() -> ChatOllama:
    """LLM principal para geração da resposta fundamentada no contexto recuperado."""
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
        num_ctx=8192,
    )


def format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


# ---------------------------------------------------------------------------
# Execução Unificada (Reescrita + Busca Híbrida + Geração + Fontes em 1 passagem)
# ---------------------------------------------------------------------------

def _retrieve_context_and_sources(standalone_question: str, original_question: str) -> tuple[str, list[str]]:
    """
    Executa a busca híbrida (BM25 + ChromaDB) e, se aplicável, injeta a Agenda
    Institucional em tempo real. Retorna (full_context, sources).
    """
    is_cal = is_calendar_query(standalone_question) or is_calendar_query(original_question)
    augmented_q = augment_query(standalone_question)

    docs = hybrid_retrieve(augmented_q, k=settings.retriever_k)
    rag_context = format_docs(docs)

    seen = set()
    sources: list[str] = []
    for doc in docs:
        src = doc.metadata.get("source", "Documentos FAMED/UFPA")
        if src not in seen:
            seen.add(src)
            sources.append(src)

    if is_cal:
        cal_context = get_calendar_context(query=standalone_question)
        cal_source = "Agenda Institucional da FAMED/UFPA (Google Agenda)"
        if cal_source not in seen:
            sources.insert(0, cal_source)
        full_context = f"{cal_context}\n\n---\n\n{rag_context}"
    else:
        full_context = rag_context

    return full_context, sources


def answer_question(question: str, history: list[dict] | None = None) -> tuple[str, list[str]]:
    """
    Executa o pipeline completo em uma única passagem:
    1. Reescreve a pergunta com base no histórico válido (se houver histórico).
    2. Recupera contexto relevante via busca híbrida + Google Calendar.
    3. Gera a resposta limpa com ChatOllama (sem histórico poluído no prompt final).
    """
    clean_q = clean_user_message(question)
    standalone_q = rewrite_question_with_llm(clean_q, history, llm=get_rewriter_llm())

    full_context, sources = _retrieve_context_and_sources(standalone_q, clean_q)

    human_content = (
        f"Data de hoje: {get_dynamic_today()}\n"
        f"{get_dynamic_period()}\n\n"
        f"CONTEXTO DOS DOCUMENTOS OFICIAIS DA FAMED/UFPA:\n"
        f"{full_context}\n\n"
        f"PERGUNTA DO USUÁRIO:\n"
        f"{standalone_q}"
    )

    response = get_answer_llm().invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ])
    answer = (response.content if hasattr(response, "content") else str(response)).strip()

    # Se o modelo respondeu com o fallback de "não encontrei", não exibe fontes enganosas
    if answer.startswith("Não encontrei essa informação nos documentos oficiais"):
        sources = []

    return answer, sources


# ---------------------------------------------------------------------------
# Compatibilidade retroativa para scripts existentes
# ---------------------------------------------------------------------------

def get_full_context(question: str, history: list[dict] | None = None) -> str:
    clean_q = clean_user_message(question)
    standalone_q = rewrite_question_with_llm(clean_q, history, llm=get_rewriter_llm())
    full_context, _ = _retrieve_context_and_sources(standalone_q, clean_q)
    return full_context


def build_chain():
    """Retorna um Runnable compatível com .invoke({'question': ..., 'history': ...})."""
    def _run(input_data: dict | str) -> str:
        if isinstance(input_data, str):
            q, hist = input_data, []
        else:
            q = input_data.get("question", "")
            hist = input_data.get("history", [])
        answer, _ = answer_question(q, history=hist)
        return answer

    return RunnableLambda(_run)


def get_sources(question: str, history: list[dict] | None = None) -> list[str]:
    clean_q = clean_user_message(question)
    standalone_q = rewrite_question_with_llm(clean_q, history, llm=get_rewriter_llm())
    _, sources = _retrieve_context_and_sources(standalone_q, clean_q)
    return sources
