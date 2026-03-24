import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from io import BytesIO
import urllib.parse

# --- 1. GÜVENLİK VE ANAHTARLAR ---
# Paylaştığınız yeni API anahtarı sisteme tanımlandı 
GEMINI_API_KEY = "AIzaSyBLG5jhEOO44BU_BfIVVSz7L64AAIi7qBs"

try:
    # Google Sheets için kimlik bilgileri (Secrets üzerinden) 
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    GOOGLE_CREDS = None

# Sayfa Yapılandırması 
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- FONKSİYONLAR ---
def karakter_filtresi(text):
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
        '\u2019': "'", '\u2018': "'", '\u201d': '"', '\u201c': '"',
        '\u2013': "-", '\u2014': "-", '\u2022': "*", '\u2026': "..."
    }
    for k, v in harita.items(): text = text.replace(k, v)
    return text

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=karakter_filtresi(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=karakter_filtresi(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Yapay Zeka Robotu V1</h1>", unsafe_allow_html=True) [cite: 4]

with st.expander("1. ℹ️ Açıklama"):
    st.write("Derepazarı İlçe MEM Arge Birimi tarafından öğretmen ve öğrencilerimiz için geliştirilen profesyonel rapor hazırlama asistanı.")

with st.expander("2. ⚙️ Rapor Ayarları"):
    hedef_sayfa = st.slider("Rapor Kaç Sayfa Olsun?", 1, 6, 3) [cite: 4]
    yazim_modu = st.selectbox(
        "Yazım Karakteri",
        options=["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI"],
        index=0
    ) [cite: 5]

with st.expander("3. 📝 Proje Bilgileri", expanded=True):
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"]) [cite: 6]
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım", "Engelsiz Yaşam"]) [cite: 6]
    
    # Proje adı ve özeti isteğiniz üzerine alt alta aynı bölümde
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Akıllı Atık Sistemi") [cite: 6]
    proje_aciklamasi = st.text_area("Proje Özeti (Temel Mantık)", height=150, placeholder="Projenizin nasıl çalıştığını anlatın...") [cite: 6]
    
    st.markdown("---")
    ozgunluk = st.text_area("Kişisel Dokunuş / Yerlilik ve Özgünlük Tarafı", height=100) [cite: 6]

    if st.button("🚀 Teknofest Standartlarında Raporu Hazırla", use_container_width=True, type="primary"): [cite: 6]
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen Proje Adı ve Özeti alanlarını boş bırakmayın.")
        else:
            with st.status("🛠️ Yapay zeka raporu oluşturuyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    # Hata veren model seçimi düzeltildi 
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    hedef_kelime = hedef_sayfa * 400
                    prompt = f"""
                    Sen profesyonel bir Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde bir Ön Değerlendirme Raporu yaz.
                    İçerik yaklaşık {hedef_kelime} kelime olmalı.
                    MOD: {yazim_modu}. (Doğal ve akıcı bir dil kullan).
                    
                    RAPOR BÖLÜMLERİ:
                    1. PROJE ÖZETİ
                    2. PROJE KONUSU VE PROBLEM
                    3. ÇÖZÜM ÖNERİSİ
                    4. YÖNTEM
                    5. YERLİLİK VE ÖZGÜNLÜK
                    6. HEDEF KİTLE
                    7. PROJE TAKVİMİ VE MALİYET
                    
                    Proje Bilgileri: {proje_adi} - {proje_aciklamasi}.
                    Ekstra Notlar: {ozgunluk}
                    """ [cite: 10, 11, 12, 13]
                    
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Rapor Başarıyla Hazırlandı!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Sistemsel Hata: {str(e)}")

# --- 4. SONUÇ VE İSTATİSTİKLER ---
if "rapor_hazir" in st.session_state and st.session_state.rapor_hazir: [cite: 14]
    st.markdown("---")
    metin = st.session_state.rapor_metni
    
    st.subheader("Rapor Önizleme")
    st.text_area("", metin, height=400) [cite: 14]
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button("📥 PDF Olarak İndir", create_pdf(metin, proje_adi), f"{proje_adi}.pdf", "application/pdf", use_container_width=True) [cite: 16]
    with col_d2:
        st.download_button("📥 Word Olarak İndir", create_word(metin, proje_adi), f"{proje_adi}.docx", use_container_width=True) [cite: 16]

# --- FOOTER ---
st.markdown(f"""
<hr>
<p style='text-align: center; color: gray; font-size: 0.9em;'>
    Derepazarı İlçe MEM Arge Birimi © 2026<br>
    <b>Hazırlayan: Hüsamettin KAYMAKÇI</b><br>
    E-Posta: sosyalcinet@gmail.com
</p>
""", unsafe_allow_html=True) [cite: 18, 19]
