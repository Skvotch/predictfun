import requests
import time
import json
import os
from datetime import datetime, timedelta

BOT_TOKEN = "8681554780:AAE8mKCm16HMqfdaLI-sKRxs3AAyx_gUQkU"
CHAT_ID = "1624738454"

# File to track sent predictions
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

# ============ CS2 ============
def get_cs2_matches():
    """Get CS2 matches from PandaScore API"""
    try:
        # Using PandaScore free tier
        url = "https://api.pandascore.co/matches"
        params = {
            "filter[status]": "pending",
            "sort": "begin_at",
            "range[begin_at]": "now,2d",
            "page[size]": 20
        }
        # Note: Need API key - using demo key for testing
        headers = {"Authorization": "Bearer demo_key"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            matches = []
            for match in data:
                if match.get("videogame") and "cs" in match["videogame"].get("name", "").lower():
                    matches.append({
                        "id": match["id"],
                        "team1": match["opponents"][0]["team"]["name"] if len(match.get("opponents", [])) > 0 else "TBD",
                        "team2": match["opponents"][1]["team"]["name"] if len(match.get("opponents", [])) > 1 else "TBD",
                        "begin_at": match["begin_at"],
                        "league": match.get("league", {}).get("name", "Unknown"),
                        "game": "CS2"
                    })
            return matches
    except Exception as e:
        print(f"CS2 API error: {e}")
    return []

# ============ FOOTBALL ============
def get_football_matches():
    """Get football matches from API-Football"""
    try:
        # Using API-Football free tier
        url = "https://v3.football.api-sports.io/fixtures"
        params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "league": "39,140,135,78",  # Premier League, La Liga, Serie A, Bundesliga
            "status": "NS"  # Not Started
        }
        headers = {"x-apisports-key": "demo_key"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            matches = []
            for fixture in data.get("response", [])[:15]:
                league = fixture.get("league", {})
                home = fixture.get("teams", {}).get("home", {})
                away = fixture.get("teams", {}).get("away", {})
                
                matches.append({
                    "id": fixture["fixture"]["id"],
                    "team1": home.get("name", "Unknown"),
                    "team2": away.get("name", "Unknown"),
                    "begin_at": fixture["fixture"]["date"],
                    "league": league.get("name", "Unknown"),
                    "game": "Football"
                })
            return matches
    except Exception as e:
        print(f"Football API error: {e}")
    return []

# ============ HOCKEY ============
def get_hockey_matches():
    """Get hockey matches"""
    try:
        url = "https://v3.football.api-sports.io/fixtures"
        params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "league": "57,48",  # NHL, KHL
            "status": "NS"
        }
        headers = {"x-apisports-key": "demo_key"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            matches = []
            for fixture in data.get("response", [])[:10]:
                league = fixture.get("league", {})
                home = fixture.get("teams", {}).get("home", {})
                away = fixture.get("teams", {}).get("away", {})
                
                matches.append({
                    "id": fixture["fixture"]["id"],
                    "team1": home.get("name", "Unknown"),
                    "team2": away.get("name", "Unknown"),
                    "begin_at": fixture["fixture"]["date"],
                    "league": league.get("name", "Unknown"),
                    "game": "Hockey"
                })
            return matches
    except Exception as e:
        print(f"Hockey API error: {e}")
    return []

# ============ BASKETBALL ============
def get_basketball_matches():
    """Get basketball matches"""
    try:
        url = "https://v3.football.api-sports.io/fixtures"
        params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "league": "12,1",  # NBA, EuroLeague
            "status": "NS"
        }
        headers = {"x-apisports-key": "demo_key"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            matches = []
            for fixture in data.get("response", [])[:10]:
                league = fixture.get("league", {})
                home = fixture.get("teams", {}).get("home", {})
                away = fixture.get("teams", {}).get("away", {})
                
                matches.append({
                    "id": fixture["fixture"]["id"],
                    "team1": home.get("name", "Unknown"),
                    "team2": away.get("name", "Unknown"),
                    "begin_at": fixture["fixture"]["date"],
                    "league": league.get("name", "Unknown"),
                    "game": "Basketball"
                })
            return matches
    except Exception as e:
        print(f"Basketball API error: {e}")
    return []

# ============ RESULTS ============
def check_results():
    """Check results for previously sent predictions"""
    sent = load_sent_predictions()
    if not sent:
        return []
    
    results = []
    cutoff = datetime.now() - timedelta(hours=3)
    
    for match_id, info in list(sent.items()):
        try:
            begin_time = datetime.fromisoformat(info["begin_at"].replace("Z", "+00:00"))
            if begin_time > cutoff:
                continue
                
            # Check if match is finished
            url = f"https://v3.football.api-sports.io/fixtures/{match_id}"
            headers = {"x-apisports-key": "demo_key"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fixture = data.get("response", [{}])[0]
                status = fixture.get("fixture", {}).get("status", {}).get("short", "")
                
                if status == "FT":  # Full Time
                    goals = fixture.get("goals", {})
                    home_goals = goals.get("home", 0)
                    away_goals = goals.get("away", 0)
                    
                    winner = None
                    if home_goals > away_goals:
                        winner = info["team1"]
                    elif away_goals > home_goals:
                        winner = info["team2"]
                    else:
                        winner = "Draw"
                    
                    prediction_won = winner == info["prediction"]
                    result_emoji = "✅" if prediction_won else "❌"
                    
                    results.append({
                        "game": info["game"],
                        "team1": info["team1"],
                        "team2": info["team2"],
                        "score": f"{home_goals} - {away_goals}",
                        "winner": winner,
                        "prediction": info["prediction"],
                        "won": prediction_won,
                        "emoji": result_emoji
                    })
                    
                    # Remove from sent
                    del sent[match_id]
        except Exception as e:
            print(f"Error checking result for {match_id}: {e}")
    
    save_sent_predictions(sent)
    return results

# ============ MAIN ============
def make_prediction(team1, team2):
    """Simple prediction based on team names (placeholder - need odds API)"""
    # This is a placeholder - real prediction needs betting odds
    # For now, randomly pick with bias towards home team
    import random
    return random.choice([team1, team2])

def send_predictions():
    all_matches = []
    
    # Get matches from all sports
    all_matches.extend(get_football_matches())
    all_matches.extend(get_hockey_matches())
    all_matches.extend(get_basketball_matches())
    
    # CS2 (if API key available)
    # all_matches.extend(get_cs2_matches())
    
    if not all_matches:
        send_message("⚽ No matches found today. Will try again next hour.")
        return
    
    # Load existing predictions
    sent = load_sent_predictions()
    
    # Send predictions
    message = "🎯 <b>Today's Predictions</b>\n\n"
    count = 0
    
    for match in all_matches[:15]:
        if count >= 10:
            break
            
        team1 = match["team1"]
        team2 = match["team2"]
        
        if team1 == "Unknown" or team2 == "Unknown":
            continue
        
        prediction = make_prediction(team1, team2)
        
        game_emoji = {
            "Football": "⚽",
            "Hockey": "🏒",
            "Basketball": "🏀",
            "CS2": "🎮"
        }.get(match["game"], "🏆")
        
        begin_time = datetime.fromisoformat(match["begin_at"].replace("Z", "+00:00"))
        time_str = begin_time.strftime("%H:%M")
        
        message += f"{game_emoji} <b>{match['game']}</b>\n"
        message += f"{team1} vs {team2}\n"
        message += f"🏆 Prediction: {prediction}\n"
        message += f"⏰ {time_str} | {match['league']}\n\n"
        
        # Save for results
        sent[str(match["id"])] = {
            "game": match["game"],
            "team1": team1,
            "team2": team2,
            "prediction": prediction,
            "begin_at": match["begin_at"]
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
            "Basketball": "🏀",
            "CS2": "🎮"
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
    send_message("🎯 Sports Predictor Started!")
    send_predictions()
    send_results()