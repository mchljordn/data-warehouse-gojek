"""
Revenue & Service Analytics page.
Displays revenue breakdowns, monthly trends, top cities, and payment methods.
"""
import streamlit as st
import pandas as pd
from dashboard.utils.db import run_query, format_rupiah, format_number
from database.olap_queries import (
    q_revenue_by_service, q_revenue_monthly_trend,
    q_top_cities_revenue, q_payment_method_breakdown,
    q_revenue_by_region,
)
from dashboard.components.charts import (
    bar_horizontal, line_trend, donut,
)
from dashboard.components.kpi_cards import section_header, insight_box


def render(filters: dict):
    # Fetch data based on dynamic sidebar filters
    df_service  = run_query(q_revenue_by_service(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_trend    = run_query(q_revenue_monthly_trend(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_cities   = run_query(q_top_cities_revenue(
        limit=15, years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_payment  = run_query(q_payment_method_breakdown(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))
    df_region   = run_query(q_revenue_by_region(
        years=filters.get("years"), regions=filters.get("regions"), services=filters.get("services")
    ))

    # Show warning if selected filters return empty data
    if df_service.empty or df_cities.empty or df_region.empty:
        st.warning("No data found matching the selected Global Filters combination. Please adjust your sidebar settings.")
        return

    # Service Breakdown & Payment Methods
    section_header("Revenue Breakdown by Service & Payment Method")
    col1, col2 = st.columns([3, 2])

    with col1:
        fig = bar_horizontal(
            df_service.sort_values("total_revenue", ascending=False),
            x="total_revenue", y="service_name",
            title="Total Revenue by Service Type",
        )
        st.plotly_chart(fig, width="stretch", theme=None)

    with col2:
        fig = donut(df_payment, names="payment_method", values="total_revenue",
                    title="Revenue Proportion by Payment Method")
        st.plotly_chart(fig, width="stretch", theme=None)

    # Monthly Trends
    section_header("Monthly Revenue Trend")
    fig = line_trend(
        df_trend, x="period", y="revenue",
        secondary_y="mom_growth_pct",
        title="Monthly Revenue (IDR) & MoM Growth Rate (%)",
    )
    st.plotly_chart(fig, width="stretch", theme=None)

    # City Performance
    section_header("Top Cities by Revenue Performance")
    fig = bar_horizontal(
        df_cities.sort_values("total_revenue", ascending=False),
        x="total_revenue", y="city",
        title="Top 15 Performing Cities",
    )
    st.plotly_chart(fig, width="stretch", theme=None)

    # Regional Revenue Distribution
    section_header("Regional Revenue Distribution")
    with st.expander("View Regional Revenue Data Sheet", expanded=False):
        # Exclude national totals from detailed display
        display_df = df_region[df_region["region"] != 'ALL REGIONS'].copy()
        
        # Format total revenue as IDR currency
        display_df["total_revenue"] = display_df["total_revenue"].apply(
            format_rupiah
        )
        st.markdown(display_df.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

    # Detailed Service Sector Performance
    section_header("Detailed Service Sector Performance")
    col1, col2, col3 = st.columns(3)
    col1.metric("Highest Revenue Service",
                df_service.loc[df_service["total_revenue"].idxmax(), "service_name"],
                format_rupiah(df_service['total_revenue'].max()))
    col2.metric("Highest Average Order Value (AOV)",
                df_service.loc[df_service["avg_price"].idxmax(), "service_name"],
                format_rupiah(df_service['avg_price'].max()))
    col3.metric("Highest Order Volume",
                df_service.loc[df_service["total_orders"].idxmax(), "service_name"],
                format_number(df_service['total_orders'].max()))

    # Automated Insights Generation
    top_service = df_service.iloc[0]
    top_city    = df_cities.iloc[0]
    top_payment = df_payment.iloc[0]

    insight_box("Revenue & Performance Insights", [
        f"The <b>{top_service['service_name'].title()}</b> sector dominates the total revenue, contributing "
        f"<b>{format_rupiah(top_service['total_revenue'])}</b> ({top_service['revenue_share_pct']}% market share).",
        f"<b>{top_city['city']}</b> is the highest revenue-contributing city, generating <b>{format_rupiah(top_city['total_revenue'])}</b> "
        f"across {format_number(top_city['total_orders'])} total orders.",
        f"The <b>{top_payment['payment_method'].title()}</b> payment method is the primary customer preference, holding a "
        f"share of {top_payment['order_share_pct']}% of the total transaction volume.",
        f"The monthly trend shows fluctuating Month-over-Month (MoM) growth rates. "
        f"This historical trend can serve as a baseline for scheduling upcoming marketing campaigns.",
    ])
