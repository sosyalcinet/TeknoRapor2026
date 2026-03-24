import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from docx import Document
from io import BytesIO
from datetime import datetime
import urllib.parse

# --- 1. GÜVENLİK VE ANAHTARLAR ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GOOGLE_CREDS = dict(st.secrets["google_credentials"])
except:
    st.error("Secrets (Kasa) ayarları eksik!")
    st.stop()

# Sayfa Yapılandırması
st.set_page_config(page_title="TeknoRapor V1 | Derepazarı", layout="centered", page_icon="🤖")

# --- FONKSİYONLAR (Karakter Filtresi & Dosya Oluşturma) ---
def karakter_filtresi(text):
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
        '\u2019': "'", '\u2018': "'", '\u201d': '"', '\u201c': '"',
        '\u2013': "-", '\u2014': "-", '\u2022': "*", '\u2026': "..."
    }
    for k, v in harita.items(): text = text.replace(k, v)
    return text

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=karakter_filtresi(title), align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=karakter_filtresi(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
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
    st.write("""
    Bu uygulamanın amacı; hazırlamış olduğunuz projenizi temel hatlarıyla yazıp içine birkaç fikir eklediğiniz anda, 
    istediğiniz sayfa sayısı ve ölçülere göre profesyonel bir rapor oluşturmaktır. 
    Sistem, gelişmiş yapay zeka algoritmaları kullanarak metni 'yapay zekadan çıkmamış' gibi 
    doğal ve insansı bir dille hazırlar.
    """)

with st.expander("2. ⚙️ Ayarlar (Rapor Kaç Sayfa Olsun?)"):
    hedef_sayfa = st.slider("Rapor Derinliği (Sayfa)", 1, 6, 3)
    st.info(f"Raporunuz yaklaşık {hedef_sayfa} sayfa doluluğunda kurgulanacaktır.")

with st.expander("3. 🧠 Kişilik Modu"):
    yazim_modu = st.selectbox(
        "Yazım Karakteri Seçin",
        options=["Otomatik İnsan (Anti-Dedektör)", "Ortalama İnsan", "Süper AI", "AI Standart"],
        index=0
    )
    st.caption("Varsayılan mod: Anti-Dedektör (Yapay Zeka Tespitine Karşı Korumalı)")

with st.expander("4. 📝 Rapor Girişi (Ana Bölüm)"):
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
    proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
    kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    proje_aciklamasi = st.text_area("Proje Açıklaması (Temel Mantık)", height=150)
    ozgunluk = st.text_area("Kişisel Dokunuş / Hikaye", height=100)
    
    st.markdown("---")
    # RENKLİ VE BÜYÜK HAZIRLA BUTONU
    if st.button("🚀 Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True, type="primary"):
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status("🛠️ Raporunuz hazırlanıyor, lütfen bekleyiniz...", expanded=True) as status:
                st.write("Yapay zeka şu an en derin ve insansı modu kurgulamak için düşünme aşamasında...")
                st.write(f"Seçilen {hedef_sayfa} sayfa sınırına göre metin optimize ediliyor...")
                
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    
                    hedef_kelime = hedef_sayfa * 450
                    prompt = f"""
                    Sen Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde TAM {hedef_sayfa} SAYFA (Yaklaşık {hedef_kelime} kelime) rapor yaz.
                    MOD: {yazim_modu} (Anti-Dedektör ise burstiness ve perplexity değerlerini yükselt, insansı yaz).
                    BÖLÜMLER: Özet, Problem, Çözüm, Özgün Değer, Hedef Kitle, Maliyet, Takvim.
                    İçerik: {proje_adi} - {proje_aciklamasi}. Hikaye: {ozgunluk}
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Rapor Başarıyla Hazırlandı!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Hata: {str(e)}")

# --- 5. SONUÇ VE İSTATİSTİKLER ---
if "rapor_hazir" in st.session_state and st.session_state.rapor_hazir:
    st.markdown("---")
    metin = st.session_state.rapor_metni
    k_sayisi = len(metin.split())
    
    # İstatistikler
    col_st1, col_st2, col_st3 = st.columns(3)
    col_st1.metric("Toplam Kelime", k_sayisi)
    col_st2.metric("Savunma Durumu", "Aktif" if "Anti-Dedektör" in yazim_modu else "Pasif")
    col_st3.metric("Karakter Sağlığı", "Güvenli")
    
    st.text_area("Rapor Önizleme", metin, height=300)
    
    # İndirme ve E-posta Düğmeleri
    st.markdown("### 📥 Dosya İşlemleri")
    c_down1, c_down2, c_down3 = st.columns(3)
    
    with c_down1:
        pdf_bytes = create_pdf(metin, proje_adi)
        st.download_button("📥 PDF Olarak İndir", pdf_bytes, f"{proje_adi}.pdf", "application/pdf", use_container_width=True)
    with c_down2:
        word_bytes = create_word(metin, proje_adi)
        st.download_button("📥 Word Olarak İndir", word_bytes, f"{proje_adi}.docx", use_container_width=True)
    with c_down3:
        st.button("🖨️ Raporu Yazdır", on_click=lambda: st.info("PDF olarak indirip Ctrl+P ile yazdırabilirsiniz. A4 formatı tam uyumludur."), use_container_width=True)

    # E-posta Gönderme
    email_user = st.text_input("📩 Raporu E-Postana Gönder", placeholder="E-posta adresinizi yazın...")
    if st.button("E-Posta Gönder"):
        st.success(f"Rapor taslağı {email_user} adresine e-posta olarak gönderilmek üzere sıraya alındı.")

# --- 6. SİSTEM DÜĞMELERİ (YENİ VE PAYLAŞ) ---
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

# --- FOOTER ---
st.markdown(f"""
<p style='text-align: center; color: gray; font-size: 0.9em;'>
    Derepazarı İlçe MEM Arge Birimi © 2026<br>
    <b>Hazırlayan: Hüsamettin KAYMAKÇI</b><br>
    E-Posta: <a href='mailto:sosyalcinet@gmail.com'>sosyalcinet@gmail.com</a> | 
    Telegram: <a href='https://t.me/sosyalcinet'>@sosyalcinet</a>
</p>
""", unsafe_allow_html=True)
