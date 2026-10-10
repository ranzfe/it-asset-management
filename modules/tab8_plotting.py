import streamlit as st
import pandas as pd
import io
import re

def render_tab8(df_asset):
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
                    if not df_hist.empty:
                        sim_col_hist = [c for c in df_hist.columns if any(k in c.upper() for k in ["SIM", "MSISDN", "NOMOR"])]
                        if sim_col_hist:
                            df_hist["SIM_clean"] = df_hist[sim_col_hist[0]].apply(normalize_phone)
                        else:
                            df_hist["SIM_clean"] = ""

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

                        # ALUR 1: CEK HISTORIS
                        hist_match = pd.DataFrame()
                        if not df_hist.empty and sim_clean != "" and "SIM_clean" in df_hist.columns:
                            hist_match = df_hist[df_hist["SIM_clean"] == sim_clean]

                        if not hist_match.empty:
                            h_target = hist_match.iloc[0]
                            depo_val = str(h_target.get("DEPO", "-")).strip()
                            user_val = str(h_target.get("NAMA USER", "-")).strip()
                            mobil_val = str(h_target.get("KODE DA/NO MOBIL", "-")).strip()
                            sn_val = str(h_target.get("SN DEVICE", "-")).strip()

                        # ALUR 2: CEK UPDATE TERBARU BULAN INI
                        if not df_users.empty:
                            user_match = pd.DataFrame()
                            
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

                            if user_match.empty and sim_clean != "" and "SIM_clean" in df_users.columns:
                                user_match = df_users[df_users["SIM_clean"] == sim_clean]

                            if not user_match.empty:
                                u_row = user_match.iloc[0]
                                
                                if col_u_site != "-- Pilih / Tidak Ada --":
                                    val_site = str(u_row.get(col_u_site, "")).strip()
                                    if val_site not in ["", "-", "nan", "None"]:
                                        depo_val = val_site
                                
                                nama_da_v = str(u_row.get(col_u_namada, "")).strip() if col_u_namada != "-- Pilih / Tidak Ada --" else ""
                                nama_asp_v = str(u_row.get(col_u_asp, "")).strip() if col_u_asp != "-- Pilih / Tidak Ada --" else ""
                                new_user = nama_da_v if nama_da_v != "" else (nama_asp_v if nama_asp_v != "" else "")
                                if new_user not in ["", "-", "nan", "None"]:
                                    user_val = new_user

                                da_v = str(u_row.get(col_u_da, "")).strip() if col_u_da != "-- Pilih / Tidak Ada --" else ""
                                mobil_v = str(u_row.get(col_u_mobil, "")).strip() if col_u_mobil != "-- Pilih / Tidak Ada --" else ""
                                new_da = da_v if da_v != "" else (mobil_v if mobil_v != "" else "")
                                if new_da not in ["", "-", "nan", "None"]:
                                    mobil_val = new_da

                                if col_u_sn != "-- Pilih / Tidak Ada --":
                                    c_sn = str(u_row.get(col_u_sn, "")).strip()
                                    if c_sn not in ["", "-", "nan", "None"]:
                                        sn_val = c_sn

                        # DEEP SEARCH SN DEVICE
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

                        # FALLBACK DB ITAM
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

                        clean_user_check = str(user_val).strip()
                        ket_status = "AKTIF" if clean_user_check not in ["", "-", "nan", "None"] else "TIDAK AKTIF"

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
                    st.success("🎉 **Auto-Plotting Selesai!** Status AKTIF/TIDAK AKTIF diperbarui secara presisi.")

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

                if filter_depo != "Semua Depo":
                    df_res = df_res[df_res["DEPO"] == filter_depo]
                if filter_ket != "Semua Status":
                    df_res = df_res[df_res["KETERANGAN"] == filter_ket]

                asc_flag = True if sort_order_plot == "A-Z (Asc)" else False
                if sort_col_plot == "TAGIHAN":
                    df_res["_tagihan_num"] = pd.to_numeric(df_res["TAGIHAN"].str.replace(r'\D', '', regex=True), errors='coerce').fillna(0)
                    df_res = df_res.sort_values(by="_tagihan_num", ascending=asc_flag).drop(columns=["_tagihan_num"])
                else:
                    df_res = df_res.sort_values(by=sort_col_plot, ascending=asc_flag)

                st.markdown("---")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                tot_items = len(df_res)
                tot_aktif = len(df_res[df_res["KETERANGAN"] == "AKTIF"])
                tot_no_aktif = len(df_res[df_res["KETERANGAN"] == "TIDAK AKTIF"])
                
                tagihan_sum = pd.to_numeric(df_res["TAGIHAN"].astype(str).str.replace(r'\D', '', regex=True), errors='coerce').fillna(0).sum()

                col_m1.metric("Total SIM Card", tot_items)
                col_m2.metric("Nomor AKTIF", tot_aktif)
                col_m3.metric("Nomor TIDAK AKTIF", tot_no_aktif)
                col_m4.metric("Total Tagihan (Rp)", f"Rp {tagihan_sum:,.0f}")

                st.markdown("##### ✏️ Tabel Hasil Plotting Final (Siap Export):")
                st.caption("Status `AKTIF` jika memiliki Nama User pemakai, dan `TIDAK AKTIF` jika nomor SIM card tidak terikat ke user manapun.")

                edited_plotting = st.data_editor(
                    df_res,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic"
                )

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
