import os
import json
import logging
import subprocess
import datetime
from uuid import uuid4
from dotenv import load_dotenv
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Constants for conversation states
NAME, DESCRIPTION, PHOTO = range(3)

# File paths
PRODUCTS_FILE = "products.json"
IMAGES_DIR = "images"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_products(products):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def generate_site():
    subprocess.run(["python3", "generate_site.py"])
    push_images_to_github()

def push_images_to_github():
    try:
        subprocess.run(["git", "add", "images/"], check=True)
        subprocess.run(["git", "commit", "-m", f"🖼️ Додано фото {datetime.datetime.now()}"])
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Git push failed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Привіт! Це адмін-бот для керування товарами.")

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    products = load_products()
    if not products:
        await update.message.reply_text("Список товарів порожній.")
        return
    for product in products:
        caption = f"{product['name']}\n{product['description']}"
        image_path = os.path.join(IMAGES_DIR, product['photo'])
        if os.path.exists(image_path):
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(image_path), caption=caption)
        else:
            await update.message.reply_text(caption)

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Введіть назву товару:")
    return NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введіть опис товару:")
    return DESCRIPTION

async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Надішліть фото товару:")
    return PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_ext = '.jpg'
    filename = f"{uuid4().hex}{file_ext}"
    path = os.path.join(IMAGES_DIR, filename)
    await file.download_to_drive(path)

    products = load_products()
    new_product = {
        "id": uuid4().hex,
        "name": context.user_data['name'],
        "description": context.user_data['description'],
        "photo": filename
    }
    products.append(new_product)
    save_products(products)
    generate_site()

    await update.message.reply_text("✅ Товар додано!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дію скасовано.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_products))

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_product)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(add_conv)

    app.run_polling()

if __name__ == '__main__':
    main()

