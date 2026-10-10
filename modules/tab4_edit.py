import streamlit as st
from database import save_data, add_log, COLUMNS, STATUS_OPTIONS

def render_tab4(df_asset):
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
