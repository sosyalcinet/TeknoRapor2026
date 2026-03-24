import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from io import BytesIO
from datetime import datetime

# --- 1. GÜVENLİK VE AYARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Kasa (Secrets) ayarları bulunamadı! Lütfen Adım 1 ve 2'yi yapın.")
    st.stop()

st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- YARDIMCI FONKSİYONLAR ---
def format_temizle(text):
    temiz = text.replace("**", "").replace("##", "").replace("#", "")
    harita = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u'}
    for k, v in harita.items(): temiz = temiz.replace(k, v)
    return temiz.encode('latin-1', 'replace').decode('latin-1')

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=format_temizle(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=format_temizle(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text.replace("**", "").replace("##", ""))
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Robotu V1</h1>", unsafe_allow_html=True)

with st.expander("📝 Rapor Bilgileri (Resmi Taslak)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        proje_adi = st.text_input("Proje Adı")
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    with col2:
        danisman = st.text_input("Danışman Adı (Doldurulması Zorunludur)")
        takim = st.text_input("Takım Adı")
    
    aciklama = st.text_area("Proje Özeti ve Fikriniz", height=150)
    hedef_sayfa = st.slider("Rapor Sayfa Sayısı", 1, 6, 3)

    if st.button("🚀 Raporu Hazırla", use_container_width=True, type="primary"):
        with st.status("🛠️ Raporunuz yazılıyor...", expanded=True):
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Teknofest danışmanısın. {proje_adi} projesi için {hedef_sayfa} sayfalık rapor yaz.
            Markdown (**, #) kullanma. 
            
            RAPORUN EN BAŞINA ŞUNLARI BOLD (KALIN) OLARAK YAZ:
            PROJE ADI: {proje_adi}
            DANIŞMAN: {danisman}
            TAKIM: {takim}
            ---
            İçerik: {aciklama}
            """
            response = model.generate_content(prompt)
            st.session_state.rapor = response.text
            st.session_state.hazir = True

# --- ÇIKTILAR ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"### 📄 {proje_adi} - Rapor Önizleme")
    st.text_area("", st.session_state.rapor, height=300)
    
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 PDF İndir", create_pdf(st.session_state.rapor, proje_adi), f"{proje_adi}.pdf", use_container_width=True)
    with c2:
        st.download_button("📥 Word İndir", create_word(st.session_state.rapor, proje_adi), f"{proje_adi}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026 | Hazırlayan: Hüsamettin KAYMAKÇI</p>", unsafe_allow_html=True)
