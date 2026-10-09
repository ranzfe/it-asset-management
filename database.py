import os
import pandas as pd
from datetime import datetime

DB_FILE = "database_asset.csv"
LOG_FILE = "history_log.csv"

COLUMNS = [
    "Ket Wilayah", "SN", "Tipe", "Model", "Status Beli", "Asal PO",
    "Status", "NIK", "User", "Kd Site", "Site", "No Mobil",
    "SIM Card", "Imei", "Keterangan"
]

LOG_COLUMNS = ["Waktu_Log", "Aksi", "SN", "User_Terkait", "Rincian_Perubahan"]
STATUS_OPTIONS = ["Pakai", "Rusak", "Hilang", "Jual", "Cadangan", "Cek"]

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)
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
    df[COLUMNS].to_csv(DB_FILE, index=False)

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
    df_updated_log.to_csv(LOG_FILE, index=False)
