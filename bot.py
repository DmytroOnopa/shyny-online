import os
import json
from telegram import Update
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
            "/edit_photo - Редагувати фото товару\n"
            "/delete - Видалити товар"
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

    await update.message.reply_text("Відправте фото для товару.")
    return 1

# Додавання фото для товару
async def add_photo(update: Update, context: CallbackContext):
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"images/{photo_file.file_id}.jpg"
    photo_file.download(photo_path)

    context.user_data["photo_path"] = photo_path
    await update.message.reply_text("Тепер введіть назву товару.")
    return 2

# Додавання назви товару
async def add_name(update: Update, context: CallbackContext):
    name = update.message.text
    context.user_data["name"] = name
    await update.message.reply_text("Тепер введіть опис товару.")
    return 3

# Додавання опису товару
async def add_description(update: Update, context: CallbackContext):
    description = update.message.text
    context.user_data["description"] = description

    products = load_products()
    product_id = len(products) + 1  # Призначаємо унікальний ID товару
    new_product = {
        "id": product_id,
        "name": context.user_data["name"],
        "description": context.user_data["description"],
        "photo": context.user_data["photo_path"]
    }
    products.append(new_product)

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    generate_site()
    await update.message.reply_text(f"Товар '{new_product['name']}' успішно додано.")
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

# Вибір товару для редагування
async def choose_product(update: Update, context: CallbackContext):
    product_id = int(update.message.text)
    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await update.message.reply_text("Товар не знайдено.")
        return ConversationHandler.END

    context.user_data["product_id"] = product_id
    await update.message.reply_text(f"Вибрано товар: {product['name']}. Введіть нову назву товару.")
    return 5

# Оновлення назви товару
async def update_name(update: Update, context: CallbackContext):
    new_name = update.message.text
    product_id = context.user_data["product_id"]

    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await update.message.reply_text("Товар не знайдено.")
        return ConversationHandler.END

    product["name"] = new_name

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    generate_site()
    await update.message.reply_text(f"Назву товару успішно змінено на '{new_name}'.")
    return ConversationHandler.END

# Редагування опису товару
async def edit_description(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return

    products = load_products()
    if not products:
        await update.message.reply_text("Немає товарів для редагування.")
        return

    product_list = "\n".join([f"{p['name']} (ID: {p['id']})" for p in products])
    await update.message.reply_text(f"Оберіть товар для редагування опису:\n{product_list}")
    return 6

# Оновлення опису товару
async def update_description(update: Update, context: CallbackContext):
    new_description = update.message.text
    product_id = context.user_data["product_id"]

    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await update.message.reply_text("Товар не знайдено.")
        return ConversationHandler.END

    product["description"] = new_description

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    generate_site()
    await update.message.reply_text(f"Опис товару успішно змінено.")
    return ConversationHandler.END

# Редагування фото товару
async def edit_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return

    products = load_products()
    if not products:
        await update.message.reply_text("Немає товарів для редагування.")
        return

    product_list = "\n".join([f"{p['name']} (ID: {p['id']})" for p in products])
    await update.message.reply_text(f"Оберіть товар для редагування фото:\n{product_list}")
    return 8

# Оновлення фото товару
async def update_photo(update: Update, context: CallbackContext):
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"images/{photo_file.file_id}.jpg"
    photo_file.download(photo_path)

    product_id = context.user_data["product_id"]

    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await update.message.reply_text("Товар не знайдено.")
        return ConversationHandler.END

    product["photo"] = photo_path

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    generate_site()
    await update.message.reply_text(f"Фото товару успішно оновлено.")
    return ConversationHandler.END

# Видалення товару
async def delete_product(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цієї команди.")
        return

    products = load_products()
    if not products:
        await update.message.reply_text("Немає товарів для видалення.")
        return

    product_list = "\n".join([f"{p['name']} (ID: {p['id']})" for p in products])
    await update.message.reply_text(f"Оберіть товар для видалення:\n{product_list}")
    return 6

# Обробка вибору товару для видалення
async def choose_product_for_deletion(update: Update, context: CallbackContext):
    product_id = int(update.message.text)
    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        await update.message.reply_text("Товар не знайдено.")
        return ConversationHandler.END

    context.user_data["product_id"] = product_id
    await update.message.reply_text(f"Вибрано товар: {product['name']}. Підтвердіть видалення, надіславши команду /confirm_delete.")
    return 7

# Підтвердження видалення товару
async def confirm_delete(update: Update, context: CallbackContext):
    product_id = context.user_data["product_id"]
    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)

    if product:
        products = [p for p in products if p["id"] != product_id]
        with open("products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        generate_site()

    await update.message.reply_text(f"Товар '{product['name']}' успішно видалено.")
    return ConversationHandler.END

# Основна функція для запуску бота
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    list_handler = CommandHandler("list", list_products)
    add_handler = CommandHandler("add", add_product)
    edit_name_handler = CommandHandler("edit_name", edit_name)
    edit_description_handler = CommandHandler("edit_description", edit_description)
    edit_photo_handler = CommandHandler("edit_photo", edit_photo)
    delete_handler = CommandHandler("delete", delete_product)

    conversation_handler = ConversationHandler(
        entry_points=[add_handler, edit_name_handler, edit_description_handler, edit_photo_handler, delete_handler],
        states={
            1: [MessageHandler(filters.PHOTO, add_photo)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_product)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_name)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_product_for_deletion)],
            7: [MessageHandler(filters.COMMAND, confirm_delete)],
            8: [MessageHandler(filters.PHOTO, update_photo)],
        },
        fallbacks=[],
    )

    application.add_handler(start_handler)
    application.add_handler(list_handler)
    application.add_handler(conversation_handler)

    application.run_polling()

if __name__ == "__main__":
    main()

