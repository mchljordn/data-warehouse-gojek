"""
KPI card renderer for the GoGrab DWH Dashboard.
Injects CSS once, then renders metric cards via st.markdown.
"""
import streamlit as st


def inject_styles(theme: str = "Dark Mode"):
    """Call once at app startup to inject global dashboard CSS based on active theme."""
    if theme == "Light Mode":
        variables = """
        :root {
            --bg-base:      #F8FAFC;
            --bg-surface:   #FFFFFF;
            --bg-card:      #FFFFFF;
            --bg-card-hover:#F1F5F9;
            --border:       #E2E8F0;
            --green:        #00AA5B;
            --green-glow:   rgba(0,170,91,0.08);
            --red:          #D92727;
            --cyan:         #009FBD;
            --orange:       #E25822;
            --purple:       #9333EA;
            --yellow:       #D97706;
            --text-primary: #0F172A;
            --text-muted:   #475569;
            --text-dim:     #334155;
            --radius:       12px;
        }
        """
    else:
        variables = """
        :root {
            --bg-base:      #080D14;
            --bg-surface:   #0F1620;
            --bg-card:      #141D2A;
            --bg-card-hover:#1A2436;
            --border:       rgba(255,255,255,0.07);
            --green:        #00AA5B;
            --green-glow:   rgba(0,170,91,0.25);
            --red:          #E82C2C;
            --cyan:         #00D4FF;
            --orange:       #FF6B35;
            --purple:       #A855F7;
            --yellow:       #FBBF24;
            --text-primary: #E2E8F0;
            --text-muted:   #64748B;
            --text-dim:     #94A3B8;
            --radius:       12px;
        }
        """

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght=300;400;500;600;700&family=DM+Mono:wght=400;500&display=swap');

    {variables}

    html, body, [class*="css"], .stApp {{
        font-family: 'DM Sans', sans-serif !important;
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
    }}

    /* ── Seamless Header Bar ── */
    [data-testid="stHeader"] {{
        background-color: var(--bg-base) !important;
        border-bottom: 1px solid var(--border) !important;
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: var(--bg-surface) !important;
        border-right: 1px solid var(--border) !important;
    }}
    [data-testid="stSidebar"] * {{ color: var(--text-primary) !important; }}

    /* ── Premium Theme Toggle Button (Card Style) ── */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] div.stButton > button,
    [data-testid="stSidebar"] button {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
        font-size: 14px !important;
        padding: 0 !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.22s ease !important;
        width: 30px !important;
        height: 30px !important;
        margin: 0 !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"] *,
    [data-testid="stSidebar"] div.stButton > button *,
    [data-testid="stSidebar"] button * {{
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        background-color: transparent !important;
    }}
    [data-testid="stSidebar"] button:hover {{
        transform: scale(1.08) !important;
        border-color: var(--green) !important;
        box-shadow: 0 4px 8px rgba(0,170,91,0.12) !important;
        background-color: var(--bg-card) !important;
    }}
    [data-testid="stSidebar"] button:active {{
        background-color: var(--bg-card) !important;
        border-color: var(--green) !important;
    }}

    /* ── Expanders ── */
    [data-testid="stExpanderDetails"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }}
    [data-testid="stExpander"] details, 
    [data-testid="stExpander"] details summary,
    [data-testid="stExpander"] details summary:hover,
    [data-testid="stExpander"] details summary:focus,
    [data-testid="stExpander"] details summary * {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }}
    [data-testid="stExpander"] details {{
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--bg-surface) !important;
        border-bottom: 1px solid var(--border) !important;
        border-radius: var(--radius) var(--radius) 0 0;
        gap: 4px;
        padding: 8px 12px 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: var(--text-muted) !important;
        border-radius: 8px 8px 0 0 !important;
        border: none !important;
        padding: 10px 18px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        transition: all 0.2s;
    }}
    .stTabs [aria-selected="true"] {{
        background: var(--bg-card) !important;
        color: var(--green) !important;
        border-bottom: 2px solid var(--green) !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius) var(--radius);
        padding: 20px !important;
    }}

    /* ── KPI Cards ── */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }}
    .kpi-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        transition: all 0.25s ease;
    }}
    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--accent-color, var(--green));
    }}
    .kpi-card:hover {{ background: var(--bg-card-hover); transform: translateY(-2px); }}
    .kpi-icon  {{ font-size: 22px; margin-bottom: 10px; line-height: 1; }}
    .kpi-label {{ font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-bottom: 6px; }}
    .kpi-value {{ font-size: 19px; font-weight: 700; color: var(--text-primary); font-family: 'DM Mono', monospace; line-height: 1.1; }}
    .kpi-sub   {{ font-size: 11px; color: var(--text-dim); margin-top: 5px; }}
    .kpi-delta-pos {{ color: var(--green); font-size: 11px; font-weight: 600; margin-top: 4px; }}
    .kpi-delta-neg {{ color: var(--red);   font-size: 11px; font-weight: 600; margin-top: 4px; }}

    /* ── Section Headers ── */
    .section-header {{
        font-size: 17px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 28px 0 14px;
        padding-left: 12px;
        border-left: 3px solid var(--green);
        letter-spacing: -0.01em;
    }}

    /* ── Metrics ── */
    [data-testid="stMetricLabel"] * {{
        color: var(--text-muted) !important;
    }}
    [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
    }}
    [data-testid="stMetricDelta"] * {{
        /* Default Delta colors are managed by Streamlit, but we can enforce opacity */
        opacity: 0.9;
    }}

    /* ── Data Tables ── */
    .stDataFrame {{ border-radius: var(--radius) !important; }}
    [data-testid="stDataFrame"] > div {{ border-radius: var(--radius) !important; }}

    /* ── Plotly chart containers ── */
    .js-plotly-plot .plotly {{ border-radius: var(--radius); }}

    /* ── Dividers ── */
    hr {{ border-color: var(--border) !important; }}

    /* ── Selectbox / Multiselect Form Controls ── */
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {{
        background-color: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }}
    .stSelectbox [data-baseweb="select"] * {{
        color: var(--text-primary) !important;
    }}

    /* Multiselect tag items */
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: var(--green-glow) !important;
        border: 1px solid var(--green) !important;
        color: var(--text-primary) !important;
        border-radius: 6px !important;
    }}
    .stMultiSelect [data-baseweb="tag"] span {{
        color: var(--text-primary) !important;
    }}
    .stMultiSelect [data-baseweb="tag"] svg {{
        fill: var(--text-primary) !important;
    }}

    /* Dropdown popup menus */
    div[data-baseweb="popover"], div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul, div[data-baseweb="menu"], ul[role="listbox"] {{
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
    }}
    div[data-baseweb="popover"] li, ul[role="listbox"] li, ul[role="listbox"] div {{
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
    }}
    div[data-baseweb="popover"] li:hover, ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"] {{
        background-color: var(--bg-card-hover) !important;
        color: var(--text-primary) !important;
    }}

    /* ── Custom HTML Tables ── */
    .custom-table {{
        display: block;
        width: 100%;
        border-collapse: collapse;
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary);
        font-size: 11.5px;
        background-color: var(--bg-card);
        border-radius: var(--radius);
        overflow-x: auto;
        white-space: nowrap;
    }}
    .custom-table thead {{
        background-color: var(--bg-card-hover);
        text-align: left;
    }}
    .custom-table th, .custom-table td {{
        padding: 8px 10px;
        border-bottom: 1px solid var(--border);
    }}
    .custom-table tbody tr:hover {{
        background-color: var(--bg-card-hover);
    }}

    /* ── Insight boxes ── */
    .insight-box {{
        background: linear-gradient(135deg, rgba(0,170,91,0.08), rgba(0,212,255,0.05));
        border: 1px solid rgba(0,170,91,0.25);
        border-radius: var(--radius);
        padding: 16px 20px;
        margin: 12px 0;
    }}
    .insight-box .insight-title {{
        font-size: 13px; font-weight: 700; color: var(--green);
        text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;
    }}
    .insight-box ul {{ margin: 0; padding-left: 18px; }}
    .insight-box li {{ font-size: 13px; color: var(--text-dim); margin-bottom: 4px; line-height: 1.5; }}
    </style>
    """, unsafe_allow_html=True)


def kpi_grid(cards: list[dict]):
    """ Renders a row of KPI cards cleanly without breaking Streamlit's Markdown parser. """
    cards_html = ""
    for c in cards:
        accent = c.get("accent", "var(--green)")
        delta_html = ""
        
        if "delta" in c:
            d = c["delta"]
            cls = "kpi-delta-pos" if str(d).startswith("+") or (isinstance(d, (int, float)) and d >= 0) else "kpi-delta-neg"
            delta_html = f'<div class="{cls}">{d}</div>'

        icon_html = f'<div class="kpi-icon">{c["icon"]}</div>' if c.get("icon") else ""
        cards_html += f"""
<div class="kpi-card" style="--accent-color:{accent}">
{icon_html}
<div class="kpi-label">{c["label"]}</div>
<div class="kpi-value">{c["value"]}</div>
{f'<div class="kpi-sub">{c["sub"]}</div>' if c.get("sub") else ""}
{delta_html}
</div>"""

    full_html = f'<div class="kpi-grid">{cards_html}</div>'
    st.markdown(full_html, unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def insight_box(title: str, points: list[str]):
    items = "".join(f"<li>{p}</li>" for p in points)
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">{title}</div>
        <ul>{items}</ul>
    </div>""", unsafe_allow_html=True)
