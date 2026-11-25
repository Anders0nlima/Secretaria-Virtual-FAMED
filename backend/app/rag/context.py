"""
Módulo de Gerenciamento de Contexto Conversacional e Reescrita de Perguntas (Query Rewriting).

Estratégia padrão de mercado para Conversational RAG:
1. Se NÃO houver histórico válido (1º turno): retorna a pergunta limpa imediatamente (0 latência extra).
2. Se houver histórico válido: usa o próprio LLM (ChatOllama, temperature=0, poucos tokens)
   com exemplos few-shot para transformar (histórico + última pergunta) em uma
   PERGUNTA INDEPENDENTE (Standalone Question):
   - Se for continuação ("e se passar do prazo?", "e amanhã?"), incorpora o assunto anterior.
   - Se o usuário mudou de assunto, ignora o histórico e corrige eventuais erros de digitação
     (ex: "a genda do dia" -> "Qual é a agenda de atividades de hoje na FAMED?").
3. A busca RAG e a geração final acontecem sobre a pergunta independente limpa,
   evitando contaminação entre tópicos e repetição de respostas anteriores.
"""
import re
import unicodedata
from langchain_core.messages import HumanMessage, SystemMessage
from app.rag.intent import is_calendar_query


# ---------------------------------------------------------------------------
# Limpeza de Mensagens e Filtragem de Histórico
# ---------------------------------------------------------------------------

_FALLBACK_PREFIXES = (
    "Não encontrei essa informação nos documentos oficiais",
    "Desculpe, ocorreu um erro",
)


def clean_user_message(text: str) -> str:
    """Corrige erros de digitação e discordâncias muito comuns antes da busca."""
    if not text:
        return ""
    q = text.strip()
    q = re.sub(r"\ba\s+genda\b", "agenda", q, flags=re.IGNORECASE)
    q = re.sub(r"\bda\s+professor\b", "do professor", q, flags=re.IGNORECASE)
    q = re.sub(r"\bdo\s+professora\b", "da professora", q, flags=re.IGNORECASE)
    q = re.sub(r"\s{2,}", " ", q)
    return q


def filter_valid_history(history: list[dict] | None, max_turns: int = 4) -> list[dict]:
    """
    Filtra o histórico removendo mensagens de erro/fallback ("Não encontrei...")
    e seus respectivos pares de pergunta, para evitar que falhas anteriores
    contaminem o reescritor de perguntas.
    """
    if not history:
        return []

    cleaned: list[dict] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if not content or role not in ("user", "assistant"):
            continue

        if role == "assistant" and content.startswith(_FALLBACK_PREFIXES):
            if cleaned and cleaned[-1]["role"] == "user":
                cleaned.pop()
            continue

        if role == "assistant" and len(content) > 280:
            content = content[:280].rsplit(" ", 1)[0] + "..."

        cleaned.append({"role": role, "content": content})

    return cleaned[-max_turns:]


# ---------------------------------------------------------------------------
# Reescrita de Pergunta Independente (Standalone Question) via LLM
# ---------------------------------------------------------------------------

_REWRITER_SYSTEM_PROMPT = """Você é um reescritor de consultas para o sistema de busca da Faculdade de Medicina da UFPA (FAMED/UFPA).
Sua ÚNICA função é reescrever a ÚLTIMA mensagem do usuário em uma pergunta independente, clara e completa em português do Brasil.

REGRAS ESTRITAS:
1. Se a última mensagem continua o assunto do histórico (ex.: "e se passar do prazo?", "quais documentos?", "e amanhã?", "qual o email?"), inclua o assunto do histórico na pergunta reescrita para que ela faça sentido sozinha.
2. Se a última mensagem for um NOVO assunto diferente do histórico (ex.: antes falou de segunda chamada e agora perguntou sobre agenda, calendário, aproveitamento, TCC ou TEA), IGNORE COMPLETAMENTE o histórico e apenas retorne a nova pergunta de forma clara.
3. Corrija eventuais erros simples de digitação (ex.: "a genda" -> "agenda").
4. NUNCA responda à pergunta. Retorne APENAS a pergunta reescrita em uma única linha, sem aspas, sem prefixos e sem explicações.

EXEMPLOS:
Histórico:
Usuário: quero solicitar uma segunda chamada de prova
Assistente: Para solicitar segunda chamada de prova na FAMED, o prazo é de até 72 horas úteis via SAGITTA...
Última mensagem: e se passar do prazo?
Saída: O que acontece se passar do prazo para solicitar segunda chamada de prova na FAMED?

Histórico:
Usuário: segunda chamada
Assistente: Para solicitar segunda chamada de prova na FAMED...
Última mensagem: a genda do dia
Saída: Qual é a agenda de atividades de hoje na FAMED?

Histórico:
Usuário: quando posso solicitar os aproveitamentos?
Assistente: O prazo para protocolar aproveitamento de estudos é até o 20º dia do semestre...
Última mensagem: tenho tea e quero saber como fazer as adaptações para a prova
Saída: Como solicitar adaptações de prova para estudante com TEA na FAMED?

Histórico:
Usuário: Agenda das atividades do dia 25/11/2026 da famed
Assistente: As atividades agendadas para 25/11/2026 são...
Última mensagem: e amanhã?
Saída: Quais são as atividades agendadas para amanhã na FAMED?"""


def _sanitize_rewritten_output(raw_output: str, fallback: str) -> str:
    """Garante que a saída do reescritor seja sempre uma única pergunta válida."""
    if not raw_output:
        return fallback
    text = raw_output.strip()
    # Pega apenas a primeira linha não vazia (evita explicações extras do modelo)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return fallback
    text = lines[0]
    # Remove prefixos que modelos pequenos às vezes adicionam
    text = re.sub(
        r"^(sa[ií]da|pergunta reescrita|reescrita|consulta|query)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    text = text.strip('"\'` ')
    # Se ficou vazio ou longo demais (sinal de que o modelo tentou responder), usa fallback seguro
    if not text or len(text) < 3 or len(text) > 220:
        return fallback
    return text


def rewrite_question_with_llm(question: str, history: list[dict] | None, llm) -> str:
    """
    Reescreve a pergunta do usuário em uma consulta independente usando o LLM
    quando existe histórico válido. Se não houver histórico ou ocorrer falha,
    retorna a pergunta limpa original.
    """
    clean_q = clean_user_message(question)
    valid_history = filter_valid_history(history)

    if not valid_history or llm is None:
        return clean_q

    hist_lines = []
    for msg in valid_history:
        label = "Usuário" if msg["role"] == "user" else "Assistente"
        hist_lines.append(f"{label}: {msg['content']}")
    hist_text = "\n".join(hist_lines)

    user_prompt = (
        f"Histórico:\n{hist_text}\n\n"
        f"Última mensagem: {clean_q}\n"
        f"Saída:"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=_REWRITER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        raw = response.content if hasattr(response, "content") else str(response)
        rewritten = _sanitize_rewritten_output(raw, fallback=clean_q)
        return clean_user_message(rewritten)
    except Exception as exc:
        print(f"[Context] Aviso ao reescrever pergunta com LLM (usando original): {exc}")
        return clean_q


# ---------------------------------------------------------------------------
# Compatibilidade retroativa: analisador heurístico leve (sem contaminar novos assuntos)
# ---------------------------------------------------------------------------

DOMAINS = {
    "TRANCAMENTO": {
        "keywords": ["trancamento", "trancar", "trancamentos", "desistencia"],
        "default_subject": "trancamento do período letivo total",
    },
    "SEGUNDA_CHAMADA": {
        "keywords": [
            "segunda chamada", "2 chamada", "2a chamada", "segunda avaliacao",
            "segunda prova", "perdi a prova", "perdi prova", "substitutiva",
        ],
        "default_subject": "segunda chamada de prova",
    },
    "SAPE": {
        "keywords": ["sape", "apoio pedagogico", "orientacao pedagogica"],
        "default_subject": "SAPE - Serviço de Apoio Pedagógico ao Estudante",
    },
    "PEAPS": {
        "keywords": ["peaps", "saude mental", "psicologico", "psicossocial", "psiquiatria"],
        "default_subject": "PEAPS - Apoio Psicossocial e Saúde Mental",
    },
    "ACESSIBILIDADE_PCD": {
        "keywords": [
            "tea", "tdah", "pcd", "acessibilidade", "adaptacao", "adaptacoes",
            "dacess", "cades", "autista", "autismo", "deficiencia",
        ],
        "default_subject": "adaptações razoáveis e acessibilidade (TEA, TDAH, PcD)",
    },
    "CALENDARIO": {
        "keywords": [
            "calendario", "feriado", "feriados", "recesso", "periodo letivo",
            "inicio das aulas", "termino das aulas", "fim das aulas",
            "2026.1", "2026.2", "2026.3", "2026.4",
        ],
        "default_subject": "calendário acadêmico 2026",
    },
    "TCC": {
        "keywords": ["tcc", "trabalho de conclusao", "banca de tcc", "defesa de tcc"],
        "default_subject": "Trabalho de Conclusão de Curso (TCC)",
    },
    "ESTAGIO_INTERNATO": {
        "keywords": ["internato", "estagio", "estagios", "plantao", "tce"],
        "default_subject": "estágio e internato médico",
    },
    "APROVEITAMENTO": {
        "keywords": ["aproveitamento", "aproveitamentos", "dispensa", "equivalencia"],
        "default_subject": "aproveitamento de estudos",
    },
    "TAE": {
        "keywords": ["tae", "tratamento academico excepcional", "regime domiciliar", "exercicios domiciliares"],
        "default_subject": "Tratamento Acadêmico Excepcional (TAE)",
    },
    "PRESCRICAO": {
        "keywords": ["prescricao", "jubilamento", "jubilar", "tempo maximo"],
        "default_subject": "prescrição de matrícula e jubilamento",
    },
    "AGENDA": {
        "keywords": ["agenda", "agendamento", "reuniao", "reunioes", "evento", "eventos", "sala de aula"],
        "default_subject": "Agenda Institucional da FAMED",
    },
}

_STRICT_FOLLOWUP_PATTERNS = [
    r"^(e se|e quanto|e no caso|e para|e o prazo|e os documentos|e amanh[aã]|e hoje)\b",
    r"\b(dele|dela|deles|delas|disso|disto|nisso|nisto)\b",
    r"^(qual o prazo\??|quais os documentos\??|como solicito\??|onde solicito\??|ainda da tempo\??)$",
]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return norm.lower().strip()


def detect_domain(text: str) -> str | None:
    norm = normalize_text(text)
    for domain, info in DOMAINS.items():
        for kw in info["keywords"]:
            if re.search(r"\b" + re.escape(normalize_text(kw)) + r"\b", norm):
                return domain
    return None


def analyze_turn(question: str, history: list[dict] | None = None) -> dict:
    """
    Fallback heurístico conservador (usado apenas se não houver LLM rewriter):
    só marca follow-up quando há sinal explícito de continuidade E não houve troca de domínio.
    """
    clean_q = clean_user_message(question)
    valid_history = filter_valid_history(history)
    curr_domain = detect_domain(clean_q)

    last_domain = None
    last_subject = None
    for msg in reversed(valid_history):
        if msg["role"] == "user":
            d = detect_domain(msg["content"])
            if d:
                last_domain = d
                last_subject = DOMAINS[d]["default_subject"]
                break

    norm_curr = normalize_text(clean_q)
    is_fu = False
    if valid_history and last_domain:
        if curr_domain and curr_domain != last_domain:
            is_fu = False
        elif any(re.search(pat, norm_curr) for pat in _STRICT_FOLLOWUP_PATTERNS):
            is_fu = True

    is_cal = is_calendar_query(clean_q)
    if not is_cal and is_fu and last_domain == "AGENDA":
        is_cal = True

    active_subject = last_subject if (is_fu and last_subject) else (
        DOMAINS[curr_domain]["default_subject"] if curr_domain else None
    )
    retrieval_query = f"{clean_q} ({active_subject})" if (is_fu and active_subject) else clean_q

    return {
        "is_follow_up": is_fu,
        "is_calendar": is_cal,
        "active_domain": last_domain if is_fu else curr_domain,
        "active_subject": active_subject,
        "retrieval_query": retrieval_query,
        "chat_history_block": "",
    }
