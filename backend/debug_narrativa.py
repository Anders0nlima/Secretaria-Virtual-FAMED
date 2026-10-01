import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.getcwd())
from app.rag.chain import augment_query, build_chain
from app.rag.vectorstore import get_retriever

q = "Revisão narrativa pura é aceita como formato de TCC na FAMED?"
retriever = get_retriever()
docs = retriever.invoke(augment_query(q))
print("TOTAL DOCS:", len(docs))
for i, d in enumerate(docs):
    print(f"\n--- DOC {i+1} ({d.metadata.get('source')}) ---")
    print(d.page_content)

print("\n--- RESPOSTA DA CHAIN ---")
chain = build_chain()
print(chain.invoke(q))

