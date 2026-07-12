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

def get_dashboard_keyboard():
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
    print(f"✅ Bot Started | Admin: {ADMIN_ID}")

    offset = 0
    while True:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            if resp.status_code != 200:
                time.sleep(5)
                continue

            updates = resp.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "message" not in update:
                    continue

                msg = update["message"]
                chat_id = msg["chat"]["id"]
                user_id = msg["from"]["id"]
                username = msg["from"].get("username", "NoUsername")
                text = msg.get("text", "").strip().upper()

                # Initialize user
                if str(user_id) not in data["users"]:
                    data["users"][str(user_id)] = {
                        "username": username,
                        "credits": FREE_CREDITS_ON_START,
                        "searches": 0,
                        "joined": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }

                user = data["users"][str(user_id)]

                # ================== DASHBOARD / START ==================
                if text == "/START" or text == "/START START":
                    dashboard_text = f"""🔥 **MULTI LOOKUP DASHBOARD**

Welcome @{username}!

💰 **Your Credits:** {user['credits']}
📊 **Total Searches:** {user['searches']}

Choose any option below 👇"""

                    send_message(chat_id, dashboard_text, reply_markup=get_dashboard_keyboard(), parse_mode="Markdown")
                    continue

                # ================== BUTTONS ==================
                elif text == "📱 BASIC PHONE":
                    if user["credits"] <= 0:
                        send_message(chat_id, "❌ No credits left. Use Referral.")
                    else:
                        send_message(chat_id, "📞 Send 10 digit mobile number:")

                elif text == "📲 ADVANCED PHONE":
                    if user["credits"] <= 0:
                        send_message(chat_id, "❌ No credits left.")
                    else:
                        send_message(chat_id, "📲 Send 10 digit mobile number for **Advanced** Info:")

                elif text == "🆔 AADHAAR LOOKUP":
                    if user["credits"] <= 0:
                        send_message(chat_id, "❌ No credits left.")
                    else:
                        send_message(chat_id, "🆔 Send 12 digit Aadhaar number:")

                elif text == "🚗 VEHICLE INFO":
                    if user["credits"] <= 0:
                        send_message(chat_id, "❌ No credits left.")
                    else:
                        send_message(chat_id, "🚗 Send Vehicle RC Number (Example: RJ18CF3690):")

                # ================== LOOKUP LOGIC ==================
                elif text.isdigit():
                    if user["credits"] <= 0:
                        send_message(chat_id, "❌ No credits left.")
                        continue

                    user["credits"] -= 1
                    user["searches"] += 1
                    data["total_searches"] += 1

                    try:
                        if len(text) == 10:
                            api_url = f"{EXTERNAL_API_BASE}?type=number_adv&mobile={text}"
                            title = "Advanced Phone Info"
                        elif len(text) == 12:
                            api_url = f"{EXTERNAL_API_BASE}?type=adhaar&adhaar={text}"
                            title = "Aadhaar Info"
                        else:
                            continue

                        api_resp = requests.get(api_url, timeout=15)
                        result = api_resp.json()
                        formatted = json.dumps(result, indent=2, ensure_ascii=False)
                        send_message(chat_id, f"✅ {title}:\n\n<pre>{formatted}</pre>", parse_mode="HTML")

                    except:
                        send_message(chat_id, "❌ API Error. Credit refunded.")
                        user["credits"] += 1
                        user["searches"] -= 1
                        data["total_searches"] -= 1

                # Vehicle RC
                elif any(c.isalpha() for c in text) and len(text) >= 5:
                    if user["credits"] <= 0:
                        send_message(chat_id, "❌ No credits left.")
                        continue

                    user["credits"] -= 1
                    user["searches"] += 1
                    data["total_searches"] += 1

                    try:
                        api_url = f"{EXTERNAL_API_BASE}?type=vehicle&rc={text}"
                        api_resp = requests.get(api_url, timeout=15)
                        result = api_resp.json()
                        formatted = json.dumps(result, indent=2, ensure_ascii=False)
                        send_message(chat_id, f"✅ Vehicle Information:\n\n<pre>{formatted}</pre>", parse_mode="HTML")
                    except:
                        send_message(chat_id, "❌ API Error. Credit refunded.")
                        user["credits"] += 1
                        user["searches"] -= 1
                        data["total_searches"] -= 1

                # Other Options
                elif text == "💰 MY CREDITS":
                    send_message(chat_id, f"💰 **Your Credits:** {user['credits']}\n📊 Searches Done: {user['searches']}", parse_mode="Markdown")

                elif text == "👥 REFERRAL":
                    ref_link = f"https://t.me/{BOT_TOKEN.split(':')[0]}?start=ref_{user_id}"
                    send_message(chat_id, f"🔗 **Your Referral Link**\n{ref_link}\n\n2 Referrals = 1 Free Credit (Auto)")

                elif text == "📞 CONTACT ADMIN":
                    send_message(chat_id, "📞 Contact Admin → @YourAdminUsername")

                # Admin Panel
                elif text == "/ADMIN" and user_id == ADMIN_ID:
                    stats = f"""🛠 <b>ADMIN DASHBOARD</b>

Total Users: {len(data['users'])}
Total Searches: {data['total_searches']}

"""
                    for uid, u in list(data["users"].items())[:15]:
                        stats += f"• {u['username']} : {u['credits']} credits\n"
                    send_message(chat_id, stats, parse_mode="HTML")

                # Referral System
                elif text.startswith("/START REF_"):
                    referrer_id = text.split("_")[1]
                    if referrer_id != str(user_id) and referrer_id in data["users"]:
                        if "referrals" not in data:
                            data["referrals"] = {}
                        data["referrals"][str(user_id)] = referrer_id
                        count = sum(1 for v in data.get("referrals", {}).values() if v == referrer_id)
                        if count % 2 == 0:
                            data["users"][referrer_id]["credits"] += 1
                            send_message(int(referrer_id), "🎉 Congratulations! You earned 1 credit from referrals!")

                save_data(data)

            time.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
