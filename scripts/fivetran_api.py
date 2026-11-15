
# ShipLens - Fivetran API Integration
# Safe connector allowlist and sync monitoring

import os
import time
import requests
from datetime import datetime, timezone

BASE_URL = "https://api.fivetran.com/v1"

CONNECTORS = {
    "shipments": "FIVETRAN_SHIPMENTS_CONNECTION_ID",
    "tracking_events": "FIVETRAN_TRACKING_EVENTS_CONNECTION_ID",
    "carriers": "FIVETRAN_CARRIERS_CONNECTION_ID",
}

# Only these two connectors may be triggered.
# Carriers is intentionally excluded.
ALLOWED_SYNC_CONNECTORS = {
    "runner_calendar",
    "pictorial_protoplasm",
}


def get_credentials():
    key = os.getenv("FIVETRAN_API_KEY")
    secret = os.getenv("FIVETRAN_API_SECRET")

    if not key or not secret:
        raise RuntimeError("Fivetran credentials missing.")

    return key, secret


def get_connector_ids():
    ids = {}

    for name, env_var in CONNECTORS.items():
        value = os.getenv(env_var)

        if not value:
            raise RuntimeError(
                f"Missing configuration: {env_var}"
            )

        ids[name] = value

    return ids


def get_sync_status(connector_id):
    response = requests.get(
        f"{BASE_URL}/connections/{connector_id}",
        auth=get_credentials(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def parse_fivetran_time(value):
    if not value:
        return None

    parsed = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if parsed.tzinfo is None:
        raise ValueError(
            "Fivetran timestamp lacks timezone."
        )

    return parsed.astimezone(timezone.utc)


def get_sync_baseline(connector_id):
    result = get_sync_status(connector_id)
    data = result.get("data", {})

    if not isinstance(data, dict):
        raise RuntimeError("Invalid Fivetran response.")

    return {
        "succeeded_at": parse_fivetran_time(
            data.get("succeeded_at")
        ),
        "failed_at": parse_fivetran_time(
            data.get("failed_at")
        ),
        "paused": data.get("paused"),
    }


def trigger_sync(connector_id):
    # Block carriers and all unknown connectors
    # BEFORE making any API request.
    if connector_id not in ALLOWED_SYNC_CONNECTORS:
        raise PermissionError(
            "Sync blocked: connector not in allowlist."
        )

    baseline = get_sync_baseline(connector_id)

    if baseline["paused"] is not False:
        raise RuntimeError(
            "Connector is paused or status is unknown."
        )

    response = requests.post(
        f"{BASE_URL}/connections/{connector_id}/force",
        auth=get_credentials(),
        timeout=30,
    )
    response.raise_for_status()

    return baseline


def wait_for_sync(
    connector_id,
    baseline,
    timeout_seconds=1800,
    interval=30,
):
    if not isinstance(baseline, dict):
        raise ValueError(
            "Valid sync baseline is required."
        )

    previous_success = baseline["succeeded_at"]
    previous_failure = baseline["failed_at"]

    started = time.monotonic()

    while time.monotonic() - started < timeout_seconds:
        data = get_sync_status(connector_id).get("data", {})

        if not isinstance(data, dict):
            raise RuntimeError(
                "Invalid Fivetran response."
            )

        succeeded = parse_fivetran_time(
            data.get("succeeded_at")
        )
        failed = parse_fivetran_time(
            data.get("failed_at")
        )

        new_success = (
            succeeded is not None
            and (
                previous_success is None
                or succeeded > previous_success
            )
        )

        new_failure = (
            failed is not None
            and (
                previous_failure is None
                or failed > previous_failure
            )
        )

        if new_failure and (
            not new_success or failed >= succeeded
        ):
            raise RuntimeError(
                "Fivetran connector sync failed."
            )

        if new_success and (
            not new_failure or succeeded > failed
        ):
            return True

        time.sleep(interval)

    raise TimeoutError(
        "Fivetran sync did not finish within timeout."
    )


if __name__ == "__main__":
    print("ShipLens Fivetran API helper loaded.")
    print("No live sync triggered.")
