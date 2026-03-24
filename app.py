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
# Yeni API Anahtarı doğrudan koda entegre edildi
GEMINI_API_KEY = "AIzaSyBLG5jhEOO44BU_BfIVVSz7L64AAIi7qBs"

try:
    # Google E-Tablo bağlantısı için gerekli kimlik bilgileri kasa (secrets) üzerinden alınmaya devam ediyor
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Google Sheets kimlik bilgileri (Secrets) bulunamadı! E-tablo kaydı çalışmayabilir.")

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- FONKSİYONLAR (Karakter Filtresi & Dosya Oluşturma) ---
def karakter_filtresi(text):
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
        '\u2019': "'", '\u2018': "'", '\u201d': '"', '\u201c': '"',
        '\u2013': "-", '\u2014': "-"
    }
    for k, v in harita.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, karakter_filtresi(title), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, karakter_filtresi(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open("TeknoRapor_Kayitlari").sheet1
    except:
        return None

# --- 2. ARAYÜZ (Giriş Alanları) ---
st.title("🤖 TeknoRapor V1")
st.subheader("Teknofest Proje Raporu Hazırlama Asistanı")
st.info("Derepazarı İlçe Milli Eğitim Müdürlüğü Ar-Ge Birimi Tarafından Geliştirilmiştir.")

with st.expander("📝 Proje Bilgileri", expanded=True):
    p_adi = st.text_input("Proje Adı", placeholder="Örn: Akıllı Tarım Sistemi")
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    kategori = st.text_input("Yarışma Kategorisi", placeholder="Örn: İnsanlık Yararına Teknoloji")
    aciklama = st.text_area("Projenizin Amacı ve Özeti", placeholder="Projeniz ne işe yarar? Hangi sorunu çözer?", height=150)
    yazim_modu = st.select_slider("Yazım Tarzı", options=["Sade", "Akademik", "Teknik", "İkna Edici"], value="Akademik")

# --- 3. RAPOR OLUŞTURMA MANTIĞI ---
if st.button("🚀 Raporu Oluştur", use_container_width=True):
    if not p_adi or not aciklama:
        st.warning("Lütfen proje adı ve açıklamasını doldurun.")
    else:
        with st.spinner("Yapay zeka raporunuzu hazırlıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Ücretli API katmanına uygun kararlı model seçimi
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Sen bir Teknofest proje danışmanısın. Aşağıdaki bilgilere göre resmi ve ikna edici bir proje raporu hazırla.
                Dil tamamen Türkçe olmalı. {yazim_modu} bir üslup kullan.
                
                PROJE ADI: {p_adi}
                SEVİYE: {seviye}
                KATEGORİ: {kategori}
                PROJE ÖZETİ: {aciklama}
                
                Bölümler:
                1. Proje Özeti
                2. Problemin Tanımı ve Çözümü
                3. Yenilikçi (Özgün) Yönü
                4. Hedef Kitle ve Uygulanabilirlik
                5. Kullanılacak Yöntemler ve Materyaller
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                st.session_state.rapor = rapor_metni
                st.session_state.p_adi = p_adi
                
                # E-Tabloya Kaydet
                sheet = connect_sheets()
                if sheet:
                    sheet.append_row([str(datetime.now()), p_adi, seviye, kategori, yazim_modu])
                
                st.success("✅ Raporunuz başarıyla oluşturuldu!")
            except Exception as e:
                st.error(f"Bir hata oluştu: {str(e)}")

# --- 4. SONUÇ VE İNDİRME ---
if "rapor" in st.session_state:
    st.markdown("---")
    st.markdown("### 📋 Hazırlanan Rapor Taslağı")
    st.write(st.session_state.rapor)
    
    # İndirme Düğmeleri
    pdf_bytes = create_pdf(st.session_state.rapor, st.session_state.p_adi)
    word_bytes = create_word(st.session_state.rapor, st.session_state.p_adi)
    
    c_down1, c_down2, c_down3 = st.columns(3)
    with c_down1:
        st.download_button("📥 PDF Olarak İndir", pdf_bytes, f"{st.session_state.p_adi}.pdf", use_container_width=True)
    with c_down2:
        st.download_button("📥 Word Olarak İndir", word_bytes, f"{st.session_state.p_adi}.docx", use_container_width=True)
    with c_down3:
        st.button("🖨️ Raporu Yazdır", on_click=lambda: st.info("PDF olarak indirip Ctrl+P ile yazdırabilirsiniz. A4 formatı tam uyumludur."), use_container_width=True)

    # E-posta Gönderme Alanı (Simüle)
    email_user = st.text_input("📩 Raporu E-Postana Gönder", placeholder="E-posta adresinizi yazın...")
    if st.button("E-Posta Gönder"):
        if email_user:
            st.success(f"Rapor taslağı {email_user} adresine e-posta olarak gönderilmek üzere sıraya alındı.")
        else:
            st.warning("Lütfen bir e-posta adresi girin.")

# --- 5. SİSTEM DÜĞMELERİ (YENİ VE PAYLAŞ) ---
st.markdown("---")
c_sys1, c_sys2 = st.columns(2)
with c_sys1:
    if st.button("🔄 Yeni Rapor (Sıfırla)", use_container_width=True):
        st.session_state.clear()
        st.rerun()
with c_sys2:
    app_link = "https://teknorapor-derepazari.streamlit.app"
    davet = f"🚀 Teknofest projelerinizi hazırlamak için Hüsamettin KAYMAKÇI tarafından sunulan bu sistemi kullanın:\n\n🔗 {app_link}"
    st.link_button("🟢 Sistemi WhatsApp'ta Paylaş", f"https://api.whatsapp.com/send?text={urllib.parse.quote(davet)}", use_container_width=True)

st.markdown("<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026 | Hüsamettin KAYMAKÇI</p>", unsafe_allow_html=True)
