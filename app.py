import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
st.set_page_config(page_title="TeknoRapor V1 | Resmi Şablon", layout="centered", page_icon="🤖")

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
    # Başlık Arial Black, 14 punto
    heading = doc.add_heading(title, 0)
    # İçerik Arial, 12 punto, 1.15 satır aralığı kuralına uygun
    temiz_word = text.replace("**", "").replace("##", "").replace("#", "")
    p = doc.add_paragraph(temiz_word)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
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
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest ÖDR Otomatik Rapor Robotu</h1>", unsafe_allow_html=True)

# --- AYARLAR ---
with st.expander("⚙️ Rapor Derinliği ve Karakter", expanded=True):
    st.write("**Rapor Kaç Sayfa Olsun?**")
    hedef_sayfa = st.radio("Sayfa Sayısı", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True, label_visibility="collapsed")
    yazim_modu = st.selectbox("Yazım Karakteri", options=["Otomatik İnsan (Anti-Dedektör)", "Akademik/Resmi", "Süper AI"], index=0)

# --- RAPOR GİRİŞİ ---
with st.expander("📝 Proje ve Takım Bilgileri", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
        proje_adi = st.text_input("Proje Adı (Zorunlu)")
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        takim_id = st.text_input("Takım/Başvuru ID")

    aciklama = st.text_area("Proje Özeti ve Kapsamı (Ana Fikir)", height=150)
    ozgunluk = st.text_area("Problemin Tanımı ve Özgün Değer (Opsiyonel)", height=100)
    
    if st.button("🚀 Resmi Şablona Göre Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama or not proje_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status("🛠️ Resmi kriterler analiz ediliyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Resmi şablonlardaki 7 ana bölüm ve puanlama kriterleri baz alındı
                    prompt = f"""
                    Sen bir Teknofest danışmanısın. {seviye} seviyesi {kategori} kategorisi için resmi ÖDR şablonuna göre rapor yaz.
                    Sayfa Hedefi: {hedef_sayfa}. MOD: {yazim_modu}. Markdown kullanma.
                    
                    AŞAĞIDAKİ BÖLÜMLERİ EKSİKSİZ OLUŞTUR:
                    1. KAPAK VE İÇİNDEKİLER (Özet sayfa)
                    2. PROJE ÖZETİ (Amacı, Kapsamı, Hedef Kitlesi)
                    3. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ (Gerçek yaşamdaki sorun ve çözümün mantığı)
                    4. ÖZGÜN DEĞER, UYGULANABİLİRLİK VE SÜRDÜRÜLEBİLİRLİK
                    5. PROJENİN HAZIRLANIŞ SÜRECİ VE ÇALIŞMA YÖNTEMİ
                    6. PROJE TAKIMI (Tablo formatında görev dağılımı)
                    7. KAYNAKLAR
                    
                    EĞER ŞU BİLGİLER EKSİKSE [BURAYA ... YAZINIZ] İBARESİ KOY:
                    Proje: {proje_adi if proje_adi else '[BURAYA PROJE ADINI YAZINIZ]'}
                    Danışman: {danisman if danisman else '[BURAYA DANIŞMAN ADINI YAZINIZ]'}
                    Takım: {takim if takim else '[BURAYA TAKIM ADINI YAZINIZ]'}
                    ID: {takim_id if takim_id else '[BURAYA ID YAZINIZ]'}
                    
                    İçerik Temeli: {aciklama}. Özgünlük: {ozgunluk}
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    st.session_state.p_adi_state = proje_adi
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Rapor Şablona Uygun Hazırlandı!", state="complete")
                except Exception as e: st.error(str(e))

# --- ÇIKTILAR ---
if "rapor_hazir" in st.session_state:
    metin = st.session_state.rapor_metni
    p_adi = st.session_state.p_adi_state
    temiz = metin.replace("**", "").replace("##", "")
    
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'> <h2 style='text-align:center;'>{p_adi.upper()}</h2><p>{temiz.replace('\n', '<br>')}</p></div>", unsafe_allow_html=True)

    st.markdown("### 📥 Resmi Çıktılar")
    c1, c2 = st.columns(2)
    with c1: st.download_button("📥 PDF (Arial Format)", create_pdf(temiz, p_adi), f"{p_adi}.pdf", use_container_width=True)
    with c2: st.download_button("📥 Word (Arial 12pt)", create_word(temiz, p_adi), f"{p_adi}.docx", use_container_width=True)

    try:
        sheet = connect_sheets()
        if sheet: sheet.append_row([str(datetime.now()), yazim_modu, p_adi, temiz[:30000]])
    except: pass

st.markdown("---")
if st.button("🔄 Yeni Rapor Başlat", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b></p>", unsafe_allow_html=True)
