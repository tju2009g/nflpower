import json
import csv
import io
import os
import urllib.request
from datetime import datetime, timezone

NFLVERSE_GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
NAME_MAP = {'LA': 'LAR', 'OAK': 'LV', 'SD': 'LAC', 'STL': 'LAR'}

# 프론트엔드 기본 슬라이더 가중치(40/30/15/15)와 동일하게 맞춰서
# "사이트가 기본으로 보여주는 순위"가 곧 "우리가 실제로 베팅하는 예측"이 되게 함.
WEIGHTS = {'elo': 0.4, 'epa': 0.3, 'sr': 0.15, 'recency': 0.15}


def blend(team):
    return (
        team['normElo'] * WEIGHTS['elo']
        + team['normEpa'] * WEIGHTS['epa']
        + team['normSr'] * WEIGHTS['sr']
        + team['normRecency'] * WEIGHTS['recency']
    )


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default


def main():
    teams = json.load(open('nfl_data.json', encoding='utf-8'))
    by_id = {t['id']: t for t in teams}

    req = urllib.request.Request(NFLVERSE_GAMES_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=25) as resp:
        csv_text = resp.read().decode('utf-8')
    rows = list(csv.DictReader(io.StringIO(csv_text)))

    seasons_with_scores = [
        int(r['season']) for r in rows
        if r.get('game_type') == 'REG' and r.get('home_score') and r.get('away_score')
    ]
    target_season = (
        max(seasons_with_scores) if seasons_with_scores
        else max(int(r['season']) for r in rows if r.get('game_type') == 'REG')
    )

    store = load_json('predictions.json', {"games": {}, "summary": {}})
    games_store = store['games']
    now_iso = datetime.now(timezone.utc).isoformat()

    # 아직 시작 안 한 경기 중 가장 빠른 주(week)만 새로 예측 대상으로 삼는다.
    # 시즌 전체를 한 번에 미리 예측해버리면, 뒤쪽 주차 예측이 "1주차 데이터만
    # 반영된 미성숙한 지표"로 영구 고정되는 문제가 생긴다 — 매주 갱신되는
    # 예측이라는 취지에 맞게, 딱 다음 한 주만 그 시점 최신 지표로 예측한다.
    incomplete_weeks = [
        int(r['week']) for r in rows
        if str(r.get('season')) == str(target_season)
        and r.get('game_type') == 'REG'
        and not (r.get('home_score') and r.get('away_score'))
    ]
    next_week_to_predict = min(incomplete_weeks) if incomplete_weeks else None

    for row in rows:
        if str(row.get('season')) != str(target_season) or row.get('game_type') != 'REG':
            continue

        home = NAME_MAP.get(row['home_team'], row['home_team'])
        away = NAME_MAP.get(row['away_team'], row['away_team'])
        if home not in by_id or away not in by_id:
            continue

        week = row.get('week')
        game_key = f"{target_season}-{week}-{away}-{home}"
        has_score = bool(row.get('home_score')) and bool(row.get('away_score'))

        if game_key not in games_store:
            # 아직 결과가 없는 경기 중, "다음에 열릴 주차"에 한해서만 새 예측을 만든다.
            if not has_score and int(week) == next_week_to_predict:
                away_b = round(blend(by_id[away]), 1)
                home_b = round(blend(by_id[home]), 1)
                games_store[game_key] = {
                    "season": target_season,
                    "week": int(week) if week else None,
                    "away": away,
                    "home": home,
                    "away_blend": away_b,
                    "home_blend": home_b,
                    "predicted_winner": home if home_b > away_b else away,
                    "predicted_at": now_iso,
                    "actual_winner": None,
                    "correct": None,
                    "settled_at": None,
                }
            continue

        # 이미 예측이 저장돼 있고 아직 정산 안 됐는데 스코어가 들어왔으면 정산.
        entry = games_store[game_key]
        if entry['actual_winner'] is None and has_score:
            try:
                h_score = int(float(row['home_score']))
                a_score = int(float(row['away_score']))
            except ValueError:
                continue
            if h_score == a_score:
                continue  # 타이는 정산 제외
            actual_winner = home if h_score > a_score else away
            entry['actual_winner'] = actual_winner
            entry['correct'] = (actual_winner == entry['predicted_winner'])
            entry['settled_at'] = now_iso

    settled = [g for g in games_store.values() if g['correct'] is not None]
    correct = [g for g in settled if g['correct']]

    by_week = {}
    for g in settled:
        wk = g['week']
        by_week.setdefault(wk, {'total': 0, 'correct': 0})
        by_week[wk]['total'] += 1
        if g['correct']:
            by_week[wk]['correct'] += 1

    store['summary'] = {
        "season": target_season,
        "total_settled": len(settled),
        "total_correct": len(correct),
        "accuracy": round(len(correct) / len(settled), 3) if settled else None,
        "by_week": by_week,
        "updated_at": now_iso,
    }

    with open('predictions.json', 'w', encoding='utf-8') as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

    print(
        f"Predictions updated: {len(games_store)} total tracked, "
        f"{len(settled)} settled, accuracy={store['summary']['accuracy']}"
    )


if __name__ == "__main__":
    main()
