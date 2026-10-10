import streamlit as st
import json
import os
from database import load_data, commit_to_github
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
from modules.tab9_mutasi import render_tab9

CONFIG_FILE = "admin_config.json"
DEFAULT_PIN = "1234"

def get_admin_pin():
    """Membaca PIN Admin dari file konfigurasi"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("admin_pin", DEFAULT_PIN)
        except Exception:
            return DEFAULT_PIN
    return DEFAULT_PIN

def save_admin_pin(new_pin):
    """Menyimpan PIN Admin baru ke file konfigurasi & sync ke GitHub"""
    with open(CONFIG_FILE, "w") as f:
        json.dump({"admin_pin": new_pin}, f)
    commit_to_github(CONFIG_FILE, "Update Admin PIN")

# Konfigurasi Halaman Web
st.set_page_config(page_title="IT Asset Management System", page_icon="💻", layout="wide")

# Muat Data Utama
df_asset = load_data()

# Inisialisasi Session State Login
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

current_pin = get_admin_pin()

# --- SIDEBAR ACCESS CONTROL ---
st.sidebar.title("🔐 Login Administrator")

if not st.session_state["admin_logged_in"]:
    st.sidebar.info("💡 Mode PIC (Akses Terbatas: Hanya Form Mutasi)")
    pin_input = st.sidebar.text_input("Masukkan PIN Admin / EDP:", type="password", key="login_pin_input")
    
    if st.sidebar.button("🔓 Login Admin"):
        if pin_input == current_pin:
            st.session_state["admin_logged_in"] = True
            st.sidebar.success("🔑 Login Berhasil!")
            st.rerun()
        else:
            st.sidebar.error("❌ PIN Salah!")
else:
    st.sidebar.success("✅ Terverifikasi sebagai Admin / IT EDP")
    
    # TOMBOL KELUAR MODE ADMIN
    if st.sidebar.button("🔒 Keluar Mode Admin"):
        st.session_state["admin_logged_in"] = False
        st.rerun()

    st.sidebar.markdown("---")
    
    # MENU UBAH PIN ADMIN DITAMPILKAN SECARA EKSPLISIT
    st.sidebar.subheader("⚙️ Pengaturan Akses")
    with st.sidebar.expander("🔑 Ubah PIN Admin", expanded=False):
        with st.form("form_change_pin", clear_on_submit=True):
            old_pin = st.text_input("PIN Lama*:", type="password")
            new_pin = st.text_input("PIN Baru*:", type="password")
            confirm_pin = st.text_input("Konfirmasi PIN Baru*:", type="password")
            
            btn_change_pin = st.form_submit_button("💾 Simpan PIN Baru")
            
            if btn_change_pin:
                if old_pin != current_pin:
                    st.error("❌ PIN Lama Salah!")
                elif new_pin.strip() == "":
                    st.error("❌ PIN Baru Tidak Boleh Kosong!")
                elif new_pin != confirm_pin:
                    st.error("❌ Konfirmasi PIN Baru Tidak Cocok!")
                else:
                    save_admin_pin(new_pin)
                    st.success("🎉 PIN Admin Berhasil Diperbarui!")

    st.sidebar.markdown("---")

# --- TAMPILAN SESUAI HAK AKSES ---
if not st.session_state["admin_logged_in"]:
    # Mode PIC / User Field (Hanya Form Mutasi)
    st.title("💻 IT Asset Management - Form Mutasi Aset")
    st.info("💡 Anda berada di Mode PIC (Hanya Pengisian Mutasi Aset). Masukkan PIN Admin di sidebar untuk membuka semua menu.")
    st.markdown("---")
    render_tab9(df_asset)

else:
    # Mode Full Admin / IT EDP
    st.title("💻 IT Asset Management System (Admin Mode)")
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

    # Tab Menu Utama Admin
    tab1, tab2, tab9, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 Daftar, Sort & Filter Aset", 
        "📄 Serah Terima Hardware (BAST)",
        "🔄 Form Mutasi Aset",
        "📊 Analytics & Grafik",
        "✏️ Edit & Hapus Aset",
        "📤 Upload Excel/CSV", 
        "➕ Tambah Manual",
        "📜 Log History",
        "📱 Plotting Tagihan Simcard"
    ])

    with tab1:
        render_tab1(df_asset)

    with tab2:
        render_tab2(df_asset)

    with tab9:
        render_tab9(df_asset)

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

    # RENDER AI ASSISTANT DI BAGIAN PALING BAWAH SIDEBAR
    render_ai_assistant()
