"""
Módulo de integração com a Google Calendar API utilizando Service Account.
Permite consultar eventos agendados (como reuniões, defesas, horários de atendimento da secretaria)
e formatá-los para injeção contextual no pipeline RAG.
"""
import os
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Cache em memória simples para evitar chamadas de rede a cada pergunta
_cached_events_text: Optional[str] = None
_cached_at: Optional[datetime.datetime] = None
CACHE_TTL_MINUTES = 5


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


def fetch_upcoming_events(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """
    Busca os próximos eventos da agenda a partir da data/hora atual até days_ahead dias.
    """
    service = get_calendar_service()
    if not service:
        return []

    calendar_id = settings.google_calendar_id
    now = datetime.datetime.now(datetime.timezone.utc)
    time_min = now.isoformat()
    time_max = (now + datetime.timedelta(days=days_ahead)).isoformat()

    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=25,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])
    except HttpError as error:
        print(f"[GoogleCalendar] Erro na API do Google Calendar ({calendar_id}): {error}")
        return []
    except Exception as exc:
        print(f"[GoogleCalendar] Erro inesperado ao listar eventos: {exc}")
        return []


def format_events_as_context(events: List[Dict[str, Any]]) -> str:
    """
    Converte os eventos do Google Calendar em formato legível para o prompt do LLM.
    """
    if not events:
        return "[Fonte: Agenda Institucional da FAMED/UFPA (Google Agenda)]\nNenhum evento, reunião ou agendamento oficial marcado para os próximos dias na agenda institucional."

    lines = [
        "[Fonte: Agenda Institucional da FAMED/UFPA (Google Agenda)]",
        "Eventos e horários agendados oficialmente para os próximos dias:",
    ]

    for ev in events:
        # Eventos sem título são ignorados (título obrigatório para contexto útil)
        summary = (ev.get("summary") or "").strip()
        if not summary:
            continue
        start = ev.get("start", {})
        end = ev.get("end", {})
        location = ev.get("location", "")
        description = ev.get("description", "")

        # Trata data/hora (pode ser dateTime ou date para evento de dia inteiro)
        start_raw = start.get("dateTime") or start.get("date")
        end_raw = end.get("dateTime") or end.get("date")

        try:
            if "T" in str(start_raw):
                # Data e hora específica
                dt_start = datetime.datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                # Formata em horário de Brasília / local
                data_str = dt_start.strftime("%d/%m/%Y")
                hora_inicio = dt_start.strftime("%H:%M")
                if end_raw and "T" in str(end_raw):
                    dt_end = datetime.datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
                    hora_fim = dt_end.strftime("%H:%M")
                    horario_str = f"{data_str}, das {hora_inicio} às {hora_fim}"
                else:
                    horario_str = f"{data_str} às {hora_inicio}"
            else:
                # Dia inteiro (YYYY-MM-DD)
                dt_start = datetime.date.fromisoformat(start_raw)
                horario_str = f"{dt_start.strftime('%d/%m/%Y')} (Dia inteiro)"
        except Exception:
            horario_str = str(start_raw)

        item = f"- {horario_str}: {summary}"
        if location:
            item += f" | Local: {location}"
        if description:
            # Resumo simples da descrição para não poluir
            desc_clean = description.strip().replace("\n", " ")
            if len(desc_clean) > 120:
                desc_clean = desc_clean[:120] + "..."
            item += f" | Detalhes: {desc_clean}"

        lines.append(item)

    return "\n".join(lines)


def get_calendar_context(force_refresh: bool = False) -> str:
    """
    Retorna o contexto textual dos próximos eventos com cache de 5 minutos.
    """
    global _cached_events_text, _cached_at

    now = datetime.datetime.now()
    if (
        not force_refresh
        and _cached_events_text is not None
        and _cached_at is not None
        and (now - _cached_at).total_seconds() < (CACHE_TTL_MINUTES * 60)
    ):
        return _cached_events_text

    events = fetch_upcoming_events(days_ahead=settings.google_calendar_days_ahead)
    _cached_events_text = format_events_as_context(events)
    _cached_at = now
    return _cached_events_text

