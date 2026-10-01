import os

# 1. Ajustar em links.md para ficar claro e alinhado com o FAQ do LAEPE
path_links = os.path.join("data", "documentos_curados", "links.md")
with open(path_links, "r", encoding="utf-8") as f:
    text_links = f.read()

target_links = """**Quais tipos de trabalho são aceitos como TCC na FAMED?**
Tipos aceitos: estudos clínicos observacionais ou de intervenção, ciência básica (modelos celulares/animais), relato ou série de casos (acompanhados pelo aluno/orientador), revisão sistemática (meta-análise opcional).
Tipos NÃO aceitos: revisões narrativas isoladas, capítulo de livro, relatório, cartilhas.
Revisão integrativa só é aceita se incluir revisão sistemática.
Formatos de entrega: monografia ou artigo científico publicado em revista Qualis A ou B."""

replacement_links = """### Tipos de Estudos Aceitos e Proibidos no TCC
**Quais tipos de trabalho são aceitos como TCC na FAMED? Revisão narrativa pura é aceita como formato de TCC na FAMED?**
Não, revisão narrativa pura (isolada) NÃO é aceita como formato de TCC na FAMED.
- Tipos aceitos pelo LAEPE: estudos clínicos observacionais ou de intervenção, ciência básica (modelos celulares/animais), relato ou série de casos (desde que acompanhados pelo aluno/orientador), revisão sistemática (com meta-análise opcional).
- Tipos expressamente NÃO aceitos: revisões narrativas isoladas (puras), capítulos de livro, relatórios e cartilhas.
- Revisão integrativa só é aceita se for conduzida com metodologia de revisão sistemática.
- Formatos oficiais de entrega: Monografia tradicional ou Artigo científico publicado em periódico Qualis A ou B."""

if target_links in text_links:
    text_links = text_links.replace(target_links, replacement_links)
    with open(path_links, "w", encoding="utf-8") as f:
        f.write(text_links)
    print("OK em links.md")
else:
    print("Target não encontrado em links.md")

# 2. Ajustar em tcc_normas.md para eliminar a contradição com o LAEPE
path_tcc = os.path.join("data", "documentos_curados", "tcc_normas.md")
with open(path_tcc, "r", encoding="utf-8") as f:
    text_tcc = f.read()

target_tcc = """### Sobre Revisões Narrativas e Outros Formatos de TCC
**Revisões narrativas são permitidas no TCC de Medicina da FAMED?**
O regulamento de TCC da FAMED/UFPA não proíbe nem autoriza explicitamente revisões narrativas como formato isolado de TCC. Os dois formatos oficiais aceitos são: Monografia tradicional e Artigo científico Qualis A ou B. Para dúvidas sobre a aceitação de formatos específicos (como revisão narrativa, relato de caso, meta-análise), consulte diretamente a Coordenação de TCC do LAEPE antes de iniciar o projeto."""

replacement_tcc = """### Sobre Revisões Narrativas e Outros Formatos de TCC
**Revisão narrativa pura é aceita como formato de TCC na FAMED? Revisões narrativas são permitidas no TCC de Medicina da FAMED?**
Não. Segundo as diretrizes do LAEPE e as normas da FAMED, revisões narrativas puras (isoladas) NÃO são aceitas como formato de TCC.
Os formatos e tipos de estudos aceitos são:
1. Monografia tradicional (estudos originais clínicos ou experimentais, relatos de casos acompanhados e revisões sistemáticas).
2. Artigo científico Qualis A ou B publicado nos últimos 4 anos.
Revisão integrativa só é aceita se incluir metodologia sistemática. Capítulos de livros, relatórios e revisões puramente narrativas não são permitidos."""

if target_tcc in text_tcc:
    text_tcc = text_tcc.replace(target_tcc, replacement_tcc)
    with open(path_tcc, "w", encoding="utf-8") as f:
        f.write(text_tcc)
    print("OK em tcc_normas.md")
else:
    print("Target não encontrado em tcc_normas.md")

