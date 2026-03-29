import requests
import os
from datetime import datetime, timedelta

# --- KONFIGURASI SECRETS ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# --- SETTING LOKASI JAYAPURA ---
KOTA = "Jayapura"
NEGARA = "Indonesia"
LAT = "-2.5916"
LON = "140.669"

def kirim_telegram(pesan):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"})

def cek_ramalan_cuaca(untuk_jam):
    # Menggunakan API Forecast (Ramalan) 5 hari / 3 jam
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={WEATHER_API_KEY}&units=metric&lang=id"
    try:
        data = requests.get(url).json()
        # Ambil ramalan terdekat (indeks 0 biasanya untuk 3 jam ke depan)
        forecast = data['list'][0]
        temp = forecast['main']['temp']
        deskripsi = forecast['weather'][0]['description']
        
        pesan = (f"🔮 *PREDIKSI CUACA JAYAPURA*\n"
                 f"Untuk jam: *{untuk_jam}:00 WIT*\n\n"
                 f"Kondisi: *{deskripsi.capitalize()}*\n"
                 f"Suhu: {temp}°C\n\n"
                 f"_(Laporan ini dikirim otomatis 1 jam sebelumnya)_")
        kirim_telegram(pesan)
    except Exception as e:
        print(f"Gagal ambil ramalan: {e}")

def ambil_jadwal_sholat():
    url = f"http://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    try:
        res = requests.get(url).json()
        return res['data']['timings']
    except: return None

def cek_dan_kirim():
    # Waktu Jayapura (UTC+9)
    waktu_skrg = datetime.utcnow() + timedelta(hours=9)
    jam_menit = waktu_skrg.strftime("%H:%M")
    
    # 1. LOGIKA RAMALAN CUACA (Dikirim 1 jam sebelum target)
    # Target jam 09:00 -> Dikirim jam 08:00
    # Target jam 16:00 -> Dikirim jam 15:00
    # Target jam 20:00 -> Dikirim jam 19:00
    jadwal_kirim = {"08:00": "09", "15:00": "16", "19:00": "20"}

    for pemicu, target in jadwal_kirim.items():
        # Rentang 5 menit agar tidak terlewat delay GitHub
        if pemicu <= jam_menit <= (datetime.strptime(pemicu, "%H:%M") + timedelta(minutes=5)).strftime("%H:%M"):
            marker = f"sent_{target}.txt"
            if not os.path.exists(marker):
                cek_ramalan_cuaca(target)
                with open(marker, "w") as f: f.write("ok")

    # Reset marker setiap tengah malam
    if jam_menit == "00:00":
        for target in ["09", "16", "20"]:
            if os.path.exists(f"sent_{target}.txt"): os.remove(f"sent_{target}.txt")

    # 2. LOGIKA ADZAN (10 menit sebelum)
    jadwal = ambil_jadwal_sholat()
    if not jadwal: return
    
    sholat_list = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    nama_indo = {"Fajr":"Subuh", "Dhuhr":"Dzuhur", "Asr":"Ashar", "Maghrib":"Maghrib", "Isha":"Isya"}
    
    for s in sholat_list:
        waktu_adzan = jadwal[s]
        obj_adzan = datetime.strptime(waktu_adzan, "%H:%M").replace(
            year=waktu_skrg.year, month=waktu_skrg.month, day=waktu_skrg.day)
        
        selisih = (obj_adzan - waktu_skrg).total_seconds() / 60
        
        if 6 <= selisih <= 10.5:
            kirim_telegram(f"⏳ *PENGINGAT SHOLAT*\n\nSekitar 10 menit lagi waktu *{nama_indo[s]}* ({waktu_adzan} WIT).")
            return

if __name__ == "__main__":
    cek_dan_kirim()