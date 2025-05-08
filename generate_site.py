import json
import os
import subprocess

def load_products():
    if not os.path.exists("products.json"):
        return []
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_site():
    products = load_products()

    html = """<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Шини Онлайн – Вживані шини для будь-якої техніки</title>
  <link rel="icon" href="favicon.ico" type="image/x-icon">
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <style>
    .card:hover {
      transform: scale(1.03);
      transition: transform 0.3s ease;
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
    }
  </style>
</head>
<body class="bg-gray-900 text-white">

  <header class="bg-gray-800 shadow sticky top-0 z-10">
    <div class="max-w-6xl mx-auto px-4 py-6 flex justify-between items-center">
      <a href="index.html" class="text-2xl font-bold text-white hover:text-blue-400 transition">🔘 ШИНИ.ONLINE</a>
      <a href="https://t.me/shynyRobot" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl transition shadow-lg">Зв'язатися</a>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 py-10">
    <h2 class="text-xl font-semibold mb-6">Доступні товари:</h2>
    <div class="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
"""

    for p in products:
        image_path = p["image"].replace("images/", "")
        html += f"""
      <div class="card bg-gray-800 rounded-2xl shadow-lg overflow-hidden transition p-4">
        <img src="images/{image_path}" alt="{p['name']}" class="rounded-xl w-full h-52 object-cover mb-4">
        <h3 class="text-lg font-bold text-white">{p['name']}</h3>
        <p class="text-sm text-gray-300">{p['description']}</p>
      </div>
"""

    html += """
    </div>
  </main>

  <section class="max-w-6xl mx-auto px-4 py-10">
    <h2 class="text-xl font-semibold mb-4">Контакти</h2>
    <p class="mb-2"><strong>Адреса:</strong> Траса Київ-Луганськ-Ізварено 295, Знам'янка, Кіровоградська область</p>
    <p class="mb-4"><strong>Телефон:</strong> <a href="tel:+380667204855" class="text-blue-400 hover:underline">066 720 48 55</a></p>
    <iframe src="https://maps.google.com/maps?q=Траса%20Київ-Луганськ-Ізварено%20295,%20Знам'янка&t=&z=13&ie=UTF8&iwloc=&output=embed"
      class="w-full h-64 rounded-xl border-0 shadow-lg"></iframe>
  </section>

  <footer class="text-center text-gray-400 text-sm py-6">
    &copy; 2025 ШИНИ.ONLINE — Вживані шини для будь-якої техніки
  </footer>

</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def git_push():
    try:
        subprocess.run(["git", "add", "index.html"], check=True)
        subprocess.run(["git", "commit", "-m", "🔄 Автоматичне оновлення сайту"], check=True)
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ Помилка під час git push. Перевір автентифікацію або з'єднання.")

if __name__ == "__main__":
    generate_site()
    git_push()

