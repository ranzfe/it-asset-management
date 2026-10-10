import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, save_data, add_log, SITE_MAP

def render_tab9(df_asset):
    st.subheader("🔄 Form Mutasi Aset (Update Pemakai & Lokasi Baru)")
    st.caption("Gunakan form ini untuk mencatat mutasi unit, pergantian user/DA/ASP, update lokasi, serta link foto unit.")

    if df_asset.empty:
        st.warning("⚠️ **Database Aset Masih Kosong!** Silakan unggah master data aset terlebih dahulu di tab 'Upload Excel/CSV'.")
        return

    # Ambil list SN unik
    list_sn = []
    if "SN" in df_asset.columns:
        list_sn = sorted([str(sn).strip() for sn in df_asset["SN"].unique() if str(sn).strip() not in ["", "-", "nan", "None"]])

    # List pilihan Kd Site dengan label Depo resmi
    kd_site_options = ["-- Pilih Kd Site --"]
    for kd, site_name in SITE_MAP.items():
        kd_site_options.append(f"{kd} - {site_name}")
    kd_site_options.append("-- Ketik Manual --")

    # Ambil list DA / No Mobil unik dari database
    list_da = set()
    for col in ["DA/No Mobil", "No Mobil", "DA", "Kode DA"]:
        if col in df_asset.columns:
            vals = [str(v).strip() for v in df_asset[col].unique() if str(v).strip() not in ["", "-", "nan", "None"]]
            list_da.update(vals)
    sorted_list_da = sorted(list(list_da))

    st.markdown("##### 1. Pilih Aset yang Akan Dimutasi")
    selected_sn = st.selectbox(
        "Pilih / Ketik Serial Number (SN) Aset:", 
        ["-- Pilih SN --"] + list_sn, 
        key="sel_sn_mutasi_clean"
    )
    
    st.markdown("---")
    
    with st.form("form_mutasi_clean", clear_on_submit=False):
        st.markdown("##### 2. Input Data Pemakai & Lokasi Baru (TO BE)")
        
        col1, col2 = st.columns(2)
        with col1:
            # DROPDOWN KD SITE
            sel_kd_site = st.selectbox("Kd Site Baru*:", kd_site_options, key="m_kd_site_select")
            
            manual_kd_site = ""
            if sel_kd_site == "-- Ketik Manual --":
                manual_kd_site = st.text_input("Ketik Kd Site Baru Manual*:", placeholder="Contoh: 030601", key="m_kd_site_manual")

            # DROPDOWN DA / NO MOBIL DENGAN OPSI CUSTOM
            opt_da = ["-- Pilih DA / No Mobil --"] + sorted_list_da + ["-- Ketik Manual / DA Baru --"]
            sel_da = st.selectbox("DA / No Mobil Baru*:", opt_da, key="m_da_select")
            
            manual_da = ""
            if sel_da == "-- Ketik Manual / DA Baru --":
                manual_da = st.text_input("Ketik DA / No Mobil Baru Manual*:", placeholder="Contoh: 0301M04", key="m_da_manual")

            to_be_nama = st.text_input("Nama User / DA / ASP Baru*:", key="m_nama_new")
            
        with col2:
            to_be_sim = st.text_input("No SIM Card*:", key="m_sim_new")
            to_be_nik = st.text_input("Employee NIK*:", key="m_nik_new")
            link_foto_drive = st.text_input("Link Foto Asset (Google Drive)*:", placeholder="https://drive.google.com/file/d/...", key="m_foto_new")

        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            ket_mutasi = st.selectbox("Jenis / Keterangan Mutasi*:", [
                "MUTASI TAB DA", "MUTASI TAB ASP", "TAB BARU", "TUKAR TABLET", 
                "DA BARU", "NOPOL BARU", "TUKAR KODE/RUTE", "ASP BARU", "LAINNYA"
            ], key="m_ket_select")
            
            # OPSI KHUSUS TUKAR TABLET
            sn_pengganti = selected_sn
            if ket_mutasi == "TUKAR TABLET":
                st.info("🔄 Untuk jenis **TUKAR TABLET**, pilih SN Tablet Pengganti:")
                sn_pengganti = st.selectbox("Pilih SN Tablet Pengganti*:", [sn for sn in list_sn if sn != selected_sn], key="m_sn_swap_clean")

        with col4:
            catatan_tambahan = st.text_input("Catatan Tambahan / Detail Mutasi* (Masuk ke Kolom Keterangan):", placeholder="Contoh: TAB LAMA RUSAK", key="m_cat_clean")

        st.caption("* Menunjukkan kolom wajib diisi.")
        btn_submit = st.form_submit_button("💾 Simpan Mutasi & Update Database", type="primary")

        if btn_submit:
            # Ekstrak Kode Site murni
            raw_kd = manual_kd_site if sel_kd_site == "-- Ketik Manual --" else sel_kd_site.split(" - ")[0]
            final_da = manual_da if sel_da == "-- Ketik Manual / DA Baru --" else sel_da

            # VALIDASI WAJIB ISI
            if selected_sn == "-- Pilih SN --":
                st.error("❌ **Gagal Process!** Silakan pilih Serial Number (SN) terlebih dahulu.")
            elif raw_kd in ["-- Pilih Kd Site --", ""]:
                st.error("❌ **Gagal Process!** Kd Site Baru wajib dipilih atau diisi.")
            elif final_da in ["-- Pilih DA / No Mobil --", ""]:
                st.error("❌ **Gagal Process!** DA / No Mobil Baru wajib dipilih atau diisi.")
            elif to_be_nama.strip() == "":
                st.error("❌ **Gagal Process!** Nama User Baru wajib diisi.")
            elif to_be_sim.strip() == "":
                st.error("❌ **Gagal Process!** No SIM Card wajib diisi.")
            elif to_be_nik.strip() == "":
                st.error("❌ **Gagal Process!** Employee NIK wajib diisi.")
            elif link_foto_drive.strip() == "":
                st.error("❌ **Gagal Process!** Link Foto Asset (Google Drive) wajib diisi.")
            elif catatan_tambahan.strip() == "":
                st.error("❌ **Gagal Process!** Catatan Tambahan / Detail Mutasi wajib diisi.")
            else:
                kd_site_cap = raw_kd.strip().upper()
                site_name_auto = SITE_MAP.get(kd_site_cap, f"DP {kd_site_cap}")
                
                da_cap = final_da.strip().upper()
                nama_cap = to_be_nama.strip().upper()
                sim_cap = to_be_sim.strip().upper()
                nik_cap = to_be_nik.strip().upper()
                catatan_cap = catatan_tambahan.strip().upper()
                foto_url = link_foto_drive.strip()

                df_curr = load_data()
                
                idx_target = df_curr[df_curr["SN"].astype(str).str.strip().str.upper() == selected_sn.strip().upper()].index
                
                if not idx_target.empty:
                    target_sn = sn_pengganti if ket_mutasi == "TUKAR TABLET" else selected_sn
                    
                    df_curr.loc[idx_target, "User"] = nama_cap
                    df_curr.loc[idx_target, "Kd Site"] = kd_site_cap
                    df_curr.loc[idx_target, "Site"] = site_name_auto
                    df_curr.loc[idx_target, "DA/No Mobil"] = da_cap
                    if "No Mobil" in df_curr.columns:
                        df_curr.loc[idx_target, "No Mobil"] = da_cap
                    df_curr.loc[idx_target, "SIM Card"] = sim_cap
                    df_curr.loc[idx_target, "NIK"] = nik_cap
                    df_curr.loc[idx_target, "SN"] = target_sn
                    df_curr.loc[idx_target, "Keterangan"] = catatan_cap
                    df_curr.loc[idx_target, "Link Foto Asset"] = foto_url
                    
                    log_detail = f"MUTASI [{ket_mutasi}]: Diserahkan ke {nama_cap} ({kd_site_cap}-{site_name_auto} | {da_cap}). FOTO: {foto_url}. KETERANGAN: {catatan_cap}"
                    add_log("MUTASI ASET", target_sn, nama_cap, log_detail)
                    
                    save_data(df_curr)
                    
                    st.success(f"""
                    🎉 **MUTASI ASET BERHASIL DIPROSES & DISIMPAN!**
                    
                    * **User Baru**: {nama_cap}
                    * **Kd Site**: {kd_site_cap} ➔ **Site**: {site_name_auto}
                    * **DA / No Mobil**: {da_cap}
                    * **Keterangan**: {catatan_cap}
                    """)
                    st.balloons()
