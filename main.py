import os
import telebot
import subprocess
import json
from telebot import types
from datetime import datetime
from collections import defaultdict
from random import randint, choice
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

KOORDINAT_DAERAH = {
    "KAB. BANTUL": (-7.888056, 110.328056),
    "KAB. CIANJUR": (-6.8161, 107.1424),
    "KAB. BOGOR": (-6.595, 106.816),
    "KAB. MAGELANG": (-7.4799, 110.2172)
}

PASARAN_JAWA = ["Legi", "Pahing", "Pon", "Wage", "Kliwon"]
user_counter = defaultdict(int)

ADMIN_IDS = [123456789]  # Ganti dengan user ID kamu

def is_admin(user_id):
    return user_id in ADMIN_IDS

@bot.message_handler(commands=['myid'])
def get_my_id(message):
    bot.reply_to(message, f"🆔 User ID kamu adalah: `{message.from_user.id}`", parse_mode="Markdown")

def validasi_nik(nik):
    return bool(re.fullmatch(r'\d{16}', nik))

def hitung_umur(tanggal_lahir_str):
    try:
        tanggal = datetime.strptime(tanggal_lahir_str, "%d %B %Y")
        today = datetime.today()
        return today.year - tanggal.year - ((today.month, today.day) < (tanggal.month, tanggal.day))
    except:
        return "-"

def cari_zodiak(tanggal_lahir_str):
    try:
        tgl = datetime.strptime(tanggal_lahir_str, "%d %B %Y")
        bulan, hari = tgl.month, tgl.day
        zodiak_list = [
            ((1, 20), (2, 18), "Aquarius"), ((2, 19), (3, 20), "Pisces"),
            ((3, 21), (4, 19), "Aries"), ((4, 20), (5, 20), "Taurus"),
            ((5, 21), (6, 20), "Gemini"), ((6, 21), (7, 22), "Cancer"),
            ((7, 23), (8, 22), "Leo"), ((8, 23), (9, 22), "Virgo"),
            ((9, 23), (10, 22), "Libra"), ((10, 23), (11, 21), "Scorpio"),
            ((11, 22), (12, 21), "Sagittarius"), ((12, 22), (1, 19), "Capricorn")
        ]
        for start, end, name in zodiak_list:
            if (bulan == start[0] and hari >= start[1]) or (bulan == end[0] and hari <= end[1]):
                return name
        return "-"
    except:
        return "-"

def cari_pasaran(tanggal_lahir_str):
    try:
        base = datetime(1900, 1, 1)
        target = datetime.strptime(tanggal_lahir_str, "%d %B %Y")
        selisih = (target - base).days
        return PASARAN_JAWA[selisih % 5]
    except:
        return "-"

def generate_random_nik():
    wilayah = choice(["320301", "340207", "330204", "337401"])
    kelamin = choice(["L", "P"])
    tgl = datetime(randint(1950, 2010), randint(1, 12), randint(1, 28))
    hari = tgl.day + (40 if kelamin == "P" else 0)
    tgllhr = f"{hari:02d}{tgl.month:02d}{str(tgl.year)[2:]}"
    akhir = "".join([str(randint(0, 9)) for _ in range(4)])
    return wilayah + tgllhr + akhir

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Selamat datang!\nKetik /help untuk melihat fitur yang tersedia.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📖 *Perintah:*\n"
        "/ceknik <NIK> - Cek info lengkap\n"
        "/randomnik - NIK acak\n"
        "/topuser - Ranking pengguna (admin)\n"
        "/loglast - Log terakhir (admin)\n"
        "/lacaknik <NIK> - Estimasi lokasi (admin)\n"
        "/myid - Lihat user ID\n"
        "/about - Tentang bot"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['about'])
def send_about(message):
    bot.reply_to(message, "🤖 Bot pemeriksa NIK dengan lokasi, umur, zodiak, dan pasaran Jawa.\nDibuat oleh @yourtelegramusername", parse_mode="Markdown")

@bot.message_handler(commands=['randomnik'])
def random_nik(message):
    bot.reply_to(message, f"🔢 Contoh NIK Acak:\n`{generate_random_nik()}`", parse_mode="Markdown")

@bot.message_handler(commands=['topuser'])
def top_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 Hanya admin.")
        return
    if not user_counter:
        bot.reply_to(message, "📭 Belum ada aktivitas.")
        return
    ranking = sorted(user_counter.items(), key=lambda x: x[1], reverse=True)
    hasil = "\n".join([f"{i+1}. @{u} - {c}x" for i, (u, c) in enumerate(ranking[:5])])
    bot.reply_to(message, f"🏆 *Top User:*\n{hasil}", parse_mode="Markdown")

@bot.message_handler(commands=['loglast'])
def show_log_last(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 Hanya admin.")
        return
    try:
        with open("log.txt", "r") as f:
            lines = f.readlines()
            if lines:
                bot.reply_to(message, f"🗂️ Log Terakhir:\n{lines[-1]}")
            else:
                bot.reply_to(message, "📭 Belum ada log.")
    except FileNotFoundError:
        bot.reply_to(message, "📁 File log belum dibuat.")

@bot.message_handler(commands=['lacaknik'])
def lacak_nik(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 Hanya admin.")
        return
    try:
        nik = message.text.split(" ")[1]
        if len(nik) < 6 or not nik[:6].isdigit():
            bot.reply_to(message, "❌ Format NIK tidak valid.")
            return
        kode = nik[:6]
        prov = kode[:2]
        kab = kode[:4]
        bot.reply_to(message, f"📍 Estimasi Wilayah:\nKode: {kode}\nProvinsi: {prov}xxx\nKabupaten: {kab}xx")
    except IndexError:
        bot.reply_to(message, "❗ Gunakan: /lacaknik <NIK>")

@bot.message_handler(commands=['ceknik'])
def cek_nik(message):
    try:
        nik = message.text.split(" ")[1]
        if not validasi_nik(nik):
            bot.reply_to(message, "❌ NIK harus 16 digit angka.")
            return

        result = subprocess.run(['python3', 'nik_parse.py', '-n', nik], capture_output=True, text=True)
        parsed = json.loads(result.stdout)
        if parsed.get("status") != "success":
            bot.reply_to(message, "❌ NIK gagal diproses.")
            return

        data = parsed["data"]
        lokasi = f"{data.get('kotakab', '-')}, {data.get('provinsi', '-')}"
        maps_url = "https://www.google.com/maps/search/" + lokasi.replace(" ", "+")
        tgl_lahir = data.get('lahir', '-')
        umur = hitung_umur(tgl_lahir)
        zodiak = cari_zodiak(tgl_lahir)
        pasaran = cari_pasaran(tgl_lahir)

        output = "\n".join([
            "*✅ Info NIK:*",
            f"NIK: {data.get('nik', '-')}",
            f"Jenis Kelamin: {data.get('kelamin', '-')}",
            f"Tanggal Lahir: {tgl_lahir}",
            f"Umur: {umur} tahun",
            f"Zodiak: {zodiak}",
            f"Pasaran Jawa: {pasaran}",
            f"Provinsi: {data.get('provinsi', '-')}",
            f"Kabupaten: {data.get('kotakab', '-')}",
            f"Kecamatan: {data.get('kecamatan', '-')}"
        ])

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🌐 Google Maps", url=maps_url))
        bot.reply_to(message, output, parse_mode="Markdown", reply_markup=keyboard)

        if data.get("kotakab") in KOORDINAT_DAERAH:
            lat, lon = KOORDINAT_DAERAH[data["kotakab"]]
            bot.send_location(message.chat.id, lat, lon)

        with open("log.txt", "a") as f:
            f.write(f"{datetime.now()} | @{message.from_user.username} | {nik} | {data.get('provinsi')} | {data.get('kotakab')}\n")

        user_counter[message.from_user.username] += 1

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

print("✅ Bot aktif dan polling dimulai...")
bot.infinity_polling()
