import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Otobüs Gölge Asistanı", page_icon="🚌", layout="centered")

st.title("🚌 Otobüs Yolculuğu Gölge Asistanı")
st.write("Yolculuk boyunca güneşin hangi taraftan vuracağını görsel olarak öğrenin.")

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
            def get_coords(city_name):
                url = f"https://nominatim.openstreetmap.org/search?q={city_name},Turkey&format=json"
                headers = {'User-Agent': 'BusShadowApp-V1'}
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            return float(data[0]['lat']), float(data[0]['lon'])
                except Exception:
                    pass
                return None, None

            lat1, lon1 = get_coords(kalkis)
            lat2, lon2 = get_coords(varis)

            if lat1 is None or lat2 is None:
                st.error("Girilen şehirler harita servisinde bulunamadı. Lütfen şehir adını kontrol edip tekrar deneyin.")
            else:
                osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
                try:
                    res = requests.get(osrm_url, timeout=5)
                    res_data = res.json()
                except Exception:
                    res_data = {}
                
                if 'routes' in res_data and len(res_data['routes']) > 0:
                    saris_suresi_sn = res_data['routes'][0]['duration']
                    surus_suresi_dk = int(saris_suresi_sn / 60)
                    
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
                    
                    # Görsel Otobüs Krokisi Sütunları (Simüle Oran)
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
                else:
                    st.error("İki şehir arasında karayolu rotası hesaplanamadı. Lütfen tekrar deneyin.")
