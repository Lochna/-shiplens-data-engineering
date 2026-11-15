"""Read-only Snowflake execution for Ask ShipLens."""

from pathlib import Path

import snowflake.connector
import yaml

from conversational_bi.query_engine import QUERIES


def get_connection_config():
    """Use Streamlit Cloud secrets, falling back to local dbt credentials."""
    try:
        import streamlit as st

        settings = st.secrets["snowflake"]
    except (ImportError, FileNotFoundError, KeyError):
        settings = None

    if settings is not None:
        from cryptography.hazmat.primitives import serialization

        key = serialization.load_pem_private_key(
            settings["private_key"].encode("utf-8"),
            password=None,
        )
        private_key_der = key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        return {
            "account": settings["account"],
            "user": settings["user"],
            "private_key": private_key_der,
            "role": "DBT_ROLE",
            "warehouse": "SHIPLENS_WH",
            "database": "SHIPLENS_DB",
            "schema": "DBT_DEV",
        }

    profile_path = Path.home() / ".dbt" / "profiles.yml"
    profiles = yaml.safe_load(profile_path.read_text())
    profile = profiles["shiplens_dbt"]
    config = profile["outputs"][profile.get("target", "dev")]

    return {
        "account": config["account"],
        "user": config["user"],
        "private_key_file": config["private_key_path"],
        "role": config["role"],
        "warehouse": config["warehouse"],
        "database": config["database"],
        "schema": config["schema"],
    }


def run_query(query_key: str):
    """Execute only an approved analytics query."""
    if query_key not in QUERIES:
        raise ValueError("Unsupported query key")

    config = get_connection_config()

    with snowflake.connector.connect(
        **config,
        session_parameters={
            "QUERY_TAG": "SHIPLENS_CONVERSATIONAL_BI",
            "STATEMENT_TIMEOUT_IN_SECONDS": 30,
        },
        client_session_keep_alive=False,
        enable_server_session_keep_alive_auto_detection=False,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(QUERIES[query_key])
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
