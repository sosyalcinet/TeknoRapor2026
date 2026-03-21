import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from datetime import datetime

# --- KİMLİK BİLGİLERİ ---
GEMINI_API_KEY = "AIzaSyAE8lRdc5kvG2Bu-DbNNdrtqbO-CUrb7WM" 
SHEET_ID = "1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4"
JSON_FILE = "teknorapor2026-75e526daaee5.json"

# --- SAYFA TASARIMI ---
st.set_page_config(page_title="TeknoRapor Asistanı Derepazarı", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Asistanı Derepazarı</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>İlçe Milli Eğitim Müdürlüğü | Arge Birimi 2026</h3>", unsafe_allow_html=True)

# Proje Bilgileri
seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise"])
proje_adi = st.text_input("Proje Adı", value="BULUT KUMBARASI: Gökten İnen Bereket")
ham_fikir = st.text_area("Projenizin ana fikri nedir?", value="Rize'nin yağmurlarını depolayıp bahçelerde kullanan akıllı bir kumbara sistemi.")
insan_dokunusu = st.text_area("Kişisel Gözlem", value="Rize merkezde su kesintileri ve yağmurun israfı bu fikri doğurdu.")

if st.button("Raporu Hemen Hazırla"):
    with st.spinner("Sistem hesabınızdaki en uygun modeli (Gemini 3 veya 1.5) seçiyor..."):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # --- MODELİ OTOMATİK BULAN SİHİRLİ KISIM ---
            model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Listeden en güncel olanı (genellikle ilk sıradakini) seçer
            active_model_name = model_list[0] if model_list else "models/gemini-1.5-flash"
            
            model = genai.GenerativeModel(active_model_name)
            
            prompt = f"""
            Sen bir Teknofest uzmanısın. {seviye} seviyesi için akademik dille ÖDR yaz.
            KURALLAR:
            1. Proje Özeti: Kesinlikle 150-250 kelime arasında olmalı.
            2. Yazı Tipi: Arial 12 ve 1.15 satır aralığına uygun kurgula.
            3. Bölümler: Özet, Problem Tanımı, Çözüm Önerisi, Özgün Değer, Uygulanabilirlik.
            4. İçerik: {proje_adi} projesini {ham_fikir} ve '{insan_dokunusu}' üzerinden detaylandır.
            """
            
            response = model.generate_content(prompt)
            st.success(f"Başarı! ({active_model_name} modeliyle rapor üretildi)")
            st.markdown("### 📄 Raporunuz Hazır")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"Teknik bir sorun: {str(e)}. Lütfen API anahtarınızı AI Studio'dan tekrar kontrol edin.")

st.markdown("---")
st.markdown("<p style='text-align: center;'>Derepazarı İlçe MEM Arge Birimi 2026 | <a href='https://wa.me/905062840001'>WhatsApp</a></p>", unsafe_allow_html=True)