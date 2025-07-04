import requests
import datetime
import time
import pytz

# === KONFIGURASI ===
BOT_TOKEN = '8177793125:AAF1LPZ4rMJ3zZSzsTi4VxQzJt3LNvOBU1w'
CHAT_ID = '-1002790497800'
API_KEY = '29341fd3f882419b81d1d602b66a1c7d'
API_URL = f'https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&outputsize=50&apikey={API_KEY}'

WIB = pytz.timezone('Asia/Jakarta')
last_signal = None
last_alert = None

def send_signal(text):
    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
        )
    except Exception as e:
        print("❌ Gagal kirim sinyal:", e)

def calculate_ema(data, period):
    k = 2 / (period + 1)
    ema = float(data[0])
    for price in data[1:]:
        ema = float(price) * k + ema * (1 - k)
    return ema

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

print("🚀 Bot sinyal aktif...")

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

        ema14 = calculate_ema(close_prices[-15:], 14)
        ema50 = calculate_ema(close_prices[-50:], 50)
        rsi = calculate_rsi(close_prices)

        current_price = close_prices[-1]
        diff = abs(ema14 - ema50)

        direction = None
        if ema14 > ema50 and rsi > 50:
            direction = "BUY"
        elif ema14 < ema50 and rsi < 50:
            direction = "SELL"

        if direction and direction != last_signal:
            pip = 0.10
            tp1 = current_price + 3 * pip if direction == "BUY" else current_price - 3 * pip
            tp2 = current_price + 5 * pip if direction == "BUY" else current_price - 5 * pip
            sl = current_price - 3 * pip if direction == "BUY" else current_price + 3 * pip

            send_signal(
                f"🚀 *Signal {direction} Detected!*\n"
                f"📊 Entry: {current_price:.2f}\n"
                f"🎯 TP1: {tp1:.2f} | TP2: {tp2:.2f}\n"
                f"🛡️ SL: {sl:.2f}\n"
                f"🧠 EMA14 {'above' if direction == 'BUY' else 'below'} EMA50\n"
                f"📈 RSI: {rsi:.1f} ✅\n"
                f"🕒 {now} WIB"
            )
            last_signal = direction
            last_alert = None  # reset alert supaya muncul lagi nanti

        elif diff < 0.15 and rsi:  # alert crossover
            if last_alert != direction:
                alert_type = "BUY" if ema14 > ema50 else "SELL"
                send_signal(
                    f"⚠️ *Potensi {alert_type}*\n"
                    f"🧠 EMA14 mendekati EMA50\n"
                    f"📈 RSI: {rsi:.1f}\n"
                    f"🕒 {now} WIB"
                )
                last_alert = direction

        else:
            print(f"[{now}] EMA14: {ema14:.2f} | EMA50: {ema50:.2f} | RSI: {rsi:.1f} | Monitoring...")

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(10)
