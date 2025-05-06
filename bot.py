# bot.py — Telegram-бот для керування товарами
from telegram import Update, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import json, os, subprocess

TOKEN = "8043656898:AAGTfXdIV0s60scs_5WPXwMlnd2RRQvDLQs"
PRODUCTS_FILE = "products.json"

ADD_NAME, ADD_DESC, ADD_PHOTO = range(3)
EDIT_NAME, EDIT_DESC = range(2)

# Завантаження товарів
def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Збереження товарів
def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

# Генерація сайту
def generate_site():
    subprocess.run(["python3", "generate_site.py"])

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привіт! Надішли /add, щоб додати товар, /list — переглянути.")

# Команда /add — старт додавання
def add_start(update: Update, context: CallbackContext):
    update.message.reply_text("Введи назву товару:")
    return ADD_NAME

def add_name(update: Update, context: CallbackContext):
    context.user_data["name"] = update.message.text
    update.message.reply_text("Опис товару:")
    return ADD_DESC

def add_desc(update: Update, context: CallbackContext):
    context.user_data["desc"] = update.message.text
    update.message.reply_text("Надішли фото товару:")
    return ADD_PHOTO

def add_photo(update: Update, context: CallbackContext):
    photo_file = update.message.photo[-1].get_file()
    file_path = f"images/{photo_file.file_id}.jpg"
    os.makedirs("images", exist_ok=True)
    photo_file.download(file_path)

    products = load_products()
    products.append({
        "id": len(products) + 1,
        "name": context.user_data["name"],
        "desc": context.user_data["desc"],
        "image": file_path
    })
    save_products(products)
    generate_site()
    update.message.reply_text("✅ Товар додано!")
    return ConversationHandler.END

def list_products(update: Update, context: CallbackContext):
    products = load_products()
    if not products:
        update.message.reply_text("Список порожній")
        return
    for product in products:
        with open(product["image"], "rb") as photo:
            update.message.reply_photo(photo=photo, caption=f"ID: {product['id']}\n{product['name']}\n{product['desc']}")

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Скасовано")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_NAME: [MessageHandler(Filters.text & ~Filters.command, add_name)],
            ADD_DESC: [MessageHandler(Filters.text & ~Filters.command, add_desc)],
            ADD_PHOTO: [MessageHandler(Filters.photo, add_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("list", list_products))
    dp.add_handler(add_conv)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

