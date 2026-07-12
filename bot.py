import requests
import json
import time

# Telegram Bot Token
BOT_TOKEN = "8914784117:AAGbEGulg9rKF25cmMYedyAJlBaZjIkZy5Q"

# External Phone Lookup API
EXTERNAL_API_BASE = "https://nitin-apis-the-best.vercel.app/api"

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    """Helper function to send a message via Telegram Bot API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True
    }
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if not response.ok:
            print(f"Failed to send message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending message: {e}")


def main():
    print("✅ Bot started successfully!")
    print("Bot is running... Press Ctrl+C to stop.")
    
    offset = 0
    while True:
        try:
            # Long polling
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": ["message"]
            }
            
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code != 200:
                print(f"Error getting updates: {response.status_code}")
                time.sleep(5)
                continue
                
            data = response.json()
            
            if not data.get("ok"):
                print("Error in API response")
                time.sleep(5)
                continue
            
            updates = data.get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                
                if "message" not in update:
                    continue
                    
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message.get("text", "").strip()
                
                # Handle /start command
                if text == "/start":
                    welcome_text = (
                        "👋 Welcome to the Phone Lookup Bot!\n\n"
                        "Use the keyboard below to perform a phone number lookup."
                    )
                    
                    keyboard = {
                        "keyboard": [
                            ["📱 Phone Lookup"]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": False
                    }
                    
                    send_message(chat_id, welcome_text, reply_markup=keyboard)
                
                # Handle Phone Lookup button press
                elif text == "📱 Phone Lookup":
                    prompt_text = "📞 Send 10 digit mobile number:"
                    send_message(chat_id, prompt_text)
                
                # Handle 10-digit phone number
                elif text.isdigit() and len(text) == 10:
                    try:
                        api_url = f"{EXTERNAL_API_BASE}?type=number&mobile={text}"
                        print(f"Calling API for number {text}")
                        
                        api_response = requests.get(api_url, timeout=15)
                        
                        if api_response.status_code != 200:
                            send_message(chat_id, f"❌ API returned error: {api_response.status_code}")
                            continue
                        
                        api_data = api_response.json()
                        formatted_json = json.dumps(api_data, indent=2, ensure_ascii=False)
                        
                        result_text = f"✅ Phone Lookup Result:\n\n<pre>{formatted_json}</pre>"
                        send_message(chat_id, result_text, parse_mode="HTML")
                        
                    except json.JSONDecodeError:
                        send_message(chat_id, "❌ Invalid response from API (not JSON)")
                    except requests.exceptions.RequestException:
                        send_message(chat_id, "❌ Failed to connect to the lookup API")
                    except Exception as e:
                        send_message(chat_id, f"❌ An error occurred: {str(e)[:150]}")
                
                # Invalid input
                else:
                    error_text = (
                        "❌ Invalid input!\n\n"
                        "Please send a valid 10-digit mobile number (numbers only).\n"
                        "Or press the 📱 Phone Lookup button."
                    )
                    send_message(chat_id, error_text)
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
