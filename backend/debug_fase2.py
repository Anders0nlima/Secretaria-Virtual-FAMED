"""Diagnostico: por que Q2, Q6 e Q10 falharam?"""
import sys
sys.path.insert(0, ".")
from app.rag.vectorstore import get_retriever

retriever = get_retriever()

queries = [
    ("Q2",  "O que e o Nucleo Docente Estruturante?"),
    ("Q6",  "Quantas horas de atividades complementares preciso para me formar?"),
    ("Q10", "O que e tutoria e como funciona?"),
    ("Q8",  "O que e a avaliacao substitutiva e quando posso solicitar?"),
]

for label, query in queries:
    print(f"\n{'='*80}")
    print(f"{label}: {query}")
    print(f"{'='*80}")
    docs = retriever.invoke(query)
    for j, doc in enumerate(docs):
        src = doc.metadata.get("source", "?")
        preview = doc.page_content[:250].replace("\n", " | ")
        print(f"\n  [{j+1}] Fonte: {src}")
        print(f"      {preview}...")