import re

with open("data/calendario_2026_curado.md", "r", encoding="utf-8") as f:
    content = f.read()

# The file has a few main parts. We want to find all "### " headers inside the Cronograma sections.
# Sections:
# ## Cronograma de Ações Acadêmicas
# ## Cronograma de Ações — Colação de Grau

def process_cronograma(text):
    # Split by ### 
    parts = re.split(r'(### .+?\n)', text)
    if len(parts) == 1:
        return text
    
    out = parts[0]
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i+1]
        
        # We look for lines containing "2026.1", "2026.2", etc.
        lines = body.strip().split('\n')
        
        new_blocks = []
        other_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Find period
            m = re.search(r'período (2026\.[1-4])', line)
            if not m:
                m = re.search(r'período de (2026\.[1-4])', line)
            
            if m:
                period = m.group(1)
                # Create a specific header for this period
                # e.g. ### Consolidação de Conceitos - Período 2026.1
                clean_header = header.replace("### ", "").strip()
                new_blocks.append(f"### {clean_header} ({period})\n{line}\n")
            else:
                other_lines.append(line)
                
        if new_blocks:
            if other_lines:
                out += header + "\n" + "\n".join(other_lines) + "\n\n"
            out += "\n".join(new_blocks) + "\n"
        else:
            out += header + "\n" + body
            
    return out

# Split the document at the first cronograma
parts = re.split(r'(## Cronograma de Ações Acadêmicas\n)', content)
if len(parts) > 1:
    before_cronograma = parts[0]
    cronograma_part = parts[1] + parts[2]
    
    parts2 = re.split(r'(## Cronograma de Ações — Colação de Grau\n)', cronograma_part)
    if len(parts2) > 1:
        cronograma_academicas = parts2[0]
        cronograma_colacao = parts2[1] + parts2[2]
        
        new_acad = process_cronograma(cronograma_academicas)
        new_col = process_cronograma(cronograma_colacao)
        
        new_content = before_cronograma + new_acad + new_col
    else:
        new_content = before_cronograma + process_cronograma(cronograma_part)

    with open("data/calendario_2026_curado.md", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Calendário reformatado com sucesso!")
else:
    print("Seção cronograma não encontrada.")

