import requests
import time
import random
from datetime import datetime

BOT_TOKEN = "8681554780:AAE8mKCm16HMqfdaLI-sKRxs3AAyx_gUQkU"
CHAT_ID = "1624738454"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_btc_data():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "prices" not in data:
            return None, None
        
        prices = [p[1] for p in data["prices"]]
        volumes = [v[1] for v in data.get("total_volumes", [])]
        
        return prices, volumes
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ma(prices, period=20):
    if len(prices) < period:
        return prices[-1] if prices else 0
    return sum(prices[-period:]) / period

def calculate_volatility(prices, period=20):
    if len(prices) < period:
        return 0
    recent = prices[-period:]
    mean = sum(recent) / len(recent)
    variance = sum((p - mean) ** 2 for p in recent) / len(recent)
    return (variance ** 0.5) / mean * 100

def analyze_and_predict():
    closes, volumes = get_btc_data()
    
    if not closes:
        send_message("❌ Error fetching data. Using fallback.")
        return random.uniform(80000, 95000), "UNKNOWN", 50
    
    current_price = closes[-1]
    rsi = calculate_rsi(closes)
    ma20 = calculate_ma(closes, 20)
    ma50 = calculate_ma(closes, 50) if len(closes) >= 50 else ma20
    volatility = calculate_volatility(closes)
    
    signals = 0
    
    if rsi < 30:
        signals += 2
    elif rsi < 45:
        signals += 1
    elif rsi > 70:
        signals -= 2
    elif rsi > 55:
        signals -= 1
    
    if current_price > ma20:
        signals += 1
    else:
        signals -= 1
    
    if current_price > ma50:
        signals += 1
    else:
        signals -= 1
    
    if ma20 > ma50:
        signals += 1
    else:
        signals -= 1
    
    if signals >= 3:
        direction = "📈 UP"
        confidence = min(85, 60 + signals * 5)
    elif signals >= 1:
        direction = "↗️ UP"
        confidence = min(75, 55 + signals * 5)
    elif signals <= -3:
        direction = "📉 DOWN"
        confidence = min(85, 60 + abs(signals) * 5)
    elif signals <= -1:
        direction = "↘️ DOWN"
        confidence = min(75, 55 + abs(signals) * 5)
    else:
        direction = "➡️ SIDEWAYS"
        confidence = 50 + abs(signals) * 5
    
    change_percent = (volatility * 0.5) * (signals / 3)
    predicted_price = current_price * (1 + change_percent / 100)
    
    return current_price, direction, confidence, rsi, ma20, predicted_price, volatility

def predict():
    result = analyze_and_predict()
    
    if len(result) == 3:
        return
    
    current_price, direction, confidence, rsi, ma20, predicted_price, volatility = result
    
    message = f"""📊 BTC Technical Analysis

💰 Current Price: ${current_price:,.2f}
🎯 Prediction: {direction}
📈 Confidence: {confidence}%

📉 RSI: {rsi:.1f}
📊 MA20: ${ma20:,.2f}
⚡ Volatility: {volatility:.2f}%

⏰ Time: {datetime.now().strftime('%H:%M')}"""
    
    send_message(message)

if __name__ == "__main__":
    send_message("🔔 BTC Predictor Started! Hourly updates with technical analysis.")
    while True:
        predict()
        time.sleep(3600)