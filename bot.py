import requests
import time
import threading
from flask import Flask, request

# ===== TELEGRAM =====
BOT_TOKEN = "8285229070:AAGZQnCbjULqMUsZkmNMBSG9NCh3WlI2bNo"
CHAT_ID = "1207682165"

app = Flask(__name__)

bot_running = False

# ===== SEND MESSAGE =====
def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# ===== FETCH DATA =====
def get_prices(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
        r = requests.get(url, timeout=10)
        data = r.json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c is not None]
    except:
        return []

# ===== EMA =====
def ema(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema_val = prices[0]
    for p in prices:
        ema_val = p * k + ema_val * (1 - k)
    return ema_val

last_signal = {
    "NIFTY": None,
    "BANKNIFTY": None,
    "SENSEX": None
}

# ===== CHECK SIGNAL =====
def check(symbol, name):
    prices = get_prices(symbol)
    if len(prices) < 30:
        return

    ema9_prev = ema(prices[-21:-1], 9)
    ema15_prev = ema(prices[-21:-1], 15)

    ema9_now = ema(prices[-20:], 9)
    ema15_now = ema(prices[-20:], 15)

    if not all([ema9_prev, ema15_prev, ema9_now, ema15_now]):
        return

    if ema9_prev < ema15_prev and ema9_now > ema15_now:
        if last_signal[name] != "BUY":
            send_msg(f"{name} BUY 🔼")
            last_signal[name] = "BUY"

    elif ema9_prev > ema15_prev and ema9_now < ema15_now:
        if last_signal[name] != "SELL":
            send_msg(f"{name} SELL 🔽")
            last_signal[name] = "SELL"

# ===== BOT LOOP =====
def run_bot():
    global bot_running
    while True:
        if bot_running:
            print("Running strategy...")
            check("^NSEI", "NIFTY")
            check("^NSEBANK", "BANKNIFTY")
            check("^BSESN", "SENSEX")
        time.sleep(300)

# ===== TELEGRAM WEBHOOK =====
@app.route("/", methods=["POST"])
def webhook():
    global bot_running

    data = request.json

    if "message" in data:
        text = data["message"].get("text", "")

        if text == "/on":
            bot_running = True
            send_msg("Bot Started ✅")

        elif text == "/off":
            bot_running = False
            send_msg("Bot Stopped ❌")

    return "ok"

# ===== KEEP SERVER ALIVE =====
@app.route("/")
def home():
    return "Bot running..."

# ===== START =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
