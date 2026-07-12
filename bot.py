import requests
import json
import time
import os

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
        users[uid] = {"free_uses": 2, "credits": 0, "referrals": 0, "referred_by": None}
        save_users(users)
    return users[uid]

def update_user_data(user_id, **kwargs):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"free_uses": 2, "credits": 0, "referrals": 0, "referred_by": None}
    for key, value in kwargs.items():
        users[uid][key] = value
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
    print("✅ Full Advanced Lookup Bot Started")
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

                # ADMIN
                if is_admin(chat_id):
                    if text in ["/dashboard", "/admin"]:
                        users = load_users()
                        txt = f"📊 **Admin Dashboard**\nTotal Users: {len(users)}\n\n"
                        for uid, d in list(users.items())[:30]:
                            txt += f"• `{uid}` | Free:{d.get('free_uses',0)} | Cred:{d.get('credits',0)}\n"
                        send_message(chat_id, txt, parse_mode="Markdown")

                    elif text.startswith("/addcredits"):
                        try:
                            _, uid, amt = text.split()
                            update_user_data(int(uid), credits=int(amt))
                            send_message(chat_id, f"✅ {amt} credits added to {uid}")
                        except:
                            send_message(chat_id, "Usage: /addcredits <user_id> <amount>")

                # MAIN MENU
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
                    send_message(chat_id, f"👋 Welcome to Advanced Lookup Bot!\n\n🎁 Free Uses: **{free}**\n💰 Credits: **{credits}**", reply_markup=keyboard, parse_mode="Markdown")

                # Button Handlers
                elif text in ["📱 Phone", "📱 Adv Phone", "🆔 Aadhaar", "✉️ Gmail", "🚗 Vehicle", "🚗 Adv Vehicle", "💰 Paytm"]:
                    if free <= 0 and credits <= 0:
                        send_message(chat_id, "❌ No balance left.\nContact Admin.")
                        continue

                    if "Phone" in text:
                        send_message(chat_id, "📞 Send 10 digit mobile number:")
                    elif "Aadhaar" in text:
                        send_message(chat_id, "🆔 Send 12 digit Aadhaar number:")
                    elif "Gmail" in text:
                        send_message(chat_id, "✉️ Send Gmail address:")
                    elif "Vehicle" in text:
                        send_message(chat_id, "🚗 Send Vehicle RC Number (e.g. RJ18CF3690):")
                    elif "Paytm" in text:
                        send_message(chat_id, "💰 Send Paytm Number or Info:")

                elif text == "👥 Invite":
                    link = f"https://t.me/{BOT_TOKEN.split(':')[0]}?start={chat_id}"
                    send_message(chat_id, f"🔗 Referral Link:\n{link}\n\n2 Referrals = 1 Credit")

                elif text == "📞 Admin":
                    send_message(chat_id, f"👨‍💼 Contact Admin:\n{ADMIN_USERNAME}")

                # ==================== LOOKUP PROCESSING ====================
                elif any([text.isdigit(), "@" in text, text.replace(" ", "").isalnum()]):
                    wait_id = send_message(chat_id, "⏳ Searching data... (Max 30 sec)")

                    try:
                        # Determine type
                        if "@" in text:
                            lookup_type = "gmail"
                            param = "email"
                        elif len(text) == 10 and text.isdigit():
                            lookup_type = "number_adv" if "Adv" in str(msg.get("reply_to_message", "")) else "number"  # Simple logic
                            param = "mobile"
                        elif len(text) == 12 and text.isdigit():
                            lookup_type = "adhaar"
                            param = "adhaar"
                        elif text.isalnum() and len(text) >= 5:  # RC or Paytm
                            if any(c.isalpha() for c in text):
                                lookup_type = "vehicle_adv" if "Adv" in str(msg.get("reply_to_message", "")) else "vehicle"
                                param = "rc"
                            else:
                                lookup_type = "paytm"
                                param = "info"
                        else:
                            lookup_type = "number"
                            param = "mobile"

                        api_url = f"{EXTERNAL_API_BASE}?type={lookup_type}&{param}={text}"
                        resp = requests.get(api_url, timeout=28)

                        if resp.status_code != 200:
                            edit_message(chat_id, wait_id, "❌ Data Unavailable")
                            continue

                        api_data = resp.json()
                        data_str = str(api_data).lower()

                        if not api_data or "not found" in data_str or "no data" in data_str or len(data_str) < 40:
                            edit_message(chat_id, wait_id, "❌ Data Unavailable")
                        else:
                            formatted = json.dumps(api_data, indent=2, ensure_ascii=False)
                            result = f"✅ {lookup_type.upper()} Result:\n\n<pre>{formatted}</pre>"
                            edit_message(chat_id, wait_id, result, parse_mode="HTML")

                        # Deduct balance
                        if free > 0:
                            update_user_data(chat_id, free_uses=free-1)
                        else:
                            update_user_data(chat_id, credits=credits-1)

                    except Exception:
                        edit_message(chat_id, wait_id, "❌ Data Unavailable")

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("Bot Stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
