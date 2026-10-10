import streamlit as st
import pandas as pd
from database import save_data, add_log, STATUS_OPTIONS

def render_tab6(df_asset):
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
