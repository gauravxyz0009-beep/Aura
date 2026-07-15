import requests
import time
import sqlite3
from datetime import datetime, timedelta
from flask import Flask
import threading

BOT_TOKEN = "8914784117:AAGbEGulg9rKF25cmMYedyAJlBaZjIkZy5Q"
ADMIN_ID = 8877443750

API = f"https://api.telegram.org/bot{BOT_TOKEN}/"

USER_FILE = "users.json"
DB_FILE = "lectures.db"

offset = 0
admin_state = {}   # {chat_id: key}

app = Flask(__name__)

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS lectures (
                    key TEXT PRIMARY KEY,
                    name TEXT,
                    time TEXT,
                    link TEXT)''')
    conn.commit()
    conn.close()

def save_lecture(key, name, time_str, link=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO lectures VALUES (?, ?, ?, ?)", 
              (key, name, time_str, link))
    conn.commit()
    conn.close()

def get_lecture(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM lectures WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"name": row[1], "time": row[2], "link": row[3]}
    return None

def default_lectures():
    lectures = [
        ("mr", "Physics by MR Sir", "08:47", ""),
        ("saleem", "Physics by Saleem Sir", "08:47", ""),
        ("sudhanshu", "Physical Chemistry by Sudhanshu Sir", "11:03", ""),
        ("amit", "Physical Chemistry by Amit Sir", "11:03", ""),
        ("bio1", "Biology Live 1", "13:20", ""),
        ("bio2", "Biology Live 2", "13:20", "")
    ]
    for lec in lectures:
        save_lecture(*lec)

init_db()
if not get_lecture("mr"):   # Check if data exists
    default_lectures()

# ---------------- FILE FUNCTIONS (Users) ----------------

def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def create_user(user_id):
    users = load_json(USER_FILE)
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "credits": 7,
            "lectures": 0,
            "streak": 1,
            "last_claim": "",
            "last_day": str(datetime.now().date())
        }
        save_json(USER_FILE, users)

# ---------------- TELEGRAM ----------------

def send_message(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["reply_markup"] = {"inline_keyboard": keyboard}
    requests.post(API + "sendMessage", json=data)

def get_updates():
    global offset
    r = requests.get(API + "getUpdates", params={"offset": offset, "timeout": 30})
    return r.json().get("result", [])

# ---------------- DASHBOARD & FUNCTIONS ----------------

def dashboard(chat_id):
    keyboard = [
        [{"text": "📘 Physics Live Lec", "callback_data": "physics"}],
        [{"text": "🧪 Physical Chemistry Live", "callback_data": "chemistry"}],
        [{"text": "🧬 Biology Live Lec", "callback_data": "biology"}],
        [{"text": "📊 Study Tracker", "callback_data": "tracker"}],
        [{"text": "🎁 Daily Free Credit", "callback_data": "claim"}, {"text": "💳 My Credits", "callback_data": "credits"}],
        [{"text": "👤 Contact Admin", "url": "https://t.me/gaurav0247"}]
    ]
    send_message(chat_id, "🔥 Welcome to GxNOVaa\n\nThis bot is made by @gaurav0247\n\nSelect Option 👇", keyboard)

def use_credit(user_id):
    users = load_json(USER_FILE)
    uid = str(user_id)
    if uid not in users:
        create_user(user_id)
        users = load_json(USER_FILE)
    if users[uid]["credits"] <= 0:
        return False
    users[uid]["credits"] -= 1
    users[uid]["lectures"] += 1
    save_json(USER_FILE, users)
    return True

def show_credits(user_id):
    users = load_json(USER_FILE)
    data = users.get(str(user_id), {})
    return f"💳 My Credits\n\n⭐ Available Credits: {data.get('credits', 0)}\n📚 Lectures Watched: {data.get('lectures', 0)}"

def claim_daily(user_id):
    users = load_json(USER_FILE)
    uid = str(user_id)
    now = datetime.now()
    last = users[uid].get("last_claim")
    if last and (now - datetime.fromisoformat(last)) < timedelta(hours=24):
        return False
    users[uid]["credits"] += 4
    users[uid]["last_claim"] = now.isoformat()
    save_json(USER_FILE, users)
    return True

def study_tracker(user_id):
    users = load_json(USER_FILE)
    data = users.get(str(user_id), {})
    return f"📊 Study Tracker\n\n📚 Completed Lectures: {data.get('lectures', 0)}\n🔥 Streak: {data.get('streak', 1)} Days\n⭐ Credits: {data.get('credits', 0)}"

def open_lecture(user_id, key):
    lec = get_lecture(key)
    if not lec:
        return "❌ Invalid Lecture"
    now = datetime.now().strftime("%H:%M")
    if now < lec["time"]:
        return f"⏳ Class abhi start nahi hui\n\n{lec['name']}\n⏰ Time: {lec['time']}"
    if not lec.get("link"):
        return "⚠️ Lecture link not added yet\n\nAdmin will update soon."
    if use_credit(user_id):
        return f"🔴 LIVE NOW\n\n{lec['name']}\n\n▶️ Watch Lecture:\n{lec['link']}"
    return "❌ Credits khatam ho gaye\n\n🎁 Daily Free Credit claim karein"

def is_admin(user_id):
    return user_id == ADMIN_ID

def admin_panel(chat_id):
    keyboard = [
        [{"text": "📊 Bot Stats", "callback_data": "stats"}],
        [{"text": "💳 Add Credit", "callback_data": "admin_credit"}],
        [{"text": "🔗 Update Link", "callback_data": "admin_link"}]
    ]
    send_message(chat_id, "⚙️ GxNOVaa Admin Panel", keyboard)

def update_lecture_link(key, new_link):
    lec = get_lecture(key)
    if lec:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE lectures SET link=? WHERE key=?", (new_link.strip(), key))
        conn.commit()
        conn.close()
        return f"✅ Link Updated Successfully!\n\n{lec['name']}"
    return "❌ Invalid Key"

# ---------------- MAIN BOT ----------------

def run_bot():
    global offset
    while True:
        try:
            updates = get_updates()
            for update in updates:
                offset = update["update_id"] + 1

                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "").strip()

                    if text == "/start":
                        create_user(chat_id)
                        dashboard(chat_id)

                    elif text == "/admin" and is_admin(chat_id):
                        admin_panel(chat_id)

                    elif is_admin(chat_id) and chat_id in admin_state:
                        key = admin_state.pop(chat_id)
                        result = update_lecture_link(key, text)
                        send_message(chat_id, result)
                        admin_panel(chat_id)

                elif "callback_query" in update:
                    query = update["callback_query"]
                    chat_id = query["message"]["chat"]["id"]
                    data = query["data"]

                    if data == "physics":
                        kb = [[{"text":"⚡ MR Sir","callback_data":"mr"}], [{"text":"🔥 Saleem Sir","callback_data":"saleem"}]]
                        send_message(chat_id, "📘 Physics Live Lec\n\nSelect Teacher 👇", kb)
                    elif data == "chemistry":
                        kb = [[{"text":"Sudhanshu Sir","callback_data":"sudhanshu"}], [{"text":"Amit Sir","callback_data":"amit"}]]
                        send_message(chat_id, "🧪 Physical Chemistry Live Lec\n\nSelect Teacher 👇", kb)
                    elif data == "biology":
                        kb = [[{"text":"Biology Live 1","callback_data":"bio1"}], [{"text":"Biology Live 2","callback_data":"bio2"}]]
                        send_message(chat_id, "🧬 Biology Live Lec\n\nSelect Option 👇", kb)

                    elif data in ["mr", "saleem", "sudhanshu", "amit", "bio1", "bio2"]:
                        send_message(chat_id, open_lecture(chat_id, data))

                    elif data == "credits":
                        send_message(chat_id, show_credits(chat_id))
                    elif data == "claim":
                        msg_text = "🎉 Daily Reward Claimed!\n\n+4 Credits Added" if claim_daily(chat_id) else "⏳ Already Claimed\n\nNext claim after 24 hours"
                        send_message(chat_id, msg_text)
                    elif data == "tracker":
                        send_message(chat_id, study_tracker(chat_id))

                    # Admin
                    elif is_admin(chat_id):
                        if data == "admin_link":
                            kb = [
                                [{"text": "⚡ MR Sir Physics", "callback_data": "edit_mr"}],
                                [{"text": "🔥 Saleem Sir Physics", "callback_data": "edit_saleem"}],
                                [{"text": "🧪 Sudhanshu Sir Chem", "callback_data": "edit_sudhanshu"}],
                                [{"text": "🧪 Amit Sir Chem", "callback_data": "edit_amit"}],
                                [{"text": "🧬 Biology Live 1", "callback_data": "edit_bio1"}],
                                [{"text": "🧬 Biology Live 2", "callback_data": "edit_bio2"}]
                            ]
                            send_message(chat_id, "🔗 Kis teacher ka link update karna hai?", kb)

                        elif data.startswith("edit_"):
                            key = data.replace("edit_", "")
                            admin_state[chat_id] = key
                            send_message(chat_id, f"📌 Ab naya link bhejo for: **{key}**\n\nDirect link paste kar do.")

                        elif data == "stats":
                            send_message(chat_id, "📊 Bot Stats - Coming Soon")

        except Exception as e:
            print("Error:", e)
            time.sleep(5)

@app.route('/')
def home():
    return "GxNOVaa Bot is Running ✅"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host="0.0.0.0", port=10000)
