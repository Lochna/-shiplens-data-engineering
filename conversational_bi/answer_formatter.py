"""Convert Ask ShipLens query results into readable answers."""


def format_answer(query_key: str, rows: list[dict]) -> str:
    """Format results from approved ShipLens analytics queries."""
    if not rows:
        return "No matching data was found."

    row = rows[0]

    if query_key == "total_shipments":
        return f"ShipLens has {row['TOTAL_SHIPMENTS']:,} total shipments."

    if query_key == "delivered_shipments":
        return f"{row['DELIVERED_SHIPMENTS']:,} shipments have been delivered."

    if query_key == "best_carrier":
        return (
            f"{row['CARRIER_NAME']} has the highest on-time delivery rate "
            f"at {row['ON_TIME_PERCENT']}%."
        )

    if query_key == "most_delays":
        return (
            f"{row['CARRIER_NAME']} has the most late deliveries "
            f"({row['LATE_DELIVERIES']:,} shipments)."
        )

    if query_key == "average_delivery":
        days = row["AVG_DELIVERY_DAYS"]
        if days is None:
            return "Average delivery time is not available."
        return f"The average delivery time is {days} days."

    raise ValueError("Unsupported query key")
