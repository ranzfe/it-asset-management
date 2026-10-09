import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
from database import (
    load_data, load_logs, save_data, add_log, 
    COLUMNS, STATUS_OPTIONS
)
from ai_assistant import render_ai_assistant

# Konfigurasi Halaman Web
st.set_page_config(page_title="IT Asset Management", page_icon="💻", layout="wide")

# Muat Data Utama
df_asset = load_data()

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📋 Daftar, Sort & Filter Aset", 
    "📊 Analytics & Grafik",
    "✏️ Edit & Hapus Aset",
    "📤 Upload Excel/CSV", 
    "➕ Tambah Manual",
    "📜 Log History",
    "📱 Plotting Tagihan Simcard"
])

# TAB 1: LIHAT, SORT, & FILTER DATA
with tab1:
    st.subheader("Daftar Aset Terdaftar")
    
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
            sort_column = st.selectbox("Urutkan Berdasarkan (Sort By):", ["SN", "User", "Site", "Tipe", "Purchase Date", "Status", "Model"])
        with col_s2:
            sort_order = st.radio("Urutan:", ["A-Z (Asc)", "Z-A (Desc)"])

    df_filtered = df_asset.copy()
    
    if search_term:
        mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]
        
    if filter_status != "Semua Status":
        df_filtered = df_filtered[df_filtered["Status"] == filter_status]

    if filter_tipe != "Semua Tipe":
        df_filtered = df_filtered[df_filtered["Tipe"] == filter_tipe]
        
    if filter_site != "Semua Site":
        df_filtered = df_filtered[df_filtered["Site"] == filter_site]

    is_ascending = True if sort_order == "A-Z (Asc)" else False
    if sort_column in df_filtered.columns:
        df_filtered = df_filtered.sort_values(by=sort_column, ascending=is_ascending)

    st.caption(f"Menampilkan **{len(df_filtered)}** dari total **{len(df_asset)}** aset.")
    
    st.dataframe(
        df_filtered, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Link Foto Asset": st.column_config.LinkColumn(
                "Link Foto Asset (Google Drive)",
                display_text="🔗 Buka Link Foto",
                help="Klik untuk membuka langsung di Google Drive"
            ),
            "Purchase Date": st.column_config.DateColumn(
                "Purchase Date",
                format="YYYY-MM-DD"
            )
        }
    )

    if not df_filtered.empty:
        col_ex1, col_ex2, col_ex_empty = st.columns([0.2, 0.25, 1])
        with col_ex1:
            csv_data = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", csv_data, "export_it_asset.csv", "text/csv")
        with col_ex2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='IT_Assets')
            excel_data = output.getvalue()
            st.download_button("📊 Export Excel (.xlsx)", excel_data, "export_it_asset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# TAB 2: ANALYTICS & GRAFIK
with tab2:
    st.subheader("📊 Analisis & Distribusi Aset IT")
    if not df_asset.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### Jumlah Aset Berdasarkan Status")
            st.bar_chart(df_asset["Status"].value_counts())
        with col_g2:
            st.markdown("##### Jumlah Aset Berdasarkan Tipe Perangkat")
            st.bar_chart(df_asset["Tipe"].value_counts().head(10))
            
        st.markdown("---")
        st.markdown("##### Top 10 Site/Lokasi dengan Aset Terbanyak")
        st.bar_chart(df_asset["Site"].value_counts().head(10))
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
                        sn_edit = st.text_input("SN", value=str(asset_row["SN"]), disabled=True)
                        tipe_edit = st.text_input("Tipe", value=str(asset_row["Tipe"]))
                        model_edit = st.text_input("Model", value=str(asset_row["Model"]))
                        p_date_val = str(asset_row["Purchase Date"]).strip()
                        purchase_date_edit = st.text_input("Purchase Date (YYYY-MM-DD)", value=p_date_val)
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
                        foto_edit = st.text_input("Link Foto Asset (Google Drive)", value=str(asset_row["Link Foto Asset"]))
                        keterangan_edit = st.text_area("Keterangan", value=str(asset_row["Keterangan"]))
                    
                    if st.form_submit_button("💾 Simpan Perubahan"):
                        idx_target = df_asset[df_asset["SN"] == selected_sn].index[0]
                        updated_vals = {
                            "SN": selected_sn, "Tipe": tipe_edit, "Model": model_edit,
                            "Purchase Date": purchase_date_edit, "Status Beli": status_beli_edit, 
                            "Asal PO": asal_po_edit, "Status": status_edit, "NIK": nik_edit, 
                            "User": user_edit, "Kd Site": kd_site_edit, "Site": site_edit, 
                            "No Mobil": no_mobil_edit, "SIM Card": sim_card_edit, 
                            "Imei": imei_edit, "Link Foto Asset": foto_edit, 
                            "Keterangan": keterangan_edit
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
                    add_log("HAPUS ASET", selected_sn, asset_row["User"], "Aset dihapus.")
                    st.success(f"✅ **Selesai!** SN {selected_sn} berhasil dihapus.")
                    st.rerun()

# TAB 4: UPLOAD FILE
with tab4:
    st.subheader("Upload File Excel / CSV")
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV (.csv)", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file, dtype=str) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, dtype=str)
            
            if "Ket Wilayah" in df_upload.columns:
                df_upload = df_upload.drop(columns=["Ket Wilayah"])
                
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
                                add_log("TAMBAH BARU (via Upload)", row["SN"], row["User"], "Aset baru ditambahkan.")
                    
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
            sn = st.text_input("SN")
            tipe = st.text_input("Tipe")
            model = st.text_input("Model")
            purchase_date = st.date_input("Purchase Date (Tanggal Beli)", value=None)
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
            foto = st.text_input("Link Foto Asset (Google Drive)")
            keterangan = st.text_area("Keterangan")
            
        if st.form_submit_button("Simpan Aset"):
            p_date_str = purchase_date.strftime("%Y-%m-%d") if purchase_date else ""
            new_data = {
                "SN": sn, "Tipe": tipe, "Model": model,
                "Purchase Date": p_date_str, "Status Beli": status_beli, 
                "Asal PO": asal_po, "Status": status, "NIK": nik, "User": user, 
                "Kd Site": kd_site, "Site": site, "No Mobil": no_mobil, 
                "SIM Card": sim_card, "Imei": imei, "Link Foto Asset": foto, 
                "Keterangan": keterangan
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

# TAB 7: PLOTTING TAGIHAN SIMCARD (DENGAN SORTING & FILTER RAPI)
with tab7:
    st.subheader("📱 Auto-Plotting Tagihan SIM Card")
    st.caption("Alur Kerja: Tagihan Telkom ➔ Cek Historis (Dapatkan Kode DA/No Mobil) ➔ Validasi Keaktifan & Deep Search SN Device dari Update Bulan Ini.")
    
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        file_telkom = st.file_uploader("1. File Tagihan Telkom (.xlsx/.csv)", type=["xlsx", "csv"], key="u3_telkom")
    with col_u2:
        file_historis = st.file_uploader("2. File Data Historis Sebelum Bulan Ini (.xlsx/.csv)", type=["xlsx", "csv"], key="u3_historis")
    with col_u3:
        file_active_users = st.file_uploader("3. File Data Update User Terbaru Bulan Ini (.xlsx/.csv)", type=["xlsx", "csv"], key="u3_users")
        
    if file_telkom is not None:
        try:
            df_tel = pd.read_csv(file_telkom, dtype=str) if file_telkom.name.endswith('.csv') else pd.read_excel(file_telkom, dtype=str)
            df_tel = df_tel.fillna("").astype(str)
            
            df_hist = pd.DataFrame()
            if file_historis is not None:
                df_hist = pd.read_csv(file_historis, dtype=str) if file_historis.name.endswith('.csv') else pd.read_excel(file_historis, dtype=str)
                df_hist = df_hist.fillna("").astype(str)

            df_users = pd.DataFrame()
            if file_active_users is not None:
                df_users = pd.read_csv(file_active_users, dtype=str) if file_active_users.name.endswith('.csv') else pd.read_excel(file_active_users, dtype=str)
                df_users = df_users.fillna("").astype(str)

            st.markdown("---")
            st.markdown("##### 🎛️ Konfirmasi Pemetaan Kolom File Upload:")
            
            # PEMETAAN KOLOM TELKOM
            tel_cols = ["-- Pilih Kolom --"] + list(df_tel.columns)
            col_t1, col_t2 = st.columns(2)
            
            def_msisdn = 0
            for i, c in enumerate(tel_cols):
                if "MSISDN" in c.upper():
                    def_msisdn = i
                    break
            
            def_tagihan = 0
            for i, c in enumerate(tel_cols):
                if "TAGIHAN" in c.upper() or "BILL" in c.upper():
                    def_tagihan = i
                    break

            with col_t1:
                col_tel_msisdn = st.selectbox("📌 Kolom Nomor SIM / MSISDN (File Telkom):", tel_cols, index=def_msisdn)
            with col_t2:
                col_tel_tagihan = st.selectbox("📌 Kolom Jumlah Tagihan (File Telkom):", tel_cols, index=def_tagihan)

            # PEMETAAN KOLOM USER AKTIF BULAN INI
            if not df_users.empty:
                st.markdown("---")
                st.markdown("##### 👤 Pemetaan Kolom File Data Update User Terbaru Bulan Ini:")
                usr_cols = ["-- Pilih / Tidak Ada --"] + list(df_users.columns)
                
                def get_idx_exact(col_name_part):
                    for idx, col in enumerate(usr_cols):
                        if col.strip().upper() == col_name_part.upper():
                            return idx
                    for idx, col in enumerate(usr_cols):
                        if col_name_part.upper() in col.upper():
                            return idx
                    return 0

                cu1, cu2, cu3, cu4, cu5, cu6 = st.columns(6)
                with cu1:
                    col_u_sn = st.selectbox("Kolom SN:", usr_cols, index=get_idx_exact("SN"))
                with cu2:
                    col_u_site = st.selectbox("Kolom Ket Site:", usr_cols, index=get_idx_exact("Ket Site"))
                with cu3:
                    col_u_da = st.selectbox("Kolom DA:", usr_cols, index=get_idx_exact("DA"))
                with cu4:
                    col_u_namada = st.selectbox("Kolom Nama DA:", usr_cols, index=get_idx_exact("Nama DA"))
                with cu5:
                    col_u_mobil = st.selectbox("Kolom No Mobil:", usr_cols, index=get_idx_exact("No Mobil"))
                with cu6:
                    col_u_asp = st.selectbox("Kolom Nama ASP:", usr_cols, index=get_idx_exact("Nama ASP"))

            def normalize_phone(val):
                cleaned = re.sub(r'\D', '', str(val))
                if cleaned.startswith("62"):
                    cleaned = "0" + cleaned[2:]
                return cleaned

            if st.button("🚀 Jalankan Auto-Plotting Data", type="primary"):
                if col_tel_msisdn == "-- Pilih Kolom --":
                    st.error("Pilih kolom Nomor SIM / MSISDN terlebih dahulu!")
                else:
                    # Normalisasi SIM pada File Historis
                    if not df_hist.empty:
                        sim_col_hist = [c for c in df_hist.columns if any(k in c.upper() for k in ["SIM", "MSISDN", "NOMOR"])]
                        if sim_col_hist:
                            df_hist["SIM_clean"] = df_hist[sim_col_hist[0]].apply(normalize_phone)
                        else:
                            df_hist["SIM_clean"] = ""

                    # Normalisasi SIM pada File Update User (Jika ada)
                    if not df_users.empty:
                        sim_col_usr = [c for c in df_users.columns if any(k in c.upper() for k in ["SIM", "MSISDN", "NOMOR"])]
                        if sim_col_usr:
                            df_users["SIM_clean"] = df_users[sim_col_usr[0]].apply(normalize_phone)
                        else:
                            df_users["SIM_clean"] = ""

                    results = []
                    for idx, row in df_tel.iterrows():
                        raw_msisdn = str(row[col_tel_msisdn]).strip()
                        sim_clean = normalize_phone(raw_msisdn)
                        tagihan_val = str(row[col_tel_tagihan]).strip() if col_tel_tagihan != "-- Pilih Kolom --" else "0"

                        depo_val = user_val = mobil_val = sn_val = "-"
                        ket_status = "TIDAK AKTIF"

                        # ALUR 1: CEK DAHULU KE DATA HISTORIS DARI NOMOR SIM
                        hist_match = pd.DataFrame()
                        if not df_hist.empty and sim_clean != "" and "SIM_clean" in df_hist.columns:
                            hist_match = df_hist[df_hist["SIM_clean"] == sim_clean]

                        if not hist_match.empty:
                            h_target = hist_match.iloc[0]
                            depo_val = str(h_target.get("DEPO", "-")).strip()
                            user_val = str(h_target.get("NAMA USER", "-")).strip()
                            mobil_val = str(h_target.get("KODE DA/NO MOBIL", "-")).strip()
                            sn_val = str(h_target.get("SN DEVICE", "-")).strip()

                        # ALUR 2: CEK KE DATA UPDATE TERBARU BULAN INI
                        if not df_users.empty:
                            user_match = pd.DataFrame()
                            
                            # A. Cari berdasarkan Kode DA / No Mobil yang ditarik dari Historis
                            if mobil_val not in ["-", ""]:
                                target_da = mobil_val.strip().upper()
                                if col_u_da != "-- Pilih / Tidak Ada --":
                                    user_match = df_users[df_users[col_u_da].astype(str).str.strip().str.upper() == target_da]
                                if user_match.empty and col_u_mobil != "-- Pilih / Tidak Ada --":
                                    user_match = df_users[df_users[col_u_mobil].astype(str).str.strip().str.upper() == target_da]
                                if user_match.empty:
                                    for c in df_users.columns:
                                        m = df_users[df_users[c].astype(str).str.strip().str.upper() == target_da]
                                        if not m.empty:
                                            user_match = m
                                            break

                            # B. Cari berdasarkan Nomor SIM langsung jika belum ketemu
                            if user_match.empty and sim_clean != "" and "SIM_clean" in df_users.columns:
                                user_match = df_users[df_users["SIM_clean"] == sim_clean]

                            # JIKA DITEMUKAN DI FILE UPDATE TERBARU BULAN INI (STATUS = AKTIF)
                            if not user_match.empty:
                                u_row = user_match.iloc[0]
                                ket_status = "AKTIF"
                                
                                # Update DEPO -> Ket Site
                                if col_u_site != "-- Pilih / Tidak Ada --":
                                    val_site = str(u_row.get(col_u_site, "")).strip()
                                    if val_site not in ["", "-", "nan", "None"]:
                                        depo_val = val_site
                                
                                # Update NAMA USER -> Nama DA / Nama ASP
                                nama_da_v = str(u_row.get(col_u_namada, "")).strip() if col_u_namada != "-- Pilih / Tidak Ada --" else ""
                                nama_asp_v = str(u_row.get(col_u_asp, "")).strip() if col_u_asp != "-- Pilih / Tidak Ada --" else ""
                                new_user = nama_da_v if nama_da_v != "" else (nama_asp_v if nama_asp_v != "" else "")
                                if new_user not in ["", "-", "nan", "None"]:
                                    user_val = new_user

                                # Update KODE DA / NO MOBIL
                                da_v = str(u_row.get(col_u_da, "")).strip() if col_u_da != "-- Pilih / Tidak Ada --" else ""
                                mobil_v = str(u_row.get(col_u_mobil, "")).strip() if col_u_mobil != "-- Pilih / Tidak Ada --" else ""
                                new_da = da_v if da_v != "" else (mobil_v if mobil_v != "" else "")
                                if new_da not in ["", "-", "nan", "None"]:
                                    mobil_val = new_da

                                # Tarik SN dari baris match
                                if col_u_sn != "-- Pilih / Tidak Ada --":
                                    c_sn = str(u_row.get(col_u_sn, "")).strip()
                                    if c_sn not in ["", "-", "nan", "None"]:
                                        sn_val = c_sn

                        # DEEP SEARCH SN DEVICE BERDASARKAN KODE DA PADA SELURUH FILE USER AKTIF
                        if (sn_val in ["-", "", "nan", "None"]) and not df_users.empty and mobil_val not in ["-", ""]:
                            target_da_clean = mobil_val.strip().upper()
                            
                            matches_da_all = pd.DataFrame()
                            if col_u_da != "-- Pilih / Tidak Ada --":
                                matches_da_all = df_users[df_users[col_u_da].astype(str).str.strip().str.upper() == target_da_clean]
                            if matches_da_all.empty and col_u_mobil != "-- Pilih / Tidak Ada --":
                                matches_da_all = df_users[df_users[col_u_mobil].astype(str).str.strip().str.upper() == target_da_clean]
                            if matches_da_all.empty:
                                for c in df_users.columns:
                                    m = df_users[df_users[c].astype(str).str.strip().str.upper() == target_da_clean]
                                    if not m.empty:
                                        matches_da_all = m
                                        break
                            
                            if not matches_da_all.empty:
                                sn_col_target = col_u_sn if col_u_sn != "-- Pilih / Tidak Ada --" else "SN"
                                if sn_col_target in matches_da_all.columns:
                                    for _, r_sn in matches_da_all.iterrows():
                                        found_sn = str(r_sn.get(sn_col_target, "")).strip()
                                        if found_sn not in ["", "-", "nan", "None"]:
                                            sn_val = found_sn
                                            break

                        # ALUR 3: FALLBACK DATABASE ITAM INTERNAL JIKA SN MASIH KOSONG
                        if sn_val in ["-", "", "nan", "None"]:
                            db_match = pd.DataFrame()
                            if mobil_val not in ["-", ""]:
                                db_match = df_asset[df_asset["No Mobil"].astype(str).str.strip().str.upper() == mobil_val.strip().upper()]
                            if db_match.empty and sim_clean != "":
                                db_match = df_asset[df_asset["SIM Card"].apply(normalize_phone) == sim_clean]

                            if not db_match.empty:
                                db_target = db_match.iloc[0]
                                if depo_val in ["-", ""]: depo_val = str(db_target.get("Site", "-"))
                                if user_val in ["-", ""]: user_val = str(db_target.get("User", "-"))
                                if mobil_val in ["-", ""]: mobil_val = str(db_target.get("No Mobil", "-"))
                                sn_val = str(db_target.get("SN", "-"))

                        results.append({
                            "DEPO": depo_val,
                            "NAMA USER": user_val,
                            "KODE DA/NO MOBIL": mobil_val,
                            "NOMOR SIM": raw_msisdn,
                            "TAGIHAN": tagihan_val,
                            "SN DEVICE": sn_val,
                            "KETERANGAN": ket_status
                        })

                    st.session_state["plotting_result"] = pd.DataFrame(results)
                    st.success("🎉 **Auto-Plotting Selesai!** Data berhasil ditarik.")

            # FITUR SORTING, FILTER, & RINGKASAN REKAPITULASI
            if "plotting_result" in st.session_state and not st.session_state["plotting_result"].empty:
                df_res = st.session_state["plotting_result"].copy()

                st.markdown("---")
                st.markdown("##### 🎛️ Panel Pengurutan (Sort) & Filter Hasil Plotting:")
                
                col_s1, col_s2, col_f1, col_f2 = st.columns([1.5, 1, 1.2, 1.2])
                with col_s1:
                    sort_col_plot = st.selectbox("Urutkan Berdasarkan:", ["DEPO", "NAMA USER", "KETERANGAN", "KODE DA/NO MOBIL", "TAGIHAN", "SN DEVICE"], index=0)
                with col_s2:
                    sort_order_plot = st.radio("Urutan Sort:", ["A-Z (Asc)", "Z-A (Desc)"], key="plot_sort_order")
                with col_f1:
                    depo_options = ["Semua Depo"] + sorted([d for d in df_res["DEPO"].unique() if d not in ["-", ""]])
                    filter_depo = st.selectbox("Filter Depo:", depo_options)
                with col_f2:
                    filter_ket = st.selectbox("Filter Keterangan:", ["Semua Status", "AKTIF", "TIDAK AKTIF"])

                # PROSES FILTER
                if filter_depo != "Semua Depo":
                    df_res = df_res[df_res["DEPO"] == filter_depo]
                if filter_ket != "Semua Status":
                    df_res = df_res[df_res["KETERANGAN"] == filter_ket]

                # PROSES SORTING
                asc_flag = True if sort_order_plot == "A-Z (Asc)" else False
                if sort_col_plot == "TAGIHAN":
                    # Convert ke numerik untuk sorting angka tagihan yang benar
                    df_res["_tagihan_num"] = pd.to_numeric(df_res["TAGIHAN"].str.replace(r'\D', '', regex=True), errors='coerce').fillna(0)
                    df_res = df_res.sort_values(by="_tagihan_num", ascending=asc_flag).drop(columns=["_tagihan_num"])
                else:
                    df_res = df_res.sort_values(by=sort_col_plot, ascending=asc_flag)

                # METRICS RINGKASAN
                st.markdown("---")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                tot_items = len(df_res)
                tot_aktif = len(df_res[df_res["KETERANGAN"] == "AKTIF"])
                tot_no_aktif = len(df_res[df_res["KETERANGAN"] == "TIDAK AKTIF"])
                
                # Hitung Total Rp Tagihan
                tagihan_sum = pd.to_numeric(df_res["TAGIHAN"].astype(str).str.replace(r'\D', '', regex=True), errors='coerce').fillna(0).sum()

                col_m1.metric("Total SIM Card", tot_items)
                col_m2.metric("Nomor AKTIF", tot_aktif)
                col_m3.metric("Nomor TIDAK AKTIF", tot_no_aktif)
                col_m4.metric("Total Tagihan (Rp)", f"Rp {tagihan_sum:,.0f}")

                st.markdown("##### ✏️ Tabel Hasil Plotting Final (Siap Export):")
                st.caption("Data di bawah sudah terurut dengan rapi. Anda dapat mengedit sel secara manual sebelum mengunduh file Excel.")

                edited_plotting = st.data_editor(
                    df_res,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic"
                )

                # EXPORT HASIL AKHIR EXCEL (DENGAN URUTAN TERBARU)
                output_plot = io.BytesIO()
                with pd.ExcelWriter(output_plot, engine='openpyxl') as writer:
                    edited_plotting.to_excel(writer, index=False, sheet_name='Hasil_Plotting')
                excel_plot_data = output_plot.getvalue()

                st.download_button(
                    "📊 Export Hasil Plotting Rapi ke Excel (.xlsx)", 
                    excel_plot_data, 
                    "hasil_plotting_tagihan_telkom.xlsx", 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses file: {e}")

# RENDER AI ASSISTANT SIDEBAR
render_ai_assistant()
