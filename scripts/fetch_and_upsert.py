import os
import sys
import logging
from datetime import datetime
from typing import Dict, List

import requests
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

API_URL = "https://finnhub.io/api/v1/quote"
API_KEY = os.getenv("FINNHUB_API_KEY")
TICKERS = [t.strip().upper() for t in os.getenv("TARGET_STOCKS", "AAPL").split(",") if t.strip()]

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "airflow")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASSWORD = os.getenv("DB_PASSWORD", "airflow")

TARGET_TABLE = os.getenv("TARGET_TABLE", "stock_quotes")

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TARGET_TABLE} (
    symbol TEXT NOT NULL,
    trading_day DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    prev_close NUMERIC,
    fetched_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (symbol, trading_day)
);
"""

UPSERT_SQL = f"""
INSERT INTO {TARGET_TABLE} (
    symbol, trading_day, open, high, low, close, prev_close, fetched_at
) VALUES %s
ON CONFLICT (symbol, trading_day) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    prev_close = EXCLUDED.prev_close,
    fetched_at = NOW();
"""

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

def create_table():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    logging.info("Table ready.")

def fetch_symbol(symbol: str) -> Dict:
    params = {"symbol": symbol, "token": API_KEY}
    r = requests.get(API_URL, params=params, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text}")
    return r.json()

def parse_and_format(symbol: str, data: Dict) -> tuple:
    trading_day = datetime.utcnow().date()
    return (
        symbol,
        trading_day,
        data.get("o"),
        data.get("h"),
        data.get("l"),
        data.get("c"),
        data.get("pc"),
        datetime.utcnow(),
    )

def upsert_rows(rows: List[tuple]):
    if not rows: return
    with get_conn() as conn, conn.cursor() as cur:
        execute_values(cur, UPSERT_SQL, rows, page_size=100)
        conn.commit()
    logging.info("Upserted %d rows.", len(rows))

def main():
    if not API_KEY:
        logging.error("FINNHUB_API_KEY not set")
        sys.exit(1)

    create_table()
    rows = []
    for ticker in TICKERS:
        try:
            data = fetch_symbol(ticker)
            rows.append(parse_and_format(ticker, data))
        except Exception as e:
            logging.error("Failed for %s: %s", ticker, e)
    upsert_rows(rows)

if __name__ == "__main__":
    main()
