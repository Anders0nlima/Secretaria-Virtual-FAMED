import sys
sys.stdout.reconfigure(encoding="utf-8")
from app.rag.chain import augment_query
from app.rag.vectorstore import get_retriever

retriever = get_retriever()
q = "Qual é o prazo para os professores consolidarem as notas do período 2026.4?"
docs = retriever.invoke(augment_query(q))
print("CHUNKS RECUPERADOS:")
for i, doc in enumerate(docs):
    print(f"--- CHUNK {i+1} ---")
    print(doc.page_content)

