import streamlit as st
from database import load_data
from ai_assistant import render_ai_assistant

# Import Modul Per-Tab
from modules.tab1_daftar import render_tab1
from modules.tab2_bast import render_tab2
from modules.tab3_analytics import render_tab3
from modules.tab4_edit import render_tab4
from modules.tab5_upload import render_tab5
from modules.tab6_manual import render_tab6
from modules.tab7_logs import render_tab7
from modules.tab8_plotting import render_tab8

# Konfigurasi Halaman Web
st.set_page_config(page_title="IT Asset Management", page_icon="💻", layout="wide")

# Muat Data Utama
df_asset = load_data()

# --- HEADER & DASHBOARD METRICS ---
st.title("💻 IT Asset Management System")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
total_asset = len(df_asset)
pakai_count = len(df_asset[df_asset["Status"].str.upper() == "PAKAI"]) if not df_asset.empty else 0
rusak_count = len(df_asset[df_asset["Status"].str.upper() == "RUSAK"]) if not df_asset.empty else 0
hilang_count = len(df_asset[df_asset["Status"].str.upper() == "HILANG"]) if not df_asset.empty else 0
jual_count = len(df_asset[df_asset["Status"].str.upper() == "JUAL"]) if not df_asset.empty else 0

col1.metric("Total Aset", total_asset)
col2.metric("Pakai", pakai_count)
col3.metric("Rusak", rusak_count)
col4.metric("Hilang", hilang_count)
col5.metric("Jual", jual_count)
st.markdown("---")

# --- TAB MENU UTAMA ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📋 Daftar, Sort & Filter Aset", 
    "📄 Serah Terima Hardware (BAST)",
    "📊 Analytics & Grafik",
    "✏️ Edit & Hapus Aset",
    "📤 Upload Excel/CSV", 
    "➕ Tambah Manual",
    "📜 Log History",
    "📱 Plotting Tagihan Simcard"
])

# RENDER MASING-MASING TAB DARI MODUL TERPISAH
with tab1:
    render_tab1(df_asset)

with tab2:
    render_tab2(df_asset)

with tab3:
    render_tab3(df_asset)

with tab4:
    render_tab4(df_asset)

with tab5:
    render_tab5(df_asset)

with tab6:
    render_tab6(df_asset)

with tab7:
    render_tab7()

with tab8:
    render_tab8(df_asset)

# RENDER AI ASSISTANT SIDEBAR
render_ai_assistant()
