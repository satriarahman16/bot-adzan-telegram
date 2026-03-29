import requests
import os
from datetime import datetime, timedelta

# --- KONFIGURASI SECRETS (Diambil dari GitHub Actions) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# --- SETTING LOKASI JAYAPURA ---
KOTA = "Jayapura"
NEGARA = "Indonesia"
LAT = "-2.5916"
LON = "140.669"

def kirim_telegram(pesan):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Token atau Chat ID tidak ditemukan!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def cek_ramalan_cuaca(untuk_jam):
    # Menggunakan API Forecast (Ramalan) 5 hari / 3 jam
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={WEATHER_API_KEY}&units=metric&lang=id"
    try:
        data = requests.get(url).json()
        # Ambil ramalan indeks 0 (biasanya mencakup 3 jam ke depan)
        forecast = data['list'][0]
        temp = forecast['main']['temp']
        deskripsi = forecast['weather'][0]['description']
        
        pesan = (f"🔮 *PREDIKSI CUACA JAYAPURA*\n"
                 f"Untuk jam: *{untuk_jam}:00 WIT*\n\n"
                 f"Kondisi: *{deskripsi.capitalize()}*\n"
                 f"Suhu: {temp}°C\n\n"
                 f"_(Laporan otomatis dikirim 1 jam sebelumnya)_")
        kirim_telegram(pesan)
    except Exception as e:
        print(f"Gagal ambil ramalan cuaca: {e}")

def ambil_jadwal_sholat():
    url = f"http://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    try:
        res = requests.get(url).json()
        return res['data']['timings']
    except Exception as e:
        print(f"Gagal ambil jadwal sholat: {e}")
        return None

def cek_dan_kirim():
    # Waktu Jayapura (UTC+9)
    waktu_skrg = datetime.utcnow() + timedelta(hours=9)
    jam_menit = waktu_skrg.strftime("%H:%M")
    tanggal_skrg = waktu_skrg.strftime("%d %B %Y")
    
    print(f"--- Menjalankan Bot ({jam_menit} WIT) ---")

    # 1. LAPORAN STATUS PAGI (Jam 05:00 WIT)
    if "05:00" <= jam_menit <= "05:05":
        pesan_status = (f"✅ *LAPORAN SISTEM AKTIF*\n"
                        f"📅 Tanggal: {tanggal_skrg}\n"
                        f"📍 Lokasi: {KOTA}, Papua\n"
                        f"🤖 Status: Bot berjalan normal.\n\n"
                        f"Selamat pagi dan semangat beraktivitas, Satria!")
        kirim_telegram(pesan_status)

    # 2. RAMALAN CUACA (Dikirim 1 jam sebelum target: 09, 16, 20)
    jadwal_cuaca = {"08:00": "09", "15:00": "16", "19:00": "20"}
    for pemicu, target in jadwal_cuaca.items():
        if pemicu <= jam_menit <= (datetime.strptime(pemicu, "%H:%M") + timedelta(minutes=5)).strftime("%H:%M"):
            cek_ramalan_cuaca(target)

    # 3. PENGINGAT ADZAN (Rentang 6-10 menit sebelum)
    jadwal = ambil_jadwal_sholat()
    if not jadwal: return
    
    sholat_list = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    nama_indo = {"Fajr":"Subuh", "Dhuhr":"Dzuhur", "Asr":"Ashar", "Maghrib":"Maghrib", "Isha":"Isya"}
    
    for s in sholat_list:
        waktu_adzan = jadwal[s]
        obj_adzan = datetime.strptime(waktu_adzan, "%H:%M").replace(
            year=waktu_skrg.year, month=waktu_skrg.month, day=waktu_skrg.day)
        
        selisih = (obj_adzan - waktu_skrg).total_seconds() / 60
        
        # Jika waktu adzan tinggal 6 s/d 10 menit lagi
        if 6 <= selisih <= 10.5:
            sholat = nama_indo[s]
            kirim_telegram(f"⏳ *PENGINGAT SHOLAT ({KOTA})*\n\nSekitar 10 menit lagi waktu *{sholat}* ({waktu_adzan} WIT). Mari bersiap-siap!")
            print(f"Pesan {sholat} terkirim.")
            return

if __name__ == "__main__":
    cek_dan_kirim()