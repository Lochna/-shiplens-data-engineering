"""Safe, rule-based question-to-SQL mapping for Ask ShipLens."""

QUERIES = {
    "total_shipments": """
        SELECT COUNT(*) AS TOTAL_SHIPMENTS
        FROM SHIPLENS_DB.DBT_DEV.FCT_DELIVERIES
    """,
    "delivered_shipments": """
        SELECT COUNT(*) AS DELIVERED_SHIPMENTS
        FROM SHIPLENS_DB.DBT_DEV.FCT_DELIVERIES
        WHERE DELIVERED_AT IS NOT NULL
    """,
    "best_carrier": """
        SELECT CARRIER_NAME, ON_TIME_PERCENTAGE AS ON_TIME_PERCENT
        FROM SHIPLENS_DB.DBT_DEV.CARRIER_PERFORMANCE
        WHERE DELIVERED_SHIPMENTS > 0
        ORDER BY ON_TIME_PERCENT DESC, CARRIER_NAME
        LIMIT 1
    """,
    "most_delays": """
        SELECT CARRIER_NAME, LATE_DELIVERIES
        FROM SHIPLENS_DB.DBT_DEV.CARRIER_PERFORMANCE
        ORDER BY LATE_DELIVERIES DESC, CARRIER_NAME
        LIMIT 1
    """,
    "average_delivery": """
        SELECT ROUND(AVG(DELIVERY_DAYS), 2) AS AVG_DELIVERY_DAYS
        FROM SHIPLENS_DB.DBT_DEV.FCT_DELIVERIES
        WHERE DELIVERED_AT IS NOT NULL
    """,
}


def get_query(question: str):
    """Return a predefined SQL query, or None for unsupported questions."""
    text = " ".join(question.lower().strip().split())

    if "carrier" in text and any(
        word in text for word in ("delay", "late", "most")
    ) and ("delay" in text or "late" in text):
        return QUERIES["most_delays"]

    if "carrier" in text and any(
        word in text for word in ("best", "top", "highest", "on-time")
    ):
        return QUERIES["best_carrier"]

    if "average" in text and "delivery" in text:
        return QUERIES["average_delivery"]

    if "delivered" in text and "shipment" in text:
        return QUERIES["delivered_shipments"]

    if "shipment" in text and any(
        word in text for word in ("total", "many", "count")
    ):
        return QUERIES["total_shipments"]

    return None
