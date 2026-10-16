"""Painel da pesquisa (Sprint 16, V8): os resultados do Cap. 5 dentro do app.

Os numeros NAO sao recalculados nem copiados: a tela e montada das proprias
tabelas de `docs/resultados/`, geradas pelos scripts sobre o dataset completo
(o banco da aplicacao tem so a amostra). Rodou o script de novo, a tela muda.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

from src.schemas.sdui import (
    ContentSectionBlock,
    ContentSectionProps,
    DataTableBlock,
    DataTableProps,
    DataTableRowProps,
    HeroBannerBlock,
    HeroBannerProps,
    NavigateAction,
    NavigatePayload,
    ScreenResponse,
)

RESULTADOS = Path(__file__).resolve().parents[3] / "docs" / "resultados"
# Ordem da tela = a pergunta que cada um responde: ha onde comprar perto? a
# recomendacao reduz CO2? a distancia em linha reta e confiavel? e se os
# parametros do motor estiverem errados?
ARQUIVOS = ("concentracao-regional.md", "co2-evitado.md", "haversine-osrm.md", "sensibilidade-co2.md")


def _limpo(texto: str) -> str:
    return texto.replace("**", "").replace("`", "").strip()


def _celulas(linha: str) -> list[str]:
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def blocos_do_markdown(md: str) -> list[ContentSectionBlock | DataTableBlock]:
    """`#`/`##` abrem um grupo de texto; uma tabela logo apos um `##` herda o
    titulo e o texto dele como legenda. Linha cuja 1a celula esta em negrito
    (ex.: **Brasil**, **todas**) vira destaque.

    ponytail: so o subconjunto de Markdown que os scripts de `scripts/` escrevem
    (titulo, citacao, lista, paragrafo de uma linha, tabela); `tests/test_pesquisa.py`
    quebra se um script mudar de formato.
    """
    blocos: list[ContentSectionBlock | DataTableBlock] = []
    grupo: dict | None = None
    tabela: list[list[str]] = []

    def fechar_grupo() -> None:
        nonlocal grupo
        if grupo and (grupo["paragraphs"] or grupo["items"] or grupo["note"] or grupo["nivel"] == 1):
            blocos.append(ContentSectionBlock(props=ContentSectionProps(
                title=grupo["title"], paragraphs=grupo["paragraphs"], items=grupo["items"],
                note=" ".join(grupo["note"]) or None,
            )))
        grupo = None

    def fechar_tabela() -> None:
        nonlocal grupo
        if not tabela:
            return
        titulo = legenda = None
        if grupo and grupo["nivel"] == 2 and not grupo["items"] and not grupo["note"]:
            titulo, legenda = grupo["title"], " ".join(grupo["paragraphs"]) or None
            grupo = None
        else:
            fechar_grupo()
        cabecalho, *linhas = tabela
        blocos.append(DataTableBlock(props=DataTableProps(
            title=titulo, caption=legenda, columns=[_limpo(c) for c in cabecalho],
            rows=[DataTableRowProps(cells=[_limpo(c) for c in l], emphasis=l[0].startswith("**")) for l in linhas],
        )))
        tabela.clear()

    for bruta in md.splitlines():
        linha = bruta.strip()
        if linha.startswith("|"):
            if not set(linha) <= set("|-: "):  # separador | --- |
                tabela.append(_celulas(linha))
            continue
        fechar_tabela()
        if not linha:
            continue
        if linha.startswith("#"):
            fechar_grupo()
            nivel = len(linha) - len(linha.lstrip("#"))
            grupo = {"nivel": nivel, "title": _limpo(linha.lstrip("#")), "paragraphs": [], "items": [], "note": []}
        elif grupo is None:
            # Nota logo abaixo de uma tabela (ex.: como o preco foi medido): vai na legenda dela.
            if blocos and isinstance(blocos[-1], DataTableBlock):
                anterior = blocos[-1].props
                anterior.caption = f"{anterior.caption} {_limpo(linha)}" if anterior.caption else _limpo(linha)
        elif linha.startswith(">"):
            grupo["note"].append(_limpo(linha.lstrip(">")))
        elif linha.startswith("- "):
            grupo["items"].append(_limpo(linha[2:]))
        elif grupo["items"] and bruta.startswith("  "):  # continuacao de item
            grupo["items"][-1] += " " + _limpo(linha)
        else:
            grupo["paragraphs"].append(_limpo(linha))
    fechar_tabela()
    fechar_grupo()
    return blocos


@lru_cache(maxsize=1)
def _blocos() -> tuple[ContentSectionBlock | DataTableBlock, ...]:
    # Lido uma vez por processo: os arquivos so mudam quando um script roda de novo.
    return tuple(b for nome in ARQUIVOS for b in blocos_do_markdown((RESULTADOS / nome).read_text(encoding="utf-8")))


def compose_pesquisa(customer_zip_prefix: str | None = None) -> ScreenResponse:
    volta = "/?" + urlencode({"customer_zip_prefix": customer_zip_prefix}) if customer_zip_prefix else "/"
    metodologia = "/metodologia" + ("?" + urlencode({"customer_zip_prefix": customer_zip_prefix}) if customer_zip_prefix else "")
    return ScreenResponse(
        screen_id="research",
        context="research",
        components=[
            HeroBannerBlock(
                props=HeroBannerProps(
                    title="O que a pesquisa encontrou",
                    subtitle=(
                        "Os resultados do TCC sobre as compras reais do Olist completo: onde há oferta "
                        "local, quanto CO₂ a recomendação evitaria e quanto vale a distância em linha reta."
                    ),
                    image_url="",
                    cta_label="Voltar à vitrine",
                    secondary_cta_label="Como calculamos",
                ),
                actions=[
                    NavigateAction(payload=NavigatePayload(path=volta)),
                    NavigateAction(payload=NavigatePayload(path=metodologia)),
                ],
            ),
            *_blocos(),
        ],
    )
