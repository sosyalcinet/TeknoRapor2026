import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# --- 1. TEKNOFEST SEVİYE BAZLI VERİ MATRİSİ ---
LEVEL_DATA = {
    "İlkokul": {
        "Temalar": {
            "Sosyal İnovasyon": ["Eğitimde Yardımcı Araçlar", "Okul Yaşamı", "Oyunla Öğrenme", "Çevre Bilinci"],
            "Sağlık ve İlk Yardım": ["Kişisel Hijyen", "Sağlıklı Beslenme", "Çocuk Güvenliği"],
            "Afet Yönetimi": ["Okul Tahliye Farkındalığı", "Temel Afet Bilinci"]
        },
        "Hedef_Kitle": ["İlkokul Öğrencileri", "Öğretmenler", "Veliler", "Okul Çalışanları"]
    },
    "Ortaokul": {
        "Temalar": {
            "Sosyal İnovasyon": ["Dezavantajlı Gruplar", "Toplumsal Yardımlaşma", "Eğitim Teknolojileri", "Erişilebilirlik"],
            "Sağlık ve İlk Yardım": ["Hastalık Takibi", "Engelli Dostu Çözümler", "Sporcu Sağlığı"],
            "Afet Yönetimi": ["Arama Kurtarma Destek", "Erken Uyarı Düzenekleri", "Geçici Barınma Çözümleri"]
        },
        "Hedef_Kitle": ["Ortaokul ve Lise Öğrencileri", "Bedensel Engelli Bireyler", "Yaşlılar", "Afetzedeler"]
    },
    "Lise": {
        "Temalar": {
            "Sosyal İnovasyon": ["Mülteci ve Göçmen Uyumu", "İstihdam Çözümleri", "Sürdürülebilir Şehirler", "Fırsat Eşitliği"],
            "Sağlık ve İlk Yardım": ["Biyomedikal Teknolojiler", "Giyilebilir Sağlık Cihazları", "Akıllı İlaç Takibi"],
            "Afet Yönetimi": ["İnsansız Arama Kurtarma", "Kriz Yönetim Yazılımları", "Lojistik Destek Sistemleri"]
        },
        "Hedef_Kitle": ["Sektörel Uzmanlar", "Kronik Hastalar", "Yerel Yönetimler", "Görme/İşitme Engelli Bireyler", "Profesyonel Kurtarma Ekipleri"]
    }
}

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Secrets ayarlarında API anahtarı bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V7 | Akıllı Filtre", layout="centered", page_icon="🤖")

# --- FORMATLAMA FONKSİYONLARI ---
def create_word(text, title):
    doc = Document()
    h = doc.add_heading(title.upper(), 0)
    p = doc.add_paragraph(text.replace("**", "").replace("##", "").replace("#", ""))
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'; font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.15
    bio = BytesIO()
    doc.save(bio); return bio.getvalue()

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=title.encode('latin-1', 'replace').decode('latin-1'), align='C')
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V7</h1>", unsafe_allow_html=True)

with st.expander("⚙️ Rapor Derinliği", expanded=True):
    hedef_sayfa = st.radio("Sayfa Sayısı", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True)

with st.expander("📝 Proje Bilgileri (Akıllı Filtreli)", expanded=True):
    # 1. SEVİYE SEÇİMİ (Ana Tetikleyici)
    seviye = st.selectbox("Eğitim Seviyesi Seçin", ["İlkokul", "Ortaokul", "Lise"])
    
    col1, col2 = st.columns(2)
    with col1:
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        # SEVİYEYE GÖRE TEMA FİLTRESİ
        ana_tema = st.selectbox("Ana Tema", list(LEVEL_DATA[seviye]["Temalar"].keys()))
        alt_tema = st.selectbox("Alt Tema", LEVEL_DATA[seviye]["Temalar"][ana_tema])
        
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        # SEVİYEYE GÖRE HEDEF KİTLE FİLTRESİ
        h_kitle = st.selectbox("Hedef Kitle", LEVEL_DATA[seviye]["Hedef_Kitle"])
        takim_id = st.text_input("Takım/Başvuru ID")

    aciklama = st.text_area("Proje Özeti ve Kapsamı (Buraya ana fikrinizi yazın)", height=150)
    
    if st.button("🚀 Şartnameye Uygun Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama:
            st.warning("Lütfen proje fikrinizi kısaca açıklayın.")
        else:
            with st.status(f"🛠️ {seviye} Seviyesi Kriterleri Analiz Ediliyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    p_name = proje_adi if proje_adi else "[PROJE ADI]"
                    d_name = danisman if danisman else "[DANIŞMAN ADI]"
                    t_name = takim if takim else "[TAKIM ADI]"
                    id_no = takim_id if takim_id else "[ID]"

                    prompt = f"""
                    Sen profesyonel bir Teknofest {seviye} seviyesi danışmanısın. 
                    {ana_tema} ana teması ve {alt_tema} alt temasında, {h_kitle} hedef kitlesine yönelik bir ÖDR yaz.
                    Puanlama: Özet (20p), Problem (35p), Özgünlük (24p), Yöntem (12p), Takım (3p), Kaynaklar (3p).
                    Format: Arial 12pt, 1.15 aralık. Markdown kullanma.
                    
                    BAŞLIKLAR:
                    PROJE ADI: {p_name} | DANIŞMAN: {d_name} | TAKIM: {t_name} | ID: {id_no}
                    SEVİYE/TEMA: {seviye} / {ana_tema} - {alt_tema}
                    HEDEF KİTLE: {h_kitle}
                    ---
                    BÖLÜMLER:
                    1. PROJE ÖZETİ (Amacı, Kapsamı, Hedef Kitle: {h_kitle})
                    2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ
                    3. ÖZGÜNLÜK VE UYGULANABİLİRLİK (Akademik dille)
                    4. ÇALIŞMA YÖNTEMİ VE SÜREÇ
                    5. PROJE TAKIMI (Görev dağılımı anlatımı)
                    6. KAYNAKLAR
                    
                    İçerik Temeli: {aciklama}
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor = response.text
                    st.session_state.p_adi = p_name
                    st.session_state.hazir = True
                    status.update(label="✅ Rapor Hazır!", state="complete")
                except Exception as e: st.error(str(e))

# --- SONUÇ ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'> <h2 style='text-align:center;'>{st.session_state.p_adi.upper()}</h2><p>{st.session_state.rapor.replace('\n', '<br>')}</p></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: st.download_button("📥 PDF İndir", create_pdf(st.session_state.rapor, st.session_state.p_adi), f"{st.session_state.p_adi}.pdf", use_container_width=True)
    with c2: st.download_button("📥 Word İndir", create_word(st.session_state.rapor, st.session_state.p_adi), f"{st.session_state.p_adi}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026 | Hazırlayan: Hüsamettin KAYMAKÇI</p>", unsafe_allow_html=True)
