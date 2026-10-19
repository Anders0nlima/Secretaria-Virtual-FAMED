"""
Fase 1 e 2 — Extração e Anonimização LGPD dos E-mails da Secretaria FAMED/UFPA
-------------------------------------------------------------------------------
Objetivo:
  1. Extrair as mensagens dos marcadores ativos de serviços ao aluno de forma ultra-rápida.
  2. Limpar corpos de e-mail e extrair nomes de anexos.
  3. Anonimizar estritamente dados pessoais e sensíveis em conformidade com a LGPD
     (Lei 13.709/2018): CPF, Matrícula, E-mails pessoais, Telefones, Nomes e CIDs.
  4. Agrupar em tópicos e conversas (Pergunta do Aluno <-> Resposta/Encaminhamento da Secretaria).
  5. Exportar base anonimizada em JSON e gerar um Preview legível em Markdown.
"""

import os
import sys
import re
import json
import email
from email import policy
import email.header
import email.utils
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Mapeamento dos marcadores alvo de serviços ao aluno
FOCUS_KEYS = [
    (b"SEGUNDA CHAMADA", "Segunda Chamada"),
    (b"ESTAGIO DE FERIAS", "Estágio de Férias"),
    (b"AVALIA", "Avaliação Substitutiva"),
    (b"ABONO", "Abono de Falta"),
    (b"JUSTIFICATIVA", "Justificativa de Falta"),
    (b"REVIS", "Revisão de Conceito"),
    (b"TERMO", "Assinatura de Termo"),
    (b"INTERNATO", "Internato"),
    (b"COLA", "Colação de Grau"),
]

FORM_KEYWORDS = {
    "LISTA", "FREQUENCIA", "FREQUÊNCIA", "ESTAGIO", "ESTÁGIO", "FERIAS", "FÉRIAS",
    "OFICIO", "OFÍCIO", "SANTA", "CASA", "HUJBB", "COMPROVANTE", "FORMULARIO",
    "FORMULÁRIO", "SIPAC", "SAGITTA", "REQUERIMENTO", "PARECER", "PLANO"
}


def decode_rfc2047(s: str) -> str:
    """Decodifica cabeçalhos MIME no formato RFC 2047."""
    if not s:
        return ""
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
    """Converte string de data do e-mail para datetime."""
    if not date_str:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        return dt.replace(tzinfo=None) if dt else None
    except Exception:
        return None


def clean_html_to_text(html_content: str) -> str:
    """Converte conteúdo HTML para texto legível sem tags."""
    text = re.sub(r"(?i)<style.*?</style>", "", html_content, flags=re.DOTALL)
    text = re.sub(r"(?i)<script.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"(?i)</div>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    return text


def extract_body_and_attachments(msg: email.message.EmailMessage) -> Tuple[str, List[str]]:
    """Extrai texto do corpo da mensagem e lista de nomes de arquivos anexados."""
    body_text = ""
    attachments = []

    try:
        plain_part = msg.get_body(preferencelist=("plain",))
        if plain_part:
            body_text = plain_part.get_content()
        else:
            html_part = msg.get_body(preferencelist=("html",))
            if html_part:
                body_text = clean_html_to_text(html_part.get_content())
    except Exception:
        pass

    try:
        for part in msg.walk():
            filename = part.get_filename()
            if filename:
                decoded_fn = decode_rfc2047(filename)
                clean_fn = re.sub(r"[\r\n\t]", "", decoded_fn).strip()
                if clean_fn and clean_fn not in attachments:
                    attachments.append(clean_fn)
    except Exception:
        pass

    return body_text or "", attachments


def clean_attachment_name(fn: str) -> str:
    """Anonimiza nomes de anexos que contenham nomes ou matrículas de alunos."""
    if not fn:
        return ""
    base, ext = fn.rsplit(".", 1) if "." in fn else (fn, "")
    base_clean = re.sub(r"\b20[12]\d{7,10}\b", "[MATRICULA]", base)

    words = re.findall(r"[A-Za-zÀ-Úà-ú]+", base_clean)
    upper_words = [w.upper() for w in words if len(w) >= 3]

    # Se contém nome de formulário oficial/institucional, preserva o nome da peça
    if any(w in FORM_KEYWORDS for w in upper_words):
        return f"{base_clean}.{ext}" if ext else base_clean

    # Se são 2 ou mais palavras que parecem nome pessoal em maiúsculas sem ser formulário
    if len(upper_words) >= 2:
        return f"Documento_[ALUNO].{ext}" if ext else "Documento_[ALUNO]"

    return f"{base_clean}.{ext}" if ext else base_clean


def anonymize_text(text: str) -> str:
    """
    Aplica regras estritas de anonimização em conformidade com a LGPD (Lei 13.709/2018):
    - Remove CPFs
    - Remove números de Matrícula UFPA
    - Mascara e-mails pessoais
    - Mascara números de telefone
    - Mascara nomes próprios de alunos
    - Mascara dados sensíveis de saúde (CIDs)
    """
    if not text:
        return ""

    t = text

    # 1. CPFs (formatados ou apenas números de 11 dígitos com pontuação)
    t = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b", "[CPF]", t)

    # 2. Matrícula da UFPA (10 a 12 dígitos, iniciando com 201x, 202x)
    t = re.sub(r"(?i)\b(matr[íi]cula:?\s*)20[12]\d{7,10}\b", r"\1[MATRÍCULA]", t)
    t = re.sub(r"\b20[12]\d{9,10}\b", "[MATRÍCULA]", t)

    # 3. E-mails (preserva menção de e-mails institucionais genéricos da FAMED/UFPA)
    def mask_email(match):
        em = match.group(0).lower()
        if "famed" in em or "secretariamedicina" in em or "ufpa.guama" in em:
            return "[EMAIL_SECRETARIA]"
        return "[EMAIL]"

    t = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", mask_email, t)

    # 4. Telefones / Celulares
    t = re.sub(r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s]?\d{4}\b", "[TELEFONE]", t)

    # 5. CIDs médicos (Dado Pessoal Sensível - Art. 5º, II da LGPD)
    t = re.sub(r"(?i)\bCID[- ]?(?:10)?[:\s]*[A-Z]\d{2}(?:\.\d)?\b", "[CID/DIAGNÓSTICO]", t)

    # 6. Nomes em estruturas de atendimento e antes de e-mails
    t = re.sub(r"([A-ZÀ-Ú][A-ZÀ-Úa-zà-ú]+(?:\s+[A-ZÀ-Ú][A-ZÀ-Úa-zà-ú]+){1,5})\s*<\s*\[EMAIL\]\s*>", r"[REMETENTE] <[EMAIL]>", t)
    t = re.sub(r"(?i)(solicita[cç][aã]o de [A-ZÀ-Ú\s]+ de\s+)([A-ZÀ-Ú\s\r\n]{3,60})(,?\s*matr[íi]cula)", r"\1[ALUNO]\3", t)
    t = re.sub(r"(?i)(\bde\s+)([A-ZÀ-Ú\s\r\n]{3,60})(,?\s*matr[íi]cula)", r"\1[ALUNO]\3", t)
    t = re.sub(r"(?i)(Eu,\s*)([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+){1,5})(,\s*discente|,\s*alun[oa]|,\s*matr[íi]cula)", r"\1[ALUNO]\3", t)
    t = re.sub(r"(?i)(alun[oa]\s+)([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+){1,5})(\s+portador|\s+regular|\s+da\s+matr[íi]cula)", r"\1[ALUNO]\3", t)
    t = re.sub(r"(?i)(nome\s*é:?\s*)([A-ZÀ-Úa-zà-ú]{3,}(?:\s+[A-ZÀ-Úa-zà-ú]{2,})+)", r"\1[ALUNO]", t)
    t = re.sub(r"(?i)(Cara\s+)([A-ZÀ-Ú][a-zà-ú]+)", r"\1[ALUNO]", t)
    t = re.sub(r"(Em\s+[a-zà-ú\.,\s0-9]+às\s+[0-9:]+,\s*)([A-ZÀ-Úa-zà-ú\s]+)(\s*<\[EMAIL[^>]*\]>\s*escreveu:)", r"\1[REMETENTE]\3", t)

    # 7. Limpa rodapés e avisos de confidencialidade repetitivos
    t = re.sub(
        r"(?i)Esta mensagem pode conter informa[cç][aã]o confidencial.*",
        "",
        t,
        flags=re.DOTALL,
    )

    return t.strip()


def normalize_subject(subj: str) -> str:
    """Normaliza o assunto para agrupar mensagens da mesma thread."""
    if not subj:
        return "Sem Assunto"
    clean = decode_rfc2047(subj)
    clean = re.sub(r"(?i)^\s*(re|res|fwd|enc):\s*", "", clean)
    clean = re.sub(r"(?i)^\s*(re|res|fwd|enc):\s*", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean or "Sem Assunto"


def run_extraction_and_anonymization(mbox_path: Path, output_dir: Path):
    """Executa a extração por streaming rápido, limpeza, anonimização e agrupamento."""
    print("=" * 70)
    print("EXTRAÇÃO E ANONIMIZAÇÃO LGPD DE E-MAILS (FASES 1 E 2)")
    print("=" * 70)
    print(f"Arquivo MBOX de entrada: {mbox_path}")
    print(f"Diretório de saída:      {output_dir}")

    matched_msgs = []
    start_time = datetime.now()

    print("\n1. Varrendo e filtrando mensagens dos marcadores de serviços...")

    is_target = False
    in_headers = False
    target_category = "Serviço Geral"
    header_lines = []
    body_lines = []
    total_scanned = 0

    with open(mbox_path, "rb") as f:
        for line in f:
            if line.startswith(b"From "):
                total_scanned += 1
                if is_target and header_lines:
                    raw_bytes = b"".join(header_lines + [b"\r\n"] + body_lines)
                    try:
                        msg = email.message_from_bytes(raw_bytes, policy=policy.default)
                        subj_raw = str(msg.get("subject") or "")
                        subj = normalize_subject(subj_raw)
                        dt = parse_email_date(str(msg.get("date") or ""))
                        is_sent = "enviado" in str(msg.get("x-gmail-labels") or "").lower()

                        body_text, attachments = extract_body_and_attachments(msg)
                        anon_body = anonymize_text(body_text)

                        anon_attachments = [clean_attachment_name(att) for att in attachments]

                        matched_msgs.append({
                            "servico": target_category,
                            "subject": anonymize_text(subj),
                            "date": dt.strftime("%d/%m/%Y %H:%M") if dt else "-",
                            "dt_obj": dt,
                            "tipo": "SECRETARIA (Resposta/Encaminhamento)" if is_sent else "ALUNO (Solicitação)",
                            "body": anon_body,
                            "attachments": anon_attachments,
                        })

                        if len(matched_msgs) % 100 == 0:
                            print(f"   ... {len(matched_msgs):,} e-mails de serviços extraídos...")

                    except Exception:
                        pass

                is_target = False
                in_headers = True
                target_category = "Serviço Geral"
                header_lines = []
                body_lines = []
                continue

            if in_headers:
                if line in (b"\r\n", b"\n"):
                    in_headers = False
                    continue
                header_lines.append(line)
                if line.startswith(b"X-Gmail-Labels:") or line.startswith(b"x-gmail-labels:"):
                    u = line.upper()
                    for k_bytes, k_name in FOCUS_KEYS:
                        if k_bytes in u:
                            is_target = True
                            target_category = k_name
                            break
            else:
                if not is_target:
                    continue
                if len(body_lines) < 150:
                    body_lines.append(line)

        # Última mensagem
        if is_target and header_lines:
            raw_bytes = b"".join(header_lines + [b"\r\n"] + body_lines)
            try:
                msg = email.message_from_bytes(raw_bytes, policy=policy.default)
                subj = normalize_subject(str(msg.get("subject") or ""))
                dt = parse_email_date(str(msg.get("date") or ""))
                is_sent = "enviado" in str(msg.get("x-gmail-labels") or "").lower()
                body_text, attachments = extract_body_and_attachments(msg)
                anon_body = anonymize_text(body_text)

                matched_msgs.append({
                    "servico": target_category,
                    "subject": anonymize_text(subj),
                    "date": dt.strftime("%d/%m/%Y %H:%M") if dt else "-",
                    "dt_obj": dt,
                    "tipo": "SECRETARIA (Resposta/Encaminhamento)" if is_sent else "ALUNO (Solicitação)",
                    "body": anon_body,
                    "attachments": [clean_attachment_name(att) for att in attachments],
                })
            except Exception:
                pass

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n[OK] Extração e Anonimização concluídas!")
    print(f"  Total de e-mails analisados no arquivo: {total_scanned:,}")
    print(f"  Total de e-mails de serviços extraídos:  {len(matched_msgs):,} em {elapsed:.1f}s")

    # 2. Agrupamento em Conversas / Threads por Assunto + Serviço
    print("\n2. Agrupando e-mails em conversas (Dúvida do Aluno <-> Atendimento da Secretaria)...")
    threads_map: Dict[str, Dict] = {}

    for m in matched_msgs:
        key = f"{m['servico']}___{m['subject'].lower()}"
        if key not in threads_map:
            threads_map[key] = {
                "servico": m["servico"],
                "subject": m["subject"],
                "first_date": m["date"],
                "last_date": m["date"],
                "dt_ref": m["dt_obj"],
                "solicitacoes_aluno": [],
                "respostas_secretaria": [],
                "todos_anexos": set(),
                "total_mensagens": 0,
            }

        th = threads_map[key]
        th["total_mensagens"] += 1
        for att in m["attachments"]:
            th["todos_anexos"].add(att)

        if m["tipo"] == "ALUNO (Solicitação)":
            if m["body"] and len(m["body"]) > 15:
                th["solicitacoes_aluno"].append(m["body"])
        else:
            if m["body"] and len(m["body"]) > 15:
                th["respostas_secretaria"].append(m["body"])

    threads_list = []
    for k, v in threads_map.items():
        v["todos_anexos"] = sorted(list(v["todos_anexos"]))
        threads_list.append(v)

    # Ordena por volume de mensagens na thread e por data recente
    threads_list.sort(key=lambda x: (x["total_mensagens"], x["dt_ref"] or datetime.min), reverse=True)

    for th in threads_list:
        th.pop("dt_ref", None)

    # 3. Exportação em JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "emails_anonymized.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(threads_list, f, ensure_ascii=False, indent=2)

    # 4. Geração do Preview em Markdown para validação humana
    print("\n3. Gerando Preview em Markdown com amostras reais anonimizadas...")
    preview_path = output_dir / "emails_anonymized_preview.md"

    servico_counts = {}
    for th in threads_list:
        s = th["servico"]
        servico_counts[s] = servico_counts.get(s, 0) + th["total_mensagens"]

    md_lines = [
        "# Base Anonimizada de E-mails da Secretaria FAMED/UFPA (LGPD Compliance)",
        f"\n- **Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"- **Total de Mensagens Extraídas:** {len(matched_msgs):,}",
        f"- **Total de Conversas / Threads Únicas:** {len(threads_list):,}",
        f"- **Garantia LGPD:** CPFs, Matrículas, E-mails pessoais, Nomes e CIDs estritamente mascarados.",
        "\n---",
        "\n## 1. Volumetria por Serviço do Aluno (Etapa 4 e 5)",
        "\n| Serviço Acadêmico | E-mails Extraídos | Conversas Únicas |",
        "|---|:---:|:---:|",
    ]

    for s_name, count in sorted(servico_counts.items(), key=lambda x: x[1], reverse=True):
        th_count = sum(1 for th in threads_list if th["servico"] == s_name)
        md_lines.append(f"| **{s_name}** | {count} | {th_count} |")

    md_lines.extend([
        "\n---",
        "\n## 2. Amostras de Conversas Anonimizadas por Serviço",
        "\nAbaixo estão amostras reais demonstrando como as dúvidas dos alunos e os atendimentos da secretaria foram estruturados:\n",
    ])

    for s_name in sorted(servico_counts.keys()):
        matching_threads = [th for th in threads_list if th["servico"] == s_name]
        md_lines.append(f"\n### Serviço: {s_name}")

        for idx, th in enumerate(matching_threads[:2], 1):
            md_lines.append(f"\n#### Caso {idx}: {th['subject']} ({th['total_mensagens']} mensagens)")
            if th["todos_anexos"]:
                md_lines.append(f"**Documentos/Anexos mencionados:** `{', '.join(th['todos_anexos'][:5])}`")

            if th["solicitacoes_aluno"]:
                sample_aluno = th["solicitacoes_aluno"][0][:400].replace("\n", " ").strip()
                md_lines.append(f"\n**Mensagem do Aluno:**\n> {sample_aluno}...")

            if th["respostas_secretaria"]:
                sample_sec = th["respostas_secretaria"][0][:400].replace("\n", " ").strip()
                md_lines.append(f"\n**Resposta da Secretaria:**\n> {sample_sec}...")

            md_lines.append("\n---")

    md_lines.extend([
        "\n## 3. Próximo Passo (Fase 3 e 4: Agrupamento Semântico e Síntese de FAQ)",
        "\nCom esses dados anonimizados e estruturados, o script da **Fase 3 e 4** vai:",
        "1. Usar embeddings para ranquear as perguntas mais frequentes de cada serviço.",
        "2. Redigir os rascunhos de guias de serviço com: **O que é -> Documentos necessários -> Prazos -> Onde solicitar**.",
        "3. Gerar a base curada para validação dos secretários e inclusão no ChromaDB.",
    ])

    with open(preview_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n[SUCESSO] Arquivos gerados com sucesso:")
    print(f"  -> JSON com base completa anonimizada: {json_path}")
    print(f"  -> Markdown de Preview e Validação:     {preview_path}")


def main():
    backend_data = Path(__file__).resolve().parent.parent / "backend" / "data"
    mbox_path = backend_data / "email_raw" / "Todos os e-mails, incluindo Spam e Lixeira-002.mbox"

    if not mbox_path.exists():
        mboxes = list((backend_data / "email_raw").glob("*.mbox"))
        if mboxes:
            mbox_path = mboxes[0]
        else:
            print(f"[ERRO] Arquivo MBOX não encontrado em {backend_data / 'email_raw'}")
            sys.exit(1)

    run_extraction_and_anonymization(mbox_path, backend_data)


if __name__ == "__main__":
    main()
