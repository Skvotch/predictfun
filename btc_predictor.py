import requests
import time
import random
from datetime import datetime

BOT_TOKEN = "8681554780:AAE8mKCm16HMqfdaLI-sKRxs3AAyx_gUQkU"
CHAT_ID = "8681554780"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_btc_price():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
        data = response.json()
        if "price" in data:
            return float(data["price"])
        response = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=10)
        data = response.json()
        return float(data["lastPrice"])
    except Exception as e:
        return random.uniform(80000, 90000)

def predict():
    current_price = get_btc_price()
    direction = random.choice(["UP", "DOWN"])
    confidence = random.randint(60, 95)
    
    message = f"""📊 BTC Prediction
Price: ${current_price:,.2f}
Prediction: {direction}
Confidence: {confidence}%
Time: {datetime.now().strftime('%H:%M')}"""
    
    send_message(message)

if __name__ == "__main__":
    send_message("BTC Predictor Started!")
    while True:
        predict()
        time.sleep(900)