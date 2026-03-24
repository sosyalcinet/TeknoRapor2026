import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from io import BytesIO
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE AYARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Kasa (Secrets) ayarları bulunamadı! Lütfen kontrol edin.")
    st.stop()

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- KARAKTER VE BİÇİM TEMİZLEYİCİ ---
def format_temizle(text):
    temiz = text.replace("**", "").replace("##", "").replace("#", "").replace("__", "")
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
        '\u2019': "'", '\u2018': "'", '\u201d': '"', '\u201c': '"',
        '\u2013': "-", '\u2014': "-", '\u2022': "*", '\u2026': "..."
    }
    for k, v in harita.items(): temiz = temiz.replace(k, v)
    return temiz.encode('latin-1', 'replace').decode('latin-1')

# --- DOSYA OLUŞTURUCULAR ---
def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=format_temizle(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=format_temizle(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    temiz_word = text.replace("**", "").replace("##", "").replace("#", "")
    doc.add_paragraph(temiz_word)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def connect_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        return gspread.authorize(creds).open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# --- BAŞLIK ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Yapay Zeka Robotu V1</h1>", unsafe_allow_html=True)

# --- 2. AYARLAR MENÜSÜ (SAYI DÜĞMELERİ EKLENDİ) ---
with st.expander("⚙️ Rapor Ayarları", expanded=True):
    st.write("**Rapor Kaç Sayfa Olsun? (Sayı Seçin)**")
    # Sayı düğmeleri (Horizontal Radio Button)
    hedef_sayfa = st.radio(
        "Sayfa Sayısı", 
        options=[1, 2, 3, 4, 5, 6], 
        index=2, # Varsayılan 3 seçili gelir
        horizontal=True,
        label_visibility="collapsed"
    )
    st.info(f"Seçilen Derinlik: {hedef_sayfa} Sayfa")
    
    yazim_modu = st.selectbox(
        "Yazım Karakteri",
        options=["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI"],
        index=0
    )

# --- 4. RAPOR GİRİŞİ ---
with st.expander("📝 Proje ve Danışman Bilgileri (Resmi Taslak)", expanded=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    with col_f2:
        danisman_adi = st.text_input("Danışman Adı", placeholder="Hüsamettin KAYMAKÇI")
        takim_adi = st.text_input("Takım Adı", placeholder="Takım İsmi")
        takim_id = st.text_input("Takım ID", placeholder="T26-...")

    proje_aciklamasi = st.text_area("Proje Açıklaması (Fikrinizi buraya yazın)", height=150)
    ozgunluk = st.text_area("Kişisel Dokunuş / Hikaye", height=100)
    
    if st.button("🚀 Teknofest Standartlarında Raporu Hazırla", use_container_width=True, type="primary"):
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status("🛠️ Rapor hazırlanıyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde TAM {hedef_sayfa} SAYFA rapor yaz.
                    MOD: {yazim_modu}. Markdown işaretleri (** veya ##) KESİNLİKLE kullanma.
                    
                    RAPORUN BAŞINA ŞUNLARI KALIN (BOLD) HARFLERLE EKLE:
                    PROJE ADI: {proje_adi}
                    DANIŞMAN ADI: {danisman_adi}
                    TAKIM ADI: {takim_adi}
                    TAKIM ID: {takim_id}
                    KATEGORİ: {kategori}
                    ---
                    İçerik: {proje_adi} - {proje_aciklamasi}. Hikaye: {ozgunluk}
                    Bölümler: Özet, Problem, Çözüm, Özgün Değer, Hedef Kitle, Maliyet, Takvim.
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    st.session_state.p_adi_state = proje_adi
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Hazır!", state="complete")
                except Exception as e: st.error(str(e))

# --- 5. SONUÇ VE İSTATİSTİKLER ---
if "rapor_hazir" in st.session_state:
    metin = st.session_state.rapor_metni
    p_adi = st.session_state.p_adi_state
    temiz = metin.replace("**", "").replace("##", "").replace("#", "")
    
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px;'> <h2 style='text-align:center;'>{p_adi.upper()}</h2><p>{temiz.replace('\n', '<br>')}</p></div>", unsafe_allow_html=True)

    st.markdown("### 📥 İşlemler")
    c_down1, c_down2 = st.columns(2)
    with c_down1:
        st.download_button("📥 PDF İndir", create_pdf(temiz, p_adi), f"{p_adi}.pdf", use_container_width=True)
    with c_down2:
        st.download_button("📥 Word İndir", create_word(temiz, p_adi), f"{p_adi}.docx", use_container_width=True)

    try:
        sheet = connect_sheets()
        if sheet: sheet.append_row([str(datetime.now()), yazim_modu, p_adi, temiz[:30000]])
    except: pass

# --- 6. SİSTEM DÜĞMELERİ ---
st.markdown("---")
if st.button("🔄 Yeni Rapor (Sıfırla)", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# --- FOOTER ---
st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b></p>", unsafe_allow_html=True)
