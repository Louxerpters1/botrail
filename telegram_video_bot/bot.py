import os
import subprocess
import logging
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import InputMessagesFilterVideo
import shutil
import time
from tempfile import NamedTemporaryFile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Konfigurasi Bot Telegram
API_ID = '23615009'  # Ganti dengan API ID Anda
API_HASH = '4a7525f3da2136eb61edf0800bf49b75'  # Ganti dengan API Hash Anda
BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Ganti dengan Token Bot dari BotFather
GROUP_ID = 'TARGET_GROUP_ID'  # Ganti dengan ID grup target

client = TelegramClient('session_name', API_ID, API_HASH)

async def download_video_from_message(message):
    """Mengunduh video dari pesan yang diterima"""
    logger.info(f"Video diterima, ID pesan: {message.id}")
    video_path = await message.download_media()
    logger.info(f"Video berhasil diunduh ke path: {video_path}")
    return video_path

def speed_up_video(input_path, output_path):
    """Fungsi untuk mempercepat video dengan ffmpeg"""
    logger.info(f"Mempercepat video: {input_path}")
    command = f"ffmpeg -i \"{input_path}\" -vf \"setpts=0.25*PTS\" -filter:a \"atempo=4.0\" -r 30 \"{output_path}\""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Kesalahan saat mempercepat video: {result.stderr}")
        raise Exception(f"FFmpeg error: {result.stderr}")
    logger.info(f"Video dipercepat disimpan di: {output_path}")

async def send_processed_video_to_user(user_id, file_path):
    """Mengirimkan video yang telah diproses ke pengguna"""
    logger.info(f"Mengirim video ke user {user_id}")
    await client.send_file(user_id, file_path)
    logger.info(f"Video berhasil dikirim ke {user_id}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Menangani perintah /start untuk bot"""
    await event.reply("Selamat datang! Kirimkan video untuk diproses.")

@client.on(events.NewMessage(func=lambda e: e.video))
async def handle_video(event):
    """Menangani video yang diterima dari pengguna"""
    user_id = event.sender_id
    video_path = await download_video_from_message(event.message)

    try:
        # Mempercepat video
        output_path = os.path.join("processed_videos", f"processed_{int(time.time())}.mp4")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        speed_up_video(video_path, output_path)

        # Mengirim kembali video yang sudah diproses
        await send_processed_video_to_user(user_id, output_path)
    except Exception as e:
        logger.error(f"Gagal memproses video: {e}")
        await event.reply("Terjadi kesalahan saat memproses video, coba lagi nanti.")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)

async def main():
    # Mulai client Telegram
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Bot berjalan...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
