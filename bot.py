from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Токен бота
TOKEN = "8043656898:AAGTfXdIV0s60scs_5WPXwMlnd2RRQvDLQs"
ADMIN_ID = "249385425"  # Замінити на ID адміністратора

# Товари
products = [
    {"name": "195/65 R15", "image": "images/tire1.jpg", "description": "Стан: 80%, пара"},
    {"name": "205/55 R16", "image": "images/tire2.jpg", "description": "Стан: 70%, комплект"},
    {"name": "385/65 R22.5", "image": "images/tire3.jpg", "description": "Стан: 60%, одна"}
]

# Функція для старту бота
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=str(index))]
        for index, product in enumerate(products)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Виберіть товар для замовлення:", reply_markup=reply_markup)

# Обробка натискання на кнопку
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    product_index = int(query.data)
    product = products[product_index]
    
    # Надсилаємо повідомлення адміну
    await context.bot.send_photo(
        ADMIN_ID,
        photo=open(product['image'], 'rb'),
        caption=f"Замовлення:\n\nТовар: {product['name']}\n{product['description']}\n\nЗамовив: {update.effective_user.full_name} (@{update.effective_user.username})",
    )
    
    # Підтверджуємо замовлення користувачу
    await query.answer()
    await query.edit_message_text(f"Ваше замовлення: {product['name']} підтверджено! Очікуйте на зв'язок.")

# Запуск бота
def main():
    application = Application.builder().token(TOKEN).build()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()

if __name__ == "__main__":
    main()

