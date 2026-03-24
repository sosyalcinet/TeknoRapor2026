import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# --- 1. SEÇENEK LİSTELERİ ---
TEMALAR = {
    "Sağlık ve İlk Yardım": ["Engelli Dostu", "Sağlıklı Yaşam", "Hastalık Takibi", "Yaşlı Bakımı", "İlk Yardım Teknolojileri"],
    "Afet Yönetimi": ["Deprem", "Sel", "Yangın", "Tahliye Sistemleri", "Arama Kurtarma", "Erken Uyarı Sistemleri"],
    "Sosyal İnovasyon": ["Dezavantajlı Gruplar", "Eğitim Teknolojileri", "Aile ve Çocuk", "Toplumsal Farkındalık", "Göç ve Uyum"]
}

HEDEF_KITLELER = [
    "Engelli Bireyler", 
    "Yaşlılar ve Bakıma Muhtaç Kişiler", 
    "Öğrenciler ve Eğitimciler", 
    "Afetzedeler ve Arama Kurtarma Ekipleri", 
    "Sağlık Çalışanları ve Hastalar",
    "Düşük Gelirli Gruplar",
    "Çocuklar ve Ebeveynler",
    "Toplumun Geneli (Sosyal Farkındalık)"
]

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Kasa (Secrets) ayarlarında API anahtarı bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V6 | Resmi Şablon", layout="centered", page_icon="🤖")

# --- FORMATLAMA FONKSİYONLARI ---
def create_word(text, title):
    doc = Document()
    h = doc.add_heading(title.upper(), 0)
    p = doc.add_paragraph(text.replace("**", "").replace("##", "").replace("#", ""))
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.15 # Şartnameye uygun 1.15 aralık
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=title.encode('latin-1', 'replace').decode('latin-1'), align='C')
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V6</h1>", unsafe_allow_html=True)

with st.expander("⚙️ Rapor Derinliği", expanded=True):
    hedef_sayfa = st.radio("Sayfa Sayısı", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True)

with st.expander("📝 Proje Bilgileri (Resmi Seçenekli Sistem)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise"])
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        ana_tema = st.selectbox("Ana Tema", list(TEMALAR.keys()))
        alt_tema = st.selectbox("Alt Tema", TEMALAR[ana_tema])
        
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        # HEDEF KİTLE SEÇİMİ
        hedef_kitle = st.selectbox("Hedef Kitle Seçin", HEDEF_KITLELER)
        takim_id = st.text_input("Takım/Başvuru ID")

    aciklama = st.text_area("Proje Özeti ve Kapsamı (Buraya ana fikrinizi yazın)", height=150)
    
    if st.button("🚀 Şartnameye Uygun Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama:
            st.warning("Lütfen proje fikrinizi kısaca açıklayın.")
        else:
            with st.status("🛠️ Şartname kriterleri analiz ediliyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    p_name = proje_adi if proje_adi else "[BURAYA PROJE ADINI YAZINIZ]"
                    d_name = danisman if danisman else "[BURAYA DANIŞMAN ADINI YAZINIZ]"
                    t_name = takim if takim else "[BURAYA TAKIM ADINI YAZINIZ]"
                    id_no = takim_id if takim_id else "[BURAYA ID YAZINIZ]"

                    prompt = f"""
                    Sen bir Teknofest jürisisin. {seviye} seviyesi için {ana_tema} ana teması ve {alt_tema} alt temasında bir ÖDR yazacaksın.
                    HEDEF KİTLE: {hedef_kitle}. 
                    Puanlama Kriterleri: Özet (20p), Problem (35p), Özgünlük (24p), Yöntem (12p), Takım (3p), Kaynaklar (3p).
                    Format: Arial 12pt, 1.15 aralık. Markdown kullanma.
                    
                    BAŞLIKLAR:
                    PROJE ADI: {p_name}
                    DANIŞMAN: {d_name}
                    TAKIM: {t_name}
                    ID: {id_no}
                    TEMA: {ana_tema} / {alt_tema}
                    HEDEF KİTLE: {hedef_kitle}
                    ---
                    BÖLÜMLER:
                    1. PROJE ÖZETİ (Amacı, Kapsamı, Hedef Kitle: {hedef_kitle})
                    2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ
                    3. ÖZGÜNLÜK VE UYGULANABİLİRLİK
                    4. ÇALIŞMA YÖNTEMİ VE SÜREÇ
                    5. PROJE TAKIMI VE GÖREV DAĞILIMI
                    6. KAYNAKLAR
                    
                    İçerik Temeli: {aciklama}
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor = response.text
                    st.session_state.p_adi = p_name
                    st.session_state.hazir = True
                    status.update(label="✅ Rapor Şartnameye Uygun Hazırlandı!", state="complete")
                except Exception as e:
                    st.error(f"Sistem Hatası: {str(e)}")

# --- SONUÇ ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'> <h2 style='text-align:center;'>{st.session_state.p_adi.upper()}</h2><p>{st.session_state.rapor.replace('\n', '<br>')}</p></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: st.download_button("📥 PDF İndir", create_pdf(st.session_state.rapor, st.session_state.p_adi), f"{st.session_state.p_adi}.pdf", use_container_width=True)
    with c2: st.download_button("📥 Word İndir", create_word(st.session_state.rapor, st.session_state.p_adi), f"{st.session_state.p_adi}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026 | Hazırlayan: Hüsamettin KAYMAKÇI</p>", unsafe_allow_html=True)
