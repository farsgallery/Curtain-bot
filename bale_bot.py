import requests

TOKEN = "1707286533:8RiZ3SLHubKYeU9qMV3WVWx2cKHuGVDIiMg"

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# تست کن
try:
    send_message("822951933", "سلام از ربات!")
    print("✅ پیام رفت!")
except Exception as e:
    print(f"❌ خطا: {e}")
