import os

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
_PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
CORS(app)


def _openrouter_key():
    """Must read OPENROUTER_API_KEY from env on Vercel — do not hardcode keys in source."""
    return (os.environ.get("OPENROUTER_API_KEY") or "").strip()


def _openrouter_referer():
    site = (os.environ.get("SITE_URL") or os.environ.get("VERCEL_URL") or "").strip()
    if site and not site.startswith("http"):
        site = "https://" + site
    if site:
        return site
    return request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost"


@app.route("/ai", methods=["POST"])
def ai():
    payload = request.get_json(silent=True) or {}
    user_input = payload.get("message")
    if user_input is None:
        return jsonify({"error": "message is required"}), 400

    api_key = _openrouter_key()
    if not api_key:
        return jsonify({
            "answer": "Задайте OPENROUTER_API_KEY в Vercel (Settings → Environment Variables), "
            "включите для Production и Preview, затем Redeploy. Ключ не должен быть в коде."
        })

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": _openrouter_referer(),
        "X-Title": "Almaty DataLab",
    }

    data = {
        "model": "qwen/qwen3.6-plus:free",
        "messages": [
            {
                "role": "system",
                "content": "Ты AI-консультант по недвижимости в Алматы. Отвечай кратко, по делу, с аналитикой."
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        # ↓ Qwen3 — reasoning-модель, это отключает "думалку" и даёт чистый ответ
        "include_reasoning": False
    }

    response = requests.post(url, headers=headers, json=data, timeout=60)
    try:
        result = response.json()
    except Exception:
        return jsonify({"answer": f"OpenRouter HTTP {response.status_code}: {response.text[:400]}"})

    # Логируем весь ответ — смотри в терминале Flask
    print("STATUS:", response.status_code)
    print("RESPONSE:", result)

    if result.get("error"):
        e = result["error"]
        msg = e.get("message", str(e)) if isinstance(e, dict) else str(e)
        code = e.get("code", response.status_code) if isinstance(e, dict) else response.status_code
        hint = ""
        if response.status_code == 401 or code == 401:
            hint = " Проверьте ключ на https://openrouter.ai/keys и что в Vercel нет лишних пробелов в значении."
        return jsonify({"answer": f"OpenRouter ({code}): {msg}.{hint}"})

    try:
        answer = result["choices"][0]["message"]["content"]
        if not answer:
            answer = result["choices"][0]["message"].get("reasoning", "Нет ответа")
    except Exception as e:
        print("PARSE ERROR:", e)
        answer = f"Ошибка парсинга: {result}"

    return jsonify({"answer": answer})

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/style.css")
def style_css():
    return send_from_directory(_PUBLIC, "style.css")

if __name__ == "__main__":
    app.run(port=5000, debug=True)