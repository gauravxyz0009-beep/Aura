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
        requests.post(url, json=payload, timeout=10)
    except: pass

# ====================== MAIN BOT ======================
def main():
    print("✅ Bot Started with Phone + Aadhaar Lookup")
    offset = 0
    while True:
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            if response.status_code != 200:
                time.sleep(5)
                continue

            data = response.json()
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
                free = user_data["free_uses"]
                credits = user_data["credits"]

                # ==================== ADMIN ====================
                if is_admin(chat_id):
                    if text in ["/dashboard", "/admin"]:
                        users = load_users()
                        msg_text = f"📊 **Admin Dashboard**\nTotal Users: {len(users)}\n\n"
                        for uid, d in list(users.items())[:25]:
                            msg_text += f"• `{uid}` | Free: {d.get('free_uses',0)} | Credits: {d.get('credits',0)}\n"
                        send_message(chat_id, msg_text, parse_mode="Markdown")

                    elif text.startswith("/addcredits"):
                        try:
                            _, uid, amt = text.split()
                            update_user_data(int(uid), credits=int(amt))
                            send_message(chat_id, f"✅ {amt} credits added to {uid}")
                        except:
                            send_message(chat_id, "Format: /addcredits <user_id> <amount>")

                # ==================== USER MENU ====================
                if text == "/start":
                    keyboard = {
                        "keyboard": [
                            ["📱 Phone Lookup"],
                            ["🆔 Aadhaar Lookup"],
                            ["👥 Invite Friends", "📞 Contact Admin"]
                        ],
                        "resize_keyboard": True
                    }
                    welcome = (
                        f"👋 Welcome to Lookup Bot!\n\n"
                        f"🎁 Free Uses: **{free}**\n"
                        f"💰 Credits: **{credits}**\n\n"
                        "2 Referrals = 1 Free Credit"
                    )
                    send_message(chat_id, welcome, reply_markup=keyboard, parse_mode="Markdown")

                elif text in ["📱 Phone Lookup", "🆔 Aadhaar Lookup"]:
                    lookup_type = "phone" if text == "📱 Phone Lookup" else "aadhaar"
                    prompt = "10 digit mobile number" if lookup_type == "phone" else "12 digit Aadhaar number"
                    if free > 0 or credits > 0:
                        send_message(chat_id, f"🔍 Send {prompt}:")
                    else:
                        send_message(chat_id, "❌ No balance left.\nContact Admin.")

                elif text == "👥 Invite Friends":
                    ref_link = f"https://t.me/{BOT_TOKEN.split(':')[0]}?start={chat_id}"
                    send_message(chat_id, f"🔗 Your Referral Link:\n{ref_link}\n\n2 Referrals = 1 Credit")

                elif text == "📞 Contact Admin":
                    send_message(chat_id, f"👨‍💼 Contact Admin:\n{ADMIN_USERNAME}")

                # ==================== HANDLE LOOKUP INPUT ====================
                elif text.isdigit():
                    if len(text) == 10:
                        lookup_type = "number"
                        display_type = "Phone"
                    elif len(text) == 12:
                        lookup_type = "adhaar"
                        display_type = "Aadhaar"
                    else:
                        send_message(chat_id, "❌ Invalid number. 10 digit phone ya 12 digit Aadhaar bhejein.")
                        continue

                    if free <= 0 and credits <= 0:
                        send_message(chat_id, "❌ Balance khatam ho gaya. Admin se contact karein.")
                        continue

                    # Show "Please Wait" message
                    wait_msg = send_message(chat_id, "⏳ Please wait... Searching data (10 seconds)")
                    
                    try:
                        # Simulate 10 second wait (realistic processing time)
                        time.sleep(8)  

                        api_url = f"{EXTERNAL_API_BASE}?type={lookup_type}&{'mobile' if lookup_type=='number' else 'adhaar'}={text}"
                        resp = requests.get(api_url, timeout=20)
                        
                        if resp.status_code != 200:
                            send_message(chat_id, "❌ API Error. Try again later.")
                            continue

                        api_data = resp.json()

                        # Check if data is empty or not found
                        if not api_data or api_data == {} or (isinstance(api_data, dict) and len(api_data) <= 1):
                            send_message(chat_id, "❌ No Data Found for this number/Aadhaar.")
                        else:
                            formatted = json.dumps(api_data, indent=2, ensure_ascii=False)
                            send_message(chat_id, f"✅ {display_type} Lookup Result:\n\n<pre>{formatted}</pre>", parse_mode="HTML")

                        # Deduct balance
                        if free > 0:
                            update_user_data(chat_id, free_uses=free-1)
                        else:
                            update_user_data(chat_id, credits=credits-1)

                    except Exception:
                        send_message(chat_id, "❌ Lookup failed. Please try again.")

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("Bot Stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
