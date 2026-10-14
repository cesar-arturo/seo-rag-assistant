"""Crawl Google Search Central documentation into the docs_bronze Delta table."""

import argparse
import hashlib

from pyspark.sql import types as T

from seo_rag.ingestion.crawler import crawl
from seo_rag.spark import get_spark

SOURCE = "google_search_central"
START_URL = "https://developers.google.com/search/docs"

SCHEMA = T.StructType(
    [
        T.StructField("url", T.StringType(), False),
        T.StructField("source", T.StringType(), False),
        T.StructField("http_status", T.IntegerType(), False),
        T.StructField("content_hash", T.StringType(), False),
        T.StructField("html", T.StringType(), False),
        T.StructField("fetched_at", T.TimestampType(), False),
    ]
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="seo_rag")
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    table = f"{args.catalog}.{args.schema}.docs_bronze"

    rows, failures = [], []
    for page in crawl(START_URL, START_URL, max_pages=args.max_pages, delay_seconds=args.delay):
        if page.html is None:
            failures.append((page.url, page.status))
            continue
        content_hash = hashlib.sha256(page.html.encode()).hexdigest()
        rows.append((page.url, SOURCE, page.status, content_hash, page.html, page.fetched_at))
        if len(rows) % 25 == 0:
            print(f"fetched {len(rows)} pages")

    print(f"fetched {len(rows)} pages, {len(failures)} failed")
    for url, status in failures:
        print(f"  failed ({status}): {url}")
    if not rows:
        raise RuntimeError("crawl returned no pages")

    spark = get_spark()
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            url STRING NOT NULL,
            source STRING NOT NULL,
            http_status INT NOT NULL,
            content_hash STRING NOT NULL,
            html STRING NOT NULL,
            fetched_at TIMESTAMP NOT NULL
        )
        COMMENT 'Raw HTML of crawled SEO documentation pages, one row per URL'
        TBLPROPERTIES (delta.enableChangeDataFeed = true)
        """
    )
    spark.createDataFrame(rows, SCHEMA).createOrReplaceTempView("docs_bronze_updates")
    spark.sql(
        f"""
        MERGE INTO {table} t
        USING docs_bronze_updates s
        ON t.url = s.url
        WHEN MATCHED AND t.content_hash <> s.content_hash THEN UPDATE SET *
        WHEN MATCHED THEN UPDATE SET t.http_status = s.http_status, t.fetched_at = s.fetched_at
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    print(f"merged into {table}")


if __name__ == "__main__":
    main()
