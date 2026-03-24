import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO

# --- API KEY ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API anahtarı bulunamadı! (Streamlit secrets)")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# --- MODEL (GÜNCEL) ---
MODEL_NAME = "gemini-2.0-flash"

# --- SAYFA AYARI ---
st.set_page_config(
    page_title="TeknoRapor 2026",
    layout="centered",
    page_icon="🤖"
)

# --- WORD OLUŞTUR ---
def create_word(text, info):
    doc = Document()

    h = doc.add_heading(info['yarisma'], 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("ÖN DEĞERLENDİRME RAPORU", 1).alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    p.add_run(
        f"\nPROJE: {info['proje']}\nTAKIM: {info['takim']}\nBAŞVURU ID: {info['bid']}"
    ).bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    content = doc.add_paragraph(text)
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(12)
    content.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- ARAYÜZ ---
st.title("🤖 Teknofest ÖDR Robotu (2026)")

# --- GİRİŞ ---
st.subheader("📌 Proje Bilgileri")

proje_adi = st.text_input("Proje Adı")
takim_adi = st.text_input("Takım Adı")
basvuru_id = st.text_input("Başvuru ID")

st.subheader("🧠 Proje Özeti")
aciklama = st.text_area("Projenizi anlatın", height=150)

sayfa = st.selectbox("Rapor uzunluğu", [1, 2, 3, 4, 5])

mod = st.selectbox(
    "Yazım Modu",
    ["Standart", "Akademik", "Doğal (AI tespiti zor)"]
)

# --- BUTON ---
if st.button("🚀 Rapor Oluştur"):

    if not proje_adi or not aciklama:
        st.warning("Proje adı ve açıklama gerekli")
        st.stop()

    try:
        with st.spinner("Rapor hazırlanıyor..."):

            model = genai.GenerativeModel(MODEL_NAME)

            prompt = f"""
            Sen Teknofest jüri üyesisin.

            {sayfa} sayfalık resmi ÖDR raporu yaz.

            MOD: {mod}

            PROJE ADI: {proje_adi}
            TAKIM: {takim_adi}

            İÇERİK:
            {aciklama}

            Bölümler:
            1. Proje Özeti
            2. Problem Tanımı
            3. Özgünlük
            4. Yöntem
            5. Sonuç
            """

            response = model.generate_content(prompt)

            rapor = response.text

            st.success("Rapor hazır!")

            st.markdown("---")
            st.markdown(rapor)

            info = {
                "yarisma": "TEKNOFEST 2026",
                "proje": proje_adi,
                "takim": takim_adi,
                "bid": basvuru_id
            }

            st.download_button(
                "📥 Word indir",
                create_word(rapor, info),
                file_name=f"{proje_adi}.docx"
            )

    except Exception as e:
        st.error(f"Hata oluştu: {str(e)}")

# --- FOOTER ---
st.markdown(
    "<center><small>Derepazarı İlçe MEM AR-GE © 2026</small></center>",
    unsafe_allow_html=True
)
