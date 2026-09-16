"""
Monta a RAG chain: retriever + prompt endurecido + LLM via Ollama.
Inclui Query Augmentation para melhorar a busca vetorial.
"""
from datetime import date
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from app.rag.vectorstore import get_retriever


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
    "corrente", "em curso",
]

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

PROMPT_TEMPLATE = """Voce e a Secretaria Virtual da FAMED/UFPA.

Data de hoje: {today}
{current_period}

Sua UNICA fonte de informacao e o contexto fornecido abaixo, extraido do Calendario Academico 2026 da UFPA.

REGRAS OBRIGATORIAS - siga todas sem excecao:
1. Responda SOMENTE com informacoes que estejam EXPLICITAMENTE escritas no contexto abaixo.
2. Quando a pergunta mencionar "esse periodo", "periodo atual" ou "agora", use a data de hoje acima para identificar o periodo correto e busque no contexto.
3. Ao informar um periodo letivo, SEMPRE mencione a data de inicio E a data de termino.
4. Se a informacao solicitada NAO aparecer claramente no contexto, responda: "Nao encontrei essa informacao no Calendario Academico 2026. Entre em contato com a secretaria da FAMED."
5. NUNCA calcule, estime ou infira datas. Copie-as exatamente como aparecem no contexto.
6. NUNCA afirme que algo nao existe apenas porque nao aparece no trecho recebido.
7. Quando a pergunta for sobre um feriado especifico, responda SOMENTE sobre esse feriado, sem listar outros.
8. Responda sempre em portugues do Brasil, de forma objetiva e direta.
9. IMPORTANTE — Diferencie os dois tipos de trancamento:
   - "Trancamento do Periodo Letivo Total" e feito pelo DISCENTE voluntariamente. O prazo coincide com a matricula (geralmente na primeira semana do periodo).
   - "Trancamento Administrativo" e feito pelo CIAC automaticamente em alunos que NAO se matricularam. O discente NAO faz esse trancamento.
   Quando o usuario perguntar sobre "fazer trancamento", "trancar matricula" ou "periodo de trancamento", ele se refere SEMPRE ao trancamento feito pelo DISCENTE.

Contexto do Calendario Academico 2026:
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
)


def format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def build_chain():
    """
    Monta a RAG chain com Query Augmentation.

    Fluxo:
    1. Query Augmentation: injeta periodo atual na query de busca
    2. Retriever: busca os chunks mais relevantes no ChromaDB
    3. Prompt: formata contexto + data + regras + pergunta original
    4. LLM: gera a resposta
    """
    retriever = get_retriever()
    augment = RunnableLambda(augment_query)

    chain = (
        {
            # Busca com a query enriquecida (tem periodo atual se necessario)
            "context": augment | retriever | format_docs,
            # Pergunta original (sem alteracao) e enviada ao LLM
            "question": RunnablePassthrough(),
            "today": RunnableLambda(get_dynamic_today),
            "current_period": RunnableLambda(get_dynamic_period),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def get_sources(question: str) -> list[str]:
    retriever = get_retriever()
    docs = retriever.invoke(augment_query(question))
    if docs:
        return ["Calendario Academico 2026 - UFPA"]
    return []