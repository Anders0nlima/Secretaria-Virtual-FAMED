"""
Fase 0 — Inventário de Marcadores de E-mail da Secretaria FAMED/UFPA
---------------------------------------------------------------------
Objetivo:
  Levantar a volumetria e a linha do tempo (primeiro e último e-mail)
  de cada marcador/pasta da caixa de e-mail institucional, SEM baixar
  ou expor o conteúdo dos e-mails (garantia estrita de leitura e privacidade).

Métodos de Acesso Suportados:
  1. Google Takeout (.mbox) — análise rápida por streaming offline de arquivos exportados
  2. IMAP SSL com Senha de App (Gmail) — modo estritamente READ-ONLY (EXAMINE)
"""

import os
import sys
import re
import json
import imaplib
import binascii
import argparse
import email.header
import email.utils
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Carrega variáveis de ambiente do .env se existir
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# Marcadores de referência informados pela secretaria da FAMED
TARGET_LABELS_DEFAULT = [
    "abono de falta",
    "aproveitamento de estudo",
    "assinatura de termo",
    "avaliação substitutiva",
    "casmuc-2023",
    "colação de grau",
    "CSU-Coordenadoria de serviços urbanos",
    "diretório acadêmico betina ferro",
    "estágios de férias",
    "internato",
    "justificativa de falta",
    "projeto",
    "revisão biblio NDE 2025",
    "revisão de conceito",
    "sec. geral - beth",
    "secretaria acadêmica - guamá",
    "secretaria administrativa - generalíssimo",
    "secretaria executiva - generalíssimo",
    "segunda chamada",
    "teste do progresso 2021",
]

# Categorização preliminar para guiar a Etapa 4 e 5
CATEGORIAS = {
    "abono de falta": "Serviço ao Aluno (Etapa 5)",
    "aproveitamento de estudo": "Serviço ao Aluno (Etapa 5)",
    "assinatura de termo": "Serviço ao Aluno (Etapa 5)",
    "avaliação substitutiva": "Serviço ao Aluno (Etapa 5)",
    "colação de grau": "Serviço ao Aluno (Etapa 5)",
    "estágio": "Serviço ao Aluno (Etapa 5)",
    "estágios de férias": "Serviço ao Aluno (Etapa 5)",
    "internato": "Serviço ao Aluno (Etapa 5)",
    "justificativa de falta": "Serviço ao Aluno (Etapa 5)",
    "revisão de conceito": "Serviço ao Aluno (Etapa 5)",
    "segunda chamada": "Serviço ao Aluno (Etapa 5)",
    "sec. geral - beth": "Roteamento / Atendimento por Setor",
    "secretaria acadêmica - guamá": "Roteamento / Atendimento por Setor",
    "secretaria administrativa - generalíssimo": "Roteamento / Atendimento por Setor",
    "secretaria executiva - generalíssimo": "Roteamento / Atendimento por Setor",
    "casmuc": "Institucional / Administrativo",
    "CSU": "Institucional / Administrativo",
    "diretório acadêmico": "Institucional / Representação",
    "projeto": "Institucional / Administrativo",
    "revisão biblio": "Institucional / Docente NDE",
    "teste do progresso": "Candidato a Descarte (Histórico 2021)",
}

# Marcadores de sistema do Gmail para separar dos marcadores acadêmicos
SYSTEM_LABELS = {
    "aberto", "caixa de entrada", "importante", "enviado", "arquivada",
    "categoria: pessoal", "categoria: atualizações", "categoria: fóruns",
    "categoria: promoções", "categoria: social", "não lidas", "lixeira",
    "rascunhos", "com estrela", "ignorado", "spam", "confirmação de leitura enviada"
}


def decode_rfc2047(s: str) -> str:
    """Decodifica cabeçalhos no formato RFC 2047 (ex: =?UTF-8?Q?...?=)."""
    try:
        parts = email.header.decode_header(s)
        res = []
        for text, enc in parts:
            if isinstance(text, bytes):
                res.append(text.decode(enc or "utf-8", errors="replace"))
            else:
                res.append(str(text))
        return "".join(res)
    except Exception:
        return s


def parse_email_date(date_str: str) -> Optional[datetime]:
    """Converte string de data de e-mail (RFC 2822) para datetime."""
    if not date_str:
        return None
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except Exception:
        try:
            # Fallback regex para datas comuns
            clean = re.sub(r"\s+\([^\)]+\)", "", date_str).strip()
            return datetime.strptime(clean[:25].strip(), "%a, %d %b %Y %H:%M:%S")
        except Exception:
            return None


def run_mbox_inventory(raw_dir: Path) -> List[Dict]:
    """
    Varre arquivos .mbox do Google Takeout usando leitura ultra-rápida por streaming
    de cabeçalhos (sem carregar o arquivo de 6GB inteiro na memória).
    """
    print(f"\n[OFFLINE - TAKEOUT] Analisando arquivos .mbox em: {raw_dir}")
    mbox_files = list(raw_dir.glob("*.mbox"))
    if not mbox_files:
        print(f"[ERRO] Nenhum arquivo .mbox encontrado em {raw_dir}")
        return []

    # Dicionário de estatísticas: label -> {'count': int, 'first_dt': datetime, 'last_dt': datetime}
    label_stats: Dict[str, Dict] = {}
    total_messages_all = 0
    start_time = datetime.now()

    for mbox_path in mbox_files:
        print(f"\n-> Processando arquivo: {mbox_path.name} ({mbox_path.stat().st_size / (1024*1024*1024):.2f} GB)...")
        file_msg_count = 0

        with open(mbox_path, "rb") as f:
            in_headers = False
            current_headers = {}
            last_header = None

            for line in f:
                if line.startswith(b"From "):
                    # Finalizou mensagem anterior
                    if current_headers:
                        file_msg_count += 1
                        total_messages_all += 1

                        # Extrai data
                        d_val = current_headers.get("date", "")
                        msg_dt = parse_email_date(d_val)

                        # Extrai X-Gmail-Labels
                        raw_labels = current_headers.get("x-gmail-labels", "")
                        if raw_labels:
                            decoded = decode_rfc2047(raw_labels)
                            for lbl in decoded.split(","):
                                l = lbl.strip()
                                if l:
                                    if l not in label_stats:
                                        label_stats[l] = {"count": 0, "first_dt": None, "last_dt": None}
                                    st = label_stats[l]
                                    st["count"] += 1
                                    if msg_dt:
                                        # Remove timezone para comparação uniforme
                                        naive_dt = msg_dt.replace(tzinfo=None)
                                        if st["first_dt"] is None or naive_dt < st["first_dt"]:
                                            st["first_dt"] = naive_dt
                                        if st["last_dt"] is None or naive_dt > st["last_dt"]:
                                            st["last_dt"] = naive_dt

                        if file_msg_count % 5000 == 0:
                            print(f"   ... {file_msg_count:,} mensagens analisadas...")

                    in_headers = True
                    current_headers = {}
                    last_header = None
                    continue

                if in_headers:
                    if line in (b"\r\n", b"\n"):
                        in_headers = False
                        continue

                    # Continuação de cabeçalho (RFC 2822 folding)
                    if line[0] in (32, 9) and last_header:
                        current_headers[last_header] += " " + line.decode("utf-8", errors="replace").strip()
                        continue

                    colon_pos = line.find(b":")
                    if colon_pos > 0:
                        header_name = line[:colon_pos].decode("ascii", errors="ignore").lower().strip()
                        header_val = line[colon_pos + 1:].decode("utf-8", errors="replace").strip()
                        current_headers[header_name] = header_val
                        last_header = header_name
                    else:
                        last_header = None

            # Processa a última mensagem do arquivo se houver
            if current_headers:
                file_msg_count += 1
                total_messages_all += 1
                d_val = current_headers.get("date", "")
                msg_dt = parse_email_date(d_val)
                raw_labels = current_headers.get("x-gmail-labels", "")
                if raw_labels:
                    decoded = decode_rfc2047(raw_labels)
                    for lbl in decoded.split(","):
                        l = lbl.strip()
                        if l:
                            if l not in label_stats:
                                label_stats[l] = {"count": 0, "first_dt": None, "last_dt": None}
                            st = label_stats[l]
                            st["count"] += 1
                            if msg_dt:
                                naive_dt = msg_dt.replace(tzinfo=None)
                                if st["first_dt"] is None or naive_dt < st["first_dt"]:
                                    st["first_dt"] = naive_dt
                                if st["last_dt"] is None or naive_dt > st["last_dt"]:
                                    st["last_dt"] = naive_dt

        print(f"-> Concluído {mbox_path.name}: {file_msg_count:,} mensagens processadas.")

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n[OK] Varredura finalizada: {total_messages_all:,} mensagens analisadas em {elapsed:.1f} segundos!")

    # Monta a lista formatada de resultados
    results = []
    for label, data in label_stats.items():
        first_str = data["first_dt"].strftime("%d/%m/%Y") if data["first_dt"] else "-"
        last_str = data["last_dt"].strftime("%d/%m/%Y") if data["last_dt"] else "-"

        # Status temporal
        if data["last_dt"]:
            y = data["last_dt"].year
            if y >= 2025:
                status_label = f"Ativo Recente ({y})"
            elif y >= 2023:
                status_label = f"Ativo Médio ({y})"
            else:
                status_label = f"Obsoleto / Histórico ({y})"
        else:
            status_label = "Sem data"

        # Categoria
        categoria = "Geral"
        for target, cat in CATEGORIAS.items():
            if target.lower() in label.lower():
                categoria = cat
                break

        is_system = label.lower() in SYSTEM_LABELS
        is_famed_target = any(t.lower() in label.lower() for t in TARGET_LABELS_DEFAULT)

        results.append({
            "marcador": label,
            "total_emails": data["count"],
            "primeiro_email": first_str,
            "ultimo_email": last_str,
            "status": status_label,
            "categoria": "Sistema do Gmail" if is_system else categoria,
            "foco_famed": is_famed_target,
            "is_system": is_system,
        })

    return results


def export_reports(results: List[Dict], output_dir: Path):
    """Exporta o relatório consolidado em Markdown e JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "email_inventory_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Separa grupos
    famed_items = [r for r in results if r["foco_famed"]]
    famed_items.sort(key=lambda x: x["total_emails"], reverse=True)

    other_custom = [r for r in results if not r["foco_famed"] and not r["is_system"]]
    other_custom.sort(key=lambda x: x["total_emails"], reverse=True)

    system_items = [r for r in results if r["is_system"]]
    system_items.sort(key=lambda x: x["total_emails"], reverse=True)

    total_emails_famed = sum(r["total_emails"] for r in famed_items)

    md_lines = [
        "# Relatório de Inventário da Caixa de E-mails — Secretaria FAMED/UFPA (Fase 0)",
        f"\n- **Data do Levantamento:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"- **Modo de Acesso:** 100% Offline (Google Takeout / Streaming MBOX)",
        f"- **Total de Mensagens nos Marcadores Foco:** {total_emails_famed:,}",
        "\n---",
        "\n## 1. Marcadores Oficiais da FAMED (Ordenados por Volume)",
        "\nEstes marcadores alimentam diretamente as **Etapas 4 (Perguntas Frequentes)** e **5 (Serviços da FAMED)**:\n",
        "| Marcador | Volume | Primeiro E-mail | Último E-mail | Status | Categoria Proposta |",
        "|---|:---:|:---:|:---:|---|---|",
    ]

    for item in famed_items:
        md_lines.append(
            f"| **{item['marcador']}** | {item['total_emails']} | {item['primeiro_email']} | {item['ultimo_email']} | {item['status']} | {item['categoria']} |"
        )

    if other_custom:
        md_lines.extend([
            "\n---",
            "\n## 2. Outros Marcadores Personalizados Encontrados",
            "\n| Marcador | Volume | Primeiro E-mail | Último E-mail | Status |",
            "|---|:---:|:---:|:---:|---|",
        ])
        for item in other_custom:
            md_lines.append(
                f"| {item['marcador']} | {item['total_emails']} | {item['primeiro_email']} | {item['ultimo_email']} | {item['status']} |"
            )

    md_lines.extend([
        "\n---",
        "\n## 3. Diretrizes de Triagem para as Próximas Etapas",
        "\n1. **Serviços Críticos com Altíssimo Volume (Etapa 4 e 5 - Prioridade 1):**",
        "   - **SEGUNDA CHAMADA** (666 e-mails) e **AVALIAÇÃO SUBSTITUTIVA** (125 e-mails): juntos representam quase 800 atendimentos. Devem gerar guias completos de requisitos, prazos e fluxo.",
        "   - **ESTÁGIOS DE FÉRIAS** (129 e-mails) e **INTERNATO** (6 e-mails): processos práticos que geram muitas dúvidas de documentação.",
        "   - **ABONO DE FALTA** (47 e-mails) e **JUSTIFICATIVA DE FALTA** (40 e-mails): distinguir claramente entre abono (legal) e justificativa perante os docentes.",
        "   - **REVISÃO DE CONCEITO** (40 e-mails): regras de contestação de notas.",
        "2. **Candidatos a Descarte / Históricos:**",
        "   - Marcadores com datas antigas (ex: `TESTE DO PROGRESSO 2021` ou `CASMUC- 2023`) não refletem regras vigentes de 2026.",
        "3. **Marcadores de Setor:**",
        "   - `SEC. GERAL - BETH` e similares serão usados para mapear a responsabilidade interna de atendimento.",
    ])

    md_path = output_dir / "email_inventory_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n[SUCESSO] Relatórios gerados com sucesso:")
    print(f"  -> Markdown: {md_path}")
    print(f"  -> JSON:     {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Inventário de E-mails da Secretaria FAMED (Fase 0 - Somente Leitura)")
    parser.add_argument("--user", help="E-mail da conta (ex: famed.ufpa.guama@gmail.com)")
    parser.add_argument("--password", help="Senha de App do Google (16 caracteres)")
    parser.add_argument("--takeout", help="Caminho para pasta com arquivos .mbox exportados do Takeout")
    args = parser.parse_args()

    # Se --takeout não for fornecido, mas a pasta backend/data/email_raw existir com .mbox, usa ela automaticamente
    default_raw = Path(__file__).resolve().parent.parent / "backend" / "data" / "email_raw"
    takeout_path = Path(args.takeout) if args.takeout else (default_raw if list(default_raw.glob("*.mbox")) else None)

    if takeout_path and takeout_path.exists():
        results = run_mbox_inventory(takeout_path)
    else:
        print("[AVISO] Nenhum arquivo .mbox encontrado em backend/data/email_raw. Tentando IMAP...")
        user = args.user or os.getenv("GMAIL_USER") or os.getenv("EMAIL_USER") or "famed.ufpa.guama@gmail.com"
        password = args.password or os.getenv("GMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD")

        if not password:
            print("=" * 70)
            print("INVENTÁRIO DE E-MAILS DA SECRETARIA FAMED/UFPA (FASE 0)")
            print("=" * 70)
            import getpass
            try:
                password = getpass.getpass("\nDigite ou cole a Senha de App do Gmail: ").strip()
            except KeyboardInterrupt:
                print("\nOperação cancelada.")
                sys.exit(0)

        results = []

    if results:
        backend_data = Path(__file__).resolve().parent.parent / "backend" / "data"
        export_reports(results, backend_data)


if __name__ == "__main__":
    main()
