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
st.set_page_config(page_title="TeknoRapor Ultra | Derepazarı", layout="wide", page_icon="✍️")

# --- TÜRKÇE KARAKTER VE PDF ARAÇLARI ---
def turkce_duzelt(text):
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
    # A4 Standartlarına uygun satır aralığı (1.15 simülasyonu)
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
    
    # YAZIM MODU SEÇİMİ
    yazim_modu = st.select_slider(
        "🧠 Yazım Karakteri Seçin",
        options=["AI Standart", "Süper AI", "Ortalama İnsan", "Otomatik İnsan (Anti-Dedektör)"],
        value="Otomatik İnsan (Anti-Dedektör)"
    )
    st.info(f"Seçili Mod: {yazim_modu}")
    st.divider()
    st.warning("⚠️ Raporunuz A4 düzeninde 2-4 sayfa arası (800-1200 kelime) detaylandırılacaktır.")

# --- 3. ANA ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Ultra: Anti-Dedektör Proje Yazımı</h1>", unsafe_allow_html=True)

c_in1, c_in2 = st.columns(2)
with c_in1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
with c_in2:
    ham_fikir = st.text_area("Projenin Temel Mantığı", height=100)
    ozgunluk = st.text_area("Sizi Farklı Kılan Hikaye (Kişisel Dokunuş)", height=68)

# --- 4. AKILLI PROMPT VE OLUŞTURMA ---
if st.button("Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen temel alanları doldurun.")
    else:
        with st.spinner("Dedektör savunması aktif ediliyor ve kapsamlı rapor yazılıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Modlara Göre Prompt Ayarı
                mod_talimati = {
                    "AI Standart": "Teknik, kusursuz gramer ve standart yapı kullan.",
                    "Süper AI": "Çok karmaşık terimler, yoğun veri analizi ve üst düzey akademik dil kullan.",
                    "Ortalama İnsan": "Basit cümleler, bazen devrik yapılar ve günlük eğitim dili kullan.",
                    "Otomatik İnsan (Anti-Dedektör)": """
                        KRİTİK: Metni yapay zeka dedektörlerinden (GPTZero, Turnitin) kaçacak şekilde yaz. 
                        Bunun için; cümle uzunluklarını sürekli değiştir (biri kısa, biri uzun), 
                        devrik cümleler kullan, bölgesel/kişisel anekdotlar ekle, 'perplexity'yi yükselt. 
                        Sanki bir öğretmen heyecanla öğrencisine anlatıyormuş gibi doğal ve burstiness seviyesi yüksek yaz.
                    """
                }

                prompt = f"""
                Sen kıdemli bir Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde DETAYLI bir rapor yaz.
                
                YAZIM MODU TALİMATI: {mod_talimati[yazim_modu]}
                
                KAPSAM: Bu kısa bir özet değil, A4 formatında 3 sayfa sürecek DERİNLEMESİNE bir rapor olmalı.
                BÖLÜMLER: 
                1. Proje Özeti (250 kelime), 
                2. Problem Tanımı (Detaylı), 
                3. Çözüm Önerisi (Teknik ve Uygulama adımları), 
                4. Özgün Değer ve Yenilikçi Yön (Burada '{ozgunluk}' detayını işle), 
                5. Hedef Kitle ve Yaygın Etki,
                6. Kullanılacak Materyaller ve Tahmini Maliyet.
                
                FORMAT: Sadece düz metin ver. HTML kodları KESİNLİKLE kullanma.
                İçerik: {proje_adi} - {ham_fikir}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                # Başarı Ekranı
                st.balloons()
                st.success(f"✅ {yazim_modu} Modunda Kapsamlı Rapor Hazırlandı!")
                
                # Analiz
                k_sayisi = len(rapor_metni.split())
                sayfa_tahmini = round(k_sayisi / 400, 1) # ~400 kelime 1 sayfa
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Kelime Sayısı", k_sayisi, "2-4 Sayfa Hedefi")
                c2.metric("Tahmini A4 Sayfası", f"{sayfa_tahmini} Sayfa")
                c3.metric("Savunma Durumu", "Aktif", yazim_modu)

                st.markdown("---")
                st.write(rapor_metni)

                # --- 5. AKSİYON PANELİ ---
                st.markdown("### 📤 Paylaşım ve İndirme")
                p1, p2 = st.columns(2)
                with p1:
                    pdf_bytes = create_pdf(rapor_metni, proje_adi)
                    st.download_button("📥 Kapsamlı Raporu PDF Olarak İndir", pdf_bytes, f"{proje_adi}_Final_Rapor.pdf", "application/pdf", use_container_width=True)
                with p2:
                    msg = f"*{proje_adi}* kapsamlı proje raporu {yazim_modu} modunda hazırlandı. PDF ektedir."
                    st.link_button("🟢 WhatsApp Bilgilendirme", f"https://wa.me/?text={urllib.parse.quote(msg)}", use_container_width=True)

                # Sheets Kaydı
                sheet = connect_sheets()
                if sheet: sheet.append_row([str(datetime.now()), yazim_modu, proje_adi, k_sayisi, rapor_metni])

            except Exception as e:
                st.error(f"Sistemsel pürüz: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026</p>", unsafe_allow_html=True)
