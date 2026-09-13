"""
Monta a RAG chain: retriever + prompt endurecido + LLM via Ollama.
"""
from datetime import date
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from app.rag.vectorstore import get_retriever

def get_current_period(today: date) -> str:
    """Determina o periodo letivo atual com base na data fornecida."""
    periods = [
        ("2026.1", date(2026, 1, 5),  date(2026, 3, 6)),
        ("2026.2", date(2026, 3, 23), date(2026, 7, 23)),
        ("2026.3", date(2026, 7, 1),  date(2026, 8, 28)),
        ("2026.4", date(2026, 8, 24), date(2026, 12, 23)),
    ]
    active = []
    for name, start, end in periods:
        if start <= today <= end:
            active.append(name)

    if not active:
        return "Nenhum periodo letivo esta ativo nesta data."
    if len(active) == 1:
        return f"O periodo letivo ativo hoje e o {active[0]}."
    return f"Os periodos letivos ativos hoje sao: {', '.join(active)} (sobreposicao)."

def get_dynamic_today(_):
    """Calcula a data dinamicamente no momento da requisicao."""
    today = date.today()
    return today.strftime("%d de %B de %Y").replace(
        "January", "janeiro").replace("February", "fevereiro").replace(
        "March", "marco").replace("April", "abril").replace(
        "May", "maio").replace("June", "junho").replace(
        "July", "julho").replace("August", "agosto").replace(
        "September", "setembro").replace("October", "outubro").replace(
        "November", "novembro").replace("December", "dezembro")

def get_dynamic_period(_):
    """Calcula o periodo atual dinamicamente no momento da requisicao."""
    return get_current_period(date.today())

# ---------------------------------------------------------------------------
# Prompt endurecido
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE = """Voce e a Secretaria Virtual da FAMED/UFPA.

Data de hoje: {today}
{current_period}

Sua UNICA fonte de informacao e o contexto fornecido abaixo, extraido do Calendario Academico 2026 da UFPA.

REGRAS OBRIGATORIAS - siga todas sem excecao:
1. Responda SOMENTE com informacoes que estejam EXPLICITAMENTE escritas no contexto abaixo.
2. Quando a pergunta mencionar "esse periodo", "periodo atual" ou "agora", use a informacao de data de hoje fornecida acima para identificar o periodo correto e busque a resposta no contexto.
3. Ao informar um periodo letivo, SEMPRE mencione a data de inicio E a data de termino.
4. Se a informacao solicitada NAO aparecer claramente no contexto, responda EXATAMENTE assim: "Nao encontrei essa informacao no Calendario Academico 2026. Entre em contato com a secretaria da FAMED."
5. NUNCA calcule, estime ou infira datas. Copie-as exatamente como aparecem no contexto.
6. NUNCA afirme que algo nao existe apenas porque nao aparece no trecho recebido.
7. Quando a pergunta for sobre um feriado especifico, responda SOMENTE sobre esse feriado, sem listar outros.
8. Responda sempre em portugues do Brasil, de forma objetiva e direta.

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
    retriever = get_retriever()
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "today": get_dynamic_today,
            "current_period": get_dynamic_period,
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain

def get_sources(question: str) -> list[str]:
    retriever = get_retriever()
    docs = retriever.invoke(question)
    if docs:
        return ["Calendario Academico 2026 - UFPA"]
    return []