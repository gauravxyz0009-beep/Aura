import requests
import time
import json
from datetime import datetime, timedelta

BOT_TOKEN = "8914784117:AAGbEGulg9rKF25cmMYedyAJlBaZjIkZy5Q"
ADMIN_ID = 8877443750

API = f"https://api.telegram.org/bot{BOT_TOKEN}/"

USER_FILE = "users.json"
LECTURE_FILE = "lectures.json"

offset = 0


# ---------------- DATABASE ----------------

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


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

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = {
            "inline_keyboard": keyboard
        }

    requests.post(
        API + "sendMessage",
        json=data
    )


def get_updates():

    global offset

    r = requests.get(
        API + "getUpdates",
        params={
            "offset": offset,
            "timeout": 30
        }
    )

    return r.json().get("result", [])


# ---------------- DASHBOARD ----------------

def dashboard(chat_id):

    keyboard = [

        [
            {
                "text":"📘 Physics Live Lec",
                "callback_data":"physics"
            }
        ],

        [
            {
                "text":"🧪 Physical Chemistry Live",
                "callback_data":"chemistry"
            }
        ],

        [
            {
                "text":"🧬 Biology Live Lec",
                "callback_data":"biology"
            }
        ],

        [
            {
                "text":"📊 Study Tracker",
                "callback_data":"tracker"
            }
        ],

        [
            {
                "text":"🎁 Daily Free Credit",
                "callback_data":"claim"
            },

            {
                "text":"💳 My Credits",
                "callback_data":"credits"
            }
        ],

        [
            {
                "text":"👤 Contact Admin",
                "url":"https://t.me/gaurav0247"
            }
        ]
    ]


    send_message(
        chat_id,
        "🔥 Welcome to GxNOVaa\n\n"
        "This bot is made by @gaurav0247\n\n"
        "Select Option 👇",
        keyboard
    )


# ---------------- LECTURE DATA ----------------

def default_lectures():

    data = {

        "mr":{
            "name":"Physics by MR Sir",
            "time":"08:47",
            "link":""
        },

        "saleem":{
            "name":"Physics by Saleem Sir",
            "time":"08:47",
            "link":""
        },


        "sudhanshu":{
            "name":"Physical Chemistry by Sudhanshu Sir",
            "time":"11:03",
            "link":""
        },


        "amit":{
            "name":"Physical Chemistry by Amit Sir",
            "time":"11:03",
            "link":""
        },


        "bio1":{
            "name":"Biology Live 1",
            "time":"13:20",
            "link":""
        },


        "bio2":{
            "name":"Biology Live 2",
            "time":"13:20",
            "link":""
        }

    }

    save_json(LECTURE_FILE,data)


if not load_json(LECTURE_FILE):
    default_lectures()


# ---------------- START BOT ----------------


while True:

    try:

        updates = get_updates()


        for update in updates:

            offset = update["update_id"] + 1


            if "message" in update:

                msg = update["message"]

                chat_id = msg["chat"]["id"]

                text = msg.get("text","")


                if text == "/start":

                    create_user(chat_id)

                    dashboard(chat_id)



            elif "callback_query" in update:

                query = update["callback_query"]

                chat_id = query["message"]["chat"]["id"]

                data = query["data"]


                if data=="physics":

                    send_message(
                        chat_id,
                        "📘 Physics Live Lec\n\nSelect Teacher 👇",
                        [
                            [
                                {
                                    "text":"⚡ MR Sir",
                                    "callback_data":"mr"
                                }
                            ],

                            [
                                {
                                    "text":"🔥 Saleem Sir",
                                    "callback_data":"saleem"
                                }
                            ]
                        ]
                    )


                elif data=="chemistry":

                    send_message(
                        chat_id,
                        "🧪 Physical Chemistry Live Lec\n\nSelect Teacher 👇",
                        [
                            [
                                {
                                    "text":"Sudhanshu Sir",
                                    "callback_data":"sudhanshu"
                                }
                            ],

                            [
                                {
                                    "text":"Amit Sir",
                                    "callback_data":"amit"
                                }
                            ]
                        ]
                    )


                elif data=="biology":

                    send_message(
                        chat_id,
                        "🧬 Biology Live Lec\n\n",
                        [
                            [
                                {
                                    "text":"Biology Live 1",
                                    "callback_data":"bio1"
                                }
                            ],

                            [
                                {
                                    "text":"Biology Live 2",
                                    "callback_data":"bio2"
                                }
                            ]
                        ]
        )
                    # ---------------- CREDIT SYSTEM ----------------

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

    data = users[str(user_id)]

    return (
        "💳 My Credits\n\n"
        f"⭐ Available Credits: {data['credits']}\n"
        f"📚 Lectures Watched: {data['lectures']}"
    )



# ---------------- DAILY CLAIM ----------------

def claim_daily(user_id):

    users = load_json(USER_FILE)

    uid = str(user_id)

    now = datetime.now()

    last = users[uid]["last_claim"]


    if last:

        last_time = datetime.fromisoformat(last)

        if now - last_time < timedelta(hours=24):

            return False


    users[uid]["credits"] += 4
    users[uid]["last_claim"] = now.isoformat()

    save_json(USER_FILE, users)

    return True



# ---------------- STUDY TRACKER ----------------

def study_tracker(user_id):

    users = load_json(USER_FILE)

    data = users[str(user_id)]

    return (
        "📊 Study Tracker\n\n"
        f"📚 Completed Lectures: {data['lectures']}\n"
        f"🔥 Streak: {data['streak']} Days\n"
        f"⭐ Credits: {data['credits']}"
    )



# ---------------- LECTURE CHECK ----------------

def open_lecture(user_id, key):

    lectures = load_json(LECTURE_FILE)

    lec = lectures[key]


    now = datetime.now().strftime("%H:%M")


    if now < lec["time"]:

        return (
            "⏳ Class abhi start nahi hui\n\n"
            f"{lec['name']}\n"
            f"⏰ Time: {lec['time']}"
        )


    if lec["link"] == "":

        return (
            "⚠️ Lecture link not added yet\n\n"
            "Admin will update soon."
        )


    if use_credit(user_id):

        return (
            "🔴 LIVE NOW\n\n"
            f"{lec['name']}\n\n"
            f"▶️ Watch Lecture:\n{lec['link']}"
        )


    return (
        "❌ Credits khatam ho gaye\n\n"
        "🎁 Daily Free Credit claim karein"
    )



# ---------------- ADMIN ----------------

def is_admin(user_id):

    return user_id == ADMIN_ID



def admin_panel(chat_id):

    keyboard = [

        [
            {
                "text":"📊 Bot Stats",
                "callback_data":"stats"
            }
        ],

        [
            {
                "text":"💳 Add Credit",
                "callback_data":"admin_credit"
            }
        ],

        [
            {
                "text":"🔗 Update Link",
                "callback_data":"admin_link"
            }
        ]

    ]


    send_message(
        chat_id,
        "⚙️ GxNOVaa Admin Panel",
        keyboard
    )



# ---------------- CALLBACK CONTINUE ----------------


# Is part ko Part 1 ke callback section ke andar
# biology ke baad add karna


if data in [
    "mr",
    "saleem",
    "sudhanshu",
    "amit",
    "bio1",
    "bio2"
]:

    send_message(
        chat_id,
        open_lecture(chat_id,data)
    )


elif data=="credits":

    send_message(
        chat_id,
        show_credits(chat_id)
    )


elif data=="claim":

    if claim_daily(chat_id):

        send_message(
            chat_id,
            "🎉 Daily Reward Claimed!\n\n"
            "+4 Credits Added"
        )

    else:

        send_message(
            chat_id,
            "⏳ Already Claimed\n\n"
            "Next claim after 24 hours"
        )


elif data=="tracker":

    send_message(
        chat_id,
        study_tracker(chat_id)
    )



# ---------------- ADMIN COMMAND ----------------


if text == "/admin":

    if is_admin(chat_id):

        admin_panel(chat_id)

    else:

        send_message(
            chat_id,
            "❌ Access Denied"
    )
                    
