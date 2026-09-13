"""
Monta a RAG chain: retriever + prompt + LLM (Gemma 3 1B via Ollama).
"""
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from app.rag.vectorstore import get_retriever

# ---------------------------------------------------------------------------
# Prompt em português — instrui o modelo a responder SOMENTE com base no
# contexto recuperado e a não inventar informações.
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE = """Você é a Secretaria Virtual da FAMED/UFPA, um assistente acadêmico prestativo e cordial.

Responda a pergunta do usuário SOMENTE com base nas informações do Calendário Acadêmico 2026 da UFPA fornecidas abaixo no campo "Contexto".

Regras importantes:
- Responda sempre em português do Brasil.
- Se a informação não estiver no contexto, diga educadamente que não encontrou essa informação no Calendário Acadêmico e oriente o usuário a entrar em contato com a secretaria da FAMED.
- Não invente datas, prazos ou qualquer outra informação.
- Seja objetivo e claro.
- Quando citar datas ou prazos, confirme as informações diretamente do contexto.

Contexto do Calendário Acadêmico 2026:
{context}

Pergunta: {question}

Resposta:"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=PROMPT_TEMPLATE,
)

# ---------------------------------------------------------------------------
# LLM via Ollama
# ---------------------------------------------------------------------------
llm = OllamaLLM(
    model=settings.ollama_model,
    base_url=settings.ollama_base_url,
    temperature=0.1,  # Baixa temperatura para respostas mais precisas/factuais
)


def format_docs(docs: list) -> str:
    """Concatena os chunks recuperados em um único bloco de texto."""
    return "\n\n---\n\n".join(
        f"[Página {doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in docs
    )


def build_chain():
    """Monta e retorna a RAG chain completa."""
    retriever = get_retriever()
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def get_sources(question: str) -> list[str]:
    """Retorna as páginas dos chunks usados como fonte para a pergunta."""
    retriever = get_retriever()
    docs = retriever.invoke(question)
    pages = sorted(
        {f"Calendário Acadêmico 2026 — Página {doc.metadata.get('page', '?')}" for doc in docs}
    )
    return pages
