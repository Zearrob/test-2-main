import os

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
_PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
CORS(app)


@app.route("/ai", methods=["POST"])
def ai():
    payload = request.get_json(silent=True) or {}
    user_input = payload.get("message")
    if user_input is None:
        return jsonify({"error": "message is required"}), 400

    api_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        return jsonify({"answer": "Нет OPENROUTER_API_KEY в окружении (Vercel → Env → Redeploy)."})

    site = (os.environ.get("SITE_URL") or os.environ.get("VERCEL_URL") or "").strip()
    if site and not site.startswith("http"):
        site = "https://" + site
    ref = site or request.headers.get("Origin") or request.headers.get("Referer") or "http://localhost"

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": ref,
        "X-Title": "Almaty DataLab",
    }
    data = {
        "model": "qwen/qwen3.6-plus:free",
        "messages": [
            {"role": "system", "content": "Ты AI-консультант по недвижимости в Алматы. Отвечай кратко, по делу, с аналитикой."},
            {"role": "user", "content": user_input},
        ],
        "include_reasoning": False,
    }

    response = requests.post(url, headers=headers, json=data, timeout=60)
    try:
        result = response.json()
    except Exception:
        return jsonify({"answer": f"OpenRouter HTTP {response.status_code}: {response.text[:400]}"})

    if result.get("error"):
        e = result["error"]
        msg = e.get("message", str(e)) if isinstance(e, dict) else str(e)
        code = e.get("code", response.status_code) if isinstance(e, dict) else response.status_code
        extra = " Проверь ключ на openrouter.ai/keys." if (response.status_code == 401 or code == 401) else ""
        return jsonify({"answer": f"OpenRouter ({code}): {msg}.{extra}"})

    try:
        answer = result["choices"][0]["message"]["content"]
        if not answer:
            answer = result["choices"][0]["message"].get("reasoning", "Нет ответа")
    except Exception:
        answer = f"Ошибка разбора: {result}"

    return jsonify({"answer": answer})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/style.css")
def style_css():
    return send_from_directory(_PUBLIC, "style.css")


if __name__ == "__main__":
    app.run(port=5000, debug=True)
