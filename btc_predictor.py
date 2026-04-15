import requests
import time
import random
import json
import os
from datetime import datetime
from pathlib import Path

BOT_TOKEN = "8681554780:AAE8mKCm16HMqfdaLI-sKRxs3AAyx_gUQkU"
CHAT_ID = "1624738454"
DATA_FILE = "predictions.json"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def load_predictions():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_prediction(prediction):
    predictions = load_predictions()
    predictions.append(prediction)
    with open(DATA_FILE, "w") as f:
        json.dump(predictions, f)

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
        direction_raw = "UP"
        confidence = min(85, 60 + signals * 5)
    elif signals >= 1:
        direction = "↗️ UP"
        direction_raw = "UP"
        confidence = min(75, 55 + signals * 5)
    elif signals <= -3:
        direction = "📉 DOWN"
        direction_raw = "DOWN"
        confidence = min(85, 60 + abs(signals) * 5)
    elif signals <= -1:
        direction = "↘️ DOWN"
        direction_raw = "DOWN"
        confidence = min(75, 55 + abs(signals) * 5)
    else:
        direction = "➡️ SIDEWAYS"
        direction_raw = "SIDEWAYS"
        confidence = 50 + abs(signals) * 5
    
    change_percent = (volatility * 0.5) * (signals / 3)
    predicted_price = current_price * (1 + change_percent / 100)
    
    return current_price, direction, direction_raw, confidence, rsi, ma20, predicted_price, volatility

def send_daily_stats():
    predictions = load_predictions()
    
    if not predictions:
        send_message("📊 No predictions yet!")
        return
    
    # Get today's predictions
    today = datetime.now().strftime("%Y-%m-%d")
    today_preds = [p for p in predictions if p.get("date", "").startswith(today)]
    
    # Calculate stats
    total = len(predictions)
    today_total = len(today_preds)
    
    correct = sum(1 for p in predictions if p.get("correct", False))
    today_correct = sum(1 for p in today_preds if p.get("correct", False))
    
    accuracy = (correct / total * 100) if total > 0 else 0
    today_accuracy = (today_correct / today_total * 100) if today_total > 0 else 0
    
    up_preds = sum(1 for p in predictions if p.get("direction") == "UP")
    down_preds = sum(1 for p in predictions if p.get("direction") == "DOWN")
    
    message = f"""📊 BTC Prediction Stats

📈 Total: {total} predictions
✅ Correct: {correct} ({accuracy:.1f}%)

📅 Today: {today_total} predictions
✅ Today correct: {today_correct} ({today_accuracy:.1f}%)

📊 Direction breakdown:
  UP: {up_preds}
  DOWN: {down_preds}

⏰ Updated: {datetime.now().strftime('%H:%M')}"""
    
    send_message(message)

def predict():
    result = analyze_and_predict()
    
    if len(result) == 3:
        return
    
    current_price, direction, direction_raw, confidence, rsi, ma20, predicted_price, volatility = result
    
    # Save prediction
    prediction = {
        "date": datetime.now().isoformat(),
        "price": current_price,
        "direction": direction_raw,
        "confidence": confidence,
        "rsi": rsi,
        "correct": None  # Will be updated next hour
    }
    save_prediction(prediction)
    
    # Check previous prediction
    predictions = load_predictions()
    if len(predictions) >= 2:
        prev = predictions[-2]
        if prev.get("correct") is None:
            # Calculate if previous was correct
            price_change = current_price - prev["price"]
            was_correct = False
            if prev["direction"] == "UP" and price_change > 0:
                was_correct = True
            elif prev["direction"] == "DOWN" and price_change < 0:
                was_correct = True
            elif prev["direction"] == "SIDEWAYS" and abs(price_change) < prev["price"] * 0.01:
                was_correct = True
            
            prev["correct"] = was_correct
            predictions[-2] = prev
            with open(DATA_FILE, "w") as f:
                json.dump(predictions, f)
    
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
    # Check if it's 00:00 MSK (21:00 UTC)
    current_hour_utc = datetime.utcnow().hour
    
    if current_hour_utc == 21:
        send_daily_stats()
    else:
        send_message("🔔 BTC Predictor Started! Hourly updates with technical analysis.")
        while True:
            predict()
            time.sleep(3600)