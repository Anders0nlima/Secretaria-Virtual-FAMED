import sys
sys.stdout.reconfigure(encoding="utf-8")
from app.rag.chain import build_chain
from langchain.globals import set_debug

set_debug(True)
chain = build_chain()

question = "Qual é o prazo para os professores consolidarem as notas do período 2026.4?"
print("Testing:", question)
print(chain.invoke(question))

