import streamlit as st
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- GÜVENLİK VE AYARLAR ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- ARAYÜZ ---
st.set_page_config(page_title="TeknoRapor Asistanı Derepazarı", layout="centered")

st.markdown("<h1 style='text-align: center;'>🚀 TeknoRapor Asistanı Derepazarı</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: gray;'>İlçe Milli Eğitim Müdürlüğü | Arge Birimi 2026</h3>", unsafe_allow_html=True)

# Formu Sıfırlama Fonksiyonu (Tekrar Hazırla için)
if 'rapor_hazir' not in st.session_state:
    st.session_state.rapor_hazir = False
    st.session_state.rapor_metni = ""

# Giriş Alanları
seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise"])
proje_adi = st.text_input("Proje Adı")
ham_fikir = st.text_area("Projenizin ana fikri nedir?")
insan_dokunusu = st.text_area("Kişisel Gözleminiz")

col1, col2 = st.columns(2)

with col1:
    if st.button("Raporu Hazırla"):
        if not ham_fikir or not proje_adi:
            st.error("Lütfen alanları doldurun.")
        else:
            with st.spinner("Rapor oluşturuluyor..."):
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Sen bir Teknofest uzmanısın. {seviye} seviyesi için ÖDR yaz.
                KURALLAR: 150-250 kelime özet, Arial 12 ve 1.15 aralık yapısı.
                İçerik: {proje_adi} - {ham_fikir}. Özgünlük hikayesi: {insan_dokunusu}.
                """
                
                response = model.generate_content(prompt)
                st.session_state.rapor_metni = response.text
                st.session_state.rapor_hazir = True

with col2:
    if st.button("Formu Temizle (Yeniden Başla)"):
        st.session_state.rapor_hazir = False
        st.session_state.rapor_metni = ""
        st.rerun()

# --- RAPOR HAZIRLANDIKTAN SONRA ÇIKACAK SEÇENEKLER ---
if st.session_state.rapor_hazir:
    st.markdown("---")
    st.success("✅ Raporunuz Başarıyla Hazırlandı!")
    st.text_area("Hazırlanan Metin (Buradan kopyalayabilirsiniz):", st.session_state.rapor_metni, height=300)

    st.markdown("### 📤 Raporu Paylaş veya Gönder")
    
    # Paylaşım metnini internet adresine uygun hale getirme
    paylasim_metni = urllib.parse.quote(f"TeknoRapor Asistanı ile hazırladığım rapor:\n\n{st.session_state.rapor_metni}")

    c1, c2, c3 = st.columns(3)
    
    with c1:
        # WhatsApp Paylaş
        wa_link = f"https://wa.me/?text={paylasim_metni}"
        st.markdown(f"[![WhatsApp](https://img.shields.io/badge/WhatsApp-Paylaş-25D366?style=for-the-badge&logo=whatsapp)]({wa_link})")

    with c2:
        # Telegram Paylaş
        tg_link = f"https://t.me/share/url?url=TeknoRapor&text={paylasim_metni}"
        st.markdown(f"[![Telegram](https://img.shields.io/badge/Telegram-Paylaş-26A5E4?style=for-the-badge&logo=telegram)]({tg_link})")

    with c3:
        # E-posta için hazır link (Mailto)
        mail_link = f"mailto:?subject={proje_adi} Raporu&body={paylasim_metni}"
        st.markdown(f"[![Email](https://img.shields.io/badge/E--Posta-Gönder-D14836?style=for-the-badge&logo=gmail)]({mail_link})")

# Footer
st.markdown("---")
st.markdown(f"<p style='text-align: center;'>Derepazarı İlçe MEM Arge Birimi 2026<br>Destek: +905062840001</p>", unsafe_allow_html=True)
