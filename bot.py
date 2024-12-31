import os
import subprocess
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon import events
import asyncio
import nest_asyncio

# Menggunakan nest_asyncio untuk menghindari masalah di Railway
nest_asyncio.apply()

# Mengambil API_ID dan API_HASH dari environment variables atau file konfigurasi
API_ID = os.getenv("API_ID", "23615009")  # API ID kamu
API_HASH = os.getenv("API_HASH", "4a7525f3da2136eb61edf0800bf49b75")  # API Hash kamu
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "+62859370813097")  # Nomor Telegram

# Menginisialisasi client Telethon dengan StringSession
client = TelegramClient(StringSession(), API_ID, API_HASH)

# ID grup yang diset melalui perintah Telegram
group_id = None
target_group_id = None

# Fungsi untuk mempercepat video
def speed_up_video(input_path, output_path):
    command = f"ffmpeg -i \"{input_path}\" -vf \"setpts=0.25*PTS\" -filter:a \"atempo=4.0\" -r 30 \"{output_path}\""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Kesalahan saat menjalankan ffmpeg: {result.stderr}")
        raise Exception("FFmpeg gagal mempercepat video.")

    print(f"Video dipercepat disimpan ke: {output_path}")

# Fungsi untuk mengunduh dan memproses video
async def download_and_process_videos():
    global group_id, target_group_id

    if not group_id or not target_group_id:
        print("ID grup sumber atau target belum diatur.")
        return

    async for message in client.iter_messages(group_id):
        if message.video:
            print(f"Mengunduh video dari pesan ID: {message.id}")
            file_path = await message.download_media()
            print(f"Video berhasil diunduh: {file_path}")

            output_path = f"output_{os.path.basename(file_path)}"
            try:
                speed_up_video(file_path, output_path)
            except Exception as e:
                print(f"Terjadi kesalahan saat mempercepat video: {e}")
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
        print(f"Video berhasil diunggah ke grup: {target_group_id}")
    except Exception as e:
        print(f"Terjadi kesalahan saat mengunggah ke grup: {e}")

# Fungsi login ke Telegram
async def login():
    await client.start(phone=PHONE_NUMBER)
    print("Login berhasil!")

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

# Fungsi untuk menjalankan bot
async def run():
    # Login dan menunggu pesan
    await login()

    # Menunggu pesan yang masuk dan memproses video jika ID grup sudah diatur
    print("Bot Telegram siap menerima perintah...")
    while True:
        await download_and_process_videos()

if __name__ == "__main__":
    # Jalankan client Telethon dan mulai menerima perintah dari Telegram
    client.loop.run_until_complete(run())
