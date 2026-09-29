import streamlit as st
import requests
import math
from datetime import datetime, timedelta, timezone
import urllib.parse

st.set_page_config(page_title="Otobüs Gölge Asistanı", page_icon="🚌", layout="centered")

st.title("🚌 Otobüs Yolculuğu Gölge Asistanı")
st.write("Yolculuk boyunca güneşin konumunu gerçek astronomik açılarla hesaplayın.")

# Türkiye'nin 81 İlinin Merkez Koordinatları Veritabanı
SEHIR_KOORDINATLARI = {
    "adana": (37.0, 35.3213),
    "adıyaman": (37.7648, 38.2786),
    "afyonkarahisar": (38.7507, 30.5567),
    "ağrı": (39.7191, 43.0503),
    "amasya": (40.6547, 35.8339),
    "ankara": (39.9334, 32.8597),
    "antalya": (36.8969, 30.7133),
    "artvin": (41.1828, 41.8183),
    "aydın": (37.8444, 27.8458),
    "balıkesir": (39.6484, 27.8826),
    "bandırma": (40.3522, 27.9731),
    "bilecik": (40.3456, 29.9803),
    "bingöl": (38.8854, 40.498),
    "bitlis": (38.4006, 42.1091),
    "bolu": (40.7359, 31.6061),
    "burdur": (37.7226, 30.2887),
    "bursa": (40.1828, 29.0665),
    "çanakkale": (40.1553, 26.4142),
    "çankırı": (40.6013, 33.6134),
    "çorum": (40.5506, 34.9556),
    "denizli": (37.7765, 29.0864),
    "diyarbakır": (37.9144, 40.2306),
    "edirne": (41.6771, 26.5557),
    "elazığ": (38.681, 39.2264),
    "erzincan": (39.75, 39.5),
    "erzurum": (39.9043, 41.2658),
    "eskişehir": (39.7767, 30.5206),
    "gaziantep": (37.0662, 37.3833),
    "giresun": (40.9128, 38.3895),
    "gümüşhane": (40.46, 39.479),
    "hakkari": (37.5833, 43.7333),
    "hatay": (36.2, 36.16),
    "ısparta": (37.7648, 30.5566),
    "mersin": (36.8, 34.6333),
    "istanbul": (41.0082, 28.9784),
    "izmir": (38.4192, 27.1287),
    "kars": (40.6013, 43.0975),
    "kastamonu": (41.3887, 33.7827),
    "kayseri": (38.7312, 35.4787),
    "kırklareli": (41.7333, 27.2167),
    "kırşehir": (39.1425, 34.1709),
    "kocaeli": (40.7654, 29.9408),
    "konya": (37.8667, 32.4833),
    "kütahya": (39.4242, 29.9833),
    "malatya": (38.3552, 38.3095),
    "manisa": (38.6191, 27.4289),
    "kahramanmaraş": (37.5858, 36.9371),
    "mardin": (37.3211, 40.7245),
    "muğla": (37.2153, 28.3636),
    "muş": (38.9444, 41.5056),
    "nevşehir": (38.6244, 34.7239),
    "niğde": (37.9667, 34.6833),
    "ordu": (40.9839, 37.8764),
    "rize": (41.02, 40.523),
    "sakarya": (40.7569, 30.3783),
    "samsun": (41.2867, 36.33),
    "siirt": (37.9333, 41.95),
    "sinop": (42.0231, 35.1531),
    "sivas": (39.7477, 37.0179),
    "tekirdağ": (40.9833, 27.5167),
    "tokat": (40.3167, 36.55),
    "trabzon": (41.0015, 39.7178),
    "tunceli": (39.1078, 39.5401),
    "şanlıurfa": (37.1591, 38.7969),
    "uşak": (38.6823, 29.4082),
    "van": (38.4891, 43.4089),
    "yozgat": (39.8181, 34.8147),
    "zonguldak": (41.4564, 31.7987),
    "aksaray": (38.3687, 34.037),
    "bayburt": (40.2552, 40.2249),
    "karaman": (37.1759, 33.2287),
    "kırıkkale": (39.8468, 33.5153),
    "batman": (37.8812, 41.1351),
    "şırnak": (37.5164, 42.4611),
    "bartın": (41.6386, 32.3375),
    "ardahan": (41.1105, 42.7022),
    "ığdır": (39.9167, 44.0333),
    "yalova": (40.65, 29.0),
    "karabük": (41.2, 32.62),
    "kilis": (36.7184, 37.1212),
    "osmaniye": (37.0742, 36.2467),
    "düzce": (40.8438, 31.1565)
}

def turkce_temizle(metin):
    return metin.strip().replace('İ', 'i').replace('I', 'ı').lower()

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def get_solar_position(lat, lon, dt_utc):
    day_of_year = dt_utc.timetuple().tm_yday
    hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    
    gamma = (2 * math.pi / 365.0) * (day_of_year - 1 + (hour - 12) / 24.0)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) 
                      - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
    
    decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) \
           - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma) \
           - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
    
    time_offset = eqtime + 4 * lon
    tst = hour * 60 + time_offset
    
    ha = (tst / 4.0) - 180.0
    ha_rad = math.radians(ha)
    lat_rad = math.radians(lat)
    
    cos_zenith = math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(decl) * math.cos(ha_rad)
    cos_zenith = max(-1.0, min(1.0, cos_zenith))
    zenith_rad = math.acos(cos_zenith)
    elevation_deg = 90.0 - math.degrees(zenith_rad)
    
    sin_zenith = math.sin(zenith_rad)
    if sin_zenith == 0:
        azimuth_deg = 180.0
    else:
        cos_az = (math.sin(decl) - math.sin(lat_rad) * cos_zenith) / (math.cos(lat_rad) * sin_zenith)
        cos_az = max(-1.0, min(1.0, cos_az))
        az_rad = math.acos(cos_az)
        azimuth_deg = (360.0 - math.degrees(az_rad)) if ha > 0 else math.degrees(az_rad)
        
    return azimuth_deg, elevation_deg

def analyze_sun_exposure(lat1, lon1, lat2, lon2, kalkis_dt, toplam_sure_dk, samples=20):
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    sol_count = 0
    sag_count = 0
    gunduz_count = 0
    
    tr_tz = timezone(timedelta(hours=3))
    
    for i in range(samples):
        fraction = i / max(1, (samples - 1))
        curr_lat = lat1 + fraction * (lat2 - lat1)
        curr_lon = lon1 + fraction * (lon2 - lon1)
        
        curr_dt_tr = kalkis_dt + timedelta(minutes=fraction * toplam_sure_dk)
        curr_dt_utc = curr_dt_tr.replace(tzinfo=tr_tz).astimezone(timezone.utc)
        
        azimuth, elevation = get_solar_position(curr_lat, curr_lon, curr_dt_utc)
        
        if elevation > 0:
            gunduz_count += 1
            rel_angle = (azimuth - bearing + 360) % 360
            if 0 < rel_angle < 180:
                sag_count += 1
            elif 180 < rel_angle < 360:
                sol_count += 1

    if gunduz_count == 0:
        return 0, 0, True
        
    sol_orani = round((sol_count / gunduz_count) * 100)
    sag_orani = round((sag_count / gunduz_count) * 100)
    return sol_orani, sag_orani, False

# Kullanıcı Giriş Alanları
col1, col2 = st.columns(2)
with col1:
    kalkis = st.text_input("Kalkış Yeri (Şehir)", "Muş")
with col2:
    varis = st.text_input("Varış Yeri (Şehir)", "İzmir")

kalkis_saati = st.time_input("Kalkış Saati", datetime.strptime("10:00", "%H:%M").time())

col3, col4 = st.columns(2)
with col3:
    mola_sayisi = st.number_input("Mola Sayısı", min_value=0, max_value=5, value=1)
with col4:
    mola_suresi = st.number_input("Her Mola Süresi (Dakika)", min_value=0, max_value=60, value=20)

if st.button("Gölge Analizini Başlat", type="primary"):
    if not kalkis or not varis:
        st.warning("Lütfen kalkış ve varış yerlerini giriniz.")
    else:
        with st.spinner("Gerçek güneş pozisyonu ve rotalar hesaplanıyor..."):
            
            def koordinat_bul(sehir):
                sehir_temiz = turkce_temizle(sehir)
                if sehir_temiz in SEHIR_KOORDINATLARI:
                    return SEHIR_KOORDINATLARI[sehir_temiz]
                
                # Yedek olarak harita servisi sorgusu
                try:
                    encoded_sehir = urllib.parse.quote(sehir.strip())
                    url = f"https://nominatim.openstreetmap.org/search?q={encoded_sehir},Turkey&format=json"
                    headers = {'User-Agent': 'BusShadowApp-V6'}
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
                st.error(f"'{kalkis}' veya '{varis}' şehri bulunamadı. Lütfen adını kontrol edin.")
            else:
                osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
                surus_suresi_dk = 480 
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
                
                sol_gunes_orani, sag_gunes_orani, gece_mi = analyze_sun_exposure(lat1, lon1, lat2, lon2, kalkis_dt, toplam_sure_dk)
                
                st.success("Gerçek Astronomik Hesaplama Tamamlandı!")
                st.info(f"📍 **Rota:** {kalkis} ➔ {varis}")
                
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Sürüş Süresi", f"{surus_suresi_dk // 60} sa {surus_suresi_dk % 60} dk")
                m_col2.metric("Mola", f"{toplam_mola_dk} dk")
                m_col3.metric("Varış Saati", varis_dt.strftime("%H:%M"))
                
                st.markdown("---")
                st.subheader("🚌 Otobüs Koltuk ve Gölge Krokisi")
                
                if gece_mi:
                    st.info("🌙 Yolculuk tamamen gece saatlerine denk geldiği için doğrudan güneş ışığı maruziyeti yoktur. İstediğiniz koltuğu seçebilirsiniz.")
                else:
                    st.write("Hesaplanan gerçek astronomik güneş açılarına göre taraf analizi:")
                    
                    bus_col_sol, bus_col_koridor, bus_col_sag = st.columns([2, 1, 2])
                    
                    with bus_col_sol:
                        st.markdown("#### 🪟 Sol Taraf")
                        if sol_gunes_orani <= sag_gunes_orani:
                            st.success(f"🟢 Gölgede / Az Güneşli\n\n(Güneş Alma Oranı: %{sol_gunes_orani})")
                            st.markdown("✨ **Tavsiye Edilen**")
                        else:
                            st.error(f"☀️ Güneş Alır\n\n(Güneş Alma Oranı: %{sol_gunes_orani})")
                            
                    with bus_col_koridor:
                        st.markdown("<br><center>🚶‍♂️<br><b>Koridor</b></center>", unsafe_allow_html=True)
                        
                    with bus_col_sag:
                        st.markdown("#### 🪟 Sağ Taraf")
                        if sag_gunes_orani < sol_gunes_orani:
                            st.success(f"🟢 Gölgede / Az Güneşli\n\n(Güneş Alma Oranı: %{sag_gunes_orani})")
                            st.markdown("✨ **Tavsiye Edilen**")
                        else:
                            st.error(f"☀️️ Güneş Alır\n\n(Güneş Alma Oranı: %{sag_gunes_orani})")
                            st.markdown("⚠️ **Dikkat**")
