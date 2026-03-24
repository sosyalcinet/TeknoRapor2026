import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from io import BytesIO
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE ANAHTARLAR ---
# Yeni API Anahtarınız [cite: 1]
GEMINI_API_KEY = "AIzaSyBLG5jhEOO44BU_BfIVVSz7L64AAIi7qBs"

try:
    # Google Sheets için kimlik bilgileri [cite: 1]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    GOOGLE_CREDS = None

# Sayfa Yapılandırması [cite: 1]
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- FONKSİYONLAR ---
def karakter_filtresi(text): # [cite: 2]
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
        '\u2019': "'", '\u2018': "'", '\u201d': '"', '\u201c': '"',
        '\u2013': "-", '\u2014': "-", '\u2022': "*", '\u2026': "..."
    }
    for k, v in harita.items(): text = text.replace(k, v)
    return text

def create_pdf(text, title): # [cite: 2, 3]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=karakter_filtresi(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=karakter_filtresi(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title): # [cite: 3]
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Yapay Zeka Robotu V1</h1>", unsafe_allow_html=True) # [cite: 4]

with st.expander("2. ⚙️ Ayarlar (Rapor Kaç Sayfa Olsun?)"): # [cite: 4]
    hedef_sayfa = st.slider("Rapor Derinliği (Sayfa)", 1, 6, 3) # [cite: 4]

with st.expander("3. 🧠 Kişilik Modu"): # [cite: 5]
    yazim_modu = st.selectbox(
        "Yazım Karakteri Seçin",
        options=["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI", "AI Standart"],
        index=0
    ) # [cite: 5]

with st.expander("4. 📝 Rapor Girişi (Ana Bölüm)"): # [cite: 6]
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"]) # [cite: 6]
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası") # [cite: 6]
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"]) # [cite: 6]
    proje_aciklamasi = st.text_area("Proje Açıklaması (Temel Mantık)", height=150) # [cite: 6]
    ozgunluk = st.text_area("Kişisel Dokunuş / Hikaye", height=100) # [cite: 6]
    
    if st.button("🚀 Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True, type="primary"): # [cite: 6]
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.") # [cite: 7]
        else:
            with st.status("🛠️ Raporunuz hazırlanıyor...", expanded=True) as status: # [cite: 7]
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    
                    # 404 Hatasını önlemek için sabit model ismi kullanımı 
                    # 'gemini-1.5-flash' ismi çoğu SDK sürümüyle uyumludur.
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    hedef_kelime = hedef_sayfa * 450 # 
                    prompt = f"""
                    Sen Teknofest danışmanısın.
                    {seviye} seviyesi için {kategori} kategorisinde TAM {hedef_sayfa} SAYFA (Yaklaşık {hedef_kelime} kelime) rapor yaz.
                    MOD: {yazim_modu} (Anti-Dedektör ise insansı yaz).
                    BÖLÜMLER: Özet, Problem, Çözüm, Özgün Değer, Hedef Kitle, Maliyet, Takvim.
                    İçerik: {proje_adi} - {proje_aciklamasi}.
                    Hikaye: {ozgunluk}
                    """ # [cite: 10, 11, 12, 13]
                    
                    response = model.generate_content(prompt) # [cite: 13]
                    st.session_state.rapor_metni = response.text # [cite: 13]
                    st.session_state.rapor_hazir = True # [cite: 14]
                    status.update(label="✅ Rapor Hazır!", state="complete", expanded=False) # [cite: 14]
                except Exception as e:
                    # Eğer hala hata alırsanız model ismini 'gemini-pro' olarak deneyebilirsiniz.
                    st.error(f"Sistemsel Hata: {str(e)}")

# --- SONUÇLAR VE İNDİRME ---
if "rapor_hazir" in st.session_state and st.session_state.rapor_hazir: # [cite: 14]
    st.markdown("---")
    metin = st.session_state.rapor_metni
    st.text_area("Rapor Önizleme", metin, height=300) # [cite: 15]
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 PDF Olarak İndir", create_pdf(metin, proje_adi), f"{proje_adi}.pdf", "application/pdf") # [cite: 16]
    with col2:
        st.download_button("📥 Word Olarak İndir", create_word(metin, proje_adi), f"{proje_adi}.docx") # [cite: 16]

# --- FOOTER ---
st.markdown(f"""
<p style='text-align: center; color: gray; font-size: 0.9em;'>
    Derepazarı İlçe MEM Arge Birimi © 2026<br>
    <b>Hazırlayan: Hüsamettin KAYMAKÇI</b>
</p>
""", unsafe_allow_html=True) # [cite: 19]
