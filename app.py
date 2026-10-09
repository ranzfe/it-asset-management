import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="IT Asset Management",
    page_icon="💻",
    layout="wide"
)

# Nama File Database & Log Lokal
DB_FILE = "database_asset.csv"
LOG_FILE = "history_log.csv"

# Daftar Kolom Sesuai Permintaan
COLUMNS = [
    "Ket Wilayah", "SN", "Tipe", "Model", "Status Beli", "Asal PO",
    "Status", "NIK", "User", "Kd Site", "Site", "No Mobil",
    "SIM Card", "Imei", "Keterangan"
]

LOG_COLUMNS = ["Waktu_Log", "Aksi", "SN", "User_Terkait", "Rincian_Perubahan"]

STATUS_OPTIONS = ["Pakai", "Rusak", "Hilang", "Jual"]

# Fungsi Memuat Data Aset
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS].fillna("")
    else:
        return pd.DataFrame(columns=COLUMNS)

# Fungsi Memuat Data Log History
def load_logs():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE, dtype=str)
        for col in LOG_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[LOG_COLUMNS].fillna("")
    else:
        return pd.DataFrame(columns=LOG_COLUMNS)

# Fungsi Menyimpan Data Aset
def save_data(df):
    df[COLUMNS].to_csv(DB_FILE, index=False)

# Fungsi Mencatat Log / Riwayat Perubahan
def add_log(aksi, sn, user_terkait, rincian):
    df_logs = load_logs()
    waktu_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = {
        "Waktu_Log": waktu_now,
        "Aksi": aksi,
        "SN": sn,
        "User_Terkait": user_terkait,
        "Rincian_Perubahan": rincian
    }
    df_updated_log = pd.concat([pd.DataFrame([new_log]), df_logs], ignore_index=True)
    df_updated_log.to_csv(LOG_FILE, index=False)

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
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Daftar & Filter Aset", 
    "📤 Upload Excel/CSV", 
    "➕ Tambah Manual",
    "📜 Log History"
])

# TAB 1: LIHAT & FILTER DATA
with tab1:
    st.subheader("Daftar Aset Terdaftar")
    
    search_term = st.text_input("🔍 Cari (berdasarkan SN, User, Site, Tipe, dll):", "")
    
    df_filtered = df_asset.copy()
    if search_term:
        mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]
    
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    
    if not df_filtered.empty:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Data Ke CSV",
            data=csv,
            file_name="export_it_asset.csv",
            mime="text/csv"
        )

# TAB 2: UPLOAD FILE EXCEL / CSV (DENGAN CATATAN HISTORY)
with tab2:
    st.subheader("Upload File Excel / CSV Untuk Menambah atau Memperbarui Data Aset")
    st.info("💡 **Fitur Cerdas & Log:** Data dengan **SN baru** akan ditambahkan. Data dengan **SN lama** akan diperbarui (*update*) dan perubahan perilakunya akan dicatat otomatis di **Log History**.")
    
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV (.csv)", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file, dtype=str)
            else:
                df_upload = pd.read_excel(uploaded_file, dtype=str)
            
            for col in COLUMNS:
                if col not in df_upload.columns:
                    df_upload[col] = ""
            df_upload = df_upload[COLUMNS].fillna("")
            
            st.write("Preview Data Yang Diunggah:")
            st.dataframe(df_upload.head(), use_container_width=True)
            
            if st.button("Proses Simpan & Update Data"):
                df_current = df_asset.copy().fillna("")
                
                if not df_current.empty and "SN" in df_current.columns:
                    df_current["SN_clean"] = df_current["SN"].astype(str).str.strip().str.upper()
                    df_upload["SN_clean"] = df_upload["SN"].astype(str).str.strip().str.upper()
                    
                    count_update = 0
                    count_baru = 0
                    
                    for idx, row in df_upload.iterrows():
                        sn_val = row["SN_clean"]
                        if sn_val != "":
                            match = df_current[df_current["SN_clean"] == sn_val]
                            if not match.empty:
                                # Update data lama & catat log perubahan
                                match_idx = match.index[0]
                                perubahans = []
                                for col in COLUMNS:
                                    val_lama = str(df_current.at[match_idx, col]).strip()
                                    val_baru = str(row[col]).strip()
                                    if val_baru != "" and val_baru != val_lama:
                                        df_current.at[match_idx, col] = val_baru
                                        perubahans.append(f"{col}: '{val_lama}' ➔ '{val_baru}'")
                                
                                if perubahans:
                                    count_update += 1
                                    add_log(
                                        aksi="UPDATE (via Upload)",
                                        sn=row["SN"],
                                        user_terkait=row["User"],
                                        rincian="; ".join(perubahans)
                                    )
                            else:
                                # Data baru
                                new_row = row[COLUMNS].to_dict()
                                df_current = pd.concat([df_current, pd.DataFrame([new_row])], ignore_index=True)
                                count_baru += 1
                                add_log(
                                    aksi="TAMBAH BARU (via Upload)",
                                    sn=row["SN"],
                                    user_terkait=row["User"],
                                    rincian=f"Aset baru ditambahkan (Model: {row['Model']}, Site: {row['Site']})"
                                )
                    
                    if "SN_clean" in df_current.columns:
                        df_current = df_current.drop(columns=["SN_clean"])
                        
                    save_data(df_current[COLUMNS])
                    st.success(f"✅ Selesai! **{count_baru} data baru** ditambahkan, dan **{count_update} data lama** diperbarui!")
                    st.rerun()
                else:
                    save_data(df_upload[COLUMNS])
                    for idx, row in df_upload.iterrows():
                        add_log("TAMBAH BARU (Upload Perdana)", row["SN"], row["User"], "Inisialisasi data aset pertamanya.")
                    st.success(f"✅ Berhasil menyimpan {len(df_upload)} data aset pertama!")
                    st.rerun()
                
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
                "Ket Wilayah": ket_wilayah, "SN": sn, "Tipe": tipe, "Model": model,
                "Status Beli": status_beli, "Asal PO": asal_po, "Status": status,
                "NIK": nik, "User": user, "Kd Site": kd_site, "Site": site,
                "No Mobil": no_mobil, "SIM Card": sim_card, "Imei": imei, "Keterangan": keterangan
            }
            df_new = pd.DataFrame([new_data])
            df_updated = pd.concat([df_asset, df_new], ignore_index=True)
            save_data(df_updated)
            
            # Catat ke Log History
            add_log("TAMBAH BARU (Manual)", sn, user, f"Tambah manual Aset Tipe {tipe} Model {model} di Site {site}")
            
            st.success("Aset berhasil ditambahkan secara manual!")
            st.rerun()

# TAB 4: LOG HISTORY / RIWAYAT PERUBAHAN
with tab4:
    st.subheader("📜 Riwayat & Log Perubahan Data Aset")
    df_logs = load_logs()
    
    if not df_logs.empty:
        search_log = st.text_input("🔍 Cari di Log History (SN, Tanggal, User, Aksi):", "")
        if search_log:
            mask_log = df_logs.apply(lambda row: row.astype(str).str.contains(search_log, case=False).any(), axis=1)
            df_logs = df_logs[mask_log]
            
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada riwayat aktivitas perubahan data.")
