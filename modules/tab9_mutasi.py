import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, save_data, add_log

def render_tab9(df_asset):
    st.subheader("🔄 Form Mutasi & Perubahan User Aset (AS IS ➔ TO BE)")
    st.caption("Form ini digunakan untuk mencatat perpindahan tablet/hardware antar user/sales/DA, tukar unit, atau perubahan rute DA/ASP.")

    if df_asset.empty:
        st.warning("⚠️ **Database Aset Masih Kosong!** Silakan unggah master data aset terlebih dahulu di tab 'Upload Excel/CSV'.")

    list_sn = sorted([str(sn).strip() for sn in df_asset["SN"].unique() if str(sn).strip() not in ["", "-", "nan", "None"]])
    
    st.markdown("##### 1. Pilih Aset yang Akan Dimutasi")
    selected_sn_mutasi = st.selectbox(
        "Pilih / Ketik Serial Number (SN) Aset Saat Ini:", 
        ["-- Pilih SN --"] + list_sn, 
        key="sel_sn_mutasi_ext"
    )
    
    # DENGAN PEMETAAN YANG TEPAT DARI DATABASE
    as_is_depo = as_is_da = as_is_nama = as_is_sim = as_is_nik = ""
    
    if selected_sn_mutasi != "-- Pilih SN --" and not df_asset.empty:
        # Match SN secara persis & case-insensitive
        match_row = df_asset[df_asset["SN"].astype(str).str.strip().str.upper() == selected_sn_mutasi.strip().upper()]
        
        if not match_row.empty:
            r = match_row.iloc[0]
            
            # Sesuai struktur data di Form Edit (Gambar 1)
            as_is_depo = str(r.get("Site", r.get("Kd Site", r.get("Ket Site", "")))).strip()
            as_is_da = str(r.get("No Mobil", r.get("DA", ""))).strip()
            as_is_nama = str(r.get("User", r.get("Nama DA", r.get("Nama ASP", "")))).strip()
            as_is_sim = str(r.get("SIM Card", r.get("SIM", ""))).strip()
            as_is_nik = str(r.get("NIK", "")).strip()

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
            to_be_depo = st.text_input("Depo Baru (TO BE)*:", value=as_is_depo, key="m_to_depo")
            to_be_da = st.text_input("Kode DA / ASP Baru (TO BE)*:", value=as_is_da, key="m_to_da")
            to_be_nama = st.text_input("Nama User / DA / ASP Baru (TO BE)*:", value="", key="m_to_nama")
            
            # KOTAK SN TO BE OTOMATIS SAMA DENGAN SN AS IS & TERKUNCI
            sn_tobe_val = selected_sn_mutasi if selected_sn_mutasi != "-- Pilih SN --" else ""
            st.text_input("SN Device Baru (Otomatis Terkunci Sama):", value=sn_tobe_val, disabled=True, key="m_to_sn_disabled")
            
            to_be_sim = st.text_input("No SIM Card Baru (TO BE)*:", value=as_is_sim, key="m_to_sim")
            to_be_nik = st.text_input("Employee NIK Baru (TO BE)*:", value="", key="m_to_nik")

        st.markdown("---")
        ket_mutasi = st.selectbox("Jenis / Keterangan Mutasi*:", [
            "TAB BARU", "TUKAR TABLET", "DA BARU", "NOPOL BARU", 
            "TUKAR KODE/RUTE", "ASP BARU", "MUTASI TAB DA", "MUTASI TAB ASP", "LAINNYA"
        ], key="m_ket")
        
        # OPSI KHUSUS TUKAR TABLET
        sn_pengganti = sn_tobe_val
        if ket_mutasi == "TUKAR TABLET":
            st.info("🔄 Untuk jenis **TUKAR TABLET**, pilih SN Tablet Pengganti:")
            sn_pengganti = st.selectbox("Pilih SN Tablet Pengganti*:", [sn for sn in list_sn if sn != selected_sn_mutasi], key="m_sn_swap")

        catatan_tambahan = st.text_input("Catatan Tambahan / Detail Mutasi*:", value="", key="m_cat")

        st.caption("* Menunjukkan kolom wajib diisi.")
        btn_submit_mutasi = st.form_submit_button("💾 Simpan Mutasi & Update Database", type="primary")

        if btn_submit_mutasi:
            # 1. VALIDASI WAJIB ISI UNTUK SEMUA FORM
            if selected_sn_mutasi == "-- Pilih SN --":
                st.error("❌ **Gagal Process!** Silakan pilih Serial Number (SN) terlebih dahulu.")
            elif to_be_depo.strip() == "":
                st.error("❌ **Gagal Process!** Depo Baru (TO BE) wajib diisi.")
            elif to_be_da.strip() == "":
                st.error("❌ **Gagal Process!** Kode DA / ASP Baru (TO BE) wajib diisi.")
            elif to_be_nama.strip() == "":
                st.error("❌ **Gagal Process!** Nama User / DA / ASP Baru (TO BE) wajib diisi.")
            elif to_be_sim.strip() == "":
                st.error("❌ **Gagal Process!** No SIM Card Baru (TO BE) wajib diisi.")
            elif to_be_nik.strip() == "":
                st.error("❌ **Gagal Process!** Employee NIK Baru (TO BE) wajib diisi.")
            elif catatan_tambahan.strip() == "":
                st.error("❌ **Gagal Process!** Catatan Tambahan / Detail Mutasi wajib diisi.")
            else:
                # 2. AUTO-CONVERT ISI INPUTAN MENJADI HURUF KAPITAL (UPPERCASE)
                to_be_depo_cap = to_be_depo.strip().upper()
                to_be_da_cap = to_be_da.strip().upper()
                to_be_nama_cap = to_be_nama.strip().upper()
                to_be_sim_cap = to_be_sim.strip().upper()
                to_be_nik_cap = to_be_nik.strip().upper()
                catatan_tambahan_cap = catatan_tambahan.strip().upper()

                df_curr = load_data()
                
                idx_target = df_curr[df_curr["SN"].astype(str).str.strip().str.upper() == selected_sn_mutasi.strip().upper()].index
                if not idx_target.empty:
                    final_sn = sn_pengganti if ket_mutasi == "TUKAR TABLET" else sn_tobe_val
                    
                    # Update bidang utama dengan data KAPITAL
                    df_curr.loc[idx_target, "User"] = to_be_nama_cap
                    df_curr.loc[idx_target, "Site"] = to_be_depo_cap
                    df_curr.loc[idx_target, "No Mobil"] = to_be_da_cap
                    df_curr.loc[idx_target, "SIM Card"] = to_be_sim_cap
                    df_curr.loc[idx_target, "NIK"] = to_be_nik_cap
                    df_curr.loc[idx_target, "SN"] = final_sn
                    
                    log_detail = f"MUTASI [{ket_mutasi}]: ({as_is_depo} | {as_is_da} | {as_is_nama}) ➔ ({to_be_depo_cap} | {to_be_da_cap} | {to_be_nama_cap}). CATATAN: {catatan_tambahan_cap}"
                    add_log("MUTASI ASET", final_sn, to_be_nama_cap, log_detail)
                    
                    save_data(df_curr)
                    
                    # 3. NOTIFIKASI SUKSES & HAPUS STATE Form
                    st.success(f"""
                    🎉 **MUTASI ASET BERHASIL DIPROSES & DISIMPAN!**
                    - **User Baru**: {to_be_nama_cap}
                    - **Kode DA/ASP**: {to_be_da_cap}
                    - **Depo**: {to_be_depo_cap}
                    - **SN Device**: {final_sn}
                    - **Status Database**: Tersimpan & Ter-commit ke GitHub.
                    """)
                    st.balloons()
