import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from app.rag.chain import build_chain

chain = build_chain()

test_questions = [
    "Quantas horas de atividades complementares preciso para me formar?",
    "O que e tutoria e como funciona?",
    "O que e a avaliacao substitutiva e quando posso solicitar?",
    "O que e o Nucleo Docente Estruturante?",
    "Como eu solicito o TCC?",
    "Qual e o prazo final para os professores consolidarem as notas do periodo 2026.2?",
    "Quando posso fazer o trancamento do periodo atual?",
]

for q in test_questions:
    print("=" * 80)
    print(f"PERGUNTA: {q}")
    print("=" * 80)
    ans = chain.invoke(q)
    print(f"RESPOSTA:\n{ans}\n")