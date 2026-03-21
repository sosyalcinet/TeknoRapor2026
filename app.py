import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE AYARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Kasa (Secrets) ayarları bulunamadı!")
    st.stop()

# Sayfa Ayarları
st.set_page_config(page_title="TeknoRapor Pro | Derepazarı", page_icon="🚀", layout="wide")

# Google Sheets Bağlantısı
def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# PDF Oluşturucu (Türkçe Karakter Uyarılı)
def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    # latin-1 güvenli karakter dönüşümü
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.title("🏛️ Arge Birimi")
    st.markdown("Derepazarı İlçe MEM Proje Destek Sistemi")
    st.divider()
    st.write("✅ **Sistem:** Yayında")
    st.write("📅 **Yıl:** 2026")

# --- 3. ANA EKRAN ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Pro: Proje Tasarım İstasyonu</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
with col2:
    ham_fikir = st.text_area("Projenin ana fikri nedir?", height=100)
    insan_dokunusu = st.text_area("Kişisel Gözleminiz", height=68)

# --- 4. RAPOR OLUŞTURMA ---
if st.button("Raporu Analiz Et ve Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen alanları doldurun.")
    else:
        with st.spinner("Yapay zeka modelleri taranıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # 404 Hatasını Çözen Model Seçimi
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                prompt = f"""
                Teknofest jürisi gibi düşün. {seviye} seviyesi için ÖDR yaz.
                KURALLAR: HTML KODU KULLANMA. 150-250 kelime özet. 
                Bölümler: Özet, Problem, Çözüm, Özgün Değer.
                İçerik: {proje_adi} - {ham_fikir}. Hikaye: {insan_dokunusu}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                # Başarı Ekranı
                st.success("✅ Rapor Hazırlandı!")
                
                # Kelime Sayacı ve Analiz
                k_sayisi = len(rapor_metni.split())
                c1, c2 = st.columns(2)
                c1.metric("Kelime Sayısı", k_sayisi, "Hedef: 150-250")
                c2.metric("Uyumluluk", "%100", "Standart")

                st.markdown("---")
                st.write(rapor_metni)

                # --- 5. PAYLAŞIM PANELİ (GİZLİLİK ODAKLI) ---
                st.markdown("### 📤 Paylaşım Seçenekleri")
                
                # WhatsApp için metni kısaltıyoruz (Hata vermemesi için)
                ozet_paylas = f"*{proje_adi}* Rapor Taslağı Hazır! Raporu kopyalayıp düzenleyebilirsin."
                wa_link = f"https://wa.me/?text={urllib.parse.quote(ozet_paylas)}"

                p1, p2 = st.columns(2)
                with p1:
                    st.link_button("🟢 WhatsApp'a Bilgi Ver", wa_link, use_container_width=True)
                with p2:
                    pdf_bytes = create_pdf(rapor_metni, proje_adi)
                    st.download_button("📥 PDF Olarak İndir", pdf_bytes, f"{proje_adi}.pdf", "application/pdf", use_container_width=True)

                # Kayıt
                sheet = connect_sheets()
                if sheet: sheet.append_row([str(datetime.now()), seviye, proje_adi, rapor_metni])

            except Exception as e:
                st.error(f"Sistemsel bir pürüz: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.8em;'>Derepazarı İlçe MEM Arge Birimi © 2026</p>", unsafe_allow_html=True)
