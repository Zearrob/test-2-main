from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

API_KEY = "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"


@app.route("/ai", methods=["POST"])
def ai():
    user_input = request.json.get("message")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",   # ← обязательно для free-моделей
        "X-Title": "Almaty DataLab"
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

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    # Логируем весь ответ — смотри в терминале Flask
    print("STATUS:", response.status_code)
    print("RESPONSE:", result)

    try:
        answer = result["choices"][0]["message"]["content"]
        if not answer:  # ← бывает пустым у reasoning-моделей
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