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
        users[uid] = {
            "free_uses": 2,
            "credits": 0,
            "referrals": 0,
            "referred_by": None
        }
        save_users(users)
    return users[uid]

def update_user_data(user_id, **kwargs):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"free_uses": 2, "credits": 0, "referrals": 0, "referred_by": None}
    
    for key, value in kwargs.items():
        if key in users[uid]:
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
    print("✅ Bot Started with Admin Panel + Referral System")
    offset = 0
    while True:
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30, "allowed_updates": ["message"]},
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

                # ==================== ADMIN COMMANDS ====================
                if is_admin(chat_id):
                    if text == "/dashboard" or text == "/admin":
                        users = load_users()
                        total_users = len(users)
                        text_msg = f"📊 **Admin Dashboard**\n\n"
                        text_msg += f"Total Users: {total_users}\n"
                        text_msg += f"Admin: {ADMIN_USERNAME}\n\n"
                        text_msg += "Users List:\n"
                        
                        for uid, data in list(users.items())[:30]:  # Show max 30
                            free = data.get("free_uses", 0)
                            cred = data.get("credits", 0)
                            ref = data.get("referrals", 0)
                            text_msg += f"• `{uid}` | Free: {free} | Credits: {cred} | Ref: {ref}\n"
                        
                        if total_users > 30:
                            text_msg += f"\n... and {total_users-30} more users"
                        
                        send_message(chat_id, text_msg, parse_mode="Markdown")

                    elif text.startswith("/addcredits"):
                        try:
                            _, target_id, amount = text.split()
                            target_id = int(target_id)
                            amount = int(amount)
                            update_user_data(target_id, credits=amount)
                            send_message(chat_id, f"✅ {amount} credits added to user {target_id}")
                            send_message(target_id, f"🎁 Admin ne aapko {amount} credits diye hain!")
                        except:
                            send_message(chat_id, "❌ Format: /addcredits <user_id> <amount>")

                # ==================== NORMAL USERS ====================
                user_data = get_user_data(chat_id)
                free = user_data["free_uses"]
                credits = user_data["credits"]

                if text == "/start":
                    keyboard = {
                        "keyboard": [
                            ["📱 Phone Lookup"],
                            ["👥 Invite Friends", "📞 Contact Admin"]
                        ],
                        "resize_keyboard": True
                    }
                    welcome = (
                        f"👋 Welcome!\n\n"
                        f"🎁 Free Uses Left: **{free}**\n"
                        f"💰 Credits: **{credits}**\n\n"
                        f"Invite friends to earn more credits!\n"
                        f"2 Referrals = 1 Free Credit"
                    )
                    send_message(chat_id, welcome, reply_markup=keyboard, parse_mode="Markdown")

                elif text == "📱 Phone Lookup":
                    if free > 0 or credits > 0:
                        send_message(chat_id, "📞 Send 10 digit mobile number:")
                    else:
                        send_message(chat_id, "❌ No free uses or credits left.\nContact Admin to buy credits.")

                elif text == "👥 Invite Friends":
                    ref_link = f"https://t.me/{BOT_TOKEN.split(':')[0]}?start={chat_id}"
                    send_message(chat_id, f"🔗 Share this link to invite friends:\n\n{ref_link}\n\n2 Referrals = 1 Credit")

                elif text == "📞 Contact Admin":
                    send_message(chat_id, f"👨‍💼 Contact Admin:\n{ADMIN_USERNAME}")

                # Handle Phone Number
                elif text.isdigit() and len(text) == 10:
                    if free <= 0 and credits <= 0:
                        send_message(chat_id, "❌ Credits khatam ho gaye. Admin se contact karein.")
                        continue

                    # API Call
                    try:
                        api_url = f"{EXTERNAL_API_BASE}?type=number&mobile={text}"
                        resp = requests.get(api_url, timeout=15)
                        data = resp.json()
                        result = json.dumps(data, indent=2, ensure_ascii=False)
                        
                        send_message(chat_id, f"✅ Result for {text}:\n\n<pre>{result}</pre>", parse_mode="HTML")

                        # Deduct usage
                        if free > 0:
                            update_user_data(chat_id, free_uses=free-1)
                        else:
                            update_user_data(chat_id, credits=credits-1)

                    except:
                        send_message(chat_id, "❌ Lookup failed. Try again.")

                # Referral Check (when someone starts with ref link)
                elif text.startswith("/start ") and not is_admin(chat_id):
                    try:
                        referrer_id = int(text.split()[1])
                        if referrer_id != chat_id:  # Avoid self-refer
                            ref_data = get_user_data(referrer_id)
                            new_ref = ref_data.get("referrals", 0) + 1
                            update_user_data(referrer_id, referrals=new_ref)
                            
                            if new_ref % 2 == 0:
                                update_user_data(referrer_id, credits=ref_data.get("credits", 0) + 1)
                                send_message(referrer_id, "🎉 2 Referrals complete! +1 Credit added.")
                    except:
                        pass

                else:
                    send_message(chat_id, "❌ Invalid command. Use buttons.")

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("Bot Stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
