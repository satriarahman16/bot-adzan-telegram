import requests
import os
from datetime import datetime, timedelta
import time
from flask import Flask
from threading import Thread

# --- KONFIGURASI TELEGRAM (MENGGUNAKAN ENVIRONMENT VARIABLES) ---
# Kunci rahasia akan diambil dari brankas Render, bukan ditulis di sini
BOT_TOKEN = os.getenv("BOT_TOKEN")  
CHAT_ID = os.getenv("CHAT_ID")  

# Pengaturan Lokasi saat ini (WITA)
KOTA = "Banjarmasin" 
NEGARA = "Indonesia"
# ----------------------------------------------------------------

# --- 1. SETUP WEB SERVER MINI (ANTI-TIDUR UNTUK RENDER) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Server Bot Adzan Menyala 24/7!"

def jalankan_server():
    # Berjalan di port 10000 (standar Render) atau 8080
    app.run(host='0.0.0.0', port=10000)

# --- 2. FUNGSI BOT TELEGRAM & ADZAN ---
def kirim_telegram(pesan):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: BOT_TOKEN atau CHAT_ID belum disetting di Render!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": pesan,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sistem saat mengirim pesan: {e}")

def ambil_jadwal_sholat():
    url = f"http://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    try:
        response = requests.get(url).json()
        timings = response['data']['timings']
        return {
            "Subuh": timings['Fajr'],
            "Dzuhur": timings['Dhuhr'],
            "Ashar": timings['Asr'],
            "Maghrib": timings['Maghrib'],
            "Isya": timings['Isha']
        }
    except Exception as e:
        print("Gagal mengambil jadwal sholat dari API:", e)
        return None

def pantau_waktu():
    pesan_terkirim = []
    tanggal_hari_ini = ""
    
    # Pesan tes saat server baru menyala
    kirim_telegram(f"🚀 *Sistem Cloud Aktif!*\nBot berhasil di-deploy dan siap memantau waktu sholat untuk wilayah {KOTA}.")
    print("Sistem pemantau waktu mulai berjalan...")

    while True:
        # Menyesuaikan zona waktu Banjarmasin (WITA = UTC+8)
        waktu_sekarang_wita = datetime.utcnow() + timedelta(hours=8) 
        tanggal_sekarang = waktu_sekarang_wita.strftime("%Y-%m-%d")
        jam_menit_sekarang = waktu_sekarang_wita.strftime("%H:%M")

        # Update jadwal setiap berganti hari
        if tanggal_sekarang != tanggal_hari_ini:
            jadwal_hari_ini = ambil_jadwal_sholat()
            pesan_terkirim = [] 
            tanggal_hari_ini = tanggal_sekarang
            print(f"--- Jadwal {tanggal_hari_ini} Diperbarui ---")

        # Cek apakah waktu saat ini = waktu adzan dikurangi 5 menit
        if jadwal_hari_ini:
            for sholat, waktu_adzan in jadwal_hari_ini.items():
                jam_adzan = datetime.strptime(waktu_adzan, "%H:%M")
                waktu_pengingat = (jam_adzan - timedelta(minutes=5)).strftime("%H:%M")

                if jam_menit_sekarang == waktu_pengingat and sholat not in pesan_terkirim:
                    pesan_adzan = f"⏳ *PENGINGAT SHOLAT* ⏳\n\n5 menit lagi masuk waktu sholat *{sholat}* untuk wilayah {KOTA}.\n(Waktu Adzan: {waktu_adzan} WITA).\n\nSiap-siap ambil wudhu ya!"
                    kirim_telegram(pesan_adzan)
                    pesan_terkirim.append(sholat)
                    print(f"Berhasil mengirim pengingat {sholat}")

        # Istirahatkan script 30 detik agar server tidak terbebani
        time.sleep(30)

# --- 3. EKSEKUSI UTAMA ---
if __name__ == "__main__":
    # Jalankan web server Flask di latar belakang
    Thread(target=jalankan_server).start()
    
    # Jalankan pemantau waktu Adzan
    pantau_waktu()