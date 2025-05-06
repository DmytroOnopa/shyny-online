from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import json, os, subprocess

TOKEN = "8043656898:AAGTfXdIV0s60scs_5WPXwMlnd2RRQvDLQs"
PRODUCTS_FILE = "products.json"
ADD_NAME, ADD_DESC, ADD_PHOTO = range(3)

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот для керування товарами 🛞\n"
        "/add — додати товар\n"
        "/list — переглянути всі товари\n"
        "/cancel — скасувати дію"
    )

# Команда /add — початок додавання
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введи назву товару:")
    return ADD_NAME

# Збереження назви
async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Тепер введи опис товару:")
    return ADD_DESC

# Збереження опису
async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["desc"] = update.message.text
    await update.message.reply_text("Надішли фото товару:")
    return ADD_PHOTO

# Збереження фото
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

# Скасування
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Дію скасовано.")
    return ConversationHandler.END

# Команда /list — список товарів
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    if not products:
        await update.message.reply_text("Список товарів порожній.")
        return
    for p in products:
        caption = f"ID: {p['id']}\n{p['name']}\n{p['desc']}"
        with open(p['image'], 'rb') as img:
            await update.message.reply_photo(photo=img, caption=caption)

# Запуск бота
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_products))
    app.add_handler(add_conv)

    app.run_polling()

if __name__ == "__main__":
    main()

