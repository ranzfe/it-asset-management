import streamlit as st
import pandas as pd
from database import load_data, load_logs

def render_ai_assistant():
    # CSS Khusus untuk Memaksa Tombol & Popup Mengapung Selalu di Pojok Kiri Bawah
    st.markdown(
        """
        <style>
        /* Mengubah container popover menjadi Floating Overlay Fixed di Pojok Kiri Bawah */
        div[data-testid="stPopover"] {
            position: fixed !important;
            bottom: 25px !important;
            left: 25px !important;
            z-index: 9999999 !important;
        }

        /* Desain Tombol Bulat Melayang warna Ungu dengan Ikon Robot 🤖 */
        div[data-testid="stPopover"] > button {
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #7C5CFF 0%, #5E35B1 100%) !important;
            color: white !important;
            border: 2px solid #ffffff33 !important;
            box-shadow: 0 8px 20px rgba(124, 92, 255, 0.6) !important;
            font-size: 30px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        div[data-testid="stPopover"] > button:hover {
            transform: scale(1.12) rotate(5deg) !important;
            box-shadow: 0 10px 28px rgba(124, 92, 255, 0.8) !important;
            background: linear-gradient(135deg, #8A6CFF 0%, #6A3DE8 100%) !important;
        }

        /* Container Jendela Chat AI */
        div[data-testid="stPopoverBody"] {
            width: 380px !important;
            max-width: 90vw !important;
            border-radius: 16px !important;
            background-color: #12141D !important;
            border: 1px solid #7C5CFF !important;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6) !important;
            padding: 16px !important;
            position: fixed !important;
            bottom: 95px !important;
            left: 25px !important;
        }

        .ai-title-bar {
            background: linear-gradient(90deg, #7C5CFF 0%, #5E35B1 100%);
            padding: 10px 14px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Menampilkan Popover Floating Button
    with st.popover("🤖", help="Buka AI Assistant"):
        st.markdown('<div class="ai-title-bar">🤖 <span>ITAM AI Assistant</span></div>', unsafe_allow_html=True)
        st.caption("Tanyakan Serial Number (SN), Nama User, atau detail aset IT di sini.")
        
        chat_container = st.container(height=320)
        
        if "ai_messages" not in st.session_state:
            st.session_state.ai_messages = [
                {"role": "assistant", "content": "Halo! Ketik **Serial Number (SN)** atau nama User untuk mencari detail aset secara cepat."}
            ]

        with chat_container:
            for msg in st.session_state.ai_messages:
                st.chat_message(msg["role"]).write(msg["content"])

        if user_query := st.chat_input("Ketik pertanyaan Anda..."):
            st.session_state.ai_messages.append({"role": "user", "content": user_query})
            
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
                    response += f"- **Status:** `{row['Status']}` | **Site:** {row['Site']}\n"
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
                
            st.session_state.ai_messages.append({"role": "assistant", "content": response})
            st.rerun()
