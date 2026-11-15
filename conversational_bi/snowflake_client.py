"""Read-only Snowflake execution for Ask ShipLens."""

from pathlib import Path

import snowflake.connector
import yaml

from conversational_bi.query_engine import QUERIES


def run_query(query_key: str):
    """Execute only an approved analytics query."""
    if query_key not in QUERIES:
        raise ValueError("Unsupported query key")

    profile_path = Path.home() / ".dbt" / "profiles.yml"
    profiles = yaml.safe_load(profile_path.read_text())
    profile = profiles["shiplens_dbt"]
    config = profile["outputs"][profile.get("target", "dev")]

    with snowflake.connector.connect(
        account=config["account"],
        user=config["user"],
        private_key_file=config["private_key_path"],
        role=config["role"],
        warehouse=config["warehouse"],
        database=config["database"],
        schema=config["schema"],
        session_parameters={
            "QUERY_TAG": "SHIPLENS_CONVERSATIONAL_BI"
        },
        enable_server_session_keep_alive_auto_detection=False,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 30"
            )
            cursor.execute(QUERIES[query_key])
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
