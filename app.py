import streamlit as st
import pandas as pd
import os

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="IT Asset Management",
    page_icon="💻",
    layout="wide"
)

# Nama File Database Lokal
DB_FILE = "database_asset.csv"

# Daftar Kolom Sesuai Permintaan
COLUMNS = [
    "Ket Wilayah", "SN", "Tipe", "Model", "Status Beli", "Asal PO",
    "Status", "NIK", "User", "Kd Site", "Site", "No Mobil",
    "SIM Card", "Imei", "Keterangan"
]

STATUS_OPTIONS = ["Pakai", "Rusak", "Hilang", "Jual"]

# Fungsi Memuat Data
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)
        # Pastikan seluruh kolom tersedia
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS]
    else:
        return pd.DataFrame(columns=COLUMNS)

# Fungsi Menyimpan Data
def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Inisialisasi Data
df_asset = load_data()

# --- HEADER APLIKASI ---
st.title("💻 IT Asset Management System")
st.markdown("---")

# --- DASHBOARD RINGKASAN ---
col1, col2, col3, col4, col5 = st.columns(5)
total_asset = len(df_asset)
pakai_count = len(df_asset[df_asset["Status"] == "Pakai"]) if not df_asset.empty else 0
rusak_count = len(df_asset[df_asset["Status"] == "Rusak"]) if not df_asset.empty else 0
hilang_count = len(df_asset[df_asset["Status"] == "Hilang"]) if not df_asset.empty else 0
jual_count = len(df_asset[df_asset["Status"] == "Jual"]) if not df_asset.empty else 0

col1.metric("Total Aset", total_asset)
col2.metric("Pakai", pakai_count)
col3.metric("Rusak", rusak_count)
col4.metric("Hilang", hilang_count)
col5.metric("Jual", jual_count)

st.markdown("---")

# --- TAB FITUR UTAMA ---
tab1, tab2, tab3 = st.tabs(["📋 Daftar & Filter Aset", "📤 Upload Excel/CSV", "➕ Tambah Manual"])

# TAB 1: LIHAT & FILTER DATA
with tab1:
    st.subheader("Daftar Aset Terdaftar")
    
    # Filter Pencarian
    search_term = st.text_input("🔍 Cari (berdasarkan SN, User, Site, Tipe, dll):", "")
    
    df_filtered = df_asset.copy()
    if search_term:
        mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]
    
    # Tampilkan Tabel Data
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    
    # Tombol Download Data Saat Ini
    if not df_filtered.empty:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Data Ke CSV",
            data=csv,
            file_name="export_it_asset.csv",
            mime="text/csv"
        )

# TAB 2: UPLOAD FILE EXCEL / CSV
with tab2:
    st.subheader("Upload File Excel / CSV Untuk Menambah Data Aset Baru")
    st.info("Sistem akan otomatis **memeriksa Serial Number (SN)**. Data dengan SN yang sudah ada di database akan **dilewati (tidak akan duplikat)**.")
    
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV (.csv)", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            # Membaca file yang diunggah
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file, dtype=str)
            else:
                df_upload = pd.read_excel(uploaded_file, dtype=str)
            
            # Menyesuaikan kolom agar pas dengan format database
            for col in COLUMNS:
                if col not in df_upload.columns:
                    df_upload[col] = ""
            df_upload = df_upload[COLUMNS]
            
            # --- PROSES CEK DUPLIKASI BERDASARKAN SN ---
            if not df_asset.empty and "SN" in df_asset.columns:
                # Ambil daftar SN yang sudah tersimpan di database
                sn_lama = set(df_asset["SN"].dropna().str.strip().str.upper())
                
                # Filter hanya baris baru yang SN-nya BELUM ADA di database
                df_baru = df_upload[~df_upload["SN"].astype(str).str.strip().str.upper().isin(sn_lama)]
                jumlah_duplikat = len(df_upload) - len(df_baru)
            else:
                df_baru = df_upload
                jumlah_duplikat = 0

            st.write("Preview Data Baru Yang Akan Diimpor:")
            st.dataframe(df_baru, use_container_width=True)
            
            if jumlah_duplikat > 0:
                st.warning(f"⚠️ Ditemukan **{jumlah_duplikat} data duplikat** (SN sudah terdaftar). Data duplikat ini akan otomatis dilewati.")

            if st.button("Simpan Data Baru ke Database"):
                if not df_baru.empty:
                    # Gabungkan hanya data yang benar-benar baru
                    df_combined = pd.concat([df_asset, df_baru], ignore_index=True)
                    save_data(df_combined)
                    st.success(f"✅ Berhasil menambahkan **{len(df_baru)} data aset baru**!")
                    st.rerun()
                else:
                    st.info("Semua data dalam file yang Anda unggah sudah ada di database.")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")

# TAB 3: TAMBAH MANUAL
with tab3:
    st.subheader("Form Tambah Aset Manual")
    with st.form("form_tambah_aset", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            ket_wilayah = st.text_input("Ket Wilayah")
            sn = st.text_input("SN (Serial Number)")
            tipe = st.text_input("Tipe")
            model = st.text_input("Model")
            status_beli = st.text_input("Status Beli")
            
        with col_b:
            asal_po = st.text_input("Asal PO")
            status = st.selectbox("Status", STATUS_OPTIONS)
            nik = st.text_input("NIK")
            user = st.text_input("User")
            kd_site = st.text_input("Kd Site")
            
        with col_c:
            site = st.text_input("Site")
            no_mobil = st.text_input("No Mobil")
            sim_card = st.text_input("SIM Card")
            imei = st.text_input("Imei")
            keterangan = st.text_area("Keterangan")
            
        submitted = st.form_submit_button("Simpan Aset")
        
        if submitted:
            new_data = {
                "Ket Wilayah": ket_wilayah,
                "SN": sn,
                "Tipe": tipe,
                "Model": model,
                "Status Beli": status_beli,
                "Asal PO": asal_po,
                "Status": status,
                "NIK": nik,
                "User": user,
                "Kd Site": kd_site,
                "Site": site,
                "No Mobil": no_mobil,
                "SIM Card": sim_card,
                "Imei": imei,
                "Keterangan": keterangan
            }
            df_new = pd.DataFrame([new_data])
            df_updated = pd.concat([df_asset, df_new], ignore_index=True)
            save_data(df_updated)
            st.success("Aset berhasil ditambahkan secara manual!")
            st.rerun()
