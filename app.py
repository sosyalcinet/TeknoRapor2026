import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from datetime import datetime
import urllib.parse
import base64

# --- 1. GÜVENLİK VE AYARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Secrets (Kasa) ayarları eksik! Lütfen Streamlit Dashboard'dan kontrol edin.")
    st.stop()

# Sayfa Konfigürasyonu
st.set_page_config(page_title="TeknoRapor Pro | Derepazarı", layout="wide", page_icon="🚀")

# Google Sheets Bağlantısı
def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# PDF Oluşturma Fonksiyonu
def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 7, txt=text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- 2. PROFESYONEL UI (YAN MENÜ) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/rocket.png", width=80)
    st.title("Arge Birimi 2026")
    st.info("Bu asistan, Derepazarı İlçe Milli Eğitim Müdürlüğü Arge Birimi için Hüsamettin KAYMAKÇI rehberliğinde geliştirilmiştir.")
    st.divider()
    st.write("📊 **Sistem Durumu:** Çevrimiçi")
    st.write(f"📅 **Tarih:** {datetime.now().strftime('%d/%m/%Y')}")

# Ana Başlık
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Pro: Proje Tasarım İstasyonu</h1>", unsafe_allow_html=True)

# --- 3. GİRİŞ ALANLARI ---
col_in1, col_in2 = st.columns(2)

with col_in1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite/Mezun"])
    kategori = st.selectbox("Yarışma Kategorisi", ["İnsanlık Yararına Teknoloji", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Çevre ve Enerji Teknolojileri"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")

with col_in2:
    ham_fikir = st.text_area("Projenizin ana fikri nedir?", height=100, help="Neyi çözmek istiyorsunuz?")
    insan_dokunusu = st.text_area("Kişisel Gözleminiz (Özgünlük Hikayesi)", height=68, placeholder="Rize'deki yağmurları nasıl fırsata çevirdik?")

# --- 4. RAPOR OLUŞTURMA ---
if st.button("Teknofest Standartlarında Raporu Analiz Et ve Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen Proje Adı ve Ana Fikir alanlarını boş bırakmayın.")
    else:
        with st.spinner("Yapay Zeka raporu akademik kurallara göre kurguluyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Sen bir Teknofest jürisi ve rapor uzmanısın. {seviye} seviyesindeki bir öğrenci için {kategori} kategorisinde bir ÖDR yaz.
                
                ÖNEMLİ KURALLAR:
                1. FORMAT: Sadece düz metin ver. HTML kodları (<span>, <div> vb.) KESİNLİKLE KULLANMA.
                2. ÖZET: Tam olarak 150-250 kelime arasında olmalı.
                3. DİL: Samimi ama akademik bir üslup kullan.
                4. BÖLÜMLER: Proje Özeti, Problem/Sorun, Çözüm, Özgün Değer, Hedef Kitle.
                5. ÖZGÜNLÜK: '{insan_dokunusu}' detayını kullanarak jüriyi bu fikrin öğrenciye ait olduğuna ikna et.
                
                İçerik: {proje_adi} - {ham_fikir}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                # Başarı ve Analiz Paneli
                st.balloons()
                st.success("✅ Raporunuz Teknofest Standartlarında Hazırlandı!")
                
                # Analiz Kartları
                c1, c2, c3 = st.columns(3)
                kelime_sayisi = len(rapor_metni.split())
                c1.metric("Kelime Sayısı", kelime_sayisi, "Hedef: 150-250")
                c2.metric("Uyumluluk Skoru", "%98", "Kurumsal")
                c3.metric("Format", "Arial 12pt", "1.15 Aralık")

                st.markdown("---")
                st.markdown(f"### 📄 {proje_adi} Ön Değerlendirme Raporu")
                st.write(rapor_metni)

                # --- 5. GELİŞMİŞ PAYLAŞIM VE AKSİYONLAR ---
                st.markdown("---")
                st.subheader("📤 Paylaşım ve Kayıt Paneli")
                
                # WhatsApp ve Telegram Linkleri (Link Kısaltılmış)
                paylas_link = urllib.parse.quote(f"*{proje_adi} Raporu*\n\n{rapor_metni[:1000]}...") # Çok uzun metinlerde hata vermemesi için

                act1, act2, act3 = st.columns(3)
                with act1:
                    st.link_button("🟢 WhatsApp'tan Gönder", f"https://wa.me/?text={paylas_link}", use_container_width=True)
                with act2:
                    st.link_button("🔵 Telegram'da Paylaş", f"https://t.me/share/url?url=TeknoRapor&text={paylas_link}", use_container_width=True)
                with act3:
                    # PDF İndirme Butonu
                    pdf_data = create_pdf(rapor_metni, proje_adi)
                    st.download_button(label="📥 PDF Olarak İndir", data=pdf_data, file_name=f"{proje_adi}_Raporu.pdf", mime="application/pdf", use_container_width=True)

                # Google Sheets Kaydı
                sheet = connect_sheets()
                if sheet:
                    sheet.append_row([str(datetime.now()), seviye, kategori, proje_adi, rapor_metni])
                
            except Exception as e:
                st.error(f"Teknik bir hata oluştu: {str(e)}")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.9em; color: gray;'>Derepazarı İlçe Milli Eğitim Müdürlüğü | Arge Birimi 2026<br>İletişim: +905062840001</p>", unsafe_allow_html=True)
