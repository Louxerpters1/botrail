import os
import subprocess
import logging
import time
from tempfile import NamedTemporaryFile
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, PicklePersistence

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Konfigurasi Bot Telegram
API_TOKEN = '7679765494:AAE4zbz8cSGLjuwyX_Xbm05bOwn0r1BRqOo'  # Ganti dengan Token Bot dari BotFather

# Setup bot dan updater
updater = Updater(API_TOKEN, use_context=True, persistence=PicklePersistence('bot_data'))
dispatcher = updater.dispatcher
job_queue = updater.job_queue

# Menggunakan penyimpanan untuk menyimpan grup sumber dan target
persistence = updater.persistence

# Fungsi untuk mempercepat video menggunakan ffmpeg
def speed_up_video(input_path, output_path):
    """Mempercepat video dengan ffmpeg"""
    logger.info(f"Mempercepat video: {input_path}")
    command = f"ffmpeg -i \"{input_path}\" -vf \"setpts=0.25*PTS\" -filter:a \"atempo=4.0\" -r 30 \"{output_path}\""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Kesalahan saat mempercepat video: {result.stderr}")
        raise Exception(f"FFmpeg error: {result.stderr}")
    logger.info(f"Video dipercepat disimpan di: {output_path}")

# Fungsi untuk menangani pesan yang masuk dari grup
def handle_video(update: Update, context: CallbackContext):
    """Menangani video yang diterima dari grup"""
    # Mengecek apakah pesan memiliki video
    if update.message.video:
        video_file = update.message.video
        video_path = download_video(video_file)

        # Menyimpan video yang telah diproses
        try:
            output_path = os.path.join("processed_videos", f"processed_{int(time.time())}.mp4")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Mengirim pesan pengolahan video
            update.message.reply_text("Proses video sedang berjalan...")

            # Mempercepat video
            speed_up_video(video_path, output_path)

            # Mengirim video yang sudah diproses ke grup target
            group_target = persistence.get_data()["group_target"]
            if group_target:
                bot.send_video(group_target, video=open(output_path, 'rb'))

            # Mengirimkan notifikasi ke grup
            bot.send_message(group_target, "Video telah diproses dan dikirimkan!")

        except Exception as e:
            logger.error(f"Gagal memproses video: {e}")
            update.message.reply_text("Terjadi kesalahan saat memproses video, coba lagi nanti.")
        
        finally:
            # Hapus video sementara setelah selesai
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(output_path):
                os.remove(output_path)

# Fungsi untuk mendownload video
def download_video(video):
    """Men-download video dari Telegram"""
    file_path = video.get_file().download()
    logger.info(f"Video berhasil diunduh ke path: {file_path}")
    return file_path

# Fungsi untuk mengatur grup sumber
def set_source(update: Update, context: CallbackContext):
    """Set grup sumber dari perintah /setsource"""
    persistence_data = persistence.get_data()
    persistence_data["group_source"] = update.message.chat.id
    persistence.update_data(persistence_data)
    update.message.reply_text(f"Grup sumber diatur ke: {update.message.chat.title} (ID: {update.message.chat.id})")

# Fungsi untuk mengatur grup target
def set_target(update: Update, context: CallbackContext):
    """Set grup target dari perintah /settarget"""
    persistence_data = persistence.get_data()
    persistence_data["group_target"] = update.message.chat.id
    persistence.update_data(persistence_data)
    update.message.reply_text(f"Grup target diatur ke: {update.message.chat.title} (ID: {update.message.chat.id})")

# Fungsi untuk menangani perintah /start
def start(update: Update, context: CallbackContext):
    """Menangani perintah /start untuk bot"""
    update.message.reply_text("Selamat datang! Kirimkan video untuk diproses atau gunakan perintah /setsource dan /settarget untuk mengatur grup sumber dan target.")

# Menambahkan handler untuk perintah /start
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# Menambahkan handler untuk perintah /setsource
set_source_handler = CommandHandler('setsource', set_source)
dispatcher.add_handler(set_source_handler)

# Menambahkan handler untuk perintah /settarget
set_target_handler = CommandHandler('settarget', set_target)
dispatcher.add_handler(set_target_handler)

# Menambahkan handler untuk pesan video
video_handler = MessageHandler(Filters.video, handle_video)
dispatcher.add_handler(video_handler)

# Mulai bot
if __name__ == '__main__':
    updater.start_polling()
    logger.info("Bot Telegram berjalan...")
    updater.idle()
