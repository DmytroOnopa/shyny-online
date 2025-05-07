import os
import json
import logging
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from telegram import Update, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters,
                          ConversationHandler, CallbackQueryHandler, ContextTypes)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

PRODUCTS_FILE = "products.json"
IMAGES_DIR = "images"

logging.basicConfig(level=logging.INFO)

# Станови для ConversationHandler
NAME, DESCRIPTION, PHOTO = range(3)
EDIT_CHOOSE, EDIT_NAME, EDIT_DESCRIPTION, EDIT_PHOTO = range(3, 7)
DELETE_CHOOSE = 7

# Завантаження/збереження продуктів
def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

# Генерація сайту
def generate_site():
    print("🔄 Генеруємо сайт...")
    subprocess.run(["python3", "generate_site.py"])

# Додавання товару
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Введи назву товару:")
    return NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введи опис товару:")
    return DESCRIPTION

async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Надішли фото товару:")
    return PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    image_id = str(uuid4()) + ".jpg"
    image_path = os.path.join(IMAGES_DIR, image_id)
    await photo_file.download_to_drive(image_path)

    products = load_products()
    products.append({
        "id": str(uuid4()),
        "name": context.user_data["name"],
        "description": context.user_data["description"],
        "image": os.path.join(IMAGES_DIR, image_id)
    })
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Товар додано!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Скасовано")
    return ConversationHandler.END

# Список товарів
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    products = load_products()
    for p in products:
        try:
            await update.message.reply_photo(
                photo=open(p["image"], "rb"),
                caption=f"{p['name']}\n{p['description']}\nID: {p['id']}"
            )
        except Exception as e:
            logging.error(f"Помилка при надсиланні фото: {e}")

# Видалення товару
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=p["id"])] for p in products]
    await update.message.reply_text("Оберіть товар для видалення:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DELETE_CHOOSE

async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = query.data

    products = load_products()
    updated = [p for p in products if p["id"] != product_id]
    save_products(updated)
    generate_site()
    await query.edit_message_text("🗑️ Товар видалено.")
    return ConversationHandler.END

# Редагування товару
async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=p["id"])] for p in products]
    await update.message.reply_text("Оберіть товар для редагування:", reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_CHOOSE

async def edit_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = query.data
    context.user_data["edit_id"] = product_id
    await query.edit_message_text("Що змінити?", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Назву", callback_data="name")],
        [InlineKeyboardButton("Опис", callback_data="description")],
        [InlineKeyboardButton("Фото", callback_data="photo")],
    ]))
    return EDIT_NAME

async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data["edit_field"] = choice

    if choice == "name":
        await query.edit_message_text("Введи нову назву:")
        return EDIT_NAME
    elif choice == "description":
        await query.edit_message_text("Введи новий опис:")
        return EDIT_DESCRIPTION
    elif choice == "photo":
        await query.edit_message_text("Надішли нове фото:")
        return EDIT_PHOTO

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    products = load_products()
    for p in products:
        if p["id"] == context.user_data["edit_id"]:
            p["name"] = new_value
            break
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Назву оновлено.")
    return ConversationHandler.END

async def edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    products = load_products()
    for p in products:
        if p["id"] == context.user_data["edit_id"]:
            p["description"] = new_value
            break
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Опис оновлено.")
    return ConversationHandler.END

async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    image_id = str(uuid4()) + ".jpg"
    image_path = os.path.join(IMAGES_DIR, image_id)
    await photo_file.download_to_drive(image_path)

    products = load_products()
    for p in products:
        if p["id"] == context.user_data["edit_id"]:
            p["image"] = os.path.join(IMAGES_DIR, image_id)
            break
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Фото оновлено.")
    return ConversationHandler.END

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Привіт, адміне! Скористайся /add, /list, /edit або /delete")
    else:
        await update.message.reply_text("⛔ У тебе немає доступу.")

if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    delete_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            DELETE_CHOOSE: [CallbackQueryHandler(delete_product)]
        },
        fallbacks=[]
    )

    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_start)],
        states={
            EDIT_CHOOSE: [CallbackQueryHandler(edit_choose)],
            EDIT_NAME: [CallbackQueryHandler(edit_choice), MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
            EDIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_description)],
            EDIT_PHOTO: [MessageHandler(filters.PHOTO, edit_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_products))
    app.add_handler(add_conv)
    app.add_handler(delete_conv)
    app.add_handler(edit_conv)

    app.run_polling()

