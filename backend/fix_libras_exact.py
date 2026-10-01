import os

path = os.path.join("data", "documentos_curados", "ppc_medicina_2025.md")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

target = """### LIBRAS — Obrigatória ou Optativa?
**A matéria de Libras (Língua Brasileira de Sinais) é obrigatória ou optativa? Aluno que entrou em 2022 é obrigado a fazer LIBRAS?**
A obrigatoriedade de LIBRAS depende do ano de ingresso do aluno:
- Calouros (ingressantes a partir de 2025, PPC 2025): LIBRAS é disciplina obrigatória.
- Veteranos (ingressantes até 2024, currículo anterior): LIBRAS continua sendo disciplina optativa. Alunos que ingressaram em 2022, 2023 ou 2024 não são obrigados a cursar LIBRAS."""

replacement = """### LIBRAS — Obrigatoriedade para Veteranos e Calouros
**Sou aluno que entrou em 2022. Eu sou obrigado a fazer a disciplina de LIBRAS?**
Não. O aluno que ingressou em 2022 é veterano e NÃO é obrigado a cursar a disciplina de LIBRAS. Para quem entrou até 2024 (currículo anterior ao PPC 2025), LIBRAS é uma disciplina optativa.

**A matéria de Libras (Língua Brasileira de Sinais) é obrigatória ou optativa na FAMED?**
A obrigatoriedade depende do ano de ingresso:
- Alunos que ingressaram até 2024 (veteranos, como turmas de 2021, 2022, 2023 e 2024): NÃO são obrigados a fazer LIBRAS; para eles a disciplina é optativa.
- Alunos que ingressaram a partir de 2025 (calouros do novo PPC 2025): LIBRAS é uma disciplina obrigatória."""

if target in text:
    text = text.replace(target, replacement)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("SUBSTITUIÇÃO EM PPC_MEDICINA_2025 REALIZADA COM SUCESSO!")
else:
    print("TARGET NÃO ENCONTRADO!")

