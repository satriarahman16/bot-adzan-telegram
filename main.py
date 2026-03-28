import requests
import os
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")  
CHAT_ID = os.getenv("CHAT_ID")  
# Karena Anda di Jayapura, kita pakai Jayapura
KOTA = "Jayapura"
NEGARA = "Indonesia"

def kirim_telegram(pesan):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Token atau Chat ID kosong!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"})

def ambil_jadwal_sholat():
    url = f"http://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    response = requests.get(url).json()
    timings = response['data']['timings']
    return {k: timings[k] for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]}

def cek_dan_kirim():
    # Jayapura adalah WIT (UTC+9)
    waktu_sekarang = datetime.utcnow() + timedelta(hours=9)
    jam_menit_sekarang = waktu_sekarang.strftime("%H:%M")
    
    jadwal = ambil_jadwal_sholat()
    nama_sholat = {"Fajr": "Subuh", "Dhuhr": "Dzuhur", "Asr": "Ashar", "Maghrib": "Maghrib", "Isha": "Isya"}

    print(f"Mengecek jadwal untuk {KOTA} jam {jam_menit_sekarang} WIT...")

    for key, waktu_adzan in jadwal.items():
        obj_adzan = datetime.strptime(waktu_adzan, "%H:%M")
        waktu_pengingat = (obj_adzan - timedelta(minutes=5)).strftime("%H:%M")

        if jam_menit_sekarang == waktu_pengingat:
            sholat = nama_sholat[key]
            pesan = f"⏳ *PENGINGAT SHOLAT* ⏳\n\n5 menit lagi waktu *{sholat}* ({waktu_adzan} WIT)."
            kirim_telegram(pesan)
            print(f"Sent reminder for {sholat}")

if __name__ == "__main__":
    # --- BARIS PENGETESAN (Bisa dihapus nanti jika sudah oke) ---
    waktu_tes = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S")
    kirim_telegram(f"🚀 *Tes Bot Adzan Berhasil!*\nBot sedang aktif memantau jadwal sholat {KOTA}.\nWaktu saat ini: {waktu_tes} WIT.")
    # ------------------------------------------------------------
    
    cek_dan_kirim()