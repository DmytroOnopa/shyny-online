import json
import os

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
  <title>ШИНИ.ONLINE</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 text-gray-800">

  <header class="bg-white shadow sticky top-0 z-10">
    <div class="max-w-6xl mx-auto px-4 py-6 flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">🛞 ШИНИ.ONLINE</h1>
      <a href="https://t.me/shynyRobot" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition">Зв'язатися</a>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 py-10">
    <h2 class="text-xl font-semibold mb-6">Доступні товари:</h2>
    <div class="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
"""

    for p in products:
        image_path = p["image"].replace("images/", "")
        html += f"""
      <div class="bg-white rounded-2xl shadow hover:shadow-lg transition p-4">
        <img src="images/{image_path}" alt="{p['name']}" class="rounded-xl w-full h-52 object-cover mb-4">
        <h3 class="text-lg font-bold">{p['name']}</h3>
        <p class="text-sm text-gray-600">{p['desc']}</p>
      </div>
"""

    html += """
    </div>
  </main>

  <footer class="text-center text-gray-500 text-sm py-6">
    &copy; 2025 ШИНИ.ONLINE — Вживані шини для будь-якої техніки
  </footer>

</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    generate_site()

