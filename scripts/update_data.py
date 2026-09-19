import json
import urllib.request
import csv
import io
import sys

# nflverse 공식 원격 경기 일정 및 스코어 데이터
NFLVERSE_GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"

# 32개 팀 메타데이터. 팀 컬러(공개된 팬터스톤/브랜드 컬러값)만 사용 —
# 공식 로고 이미지는 상표/저작권 리스크가 있어 자체 제작 배지로 대체.
TEAM_METADATA = {
    'KC': {'name': 'Kansas City Chiefs', 'conf': 'AFC', 'div': 'West', 'colors': ('#E31837', '#FFB81C')},
    'SF': {'name': 'San Francisco 49ers', 'conf': 'NFC', 'div': 'West', 'colors': ('#AA0000', '#B3995D')},
    'BAL': {'name': 'Baltimore Ravens', 'conf': 'AFC', 'div': 'North', 'colors': ('#241773', '#9E7C0C')},
    'DET': {'name': 'Detroit Lions', 'conf': 'NFC', 'div': 'North', 'colors': ('#0076B6', '#B0B7BC')},
    'BUF': {'name': 'Buffalo Bills', 'conf': 'AFC', 'div': 'East', 'colors': ('#00338D', '#C60C30')},
    'PHI': {'name': 'Philadelphia Eagles', 'conf': 'NFC', 'div': 'East', 'colors': ('#004C54', '#A5ACAF')},
    'HOU': {'name': 'Houston Texans', 'conf': 'AFC', 'div': 'South', 'colors': ('#03202F', '#A71930')},
    'DAL': {'name': 'Dallas Cowboys', 'conf': 'NFC', 'div': 'East', 'colors': ('#041E42', '#869397')},
    'GB': {'name': 'Green Bay Packers', 'conf': 'NFC', 'div': 'North', 'colors': ('#203731', '#FFB612')},
    'MIA': {'name': 'Miami Dolphins', 'conf': 'AFC', 'div': 'East', 'colors': ('#008E97', '#FC4C02')},
    'LAR': {'name': 'Los Angeles Rams', 'conf': 'NFC', 'div': 'West', 'colors': ('#003594', '#FFA300')},
    'CIN': {'name': 'Cincinnati Bengals', 'conf': 'AFC', 'div': 'North', 'colors': ('#FB4F14', '#000000')},
    'PIT': {'name': 'Pittsburgh Steelers', 'conf': 'AFC', 'div': 'North', 'colors': ('#000000', '#FFB612')},
    'NYJ': {'name': 'New York Jets', 'conf': 'AFC', 'div': 'East', 'colors': ('#125740', '#FFFFFF')},
    'TB': {'name': 'Tampa Bay Buccaneers', 'conf': 'NFC', 'div': 'South', 'colors': ('#D50A0A', '#34302B')},
    'CHI': {'name': 'Chicago Bears', 'conf': 'NFC', 'div': 'North', 'colors': ('#0B162A', '#C83803')},
    'SEA': {'name': 'Seattle Seahawks', 'conf': 'NFC', 'div': 'West', 'colors': ('#002244', '#69BE28')},
    'JAX': {'name': 'Jacksonville Jaguars', 'conf': 'AFC', 'div': 'South', 'colors': ('#006778', '#9F792C')},
    'CLE': {'name': 'Cleveland Browns', 'conf': 'AFC', 'div': 'North', 'colors': ('#311D00', '#FF3C00')},
    'IND': {'name': 'Indianapolis Colts', 'conf': 'AFC', 'div': 'South', 'colors': ('#002C5F', '#A2AAAD')},
    'ATL': {'name': 'Atlanta Falcons', 'conf': 'NFC', 'div': 'South', 'colors': ('#A71930', '#000000')},
    'NO': {'name': 'New Orleans Saints', 'conf': 'NFC', 'div': 'South', 'colors': ('#D3BC8D', '#101820')},
    'MIN': {'name': 'Minnesota Vikings', 'conf': 'NFC', 'div': 'North', 'colors': ('#4F2683', '#FFC62F')},
    'LAC': {'name': 'Los Angeles Chargers', 'conf': 'AFC', 'div': 'West', 'colors': ('#0080C6', '#FFC20E')},
    'ARI': {'name': 'Arizona Cardinals', 'conf': 'NFC', 'div': 'West', 'colors': ('#97233F', '#000000')},
    'LV': {'name': 'Las Vegas Raiders', 'conf': 'AFC', 'div': 'West', 'colors': ('#000000', '#A5ACAF')},
    'TEN': {'name': 'Tennessee Titans', 'conf': 'AFC', 'div': 'South', 'colors': ('#0C2340', '#4B92DB')},
    'WAS': {'name': 'Washington Commanders', 'conf': 'NFC', 'div': 'East', 'colors': ('#5A1414', '#FFB612')},
    'DEN': {'name': 'Denver Broncos', 'conf': 'AFC', 'div': 'West', 'colors': ('#002244', '#FB4F14')},
    'NYG': {'name': 'New York Giants', 'conf': 'NFC', 'div': 'East', 'colors': ('#0B2265', '#A71930')},
    'NE': {'name': 'New England Patriots', 'conf': 'AFC', 'div': 'East', 'colors': ('#002244', '#C60C30')},
    'CAR': {'name': 'Carolina Panthers', 'conf': 'NFC', 'div': 'South', 'colors': ('#0085CA', '#101820')}
}

NAME_MAP = {'LA': 'LAR', 'OAK': 'LV', 'SD': 'LAC', 'STL': 'LAR'}

# 프리시즌 전문가 컨센서스 순위(1=최강, 32=최약) — PFT(NBC) 등 주요 매체의
# 시즌 개막 전 파워랭킹 기준. "로스터 전력에 대한 사전 기대치"를 외부 검증된
# 값으로 주입하기 위한 앵커. 매년 프리시즌 끝나면 이 값만 갱신하면 됨.
PRESEASON_RANK = {
    'SEA': 1, 'LAR': 2, 'HOU': 3, 'DEN': 4, 'BUF': 5, 'CHI': 6, 'NE': 7,
    'PHI': 8, 'JAX': 9, 'BAL': 10, 'CIN': 11, 'LAC': 12, 'KC': 13, 'DET': 14,
    'SF': 15, 'GB': 16, 'DAL': 17, 'PIT': 18, 'MIN': 19, 'NYG': 20, 'CAR': 21,
    'TB': 22, 'IND': 23, 'NO': 24, 'ATL': 25, 'TEN': 26, 'WAS': 27, 'MIA': 28,
    'NYJ': 29, 'LV': 30, 'CLE': 31, 'ARI': 32,
}


def preseason_prior_win_rate(tid):
    """프리시즌 순위(1~32)를 승률 프라이어(0.75~0.25)로 선형 변환.
    1위=0.75, 32위=0.25, 그 사이는 선형 보간. 완전 중립(0.5)이 아니라
    실제 전문가 컨센서스를 사전분포로 쓴다."""
    rank = PRESEASON_RANK.get(tid, 16.5)
    return 0.75 - (rank - 1) / 31 * 0.5


# 표본 부족 시 조기 포화(1경기만에 99/30 캡에 몰리는 문제)를 막기 위한
# 베이지안 축소 상수 — 득실차(pt_diff)에 적용, "K경기 분량의 중립(0) 사전분포"를
# 실제 경기 수와 섞는다. gp가 커질수록 실제 성적 비중이 자연히 커짐.
SHRINKAGE_GAMES = 3

# 프리시즌 프라이어가 승률 계산에 미치는 영향력 — "N경기 분량의 사전 기대치"로
# 취급한다. 값이 클수록 시즌 초반 프리시즌 기대치 비중이 커지고, 시즌이
# 진행되면서(gp 증가) 자연히 실제 성적 비중이 지배적이 됨.
PRIOR_GAMES = 4

# SOS(상대 전력)가 elo/epa 점수에 미치는 최대 폭.
# opponent 평균 승률이 0~1 극단일 때 ±(SOS_WEIGHT/2)점까지 보정.
SOS_WEIGHT = 20


def generate_blurb(record_str, gp, pt_diff_avg, sos, preseason_rank, current_rank):
    """기록/득실차/SOS/프리시즌 대비 순위를 조합해 1~2문장 자동 요약 생성 (영어).
    실제 뉴스가 아니라 지금 갖고 있는 데이터로만 설명 가능한 근거를 서술."""
    if gp == 0:
        return f"No games played yet. Currently reflecting preseason expert consensus rank #{preseason_rank}."

    margin_txt = f"averaging {pt_diff_avg:+.1f} pts/game" if abs(pt_diff_avg) >= 0.5 else "in tightly contested games"

    if sos >= 0.55:
        sos_txt = "faced a relatively tough schedule"
    elif sos <= 0.45:
        sos_txt = "faced a relatively weak schedule"
    else:
        sos_txt = "faced an average-strength schedule"

    delta = preseason_rank - current_rank  # 양수면 프리시즌 예상보다 상승
    if delta >= 5:
        expectation_txt = f"far exceeding the preseason #{preseason_rank} projection, now ranked #{current_rank}."
    elif delta <= -5:
        expectation_txt = f"falling short of the preseason #{preseason_rank} projection, now down at #{current_rank}."
    else:
        expectation_txt = f"roughly in line with the preseason #{preseason_rank} projection at #{current_rank}."

    return f"{record_str} record, {margin_txt}. Has {sos_txt}, {expectation_txt}"


# 리그 평균 경기당 득점(근사치) — 표본 없는 팀의 예측 스코어 계산 시 중립값.
LEAGUE_AVG_POINTS = 22.0
# 득점/실점 평균에도 승률과 같은 논리의 축소를 적용 — 1경기 대승/대패가
# 시즌 내내 그대로 "이 팀 평균 득점"으로 고정되는 걸 방지.
SCORING_SHRINKAGE_GAMES = 4


def shrunk_scoring_avg(total_points, gp):
    return (total_points + LEAGUE_AVG_POINTS * SCORING_SHRINKAGE_GAMES) / (gp + SCORING_SHRINKAGE_GAMES)


def fetch_and_calculate_stats():
    team_stats = {
        tid: {
            'wins': 0, 'losses': 0, 'ties': 0,
            'points_for': 0, 'points_against': 0, 'games_played': 0,
            'opponents': [],  # 이번 시즌 맞붙은 상대 팀 id 목록 (SOS 계산용)
        }
        for tid in TEAM_METADATA.keys()
    }

    try:
        req = urllib.request.Request(NFLVERSE_GAMES_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=25) as resp:
            csv_text = resp.read().decode('utf-8')

        rows = list(csv.DictReader(io.StringIO(csv_text)))

        # 1. 최신 정규시즌 연도(Season) 자동 탐색
        seasons_with_scores = [
            int(r['season']) for r in rows
            if r.get('game_type') == 'REG' and r.get('home_score') and r.get('away_score')
        ]
        if not seasons_with_scores:
            raise RuntimeError("no completed REG-season games found in nflverse feed")
        target_season = max(seasons_with_scores)
        print(f"Targeting active NFL season: {target_season}")

        # 2. 해당 최신 시즌의 경기만 집계
        for row in rows:
            if str(row.get('season')) == str(target_season) and row.get('game_type') == 'REG':
                if row.get('home_score') and row.get('away_score'):
                    h_team = NAME_MAP.get(row['home_team'], row['home_team'])
                    a_team = NAME_MAP.get(row['away_team'], row['away_team'])

                    if h_team in team_stats and a_team in team_stats:
                        try:
                            h_score = int(float(row['home_score']))
                            a_score = int(float(row['away_score']))
                        except ValueError:
                            continue

                        team_stats[h_team]['games_played'] += 1
                        team_stats[a_team]['games_played'] += 1
                        team_stats[h_team]['points_for'] += h_score
                        team_stats[h_team]['points_against'] += a_score
                        team_stats[a_team]['points_for'] += a_score
                        team_stats[a_team]['points_against'] += h_score
                        team_stats[h_team]['opponents'].append(a_team)
                        team_stats[a_team]['opponents'].append(h_team)

                        if h_score > a_score:
                            team_stats[h_team]['wins'] += 1
                            team_stats[a_team]['losses'] += 1
                        elif a_score > h_score:
                            team_stats[a_team]['wins'] += 1
                            team_stats[h_team]['losses'] += 1
                        else:
                            team_stats[h_team]['ties'] += 1
                            team_stats[a_team]['ties'] += 1

    except Exception as e:
        # 원격 소스가 죽어도 job 자체는 실패시키지 않는다 — 이전 nfl_data.json이
        # 남아있으면 그대로 유지되고, 없으면 gp=0 중립값(전 팀 50점)으로 생성된다.
        print(f"Warning: Remote fetch issue ({e})", file=sys.stderr)

    # 3. SOS(상대 전력) 계산 — 상대팀의 "프리시즌 프라이어 + 축소 적용된" 승률을
    #    먼저 구한다. (raw 승률을 쓰면 시즌 초반 순환 문제 발생 — 이전 커밋에서
    #    이미 확인된 이슈. 프리시즌 프라이어까지 섞으면 이 문제가 더 완화된다:
    #    상대가 이번 시즌 첫 경기를 이겼어도 원래 약체로 평가받던 팀이면
    #    SOS가 과도하게 튀지 않는다.)
    shrunk_win_rate = {}
    for tid in TEAM_METADATA:
        st = team_stats[tid]
        gp = st['games_played']
        prior = preseason_prior_win_rate(tid)
        shrunk_win_rate[tid] = (
            (st['wins'] + 0.5 * st['ties'] + prior * PRIOR_GAMES) / (gp + PRIOR_GAMES)
        )

    def strength_of_schedule(tid):
        opponents = team_stats[tid]['opponents']
        if not opponents:
            return 0.5
        return sum(shrunk_win_rate[opp] for opp in opponents) / len(opponents)

    # 4. 표본 수 축소(shrinkage) + 프리시즌 프라이어 + SOS 보정 적용 정규화
    teams_output = []
    K = SHRINKAGE_GAMES
    for tid, meta in TEAM_METADATA.items():
        st = team_stats[tid]
        gp = st['games_played']
        w, l, t = st['wins'], st['losses'], st['ties']

        record_str = f"{w}-{l}" + (f"-{t}" if t > 0 else "") if gp > 0 else "0-0"
        sos = strength_of_schedule(tid)
        prior = preseason_prior_win_rate(tid)

        # 승률: 프리시즌 프라이어를 PRIOR_GAMES경기 분량으로 섞는다.
        # gp=0이면 그대로 프라이어값 — gp가 커질수록 실제 성적 비중이 지배적.
        adj_win_rate = (w + 0.5 * t + prior * PRIOR_GAMES) / (gp + PRIOR_GAMES)
        # 득실차는 여전히 중립(0)을 K경기 분량으로 섞어 조기 포화만 방지.
        adj_pt_diff = (st['points_for'] - st['points_against']) / (gp + K)

        # SOS 보정: 상대 평균 승률이 0.5보다 높으면(강한 일정) 가산,
        # 낮으면(약한 일정) 감산. gp=0이면 sos=0.5라 보정 0.
        sos_adjustment = (sos - 0.5) * SOS_WEIGHT

        norm_elo = round(max(30, min(99, 50 + (adj_win_rate - 0.5) * 70 + adj_pt_diff * 1.5 + sos_adjustment)), 1)
        norm_epa = round(max(25, min(99, 50 + (adj_win_rate - 0.5) * 50 + adj_pt_diff * 2.0 + sos_adjustment)), 1)
        norm_sr = round(max(30, min(98, 50 + (adj_win_rate - 0.5) * 90)), 1)
        norm_rec = round(max(25, min(99, norm_elo + adj_pt_diff * 0.8)), 1)

        teams_output.append({
            "id": tid,
            "name": meta['name'],
            "conf": meta['conf'],
            "div": meta['div'],
            "record": record_str,
            "gamesPlayed": gp,
            "sos": round(sos, 3),
            "preseasonRank": PRESEASON_RANK.get(tid),
            "ptDiffAvg": round((st['points_for'] - st['points_against']) / gp, 1) if gp > 0 else 0,
            "avgPointsFor": round(shrunk_scoring_avg(st['points_for'], gp), 1),
            "avgPointsAgainst": round(shrunk_scoring_avg(st['points_against'], gp), 1),
            "colorPrimary": meta['colors'][0],
            "colorSecondary": meta['colors'][1],
            "normElo": norm_elo,
            "normEpa": norm_epa,
            "normSr": norm_sr,
            "normRecency": norm_rec,
            "prevRank": 16
        })

    # 정렬 및 전주 순위 매핑
    teams_output.sort(key=lambda x: x['normElo'], reverse=True)
    for idx, tm in enumerate(teams_output):
        current_rank = idx + 1
        tm['blurb'] = generate_blurb(
            tm['record'], tm['gamesPlayed'], tm['ptDiffAvg'],
            tm['sos'], tm['preseasonRank'], current_rank
        )
        tm['prevRank'] = current_rank

    with open("nfl_data.json", "w", encoding="utf-8") as f:
        json.dump(teams_output, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated data for {len(teams_output)} teams (shrinkage K={K}, prior K={PRIOR_GAMES}, SOS weight={SOS_WEIGHT}).")


if __name__ == "__main__":
    fetch_and_calculate_stats()
