import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from datetime import datetime

# --- 1. GÜVENLİK VE SİSTEM AYARLARI ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Kasa (Secrets) ayarları bulunamadı! Lütfen kontrol edin.")
    st.stop()

st.set_page_config(page_title="TeknoRapor V4 | Resmi Şablon", layout="centered", page_icon="🤖")

# --- KARAKTER FİLTRESİ ---
def format_temizle(text):
    temiz = text.replace("**", "").replace("##", "").replace("#", "").replace("__", "")
    harita = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u'}
    for k, v in harita.items(): temiz = temiz.replace(k, v)
    return temiz.encode('latin-1', 'replace').decode('latin-1')

# --- RESMİ WORD FORMATLAMA (Arial 12pt, 1.15 Aralığı) ---
def create_word(text, title):
    doc = Document()
    # Başlık: Arial Black, 14pt
    h = doc.add_heading(title.upper(), 0)
    for run in h.runs:
        run.font.name = 'Arial Black'
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0, 0, 0)

    # İçerik: Arial, 12pt, 1.15 satır aralığı
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
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V4</h1>", unsafe_allow_html=True)

with st.expander("⚙️ Rapor Derinliği (Sayı Düğmeleri)", expanded=True):
    hedef_sayfa = st.radio("Hedef Sayfa Sayısı", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True)

with st.expander("📝 Proje Bilgileri (Resmi Şablona Göre)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise"])
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına Teknoloji", "Eğitim Teknolojileri", "Akıllı Ulaşım"])
        tema = st.text_input("Ana / Alt Tema", placeholder="Örn: Sosyal İnovasyon")
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        t_id = st.text_input("Takım/Başvuru ID")
        h_kitle = st.text_input("Hedef Kitle", placeholder="Örn: Rize'deki Çay Üreticileri")

    aciklama = st.text_area("Proje Özeti ve Fikriniz (Ana Taslak)", height=150)
    
    if st.button("🚀 Resmi Şablona Göre Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama:
            st.warning("Lütfen en azından bir proje fikri giriniz.")
        else:
            with st.status("🛠️ Resmi kriterler ve puanlama anahtarı analiz ediliyor...", expanded=True) as status:
                try:
                    # 404 HATASINI ÇÖZEN GÜNCELLENMİŞ ÇAĞRI
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Eksik Bilgi Yönetimi
                    p_name = proje_adi if proje_adi else "[BURAYA PROJE ADINI YAZINIZ]"
                    d_name = danisman if danisman else "[BURAYA DANIŞMAN ADINI YAZINIZ]"
                    t_name = takim if takim else "[BURAYA TAKIM ADINI YAZINIZ]"
                    id_no = t_id if t_id else "[BURAYA ID NUMARASINI YAZINIZ]"
                    target = h_kitle if h_kitle else "[BURAYA HEDEF KİTLEYİ YAZINIZ]"
                    theme = tema if tema else "[BURAYA TEMA UYUMUNU YAZINIZ]"

                    prompt = f"""
                    Sen profesyonel bir Teknofest danışmanısın. {seviye} seviyesi {kategori} yarışması için resmi ÖDR hazırlayacaksın.
                    Hedef: {hedef_sayfa} Sayfa. Yazım Kuralları: Arial 12pt, 1.15 aralık (Markdown kullanma).
                    
                    BAŞLIK BİLGİLERİ (EN BAŞA):
                    PROJE ADI: {p_name}
                    DANIŞMAN: {d_name}
                    TAKIM: {t_name}
                    BAŞVURU ID: {id_no}
                    ---
                    AŞAĞIDAKİ RESMİ BÖLÜMLERİ PUANLAMA KRİTERLERİNE GÖRE YAZ:
                    1. PROJE ÖZETİ (20 PUAN): Amacı, kapsamı, ana fikri ({theme}) ve hedef kitlesi ({target}).
                    2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ (35 PUAN): Problemin güncelliği ve çözümün temel mantığı.
                    3. ÖZGÜN DEĞER, UYGULANABİLİRLİK VE SÜRDÜRÜLEBİLİRLİK (24 PUAN).
                    4. PROJENİN HAZIRLANIŞ SÜRECİ VE ÇALIŞMA YÖNTEMİ (12 PUAN).
                    5. PROJE TAKIMI (3 PUAN): Görev dağılımı tablosunu anlatarak hazırla.
                    6. KAYNAKLAR (3 PUAN).
                    
                    İçerik Kaynağı: {aciklama}
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state.rapor = response.text
                    st.session_state.p_adi_son = p_name
                    st.session_state.hazir = True
                    status.update(label="✅ Rapor Şablona Uygun Şekilde Hazırlandı!", state="complete")
                except Exception as e:
                    st.error(f"Sistem Hatası (404/API): {str(e)}")

# --- SONUÇ VE İNDİRME ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'> <h2 style='text-align:center;'>{st.session_state.p_adi_son.upper()}</h2><p>{st.session_state.rapor.replace('\n', '<br>')}</p></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: st.download_button("📥 PDF (Resmi Format)", create_pdf(st.session_state.rapor, st.session_state.p_adi_son), f"{st.session_state.p_adi_son}.pdf", use_container_width=True)
    with c2: st.download_button("📥 Word (Arial 12pt)", create_word(st.session_state.rapor, st.session_state.p_adi_son), f"{st.session_state.p_adi_son}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b></p>", unsafe_allow_html=True)
