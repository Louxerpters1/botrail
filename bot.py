from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Telegram API Credentials
API_ID = '23615009'  # Ganti dengan API ID Anda
API_HASH = '4a7525f3da2136eb61edf0800bf49b75'  # Ganti dengan API Hash Anda
PHONE_NUMBER = '+62859370813097'  # Nomor Telegram Anda

# Inisialisasi Client dengan StringSession (untuk Telethon)
client = TelegramClient(StringSession(), API_ID, API_HASH)

# Telegram Bot untuk mengatur perintah
updater = Updater("YOUR_BOT_API_KEY", use_context=True)
dispatcher = updater.dispatcher

# Variabel global untuk menyimpan ID grup
group_id = None
target_group_id = None

# Fungsi untuk mengubah ID Grup Sumber
def set_group_id(update: Update, context: CallbackContext):
    global group_id
    try:
        group_id = int(context.args[0])
        update.message.reply_text(f"ID grup sumber berhasil diubah menjadi: {group_id}")
    except (IndexError, ValueError):
        update.message.reply_text("Harap masukkan ID grup sumber yang valid.")

# Fungsi untuk mengubah ID Grup Target
def set_target_group_id(update: Update, context: CallbackContext):
    global target_group_id
    try:
        target_group_id = int(context.args[0])
        update.message.reply_text(f"ID grup target berhasil diubah menjadi: {target_group_id}")
    except (IndexError, ValueError):
        update.message.reply_text("Harap masukkan ID grup target yang valid.")

# Fungsi untuk mempercepat video
def speed_up_video(input_path, output_path):
    command = f"ffmpeg -i \"{input_path}\" -vf \"setpts=0.25*PTS\" -filter:a \"atempo=4.0\" -r 30 \"{output_path}\""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Kesalahan saat menjalankan ffmpeg: {result.stderr}")
        raise Exception("FFmpeg gagal mempercepat video.")

    print(f"Video dipercepat disimpan ke: {output_path}")

# Fungsi untuk mengunduh dan memproses video
async def download_and_process_videos(group_id, target_group_id):
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

            await upload_to_target_group(output_path, target_group_id)

            os.remove(file_path)
            if os.path.exists(output_path):
                os.remove(output_path)

# Fungsi untuk mengunggah video ke grup target
async def upload_to_target_group(file_path, target_group_id):
    try:
        await client.send_file(target_group_id, file_path)
        print(f"Video berhasil diunggah ke grup: {target_group_id}")
    except Exception as e:
        print(f"Terjadi kesalahan saat mengunggah ke grup: {e}")

# Fungsi untuk login
async def login():
    await client.start(phone=PHONE_NUMBER)
    print("Login berhasil!")

# Fungsi utama untuk menjalankan bot Telegram
async def run():
    async with client:
        await login()

        print("Menunggu perintah dari Telegram...")

# Menjalankan bot Telegram
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bot sudah aktif! Anda dapat mengatur ID grup dengan perintah /setgroup <ID> atau /settarget <ID>.")

# Fungsi untuk menjalankan bot Telegram
def main():
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("setgroup", set_group_id))
    dispatcher.add_handler(CommandHandler("settarget", set_target_group_id))

    updater.start_polling()

# Fungsi untuk menjalankan semua proses secara bersamaan
if __name__ == "__main__":
    import asyncio
    # Menjalankan bot Telegram dan client Telethon bersamaan
    loop = asyncio.get_event_loop()
    loop.create_task(run())
    main()
