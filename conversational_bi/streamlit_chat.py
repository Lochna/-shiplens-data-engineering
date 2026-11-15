"""Reusable Streamlit chat interface for Ask ShipLens."""

import streamlit as st

from conversational_bi.query_engine import get_query, QUERIES
from conversational_bi.snowflake_client import run_query
from conversational_bi.answer_formatter import format_answer


SUGGESTED_QUESTIONS = [
    "How many total shipments are there?",
    "How many shipments were delivered?",
    "Which carrier has the best on-time delivery rate?",
    "Which carrier has the most late deliveries?",
    "What is the average delivery time?",
]


def render_ask_shiplens():
    """Render the Ask ShipLens Q&A interface."""
    st.subheader("💬 Ask ShipLens")
    st.caption("Ask questions about shipment and carrier performance.")

    with st.expander("Example questions"):
        for question in SUGGESTED_QUESTIONS:
            st.write("•", question)

    if "shiplens_chat_history" not in st.session_state:
        st.session_state.shiplens_chat_history = []

    for message in st.session_state.shiplens_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input("Ask about your shipments...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        sql = get_query(question)

        if sql is None:
            answer = (
                "I can answer the five example questions shown above. "
                "Please try one of those."
            )
        else:
            query_key = next(
                key for key, value in QUERIES.items()
                if value == sql
            )

            try:
                with st.spinner("Checking Snowflake analytics..."):
                    rows = run_query(query_key)
                answer = format_answer(query_key, rows)
            except Exception:
                answer = (
                    "Sorry, I couldn't retrieve the analytics data. "
                    "Please try again later."
                )

        with st.chat_message("assistant"):
            st.write(answer)

        st.session_state.shiplens_chat_history.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ])


if __name__ == "__main__":
    st.set_page_config(page_title="Ask ShipLens", page_icon="📦")
    render_ask_shiplens()
