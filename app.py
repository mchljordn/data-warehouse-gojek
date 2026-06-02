"""
Gojek DWH Analytics Dashboard - Main Entry Point.
Run command: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Gojek Data Warehouse Analytics",
    page_icon="🛵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Imports
from dashboard.utils.db import run_query, test_connection
from database.olap_queries import (
    q_kpi_summary, q_filter_years,
    q_filter_regions, q_filter_services,
    q_revenue_monthly_trend,
    q_revenue_by_service,
    q_top_cities_revenue
)
from dashboard.components.kpi_cards import inject_styles, kpi_grid, section_header
import dashboard.pages.revenue           as pg_revenue
import dashboard.pages.driver_performance as pg_driver
import dashboard.pages.demand_time        as pg_demand
import dashboard.pages.customer_discount  as pg_customer

# Sidebar Navigation, Theme Selector, and Filters
with st.sidebar:
    st.html("""
    <div style="padding:16px 0 24px; text-align:center; font-family: sans-serif;">
        <div style="font-size:32px; margin-bottom:4px;">🛵</div>
        <div style="font-size:17px; font-weight:700; color: var(--text-primary); letter-spacing:-0.01em;">
            Gojek Data Warehouse
        </div>
        <div style="font-size:11px; color: var(--text-muted); text-transform:uppercase; letter-spacing:0.08em;">
            Analytics Dashboard
        </div>
    </div>
    """)

    st.markdown("---")

    # Silent database connection check (stops rendering and shows error only on failure)
    if not test_connection():
        st.error("🔴 Connection Failed - Check secrets.toml")
        st.stop()

    # Theme state initialization
    if "theme_selector" not in st.session_state:
        st.session_state.theme_selector = "Dark Mode"
    theme = st.session_state.theme_selector

    # Sidebar Header & Theme Toggle Column Layout
    col_title, col_theme = st.columns([8, 1.5])
    with col_title:
        st.markdown("**🔍 Global Filters**")
    with col_theme:
        icon = "☀️" if theme == "Dark Mode" else "🌙"
        if st.button(icon, key="theme_toggle_btn", help="Toggle Light/Dark Theme"):
            st.session_state.theme_selector = "Light Mode" if theme == "Dark Mode" else "Dark Mode"
            st.rerun()

    # Year filter loading
    try:
        years_df  = run_query(q_filter_years())
        all_years = sorted(years_df["year"].tolist())
    except Exception:
        all_years = [2023, 2024]

    selected_years = st.multiselect(
        "Year", options=all_years, default=all_years, key="year_filter"
    )

    # Region filter loading
    try:
        regions_df  = run_query(q_filter_regions())
        all_regions = regions_df["region"].tolist()
    except Exception:
        all_regions = []

    selected_regions = st.multiselect(
        "Region", options=all_regions, default=[], key="region_filter",
        placeholder="All regions",
    )

    # Service filter loading
    try:
        svc_df   = run_query(q_filter_services())
        all_svcs = svc_df["service_name"].tolist()
    except Exception:
        all_svcs = []

    selected_services = st.multiselect(
        "Service", options=all_svcs, default=[], key="svc_filter",
        placeholder="All services",
    )

    st.markdown("---")
    st.caption("Universitas Padjadjaran · Gojek Data Warehouse · 2026")

# Global styles injection based on theme selector
inject_styles(theme)

# Filters compilation
filters = {
    "years":    selected_years,
    "regions":  selected_regions,
    "services": selected_services,
}

# Page header
st.markdown("""
<div style="padding:24px 0 8px;">
    <h1 style="font-size:28px; font-weight:800; color: var(--text-primary); margin:0; letter-spacing:-0.02em;">
        Gojek Service Analytics Dashboard
    </h1>
    <p style="color: var(--text-muted); font-size:13px; margin:6px 0 0;">
        Data Warehouse · Star Schema · OLAP Analytics · 100K Orders · 2023–2024
    </p>
</div>
""", unsafe_allow_html=True)

# Reactive global KPI cards
try:
    kpi = run_query(q_kpi_summary(
        years=filters.get("years"),
        regions=filters.get("regions"),
        services=filters.get("services")
    )).iloc[0]

    total_revenue = float(kpi['total_revenue'])
    total_orders = int(kpi['total_orders'])
    avg_order_value = float(kpi['avg_order_value'])
    total_discount = float(kpi['total_discount'])
    cancellation_rate = float(kpi['cancellation_rate_pct'])
    unique_customers = int(kpi['unique_customers'])
    active_drivers = int(kpi['active_drivers'])
    avg_distance      = float(kpi['avg_distance_km'])
    
    kpi_grid([
        {
            "icon": "💰",
            "label": "Total Revenue",
            "value": f"Rp {total_revenue:,.0f}",
            "sub": f"{total_orders:,} total orders",
            "accent": "var(--green)",
        },
        {
            "icon": "📦",
            "label": "Average Order Value (AOV)",
            "value": f"Rp {avg_order_value:,.0f}",
            "sub": f"Avg distance: {avg_distance:.1f} km",
            "accent": "var(--cyan)",
        },
        {
            "icon": "🎟️",
            "label": "Total Discount",
            "value": f"Rp {total_discount:,.0f}",
            "sub": "Discount across active segments",
            "accent": "var(--orange)",
        },
        {
            "icon": "❌",
            "label": "Cancellation Rate",
            "value": f"{cancellation_rate:.2f}%",
            "sub": "Target: < 15.00%",
            "accent": "var(--red)" if cancellation_rate > 15 else "var(--green)",
            "delta": f"+{cancellation_rate:.2f}%" if cancellation_rate > 15 else f"{cancellation_rate:.2f}%",
        },
        {
            "icon": "👥",
            "label": "Unique Customers",
            "value": f"{unique_customers:,}",
            "sub": "Distinct active users",
            "accent": "var(--purple)",
        },
        {
            "icon": "🛵",
            "label": "Active Drivers",
            "value": f"{active_drivers:,}",
            "sub": "Fitted partner fleet",
            "accent": "var(--yellow)",
        },
    ])
except Exception as e:
    st.warning(f"Could not load reactive KPI summary: {e}")

st.markdown("---")

# Main Navigation Tabs
tab_rev, tab_driver, tab_demand, tab_customer = st.tabs([
    "💰   Revenue & Service",
    "🛵   Driver Performance",
    "⏱️   Demand & Time",
    "👥   Customer & Discount",
])

with tab_rev:
    try:
        pg_revenue.render(filters)
    except Exception as e:
        st.error(f"Revenue page error: {e}")

with tab_driver:
    try:
        pg_driver.render(filters)
    except Exception as e:
        st.error(f"Driver page error: {e}")

with tab_demand:
    try:
        pg_demand.render(filters)
    except Exception as e:
        st.error(f"Demand page error: {e}")

with tab_customer:
    try:
        pg_customer.render(filters)
    except Exception as e:
        st.error(f"Customer page error: {e}")
