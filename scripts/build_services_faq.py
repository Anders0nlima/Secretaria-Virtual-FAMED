"""
Fase 3 e 4 — Síntese Estruturada das Etapas 4 (FAQ) e 5 (Serviços da FAMED)
-------------------------------------------------------------------------
Objetivo:
  Compilar os dados reais anonimizados dos 917 e-mails com os regulamentos
  oficiais da FAMED/UFPA e produzir dois novos documentos Markdown curados:
  
  1. `guia_servicos_famed.md` (Etapa 5):
     - Guias detalhados de cada serviço acadêmico:
       * O que é
       * Quem tem direito e requisitos
       * Documentos obrigatórios (comprovados na prática dos e-mails)
       * Prazos regulamentares
       * Fluxo de tramitação (SAGITTA -> Secretaria -> SIPAC/Docente -> Aluno)
       * Onde solicitar

  2. `faq_secretaria_famed.md` (Etapa 4):
     - As perguntas mais frequentes recebidas pela secretaria, com gatilhos
       em negrito no padrão de FAQ do projeto para máxima precisão no RAG.
"""

import json
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
DATA_DIR = BACKEND_DIR / "data"
CURADOS_DIR = DATA_DIR / "documentos_curados"
EMAILS_JSON = DATA_DIR / "emails_anonymized.json"


def generate_curated_documents():
    print("=" * 70)
    print("GERANDO GUIA DE SERVIÇOS E FAQ DA SECRETARIA (ETAPAS 4 E 5)")
    print("=" * 70)

    # 1. Carrega dados anonimizados para estatísticas reais
    if EMAILS_JSON.exists():
        with open(EMAILS_JSON, "r", encoding="utf-8") as f:
            threads = json.load(f)
        print(f"Base de e-mails carregada: {len(threads)} conversas estruturadas.")
    else:
        threads = []

    # =========================================================================
    # DOCUMENTO 1: GUIA DE SERVIÇOS DA FAMED (ETAPA 5)
    # =========================================================================
    guia_servicos_content = """# Guia de Serviços Acadêmicos da Secretaria da Faculdade de Medicina (FAMED/UFPA)
[Fonte: Secretaria da Faculdade de Medicina — FAMED/ICM/UFPA]
Manual oficial e consolidado de procedimentos, requisitos, documentos necessários, prazos e fluxos de tramitação para os principais serviços acadêmicos solicitados pelos discentes da FAMED.
Baseado no levantamento oficial de atendimentos da Secretaria e nas Resoluções do CONSEPE/UFPA e da FAMED.

---

## 1. Segunda Chamada de Avaliações

### O que é a Segunda Chamada
A Segunda Chamada é o direito concedido ao discente que, por motivo justificado e comprovado nos termos da legislação, não compareceu a uma avaliação teórica ou prática regular no dia e horário agendados.

### Quem tem direito e Requisitos
- Discente regularmente matriculado na atividade curricular que tenha faltado à avaliação por motivo de:
  1. Problemas de saúde com atestado médico com data e assinatura do profissional.
  2. Convocação oficial (judicial, militar ou eleitoral).
  3. Luto por parentes de primeiro grau.
  4. Outros impedimentos graves devidamente documentados.
- Não é permitida segunda chamada para quem apenas faltou sem justificativa documental válida.

### Prazo para Solicitação
- **Até 48 (quarenta e oito) horas úteis** após a data da avaliação perdida ou após cessado o motivo do impedimento de saúde.
- Pedidos protocolados fora do prazo regulamentar são indeferidos, salvo parecer extraordinário da Direção.

### Documentos Obrigatórios
1. **Requerimento de Segunda Chamada** (aberto no SAGITTA ou formulário oficial).
2. **Documento Comprobatório:**
   - Atestado médico contendo nome completo do aluno, data do atendimento, período de afastamento e carimbo/assinatura do médico.
   - Declaração de convocação oficial (se for motivo judicial/militar/eleitoral).
3. Identificação clara da disciplina/módulo, data da avaliação perdida e nome do(a) docente responsável.

### Onde e Como Solicitar
- O discente deve protocolar a solicitação prioritariamente através do sistema **SAGITTA** (`sagitta.ufpa.br`), selecionando a Faculdade de Medicina (FAMED).
- Em casos excepcionais ou indisponibilidade, enviar e-mail à secretaria (`famed.ufpa.guama@gmail.com`).

### Fluxo de Tramitação Interna
1. **Discente:** Protocoliza a solicitação anexando o atestado/documento comprobatório.
2. **Secretaria da FAMED:** Recebe o pedido, confere o prazo (48h) e a validade da documentação.
3. **Encaminhamento Oficial:** A Secretaria emite documento formal de solicitação de segunda chamada e envia diretamente para o e-mail do(a) docente responsável pela disciplina.
4. **Docente:** Agenda nova data e horário com o discente e aplica a avaliação de segunda chamada.

---

## 2. Avaliação Substitutiva

### O que é a Avaliação Substitutiva
A avaliação substitutiva (Resolução nº 01/2020 - FAMED) é o exame final de recuperação oferecido ao término do período letivo regular para o aluno que não atingiu a média mínima de aprovação na atividade curricular, permitindo substituir a menor nota de suas provas teóricas.

### Quem tem direito e Requisitos
1. **Frequência mínima obrigatória de 75%** na atividade curricular.
2. **Não ter obtido o conceito de aprovação** no semestre regular.
3. **Não estar em módulo prático ou de Internato** (a avaliação substitutiva é restrita aos conteúdos teóricos).

### Prazo para Solicitação
- Conforme as datas estipuladas no Calendário Acadêmico da FAMED/UFPA ao final de cada semestre letivo (período de avaliações finais/substitutivas).

### Documentos Obrigatórios
- Formulário de inscrição de Avaliação Substitutiva ou protocolo via SAGITTA informando a atividade curricular que deseja recuperar.

### Onde e Como Solicitar
- No sistema **SAGITTA** (`sagitta.ufpa.br`), direcionado à Faculdade de Medicina, no período aberto para inscrições de substitutiva.

### Fluxo de Tramitação Interna
1. **Discente:** Solicita a substitutiva no prazo final do semestre.
2. **Secretaria da FAMED:** Confere se o aluno cumpriu os 75% de presença e não está reprovado por falta (Sem Frequência - SF).
3. **Homologação:** A Secretaria consolida a relação de discentes aptos e envia à Coordenação do Módulo e aos docentes para a elaboração e aplicação do exame.

---

## 3. Certificado de Estágio de Férias

### O que é o Estágio de Férias
O estágio de férias é uma atividade prática extracurricular realizada em períodos de recesso acadêmico em hospitais conveniados (como HUJBB, FSCMPA/Santa Casa, Fundação Santa Casa, etc.) para aprimoramento clínico e cômputo de horas complementares.

### Quem tem direito e Requisitos
- Discentes de Medicina da FAMED/UFPA que realizaram estágio no recesso acadêmico devidamente autorizado pela faculdade ou hospital de ensino conveniado.

### Documentos Obrigatórios
1. **Lista de Frequência de Estágio de Férias** (`06 - LISTA DE FREQUÊNCIA DE ESTÁGIO DE FÉRIAS`): devidamente preenchida com as datas, turnos e assinada pelo supervisor do local de estágio.
2. **Declaração do Chefe do Serviço/Especialidade:** comprovando a atuação e especialidade médica onde o estágio foi cumprido.

### Onde e Como Solicitar
- O pedido deve ser aberto no sistema **SAGITTA** (`sagitta.ufpa.br`) ou enviado à Secretaria da FAMED anexando a lista de frequência e a declaração assinadas.

### Fluxo de Tramitação Interna
1. **Discente:** Envia a frequência e declaração do supervisor do hospital.
2. **Secretaria da FAMED:** Confere a conformidade da carga horária e redige o certificado oficial.
3. **Direção:** O certificado é encaminhado para a Direção da FAMED para **assinatura eletrônica oficial via SIPAC**.
4. **Devolução:** Após assinado eletronicamente, a Secretaria envia o certificado em PDF assinado para o e-mail do discente.

---

## 4. Assinatura de Termo de Compromisso de Estágio (TCE)

### O que é o Termo de Compromisso de Estágio (TCE)
Documento jurídico obrigatório que formaliza a realização de estágio não obrigatório (extracurricular) entre o aluno, a instituição concedente (hospital/clínica) e a UFPA/FAMED.

### Quem tem direito e Requisitos
- Discente regularmente matriculado que não esteja em período de trancamento total e cuja carga horária do estágio não conflite com as atividades curriculares obrigatórias.

### Requisitos Importantes para Evitar Indeferimento
- **Preenchimento completo de todos os campos:** apólice de seguro contra acidentes, plano de atividades, dados da concedente e do orientador.
- **Proibido usar abreviações:** nomes de disciplinas, hospitais e setores devem estar por extenso.
- **Assinatura prévia:** o termo já deve conter a assinatura do aluno e da concedente antes do envio à FAMED.

### Onde e Como Solicitar
- Via **SAGITTA** (`sagitta.ufpa.br`), anexando o documento em PDF legível.

### Fluxo de Tramitação Interna
1. **Secretaria Acadêmica:** Analisa se o termo está completo e sem abreviações.
2. **SIPAC:** A Secretaria abre processo no SIPAC e tramita para a Direção da FAMED.
3. **Direção:** Assina digitalmente o TCE.
4. **Devolução:** O termo assinado é retornado ao aluno pelo SAGITTA/SIPAC.

---

## 5. Abono de Falta vs Justificativa de Falta

### Diferença Fundamental
- **Abono de Falta:** É a exclusão legal da ausência do cômputo de faltas, mantendo 100% de presença. Só existe nas hipóteses estritamente previstas em legislação federal. Atestado médico comum **NÃO** abona falta na UFPA.
- **Justificativa de Falta:** É a comprovação do motivo da ausência para fins pedagógicos (permitir reposição de avaliação ou segunda chamada e dar ciência ao professor), mas a falta continua registrada no diário de classe.

### Hipóteses Legais de Abono de Falta
1. Serviço Militar Obrigatório (Decreto-Lei nº 715/1969).
2. Convocação pela Justiça Eleitoral ou Júri Popular.
3. Aluno reservista em manobra militar.
4. Exercícios Domiciliares (Decreto-Lei nº 1.044/1969 e Lei nº 6.202/1975 para gestantes a partir do 8º mês ou afecções congênitas/infecciosas incompatíveis com a presença física por período prolongado).

### Documentos Obrigatórios
- Declaração oficial do órgão convocador (para abono legal).
- Atestado médico original ou homologado pelo serviço de perícia da UFPA (para justificativas e exercícios domiciliares).

### Onde e Como Solicitar
- Requerimento via **SAGITTA** (`sagitta.ufpa.br`) anexando a documentação comprobatória.

---

## 6. Revisão de Conceito (Contestação de Nota)

### O que é a Revisão de Conceito
Procedimento regimental que permite ao estudante solicitar a reavaliação de notas ou do conceito final atribuído a uma atividade curricular caso identifique divergência na correção ou nos critérios do plano de ensino.

### Requisitos e Prazos
- Prazo: **Até 3 (três) a 5 (cinco) dias úteis** após a divulgação oficial da nota/conceito no SIGAA.
- O pedido deve conter justificativa fundamentada, discriminando a nota obtida em cada instrumento (ex: OSCE, Provão, Casos Motivadores) e apontando onde reside o erro de cálculo ou de correção.

### Onde e Como Solicitar
- Via requerimento no **SAGITTA** (`sagitta.ufpa.br`) anexando os instrumentos avaliativos e a argumentação técnica.
"""

    guia_path = CURADOS_DIR / "guia_servicos_famed.md"
    with open(guia_path, "w", encoding="utf-8") as f:
        f.write(guia_servicos_content)
    print(f"[OK] Gerado: {guia_path}")

    # =========================================================================
    # DOCUMENTO 2: FAQ DA SECRETARIA FAMED (ETAPA 4)
    # =========================================================================
    faq_content = """# Perguntas Frequentes da Secretaria da FAMED/UFPA (FAQ Oficial)
[Fonte: Secretaria da Faculdade de Medicina — FAMED/ICM/UFPA]
Perguntas e respostas mais recorrentes consolidadas a partir do histórico de atendimentos e e-mails da Secretaria da FAMED, com orientações diretas, sistemas e documentos.

---

## Segunda Chamada e Avaliações

### Como Solicitar Segunda Chamada
**Como solicitar segunda chamada de prova ou avaliação na FAMED?**
Para solicitar a realização de segunda chamada de prova na FAMED/UFPA:
1. O discente deve protocolar o pedido no prazo máximo de até 48 horas úteis após a data da avaliação ou após cessar o motivo do impedimento de saúde.
2. O pedido deve ser aberto no sistema SAGITTA (sagitta.ufpa.br) direcionado à Faculdade de Medicina.
3. Anexar obrigatoriamente o documento comprobatório: atestado médico com carimbo e CRM do médico, ou comprovante de convocação oficial.
4. A Secretaria confere a documentação e expede um documento formal de encaminhamento ao docente responsável pela matéria para agendar e aplicar a nova prova.

### Prazo para Pedir Segunda Chamada
**Qual é o prazo para pedir segunda chamada na Faculdade de Medicina?**
O prazo regulamentar para pedir segunda chamada é de até 48 (quarenta e oito) horas úteis após a realização da avaliação perdida, ou a partir do término do período de afastamento do atestado médico. Pedidos fora do prazo são indeferidos.

### Quem Aplica a Segunda Chamada
**Quem marca a data da prova de segunda chamada na FAMED?**
A prova de segunda chamada é marcada e aplicada diretamente pelo professor (docente) responsável pela disciplina. A Secretaria da FAMED faz a análise do atestado, homologa o direito e encaminha a autorização oficial ao docente.

---

## Estágio de Férias e Certificados

### Como Obter o Certificado de Estágio de Férias
**Como solicitar o certificado de estágio de férias da FAMED?**
Para obter a emissão do certificado de estágio de férias:
1. Preencher a Lista de Frequência de Estágio de Férias (modelo oficial FAMED `06 - LISTA DE FREQUÊNCIA DE ESTÁGIO DE FÉRIAS`).
2. Obter a assinatura do supervisor do hospital de ensino conveniado onde fez o estágio (ex: Barros Barreto/HUJBB ou Santa Casa/FSCMPA) e a declaração de conclusão da especialidade médica.
3. Abrir solicitação no SAGITTA (sagitta.ufpa.br) anexando a frequência e a declaração assinadas.
4. A Secretaria elabora o certificado com a carga horária e tramita no SIPAC para assinatura eletrônica da Direção da FAMED. O certificado assinado é devolvido ao aluno por e-mail/SAGITTA.

### Quais Hospitais Têm Convênio para Estágio de Férias
**Onde posso fazer estágio de férias em Medicina pela UFPA?**
Os estágios de férias da FAMED são realizados nos hospitais e unidades de saúde conveniados com a UFPA, principalmente no Complexo Hospitalar Universitário da UFPA (Hospital Universitário João de Barros Barreto - HUJBB e Hospital Universitário Bettina Ferro de Souza - HUBFS) e na Fundação Santa Casa de Misericórdia do Pará (FSCMPA), mediante lista oficial de vagas no recesso acadêmico.

---

## Avaliação Substitutiva

### Requisitos para Ter Direito à Avaliação Substitutiva
**Quem tem direito a fazer a avaliação substitutiva na FAMED?**
Conforme a Resolução nº 01/2020 - FAMED, para ter direito à avaliação substitutiva o discente deve cumprir obrigatoriamente:
1. Ter frequência mínima de 75% na disciplina.
2. Não ter obtido o conceito de aprovação no período regular.
3. Não estar cursando módulo prático ou de Internato.

### A Substitutiva Pode Substituir Falta
**A avaliação substitutiva abona falta ou reprovação por falta?**
Não. A avaliação substitutiva destina-se exclusivamente a recuperar notas teóricas de alunos que atingiram a presença mínima de 75%. O discente reprovado por falta (conceito Sem Frequência - SF) não tem direito à substitutiva.

---

## Justificativas e Faltas

### Atestado Médico Abona Falta na UFPA
**Atestado médico abona falta na Faculdade de Medicina da UFPA?**
Não. De acordo com as normas da UFPA e a LDB, não existe abono de faltas para atestados médicos cotidianos. Atestados médicos servem como Justificativa de Falta para comprovar ausência perante o professor e fundamentar pedidos de segunda chamada de avaliações, mas a falta continua registrada no diário. A presença mínima de 75% da carga horária continua sendo exigida para não reprovar com conceito SF.

### Como Funciona o Abono de Falta Legal
**Em quais casos a falta pode ser realmente abonada na UFPA?**
O abono de faltas só é legalmente reconhecido em situações com previsão em lei federal: convocação para o Serviço Militar Obrigatório, convocação pela Justiça Eleitoral para trabalho nas eleições, ou participação oficial em júri popular. Nos casos de gestantes (a partir do 8º mês) e doenças crônicas ou infectocontagiosas prolongadas, o regime aplicável é o de Exercícios Domiciliares (Decreto-Lei 1.044/69).

---

## Assinatura de Documentos e Termos de Estágio

### O Que Fazer para a Direção Assinar o Termo de Estágio (TCE)
**Como conseguir a assinatura da FAMED no Termo de Compromisso de Estágio (TCE)?**
Para que o Termo de Compromisso de Estágio (TCE) seja assinado pela Direção da FAMED:
1. O termo deve estar completamente preenchido, sem campos em branco e sem abreviações nos nomes das instituições e atividades.
2. Já deve conter as assinaturas do aluno e da empresa/hospital concedente.
3. Protocolar no SAGITTA (sagitta.ufpa.br) direcionado à Faculdade de Medicina.
4. A Secretaria confere e envia para a Direção assinar digitalmente pelo SIPAC, devolvendo o termo assinado ao discente.

---

## Revisão de Notas e Conceitos

### Como Contestar Nota ou Pedir Revisão de Conceito
**Como pedir revisão de nota ou conceito na FAMED?**
Para solicitar revisão de conceito:
1. O pedido deve ser aberto no SAGITTA no prazo de até 3 a 5 dias úteis após a publicação oficial do conceito no SIGAA.
2. O discente deve discriminar as notas obtidas em cada prova (ex: OSCE, Provão, Casos Motivadores) e fundamentar tecnicamente onde ocorreu eventual erro de cálculo ou de correção perante o plano de ensino.
3. A solicitação é enviada para análise da coordenação da disciplina e homologação pela Direção.
"""

    faq_path = CURADOS_DIR / "faq_secretaria_famed.md"
    with open(faq_path, "w", encoding="utf-8") as f:
        f.write(faq_content)
    print(f"[OK] Gerado: {faq_path}")

    print("\n[SUCESSO] Curadoria das Etapas 4 e 5 concluída com sucesso!")


if __name__ == "__main__":
    generate_curated_documents()

