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
    st.error("Secrets (Kasa) ayarları eksik!")
    st.stop()

st.set_page_config(page_title="TeknoRapor Ultra | Derepazarı", layout="wide", page_icon="✍️")

# --- KARAKTER TEMİZLEYİCİ (CRITICAL FIX) ---
def karakter_filtresi(text):
    """PDF'i çökerten tüm özel karakterleri (akıllı tırnak, uzun çizgi vb.) temizler."""
    # Türkçe Karakter Dönüşümü
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
        '\u2019': "'", '\u2018': "'", '\u201d': '"', '\u201c': '"', # Akıllı tırnaklar
        '\u2013': "-", '\u2014': "-", '\u2022': "*", '\u2026': "..." # Çizgiler ve noktalar
    }
    for kaynak, hedef in harita.items():
        text = text.replace(kaynak, hedef)
    
    # Kalan tüm Unicode karakterleri Latin-1 güvenli hale getir
    return text.encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'TEKNOFEST 2026 PROJE RAPOR TASLAGI', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

def create_pdf(text, title):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=karakter_filtresi(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    # Metni PDF'e yazmadan önce filtreden geçiriyoruz
    pdf.multi_cell(0, 7.5, txt=karakter_filtresi(text))
    return pdf.output(dest='S').encode('latin-1')

def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        return gspread.authorize(creds).open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.title("🏛️ Arge İstasyonu")
    st.markdown("**Derepazarı İlçe MEM**")
    st.divider()
    yazim_modu = st.select_slider(
        "🧠 Yazım Karakteri Seçin",
        options=["AI Standart", "Süper AI", "Ortalama İnsan", "Otomatik İnsan (Anti-Dedektör)"],
        value="Otomatik İnsan (Anti-Dedektör)"
    )
    st.info(f"Mod: {yazim_modu}")
    st.warning("⚠️ Rapor 2-4 sayfa arası derinlikte hazırlanacaktır.")

# --- 3. ANA ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Ultra: Dedektör Savunmalı Sistem</h1>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
with c2:
    ham_fikir = st.text_area("Projenizin Temel Mantığı", height=100)
    ozgunluk = st.text_area("Kişisel Dokunuş (Hikaye)", height=68)

# --- 4. MODEL SEÇİCİ VE OLUŞTURMA ---
if st.button("Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen alanları doldurun.")
    else:
        with st.spinner("Karakter analizi yapılıyor ve rapor yazılıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Otomatik model seçici
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                best_model = next((m for m in models if "flash" in m), models[0])
                model = genai.GenerativeModel(best_model)
                
                mod_talimati = {
                    "AI Standart": "Teknik, kusursuz gramer kullan.",
                    "Süper AI": "Üst düzey akademik dil ve yoğun teknik terimler kullan.",
                    "Ortalama İnsan": "Basit, bazen devrik ve doğal bir eğitim dili kullan.",
                    "Otomatik İnsan (Anti-Dedektör)": "Metni AI dedektörlerinden kaçacak şekilde; cümle uzunluklarını değiştirerek, devrik yapılar ve kişisel gözlemler ekleyerek yaz."
                }

                prompt = f"""
                Sen kıdemli bir Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde A4 formatında 3-4 sayfa sürecek DERİNLEMESİNE rapor yaz.
                YAZIM MODU: {mod_talimati[yazim_modu]}
                BÖLÜMLER: Özet (250 kelime), Problem, Çözüm, Özgün Değer ('{ozgunluk}' detayını işle), Hedef Kitle, Tahmini Maliyet.
                İçerik: {proje_adi} - {ham_fikir}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                st.balloons()
                st.success(f"✅ Rapor Hazırlandı! (Sistem: {best_model})")
                
                k_sayisi = len(rapor_metni.split())
                m1, m2, m3 = st.columns(3)
                m1.metric("Kelime Sayısı", k_sayisi)
                m2.metric("Savunma", "Aktif", yazim_modu)
                m3.metric("Karakter", "Güvenli", "UTF-8 Clean")

                st.markdown("---")
                st.write(rapor_metni)

                # --- 5. AKSİYON PANELİ ---
                st.markdown("### 📤 Paylaşım ve Kayıt")
                act1, act2 = st.columns(2)
                with act1:
                    pdf_bytes = create_pdf(rapor_metni, proje_adi)
                    st.download_button("📥 Kapsamlı PDF'i İndir", pdf_bytes, f"{proje_adi}_Rapor.pdf", "application/pdf", use_container_width=True)
                with act2:
                    msg = urllib.parse.quote(f"*{proje_adi}* kapsamlı raporu hazırlandı. PDF ektedir.")
                    st.link_button("🟢 WhatsApp Bilgilendirme", f"https://wa.me/?text={msg}", use_container_width=True)

                sheet = connect_sheets()
                if sheet: sheet.append_row([str(datetime.now()), yazim_modu, proje_adi, k_sayisi, rapor_metni])

            except Exception as e:
                st.error(f"Sistemsel pürüz: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026</p>", unsafe_allow_html=True)
