import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, save_data, add_log

def render_tab9(df_asset):
    st.subheader("🔄 Form Mutasi Aset (Update Pemakai & Lokasi Baru)")
    st.caption("Gunakan form ini untuk mencatat mutasi unit, pergantian user/DA/ASP, update lokasi, serta link foto unit.")

    if df_asset.empty:
        st.warning("⚠️ **Database Aset Masih Kosong!** Silakan unggah master data aset terlebih dahulu di tab 'Upload Excel/CSV'.")
        return

    # Ambil daftar SN unik
    list_sn = []
    if "SN" in df_asset.columns:
        list_sn = sorted([str(sn).strip() for sn in df_asset["SN"].unique() if str(sn).strip() not in ["", "-", "nan", "None"]])

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
            to_be_depo = st.text_input("Depo / Site Baru*:", key="m_depo_new")
            to_be_da = st.text_input("Kode DA / No Mobil Baru*:", key="m_da_new")
            to_be_nama = st.text_input("Nama User / DA / ASP Baru*:", key="m_nama_new")
            
        with col2:
            to_be_sim = st.text_input("No SIM Card*:", key="m_sim_new")
            to_be_nik = st.text_input("Employee NIK*:", key="m_nik_new")
            link_foto_drive = st.text_input("Link Foto Asset (Google Drive):", placeholder="https://drive.google.com/file/d/...", key="m_foto_new")

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
            # VALIDASI KETAT WAJIB ISI
            if selected_sn == "-- Pilih SN --":
                st.error("❌ **Gagal Process!** Silakan pilih Serial Number (SN) terlebih dahulu.")
            elif to_be_depo.strip() == "":
                st.error("❌ **Gagal Process!** Depo / Site Baru wajib diisi.")
            elif to_be_da.strip() == "":
                st.error("❌ **Gagal Process!** Kode DA / No Mobil Baru wajib diisi.")
            elif to_be_nama.strip() == "":
                st.error("❌ **Gagal Process!** Nama User Baru wajib diisi.")
            elif to_be_sim.strip() == "":
                st.error("❌ **Gagal Process!** No SIM Card wajib diisi.")
            elif to_be_nik.strip() == "":
                st.error("❌ **Gagal Process!** Employee NIK wajib diisi.")
            elif catatan_tambahan.strip() == "":
                st.error("❌ **Gagal Process!** Catatan Tambahan / Detail Mutasi wajib diisi.")
            else:
                # AUTO-CONVERT INPUT TEKS KE HURUF KAPITAL (UPPERCASE)
                depo_cap = to_be_depo.strip().upper()
                da_cap = to_be_da.strip().upper()
                nama_cap = to_be_nama.strip().upper()
                sim_cap = to_be_sim.strip().upper()
                nik_cap = to_be_nik.strip().upper()
                catatan_cap = catatan_tambahan.strip().upper()
                foto_url = link_foto_drive.strip()

                df_curr = load_data()
                
                idx_target = df_curr[df_curr["SN"].astype(str).str.strip().str.upper() == selected_sn.strip().upper()].index
                
                if not idx_target.empty:
                    final_sn = sn_pengganti if ket_mutasi == "TUKAR TABLET" else selected_sn
                    
                    # UPDATE DATA DI KOLOM UTAMA DATABASE
                    df_curr.loc[idx_target, "User"] = nama_cap
                    df_curr.loc[idx_target, "Site"] = depo_cap
                    df_curr.loc[idx_target, "No Mobil"] = da_cap
                    df_curr.loc[idx_target, "SIM Card"] = sim_cap
                    df_curr.loc[idx_target, "NIK"] = nik_cap
                    df_curr.loc[idx_target, "SN"] = final_sn
                    
                    # SIMPAN CATATAN TAMBAHAN KE KOLOM KETERANGAN
                    df_curr.loc[idx_target, "Keterangan"] = catatan_cap
                    
                    # SIMPAN LINK FOTO GDRIVE
                    if foto_url != "":
                        df_curr.loc[idx_target, "Link Foto Asset"] = foto_url
                    
                    # PENCATATAN LOG HISTORY
                    log_detail = f"MUTASI [{ket_mutasi}]: Diserahkan ke {nama_cap} ({depo_cap} | {da_cap}). KETERANGAN: {catatan_cap}"
                    add_log("MUTASI ASET", final_sn, nama_cap, log_detail)
                    
                    save_data(df_curr)
                    
                    st.success(f"""
                    🎉 **MUTASI ASET BERHASIL DIPROSES & DISIMPAN!**
                    - **User Baru**: {nama_cap}
                    - **Kode DA/No Mobil**: {da_cap}
                    - **Depo/Site**: {depo_cap}
                    - **Keterangan**: {catatan_cap}
                    - **Status Database**: Tersimpan & Otomatis Ter-commit ke GitHub.
                    """)
                    st.balloons()
