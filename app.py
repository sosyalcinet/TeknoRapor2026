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
st.set_page_config(page_title="TeknoRapor V1", layout="centered", page_icon="🤖")

# --- KARAKTER VE BİÇİM TEMİZLEYİCİ ---
def format_temizle(text):
    """Metindeki Markdown işaretlerini temizler ve PDF uyumlu hale getirir."""
    temiz = text.replace("**", "").replace("##", "").replace("#", "").replace("__", "")
    harita = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
        'Ç': 'C', 'ç': 'c', 'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
        '\u2019': "'", '\u2018': "'", '\u201d': '"', '\u201c': '"',
        '\u2013': "-", '\u2014': "-", '\u2022': "*", '\u2026': "..."
    }
    for kaynak, hedef in harita.items():
        temiz = temiz.replace(kaynak, hedef)
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
    # Metni PDF için temizliyoruz
    pdf.multi_cell(0, 7.5, txt=format_temizle(text))
    return pdf.output(dest='S').encode('latin-1')

def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    # Word için sadece Markdown temizliği
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

# --- BAŞLIK (SABİT) ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Otomatik ÖDR Yapay Zeka Robotu V1</h1>", unsafe_allow_html=True)

# --- DÜĞME SİSTEMİ (EXPANDERS) ---

with st.expander("1. ℹ️ Açıklama"):
    st.write("""
    Bu uygulamanın amacı; hazırladığınız projenizi temel hatlarıyla sisteme girdiğinizde, 
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

with st.expander("4. 📝 Rapor Girişi (Ana Bölüm)", expanded=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise", "Üniversite"])
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        kategori = st.selectbox("Kategori", ["İnsanlık Yararına", "Eğitim Teknolojileri", "Akıllı Ulaşım", "Tarım"])
    with col_f2:
        danisman_adi = st.text_input("Danışman Adı (Varsa)", placeholder="Ad Soyad")
        takim_adi = st.text_input("Takım Adı (Varsa)", placeholder="Takım İsmi")
        takim_id = st.text_input("Takım ID (Varsa)", placeholder="T26-...")

    proje_aciklamasi = st.text_area("Proje Açıklaması", height=150)
    ozgunluk = st.text_area("Kişisel Dokunuş / Hikaye", height=100)
    
    st.markdown("---")
    if st.button("🚀 Teknofest Standartlarında Kapsamlı Raporu Hazırla", use_container_width=True, type="primary"):
        if not proje_aciklamasi or not proje_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status("🛠️ Rapor hazırlanıyor, lütfen bekleyiniz...", expanded=True) as status:
                st.write("Yapay zeka şu an düşünen modda en iyi işi çıkarmaya çalışıyor...")
                st.write(f"Raporunuz {hedef_sayfa} sayfa kuralına göre optimize ediliyor. Lütfen ayrılmayınız...")
                
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    
                    hedef_kelime = hedef_sayfa * 450
                    prompt = f"""
                    Sen Teknofest danışmanısın. {seviye} seviyesi için {kategori} kategorisinde TAM {hedef_sayfa} SAYFA (Yaklaşık {hedef_kelime} kelime) rapor yaz.
                    MOD: {yazim_modu} (Anti-Dedektör ise insansı ve akademik yaz). HTML veya Markdown (** veya ##) işaretleri KESİNLİKLE kullanma.
                    
                    RAPORUN BAŞINA ŞUNLARI KALIN HARFLERLE EKLE:
                    - Proje Adı: {proje_adi}
                    - Danışman Adı: {danisman_adi}
                    - Takım Adı: {takim_adi}
                    - Takım ID: {takim_id}
                    - Seviye/Kategori: {seviye} / {kategori}
                    ---
                    
                    BÖLÜMLER: Özet (250 kelime), Problem, Çözüm, Özgün Değer, Hedef Kitle, Maliyet, Takvim.
                    İçerik: {proje_adi} - {proje_aciklamasi}. Hikaye: {ozgunluk}
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state.rapor_metni = response.text
                    st.session_state.proje_adi_state = proje_adi
                    st.session_state.rapor_hazir = True
                    status.update(label="✅ Rapor Başarıyla Hazırlandı!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Hata: {str(e)}")

# --- 5. SONUÇ VE İSTATİSTİKLER ---
if "rapor_hazir" in st.session_state and st.session_state.rapor_hazir:
    st.markdown("---")
    metin = st.session_state.rapor_metni
    p_adi = st.session_state.proje_adi_state
    temiz_metin = metin.replace("**", "").replace("##", "").replace("#", "")
    
    col_st1, col_st2, col_st3 = st.columns(3)
    col_st1.metric("Toplam Kelime", len(metin.split()))
    col_st2.metric("Savunma Durumu", "Aktif" if "Anti-Dedektör" in yazim_modu else "Pasif")
    col_st3.metric("Karakter Sağlığı", "Güvenli (UTF-8)")
    
    # DİJİTAL RAPOR SAYFASI
    st.markdown("### 📄 Rapor Önizleme")
    st.markdown(f"""
    <div style="background-color: white; padding: 40px; color: black; border: 1px solid #ddd; border-radius: 5px; font-family: Arial; line-height: 1.6; text-align: justify; height: 500px; overflow-y: scroll;">
        <h2 style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px;">{p_adi.upper()}</h2>
        <p>{temiz_metin.replace('\n', '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📥 İşlemler")
    c_down1, c_down2 = st.columns(2)
    with c_down1:
        pdf_bytes = create_pdf(temiz_metin, p_adi)
        st.download_button("📥 PDF Olarak İndir", pdf_bytes, f"{p_adi}.pdf", use_container_width=True)
    with c_down2:
        word_bytes = create_word(temiz_metin, p_adi)
        st.download_button("📥 Word Olarak İndir", word_bytes, f"{p_adi}.docx", use_container_width=True)

    # E-tabloya Kayıt
    try:
        sheet = connect_sheets()
        if sheet:
            sheet.append_row([str(datetime.now()), yazim_modu, p_adi, temiz_metin[:30000]])
    except: pass

# --- 6. SİSTEM DÜĞMELERİ ---
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
