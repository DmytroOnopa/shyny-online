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
  <style>
    body {
      background-color: #1a202c;
      color: #e2e8f0;
      font-family: 'Segoe UI', sans-serif;
    }
    .card:hover {
      transform: translateY(-5px);
      box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .card {
      transition: all 0.3s ease;
    }
    a.button {
      background-color: #3182ce;
      padding: 0.5rem 1rem;
      color: white;
      border-radius: 0.5rem;
      transition: background 0.3s ease;
    }
    a.button:hover {
      background-color: #2b6cb0;
    }
  </style>
</head>
<body>

  <header class="bg-gray-900 shadow sticky top-0 z-10">
    <div class="max-w-6xl mx-auto px-4 py-6 flex justify-between items-center">
      <a href="/" class="text-2xl font-bold text-white hover:text-blue-400 transition">🛞 ШИНИ.ONLINE</a>
      <a href="https://t.me/shynyRobot" class="button">Зв'язатися</a>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 py-10">
    <h2 class="text-2xl font-semibold mb-8">🛒 Доступні товари</h2>
    <div class="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
"""

    for p in products:
        image_path = p["image"].replace("images/", "")
        html += f"""
      <div class="bg-gray-800 rounded-2xl card shadow p-4">
        <img src="images/{image_path}" alt="{p['name']}" class="rounded-xl w-full h-52 object-cover mb-4">
        <h3 class="text-lg font-bold text-white mb-2">{p['name']}</h3>
        <p class="text-sm text-gray-300">{p['desc']}</p>
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

