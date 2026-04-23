import requests
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
    matches = []
    headers = {"X-API-Key": BETSTACK_API_KEY}
    
    # Try different league formats
    league_tests = [
        ("american_basketball_nba", "NBA", "Basketball"),
        ("basketball_nba", "NBA", "Basketball"),
        ("nba", "NBA", "Basketball"),
        ("ice_hockey_nhl", "NHL", "Hockey"),
        ("hockey_nhl", "NHL", "Hockey"),
        ("nhl", "NHL", "Hockey"),
    ]
    
    for league_slug, league_name, game_type in league_tests:
        try:
            url = f"https://api.betstack.dev/api/v1/events?league={league_slug}&per_page=20"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                events = data if isinstance(data, list) else data.get("data", [])
                
                for event in events:
                    # Extract team names properly
                    home = event.get("home_team")
                    away = event.get("away_team")
                    
                    # Handle both string and dict formats
                    if isinstance(home, dict):
                        home_name = home.get("name", "")
                    else:
                        home_name = str(home) if home else ""
                        
                    if isinstance(away, dict):
                        away_name = away.get("name", "")
                    else:
                        away_name = str(away) if away else ""
                    
                    if not home_name or not away_name:
                        continue
                    
                    # Get commence_time
                    commence = event.get("commence_time") or event.get("start_time") or ""
                    
                    # Parse date and filter to next 48 hours
                    if commence:
                        try:
                            dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                            now = datetime.now(dt.tzinfo)
                            hours_diff = (dt - now).total_seconds() / 3600
                            # Only include matches in next 48 hours
                            if hours_diff < 0 or hours_diff > 48:
                                continue
                        except:
                            pass
                    
                    # Get odds from lines
                    lines = event.get("lines", [])
                    odds = {}
                    for line in lines:
                        if line.get("type") == "moneyline":
                            odds["home_ml"] = line.get("home_price")
                            odds["away_ml"] = line.get("away_price")
                    
                    matches.append({
                        "id": str(event.get("id")),
                        "team1": home_name,
                        "team2": away_name,
                        "begin_at": commence,
                        "league": league_name,
                        "game": game_type,
                        "odds": odds
                    })
        except Exception as e:
            print(f"{league_slug} error: {e}")
    
    return matches


def make_prediction(match):
    odds = match.get("odds", {})
    team1 = match["team1"]
    team2 = match["team2"]
    
    home_ml = odds.get("home_ml")
    away_ml = odds.get("away_ml")
    
    if home_ml and away_ml:
        try:
            home_val = int(home_ml)
            away_val = int(away_ml)
            if home_val < away_val:
                return team1
            elif away_val < home_val:
                return team2
        except:
            pass
    
    return team1


def get_odds_text(match):
    odds = match.get("odds", {})
    team1 = match["team1"]
    team2 = match["team2"]
    
    home_ml = odds.get("home_ml")
    away_ml = odds.get("away_ml")
    
    if home_ml and away_ml:
        return f"💰 {team1} {home_ml} | {team2} {away_ml}\n"
    return ""


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
                event = response.json()
                if isinstance(event, dict):
                    event = event.get("data", event)
                
                result = event.get("result", {})
                if result.get("final"):
                    home_score = result.get("home_score")
                    away_score = result.get("away_score")
                    
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
        send_message("🎯 No upcoming matches in 48h. Try again later.")
        return
    
    sent = load_sent_predictions()
    
    message = "🎯 <b>Predictions (BetStack)</b>\n\n"
    count = 0
    
    for match in matches[:10]:
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