import streamlit as st
import pandas as pd
import os
from datetime import datetime
from github import Github

# Konfigurasi Nama File
DATA_FILE = "database_asset.csv"
LOG_FILE = "history_log.csv"

# HEADER DENGAN "DA/No Mobil" BARU (RAPIH)
COLUMNS = [
    "SN", "Tipe", "Model", "Purchase Date", "Status Beli", 
    "Asal PO", "Status", "NIK", "User", "Kd Site", 
    "Site", "DA/No Mobil", "SIM Card", "Imei", "Link Foto Asset", "Keterangan"
]

STATUS_OPTIONS = ["Pakai", "Cadangan", "Rusak", "Hilang", "Jual"]

def commit_to_github(file_path, commit_message):
    """Fungsi otomatis menyimpan file CSV balik ke Repository GitHub"""
    try:
        github_token = st.secrets.get("GITHUB_TOKEN")
        repo_name = st.secrets.get("REPO_NAME")
        
        if github_token and repo_name:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            try:
                contents = repo.get_contents(file_path)
                repo.update_file(contents.path, commit_message, content, contents.sha)
            except Exception:
                repo.create_file(file_path, commit_message, content)
    except Exception as e:
        print(f"Bypass auto-commit GitHub: {e}")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype=str).fillna("")
            
            # MAPPING OTOMATIS JIKA MASIH PAKAI NAMA KOLOM LAMA "No Mobil"
            if "No Mobil" in df.columns and "DA/No Mobil" not in df.columns:
                df["DA/No Mobil"] = df["No Mobil"]
            elif "DA" in df.columns and "DA/No Mobil" not in df.columns:
                df["DA/No Mobil"] = df["DA"]

            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df_clean = df.fillna("").astype(str)
    
    # Mapping otomatis jika ada input nama lama
    if "No Mobil" in df_clean.columns and "DA/No Mobil" not in df_clean.columns:
        df_clean["DA/No Mobil"] = df_clean["No Mobil"]

    for col in COLUMNS:
        if col not in df_clean.columns:
            df_clean[col] = ""
            
    df_clean.to_csv(DATA_FILE, index=False)
    commit_to_github(DATA_FILE, f"Auto-update asset data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def load_logs():
    if os.path.exists(LOG_FILE):
        try:
            return pd.read_csv(LOG_FILE, dtype=str).fillna("")
        except Exception:
            return pd.DataFrame(columns=["TIMESTAMP", "ACTION", "SN", "USER", "DETAILS"])
    return pd.DataFrame(columns=["TIMESTAMP", "ACTION", "SN", "USER", "DETAILS"])

def add_log(action, sn, user, details):
    logs = load_logs()
    new_log = {
        "TIMESTAMP": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ACTION": action,
        "SN": sn,
        "USER": user,
        "DETAILS": details
    }
    updated_logs = pd.concat([pd.DataFrame([new_log]), logs], ignore_index=True)
    updated_logs.to_csv(LOG_FILE, index=False)
    commit_to_github(LOG_FILE, f"Auto-update history log: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
