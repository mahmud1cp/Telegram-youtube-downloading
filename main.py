import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import yt_dlp

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube download options
ydl_opts_video = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
}

ydl_opts_audio = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
}

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please provide a YouTube link to download the video or audio.')

# Function to ask whether to download video or audio
def ask_download_type(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Video", callback_data='video'),
            InlineKeyboardButton("Audio", callback_data='audio'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please select whether to download video or audio:', reply_markup=reply_markup)

# Handle the download type choice
def download_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.user_data['choice'] = query.data
    query.edit_message_text(text=f"Selected option: {query.data.capitalize()}")

    # Proceed with downloading
    download_video_audio(query, context)

# Function to download video or audio
def download_video_audio(update: Update, context: CallbackContext) -> None:
    choice = context.user_data.get('choice', 'video')
    url = context.user_data.get('url', '')
    
    update.message.reply_text('Downloading...')

    ydl_opts = ydl_opts_video if choice == 'video' else ydl_opts_audio

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            
            if choice == 'video' and info_dict['filesize_approx'] > 50 * 1024 * 1024:
                update.message.reply_text('The file is too large to send through Telegram. You can download it from the following link:')
                context.bot.send_message(chat_id=update.effective_chat.id, text=file_path)
            else:
                context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, 'rb'))
            
            update.message.reply_text('Download complete!')
    except Exception as e:
        update.message.reply_text(f'Error: {e}')

# Handle YouTube link input
def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    context.user_data['url'] = url
    ask_download_type(update, context)

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    update.message.reply_text(f'An error occurred: {context.error}')

# Main function to run the bot
def main() -> None:
    # Get the bot token from the environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(download_choice))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
