import os
import time
import threading
import requests
from flask import Flask
from google import genai


TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


client = genai.Client(api_key=GEMINI_API_KEY)

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Gemini Bot is running!"


def ask_gemini(text):
    try:
        print("Gemini'ga so'rov yuborilmoqda...")

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=text
        )

        print("Gemini javob berdi!")

        return response.text

    except Exception as e:
        print("GEMINI XATOSI:", e)

        return "Kechirasiz, hozir javob olishda xatolik yuz berdi."


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )


def telegram_loop():
    offset = 0

    print("Telegram bot started!")

    while True:
        try:
            response = requests.get(
                f"{TELEGRAM_URL}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 30
                },
                timeout=40
            )

            data = response.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                user_text = message.get("text")

                if not user_text:
                    continue

                chat_id = message["chat"]["id"]

                if user_text == "/start":
                    send_message(
                        chat_id,
                        "Salom! Men AI yordamchiman. Savolingizni yozing."
                    )
                    continue

                print("Foydalanuvchi:", user_text)

                answer = ask_gemini(user_text)

                send_message(chat_id, answer)

        except Exception as e:
            print("TELEGRAM XATOSI:", e)
            time.sleep(5)


def start_web_server():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )


if __name__ == "__main__":

    web_thread = threading.Thread(
        target=start_web_server,
        daemon=True
    )

    web_thread.start()

    telegram_loop()
