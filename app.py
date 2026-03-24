import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from datetime import datetime

# --- 1. GÜVENLİK VE AYARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Kasa (Secrets) ayarları bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V3 | Resmi Şablon", layout="centered", page_icon="🤖")

# --- KARAKTER FİLTRESİ ---
def format_temizle(text):
    temiz = text.replace("**", "").replace("##", "").replace("#", "").replace("__", "")
    harita = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u'}
    for k, v in harita.items(): temiz = temiz.replace(k, v)
    return temiz.encode('latin-1', 'replace').decode('latin-1')

# --- WORD FORMATLAMA (Resmi Kurallar: Arial 12pt, 1.15 Aralığı) ---
def create_word(text, title):
    doc = Document()
    h = doc.add_heading(title.upper(), 0)
    temiz_word = text.replace("**", "").replace("##", "").replace("#", "")
    p = doc.add_paragraph(temiz_word)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.15
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=format_temizle(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=format_temizle(text))
    return pdf.output(dest='S').encode('latin-1')

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V3</h1>", unsafe_allow_html=True)

with st.expander("⚙️ Rapor Derinliği (Sayı Düğmeleri)", expanded=True):
    hedef_sayfa = st.radio("Hedef Sayfa Sayısı", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True)

with st.expander("📝 Proje Bilgileri (Resmi Şablona Göre)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise"])
        proje_adi = st.text_input("Proje Adı", placeholder="Bulut Kumbarası")
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına Teknoloji", "Eğitim Teknolojileri", "Akıllı Ulaşım"])
        ana_tema = st.text_input("Ana / Alt Tema Uyumu", placeholder="Örn: Sosyal İnovasyon")
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        takim_id = st.text_input("Başvuru/Takım ID")
        hedef_kitle = st.text_input("Hedef Kitle", placeholder="Örn: Yaşlılar, Öğrenciler")

    aciklama = st.text_area("Proje Özeti ve Kapsamı (Fikrinizi buraya yazın)", height=150)
    problem_tanimi = st.text_area("Problemin Tanımı ve Önemi (Boş bırakılabilir)", height=100)
    
    if st.button("🚀 Resmi Şablona Göre Çıktı Hazırla", use_container_width=True, type="primary"):
        if not aciklama:
            st.warning("Lütfen en azından proje fikrinizi yazın.")
        else:
            with st.status("🛠️ Resmi kriterler inceleniyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    # 404 HATASINI ÇÖZEN GÜNCELLENMİŞ MODEL ÇAĞRISI
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    
                    # Eksik verileri yönetme (Boşsa ibare ekleme)
                    p_adi = proje_adi if proje_adi else "[BURAYA PROJE ADINI YAZINIZ]"
                    d_adi = danisman if danisman else "[BURAYA DANIŞMAN ADINI YAZINIZ]"
                    t_adi = takim if takim else "[BURAYA TAKIM ADINI YAZINIZ]"
                    t_id = takim_id if takim_id else "[BURAYA ID YAZINIZ]"
                    h_kitle = hedef_kitle if hedef_kitle else "[BURAYA HEDEF KİTLEYİ YAZINIZ]"
                    tema = ana_tema if ana_tema else "[BURAYA TEMA UYUMUNU YAZINIZ]"

                    prompt = f"""
                    Sen bir Teknofest danışmanısın. {seviye} seviyesi {kategori} şablonuna göre {hedef_sayfa} sayfalık rapor yaz.
                    Sayfa Yapısı: Arial 12pt, 1.15 satır aralığı mantığında. Markdown kullanma.
                    
                    ZORUNLU RESMİ BÖLÜMLER VE PUANLAMA (Bu bölümleri mutlaka kullan):
                    1. PROJE ÖZETİ (20 PUAN): Amacı, ana fikri ({tema}), hedef kitlesi ({h_kitle}) ve çözüm yaklaşımı. (150-250 kelime)
                    2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ (35 PUAN): Problemin önemi ve çözümün temel işleyiş mantığı.
                    3. ÖZGÜN DEĞER, UYGULANABİLİRLİK VE SÜRDÜRÜLEBİLİRLİK (24 PUAN): Projenin farklılığı ve geleceği.
                    4. PROJENİN HAZIRLANIŞ SÜRECİ VE ÇALIŞMA YÖNTEMİ (12 PUAN).
                    5. PROJE TAKIMI (3 PUAN): Görev dağılımı tablosu anlatımı.
                    6. KAYNAKLAR (3 PUAN).
                    
                    BAŞLANGIÇ BİLGİLERİ (EN BAŞA EKLE):
                    PROJE ADI: {p_adi}
                    DANIŞMAN: {d_adi}
                    TAKIM: {t_adi}
                    ID: {t_id}
                    ---
                    İçerik Temeli: {aciklama}. Ek Sorun Tanımı: {problem_tanimi}
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor = response.text
                    st.session_state.p_adi = p_adi
                    st.session_state.hazir = True
                    status.update(label="✅ Rapor Şablona Göre Hazırlandı!", state="complete")
                except Exception as e:
                    st.error(f"Pürüz: {str(e)}")

# --- ÇIKTILAR ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'> <h2 style='text-align:center;'>{st.session_state.p_adi.upper()}</h2><p>{st.session_state.rapor.replace('\n', '<br>')}</p></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: st.download_button("📥 PDF Olarak İndir", create_pdf(st.session_state.rapor, st.session_state.p_adi), f"{st.session_state.p_adi}.pdf", use_container_width=True)
    with c2: st.download_button("📥 Word Olarak İndir", create_word(st.session_state.rapor, st.session_state.p_adi), f"{st.session_state.p_adi}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026 | Hazırlayan: Hüsamettin KAYMAKÇI</p>", unsafe_allow_html=True)
