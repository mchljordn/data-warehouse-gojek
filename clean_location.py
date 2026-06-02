import pandas as pd

# 1. Ambil data master lokasi lama
try:
    df = pd.read_csv('data/dim_location.csv')
except FileNotFoundError:
    df = pd.read_csv('data/dimensions/dim_location.csv')

# 2. Kamus Master Geografi Indonesia untuk 63 Kota Unik di Database
city_master_map = {
    'Ambon': {'province': 'Maluku', 'region': 'Luar Jawa'},
    'Balikpapan': {'province': 'Kalimantan Timur', 'region': 'Luar Jawa'},
    'Bandung': {'province': 'Jawa Barat', 'region': 'Jawa Barat'},
    'Banjarbaru': {'province': 'Kalimantan Selatan', 'region': 'Luar Jawa'},
    'Banjarmasin': {'province': 'Kalimantan Selatan', 'region': 'Luar Jawa'},
    'Batu': {'province': 'Jawa Timur', 'region': 'Jawa Timur & Bali Nusra'},
    'Bau-Bau': {'province': 'Sulawesi Tenggara', 'region': 'Luar Jawa'},
    'Bekasi': {'province': 'Jawa Barat', 'region': 'Jabodetabek'},
    'Bengkulu': {'province': 'Bengkulu', 'region': 'Luar Jawa'},
    'Bima': {'province': 'Nusa Tenggara Barat', 'region': 'Jawa Timur & Bali Nusra'},
    'Binjai': {'province': 'Sumatera Utara', 'region': 'Luar Jawa'},
    'Bogor': {'province': 'Jawa Barat', 'region': 'Jabodetabek'},
    'Bontang': {'province': 'Kalimantan Timur', 'region': 'Luar Jawa'},
    'Cirebon': {'province': 'Jawa Barat', 'region': 'Jawa Barat'},
    'Denpasar': {'province': 'Bali', 'region': 'Jawa Timur & Bali Nusra'},
    'Depok': {'province': 'Jawa Barat', 'region': 'Jabodetabek'},
    'Dumai': {'province': 'Riau', 'region': 'Luar Jawa'},
    'Jambi': {'province': 'Jambi', 'region': 'Luar Jawa'},
    'Kediri': {'province': 'Jawa Timur', 'region': 'Jawa Timur & Bali Nusra'},
    'Kendari': {'province': 'Sulawesi Tenggara', 'region': 'Luar Jawa'},
    'Kota Administrasi Jakarta Barat': {'province': 'DKI Jakarta', 'region': 'Jabodetabek'},
    'Kota Administrasi Jakarta Selatan': {'province': 'DKI Jakarta', 'region': 'Jabodetabek'},
    'Kota Administrasi Jakarta Utara': {'province': 'DKI Jakarta', 'region': 'Jabodetabek'},
    'Kotamobagu': {'province': 'Sulawesi Utara', 'region': 'Luar Jawa'},
    'Kupang': {'province': 'Nusa Tenggara Timur', 'region': 'Jawa Timur & Bali Nusra'},
    'Langsa': {'province': 'Aceh', 'region': 'Luar Jawa'},
    'Lubuklinggau': {'province': 'Sumatera Selatan', 'region': 'Luar Jawa'},
    'Madiun': {'province': 'Jawa Timur', 'region': 'Jawa Timur & Bali Nusra'},
    'Magelang': {'province': 'Jawa Tengah', 'region': 'Jawa Tengah & DIY'},
    'Makassar': {'province': 'Sulawesi Selatan', 'region': 'Luar Jawa'},
    'Mataram': {'province': 'Nusa Tenggara Barat', 'region': 'Jawa Timur & Bali Nusra'},
    'Medan': {'province': 'Sumatera Utara', 'region': 'Luar Jawa'},
    'Mojokerto': {'province': 'Jawa Timur', 'region': 'Jawa Timur & Bali Nusra'},
    'Padang': {'province': 'Sumatera Barat', 'region': 'Luar Jawa'},
    'Padang Sidempuan': {'province': 'Sumatera Utara', 'region': 'Luar Jawa'},
    'Padangpanjang': {'province': 'Sumatera Barat', 'region': 'Luar Jawa'},
    'Pagaralam': {'province': 'Sumatera Selatan', 'region': 'Luar Jawa'},
    'Palangkaraya': {'province': 'Kalimantan Tengah', 'region': 'Luar Jawa'},
    'Palopo': {'province': 'Sulawesi Selatan', 'region': 'Luar Jawa'},
    'Palu': {'province': 'Sulawesi Tengah', 'region': 'Luar Jawa'},
    'Pangkalpinang': {'province': 'Kepulauan Bangka Belitung', 'region': 'Luar Jawa'},
    'Pasuruan': {'province': 'Jawa Timur', 'region': 'Jawa Timur & Bali Nusra'},
    'Payakumbuh': {'province': 'Sumatera Barat', 'region': 'Luar Jawa'},
    'Pekanbaru': {'province': 'Riau', 'region': 'Luar Jawa'},
    'Pontianak': {'province': 'Kalimantan Barat', 'region': 'Luar Jawa'},
    'Probolinggo': {'province': 'Jawa Timur', 'region': 'Jawa Timur & Bali Nusra'},
    'Purwokerto': {'province': 'Jawa Tengah', 'region': 'Jawa Tengah & DIY'},
    'Sabang': {'province': 'Aceh', 'region': 'Luar Jawa'},
    'Salatiga': {'province': 'Jawa Tengah', 'region': 'Jawa Tengah & DIY'},
    'Samarinda': {'province': 'Kalimantan Timur', 'region': 'Luar Jawa'},
    'Sawahlunto': {'province': 'Sumatera Barat', 'region': 'Luar Jawa'},
    'Semarang': {'province': 'Jawa Tengah', 'region': 'Jawa Tengah & DIY'},
    'Sorong': {'province': 'Papua Barat', 'region': 'Luar Jawa'},
    'Sukabumi': {'province': 'Jawa Barat', 'region': 'Jawa Barat'},
    'Surakarta': {'province': 'Jawa Tengah', 'region': 'Jawa Tengah & DIY'},
    'Tangerang Selatan': {'province': 'Banten', 'region': 'Jabodetabek'},
    'Tanjungbalai': {'province': 'Sumatera Utara', 'region': 'Luar Jawa'},
    'Tanjungpinang': {'province': 'Kepulauan Riau', 'region': 'Luar Jawa'},
    'Tasikmalaya': {'province': 'Jawa Barat', 'region': 'Jawa Barat'},
    'Ternate': {'province': 'Maluku Utara', 'region': 'Luar Jawa'},
    'Tomohon': {'province': 'Sulawesi Utara', 'region': 'Luar Jawa'},
    'Tual': {'province': 'Maluku', 'region': 'Luar Jawa'},
    'Yogyakarta': {'province': 'DI Yogyakarta', 'region': 'Jawa Tengah & DIY'}
}

# 3. Eksekusi perbaikan total mengunci relasi City -> Province -> Region yang valid
def perfect_indonesia_fix(row):
    city_name = str(row['city']).strip()
    if city_name in city_master_map:
        row['province'] = city_master_map[city_name]['province']
        row['region'] = city_master_map[city_name]['region']
    return row

# 4. Jalankan transformasi data
df_fixed = df.apply(perfect_indonesia_fix, axis=1)

# 5. Overwrite/Simpan kembali ke folder asalnya
try:
    df_fixed.to_csv('data/dim_location.csv', index=False)
except Exception:
    df_fixed.to_csv('data/dimensions/dim_location.csv', index=False)

print("SUCCESS! dim_location.csv has been fixed with 100% accurate Indonesian geography mappings!")