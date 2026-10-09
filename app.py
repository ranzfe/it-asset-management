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

    # --- PANEL FILTER & SORTING (TERMASUK FILTER TIPE) ---
    with st.expander("🎛️ Panel Filter & Sorting Data", expanded=True):
        col_f1, col_f2, col_f3, col_f4, col_s1, col_s2 = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1])
        
        with col_f1:
            search_term = st.text_input("🔍 Cari (SN, User, Site, Tipe, NIK, dll):", "")
        with col_f2:
            status_list = ["Semua Status"] + sorted([s for s in df_asset["Status"].unique() if str(s).strip() != ""])
            filter_status = st.selectbox("Filter Status:", status_list)
        with col_f3:
            tipe_list = ["Semua Tipe"] + sorted([t for t in df_asset["Tipe"].unique() if str(t).strip() != ""])
            filter_tipe = st.selectbox("Filter Tipe:", tipe_list)
        with col_f4:
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

    # Filter Dropdown Tipe
    if filter_tipe != "Semua Tipe":
        df_filtered = df_filtered[df_filtered["Tipe"] == filter_tipe]
        
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
        site_counts = df_asset["Site"].value_counts().head(10)
        st.bar_chart(site_counts)
    else:
        st.info("Belum ada data untuk grafik analisis.")

# TAB 3: EDIT & HAPUS ASET
with tab3:
    st.subheader("✏️ Kelola (Edit & Hapus) Data Aset")
    if df_asset.empty:
        st.info("Belum ada data aset.")
    else:
        list_sn = sorted([sn for sn in df_asset["SN"].unique() if str(sn).strip() != ""])
        selected_sn = st.selectbox("Pilih Serial Number (SN) Aset:", ["-- Pilih SN --"] + list_sn)
        
        if selected_sn != "-- Pilih SN --":
            asset_row = df_asset[df_asset["SN"] == selected_sn].iloc[0]
            st.markdown("---")
            col_edit, col_del = st.columns([3, 1])
            
            with col_edit:
                st.markdown(f"#### 📝 Form Edit Aset (SN: `{selected_sn}`)")
                with st.form("form_edit_asset"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        ket_wilayah_edit = st.text_input("Ket Wilayah", value=str(asset_row["Ket Wilayah"]))
                        sn_edit = st.text_input("SN", value=str(asset_row["SN"]), disabled=True)
                        tipe_edit = st.text_input("Tipe", value=str(asset_row["Tipe"]))
                        model_edit = st.text_input("Model", value=str(asset_row["Model"]))
                        status_beli_edit = st.text_input("Status Beli", value=str(asset_row["Status Beli"]))
                    with col_b:
                        asal_po_edit = st.text_input("Asal PO", value=str(asset_row["Asal PO"]))
                        curr_status = str(asset_row["Status"])
                        status_idx = STATUS_OPTIONS.index(curr_status) if curr_status in STATUS_OPTIONS else 0
                        status_edit = st.selectbox("Status", STATUS_OPTIONS, index=status_idx)
                        nik_edit = st.text_input("NIK", value=str(asset_row["NIK"]))
                        user_edit = st.text_input("User", value=str(asset_row["User"]))
                        kd_site_edit = st.text_input("Kd Site", value=str(asset_row["Kd Site"]))
                    with col_c:
                        site_edit = st.text_input("Site", value=str(asset_row["Site"]))
                        no_mobil_edit = st.text_input("No Mobil", value=str(asset_row["No Mobil"]))
                        sim_card_edit = st.text_input("SIM Card", value=str(asset_row["SIM Card"]))
                        imei_edit = st.text_input("Imei", value=str(asset_row["Imei"]))
                        keterangan_edit = st.text_area("Keterangan", value=str(asset_row["Keterangan"]))
                    
                    if st.form_submit_button("💾 Simpan Perubahan"):
                        idx_target = df_asset[df_asset["SN"] == selected_sn].index[0]
                        updated_vals = {
                            "Ket Wilayah": ket_wilayah_edit, "SN": selected_sn, "Tipe": tipe_edit,
                            "Model": model_edit, "Status Beli": status_beli_edit, "Asal PO": asal_po_edit,
                            "Status": status_edit, "NIK": nik_edit, "User": user_edit,
                            "Kd Site": kd_site_edit, "Site": site_edit, "No Mobil": no_mobil_edit,
                            "SIM Card": sim_card_edit, "Imei": imei_edit, "Keterangan": keterangan_edit
                        }
                        perubahans = []
                        for col in COLUMNS:
                            val_lama = str(df_asset.at[idx_target, col]).strip()
                            val_baru = str(updated_vals[col]).strip()
                            if val_lama != val_baru:
                                df_asset.at[idx_target, col] = val_baru
                                perubahans.append(f"{col}: '{val_lama}' ➔ '{val_baru}'")
                        save_data(df_asset)
                        if perubahans:
                            add_log("EDIT MANUAL", selected_sn, user_edit, "; ".join(perubahans))
                            st.success("✅ **Proses Edit Selesai!** Data diperbarui.")
                        st.rerun()

            with col_del:
                st.markdown("#### 🗑️ Hapus Aset")
                if st.button("❌ Hapus Aset Ini", type="primary"):
                    df_new = df_asset[df_asset["SN"] != selected_sn]
                    save_data(df_new)
                    add_log("HAPUS ASET", selected_sn, asset_row["User"], f"Aset dihapus.")
                    st.success(f"✅ **Selesai!** SN {selected_sn} berhasil dihapus.")
                    st.rerun()

# TAB 4: UPLOAD FILE
with tab4:
    st.subheader("Upload File Excel / CSV")
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV (.csv)", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file, dtype=str) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, dtype=str)
            for col in COLUMNS:
                if col not in df_upload.columns:
                    df_upload[col] = ""
            df_upload = df_upload[COLUMNS].fillna("")
            df_upload["SN_clean"] = df_upload["SN"].astype(str).str.strip().str.upper()
            df_upload = df_upload.drop_duplicates(subset=["SN_clean"], keep='last')
            
            st.dataframe(df_upload[COLUMNS].head(), use_container_width=True)
            if st.button("Proses Simpan & Update Data"):
                df_current = df_asset.copy().fillna("")
                if not df_current.empty and "SN" in df_current.columns:
                    df_current["SN_clean"] = df_current["SN"].astype(str).str.strip().str.upper()
                    count_update = count_baru = 0
                    for idx, row in df_upload.iterrows():
                        sn_val = row["SN_clean"]
                        if sn_val != "":
                            match = df_current[df_current["SN_clean"] == sn_val]
                            if not match.empty:
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
                                    add_log("UPDATE (via Upload)", row["SN"], row["User"], "; ".join(perubahans))
                            else:
                                df_current = pd.concat([df_current, pd.DataFrame([row[COLUMNS].to_dict()])], ignore_index=True)
                                count_baru += 1
                                add_log("TAMBAH BARU (via Upload)", row["SN"], row["User"], f"Aset baru ditambahkan.")
                    
                    df_current = df_current.drop(columns=["SN_clean"], errors='ignore')
                    save_data(df_current[COLUMNS])
                    st.success(f"🎉 **PROSES UPLOAD SELESAI!**\n- ✅ **{count_baru} Data Baru**\n- 🔄 **{count_update} Data Diperbarui**")
                    st.balloons()
                else:
                    df_upload = df_upload.drop(columns=["SN_clean"], errors='ignore')
                    save_data(df_upload[COLUMNS])
                    st.success(f"🎉 **UPLOAD PERDANA SELESAI!** Tersimpan {len(df_upload)} data.")
                    st.balloons()
        except Exception as e:
            st.error(f"Error reading file: {e}")

# TAB 5: TAMBAH MANUAL
with tab5:
    st.subheader("Form Tambah Aset Manual")
    with st.form("form_tambah_aset", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            ket_wilayah = st.text_input("Ket Wilayah")
            sn = st.text_input("SN")
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
            
        if st.form_submit_button("Simpan Aset"):
            new_data = {
                "Ket Wilayah": ket_wilayah, "SN": sn, "Tipe": tipe, "Model": model,
                "Status Beli": status_beli, "Status": status, "NIK": nik, "User": user,
                "Kd Site": kd_site, "Site": site, "No Mobil": no_mobil, "SIM Card": sim_card,
                "Imei": imei, "Keterangan": keterangan
            }
            save_data(pd.concat([df_asset, pd.DataFrame([new_data])], ignore_index=True))
            add_log("TAMBAH BARU (Manual)", sn, user, f"Tambah manual Aset {tipe} {model}")
            st.success(f"✅ **SELESAI!** Aset SN `{sn}` tersimpan.")

# TAB 6: LOG HISTORY
with tab6:
    st.subheader("📜 Riwayat & Log Perubahan Data Aset")
    df_logs = load_logs()
    if not df_logs.empty:
        search_log = st.text_input("🔍 Cari di Log History:", "")
        if search_log:
            mask_log = df_logs.apply(lambda row: row.astype(str).str.contains(search_log, case=False).any(), axis=1)
            df_logs = df_logs[mask_log]
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada riwayat aktivitas.")
