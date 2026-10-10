import streamlit as st
import pandas as pd
from database import save_data, add_log, COLUMNS

def render_tab5(df_asset):
    st.subheader("Upload File Excel / CSV")
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV (.csv)", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            # Baca file upload
            df_upload = pd.read_csv(uploaded_file, dtype=str) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, dtype=str)
            df_upload = df_upload.fillna("").astype(str)

            # Normalisasi Nama Kolom jika ada variasi nama kolom lama
            col_rename = {}
            for c in df_upload.columns:
                c_u = c.strip().upper()
                if c_u in ["NO MOBIL", "DA", "KODE DA"]:
                    col_rename[c] = "DA/No Mobil"
                elif c_u in ["KET SITE", "DEPO", "LOKASI"]:
                    col_rename[c] = "Site"
                elif c_u in ["NAMA DA", "NAMA USER", "NAMA ASP"]:
                    col_rename[c] = "User"
                elif c_u in ["SIM", "NOMOR SIM", "MSISDN"]:
                    col_rename[c] = "SIM Card"
            
            if col_rename:
                df_upload = df_upload.rename(columns=col_rename)

            # Drop kolom yang tidak relevan
            if "Ket Wilayah" in df_upload.columns:
                df_upload = df_upload.drop(columns=["Ket Wilayah"])
                
            # Pastikan semua kolom standar ada
            for col in COLUMNS:
                if col not in df_upload.columns:
                    df_upload[col] = ""
                    
            df_upload = df_upload[COLUMNS].fillna("")
            df_upload["SN_clean"] = df_upload["SN"].astype(str).str.strip().str.upper()
            
            # Buang duplikat di file upload berdasarkan SN
            df_upload = df_upload[df_upload["SN_clean"] != ""].drop_duplicates(subset=["SN_clean"], keep='last')
            
            st.dataframe(df_upload[COLUMNS].head(), use_container_width=True)
            
            if st.button("🚀 Proses Simpan & Update Data (Kilat)", type="primary"):
                with st.spinner("⚡ Memproses update data secara instan..."):
                    df_current = df_asset.copy().fillna("").astype(str)
                    
                    if not df_current.empty and "SN" in df_current.columns:
                        df_current["SN_clean"] = df_current["SN"].astype(str).str.strip().str.upper()
                        
                        # Gabungkan data lama dan baru menggunakan kuncian SN_clean
                        df_current = df_current.set_index("SN_clean")
                        df_upload_indexed = df_upload.set_index("SN_clean")
                        
                        # Hitung data baru vs update
                        new_sns = set(df_upload_indexed.index) - set(df_current.index)
                        update_sns = set(df_upload_indexed.index) & set(df_current.index)
                        
                        count_baru = len(new_sns)
                        count_update = len(update_sns)
                        
                        # Update data yang sudah ada (overwrite dengan data non-empty baru)
                        df_current.update(df_upload_indexed)
                        
                        # Tambahkan data baru yang belum ada
                        if new_sns:
                            df_new_rows = df_upload_indexed.loc[list(new_sns)]
                            df_current = pd.concat([df_current, df_new_rows])
                            
                        # Reset Index
                        df_final = df_current.reset_index(drop=True)[COLUMNS]
                    else:
                        df_final = df_upload[COLUMNS]
                        count_baru = len(df_final)
                        count_update = 0

                    # PENCATATAN BULK LOG ONCE
                    add_log(
                        "BULK UPLOAD", 
                        f"TOTAL {len(df_upload)} ASET", 
                        "SYSTEM", 
                        f"Berhasil memproses upload Excel: {count_baru} Aset Baru, {count_update} Data Diperbarui."
                    )
                    
                    # SINGLE BULK COMMIT KE GITHUB
                    save_data(df_final)
                    
                    st.success(f"""
                    🎉 **PROSES SIMPAN KILAT SELESAI!**
                    - ✅ **{count_baru} Data Aset Baru** ditambahkan.
                    - 🔄 **{count_update} Data Aset** diperbarui.
                    - 💾 **Status Database**: Tersimpan & ter-sync ke GitHub dalam hitungan detik!
                    """)
                    st.balloons()
        except Exception as e:
            st.error(f"Error memproses file upload: {e}")
