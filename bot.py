from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes, CallbackQueryHandler
)
import json, os, subprocess

TOKEN = "8043656898:AAGTfXdIV0s60scs_5WPXwMlnd2RRQvDLQs"
OWNER_ID = 249385425
PRODUCTS_FILE = "products.json"
ADD_NAME, ADD_DESC, ADD_PHOTO = range(3)
EDIT_SELECT, EDIT_FIELD, EDIT_VALUE, EDIT_CONFIRM = range(4)
DELETE_CONFIRM = range(1)

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

# Обмеження доступу
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(
        "Привіт! Я бот для керування товарами 🛞\n"
        "/add — додати товар\n"
        "/edit — редагувати товар\n"
        "/delete — видалити товар\n"
        "/list — переглянути всі товари\n"
        "/cancel — скасувати дію"
    )

# Додавання товару
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text("Введи назву товару:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Тепер введи опис товару:")
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

# Перелік товарів
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    products = load_products()
    if not products:
        await update.message.reply_text("Список товарів порожній.")
        return
    for p in products:
        caption = f"ID: {p['id']}\n{p['name']}\n{p['desc']}"
        with open(p['image'], 'rb') as img:
            await update.message.reply_photo(photo=img, caption=caption)

# Скасування
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Дію скасовано.")
    return ConversationHandler.END

# Редагування товару
async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    products = load_products()
    buttons = [[InlineKeyboardButton(p['name'], callback_data=str(p['id']))] for p in products]
    await update.message.reply_text("Оберіть товар для редагування:", reply_markup=InlineKeyboardMarkup(buttons))
    return EDIT_SELECT

async def edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['edit_id'] = int(query.data)
    buttons = [
        [InlineKeyboardButton("Назва", callback_data="name")],
        [InlineKeyboardButton("Опис", callback_data="desc")],
        [InlineKeyboardButton("Фото", callback_data="image")],
    ]
    await query.edit_message_text("Що хочеш змінити?", reply_markup=InlineKeyboardMarkup(buttons))
    return EDIT_FIELD

async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['edit_field'] = query.data
    await query.edit_message_text("Введи нове значення (або надішли нове фото):")
    return EDIT_VALUE

async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    product = next((p for p in products if p['id'] == context.user_data['edit_id']), None)
    if not product:
        await update.message.reply_text("❌ Товар не знайдено.")
        return ConversationHandler.END

    field = context.user_data['edit_field']
    if field == "image" and update.message.photo:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        file_path = f"images/{photo_file.file_id}.jpg"
        await photo_file.download_to_drive(file_path)
        product['image'] = file_path
    elif field in ["name", "desc"]:
        product[field] = update.message.text
    else:
        await update.message.reply_text("❌ Неправильний ввід.")
        return ConversationHandler.END

    save_products(products)
    generate_site()
    await update.message.reply_text("✅ Товар оновлено!")
    return ConversationHandler.END

# Видалення товару
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    products = load_products()
    buttons = [[InlineKeyboardButton(p['name'], callback_data=str(p['id']))] for p in products]
    await update.message.reply_text("Оберіть товар для видалення:", reply_markup=InlineKeyboardMarkup(buttons))
    return DELETE_CONFIRM

async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = int(query.data)
    products = load_products()
    product = next((p for p in products if p['id'] == prod_id), None)
    if not product:
        await query.edit_message_text("❌ Товар не знайдено.")
        return ConversationHandler.END

    products = [p for p in products if p['id'] != prod_id]
    save_products(products)
    generate_site()
    await query.edit_message_text("🗑️ Товар видалено та сайт оновлено!")
    return ConversationHandler.END

# Запуск
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_products))

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
            EDIT_SELECT: [CallbackQueryHandler(edit_select)],
            EDIT_FIELD: [CallbackQueryHandler(edit_field)],
            EDIT_VALUE: [MessageHandler(filters.TEXT | filters.PHOTO, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True
    )

    delete_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            DELETE_CONFIRM: [CallbackQueryHandler(delete_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True
    )

    app.add_handler(add_conv)
    app.add_handler(edit_conv)
    app.add_handler(delete_conv)

    app.run_polling()

if __name__ == "__main__":
    main()

