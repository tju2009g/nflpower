import json
import urllib.request
import sys
import os

# GitHub Actions 환경에서도 403 차단 없는 공개 스코어보드 엔드포인트
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

def fetch_nfl_data():
    try:
        # 실제 최신 Chrome 브라우저 헤더 세팅 (403 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.espn.com/'
        }
        
        req = urllib.request.Request(ESPN_SCOREBOARD_URL, headers=headers)
        
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        teams_list = []
        events = data.get('events', [])

        # 경기 이벤트에서 팀 정보 파싱
        added_teams = set()
        for event in events:
            competitions = event.get('competitions', [{}])[0]
            competitors = competitions.get('competitors', [])
            
            for competitor in competitors:
                team_data = competitor.get('team', {})
                team_id = team_data.get('abbreviation')
                
                if team_id and team_id not in added_teams:
                    added_teams.add(team_id)
                    name = team_data.get('displayName', 'NFL Team')
                    logo = team_data.get('logo', '')
                    records = competitor.get('records', [])
                    record_summary = records[0].get('summary', '0-0') if records else '0-0'
                    
                    teams_list.append({
                        "id": team_id,
                        "name": name,
                        "record": record_summary,
                        "logo": logo,
                        "normElo": 80,
                        "normEpa": 75,
                        "normSr": 75,
                        "normRecency": 75,
                        "prevRank": len(added_teams)
                    })

        # 만약 비시즌이거나 경기 주간이 아니어서 빈 목록일 경우 대비 (Fallback 기본 템플릿 보존)
        if not teams_list:
            print("Notice: No live games found in scoreboard. Retaining baseline structure.")
            teams_list = [
                {"id": "KC", "name": "Kansas City Chiefs", "record": "1-0", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "normElo": 97, "normEpa": 93, "normSr": 90, "normRecency": 95, "prevRank": 1},
                {"id": "SF", "name": "San Francisco 49ers", "record": "1-0", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "normElo": 93, "normEpa": 90, "normSr": 94, "normRecency": 88, "prevRank": 2}
            ]

        output_path = "nfl_data.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(teams_list, f, ensure_ascii=False, indent=2)
            
        print(f"Success: Wrote {len(teams_list)} teams data to {output_path}")

    except Exception as e:
        print(f"Error fetching NFL data: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    fetch_nfl_data()
