import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, save_data, add_log

def render_tab9(df_asset):
    st.subheader("🔄 Form Mutasi & Perubahan User Aset (AS IS ➔ TO BE)")
    st.caption("Gunakan form ini untuk mencatat perpindahan aset/tablet antar user, ganti unit, atau update rute DA/ASP.")

    list_sn = sorted([sn for sn in df_asset["SN"].unique() if str(sn).strip() != ""])
    
    with st.form("form_mutasi_asset", clear_on_submit=True):
        st.markdown("##### 1. Pilih Aset yang Akan Dimutasi")
        selected_sn_mutasi = st.selectbox("Pilih Serial Number (SN) Aset:", ["-- Pilih SN --"] + list_sn)
        
        # Auto-pull data AS IS
        as_is_depo = as_is_da = as_is_nama = as_is_sim = as_is_nik = ""
        if selected_sn_mutasi != "-- Pilih SN --":
            r_curr = df_asset[df_asset["SN"] == selected_sn_mutasi].iloc[0]
            as_is_depo = str(r_curr.get("Site", ""))
            as_is_da = str(r_curr.get("No Mobil", ""))
            as_is_nama = str(r_curr.get("User", ""))
            as_is_sim = str(r_curr.get("SIM Card", ""))
            as_is_nik = str(r_curr.get("NIK", ""))

        st.markdown("---")
        col_asis, col_tobe = st.columns(2)
        
        # TAMPILAN DATA AS IS (KONDISI SAAT INI)
        with col_asis:
            st.markdown("### 📌 KONDISI SAAT INI (AS IS)")
            st.text_input("Depo (AS IS):", value=as_is_depo, disabled=True)
            st.text_input("Kode DA / ASP (AS IS):", value=as_is_da, disabled=True)
            st.text_input("Nama User / DA / ASP (AS IS):", value=as_is_nama, disabled=True)
            st.text_input("Serial Number (AS IS):", value=selected_sn_mutasi, disabled=True)
            st.text_input("No SIM Card (AS IS):", value=as_is_sim, disabled=True)
            st.text_input("Employee NIK (AS IS):", value=as_is_nik, disabled=True)

        # INPUT DATA TO BE (PENERIMA / DATA BARU)
        with col_tobe:
            st.markdown("### 🚀 KONDISI BARU (TO BE)")
            to_be_depo = st.text_input("Depo Baru (TO BE):", value=as_is_depo)
            to_be_da = st.text_input("Kode DA / ASP Baru (TO BE):", value=as_is_da)
            to_be_nama = st.text_input("Nama User / DA / ASP Baru (TO BE):", value="")
            to_be_sn = st.text_input("SN Device Baru (Isi jika Tukar Unit):", value=selected_sn_mutasi)
            to_be_sim = st.text_input("No SIM Card Baru (TO BE):", value=as_is_sim)
            to_be_nik = st.text_input("Employee NIK Baru (TO BE):", value="")

        st.markdown("---")
        ket_mutasi = st.selectbox("Jenis / Keterangan Mutasi:", [
            "TAB BARU", "TUKAR TABLET", "DA BARU", "NOPOL BARU", 
            "TUKAR KODE/RUTE", "ASP BARU", "MUTASI TAB DA", "MUTASI TAB ASP", "LAINNYA"
        ])
        catatan_tambahan = st.text_input("Catatan Tambahan / Detail Mutasi:", value="")

        btn_submit_mutasi = st.form_submit_button("💾 Process & Update Mutasi Aset")

        if btn_submit_mutasi:
            if selected_sn_mutasi == "-- Pilih SN --":
                st.error("Silakan pilih Serial Number (SN) terlebih dahulu!")
            elif to_be_nama.strip() == "":
                st.error("Nama User Baru (TO BE) wajib diisi!")
            else:
                df_curr = load_data()
                
                # Update data aset di database utama
                idx_target = df_curr[df_curr["SN"] == selected_sn_mutasi].index
                if not idx_target.empty:
                    df_curr.loc[idx_target, "User"] = to_be_nama
                    df_curr.loc[idx_target, "Site"] = to_be_depo
                    df_curr.loc[idx_target, "No Mobil"] = to_be_da
                    df_curr.loc[idx_target, "SIM Card"] = to_be_sim
                    df_curr.loc[idx_target, "NIK"] = to_be_nik
                    df_curr.loc[idx_target, "SN"] = to_be_sn  # Jika tukar unit SN
                    
                    # Tambah Log Detail Mutasi
                    log_detail = f"MUTASI [{ket_mutasi}]: {as_is_nama} ({as_is_da}) ➔ {to_be_nama} ({to_be_da}). {catatan_tambahan}"
                    add_log("MUTASI ASET", to_be_sn, to_be_nama, log_detail)
                    
                    save_data(df_curr)
                    st.success(f"🎉 **Mutasi Aset Berhasil!** Data {to_be_nama} telah ter-update di database dan GitHub.")
                    st.rerun()
