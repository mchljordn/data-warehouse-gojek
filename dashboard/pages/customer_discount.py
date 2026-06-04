"""
Customer & Discount Analytics page.
Displays demographic breakdowns, discount efficiency models, and localized cancellation rates.
"""
import streamlit as st
import pandas as pd
from dashboard.utils.db import run_query
from database.olap_queries import (
    q_customer_age_gender_analysis,
    q_discount_effectiveness,
    q_discount_by_age_group,
    q_cancellation_by_service,
    q_cancellation_by_region,
)
from dashboard.components.charts import (
    bar_grouped, bar_stacked,
    bar_horizontal, waterfall_discount,
)
from dashboard.components.kpi_cards import section_header, insight_box


def render(filters: dict):
    # Fetch data based on dynamic sidebar filters
    df_customer  = run_query(q_customer_age_gender_analysis(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_discount  = run_query(q_discount_effectiveness(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_disc_age  = run_query(q_discount_by_age_group(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_cancel    = run_query(q_cancellation_by_service(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_cancel_r  = run_query(q_cancellation_by_region(
        limit=250, years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))

    # Exclude ROLLUP total rows to ensure clean province-level visualization
    df_cancel_leaf = df_cancel_r[
        ~df_cancel_r["province"].str.contains("All Provinces|total|ALL", case=False, na=True)
    ].head(15).sort_values("cancellation_rate_pct", ascending=False)

    if df_discount.empty or df_cancel.empty:
        st.warning("No data found matching the selected Global Filters combination. Please adjust your sidebar settings.")
        return

    # Customer Demographics
    section_header("Customer Demographics Analysis")
    
    # Exclude CUBE sub-total rows for graphing purposes
    df_leaf = df_customer[
        (~df_customer["age_group"].str.contains("All|total", case=False, na=True)) &
        (~df_customer["gender"].str.contains("All|total", case=False, na=True))
    ].copy()

    col1, col2 = st.columns(2)
    with col1:
        fig = bar_grouped(
            df_leaf, x="age_group", y="total_revenue",
            color="gender", title="Revenue Breakdown by Age Group & Gender",
        )
        st.plotly_chart(fig, width="stretch", theme=None)

    with col2:
        fig = bar_grouped(
            df_leaf, x="age_group", y="total_orders",
            color="gender", title="Order Volume by Age Group & Gender",
        )
        st.plotly_chart(fig, width="stretch", theme=None)

    with st.expander("View Multi-dimensional Demographics Table", expanded=False):
        st.markdown(df_customer.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

    # Discount Effectiveness
    section_header("Discount Effectiveness Analytics")
    col1, col2 = st.columns(2)

    with col1:
        fig = bar_grouped(
            df_discount, x="service_name", y="completion_rate_pct",
            color="discount_tier",
            title="Order Completion Rate (%) by Discount Tier & Service",
        )
        fig.update_layout(yaxis=dict(range=[0, 105]))
        st.plotly_chart(fig, width="stretch", theme=None)

    with col2:
        fig = waterfall_discount(
            df_discount.groupby("service_name", as_index=False).agg(
                total_revenue=("total_revenue", "sum"),
                total_discount_given=("total_discount_given", "sum"),
            )
        )
        st.plotly_chart(fig, width="stretch", theme=None)

    # Discount Burn by Age Group
    section_header("Discount Cost Distribution by Age Group")
    fig = bar_stacked(
        df_disc_age[~df_disc_age["age_group"].str.contains("All|total", case=False, na=True)], 
        x="age_group", y="total_discount",
        color="discount_tier",
        title="Total Discount Burned by Age Group & Tier",
    )
    st.plotly_chart(fig, width="stretch", theme=None)

    # Cancellation Analysis
    section_header("Cancellation Analysis")
    col1, col2 = st.columns(2)

    with col1:
        fig = bar_horizontal(
            df_cancel.sort_values("cancellation_rate_pct", ascending=False),
            x="cancellation_rate_pct", y="service_name",
            title="Cancellation Rate (%) by Service Type",
            color="#E82C2C",
        )
        st.plotly_chart(fig, width="stretch", theme=None)

    with col2:
        fig = bar_horizontal(
            df_cancel_leaf, x="cancellation_rate_pct", y="province",
            title="Top 15 Provinces with Highest Cancellation Rate",
            color="#E82C2C",
        )
        st.plotly_chart(fig, width="stretch", theme=None)

    # Automated Insights Generation
    best_age  = df_leaf.groupby("age_group")["total_revenue"].sum().idxmax()
    best_disc = df_discount.loc[df_discount["completion_rate_pct"].idxmax()]
    worst_svc = df_cancel.iloc[0]

    insight_box("Customer & Discount Insights", [
        f"The customer segment in the <b>{best_age}</b> age cohort generated the highest cumulative revenue, "
        f"marking them as the key target demographic for marketing campaigns.",
        f"Applying a <b>'{best_disc['discount_tier']}'</b> discount tier to the <b>{best_disc['service_name']}</b> service "
        f"successfully drove the highest completion rate at <b>{best_disc['completion_rate_pct']}%</b>.",
        f"The <b>{worst_svc['service_name'].title()}</b> service recorded the highest cancellation rate at "
        f"<b>{worst_svc['cancellation_rate_pct']}%</b>. Fleet managers should investigate driver supply constraints in active areas.",
        f"Subsidy distribution displays diminishing returns when discounts exceed Rp 5.000,00 across sectors. "
        f"Concentrating high-value promotions on the productive 26-35 age group will optimize marketing ROI.",
    ])
