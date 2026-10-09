import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, load_logs

def render_ai_assistant():
    with st.sidebar:
        st.title("🤖 AI Asset Assistant")
        st.caption("Tanyakan Serial Number (SN) atau data aset di sini.")
        st.markdown("---")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Halo! Ketik **Serial Number (SN)**, Nama User, atau pertanyaan aset untuk saya cari detailnya."}
            ]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if user_query := st.chat_input("Tanyakan tentang SN..."):
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            
            df_asset = load_data()
            df_logs = load_logs()
            query_clean = user_query.strip().upper()
            
            match_asset = pd.DataFrame()
            if not df_asset.empty and "SN" in df_asset.columns:
                mask = df_asset.apply(lambda row: row.astype(str).str.contains(query_clean, case=False).any(), axis=1)
                match_asset = df_asset[mask]
            
            match_logs = pd.DataFrame()
            if not df_logs.empty:
                mask_log = df_logs.apply(lambda row: row.astype(str).str.contains(query_clean, case=False).any(), axis=1)
                match_logs = df_logs[mask_log]
            
            if not match_asset.empty:
                response = f"🔍 **Ditemukan {len(match_asset)} data aset terkait '{user_query}':**\n\n"
                for _, row in match_asset.head(3).iterrows():
                    response += f"📌 **SN:** `{row['SN']}`\n"
                    response += f"- **Tipe/Model:** {row['Tipe']} {row['Model']}\n"
                    response += f"- **User:** {row['User']} (NIK: {row['NIK']})\n"
                    response += f"- **Status:** `{row['Status']}` | **Site:** {row['Site']} ({row['Kd Site']})\n"
                    
                    # Hitung Usia & Rekomendasi Peremajaan
                    p_date_str = str(row.get('Purchase Date', '')).strip()
                    if p_date_str and p_date_str.lower() != 'nan':
                        try:
                            p_date = datetime.strptime(p_date_str[:10], "%Y-%m-%d")
                            years = (datetime.now() - p_date).days / 365.25
                            response += f"- **Tanggal Beli:** {p_date_str[:10]} ({years:.1f} tahun)\n"
                            if years >= 3.0:
                                response += f"- ⚠️ **Status Usia:** *Sudah > 3 tahun (Direkomendasikan Peremajaan)*\n"
                        except:
                            response += f"- **Tanggal Beli:** {p_date_str}\n"
                    
                    # Cek Link Foto
                    link_foto = str(row.get('Link Foto Asset', '')).strip()
                    if link_foto and link_foto.lower() != 'nan':
                        response += f"- **Link Foto:** [🖼️ Lihat Foto Google Drive]({link_foto})\n"
                        
                    if row.get('Keterangan'):
                        response += f"- **Keterangan:** {row['Keterangan']}\n"
                    response += "---\n"
                
                if not match_logs.empty:
                    response += f"\n📜 **Riwayat Perubahan Terakhir:**\n"
                    for _, log_row in match_logs.head(2).iterrows():
                        response += f"- [{log_row['Waktu_Log']}] **{log_row['Aksi']}**: {log_row['Rincian_Perubahan']}\n"
            else:
                response = f"❌ Tidak ditemukan data aset atau riwayat terkait kata kunci **'{user_query}'**."
                
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
