from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes, CallbackQueryHandler
)
import json, os, subprocess

import os
from dotenv import load_dotenv

# Завантажити змінні середовища з .env файлу
load_dotenv()

# Отримати токен з середовища
TOKEN = os.getenv("TELEGRAM_TOKEN")

PRODUCTS_FILE = "products.json"
ADMIN_ID = 249385425

ADD_NAME, ADD_DESC, ADD_PHOTO = range(3)
EDIT_NAME, EDIT_DESC, EDIT_PHOTO = range(3)
CONFIRM_DELETE = 0

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

# ========== AUTH ================
def is_admin(user_id):
    return user_id == ADMIN_ID

# ========== START ===============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ Доступ заборонено.")
    await update.message.reply_text(
        "Привіт! Я бот для керування товарами 🛞\n"
        "/add — додати товар\n"
        "/list — переглянути товари\n"
        "/edit — редагувати товар\n"
        "/delete — видалити товар\n"
        "/cancel — скасувати дію"
    )

# ========== ДОДАВАННЯ ============
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text("Введи назву товару:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введи опис товару:")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["desc"] = update.message.text
    await update.message.reply_text("Надішли фото товару:")
    return ADD_PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    os.makedirs("images", exist_ok=True)
    file_path = f"images/{photo_file.file_id}.jpg"
    await photo_file.download_to_drive(file_path)

    products = load_products()
    products.append({
        "id": len(products) + 1,
        "name": context.user_data["name"],
        "desc": context.user_data["desc"],
        "image": file_path
    })
    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Товар додано та сайт оновлено!")
    return ConversationHandler.END

# ========== СКАСУВАННЯ ============
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Дію скасовано.")
    return ConversationHandler.END

# ========== СПИСОК ===============
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    products = load_products()
    if not products:
        await update.message.reply_text("Список товарів порожній.")
        return
    for p in products:
        caption = f"ID: {p['id']}\n{p['name']}\n{p['desc']}"
        with open(p['image'], 'rb') as img:
            await update.message.reply_photo(photo=img, caption=caption)

# ========== РЕДАГУВАННЯ ===============
async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=f"edit_{p['id']}")] for p in products]
    await update.message.reply_text("Вибери товар для редагування:", reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_NAME

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = int(query.data.split("_")[1])
    context.user_data["edit_id"] = pid
    await query.message.reply_text("Введи нову назву:")
    return EDIT_NAME

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_name"] = update.message.text
    await update.message.reply_text("Введи новий опис:")
    return EDIT_DESC

async def edit_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_desc"] = update.message.text
    await update.message.reply_text("Надішли нове фото:")
    return EDIT_PHOTO

async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    file_path = f"images/{photo_file.file_id}.jpg"
    await photo_file.download_to_drive(file_path)

    products = load_products()
    pid = context.user_data["edit_id"]
    for p in products:
        if p["id"] == pid:
            p["name"] = context.user_data["new_name"]
            p["desc"] = context.user_data["new_desc"]
            p["image"] = file_path
            break
    save_products(products)
    generate_site()
    await update.message.reply_text("✏️ Товар оновлено!")
    return ConversationHandler.END

# ========== ВИДАЛЕННЯ ===============
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=f"del_{p['id']}")] for p in products]
    await update.message.reply_text("Вибери товар для видалення:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_DELETE

async def start_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = int(query.data.split("_")[1])
    context.user_data["delete_id"] = pid
    keyboard = [
        [InlineKeyboardButton("✅ Так", callback_data="confirm_delete")],
        [InlineKeyboardButton("❌ Ні", callback_data="cancel")]
    ]
    await query.message.reply_text("Підтверджуєш видалення?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_DELETE

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_delete":
        products = load_products()
        pid = context.user_data["delete_id"]
        products = [p for p in products if p["id"] != pid]
        for i, p in enumerate(products): p["id"] = i + 1
        save_products(products)
        generate_site()
        await query.message.reply_text("🗑️ Товар видалено!")
    else:
        await query.message.reply_text("❌ Скасовано.")
    return ConversationHandler.END

# ========== ЗАПУСК ==================
def main():
    app = Application.builder().token(TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_start)],
        states={
            EDIT_NAME: [CallbackQueryHandler(start_edit)],
            EDIT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
            EDIT_PHOTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_desc), MessageHandler(filters.PHOTO, edit_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    delete_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            CONFIRM_DELETE: [CallbackQueryHandler(start_delete), CallbackQueryHandler(confirm_delete)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_products))
    app.add_handler(add_conv)
    app.add_handler(edit_conv)
    app.add_handler(delete_conv)
    app.run_polling()

if __name__ == "__main__":
    main()

