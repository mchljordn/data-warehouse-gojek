"""
Demand & Time Analytics page.
Displays hourly peaks, peak hour heatmap, quarterly aggregations, and regional demand volume.
"""
import streamlit as st
import pandas as pd
from dashboard.utils.db import run_query
from database.olap_queries import (
    q_peak_hour_heatmap, q_orders_by_hour,
    q_revenue_by_quarter, q_cancellation_by_hour,
    q_top_cities_revenue,
)
from dashboard.components.charts import (
    heatmap_dow_hour, line_trend, bar_horizontal, bar_grouped,
)
from dashboard.components.kpi_cards import section_header, insight_box


def render(filters: dict):
    # Fetch data based on dynamic sidebar filters
    df_heatmap   = run_query(q_peak_hour_heatmap(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_hourly    = run_query(q_orders_by_hour(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_quarterly = run_query(q_revenue_by_quarter(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_cancel_hr = run_query(q_cancellation_by_hour(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_cities    = run_query(q_top_cities_revenue(
        limit=20, years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))

    # Show warning if selected filters return empty data
    if df_cities.empty:
        st.warning("⚠️ No data found matching the selected Global Filters combination. Please adjust your sidebar settings.")
        return

    # Peak Trading Hours Heatmap
    section_header("Peak Trading Hours Heatmap")
    fig = heatmap_dow_hour(df_heatmap, title="Order Volume Density: Day vs Hour")
    st.plotly_chart(fig, width="stretch", theme=None)

    # Hourly distribution charts
    section_header("Hourly Order Volume, Revenue & Cancellation Trends")
    col1, col2, col3 = st.columns(3)

    with col1:
        fig = line_trend(
            df_hourly, x="hour", y="total_orders",
            title="Hourly Total Orders Volume",
        )
        st.plotly_chart(fig, width="stretch", theme=None)

    with col2:
        fig = line_trend(
            df_hourly, x="hour", y="total_revenue",
            title="Hourly Revenue Generation",
        )
        fig.update_traces(line=dict(color="var(--cyan)", width=2.5), fillcolor="rgba(0,212,255,0.08)")
        st.plotly_chart(fig, width="stretch", theme=None)

    with col3:
        fig = line_trend(
            df_cancel_hr, x="hour", y="cancellation_rate_pct",
            title="Hourly Cancellation Rate (%) Analysis",
        )
        fig.update_traces(line=dict(color="#E82C2C", width=2.5), fillcolor="rgba(232,44,44,0.08)")
        st.plotly_chart(fig, width="stretch", theme=None)

    # Quarterly aggregations
    section_header("Quarterly Revenue Performance Trends")
    
    # Exclude ROLLUP totals to keep quarterly bar chart clean
    df_q_chart = df_quarterly[
        (~df_quarterly["year"].astype(str).str.contains("All|total", case=False, na=True)) &
        (~df_quarterly["quarter"].astype(str).str.contains("All|total", case=False, na=True))
    ].copy()
    df_q_chart["period"] = df_q_chart["year"].astype(str) + " Q" + df_q_chart["quarter"].astype(str)

    fig = bar_grouped(
        df_q_chart, x="period", y="total_revenue",
        color="year", title="Quarterly Revenue Comparisons",
    )
    st.plotly_chart(fig, width="stretch", theme=None)

    with st.expander("📊 View Quarterly Revenue Data Sheet", expanded=False):
        st.markdown(df_quarterly.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

    # Regional demand volumes
    section_header("Regional Demand — Top Cities Share")
    fig = bar_horizontal(
        df_cities.sort_values("total_orders", ascending=False),
        x="total_orders", y="city",
        title="Top 20 Demand Cities by Order Volume",
    )
    st.plotly_chart(fig, width="stretch", theme=None)

    # Automated Insights Generation
    peak_hour     = df_hourly.loc[df_hourly["total_orders"].idxmax(), "hour"]
    peak_cancel   = df_cancel_hr.loc[df_cancel_hr["cancellation_rate_pct"].idxmax(), "hour"]
    peak_city     = df_cities.iloc[0]["city"]
    low_cancel_hr = df_cancel_hr.loc[df_cancel_hr["cancellation_rate_pct"].idxmin(), "hour"]

    insight_box("Demand & Time Insights", [
        f"The peak trading hour is identified at <b>{peak_hour:02d}:00 WIB</b>. "
        f"Implementing dynamic surge pricing and driver incentive schemes during this period is highly recommended.",
        f"The order cancellation rate spikes significantly at <b>{peak_cancel:02d}:00 WIB</b>, "
        f"indicating a supply-demand imbalance. Operational teams should prioritize active fleet allocation during these hours.",
        f"The safest operating hours with the lowest cancellation rate are observed at <b>{low_cancel_hr:02d}:00 WIB</b>.",
        f"The city of <b>{peak_city}</b> drives the highest national order volume. "
        f"Targeted driver recruitment or base placement in this area is recommended to maintain optimal SLA.",
        f"Quarterly trend analysis highlights seasonality effects. "
        f"Deploying creative marketing campaigns during low-demand quarters can stabilize annual performance.",
    ])
