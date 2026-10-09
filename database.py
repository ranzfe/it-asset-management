import os
import pandas as pd
import base64
import requests
from datetime import datetime
import streamlit as st

DB_FILE = "database_asset.csv"
LOG_FILE = "history_log.csv"

COLUMNS = [
    "SN", "Tipe", "Model", "Purchase Date", "Status Beli", "Asal PO",
    "Status", "NIK", "User", "Kd Site", "Site", "No Mobil",
    "SIM Card", "Imei", "Link Foto Asset", "Keterangan"
]

LOG_COLUMNS = ["Waktu_Log", "Aksi", "SN", "User_Terkait", "Rincian_Perubahan"]
STATUS_OPTIONS = ["Pakai", "Rusak", "Hilang", "Jual", "Cadangan", "Cek"]

# --- FUNGSI SYNC DENGAN GITHUB API ---
def commit_to_github(file_path, df_content, commit_message="Auto-update dataset from Streamlit"):
    """Mengunggah & mengommit perubahan file CSV langsung ke repository GitHub"""
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    
    if not token or not repo:
        # Jika Secrets belum dikonfigurasi, simpan secara lokal saja
        df_content.to_csv(file_path, index=False)
        return

    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {"Authorization": f"token {token}"}
    
    # Ambil SHA file lama jika sudah ada di GitHub
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    # Convert DataFrame ke CSV base64
    csv_bytes = df_content.to_csv(index=False).encode("utf-8")
    content_b64 = base64.b64encode(csv_bytes).decode("utf-8")
    
    data = {
        "message": commit_message,
        "content": content_b64
    }
    if sha:
        data["sha"] = sha
        
    # Kirim perubahan ke GitHub
    requests.put(url, headers=headers, json=data)
    # Simpan juga secara lokal di server
    df_content.to_csv(file_path, index=False)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)
        if "Ket Wilayah" in df.columns:
            df = df.drop(columns=["Ket Wilayah"])
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS].fillna("")
    return pd.DataFrame(columns=COLUMNS)

def load_logs():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE, dtype=str)
        for col in LOG_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[LOG_COLUMNS].fillna("")
    return pd.DataFrame(columns=LOG_COLUMNS)

def save_data(df):
    commit_to_github(DB_FILE, df[COLUMNS], commit_message="Update database_asset.csv via ITAM App")

def add_log(aksi, sn, user_terkait, rincian):
    df_logs = load_logs()
    waktu_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = {
        "Waktu_Log": waktu_now,
        "Aksi": aksi,
        "SN": sn,
        "User_Terkait": user_terkait,
        "Rincian_Perubahan": rincian
    }
    df_updated_log = pd.concat([pd.DataFrame([new_log]), df_logs], ignore_index=True)
    commit_to_github(LOG_FILE, df_updated_log[LOG_COLUMNS], commit_message=f"Log Activity: {aksi} SN {sn}")
