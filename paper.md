# Designing a Star Schema Data Warehouse for Ride-Hailing Service Analytics with OLAP Operations

**Michael Jordan**
Informatics Engineering
Padjadjaran University
michael@mail.unpad.ac.id

**Wa Ode Zachra**
Informatics Engineering
Padjadjaran University
waode@mail.unpad.ac.id

**Shofy Aliya**
Informatics Engineering
Padjadjaran University
shofy@mail.unpad.ac.id

---

**Abstract** — The rapid growth of ride-hailing platforms in Indonesia generates vast volumes of transactional data encompassing ride orders, food deliveries, and courier services. However, this data is typically stored across heterogeneous operational systems, making it difficult to perform integrated, multidimensional analysis that can guide strategic business decisions. This paper presents the design and implementation of a data warehouse for a simulated ride-hailing platform modeled after Indonesian super-app services, to enable comprehensive service analytics. The data warehouse adopts a star schema architecture with a central fact table (fact_order) containing 100,000 synthetic transaction records and six dimension tables (dim_customer, dim_driver, dim_service, dim_time, dim_location, and dim_payment), implemented on PostgreSQL. An Extract-Transform-Load (ETL) pipeline was developed using Python (Pandas, Faker, SQLAlchemy) to generate realistic synthetic data reflecting Indonesian geographic distributions, temporal patterns across 2023–2024, and service characteristics. The analytical layer leverages advanced OLAP operations including GROUP BY ROLLUP for hierarchical drill-down analysis (region → province → city), GROUP BY CUBE for multidimensional cross-tabulation of customer demographics (age group × gender), and window functions such as LAG for month-over-month revenue trend analysis. Five materialized views with composite indexes were created to optimize query performance for the most computationally intensive analytical queries. The results are surfaced through an interactive Streamlit dashboard organized into four analytical modules: Revenue & Service Analytics, Driver Performance, Demand & Time Analytics, and Customer & Discount Analysis, each providing automated business insights derived from real query outputs. This work demonstrates the effectiveness of data warehouse design principles in transforming raw transactional data into actionable business intelligence for ride-hailing service optimization.

**Keywords** — data warehouse, star schema, OLAP, ETL, ride-hailing, PostgreSQL, business intelligence, Streamlit

---

## I. INTRODUCTION

The digital economy in Indonesia has undergone a remarkable transformation over the past decade, with the country emerging as one of the largest and most dynamic digital markets in Southeast Asia. Indonesia's internet user base has surpassed 210 million individuals, with the majority accessing online services through smartphones [1]. This widespread digital connectivity has fundamentally reshaped consumer behavior, particularly in urban transportation, where traditional modes of transit have been progressively supplemented—and in many cases replaced—by on-demand ride-hailing services. The ride-hailing industry has experienced extraordinary growth, driven by rapid urbanization and the increasing demand for accessible and affordable transportation, with major platforms capturing significant market share by addressing chronic urban mobility challenges including traffic congestion, limited public transit coverage, and the need for reliable first-and-last-mile connectivity.

Notably, these platforms have evolved beyond simple ride-booking applications into comprehensive "super-app" ecosystems that integrate ride-hailing, food delivery, courier services, and digital payment functionalities under a single platform [2]. This diversification has resulted in the generation of massive volumes of transactional data spanning multiple service categories, geographic regions, customer demographics, payment methods, and temporal patterns—each completed or cancelled order generating a data point that, when analyzed collectively, can reveal patterns of immense strategic value.

However, the operational databases that support these platforms are typically designed for Online Transactional Processing (OLTP) and are ill-suited for the complex, multidimensional analytical queries required by business stakeholders to derive strategic insights [3]. OLTP systems are optimized for high-throughput insert, update, and delete operations on individual records, with normalized schemas that minimize data redundancy and ensure transactional integrity. This fundamental mismatch between OLTP and OLAP (Online Analytical Processing) requirements creates a bottleneck for data-driven decision-making—business analysts seeking to answer questions such as "What is the month-over-month revenue growth for each service category across different geographic regions?" face prohibitively slow query execution times on transactional databases, which lack the indexing strategies and schema structures optimized for such workloads.

Data Warehouse (DW) systems address this mismatch by providing subject-oriented, integrated, time-variant, and non-volatile repositories of historical data specifically engineered for OLAP workloads [3]. Through dimensional modeling, data warehouses restructure operational data into analytical schemas that optimize read-heavy aggregation queries. The star schema, first formalized by Kimball and Ross [4], organizes data around a central fact table containing quantitative business measures, surrounded by denormalized dimension tables that provide descriptive context along various analytical axes. The simplicity of this topology—requiring only single-level joins between fact and dimension tables—yields significant query performance benefits and aligns intuitively with how business users conceptualize their analytical questions [5].

The Extract-Transform-Load (ETL) process serves as the pipeline mechanism for populating and maintaining the data warehouse, handling extraction from heterogeneous sources, transformation for quality assurance and schema conformance, and loading into the target analytical schema [6]. Modern ETL implementations increasingly leverage Python-based frameworks such as Pandas and SQLAlchemy, which provide flexibility in handling diverse data formats and complex transformation logic [7]. Furthermore, performance optimization techniques including materialized views, composite indexing, and application-level caching within relational database management systems like PostgreSQL significantly improve query responsiveness for interactive analytical workloads [8].

Despite the maturity of data warehousing theory, there remains a notable gap in the literature regarding the practical application of star schema design and advanced OLAP operations specifically tailored to the ride-hailing domain in the Indonesian context. Most existing studies on ride-hailing data analytics focus on machine learning-based demand forecasting [9], sentiment analysis of user reviews [10], or pricing strategy optimization, while the foundational data infrastructure required to support such analytics—namely, a well-designed data warehouse—receives comparatively less attention.

This paper presents the design and implementation of an OLAP-ready data warehouse for a simulated Indonesian ride-hailing platform. The system ingests synthetically generated CSV source files representing the core operational entities of a ride-hailing ecosystem—customers, drivers, services, orders, payments, locations, and time—totaling 100,000 transactional records. The warehouse layer implements a star schema consisting of one central fact table, fact_order, surrounded by six dimension tables: dim_customer, dim_driver, dim_service, dim_time, dim_location, and dim_payment. The OLAP layer derives five materialized views from the warehouse, enabling lightweight multidimensional queries without repeated execution of complex multi-table joins at visualization time. An interactive Streamlit dashboard connected directly to the PostgreSQL OLAP schema serves as the analytical delivery interface, providing business stakeholders with cross-divisional KPI visibility across four analytical domains: revenue and service analytics, driver performance, demand and time patterns, and customer and discount effectiveness.

The primary contributions of this work are threefold: (1) a star schema data warehouse implemented on PostgreSQL with strict schema-level separation between ETL and analytical layers; (2) a comprehensive OLAP query library implementing GROUP BY ROLLUP, GROUP BY CUBE, and window functions for multidimensional analysis; and (3) an interactive Streamlit dashboard with automated business insight generation across four analytical modules.

---

## II. LITERATURE REVIEW

### A. Data Warehouse Architecture
Data Warehouse systems were formally defined by Inmon [3] as subject-oriented, integrated, time-variant, and non-volatile collections of data designed to support management decision-making. Kimball and Ross [4] proposed a complementary bottom-up approach centered on dimensional modeling, where the Star Schema—a central fact table surrounded by denormalized dimension tables—serves as the foundational structure optimized for OLAP workloads [5].

### B. Rationale for Star Schema
While alternative dimensional models such as the Snowflake Schema reduce data redundancy through normalized dimension tables, the Star Schema remains the preferred architecture for many analytical workloads. The Star Schema's denormalized structure requires only a single join to connect the central fact table to any given dimension, significantly reducing query execution time compared to the multi-level joins required by a Snowflake Schema [4], [5]. For a ride-hailing analytics system where fast, interactive dashboard rendering is prioritized over storage efficiency, the Star Schema provides optimal query performance and a highly intuitive structure for business users.

### C. ETL Processes and Domain Context
The ETL (Extract-Transform-Load) process is the backbone of data warehouse population, handling extraction, quality assurance, and schema-conformant loading [6]. Modern implementations leverage Python-based frameworks such as Pandas and SQLAlchemy for flexible data manipulation [7]. In the Indonesian ride-hailing context, existing studies predominantly focus on demand forecasting [9] and sentiment analysis [10] rather than underlying data infrastructure design, which the present study aims to address [1], [2].

---

## III. METHODOLOGY

The development of the ride-hailing Business Intelligence system followed a structured architecture implemented on PostgreSQL, encompassing data generation, ETL pipeline design, star schema construction, OLAP query implementation, performance optimization, and interactive dashboard deployment.

### A. Star Schema Design

The data warehouse schema follows the Kimball dimensional modeling approach with a star schema topology consisting of one central fact table and six surrounding dimension tables.

The **fact table** (fact_order) captures transaction events at the individual order grain. Each record stores four quantitative measures—price (order amount in IDR), distance (trip distance in km), discount (discount amount applied), and order_status (completed or cancelled)—alongside six foreign keys referencing all dimension tables.

TABLE I. STAR SCHEMA TABLE STRUCTURE

| Table | Type | Primary Key | Key Attributes |
|---|---|---|---|
| fact_order | Fact | order_id | price, distance, discount, order_status, 6 FKs |
| dim_customer | Dimension | customer_id | gender, age_group, join_date, city |
| dim_driver | Dimension | driver_id | vehicle_type, driver_rating, driver_status |
| dim_service | Dimension | service_id | service_name (ride, food delivery, courier) |
| dim_time | Dimension | time_id | date, month, quarter, year, hour |
| dim_location | Dimension | location_id | city, province, region |
| dim_payment | Dimension | payment_id | payment_method (e-wallet, cash, kartu) |

The dim_time table implements hourly granularity spanning January 1, 2023 through December 31, 2024, producing 17,520 time records. The dim_location table maps 100 locations to Indonesian geographic hierarchies (city → province → region) derived from a curated city_master.json reference file.

### B. ETL Pipeline

The ETL pipeline was implemented as a Python script (ETL.py) utilizing Pandas for data manipulation, Faker (id_ID locale) for Indonesian-localized synthetic data generation, and SQLAlchemy for database connectivity.

**Generation Phase.** Dimension data is generated first: 10,000 customer records with randomized demographic attributes, 10,000 driver records with vehicle types and ratings (3.5–5.0), 100 location records mapped to real Indonesian cities, and hourly time records spanning 2023–2024. The fact table generates 100,000 order records with prices uniformly distributed between Rp 15,000–200,000, distances ranging 1.5–20.0 km, and an 85:15 completed-to-cancelled ratio.

**Transformation Phase.** Identifiers are formatted with zero-padded suffixes (e.g., CUST00001, DRV00001, LOC001). Discount values follow a weighted distribution: 50% no discount, 25% Rp 5,000, and 25% Rp 10,000. A fixed random seed (seed=42) ensures full reproducibility.

**Loading Phase.** Transformed data is loaded into the PostgreSQL dwh schema using SQLAlchemy's to_sql method, respecting referential integrity by populating dimension tables before the fact table. All data is additionally exported to CSV files for backup and portability.

TABLE II. FINAL ROW COUNTS: DATA WAREHOUSE TABLES

| Table | Row Count | Notes |
|---|---|---|
| fact_order | 100,000 | 1 row per order |
| dim_customer | 10,000 | Unique customers |
| dim_driver | 10,000 | Unique drivers |
| dim_service | 3 | ride, food delivery, courier |
| dim_payment | 3 | e-wallet, cash, kartu |
| dim_location | 100 | Unique city-province-region mappings |
| dim_time | 17,520 | Hourly records, Jan 2023 – Dec 2024 |

### C. OLAP Query Implementation

The analytical layer implements a comprehensive library of parameterized OLAP queries supporting dynamic sidebar filtering across year, region, service, city, vehicle type, and payment method dimensions.

**GROUP BY ROLLUP.** Three ROLLUP queries implement hierarchical drill-down:
- Revenue by Region: `GROUP BY ROLLUP(region, province, city)` with GROUPING() labels for subtotal rows.
- Revenue by Quarter: `GROUP BY ROLLUP(year, quarter)` for quarterly revenue with annual subtotals.
- Cancellation by Region: `GROUP BY ROLLUP(region, province)` for geographic cancellation analysis.

**GROUP BY CUBE.** Customer demographics analysis employs `GROUP BY CUBE(customer_segment, gender)` to generate a complete cross-tabulation of revenue, order volume, and cancellation rate across all dimension combinations.

**Window Functions.** The LAG() function calculates month-over-month growth: `100.0 * (revenue - LAG(revenue) OVER (ORDER BY period)) / NULLIF(LAG(revenue) OVER (ORDER BY period), 0)`. Revenue share is computed via `SUM(price) / SUM(SUM(price)) OVER ()`.

**Conditional Aggregation.** CASE expressions with GROUP BY implement segmentation: driver rating buckets (Elite, Good, Average, Low), discount tiers (No Discount, Rp 1–5K, Rp 5K+), time-of-day segments, customer tenure categories, and discount hunter behavior classification.

TABLE III. OLAP OPERATIONS VALIDATION

| OLAP Operation | Implementation | Query Target |
|---|---|---|
| Roll-up | GROUP BY ROLLUP(region, province, city) | Geographic revenue hierarchy |
| Drill-down | GROUP BY ROLLUP(year, quarter) | Temporal revenue decomposition |
| Slice | WHERE service_name = 'ride' | Single-service filtering |
| Dice | WHERE year = 2024 AND region = 'Jawa' | Multi-dimension intersection |
| Pivot | CASE WHEN payment_method... | Payment method cross-tabulation |

### D. Performance Optimization

Five materialized views were created to pre-aggregate the heaviest analytical queries:

TABLE IV. MATERIALIZED VIEWS SUMMARY

| Materialized View | Grain | Analytical Scope |
|---|---|---|
| mv_revenue_by_service | Service | Service-level revenue and order counts |
| mv_monthly_revenue | Month, Service | Monthly revenue trends by service |
| mv_driver_performance | Driver | Driver-level metrics and completion rates |
| mv_peak_hour | Day-of-week, Hour | Hourly order volume heatmap data |
| mv_city_revenue | City, Province, Region | Geographic revenue distribution |

Six single-column indexes and one composite index (order_status, service_id) were created on fact_order. Connection pooling via SQLAlchemy QueuePool (pool_size=5, max_overflow=10) and Streamlit caching (@st.cache_data with TTL=300s) provide additional performance layers.

### E. Business Intelligence Dashboard

The Streamlit dashboard connects directly to the PostgreSQL dwh schema and organizes analytics into four tabbed modules:

**Tab 1 — Revenue & Service:** Revenue by service type (bar chart), payment method distribution (donut), monthly revenue with MoM growth (dual-axis line), top 15 cities (bar), regional revenue via ROLLUP (data table), geo-tier Java vs. non-Java comparison (donut).

**Tab 2 — Driver Performance:** Fleet status KPIs, performance by vehicle type and status (grouped bar), cancellation gauge vs. 15% threshold, rating distribution across buckets (grouped bar), revenue impact by rating tier, top 20 driver leaderboard.

**Tab 3 — Demand & Time:** Peak hour heatmap (7×24 grid), hourly order/revenue/cancellation trends (line charts), time-of-day segmentation (donut), quarterly revenue via ROLLUP (grouped bar), top 20 demand cities (bar).

**Tab 4 — Customer & Discount:** Demographics via CUBE cross-tabulation (grouped bar), customer tenure segmentation, discount effectiveness by tier and service (grouped bar + waterfall), discount cost by age group (stacked bar), discount hunter vs. organic user analysis (donut), cancellation by service and by province via ROLLUP (bar).

Each tab concludes with automated insight generation that programmatically extracts key findings from query results and presents formatted business recommendations.

---

## IV. RESULTS AND DISCUSSION

### A. ETL Pipeline and Data Warehouse Construction Results

The ETL pipeline was executed successfully, producing a validated star schema data warehouse in the PostgreSQL dwh schema. Seven CSV source files were generated and ingested, comprising 100,000 fact records and dimension data distributed across customer, driver, service, payment, location, and time domains. All foreign key references from the fact table to dimension tables were validated with no orphan records detected and no null values present in core metric columns.

The star schema topology proved effective in supporting the diverse analytical queries required by the dashboard. The single-join architecture between the fact table and each dimension table resulted in straightforward query construction, while the denormalized dimension tables eliminated the need for cascading joins that would be required in a snowflake schema. The consistent use of surrogate key patterns (e.g., CUST00001, DRV00001) ensured clean referential integrity across all relationships.

### B. OLAP Layer and Dashboard Analysis

The revenue analysis module demonstrated effective service-level performance comparison through window functions. The `SUM(price) / SUM(SUM(price)) OVER ()` pattern computed each service's revenue share percentage in a single query pass. Monthly revenue trend analysis using LAG() successfully calculated month-over-month growth rates, revealing temporal patterns across the 24-month observation period.

The regional revenue drill-down using `GROUP BY ROLLUP(region, province, city)` demonstrated hierarchical aggregation within a single query. The GROUPING() function correctly identified subtotal rows at each level, allowing the dashboard to present both granular city-level data and rolled-up regional summaries simultaneously. The geo-tier segmentation comparing Java and non-Java regions provided geographic insights for resource allocation decisions.

The driver performance module showcased operational analytics capabilities. The rating distribution analysis using CASE-based bucketing (Elite: 4.8–5.0, Good: 4.5–4.7, Average: 4.0–4.4, Low: < 4.0) provided a fleet quality assessment framework. The cancellation rate gauge, benchmarked against a 15% corporate threshold, demonstrated KPI monitoring with automatic visual warnings when thresholds are exceeded.

The demand and time module leveraged the hourly resolution of dim_time to produce a 7×24 peak hour heatmap, time-of-day segmentation across five operational periods, and hourly cancellation rate trends. The quarterly analysis using `GROUP BY ROLLUP(year, quarter)` produced quarterly breakdowns with automatic annual subtotals.

The customer analytics module demonstrated the most advanced OLAP operation: `GROUP BY CUBE(customer_segment, gender)`. The CUBE operation generated a complete cross-tabulation including individual cells, row margins, column margins, and a grand total in a single SQL execution. The discount effectiveness analysis compared completion rates across three tiers stratified by service, while the discount hunter segmentation classified customers based on discount utilization frequency (≥ 50% threshold).

### C. Analytical Layer Evaluation

OLAP operations were validated through SQL queries executed directly against the warehouse schema. The roll-up operation aggregating revenue by region produces hierarchical totals that reconcile with the overall revenue figure on the dashboard. The drill-down from region to city level correctly decomposes regional totals into constituent city contributions, verifying aggregation consistency across geographic hierarchy levels. The slice operation filtering by a single service category returns results consistent with the service-level charts. The dice operation combining multiple dimension filters produces proper subsets of individual slice results, confirming correct intersection behavior.

The Streamlit dashboard integration with the OLAP schema demonstrates that materialized views and pre-aggregated structures significantly reduce query complexity at the visualization layer. Rather than executing multi-table joins at report rendering time, the dashboard queries pre-computed materialized views, enabling responsive visualization of aggregate metrics. The combination of database-level optimization (indexes and materialized views), middleware-level caching (Streamlit @st.cache_data), and connection management (SQLAlchemy QueuePool) created a multi-layered performance architecture maintaining responsive interactions with the 100,000-record fact table.

---

## V. CONCLUSION

This paper presented the design and implementation of a star schema data warehouse for service analytics on a simulated Indonesian ride-hailing platform. The system successfully demonstrates the complete data warehouse lifecycle—from synthetic data generation through ETL processing, star schema storage, OLAP query execution, and interactive dashboard visualization.

The star schema architecture with one fact table and six dimension tables proved effective in supporting multidimensional analytical queries. The ETL pipeline using Python (Pandas, Faker, SQLAlchemy) generated 100,000 reproducible synthetic records with realistic Indonesian characteristics. Advanced OLAP operations—GROUP BY ROLLUP for geographic and temporal drill-down, GROUP BY CUBE for customer demographic cross-tabulation, and window functions for trend analysis—demonstrated the analytical depth achievable through well-designed SQL queries on a properly structured dimensional model.

The interactive Streamlit dashboard with four analytical modules successfully transformed warehouse queries into actionable business insights with automated recommendation generation. Performance optimization through materialized views, composite indexing, and application-level caching ensured responsive dashboard interactions.

Limitations include the use of synthetic rather than production data and the absence of incremental ETL capabilities. Future work includes integrating real-world anonymized data, implementing change data capture for near-real-time updates, extending the schema with additional fact tables, and incorporating predictive analytics models leveraging the warehouse as a feature store.

---

## REFERENCES

[1] K. Silalahi, A. Situmorang, and R. Simanungkalit, "Analysis of ride-hailing platform adoption and growth in Indonesian urban areas," *World Journal of Advanced Research and Reviews*, vol. 18, no. 2, pp. 345–356, 2023.

[2] A. Wibowo and P. Handayani, "The evolution of super-app ecosystems: A case study of ride-hailing platforms in Southeast Asia," *SHS Web of Conferences*, vol. 76, p. 01042, 2023.

[3] W. H. Inmon, *Building the Data Warehouse*, 4th ed. Indianapolis, IN, USA: John Wiley & Sons, 2005.

[4] R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed. Indianapolis, IN, USA: John Wiley & Sons, 2013.

[5] S. Chaudhuri and U. Dayal, "An overview of data warehousing and OLAP technology," *ACM SIGMOD Record*, vol. 26, no. 1, pp. 65–74, 1997.

[6] P. Vassiliadis, "A survey of extract-transform-load technology," *International Journal of Data Warehousing and Mining*, vol. 5, no. 3, pp. 1–27, 2009.

[7] W. Sovia, M. Afri, and H. Darwis, "Data warehouse design with ETL method (extract, transform, and load) for company information centre," *International Journal of Artificial Intelligence Research*, vol. 5, no. 1, pp. 75–83, 2021.

[8] D. Joiner, A. Smith, and M. Patel, "Data warehouse vs. OLTP performance optimization in the cloud on PostgreSQL: A case study," *Proceedings of the International Conference on Data Engineering*, pp. 112–119, 2022.

[9] Y. Wang, H. Zheng, and F. Wu, "Demand forecasting for ride-hailing platforms: A deep learning approach," *Transportation Research Part C: Emerging Technologies*, vol. 127, p. 103120, 2021.

[10] A. Putri and B. Setiawan, "Sentiment analysis on ride-hailing user reviews using machine learning classification," *Jurnal Teknologi Informasi*, vol. 8, no. 3, pp. 45–58, 2022.

[11] E. F. Codd, S. B. Codd, and C. T. Salley, "Providing OLAP (On-Line Analytical Processing) to user-analysts: An IT mandate," *Codd and Date*, vol. 32, 1993.

[12] J. Gray et al., "Data cube: A relational aggregation operator generalizing group-by, cross-tab, and sub-totals," *Data Mining and Knowledge Discovery*, vol. 1, no. 1, pp. 29–53, 1997.

[13] ISO/IEC 9075-2:2003, *Information technology — Database languages — SQL — Part 2: Foundation*, International Organization for Standardization, 2003.
