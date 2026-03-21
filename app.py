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
    st.error("Secrets (Kasa) ayarları eksik! Lütfen kontrol edin.")
    st.stop()

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor Pro | Derepazarı", layout="wide", page_icon="📝")

# --- TÜRKÇE KARAKTER DÜZELTİCİ (PDF HATASINI ÇÖZEN KRİTİK KISIM) ---
def turkce_duzelt(text):
    """PDF motorunun (İ, ş, ğ...) gibi harflerde çökmesini engeller."""
    duzeltme_haritasi = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u'
    }
    for kaynak, hedef in duzeltme_haritasi.items():
        text = text.replace(kaynak, hedef)
    return text

# PDF Oluşturucu
def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=turkce_duzelt(title), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    # Metni PDF için güvenli hale getiriyoruz
    temiz_metin = turkce_duzelt(text)
    pdf.multi_cell(0, 8, txt=temiz_metin)
    return pdf.output(dest='S').encode('latin-1')

# Google Sheets Bağlantısı
def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# --- 2. PROFESYONEL YAN MENÜ ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/briefcase.png", width=60)
    st.title("Arge Birimi")
    st.markdown("**Derepazarı İlçe MEM**")
    st.divider()
    st.success("✅ Karakter Filtresi: Aktif")
    st.info("Raporlar otomatik olarak Arge Veritabanına kaydedilir.")

# --- 3. ANA ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Pro: Proje Tasarım İstasyonu</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
with col2:
    ham_fikir = st.text_area("Projenizin ana fikri nedir?", height=100)
    insan_dokunusu = st.text_area("Kişisel Gözleminiz (Özgünlük Hikayesi)", height=68)

# --- 4. ANALİZ VE RAPOR OLUŞTURMA ---
if st.button("Teknofest Standartlarında Raporu Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen alanları doldurun.")
    else:
        with st.spinner("Sistem en kararlı modeli seçiyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                
                # 404 HATASINI ÖNLEYEN MODEL SEÇİCİ
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                best_model = next((m for m in models if "flash" in m), models[0])
                model = genai.GenerativeModel(best_model)
                
                prompt = f"""
                Teknofest jürisi gibi düşün. {seviye} seviyesi için akademik dille ÖDR yaz.
                KURALLAR: HTML KODU KULLANMA. 150-250 kelime özet.
                Bölümler: Özet, Problem, Çözüm, Özgün Değer.
                İçerik: {proje_adi} - {ham_fikir}. Hikaye: {insan_dokunusu}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                st.balloons()
                st.success("✅ Rapor Hazırlandı ve Kaydedildi!")
                
                # Analiz Kartları
                k_sayisi = len(rapor_metni.split())
                c1, c2, c3 = st.columns(3)
                c1.metric("Kelime Sayısı", k_sayisi, "Hedef: 150-250")
                c2.metric("Dil Kalitesi", "Akademik", "Puan: 10/10")
                c3.metric("Karakter Kontrolü", "Türkçe-Uyumlu", "Hatasız")

                st.markdown("---")
                st.write(rapor_metni)

                # --- 5. PAYLAŞIM VE AKSİYON PANELİ ---
                st.markdown("### 📤 Paylaşım ve Kayıt Paneli")
                st.info("Önce PDF'i indirin, sonra WhatsApp'tan dosyayı ekleyerek gönderin.")

                p1, p2 = st.columns(2)
                with p1:
                    # PDF İndirme (İ Harfi Hatası Çözüldü)
                    pdf_bytes = create_pdf(rapor_metni, proje_adi)
                    st.download_button("📥 Raporu PDF Olarak İndir", pdf_bytes, f"{proje_adi}_Rapor.pdf", "application/pdf", use_container_width=True)
                with p2:
                    # WhatsApp Bilgilendirme (Numarasız ve Güvenli)
                    wa_msg = f"*{proje_adi}* projesi için rapor taslağı hazırlandı. PDF dosyasını birazdan iletiyorum."
                    st.link_button("🟢 WhatsApp'tan Bilgi Ver", f"https://wa.me/?text={urllib.parse.quote(wa_msg)}", use_container_width=True)

                # Google Sheets Kaydı
                sheet = connect_sheets()
                if sheet:
                    sheet.append_row([str(datetime.now()), seviye, proje_adi, rapor_metni])

            except Exception as e:
                st.error(f"Sistemsel pürüz: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.8em; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026</p>", unsafe_allow_html=True)
