import requests
import json
import time
import os
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKEN = "8914784117:AAGbEGulg9rKF25cmMYedyAJlBaZjIkZy5Q"
ADMIN_ID = 8877443750
EXTERNAL_API_BASE = "https://nitin-apis-the-best.vercel.app/api"
DATA_FILE = "bot_data.json"
FREE_CREDITS_ON_START = 2
# ===========================================

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"users": {}, "total_searches": 0, "referrals": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_keyboard():
    return {
        "keyboard": [
            ["📱 Basic Phone", "📲 Advanced Phone"],
            ["🆔 Aadhaar Lookup", "🚗 Vehicle Info"],
            ["💰 My Credits", "👥 Referral"],
            ["📞 Contact Admin"]
        ],
        "resize_keyboard": True
    }

def main():
    data = load_data()
    print("Bot Running...")

    offset = 0
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", 
                              params={"offset": offset, "timeout": 30}, timeout=35)
            
            if resp.status_code != 200:
                time.sleep(5)
                continue

            for update in resp.json().get("result", []):
                offset = update["update_id"] + 1
                if "message" not in update:
                    continue

                msg = update["message"]
                chat_id = msg["chat"]["id"]
                user_id = msg["from"]["id"]
                text = msg.get("text", "").strip()

                # Create user if new
                user_key = str(user_id)
                if user_key not in data["users"]:
                    data["users"][user_key] = {
                        "credits": FREE_CREDITS_ON_START,
                        "searches": 0
                    }

                user = data["users"][user_key]

                # Simple Welcome
                if text == "/start":
                    welcome = """🔥 **MULTI LOOKUP BOT**

Choose any option below 👇"""
                    send_message(chat_id, welcome, reply_markup=get_keyboard(), parse_mode="Markdown")
                    continue

                # Buttons
                if user["credits"] <= 0 and text not in ["💰 My Credits", "👥 Referral", "📞 Contact Admin"]:
                    send_message(chat_id, "❌ No credits left.\nUse Referral to earn credits.")
                    continue

                if text == "📱 Basic Phone":
                    send_message(chat_id, "📞 Send 10 digit mobile number:")

                elif text == "📲 Advanced Phone":
                    send_message(chat_id, "📲 Send 10 digit mobile number for Advanced Info:")

                elif text == "🆔 Aadhaar Lookup":
                    send_message(chat_id, "🆔 Send 12 digit Aadhaar number:")

                elif text == "🚗 Vehicle Info":
                    send_message(chat_id, "🚗 Send Vehicle RC Number (e.g. RJ18CF3690):")

                # Number Search
                elif text.replace(" ", "").isdigit():
                    num = text.replace(" ", "")
                    if len(num) not in [10, 12]:
                        send_message(chat_id, "❌ Invalid number.")
                        continue

                    user["credits"] -= 1
                    user["searches"] += 1
                    data["total_searches"] += 1

                    try:
                        if len(num) == 10:
                            api_url = f"{EXTERNAL_API_BASE}?type=number_adv&mobile={num}"
                            title = "Advanced Phone"
                        else:
                            api_url = f"{EXTERNAL_API_BASE}?type=adhaar&adhaar={num}"
                            title = "Aadhaar"

                        r = requests.get(api_url, timeout=15)
                        result = r.json()
                        formatted = json.dumps(result, indent=2, ensure_ascii=False)
                        send_message(chat_id, f"✅ {title} Result:\n\n<pre>{formatted}</pre>", parse_mode="HTML")
                    except:
                        send_message(chat_id, "❌ API Error.")
                        user["credits"] += 1   # refund
                        user["searches"] -= 1
                        data["total_searches"] -= 1

                # Vehicle
                elif len(text) >= 5 and any(c.isalpha() for c in text):
                    user["credits"] -= 1
                    user["searches"] += 1
                    data["total_searches"] += 1

                    try:
                        api_url = f"{EXTERNAL_API_BASE}?type=vehicle&rc={text.upper()}"
                        r = requests.get(api_url, timeout=15)
                        result = r.json()
                        formatted = json.dumps(result, indent=2, ensure_ascii=False)
                        send_message(chat_id, f"✅ Vehicle Result:\n\n<pre>{formatted}</pre>", parse_mode="HTML")
                    except:
                        send_message(chat_id, "❌ API Error or Invalid RC number.")
                        user["credits"] += 1
                        user["searches"] -= 1
                        data["total_searches"] -= 1

                elif text == "💰 My Credits":
                    send_message(chat_id, f"💰 Your Credits: **{user['credits']}**", parse_mode="Markdown")

                elif text == "👥 Referral":
                    link = f"https://t.me/{BOT_TOKEN.split(':')[0]}?start=ref_{user_id}"
                    send_message(chat_id, f"🔗 Your Referral Link:\n{link}\n\n2 referrals = 1 credit")

                elif text == "📞 Contact Admin":
                    send_message(chat_id, "Contact Admin: @YourAdminUsername")

                # ADMIN ONLY
                elif text.lower() == "/admin" and user_id == ADMIN_ID:
                    stats = f"""🛠 **ADMIN PANEL**

Total Users: {len(data['users'])}
Total Searches: {data['total_searches']}

"""
                    for uid, u in list(data["users"].items())[:15]:
                        stats += f"{uid}: {u['credits']} credits\n"
                    send_message(chat_id, stats, parse_mode="Markdown")

                save_data(data)

            time.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
