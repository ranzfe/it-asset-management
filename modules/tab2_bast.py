import streamlit as st
import base64
from datetime import datetime
from database import load_data, save_data, add_log

def render_tab2(df_asset):
    st.subheader("📄 Form Tanda Terima Hardware")
    st.caption("Pilih aset, upload logo, isi data penyerahan, cetak dokumen, dan update database otomatis.")
    
    list_sn_st = sorted([sn for sn in df_asset["SN"].unique() if str(sn).strip() != ""])
    col_st1, col_st2 = st.columns([1, 2])
    
    with col_st1:
        st.markdown("##### 🖼️ Upload Logo Perusahaan (Opsional):")
        logo_file = st.file_uploader("Upload Logo Artaboga (.png / .jpg)", type=["png", "jpg", "jpeg"], key="logo_uploader")
        
        logo_html_tag = '<div style="font-size: 22px; font-weight: bold; color: #000; letter-spacing: -1px;">artaboga</div><div style="font-size: 10px; color: #555;">DISTRIBUSI</div>'
        if logo_file is not None:
            base64_logo = base64.b64encode(logo_file.read()).decode()
            mime_type = logo_file.type
            logo_html_tag = f'<img src="data:{mime_type};base64,{base64_logo}" style="max-height: 50px; max-width: 160px; object-fit: contain;" />'

        st.markdown("---")
        st.markdown("##### 📝 Input Data Serah Terima")
        selected_sns = st.multiselect("Pilih SN Hardware:", list_sn_st, key="st_sns")
        
        auto_po = auto_tipe = auto_model = auto_user = auto_site = ""
        if selected_sns:
            r_first = df_asset[df_asset["SN"] == selected_sns[0]].iloc[0]
            auto_po = str(r_first.get("Asal PO", ""))
            auto_tipe = str(r_first.get("Tipe", ""))
            auto_model = str(r_first.get("Model", ""))
            auto_user = str(r_first.get("User", ""))
            auto_site = str(r_first.get("Site", ""))
            
        no_bast = st.text_input("No. BAST / Surat:", value=f"ST/{datetime.now().strftime('%Y%m%d')}/001")
        po_no = st.text_input("PO. No:", value=auto_po)
        tgl_st = st.date_input("Tanggal:", datetime.now())
        
        st.markdown("---")
        telah_diterima = st.text_input("Telah Diterima Dari:", value="FEBRIKA PUJIASMORO - EDP")
        nama_user_st = st.text_input("Nama User Penerima:", value=auto_user)
        jabatan_st = st.text_input("Jabatan / Lokasi Site:", value=auto_site)
        
        st.markdown("---")
        jenis_barang_st = st.text_input("Jenis Barang:", value=f"{auto_tipe} {auto_model}".strip())
        merk_tipe_st = st.text_input("Merk / Tipe:", value=auto_model)
        qty_st = st.number_input("Qty:", min_value=1, value=len(selected_sns) if selected_sns else 1)
        
        st.markdown("---")
        st.markdown("**Data Pelengkap (Checklist):**")
        col_chk1, col_chk2 = st.columns(2)
        with col_chk1:
            chk_baterai = st.checkbox("Baterai", value=True)
            chk_charger = st.checkbox("Charger", value=True)
            chk_tas = st.checkbox("Tas Notebook/Tab", value=True)
        with col_chk2:
            chk_mouse = st.checkbox("Mouse")
            chk_keyboard = st.checkbox("Keyboard")
            chk_kabel = st.checkbox("Kabel Power / USB")
            
        catatan_st = st.text_area("Catatan Tambahan:", value="TAB FOR DA")
        
        st.markdown("---")
        penerima_st = st.text_input("Yang Menerima:", value=nama_user_st)
        pemeriksa_st = st.text_input("Yang Memeriksa:", value="KURIR")
        penyerah_st = st.text_input("Yang Menyerahkan:", value=telah_diterima)
        lokasi_cetak = st.text_input("Kota Cetak:", value="BEKASI")

        if st.button("💾 Simpan & Update Database Aset", type="primary"):
            if selected_sns:
                df_curr = load_data()
                for sn_item in selected_sns:
                    idx_m = df_curr[df_curr["SN"] == sn_item].index
                    if not idx_m.empty:
                        df_curr.loc[idx_m, "User"] = nama_user_st
                        df_curr.loc[idx_m, "Site"] = jabatan_st
                        df_curr.loc[idx_m, "Status"] = "Pakai"
                        add_log("SERAH TERIMA (BAST)", sn_item, nama_user_st, f"Diserahkan ke {nama_user_st} ({jabatan_st}) via BAST {no_bast}")
                save_data(df_curr)
                st.success("✅ **Database Berhasil Di-update!** User & Lokasi Aset diperbarui.")
                st.rerun()
            else:
                st.warning("Pilih minimal 1 SN Hardware.")

    with col_st2:
        st.markdown("##### 🖨️ Pratinjau Dokumen Cetak (Print Preview)")
        sn_list_html = "<br>".join(selected_sns) if selected_sns else "SN-XXXXXX"
        tgl_str = tgl_st.strftime("%d %B %Y").upper()
        
        html_doc = f"""
        <div style="display: flex; flex-direction: column; align-items: center; background: #525659; padding: 10px;">
            <div id="print-area" style="width: 190mm; min-height: 260mm; background-color: white; color: black; padding: 15mm 12mm; box-sizing: border-box; font-family: Arial, sans-serif; font-size: 11px; line-height: 1.3;">
                <table style="width: 100%; border-collapse: collapse; border: none; margin-bottom: 10px;">
                    <tr>
                        <td style="width: 60%; vertical-align: top;">
                            <table style="border: none; font-size: 11px;">
                                <tr><td style="width: 70px;">No</td><td>: {no_bast}</td></tr>
                                <tr><td>PO. No</td><td>: {po_no}</td></tr>
                                <tr><td>Tanggal</td><td>: {tgl_str}</td></tr>
                            </table>
                        </td>
                        <td style="width: 40%; text-align: right; vertical-align: top;">{logo_html_tag}</td>
                    </tr>
                </table>
                <div style="text-align: center; margin: 10px 0 15px 0; font-size: 16px; font-weight: bold; text-decoration: underline;">TANDA TERIMA HARDWARE</div>
                <table style="width: 100%; margin-bottom: 12px; font-size: 11px; border: none;">
                    <tr><td style="width: 120px;">Telah diterima dari</td><td>: {telah_diterima}</td></tr>
                    <tr><td>Nama user</td><td>: {nama_user_st}</td></tr>
                    <tr><td>Jabatan</td><td>: {jabatan_st}</td></tr>
                </table>
                <table style="width: 100%; border-collapse: collapse; border: 1px solid black; text-align: center; font-size: 11px; margin-bottom: 6px;">
                    <thead>
                        <tr style="background-color: #f2f2f2; font-weight: bold;">
                            <th style="border: 1px solid black; padding: 5px; width: 6%;">No</th>
                            <th style="border: 1px solid black; padding: 5px; width: 34%;">Jenis Barang</th>
                            <th style="border: 1px solid black; padding: 5px; width: 25%;">Merk / Tipe</th>
                            <th style="border: 1px solid black; padding: 5px; width: 27%;">SN & HW ID</th>
                            <th style="border: 1px solid black; padding: 5px; width: 8%;">Qty</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="border: 1px solid black; padding: 8px; vertical-align: top;">1.</td>
                            <td style="border: 1px solid black; padding: 8px; vertical-align: top;">{jenis_barang_st}</td>
                            <td style="border: 1px solid black; padding: 8px; vertical-align: top;">{merk_tipe_st}</td>
                            <td style="border: 1px solid black; padding: 8px; vertical-align: top; font-weight: bold;">{sn_list_html}</td>
                            <td style="border: 1px solid black; padding: 8px; vertical-align: top;">{qty_st}</td>
                        </tr>
                    </tbody>
                </table>
                <div style="font-size: 9px; font-style: italic; margin-bottom: 10px;">Item: PC / Notebook / Monitor / UPS / Printer / Tape Drive / LCD Projector / Scanner / Hub / Switch / Print Server / Modem</div>
                <div style="font-weight: bold; font-size: 11px; text-decoration: underline; margin-bottom: 4px;">Data Pelengkap :</div>
                <table style="width: 100%; border-collapse: collapse; border: 1px solid black; font-size: 10px; margin-bottom: 12px;">
                    <tr style="background-color: #f2f2f2; font-weight: bold; text-align: center;">
                        <td style="border: 1px solid black; padding: 3px; width: 28%;">Spesifikasi / merk / tipe / size / driver</td>
                        <td style="border: 1px solid black; padding: 3px; width: 24%;">PC / Notebook</td>
                        <td style="border: 1px solid black; padding: 3px; width: 24%;">Notebook / Tablet</td>
                        <td style="border: 1px solid black; padding: 3px; width: 24%;">Lain-lain</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid black; padding: 5px; vertical-align: top; line-height: 1.4;">-Proc speed<br>-HDD size<br>-Mem size<br>-Password<br>-NIC driver<br>-CD driver<br>-Modem driver</td>
                        <td style="border: 1px solid black; padding: 5px; vertical-align: top; line-height: 1.4;">-NIC [{ '✔' if chk_mouse else ' ' }]<br>-CD/DVD [ ]<br>-Keyboard [{ '✔' if chk_keyboard else ' ' }]<br>-Mouse [{ '✔' if chk_mouse else ' ' }]<br>-Kabel power [{ '✔' if chk_kabel else ' ' }]</td>
                        <td style="border: 1px solid black; padding: 5px; vertical-align: top; line-height: 1.4;">-Baterai [{ '✔' if chk_baterai else ' ' }]<br>-Charger [{ '✔' if chk_charger else ' ' }]<br>-LCD Display [✔]<br>-Tas notebook [{ '✔' if chk_tas else ' ' }]</td>
                        <td style="border: 1px solid black; padding: 5px; vertical-align: top; line-height: 1.4;">Printer:<br>-Kabel power [{ '✔' if chk_kabel else ' ' }]<br>-Kabel USB [{ '✔' if chk_kabel else ' ' }]</td>
                    </tr>
                </table>
                <div style="font-size: 11px; margin-bottom: 25px;"><b>Catatan :</b> <i>{catatan_st}</i></div>
                <table style="width: 100%; border: none; text-align: center; font-size: 11px; margin-top: 15px;">
                    <tr>
                        <td style="width: 33%;">Yang menerima</td>
                        <td style="width: 33%;">Yang memeriksa</td>
                        <td style="width: 33%;">{lokasi_cetak}, {tgl_str}<br>Yang menyerahkan</td>
                    </tr>
                    <tr style="height: 50px;"><td></td><td></td><td></td></tr>
                    <tr>
                        <td><b>( {penerima_st} )</b></td>
                        <td><b>( {pemeriksa_st} )</b></td>
                        <td><b>( {penyerah_st} )</b></td>
                    </tr>
                </table>
            </div>
            <br>
            <button onclick="window.print()" style="background-color: #008CBA; color: white; padding: 10px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold;">
                🖨️ Cetak / Simpan PDF Dokumen Ini
            </button>
        </div>
        <style>
            @media print {{
                @page {{ size: A4 portrait; margin: 0; }}
                body {{ background: white !important; margin: 0 !important; padding: 0 !important; }}
                body * {{ visibility: hidden; }}
                #print-area, #print-area * {{ visibility: visible; }}
                #print-area {{ position: absolute; left: 0; top: 0; width: 210mm !important; min-height: 297mm !important; padding: 15mm !important; box-shadow: none !important; border: none !important; }}
                button {{ display: none !important; }}
            }}
        </style>
        """
        st.components.v1.html(html_doc, height=800, scrolling=True)
