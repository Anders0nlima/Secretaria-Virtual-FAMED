"""
Script de diagnostico: mostra os chunks e o que o retriever retorna.
"""
import sys
sys.path.insert(0, ".")

from app.rag.loader import load_and_split
from app.rag.embeddings import get_embeddings
from app.rag.vectorstore import get_retriever

print("=" * 80)
print("DIAGNOSTICO DA PIPELINE RAG")
print("=" * 80)

# 1. Mostrar todos os chunks
print("\n--- TODOS OS CHUNKS GERADOS ---\n")
chunks = load_and_split()
for i, chunk in enumerate(chunks):
    content_preview = chunk.page_content[:150].replace("\n", " | ")
    print(f"  Chunk {i:02d} ({len(chunk.page_content):4d} chars): {content_preview}...")

# 2. Queries de teste
queries = [
    "quando posso fazer o trancamento do período atual? 2026.4",
    "trancamento do período letivo total 2026.4",
    "trancamento 2026.4",
]

retriever = get_retriever()

for query in queries:
    print(f"\n{'=' * 80}")
    print(f"QUERY: {query}")
    print(f"{'=' * 80}")
    docs = retriever.invoke(query)
    for j, doc in enumerate(docs):
        content_preview = doc.page_content[:200].replace("\n", " | ")
        print(f"\n  Resultado {j+1}:")
        print(f"  {content_preview}...")