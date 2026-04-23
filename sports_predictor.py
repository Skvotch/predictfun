import requests
import time
import json
import os
from datetime import datetime, timedelta

BOT_TOKEN = "8681554780:AAE8mKCm16HMqfdaLI-sKRxs3AAyx_gUQkU"
CHAT_ID = "1624738454"
BETSTACK_API_KEY = "8466911183a9a0e6f2cc0b7441676e2da3df0e767d826f4232154d5af27a39a3"

SENT_PREDICTIONS_FILE = "sent_predictions.json"

def load_sent_predictions():
    if os.path.exists(SENT_PREDICTIONS_FILE):
        with open(SENT_PREDICTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_sent_predictions(data):
    with open(SENT_PREDICTIONS_FILE, 'w') as f:
        json.dump(data, f)

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


# ============ BETSTACK API ============
def get_betstack_matches():
    """Get matches from BetStack API"""
    matches = []
    headers = {"X-API-Key": BETSTACK_API_KEY}
    
    # NBA
    try:
        url = "https://api.betstack.dev/api/v1/events"
        params = {"league": "american_basketball_nba", "status": "pre", "per_page": 10}
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                for event in data["data"]:
                    home = event.get("home_team", {})
                    away = event.get("away_team", {})
                    if home.get("name") and away.get("name"):
                        matches.append({
                            "id": str(event.get("id")),
                            "team1": home.get("name"),
                            "team2": away.get("name"),
                            "begin_at": event.get("start_time"),
                            "league": "NBA",
                            "game": "Basketball",
                            "odds": event.get("consensus", {})
                        })
    except Exception as e:
        print(f"NBA error: {e}")
    
    # NHL
    try:
        url = "https://api.betstack.dev/api/v1/events"
        params = {"league": "ice_hockey_nhl", "status": "pre", "per_page": 10}
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                for event in data["data"]:
                    home = event.get("home_team", {})
                    away = event.get("away_team", {})
                    if home.get("name") and away.get("name"):
                        matches.append({
                            "id": str(event.get("id")),
                            "team1": home.get("name"),
                            "team2": away.get("name"),
                            "begin_at": event.get("start_time"),
                            "league": "NHL",
                            "game": "Hockey",
                            "odds": event.get("consensus", {})
                        })
    except Exception as e:
        print(f"NHL error: {e}")
    
    # Soccer - EPL
    try:
        url = "https://api.betstack.dev/api/v1/events"
        params = {"league": "soccer_epl", "status": "pre", "per_page": 10}
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                for event in data["data"]:
                    home = event.get("home_team", {})
                    away = event.get("away_team", {})
                    if home.get("name") and away.get("name"):
                        matches.append({
                            "id": str(event.get("id")),
                            "team1": home.get("name"),
                            "team2": away.get("name"),
                            "begin_at": event.get("start_time"),
                            "league": "EPL",
                            "game": "Football",
                            "odds": event.get("consensus", {})
                        })
    except Exception as e:
        print(f"EPL error: {e}")
    
    # Soccer - La Liga
    try:
        url = "https://api.betstack.dev/api/v1/events"
        params = {"league": "soccer_la_liga", "status": "pre", "per_page": 10}
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                for event in data["data"]:
                    home = event.get("home_team", {})
                    away = event.get("away_team", {})
                    if home.get("name") and away.get("name"):
                        matches.append({
                            "id": str(event.get("id")),
                            "team1": home.get("name"),
                            "team2": away.get("name"),
                            "begin_at": event.get("start_time"),
                            "league": "La Liga",
                            "game": "Football",
                            "odds": event.get("consensus", {})
                        })
    except Exception as e:
        print(f"La Liga error: {e}")
    
    return matches


def make_prediction(match):
    """Make prediction based on BetStack odds"""
    odds = match.get("odds", {})
    team1 = match["team1"]
    team2 = match["team2"]
    
    # Get moneyline odds
    home_ml = odds.get("home_moneyline")
    away_ml = odds.get("away_moneyline")
    
    # If we have odds, use them for prediction
    if home_ml and away_ml:
        # Lower odds = higher probability
        if home_ml < away_ml:
            return team1
        elif away_ml < home_ml:
            return team2
        else:
            return team1  # Default to home team
    
    # Fallback: home team advantage
    return team1


def get_odds_text(match):
    """Format odds for display"""
    odds = match.get("odds", {})
    home_ml = odds.get("home_moneyline")
    away_ml = odds.get("away_moneyline")
    spread = odds.get("spread")
    total = odds.get("total")
    
    text = ""
    if home_ml and away_ml:
        text += f"💰 ML: {team1} {home_ml} | {team2} {away_ml}\n"
    if spread:
        text += f"📊 Spread: {spread}\n"
    if total:
        text += f"🎯 Total: {total}\n"
    
    return text


# ============ RESULTS ============
def check_results():
    sent = load_sent_predictions()
    if not sent:
        return []
    
    results = []
    headers = {"X-API-Key": BETSTACK_API_KEY}
    
    for match_id, info in list(sent.items()):
        try:
            url = f"https://api.betstack.dev/api/v1/events/{match_id}"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                event = data.get("data", {})
                
                if event.get("status") == "final":
                    home_score = event.get("home_score")
                    away_score = event.get("away_score")
                    
                    if home_score is not None and away_score is not None:
                        if home_score > away_score:
                            winner = info["team1"]
                        elif away_score > home_score:
                            winner = info["team2"]
                        else:
                            winner = "Draw"
                        
                        prediction_won = winner == info["prediction"]
                        result_emoji = "✅" if prediction_won else "❌"
                        
                        results.append({
                            "game": info["game"],
                            "team1": info["team1"],
                            "team2": info["team2"],
                            "score": f"{home_score} - {away_score}",
                            "winner": winner,
                            "prediction": info["prediction"],
                            "won": prediction_won,
                            "emoji": result_emoji
                        })
                        
                        del sent[match_id]
                        
        except Exception as e:
            print(f"Error checking {match_id}: {e}")
    
    save_sent_predictions(sent)
    return results


# ============ MAIN ============
def send_predictions():
    matches = get_betstack_matches()
    
    if not matches:
        send_message("🎯 No matches found. Will try again later.")
        return
    
    sent = load_sent_predictions()
    
    message = "🎯 <b>Predictions (BetStack)</b>\n\n"
    count = 0
    
    for match in matches[:12]:
        if count >= 10:
            break
            
        team1 = match["team1"]
        team2 = match["team2"]
        
        prediction = make_prediction(match)
        
        game_emoji = {
            "Football": "⚽",
            "Hockey": "🏒",
            "Basketball": "🏀"
        }.get(match["game"], "🏆")
        
        begin_time = match["begin_at"]
        if begin_time:
            try:
                dt = datetime.fromisoformat(begin_time.replace("Z", "+00:00"))
                time_str = dt.strftime("%d.%m %H:%M")
            except:
                time_str = "TBD"
        else:
            time_str = "TBD"
        
        message += f"{game_emoji} <b>{match['game']}</b>\n"
        message += f"{team1} vs {team2}\n"
        message += f"🏆 Prediction: {prediction}\n"
        
        # Add odds if available
        odds_text = get_odds_text(match)
        if odds_text:
            message += odds_text
        
        message += f"⏰ {time_str} | {match['league']}\n\n"
        
        sent[match["id"]] = {
            "game": match["game"],
            "team1": team1,
            "team2": team2,
            "prediction": prediction,
            "begin_at": begin_time
        }
        
        count += 1
    
    save_sent_predictions(sent)
    message += f"📊 Total: {count} predictions"
    send_message(message)


def send_results():
    results = check_results()
    if not results:
        return
    
    message = "📊 <b>Results</b>\n\n"
    wins = 0
    
    for r in results:
        game_emoji = {
            "Football": "⚽",
            "Hockey": "🏒",
            "Basketball": "🏀"
        }.get(r["game"], "🏆")
        
        message += f"{game_emoji} {r['team1']} vs {r['team2']}\n"
        message += f"Score: {r['score']} {r['emoji']}\n"
        message += f"Winner: {r['winner']}\n\n"
        
        if r["won"]:
            wins += 1
    
    total = len(results)
    win_rate = (wins / total * 100) if total > 0 else 0
    message += f"📈 Win Rate: {wins}/{total} ({win_rate:.0f}%)"
    send_message(message)


if __name__ == "__main__":
    send_message("🎯 Sports Predictions (BetStack)")
    send_predictions()
    send_results()