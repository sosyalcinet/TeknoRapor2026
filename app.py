import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# --- 1. RESMİ VERİ YAPISI ---
TEKNOFEST_DATA = {
    "İlkokul": {
        "Yarisma_Adi": "2026 İnsanlık Yararına Teknolojiler Yarışması-İlkokul Seviyesi",
        "Temalar": {"Doğa ve Çevre": ["Geri Dönüşüm", "Su Tasarrufu"], "Sağlık": ["Hijyen"]},
        "Hedef_Kitle": ["İlkokul Öğrencileri", "Veliler"]
    },
    "Ortaokul": {
        "Yarisma_Adi": "2026 İnsanlık Yararına Teknolojiler Yarışması-Ortaokul Seviyesi",
        "Temalar": {"Afet Yönetimi": ["Erken Uyarı"], "Sosyal İnovasyon": ["Erişilebilirlik"]},
        "Hedef_Kitle": ["Ortaokul Öğrencileri", "Yaşlılar"]
    },
    "Lise": {
        "Yarisma_Adi": "2026 İnsanlık Yararına Teknolojiler Yarışması-Lise Seviyesi",
        "Temalar": {"Biyomedikal": ["Teşhis Destek"], "Kriz Lojistiği": ["Lojistik"]},
        "Hedef_Kitle": ["Lise Öğrencileri", "Profesyonel Ekipler"]
    }
}

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Secrets ayarlarında GEMINI_API_KEY bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V8 | Resmi Şablon", layout="centered")

# --- FORMATLAMA (Resmi Şartname: Arial 12pt, 1.15 Aralık) ---
def create_word(text, title, y_adi):
    doc = Document()
    doc.add_heading("BAŞVURU YAPTIĞI YARIŞMA ADI", 1)
    doc.add_paragraph(y_adi)
    doc.add_heading(title.upper(), 0)
    p = doc.add_paragraph(text.replace("**", "").replace("##", ""))
    style = doc.styles['Normal']
    style.font.name = 'Arial'; style.font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.15
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu</h1>", unsafe_allow_html=True)

with st.expander("📝 Rapor Girişi", expanded=True):
    seviye = st.selectbox("Eğitim Seviyesi", list(TEKNOFEST_DATA.keys()))
    col1, col2 = st.columns(2)
    with col1:
        proje_adi = st.text_input("Proje Adı")
        ana_tema = st.selectbox("Ana Tema", list(TEKNOFEST_DATA[seviye]["Temalar"].keys()))
    with col2:
        danisman = st.text_input("Danışman Adı")
        h_kitle = st.selectbox("Hedef Kitle", TEKNOFEST_DATA[seviye]["Hedef_Kitle"])
    
    aciklama = st.text_area("Proje Özeti (Fikriniz)", height=150)
    
    if st.button("🚀 Resmi Şablona Göre Raporu Hazırla", use_container_width=True, type="primary"):
        with st.status("🛠️ Şartname kriterleri analiz ediliyor...", expanded=True) as status:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # 404 HATASINI ÇÖZEN EN STABİL MODEL ÇAĞRISI
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Sen bir Teknofest danışmanısın. {seviye} seviyesi {ana_tema} temasında resmi ÖDR yaz.
                Puanlama: Özet 20, Problem 35, Özgünlük 24, Yöntem 12.
                BAŞLIKLAR: PROJE: {proje_adi} | DANIŞMAN: {danisman} | HEDEF: {h_kitle}
                Format: Arial 12pt, 1.15 aralık. Markdown kullanma.
                ---
                İçerik: {aciklama}
                """
                response = model.generate_content(prompt)
                st.session_state.rapor = response.text
                st.session_state.p_adi = proje_adi
                st.session_state.hazir = True
                status.update(label="✅ Rapor Hazır!", state="complete")
            except Exception as e: st.error(f"Sistem Hatası (404/API): {str(e)}")

# --- ÇIKTI ALANI ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state.rapor.replace('\n', '<br>'), unsafe_allow_html=True)
    y_tam_ad = f"{TEKNOFEST_DATA[seviye]['Yarisma_Adi']} / {ana_tema}"
    st.download_button("📥 Word İndir (Resmi Format)", create_word(st.session_state.rapor, st.session_state.p_adi, y_tam_ad), f"{st.session_state.p_adi}.docx", use_container_width=True)
