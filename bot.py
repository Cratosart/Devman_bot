from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, MessageHandler, filters
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('TELEGRAM_TOKEN')
DEVMAN_TOKEN = os.getenv('DEVMAN_TOKEN')

app = Application.builder().token(API_KEY).build()

user_chat_ids = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Используй команду /setchatid для установки твоего chat ID.")

async def set_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_ids[update.effective_user.username] = update.effective_chat.id
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Твой chat ID успешно сохранён!")

async def dvmn_long_polling(context: CallbackContext):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {DEVMAN_TOKEN}'}
    timestamp = None

    while True:
        for username, chat_id in user_chat_ids.items():
            try:
                params = {'timestamp': timestamp} if timestamp else {}
                response = requests.get(url, headers=headers, params=params, timeout=90)
                response_json = response.json()

                if response_json['status'] == 'found':
                    for attempt in response_json['new_attempts']:
                        lesson_title = attempt['lesson_title']
                        lesson_url = attempt.get('lesson_url', '#')
                        message = f"Урок '{lesson_title}' проверен: {'требуются доработки' if attempt['is_negative'] else 'успешно принят'}! [Подробнее]({lesson_url})"
                        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                        timestamp = attempt['timestamp']

                elif response_json['status'] == 'timeout':
                    timestamp = response_json['timestamp_to_request']

            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text=f"Превышено время ожидания ответа, направляю новый звпрос: {str(e)}")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setchatid", set_chat_id))

def main():
    app.run_polling()

if __name__ == '__main__':
    main()
