"""ETL Sprint 2: carrega amostra Olist (~10000 order_items, seed=42) no Postgres.

Fluxo:
1. Le CSVs em data/raw/.
2. Amostra 10000 linhas de olist_order_items_dataset.csv com seed=42 e COMPLETA
   as ofertas dos produtos sorteados — ver `sample_order_items`, que explica
   por que a amostra crua trazia produto pela metade.
3. Filtra rows com product_weight_g valido e CEPs presentes nos lookups.
4. Deriva subset de orders/customers/sellers/products e geolocation por prefixo.
5. Deriva `offers` (produto, vendedor) a partir de order_items.
6. Calcula centroides via mediana de lat/lng por prefixo.
7. Carrega tudo no Postgres (drop+create do schema, sem migrations nesta sprint).
8. Imprime um par (customer_prefix, seller_prefix) com distancia Haversine < 100 km
   e o melhor caso multi-vendedor, para servirem de demo no README.

Execucao:
    python -m scripts.etl_load_sample [--data-dir data/raw] [--sample-size 10000] [--seed 42]

Variavel de ambiente: DATABASE_URL (asyncpg ou psycopg). O script forca driver
sincrono `postgresql+psycopg` para usar com SQLAlchemy + pandas.to_sql.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from src.core.config import settings
from src.core.models import Base
from src.features.green_logistics.co2 import VOLUMETRIC_FACTOR_CM3_PER_KG
from src.features.green_logistics.delivery_options import ETA_BANDS

DEFAULT_SAMPLE_SIZE = 10000
DEFAULT_SEED = 42
DEFAULT_DATA_DIR = "data/raw"
DISTANCE_THRESHOLD_KM = 100.0


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

CSV_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
}


def load_csvs(data_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for key, name in CSV_FILES.items():
        path = data_dir / name
        if not path.exists():
            raise FileNotFoundError(f"CSV ausente: {path}")
        frames[key] = pd.read_csv(path)
    return frames


# ---------------------------------------------------------------------------
# Sampling + filtering
# ---------------------------------------------------------------------------

def _pad_prefix(value: object) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return str(int(value)).zfill(5)


def normalize_prefixes(frames: dict[str, pd.DataFrame]) -> None:
    frames["customers"]["customer_zip_code_prefix"] = (
        frames["customers"]["customer_zip_code_prefix"].map(_pad_prefix)
    )
    frames["sellers"]["seller_zip_code_prefix"] = (
        frames["sellers"]["seller_zip_code_prefix"].map(_pad_prefix)
    )
    frames["geolocation"]["geolocation_zip_code_prefix"] = (
        frames["geolocation"]["geolocation_zip_code_prefix"].map(_pad_prefix)
    )


def sample_order_items(
    items: pd.DataFrame, n: int = DEFAULT_SAMPLE_SIZE, seed: int = DEFAULT_SEED
) -> pd.DataFrame:
    """Sorteia `n` order_items e COMPLETA as ofertas dos produtos sorteados.

    Sortear `order_items` por linha trazia produtos pela metade: o dataset tem
    dois vendedores para um item, a amostra mostrava um so. Medido na amostra
    de 10 mil linhas — **528 produtos truncados, e 474 deles viram
    multi-vendedor apenas completando**. O produto entrava no catalogo com
    parte das suas origens escondida.

    Isso apagava justamente a comparacao que o trabalho defende ("mesmo item,
    duas origens, a mais perto emite menos"): sobravam 106 produtos com mais de
    um vendedor, 1,6% contra 3,7% do universo. Completando, sao 580 (8,8%), sem
    sortear nenhum produto a mais.

    A correcao e de ARTEFATO, nao estratificacao: o conjunto de produtos
    continua sendo o sorteio aleatorio de antes, e a amostra base e um
    subconjunto do resultado. Nada e super-representado de proposito.

    Sobre os 8,8% contra 3,7% do universo: sortear por LINHA pesa cada produto
    pelo numero de pedidos em que ele aparece, entao produtos populares entram
    mais — e produto popular tende a ter mais de um vendedor. A amostra e
    ponderada por popularidade, nao uniforme sobre o catalogo. Isso e mais
    parecido com o que um comprador encontra, mas precisa ser dito ao citar
    proporcoes.
    """
    base = items.sample(n=min(n, len(items)), random_state=seed)
    produtos = set(base["product_id"])
    return items[items["product_id"].isin(produtos)].reset_index(drop=True)


def filter_valid(
    frames: dict[str, pd.DataFrame],
    items_sample: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Filtra subset coerente: produtos com peso valido, CEPs com geolocation."""

    products = frames["products"].copy()
    products = products[products["product_weight_g"].notna() & (products["product_weight_g"] > 0)]
    # Volume das tres dimensoes do dataset. Produto sem alguma delas fica com
    # volume nulo e cai no peso real — nao inventamos caixa.
    products["product_volume_cm3"] = (
        products["product_length_cm"]
        * products["product_height_cm"]
        * products["product_width_cm"]
    )

    valid_geo_prefixes = set(
        frames["geolocation"]["geolocation_zip_code_prefix"].dropna().unique()
    )

    customers = frames["customers"].copy()
    customers = customers[customers["customer_zip_code_prefix"].isin(valid_geo_prefixes)]

    sellers = frames["sellers"].copy()
    sellers = sellers[sellers["seller_zip_code_prefix"].isin(valid_geo_prefixes)]

    valid_product_ids = set(products["product_id"])
    valid_seller_ids = set(sellers["seller_id"])

    items = items_sample[
        items_sample["product_id"].isin(valid_product_ids)
        & items_sample["seller_id"].isin(valid_seller_ids)
    ].copy()

    orders = frames["orders"]
    orders = orders[orders["order_id"].isin(items["order_id"])]
    orders = orders[orders["customer_id"].isin(customers["customer_id"])]

    items = items[items["order_id"].isin(orders["order_id"])]
    customers = customers[customers["customer_id"].isin(orders["customer_id"])]
    products = products[products["product_id"].isin(items["product_id"])]
    sellers = sellers[sellers["seller_id"].isin(items["seller_id"])]

    return {
        "orders": orders.reset_index(drop=True),
        "order_items": items.reset_index(drop=True),
        "customers": customers.reset_index(drop=True),
        "sellers": sellers.reset_index(drop=True),
        "products": products.reset_index(drop=True),
        "geolocation": frames["geolocation"],
    }


def attach_product_ratings(
    products: pd.DataFrame, items: pd.DataFrame, reviews: pd.DataFrame
) -> pd.DataFrame:
    """Media e contagem de `review_score` por produto.

    A nota e do PEDIDO no Olist, nao do produto — nao existe avaliacao por item.
    Atribuir a nota do pedido a cada produto dele e uma aproximacao, mas os
    numeros sao reais: nada aqui e gerado. Produto sem pedido avaliado fica com
    `rating` nulo, e a tela omite em vez de inventar.
    """
    scored = items[["order_id", "product_id"]].merge(
        reviews[["order_id", "review_score"]], on="order_id", how="inner"
    )
    agg = (
        scored.groupby("product_id")["review_score"]
        .agg(rating="mean", review_count="count")
        .reset_index()
    )
    agg["rating"] = agg["rating"].round(2)

    out = products.merge(agg, on="product_id", how="left")
    out["review_count"] = out["review_count"].fillna(0).astype(int)
    return out


def build_offers(items: pd.DataFrame) -> pd.DataFrame:
    """Deriva `offers` de `order_items`: uma linha por (produto, vendedor).

    Preco e frete saem da PRIMEIRA linha da oferta na ordem `(order_id,
    order_item_id)`, e nao de uma media, para reproduzir exatamente o que as
    telas mostram hoje — assim a troca de `order_items` por `offers` e
    verificavel por diff, e nao por impressao.

    `is_default` marca, para cada produto, a oferta que vem primeiro nessa
    mesma ordem: e a "primeira order_item" que `product_detail` e `checkout`
    ja usavam como criterio de desempate.
    """
    # ponytail: primeira linha em vez de mediana de preco. 8,2% das ofertas da
    # amostra tem mais de um preco (dispersao ~15%) e 17,9% mais de um frete —
    # a mediana seria mais representativa do catalogo, mas mudaria os numeros
    # exibidos e tiraria a verificabilidade do refactor. Trocar depois que a
    # migracao das telas estiver fechada e conferida.
    ordered = items.sort_values(["order_id", "order_item_id"])
    offers = ordered.groupby(["product_id", "seller_id"], as_index=False).agg(
        price=("price", "first"),
        freight_value=("freight_value", "first"),
        order_id=("order_id", "first"),
        order_item_id=("order_item_id", "first"),
    )

    # `duplicated` olha a ordem corrente das linhas: ordenar antes nao e
    # cosmetico, e o que define QUAL oferta vira a default.
    offers = offers.sort_values(["product_id", "order_id", "order_item_id"])
    offers["is_default"] = ~offers.duplicated("product_id")
    return offers.reset_index(drop=True)


def build_cep_centroids(geolocation: pd.DataFrame, prefixes: set[str]) -> pd.DataFrame:
    geo = geolocation[geolocation["geolocation_zip_code_prefix"].isin(prefixes)]
    centroids = (
        geo.groupby("geolocation_zip_code_prefix")
        .agg(lat=("geolocation_lat", "median"), lng=("geolocation_lng", "median"))
        .reset_index()
        .rename(columns={"geolocation_zip_code_prefix": "zip_prefix"})
    )
    return centroids


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _sync_database_url() -> str:
    """Converte URL asyncpg -> psycopg para uso sincrono no ETL."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def reset_schema(engine: Engine) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def load_tables(
    engine: Engine, subset: dict[str, pd.DataFrame], centroids: pd.DataFrame
) -> None:
    pipeline: list[tuple[str, pd.DataFrame, list[str]]] = [
        (
            "olist_customers",
            subset["customers"],
            ["customer_id", "customer_zip_code_prefix", "customer_city", "customer_state"],
        ),
        (
            "olist_sellers",
            subset["sellers"],
            ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
        ),
        (
            "olist_products",
            subset["products"],
            [
                "product_id",
                "product_category_name",
                "product_weight_g",
                "product_volume_cm3",
                "rating",
                "review_count",
            ],
        ),
        (
            "olist_orders",
            subset["orders"],
            ["order_id", "customer_id", "order_status"],
        ),
        (
            "olist_order_items",
            subset["order_items"],
            ["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"],
        ),
        (
            "offers",
            subset["offers"],
            ["product_id", "seller_id", "price", "freight_value", "is_default"],
        ),
        (
            "cep_centroids",
            centroids,
            ["zip_prefix", "lat", "lng"],
        ),
    ]
    for table, df, cols in pipeline:
        payload = df[cols].drop_duplicates()
        payload.to_sql(table, engine, if_exists="append", index=False, chunksize=500)


# ---------------------------------------------------------------------------
# Demo pair (customer_prefix, seller_prefix) com d < 100 km
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def pick_demo_pair(
    items: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
    centroids: pd.DataFrame,
) -> tuple[str, str, float] | None:
    centroid_map = {
        row.zip_prefix: (row.lat, row.lng) for row in centroids.itertuples(index=False)
    }
    cust_prefix = dict(
        zip(customers["customer_id"], customers["customer_zip_code_prefix"], strict=False)
    )
    sell_prefix = dict(
        zip(sellers["seller_id"], sellers["seller_zip_code_prefix"], strict=False)
    )

    pairs_seen: set[tuple[str, str]] = set()
    for it in items.itertuples(index=False):
        cp = cust_prefix.get(getattr(it, "customer_id", None))
        sp = sell_prefix.get(it.seller_id)
        if not cp or not sp or (cp, sp) in pairs_seen:
            continue
        pairs_seen.add((cp, sp))
        c, s = centroid_map.get(cp), centroid_map.get(sp)
        if not c or not s:
            continue
        d = _haversine(c[0], c[1], s[0], s[1])
        if d < DISTANCE_THRESHOLD_KM:
            return cp, sp, d
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def derive_eta_bands(
    frames: dict[str, pd.DataFrame], centroids_all: dict[str, tuple[float, float]]
) -> list[tuple[float, float, int]]:
    """Prazo real por faixa de distancia: `(limite_km, dias_p50, n)`.

    Sai do dataset COMPLETO, nao da amostra: a relacao distancia -> prazo e uma
    propriedade do Olist inteiro, e os 96 mil pedidos entregues dao estimativa
    melhor que o subconjunto que vira catalogo. Por isso o resultado nao muda
    com `--sample-size`, e pode viver como constante no codigo.

    Existe para CONFERIR `ETA_BANDS` em `delivery_options.py`. Sem esta
    rederivacao a tabela viraria numero magico que ninguem sabe de onde veio.
    """
    orders = frames["orders"]
    entregues = orders.dropna(subset=["order_delivered_customer_date"]).copy()
    for col in ("order_purchase_timestamp", "order_delivered_customer_date"):
        entregues[col] = pd.to_datetime(entregues[col], errors="coerce")

    # Um vendedor por pedido (o primeiro): pedido multi-vendedor tem mais de uma
    # origem e nao ha como atribuir o prazo a uma delas.
    primeiro = frames["order_items"][["order_id", "seller_id"]].drop_duplicates("order_id")
    cliente = frames["customers"][["customer_id", "customer_zip_code_prefix"]]
    vendedor = frames["sellers"][["seller_id", "seller_zip_code_prefix"]]

    base = (
        primeiro.merge(
            entregues[
                ["order_id", "customer_id", "order_purchase_timestamp",
                 "order_delivered_customer_date"]
            ],
            on="order_id",
        )
        .merge(cliente, on="customer_id")
        .merge(vendedor, on="seller_id")
    )

    def _km(row: object) -> float:
        c = centroids_all.get(getattr(row, "customer_zip_code_prefix", None))
        s = centroids_all.get(getattr(row, "seller_zip_code_prefix", None))
        if not c or not s:
            return float("nan")
        return _haversine(c[0], c[1], s[0], s[1])

    base["km"] = [_km(row) for row in base.itertuples(index=False)]
    base["dias"] = (
        base["order_delivered_customer_date"] - base["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    # Prazo negativo ou absurdo e erro de registro, nao entrega lenta.
    base = base[base["km"].notna() & (base["dias"] > 0) & (base["dias"] < 90)]

    saida: list[tuple[float, float, int]] = []
    anterior = 0.0
    for limite in (50.0, 100.0, 300.0, 600.0, 1200.0, float("inf")):
        faixa = base[(base["km"] >= anterior) & (base["km"] < limite)]
        if len(faixa):
            saida.append((limite, round(float(faixa["dias"].median()), 1), len(faixa)))
        anterior = limite
    return saida


def pick_demo_multi_seller(
    offers: pd.DataFrame, sellers: pd.DataFrame, centroids: pd.DataFrame
) -> tuple[str, float, list[tuple[str, str]]] | None:
    """Produto com dois vendedores o mais longe possivel um do outro.

    E o caso de demonstracao da tese: mesmo item, duas origens, e a escolha
    entre elas muda a emissao. Sem isto a amostra estratificada existe mas
    ninguem sabe qual produto abrir na defesa.
    """
    centroid_map = {
        row.zip_prefix: (row.lat, row.lng) for row in centroids.itertuples(index=False)
    }
    prefixo = dict(
        zip(sellers["seller_id"], sellers["seller_zip_code_prefix"], strict=False)
    )
    cidade = dict(zip(sellers["seller_id"], sellers["seller_city"], strict=False))
    uf = dict(zip(sellers["seller_id"], sellers["seller_state"], strict=False))

    contagem = offers.groupby("product_id")["seller_id"].transform("size")
    candidatos = offers[contagem > 1]

    melhor: tuple[str, float, list[tuple[str, str]]] | None = None
    for product_id, grupo in candidatos.groupby("product_id"):
        pontos = [
            (sid, centroid_map[prefixo[sid]])
            for sid in grupo["seller_id"]
            if prefixo.get(sid) in centroid_map
        ]
        if len(pontos) < 2:
            continue
        # Par a par: um produto tem no maximo 8 vendedores no Olist, entao sao
        # 28 distancias no pior caso. Nao vale indice espacial.
        for i in range(len(pontos)):
            for j in range(i + 1, len(pontos)):
                (_, (lat1, lng1)), (_, (lat2, lng2)) = pontos[i], pontos[j]
                d = _haversine(lat1, lng1, lat2, lng2)
                if melhor is None or d > melhor[1]:
                    melhor = (
                        product_id,
                        d,
                        [
                            (f"{cidade.get(sid)}/{uf.get(sid)}", prefixo.get(sid, "?"))
                            for sid, _ in pontos
                        ],
                    )
    return melhor


def main() -> int:
    parser = argparse.ArgumentParser(description="ETL Olist sample loader (Sprint 2)")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    print(f"[etl] lendo CSVs em {data_dir.resolve()}")
    frames = load_csvs(data_dir)
    normalize_prefixes(frames)

    print(f"[etl] amostrando {args.sample_size} order_items (seed={args.seed})")
    items_sample = sample_order_items(
        frames["order_items"], n=args.sample_size, seed=args.seed
    )
    print(
        f"[etl] ofertas completadas: {len(items_sample)} order_items cobrindo "
        f"todos os vendedores dos produtos sorteados (amostra ponderada por "
        f"popularidade — declarar ao citar proporcoes)"
    )

    subset = filter_valid(frames, items_sample)
    subset["products"] = attach_product_ratings(
        subset["products"], subset["order_items"], frames["reviews"]
    )
    subset["offers"] = build_offers(subset["order_items"])
    multi = int(
        (subset["offers"].groupby("product_id")["seller_id"].size() > 1).sum()
    )
    rated = int((subset["products"]["review_count"] > 0).sum())
    print(
        "[etl] subset filtrado:",
        {k: len(v) for k, v in subset.items() if k != "geolocation"},
    )
    print(f"[etl] produtos com avaliacao real: {rated}/{len(subset['products'])}")
    print(
        f"[etl] ofertas derivadas: {len(subset['offers'])} "
        f"({multi} produtos com mais de um vendedor)"
    )
    cubado = (
        subset["products"]["product_volume_cm3"] / VOLUMETRIC_FACTOR_CM3_PER_KG * 1000.0
    )
    domina = (cubado > subset["products"]["product_weight_g"]).mean()
    print(
        f"[etl] peso cubado supera o real em {domina * 100:.1f}% dos produtos "
        f"— e ele que entra no calculo de CO2 (ver co2.chargeable_weight_g)"
    )

    items_with_customer = subset["order_items"].merge(
        subset["orders"][["order_id", "customer_id"]], on="order_id", how="left"
    )

    prefixes = set(subset["customers"]["customer_zip_code_prefix"]) | set(
        subset["sellers"]["seller_zip_code_prefix"]
    )
    centroids = build_cep_centroids(subset["geolocation"], prefixes)
    print(f"[etl] centroides calculados: {len(centroids)} prefixos")

    engine = create_engine(_sync_database_url(), future=True)
    reset_schema(engine)
    load_tables(engine, subset, centroids)
    print("[etl] tabelas carregadas no Postgres")

    demo = pick_demo_pair(
        items_with_customer, subset["customers"], subset["sellers"], centroids
    )
    if demo:
        cp, sp, d = demo
        print(
            f"[etl] DEMO PAIR (badge presente): "
            f"customer_zip_prefix={cp}, seller_zip_prefix={sp}, distance_km={d:.1f}"
        )
    else:
        print("[etl] aviso: nenhum par com distancia < 100 km encontrado nesta amostra")

    # Confere `ETA_BANDS` contra o dataset. Nao carrega nada: a tabela vive no
    # codigo porque sai dos CSVs, que sao fixos. O que este passo compra e o
    # aviso quando alguem mexer nela sem rederivar.
    todos_centroides = build_cep_centroids(
        frames["geolocation"],
        set(frames["geolocation"]["geolocation_zip_code_prefix"].dropna().unique()),
    )
    mapa = {
        row.zip_prefix: (row.lat, row.lng)
        for row in todos_centroides.itertuples(index=False)
    }
    faixas = derive_eta_bands(frames, mapa)
    print("[etl] prazo real de entrega por faixa de distancia:")
    divergiu = False
    for (limite, dias, n), (lim_cod, dias_cod) in zip(faixas, ETA_BANDS, strict=False):
        rot = "inf" if limite == float("inf") else f"{limite:.0f}"
        marca = ""
        if limite != lim_cod or abs(dias - dias_cod) > 0.05:
            marca = f"  <<< DIVERGE de delivery_options.ETA_BANDS ({dias_cod})"
            divergiu = True
        print(f"[etl]   ate {rot:>5} km: {dias:5.1f} dias  (n={n}){marca}")
    if divergiu:
        print(
            "[etl] AVISO: `ETA_BANDS` em src/features/green_logistics/"
            "delivery_options.py esta desatualizada. Atualize com os valores "
            "acima antes de citar prazos no TCC."
        )

    multi_demo = pick_demo_multi_seller(subset["offers"], subset["sellers"], centroids)
    if multi_demo:
        product_id, spread, origens = multi_demo
        locais = " | ".join(f"{cidade} ({prefixo})" for cidade, prefixo in origens)
        print(
            f"[etl] DEMO MULTI-VENDEDOR: product_id={product_id} "
            f"spread={spread:.0f} km entre {locais}"
        )
    else:
        print("[etl] aviso: nenhum produto multi-vendedor com centroide nesta amostra")

    engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
