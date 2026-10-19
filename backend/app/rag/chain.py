"""
Monta a RAG chain: retriever + prompt endurecido + LLM via Ollama.
Inclui Query Augmentation para melhorar a busca vetorial.
"""
import re
from datetime import date
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from app.rag.vectorstore import get_retriever
from app.rag.intent import is_calendar_query
from app.integrations.google_calendar import get_calendar_context


# ---------------------------------------------------------------------------
# Auxiliares de data e periodo
# ---------------------------------------------------------------------------

PERIODS = [
    ("2026.1", date(2026, 1, 5),  date(2026, 3, 6)),
    ("2026.2", date(2026, 3, 23), date(2026, 7, 23)),
    ("2026.3", date(2026, 7, 1),  date(2026, 8, 28)),
    ("2026.4", date(2026, 8, 24), date(2026, 12, 23)),
]

def get_active_period_code(today: date) -> str:
    """Retorna o codigo do periodo ativo (ex: '2026.4'), ou string vazia se fora do calendario."""
    active = [name for name, start, end in PERIODS if start <= today <= end]
    if len(active) == 1:
        return active[0]
    if len(active) > 1:
        return active[-1]  # em sobreposicao, usa o mais recente
    return ""

def get_current_period_description(today: date) -> str:
    """Retorna descricao legivel do periodo ativo para o prompt."""
    active = [name for name, start, end in PERIODS if start <= today <= end]
    if not active:
        return "Nenhum periodo letivo esta ativo nesta data."
    if len(active) == 1:
        return f"O periodo letivo ativo hoje e o {active[0]}."
    return f"Os periodos letivos ativos hoje sao: {', '.join(active)} (sobreposicao de periodos)."

def format_date_pt(d: date) -> str:
    """Formata data em portugues."""
    months = ["janeiro","fevereiro","marco","abril","maio","junho",
              "julho","agosto","setembro","outubro","novembro","dezembro"]
    return f"{d.day} de {months[d.month-1]} de {d.year}"


# ---------------------------------------------------------------------------
# Query Augmentation: enriquece a busca com o periodo atual
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
    Injeta o periodo atual na query antes de buscar no ChromaDB.

    Quando o usuario pergunta sobre 'esse periodo' ou 'periodo atual',
    a busca vetorial nao sabe o que e 'atual'. Ao adicionar '2026.4'
    na query, o ChromaDB passa a buscar chunks que contenham esse codigo,
    trazendo os resultados corretos.
    """
    question_lower = question.lower()
    if any(kw in question_lower for kw in TEMPORAL_KEYWORDS):
        period_code = get_active_period_code(date.today())
        if period_code:
            return f"{question} {period_code}"
    return question


# ---------------------------------------------------------------------------
# Funcoes dinamicas (chamadas a cada requisicao, nunca no startup)
# ---------------------------------------------------------------------------

def get_dynamic_today(_=None) -> str:
    return format_date_pt(date.today())

def get_dynamic_period(_=None) -> str:
    return get_current_period_description(date.today())


# ---------------------------------------------------------------------------
# Prompt endurecido com regras de disambiguacao
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """Voce e a Secretaria Virtual da FAMED/UFPA (Faculdade de Medicina da Universidade Federal do Para).

Data de hoje: {today}
{current_period}

Sua UNICA fonte de informacao e o contexto fornecido abaixo, extraido dos documentos oficiais da FAMED/UFPA: Calendario Academico 2026, Regimentos, Resolucoes, Regulamentos e demais normas academicas.

REGRAS OBRIGATORIAS - siga todas sem excecao:
1. Responda SOMENTE com informacoes que estejam EXPLICITAMENTE escritas no contexto abaixo.
2. Quando a pergunta mencionar "esse periodo", "periodo atual", "desse semestre" ou "agora", use a data de hoje acima para identificar o periodo ativo e responda SOMENTE sobre ele, ignorando os outros periodos.
3. Ao informar um periodo letivo, SEMPRE mencione a data de inicio E a data de termino.
4. Se a informacao solicitada NAO aparecer claramente no contexto, responda APENAS: "Não encontrei essa informação nos documentos oficiais da FAMED/UFPA. Para tirar dúvidas específicas ou protocolar um pedido, recomendamos abrir uma solicitação no SAGITTA (sagitta.ufpa.br), que é o canal oficial de atendimento ao aluno. Você também pode contatar a Secretaria da FAMED pelo WhatsApp/Telefone (91) 93201-7067, pelo e-mail coord-medicina@ufpa.br ou presencialmente na sede da FAMED (Praça Camilo Salgado, nº 01 - Umarizal / salas no Campus Guamá)."
5. NUNCA calcule, estime ou infira datas. Copie-as exatamente como aparecem no contexto.
6. NUNCA afirme que algo nao existe apenas porque nao aparece no trecho recebido.
7. Quando a pergunta for sobre um feriado especifico, responda SOMENTE sobre esse feriado, sem listar outros.
8. Responda sempre em portugues do Brasil, de forma objetiva e direta.
9. IMPORTANTE — Diferencie os dois tipos de trancamento:
   - "Trancamento do Periodo Letivo Total" e feito pelo DISCENTE voluntariamente. O prazo coincide com a matricula (geralmente na primeira semana do periodo).
   - "Trancamento Administrativo" e feito pelo CIAC automaticamente em alunos que NAO se matricularam. O discente NAO faz esse trancamento.
   Quando o usuario perguntar sobre "fazer trancamento", "trancar matricula" ou "periodo de trancamento", ele se refere SEMPRE ao trancamento feito pelo DISCENTE.
10. Se a pergunta buscar requisitos, criterios, ou quem tem direito a algo, extraia e liste TODOS os requisitos mencionados no texto, de forma exata e completa.
11. Se houver informacoes da Agenda Institucional (Google Agenda) no contexto sobre eventos, reunioes ou atendimentos marcados, use-as com prioridade para responder sobre datas e horarios agendados.
12. Ao responder sobre a Agenda Institucional (Google Agenda):
    - Use SEMPRE a "Data de hoje" informada no contexto para identificar as atividades de hoje e de dias futuros. Nunca confunda datas futuras com hoje.
    - Se a pergunta for sobre um dia ou data especifica (ex: "hoje", "amanha" ou "14/10"), liste APENAS as atividades referentes a data solicitada.
    - Ao buscar por um professor ou docente, localize a linha onde o NOME COMPLETO OU SOBRENOME do professor aparece explicitamente (por exemplo, "Lucas Lobato" deve corresponder estritamente a linha que contem "Lucas Lobato"). NUNCA atribua a sala ou horario de outro docente.
    - Informe com clareza o horario de inicio e termino, a sala ou local, e o nome da atividade ou docente responsavel.

Contexto dos documentos oficiais da FAMED/UFPA:
{context}

Pergunta: {question}

Resposta:"""

prompt = PromptTemplate(
    input_variables=["today", "current_period", "context", "question"],
    template=PROMPT_TEMPLATE,
)

llm = OllamaLLM(
    model=settings.ollama_model,
    base_url=settings.ollama_base_url,
    temperature=0.0,
    num_ctx=8192,
)


def format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def get_full_context(question: str) -> str:
    """
    Combina os chunks do ChromaDB e, caso a pergunta envolva eventos/agenda,
    injeta os agendamentos em tempo real do Google Calendar no início do contexto,
    filtrando dinamicamente as entidades mencionadas na pergunta.
    """
    retriever = get_retriever()
    sanitized_q = sanitize_question(question)
    augmented_q = augment_query(sanitized_q)
    docs = retriever.invoke(augmented_q)
    rag_context = format_docs(docs)

    if is_calendar_query(sanitized_q):
        cal_context = get_calendar_context(query=sanitized_q)
        # Injeta a agenda no topo para máxima atenção e relevância temporal
        return f"{cal_context}\n\n---\n\n{rag_context}"

    return rag_context


def build_chain():
    """
    Monta a RAG chain com Query Augmentation.

    Fluxo:
    1. Query Augmentation: injeta periodo atual na query de busca
    2. Retriever: busca os chunks mais relevantes no ChromaDB
    3. Prompt: formata contexto + data + regras + pergunta original
    4. LLM: gera a resposta
    """
    chain = (
        {
            # Busca com a query enriquecida (tem periodo atual se necessario)
            "context": RunnableLambda(get_full_context),
            # Pergunta original higienizada enviada ao LLM
            "question": RunnableLambda(sanitize_question),
            "today": RunnableLambda(get_dynamic_today),
            "current_period": RunnableLambda(get_dynamic_period),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def get_sources(question: str) -> list[str]:
    """Retorna os nomes dos documentos usados para responder a pergunta."""
    retriever = get_retriever()
    sanitized_q = sanitize_question(question)
    docs = retriever.invoke(augment_query(sanitized_q))
    seen = set()
    sources = []
    for doc in docs:
        src = doc.metadata.get("source", "Documentos FAMED/UFPA")
        if src not in seen:
            seen.add(src)
            sources.append(src)
    if is_calendar_query(sanitized_q):
        cal_source = "Agenda Institucional da FAMED/UFPA (Google Agenda)"
        if cal_source not in seen:
            sources.append(cal_source)

    return sources