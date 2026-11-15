# ShipLens - Airflow Orchestration DAG
# Fivetran sync and dbt execution are controlled by safety switches.

from datetime import datetime
import os
import subprocess
import sys

from airflow.sdk import DAG, task

sys.path.insert(0, os.environ.get("SHIPLENS_SCRIPTS_DIR", "/opt/shiplens/scripts"))

from load_config import load_fivetran_config
from fivetran_api import (
    get_connector_ids,
    get_sync_status,
    get_sync_baseline,
)

# Safety switches
ENABLE_LIVE_SYNC = False
ENABLE_DBT_EXECUTION = False

DBT_EXECUTABLE = os.environ.get("SHIPLENS_DBT_EXECUTABLE", "dbt")
DBT_PROJECT_DIR = os.environ.get("SHIPLENS_DBT_PROJECT_DIR", "/opt/shiplens/dbt")


with DAG(
    dag_id="shiplens_data_pipeline",
    start_date=datetime(2026, 11, 14),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["shiplens", "fivetran", "dbt", "dry-run"],
):

    @task
    def check_configuration():
        load_fivetran_config()
        ids = get_connector_ids()

        print("ShipLens configuration loaded.")
        print("Live sync enabled:", ENABLE_LIVE_SYNC)
        print("dbt execution enabled:", ENABLE_DBT_EXECUTION)
        print("Carriers excluded from orchestration.")

        return {
            "shipments": ids["shipments"],
            "tracking_events": ids["tracking_events"],
        }

    @task
    def check_connectors(ids):
        load_fivetran_config()

        for name, connector_id in ids.items():
            result = get_sync_status(connector_id)
            data = result.get("data", {})

            if not isinstance(data, dict):
                raise RuntimeError(
                    "Invalid Fivetran API response."
                )

            print(
                f"{name}: paused={data.get('paused')}"
            )

            if data.get("paused") is not False:
                raise RuntimeError(
                    f"{name} is paused or status unknown."
                )

        print("Both allowed connectors are ready.")
        return ids

    @task
    def prepare_sync(ids):
        load_fivetran_config()

        for name, connector_id in ids.items():
            baseline = get_sync_baseline(connector_id)

            print(
                f"{name}: baseline captured; "
                f"paused={baseline['paused']}"
            )

            if baseline["paused"] is not False:
                raise RuntimeError(
                    f"{name} is not ready."
                )

        return ids

    @task
    def simulate_sync(ids):
        if ENABLE_LIVE_SYNC:
            raise RuntimeError(
                "Live Fivetran sync is not implemented "
                "in this DAG."
            )

        for name in ids:
            print(
                f"DRY RUN: Would trigger and monitor "
                f"{name} sync."
            )

        print("No Fivetran sync was triggered.")

    @task
    def dbt_pending():
        if not ENABLE_DBT_EXECUTION:
            print("DRY RUN: dbt execution is disabled.")
            print("Would execute: dbt run, then dbt test.")
            return

        print("Starting dbt run...")

        subprocess.run(
            [DBT_EXECUTABLE, "run"],
            cwd=DBT_PROJECT_DIR,
            check=True,
        )

        print("Starting dbt test...")

        subprocess.run(
            [DBT_EXECUTABLE, "test"],
            cwd=DBT_PROJECT_DIR,
            check=True,
        )

        print("dbt run and dbt test completed successfully.")

    @task
    def pipeline_complete():
        print("ShipLens Airflow orchestration completed.")

    ids = check_configuration()
    checked = check_connectors(ids)
    prepared = prepare_sync(checked)
    simulated = simulate_sync(prepared)
    dbt_step = dbt_pending()
    finished = pipeline_complete()

    simulated >> dbt_step >> finished
