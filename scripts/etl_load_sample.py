"""ETL Sprint 2: carrega amostra Olist (~1000 order_items, seed=42) no Postgres.

Fluxo:
1. Le CSVs em data/raw/.
2. Amostra 1000 linhas de olist_order_items_dataset.csv com seed=42.
3. Filtra rows com product_weight_g valido e CEPs presentes nos lookups.
4. Deriva subset de orders/customers/sellers/products e geolocation por prefixo.
5. Calcula centroides via mediana de lat/lng por prefixo.
6. Carrega tudo no Postgres (drop+create do schema, sem migrations nesta sprint).
7. Imprime um par (customer_prefix, seller_prefix) com distancia Haversine < 100 km
   para ser documentado como demo no README.

Execucao:
    python -m scripts.etl_load_sample [--data-dir data/raw] [--sample-size 1000] [--seed 42]

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

DEFAULT_SAMPLE_SIZE = 1000
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
    return items.sample(n=min(n, len(items)), random_state=seed).reset_index(drop=True)


def filter_valid(
    frames: dict[str, pd.DataFrame],
    items_sample: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Filtra subset coerente: produtos com peso valido, CEPs com geolocation."""

    products = frames["products"]
    products = products[products["product_weight_g"].notna() & (products["product_weight_g"] > 0)]

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
            ["product_id", "product_category_name", "product_weight_g"],
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
    items_sample = sample_order_items(frames["order_items"], n=args.sample_size, seed=args.seed)

    subset = filter_valid(frames, items_sample)
    print(
        "[etl] subset filtrado:",
        {k: len(v) for k, v in subset.items() if k != "geolocation"},
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

    engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
