import pandas as pd
from sqlalchemy import create_engine
from faker import Faker
import random
from datetime import datetime, timedelta
import os
import getpass
import sys

# --- SETUP KONEKSI ---
# Ambil password dari env PGPASSWORD atau prompt
PG_USER = os.getenv('PGUSER', 'postgres')
PG_PASS = os.getenv('PGPASSWORD')
PG_HOST = os.getenv('PGHOST', 'localhost')
PG_PORT = os.getenv('PGPORT', 5432)
DB_NAME = 'dwh_gojek'

if not PG_PASS:
    try:
        PG_PASS = getpass.getpass(prompt='Postgres password for user postgres: ')
    except Exception:
        print('Could not read password. Set PGPASSWORD env var and retry.')
        sys.exit(1)

# Buat connection string dengan password
conn_str = f'postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{DB_NAME}'
engine = create_engine(conn_str)
fake = Faker('id_ID')
DW_SCHEMA = 'dwh'

print("🚀 Memulai proses ETL (Versi CSV & Database)...")

# --- 1. GENERATE DATA DIMENSI ---
# dim_customer (10,000 baris) - format dengan 5 digit untuk 00001-10000
customers = [{'customer_id': f'CUST{i:05}', 'gender': random.choice(['Laki-laki', 'Perempuan']), 'age_group': random.choice(['18-25', '26-35', '36-45', '46+']), 'join_date': fake.date_between(start_date='-2y', end_date='today'), 'city': fake.city()} for i in range(1, 10001)]
df_customer = pd.DataFrame(customers)

# dim_driver (10,000 baris) - format dengan 5 digit untuk 00001-10000
drivers = [{'driver_id': f'DRV{i:05}', 'vehicle_type': random.choice(['motor', 'mobil']), 'driver_rating': round(random.uniform(3.5, 5.0), 2), 'driver_status': random.choice(['aktif', 'nonaktif'])} for i in range(1, 10001)]
df_driver = pd.DataFrame(drivers)

# dim_location (100 baris) - format dengan 3 digit untuk 001-100
locations = [{'location_id': f'LOC{i:03}', 'city': fake.city(), 'province': fake.state(), 'region': random.choice(['Jabodetabek', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur', 'Bali'])} for i in range(1, 101)]
df_location = pd.DataFrame(locations)

# dim_time (per jam dari 1 Jan 2023 s.d. 31 Des 2024)
times = []
start_dt = datetime(2023, 1, 1)
end_dt = datetime(2024, 12, 31, 23)
current_dt = start_dt
while current_dt <= end_dt:
    times.append({'time_id': current_dt.strftime('%Y%m%d%H'), 'date': current_dt.date(), 'month': current_dt.month, 'quarter': (current_dt.month - 1) // 3 + 1, 'year': current_dt.year, 'hour': current_dt.hour})
    current_dt += timedelta(hours=1)
df_time = pd.DataFrame(times)

# dim_service & dim_payment
df_service = pd.DataFrame([{'service_id': 'SRV01', 'service_name': 'ride'}, {'service_id': 'SRV02', 'service_name': 'food delivery'}, {'service_id': 'SRV03', 'service_name': 'courier'}])
df_payment = pd.DataFrame([{'payment_id': 'PAY01', 'payment_method': 'e-wallet'}, {'payment_id': 'PAY02', 'payment_method': 'cash'}, {'payment_id': 'PAY03', 'payment_method': 'kartu'}])

# --- 2. GENERATE TABEL FAKTA ---
orders = []
for i in range(1, 100001):  
    price = random.randint(15000, 200000)
    orders.append({
        'order_id': f'ORD{i:06}', 
        'customer_id': f"CUST{random.randint(1, 10000):05}",
        'driver_id': f"DRV{random.randint(1, 10000):05}",
        'service_id': f"SRV0{random.randint(1, 3)}",
        'payment_id': f"PAY0{random.randint(1, 3)}",
        'location_id': f"LOC{random.randint(1, 100):03}",
        'time_id': random.choice(df_time['time_id'].values),
        'price': price,
        'distance': round(random.uniform(1.5, 20.0), 2),
        'discount': random.choice([0, 0, 5000, 10000]),
        'order_status': random.choices(['completed', 'cancelled'], weights=[85, 15])[0]
    })
df_fact = pd.DataFrame(orders)

# --- 3. PROSES SIMPAN KE CSV ---
print("📂 Menyimpan data mentah ke file CSV...")
df_customer.to_csv('dim_customer.csv', index=False)
df_driver.to_csv('dim_driver.csv', index=False)
df_location.to_csv('dim_location.csv', index=False)
df_time.to_csv('dim_time.csv', index=False)
df_service.to_csv('dim_service.csv', index=False)
df_payment.to_csv('dim_payment.csv', index=False)
df_fact.to_csv('fact_order.csv', index=False)

# --- 4. PROSES LOAD KE POSTGRESQL ---
try:
    print("📥 Loading data ke PostgreSQL...")
    df_customer.to_sql('dim_customer', engine, schema=DW_SCHEMA, if_exists='append', index=False)
    df_driver.to_sql('dim_driver', engine, schema=DW_SCHEMA, if_exists='append', index=False)
    df_location.to_sql('dim_location', engine, schema=DW_SCHEMA, if_exists='append', index=False)    
    # Note: dim_time sudah di-seed oleh init.sql, jadi skip upload dari Python
    df_service.to_sql('dim_service', engine, schema=DW_SCHEMA, if_exists='append', index=False)
    df_payment.to_sql('dim_payment', engine, schema=DW_SCHEMA, if_exists='append', index=False)
    df_fact.to_sql('fact_order', engine, schema=DW_SCHEMA, if_exists='append', index=False)
    print("✅ SELESAI! CSV sudah dibuat & Database sudah terisi.")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)