import json
import urllib.request
import sys
import os

ESPN_NFL_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"

def fetch_nfl_data():
    try:
        req = urllib.request.Request(
            ESPN_NFL_TEAMS_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
        teams_list = []
        leagues = data.get('sports', [{}])[0].get('leagues', [{}])[0]
        teams_data = leagues.get('teams', [])

        for idx, item in enumerate(teams_data):
            t = item.get('team', {})
            team_id = t.get('abbreviation', f'T{idx}')
            name = t.get('displayName', 'NFL Team')
            logos = t.get('logos', [])
            logo = logos[0].get('href', '') if logos else ''
            
            record_items = t.get('record', {}).get('items', [])
            record_summary = record_items[0].get('summary', '0-0') if record_items else '0-0'
            
            teams_list.append({
                "id": team_id,
                "name": name,
                "record": record_summary,
                "logo": logo,
                "normElo": 80,
                "normEpa": 75,
                "normSr": 75,
                "normRecency": 75,
                "prevRank": idx + 1
            })
            
        output_path = "nfl_data.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(teams_list, f, ensure_ascii=False, indent=2)
            
        print(f"Success: wrote {len(teams_list)} teams to {output_path}")

    except Exception as e:
        print(f"Error fetching NFL data: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    fetch_nfl_data()
