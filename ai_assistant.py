import streamlit as st
import pandas as pd
from database import load_data, load_logs

@st.dialog("🤖 ITAM AI Assistant")
def show_ai_dialog():
    st.caption("Tanyakan Serial Number (SN), Nama User, Site, atau detail aset IT lainnya di sini.")
    
    chat_container = st.container(height=350)
    
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = [
            {"role": "assistant", "content": "Halo! Ketik **Serial Number (SN)** atau nama User untuk mencari detail aset secara cepat."}
        ]

    with chat_container:
        for msg in st.session_state.ai_messages:
            st.chat_message(msg["role"]).write(msg["content"])

    if user_query := st.chat_input("Ketik pertanyaan atau SN Anda..."):
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

def render_ai_assistant():
    # 1. Tombol Tersembunyi Streamlit untuk memicu Modal AI
    if st.button("TRIGGER_AI", key="hidden_ai_trigger"):
        show_ai_dialog()

    # 2. Inject CSS & JS untuk menyembunyikan tombol asli dan membuat Floating Button Murni
    st.markdown(
        """
        <style>
        /* Sembunyikan tombol trigger bawaan Streamlit */
        div.stButtonHasFocus > button[key="hidden_ai_trigger"],
        .element-container:has(button[key="hidden_ai_trigger"]) {
            display: none !important;
            height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        /* Tombol Bulat Melayang Murni di Pojok Kiri Bawah */
        #custom-floating-ai-btn {
            position: fixed !important;
            bottom: 30px !important;
            left: 30px !important;
            width: 65px !important;
            height: 65px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #7C5CFF 0%, #5E35B1 100%) !important;
            color: white !important;
            border: 2px solid rgba(255, 255, 255, 0.4) !important;
            box-shadow: 0 8px 25px rgba(124, 92, 255, 0.7) !important;
            font-size: 32px !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 99999999 !important;
            transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            user-select: none !important;
        }

        #custom-floating-ai-btn:hover {
            transform: scale(1.15) rotate(8deg) !important;
            box-shadow: 0 12px 32px rgba(124, 92, 255, 0.9) !important;
            background: linear-gradient(135deg, #8A6CFF 0%, #6A3DE8 100%) !important;
        }
        </style>

        <!-- HTML Floating Button -->
        <div id="custom-floating-ai-btn" title="Buka AI Assistant" onclick="triggerAiClick()">🤖</div>

        <script>
        function triggerAiClick() {
            // Mencari tombol trigger asli dan menstimulasi klik
            var buttons = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].innerText.includes('TRIGGER_AI')) {
                    buttons[i].click();
                    break;
                }
            }
        }
        </script>
        """,
        unsafe_allow_html=True
    )
