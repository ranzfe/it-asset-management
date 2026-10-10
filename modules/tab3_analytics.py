import streamlit as st

def render_tab3(df_asset):
    st.subheader("📊 Analisis & Distribusi Aset IT")
    if not df_asset.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### Jumlah Aset Berdasarkan Status")
            st.bar_chart(df_asset["Status"].value_counts())
        with col_g2:
            st.markdown("##### Jumlah Aset Berdasarkan Tipe Perangkat")
            st.bar_chart(df_asset["Tipe"].value_counts().head(10))
            
        st.markdown("---")
        st.markdown("##### Top 10 Site/Lokasi dengan Aset Terbanyak")
        st.bar_chart(df_asset["Site"].value_counts().head(10))
    else:
        st.info("Belum ada data untuk grafik analisis.")
