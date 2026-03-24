import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# --- 1. TEKNOFEST RESMİ VERİ MATRİSİ ---
# image_0f98e3.png örneğine ve şartnameye göre güncellendi
TEKNOFEST_DATA = {
    "İlkokul": {
        "Yarisma_Adi": "2026 İnsanlık Yararına Teknolojiler Yarışması-İlkokul Seviyesi",
        "Temalar": {
            "Doğa, Çevre ve Sürdürülebilirlik": ["Geri Dönüşüm", "Su Tasarrufu", "Enerji Verimliliği", "Yaban Hayatı Koruma"],
            "Sağlık ve İlk Yardım": ["Kişisel Hijyen", "Çocuk Sağlığı", "Sağlıklı Beslenme"],
            "Afet Yönetimi": ["Deprem Farkındalığı", "Tahliye Eğitimi"],
            "Sosyal İnovasyon": ["Okulda Yardımlaşma", "Oyunla Eğitim"]
        },
        "Hedef_Kitle": ["İlkokul Öğrencileri", "Veliler", "Öğretmenler", "Okul Çalışanları"]
    },
    "Ortaokul": {
        "Yarisma_Adi": "2026 İnsanlık Yararına Teknolojiler Yarışması-Ortaokul Seviyesi",
        "Temalar": {
            "Doğa, Çevre ve Sürdürülebilirlik": ["Akıllı Tarım", "Atık Yönetimi", "Yenilenebilir Enerji"],
            "Sağlık ve İlk Yardım": ["Engelli Dostu Sistemler", "Hastalık Takibi", "Sporcu Sağlığı"],
            "Afet Yönetimi": ["Erken Uyarı Sistemleri", "Arama Kurtarma Destek"],
            "Sosyal İnovasyon": ["Dezavantajlı Gruplar", "Erişilebilirlik", "Toplum Sağlığı"]
        },
        "Hedef_Kitle": ["Ortaokul Öğrencileri", "Bedensel Engelliler", "Afetzedeler", "Yaşlılar"]
    },
    "Lise": {
        "Yarisma_Adi": "2026 İnsanlık Yararına Teknolojiler Yarışması-Lise Seviyesi",
        "Temalar": {
            "Doğa, Çevre ve Sürdürülebilirlik": ["Karbon Ayak İzi", "Biyoçeşitlilik", "Sürdürülebilir Şehirler"],
            "Sağlık ve İlk Yardım": ["Biyomedikal Cihazlar", "Giyilebilir Teknolojiler", "Teşhis Destek Sistemleri"],
            "Afet Yönetimi": ["İHA/Robotik Kurtarma", "Kriz Lojistiği", "Haberleşme Sistemleri"],
            "Sosyal İnovasyon": ["Göç ve Uyum", "Eğitimde Fırsat Eşitliği", "Siber Güvenlik Farkındalığı"]
        },
        "Hedef_Kitle": ["Lise ve Üniversite Öğrencileri", "Kronik Hastalar", "Profesyonel Kurtarma Ekipleri", "Yerel Yönetimler"]
    }
}

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Secrets (Kasa) ayarlarında API anahtarı bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V8 | Resmi Filtreli", layout="centered", page_icon="🤖")

# --- FORMATLAMA (Arial 12pt, 1.15 Aralığı) ---
def create_word(text, title, yarisma_full):
    doc = Document()
    # image_0f98e3.png örneğine uygun Başlık
    h = doc.add_heading("BAŞVURU YAPTIĞI YARIŞMA ADI", 1)
    doc.add_paragraph(yarisma_full)
    
    doc.add_heading(title.upper(), 0)
    p = doc.add_paragraph(text.replace("**", "").replace("##", "").replace("#", ""))
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'; font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.15 # Şartname kuralı
    bio = BytesIO()
    doc.save(bio); return bio.getvalue()

def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt=title.encode('latin-1', 'replace').decode('latin-1'), align='C')
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7.5, txt=text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V8</h1>", unsafe_allow_html=True)

with st.expander("⚙️ Rapor Ayarları", expanded=True):
    hedef_sayfa = st.radio("Hedef Sayfa Sayısı (Resmi limit max 6)", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True)

with st.expander("📝 Proje Bilgileri (Resmi Filtreli)", expanded=True):
    # Ana Seviye Seçimi
    seviye = st.selectbox("Eğitim Seviyesi", list(TEKNOFEST_DATA.keys()))
    
    col1, col2 = st.columns(2)
    with col1:
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        # Seviyeye özel Temalar
        ana_tema = st.selectbox("Ana Tema", list(TEKNOFEST_DATA[seviye]["Temalar"].keys()))
        alt_tema = st.selectbox("Alt Tema", TEKNOFEST_DATA[seviye]["Temalar"][ana_tema])
        
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        # Seviyeye özel Hedef Kitle
        h_kitle = st.selectbox("Hedef Kitle", TEKNOFEST_DATA[seviye]["Hedef_Kitle"])
        takim_id = st.text_input("Başvuru/Takım ID")

    aciklama = st.text_area("Proje Özeti ve Kapsamı (Ana Fikriniz)", height=150)
    
    if st.button("🚀 Resmi Şartnameye Uygun Rapor Hazırla", use_container_width=True, type="primary"):
        if not aciklama:
            st.warning("Lütfen proje fikrinizi kısaca açıklayın.")
        else:
            with st.status(f"🛠️ {seviye} Seviyesi Şablonu İşleniyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    yarisma_tam_ad = f"{TEKNOFEST_DATA[seviye]['Yarisma_Adi']} / {ana_tema}"
                    p_name = proje_adi if proje_adi else "[PROJE ADI]"
                    d_name = danisman if danisman else "[DANIŞMAN ADI]"
                    t_name = takim if takim else "[TAKIM ADI]"
                    id_no = takim_id if takim_id else "[ID]"

                    prompt = f"""
                    Sen profesyonel bir Teknofest danışmanısın. {seviye} seviyesi için aşağıdaki bilgilerle bir ÖDR yaz.
                    BAŞVURU YAPTIĞI YARIŞMA ADI: {yarisma_tam_ad}
                    Puanlama: Özet (20p), Problem (35p), Özgünlük (24p), Yöntem (12p), Takım/Kaynaklar (6p).
                    Format: Arial 12pt, 1.15 aralık. Markdown kullanma.
                    
                    BAŞLIKLAR:
                    PROJE ADI: {p_name} | DANIŞMAN: {d_name} | TAKIM: {t_name} | ID: {id_no}
                    HEDEF KİTLE: {h_kitle} | ALT TEMA: {alt_tema}
                    ---
                    ZORUNLU BÖLÜMLER:
                    1. PROJE ÖZETİ (Amacı, Kapsamı, Hedef Kitle)
                    2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ (Problemin güncelliği)
                    3. ÖZGÜN DEĞER, UYGULANABİLİRLİK VE SÜRDÜRÜLEBİLİRLİK
                    4. ÇALIŞMA YÖNTEMİ VE SÜREÇ
                    5. PROJE TAKIMI (Görev dağılımı anlatımı)
                    6. KAYNAKLAR
                    
                    İçerik Temeli: {aciklama}
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor = response.text
                    st.session_state.p_adi = p_name
                    st.session_state.y_adi = yarisma_tam_ad
                    st.session_state.hazir = True
                    status.update(label="✅ Rapor Şartnameye Uygun!", state="complete")
                except Exception as e: st.error(str(e))

# --- SONUÇ ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"**Yarışma:** {st.session_state.y_adi}")
    st.markdown(f"""
    <div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'> 
        <h2 style='text-align:center; border-bottom: 2px solid #1E3A8A;'>{st.session_state.p_adi.upper()}</h2>
        <p>{st.session_state.rapor.replace('\n', '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: st.download_button("📥 PDF İndir", create_pdf(st.session_state.rapor, st.session_state.p_adi), f"{st.session_state.p_adi}.pdf", use_container_width=True)
    with c2: st.download_button("📥 Word (Resmi Format)", create_word(st.session_state.rapor, st.session_state.p_adi, st.session_state.y_adi), f"{st.session_state.p_adi}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b></p>", unsafe_allow_html=True)
