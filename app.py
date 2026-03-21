import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE ANAHTARLAR (KASADAN ALINIR) ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Secrets (Kasa) ayarları eksik! Lütfen kontrol edin.")
    st.stop()

# Sayfa Ayarları
st.set_page_config(page_title="TeknoRapor Pro | Derepazarı", layout="wide", page_icon="📝")

# Google Sheets Bağlantısı
def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# --- TÜRKÇE KARAKTER DÜZELTİCİ (PDF HATASINI ÇÖZEN KISIM) ---
def turkce_duzelt(text):
    """PDF motorunun tanımadığı 'İ, ş, ğ' gibi harfleri uyumlu hale getirir."""
    harita = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u'}
    for kaynak, hedef in harita.items():
        text = text.replace(kaynak, hedef)
    return text

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=turkce_duzelt(title), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, txt=turkce_duzelt(text))
    return pdf.output(dest='S').encode('latin-1')

# --- 2. ANA ARAYÜZ ---
with st.sidebar:
    st.title("🏛️ Arge Birimi")
    st.markdown("Derepazarı İlçe MEM Proje Sistemi")
    st.divider()
    st.info("Raporlar otomatik olarak Arge veri tabanına kaydedilmektedir.")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Pro: Proje Tasarım İstasyonu</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
with col2:
    ham_fikir = st.text_area("Projenizin ana fikri nedir?", height=100)
    insan_dokunusu = st.text_area("Kişisel Gözleminiz (Özgünlük Hikayesi)", height=68)

# --- 3. RAPOR OLUŞTURMA ---
if st.button("Raporu Analiz Et ve Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen boş alanları doldurun.")
    else:
        with st.spinner("Yapay zeka kriterleri tarıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # En kararlı modeli seçiyoruz
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Teknofest jürisi gibi düşün. {seviye} seviyesi için akademik dille ÖDR yaz.
                KURALLAR: HTML KODU KULLANMA. 150-250 kelime özet.
                Bölümler: Özet, Problem, Çözüm, Özgün Değer.
                İçerik: {proje_adi} - {ham_fikir}. Hikaye: {insan_dokunusu}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                st.balloons()
                st.success("✅ Rapor Hazırlandı ve Arge Veri Tabanına Kaydedildi!")
                st.markdown("---")
                st.write(rapor_metni)

                # --- 4. PAYLAŞIM VE PDF PANELİ ---
                st.markdown("### 📤 Paylaşım ve İndirme Paneli")
                st.warning("Önce PDF olarak indirin, sonra WhatsApp'tan dosyayı ekleyerek gönderin.")
                
                c1, c2 = st.columns(2)
                with c1:
                    # PDF İndirme (Hatasız)
                    pdf_data = create_pdf(rapor_metni, proje_adi)
                    st.download_button("📥 Raporu PDF Olarak İndir", pdf_data, f"{proje_adi}_Rapor.pdf", "application/pdf", use_container_width=True)
                with c2:
                    # WhatsApp Bilgi Mesajı
                    msg = f"*{proje_adi}* projemin Teknofest raporunu hazırladım. PDF dosyasını birazdan iletiyorum."
                    st.link_button("🟢 WhatsApp'tan Bilgi Ver", f"https://wa.me/?text={urllib.parse.quote(msg)}", use_container_width=True)

                # Arka planda Google Sheets kaydı
                sheet = connect_sheets()
                if sheet:
                    sheet.append_row([str(datetime.now()), seviye, proje_adi, rapor_metni])

            except Exception as e:
                st.error(f"Pürüz: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.8em;'>Derepazarı İlçe MEM Arge Birimi © 2026</p>", unsafe_allow_html=True)
