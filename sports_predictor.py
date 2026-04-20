import requests
import time
import json
import os
import random
from datetime import datetime, timedelta

BOT_TOKEN = "8681554780:AAE8mKCm16HMqfdaLI-sKRxs3AAyx_gUQkU"
CHAT_ID = "1624738454"

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

# ============ THE SPORTS DB ============
def get_sportsdb_matches():
    """Get matches from TheSportsDB (free, no key)"""
    matches = []
    
    # Football - Today's matches from major leagues
    football_leagues = {
        "4328": "English Premier League",
        "4335": "Spanish La Liga",
        "4331": "Italian Serie A",
        "4332": "German Bundesliga",
        "4334": "French Ligue 1"
    }
    
    for league_id, league_name in football_leagues.items():
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id={league_id}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("events"):
                    for event in data["events"]:
                        matches.append({
                            "id": str(event["idEvent"]),
                            "team1": event.get("strHomeTeam", "Unknown"),
                            "team2": event.get("strAwayTeam", "Unknown"),
                            "begin_at": event.get("strTimestamp", ""),
                            "league": league_name,
                            "game": "Football"
                        })
        except Exception as e:
            print(f"Error fetching {league_name}: {e}")
    
    # Basketball - NBA
    try:
        url = "https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id=4387"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("events"):
                for event in data["events"][:5]:
                    matches.append({
                        "id": str(event["idEvent"]),
                        "team1": event.get("strHomeTeam", "Unknown"),
                        "team2": event.get("strAwayTeam", "Unknown"),
                        "begin_at": event.get("strTimestamp", ""),
                        "league": "NBA",
                        "game": "Basketball"
                    })
    except Exception as e:
        print(f"Error fetching NBA: {e}")
    
    # Hockey - NHL
    try:
        url = "https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id=4388"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("events"):
                for event in data["events"][:5]:
                    matches.append({
                        "id": str(event["idEvent"]),
                        "team1": event.get("strHomeTeam", "Unknown"),
                        "team2": event.get("strAwayTeam", "Unknown"),
                        "begin_at": event.get("strTimestamp", ""),
                        "league": "NHL",
                        "game": "Hockey"
                    })
    except Exception as e:
        print(f"Error fetching NHL: {e}")
    
    return matches

# ============ CS2 FROM LIQUIPEDIA (PARSING) ============
def get_cs2_matches():
    """Get CS2 matches from Liquipedia (scraping)"""
    matches = []
    
    try:
        url = "https://liquipedia.net/counterstrike/api.php"
        params = {
            "action": "parse",
            "page": "Liquipedia:Current_and_upcoming_matches",
            "format": "json"
        }
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Parse HTML content
            html = data.get("parse", {}).get("text", {}).get("*", "")
            
            # Simple parsing - look for match patterns
            # This is a simplified version
            pass
            
    except Exception as e:
        print(f"CS2 error: {e}")
    
    return matches

# ============ PREDICTION LOGIC ============
def get_team_stats(team_name):
    """Get team statistics from TheSportsDB"""
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/1/searchteams.php?t={team_name}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("teams"):
                team = data["teams"][0]
                return {
                    "name": team.get("strTeam", ""),
                    "formed": team.get("intFormedYear", ""),
                    "country": team.get("strCountry", ""),
                    "league": team.get("strLeague", "")
                }
    except:
        pass
    return {}

def make_prediction(team1, team2, game):
    """Make prediction based on available data"""
    
    # For now, use a combination of:
    # 1. Home team advantage (slight bias)
    # 2. Random factor
    # 3. Team "form" (simulated)
    
    # Get team info
    info1 = get_team_stats(team1)
    info2 = get_team_stats(team2)
    
    # Calculate simple score based on various factors
    score1 = random.randint(40, 60)  # Base score
    score2 = random.randint(40, 60)
    
    # Home advantage
    score1 += 10
    
    # Older teams (more experience) get slight boost
    try:
        if info1.get("formed") and int(info1.get("formed", 0)) < 1990:
            score1 += 5
        if info2.get("formed") and int(info2.get("formed", 0)) < 1990:
            score2 += 5
    except:
        pass
    
    # Return winner
    if score1 > score2:
        return team1
    elif score2 > score1:
        return team2
    else:
        return random.choice([team1, team2, "Draw"])

# ============ RESULTS ============
def check_results():
    """Check results for previously sent predictions"""
    sent = load_sent_predictions()
    if not sent:
        return []
    
    results = []
    
    for match_id, info in list(sent.items()):
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/1/eventresults.php?id={match_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event = data.get("event")
                
                if event and event.get("strStatus") == "Final":
                    home_score = event.get("intHomeScore", 0)
                    away_score = event.get("intAwayScore", 0)
                    
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
    matches = get_sportsdb_matches()
    
    if not matches:
        send_message("⚽ No matches found today. Will try again later.")
        return
    
    sent = load_sent_predictions()
    
    message = "🎯 <b>Today's Predictions</b>\n\n"
    count = 0
    
    for match in matches[:15]:
        if count >= 10:
            break
            
        team1 = match["team1"]
        team2 = match["team2"]
        
        if team1 == "Unknown" or team2 == "Unknown":
            continue
        
        prediction = make_prediction(team1, team2, match["game"])
        
        game_emoji = {
            "Football": "⚽",
            "Hockey": "🏒",
            "Basketball": "🏀",
            "CS2": "🎮"
        }.get(match["game"], "🏆")
        
        begin_time = match["begin_at"]
        if begin_time:
            try:
                dt = datetime.fromisoformat(begin_time.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except:
                time_str = "TBD"
        else:
            time_str = "TBD"
        
        message += f"{game_emoji} <b>{match['game']}</b>\n"
        message += f"{team1} vs {team2}\n"
        message += f"🏆 Prediction: {prediction}\n"
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
    send_message("🎯 Sports Predictor Started! (Free API)")
    send_predictions()
    send_results()