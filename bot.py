import requests
import time
from flask import Flask
import threading

# ===== TELEGRAM =====
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

BOT_ACTIVE = False

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# ===== DATA =====
def get_prices():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?interval=5m&range=1d"
        data = requests.get(url).json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c]
    except:
        return []

# ===== EMA =====
def ema(prices, period):
    k = 2 / (period + 1)
    val = prices[0]
    for p in prices:
        val = p * k + val * (1 - k)
    return val

last_signal = None

def check():
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

# ===== TELEGRAM COMMAND =====
last_update_id = None

def check_commands():
    global BOT_ACTIVE, last_update_id

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    data = requests.get(url).json()

    for update in data["result"]:
        uid = update["update_id"]

        if last_update_id and uid <= last_update_id:
            continue

        last_update_id = uid

        msg = update.get("message", {}).get("text", "").lower()

        if msg == "/on":
            BOT_ACTIVE = True
            send_msg("Bot ON ✅")

        elif msg == "/off":
            BOT_ACTIVE = False
            send_msg("Bot OFF 🛑")

# ===== LOOP =====
def run_bot():
    send_msg("Bot ready ✅")

    while True:
        check_commands()

        if BOT_ACTIVE:
            check()
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
