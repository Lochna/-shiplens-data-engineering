import logging
import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector
from cryptography.hazmat.primitives import serialization

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conversational_bi.streamlit_chat import render_ask_shiplens

st.set_page_config(
    page_title="ShipLens | Shipment Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background-color: #F5F7FB;
        color: #14213D;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #14213D !important;
    }
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #E3E8F0;
        border-radius: 14px;
        padding: 18px;
    }
    div.stButton > button {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def connect_snowflake():
    settings = st.secrets["snowflake"]

    key = serialization.load_pem_private_key(
        settings["private_key"].encode("utf-8"),
        password=None,
    )

    private_key_der = key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(
        account=settings["account"],
        user=settings["user"],
        private_key=private_key_der,
        warehouse="SHIPLENS_WH",
        database="SHIPLENS_DB",
        schema="DBT_DEV",
        role="DBT_ROLE",
        client_session_keep_alive=False,
    )


@st.cache_data(ttl=300)
def fetch_data(query):
    conn = connect_snowflake()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [column[0].lower() for column in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)
    finally:
        cursor.close()


st.sidebar.title("📦 ShipLens")
st.sidebar.caption("Shipment Intelligence Platform")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Carrier Analytics", "Shipment Explorer", "Ask ShipLens AI"],
)

st.sidebar.divider()
st.sidebar.caption("Data Source: Snowflake")
st.sidebar.caption("Transformation: dbt")
st.sidebar.caption("Orchestration: Apache Airflow")

st.title("ShipLens")
st.caption("Shipment Delivery Intelligence & Performance Analytics")

try:
    deliveries = fetch_data("""
        SELECT
            SHIPMENT_ID,
            CARRIER_ID,
            CARRIER_NAME,
            ORIGIN_CITY,
            DESTINATION_CITY,
            ORDER_DATETIME,
            PROMISED_DELIVERY_DATE,
            CURRENT_STATUS,
            DELIVERED_AT,
            DELIVERY_DAYS,
            IS_LATE
        FROM SHIPLENS_DB.DBT_DEV.FCT_DELIVERIES
    """)

    carriers = fetch_data("""
        SELECT
            CARRIER_ID,
            CARRIER_NAME,
            TOTAL_SHIPMENTS,
            DELIVERED_SHIPMENTS,
            UNDELIVERED_SHIPMENTS,
            AVG_DELIVERY_DAYS,
            LATE_DELIVERIES,
            ON_TIME_DELIVERIES,
            ON_TIME_PERCENTAGE
        FROM SHIPLENS_DB.DBT_DEV.CARRIER_PERFORMANCE
    """)

except Exception:
    logging.exception("ShipLens Snowflake connection failed")
    st.error(
        "Unable to connect to Snowflake. "
        "Please check the dashboard's Snowflake credentials and permissions."
    )
    st.stop()

if deliveries.empty:
    st.warning("No shipment records found in Snowflake.")
    st.stop()

carrier_names = sorted(
    deliveries["carrier_name"].dropna().unique().tolist()
)

selected_carriers = st.sidebar.multiselect(
    "Filter by carrier",
    carrier_names,
    default=carrier_names,
)

filtered = deliveries[
    deliveries["carrier_name"].isin(selected_carriers)
].copy()

if filtered.empty:
    st.info("No shipments match the selected filters.")
    st.stop()

delivered = filtered[filtered["delivered_at"].notna()]
late = delivered[delivered["is_late"] == True]
on_time = delivered[delivered["is_late"] == False]

total_shipments = len(filtered)
delivered_count = len(delivered)
on_time_rate = (
    len(on_time) / delivered_count * 100
    if delivered_count else 0
)

average_days = (
    pd.to_numeric(
        delivered["delivery_days"], errors="coerce"
    ).mean()
    if delivered_count else 0
)

average_days = 0 if pd.isna(average_days) else average_days

if page == "Overview":
    st.subheader("Delivery Performance Overview")

    a, b, c, d = st.columns(4)

    a.metric("Total Shipments", f"{total_shipments:,}")
    b.metric("Delivered", f"{delivered_count:,}")
    c.metric("On-Time Rate", f"{on_time_rate:.1f}%")
    d.metric("Avg Delivery Time", f"{average_days:.1f} days")

    st.markdown("")

    left, right = st.columns(2)

    with left:
        st.subheader("Shipments by Carrier")

        counts = (
            filtered.groupby("carrier_name")
            .size()
            .reset_index(name="shipments")
        )

        fig = px.bar(
            counts,
            x="carrier_name",
            y="shipments",
            color="carrier_name",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={
                "carrier_name": "Carrier",
                "shipments": "Shipments",
            },
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Delivery Status")

        status_counts = (
            filtered.groupby("current_status")
            .size()
            .reset_index(name="count")
        )

        fig = px.pie(
            status_counts,
            names="current_status",
            values="count",
            hole=0.58,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_layout(paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Delivery Outcomes")

    x, y, z = st.columns(3)
    x.metric("On-Time Deliveries", len(on_time))
    y.metric("Late Deliveries", len(late))
    z.metric("Not Yet Delivered", total_shipments - delivered_count)

elif page == "Carrier Analytics":
    st.subheader("Carrier Performance Comparison")

    selected = carriers[
        carriers["carrier_name"].isin(selected_carriers)
    ].copy()

    st.dataframe(
        selected,
        use_container_width=True,
        hide_index=True,
    )

    left, right = st.columns(2)

    with left:
        st.subheader("On-Time Delivery Rate")

        fig = px.bar(
            selected,
            x="carrier_name",
            y="on_time_percentage",
            color="carrier_name",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={
                "carrier_name": "Carrier",
                "on_time_percentage": "On-Time Rate (%)",
            },
        )
        fig.update_yaxes(range=[0, 100])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Average Delivery Time")

        fig = px.bar(
            selected,
            x="carrier_name",
            y="avg_delivery_days",
            color="carrier_name",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={
                "carrier_name": "Carrier",
                "avg_delivery_days": "Average Days",
            },
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

elif page == "Shipment Explorer":
    st.subheader("Shipment Explorer")

    search = st.text_input(
        "Search Shipment ID",
        placeholder="Enter shipment ID...",
    )

    result = filtered.copy()

    if search:
        result = result[
            result["shipment_id"]
            .astype(str)
            .str.contains(search, case=False, regex=False, na=False)
        ]

    st.caption(f"{len(result):,} shipments found")

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download CSV",
        result.to_csv(index=False).encode("utf-8"),
        "shiplens_shipments.csv",
        "text/csv",
    )



elif page == "Ask ShipLens AI":
    st.subheader("Ask ShipLens AI")
    st.caption("Conversational Business Intelligence powered by Snowflake")

    render_ask_shiplens()

st.divider()
st.caption(
    "ShipLens | Fivetran • Snowflake • dbt • Airflow • Streamlit"
)

