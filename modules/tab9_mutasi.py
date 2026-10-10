import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, save_data, add_log

def render_tab9(df_asset):
    st.subheader("🔄 Form Mutasi & Perubahan User Aset (AS IS ➔ TO BE)")
    st.caption("Form ini digunakan untuk mencatat perpindahan tablet/hardware antar user/sales/DA, tukar unit, atau perubahan rute DA/ASP.")

    if df_asset.empty:
        st.warning("⚠️ **Database Aset Masih Kosong!** Silakan upload atau masukkan data aset terlebih dahulu di tab 'Upload Excel/CSV' atau 'Tambah Manual'.")

    list_sn = sorted([str(sn).strip() for sn in df_asset["SN"].unique() if str(sn).strip() not in ["", "-", "nan", "None"]])
    
    st.markdown("##### 1. Pilih Aset yang Akan Dimutasi")
    selected_sn_mutasi = st.selectbox(
        "Pilih / Ketik Serial Number (SN) Aset Saat Ini:", 
        ["-- Pilih SN --"] + list_sn, 
        key="sel_sn_mutasi_ext"
    )
    
    # EKSTRAKSI DATA AS IS DARI DATABASE
    as_is_depo = as_is_da = as_is_nama = as_is_sim = as_is_nik = ""
    
    if selected_sn_mutasi != "-- Pilih SN --" and not df_asset.empty:
        # Match case-insensitive & strip
        match_row = df_asset[df_asset["SN"].astype(str).str.strip().str.upper() == selected_sn_mutasi.strip().upper()]
        
        if not match_row.empty:
            r_curr = match_row.iloc[0]
            
            # DEPO -> Ket Site / Site
            as_is_depo = str(r_curr.get("Site", r_curr.get("Ket Site", ""))).strip()
            
            # KODE DA -> No Mobil / DA
            as_is_da = str(r_curr.get("No Mobil", r_curr.get("DA", ""))).strip()
            
            # NAMA USER -> User / Nama DA / Nama ASP
            user_v = str(r_curr.get("User", "")).strip()
            nama_da_v = str(r_curr.get("Nama DA", "")).strip()
            nama_asp_v = str(r_curr.get("Nama ASP", "")).strip()
            as_is_nama = user_v if user_v != "" else (nama_da_v if nama_da_v != "" else nama_asp_v)
            
            # NO SIMCARD -> SIM Card / SIM
            as_is_sim = str(r_curr.get("SIM Card", r_curr.get("SIM", ""))).strip()
            
            # EMPLOYEE NIK -> NIK
            as_is_nik = str(r_curr.get("NIK", "")).strip()

    st.markdown("---")
    
    with st.form("form_mutasi_asset", clear_on_submit=False):
        col_asis, col_tobe = st.columns(2)
        
        # TAMPILAN DATA AS IS (KONDISI SAAT INI)
        with col_asis:
            st.markdown("### 📌 KONDISI SAAT INI (AS IS)")
            st.text_input("Depo (AS IS):", value=as_is_depo, disabled=True, key="m_as_depo")
            st.text_input("Kode DA / ASP (AS IS):", value=as_is_da, disabled=True, key="m_as_da")
            st.text_input("Nama User / DA / ASP (AS IS):", value=as_is_nama, disabled=True, key="m_as_nama")
            st.text_input("Serial Number (AS IS):", value=selected_sn_mutasi if selected_sn_mutasi != "-- Pilih SN --" else "", disabled=True, key="m_as_sn")
            st.text_input("No SIM Card (AS IS):", value=as_is_sim, disabled=True, key="m_as_sim")
            st.text_input("Employee NIK (AS IS):", value=as_is_nik, disabled=True, key="m_as_nik")

        # INPUT DATA TO BE (KONDISI BARU)
        with col_tobe:
            st.markdown("### 🚀 KONDISI BARU (TO BE)")
            to_be_depo = st.text_input("Depo Baru (TO BE):", value=as_is_depo, key="m_to_depo")
            to_be_da = st.text_input("Kode DA / ASP Baru (TO BE):", value=as_is_da, key="m_to_da")
            to_be_nama = st.text_input("Nama User / DA / ASP Baru (TO BE):", value="", key="m_to_nama")
            
            # KOTAK SN TO BE OTOMATIS SAMA DENGAN SN ATAS & TIDAK BISA DIEDIT (DISABLED)
            sn_tobe_val = selected_sn_mutasi if selected_sn_mutasi != "-- Pilih SN --" else ""
            st.text_input("SN Device Baru (Otomatis Sama):", value=sn_tobe_val, disabled=True, key="m_to_sn_disabled")
            
            to_be_sim = st.text_input("No SIM Card Baru (TO BE):", value=as_is_sim, key="m_to_sim")
            to_be_nik = st.text_input("Employee NIK Baru (TO BE):", value="", key="m_to_nik")

        st.markdown("---")
        ket_mutasi = st.selectbox("Jenis / Keterangan Mutasi:", [
            "TAB BARU", "TUKAR TABLET", "DA BARU", "NOPOL BARU", 
            "TUKAR KODE/RUTE", "ASP BARU", "MUTASI TAB DA", "MUTASI TAB ASP", "LAINNYA"
        ], key="m_ket")
        
        # OPSI KHUSUS JIKA TUKAR TABLET
        sn_pengganti = sn_tobe_val
        if ket_mutasi == "TUKAR TABLET":
            st.info("🔄 Untuk jenis **TUKAR TABLET**, silakan pilih SN Tablet Pengganti di bawah ini:")
            sn_pengganti = st.selectbox("Pilih SN Tablet Pengganti:", [sn for sn in list_sn if sn != selected_sn_mutasi], key="m_sn_swap")

        catatan_tambahan = st.text_input("Catatan Tambahan / Detail Mutasi:", value="", key="m_cat")

        btn_submit_mutasi = st.form_submit_button("💾 Simpan Mutasi & Update Database")

        if btn_submit_mutasi:
            if selected_sn_mutasi == "-- Pilih SN --":
                st.error("Silakan pilih Serial Number (SN) terlebih dahulu!")
            elif to_be_nama.strip() == "":
                st.error("Nama User Baru (TO BE) wajib diisi!")
            else:
                df_curr = load_data()
                
                idx_target = df_curr[df_curr["SN"].astype(str).str.strip().str.upper() == selected_sn_mutasi.strip().upper()].index
                if not idx_target.empty:
                    final_sn = sn_pengganti if ket_mutasi == "TUKAR TABLET" else sn_tobe_val
                    
                    df_curr.loc[idx_target, "User"] = to_be_nama
                    df_curr.loc[idx_target, "Site"] = to_be_depo
                    df_curr.loc[idx_target, "No Mobil"] = to_be_da
                    df_curr.loc[idx_target, "SIM Card"] = to_be_sim
                    df_curr.loc[idx_target, "NIK"] = to_be_nik
                    df_curr.loc[idx_target, "SN"] = final_sn
                    
                    log_detail = f"MUTASI [{ket_mutasi}]: ({as_is_depo} | {as_is_da} | {as_is_nama}) ➔ ({to_be_depo} | {to_be_da} | {to_be_nama}). {catatan_tambahan}"
                    add_log("MUTASI ASET", final_sn, to_be_nama, log_detail)
                    
                    save_data(df_curr)
                    st.success(f"🎉 **Mutasi Berhasil!** Data {to_be_nama} ({to_be_da}) telah otomatis ter-update ke database dan GitHub.")
                    st.rerun()
