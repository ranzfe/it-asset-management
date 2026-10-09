import streamlit as st
import pandas as pd
import io
from database import (
    load_data, load_logs, save_data, add_log, 
    COLUMNS, STATUS_OPTIONS
)
from ai_assistant import render_ai_assistant

# Konfigurasi Halaman Web
st.set_page_config(page_title="IT Asset Management", page_icon="💻", layout="wide")

# Muat Data & AI Assistant Sidebar
df_asset = load_data()
render_ai_assistant()

# --- HEADER & DASHBOARD METRICS ---
st.title("💻 IT Asset Management System")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
total_asset = len(df_asset)
pakai_count = len(df_asset[df_asset["Status"].str.upper() == "PAKAI"]) if not df_asset.empty else 0
rusak_count = len(df_asset[df_asset["Status"].str.upper() == "RUSAK"]) if not df_asset.empty else 0
hilang_count = len(df_asset[df_asset["Status"].str.upper() == "HILANG"]) if not df_asset.empty else 0
jual_count = len(df_asset[df_asset["Status"].str.upper() == "JUAL"]) if not df_asset.empty else 0

col1.metric("Total Aset", total_asset)
col2.metric("Pakai", pakai_count)
col3.metric("Rusak", rusak_count)
col4.metric("Hilang", hilang_count)
col5.metric("Jual", jual_count)
st.markdown("---")

# --- TAB MENU UTAMA ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Daftar, Sort & Filter Aset", 
    "📊 Analytics & Grafik",
    "✏️ Edit & Hapus Aset",
    "📤 Upload Excel/CSV", 
    "➕ Tambah Manual",
    "📜 Log History"
])

# TAB 1: LIHAT, SORT, & FILTER DATA
with tab1:
    st.subheader("Daftar Aset Terdaftar")
    
    # Deteksi Duplikat
    if not df_asset.empty and "SN" in df_asset.columns:
        sn_series = df_asset["SN"].astype(str).str.strip().str.upper()
        duplikat_mask = sn_series.duplicated(keep='first') & (sn_series != "")
        total_duplikat = duplikat_mask.sum()
        
        if total_duplikat > 0:
            st.error(f"⚠️ Ditemukan **{total_duplikat} data duplikat SN** pada database!")
            if st.button("🧹 Hapus Data Duplikat (Simpan 1 Aset Teratas)"):
                df_clean = df_asset[~duplikat_mask].copy()
                save_data(df_clean)
                add_log("CLEAN DUPLICATES", "BULK", "SYSTEM", f"Menghapus {total_duplikat} baris duplikat.")
                st.success(f"Berhasil membersihkan {total_duplikat} data duplikat!")
                st.rerun()

    # --- PANEL FILTER & SORTING (FILTER SITE) ---
    with st.expander("🎛️ Panel Filter & Sorting Data", expanded=True):
        col_f1, col_f2, col_f3, col_s1, col_s2 = st.columns([2, 1.5, 1.5, 1.5, 1])
        
        with col_f1:
            search_term = st.text_input("🔍 Cari (SN, User, Site, Tipe, NIK, dll):", "")
        with col_f2:
            status_list = ["Semua Status"] + sorted([s for s in df_asset["Status"].unique() if str(s).strip() != ""])
            filter_status = st.selectbox("Filter Status:", status_list)
        with col_f3:
            site_list = ["Semua Site"] + sorted([s for s in df_asset["Site"].unique() if str(s).strip() != ""])
            filter_site = st.selectbox("Filter Site:", site_list)
            
        with col_s1:
            sort_column = st.selectbox("Urutkan Berdasarkan (Sort By):", ["SN", "User", "Site", "Tipe", "Status", "Ket Wilayah", "Model"])
        with col_s2:
            sort_order = st.radio("Urutan:", ["A-Z (Asc)", "Z-A (Desc)"])

    # --- MEMPROSES FILTER & SORT ---
    df_filtered = df_asset.copy()
    
    # Filter Teks
    if search_term:
        mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]
        
    # Filter Dropdown Status
    if filter_status != "Semua Status":
        df_filtered = df_filtered[df_filtered["Status"] == filter_status]
        
    # Filter Dropdown Site
    if filter_site != "Semua Site":
        df_filtered = df_filtered[df_filtered["Site"] == filter_site]

    # Sorting Data
    is_ascending = True if sort_order == "A-Z (Asc)" else False
    if sort_column in df_filtered.columns:
        df_filtered = df_filtered.sort_values(by=sort_column, ascending=is_ascending)

    # Tampilkan Jumlah Data Terfilter
    st.caption(f"Menampilkan **{len(df_filtered)}** dari total **{len(df_asset)}** aset.")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    
    # --- TOMBOL EXPORT (CSV & EXCEL) ---
    if not df_filtered.empty:
        col_ex1, col_ex2 = st.columns([1, 1])
        with col_ex1:
            csv_data = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Hasil Filter ke CSV", csv_data, "export_it_asset.csv", "text/csv")
        with col_ex2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='IT_Assets')
            excel_data = output.getvalue()
            st.download_button("📊 Export Hasil Filter ke Excel (.xlsx)", excel_data, "export_it_asset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# TAB 2: ANALYTICS & GRAFIK
with tab2:
    st.subheader("📊 Analisis & Distribusi Aset IT")
    if not df_asset.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### Jumlah Aset Berdasarkan Status")
            status_counts = df_asset["Status"].value_counts()
            st.bar_chart(status_counts)
        with col_g2:
            st.markdown("##### Jumlah Aset Berdasarkan Tipe Perangkat")
            tipe_counts = df_asset["Tipe"].value_counts().head(10)
            st.bar_chart(tipe_counts)
            
        st.markdown("---")
        st.markdown("##### Top 10 Site/Lokasi dengan Aset Terbanyak")
        site_counts = df_asset["Site"].value_counts
