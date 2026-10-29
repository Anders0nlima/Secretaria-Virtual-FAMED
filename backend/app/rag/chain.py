"""
Monta a RAG chain: retriever + prompt endurecido + LLM via Ollama.
Inclui Query Augmentation e Janela de Contexto Conversacional Inteligente.
"""
from datetime import date
import re
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import OllamaLLM
from app.config import settings
from app.integrations.google_calendar import get_calendar_context
from app.rag.context import analyze_turn
from app.rag.vectorstore import get_retriever


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
        return active[-1]  # em sobreposição, usa o mais recente
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
    months = ["janeiro","fevereiro","março","abril","maio","junho",
              "julho","agosto","setembro","outubro","novembro","dezembro"]
    return f"{d.day} de {months[d.month-1]} de {d.year}"


# ---------------------------------------------------------------------------
# Query Augmentation: enriquece a busca com o período atual
# ---------------------------------------------------------------------------

TEMPORAL_KEYWORDS = [
    "atual", "agora", "esse periodo", "este periodo",
    "esse período", "este período", "hoje", "vigente",
    "corrente", "em curso", "desse periodo", "desse período",
    "deste periodo", "deste período", "desse semestre", "deste semestre",
    "nesse periodo", "nesse período", "neste periodo", "neste período",
    "nesse semestre", "neste semestre"
]

def sanitize_question(q: str) -> str:
    """Corrige discordâncias gramaticais comuns em perguntas sobre docentes."""
    if not q:
        return q
    q = re.sub(r"\bda\s+professor\b", "do professor", q, flags=re.IGNORECASE)
    q = re.sub(r"\bdo\s+professora\b", "da professora", q, flags=re.IGNORECASE)
    return q

def augment_query(question: str) -> str:
    """
    Injeta o período atual na query antes de buscar no ChromaDB caso mencione termos temporais.
    """
    question_lower = question.lower()
    if any(kw in question_lower for kw in TEMPORAL_KEYWORDS):
        period_code = get_active_period_code(date.today())
        if period_code:
            return f"{question} {period_code}"
    return question


# ---------------------------------------------------------------------------
# Funções dinâmicas (chamadas a cada requisição, nunca no startup)
# ---------------------------------------------------------------------------

def get_dynamic_today(_=None) -> str:
    return format_date_pt(date.today())

def get_dynamic_period(_=None) -> str:
    return get_current_period_description(date.today())


# ---------------------------------------------------------------------------
# Prompt endurecido com regras de desambiguação e continuidade
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """Você é a Secretaria Virtual da FAMED/UFPA (Faculdade de Medicina da Universidade Federal do Pará).

Data de hoje: {today}
{current_period}

{chat_history_block}

Sua ÚNICA fonte de informação é o contexto fornecido abaixo, extraído dos documentos oficiais da FAMED/UFPA: Calendário Acadêmico 2026, Regimentos, Resoluções, Regulamentos e demais normas acadêmicas.

REGRAS OBRIGATÓRIAS - siga todas sem exceção:
1. Responda SOMENTE com informações que estejam EXPLICITAMENTE escritas no contexto abaixo.
2. Quando a pergunta mencionar "esse período", "período atual", "desse semestre" ou "agora", use a data de hoje acima para identificar o período ativo e responda SOMENTE sobre ele, ignorando os outros períodos.
3. Ao informar um período letivo, SEMPRE mencione a data de início E a data de término.
4. Se a informação solicitada NÃO aparecer claramente no contexto, responda APENAS: "Não encontrei essa informação nos documentos oficiais da FAMED/UFPA. Para tirar dúvidas específicas ou protocolar um pedido, recomendamos abrir uma solicitação no SAGITTA (sagitta.ufpa.br), que é o canal oficial de atendimento ao aluno. Você também pode contatar a Secretaria da FAMED pelo telefone (91) 3201-7067, pelo e-mail coord-medicina@ufpa.br ou presencialmente na sede da FAMED (Praça Camilo Salgado, nº 01 - Umarizal / salas no Campus Guamá)."
5. NUNCA calcule, estime ou infira datas. Copie-as exatamente como aparecem no contexto.
6. NUNCA afirme que algo não existe apenas porque não aparece no trecho recebido.
7. Quando a pergunta for sobre um feriado específico, responda SOMENTE sobre esse feriado, sem listar outros.
8. Responda sempre em português do Brasil, de forma objetiva e direta.
9. IMPORTANTE — Diferencie os dois tipos de trancamento:
   - "Trancamento do Período Letivo Total" é feito pelo DISCENTE voluntariamente. O prazo coincide com a matrícula (geralmente na primeira semana do período).
   - "Trancamento Administrativo" é feito pelo CIAC automaticamente em alunos que NÃO se matricularam. O discente NÃO faz esse trancamento.
   Quando o usuário perguntar sobre "fazer trancamento", "trancar matrícula" ou "período de trancamento", ele se refere SEMPRE ao trancamento feito pelo DISCENTE.
10. Se a pergunta buscar requisitos, critérios, ou quem tem direito a algo, extraia e liste TODOS os requisitos mencionados no texto, de forma exata e completa.
11. Se houver informações da Agenda Institucional (Google Agenda) no contexto sobre eventos, reuniões ou atendimentos marcados, use-as com prioridade para responder sobre datas e horários agendados.
12. Ao responder sobre a Agenda Institucional (Google Agenda):
    - Use SEMPRE a "Data de hoje" informada no contexto para identificar as atividades de hoje e de dias futuros. Nunca confunda datas futuras com hoje.
    - Se a pergunta for sobre um dia ou data específica (ex: "hoje", "amanhã" ou "14/10"), liste APENAS as atividades referentes à data solicitada.
    - Ao buscar por um professor ou docente, localize a linha onde o NOME COMPLETO OU SOBRENOME do professor aparece explicitamente. NUNCA atribua a sala ou horário de outro docente.
    - Informe com clareza o horário de início e término, a sala ou local, e o nome da atividade ou docente responsável.
13. FORMATAÇÃO E ESTRUTURA VISUAL:
    - Utilize Markdown claro e bem organizado.
    - Quando listar múltiplos itens, documentos, etapas ou prazos, SEMPRE use tópicos em linhas separadas começando com '- ' ou números (ex:
      - Item A
      - Item B).
      NUNCA junte tópicos na mesma linha.
    - Destaque em **negrito** informações-chave (como datas, prazos, locais e nomes de setores).
    - Separe parágrafos com uma linha em branco para facilitar a leitura.
14. FOCO NA PERGUNTA E CONTINUIDADE:
    - Responda APENAS ao que foi solicitado na "Pergunta:". NUNCA inclua informações de outros assuntos que não foram pedidos.
    - Se houver "HISTÓRICO RECENTE DA CONVERSA", use-o EXCLUSIVAMENTE para entender continuidade ou pronomes da pergunta atual. NUNCA misture tópicos passados com novos assuntos.
    - Só fale do SAPE (Serviço de Apoio Pedagógico), do PEAPS ou de saúde mental se a pergunta mencionar explicitamente esses temas (apoio pedagógico, acolhimento, acessibilidade, TEA/TDAH, atendimento psicológico etc.).
    - Se a mensagem for apenas um cumprimento ou agradecimento (ex.: "olá", "bom dia", "obrigado"), responda de forma breve e cordial.

Contexto dos documentos oficiais da FAMED/UFPA:
{context}

Pergunta: {question}

Resposta:"""

prompt = PromptTemplate(
    input_variables=["today", "current_period", "chat_history_block", "context", "question"],
    template=PROMPT_TEMPLATE,
)


def format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def get_full_context(question: str, history: list[dict] | None = None) -> str:
    """
    Combina os chunks do ChromaDB e, caso a pergunta envolva eventos/agenda,
    injeta os agendamentos em tempo real do Google Calendar no início do contexto.
    """
    if history is None:
        history = []
    analysis = analyze_turn(question, history)
    sanitized_q = sanitize_question(analysis["retrieval_query"])
    augmented_q = augment_query(sanitized_q)
    retriever = get_retriever()
    docs = retriever.invoke(augmented_q)
    rag_context = format_docs(docs)

    if analysis["is_calendar"]:
        cal_context = get_calendar_context(query=sanitize_question(question))
        return f"{cal_context}\n\n---\n\n{rag_context}"

    return rag_context


def prepare_chain_inputs(input_data: dict | str) -> dict:
    """
    Prepara todas as variáveis para o prompt do modelo:
    - Executa a análise de continuidade conversacional (analyze_turn).
    - Busca os documentos relevantes via retriever (com enriquecimento semântico).
    - Injeta agendamentos do Google Calendar se a intenção for de agenda.
    - Monta o bloco de histórico recente de forma controlada.
    """
    if isinstance(input_data, str):
        question = input_data
        history = []
    else:
        question = input_data.get("question", "")
        history = input_data.get("history", [])

    analysis = analyze_turn(question, history)
    sanitized_retrieval_q = sanitize_question(analysis["retrieval_query"])
    augmented_q = augment_query(sanitized_retrieval_q)

    retriever = get_retriever()
    docs = retriever.invoke(augmented_q)
    rag_context = format_docs(docs)

    if analysis["is_calendar"]:
        cal_context = get_calendar_context(query=sanitize_question(question))
        full_context = f"{cal_context}\n\n---\n\n{rag_context}"
    else:
        full_context = rag_context

    return {
        "context": full_context,
        "question": sanitize_question(question),
        "today": get_dynamic_today(),
        "current_period": get_dynamic_period(),
        "chat_history_block": analysis["chat_history_block"],
    }


def build_chain():
    """
    Monta a RAG chain com controle rigoroso de contexto e Query Augmentation.
    """
    llm = OllamaLLM(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
        num_ctx=8192,
    )

    chain = (
        RunnableLambda(prepare_chain_inputs)
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def get_sources(question: str, history: list[dict] | None = None) -> list[str]:
    """Retorna os nomes dos documentos oficiais usados para responder à pergunta."""
    if history is None:
        history = []
    analysis = analyze_turn(question, history)
    sanitized_retrieval_q = sanitize_question(analysis["retrieval_query"])
    augmented_q = augment_query(sanitized_retrieval_q)

    retriever = get_retriever()
    docs = retriever.invoke(augmented_q)
    seen = set()
    sources = []
    for doc in docs:
        src = doc.metadata.get("source", "Documentos FAMED/UFPA")
        if src not in seen:
            seen.add(src)
            sources.append(src)

    if analysis["is_calendar"]:
        cal_source = "Agenda Institucional da FAMED/UFPA (Google Agenda)"
        if cal_source not in seen:
            sources.append(cal_source)

    return sources
