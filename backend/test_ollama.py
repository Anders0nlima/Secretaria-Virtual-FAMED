import json
import urllib.request

prompt = """Voce e a Secretaria Virtual da FAMED/UFPA (Faculdade de Medicina da Universidade Federal do Para).

Data de hoje: 21 de setembro de 2026
O periodo letivo ativo hoje e o 2026.4.

Sua UNICA fonte de informacao e o contexto fornecido abaixo, extraido dos documentos oficiais da FAMED/UFPA: Calendario Academico 2026, Regimentos, Resolucoes, Regulamentos e demais normas academicas.

REGRAS OBRIGATORIAS - siga todas sem excecao:
1. Responda SOMENTE com informacoes que estejam EXPLICITAMENTE escritas no contexto abaixo.
2. Quando a pergunta mencionar "esse periodo", "periodo atual", "desse semestre" ou "agora", use a data de hoje acima para identificar o periodo ativo e responda SOMENTE sobre ele, ignorando os outros periodos.
3. Ao informar um periodo letivo, SEMPRE mencione a data de inicio E a data de termino.
4. Se a informacao solicitada NAO aparecer claramente no contexto, responda APENAS: "Nao encontrei essa informacao nos documentos da FAMED/UFPA. Entre em contato com a secretaria da FAMED."
5. NUNCA calcule, estime ou infira datas. Copie-as exatamente como aparecem no contexto.
6. NUNCA afirme que algo nao existe apenas porque nao aparece no trecho recebido.
7. Quando a pergunta for sobre um feriado especifico, responda SOMENTE sobre esse feriado, sem listar outros.
8. Responda sempre em portugues do Brasil, de forma objetiva e direta.
9. LEIA ATENTAMENTE linha por linha. NUNCA misture as datas de um periodo letivo com outro. Se a pergunta for sobre 2026.4, procure a linha exata que menciona 2026.4.

Contexto dos documentos oficiais da FAMED/UFPA:
[Fonte: Calendario Academico 2026 - UFPA]
### Consolidação de Conceitos (inclusive TCC, Estágio e Atividades Complementares) (responsável: Docente)
O prazo para consolidação de conceitos pelo docente no período 2026.1 é até 13 de março de 2026.
O prazo para consolidação de conceitos pelo docente no período 2026.2 é até 31 de julho de 2026.
O prazo para consolidação de conceitos pelo docente no período 2026.3 é até 04 de setembro de 2026.
O prazo para consolidação de conceitos pelo docente no período 2026.4 é até 10 de janeiro de 2027.

---

[Fonte: Calendario Academico 2026 - UFPA]
### Colação de Grau (responsável: Unidade)
A colação de grau do período 2026.1 deve ocorrer até 06 de junho de 2026.
A colação de grau do período 2026.2 deve ocorrer até 12 de novembro de 2026.
A colação de grau do período 2026.3 deve ocorrer até 10 de janeiro de 2027.
A colação de grau do período 2026.4 deve ocorrer até 20 de maio de 2027.

---

[Fonte: Calendario Academico 2026 - UFPA]
## Cronograma de Ações Acadêmicas  
### Oferta de Turmas (responsável: Subunidade)
A oferta de turmas para o período 2026.1 ocorre de 17 a 26 de novembro de 2025.
A oferta de turmas para o período 2026.2 ocorre de 19 de fevereiro a 04 de março de 2026.
A oferta de turmas para o período 2026.3 ocorre de 21 de maio a 03 de junho de 2026.
A oferta de turmas para o período 2026.4 ocorre de 20 a 29 de julho de 2026.

---

[Fonte: Calendario Academico 2026 - UFPA]
### Início das Aulas
As aulas do período 2026.1 iniciam em 05 de janeiro de 2026.
As aulas do período 2026.2 iniciam em 23 de março de 2026.
As aulas do período 2026.3 iniciam em 01 de julho de 2026.
As aulas do período 2026.4 iniciam em 24 de agosto de 2026.

---

[Fonte: Calendario Academico 2026 - UFPA]
### Pedido de Turma de Ensino Individual - Tutoria (responsável: Discente)
O pedido de tutoria para o período 2026.1 pode ser feito de 05 de janeiro a 05 de fevereiro de 2026.
O pedido de tutoria para o período 2026.2 pode ser feito em 23 de março de 2026.
O pedido de tutoria para o período 2026.3 pode ser feito de 01 de julho a 01 de agosto de 2026.
O pedido de tutoria para o período 2026.4 pode ser feito de 24 de agosto a 30 de novembro de 2026.

Pergunta: Qual é o prazo para os professores consolidarem as notas do período 2026.4?

Resposta:"""

req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps({
    "model": "gemma3:4b",
    "prompt": prompt,
    "stream": False,
    "temperature": 0.0
}).encode('utf-8'), headers={'Content-Type': 'application/json'})

with urllib.request.urlopen(req) as response:
    print(json.loads(response.read().decode('utf-8'))['response'])

