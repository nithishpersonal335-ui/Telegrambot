import requests
import time
from flask import Flask
import threading
import os

# ===== TELEGRAM =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = str(os.getenv("CHAT_ID"))

BOT_ACTIVE = False
last_update_id = None

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Send error:", e)

# ===== CLEAR OLD UPDATES (VERY IMPORTANT) =====
def clear_old_updates():
    global last_update_id
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        data = requests.get(url).json()

        if data["result"]:
            last_update_id = data["result"][-1]["update_id"]
            print("Old messages cleared")
    except:
        pass

# ===== READ COMMANDS =====
def check_commands():
    global BOT_ACTIVE, last_update_id

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        data = requests.get(url, timeout=10).json()

        for update in data.get("result", []):
            uid = update["update_id"]

            if last_update_id is not None and uid <= last_update_id:
                continue

            last_update_id = uid

            msg = update.get("message", {}).get("text", "").lower()
            chat = str(update.get("message", {}).get("chat", {}).get("id"))

            # 🔒 Only allow your chat
            if chat != CHAT_ID:
                continue

            print("Command received:", msg)

            if msg == "/on":
                BOT_ACTIVE = True
                send_msg("Bot ON ✅")

            elif msg == "/off":
                BOT_ACTIVE = False
                send_msg("Bot OFF 🛑")

    except Exception as e:
        print("Command error:", e)

# ===== EMA =====
def ema(prices, period):
    k = 2 / (period + 1)
    val = prices[0]
    for p in prices:
        val = p * k + val * (1 - k)
    return val

def get_prices():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?interval=5m&range=1d"
        data = requests.get(url, timeout=10).json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c]
    except:
        return []

last_signal = None

def check_market():
    global last_signal

    prices = get_prices()
    if len(prices) < 30:
        return

    e9_prev = ema(prices[-21:-1], 9)
    e15_prev = ema(prices[-21:-1], 15)
    e9_now = ema(prices[-20:], 9)
    e15_now = ema(prices[-20:], 15)

    if e9_prev < e15_prev and e9_now > e15_now:
        if last_signal != "BUY":
            send_msg("NIFTY ema crossing")
            last_signal = "BUY"

    elif e9_prev > e15_prev and e9_now < e15_now:
        if last_signal != "SELL":
            send_msg("NIFTY ema crossing")
            last_signal = "SELL"

# ===== LOOP =====
def run_bot():
    print("Bot Started")
    send_msg("Bot ready ✅")

    clear_old_updates()  # 🔴 KEY FIX

    while True:
        check_commands()

        if BOT_ACTIVE:
            print("Bot ON → checking market")
            check_market()
            time.sleep(300)
        else:
            time.sleep(5)

# ===== WEB =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Running"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
