import os
import json
import subprocess

PRODUCTS_FILE = "products.json"
OUTPUT_FILE = "index.html"
IMAGES_DIR = "images"

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def generate_html(products):
    html = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Шини онлайн</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .product { border: 1px solid #ccc; padding: 10px; margin: 10px; border-radius: 10px; display: inline-block; width: 200px; vertical-align: top; }
        img { max-width: 100%; border-radius: 8px; }
    </style>
</head>
<body>
<h1>Шини онлайн</h1>
"""

    for p in products:
        image_name = os.path.basename(p["image"])
        html += f"""
<div class="product">
    <img src="{IMAGES_DIR}/{image_name}" alt="{p['name']}">
    <h3>{p['name']}</h3>
    <p>{p['description']}</p>
</div>
"""

    html += """
</body>
</html>
"""
    return html

def git_commit_and_push():
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "🛠️ Автогенерація сайту"], check=False)
    subprocess.run(["git", "push"], check=True)

def generate_site():
    products = load_products()
    html = generate_html(products)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    print("✅ Сайт згенеровано")

    print("📤 Пушимо у Git...")
    git_commit_and_push()

if __name__ == "__main__":
    generate_site()

