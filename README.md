

\# ShipLens — Data Engineering Pipeline



An end-to-end shipment delivery analytics project.



\## Tech Stack

\- Fivetran — Data ingestion from Google Sheets

\- Snowflake — Cloud data warehouse

\- dbt — Data transformation and quality testing

\- Apache Airflow — Pipeline orchestration

\- Conversational BI — Natural language analytics



\## Pipeline Architecture



Google Sheets → Fivetran → Snowflake → dbt → Conversational BI



Apache Airflow orchestrates ingestion and transformation.



\## dbt Models



\### Staging

\- stg\_shipments

\- stg\_tracking\_events

\- stg\_carriers



\### Analytics

\- fct\_deliveries

\- carrier\_performance



\## Data Quality

14 dbt tests covering uniqueness, null values, and relationships.



\## Repository Structure



\- dbt/ — dbt transformation models

\- airflow/ — Airflow orchestration code



\## Status

\- Fivetran ingestion: Complete

\- Snowflake warehouse: Complete

\- dbt transformations: Complete

\- dbt quality tests: Passed

\- Airflow integration: In progress



