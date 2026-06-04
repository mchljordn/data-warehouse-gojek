"""
Reusable Plotly chart components - themed dynamically to Light & Dark modes.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import streamlit as st

# Design Colors
GOGRAB_GREEN   = "#00AA5B"
GOGRAB_RED     = "#E82C2C"
ACCENT_CYAN   = "#00D4FF"
ACCENT_ORANGE = "#FF6B35"
ACCENT_PURPLE = "#A855F7"
ACCENT_YELLOW = "#FBBF24"

PALETTE = [GOGRAB_GREEN, ACCENT_CYAN, ACCENT_ORANGE, ACCENT_PURPLE, ACCENT_YELLOW, GOGRAB_RED]


def _get_theme_tokens():
    """Retrieve theme styling design tokens dynamically based on st.session_state selector."""
    theme = st.session_state.get("theme_selector", "Dark Mode")
    if theme == "Light Mode":
        return dict(
            text_color="#0F172A",
            text_dim="#334155",
            text_muted="#475569",
            grid_color="#E2E8F0",
            plot_bg="#F8FAFC",
            legend_bg="rgba(255, 255, 255, 0.8)",
            legend_border="rgba(0, 0, 0, 0.1)",
            donut_border="#FFFFFF"
        )
    else:
        return dict(
            text_color="#E2E8F0",
            text_dim="#94A3B8",
            text_muted="#64748B",
            grid_color="rgba(255,255,255,0.06)",
            plot_bg="rgba(15,20,30,0.6)",
            legend_bg="rgba(255,255,255,0.05)",
            legend_border="rgba(255,255,255,0.1)",
            donut_border="#0F141E"
        )


def _apply_base(fig: go.Figure, title: str = "") -> go.Figure:
    """Helper to apply basic layout parameters to charts."""
    tokens = _get_theme_tokens()
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=tokens["plot_bg"],
        font=dict(family="'DM Sans', sans-serif", color=tokens["text_color"], size=12),
        margin=dict(t=40),  # Let Plotly auto-calculate l, r, b based on labels
        legend=dict(
            bgcolor=tokens["legend_bg"],
            bordercolor=tokens["legend_border"],
            borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            gridcolor=tokens["grid_color"], 
            linecolor=tokens["grid_color"], 
            tickcolor=tokens["grid_color"],
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"]))
        ),
        yaxis=dict(
            gridcolor=tokens["grid_color"], 
            linecolor=tokens["grid_color"], 
            tickcolor=tokens["grid_color"],
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"]))
        ),
    )
    fig.update_layout(**layout, title=dict(text=title, font=dict(size=15, color=tokens["text_color"])))
    return fig


# --- Bar Charts ---

def bar_horizontal(df: pd.DataFrame, x: str, y: str, title: str = "",
                   color: str = GOGRAB_GREEN, text_col: str | None = None) -> go.Figure:
    """Render horizontal bar chart sorted descendingly."""
    fig = px.bar(df, x=x, y=y, orientation="h",
                 text=text_col or x,
                 color_discrete_sequence=[color])
    fig.update_traces(
        texttemplate="%{text:,.0f}", textposition="outside",
        marker_line_width=0, opacity=0.9,
    )
    
    tokens = _get_theme_tokens()
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=tokens["plot_bg"],
        font=dict(family="'DM Sans', sans-serif", color=tokens["text_color"], size=12),
        margin=dict(t=40),
        legend=dict(
            bgcolor=tokens["legend_bg"],
            bordercolor=tokens["legend_border"],
            borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            gridcolor=tokens["grid_color"], 
            linecolor=tokens["grid_color"], 
            tickcolor=tokens["grid_color"],
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"]))
        ),
        yaxis=dict(
            autorange="reversed", 
            gridcolor=tokens["grid_color"], 
            linecolor=tokens["grid_color"], 
            tickcolor=tokens["grid_color"],
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"]))
        )
    )
    
    fig.update_layout(**layout, title=dict(text=title, font=dict(size=15, color=tokens["text_color"])))
    return fig


def bar_grouped(df: pd.DataFrame, x: str, y: str, color: str,
                title: str = "") -> go.Figure:
    """Render grouped bar chart."""
    fig = px.bar(df, x=x, y=y, color=color,
                 barmode="group", color_discrete_sequence=PALETTE)
    fig.update_traces(marker_line_width=0, opacity=0.88)
    return _apply_base(fig, title)


def bar_stacked(df: pd.DataFrame, x: str, y: str, color: str,
                title: str = "") -> go.Figure:
    """Render stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color,
                 barmode="stack", color_discrete_sequence=PALETTE)
    fig.update_traces(marker_line_width=0)
    return _apply_base(fig, title)


# --- Line & Trend Charts ---

def line_trend(df: pd.DataFrame, x: str, y: str | list, title: str = "",
               secondary_y: str | None = None) -> go.Figure:
    """Render line trend chart, supporting optional secondary Y-axis."""
    if secondary_y:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=df[x], y=df[y], name=str(y).title(),
                       line=dict(color=GOGRAB_GREEN, width=2.5),
                       fill="tozeroy", fillcolor="rgba(0,170,91,0.08)"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=df[x], y=df[secondary_y], name=str(secondary_y).replace('_pct',' %').title(),
                       line=dict(color=ACCENT_CYAN, width=2, dash="dot")),
            secondary_y=True,
        )
        
        tokens = _get_theme_tokens()
        layout = dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=tokens["plot_bg"],
            font=dict(family="'DM Sans', sans-serif", color=tokens["text_color"], size=12),
            margin=dict(t=40),
            legend=dict(
                bgcolor=tokens["legend_bg"],
                bordercolor=tokens["legend_border"],
                borderwidth=1,
                font=dict(size=11),
            )
        )
        fig.update_layout(**layout, title=dict(text=title, font=dict(size=15, color=tokens["text_color"])))
        
        fig.update_xaxes(
            gridcolor=tokens["grid_color"], 
            linecolor=tokens["grid_color"], 
            tickcolor=tokens["grid_color"],
            tickfont=dict(color=tokens["text_dim"])
        )
        fig.update_yaxes(
            title_text="Total Revenue (IDR)", 
            gridcolor=tokens["grid_color"], 
            linecolor=tokens["grid_color"], 
            tickcolor=tokens["grid_color"], 
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"])),
            secondary_y=False
        )
        fig.update_yaxes(
            title_text="MoM Growth (%)", 
            showgrid=False, 
            linecolor=tokens["grid_color"], 
            tickcolor=tokens["grid_color"], 
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"])),
            secondary_y=True
        )
        
    else:
        ys = y if isinstance(y, list) else [y]
        fig = go.Figure()
        for i, col in enumerate(ys):
            fig.add_trace(go.Scatter(
                x=df[x], y=df[col], name=col,
                line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
                fill="tozeroy" if len(ys) == 1 else None,
                fillcolor="rgba(0,170,91,0.08)" if len(ys) == 1 else None,
                mode="lines+markers",
                marker=dict(size=5),
            ))
        _apply_base(fig, title)
    return fig


# --- Pie & Donut Charts ---

def donut(df: pd.DataFrame, names: str, values: str, title: str = "") -> go.Figure:
    """Render donut chart representing proportions."""
    fig = px.pie(df, names=names, values=values, hole=0.55,
                 color_discrete_sequence=PALETTE)
    tokens = _get_theme_tokens()
    fig.update_traces(
        textposition="outside", textinfo="percent+label",
        marker=dict(line=dict(color=tokens["donut_border"], width=2)),
    )
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=tokens["plot_bg"],
        font=dict(family="'DM Sans', sans-serif", color=tokens["text_color"], size=12),
        margin=dict(t=40),
        legend=dict(
            bgcolor=tokens["legend_bg"],
            bordercolor=tokens["legend_border"],
            borderwidth=1,
            font=dict(size=11),
        ),
        showlegend=True,
    )
    fig.update_layout(**layout, title=dict(text=title, font=dict(size=15, color=tokens["text_color"])))
    return fig


# --- Heatmaps ---

def heatmap_dow_hour(df: pd.DataFrame, title: str = "Peak Hour Heatmap") -> go.Figure:
    """Render Day of Week × Hour heatmap matrix."""
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pivot = df.pivot_table(
        index="day_of_week", columns="hour",
        values="total_orders", aggfunc="sum", fill_value=0,
    )
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    tokens = _get_theme_tokens()
    theme = st.session_state.get("theme_selector", "Dark Mode")
    if theme == "Light Mode":
        colorscale = [
            [0.0,  "rgba(0,170,91,0.03)"],
            [0.4,  "rgba(0,170,91,0.3)"],
            [0.7,  "rgba(0,159,189,0.6)"],
            [1.0,  "#009FBD"],
        ]
    else:
        colorscale = [
            [0.0,  "rgba(0,170,91,0.05)"],
            [0.4,  "rgba(0,170,91,0.4)"],
            [0.7,  "rgba(0,212,255,0.7)"],
            [1.0,  "#00D4FF"],
        ]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=colorscale,
        showscale=True,
        hoverongaps=False,
        hovertemplate="<b>%{y} %{x}</b><br>Orders: %{z:,}<extra></extra>",
    ))
    
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=tokens["plot_bg"],
        font=dict(family="'DM Sans', sans-serif", color=tokens["text_color"], size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor=tokens["legend_bg"],
            bordercolor=tokens["legend_border"],
            borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            side="bottom", 
            gridcolor=tokens["grid_color"],
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"]))
        ),
        yaxis=dict(
            gridcolor=tokens["grid_color"],
            tickfont=dict(color=tokens["text_dim"]),
            title=dict(font=dict(color=tokens["text_muted"]))
        ),
    )
    fig.update_layout(**layout, title=dict(text=title, font=dict(size=15, color=tokens["text_color"])))
    return fig


# --- Scatter Plots ---

def scatter_driver(df: pd.DataFrame, title: str = "Driver Rating vs Revenue") -> go.Figure:
    """Render scatter plot for driver ratings and earnings."""
    fig = px.scatter(
        df, x="avg_distance_km", y="total_revenue",
        color="vehicle_type", size="total_orders",
        hover_data=["driver_id", "rating"],
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="white"), opacity=0.8))
    return _apply_base(fig, title)


# --- KPI Gauges ---

def gauge_kpi(value: float, title: str, max_val: float = 100,
              threshold: float = 15.0, unit: str = "%") -> go.Figure:
    """Render visual KPI gauge indicator."""
    color = GOGRAB_RED if value > threshold else GOGRAB_GREEN
    tokens = _get_theme_tokens()
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        number=dict(suffix=unit, font=dict(size=28, color=tokens["text_color"])),
        delta=dict(reference=threshold, valueformat=".1f"),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor=tokens["text_color"]),
            bar=dict(color=color, thickness=0.25),
            bgcolor="rgba(0,0,0,0.04)" if st.session_state.get("theme_selector", "Dark Mode") == "Light Mode" else "rgba(255,255,255,0.04)",
            borderwidth=0,
            steps=[
                dict(range=[0, threshold],      color="rgba(0,170,91,0.15)"),
                dict(range=[threshold, max_val], color="rgba(232,44,44,0.1)"),
            ],
            threshold=dict(line=dict(color=ACCENT_YELLOW, width=3), value=threshold),
        ),
    ))
    
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=tokens["plot_bg"],
        font=dict(family="'DM Sans', sans-serif", color=tokens["text_color"], size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor=tokens["legend_bg"],
            bordercolor=tokens["legend_border"],
            borderwidth=1,
            font=dict(size=11),
        )
    )
    fig.update_layout(**layout, title=dict(text=title, font=dict(size=15, color=tokens["text_color"])), height=220)
    return fig


# --- Waterfall Charts ---

def waterfall_discount(df: pd.DataFrame) -> go.Figure:
    """Render waterfall discount distribution comparison."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Revenue", x=df["service_name"], y=df["total_revenue"],
        marker_color=GOGRAB_GREEN, opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="Discount", x=df["service_name"], y=df["total_discount_given"],
        marker_color=GOGRAB_RED, opacity=0.85,
    ))
    _apply_base(fig, "Revenue vs Discount by Service")
    fig.update_layout(barmode="group")
    return fig
