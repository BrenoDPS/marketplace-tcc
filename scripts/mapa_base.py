"""Gera o fundo do mapa de origem: o Brasil desenhado pelos proprios CEPs.

    python -m scripts.mapa_base      # grava web/public/mapa-brasil.svg

Sem shapefile nem biblioteca de mapas: cada ponto e uma celula de 0,25 grau com
pelo menos um centroide de CEP do dataset (`cep_centroids`). A silhueta que
aparece e a do pais onde o Olist entrega — e o vazio da Amazonia tambem e dado.
Rodar de novo so se o ETL mudar a amostra.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from scripts.etl_load_sample import _sync_database_url
from src.features.green_logistics.mapa import ALTURA, LARGURA, dentro_do_brasil, projetar

SAIDA = Path("web/public/mapa-brasil.svg")
CELULA = 0.25  # graus


def main() -> None:
    engine = create_engine(_sync_database_url())
    with engine.connect() as conn:
        pontos = conn.execute(text("SELECT lat, lng FROM cep_centroids")).all()
    engine.dispose()

    celulas = {
        (round(lat / CELULA) * CELULA, round(lng / CELULA) * CELULA)
        for lat, lng in pontos
        if dentro_do_brasil(lat, lng)
    }
    circulos = "".join(
        f'<circle cx="{x:.0f}" cy="{y:.0f}" r="1.7"/>'
        for x, y in sorted(projetar(lat, lng) for lat, lng in celulas)
    )
    # Cinza medio translucido: o arquivo e carregado por <image>, que nao herda
    # o tema da pagina, entao a cor tem de funcionar no claro e no escuro.
    SAIDA.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGURA} {ALTURA}">'
        f'<g fill="#8a8178" fill-opacity="0.38">{circulos}</g></svg>\n',
        encoding="utf-8",
    )
    print(SAIDA, f"{len(celulas)} celulas de {len(pontos)} centroides", f"{SAIDA.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
