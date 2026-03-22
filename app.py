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

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor V1", layout="centered", page_icon="🤖")

# --- YAZDIRMA İÇİN ÖZEL CSS (SADECE RAPORU YAZDIRIR) ---
st.markdown("""
<style>
@media print {
    /* Menüleri ve butonları gizle */
    header, [data-testid="stSidebar"], [data-testid="stExpander"], button, .stDownloadButton, .stButton {
        display: none !important;
    }
    /* Sadece rapor alanını göster */
    #print_area {
        display: block !important;
        border: none !important;
        padding: 0 !important;
        color: black !important;
    }
}
</style>
""", unsafe_allow_html=True)

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
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
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

# --- DÜĞME SİSTEMİ (EXPANDERS) ---
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
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status("🛠️ Rapor hazırlanıyor, lütfen bekleyiniz...", expanded=True) as status:
                st.write("Yapay zeka şu an düşünen modda en iyi işi çıkarmaya çalışıyor...")
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    # 404 HATASINI ÇÖZEN DİNAMİK MODEL SEÇİCİ
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    selected_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
                    model = genai.GenerativeModel(selected_model)
                    
                    hedef_kelime = hedef_sayfa * 450
                    prompt = f"Sen Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde {hedef_sayfa} sayfalık akademik bir ÖDR yaz. MOD: {yazim_modu}. Markdown işaretleri kullanma. İçerik: {proje_adi} - {proje_aciklamasi}. Özgünlük: {ozgunluk}"
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    st.session_state.p_adi = proje_adi
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Rapor Başarıyla Hazırlandı!", state="complete")
                except Exception as e: st.error(f"Sistemsel pürüz: {str(e)}")

# --- 5. SONUÇ VE İSTATİSTİKLER ---
if "rapor_hazir" in st.session_state:
    metin = st.session_state.rapor_metni
    p_adi = st.session_state.p_adi
    temiz_metin = metin.replace("**", "").replace("##", "")
    
    st.markdown("---")
    col_st1, col_st2, col_st3 = st.columns(3)
    col_st1.metric("Toplam Kelime", len(metin.split()))
    col_st2.metric("Savunma Durumu", "Aktif" if "Anti-Dedektör" in yazim_modu else "Pasif")
    col_st3.metric("Karakter Sağlığı", "Güvenli")
    
    # RAPOR ÖNİZLEME ALANI (A4 SİMÜLASYONU)
    st.markdown("### 📄 Rapor Önizleme")
    st.markdown(f"""
    <div id='print_area' style='background: white; padding: 40px; color: black; border: 1px solid #ddd; border-radius: 5px; font-family: Arial; line-height: 1.6; text-align: justify;'>
        <h2 style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px;">{p_adi.upper()}</h2>
        <p>{temiz_metin.replace('\n', '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📥 İşlemler")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("📥 PDF Olarak İndir", create_pdf(temiz_metin, p_adi), f"{p_adi}.pdf", "application/pdf", use_container_width=True)
    with d2:
        st.download_button("📥 Word Olarak İndir", create_word(temiz_metin, p_adi), f"{p_adi}.docx", use_container_width=True)
    with d3:
        if st.button("🖨️ Raporu Yazdır", use_container_width=True):
            # Tarayıcıya yazdırma komutu gönderir (CSS ile sadece rapor alanını seçer)
            components.html("<script>window.print();</script>", height=0)

    # E-posta Taslağı
    st.markdown("---")
    email_addr = st.text_input("📩 E-posta Taslağı Oluştur", placeholder="E-posta adresinizi yazın...")
    if st.button("E-posta Taslağı Hazırla", use_container_width=True):
        st.info("Güvenlik nedeniyle dosya otomatik eklenemez. Lütfen metni kopyalayıp e-postanıza yapıştırın.")
        mailto_link = f"mailto:{email_addr}?subject={urllib.parse.quote(p_adi)}%20Raporu&body={urllib.parse.quote(temiz_metin[:1000])}..."
        st.link_button("📧 E-postayı Aç", mailto_link, use_container_width=True)

    # Kayıt
    try:
        sheet = connect_sheets()
        if sheet: sheet.append_row([str(datetime.now()), yazim_modu, p_adi, temiz_metin[:30000]])
    except: pass

# --- 6. SİSTEM DÜĞMELERİ VE FOOTER ---
st.markdown("---")
c_sys1, c_sys2 = st.columns(2)
with c_sys1:
    if st.button("🔄 Yeni Rapor (Sıfırla)", use_container_width=True):
        st.session_state.clear()
        st.rerun()
with c_sys2:
    app_link = "https://teknorapor-derepazari.streamlit.app"
    davet = f"🚀 Teknofest projelerinizi hazırlamak için Hüsamettin KAYMAKÇI tarafından sunulan bu sistemi kullanın:\n\n🔗 {app_link}"
    st.link_button("🟢 Sistemi WhatsApp'ta Paylaş", f"https://wa.me/?text={urllib.parse.quote(davet)}", use_container_width=True)

st.markdown(f"""
<p style='text-align: center; color: gray; font-size: 0.9em;'>
    Derepazarı İlçe MEM Arge Birimi © 2026<br>
    <b>Hazırlayan: Hüsamettin KAYMAKÇI</b><br>
    E-Posta: <a href='mailto:sosyalcinet@gmail.com'>sosyalcinet@gmail.com</a> | 
    Telegram: <a href='https://t.me/sosyalcinet'>@sosyalcinet</a>
</p>
""", unsafe_allow_html=True)
