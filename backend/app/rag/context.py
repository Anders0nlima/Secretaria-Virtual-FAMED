"""
Módulo de Gerenciamento de Janela de Contexto e Continuidade Conversacional.

Diferencia com precisão:
1. Perguntas de continuidade / follow-up (mesmo contexto):
   - Injeta o assunto ativo na busca vetorial para garantir recuperação precisa.
   - Fornece o histórico recente ao prompt do LLM para resolução anafórica.
2. Perguntas de novo assunto (mudança de contexto):
   - Não contamina a busca vetorial com assuntos anteriores.
   - Omite o histórico anterior no prompt do LLM, evitando contaminação de tópicos.
"""
import re
import unicodedata
from app.rag.intent import is_calendar_query

# ---------------------------------------------------------------------------
# Base de Conhecimento de Domínios Acadêmicos da FAMED/UFPA
# ---------------------------------------------------------------------------

DOMAINS = {
    "TRANCAMENTO": {
        "keywords": [
            "trancamento", "trancar", "trancar curso", "trancamento total",
            "trancamento administrativo", "desistencia", "desistência"
        ],
        "default_subject": "trancamento do período letivo total"
    },
    "SEGUNDA_CHAMADA": {
        "keywords": [
            "segunda chamada", "2 chamada", "2ª chamada", "segunda avaliacao",
            "segunda avaliação", "segunda prova", "falta de prova", "perdi a prova",
            "perdi prova", "perdi avaliacao", "substitutiva", "avaliacao substitutiva",
            "avaliação substitutiva"
        ],
        "default_subject": "segunda chamada de avaliação/prova (prazo de 72 horas úteis)"
    },
    "SAPE": {
        "keywords": [
            "sape", "apoio pedagogico", "apoio pedagógico", "orientacao pedagogica",
            "orientação pedagógica", "suporte pedagogico", "suporte pedagógico"
        ],
        "default_subject": "SAPE - Serviço de Apoio Pedagógico ao Estudante (sape.famed@gmail.com)"
    },
    "PEAPS": {
        "keywords": [
            "peaps", "saude mental", "saúde mental", "psicologico", "psicológico",
            "psicossocial", "psicologa", "psicóloga", "atendimento psicologico",
            "apoio psicologico", "psiquiatria"
        ],
        "default_subject": "PEAPS - Apoio Psicossocial e Saúde Mental (peaps@ufpa.br)"
    },
    "ACESSIBILIDADE_PCD": {
        "keywords": [
            "tea", "tdah", "pcd", "acessibilidade", "adaptacao", "adaptação",
            "adaptacoes", "adaptações", "adaptacoes razoaveis", "adaptações razoáveis",
            "dacess", "cades", "autista", "autismo", "deficiencia", "deficiência",
            "tempo estendido", "sala silenciosa"
        ],
        "default_subject": "adaptações razoáveis e acessibilidade (TEA, TDAH, PCD, CADES)"
    },
    "CALENDARIO": {
        "keywords": [
            "calendario", "calendário", "feriado", "recesso", "periodo letivo",
            "período letivo", "inicio das aulas", "início das aulas", "termino das aulas",
            "término das aulas", "ano letivo", "semestre letivo", "periodo 1", "período 1",
            "periodo 2", "período 2", "periodo 3", "período 3", "periodo 4", "período 4",
            "2026.1", "2026.2", "2026.3", "2026.4"
        ],
        "default_subject": "calendário acadêmico 2026 e períodos letivos"
    },
    "TCC": {
        "keywords": [
            "tcc", "trabalho de conclusao", "trabalho de conclusão", "banca de tcc",
            "orientador de tcc", "tcc 1", "tcc 2", "defesa de tcc", "artigo cientifico"
        ],
        "default_subject": "Trabalho de Conclusão de Curso (TCC) e normas de defesa"
    },
    "ESTAGIO_INTERNATO": {
        "keywords": [
            "internato", "estagio", "estágio", "internato medico", "internato médico",
            "plantao", "plantão", "escala de internato", "hospital de clinicas",
            "termo de compromisso de estagio", "tce"
        ],
        "default_subject": "estágio e internato médico da FAMED"
    },
    "APROVEITAMENTO": {
        "keywords": [
            "aproveitamento", "aproveitamento de estudos", "dispensa de disciplina",
            "dispensa", "equivalencia", "equivalência"
        ],
        "default_subject": "aproveitamento de estudos e dispensa de disciplinas"
    },
    "TAE": {
        "keywords": [
            "tae", "tratamento academico excepcional", "tratamento acadêmico excepcional",
            "regime domiciliar", "exercicios domiciliares", "exercícios domiciliares"
        ],
        "default_subject": "Tratamento Acadêmico Excepcional (TAE - regime domiciliar)"
    },
    "PRESCRICAO": {
        "keywords": [
            "prescricao", "prescrição", "jubilamento", "jubilar", "tempo de curso",
            "tempo maximo", "tempo máximo", "dilatacao", "dilatação de prazo"
        ],
        "default_subject": "tempo máximo de curso e risco de prescrição/jubilamento"
    },
    "CONTATO_SECRETARIA": {
        "keywords": [
            "contato da secretaria", "telefone da famed", "email da famed", "e-mail da famed",
            "horario de funcionamento", "horário de funcionamento", "diretor", "diretora",
            "direcao", "direção", "coordenador", "coordenadora", "coordenacao", "coordenação",
            "sagitta", "sigaa", "atendimento presencial", "localizacao da secretaria"
        ],
        "default_subject": "contatos e atendimento da Secretaria da FAMED, Coordenação e Direção"
    },
    "CEP_PESQUISA": {
        "keywords": [
            "cep", "comite de etica", "comitê de ética", "plataforma brasil",
            "pesquisa em seres humanos", "etica em pesquisa", "ética em pesquisa",
            "parecer consubstanciado"
        ],
        "default_subject": "Comitê de Ética em Pesquisa (CEP) e Plataforma Brasil"
    },
    "AGENDA": {
        "keywords": [
            "agenda", "reuniao", "reunião", "reunioes", "reuniões", "evento", "eventos",
            "marcado hoje", "marcado amanha", "marcado amanhã", "atividades hoje",
            "atividades amanha", "atividades amanhã", "sala de aula", "google agenda",
            "conferencia", "palestra"
        ],
        "default_subject": "Agenda Institucional da FAMED (Google Agenda)"
    },
    "OUVIDORIA": {
        "keywords": ["ouvidoria", "ouvidoria geral", "fala.br", "reclamacao", "denuncia"],
        "default_subject": "Ouvidoria Geral da UFPA"
    },
    "MONITORIA": {
        "keywords": ["monitoria", "monitor", "bolsa de monitoria", "atividades complementares", "horas complementares"],
        "default_subject": "monitoria e atividades complementares"
    },
}

# ---------------------------------------------------------------------------
# Padrões Gramaticais de Anáfora e Continuidade
# ---------------------------------------------------------------------------

STRONG_ANAPHORA = re.compile(
    r"\b(dele|dela|deles|delas|disso|desse|dessa|desses|dessas|disto|nisso|nesse|nessa|nesses|nessas|nisto|deste|desta|destes|destas|o mesmo|a mesma)\b",
    re.IGNORECASE
)

FOLLOW_UP_INDICATORS = [
    r"^(e|mas e|e no caso|e se|e quanto|e como|e qual|e quem|e onde|e quando|e para)\b",
    r"\b(esse ano|este ano|nesse ano|neste ano|no proximo|no proximo ano|ano que vem)\b",
    r"\b(ainda da tempo|da tempo|posso fazer ainda|da para fazer|consigo fazer|ainda posso)\b",
    r"^(qual|quais|quanto|quantos|onde|como|quando|quem|por que)\s+(e|eh|é|sao|são|fica|funciona|faco|faço|solicito|peco|peço|custa|demora|tem|posso|consigo|devo)\b",
    r"^(tem custo|eh gratuito|e gratuito|é gratuito|e de graca|é de graça|e obrigatorio|é obrigatório|precisa pagar)\b",
    r"^(o que acontece se|o que faco se|o que faço se|e se eu perder)\b",
]

PREFIX_PATTERN = re.compile(
    r"^(o que (é|e|eh|são|sao)|como funciona(m)?|como fa[cç]o (para|pra)?|como solicitar|como pedir|onde fica(m)?|onde (é|e|eh)|onde solicito|qual (é|e|eh)|qual o|qual a|quais (são|sao|os|as)|quem (é|e|eh|foi)|como emitir|como consigo|regras (de|do|da|dos|das)?)\s+",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Funções Auxiliares
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Normaliza o texto removendo acentos e convertendo para minúsculas."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return norm.lower().strip()


def detect_domain(text: str) -> str | None:
    """Detecta se o texto pertence a algum dos domínios acadêmicos conhecidos."""
    norm = normalize_text(text)
    for domain, info in DOMAINS.items():
        for kw in info["keywords"]:
            norm_kw = normalize_text(kw)
            if re.search(r"\b" + re.escape(norm_kw) + r"\b", norm):
                return domain
    return None


def extract_general_subject(text: str) -> str:
    """Extrai o sujeito semântico essencial de uma pergunta removendo prefixos interrogativos."""
    clean = text.strip()
    clean = re.sub(r"[?!.,]+$", "", clean).strip()
    sub = PREFIX_PATTERN.sub("", clean).strip()
    sub = re.sub(r"^(o|a|os|as|um|uma|de|do|da|dos|das)\s+", "", sub, flags=re.IGNORECASE).strip()
    return sub if len(sub) >= 3 else clean


def find_active_domain_and_subject(history: list[dict]) -> tuple[str | None, str | None]:
    """
    Varre o histórico de trás para frente procurando o domínio e o assunto ativo
    da última pergunta substantiva feita pelo usuário.
    """
    if not history:
        return None, None
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        if item.get("role") == "user":
            content = item.get("content", "")
            domain = detect_domain(content)
            if domain:
                return domain, DOMAINS[domain]["default_subject"]
            subj = extract_general_subject(content)
            if subj and len(subj) >= 4:
                return None, subj
    return None, None


# ---------------------------------------------------------------------------
# Analisador Principal do Turno Conversacional
# ---------------------------------------------------------------------------

def analyze_turn(question: str, history: list[dict]) -> dict:
    """
    Analisa o turno atual em relação ao histórico recente da conversa.

    Retorna um dicionário com:
    - is_follow_up (bool): True se a pergunta continuar o assunto anterior.
    - is_calendar (bool): True se for busca na agenda (incluindo follow-ups como 'e amanhã?').
    - active_domain (str | None): Domínio acadêmico ativo.
    - active_subject (str | None): Assunto legível para ancoragem.
    - retrieval_query (str): Query contextualizada para alimentar o ChromaDB.
    - chat_history_block (str): Bloco de histórico para o prompt (vazio se novo assunto).
    """
    curr_clean = question.strip()
    curr_domain = detect_domain(curr_clean)
    last_domain, last_subject = find_active_domain_and_subject(history)

    last_user_msg = None
    for item in reversed(history):
        if isinstance(item, dict) and item.get("role") == "user":
            last_user_msg = item.get("content", "")
            break

    is_fu = False
    if last_user_msg:
        norm_curr = normalize_text(curr_clean)
        # 1. Pronome anafórico forte (ex.: 'dele', 'deles', 'disso', 'desse', 'nessa') -> follow-up
        if STRONG_ANAPHORA.search(curr_clean):
            is_fu = True
        # 2. Domínio explícito diferente do anterior -> NOVO TÓPICO (reseta o contexto)
        elif curr_domain and last_domain and curr_domain != last_domain:
            is_fu = False
        # 3. Mesmo domínio explícito -> continuidade do assunto
        elif curr_domain and last_domain and curr_domain == last_domain:
            is_fu = True
        # 4. Indicadores sintáticos de continuidade (ex.: 'e quanto a', 'qual o prazo', 'dá para fazer esse ano ainda')
        elif any(re.search(pat, norm_curr) for pat in FOLLOW_UP_INDICATORS):
            is_fu = True
        # 5. Pergunta curta sem domínio explícito identificável
        elif len(curr_clean.split()) <= 6 and not curr_domain:
            is_fu = True

    # Detecção de intenção de calendário (incluindo follow-up na agenda)
    is_cal = is_calendar_query(curr_clean)
    if not is_cal and is_fu and last_domain == "AGENDA":
        if re.search(
            r"\b(hoje|amanh[aã]|segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo|que horas|qual hor[aá]rio|onde|sala)\b",
            curr_clean,
            re.IGNORECASE,
        ):
            is_cal = True

    # Assunto ativo para ancorar a recuperação
    active_subject = (
        last_subject
        if (is_fu and last_subject)
        else (DOMAINS[curr_domain]["default_subject"] if curr_domain else None)
    )

    # Query contextualizada para busca vetorial
    if is_fu and active_subject:
        retrieval_query = f"{curr_clean} ({active_subject})"
    else:
        retrieval_query = curr_clean

    # Bloco de histórico para o LLM
    # REGRA DE OURO: Se NÃO for follow-up (novo assunto), o bloco é VAZIO,
    # impedindo que o LLM contamine o novo assunto com dados do assunto anterior.
    if is_fu and history:
        recent_turns = [m for m in history if isinstance(m, dict)][-4:]
        lines = []
        for msg in recent_turns:
            role_label = "Usuário" if msg.get("role") == "user" else "Assistente"
            content = msg.get("content", "").strip()
            # Limita respostas longas anteriores a 400 caracteres para poupar contexto
            if role_label == "Assistente" and len(content) > 400:
                content = content[:400] + "..."
            lines.append(f"{role_label}: {content}")
        history_formatted = "\n".join(lines)
        chat_history_block = (
            f"HISTÓRICO RECENTE DA CONVERSA (Contexto ativo: {active_subject}):\n"
            f"{history_formatted}\n\n"
            f"REGRAS DE CONTEXTO:\n"
            f"- A pergunta atual continua o assunto anterior ('{active_subject}').\n"
            f"- Use o histórico acima APENAS para identificar pronomes ou continuidade ('dele', 'disso', 'esse ano', etc.).\n"
            f"- Responda EXCLUSIVAMENTE sobre o que foi perguntado agora, sem repetir informações desnecessárias do histórico."
        )
    else:
        chat_history_block = ""

    return {
        "is_follow_up": is_fu,
        "is_calendar": is_cal,
        "active_domain": last_domain if is_fu else curr_domain,
        "active_subject": active_subject,
        "retrieval_query": retrieval_query,
        "chat_history_block": chat_history_block,
    }

