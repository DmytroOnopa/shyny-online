import os
import json
import logging
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 249385425

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants for conversation states
PHOTO, NAME, DESC = range(3)
SELECT_FOR_NAME, ENTER_NEW_NAME = range(2)
SELECT_FOR_DESC, ENTER_NEW_DESC = range(2)
SELECT_FOR_PHOTO, ENTER_NEW_PHOTO = range(2)
SELECT_DELETE, CONFIRM_DELETE = range(2)

PRODUCTS_FILE = "products.json"

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def generate_site():
    subprocess.run(["python3", "generate_site.py"])

# Access check
def is_admin(user_id):
    return user_id == ADMIN_ID

# Add product flow
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("Надішли фото товару:")
    return PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Будь ласка, надішли фото.")
        return PHOTO

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_id = str(uuid4()) + ".jpg"
    path = os.path.join("images", file_id)
    os.makedirs("images", exist_ok=True)
    await file.download_to_drive(path)

    context.user_data["image"] = path
    await update.message.reply_text("Введи назву товару:")
    return NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введи опис товару:")
    return DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["desc"] = update.message.text

    products = load_products()
    products.append({
        "image": context.user_data["image"],
        "name": context.user_data["name"],
        "desc": context.user_data["desc"]
    })
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Товар додано.")
    return ConversationHandler.END

# List products
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products = load_products()
    if not products:
        await update.message.reply_text("Немає товарів.")
        return
    message = "\n\n".join(f"{i+1}. {p['name']}" for i, p in enumerate(products))
    await update.message.reply_text(f"🛒 Список товарів:\n\n{message}")

# Delete product
async def start_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products = load_products()
    if not products:
        await update.message.reply_text("Немає товарів.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(p["name"], callback_data=str(i))] for i, p in enumerate(products)]
    await update.message.reply_text("Оберіть товар для видалення:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_DELETE

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data)
    context.user_data["delete_index"] = index
    product = load_products()[index]
    await query.edit_message_text(f"Підтвердити видалення «{product['name']}»? (так / ні)")
    return CONFIRM_DELETE

async def do_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != "так":
        await update.message.reply_text("Скасовано.")
        return ConversationHandler.END

    index = context.user_data["delete_index"]
    products = load_products()
    deleted = products.pop(index)
    save_products(products)
    generate_site()
    await update.message.reply_text(f"✅ Товар «{deleted['name']}» видалено.")
    return ConversationHandler.END

# Edit name
async def start_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=str(i))] for i, p in enumerate(products)]
    await update.message.reply_text("Оберіть товар для редагування назви:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_FOR_NAME

async def ask_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["edit_index"] = int(query.data)
    await query.edit_message_text("Введіть нову назву:")
    return ENTER_NEW_NAME

async def set_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    index = context.user_data["edit_index"]
    products[index]["name"] = update.message.text
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Назву оновлено.")
    return ConversationHandler.END

# Edit description
async def start_edit_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=str(i))] for i, p in enumerate(products)]
    await update.message.reply_text("Оберіть товар для редагування опису:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_FOR_DESC

async def ask_new_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["edit_index"] = int(query.data)
    await query.edit_message_text("Введіть новий опис:")
    return ENTER_NEW_DESC

async def set_new_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    index = context.user_data["edit_index"]
    products[index]["desc"] = update.message.text
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Опис оновлено.")
    return ConversationHandler.END

# Edit photo
async def start_edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=str(i))] for i, p in enumerate(products)]
    await update.message.reply_text("Оберіть товар для редагування фото:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_FOR_PHOTO

async def ask_new_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["edit_index"] = int(query.data)
    await query.edit_message_text("Надішліть нове фото:")
    return ENTER_NEW_PHOTO

async def set_new_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_id = str(uuid4()) + ".jpg"
    path = os.path.join("images", file_id)
    os.makedirs("images", exist_ok=True)
    await file.download_to_drive(path)

    products = load_products()
    index = context.user_data["edit_index"]
    products[index]["image"] = path
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Фото оновлено.")
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Доступ заборонено.")
        return

    await update.message.reply_text(
        "👋 Вітаю! Доступні команди:\n"
        "/add – додати товар\n"
        "/list – список товарів\n"
        "/delete – видалити товар\n"
        "/edit_name – редагувати назву\n"
        "/edit_description – редагувати опис\n"
        "/edit_photo – редагувати фото"
    )


# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("list", list_products))

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", start_add)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
            NAME: [MessageHandler(filters.TEXT, add_name)],
            DESC: [MessageHandler(filters.TEXT, add_desc)],
        },
        fallbacks=[],
    )

    delete_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", start_delete)],
        states={
            SELECT_DELETE: [CallbackQueryHandler(confirm_delete)],
            CONFIRM_DELETE: [MessageHandler(filters.TEXT, do_delete)],
        },
        fallbacks=[],
    )

    edit_name_conv = ConversationHandler(
        entry_points=[CommandHandler("edit_name", start_edit_name)],
        states={
            SELECT_FOR_NAME: [CallbackQueryHandler(ask_new_name)],
            ENTER_NEW_NAME: [MessageHandler(filters.TEXT, set_new_name)],
        },
        fallbacks=[],
    )

    edit_desc_conv = ConversationHandler(
        entry_points=[CommandHandler("edit_description", start_edit_desc)],
        states={
            SELECT_FOR_DESC: [CallbackQueryHandler(ask_new_desc)],
            ENTER_NEW_DESC: [MessageHandler(filters.TEXT, set_new_desc)],
        },
        fallbacks=[],
    )

    edit_photo_conv = ConversationHandler(
        entry_points=[CommandHandler("edit_photo", start_edit_photo)],
        states={
            SELECT_FOR_PHOTO: [CallbackQueryHandler(ask_new_photo)],
            ENTER_NEW_PHOTO: [MessageHandler(filters.PHOTO, set_new_photo)],
        },
        fallbacks=[],
    )

    app.add_handler(add_conv)
    app.add_handler(delete_conv)
    app.add_handler(edit_name_conv)
    app.add_handler(edit_desc_conv)
    app.add_handler(edit_photo_conv)

    app.run_polling()

