"""Gera o .docx da versão final a partir dos rascunhos .md. Ferramenta de documento, fora do produto.

    python docs/tcc/_gerar_docx.py        # precisa de python-docx (pip install python-docx)

Base: `Report 6 - Resultados.docx` (template da Facens, capa, Caps. 1–3, que são
iguais aos do PDF de 14/10). Troca:
  - Lista de siglas, Resumo e Abstract   <- pre-e-pos-textuais.md
  - Caps. 4, 5 e 6                       <- capitulo-4/5/6-rascunho.md
  - Referências                          <- pre-e-pos-textuais.md
e padroniza: quebra de página antes de cada capítulo (no lugar de parágrafos vazios),
legendas "Figura N – " com numeração automática, fontes "Elaborada pelos autores".
Sumário e listas são campos: atualize no Word (o gerador chama o Word, se houver).

O .md é a fonte da verdade do texto: corrija lá e gere de novo.
"""
from __future__ import annotations

import copy
import re
import subprocess
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.shared import Cm
from lxml import etree
from PIL import Image

TCC = Path(__file__).resolve().parent
BASE = TCC / "Report 6 - Resultados.docx"
SAIDA = TCC / "Monografia - versao final.docx"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
LARGURA_MAX, ALTURA_MAX = Cm(16), Cm(17)

d = docx.Document(str(BASE))
body = d.element.body
SECT = body[-1]


def estilo(p) -> str:
    s = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    return s.get(qn("w:val")) if s is not None else ""


def texto(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def achar(pred, depois=0):
    return next(i for i, el in enumerate(body) if i >= depois and el.tag == qn("w:p") and pred(el))


# ---------------------------------------------------------------- modelos
i_h4 = achar(lambda p: estilo(p) == "Ttulo1" and texto(p).startswith("4 DESENVOLVIMENTO"))
# títulos e espaçamento copiados do Cap. 2, para os Caps. 4–6 ficarem iguais aos Caps. 1–3
i_c2 = achar(lambda p: estilo(p) == "Ttulo1" and texto(p).startswith("2 CRESCIMENTO"))
H = {1: copy.deepcopy(body[i_c2]),
     2: copy.deepcopy(body[achar(lambda p: estilo(p) == "Ttulo2" and texto(p).startswith("2.1 "), i_c2)]),
     3: copy.deepcopy(body[achar(lambda p: estilo(p) == "Ttulo3" and texto(p).startswith("2.2.1"), i_c2)])}
for x in H.values():
    for b in list(x.iter(qn("w:bookmarkStart"))) + list(x.iter(qn("w:bookmarkEnd"))):
        b.getparent().remove(b)
BRANCO = copy.deepcopy(body[i_c2 + 1])
CORPO = copy.deepcopy(body[achar(lambda p: texto(p).startswith("Este estudo apresenta"))])
LISTA = copy.deepcopy(body[achar(lambda p: texto(p).startswith("a) home_contextual"))])
i_leg = achar(lambda p: estilo(p) == "Legenda", i_h4)
LEGENDA, IMAGEM_PPR, FONTE = (copy.deepcopy(body[i_leg]), copy.deepcopy(body[i_leg + 1].find(qn("w:pPr"))),
                              copy.deepcopy(body[i_leg + 2]))
i_tab = achar(lambda p: texto(p).startswith("Tabela 2 –"), i_h4)
LEG_TABELA = copy.deepcopy(body[i_tab])
QUEBRA = copy.deepcopy(next(p for p in body[i_h4:] if p.tag == qn("w:p") and not texto(p)
                            and any(b.get(qn("w:type")) == "page" for b in p.iter(qn("w:br")))))
TITULO_PRE = copy.deepcopy(body[achar(lambda p: texto(p).strip() == "LISTA DE ILUSTRAÇÕES")])
SIGLA = copy.deepcopy(body[achar(lambda p: texto(p).startswith("API"))])
VAZIO = copy.deepcopy(body[achar(lambda p: not texto(p) and estilo(p) == "" and len(p) == 1 and p[0].tag == qn("w:pPr"))])


def _rpr(par):
    r = par.find(qn("w:r"))
    rpr = r.find(qn("w:rPr")) if r is not None else None
    return copy.deepcopy(rpr) if rpr is not None else etree.SubElement(etree.Element(qn("w:r")), qn("w:rPr"))


def _limpa(par):
    for filho in list(par):
        if filho.tag != qn("w:pPr"):
            par.remove(filho)
    return par


NOTAS: dict[str, str] = {}
ID_NOTA = {"n": 0}


def _run(rpr, t, negrito=False, italico=False):
    r = etree.Element(qn("w:r"))
    rp = copy.deepcopy(rpr)
    for tag, liga in ((qn("w:b"), negrito), (qn("w:i"), italico)):
        if liga:
            for x in rp.findall(tag):
                rp.remove(x)
            rp.insert(0, etree.Element(tag))
    r.append(rp)
    el = etree.SubElement(r, qn("w:t"))
    el.text = t
    el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


def _nota(chave):
    ID_NOTA["n"] += 1
    r = etree.Element(qn("w:r"))
    rp = etree.SubElement(r, qn("w:rPr"))
    etree.SubElement(rp, qn("w:rStyle")).set(qn("w:val"), "Refdenotaderodap")
    etree.SubElement(r, qn("w:footnoteReference")).set(qn("w:id"), str(ID_NOTA["n"]))
    NOTAS_USADAS.append((ID_NOTA["n"], NOTAS[chave]))
    return r


NOTAS_USADAS: list[tuple[int, str]] = []


def paragrafo(modelo, conteudo: str):
    """Parágrafo com **negrito**, *itálico* e [^nota] (markdown mínimo dos rascunhos)."""
    p = _limpa(copy.deepcopy(modelo))
    rpr = _rpr(modelo)
    for pedaco in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|\[\^\w+\])", conteudo):
        if not pedaco:
            continue
        if pedaco.startswith("**"):
            p.append(_run(rpr, pedaco[2:-2], negrito=True))
        elif pedaco.startswith("[^"):
            p.append(_nota(pedaco[2:-1]))
        elif pedaco.startswith("*"):
            p.append(_run(rpr, pedaco[1:-1], italico=True))
        else:
            p.append(_run(rpr, pedaco))
    return p


def legenda_figura(t: str):
    """'Figura N - texto' -> 'Figura ' + SEQ Figura + ' – texto' (numeração automática do Word)."""
    resto = re.sub(r"^Figura \d+\s*[-–]\s*", "", t)
    p = copy.deepcopy(LEGENDA)
    rs = p.findall(qn("w:r"))
    rs[0].find(qn("w:t")).text = "Figura "
    num = [r for r in rs if r.find(qn("w:t")) is not None][1]  # o número entre separate e end
    num.find(qn("w:t")).text = re.match(r"Figura (\d+)", t).group(1)
    depois = rs[rs.index(num) + 2:]  # depois do fldChar end
    for r in depois:
        p.remove(r)
    p.append(_run(_rpr(LEGENDA), " – " + resto))
    return p


def imagem(caminho: Path):
    w, h = Image.open(caminho).size
    largura = min(LARGURA_MAX, int(ALTURA_MAX * w / h))
    d.add_picture(str(caminho), width=largura)  # entra no fim do corpo, antes do sectPr
    p = body[-2]
    p.remove(p.find(qn("w:pPr"))) if p.find(qn("w:pPr")) is not None else None
    p.insert(0, copy.deepcopy(IMAGEM_PPR))
    return p


def tabela(linhas: list[str]):
    cel = [[c.strip() for c in l.strip().strip("|").split("|")] for l in linhas]
    cab, sep, dados = cel[0], cel[1], cel[2:]
    alin = ["right" if s.endswith(":") and not s.startswith(":") else "center" if s.startswith(":") and s.endswith(":") else "left" for s in sep]
    total = 9038
    peso = [max(13, min(60, max(len(re.sub(r"\*", "", l[j])) for l in cel if j < len(l)))) for j in range(len(cab))]
    larg = [int(total * x / sum(peso)) for x in peso]
    borda = "".join(f'<w:{b} w:val="single" w:sz="6" w:space="0" w:color="C4C7C5"/>' for b in ("top", "left", "bottom", "right"))

    def celula(t, w, jc, negrito):
        t = t.replace("&", "&amp;").replace("<", "&lt;")
        b = "<w:b/>" if negrito or t.startswith("**") else ""
        t = t.replace("**", "")
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:tcBorders>{borda}</w:tcBorders>'
                f'<w:tcMar><w:top w:w="40" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/>'
                f'<w:right w:w="100" w:type="dxa"/></w:tcMar><w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/><w:jc w:val="{jc}"/></w:pPr>'
                f'<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>{b}<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
                f'<w:t xml:space="preserve">{t}</w:t></w:r></w:p></w:tc>')

    xml = (f'<w:tbl xmlns:w="{W}"><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
           f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
           f'<w:tblGrid>{"".join(f"<w:gridCol w:w=\"{x}\"/>" for x in larg)}</w:tblGrid>'
           f'<w:tr><w:trPr><w:tblHeader/></w:trPr>{"".join(celula(c, larg[j], "center", True) for j, c in enumerate(cab))}</w:tr>'
           + "".join(f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{"".join(celula(l[j] if j < len(l) else "", larg[j], alin[j], False) for j in range(len(cab)))}</w:tr>' for l in dados)
           + "</w:tbl>")
    return etree.fromstring(xml)


def por(el):
    SECT.addprevious(el)


# ---------------------------------------------------------------- conteúdo dos rascunhos
def blocos(md: str):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    linhas = md.splitlines()
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("## "))
    fim = next((i for i, l in enumerate(linhas) if l.strip() == "---" and i > inicio), len(linhas))
    bloco: list[str] = []
    for l in linhas[inicio:fim] + [""]:
        if l.strip():
            bloco.append(l.rstrip())
        elif bloco:
            yield bloco
            bloco = []


def capitulo(arquivo: str):
    for b in blocos((TCC / arquivo).read_text(encoding="utf-8")):
        primeira = b[0]
        m = re.match(r"^(#{2,4}) (.+)", primeira)
        if m:
            nivel = len(m.group(1)) - 1
            if nivel == 1:
                por(copy.deepcopy(QUEBRA))
            elif estilo(SECT.getprevious()) not in ("Ttulo1", "Ttulo2", "Ttulo3") and texto(SECT.getprevious()):
                por(copy.deepcopy(BRANCO))
            p = _limpa(copy.deepcopy(H[nivel]))
            p.append(_run(_rpr(H[nivel]), m.group(2)))
            por(p)
            por(copy.deepcopy(BRANCO))
            continue
        if primeira.startswith("[^"):
            chave, t = re.match(r"\[\^(\w+)\]:\s*(.*)", " ".join(b)).groups()
            NOTAS[chave] = t
            continue
        junto = " ".join(x.strip() for x in b)
        if primeira.startswith("Figura "):
            por(legenda_figura(junto))
        elif primeira.startswith("!["):
            imagem(TCC / re.search(r"\((.+?)\)", primeira).group(1))
        elif primeira.startswith("Fonte:"):
            por(paragrafo(FONTE, junto))
        elif re.match(r"^(Tabela|Quadro) \d+", primeira):
            por(paragrafo(LEG_TABELA, junto))
        elif primeira.startswith("|"):
            por(tabela(b))
        elif re.match(r"^[a-k]\) ", primeira):
            por(paragrafo(LISTA, junto))
        else:
            por(paragrafo(CORPO, junto))


def secao(md: str, titulo: str) -> list[list[str]]:
    texto_secao = md.split(f"## {titulo}\n", 1)[1].split("\n## ", 1)[0]
    return list(blocos(f"## x\n{texto_secao}"))[1:]


# Notas de rodapé dos rascunhos são definidas antes do uso no arquivo; lê todas primeiro.
for arq in ("capitulo-4-rascunho.md", "capitulo-5-rascunho.md", "capitulo-6-rascunho.md"):
    for k, t in re.findall(r"^\[\^(\w+)\]:\s*((?:.+\n?)+?)(?=\n\n|\Z)", (TCC / arq).read_text(encoding="utf-8"), re.M):
        NOTAS[k] = " ".join(t.split())

# 1. apaga Caps. 4 em diante (e Referências) e escreve de novo
for el in list(body)[i_h4:-1]:
    body.remove(el)
for arq in ("capitulo-4-rascunho.md", "capitulo-5-rascunho.md", "capitulo-6-rascunho.md"):
    capitulo(arq)

pre = (TCC / "pre-e-pos-textuais.md").read_text(encoding="utf-8")
por(copy.deepcopy(QUEBRA))
ref_h = _limpa(copy.deepcopy(H[1]))
ref_h.append(_run(_rpr(H[1]), "REFERÊNCIAS"))
por(ref_h)
por(copy.deepcopy(VAZIO))
REF = copy.deepcopy(CORPO)
ppr = REF.find(qn("w:pPr"))
for tag in ("w:ind", "w:jc", "w:spacing"):
    x = ppr.find(qn(tag))
    if x is not None:
        ppr.remove(x)
etree.SubElement(ppr, qn("w:spacing")).attrib.update({qn("w:after"): "240", qn("w:line"): "240", qn("w:lineRule"): "auto"})
for b in secao(pre, "REFERÊNCIAS"):
    por(paragrafo(REF, " ".join(b)))

# 2. padroniza Caps. 1–3: parágrafos vazios antes de cada capítulo viram uma quebra de página
for i, el in reversed(list(enumerate(body))):
    if el.tag == qn("w:p") and estilo(el) == "Ttulo1" and re.match(r"^[23] ", texto(el)):
        j = i - 1
        while j > 0 and body[j].tag == qn("w:p") and not texto(body[j]) and not list(body[j].iter(qn("w:drawing"))) \
                and body[j].find(qn("w:pPr") + "/" + qn("w:sectPr")) is None:
            j -= 1
        for k in range(i - 1, j, -1):
            body.remove(body[k])
        body[j].addnext(copy.deepcopy(QUEBRA))
for el in body.iter(qn("w:p")):
    t = texto(el)
    if re.match(r"^Figura \d", t):
        for r in el.iter(qn("w:t")):
            if r.text and re.match(r"^\s*-\s", r.text):
                r.text = re.sub(r"^\s*-\s", " – ", r.text)
            elif r.text and " - " in r.text:
                r.text = r.text.replace(" - ", " – ", 1)
    if t.startswith("Fonte: Elaborada pelo autor"):
        for r in el.iter(qn("w:t")):
            if r.text and "pelo autor" in r.text:
                r.text = r.text.replace("pelo autor", "pelos autores")
        if texto(el).strip() == "Fonte: Elaborada pelos autores":
            ultimo = [r for r in el.iter(qn("w:t")) if r.text][-1]
            ultimo.text = ultimo.text.rstrip() + " (2026)."

# 3. pré-textuais: siglas (em página própria), resumo e abstract
i_sig = achar(lambda p: texto(p).strip() == "LISTA DE SIGLAS")
j = i_sig - 1
while body[j].tag == qn("w:p") and not texto(body[j]) and not list(body[j].iter(qn("w:fldChar"))):
    body.remove(body[j])
    j -= 1
i_sig = achar(lambda p: texto(p).strip() == "LISTA DE SIGLAS")
body[i_sig].addprevious(copy.deepcopy(QUEBRA))
i_sig += 1
i_fim_pre = achar(lambda p: p.find(qn("w:pPr") + "/" + qn("w:sectPr")) is not None, i_sig)
for el in [e for e in body[i_sig + 1:i_fim_pre] if texto(e).strip()]:
    body.remove(el)
i_fim_pre = achar(lambda p: p.find(qn("w:pPr") + "/" + qn("w:sectPr")) is not None, i_sig)
ancora = body[i_fim_pre]
linhas_sigla = [l for l in pre.split("## LISTA DE SIGLAS\n", 1)[1].split("\n## ", 1)[0].splitlines() if l.startswith("|")][2:]
for l in linhas_sigla:
    sigla, signif = [c.strip() for c in l.strip("|").split("|")]
    p = _limpa(copy.deepcopy(SIGLA))
    rpr = _rpr(SIGLA)
    p.append(_run(rpr, sigla))
    r = etree.SubElement(p, qn("w:r"))
    r.append(copy.deepcopy(rpr))
    etree.SubElement(r, qn("w:tab"))
    etree.SubElement(r, qn("w:tab"))  # dois tabs, como no template, alinham a coluna
    p.append(_run(rpr, signif))
    ancora.addprevious(p)
for titulo in ("RESUMO", "ABSTRACT"):
    ancora.addprevious(copy.deepcopy(QUEBRA))
    t = _limpa(copy.deepcopy(TITULO_PRE))
    t.append(_run(_rpr(TITULO_PRE), titulo))
    ancora.addprevious(t)
    ancora.addprevious(copy.deepcopy(VAZIO))
    for b in secao(pre, titulo):
        junto = " ".join(b)
        if junto.startswith(("Palavras-chave:", "Key words:")):
            ancora.addprevious(copy.deepcopy(VAZIO))
            rotulo, resto = junto.split(":", 1)
            p = paragrafo(CORPO, f"**{rotulo}:**{resto}")
        else:
            p = paragrafo(CORPO, junto)
        ancora.addprevious(p)

# 4. notas de rodapé e comentários antigos (os do .docx de 13/10 estão resolvidos)
def _xml(parte):
    if hasattr(parte, "_element"):
        return parte._element, lambda raiz: None
    raiz = etree.fromstring(parte.blob)

    def gravar(r):
        parte._blob = etree.tostring(r, xml_declaration=True, encoding="UTF-8", standalone=True)
    return raiz, gravar


for rel in d.part.rels.values():
    if rel.reltype.endswith("/footnotes"):
        parte = rel.target_part
        raiz, gravar = _xml(parte)
        for i, t in NOTAS_USADAS:
            raiz.append(etree.fromstring(
                f'<w:footnote xmlns:w="{W}" w:id="{i}"><w:p><w:pPr><w:pStyle w:val="Textodenotaderodap"/><w:jc w:val="both"/></w:pPr>'
                f'<w:r><w:rPr><w:rStyle w:val="Refdenotaderodap"/></w:rPr><w:footnoteRef/></w:r>'
                f'<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="20"/></w:rPr>'
                f'<w:t xml:space="preserve"> {t}</w:t></w:r></w:p></w:footnote>'))
        gravar(raiz)
    if "comments" in rel.reltype:
        raiz, gravar = _xml(rel.target_part)
        for filho in list(raiz):
            raiz.remove(filho)
        gravar(raiz)
for tag in ("w:commentRangeStart", "w:commentRangeEnd"):
    for el in list(body.iter(qn(tag))):
        el.getparent().remove(el)
for el in list(body.iter(qn("w:commentReference"))):
    r = el.getparent()
    r.getparent().remove(r)

d.save(str(SAIDA))
print("gravado:", SAIDA)

# 5. Word, se houver: atualiza sumário, listas e numeração; exporta PDF para conferência
ps = f"""
$w = New-Object -ComObject Word.Application; $w.Visible = $false
$doc = $w.Documents.Open('{SAIDA}')
$doc.Fields.Update() | Out-Null
foreach ($t in $doc.TablesOfContents) {{ $t.Update() }}
foreach ($t in $doc.TablesOfFigures) {{ $t.Update() }}
$doc.Save()
$doc.ExportAsFixedFormat('{SAIDA.with_suffix(".pdf")}', 17)
$doc.Close(); $w.Quit()
"""
if "--sem-word" not in sys.argv:
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    print("Word:", "ok" if r.returncode == 0 else r.stderr[-800:])
