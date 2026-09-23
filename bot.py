import os
import time
import threading
import requests
from flask import Flask
from google import genai

# =========================
# SETTINGS
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Render Environment Variables'da GEMINI_MODEL bo'lmasa,
# shu qiymatdan foydalanadi.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)


# =========================
# WEB SERVER
# =========================

@app.route("/")
def home():
    return "Telegram Gemini Bot is running!"


@app.route("/health")
def health():
    return "OK"


# =========================
# GEMINI
# =========================

def ask_gemini(user_text):
    try:
        print("Gemini request:", user_text)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_text
        )

        answer = response.text

        if not answer:
            return "Gemini javob qaytarmadi."

        print("Gemini response received.")

        return answer

    except Exception as e:
        print("GEMINI ERROR:", repr(e))
        return "Kechirasiz, AI javob berishda xatolik yuz berdi."


# =========================
# TELEGRAM
# =========================

def send_message(chat_id, text):
    try:
        # Telegram bitta xabarda juda uzun matnni qabul qilmaydi.
        max_length = 4000

        for i in range(0, len(text), max_length):
            part = text[i:i + max_length]

            response = requests.post(
                f"{TELEGRAM_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": part
                },
                timeout=30
            )

            print("Telegram send status:", response.status_code)

    except Exception as e:
        print("TELEGRAM SEND ERROR:", repr(e))


# =========================
# TELEGRAM LOOP
# =========================

def telegram_loop():
    offset = 0

    print("================================")
    print("TELEGRAM BOT STARTED")
    print("================================")

    # Agar Telegram'da eski webhook qolgan bo'lsa,
    # polling ishlashi uchun uni olib tashlaymiz.
    try:
        requests.get(
            f"{TELEGRAM_URL}/deleteWebhook",
            params={"drop_pending_updates": False},
            timeout=20
        )

        print("Telegram webhook checked.")

    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))

    while True:
        try:
            response = requests.get(
                f"{TELEGRAM_URL}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": ["message"]
                },
                timeout=35
            )

            print("Telegram getUpdates:", response.status_code)

            data = response.json()

            if not data.get("ok"):
                print("TELEGRAM API ERROR:", data)
                time.sleep(5)
                continue

            for update in data.get("result", []):

                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                chat_id = message["chat"]["id"]

                user_text = message.get("text")

                if not user_text:
                    continue

                print("USER MESSAGE:", user_text)

                if user_text == "/start":
                    send_message(
                        chat_id,
                        "Salom! Men Gemini AI yordamchiman. Savolingizni yozing."
                    )
                    continue

                answer = ask_gemini(user_text)

                send_message(chat_id, answer)

        except Exception as e:
            print("TELEGRAM LOOP ERROR:", repr(e))
            time.sleep(5)


# =========================
# START
# =========================

def start_web_server():
    port = int(os.environ.get("PORT", "10000"))

    print("Starting web server on port:", port)

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
    )


if __name__ == "__main__":

    web_thread = threading.Thread(
        target=start_web_server,
        daemon=True
    )

    web_thread.start()

    telegram_loop()
