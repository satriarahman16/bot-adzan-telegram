import requests
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI SECRETS ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

KOTA = "Jayapura"
NEGARA = "Indonesia"
LAT = "-2.5916"
LON = "140.669"

def kirim_telegram(pesan):
    """Fungsi dasar untuk mengirim pesan ke Telegram"""
    if not BOT_TOKEN or not CHAT_ID: 
        print("GAGAL: Token atau Chat ID kosong!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"})
        print("SUKSES: Pesan terkirim ke Telegram.")
    except Exception as e:
        print(f"GAGAL: Terjadi error saat kirim Telegram -> {e}")

def cek_ramalan_cuaca(target_jam):
    """Fungsi mengambil data cuaca dari OpenWeatherMap"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={WEATHER_API_KEY}&units=metric&lang=id"
    try:
        res = requests.get(url).json()
        # Ambil cuaca terdekat saat ini
        cuaca = res['list'][0]
        temp = cuaca['main']['temp']
        desc = cuaca['weather'][0]['description'].title()
        
        pesan = (f"🔮 *PREDIKSI CUACA JAYAPURA*\n"
                 f"Untuk sekitar jam: *{target_jam}:00 WIT*\n\n"
                 f"Kondisi: *{desc}*\n"
                 f"Suhu: {temp}°C\n\n"
                 f"_(Laporan otomatis dari Bot Satria)_")
        kirim_telegram(pesan)
    except Exception as e:
        print(f"GAGAL: Error mengambil data cuaca -> {e}")

def ambil_jadwal_sholat():
    """Fungsi mengambil waktu sholat hari ini"""
    url = f"http://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    try:
        return requests.get(url).json()['data']['timings']
    except Exception as e:
        print(f"GAGAL: Error mengambil jadwal sholat -> {e}")
        return None

def jalankan_bot():
    # Set Waktu Jayapura (UTC+9)
    waktu_skrg = datetime.utcnow() + timedelta(hours=9)
    jam_menit = waktu_skrg.strftime("%H:%M")
    tanggal = waktu_skrg.strftime("%d/%m/%Y")
    
    print(f"=== BOT BERJALAN PADA {tanggal} JAM {jam_menit} WIT ===")

    # --- FITUR 1: STATUS PAGI ---
    # Jika GitHub jalan di antara jam 05:00 sampai 05:14 WIT
    if "05:00" <= jam_menit <= "05:14":
        kirim_telegram(f"✅ *LAPORAN PAGI*\nBot aktif pada {tanggal}.\nSistem berjalan normal. Semangat, Satria!")

    # --- FITUR 2: RAMALAN CUACA ---
    # Jendela waktu dibuat 14 menit agar PASTI kena meskipun GitHub delay
    jadwal_cuaca = {"08:00": "09", "15:00": "16", "19:00": "20"}
    
    for pemicu, target in jadwal_cuaca.items():
        # Hitung batas toleransi (pemicu + 14 menit)
        batas_akhir = (datetime.strptime(pemicu, "%H:%M") + timedelta(minutes=14)).strftime("%H:%M")
        
        if pemicu <= jam_menit <= batas_akhir:
            print(f"DEBUG: Masuk waktu pengiriman cuaca untuk jam {target}:00")
            cek_ramalan_cuaca(target)

    # --- FITUR 3: PENGINGAT ADZAN ---
    jadwal = ambil_jadwal_sholat()
    if not jadwal: return
    
    sholat_list = {"Fajr":"Subuh", "Dhuhr":"Dzuhur", "Asr":"Ashar", "Maghrib":"Maghrib", "Isha":"Isya"}
    
    for s, nama in sholat_list.items():
        waktu_adzan = jadwal[s]
        adzan_dt = datetime.strptime(waktu_adzan, "%H:%M").replace(
            year=waktu_skrg.year, month=waktu_skrg.month, day=waktu_skrg.day)
        
        selisih = (adzan_dt - waktu_skrg).total_seconds() / 60
        
        # Jika sisa waktu menuju adzan adalah 1 hingga 15 menit
        if 1 <= selisih <= 16:
            kirim_telegram(f"⏳ *PENGINGAT {nama.upper()}*\n\nSekitar {int(selisih)} menit lagi masuk waktu *{nama}* untuk wilayah Jayapura ({waktu_adzan} WIT).\nMari bersiap-siap!")
            return # Hentikan loop agar tidak double cek

if __name__ == "__main__":
    jalankan_bot()