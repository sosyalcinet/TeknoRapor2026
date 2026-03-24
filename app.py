import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# --- 1. RESMİ ŞARTNAME VERİ MATRİSİ (Ekteki Dosyalardan Çekildi) ---
TEKNOFEST_MATRIS = {
    "İlkokul": {
        "Yarisma": "2026 İnsanlık Yararına Teknolojiler Yarışması-İlkokul Seviyesi",
        "Temalar": {
            "Doğa, Çevre ve Sürdürülebilirlik": ["Atık Yönetimi ve Geri Dönüşüm", "Yeşil Teknolojiler ve Yenilenebilir Enerji", "Akıllı Şehirler", "Doğal Yaşam", "Afet Teknolojileri"],
            "Astronomi, Uzay Bilimleri ve Havacılık": ["Gezegenimiz ve Evren", "Gözlemler ve Teleskoplar", "Uydular ve Roketler", "Uzayda Yaşam"],
            "Sağlıklı Yaşam": ["Fiziksel ve Zihinsel Sağlık", "Besin (Gıda) Teknolojileri", "Sürdürülebilir Tarım"]
        },
        "Hedef_Kitle": ["İlkokul Öğrencileri", "Veliler", "Öğretmenler", "Okul Çalışanları"]
    },
    "Ortaokul": {
        "Yarisma": "2026 İnsanlık Yararına Teknolojiler Yarışması-Ortaokul Seviyesi",
        "Temalar": {
            "Astronomi ve Uzay Teknolojileri": ["Uzay Araçları ve Keşif", "Gezegenler", "Gözlem Teknolojileri", "Evreni Keşfetmek"],
            "Doğa Bilimleri ve Çevresel Farkındalık": ["Akıllı Şehirler", "Ekosistemler", "Afetler ve Güvenli Yaşam", "Enerji Kaynakları", "Atık Yönetimi"],
            "Sağlık ve İyi Yaşam Teknolojileri": ["Beslenme ve Gıda", "Hareketli Yaşam", "Günlük Sağlık Teknolojileri", "Zihinsel Sağlık", "Engelsiz Yaşam"],
            "Eğitim Teknolojileri": ["Dijital Araçlar", "Oyunlaştırma", "Dijital Güvenlik", "Öğrenmeyi Kolaylaştıran Çözümler"]
        },
        "Hedef_Kitle": ["Ortaokul Öğrencileri", "Bedensel Engelliler", "Yaşlılar", "Afetzedeler"]
    },
    "Lise": {
        "Yarisma": "2026 İnsanlık Yararına Teknolojiler Yarışması-Lise Seviyesi",
        "Temalar": {
            "Akıllı Teknolojiler ve Sistem Tasarımı": ["Ulaşım ve Mobilite", "Şehir ve Kentsel Sistem", "Afet ve Acil Durum"],
            "Sağlık ve İyi Yaşam Teknolojileri": ["Hasta Odaklı", "Sağlık Çalışanlarına Yönelik", "İleri Araştırma", "Güvenli Yaşam"],
            "Eğitim, Kültür ve Dijital Deneyim Teknolojileri": ["Dijital Eğitim", "Etkileşimli Öğrenme", "Kültürel Miras"]
        },
        "Hedef_Kitle": ["Lise Öğrencileri", "Kronik Hastalar", "Profesyonel Kurtarma Ekipleri", "Yerel Yönetimler"]
    }
}

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Secrets ayarlarında API anahtarı bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V10 | Resmi Filtreli", layout="centered", page_icon="🤖")

# --- RESMİ WORD FORMATLAMA (Kapak + İçindekiler + İçerik) ---
def create_word_official(text, info):
    doc = Document()
    # 1. SAYFA: KAPAK
    h_yarisma = doc.add_heading(info['y_adi'].upper(), 0)
    h_yarisma.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading("ÖN DEĞERLENDİRME RAPORU", 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.add_run(f"\nKATEGORİ: {info['ana_tema']}\n").bold = True
    p.add_run(f"TAKIM ADI: {info['takim']}\n").bold = True
    p.add_run(f"BAŞVURU ID: {info['b_id']}\n").bold = True
    p.add_run(f"TAKIM ID: {info['t_id']}\n").bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    
    # 2. SAYFA: İÇİNDEKİLER
    doc.add_heading("İÇİNDEKİLER", 1)
    doc.add_paragraph("1. PROJE ÖZETİ\n2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ\n3. ÖZGÜNLÜK VE UYGULANABİLİRLİK\n4. YÖNTEM VE SÜREÇ\n5. PROJE TAKIMI\n6. KAYNAKLAR")
    doc.add_page_break()
    
    # 3. SAYFA: İÇERİK (Arial 12, 1.15 Aralık)
    content = doc.add_paragraph(text.replace("**", "").replace("##", ""))
    style = doc.styles['Normal']
    style.font.name = 'Arial'; style.font.size = Pt(12)
    content.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    content.paragraph_format.line_spacing = 1.15
    
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V10</h1>", unsafe_allow_html=True)

# 1. SAYFA SAYISI (6 Düğme)
st.write("**Rapor Sayfa Derinliği:**")
hedef_sayfa = st.radio("Sayfa", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True, label_visibility="collapsed")

# 2. PROJE GİRİŞİ (Bölümlendirilmiş)
st.markdown("### 🛠️ PROJE GİRİŞİ")

# TAKIM VE ID BİLGİLERİ (Grup 1)
with st.expander("👥 Takım ve Başvuru Bilgileri", expanded=True):
    c1, c2, c3 = st.columns(3)
    t_adi = c1.text_input("Takım Adı", placeholder="Örn: ATMACALAR")
    b_id = c2.text_input("Başvuru ID", placeholder="123456")
    t_id = c3.text_input("Takım ID", placeholder="T26-...")

# SEVİYE VE TEMA BİLGİLERİ (Grup 2 - Dinamik)
with st.expander("🏷️ Seviye ve Kategori Seçimi", expanded=True):
    # Eğitim Seviyesi Seçimi (Tetikleyici)
    seviye = st.selectbox("Eğitim Seviyesi", ["İlkokul", "Ortaokul", "Lise"])
    
    col_a, col_b = st.columns(2)
    # Şartnameye Göre Dinamik Filtreleme
    ana_t = col_a.selectbox("Ana Tema", list(TEKNOFEST_MATRIS[seviye]["Temalar"].keys()))
    alt_t = col_a.selectbox("Alt Tema", TEKNOFEST_MATRIS[seviye]["Temalar"][ana_t])
    h_kitle = col_b.selectbox("Hedef Kitle", TEKNOFEST_MATRIS[seviye]["Hedef_Kitle"])
    p_adi = col_b.text_input("Proje Adı", placeholder="Örn: Akıllı Kumbara")

# PROJE DETAYLARI
with st.expander("📝 Proje Özeti ve Yazım Karakteri", expanded=True):
    aciklama = st.text_area("Projenizin Ana Fikrini Yazın", height=150)
    yazim_modu = st.selectbox("Yazım Karakteri", ["Standart AI Dedektör (İnsan Gibi Yaz)", "Akademik/Resmi", "Süper AI"])

    if st.button("🚀 Şartnameye Uygun Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama or not p_adi:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status(f"🛠️ {seviye} Seviyesi Kriterleri Analiz Ediliyor...", expanded=True) as status:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    info_dict = {
                        "y_adi": TEKNOFEST_MATRIS[seviye]["Yarisma"],
                        "takim": t_adi if t_adi else "________________",
                        "b_id": b_id if b_id else "________________",
                        "t_id": t_id if t_id else "________________",
                        "ana_tema": f"{ana_t} / {alt_t}",
                        "p_adi": p_adi
                    }

                    prompt = f"""
                    Sen profesyonel bir Teknofest danışmanısın. {seviye} seviyesi {ana_t} temasında ÖDR yaz.
                    HEDEF KİTLE: {h_kitle}. ALT TEMA: {alt_t}.
                    MOD: {yazim_modu} (Yapay zeka tespitinden kaçınan doğal bir dil kullan).
                    Puanlama Kriterlerine (Özet 20p, Problem 35p, Özgünlük 24p, Yöntem 12p) göre {hedef_sayfa} sayfa yaz.
                    
                    RESMİ BÖLÜMLER:
                    1. PROJE ÖZETİ: {ana_t} uyumu ve {h_kitle} faydası.
                    2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ.
                    3. ÖZGÜNLÜK VE UYGULANABİLİRLİK.
                    4. ÇALIŞMA YÖNTEMİ VE SÜREÇ.
                    5. PROJE TAKIMI VE KAYNAKLAR.
                    
                    İçerik Kaynağı: {aciklama}
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor = response.text
                    st.session_state.info = info_dict
                    st.session_state.hazir = True
                    status.update(label="✅ Rapor Hazır!", state="complete")
                except Exception as e: st.error(str(e))

# --- ÇIKTILAR ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"**Hazırlanan:** {st.session_state.info['p_adi']}")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'>{st.session_state.rapor.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
    
    st.download_button("📥 Resmi Word Çıktısını İndir (Kapaklı)", create_word_official(st.session_state.rapor, st.session_state.info), f"{st.session_state.info['p_adi']}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b></p>", unsafe_allow_html=True)
