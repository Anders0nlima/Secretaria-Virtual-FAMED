import os

BASE = "data/documentos_curados"

# ============================================================
# FIX 1: SAGITTA — seção ficou numa única FAQ sem ###
# O SAGITTA FAQ precisa de ### para virar chunk isolado,
# pois o passo a passo estava sendo cortado pelo model.
# ============================================================
path = os.path.join(BASE, "links.md")
c = open(path, encoding="utf-8").read()

# O SAGITTA não tinha ### para separar "o que é" do "passo a passo"
old_sagitta = """## SAGITTA — Sistema de Atendimento ao Usuário

**O que é o SAGITTA e como acessar?**
O SAGITTA é o sistema da UFPA para atendimento digital. É por ele que o aluno abre todos os requerimentos e solicitações à secretaria da FAMED (declarações, documentos, aproveitamento de estudos etc.).
URL de acesso: https://sagitta.ufpa.br/sagitta/
Login direto: https://sagitta.ufpa.br/sagitta/login.jsf
Login: as mesmas credenciais do SIGAA.
Manual do usuário (PDF): https://sagitta.ufpa.br/sagitta/documentos/manual_sagitta.pdf

**Qual é o passo a passo para abrir uma chamada no SAGITTA?**
1. Acesse o SAGITTA e entre com usuário e senha do SIGAA.
2. Escolha o serviço que corresponde à sua necessidade no catálogo da Faculdade de Medicina.
3. Preencha o formulário: telefone atualizado (obrigatório) e descrição detalhada do pedido (obrigatório).
4. Anexe os comprovantes exigidos e aguarde o upload terminar antes de clicar em Criar Chamada.
5. Acompanhe pelo próprio SAGITTA e pelo e-mail institucional.
6. Enquanto a chamada estiver com situação "Nova", você pode cancelá-la no próprio sistema.
Atenção: se não encontrar o serviço no catálogo, entre em contato com a secretaria da FAMED."""

new_sagitta = """## SAGITTA — Sistema de Atendimento ao Usuário

### Acessando o SAGITTA
**O que é o SAGITTA e como acessar?**
O SAGITTA é o sistema da UFPA para atendimento digital. É por ele que o aluno abre todos os requerimentos e solicitações à secretaria da FAMED (declarações, documentos, aproveitamento de estudos etc.).
URL de acesso: https://sagitta.ufpa.br/sagitta/
Login direto: https://sagitta.ufpa.br/sagitta/login.jsf
Login: as mesmas credenciais do SIGAA.
Manual do usuário (PDF): https://sagitta.ufpa.br/sagitta/documentos/manual_sagitta.pdf

### Passo a Passo para Abrir uma Chamada no SAGITTA
**Qual é o passo a passo completo para abrir um chamado na secretaria da FAMED pelo SAGITTA?**
1. Acesse o SAGITTA (https://sagitta.ufpa.br/sagitta/) e entre com usuário e senha do SIGAA.
2. No catálogo de serviços, selecione a unidade "Faculdade de Medicina" e escolha o serviço correspondente à sua necessidade.
3. Preencha o formulário: telefone atualizado (obrigatório) e descrição detalhada do pedido (obrigatório).
4. Anexe os comprovantes exigidos e aguarde o upload terminar antes de clicar em "Criar Chamada".
5. Acompanhe o andamento pelo próprio SAGITTA e pelo e-mail institucional.
6. Enquanto a chamada estiver com situação "Nova", você pode cancelá-la no próprio sistema.
Atenção: se não encontrar o serviço no catálogo, entre em contato diretamente com a secretaria da FAMED."""

c = c.replace(old_sagitta, new_sagitta)

# ============================================================
# FIX 2: SIGAA matrícula — diferencia passo a passo de matrícula
# (Q3 trouxe chunk de trancamento para pergunta de matrícula)
# ============================================================
old_sigaa_mat = """### Matrícula em Disciplinas no SIGAA
**O que é o SIGAA e como fazer matrícula em disciplinas?**
O SIGAA (https://sigaa.ufpa.br) é o sistema para matrícula em turmas, trancamento, notas, faltas, histórico escolar e atestado de matrícula.
Passo a passo para matrícula: entre no SIGAA, abra o módulo de matrícula, selecione as turmas ofertadas, confira título e professor, e clique em Confirmar Matrículas. Se o sistema estiver instável, tente em outro horário, sempre antes do último dia do período de matrícula.
A primeira matrícula do calouro é feita pela coordenação; nas seguintes, o aluno seleciona as turmas no SIGAA."""

new_sigaa_mat = """### Matrícula em Disciplinas no SIGAA
**Qual o passo a passo para se matricular nas matérias (disciplinas) pelo SIGAA?**
O SIGAA (https://sigaa.ufpa.br) é o sistema para matrícula em turmas, notas, faltas, histórico escolar e atestado de matrícula.
Passo a passo completo para matrícula em disciplinas pelo SIGAA:
1. Acesse o SIGAA (https://sigaa.ufpa.br) com seu login e senha.
2. No menu, acesse o módulo de Matrícula.
3. Selecione as turmas ofertadas que deseja cursar, conferindo título e professor.
4. Clique em "Confirmar Matrículas" e salve o comprovante.
Se o sistema estiver instável, tente em outro horário, sempre antes do último dia do período de matrícula.
A primeira matrícula do calouro é feita pela coordenação; nas semestres seguintes, o próprio aluno faz a matrícula no SIGAA."""

c = c.replace(old_sigaa_mat, new_sigaa_mat)

# ============================================================
# FIX 3: Aproveitamento — adicionar FAQ específica de PRAZO
# (Q25 falhou porque a FAQ sobre prazo não tinha as palavras-chave "prazo para solicitar")
# ============================================================
old_aprove = """**Como funciona o processo de aproveitamento de estudos na FAMED e quais são os prazos?**
A Comissão de Aproveitamento de Estudos da FAMED analisa disciplinas cursadas em outras instituições.
Página da comissão: https://www.faculdademedicina.ufpa.br/index.php/aproveitamento-de-estudos [Verificado]
Regimento (Resolução 01/2024): https://drive.google.com/file/d/1-0WUB4DAkVLxFaXplnZrLp9J_2nsVcAF/view?usp=sharing
Prazos: as solicitações são recebidas até o 20º dia do início do semestre letivo. A primeira análise leva até 15 dias úteis e recursos até 20 dias úteis.
O resultado é despachado via SIPAC com justificativa em caso de indeferimento. O aluno pode pedir reavaliação uma única vez.
Atenção: o formulário de aproveitamento de estudos deve ser obtido no SAGITTA ou confirmado com a secretaria da FAMED."""

new_aprove = """**Como funciona o processo de aproveitamento de estudos na FAMED e quais são os prazos?**
A Comissão de Aproveitamento de Estudos da FAMED analisa disciplinas cursadas em outras instituições.
Página da comissão: https://www.faculdademedicina.ufpa.br/index.php/aproveitamento-de-estudos [Verificado]
Regimento (Resolução 01/2024): https://drive.google.com/file/d/1-0WUB4DAkVLxFaXplnZrLp9J_2nsVcAF/view?usp=sharing
O resultado é despachado via SIPAC com justificativa em caso de indeferimento. O aluno pode pedir reavaliação uma única vez.
Atenção: o formulário de aproveitamento de estudos deve ser obtido no SAGITTA ou confirmado com a secretaria da FAMED.

**Qual é o prazo para solicitar aproveitamento de estudos ou dispensa de disciplinas cursadas em outra faculdade?**
O prazo para protocolar o pedido de aproveitamento de estudos na FAMED é de até o 20º dia do início do semestre letivo, contado a partir do primeiro dia do semestre no Calendário Acadêmico da UFPA. Pedidos entregues fora desse prazo são analisados somente no semestre seguinte. A primeira análise leva até 15 dias úteis e os recursos até 20 dias úteis."""

c = c.replace(old_aprove, new_aprove)

# ============================================================
# FIX 4: CEP — Adicionar FAQ específica para "estudo clínico com pacientes"
# (Q18 trouxe chunk de inscrição do TCC em vez de CEP/Plataforma Brasil)
# ============================================================
old_cep = """**Como submeter um projeto de pesquisa com seres humanos ao Comitê de Ética (CEP)?**
A submissão é 100% online pela Plataforma Brasil (http://aplicacao.saude.gov.br/plataformabrasil/login.jsf). Não se entrega projeto impresso no CEP."""

new_cep = """**Como submeter um projeto de pesquisa com seres humanos ao Comitê de Ética (CEP)? Meu TCC é um estudo clínico com pacientes, onde submeto ao CEP?**
Projetos com seres humanos (estudos clínicos, observacionais, com entrevistas, dados de prontuário, etc.) precisam de aprovação do CEP antes de iniciar a coleta.
A submissão é 100% online pela Plataforma Brasil (http://aplicacao.saude.gov.br/plataformabrasil/login.jsf). Não se entrega projeto impresso no CEP."""

c = c.replace(old_cep, new_cep)

open(path, "w", encoding="utf-8").write(c)

# ============================================================
# FIX 5: TCC em dupla — corrigir o "Sim" que contradiz a regra
# (Q16: O modelo disse "Sim" e depois "mesmo semestre obrigatório")
# ============================================================
path2 = os.path.join(BASE, "tcc_normas.md")
c2 = open(path2, encoding="utf-8").read()

old_dupla = """### Autoria e TCC em Dupla
**É permitido fazer o Trabalho de Conclusão de Curso (TCC) em dupla na FAMED? Quais são as condições?**
Sim. Segundo o regulamento, é permitida a autoria de até dois discentes (em dupla) por TCC. A condição exigida é que ambos os discentes sejam obrigatoriamente do mesmo semestre no ato da inscrição do trabalho no SAGITTA/LAEPE."""

new_dupla = """### Autoria e TCC em Dupla
**É permitido fazer o TCC em dupla com um colega de outro semestre?**
Não. Embora o regulamento permita TCC com até dois discentes (em dupla), a condição obrigatória é que ambos estejam no mesmo semestre no ato da inscrição. Portanto, não é permitido fazer TCC em dupla com colegas de semestres diferentes.

**É permitido fazer o Trabalho de Conclusão de Curso (TCC) em dupla na FAMED? Quais são as condições?**
É permitida a autoria de até dois discentes (em dupla) por TCC, desde que ambos sejam obrigatoriamente do mesmo semestre no ato da inscrição do trabalho no SAGITTA/LAEPE. Duplas de semestres diferentes não são permitidas."""

c2 = c2.replace(old_dupla, new_dupla)
open(path2, "w", encoding="utf-8").write(c2)

# ============================================================
# FIX 6: LIBRAS para veterano — o retrieval falhou pois a FAQ
# estava num chunk grande de inovações. Adicionamos FAQ isolada.
# ============================================================
path3 = os.path.join(BASE, "ppc_medicina_2025.md")
c3 = open(path3, encoding="utf-8").read()

old_libras = """### LIBRAS e Inovações Curriculares (Componentes Obrigatórios)
**A matéria de Libras (Língua Brasileira de Sinais) é obrigatória ou optativa?**
**Quais disciplinas tornaram-se obrigatórias e quais são as inovações curriculares do PPC 2025?**
O PPC 2025 introduziu inovações curriculares significativas:
- LIBRAS (Língua Brasileira de Sinais): A obrigatoriedade depende do ano de ingresso. LIBRAS é obrigatória para calouros (ingressantes a partir de 2025). Para veteranos (ingressantes até 2024), LIBRAS continua sendo uma disciplina optativa."""

new_libras = """### LIBRAS — Obrigatória ou Optativa?
**A matéria de Libras (Língua Brasileira de Sinais) é obrigatória ou optativa? Aluno que entrou em 2022 é obrigado a fazer LIBRAS?**
A obrigatoriedade de LIBRAS depende do ano de ingresso do aluno:
- Calouros (ingressantes a partir de 2025, PPC 2025): LIBRAS é disciplina obrigatória.
- Veteranos (ingressantes até 2024, currículo anterior): LIBRAS continua sendo disciplina optativa. Alunos que ingressaram em 2022, 2023 ou 2024 não são obrigados a cursar LIBRAS.

### Inovações Curriculares do PPC 2025
**Quais disciplinas tornaram-se obrigatórias e quais são as inovações curriculares do PPC 2025?**
O PPC 2025 introduziu inovações curriculares significativas para os calouros (ingressantes a partir de 2025):
- LIBRAS (Língua Brasileira de Sinais): passou de optativa para disciplina obrigatória (somente PPC 2025)."""

c3 = c3.replace(old_libras, new_libras)
open(path3, "w", encoding="utf-8").write(c3)

print("Todas as correções aplicadas com sucesso!")
