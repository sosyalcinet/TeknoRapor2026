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

# --- 1. GÜVENLİK VE ANAHTAR HAVUZU ---
# Sizin paylaştığınız anahtarı listenin başına ekledim. 
# Gelecekte yeni hesaplardan anahtar alırsanız bu listeye ekleyebilirsiniz.
API_ANAHTARLARI = [
    "AIzaSyAUTfWM9cDG4PyEPdo1m-Qqd7-ulPA2gUo"
]

try:
    # Google E-Tablo kayıtları için kimlik bilgileri
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    # Eğer Sheets ayarı yoksa sistem hata vermeden devam etsin
    GOOGLE_CREDS = None

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- KARAKTER VE BİÇİM FİLTRESİ ---
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
    if not GOOGLE_CREDS: return None
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
        return gspread.authorize(creds).open_by_key("1XSgC6lLDcuHjJ2eyj-bkIuoWW9bvulp4yo_SqeiVxL4").sheet1
    except: return None

# --- BAŞLIK (SABİT) ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Yapay Zeka Robotu V1</h1>", unsafe_allow_html=True)

# --- DÜĞME SİSTEMİ (EXPANDERS) ---
with st.expander("1. ℹ️ Açıklama"):
    st.write("Bu uygulamanın amacı; hazırlamış olduğunuz projenizi sisteme girdiğiniz anda, istediğiniz sayfa sayısı ve akademik ölçülere göre kapsamlı bir Teknofest raporu oluşturmaktır. Sistem, metni yapay zeka tespit araçlarına yakalanmayacak şekilde doğal bir dille kurgular.")

with st.expander("2. ⚙️ Ayarlar (Rapor Kaç Sayfa Olsun?)"):
    hedef_sayfa = st.slider("Rapor Derinliği (Sayfa)", 1, 6, 3)

with st.expander("3. 🧠 Kişilik Modu"):
    yazim_modu = st.selectbox("Yazım Karakteri", options=["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI", "AI Standart"], index=0)

with st.expander("4. 📝 Rapor Girişi (Ana Bölüm)", expanded=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    with col_f2:
        danisman_adi = st.text_input("Danışman Adı", placeholder="Ad Soyad")
        takim_adi = st.text_input("Takım Adı", placeholder="Takım İsmi")
        takim_id = st.text_input("Takım ID", placeholder="T26-...")

    aciklama = st.text_area("Proje Açıklaması", height=150)
    hikaye = st.text_area("Kişisel Dokunuş / Hikaye", height=100)
    
    if st.button("🚀 Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama or not proje_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status("🛠️ Rapor hazırlanıyor, lütfen bekleyiniz...", expanded=True) as status:
                success = False
                for key in API_ANAHTARLARI:
                    try:
                        genai.configure(api_key=key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""
                        Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde TAM {hedef_sayfa} SAYFA rapor yaz.
                        MOD: {yazim_modu}. Markdown işaretleri (** veya ##) KULLANMA.
                        
                        RAPORUN EN BAŞINA ŞUNLARI KALIN HARFLERLE EKLE:
                        - Proje Adı: {proje_adi}
                        - Danışman Adı: {danisman_adi}
                        - Takım Adı: {takim_adi}
                        - Takım ID: {takim_id}
                        ---
                        İçerik: {proje_adi} - {aciklama}. Hikaye: {hikaye}
                        """
                        response = model.generate_content(prompt)
                        st.session_state.rapor_metni = response.text
                        st.session_state.p_adi = proje_adi
                        st.session_state.rapor_hazir = True
                        success = True
                        break 
                    except exceptions.ResourceExhausted:
                        continue 
                    except Exception as e:
                        st.error(f"Pürüz: {str(e)}")
                        break

                if success:
                    status.update(label="✅ Rapor Başarıyla Hazırlandı!", state="complete")
                else:
                    st.error("⚠️ Günlük 20 giriş kotası dolmuştur.")
                    status.update(label="❌ Kota Sınırı", state="error")

# --- 5. SONUÇ VE ÇIKTILAR ---
if "rapor_hazir" in st.session_state:
    metin = st.session_state.rapor_metni
    p_adi = st.session_state.p_adi
    temiz = metin.replace("**", "").replace("##", "").replace("#", "")
    
    st.markdown("---")
    st.markdown(f"""
    <div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:5px; font-family:Arial; line-height:1.6; text-align:justify;'> 
        <h2 style='text-align:center; border-bottom: 2px solid #1E3A8A;'>{p_adi.upper()}</h2>
        <p>{temiz.replace('\n', '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📥 İşlemler")
    d1, d2 = st.columns(2)
    with d1: st.download_button("📥 PDF İndir", create_pdf(temiz, p_adi), f"{p_adi}.pdf", use_container_width=True)
    with d2: st.download_button("📥 Word İndir", create_word(temiz, p_adi), f"{p_adi}.docx", use_container_width=True)

    try:
        sheet = connect_sheets()
        if sheet: sheet.append_row([str(datetime.now()), yazim_modu, p_adi, temiz[:30000]])
    except: pass

# --- 6. SİSTEM VE FOOTER ---
st.markdown("---")
if st.button("🔄 Yeni Rapor", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.markdown(f"""
<p style='text-align: center; color: gray; font-size: 0.9em;'>
    Derepazarı İlçe MEM Arge Birimi © 2026<br>
    <b>Hazırlayan: Hüsamettin KAYMAKÇI</b><br>
    E-Posta: <a href='mailto:sosyalcinet@gmail.com'>sosyalcinet@gmail.com</a> | 
    Telegram: <a href='https://t.me/sosyalcinet'>@sosyalcinet</a>
</p>
""", unsafe_allow_html=True)
