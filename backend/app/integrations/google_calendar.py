"""
Módulo de integração com a Google Calendar API utilizando Service Account.
Permite consultar eventos agendados (como reuniões, defesas, horários de atendimento da secretaria)
e formatá-los para injeção contextual no pipeline RAG.
"""
import os
import datetime
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Fuso horário oficial de Belém / Pará (UTC-3 fixo o ano inteiro)
BELEM_TZ = datetime.timezone(datetime.timedelta(hours=-3))

# Cache em memória simples para evitar chamadas de rede a cada pergunta
_cached_raw_events: Optional[List[Dict[str, Any]]] = None
_cached_at: Optional[datetime.datetime] = None
CACHE_TTL_MINUTES = 5

STOPWORDS = {
    "onde", "esta", "está", "sendo", "aula", "aulas", "da", "de", "do", "das", "dos",
    "o", "a", "os", "as", "e", "em", "na", "no", "nas", "nos", "para", "por", "com",
    "prof", "professor", "professora", "profa", "profo", "docente", "docentes", "quem",
    "qual", "quais", "que", "horas", "hora", "quando", "comeca", "começa", "termina",
    "fim", "inicio", "início", "acontece", "ocorre", "vai", "ser", "ter", "tem", "hoje",
    "amanha", "amanhã", "ontem", "agora", "marcado", "marcada", "agendado", "agendada",
    "programado", "programada", "evento", "eventos", "atendimento", "secretaria",
    "sala", "salas", "dando", "dar", "dia", "dias", "sobre", "fazer", "saber", "pode", "dizer",
    "me", "uma", "um", "uns", "umas", "agenda", "agendas", "prova", "provas", "exame",
    "exames", "atividade", "atividades", "coisa", "coisas", "acontecendo", "horario", "horário"
}


def extract_query_entities(query: str) -> List[str]:
    """Extrai entidades principais (nomes de pessoas, matérias, códigos) da pergunta."""
    words = re.findall(r"[a-zA-Z0-9áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]+", (query or "").lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def extract_date_filter(query: str, today: datetime.date) -> Optional[str]:
    """Detecta se a pergunta solicita uma data específica (hoje, amanhã ou DD/MM)."""
    q_low = (query or "").lower()
    if "hoje" in q_low or "agora" in q_low:
        return today.strftime("%d/%m/%Y")
    if "amanhã" in q_low or "amanha" in q_low:
        return (today + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
    match = re.search(r"\b(\d{1,2})[/\.](\d{1,2})\b", q_low)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        return f"{day:02d}/{month:02d}/{today.year}"
    return None


def extract_room_filter(query: str) -> Optional[str]:
    """Detecta se a pergunta especifica uma sala ou auditório."""
    q_low = (query or "").lower()
    m = re.search(r"\bsala\s*(\d{1,2})\b", q_low)
    if m:
        return f"SALA {int(m.group(1)):02d}"
    if "auditório" in q_low or "auditorio" in q_low:
        return "AUDITÓRIO"
    if "simulação" in q_low or "simulacao" in q_low:
        return "SALA DE SIMULAÇÃO"
    return None


def _clean_calendar_name(name: str) -> str:
    """Remove anotações internas entre parênteses dos nomes de salas/recursos.
    Ex: 'SALA 08 (molhando piso)' -> 'SALA 08'
    """
    return re.sub(r"\s*\(.*?\)", "", name).strip()


def _strip_html(text: str) -> str:
    """Remove quebras de linha brutas, tags HTML e converte entidades comuns para texto limpo."""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&[a-z]+;", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _clean_summary(s: str) -> str:
    """Remove ruídos comuns nos títulos da secretaria e normaliza abreviações acadêmicas."""
    s = s.replace("\r", " ").replace("\n", " ")
    s = re.sub(r"^as?\s+\d+[:h\d\w]*\s*\([^\)]*\)\s*[-–]?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\([^\)]+\)\s*", "", s)
    s = re.sub(r"\bprof[ªa]\b\.?", "Professora", s, flags=re.IGNORECASE)
    s = re.sub(r"\bprof[ºo]?\b\.?", "Professor", s, flags=re.IGNORECASE)
    s = re.sub(r"\bM[ªa]\b\.?", "Maria", s)
    s = re.sub(r"\bped\b\.?", "Pediatria", s, flags=re.IGNORECASE)
    s = re.sub(r"\bmed\b\.?", "Medicina", s, flags=re.IGNORECASE)
    s = re.sub(r"\bsist?\b\.?", "Sistema", s, flags=re.IGNORECASE)
    s = re.sub(r"\burg\.\s*emer\b\.?", "Urgência e Emergência", s, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", s).strip()


def _clean_description(desc: str) -> str:
    """Limpa detalhes de eventos, removendo HTML, códigos de reserva e normalizando títulos."""
    if not desc:
        return ""
    text = _strip_html(desc)
    text = re.sub(r"(?:código|codigo):?\s*\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{6,}\b", "", text)
    text = re.sub(r"\bprof[ªa]\b\.?", "Professora", text, flags=re.IGNORECASE)
    text = re.sub(r"\bprof[ºo]?\b\.?", "Professor", text, flags=re.IGNORECASE)
    text = re.sub(r"\bM[ªa]\b\.?", "Maria", text)
    text = re.sub(r"\bped\b\.?", "Pediatria", text, flags=re.IGNORECASE)
    text = re.sub(r"^[-,\\s:|]+", "", text).strip()
    text = re.sub(r"[-,\\s:|]+$", "", text).strip()
    if len(text) < 4:
        return ""
    if len(text) > 100:
        text = text[:100] + "..."
    return text


def get_calendar_service():
    """Autentica e retorna o serviço da Google Calendar API via Service Account."""
    creds_path = Path(settings.google_credentials_path)
    if not creds_path.is_absolute():
        from app.config import BASE_DIR
        creds_path = BASE_DIR / creds_path

    if not creds_path.exists():
        print(f"[GoogleCalendar] Arquivo de credenciais não encontrado em: {creds_path}")
        return None

    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(creds_path), scopes=SCOPES
        )
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        return service
    except Exception as e:
        print(f"[GoogleCalendar] Erro ao autenticar com Service Account: {e}")
        return None


def get_calendar_ids() -> List[str]:
    """
    Retorna a lista de IDs de agenda configurados no .env.
    Aceita um único ID ou vários separados por vírgula.
    """
    raw = settings.google_calendar_id or ""
    return [cid.strip() for cid in raw.split(",") if cid.strip()]


def _event_sort_key(ev: Dict[str, Any]) -> str:
    start = ev.get("start", {})
    return str(start.get("dateTime") or start.get("date") or "")


def fetch_upcoming_events(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """
    Busca todos os eventos desde o início do dia de hoje (00:00:00 no fuso de Belém)
    até days_ahead dias à frente, garantindo que eventos ocorridos pela manhã continuem visíveis
    para consultas realizadas à tarde ou à noite.
    """
    service = get_calendar_service()
    if not service:
        return []

    now_belem = datetime.datetime.now(BELEM_TZ)
    # Começa sempre a partir da meia-noite (00:00:00) de hoje no fuso de Belém
    today_start = datetime.datetime.combine(now_belem.date(), datetime.time.min).replace(tzinfo=BELEM_TZ)
    time_min = today_start.isoformat()
    time_max = (today_start + datetime.timedelta(days=days_ahead)).isoformat()

    all_events: List[Dict[str, Any]] = []
    for calendar_id in get_calendar_ids():
        try:
            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    timeZone="America/Belem",
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            calendar_name = events_result.get("summary") or calendar_id
            for ev in events_result.get("items", []):
                ev["_calendar_name"] = _clean_calendar_name(calendar_name)
                all_events.append(ev)
        except HttpError as error:
            print(f"[GoogleCalendar] Erro na API do Google Calendar ({calendar_id}): {error}")
        except Exception as exc:
            print(f"[GoogleCalendar] Erro inesperado ao listar eventos ({calendar_id}): {exc}")

    all_events.sort(key=_event_sort_key)
    return all_events  # Retorna todos os eventos das salas no intervalo


def _format_datetime(start_raw: Any, end_raw: Any) -> Tuple[str, str]:
    """Formata data e horário garantindo conversão precisa para o fuso de Belém (UTC-3)."""
    try:
        if "T" in str(start_raw):
            dt_start = datetime.datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
            if dt_start.tzinfo is not None:
                dt_start = dt_start.astimezone(BELEM_TZ)
            data_str = dt_start.strftime("%d/%m/%Y")
            hora_inicio = dt_start.strftime("%H:%M")

            if end_raw and "T" in str(end_raw):
                dt_end = datetime.datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
                if dt_end.tzinfo is not None:
                    dt_end = dt_end.astimezone(BELEM_TZ)
                hora_fim = dt_end.strftime("%H:%M")
                horario_str = f"das {hora_inicio} às {hora_fim}"
            else:
                horario_str = f"às {hora_inicio}"
        else:
            dt_start = datetime.date.fromisoformat(str(start_raw))
            data_str = dt_start.strftime("%d/%m/%Y")
            horario_str = "Dia inteiro"
    except Exception:
        data_str = str(start_raw)
        horario_str = ""
    return data_str, horario_str


def format_events_as_context(events: List[Dict[str, Any]], query: Optional[str] = None) -> str:
    """
    Converte os eventos do Google Calendar em formato textual para o LLM.
    Filtra de forma inteligente por:
    - Data solicitada (ex.: 'hoje', 'amanhã', '15/10')
    - Sala solicitada (ex.: 'Sala 11', 'Auditório')
    - Entidades/nomes (ex.: 'Lucas Lobato', 'Akira', 'Kellen Freitas', 'HM3')
    Evita sobrecarregar o modelo com salas e datas irrelevantes à pergunta.
    """
    if not events:
        return "[Fonte: Agenda Institucional da FAMED/UFPA (Google Agenda)]\nNenhum evento, reunião ou agendamento oficial marcado para os próximos dias na agenda institucional."

    now_belem = datetime.datetime.now(BELEM_TZ)
    today = now_belem.date()
    today_str = today.strftime("%d/%m/%Y")
    tomorrow_str = (today + datetime.timedelta(days=1)).strftime("%d/%m/%Y")

    q_text = query or ""
    date_filter = extract_date_filter(q_text, today)
    room_filter = extract_room_filter(q_text)
    entities = extract_query_entities(q_text)

    # Coleta e pontua eventos relevantes
    scored_events = []
    for ev in events:
        summary = (ev.get("summary") or "").strip()
        if not summary:
            continue
        clean_sum = _clean_summary(summary)
        room = ev.get("_calendar_name") or ""
        desc = _clean_description(ev.get("description") or "")
        start_raw = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
        end_raw = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
        data_str, horario_str = _format_datetime(start_raw, end_raw)

        # 1. Filtro estrito de data se o usuário perguntou sobre um dia específico
        if date_filter and data_str != date_filter:
            continue

        # 2. Filtro estrito de sala se o usuário perguntou sobre uma sala específica
        if room_filter:
            norm_rf = room_filter.lower().replace("sala 0", "sala ")
            norm_room = room.lower().replace("sala 0", "sala ")
            if norm_rf not in norm_room:
                continue

        # 3. Pontuação por entidades/docentes/matérias
        full_text = f"{clean_sum} {room} {desc}".lower()
        score = 0

        if entities:
            # Frase completa de busca
            query_phrase = " ".join(entities).lower()
            if len(entities) > 1 and query_phrase in full_text:
                score += 25
            # Pares consecutivos (ex: "kellen freitas", "lucas lobato", "saul rassy")
            for i in range(len(entities) - 1):
                pair = f"{entities[i]} {entities[i+1]}"
                if pair in full_text:
                    score += 20
            # Palavras individuais
            for ent in entities:
                if ent in full_text:
                    score += 3

            if score >= 3:
                scored_events.append((score, data_str, horario_str, room, clean_sum, desc))
        else:
            # Sem entidades específicas (ex: "o que tem hoje?", "o que tem no dia 15/10?")
            scored_events.append((1, data_str, horario_str, room, clean_sum, desc))

    # Se há correspondências por frase/nome próprio forte, mantém apenas o topo
    if entities and scored_events:
        max_score = max(s for s, *_ in scored_events)
        if max_score >= 20:
            scored_events = [x for x in scored_events if x[0] >= 20]
        else:
            scored_events.sort(key=lambda x: x[0], reverse=True)
            scored_events = scored_events[:10]

    # Formatação do resultado para o LLM
    lines = [
        "[Fonte: Agenda Institucional da FAMED/UFPA (Google Agenda)]",
        f"Data de hoje: {today_str}",
        "",
    ]

    if date_filter:
        tag_header = " (HOJE)" if date_filter == today_str else (" (AMANHÃ)" if date_filter == tomorrow_str else "")
        lines.append(f"=== Atividades para o dia {date_filter}{tag_header} ===")
    elif entities:
        lines.append("=== Atividades encontradas para a sua busca na agenda ===")
    else:
        lines.append("=== Próximas atividades agendadas ===")

    if not scored_events:
        lines.append("Nenhuma atividade encontrada para os critérios informados.")
        return "\n".join(lines).strip()

    for _, d_str, h_str, room, clean_sum, desc in scored_events[:20]:
        tag_dia = " (HOJE)" if d_str == today_str else (" (AMANHÃ)" if d_str == tomorrow_str else "")
        room_tag = f"[{room}] " if room else ""
        item = f"- Data: {d_str}{tag_dia} | {room_tag}{h_str}: {clean_sum}"
        if desc:
            item += f" | Detalhes: {desc}"
        lines.append(item)

    return "\n".join(lines).strip()


def get_calendar_context(query: Optional[str] = None, force_refresh: bool = False) -> str:
    """
    Retorna o contexto textual dos próximos eventos com cache de eventos brutos de 5 minutos.
    Formata dinamicamente de acordo com a consulta informada.
    """
    global _cached_raw_events, _cached_at

    now = datetime.datetime.now()
    if (
        not force_refresh
        and _cached_raw_events is not None
        and _cached_at is not None
        and (now - _cached_at).total_seconds() < (CACHE_TTL_MINUTES * 60)
    ):
        events = _cached_raw_events
    else:
        events = fetch_upcoming_events(days_ahead=settings.google_calendar_days_ahead)
        _cached_raw_events = events
        _cached_at = now

    return format_events_as_context(events, query=query)
