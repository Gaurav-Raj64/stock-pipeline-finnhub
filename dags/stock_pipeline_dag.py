from __future__ import annotations
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

SCRIPT_PATH = "/opt/airflow/scripts/fetch_and_upsert.py"

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stock_pipeline_dag",
    description="Fetch stock data from Finnhub and upsert into Postgres",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    max_active_runs=1,
    tags=["stocks", "finnhub", "postgres"],
) as dag:

    def check_envs():
        required = ["FINNHUB_API_KEY", "TARGET_STOCKS", "TARGET_TABLE"]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {missing}")
        return True

    check_envs = PythonOperator(
        task_id="check_envs",
        python_callable=check_envs,
    )

    def fetch_and_upsert():
        import subprocess
        cmd = ["python", SCRIPT_PATH]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Fetch & upsert failed: {res.stderr}")
        print(res.stdout)

    run_etl = PythonOperator(
        task_id="fetch_and_upsert",
        python_callable=fetch_and_upsert,
    )

    check_envs >> run_etl
