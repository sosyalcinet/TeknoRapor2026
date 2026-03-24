import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from docx import Document
from io import BytesIO
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE ANAHTARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
    SHEET_KEY = "1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4"
except Exception as e:
    st.error(f"Secrets ayarları eksik veya hatalı! Hata: {e}")
    st.stop()

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- 2. YARDIMCI FONKSİYONLAR ---

def karakter_filtresi(text):
    """Metni temizler ve Word uyumlu hale getirir."""
    return text.encode('utf-8', 'ignore').decode('utf-8')

def create_word(text, title, kategori, seviye):
    """Metni profesyonel bir Word dokümanına dönüştürür."""
    doc = Document()
    doc.add_heading(title, 0)
    
    p_info = doc.add_paragraph()
    p_info.add_run(f"Kategori: {kategori}\n").bold = True
    p_info.add_run(f"Eğitim Seviyesi: {seviye}\n").bold = True
    p_info.add_run(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    doc.add_page_break()
    
    # Başlıkları ve metni Word'e aktarma
    lines = text.split('\n')
    for line in lines:
        if line.startswith('## '):
            doc.add_heading(line.replace('## ', ''), level=2)
        elif line.startswith('# '):
            doc.add_heading(line.replace('# ', ''), level=1)
        elif line.strip():
            doc.add_paragraph(line)
            
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def save_to_sheets(data_row):
    """Verileri Google Sheets'e kaydeder."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_KEY).sheet1
        sheet.append_row([datetime.now().strftime('%Y-%m-%d %H:%M:%S')] + data_row)
        return True
    except:
        return False

# --- 3. ARAYÜZ ---

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Robotu V1</h1>", unsafe_allow_html=True)

with st.expander("📝 Rapor Girişi", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    with col2:
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Akıllı Tarım")
        hedef_sayfa = st.slider("Sayfa Sayısı", 1, 6, 3)

    proje_aciklamasi = st.text_area("Proje Özeti", height=150)
    yazim_modu = st.selectbox("Yazım Modu", ["Anti-Dedektör", "Akademik", "Süper AI"])
    
    if st.button("🚀 Word Raporunu Hazırla", use_container_width=True, type="primary"):
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen zorunlu alanları doldurun.")
        else:
            with st.status("🛠️ Rapor hazırlanıyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"Teknofest {seviye} {kategori} raporu yaz. Adı: {proje_adi}. İçerik: {proje_aciklamasi}. Mod: {yazim_modu}. Yaklaşık {hedef_sayfa} sayfa sürsün."
                    
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    save_to_sheets([proje_adi, kategori, seviye, yazim_modu])
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Hazır!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Hata: {e}")

# --- 4. SONUÇ ---
if "rapor_hazir" in st.session_state and st.session_state.rapor_hazir:
    st.markdown("---")
    st.text_area("Önizleme", st.session_state.rapor_metni, height=300)
    
    word_file = create_word(st.session_state.rapor_metni, proje_adi, kategori, seviye)
    
    st.download_button(
        label="📥 Microsoft Word (.docx) Olarak İndir",
        data=word_file,
        file_name=f"{proje_adi}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        type="primary"
    )

st.markdown("<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge © 2026</p>", unsafe_allow_html=True)
