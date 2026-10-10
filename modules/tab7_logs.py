import streamlit as st
from database import load_logs

def render_tab7():
    st.subheader("📜 Riwayat & Log Perubahan Data Aset")
    df_logs = load_logs()
    if not df_logs.empty:
        search_log = st.text_input("🔍 Cari di Log History:", "")
        if search_log:
            mask_log = df_logs.apply(lambda row: row.astype(str).str.contains(search_log, case=False).any(), axis=1)
            df_logs = df_logs[mask_log]
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada riwayat aktivitas.")
