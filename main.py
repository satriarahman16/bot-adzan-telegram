import requests
import os
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")  
CHAT_ID = os.getenv("CHAT_ID")  
KOTA = "Banjarmasin"
NEGARA = "Indonesia"

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"})

def ambil_jadwal_sholat():
    url = f"http://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    response = requests.get(url).json()
    timings = response['data']['timings']
    return {k: timings[k] for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]}

def cek_dan_kirim():
    # UTC+8 untuk Banjarmasin
    waktu_sekarang = datetime.utcnow() + timedelta(hours=8)
    jam_menit_sekarang = waktu_sekarang.strftime("%H:%M")
    
    jadwal = ambil_jadwal_sholat()
    nama_sholat = {"Fajr": "Subuh", "Dhuhr": "Dzuhur", "Asr": "Ashar", "Maghrib": "Maghrib", "Isha": "Isya"}

    for key, waktu_adzan in jadwal.items():
        # Cek apakah waktu sekarang adalah 5 menit sebelum adzan
        obj_adzan = datetime.strptime(waktu_adzan, "%H:%M")
        waktu_pengingat = (obj_adzan - timedelta(minutes=5)).strftime("%H:%M")

        if jam_menit_sekarang == waktu_pengingat:
            sholat = nama_sholat[key]
            pesan = f"⏳ *PENGINGAT SHOLAT* ⏳\n\n5 menit lagi waktu *{sholat}* ({waktu_adzan} WITA)."
            kirim_telegram(pesan)
            print(f"Sent reminder for {sholat}")

if __name__ == "__main__":
    cek_dan_kirim()