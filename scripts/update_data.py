import json
import urllib.request
import os

ESPN_NFL_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"

def fetch_nfl_data():
    req = urllib.request.Request(
        ESPN_NFL_TEAMS_URL, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
    teams_list = []
    
    # 32개 팀 데이터 파싱
    for item in data.get('sports', [])[0].get('leagues', [])[0].get('teams', []):
        t = item.get('team', {})
        team_id = t.get('abbreviation')
        name = t.get('displayName')
        logo = t.get('logos', [{}])[0].get('href', '')
        record_summary = t.get('record', {}).get('items', [{}])[0].get('summary', '0-0')
        
        teams_list.append({
            "id": team_id,
            "name": name,
            "record": record_summary,
            "logo": logo,
            "normElo": 80,
            "normEpa": 75,
            "normSr": 75,
            "normRecency": 75,
            "prevRank": 16
        })
        
    # nfl_data.json 파일로 저장
    output_path = "nfl_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(teams_list, f, ensure_ascii=False, indent=2)
    print(f"Successfully generated {output_path} with {len(teams_list)} teams.")

if __name__ == "__main__":
    fetch_nfl_data()
