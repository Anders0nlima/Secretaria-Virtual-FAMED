"""
Modulo para deteccao de intencao de busca em agendas, eventos, reunioes ou horarios dinamicos.
"""
import re

CALENDAR_PATTERNS = [
    # Terminologia direta de agenda/evento
    r"\bagenda\b",
    r"\bagendamento[s]?\b",
    r"\bagendad[ao][s]?\b",
    r"\bevento[s]?\b",
    r"\breuni[aã]o\b",
    r"\breuni[oõ]es\b",
    r"\bmarcad[ao][s]?\b",
    r"\bprograma[cç][aã]o\b",
    r"\bcompromisso[s]?\b",
    # Tipos de atividades praticas / avaliativas na agenda da FAMED
    r"\bplant[aã]o\b",
    r"\bambulat[oó]rio\b",
    r"\bconfer[eê]ncia\b",
    r"\bpalestra\b",
    r"\baula pr[aá]tica\b",
    r"\bsess[aã]o de tutoria\b",
    r"\bjornada acad[eê]mica\b",
    r"\best[aá]gio supervisionado\b",
    r"\bosce\b",
    r"\bprova pr[aá]tica\b",
    r"\bsala de simula[cç][aã]o\b",
    # Referencia a datas especificas (formatos comuns: 05/10, 07.10, dia 5, dia 06 de outubro)
    r"\b\d{1,2}[/\.]\d{1,2}\b",
    r"\bdia \d{1,2}(?: de \w+)?\b",
    # Perguntas sobre horario/tempo de eventos
    r"\bque horas\b",
    r"\bquando come[cç]a\b",
    r"\bquando termina\b",
    r"\bhor[aá]rio[s]? de atendimento\b",
    # Perguntas sobre localizacao de eventos/aulas/salas
    r"\bonde (est[aá] sendo|[eé]|vai ser|fica|est[aá]|ser[aá]|ocorre|vai ocorrer|acontece|vai acontecer|vai ter|tem|tendo)\b",
    r"\bonde\b.*?\b(aula|prof|professor|professora|prova|reuni[aã]o|evento)\b",
    r"\b(qual|em qual|que|em que) sala\b",
    r"\bsala\s+\d+\b",
    r"\bsala (do|da|de|dos|das)\b",
    r"\bno audit[oó]rio\b",
    r"\bquem est[aá] usando\b",
    # Aulas vinculadas a docentes ou datas imediatas
    r"\baula d[eoa] (prof|professor|professora)\b",
    r"\b(prof|professor|professora) .*\baula\b",
    r"\baula[s]?\b.*?\b(hoje|amanh[aã])\b",
    r"\b(hoje|amanh[aã])\b.*?\baula[s]?\b",
    r"\b(o que|qual atividade|quais atividades)\b.*?\b(hoje|amanh[aã])\b",
    r"\b(tem|vai ter|est[aá] tendo)\b.*?\b(hoje|amanh[aã])\b",
    # Perguntas sobre conteudo/material de eventos
    r"\bpreciso levar\b",
    r"\bo que (devo|preciso) levar\b",
    r"\bmaterial (necess[aá]rio|obrigat[oó]rio)\b",
    r"\bequipamento\b",
    r"\bvestiment[a]?\b",
    r"\broupa[s]? (obrigat[oó]ria|necess[aá]ria)\b",
    r"\bpijama cir[uú]rgico\b",
    r"\bscrub\b",
    # Perguntas sobre tema/objetivo de sessoes agendadas
    r"\btema .*(sess[aã]o|aula|evento|tutoria|reuni[aã]o|palestra|confer[eê]ncia)",
    r"\bobjetivo .*(sess[aã]o|aula|evento|tutoria|reuni[aã]o)",
    # Periodo do dia com atividade marcada
    r"\bper[ií]odo da (manh[aã]|tarde|noite)\b",
    r"\bessa semana\b",
    r"\besta semana\b",
    r"\bsemana que vem\b",
    r"\bpr[oó]xima semana\b",
    r"\bhoje tem\b",
    r"\bamanh[aã] tem\b",
    r"\bpr[oó]xim[ao][s]? evento[s]?\b",
    # Atividade marcada/agendada
    r"\batividade[s]? (marcada[s]?|agendada[s]?|pr[aá]tica[s]?)\b",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CALENDAR_PATTERNS]


def is_calendar_query(question: str) -> bool:
    """
    Retorna True se a pergunta do usuario indicar interesse em eventos,
    reunioes, horarios de atendimento ou programacao da agenda.
    """
    if not question:
        return False
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(question):
            return True
    return False
