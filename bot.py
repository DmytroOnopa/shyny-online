import os
import json
import logging
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters,
                          ContextTypes, CallbackQueryHandler, ConversationHandler)

# Завантаження змінних середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 249385425

# Логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Стан для додавання
ADD_NAME, ADD_DESC, ADD_PHOTO = range(3)
# Стан для редагування
EDIT_SELECT, EDIT_NAME, EDIT_DESC, EDIT_PHOTO = range(4)
# Видалення
DELETE_SELECT, CONFIRM_DELETE = range(2)

products_file = "products.json"
images_dir = "images"
os.makedirs(images_dir, exist_ok=True)


def load_products():
    if not os.path.exists(products_file):
        return []
    with open(products_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(products_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def generate_site():
    subprocess.run(["python3", "generate_site.py"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Вітаю! Я бот для керування товарами на сайті шини.online.\nДоступні команди: /add, /list, /edit_name, /edit_description, /edit_photo, /delete")

# Додавання товару
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Введіть назву товару:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product'] = {'name': update.message.text}
    await update.message.reply_text("Введіть опис товару:")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['desc'] = update.message.text
    await update.message.reply_text("Надішліть фото товару:")
    return ADD_PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file = await context.bot.get_file(file_id)
    filename = f"{uuid4().hex}.jpg"
    image_path = os.path.join(images_dir, filename)
    await file.download_to_drive(image_path)

    product = context.user_data['new_product']
    product['image'] = image_path

    products = load_products()
    products.append(product)
    save_products(products)
    generate_site()

    await update.message.reply_text("Товар додано!")
    return ConversationHandler.END

# Список товарів
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    products = load_products()
    if not products:
        await update.message.reply_text("Список товарів порожній.")
        return

    for i, p in enumerate(products):
        caption = f"#{i+1} {p['name']}\n{p['desc']}"
        with open(p['image'], 'rb') as img:
            await update.message.reply_photo(InputFile(img), caption=caption)

# ====== РЕДАГУВАННЯ ======
async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    products = load_products()
    buttons = [[InlineKeyboardButton(p['name'], callback_data=str(i))] for i in range(len(products))]
    context.user_data['edit_type'] = context.match.string.replace("/edit_", "")
    await update.message.reply_text("Оберіть товар:", reply_markup=InlineKeyboardMarkup(buttons))
    return EDIT_SELECT

async def edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data)
    context.user_data['edit_index'] = index
    edit_type = context.user_data.get('edit_type')

    prompt = {
        'name': "Введіть нову назву:",
        'description': "Введіть новий опис:",
        'photo': "Надішліть нове фото:"
    }[edit_type]
    await query.edit_message_text(prompt)

    return {
        'name': EDIT_NAME,
        'description': EDIT_DESC,
        'photo': EDIT_PHOTO
    }[edit_type]

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    products[context.user_data['edit_index']]['name'] = update.message.text
    save_products(products)
    generate_site()
    await update.message.reply_text("Назву оновлено!")
    return ConversationHandler.END

async def edit_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_products()
    products[context.user_data['edit_index']]['desc'] = update.message.text
    save_products(products)
    generate_site()
    await update.message.reply_text("Опис оновлено!")
    return ConversationHandler.END

async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    filename = f"{uuid4().hex}.jpg"
    image_path = os.path.join(images_dir, filename)
    await file.download_to_drive(image_path)

    products = load_products()
    products[context.user_data['edit_index']]['image'] = image_path
    save_products(products)
    generate_site()
    await update.message.reply_text("Фото оновлено!")
    return ConversationHandler.END

# ====== ВИДАЛЕННЯ ======
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    products = load_products()
    buttons = [[InlineKeyboardButton(p['name'], callback_data=str(i))] for i in range(len(products))]
    await update.message.reply_text("Оберіть товар для видалення:", reply_markup=InlineKeyboardMarkup(buttons))
    return DELETE_SELECT

async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data)
    context.user_data['delete_index'] = index

    product = load_products()[index]
    buttons = [[InlineKeyboardButton("✅ Так", callback_data="yes"), InlineKeyboardButton("❌ Ні", callback_data="no")]]
    await query.edit_message_text(f"Ви впевнені, що хочете видалити '{product['name']}'?", reply_markup=InlineKeyboardMarkup(buttons))
    return CONFIRM_DELETE

async def delete_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "yes":
        products = load_products()
        index = context.user_data['delete_index']
        products.pop(index)
        save_products(products)
        generate_site()
        await query.edit_message_text("Товар видалено!")
    else:
        await query.edit_message_text("Скасовано.")
    return ConversationHandler.END

# Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_products))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PHOTO: [MessageHandler(filters.PHOTO, add_photo)]
        },
        fallbacks=[]
    ))

    for cmd, state, callback in [
        ("edit_name", EDIT_NAME, edit_name),
        ("edit_description", EDIT_DESC, edit_desc),
        ("edit_photo", EDIT_PHOTO, edit_photo)
    ]:
        app.add_handler(ConversationHandler(
            entry_points=[CommandHandler(cmd, select_product)],
            states={
                EDIT_SELECT: [CallbackQueryHandler(edit_select)],
                state: [MessageHandler(filters.ALL, callback)]
            },
            fallbacks=[],
            per_message=True
        ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            DELETE_SELECT: [CallbackQueryHandler(delete_confirm)],
            CONFIRM_DELETE: [CallbackQueryHandler(delete_finish)]
        },
        fallbacks=[],
        per_message=True
    ))

    print("✅ Бот запущено")
    app.run_polling()

