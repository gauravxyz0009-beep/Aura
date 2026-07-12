import requests
import json
import time
import os
from datetime import datetime

# ========================= CONFIG =========================
BOT_TOKEN = "8914784117:AAGbEGulg9rKF25cmMYedyAJlBaZjIkZy5Q"
ADMIN_ID = 8877443750
ADMIN_USERNAME = "@gaurav0247"
EXTERNAL_API_BASE = "https://nitin-apis-the-best.vercel.app/api"
DATA_FILE = "users.json"
# ========================================================

def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_user_data(user_id):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"free_uses": 2, "credits": 0, "referrals": 0, "referred_by": None, "history": []}
        save_users(users)
    return users[uid]

def update_user_data(user_id, **kwargs):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"free_uses": 2, "credits": 0, "referrals": 0, "referred_by": None, "history": []}
    for key, value in kwargs.items():
        users[uid][key] = value
    save_users(users)

def add_to_history(user_id, search_type, query):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"free_uses": 2, "credits": 0, "referrals": 0, "referred_by": None, "history": []}
    
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": search_type,
        "query": query
    }
    if "history" not in users[uid]:
        users[uid]["history"] = []
    users[uid]["history"].append(entry)
    if len(users[uid]["history"]) > 50:  # Keep last 50 searches
        users[uid]["history"] = users[uid]["history"][-50:]
    save_users(users)

def is_admin(chat_id):
    return chat_id == ADMIN_ID

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if parse_mode: payload["parse_mode"] = parse_mode
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("result", {}).get("message_id")
    except:
        return None

def edit_message(chat_id, message_id, text, parse_mode=None):
    if not message_id: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if parse_mode: payload["parse_mode"] = parse_mode
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

# ====================== MAIN BOT ======================
def main():
    print("✅ Advanced Bot with Admin Panel Started")
    offset = 0
    while True:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 25, "allowed_updates": ["message"]},
                timeout=30
            )
            if resp.status_code != 200:
                time.sleep(5)
                continue

            data = resp.json()
            if not data.get("ok"):
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                if "message" not in update: continue

                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()

                user_data = get_user_data(chat_id)
                free = user_data.get("free_uses", 0)
                credits = user_data.get("credits", 0)

                # ==================== ADMIN PANEL ====================
                if is_admin(chat_id):
                    if text == "/start" or text == "🔧 Admin Panel":
                        keyboard = {
                            "keyboard": [
                                ["🔧 Admin Panel", "📊 Dashboard"],
                                ["📱 Phone", "📱 Adv Phone"],
                                ["🆔 Aadhaar", "✉️ Gmail"],
                                ["🚗 Vehicle", "🚗 Adv Vehicle"],
                                ["💰 Paytm", "👥 Invite", "📞 Admin"]
                            ],
                            "resize_keyboard": True
                        }
                        send_message(chat_id, "🔧 **Admin Panel Opened**\nUse buttons below.", reply_markup=keyboard, parse_mode="Markdown")
                        continue

                    if text in ["/dashboard", "📊 Dashboard"]:
                        users = load_users()
                        total = len(users)
                        txt = f"🔥 **ADMIN DASHBOARD** 🔥\n\n"
                        txt += f"👥 Total Users: **{total}**\n"
                        txt += f"🕒 Last Updated: {datetime.now().strftime('%H:%M:%S')}\n\n"
                        txt += "━━━━━━━━━━━━━━━━━━\n\n"

                        for uid, d in list(users.items())[:15]:
                            history_count = len(d.get("history", []))
                            txt += f"👤 `{uid}` | Free: **{d.get('free_uses',0)}** | Credits: **{d.get('credits',0)}** | Searches: **{history_count}**\n"
                        send_message(chat_id, txt, parse_mode="Markdown")
                        continue

                    elif text.startswith("/addcredits"):
                        try:
                            _, uid, amt = text.split()
                            current = get_user_data(int(uid)).get("credits", 0)
                            update_user_data(int(uid), credits=current + int(amt))
                            send_message(chat_id, f"✅ {amt} credits added to {uid}")
                        except:
                            send_message(chat_id, "Usage: /addcredits <user_id> <amount>")

                    elif text.startswith("/removecredits"):
                        try:
                            _, uid, amt = text.split()
                            current = get_user_data(int(uid)).get("credits", 0)
                            new_amt = max(0, current - int(amt))
                            update_user_data(int(uid), credits=new_amt)
                            send_message(chat_id, f"✅ {amt} credits removed from {uid}. New: {new_amt}")
                        except:
                            send_message(chat_id, "Usage: /removecredits <user_id> <amount>")

                # ==================== NORMAL MENU ====================
                if text == "/start":
                    keyboard = {
                        "keyboard": [
                            ["📱 Phone", "📱 Adv Phone"],
                            ["🆔 Aadhaar", "✉️ Gmail"],
                            ["🚗 Vehicle", "🚗 Adv Vehicle"],
                            ["💰 Paytm", "👥 Invite", "📞 Admin"]
                        ],
                        "resize_keyboard": True
                    }
                    send_message(chat_id, f"👋 Welcome!\n\n🎁 Free Uses: **{free}**\n💰 Credits: **{credits}**", reply_markup=keyboard, parse_mode="Markdown")

                elif text in ["📱 Phone", "📱 Adv Phone", "🆔 Aadhaar", "✉️ Gmail", "🚗 Vehicle", "🚗 Adv Vehicle", "💰 Paytm"]:
                    if free <= 0 and credits <= 0 and not is_admin(chat_id):
                        send_message(chat_id, "❌ No balance left.\nContact Admin.")
                        continue
                    prompts = { ... }  # same as before
                    # (code shortened for brevity - full prompts same as previous version)
                    send_message(chat_id, f"🔍 Send details for {text}:")

                # Search History Logging & Lookup (same logic as before with add_to_history)
                elif any([text.isdigit(), "@" in text, len(text) > 5]):
                    if free <= 0 and credits <= 0 and not is_admin(chat_id):
                        send_message(chat_id, "❌ No balance left.\nContact Admin.")
                        continue

                    # ... (same lookup logic as previous version)
                    # After successful search:
                    # add_to_history(chat_id, lookup_type, text)

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("Bot Stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
