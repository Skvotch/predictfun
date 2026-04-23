import requests
import time
import json
import os
import random
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
    
    # NBA
    try:
        url = "https://api.betstack.dev/api/v1/events?league=american_basketball_nba&status=pregame"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                for event in data["data"][:5]:
                    home = event.get("home_team", {})
                    away = event.get("visitor_team", {})
                    if home.get("name") and away.get("name"):
                        odds = event.get("consensus_odds", {})
                        matches.append({
                            "id": str(event["id"]),
                            "team1": home["name"],
                            "team2": away["name"],
                            "begin_at": event.get("start_time", ""),
                            "league": "NBA",
                            "game": "Basketball",
                            "odds": odds
                        })
    except Exception as e:
        print(f"BetStack NBA error: {e}")
    
    # NHL
    try:
        url = "https://api.betstack.dev/api/v1/events?league=hockey_nhl&status=pregame"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                for event in data["data"][:5]:
                    home = event.get("home_team", {})
                    away = event.get("visitor_team", {})
                    if home.get("name") and away.get("name"):
                        odds = event.get("consensus_odds", {})
                        matches.append({
                            "id": str(event["id"]),
                            "team1": home["name"],
                            "team2": away["name"],
                            "begin_at": event.get("start_time", ""),
                            "league": "NHL",
                            "game": "Hockey",
                            "odds": odds
                        })
    except Exception as e:
        print(f"BetStack NHL error: {e}")
    
    # Soccer - EPL
    try:
        url = "https://api.betstack.dev/api/v1/events?league=soccer_epl&status=pregame"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                for event in data["data"][:5]:
                    home = event.get("home_team", {})
                    away = event.get("visitor_team", {})
                    if home.get("name") and away.get("name"):
                        odds = event.get("consensus_odds", {})
                        matches.append({
                            "id": str(event["id"]),
                            "team1": home["name"],
                            "team2": away["name"],
                            "begin_at": event.get("start_time", ""),
                            "league": "EPL",
                            "game": "Football",
                            "odds": odds
                        })
    except Exception as e:
        print(f"BetStack EPL error: {e}")
    
    return matches


# ============ FALLBACK: THE SPORTS DB ============
def get_sportsdb_matches():
    matches = []
    
    football_leagues = {
        "4328": "Premier League",
        "4335": "La Liga",
        "4562": "Serie A",
        "4481": "Bundesliga",
        "4554": "Ligue 1"
    }
    
    for league_id, league_name in football_leagues.items():
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id={league_id}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("events"):
                    for event in data["events"][:3]:
                        home_team = event.get("strHomeTeam", "")
                        away_team = event.get("strAwayTeam", "")
                        
                        if home_team and away_team and home_team != "Unknown":
                            matches.append({
                                "id": str(event["idEvent"]),
                                "team1": home_team,
                                "team2": away_team,
                                "begin_at": event.get("strTimestamp", ""),
                                "league": league_name,
                                "game": "Football",
                                "odds": {}
                            })
        except Exception as e:
            print(f"Error fetching {league_name}: {e}")
    
    return matches


# ============ PREDICTION LOGIC ============
def make_prediction(match):
    team1 = match["team1"]
    team2 = match["team2"]
    odds = match.get("odds", {})
    
    if odds:
        home_ml = odds.get("home_moneyline")
        away_ml = odds.get("away_moneyline")
        
        if home_ml and away_ml:
            if home_ml < away_ml:
                return team1
            elif away_ml < home_ml:
                return team2
    
    score1 = random.randint(40, 60) + 10
    score2 = random.randint(40, 60)
    
    if score1 > score2:
        return team1
    elif score2 > score1:
        return team2
    else:
        return random.choice([team1, team2, "Draw"])


def get_odds_text(odds):
    if not odds:
        return ""
    
    lines = []
    home_ml = odds.get("home_moneyline")
    away_ml = odds.get("away_moneyline")
    
    if home_ml:
        lines.append(f"Home: {home_ml}")
    if away_ml:
        lines.append(f"Away: {away_ml}")
    
    return " | " + ", ".join(lines) if lines else ""


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
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event = data.get("data", {})
                
                if event.get("status") == "final":
                    home_score = event.get("home_score")
                    away_score = event.get("visitor_score")
                    
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
                        continue
        except:
            pass
        
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/1/eventresults.php?id={match_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event = data.get("event")
                
                if event and event.get("strStatus") == "Final":
                    home_score = event.get("intHomeScore")
                    away_score = event.get("intAwayScore")
                    
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
    matches = []
    
    betstack_matches = get_betstack_matches()
    matches.extend(betstack_matches)
    
    if not matches:
        matches.extend(get_sportsdb_matches())
    
    if not matches:
        send_message("⚽ No matches found. Will try again later.")
        return
    
    sent = load_sent_predictions()
    
    message = "🎯 <b>Predictions (Next 24h)</b>\n\n"
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
            "Basketball": "🏀",
            "CS2": "🎮"
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
        
        odds_text = get_odds_text(match.get("odds", {}))
        
        message += f"{game_emoji} <b>{match['game']}</b>\n"
        message += f"{team1} vs {team2}\n"
        message += f"🏆 Prediction: {prediction}{odds_text}\n"
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
    send_message("🎯 Sports Predictions (BetStack)")
    send_predictions()
    send_results()