import streamlit as st
import pandas as pd
from database import save_data, add_log, COLUMNS

def render_tab5(df_asset):
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
