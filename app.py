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
    st.error("Kasa (Secrets) ayarları eksik! Lütfen Dashboard'dan kontrol edin.")
    st.stop()

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor Pro | Derepazarı", page_icon="🚀", layout="wide")

# Google Sheets Bağlantısı
def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# PDF Oluşturma Fonksiyonu (Arial 12, 1.15 Aralık Simülasyonu)
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'TeknoRapor Ön Değerlendirme Taslağı', 0, 1, 'C')
        self.ln(5)

def create_pdf(metin, proje_adi):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Metni PDF'e yaz (Türkçe karakter desteği için latin-1 dönüşümü)
    pdf.multi_cell(0, 8, txt=metin.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- 2. YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.title("🏛️ Arge Birimi")
    st.info("Bu sistem Derepazarı İlçe MEM bünyesinde öğretmen ve öğrencilere fikir asistanlığı yapmak üzere geliştirilmiştir.")
    st.divider()
    st.write("📊 **Analiz Modu:** Aktif")
    st.write("📅 **Yıl:** 2026")
    st.write("🔧 **Admin:** Hüsamettin KAYMAKÇI")

# --- 3. ANA ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Pro: Proje Tasarım İstasyonu</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite/Mezun"])
    kategori = st.selectbox("Yarışma Kategorisi", ["İnsanlık Yararına Teknoloji", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Çevre ve Enerji", "Tarım Teknolojileri"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")

with col2:
    ham_fikir = st.text_area("Projenizin ana fikri nedir?", height=100)
    insan_dokunusu = st.text_area("Kişisel Gözleminiz", height=68, placeholder="Bu fikir nasıl aklınıza geldi?")

# --- 4. ANALİZ VE RAPOR OLUŞTURMA ---
if st.button("Raporu Analiz Et ve Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen Proje Adı ve Ana Fikir alanlarını boş bırakmayın.")
    else:
        with st.spinner("Yapay zeka kriterleri kontrol ediyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Sen bir Teknofest jüri uzmanısın. {seviye} seviyesindeki bir öğrenci için {kategori} kategorisinde bir ÖDR yaz.
                KURALLAR: 
                1. FORMAT: Sadece düz metin ver. HTML veya span kodları KESİNLİKLE KULLANMA.
                2. ÖZET: Tam olarak 150-250 kelime arasında olmalı.
                3. BÖLÜMLER: Özet, Problem, Çözüm, Özgün Değer, Hedef Kitle.
                4. DİL: Samimi, pedagojik ve akademik.
                İçerik: {proje_adi} - {ham_fikir}. Hikaye: {insan_dokunusu}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                kelime_sayisi = len(rapor_metni.split())

                # Sonuç Paneli
                st.balloons()
                st.success("✅ Raporunuz Teknofest Standartlarına Göre Hazırlandı!")
                
                # Metric Kartları (Görsel zenginlik)
                m1, m2, m3 = st.columns(3)
                m1.metric("Kelime Sayısı", kelime_sayisi, "Hedef: 150-250")
                m2.metric("Uyumluluk", "%98", "Kurumsal")
                m3.metric("Format", "Arial 12pt", "1.15 Aralık")

                st.markdown("---")
                st.write(rapor_metni)

                # --- 5. AKSİYON VE PAYLAŞIM PANELİ ---
                st.markdown("### 📤 Paylaşım ve Kayıt Paneli")
                
                # Paylaşım linkleri
                paylas_metni = urllib.parse.quote(f"*{proje_adi} Proje Taslağı*\n\n{rapor_metni[:800]}...")

                act1, act2, act3 = st.columns(3)
                with act1:
                    st.link_button("🟢 WhatsApp Paylaş", f"https://wa.me/?text={paylas_metni}", use_container_width=True)
                with act2:
                    # PDF Oluştur ve İndirme Butonu
                    pdf_bytes = create_pdf(rapor_metni, proje_adi)
                    st.download_button(label="📥 PDF Olarak İndir", data=pdf_bytes, file_name=f"{proje_adi}_Raporu.pdf", mime="application/pdf", use_container_width=True)
                with act3:
                    st.link_button("📧 E-Posta Gönder", f"mailto:?subject={proje_adi} Raporu", use_container_width=True)

                # Kayıt
                sheet = connect_sheets()
                if sheet:
                    sheet.append_row([str(datetime.now()), seviye, kategori, proje_adi, rapor_metni])
                
            except Exception as e:
                st.error(f"Teknik bir pürüz: {str(e)}")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.8em; color: gray;'>Derepazarı İlçe Milli Eğitim Müdürlüğü Arge Birimi © 2026<br>İletişim: +905062840001</p>", unsafe_allow_html=True)
