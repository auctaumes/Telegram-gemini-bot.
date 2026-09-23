import os
import time
import requests
from google import genai

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def ask_gemini(user_message):
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=user_message
    )
    return response.text


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )


def main():
    offset = 0

    print("Bot ishga tushdi!")

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

                answer = ask_gemini(user_text)

                send_message(chat_id, answer)

        except Exception as e:
            print("Xatolik:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
