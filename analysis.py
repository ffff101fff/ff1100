# analysis.py
# 제안서에 제출한 데이터셋(data/processed, data/*.csv)으로 연구 질문에 답하는 지표를 계산한다.
# 실행: python analysis.py   -> 결과를 화면에 출력하고 results/ 폴더에 CSV로 저장
#
# Q1. 펜싱은 '올림픽 때만 보는 스포츠'인가?
#     - 상위 3일 비율 : 1년 관심 중 가장 많이 본 3일이 차지하는 비율
#     - 올림픽 배수   : 올림픽 기간 하루 최고 관심도 / 직전 1년 평상시 관심도
#     - 평상시 관심도 : 대회 기간을 뺀 날의 중앙값 (수요가 있는지 확인)
# Q2. 펜싱 스타는 왜 '돈 버는 스타'가 되지 못하는가?
#     - 대회 집중도   : 선수가 받은 관심 중 대회 기간에 몰린 비율
#     - 순간 vs 평상시 : 오상욱의 올림픽 하루 최고 관심도와 다른 스타의 평상시 관심도 비교
#     - 관심도 배수 vs 수입 배수
# Q3. 펜싱 프로 리그는 가능한가?
#     - MMA 기준선    : UFC가 크기 전(2004) MMA와 현재 펜싱의 관심도 (구글 트렌드 같은 척도)
#     - 경기 간격     : 다음 경기까지 평균 며칠 쉬는가 (회복 부담)
#     - FIE 대회 일정 : 펜싱 선수 4명이 실제로 1년에 국제 대회에 몇 번 나가는가

import os

import numpy as np
import pandas as pd

import config

RESULT_DIR = config.RESULT_DIR
PAD = pd.Timedelta(days=30)   # 대회 전후 30일까지는 '대회 영향 기간'으로 보고 평상시에서 뺀다
TOP_K = 3                     # 상위 몇 일을 볼 것인가
YEARS = range(2016, 2026)     # 1년 전체 자료가 있는 해 (2015년은 7월부터, 2026년은 10월까지)
MIN_COVERAGE = 0.9            # 최근 2년 중 조회 기록이 있는 날이 90% 미만인 문서는 비교에서 뺀다


# ---------------------------------------------------------------
# 공통 함수
# ---------------------------------------------------------------
def load():
    """제출한 통합 데이터셋 3개를 읽고, 이벤트 중 올림픽·아시안게임만 골라 둔다."""
    data = pd.read_csv(os.path.join(config.PROCESSED_DIR, "interest.csv"), parse_dates=["date"])
    athletes = pd.read_csv(os.path.join(config.PROCESSED_DIR, "athletes.csv"), parse_dates=["date"])
    events = pd.read_csv(os.path.join(config.PROCESSED_DIR, "events.csv"), parse_dates=["start", "end"])
    games = events[events["type"].isin(["olympics", "asian_games"])].reset_index(drop=True)
    return data, athletes, games


def series(data, source, region, sport):
    """한 출처·지역·종목의 관심도 시계열 (날짜 -> 보정된 관심도)"""
    s = data[(data["source"] == source) & (data["region"] == region) & (data["sport"] == sport)]
    return s.set_index("date")["value_norm"].sort_index()


def is_normal_day(dates, games):
    """대회 기간과 그 전후 30일에 속하지 않는 '평상시' 날짜이면 True"""
    mask = np.ones(len(dates), dtype=bool)
    for _, g in games.iterrows():
        mask &= ~((dates >= g["start"] - PAD) & (dates <= g["end"] + PAD))
    return mask


def normal_median(s, games):
    """평상시 날짜만 골라 중앙값을 구한다 (대회 때 튀는 값의 영향을 받지 않도록 평균 대신 중앙값)"""
    return s[is_normal_day(s.index, games)].median()


# ---------------------------------------------------------------
# Q1-a. 상위 3일 비율 (%)
#   대회 날짜를 따로 정하지 않아도 되므로 축구의 월드컵, 야구의 WBC처럼 종목마다 다른
#   큰 대회가 저절로 들어간다. 관심이 1년 내내 고르게 퍼져 있으면 3/365 = 0.8% 이다.
# ---------------------------------------------------------------
def topk_share(data, k=TOP_K):
    rows = []
    wiki = data[data["source"] == "wikipedia"]
    for (region, sport), g in wiki.groupby(["region", "sport"]):
        s = g.set_index("date")["value_norm"]
        for year in YEARS:
            x = s[str(year)]
            rows.append({"region": region, "sport": sport, "year": year,
                         "top_share": x.nlargest(k).sum() / x.sum() * 100})
    yearly = pd.DataFrame(rows)
    by_sport = yearly.groupby(["region", "sport"])["top_share"]
    summary = pd.DataFrame({"median": by_sport.median(), "max": by_sport.max()})
    summary["max_year"] = yearly.loc[by_sport.idxmax(), ["region", "sport", "year"]].set_index(
        ["region", "sport"])["year"]
    return yearly, summary


# ---------------------------------------------------------------
# Q1-b. 올림픽 배수 = 올림픽 기간 하루 최고 관심도 / 직전 1년 평상시 중앙값
# ---------------------------------------------------------------
def olympic_multiple(data, games):
    rows = []
    olympics = games[games["type"] == "olympics"]
    for region in ["ko", "en"]:
        for sport in config.WIKI_ARTICLES[region]:
            s = series(data, "wikipedia", region, sport)
            for _, g in olympics.iterrows():
                if g["start"] < s.index.min() + pd.Timedelta(days=365):
                    continue                  # 직전 1년 자료가 없는 대회(위키 자료 시작 전)는 뺀다
                before = s[g["start"] - pd.Timedelta(days=395): g["start"] - PAD]
                base = normal_median(before, games)
                peak = s[g["start"]: g["end"]].max()
                rows.append({"region": region, "sport": sport, "event": g["name"],
                             "baseline": base, "peak": peak, "multiple": peak / base})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------
# Q1-c. 평상시 관심도 (연도별 중앙값) - 평소에 펜싱을 보는 사람이 있는가 (수요)
# ---------------------------------------------------------------
def yearly_baseline(data, games):
    rows = {}
    for region in ["ko", "en"]:
        for sport in config.WIKI_ARTICLES[region]:
            s = series(data, "wikipedia", region, sport)
            normal = s[is_normal_day(s.index, games)]
            rows[(region, sport)] = normal.groupby(normal.index.year).median()
    return pd.DataFrame(rows).T[list(YEARS)]


# ---------------------------------------------------------------
# Q2. 스타 선수 지표
#   평상시 관심도 = 최근 2년(2024.10.16~2026.10.15) 평상시 중앙값 : 광고주가 보는 '매일 보이는 얼굴'
#   대회 최고 관심도 = 2021년 이후 올림픽·아시안게임 기간의 하루 최고값 : '순간 관심'
#   대회 집중도 = 2021년 이후 받은 관심 중 대회 기간(전후 30일 포함)에 몰린 비율
# ---------------------------------------------------------------
def athlete_metrics(athletes, games):
    rows = []
    recent_games = games[games["start"] >= "2021-01-01"]
    for (region, key), g in athletes.groupby(["region", "athlete"]):
        s = g.set_index("date")["value_norm"].sort_index()
        recent = s["2024-10-16":"2026-10-15"]
        # 문서 제목이 바뀌면 조회수가 옛 제목과 새 제목으로 나뉘어 기록이 빈다 -> 비율이 낮으면 비교에서 뺀다
        coverage = (recent > 0).sum() / len(pd.date_range("2024-10-16", "2026-10-15"))
        window = s["2021-01-01":"2026-10-15"]
        in_games = ~is_normal_day(window.index, recent_games)
        # 대회마다 하루 최고값을 구한 뒤 그중 가장 큰 값 (문서가 없던 대회는 NaN이라 건너뛴다)
        peaks = pd.Series([s[r["start"]:r["end"]].max() for _, r in recent_games.iterrows()])
        rows.append({"region": region, "athlete": key, "name": config.ATHLETES[key][0],
                     "sport": config.ATHLETES[key][1], "coverage": coverage,
                     "baseline": normal_median(recent, games),
                     "games_peak": peaks.max(),
                     "games_share": window[in_games].sum() / window.sum(),
                     "days_in_games_windows": in_games.mean()})
    return pd.DataFrame(rows)


def star_income(ath_metrics):
    """영어 위키 관심도와 공개 수입을 합친다 (관심도 자료가 없는 호날두·메이웨더는 여기서 빠진다)"""
    income = pd.read_csv(config.INCOME_FILE)
    en = ath_metrics[ath_metrics["region"] == "en"]
    for _, r in en[(en["coverage"] < MIN_COVERAGE) & en["athlete"].isin(income["key"])].iterrows():
        print(f"  (제외) {r['name']}: 최근 2년 조회 기록이 있는 날 {r['coverage']:.0%}")
    en = en[en["coverage"] >= MIN_COVERAGE]
    return en.merge(income[["key", "income_usd", "income_type"]], left_on="athlete", right_on="key")


def income_gap(inc, base="oh_su"):
    """기준 선수 대비 관심도와 공개 금액의 비율을 각각 계산한다."""
    b = inc.set_index("athlete")
    ref = b.loc[base]
    others = b.drop(index=base).sort_values("income_usd")
    return pd.DataFrame({"name": others["name"],
                         "interest_x": others["baseline"] / ref["baseline"],
                         "income_x": others["income_usd"] / ref["income_usd"],
                         "oh_peak_vs_baseline": ref["games_peak"] / others["baseline"]})


def income_only(base="oh_su"):
    """관심도 자료와 상관없이 공개 수입만 기준 선수와 비교한다 (호날두·메이웨더 포함)"""
    income = pd.read_csv(config.INCOME_FILE).set_index("key")
    ref = income.loc[base, "income_usd"]
    others = income.drop(index=base).sort_values("income_usd", ascending=False)
    return pd.DataFrame({"name": others["name_ko"], "sport": others["sport"],
                         "income_usd": others["income_usd"], "income_x": others["income_usd"] / ref})


# ---------------------------------------------------------------
# Q3-a. MMA 기준선: 구글 트렌드 평상시 관심도 (대회가 열린 달을 뺀 연도별 중앙값)
#   구글 트렌드는 한 화면에서 비교한 종목끼리만 같은 척도이므로, 2004년 MMA와 지금의 펜싱을
#   같은 단위로 직접 비교할 수 있다.
# ---------------------------------------------------------------
def gtrends_yearly(data, games, region="world"):
    game_months = set()
    for _, g in games.iterrows():
        game_months |= set(pd.period_range(g["start"], g["end"], freq="M"))
    rows = {}
    for sport in config.GTRENDS_TOPICS:
        s = series(data, "google_trends", region, sport)
        normal = s[[m not in game_months for m in s.index.to_period("M")]]
        rows[sport] = normal.groupby(normal.index.year).median()
    return pd.DataFrame(rows)


# ---------------------------------------------------------------
# Q3-b. 경기 간격: 다음 경기까지 평균 며칠 쉬는가 (길수록 회복 부담이 크다)
#   날짜 목록이 있으면(선수)  : 연속한 두 경기 사이 날짜 차이의 평균
#   경기 수·기간만 있으면(팀)  : 기간 / (경기 수 - 1)
#   1년 경기 수만 있으면(UFC) : 365 / 1년 경기 수
# ---------------------------------------------------------------
def match_gaps():
    load = pd.read_csv(config.MATCH_LOAD_FILE, parse_dates=["start", "end"])
    dates = pd.read_csv(config.MATCH_DATES_FILE, parse_dates=["date"])
    rows = []
    for (sport, key), g in dates.groupby(["sport", "series"], sort=False):
        gaps = g["date"].sort_values().diff().dt.days.dropna()
        rows.append({"sport": sport, "series": key, "label": g["description"].iloc[0],
                     "matches": len(g), "mean_gap": gaps.mean(), "min_gap": gaps.min()})
    for _, r in load.iterrows():
        if r["unit"] == "경기/년":
            gap = 365 / r["value"]
        elif r["unit"] == "경기":
            gap = (r["end"] - r["start"]).days / (r["value"] - 1)
        else:
            continue                          # '경기/일'(펜싱 하루 경기 수)은 간격이 아니라 따로 출력
        rows.append({"sport": r["sport"], "series": r["sport"], "label": r["item"].split(" (")[0],
                     "matches": r["value"] if r["unit"] == "경기" else np.nan,
                     "mean_gap": gap, "min_gap": np.nan})
    table = pd.DataFrame(rows).sort_values("mean_gap", ascending=False).reset_index(drop=True)
    per_day = load[load["unit"] == "경기/일"].iloc[0]
    return table, per_day


# ---------------------------------------------------------------
# Q3-c. 펜싱 선수 4명의 국제펜싱연맹(FIE) 개인전 일정
#   지금 펜싱 선수가 대회에 나가는 간격은 몸(회복)이 아니라 대회 일정이 정한다는 것을 확인한다.
# ---------------------------------------------------------------
def rest_ratio(mg, base="oh_su_paris"):
    """복싱·MMA의 경기 간 평균 간격이 기준(오상욱 파리 올림픽 4일)의 몇 배인가"""
    ref = mg.loc[mg["series"] == base, "mean_gap"].iloc[0]
    duel = mg[mg["sport"].isin(["boxing", "mma"])]
    return pd.DataFrame({"label": duel["label"], "mean_gap": duel["mean_gap"],
                         "x_vs_base": duel["mean_gap"] / ref}), ref


def fie_schedule():
    fie = pd.read_csv(config.FIE_RESULTS_FILE, parse_dates=["date"])
    rows = []
    for key, g in fie.groupby("athlete"):
        d = g["date"].sort_values()
        seasons = g.groupby("season").size()          # 시즌별 출전 대회 수
        gaps = d.diff().dt.days.dropna()
        rows.append({"athlete": key, "name": g["name_ko"].iloc[0], "seasons": len(seasons),
                     "competitions": len(g), "per_season": seasons.median(),
                     "median_gap": gaps.median(), "min_gap": gaps.min()})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------
# 실행
# ---------------------------------------------------------------
def save(df, name):
    df.to_csv(os.path.join(RESULT_DIR, name), encoding="utf-8-sig")


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    pd.set_option("display.width", 200)
    data, athletes, games = load()

    # Q1
    yearly, topk = topk_share(data)
    save(yearly, "top3_share_yearly.csv")
    save(topk, "top3_share_summary.csv")
    print("[Q1] 1년 관심 중 가장 많이 본 3일의 비율 (%, 2016~2025 보통 해=중앙값 / 가장 몰린 해=최댓값)")
    print(topk.round(1).to_string())

    om = olympic_multiple(data, games)
    save(om, "olympic_multiple.csv")
    print("\n[Q1] 올림픽 배수 = 올림픽 기간 하루 최고 관심도 / 직전 1년 평상시 관심도")
    print(om.pivot_table(index=["region", "sport"], columns="event", values="multiple")
          .assign(median=lambda t: t.median(axis=1)).round(1).to_string())

    yb = yearly_baseline(data, games)
    save(yb, "yearly_baseline_wiki.csv")
    print("\n[Q1] 평상시 관심도 (위키 전체 조회 100만 건당, 연도별 중앙값)")
    print(yb[[2016, 2019, 2022, 2025]].round(1).to_string())

    # Q2
    am = athlete_metrics(athletes, games)
    save(am, "athlete_metrics.csv")
    print("\n[Q2] 스타 선수가 받은 관심 중 대회 기간의 비율 (한국어 위키, 2021~2026)")
    ko = am[am["region"] == "ko"].sort_values("games_share", ascending=False)
    print(ko[["name", "sport", "games_share", "baseline", "games_peak"]].round(2).to_string(index=False))

    inc = star_income(am)
    save(inc, "income_vs_interest.csv")
    gap = income_gap(inc)
    save(gap, "income_gap.csv")
    print("\n[Q2] 오상욱 = 1 로 놓은 배수 (관심도 기준: 오상욱 영어 위키 평상시 관심도 / 금액 기준: 세계선수권 개인전 우승 상금 4만 달러)")
    print(gap.round(1).to_string(index=False))
    io = income_only()
    print("\n[Q2] 공개 수입만 비교 (오상욱 4만 달러 = 1, 관심도 자료가 없는 호날두·메이웨더 포함)")
    print(io.assign(income_x=io["income_x"].round(1)).to_string(index=False))

    # Q3
    gt = gtrends_yearly(data, games)
    save(gt, "gtrends_yearly_world.csv")
    print("\n[Q3] 전 세계 구글 트렌드 평상시 관심도 (같은 척도, 대회 달 제외 연도별 중앙값)")
    print(gt.loc[[2004, 2005, 2006, 2008, 2010, 2015, 2020, 2025]].to_string())

    mg, per_day = match_gaps()
    save(mg, "match_gaps.csv")
    print("\n[Q3] 다음 경기까지 평균 며칠 쉬는가 (출처: data/match_dates.csv, data/match_load.csv)")
    print(mg[["sport", "label", "matches", "mean_gap", "min_gap"]].round(1).to_string(index=False))
    print(f"  펜싱 하루 경기 수: {per_day['value']:.0f}경기 ({per_day['item']})")
    rr, ref = rest_ratio(mg)
    print(f"\n[Q3] 복싱·MMA가 다음 경기까지 쉬는 기간 ÷ 오상욱 파리 올림픽 간격({ref:.0f}일)")
    print(rr.round(1).to_string(index=False))

    fs = fie_schedule()
    save(fs, "fie_schedule.csv")
    print("\n[Q3] 펜싱 선수의 실제 국제 개인전 일정 (FIE 기록, 시즌당 대회 수는 중앙값, 간격은 일)")
    print(fs.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
