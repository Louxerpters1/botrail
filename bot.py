# Instalasi dependensi yang diperlukan
pip install telethon requests tqdm nest_asyncio

import nest_asyncio
nest_asyncio.apply()

from telethon.sessions import StringSession
from telethon import TelegramClient
import requests
import os
import asyncio
from tqdm import tqdm
import subprocess  # Untuk menjalankan ffmpeg dan menangkap output

# Konfigurasi Telegram API
API_ID = '23615009'   # Ganti dengan API ID Anda
API_HASH = '4a7525f3da2136eb61edf0800bf49b75'  # Ganti dengan API Hash Anda
PHONE_NUMBER = '+62859370813097'  # Nomor Telegram Anda

# Inisialisasi Client dengan StringSession
client = TelegramClient(StringSession(), API_ID, API_HASH)

# Fungsi Login
async def login():
    await client.start(phone=PHONE_NUMBER)
    print("Login berhasil!")

# Fungsi untuk Mengunduh dan Memproses Video Satu per Satu
async def download_and_process_videos(group_id, target_group_id):
    async for message in client.iter_messages(group_id):
        if message.video:
            print(f"Mengunduh video dari pesan ID: {message.id}")
            file_path = await message.download_media()
            print(f"Video berhasil diunduh: {file_path}")

            # Mempercepat Video
            output_path = f"output_{os.path.basename(file_path)}"
            try:
                speed_up_video(file_path, output_path)
            except Exception as e:
                print(f"Terjadi kesalahan saat mempercepat video: {e}")
                continue  # Lewati ke video berikutnya jika terjadi kesalahan

            # Unggah ke grup Telegram target
            await upload_to_target_group(output_path, target_group_id)

            # Hapus file lokal setelah selesai
            os.remove(file_path)
            if os.path.exists(output_path):
                os.remove(output_path)

# Fungsi untuk Mempercepat Video 4X dengan Audio
def speed_up_video(input_path, output_path):
    # Mengutip nama file untuk menghindari masalah dengan karakter khusus
    command = f"ffmpeg -i \"{input_path}\" -vf \"setpts=0.25*PTS\" -filter:a \"atempo=4.0\" -r 30 \"{output_path}\""
    print(f"Menjalankan perintah: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Kesalahan saat menjalankan ffmpeg: {result.stderr}")
        raise Exception("FFmpeg gagal mempercepat video.")

    print(f"Video dipercepat disimpan ke: {output_path}")

# Fungsi untuk Mengunggah ke Grup Telegram Target
async def upload_to_target_group(file_path, target_group_id):
    try:
        await client.send_file(target_group_id, file_path)
        print(f"Video berhasil diunggah ke grup: {target_group_id}")
    except Exception as e:
        print(f"Terjadi kesalahan saat mengunggah ke grup: {e}")

# Fungsi Utama
async def main():
    # Login ke Telegram
    await login()

    # ID Grup Sumber
    group_id = int(input("Masukkan ID Grup Sumber: "))
    # ID Grup Target
    target_group_id = int(input("Masukkan ID Grup Target: "))

    # Unduh dan Proses Video Satu per Satu
    await download_and_process_videos(group_id, target_group_id)

    print("Proses selesai.")

# Menjalankan Client dengan async with
async def run():
    async with client:
        await main()

# Jalankan Fungsi
await run()
