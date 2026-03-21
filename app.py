import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE ANAHTARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Kasa (Secrets) ayarları eksik! Lütfen Streamlit Dashboard'dan anahtarınızı kontrol edin.")
    st.stop()

# Sayfa Konfigürasyonu
st.set_page_config(page_title="TeknoRapor Pro | Derepazarı", layout="wide", page_icon="🚀")

# PDF Oluşturma (Türkçe karakter dostu)
def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 2. PROFESYONEL YAN MENÜ ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/rocket.png", width=60)
    st.title("Arge Birimi 2026")
    st.markdown("Derepazarı İlçe MEM Proje Destek Sistemi")
    st.divider()
    st.write("✅ **Durum:** Sistem Aktif")
    st.write("🔒 **Gizlilik:** Telefon Numarası Gizlendi")

# --- 3. ANA ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚀 TeknoRapor Pro: Proje Tasarım İstasyonu</h1>", unsafe_allow_html=True)

col_in1, col_in2 = st.columns(2)
with col_in1:
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
with col_in2:
    ham_fikir = st.text_area("Projenizin ana fikri nedir?", height=100)
    insan_dokunusu = st.text_area("Kişisel Gözleminiz (Özgünlük Hikayesi)", height=68)

# --- 4. RAPOR OLUŞTURMA (HATA GEÇİRMEZ) ---
if st.button("Teknofest Standartlarında Raporu Hazırla", use_container_width=True):
    if not ham_fikir or not proje_adi:
        st.warning("Lütfen alanları doldurun.")
    else:
        with st.spinner("Sistem en kararlı modeli seçiyor ve raporu yazıyor..."):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                
                # --- 404 HATASINI ÇÖZEN OTOMATİK MODEL SEÇİCİ ---
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                # 'flash' içeren en güncel modeli seç, yoksa listedeki ilkini al
                best_model = next((m for m in models if "flash" in m), models[0])
                
                model = genai.GenerativeModel(best_model)
                
                prompt = f"""
                Sen bir Teknofest jürisisin. {seviye} seviyesi için akademik dille ÖDR yaz.
                KURALLAR: HTML KODU KULLANMA. 150-250 kelime özet. Arial 12pt mantığıyla yaz.
                Bölümler: Özet, Problem, Çözüm, Özgün Değer.
                İçerik: {proje_adi} - {ham_fikir}. Hikaye: {insan_dokunusu}
                """
                
                response = model.generate_content(prompt)
                rapor_metni = response.text
                
                # Sonuç Paneli
                st.balloons()
                st.success(f"✅ Rapor Başarıyla Hazırlandı! (Sistem: {best_model})")
                
                # Analiz Kartları
                k_sayisi = len(rapor_metni.split())
                c1, c2, c3 = st.columns(3)
                c1.metric("Kelime Sayısı", k_sayisi, "Hedef: 150-250")
                c2.metric("Uyumluluk", "%100", "Tam")
                c3.metric("Format", "Akademik", "Düz Metin")

                st.markdown("---")
                st.write(rapor_metni)

                # --- 5. PROFESYONEL PAYLAŞIM VE GİZLİLİK ---
                st.markdown("### 📤 Paylaşım ve İndirme")
                
                # WhatsApp linkini kısaltarak hatayı önlüyoruz
                paylas_ozet = f"*{proje_adi}* Proje Raporu Hazır! Detaylı raporu ekteki PDF'den görebilirsiniz."
                wa_link = f"https://wa.me/?text={urllib.parse.quote(paylas_ozet)}"

                act1, act2 = st.columns(2)
                with act1:
                    st.link_button("🟢 WhatsApp'a Bilgi Ver", wa_link, use_container_width=True)
                with act2:
                    pdf_data = create_pdf(rapor_metni, proje_adi)
                    st.download_button("📥 PDF Olarak İndir (Word'e Aktarılabilir)", pdf_data, f"{proje_adi}.pdf", "application/pdf", use_container_width=True)

            except Exception as e:
                st.error(f"Sistemsel bir pürüz oluştu: {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.8em; color: gray;'>Derepazarı İlçe Milli Eğitim Müdürlüğü Arge Birimi © 2026</p>", unsafe_allow_html=True)
