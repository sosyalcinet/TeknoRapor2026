import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE ANAHTARLAR (KASADAN ALINIYOR) ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except Exception as e:
    st.error("Kasa (Secrets) ayarları eksik! Lütfen Streamlit Dashboard'dan Secrets kısmını kontrol edin.")
    st.stop()

# Google Sheets Bağlantısı
def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except:
        return None

# --- 2. SAYFA TASARIMI ---
st.set_page_config(page_title="TeknoRapor Asistanı Derepazarı", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Asistanı Derepazarı</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>İlçe Milli Eğitim Müdürlüğü | Arge Birimi 2026</p>", unsafe_allow_html=True)

# Form Alanları
seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise"])
proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
ham_fikir = st.text_area("Projenizin ana fikri nedir?", height=150)
insan_dokunusu = st.text_area("Kişisel Gözlem (Özgünlük Hikayesi)", height=100)

# --- 3. RAPOR OLUŞTURMA VE PAYLAŞMA ---
if st.button("Teknofest Standartlarında Raporu Hazırla"):
    if not ham_fikir or not proje_adi:
        st.error("Lütfen gerekli alanları doldurun!")
    else:
        with st.spinner("Yapay zeka modelleri taranıyor ve rapor hazırlanıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                
                # --- AKILLI MODEL SEÇİCİ (404 HATASINI ÖNLEYEN KISIM) ---
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                # En güncel modeli bulmaya çalış, bulamazsa en stabil olanı seç
                model_name = next((m for m in available_models if "flash" in m), available_models[0])
                
                model = genai.GenerativeModel(model_name)
                
                prompt = f"""
                Sen bir Teknofest rapor uzmanısın. {seviye} seviyesi için akademik dille ÖDR yaz.
                KURALLAR: 150-250 kelime özet, Arial 12 ve 1.15 aralık yapısı.
                İçerik: {proje_adi} projesini '{ham_fikir}' ve '{insan_dokunusu}' üzerinden detaylandır.
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                # Başarı mesajı ve raporu göster
                st.success(f"Rapor Hazır! (Kullanılan Model: {model_name})")
                st.markdown("---")
                st.markdown(rapor_metni)
                
                # Paylaşım Butonları
                st.markdown("### 📤 Paylaş ve Gönder")
                paylas_metni = urllib.parse.quote(f"TeknoRapor Asistanı Çıktısı:\n\n{rapor_metni}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"[![WhatsApp](https://img.shields.io/badge/WhatsApp-Paylaş-25D366?style=for-the-badge&logo=whatsapp)](https://wa.me/?text={paylas_metni})")
                with col2:
                    st.markdown(f"[![Telegram](https://img.shields.io/badge/Telegram-Paylaş-26A5E4?style=for-the-badge&logo=telegram)](https://t.me/share/url?url=TeknoRapor&text={paylas_metni})")
                with col3:
                    st.markdown(f"[![Email](https://img.shields.io/badge/Email-Gönder-D14836?style=for-the-badge&logo=gmail)](mailto:?subject={proje_adi}&body={paylas_metni})")
                
                # Sheets Kaydı (Arka Planda)
                sheet = connect_sheets()
                if sheet:
                    sheet.append_row([str(datetime.now()), seviye, proje_adi, rapor_metni])

            except Exception as e:
                st.error(f"Teknik bir sorun oluştu: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.8em;'>Derepazarı İlçe MEM Arge Birimi 2026</p>", unsafe_allow_html=True)
