import requests
import os
import pytz
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

KOTA = "Jayapura"
NEGARA = "Indonesia"
LAT = "-2.5916"
LON = "140.669"

def kirim_telegram(pesan):
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
            # ✅ Tampilkan error spesifik dari Telegram
            print(f"GAGAL dari Telegram API: {result.get('description')}")
            return False
    except Exception as e:
        print(f"GAGAL: Error saat kirim Telegram -> {e}")
        return False

def cek_ramalan_cuaca(target_jam):
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
    url = f"https://api.aladhan.com/v1/timingsByCity?city={KOTA}&country={NEGARA}&method=11"
    try:
        resp = requests.get(url, timeout=10).json()
        return resp['data']['timings']
    except Exception as e:
        print(f"GAGAL: Error mengambil jadwal sholat -> {e}")
        return None

def jalankan_bot():
    tz_jayapura = pytz.timezone('Asia/Jayapura')
    waktu_skrg = datetime.now(tz_jayapura)

    jam_menit = waktu_skrg.strftime("%H:%M")
    tanggal = waktu_skrg.strftime("%d/%m/%Y")

    print(f"=== BOT BERJALAN PADA {tanggal} JAM {jam_menit} WIT ===")

    # --- FITUR 1: STATUS PAGI ---
    if "05:00" <= jam_menit <= "05:09":
        kirim_telegram(
            f"✅ *LAPORAN PAGI*\n"
            f"Bot aktif pada {tanggal}.\n"
            f"Sistem berjalan normal. Semangat, Satria!"
        )

    # --- FITUR 2: RAMALAN CUACA ---
    jadwal_cuaca = {"08:00": "09", "15:00": "16", "19:00": "20"}
    for pemicu, target in jadwal_cuaca.items():
        # Jendela hanya 9 menit (2x run cron) agar tidak double kirim
        batas_akhir = (datetime.strptime(pemicu, "%H:%M") + timedelta(minutes=9)).strftime("%H:%M")
        if pemicu <= jam_menit <= batas_akhir:
            print(f"DEBUG: Masuk waktu pengiriman cuaca jam {target}:00")
            cek_ramalan_cuaca(target)

    # --- FITUR 3: PENGINGAT ADZAN ---
    jadwal = ambil_jadwal_sholat()
    if not jadwal:
        return

    sholat_list = {
        "Fajr": "Subuh", "Dhuhr": "Dzuhur", "Asr": "Ashar",
        "Maghrib": "Maghrib", "Isha": "Isya"
    }

    for s, nama in sholat_list.items():
        waktu_adzan_raw = jadwal[s]

        # ✅ Bersihkan format misal "04:32 (WIT)" → "04:32"
        waktu_adzan_bersih = waktu_adzan_raw.split(" ")[0].strip()

        try:
            obj_adzan = datetime.strptime(waktu_adzan_bersih, "%H:%M").replace(
                year=waktu_skrg.year,
                month=waktu_skrg.month,
                day=waktu_skrg.day
            )
        except ValueError:
            print(f"DEBUG: Format waktu tidak dikenali untuk {nama}: '{waktu_adzan_raw}'")
            continue

        obj_adzan_aware = tz_jayapura.localize(obj_adzan)
        selisih = (obj_adzan_aware - waktu_skrg).total_seconds() / 60

        print(f"DEBUG: {nama} = {waktu_adzan_bersih} WIT | Selisih = {selisih:.1f} menit")

        # ✅ Jendela 10 menit saja (2x run cron) — cukup untuk antisipasi delay
        # Hindari jendela terlalu lebar agar tidak double kirim
        if 0 <= selisih <= 10:
            if selisih < 1:
                teks_waktu = "*SEKARANG*"
            else:
                teks_waktu = f"Sekitar *{int(selisih)} menit lagi*"

            kirim_telegram(
                f"🕌 *PENGINGAT {nama.upper()}*\n\n"
                f"{teks_waktu} masuk waktu *{nama}*\n"
                f"untuk wilayah Jayapura ({waktu_adzan_bersih} WIT).\n"
                f"Mari bersiap-siap!"
            )
            break

if __name__ == "__main__":
    jalankan_bot()