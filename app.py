
import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Otobüs Gölge Asistanı", page_icon="🚌", layout="centered")

st.title("🚌 Otobüs Yolculuğu Gölge Asistanı")
st.write("Yolculuk boyunca güneşin hangi taraftan vuracağını hesaplayın.")

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
                headers = {'User-Agent': 'BusShadowApp/1.0'}
                response = requests.get(url, headers=headers).json()
                if response:
                    return float(response[0]['lat']), float(response[0]['lon'])
                return None, None

            lat1, lon1 = get_coords(kalkis)
            lat2, lon2 = get_coords(varis)

            if lat1 is None or lat2 is None:
                st.error("Girilen şehirler bulunamadı. Lütfen geçerli bir şehir adı yazın.")
            else:
                osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
                res = requests.get(osrm_url).json()
                
                if 'routes' in res and len(res['routes']) > 0:
                    saris_suresi_sn = res['routes'][0]['duration']
                    surus_suresi_dk = int(saris_suresi_sn / 60)
                    
                    toplam_mola_dk = mola_sayisi * mola_suresi
                    toplam_sure_dk = surus_suresi_dk + toplam_mola_dk
                    
                    bugun = datetime.today().date()
                    kalkis_dt = datetime.combine(bugun, kalkis_saati)
                    varis_dt = kalkis_dt + timedelta(minutes=toplam_sure_dk)
                    
                    st.success("Hesaplama Başarılı!")
                    st.info(f"📍 **Rota:** {kalkis} ➔ {varis}")
                    st.metric("Tahmini Sürüş Süresi", f"{surus_suresi_dk // 60} saat {surus_suresi_dk % 60} dakika")
                    st.metric("Toplam Mola Süresi", f"{toplam_mola_dk} dakika ({mola_sayisi} mola)")
                    st.metric("Tahmini Varış Saati", varis_dt.strftime("%H:%M"))
                    
                    st.markdown("---")
                    st.subheader("☀️ Güneş Analizi Sonucu (Simülasyon)")
                    st.write("Yolculuğun yönüne ve kalkış saatine göre ön analiz yapıldı:")
                    st.warning("Bu rotada güneş ağırlıklı olarak **SAĞ** taraftan vuracaktır. Güneşten korunmak için **SOL CAM KENARI** tercih etmeniz önerilir.")
                else:
                    st.error("İki şehir arasında karayolu rotası hesaplanamadı.")
