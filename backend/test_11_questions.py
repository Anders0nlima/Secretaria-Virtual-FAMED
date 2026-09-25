import sys
import os

# Ajustar o path para poder importar do app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.rag.chain import build_chain, get_sources

# Aumentar a formatação do console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

questions = [
    "Como solicitar aproveitamento de estudos ou dispensa de disciplinas?",
    "Como funcionam as Atividades Complementares?",
    "Como resolver pendências de matrícula ou trancamento?",
    "Quais tipos de estudos são aceitos para o TCC?",
    "Revisões narrativas são permitidas no TCC?",
    "Qual é o procedimento para entrega e defesa da monografia?",
    "Como funciona a lotação e a escala do Internato?",
    "Como se inscrever no Estágio de Férias da FAMED?",
    "Como abrir um requerimento oficial?",
    "Onde obter declarações e histórico escolar?"
]

print("=== INICIANDO TESTE DAS 10 PERGUNTAS (RAG) ===\n")
try:
    chain = build_chain()
    
    for i, q in enumerate(questions, 1):
        print(f"Pergunta {i}: {q}")
        response = chain.invoke(q)
        sources = get_sources(q)
        print(f"Resposta:\n{response}")
        print(f"\nFontes: {sources}")
        print("-" * 50)
        
except Exception as e:
    print(f"ERRO: {e}")
