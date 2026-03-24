import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from io import BytesIO
from datetime import datetime
import urllib.parse
from google.api_core import exceptions

# --- 1. GÜVENLİK VE HAVUZ SİSTEMİ ---
try:
    # Birden fazla anahtarı liste olarak alıyoruz
    API_KEYS = st.secrets["GEMINI_API_KEYS"] 
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Secrets (Kasa) ayarları eksik! Lütfen 'GEMINI_API_KEYS' listesini kontrol edin.")
    st.stop()

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor V1", layout="centered", page_icon="🤖")

# --- FONKSİYONLAR ---
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

# --- DÜĞME SİSTEMİ ---
with st.expander("1. ℹ️ Açıklama"):
    st.write("Bu uygulama, hazırlamış olduğunuz projenizi yazarak içine birkaç fikir eklediğiniz anda istediğiniz sayfa sayısı ve ölçülere göre rapor oluşturabilen, yapay zekadan yapılmamış gibi hazırlayan bir sistemdir.")

with st.expander("2. ⚙️ Ayarlar (Rapor Sayfa Sayısı)"):
    hedef_sayfa = st.slider("Rapor Derinliği (Sayfa)", 1, 6, 3)

with st.expander("3. 🧠 Kişilik Modu"):
    yazim_modu = st.selectbox("Yazım Karakteri", options=["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI", "AI Standart"], index=0)

with st.expander("4. 📝 Rapor Girişi (Ana Bölüm)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
        proje_adi = st.text_input("Proje Adı")
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        takim_id = st.text_input("Takım ID")

    aciklama = st.text_area("Proje Açıklaması", height=150)
    hikaye = st.text_area("Kişisel Dokunuş / Hikaye", height=100)
    
    if st.button("🚀 Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama or not proje_adi:
            st.warning("Lütfen alanları doldurun.")
        else:
            with st.status("🛠️ Raporunuz hazırlanıyor, lütfen bekleyiniz...", expanded=True) as status:
                st.write("Yapay zeka en iyi işi çıkarmaya çalışıyor...")
                
                success = False
                # --- ANAHTAR HAVUZU DÖNGÜSÜ ---
                for key in API_KEYS:
                    try:
                        genai.configure(api_key=key)
                        # 404 HATASINI ÖNLEYEN SABİT MODEL İSMİ
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""
                        Resmi Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde TAM {hedef_sayfa} SAYFA rapor yaz.
                        MOD: {yazim_modu}. Markdown işaretleri (** veya ##) KULLANMA.
                        BAŞLIK BİLGİLERİ (KALIN): Proje: {proje_adi}, Danışman: {danisman}, Takım: {takim}, ID: {takim_id}
                        İçerik: {proje_adi} - {aciklama}. Hikaye: {hikaye}
                        """
                        response = model.generate_content(prompt)
                        st.session_state.rapor_metni = response.text
                        st.session_state.p_adi = proje_adi
                        st.session_state.rapor_hazir = True
                        success = True
                        break # Başarılı olursa döngüden çık
                    except exceptions.ResourceExhausted:
                        continue # Kota dolmuşsa sıradaki anahtara geç
                    except Exception as e:
                        st.error(f"Sistemsel pürüz: {str(e)}")
                        break

                if success:
                    status.update(label="✅ Rapor Hazır!", state="complete")
                else:
                    st.error("⚠️ Tüm anahtarların günlük 20 giriş kotası dolmuştur.")
                    status.update(label="❌ Kota Sınırı", state="error")

# --- 5. SONUÇLAR ---
if "rapor_hazir" in st.session_state:
    metin = st.session_state.rapor_metni
    p_adi = st.session_state.p_adi
    temiz = metin.replace("**", "").replace("##", "")
    
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd;'> <h2 style='text-align:center;'>{p_adi.upper()}</h2><p>{temiz.replace('\n', '<br>')}</p></div>", unsafe_allow_html=True)

    st.markdown("### 📥 İşlemler")
    d1, d2 = st.columns(2)
    with d1: st.download_button("📥 PDF İndir", create_pdf(temiz, p_adi), f"{p_adi}.pdf", use_container_width=True)
    with d2: st.download_button("📥 Word İndir", create_word(temiz, p_adi), f"{p_adi}.docx", use_container_width=True)

    try:
        sheet = connect_sheets()
        if sheet: sheet.append_row([str(datetime.now()), yazim_modu, p_adi, temiz[:30000]])
    except: pass

# --- 6. FOOTER ---
st.markdown("---")
if st.button("🔄 Yeni Rapor", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.markdown(f"<p style='text-align:center; color:gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b><br>sosyalcinet@gmail.com | @sosyalcinet</p>", unsafe_allow_html=True)
