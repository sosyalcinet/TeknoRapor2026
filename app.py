import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

# --- 1. TEKNOFEST RESMİ VERİ MATRİSİ (Önceki Başarılı Filtreler) ---
LEVEL_DATA = {
    "İlkokul": {
        "Yarisma": "2026 İnsanlık Yararına Teknolojiler Yarışması-İlkokul Seviyesi",
        "Temalar": {
            "Doğa ve Çevre": ["Geri Dönüşüm", "Su Tasarrufu", "Enerji Verimliliği"],
            "Sağlık ve Hijyen": ["Kişisel Temizlik", "Sağlıklı Beslenme"],
            "Sosyal İnovasyon": ["Okulda Yardımlaşma", "Oyunla Eğitim"]
        },
        "Hedef_Kitle": ["İlkokul Öğrencileri", "Veliler", "Öğretmenler"]
    },
    "Ortaokul": {
        "Yarisma": "2026 İnsanlık Yararına Teknolojiler Yarışması-Ortaokul Seviyesi",
        "Temalar": {
            "Afet Yönetimi": ["Erken Uyarı Sistemleri", "Arama Kurtarma"],
            "Engelli Dostu": ["Erişilebilirlik", "Yardımcı Teknolojiler"],
            "Sosyal İnovasyon": ["Toplum Sağlığı", "Eğitimde Fırsat Eşitliği"]
        },
        "Hedef_Kitle": ["Ortaokul Öğrencileri", "Bedensel Engelliler", "Yaşlılar"]
    },
    "Lise": {
        "Yarisma": "2026 İnsanlık Yararına Teknolojiler Yarışması-Lise Seviyesi",
        "Temalar": {
            "Biyomedikal": ["Teşhis Destek", "Giyilebilir Sağlık Cihazları"],
            "Kriz Yönetimi": ["Lojistik Destek", "Haberleşme Sistemleri"],
            "Sürdürülebilir Şehirler": ["Akıllı Atık Kontrolü", "Karbon Ayak İzi"]
        },
        "Hedef_Kitle": ["Lise Öğrencileri", "Kronik Hastalar", "Profesyonel Kurtarma Ekipleri"]
    }
}

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Secrets ayarlarında API anahtarı bulunamadı!")
    st.stop()

st.set_page_config(page_title="TeknoRapor V9 | Resmi Şablon", layout="centered", page_icon="🤖")

# --- FORMATLAMA (Resmi Şartname: Arial 12pt, 1.15 Aralık) ---
def create_word(text, info_dict):
    doc = Document()
    # 1. SAYFA: KAPAK ŞABLONU
    h_kapak = doc.add_heading(info_dict['yarisma'].upper(), 0)
    h_kapak.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p_info = doc.add_paragraph()
    p_info.add_run(f"\nKATEGORİ ADI: {info_dict['kategori']}\n").bold = True
    p_info.add_run(f"TAKIM ADI: {info_dict['takim']}\n").bold = True
    p_info.add_run(f"BAŞVURU ID: {info_dict['b_id']}\n").bold = True
    p_info.add_run(f"TAKIM ID: {info_dict['t_id']}\n").bold = True
    p_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # 2. SAYFA: İÇİNDEKİLER (Sabit Başlıklar)
    doc.add_heading("İÇİNDEKİLER", 1)
    toc_text = "1. PROJE ÖZETİ\n2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ\n3. ÖZGÜNLÜK VE UYGULANABİLİRLİK\n4. YÖNTEM VE SÜREÇ\n5. PROJE TAKIMI\n6. KAYNAKLAR"
    doc.add_paragraph(toc_text)
    doc.add_page_break()
    
    # 3. SAYFA VE DEVAMI: RAPOR İÇERİĞİ
    main_p = doc.add_paragraph(text.replace("**", "").replace("##", ""))
    style = doc.styles['Normal']
    style.font.name = 'Arial'; style.font.size = Pt(12)
    main_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    main_p.paragraph_format.line_spacing = 1.15
    
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# --- ARAYÜZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Teknofest Resmi ÖDR Robotu V9</h1>", unsafe_allow_html=True)

# 1. SAYFA SAYISI (6 Düğme)
st.write("**Rapor Kaç Sayfa Olsun?**")
hedef_sayfa = st.radio("Sayfa", options=[1, 2, 3, 4, 5, 6], index=2, horizontal=True, label_visibility="collapsed")

with st.expander("📝 Proje ve Kapak Bilgileri", expanded=True):
    seviye = st.selectbox("Eğitim Seviyesi", list(LEVEL_DATA.keys()))
    
    col1, col2 = st.columns(2)
    with col1:
        proje_adi = st.text_input("Proje Adı", placeholder="Örn: Bulut Kumbarası")
        ana_tema = st.selectbox("Ana Tema", list(LEVEL_DATA[seviye]["Temalar"].keys()))
        alt_tema = st.selectbox("Alt Tema", LEVEL_DATA[seviye]["Temalar"][ana_tema])
        b_id = st.text_input("Başvuru ID", placeholder="Belirtilmezse boş kalır")
    with col2:
        danisman = st.text_input("Danışman Adı")
        takim = st.text_input("Takım Adı")
        h_kitle = st.selectbox("Hedef Kitle", LEVEL_DATA[seviye]["Hedef_Kitle"])
        t_id = st.text_input("Takım ID", placeholder="Belirtilmezse boş kalır")

    aciklama = st.text_area("Proje Özeti ve Kapsamı (Buraya ana fikrinizi yazın)", height=150)
    
    # YAPAY ZEKA SEVİYESİ
    yazim_modu = st.selectbox("AI Yazım Karakteri", ["Standart AI Dedektör (İnsan Gibi Yaz)", "Akademik/Resmi", "Süper AI"])

    if st.button("🚀 Resmi Şablona Göre Raporu Hazırla", use_container_width=True, type="primary"):
        with st.status("🛠️ Şartname kriterleri analiz ediliyor...", expanded=True) as status:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Bilgi yoksa boşluk bırakma mantığı
                info = {
                    "yarisma": LEVEL_DATA[seviye]["Yarisma"],
                    "kategori": f"İnsanlık Yararına Teknoloji / {ana_tema}",
                    "takim": takim if takim else "____________________",
                    "b_id": b_id if b_id else "____________________",
                    "t_id": t_id if t_id else "____________________",
                    "proje": proje_adi if proje_adi else "____________________"
                }

                prompt = f"""
                Teknofest jürisisin. {seviye} seviyesi için resmi ÖDR yaz. 
                MOD: {yazim_modu} (Yapay zeka tespitinden kaçınan doğal, insan benzeri bir dil kullan).
                Format: Arial 12pt, 1.15 aralık. Sayfa hedefi: {hedef_sayfa}.
                
                PUANLAMA BÖLÜMLERİ:
                1. PROJE ÖZETİ (20 PUAN): Amacı, {ana_tema} uyumu ve {h_kitle} faydası.
                2. PROBLEMİN TANIMI VE ÇÖZÜM ÖNERİSİ (35 PUAN): Problemin güncelliği.
                3. ÖZGÜNLÜK VE UYGULANABİLİRLİK (24 PUAN).
                4. YÖNTEM VE SÜREÇ (12 PUAN).
                5. PROJE TAKIMI (3 PUAN) VE KAYNAKLAR (3 PUAN).
                
                İçerik Temeli: {aciklama}. Danışman: {danisman}.
                """
                response = model.generate_content(prompt)
                st.session_state.rapor = response.text
                st.session_state.info = info
                st.session_state.hazir = True
                status.update(label="✅ Rapor Şartnameye Uygun!", state="complete")
            except Exception as e: st.error(str(e))

if "hazir" in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state.rapor.replace('\n', '<br>'), unsafe_allow_html=True)
    st.download_button("📥 Resmi Word Çıktısını İndir (Kapaklı)", create_word(st.session_state.rapor, st.session_state.info), f"{proje_adi}.docx", use_container_width=True)

st.markdown(f"<p style='text-align: center; color: gray;'>Derepazarı İlçe MEM Arge Birimi © 2026 | Hazırlayan: Hüsamettin KAYMAKÇI</p>", unsafe_allow_html=True)
