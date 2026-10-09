import streamlit as st
import pandas as pd
from database import load_data, load_logs

@st.dialog("🤖 AI Asset Assistant")
def show_ai_dialog():
    st.caption("Tanyakan Serial Number (SN), Nama User, atau detail aset lainnya di sini.")
    
    # Container pesan chat agar ada scrollbar internal
    chat_container = st.container(height=350)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Halo! Ketik **Serial Number (SN)**, Nama User, atau pertanyaan aset untuk saya cari detailnya."}
        ]

    with chat_container:
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

    if user_query := st.chat_input("Tanyakan tentang SN..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        
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
                response += f"- **Ket Wilayah:** {row['Ket Wilayah']}\n"
                if row['Keterangan']:
                    response += f"- **Keterangan:** {row['Keterangan']}\n"
                response += "---\n"
            
            if not match_logs.empty:
                response += f"\n📜 **Riwayat Perubahan Terakhir:**\n"
                for _, log_row in match_logs.head(2).iterrows():
                    response += f"- [{log_row['Waktu_Log']}] **{log_row['Aksi']}**: {log_row['Rincian_Perubahan']}\n"
        else:
            response = f"❌ Tidak ditemukan data aset atau riwayat terkait kata kunci **'{user_query}'**."
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

def render_ai_assistant():
    # Style CSS Khusus Tombol Floating Melayang di Pojok Kiri Bawah
    st.markdown(
        """
        <style>
        div[data-testid="stPopover"], div.element-container:has(button[key="floating_ai_btn"]) {
            position: fixed;
            bottom: 25px;
            left: 25px;
            z-index: 999999;
        }
        button[key="floating_ai_btn"] {
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            background-color: #7C5CFF !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(124, 92, 255, 0.4) !important;
            font-size: 28px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }
        button[key="floating_ai_btn"]:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 6px 16px rgba(124, 92, 255, 0.6) !important;
            background-color: #6942FF !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Tombol Melayang
    if st.button("🤖", key="floating_ai_btn", help="Buka AI Assistant"):
        show_ai_dialog()
