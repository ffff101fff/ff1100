# main.py
# 프로젝트 전체를 한 번에 실행하거나, 원하는 종목·선수의 지표를 바로 조회하는 진입점.
#
# 사용법
#   python main.py                    제안서에 제출한 데이터셋으로 분석 -> 그래프 생성
#   python main.py --rebuild          원본(data/raw)에서 데이터셋을 다시 만든 뒤 분석 -> 그래프
#   python main.py --sport fencing    한 종목의 상위 3일 비율·올림픽 배수·평상시 관심도 조회
#   python main.py --athlete oh_su    한 선수의 평상시 관심도·대회 집중도·공개 수입 조회
#   python main.py --list             조회할 수 있는 종목·선수 이름 목록

import argparse
import os
import sys

import pandas as pd

import config

# 분석에 쓰는 입력 파일 (제안서와 함께 제출한 CSV 7개)
INPUT_FILES = [os.path.join(config.PROCESSED_DIR, f) for f in ["interest.csv", "athletes.csv", "events.csv"]] + \
              [config.INCOME_FILE, config.MATCH_LOAD_FILE, config.MATCH_DATES_FILE, config.FIE_RESULTS_FILE]
RAW_FILES = [os.path.join(config.RAW_DIR, f) for f in
             ["wiki_pageviews.csv", "wiki_athletes.csv", "wiki_total.csv", "gtrends.csv"]]


def check_files(files, how_to_fix):
    """필요한 파일이 없으면 어떤 파일이 없는지와 해결 방법을 알려주고 멈춘다."""
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print("다음 파일이 없습니다:", ", ".join(os.path.relpath(f, config.BASE_DIR) for f in missing))
        print("  ->", how_to_fix)
        sys.exit(1)


def run_all(rebuild=False):
    """(--rebuild 이면 원본에서 데이터셋을 다시 만든 뒤) 분석 -> 그래프를 한 번에 실행한다."""
    import analysis
    import figures

    if rebuild:
        import build_dataset
        check_files(RAW_FILES, "python collect_wiki.py 와 python load_gtrends.py 를 먼저 실행하세요 (README 4번).")
        print("=" * 60, "\n0) 원본에서 통합 데이터셋 다시 만들기\n" + "=" * 60)
        build_dataset.main()
        print()
    check_files(INPUT_FILES, "GitHub 저장소를 다시 내려받거나 python main.py --rebuild 로 다시 만드세요.")
    print("=" * 60, "\n1) 분석\n" + "=" * 60)
    analysis.main()
    print("\n" + "=" * 60, "\n2) 그래프\n" + "=" * 60)
    figures.main()
    print("\n완료: results/ 에 분석 결과, figures/ 에 그래프 6개가 저장되었습니다.")


def ensure_results():
    """조회 기능은 analysis.py 결과를 읽으므로, 결과가 없으면 먼저 만든다."""
    if not os.path.exists(os.path.join(config.RESULT_DIR, "athlete_metrics.csv")):
        print("분석 결과가 없어 먼저 전체 실행을 합니다...\n")
        run_all()
        print()


def show_sport(sport):
    """--sport: 한 종목의 상위 3일 비율, 올림픽 배수, 연도별 평상시 관심도를 보여 준다."""
    if sport not in config.SPORT_GROUP:
        print(f"'{sport}' 는 없는 종목입니다. 가능한 종목: {', '.join(config.SPORT_GROUP)}")
        sys.exit(1)
    ensure_results()
    top3 = pd.read_csv(os.path.join(config.RESULT_DIR, "top3_share_summary.csv"), index_col=[0, 1])
    olympic = pd.read_csv(os.path.join(config.RESULT_DIR, "olympic_multiple.csv"), index_col=0)
    yearly = pd.read_csv(os.path.join(config.RESULT_DIR, "yearly_baseline_wiki.csv"), index_col=[0, 1])
    print(f"[{config.NAMES[sport]}] 묶음: {config.GROUP_NAMES[config.SPORT_GROUP[sport]]}")
    for region, label in [("ko", "한국어 위키"), ("en", "영어 위키")]:
        t = top3.loc[(region, sport)]
        o = olympic[(olympic["region"] == region) & (olympic["sport"] == sport)]
        y = yearly.loc[(region, sport)]
        print(f"  {label}: 1년 관심 중 상위 3일 비율 - 보통 해 {t['median']:.1f}%, "
              f"가장 몰린 해 {t['max']:.1f}% ({int(t['max_year'])}년)")
        print("            올림픽 배수 - " +
              ", ".join(f"{e.split(' (')[0]} {m:.1f}배" for e, m in zip(o["event"], o["multiple"])))
        print(f"            평상시 관심도(100만 건당) - 2016년 {y['2016']:.1f} -> 2025년 {y['2025']:.1f}")


def show_athlete(key):
    """--athlete: 한 선수의 평상시·대회 기간 관심도와 공개 수입을 보여 준다."""
    if key not in config.ATHLETES:
        print(f"'{key}' 는 없는 선수입니다. 가능한 선수: {', '.join(config.ATHLETES)}")
        sys.exit(1)
    ensure_results()
    am = pd.read_csv(os.path.join(config.RESULT_DIR, "athlete_metrics.csv"), index_col=0)
    income = pd.read_csv(config.INCOME_FILE).set_index("key")
    name, sport = config.ATHLETES[key]
    print(f"[{name}] 종목: {config.NAMES[sport]} ({config.GROUP_NAMES[config.SPORT_GROUP[sport]]})")
    rows = am[am["athlete"] == key].sort_values("region", ascending=False)   # 한국어 먼저
    for _, r in rows.iterrows():
        label = "한국어 위키" if r["region"] == "ko" else "영어 위키"
        print(f"  {label}: 평상시 관심도 {r['baseline']:.2f}, 대회 기간 하루 최고 {r['games_peak']:.1f} "
              f"(100만 건당), 관심 중 대회 기간 비율 {r['games_share']:.0%}")
        if r["coverage"] < 0.9:      # analysis.MIN_COVERAGE 와 같은 기준
            print(f"      ※ 최근 2년 중 조회 기록이 있는 날 {r['coverage']:.0%} (90% 미만이라 수입 비교에서 제외)")
    if key in income.index:
        i = income.loc[key]
        print(f"  공개 금액: ${i['income_usd']:,.0f} ({i['income_type']}, {i['period']})")
    else:
        print("  공개 금액 자료 없음")


def main():
    """명령행 옵션을 읽어 전체 실행 / 종목 조회 / 선수 조회 / 목록 중 하나를 고른다."""
    parser = argparse.ArgumentParser(
        description="3일의 관심, 362일의 공백 - 펜싱 프로 리그 가능성 분석 프로그램")
    parser.add_argument("--rebuild", action="store_true", help="원본에서 데이터셋을 다시 만든 뒤 전체 실행")
    parser.add_argument("--sport", help="종목 지표 조회 (예: fencing)")
    parser.add_argument("--athlete", help="선수 지표 조회 (예: oh_su)")
    parser.add_argument("--list", action="store_true", help="조회 가능한 종목·선수 목록")
    args = parser.parse_args()

    if args.list:
        print("종목:", ", ".join(f"{k}({v})" for k, v in config.NAMES.items()))
        print("선수:", ", ".join(f"{k}({v[0]})" for k, v in config.ATHLETES.items()))
    elif args.sport:
        show_sport(args.sport.lower())
    elif args.athlete:
        show_athlete(args.athlete.lower())
    else:
        run_all(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
