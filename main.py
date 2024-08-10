import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube download options
ydl_opts_video = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',  # Download the best video and audio quality
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,  # Do not download playlists
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Function to start the bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please provide a YouTube link to download the video.')

# Function to handle messages with YouTube links
def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    update.message.reply_text('Downloading...')

    try:
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)

            if os.path.getsize(video_file) > MAX_FILE_SIZE:
                update.message.reply_text("File size exceeds the limit.")
            else:
                with open(video_file, 'rb') as file:
                    context.bot.send_video(chat_id=update.message.chat_id, video=file)
                update.message.reply_text('Download complete!')
    except Exception as e:
        update.message.reply_text(f'Error: {e}')

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    update.message.reply_text(f'An error occurred: {context.error}')

# Main function to run the bot
def main() -> None:
    token = "YOUR_TELEGRAM_BOT_TOKEN"  # Insert your Telegram bot token here

    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
