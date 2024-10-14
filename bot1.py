from flask import Flask, request, jsonify
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext

# Настройки бота
BOT_TOKEN = '7209206884:AAGaE-wI3DyrIPgfkL7MTEHf1ENyJr_-EJI'
ADMIN_USER_ID = '33182944'  # ID администратора

# Инициализация Flask приложения
app = Flask(__name__)

# Инициализация бота
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения пользователей по NETWORK_KEY
network_users = {}

# Команда для регистрации пользователя
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    network_key = update.message.text.split()[1] if len(update.message.text.split()) > 1 else None

    if network_key:
        if network_key not in network_users:
            network_users[network_key] = []
        if user_id not in network_users[network_key]:
            network_users[network_key].append(user_id)
            await update.message.reply_text(f'Вы успешно зарегистрированы для NETWORK_KEY: {network_key}')
            logger.info(f'User {user_id} registered for NETWORK_KEY: {network_key}')
        else:
            await update.message.reply_text(f'Вы уже зарегистрированы для NETWORK_KEY: {network_key}')
    else:
        await update.message.reply_text('Пожалуйста, укажите NETWORK_KEY после команды /start')

# Команда для отмены регистрации пользователя
async def unregister(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    network_key = update.message.text.split()[1] if len(update.message.text.split()) > 1 else None

    if network_key and network_key in network_users:
        if user_id in network_users[network_key]:
            network_users[network_key].remove(user_id)
            await update.message.reply_text(f'Вы успешно отменили регистрацию для NETWORK_KEY: {network_key}')
            logger.info(f'User {user_id} unregistered for NETWORK_KEY: {network_key}')
        else:
            await update.message.reply_text(f'Вы не зарегистрированы для NETWORK_KEY: {network_key}')
    else:
        await update.message.reply_text('Пожалуйста, укажите NETWORK_KEY после команды /unregister')

# Команда для просмотра зарегистрированных пользователей
async def list_users(update: Update, context: CallbackContext) -> None:
    network_key = update.message.text.split()[1] if len(update.message.text.split()) > 1 else None

    if network_key and network_key in network_users:
        users = network_users[network_key]
        if users:
            user_list = "\n".join([str(user) for user in users])
            await update.message.reply_text(f'Зарегистрированные пользователи для NETWORK_KEY {network_key}:\n{user_list}')
        else:
            await update.message.reply_text(f'Нет зарегистрированных пользователей для NETWORK_KEY: {network_key}')
    else:
        await update.message.reply_text('Пожалуйста, укажите NETWORK_KEY после команды /list_users')

# Команда для администратора: просмотр всех зарегистрированных пользователей
async def admin_list_users(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == int(ADMIN_USER_ID):
        all_users = []
        for network_key, users in network_users.items():
            all_users.extend(users)
        if all_users:
            user_list = "\n".join([str(user) for user in all_users])
            await update.message.reply_text(f'Все зарегистрированные пользователи:\n{user_list}')
        else:
            await update.message.reply_text('Нет зарегистрированных пользователей')
    else:
        await update.message.reply_text('У вас нет прав для выполнения этой команды')

# Команда для администратора: отправка глобального сообщения всем пользователям
async def admin_send_global_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == int(ADMIN_USER_ID):
        message = ' '.join(context.args)
        if message:
            all_users = []
            for network_key, users in network_users.items():
                all_users.extend(users)
            for user_id in all_users:
                try:
                    await application.bot.send_message(chat_id=user_id, text=message, parse_mode='MarkdownV2')
                    logger.info(f'Global message sent to user {user_id}')
                except Exception as e:
                    logger.error(f'Failed to send global message to user {user_id}: {e}')
            await update.message.reply_text('Глобальное сообщение отправлено всем пользователям')
        else:
            await update.message.reply_text('Пожалуйста, укажите текст сообщения после команды /admin_send_global_message')
    else:
        await update.message.reply_text('У вас нет прав для выполнения этой команды')

# Обработчик для приема сообщений от скрипта
@app.route('/send_message', methods=['POST'])
async def send_message():
    data = request.json
    network_key = data.get('network_key')
    message = data.get('text')

    if network_key and message:
        if network_key in network_users:
            for user_id in network_users[network_key]:
                try:
                    await application.bot.send_message(chat_id=user_id, text=message, parse_mode='MarkdownV2')
                    logger.info(f'Message sent to user {user_id} for NETWORK_KEY: {network_key}')
                except Exception as e:
                    logger.error(f'Failed to send message to user {user_id}: {e}')
            return jsonify({"status": "success", "message": "Сообщения отправлены"})
        else:
            logger.warning(f'NETWORK_KEY {network_key} not found')
            return jsonify({"status": "error", "message": "NETWORK_KEY не найден"})
    else:
        logger.error('Invalid data format')
        return jsonify({"status": "error", "message": "Неверный формат данных"})

# Регистрация обработчиков
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("unregister", unregister))
application.add_handler(CommandHandler("list_users", list_users))
application.add_handler(CommandHandler("admin_list_users", admin_list_users))
application.add_handler(CommandHandler("admin_send_global_message", admin_send_global_message))

# Запуск бота и веб-сервера
if __name__ == '__main__':
    application.run_polling()
    app.run(host='0.0.0.0', port=5000)