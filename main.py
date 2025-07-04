import requests
import datetime
import time
import pytz
from flask import Flask
import threading

# === KONFIGURASI ===
BOT_TOKEN = '8177793125:AAF1LPZ4rMJ3zZSzsTi4VxQzJt3LNvOBU1w'
CHAT_ID = '-1002790497800'
API_KEY = '29341fd3f882419b81d1d602b66a1c7d'
API_URL = f'https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=5min&outputsize=100&apikey={API_KEY}'

WIB = pytz.timezone('Asia/Jakarta')
last_signal = None

# === FLASK KEEP ALIVE ===
app = Flask(__name__)
@app.route('/')
def home():
    return "✅ Bot is running!"
def run_flask():
    app.run(host="0.0.0.0", port=8080)
threading.Thread(target=run_flask).start()

# === KIRIM SINYAL ===
def send_signal(text):
    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
        )
    except Exception as e:
        print("❌ Gagal kirim sinyal:", e)

# === HITUNG RSI ===
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        delta = prices[-i] - prices[-i - 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(-delta)
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 1e-9
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

print("🚀 Bot RSI XAU/USD Aktif (5min)...")

# === LOOP UTAMA ===
while True:
    try:
        now = datetime.datetime.now(WIB).strftime('%H:%M:%S')
        res = requests.get(API_URL).json()

        if 'values' not in res:
            print("❌ Error ambil data:", res)
            time.sleep(10)
            continue

        candles = res['values'][::-1]
        close_prices = [float(c['close']) for c in candles]

        rsi = calculate_rsi(close_prices)
        current_price = close_prices[-1]

        if rsi is None:
            print("❌ Data tidak cukup untuk hitung RSI")
            time.sleep(10)
            continue

        if rsi < 25 and last_signal != "BUY":
            send_signal(
                f"📉 *RSI Oversold Detected!*\n"
                f"🚀 Signal: *BUY*\n"
                f"💰 Price: {current_price:.2f}\n"
                f"📊 RSI: {rsi:.1f} (di bawah 25)\n"
                f"🕒 {now} WIB"
            )
            last_signal = "BUY"

        elif rsi > 75 and last_signal != "SELL":
            send_signal(
                f"📈 *RSI Overbought Detected!*\n"
                f"🔻 Signal: *SELL*\n"
                f"💰 Price: {current_price:.2f}\n"
                f"📊 RSI: {rsi:.1f} (di atas 75)\n"
                f"🕒 {now} WIB"
            )
            last_signal = "SELL"

        else:
            print(f"[{now}] RSI: {rsi:.1f} | Harga: {current_price:.2f} | Monitoring...")

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(10)
