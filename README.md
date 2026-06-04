# 🛵 GoGrab Data Warehouse Analytics Dashboard

> Streamlit dashboard for the **Perancangan Data Warehouse untuk Analisis Layanan GoGrab** project  
> Universitas Padjadjaran — Michael Jordan, Wa Ode Zachra, Shofy Aliya

---

## 📁 Project Structure

```
gograb_dwh/
├── app.py                          # Main entry point
├── requirements.txt
├── .streamlit/
│   ├── config.toml                 # Dark theme config
│   └── secrets.toml.template       # DB credentials template
│
├── utils/
│   └── db.py                       # SQLAlchemy engine + cached run_query()
│
├── queries/
│   ├── olap_queries.py             # All OLAP SQL (ROLLUP, CUBE, window fns)
│   └── materialized_views.sql      # Materialized views + indexes
│
├── components/
│   ├── charts.py                   # Plotly chart components (dark themed)
│   └── kpi_cards.py                # CSS injection + KPI card renderer
│
└── pages/
    ├── revenue.py                  # Tab 1: Revenue & Service Analytics
    ├── driver_performance.py       # Tab 2: Driver Performance
    ├── demand_time.py              # Tab 3: Demand & Time Analytics
    └── customer_discount.py        # Tab 4: Customer & Discount Analytics
```

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure database credentials

**Option A — Streamlit secrets (recommended for deployment):**
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit secrets.toml with your actual credentials
```

**Option B — Environment variables:**
```bash
export PGUSER=postgres
export PGPASSWORD=your_password
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=___DWH_GOGRAB_PLACEHOLDER___
```

### 3. Run the ETL (if not done already)
```bash
cd ..
python ETL.py
```

### 4. Create materialized views (optional but recommended)
```bash
psql -U postgres -d ___DWH_GOGRAB_PLACEHOLDER___ -f queries/materialized_views.sql
```

### 5. Launch dashboard
```bash
streamlit run app.py
```

---

## 📊 Dashboard Analytics

### Tab 1 — 💰 Revenue & Service
| Analysis | Query Type | Details |
|---|---|---|
| Revenue by service | GROUP BY | Total, avg, share % |
| Monthly revenue trend | Window fn (LAG) | MoM growth rate |
| Revenue by region | **GROUP BY ROLLUP** | Region → Province → City |
| Top 15 cities | GROUP BY | Revenue + cancellation rate |
| Payment method breakdown | Window fn | Order + revenue share % |

### Tab 2 — 🛵 Driver Performance
| Analysis | Query Type | Details |
|---|---|---|
| Fleet summary | GROUP BY | Vehicle type × status |
| Rating distribution | CASE + GROUP BY | 4 rating buckets |
| Top 20 active drivers | ORDER BY | Revenue + completion count |
| Cancellation gauge | Aggregation | vs 15% threshold |

### Tab 3 — ⏱️ Demand & Time
| Analysis | Query Type | Details |
|---|---|---|
| Peak hour heatmap | GROUP BY DOW×Hour | 7×24 grid |
| Hourly distribution | GROUP BY hour | Orders + revenue |
| Cancellation by hour | GROUP BY hour | Risk window detection |
| Quarterly revenue | **GROUP BY ROLLUP** | Year → Quarter |
| Top cities demand | GROUP BY | Order volume |

### Tab 4 — 👥 Customer & Discount
| Analysis | Query Type | Details |
|---|---|---|
| Age × Gender | **GROUP BY CUBE** | Revenue + orders |
| Discount effectiveness | CASE + GROUP BY | Completion rate by tier |
| Discount by age group | CASE + GROUP BY | ROI analysis |
| Cancellation by service | GROUP BY | Rate per service |
| Cancellation by region | **GROUP BY ROLLUP** | Province-level |

---

## 🔧 OLAP Features

### GROUP BY CUBE (queries/olap_queries.py)
```sql
-- Customer CUBE: Age × Gender cross-tabulation
GROUP BY CUBE(c.age_group, c.gender)

-- Revenue CUBE: Service × Payment × Region
GROUP BY CUBE(s.service_name, p.payment_method, l.region)
```

### GROUP BY ROLLUP
```sql
-- Revenue drill-down: Region → Province → City
GROUP BY ROLLUP(l.region, l.province, l.city)

-- Time drill-down: Year → Quarter
GROUP BY ROLLUP(t.year, t.quarter)

-- Cancellation: Region → Province
GROUP BY ROLLUP(l.region, l.province)
```

### Window Functions
```sql
-- MoM growth rate
LAG(revenue) OVER (ORDER BY period)

-- Revenue share %
100.0 * SUM(price) / SUM(SUM(price)) OVER ()
```

---

## ⚡ Performance Optimizations

1. **`@st.cache_data(ttl=300)`** — query results cached 5 min in Streamlit
2. **`@st.cache_resource`** — SQLAlchemy engine created once per session
3. **Materialized views** — pre-aggregated data for the 5 heaviest queries
4. **Composite indexes** — on (order_status, service_id) and all FK columns
5. **QueuePool** — connection pooling (pool_size=5, max_overflow=10)

---

## 💡 Business Insights Generated

Each dashboard tab surfaces **automated text insights** using real query data:

- Revenue: top service, top city, preferred payment method
- Driver: best vehicle type, top driver ID, fleet cancellation alert  
- Demand: peak hour, worst cancellation hour, city allocation recommendation
- Customer: highest-value age group, most effective discount tier, worst-cancel service
