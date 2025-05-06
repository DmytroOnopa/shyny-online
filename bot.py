import os
import json
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from telegram.ext import CallbackContext
import logging
from dotenv import load_dotenv
import subprocess

# Завантажуємо змінні середовища з .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Змінна для перевірки, чи користувач є адміністратором
ADMIN_ID = 249385425

# Завантаження товарів з файлу products.json
def load_products():
    if not os.path.exists("products.json"):
        return []
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Генерація сайту
def generate_site():
    products = load_products()
    subprocess.run(["python3", "generate_site.py"])

# Стартова команда
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "Привіт! Використовуй команди для керування товарами:\n"
            "/list - Список товарів\n"
            "/add - Додати товар\n"
            "/edit_name - Редагувати назву товару\n"
            "/edit_description - Редагувати опис товару\n"
            "/edit_photo - Редагувати фото товару"
        )
    else:
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.")

# Перевірка на адміністраторський доступ
def is_admin(user_id):
    return user_id == ADMIN_ID

# Команда для перегляду списку товарів
async def list_products(update: Update, context: CallbackContext):
    products = load_products()
    if not products:
        await update.message.reply_text("Немає доступних товарів.")
    else:
        product_list = "\n".join([f"{p['name']} (ID: {p['id']})" for p in products])
        await update.message.reply_text(f"Список товарів:\n{product_list}")

# Додавання нового товару
async def add_product(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return
    await update.message.reply_text("Надішліть фото для нового товару.")
    return 1

# Обробка фото при додаванні товару
async def add_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return

    photo = update.message.photo[-1]
    
    # Генерація унікального імені для фото
    existing_files = os.listdir("images")
    indices = [int(f.split(".")[0]) for f in existing_files if f.endswith(".jpg") and f.split(".")[0].isdigit()]
    next_index = max(indices, default=0) + 1
    image_path = f"images/{next_index}.jpg"
    
    # Завантажуємо фото
    file = await context.bot.get_file(photo.file_id)
    await file.download_to_drive(image_path)

    # Запит на назву товару
    context.user_data["image_path"] = image_path
    await update.message.reply_text("Фото додано. Тепер надайте назву товару.")
    return 2

# Отримання назви товару
async def add_name(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return

    name = update.message.text
    context.user_data["name"] = name
    await update.message.reply_text(f"Назва товару: {name}. Тепер надайте опис товару.")
    return 3

# Отримання опису товару
async def add_description(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return

    description = update.message.text
    context.user_data["description"] = description

    # Збереження товару в JSON
    products = load_products()
    product = {
        "id": len(products) + 1,
        "name": context.user_data["name"],
        "desc": context.user_data["description"],
        "image": context.user_data["image_path"]
    }
    products.append(product)

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    generate_site()

    await update.message.reply_text(f"Товар '{product['name']}' успішно додано.")
    return ConversationHandler.END

# Редагування назви товару
async def edit_name(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return

    products = load_products()
    if not products:
        await update.message.reply_text("Немає товарів для редагування.")
        return

    product_list = "\n".join([f"{p['name']} (ID: {p['id']})" for p in products])
    await update.message.reply_text(f"Оберіть товар для редагування:\n{product_list}")
    return 4

# Обробка вибору товару для редагування
async def choose_product(update: Update, context: CallbackContext):
    product_id = int(update.message.text)
    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await update.message.reply_text("Товар не знайдено.")
        return ConversationHandler.END

    context.user_data["product_id"] = product_id
    await update.message.reply_text(f"Вибрано товар: {product['name']}. Введіть нову назву.")
    return 5

# Оновлення назви товару
async def update_name(update: Update, context: CallbackContext):
    new_name = update.message.text
    products = load_products()

    product = next((p for p in products if p["id"] == context.user_data["product_id"]), None)
    if product:
        product["name"] = new_name
        with open("products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        generate_site()

    await update.message.reply_text(f"Назву товару змінено на: {new_name}.")
    return ConversationHandler.END

# Основна функція для запуску бота
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    list_handler = CommandHandler("list", list_products)
    add_handler = CommandHandler("add", add_product)
    edit_name_handler = CommandHandler("edit_name", edit_name)

    conversation_handler = ConversationHandler(
        entry_points=[add_handler, edit_name_handler],
        states={
            1: [MessageHandler(filters.PHOTO, add_photo)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_product)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_name)],
        },
        fallbacks=[],
    )

    application.add_handler(start_handler)
    application.add_handler(list_handler)
    application.add_handler(conversation_handler)
    
    application.run_polling()

if __name__ == "__main__":
    main()

