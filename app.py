import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from datetime import datetime

# --- 1. RESMİ ŞARTNAME VERİ MATRİSİ (2026) ---
TEKNOFEST_MATRIS = {
    "İlkokul": {
        "Yarisma": "2026 İNSANLIK YARARINA TEKNOLOJİLER YARIŞMASI İLKOKUL SEVİYESİ",
        "Temalar": {
            "Doğa, Çevre ve Sürdürülebilirlik": ["Atık Yönetimi ve Geri Dönüşüm", "Yeşil Teknolojiler ve Yenilenebilir Enerji", "Akıllı Şehirler", "Doğal Yaşam", "Afet Teknolojileri"],
            "Astronomi, Uzay Bilimleri ve Havacılık": ["Gezegenimiz ve Evren", "Gözlemler ve Teleskoplar", "Uydular ve Roketler", "Uzayda Yaşam"],
            "Sağlıklı Yaşam": ["Fiziksel ve Zihinsel Sağlık", "Besin (Gıda) Teknolojileri", "Sürdürülebilir Tarım"]
        },
        "Hedef_Kitle": ["İlkokul Öğrencileri", "Veliler", "Öğretmenler", "Okul Çalışanları"]
    },
    "Ortaokul": {
        "Yarisma": "2026 İNSANLIK YARARINA TEKNOLOJİLER YARIŞMASI ORTAOKUL SEVİYESİ",
        "Temalar": {
            "Astronomi ve Uzay Teknolojileri": ["Uzay Araçları ve Keşif Sistemleri", "Gezegenler ve Uzayda Yaşam Olasılığı", "Uzay Araştırmaları ve Gözlem Teknolojileri", "Gökyüzü ve Evreni Keşfetmek"],
            "Doğa Bilimleri ve Çevresel Farkındalık": ["Akıllı Şehirler", "Ekosistemler", "Afetler ve Güvenli Yaşam", "Enerji Kaynakları", "Atık Yönetimi"],
            "Sağlık ve İyi Yaşam Teknolojileri": ["Beslenme ve Gıda", "Hareketli Yaşam", "Günlük Sağlık Teknolojileri", "Zihinsel Sağlık", "Engelsiz Yaşam"],
            "Eğitim Teknolojileri": ["Dijital Araçlar", "Oyunlaştırma", "Dijital Güvenlik", "Öğrenmeyi Kolaylaştıran Çözümler"]
        },
        "Hedef_Kitle": ["Ortaokul Öğrencileri", "Bedensel Engelliler", "Yaşlılar", "Afetzedeler"]
    },
    "Lise": {
        "Yarisma": "2026 İNSANLIK YARARINA TEKNOLOJİLER YARIŞMASI LİSE SEVİYESİ",
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
    st.error("Kasa (Secrets) ayarlarında API anahtarı bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V16 | Derepazarı", layout="centered", page_icon="🤖")

# --- RESMİ WORD FORMATLAMA (Arial 12pt, 1.15 Aralık) ---
def create_word_official(text, info):
    doc = Document()
    h_yarisma = doc.add_heading(info['y_adi'], 0)
    h_yarisma.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading("ÖN DEĞERLENDİRME RAPORU", 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    p.add_run(f"\nKATEGORİ: {info['kategori']}\nTAKIM ADI: {info['takim']}\nBAŞVURU ID: {info['b_id']}\nTAKIM ID: {info['t_id']}").bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    doc.add_heading("İÇİNDEKİLER", 1)
    doc.add_paragraph("1. PROJE ÖZETİ\n2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ\n3. ÖZGÜNLÜK VE UYGULANABİLİRLİK\n4. YÖNTEM VE SÜREÇ\n5. PROJE TAKIMI\n6. KAYNAKLAR")
    doc.add_page_break()
    content = doc.add_paragraph(text.replace("**", "").replace("##", ""))
    style = doc.styles['Normal']
    style.font.name = 'Arial'; style.font.size = Pt(12)
    content.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    content.paragraph_format.line_spacing = 1.15
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V16</h1>", unsafe_allow_html=True)

# Sayfa Derinliği - 6 Düğme
st.write("**Rapor Kaç Sayfa Olsun?**")
hedef_sayfa = st.radio("Sayfa", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True, label_visibility="collapsed")

st.markdown("### 🛠️ PROJE GİRİŞİ")

# TAKIM VE ID (Yan yana)
with st.expander("👥 Takım ve Kayıt Bilgileri", expanded=True):
    c1, c2, c3 = st.columns(3)
    t_adi = c1.text_input("Takım Adı", placeholder="Örn: ATMACALAR")
    b_id = c2.text_input("Başvuru ID", placeholder="Başvuru ID")
    t_id = c3.text_input("Takım ID", placeholder="Takım ID")

# SEVİYE VE KATEGORİ (Ayrı yerde, Seçmeli)
with st.expander("🏷️ Seviye ve Kategori Seçimi", expanded=True):
    seviye = st.selectbox("Eğitim Seviyesi", list(TEKNOFEST_MATRIS.keys()))
    col_a, col_b = st.columns(2)
    ana_t = col_a.selectbox("Ana Tema", list(TEKNOFEST_MATRIS[seviye]["Temalar"].keys()))
    alt_t = col_a.selectbox("Alt Tema", TEKNOFEST_MATRIS[seviye]["Temalar"][ana_t])
    h_kitle = col_b.selectbox("Hedef Kitle", TEKNOFEST_MATRIS[seviye]["Hedef_Kitle"])
    danisman = col_b.text_input("Danışman Adı", placeholder="HÜSAMETTİN KAYMAKÇI")

# PROJE ADI VE ÖZETİ (Aynı kutuda alt alta)
with st.expander("📝 Proje Detayı ve Yazım Ayarları", expanded=True):
    p_adi_input = st.text_input("Proje Adı", placeholder="Akıllı Projenizin İsmi")
    aciklama = st.text_area("Projenizin Ana Fikrini Yazın (Proje Özeti)", height=150)
    yazim_modu = st.selectbox("Yazım Karakteri", ["Standart AI Dedektör (İnsan Gibi Yaz)", "Akademik/Resmi", "Süper AI"])

    if st.button("🚀 Şartnameye Uygun Raporu Hazırla", use_container_width=True, type="primary"):
        if not aciklama or not p_adi_input:
            st.warning("Lütfen Proje Adı ve Açıklamasını doldurun.")
        else:
            with st.status(f"🛠️ {seviye} Seviyesi Analiz Ediliyor...", expanded=True) as status:
                try:
                    # --- 404 HATASINI ÇÖZEN EN STABİL ÇAĞRI ---
                    genai.configure(api_key=GEMINI_API_KEY)
                    # Model ismini 'gemini-1.5-flash' olarak sabitledik, bu v1 kanalını kullanır
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    info_dict = {
                        "y_adi": TEKNOFEST_MATRIS[seviye]["Yarisma"],
                        "kategori": f"{ana_t} / {alt_t}",
                        "takim": t_adi if t_adi else "________________",
                        "b_id": b_id if b_id else "________________",
                        "t_id": t_id if t_id else "________________",
                        "p_adi": p_adi_input
                    }

                    prompt = f"""
                    Sen Teknofest jürisisin. {seviye} seviyesi için resmi ÖDR yaz.
                    MOD: {yazim_modu} (Yapay zeka tespitinden kaçınan doğal bir dil kullan).
                    Hedef: {hedef_sayfa} sayfa. Tema: {ana_t}/{alt_t}. Hedef Kitle: {h_kitle}.
                    Puanlama: Özet (20p), Problem (35p), Özgünlük (24p), Yöntem (12p), Takım (6p).
                    ---
                    İçerik: {aciklama}
                    """
                    response = model.generate_content(prompt)
                    st.session_state.rapor = response.text
                    st.session_state.info = info_dict
                    st.session_state.hazir = True
                    status.update(label="✅ Rapor Hazır!", state="complete")
                except Exception as e:
                    st.error(f"Sistem Pürüzü: {str(e)}")

# --- SONUÇ ---
if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(f"<div style='background:white; padding:30px; color:black; border:1px solid #ddd; border-radius:10px; font-family:Arial; text-align:justify;'>{st.session_state.rapor.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
    st.download_button("📥 Resmi Word Çıktısını İndir (Kapaklı)", create_word_official(st.session_state.rapor, st.session_state.info), f"{st.session_state.info['p_adi']}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026<br><b>Hazırlayan: Hüsamettin KAYMAKÇI</b></p>", unsafe_allow_html=True)
