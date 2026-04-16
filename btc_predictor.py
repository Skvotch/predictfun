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
        params = {"vs_currency": "usd", "days": "30", "interval": "hourly"}
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "prices" not in data:
            return None
        
        prices = [p[1] for p in data["prices"]]
        return prices
    except Exception as e:
        print(f"Error: {e}")
        return None

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

def calculate_ma(prices, period):
    if len(prices) < period:
        return prices[-1] if prices else 0
    return sum(prices[-period:]) / period

def calculate_ema(prices, period):
    if len(prices) < period:
        return prices[-1] if prices else 0
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

def calculate_macd(prices):
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd_line = ema12 - ema26
    
    # Signal line (9-period EMA of MACD)
    macd_values = []
    for i in range(26, len(prices)):
        e12 = calculate_ema(prices[:i+1], 12)
        e26 = calculate_ema(prices[:i+1], 26)
        macd_values.append(e12 - e26)
    
    if len(macd_values) < 9:
        return macd_line, 0, 0
    
    signal = calculate_ema(macd_values, 9)
    histogram = macd_line - signal
    
    return macd_line, signal, histogram

def calculate_bollinger_bands(prices, period=20):
    if len(prices) < period:
        return 0, 0, 0
    
    ma = calculate_ma(prices, period)
    recent = prices[-period:]
    variance = sum((p - ma) ** 2 for p in recent) / period
    std = variance ** 0.5
    
    upper = ma + (2 * std)
    lower = ma - (2 * std)
    
    return upper, ma, lower

def calculate_stochastic(prices, period=14):
    if len(prices) < period:
        return 50, 50
    
    recent = prices[-period:]
    low_min = min(recent)
    high_max = max(recent)
    current = prices[-1]
    
    if high_max == low_min:
        return 50, 50
    
    k = ((current - low_min) / (high_max - low_min)) * 100
    
    # %D is 3-period SMA of %K
    k_values = []
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        lw = min(window)
        hw = max(window)
        if hw != lw:
            k_values.append(((prices[i] - lw) / (hw - lw)) * 100)
        else:
            k_values.append(50)
    
    d = sum(k_values[-3:]) / 3 if len(k_values) >= 3 else 50
    
    return k, d

def calculate_atr(prices, period=14):
    if len(prices) < period + 1:
        return 0
    
    tr_values = []
    for i in range(1, len(prices)):
        high = prices[i]
        low = prices[i]
        prev_close = prices[i-1]
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_values.append(tr)
    
    return sum(tr_values[-period:]) / period

def analyze_and_predict():
    prices = get_btc_data()
    
    if not prices:
        send_message("❌ Error fetching data")
        return
    
    current_price = prices[-1]
    prev_close = prices[-2]
    
    # Calculate all indicators
    rsi = calculate_rsi(prices)
    ma20 = calculate_ma(prices, 20)
    ma50 = calculate_ma(prices, 50)
    ma200 = calculate_ma(prices, 200) if len(prices) >= 200 else ma50
    ema20 = calculate_ema(prices, 20)
    ema50 = calculate_ema(prices, 50)
    
    macd_line, signal, histogram = calculate_macd(prices)
    upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(prices)
    
    stoch_k, stoch_d = calculate_stochastic(prices)
    atr = calculate_atr(prices)
    
    # Calculate volatility
    volatility = (atr / current_price) * 100
    
    # Count signals
    signals = 0
    reasons = []
    
    # RSI
    if rsi < 30:
        signals += 2
        reasons.append(f"RSI {rsi:.1f} (oversold)")
    elif rsi < 40:
        signals += 1
        reasons.append(f"RSI {rsi:.1f}")
    elif rsi > 70:
        signals -= 2
        reasons.append(f"RSI {rsi:.1f} (overbought)")
    elif rsi > 60:
        signals -= 1
        reasons.append(f"RSI {rsi:.1f}")
    
    # Price vs Moving Averages
    if current_price > ma20:
        signals += 1
        reasons.append("Price > MA20")
    else:
        signals -= 1
        reasons.append("Price < MA20")
    
    if current_price > ma50:
        signals += 1
        reasons.append("Price > MA50")
    else:
        signals -= 1
        reasons.append("Price < MA50")
    
    if current_price > ma200:
        signals += 1
        reasons.append("Price > MA200 (long-term bullish)")
    else:
        signals -= 1
        reasons.append("Price < MA200")
    
    # MA crossovers
    if ma20 > ma50:
        signals += 1
        reasons.append("MA20 > MA50 (golden cross)")
    else:
        signals -= 1
        reasons.append("MA20 < MA50 (death cross)")
    
    if ema20 > ema50:
        signals += 1
        reasons.append("EMA20 > EMA50")
    else:
        signals -= 1
        reasons.append("EMA20 < EMA50")
    
    # MACD
    if histogram > 0:
        signals += 1
        reasons.append("MACD bullish")
    else:
        signals -= 1
        reasons.append("MACD bearish")
    
    if macd_line > signal:
        signals += 1
        reasons.append("MACD > Signal")
    else:
        signals -= 1
        reasons.append("MACD < Signal")
    
    # Bollinger Bands
    if current_price < lower_bb:
        signals += 2
        reasons.append("Price at lower BB (oversold)")
    elif current_price > upper_bb:
        signals -= 2
        reasons.append("Price at upper BB (overbought)")
    
    # Stochastic
    if stoch_k < 20:
        signals += 1
        reasons.append("Stochastic oversold")
    elif stoch_k > 80:
        signals -= 1
        reasons.append("Stochastic overbought")
    
    if stoch_k > stoch_d:
        signals += 1
        reasons.append("Stochastic bullish cross")
    else:
        signals -= 1
        reasons.append("Stochastic bearish cross")
    
    # Determine direction and confidence
    if signals >= 5:
        direction = "📈 UP"
        confidence = min(90, 60 + signals * 3)
    elif signals >= 2:
        direction = "↗️ UP"
        confidence = min(75, 50 + signals * 5)
    elif signals <= -5:
        direction = "📉 DOWN"
        confidence = min(90, 60 + abs(signals) * 3)
    elif signals <= -2:
        direction = "↘️ DOWN"
        confidence = min(75, 50 + abs(signals) * 5)
    else:
        direction = "➡️ SIDEWAYS"
        confidence = 50 + abs(signals) * 5
    
    # Calculate change
    change = current_price - prev_close
    change_pct = (change / prev_close) * 100
    change_emoji = "🟢" if change > 0 else "🔴"
    
    # Format message
    message = f"""📊 BTC Technical Analysis

💰 Current: ${current_price:,.2f}
🔒 Prev Close: ${prev_close:,.2f}
{change_emoji} Change: {change:+.2f} ({change_pct:+.2f}%)

🎯 Prediction: {direction}
📈 Confidence: {confidence}%

📊 Indicators:
• RSI: {rsi:.1f}
• MA20: ${ma20:,.2f}
• MA50: ${ma50:,.2f}
• MACD: {macd_line:.2f}
• BB: ${lower_bb:,.0f} - ${upper_bb:,.0f}
• Stochastic: {stoch_k:.1f}/{stoch_d:.1f}
• ATR: {atr:.2f} ({volatility:.2f}%)

🔍 Signals ({len(reasons)}): {', '.join(reasons[:5])}

⏰ {datetime.now().strftime('%H:%M MSK')}"""
    
    send_message(message)

if __name__ == "__main__":
    send_message("🔔 BTC Predictor Started! Hourly updates.")
    analyze_and_predict()
    time.sleep(3600)