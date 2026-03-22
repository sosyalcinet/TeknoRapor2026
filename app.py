import streamlit as st
import streamlit.components.v1 as components
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
    st.error("Secrets (Kasa) ayarları eksik! Lütfen kontrol edin.")
    st.stop()

st.set_page_config(page_title="TeknoRapor V1", layout="centered", page_icon="🤖")

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
    return temiz

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
    doc.add_paragraph(text.replace("**", "").replace("##", ""))
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
    st.write("Bu uygulamanın amacı; projenizi temel hatlarıyla yazıp içine birkaç fikir eklediğiniz anda, istediğiniz sayfa sayısı ve akademik ölçülere göre profesyonel bir rapor oluşturmaktır. Sistem, metni 'yapay zekadan çıkmamış' gibi doğal ve insansı bir dille hazırlar.")

with st.expander("2. ⚙️ Ayarlar (Rapor Kaç Sayfa Olsun?)"):
    hedef_sayfa = st.slider("Rapor Derinliği (Sayfa)", 1, 6, 3)

with st.expander("3. 🧠 Kişilik Modu"):
    yazim_modu = st.selectbox("Yazım Karakteri", ["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI", "AI Standart"], index=0)

with st.expander("4. 📝 Rapor Girişi (Ana Bölüm)", expanded=True):
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    proje_aciklamasi = st.text_area("Proje Açıklaması", height=150)
    ozgunluk = st.text_area("Kişisel Dokunuş / Hikaye", height=100)
    
    if st.button("🚀 Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True, type="primary"):
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen alanları doldurun.")
        else:
            with st.status("🛠️ Rapor hazırlanıyor...", expanded=True) as status:
                st.write("Yapay zeka şu an en insansı modu kurgulamak için düşünüyor...")
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Sen Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde {hedef_sayfa} sayfalık akademik bir ÖDR yaz. MOD: {yazim_modu}. Markdown işaretleri kullanma. İçerik: {proje_adi} - {proje_aciklamasi}. Özgünlük: {ozgunluk}"
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    st.session_state.p_adi = proje_adi
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Rapor Hazır!", state="complete")
                except Exception as e: st.error(str(e))

# --- 5. SONUÇ VE ÖZEL YAZDIRMA EKRANI ---
if "rapor_hazir" in st.session_state:
    metin = st.session_state.rapor_metni
    p_adi = st.session_state.p_adi
    temiz_metin = metin.replace("**", "").replace("##", "")
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Kelime", len(metin.split()))
    c2.metric("Savunma", "Aktif")
    c3.metric("Karakter", "Güvenli")

    st.markdown(f"""<div id='print_area' style='background:white; padding:30px; color:black; border:1px solid #ddd; font-family:Arial; line-height:1.6; text-align:justify;'>
    <h2 style='text-align:center;'>{p_adi.upper()}</h2><p>{temiz_metin.replace('\n', '<br>')}</p></div>""", unsafe_allow_html=True)

    st.markdown("### 📥 İşlemler")
    d1, d2, d3 = st.columns(3)
    with d1: st.download_button("📥 PDF İndir", create_pdf(temiz_metin, p_adi), f"{p_adi}.pdf", use_container_width=True)
    with d2: st.download_button("📥 Word İndir", create_word(temiz_metin, p_adi), f"{p_adi}.docx", use_container_width=True)
    with d3:
        if st.button("🖨️ Raporu Yazdır", use_container_width=True):
            print_html = f"<html><head><title>Yazdır</title><style>body{{font-family:Arial; padding:50px; line-height:1.6;}} h2{{text-align:center;}}</style></head><body><h2>{p_adi}</h2><p>{temiz_metin.replace('\n', '<br>')}</p><script>window.print();</script></body></html>"
            components.html(f"<iframe srcdoc=\"{print_html.replace('"', '&quot;')}\" style='display:none;'></iframe>", height=0)
            st.info("Yazdırma penceresi tetiklendi. (Eğer açılmazsa PDF indirip yazdırınız.)")

    st.markdown("---")
    email = st.text_input("📩 E-posta Taslağı Oluştur", placeholder="Adresinizi yazın...")
    if st.button("E-posta Gönder (Taslak Hazırla)", use_container_width=True):
        st.info("Not: Güvenlik nedeniyle dosya otomatik eklenemez. Lütfen metni kopyalayıp e-postanıza yapıştırın.")
        mailto_link = f"mailto:{email}?subject={urllib.parse.quote(p_adi)}%20Raporu&body={urllib.parse.quote(metin[:500])}..."
        st.link_button("📧 E-postayı Aç ve Metni Yapıştır", mailto_link, use_container_width=True)

# --- 6. SİSTEM VE FOOTER ---
st.markdown("---")
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔄 Yeni Rapor", use_container_width=True):
        st.session_state.clear()
        st.rerun()
with col_b2:
    davet = f"🚀 Teknofest projelerinizi hazırlamak için Hüsamettin KAYMAKÇI tarafından sunulan bu sistemi kullanın:\n\n🔗 https://teknorapor-derepazari.streamlit.app"
    st.link_button("🟢 Sistemi Paylaş", f"https://wa.me/?text={urllib.parse.quote(davet)}", use_container_width=True)

st.markdown(f"<p style='text-align:center; color:gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b><br><a href='mailto:sosyalcinet@gmail.com'>sosyalcinet@gmail.com</a> | <a href='https://t.me/sosyalcinet'>@sosyalcinet</a></p>", unsafe_allow_html=True)
