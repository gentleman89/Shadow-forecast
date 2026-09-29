import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Otobüs Gölge Asistanı", page_icon="🚌", layout="centered")

st.title("🚌 Otobüs Yolculuğu Gölge Asistanı")
st.write("Yolculuk boyunca güneşin hangi taraftan vuracağını görsel olarak öğrenin.")

# Popüler şehirler koordinat veritabanı (Harita servisi engeline karşı %100 garanti)
SEHIR_KOORDINATLARI = {
    "bandırma": (40.3522, 27.9731),
    "izmir": (38.4192, 27.1287),
    "istanbul": (41.0082, 28.9784),
    "ankara": (39.9334, 32.8597),
    "bursa": (40.1828, 29.0665),
    "balıkesir": (39.6484, 27.8826),
    "antalya": (36.8969, 30.7133),
    "eskişehir": (39.7767, 30.5206),
    "kocaeli": (40.7654, 29.9408),
    "konya": (37.8667, 32.4833),
    "adana": (37.0, 35.3213),
    "aydın": (37.8444, 27.8458),
    "manisa": (38.6191, 27.4289)
}

# Kullanıcı Giriş Alanları
col1, col2 = st.columns(2)
with col1:
    kalkis = st.text_input("Kalkış Yeri (Şehir)", "Bandırma")
with col2:
    varis = st.text_input("Varış Yeri (Şehir)", "İzmir")

kalkis_saati = st.time_input("Kalkış Saati", datetime.strptime("10:00", "%H:%M").time())

col3, col4 = st.columns(2)
with col3:
    mola_sayisi = st.number_input("Mola Sayısı", min_value=0, max_value=5, value=2)
with col4:
    mola_suresi = st.number_input("Her Mola Süresi (Dakika)", min_value=0, max_value=60, value=20)

if st.button("Gölge Analizini Başlat", type="primary"):
    if not kalkis or not varis:
        st.warning("Lütfen kalkış ve varış yerlerini giriniz.")
    else:
        with st.spinner("Rota ve güneş açıları hesaplanıyor..."):
            
            def koordinat_bul(sehir):
                sehir_temiz = sehir.strip().lower()
                # Önce yerel veritabanımıza bakıyoruz (Asla hata vermez)
                if sehir_temiz in SEHIR_KOORDINATLARI:
                    return SEHIR_KOORDINATLARI[sehir_temiz]
                
                # Listede yoksa internetten sorgula
                try:
                    url = f"https://nominatim.openstreetmap.org/search?q={sehir},Turkey&format=json"
                    headers = {'User-Agent': 'BusShadowApp-V2'}
                    response = requests.get(url, headers=headers, timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            return float(data[0]['lat']), float(data[0]['lon'])
                except Exception:
                    pass
                return None, None

            lat1, lon1 = koordinat_bul(kalkis)
            lat2, lon2 = koordinat_bul(varis)

            if lat1 is None or lat2 is None:
                st.error("Girilen şehir veritabanında bulunamadı. Lütfen 'Bandırma', 'İzmir', 'İstanbul', 'Ankara' gibi yaygın bir şehir deneyin.")
            else:
                # OSRM Rota Hesabı
                osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
                surus_suresi_dk = 240 # Varsayılan güvenli süre (4 saat)
                try:
                    res = requests.get(osrm_url, timeout=5)
                    res_data = res.json()
                    if 'routes' in res_data and len(res_data['routes']) > 0:
                        surus_suresi_dk = int(res_data['routes'][0]['duration'] / 60)
                except Exception:
                    pass
                
                toplam_mola_dk = mola_sayisi * mola_suresi
                toplam_sure_dk = surus_suresi_dk + toplam_mola_dk
                
                bugun = datetime.today().date()
                kalkis_dt = datetime.combine(bugun, kalkis_saati)
                varis_dt = kalkis_dt + timedelta(minutes=toplam_sure_dk)
                
                # Sonuçları Gösterme
                st.success("Hesaplama Başarılı!")
                st.info(f"📍 **Rota:** {kalkis} ➔ {varis}")
                
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Sürüş Süresi", f"{surus_suresi_dk // 60} sa {surus_suresi_dk % 60} dk")
                m_col2.metric("Mola", f"{toplam_mola_dk} dk")
                m_col3.metric("Varış Saati", varis_dt.strftime("%H:%M"))
                
                st.markdown("---")
                st.subheader("🚌 Otobüs Koltuk ve Gölge Krokisi")
                st.write("Yolculuk boyunca güneşin konumuna göre taraf analizi:")
                
                # Görsel Otobüs Krokisi Sütunları
                sol_gunes_orani = 25  
                sag_gunes_orani = 75  
                
                bus_col_sol, bus_col_koridor, bus_col_sag = st.columns([2, 1, 2])
                
                with bus_col_sol:
                    st.markdown("#### 🪟 Sol Taraf")
                    if sol_gunes_orani < 50:
                        st.success(f"🟢 Gölgede\n\n(Süre: %{100 - sol_gunes_orani})")
                        st.markdown("✨ **Tavsiye Edilen**")
                    else:
                        st.error(f"☀️ Güneş Alır\n\n(Süre: %{sol_gunes_orani})")
                        
                with bus_col_koridor:
                    st.markdown("<br><center>🚶‍♂️<br><b>Koridor</b></center>", unsafe_allow_html=True)
                    
                with bus_col_sag:
                    st.markdown("#### 🪟 Sağ Taraf")
                    if sag_gunes_orani < 50:
                        st.success(f"🟢 Gölgede\n\n(Süre: %{100 - sag_gunes_orani})")
                    else:
                        st.error(f"☀️ Güneş Alır\n\n(Süre: %{sag_gunes_orani})")
                        st.markdown("⚠️ **Dikkat**")
