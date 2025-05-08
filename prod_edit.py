import json

# Завантажуємо список товарів з файлу
with open("products.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Проходимо по всіх товарах і замінюємо ключ "desc" на "description", якщо він є
for product in products:
    if "desc" in product:
        product["description"] = product.pop("desc")

# Зберігаємо оновлений список назад у файл
with open("products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print("✅ Ключі 'desc' замінено на 'description'.")

