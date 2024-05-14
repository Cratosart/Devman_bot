import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
import requests
import pprint
from dotenv import load_dotenv

API_KEY = None
DEVMAN_TOKEN = None
user_chat_ids = {}
confirmed_chat_ids = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_ids[update.effective_user.username] = update.effective_chat.id
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привет! Отправь /confirm для подтверждения получения уведомлений."
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if username in user_chat_ids:
        chat_id = user_chat_ids[username]
        confirmed_chat_ids[username] = chat_id
        await context.bot.send_message(
            chat_id=chat_id,
            text="Твой chat ID подтверждён! Теперь ты будешь получать уведомления о проверках."
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала используй команду /start."
        )

async def dvmn_long_polling(context: CallbackContext):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {DEVMAN_TOKEN}'}
    timestamp = None

    while True:
        for username, chat_id in confirmed_chat_ids.items():
            try:
                params = {'timestamp': timestamp} if timestamp else {}
                response = requests.get(url, headers=headers, params=params, timeout=90)
                response_data = response.json()

                if response_data['status'] == 'found':
                    for attempt in response_data['new_attempts']:
                        lesson_title = attempt['lesson_title']
                        lesson_url = attempt.get('lesson_url', '#')
                        result_text = 'требуются доработки' if attempt['is_negative'] else 'успешно принят'
                        message = (
                            f"Урок '{lesson_title}' проверен: {result_text}! "
                            f"[Подробнее]({lesson_url})"
                        )
                        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                        timestamp = attempt['timestamp']

                elif response_data['status'] == 'timeout':
                    timestamp = response_data['timestamp_to_request']

            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {str(e)}")

def setup():
    global API_KEY, DEVMAN_TOKEN
    load_dotenv()
    API_KEY = os.getenv('TELEGRAM_TOKEN')
    DEVMAN_TOKEN = os.getenv('DEVMAN_TOKEN')

def main():
    setup()
    app = Application.builder().token(API_KEY).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.run_polling()

if __name__ == '__main__':
    main()
