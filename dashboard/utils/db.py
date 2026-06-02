"""
Database connection utilities for Gojek DWH Dashboard.
Uses SQLAlchemy + psycopg2 with Streamlit caching for performance.
"""
import os
import streamlit as st
import toml
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool


# ─── Connection Config ────────────────────────────────────────────────────────
def get_connection_string() -> str:
    """Bypass absolut: Membaca secrets.toml lokal secara paksa tanpa st.secrets"""
    try:
        # Tentukan jalur mutlak ke file secrets lokal di folder proyek
        local_secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
        
        if os.path.exists(local_secrets_path):
            # Baca file TOML secara manual sebagai dictionary Python
            config = toml.load(local_secrets_path)
            cfg = config["postgres"]
        else:
            # Fallback pakai st.secrets bawaan kalau file lokal tidak ketemu
            cfg = st.secrets["postgres"]
            
        # Gunakan IP 127.0.0.1 agar aman dari bentrok IPv6 localhost (::1)
        host = "127.0.0.1" if cfg['host'] == "localhost" else cfg['host']
        return f"postgresql://{cfg['user']}:{cfg['password']}@{host}:{cfg['port']}/{cfg['dbname']}"
    
    except Exception as e:
        st.error(f"🔴 Gagal memuat kredensial database via Bypass Manual: {e}")
        return ""


@st.cache_resource(show_spinner=False)
def get_engine():
    """
    Cached SQLAlchemy engine — created once per session.
    QueuePool ensures connections are reused efficiently.
    """
    conn_str = get_connection_string()
    engine = create_engine(
        conn_str,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,     # auto-reconnect on stale connections
        connect_args={"options": "-csearch_path=dwh"},
    )
    return engine


# ─── Query Runner ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)   # cache 5 minutes
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """
    Execute a SQL query and return a DataFrame.
    Results are cached for 5 minutes to reduce DB load.

    Args:
        sql: SQL query string (use :param_name for named params)
        params: Optional dict of query parameters

    Returns:
        pd.DataFrame with query results
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df


def test_connection() -> bool:
    """Quick connectivity test — returns True if DB is reachable."""
    try:
        run_query.clear()   # bypass cache for health check
        df = run_query("SELECT 1 AS ok")
        return bool(df["ok"].iloc[0] == 1)
    except Exception as e:
        return str(e)
