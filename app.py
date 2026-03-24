import streamlit as st

# Sayfa ayarları
st.set_page_config(page_title="TeknoRapor | Bilgilendirme", page_icon="🚫")

# Karşılama Mesajı
st.markdown(f"""
    <div style="text-align: center; padding: 100px 20px;">
        <h1 style="color: #1E3A8A; font-family: Arial;">🤖 TeknoRapor V53</h1>
        <hr style="border: 1px solid #eee;">
        <br>
        <h2 style="color: #D32F2F; font-family: Arial;">Sistem yoğunluğu nedeniyle kapanmıştır.</h2>
        <p style="font-size: 22px; color: #555; font-family: Arial;">Başka bir çalışmada görüşmek üzere.</p>
        <br><br>
        <p style="color: gray; font-family: Arial;">Derepazarı İlçe MEM Arge Birimi © 2026</p>
    </div>
""", unsafe_allow_html=True)
