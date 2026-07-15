import requests
import time
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask
import threading

BOT_TOKEN = "8914784117:AAGbEGulg9rKF25cmMYedyAJlBaZjIkZy5Q"
ADMIN_ID = 8877443750

API = f"https://api.telegram.org/bot{BOT_TOKEN}/"

USER_FILE = "users.json"
DB_FILE = "lectures.db"

offset = 0
admin_state = {}

app = Flask(__name__)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS lectures 
                 (key TEXT PRIMARY KEY, name TEXT, time TEXT, link TEXT)''')
    conn.commit()
    conn.close()

def save_lecture(key, name, time_str, link=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO lectures VALUES (?,?,?,?)", (key, name, time_str, link))
    conn.commit()
    conn.close()

def get_lecture(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM lectures WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return {"name": row[1], "time": row[2], "link": row[3]} if row else None

def default_lectures():
    data = [
        ("mr", "Physics by MR Sir", "08:47", ""),
        ("saleem", "Physics by Saleem Sir", "08:47", ""),
        ("sudhanshu", "Physical Chemistry by Sudhanshu Sir", "11:03", ""),
        ("amit", "Physical Chemistry by Amit Sir", "11:03", ""),
        ("bio1", "Biology Live 1", "13:20", ""),
        ("bio2", "Biology Live 2", "13:20", "")
    ]
    for item in data:
        save_lecture(*item)

init_db()
if not get_lecture("mr"):
    default_lectures()

# ---------------- JSON FUNCTIONS ----------------
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
        users[uid] = {"credits": 7, "lectures": 0, "streak": 1, "last_claim": "", "last_day": str(datetime.now().date())}
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

# ---------------- FUNCTIONS ----------------
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
    return f"💳 My Credits\n\n⭐ Credits: {data.get('credits',0)}\n📚 Lectures: {data.get('lectures',0)}"

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
    return f"📊 Study Tracker\n\n📚 Lectures: {data.get('lectures',0)}\n🔥 Streak: {data.get('streak',1)}\n⭐ Credits: {data.get('credits',0)}"

def open_lecture(user_id, key):
    lec = get_lecture(key)
    if not lec:
        return "❌ Invalid Lecture"
    now = datetime.now().strftime("%H:%M")
    if now < lec["time"]:
        return f"⏳ Class abhi start nahi hui\n\n{lec['name']}\n⏰ Time: {lec['time']}"
    if not lec["link"]:
        return "⚠️ Lecture link not added yet"
    if use_credit(user_id):
        return f"🔴 LIVE NOW\n\n{lec['name']}\n\n▶️ {lec['link']}"
    return "❌ No Credits Left"

def is_admin(user_id):
    return user_id == ADMIN_ID

def admin_panel(chat_id):
    kb = [
        [{"text": "📊 Bot Stats", "callback_data": "stats"}],
        [{"text": "💳 Add Credit", "callback_data": "admin_credit"}],
        [{"text": "🔗 Update Link", "callback_data": "admin_link"}]
    ]
    send_message(chat_id, "⚙️ Admin Panel", kb)

# ---------------- MAIN LOOP ----------------
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
                        result = update_lecture_link(key, text)   # function neeche hai
                        send_message(chat_id, result)
                        admin_panel(chat_id)

                elif "callback_query" in update:
                    data = update["callback_query"]["data"]
                    chat_id = update["callback_query"]["message"]["chat"]["id"]

                    if data == "physics":
                        kb = [[{"text":"MR Sir","callback_data":"mr"}], [{"text":"Saleem Sir","callback_data":"saleem"}]]
                        send_message(chat_id, "Physics - Select Teacher", kb)
                    # ... baaki callbacks (chemistry, biology, etc.)

                    # (Baaki callbacks ke liye mujhe batao agar error aaye)

        except:
            time.sleep(5)

def update_lecture_link(key, new_link):
    lec = get_lecture(key)
    if lec:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE lectures SET link=? WHERE key=?", (new_link, key))
        conn.commit()
        conn.close()
        return f"✅ Updated: {lec['name']}"
    return "❌ Error"

@app.route('/')
def home():
    return "Bot is Running"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host="0.0.0.0", port=10000)
