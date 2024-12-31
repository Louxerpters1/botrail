import os
import subprocess
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import nest_asyncio
from datetime import datetime, timedelta
import logging

# Menggunakan nest_asyncio untuk menghindari masalah di Railway atau di lingkungan non-interaktif
nest_asyncio.apply()

# Mengambil API_ID dan API_HASH dari environment variables atau file konfigurasi
API_ID = "23615009"  # API ID kamu
API_HASH = "4a7525f3da2136eb61edf0800bf49b75"  # API Hash kamu
PHONE_NUMBER = "+62859370813097"  # Nomor Telegram

# Cek jika session string sudah ada
SESSION_STRING = os.getenv("SESSION_STRING", None)  # Anda bisa menetapkan session string jika ada

# Menginisialisasi client Telethon dengan StringSession atau default session
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ID grup yang diset melalui perintah Telegram
group_id = None
target_group_id = None

# Menyiapkan logger untuk mencatat proses
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Fungsi untuk mempercepat video dengan opsi kecepatan dinamis
def speed_up_video(input_path, output_path, speed=4.0):
    try:
        # Menggunakan ffmpeg untuk mempercepat video dengan parameter dinamis
        command = f"ffmpeg -i \"{input_path}\" -vf \"setpts=0.25*PTS\" -filter:a \"atempo={speed}\" -r 30 \"{output_path}\""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Kesalahan saat menjalankan ffmpeg: {result.stderr}")
            raise Exception("FFmpeg gagal mempercepat video.")
        logger.info(f"Video dipercepat dan disimpan ke: {output_path}")
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat mempercepat video: {e}")
        raise

# Fungsi untuk mengunduh dan memproses video berdasarkan kata kunci
async def download_and_process_videos():
    global group_id, target_group_id

    if not group_id or not target_group_id:
        logger.warning("ID grup sumber atau target belum diatur.")
        return

    async for message in client.iter_messages(group_id):
        # Memproses video hanya jika ada
        if message.video:
            logger.debug(f"Memeriksa pesan ID: {message.id}")
            # Jika video diterima dalam 24 jam terakhir
            if datetime.now() - message.date < timedelta(days=1):
                logger.info(f"Mengunduh video dari pesan ID: {message.id}")
                file_path = await message.download_media()
                logger.info(f"Video berhasil diunduh: {file_path}")

                output_path = f"output_{os.path.basename(file_path)}"
                try:
                    speed_up_video(file_path, output_path, speed=4.0)  # Mempercepat video dengan kecepatan default 4x
                except Exception as e:
                    logger.error(f"Terjadi kesalahan saat mempercepat video: {e}")
                    continue

                # Mengunggah video ke grup target
                await upload_to_target_group(output_path)

                # Menghapus file lokal setelah selesai
                os.remove(file_path)
                if os.path.exists(output_path):
                    os.remove(output_path)

# Fungsi untuk mengunggah video ke grup target
async def upload_to_target_group(file_path):
    global target_group_id
    try:
        await client.send_file(target_group_id, file_path)
        logger.info(f"Video berhasil diunggah ke grup: {target_group_id}")
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat mengunggah ke grup: {e}")

# Fungsi login ke Telegram
async def login():
    if SESSION_STRING:
        # Jika sudah ada session, login tanpa perlu autentikasi ulang
        try:
            await client.start()
            logger.info("Login berhasil dengan session string!")
        except Exception as e:
            logger.error(f"Kesalahan saat login dengan session string: {e}")
            # Re-authenticate in case of session issues
            await client.disconnect()
            await client.start(phone=PHONE_NUMBER)
            logger.info("Login berhasil dengan nomor telepon setelah sesi tidak valid!")
    else:
        # Jika belum ada session, autentikasi menggunakan nomor telepon
        try:
            await client.start(phone=PHONE_NUMBER)
            logger.info("Login berhasil dengan nomor telepon!")
        except Exception as e:
            logger.error(f"Kesalahan saat login dengan nomor telepon: {e}")
            raise

# Event handler untuk menerima perintah dari Telegram
@client.on(events.NewMessage(pattern='/setgroup'))
async def set_group_id(event):
    global group_id
    try:
        group_id = int(event.raw_text.split()[1])  # Mengambil ID grup dari perintah
        await event.respond(f"ID grup sumber berhasil diubah menjadi: {group_id}")
    except (IndexError, ValueError):
        await event.respond("Harap masukkan ID grup sumber yang valid.")

@client.on(events.NewMessage(pattern='/settarget'))
async def set_target_group_id(event):
    global target_group_id
    try:
        target_group_id = int(event.raw_text.split()[1])  # Mengambil ID grup target dari perintah
        await event.respond(f"ID grup target berhasil diubah menjadi: {target_group_id}")
    except (IndexError, ValueError):
        await event.respond("Harap masukkan ID grup target yang valid.")

# Fungsi untuk memproses perintah lainnya seperti pencarian video berdasar kata kunci
@client.on(events.NewMessage(pattern='/process_keyword'))
async def process_keyword(event):
    keyword = event.raw_text.split(' ', 1)[1] if len(event.raw_text.split()) > 1 else ''
    if keyword:
        await search_and_process_videos(keyword)
    else:
        await event.respond("Harap masukkan kata kunci yang valid.")

# Fungsi untuk mencari video berdasarkan kata kunci di deskripsi pesan
async def search_and_process_videos(keyword):
    global group_id
    if not group_id:
        logger.warning("ID grup sumber belum diatur.")
        return

    async for message in client.iter_messages(group_id):
        if message.video and keyword.lower() in (message.text or '').lower():
            logger.info(f"Video ditemukan dengan kata kunci '{keyword}' di pesan ID: {message.id}")
            file_path = await message.download_media()
            logger.info(f"Video berhasil diunduh: {file_path}")

            output_path = f"output_{os.path.basename(file_path)}"
            try:
                speed_up_video(file_path, output_path, speed=4.0)
            except Exception as e:
                logger.error(f"Terjadi kesalahan saat mempercepat video: {e}")
                continue

            # Mengunggah video ke grup target
            await upload_to_target_group(output_path)

            # Menghapus file lokal setelah selesai
            os.remove(file_path)
            if os.path.exists(output_path):
                os.remove(output_path)

# Fungsi untuk menjalankan bot
async def run():
    # Login dan menunggu pesan
    await login()

    # Menunggu pesan yang masuk dan memproses video jika ID grup sudah diatur
    logger.info("Bot Telegram siap menerima perintah...")
    while True:
        await download_and_process_videos()

if __name__ == "__main__":
    # Jalankan client Telethon dan mulai menerima perintah dari Telegram
    client.loop.run_until_complete(run())
