import os
import json
import anthropic
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ALLOWED_USER_IDS_STR = os.environ.get("ALLOWED_USER_IDS", "")

ALLOWED_USER_IDS = set()
if ALLOWED_USER_IDS_STR:
    for uid in ALLOWED_USER_IDS_STR.split(","):
        uid = uid.strip()
        if uid:
            ALLOWED_USER_IDS.add(int(uid))

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def handler(request):
    if request.method != "POST":
        return {"statusCode": 200, "body": "OK"}

    try:
        body = request.body
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        update = json.loads(body)
    except Exception as e:
        return {"statusCode": 400, "body": str(e)}

    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return {"statusCode": 200, "body": "OK"}

    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        send_message(chat_id, "Sorry, you are not authorized to use this bot.")
        return {"statusCode": 200, "body": "OK"}

    if text == "/start":
        send_message(chat_id, "Hello! I am a Claude AI bot. Send me any message and I will respond.")
        return {"statusCode": 200, "body": "OK"}

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": text}]
        )
        reply = response.content[0].text
    except Exception as e:
        reply = f"Error: {str(e)}"

    send_message(chat_id, reply)
    return {"statusCode": 200, "body": "OK"}
