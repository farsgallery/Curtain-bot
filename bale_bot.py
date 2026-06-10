import requests

TOKEN = "توکن_رابات_ت_اینجا_بذار"

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# تست کن
try:
    send_message("آیدی_چت_خودت", "سلام از ربات!")
    print("✅ پیام رفت!")
except Exception as e:
    print(f"❌ خطا: {e}")
