import requests
import os
from datetime import datetime, timedelta

# --- KONFIGURASI ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  
CHAT_ID = os.getenv("CHAT_ID")  
KOTA = "Jayapura"
NEGARA = "Indonesia"

def kirim_telegram(pesan):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Token atau Chat ID belum diatur di Secrets!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def ambil_jadwal_sholat():
    url = f"http://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    try:
        response = requests.get(url).json()
        timings = response['data']['timings']
        return {k: timings[k] for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]}
    except Exception as e:
        print(f"Gagal ambil API: {e}")
        return None

def cek_dan_kirim():
    # Jayapura WIT (UTC+9)
    waktu_sekarang_obj = datetime.utcnow() + timedelta(hours=9)
    jam_menit_sekarang = waktu_sekarang_obj.strftime("%H:%M")
    
    jadwal = ambil_jadwal_sholat()
    if not jadwal: return

    nama_sholat = {
        "Fajr": "Subuh", 
        "Dhuhr": "Dzuhur", 
        "Asr": "Ashar", 
        "Maghrib": "Maghrib", 
        "Isha": "Isya"
    }

    print(f"--- Pengecekan Sistem ({jam_menit_sekarang} WIT) ---")

    for key, waktu_adzan in jadwal.items():
        # Ubah string waktu adzan ke objek datetime hari ini
        jam_adzan_obj = datetime.strptime(waktu_adzan, "%H:%M").replace(
            year=waktu_sekarang_obj.year, 
            month=waktu_sekarang_obj.month, 
            day=waktu_sekarang_obj.day
        )

        # Hitung selisih dalam menit
        selisih_detik = (jam_adzan_obj - waktu_sekarang_obj).total_seconds()
        selisih_menit = selisih_detik / 60

        # LOGIKA AMAN: Jika waktu adzan tinggal 6 s/d 10 menit lagi
        if 6 <= selisih_menit <= 10.5:
            sholat = nama_sholat[key]
            pesan = f"⏳ *PENGINGAT SHOLAT ({KOTA})* ⏳\n\nSekitar 10 menit lagi masuk waktu *{sholat}*.\n(Waktu Adzan: {waktu_adzan} WIT).\n\nMari bersiap-siap!"
            kirim_telegram(pesan)
            print(f"✅ Pengingat {sholat} terkirim (Selisih: {round(selisih_menit, 2)} menit)")
            return # Keluar agar tidak mengecek sholat lainnya di jam yang sama

    print("Belum masuk waktu pengingat.")

if __name__ == "__main__":
    cek_dan_kirim()