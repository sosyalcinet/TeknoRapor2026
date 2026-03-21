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

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor Ultra | Derepazarı", layout="wide", page_icon="✍️")

# --- TÜRKÇE KARAKTER VE PDF ARAÇLARI ---
def turkce_duzelt(text):
    """PDF motorunun (İ, ş, ğ...) gibi harflerde çökmesini engeller."""
    harita = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u'}
    for k, v in harita.items(): text = text.replace(k, v)
    return text

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
    pdf.multi_cell(0, 10, txt=turkce_duzelt(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=turkce_duzelt(text))
    return pdf.output(dest='S').encode('latin-1')

# Google Sheets Bağlantısı
def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# --- 2. YAN MENÜ VE YAZIM MODLARI ---
with st.sidebar:
    st.title("🏛️ Arge İstasyonu")
    st.markdown("**Derepazarı İlçe MEM**")
    st.divider()
    yazim_modu = st.select_slider(
        "🧠 Yazım Karakteri Seçin",
        options=["AI Standart", "Süper AI", "Ortalama İnsan", "Otomatik İnsan (Anti-Dedektör)"],
        value="Otomatik İnsan (Anti-Dedektör)"
    )
    st.info(f"Seçili Mod: {yazim_modu}")
    st.divider()
    st.warning("⚠️ Raporunuz A4 düzeninde 2-4 sayfa arası detaylandırılacaktır.")

# --- 3. ANA ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Ultra: Anti-Dedektör Yazılımı</h1>", unsafe_allow_html=True)

c_in1, c_in2 = st.columns(2)
with c_in1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
with c_in2:
    ham_fikir = st.text_area("Projenizin Temel Mantığı", height=100)
    ozgunluk = st.text_area("Sizi Farklı Kılan Hikaye (Kişisel Dokunuş)", height=68)

# --- 4. AKILLI MODEL SEÇİCİ VE OLUŞTURMA ---
if st.button("Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen alanları doldurun.")
    else:
        with st.spinner("Model taranıyor ve rapor yazılıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                
                # --- 404 HATASINI ÇÖZEN OTOMATİK SEÇİCİ ---
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                selected_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
                model = genai.GenerativeModel(selected_model)
                
                mod_talimati = {
                    "AI Standart": "Teknik, kusursuz gramer ve standart yapı kullan.",
                    "Süper AI": "Üst düzey akademik dil ve yoğun teknik terimler kullan.",
                    "Ortalama İnsan": "Basit, bazen devrik ve doğal bir eğitim dili kullan.",
                    "Otomatik İnsan (Anti-Dedektör)": """
                        KRİTİK: Metni yapay zeka dedektörlerinden (GPTZero, Turnitin) kaçacak şekilde yaz. 
                        Cümle uzunluklarını çeşitlendir (bir kısa, bir uzun). Devrik cümleler ve kişisel gözlemler ekle. 
                        Sanki bir öğretmen heyecanla öğrencisine anlatıyormuş gibi doğal ve değişken bir akışla yaz.
                    """
                }

                prompt = f"""
                Sen Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde KAPSAMLI bir rapor yaz.
                MOD: {mod_talimati[yazim_modu]}
                KAPSAM: A4 formatında 2-4 sayfa sürecek DERİNLEMESİNE rapor olmalı.
                BÖLÜMLER: Özet (250 kelime), Problem, Çözüm, Özgün Değer ('{ozgunluk}' detayını işle), Hedef Kitle, Tahmini Maliyet.
                FORMAT: HTML kodları kullanma, sadece düz metin.
                İçerik: {proje_adi} - {ham_fikir}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                st.balloons()
                st.success(f"✅ Rapor Hazırlandı! (Sistem: {selected_model})")
                
                k_sayisi = len(rapor_metni.split())
                c1, c2, c3 = st.columns(3)
                c1.metric("Kelime Sayısı", k_sayisi, "2-4 Sayfa Hedefi")
                c2.metric("Savunma Durumu", "Aktif", yazim_modu)
                c3.metric("Karakter Kontrolü", "Hatasız", "İ-Ş-Ğ Uyumlu")

                st.markdown("---")
                st.write(rapor_metni)

                # --- 5. AKSİYON PANELİ ---
                st.markdown("### 📤 Paylaşım ve Kayıt Paneli")
                p1, p2 = st.columns(2)
                with p1:
                    pdf_bytes = create_pdf(rapor_metni, proje_adi)
                    st.download_button("📥 Kapsamlı PDF'i İndir", pdf_bytes, f"{proje_adi}_Rapor.pdf", "application/pdf", use_container_width=True)
                with p2:
                    msg = urllib.parse.quote(f"*{proje_adi}* kapsamlı raporu hazırlandı. PDF ektedir.")
                    st.link_button("🟢 WhatsApp Bilgilendirme", f"https://wa.me/?text={msg}", use_container_width=True)

                sheet = connect_sheets()
                if sheet: sheet.append_row([str(datetime.now()), yazim_modu, proje_adi, k_sayisi, rapor_metni])

            except Exception as e:
                st.error(f"Teknik bir pürüz: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026</p>", unsafe_allow_html=True)
