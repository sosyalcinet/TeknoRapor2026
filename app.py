import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF  # Not: 'pip install fpdf2' tavsiye edilir
from docx import Document
from io import BytesIO
import urllib.parse

# --- 1. GÜVENLİK VE AYARLAR ---
# API Anahtarlarını doğrudan kodun içine yazmak yerine st.secrets kullanıyoruz.
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
    SHEET_KEY = "1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4" [cite: 3]
except Exception as e:
    st.error(f"Sistem ayarları (Secrets) okunamadı! Hata: {e}")
    st.stop()

# Sayfa Yapılandırması [cite: 1]
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- 2. YARDIMCI FONKSİYONLAR ---

def karakter_filtresi(text): [cite: 1, 2]
    """Türkçe karakterleri ve özel sembolleri standart hale getirir."""
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u'
    }
    for k, v in harita.items(): 
        text = text.replace(k, v)
    return text

def create_pdf(text, title): [cite: 2, 3]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=karakter_filtresi(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=karakter_filtresi(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title): [cite: 3]
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def save_to_sheets(data_row): [cite: 3]
    """Rapor verilerini Google Sheets'e kaydeder."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_KEY).sheet1
        sheet.append_row(data_row)
        return True
    except Exception as e:
        st.error(f"Google Sheets Kayıt Hatası: {e}")
        return False

# --- 3. KULLANICI ARAYÜZÜ ---

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Yapay Zeka Robotu V1</h1>", unsafe_allow_html=True) [cite: 4]

with st.expander("1. ℹ️ Açıklama"): [cite: 4]
    st.write("Profesyonel Teknofest raporları oluşturmak için gelişmiş yapay zeka modülü.")

with st.expander("2. ⚙️ Ayarlar (Rapor Kaç Sayfa Olsun?)"): [cite: 4, 5]
    hedef_sayfa = st.slider("Rapor Derinliği (Sayfa)", 1, 6, 3)

with st.expander("3. 🧠 Kişilik Modu"): [cite: 5]
    yazim_modu = st.selectbox(
        "Yazım Karakteri Seçin",
        options=["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI", "AI Standart"],
        index=0
    )

with st.expander("4. 📝 Rapor Girişi (Ana Bölüm)"): [cite: 6]
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    proje_aciklamasi = st.text_area("Proje Açıklaması (Temel Mantık)", height=150)
    ozgunluk = st.text_area("Kişisel Dokunuş / Hikaye", height=100)
    
    st.markdown("---")
    if st.button("🚀 Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True, type="primary"): [cite: 6]
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.") [cite: 7]
        else:
            with st.status("🛠️ Raporunuz hazırlanıyor...", expanded=True) as status: [cite: 7]
                try:
                    genai.configure(api_key=GEMINI_API_KEY) [cite: 8]
                    model = genai.GenerativeModel('gemini-1.5-flash') [cite: 9]
                    
                    hedef_kelime = hedef_sayfa * 450 [cite: 9]
                    prompt = f"""
                    Sen Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde TAM {hedef_sayfa} SAYFA (Yaklaşık {hedef_kelime} kelime) rapor yaz. [cite: 10]
                    MOD: {yazim_modu}. İnsansı yaz. [cite: 11]
                    BÖLÜMLER: Özet, Problem, Çözüm, Özgün Değer, Hedef Kitle, Maliyet, Takvim. [cite: 12]
                    İçerik: {proje_adi} - {proje_aciklamasi}. Hikaye: {ozgunluk} [cite: 12, 13]
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    
                    # Verileri Google Sheets'e Kaydet 
                    save_to_sheets([proje_adi, kategori, seviye, f"{hedef_sayfa} Sayfa", yazim_modu])
                    
                    st.session_state.rapor_hazir = True [cite: 14]
                    status.update(label="✅ Rapor Başarıyla Hazırlandı ve Kaydedildi!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Hata: {str(e)}")

# --- 4. SONUÇ VE İSTATİSTİKLER ---
if "rapor_hazir" in st.session_state and st.session_state.rapor_hazir: [cite: 14]
    st.markdown("---")
    metin = st.session_state.rapor_metni
    
    col_st1, col_st2, col_st3 = st.columns(3) [cite: 15]
    col_st1.metric("Toplam Kelime", len(metin.split()))
    col_st2.metric("Savunma", "Aktif" if "Anti-Dedektör" in yazim_modu else "Pasif")
    col_st3.metric("Karakter", "Güvenli")
    
    st.text_area("Rapor Önizleme", metin, height=300) [cite: 15]
    
    st.markdown("### 📥 Dosya İşlemleri") [cite: 15]
    c_down1, c_down2, c_down3 = st.columns(3)
    
    with c_down1:
        pdf_bytes = create_pdf(metin, proje_adi) [cite: 15, 16]
        st.download_button("📥 PDF İndir", pdf_bytes, f"{proje_adi}.pdf", "application/pdf", use_container_width=True)
    with c_down2:
        word_bytes = create_word(metin, proje_adi) [cite: 16]
        st.download_button("📥 Word İndir", word_bytes, f"{proje_adi}.docx", use_container_width=True)
    with c_down3:
        if st.button("🔄 Sıfırla", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- 5. FOOTER ---
st.markdown(f"""
<p style='text-align: center; color: gray; font-size: 0.9em;'>
    Derepazarı İlçe MEM Arge Birimi © 2026<br>
    <b>Hazırlayan: Hüsamettin KAYMAKÇI</b>
</p>
""", unsafe_allow_html=True) [cite: 18, 19]
