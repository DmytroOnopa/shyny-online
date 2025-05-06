# generate_site.py
import json
import os
import subprocess

with open("products.json", encoding="utf-8") as f:
    products = json.load(f)

html = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>ШИНИ.ONLINE</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }
        .product { background: white; border-radius: 8px; padding: 10px; margin: 10px auto; max-width: 400px; box-shadow: 0 0 5px rgba(0,0,0,0.1); }
        .product img { max-width: 100%; border-radius: 6px; }
        .product h2 { margin: 10px 0 5px; }
    </style>
</head>
<body>
    <h1>ШИНИ.ONLINE — Вживані шини</h1>
"""

for p in products:
    rel_path = p["image"].replace("images/", "")
    html += f"""
    <div class="product">
        <img src="images/{rel_path}" alt="{p['name']}">
        <h2>{p['name']}</h2>
        <p>{p['desc']}</p>
    </div>
    """

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ index.html згенеровано.")

# Git auto-commit & push
subprocess.run(["git", "add", "index.html", "products.json"])
subprocess.run(["git", "add", "images"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["git", "commit", "-m", "оновлено товари"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["git", "push", "origin", "main"])

