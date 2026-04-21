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


# ============ BALLDONTLIE API (NBA) ============
def get_nba_matches():
    matches = []
    try:
        # Get matches for today and tomorrow
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        for date in [today, tomorrow]:
            date_str = date.strftime("%Y-%m-%d")
            url = f"https://www.balldontlie.io/api/v1/games?dates[]={date_str}&per_page=15"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    for game in data["data"]:
                        home_team = game.get("home_team", {}).get("full_name", "")
                        away_team = game.get("visitor_team", {}).get("full_name", "")
                        
                        if home_team and away_team:
                            matches.append({
                                "id": str(game["id"]),
                                "team1": home_team,
                                "team2": away_team,
                                "begin_at": game.get("datetime", ""),
                                "league": "NBA",
                                "game": "Basketball"
                            })
    except Exception as e:
        print(f"NBA error: {e}")
    return matches


# ============ THE SPORTS DB - NEXT 24 HOURS ============
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
            # Get next 5 events (covers ~24 hours)
            url = f"https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id={league_id}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("events"):
                    for event in data["events"][:5]:
                        home_team = event.get("strHomeTeam", "")
                        away_team = event.get("strAwayTeam", "")
                        
                        if home_team and away_team and home_team != "Unknown" and away_team != "Unknown":
                            matches.append({
                                "id": str(event["idEvent"]),
                                "team1": home_team,
                                "team2": away_team,
                                "begin_at": event.get("strTimestamp", ""),
                                "league": league_name,
                                "game": "Football"
                            })
        except Exception as e:
            print(f"Error fetching {league_name}: {e}")
    
    return matches


# ============ PREDICTION LOGIC ============
def get_team_info(team_name):
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
    info1 = get_team_info(team1)
    info2 = get_team_info(team2)
    
    score1 = random.randint(40, 60)
    score2 = random.randint(40, 60)
    
    # Home advantage
    score1 += 10
    
    # Older teams get slight boost
    try:
        if info1.get("formed") and int(info1.get("formed", 0)) < 1990:
            score1 += 5
        if info2.get("formed") and int(info2.get("formed", 0)) < 1990:
            score2 += 5
    except:
        pass
    
    if score1 > score2:
        return team1
    elif score2 > score1:
        return team2
    else:
        return random.choice([team1, team2, "Draw"])


# ============ RESULTS ============
def check_results():
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
    
    # Get football from TheSportsDB (next 24h)
    matches.extend(get_sportsdb_matches())
    
    # Get NBA from Balldontlie (today + tomorrow)
    matches.extend(get_nba_matches())
    
    if not matches:
        send_message("⚽ No matches found. Will try again later.")
        return
    
    sent = load_sent_predictions()
    
    message = "🎯 <b>Predictions (Next 24h)</b>\n\n"
    count = 0
    
    for match in matches[:15]:
        if count >= 10:
            break
            
        team1 = match["team1"]
        team2 = match["team2"]
        
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
                time_str = dt.strftime("%d.%m %H:%M")
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
    send_message("🎯 Sports Predictions (Next 24h)")
    send_predictions()
    send_results()