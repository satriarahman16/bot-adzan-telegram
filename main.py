import requests
import os
import pytz
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
    """Fungsi mengirim pesan ke Telegram dengan Timeout & Error Handling"""
    if not BOT_TOKEN or not CHAT_ID:
        print("GAGAL: Token atau Chat ID kosong!")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": pesan,
            "parse_mode": "Markdown"
        }, timeout=10)
        result = resp.json()
        if result.get("ok"):
            print("SUKSES: Pesan terkirim ke Telegram.")
            return True
        else:
            print(f"GAGAL dari Telegram API: {result.get('description')}")
            return False
    except Exception as e:
        print(f"GAGAL: Error saat kirim Telegram -> {e}")
        return False

def cek_ramalan_cuaca(target_jam):
    """Fungsi mengambil data cuaca dari OpenWeatherMap"""
    url = (f"https://api.openweathermap.org/data/2.5/forecast"
           f"?lat={LAT}&lon={LON}&appid={WEATHER_API_KEY}&units=metric&lang=id")
    try:
        res = requests.get(url, timeout=10).json()
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
    """Fungsi mengambil waktu sholat hari ini (HTTPS)"""
    url = f"https://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    try:
        resp = requests.get(url, timeout=10).json()
        return resp['data']['timings']
    except Exception as e:
        print(f"GAGAL: Error mengambil jadwal sholat -> {e}")
        return None

def jalankan_bot():
    # --- MENGGUNAKAN PYTZ UNTUK ZONA WAKTU JAYAPURA ---
    tz_jayapura = pytz.timezone('Asia/Jayapura')
    waktu_skrg = datetime.now(tz_jayapura)

    jam_menit = waktu_skrg.strftime("%H:%M")
    tanggal = waktu_skrg.strftime("%d/%m/%Y")

    print(f"=== BOT BERJALAN PADA {tanggal} JAM {jam_menit} WIT ===")

    # --- FITUR 1: STATUS PAGI ---
    # Toleransi 20 menit agar pasti terkirim walau GitHub telat bangun
    if "05:00" <= jam_menit <= "05:19":
        kirim_telegram(
            f"✅ *LAPORAN PAGI*\n"
            f"Bot aktif pada {tanggal}.\n"
            f"Sistem berjalan normal. Semangat, Satria!"
        )

    # --- FITUR 2: RAMALAN CUACA ---
    jadwal_cuaca = {"08:00": "09", "15:00": "16", "19:00": "20"}
    for pemicu, target in jadwal_cuaca.items():
        # Toleransi 20 menit (Jaring Lebar Anti-Delay)
        batas_akhir = (datetime.strptime(pemicu, "%H:%M") + timedelta(minutes=20)).strftime("%H:%M")
        if pemicu <= jam_menit <= batas_akhir:
            print(f"DEBUG: Masuk waktu pengiriman cuaca jam {target}:00")
            cek_ramalan_cuaca(target)

    # --- FITUR 3: PENGINGAT ADZAN ---
    jadwal = ambil_jadwal_sholat()
    if not jadwal: return

    sholat_list = {
        "Fajr": "Subuh", "Dhuhr": "Dzuhur", "Asr": "Ashar",
        "Maghrib": "Maghrib", "Isha": "Isya"
    }

    for s, nama in sholat_list.items():
        waktu_adzan_raw = jadwal[s]
        # Bersihkan format string dari API (Sangat Penting)
        waktu_adzan_bersih = waktu_adzan_raw.split(" ")[0].strip()

        try:
            obj_adzan = datetime.strptime(waktu_adzan_bersih, "%H:%M").replace(
                year=waktu_skrg.year, month=waktu_skrg.month, day=waktu_skrg.day
            )
        except ValueError:
            print(f"DEBUG: Format waktu error untuk {nama}: '{waktu_adzan_raw}'")
            continue

        obj_adzan_aware = tz_jayapura.localize(obj_adzan)
        selisih = (obj_adzan_aware - waktu_skrg).total_seconds() / 60

        print(f"DEBUG: {nama} = {waktu_adzan_bersih} WIT | Selisih = {selisih:.1f} menit")

        # 🚀 PERUBAHAN UTAMA: JARING ANTI-BADAI DELAY GITHUB
        # Menangkap dari 25 Menit SEBELUM adzan HINGGA 10 Menit SETELAH adzan (Total Jendela 35 Menit)
        if -10 <= selisih <= 25:
            if selisih < 0:
                teks_waktu = f"Sudah lewat *{abs(int(selisih))} menit yang lalu*"
            elif selisih < 1:
                teks_waktu = "*SEKARANG*"
            else:
                teks_waktu = f"Sekitar *{int(selisih)} menit lagi*"

            kirim_telegram(
                f"🕌 *PENGINGAT {nama.upper()}*\n\n"
                f"{teks_waktu} masuk waktu *{nama}*\n"
                f"untuk wilayah Jayapura ({waktu_adzan_bersih} WIT).\n"
                f"Mari bersiap-siap!"
            )
            break # Hentikan loop pencarian sholat, biarkan fungsi berlanjut

if __name__ == "__main__":
    jalankan_bot()