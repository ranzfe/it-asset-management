import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, save_data, add_log

def render_tab9(df_asset):
    st.subheader("🔄 Form Mutasi & Perubahan User Aset (AS IS ➔ TO BE)")
    st.caption("Form ini digunakan untuk mencatat perpindahan tablet/hardware antar user/sales/DA, tukar unit, atau perubahan rute DA/ASP.")

    list_sn = sorted([str(sn).strip() for sn in df_asset["SN"].unique() if str(sn).strip() not in ["", "-", "nan", "None"]])
    
    st.markdown("##### 1. Pilih Aset yang Akan Dimutasi")
    selected_sn_mutasi = st.selectbox("Pilih Serial Number (SN) Aset Saat Ini:", ["-- Pilih SN --"] + list_sn, key="sel_sn_mutasi_ext")
    
    # PEBAIKAN PEMETAAN PRESISI UNTUK DATA AS IS
    as_is_depo = as_is_da = as_is_nama = as_is_sim = as_is_nik = ""
    
    if selected_sn_mutasi != "-- Pilih SN --":
        # Cari baris yang cocok berdasarkan SN (case-insensitive)
        match_row = df_asset[df_asset["SN"].astype(str).str.strip().str.upper() == selected_sn_mutasi.upper()]
        
        if not match_row.empty:
            r_curr = match_row.iloc[0]
            
            # DEPO -> Ket Site / Site
            as_is_depo = str(r_curr.get("Ket Site", r_curr.get("Site", ""))).strip()
            
            # KODE DA -> DA / No Mobil
            as_is_da = str(r_curr.get("DA", r_curr.get("No Mobil", ""))).strip()
            
            # NAMA USER -> Nama DA / User / Nama ASP
            nama_da_v = str(r_curr.get("Nama DA", "")).strip()
            nama_asp_v = str(r_curr.get("Nama ASP", "")).strip()
            user_v = str(r_curr.get("User", "")).strip()
            as_is_nama = nama_da_v if nama_da_v != "" else (nama_asp_v if nama_asp_v != "" else user_v)
            
            # NO SIMCARD -> SIM Card / SIM
            as_is_sim = str(r_curr.get("SIM Card", r_curr.get("SIM", ""))).strip()
            
            # EMPLOYEE NIK -> NIK
            as_is_nik = str(r_curr.get("NIK", "")).strip()

    st.markdown("---")
    
    with st.form("form_mutasi_asset", clear_on_submit=False):
        col_asis, col_tobe = st.columns(2)
        
        # TAMPILAN DATA AS IS (KONDISI SEBELUMNYA)
        with col_asis:
            st.markdown("### 📌 KONDISI SAAT INI (AS IS)")
            st.text_input("Depo (AS IS - Ket Site):", value=as_is_depo, disabled=True, key="m_as_depo")
            st.text_input("Kode DA / ASP (AS IS - DA):", value=as_is_da, disabled=True, key="m_as_da")
            st.text_input("Nama User / DA / ASP (AS IS - User):", value=as_is_nama, disabled=True, key="m_as_nama")
            st.text_input("Serial Number (AS IS - SN):", value=selected_sn_mutasi if selected_sn_mutasi != "-- Pilih SN --" else "", disabled=True, key="m_as_sn")
            st.text_input("No SIM Card (AS IS - SIM Card):", value=as_is_sim, disabled=True, key="m_as_sim")
            st.text_input("Employee NIK (AS IS - NIK):", value=as_is_nik, disabled=True, key="m_as_nik")

        # INPUT DATA TO BE (PENERIMA / PERUBAHAN BARU)
        with col_tobe:
            st.markdown("### 🚀 KONDISI BARU (TO BE)")
            to_be_depo = st.text_input("Depo Baru (TO BE):", value=as_is_depo, key="m_to_depo")
            to_be_da = st.text_input("Kode DA / ASP Baru (TO BE):", value=as_is_da, key="m_to_da")
            to_be_nama = st.text_input("Nama User / DA / ASP Baru (TO BE):", value="", key="m_to_nama")
            to_be_sn = st.selectbox("SN Device Baru (Isi jika Tukar Unit):", [selected_sn_mutasi if selected_sn_mutasi != "-- Pilih SN --" else ""] + [sn for sn in list_sn if sn != selected_sn_mutasi], key="m_to_sn")
            to_be_sim = st.text_input("No SIM Card Baru (TO BE):", value=as_is_sim, key="m_to_sim")
            to_be_nik = st.text_input("Employee NIK Baru (TO BE):", value="", key="m_to_nik")

        st.markdown("---")
        ket_mutasi = st.selectbox("Jenis / Keterangan Mutasi:", [
            "TAB BARU", "TUKAR TABLET", "DA BARU", "NOPOL BARU", 
            "TUKAR KODE/RUTE", "ASP BARU", "MUTASI TAB DA", "MUTASI TAB ASP", "LAINNYA"
        ], key="m_ket")
        catatan_tambahan = st.text_input("Catatan Tambahan / Detail Mutasi:", value="", key="m_cat")

        btn_submit_mutasi = st.form_submit_button("💾 Simpan Mutasi & Update Database")

        if btn_submit_mutasi:
            if selected_sn_mutasi == "-- Pilih SN --":
                st.error("Silakan pilih Serial Number (SN) terlebih dahulu!")
            elif to_be_nama.strip() == "":
                st.error("Nama User Baru (TO BE) wajib diisi!")
            else:
                df_curr = load_data()
                
                idx_target = df_curr[df_curr["SN"].astype(str).str.strip().str.upper() == selected_sn_mutasi.upper()].index
                if not idx_target.empty:
                    df_curr.loc[idx_target, "User"] = to_be_nama
                    df_curr.loc[idx_target, "Site"] = to_be_depo
                    df_curr.loc[idx_target, "No Mobil"] = to_be_da
                    df_curr.loc[idx_target, "SIM Card"] = to_be_sim
                    df_curr.loc[idx_target, "NIK"] = to_be_nik
                    df_curr.loc[idx_target, "SN"] = to_be_sn
                    
                    log_detail = f"MUTASI [{ket_mutasi}]: ({as_is_depo} | {as_is_da} | {as_is_nama}) ➔ ({to_be_depo} | {to_be_da} | {to_be_nama}). {catatan_tambahan}"
                    add_log("MUTASI ASET", to_be_sn, to_be_nama, log_detail)
                    
                    save_data(df_curr)
                    st.success(f"🎉 **Mutasi Berhasil!** Data {to_be_nama} ({to_be_da}) telah otomatis ter-update ke database dan GitHub.")
                    st.rerun()
