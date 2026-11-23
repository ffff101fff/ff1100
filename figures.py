# figures.py
# 분석 결과 그래프를 figures/ 폴더에 PNG로 저장한다.
# 실행: python figures.py   (analysis.py 실행 후)
#
# 색: 펜싱만 파란색으로 강조하고, 비교의 기준이 되는 MMA(복싱)는 분홍색, 나머지는 은회색 + 직접 라벨.
# 파랑·분홍·은회색은 색각 이상(적록·청황)에서도 서로 구분되는 조합으로 골랐다.

import os

import matplotlib
matplotlib.use("Agg")                    # 창을 띄우지 않고 파일로만 저장
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager, ticker

import analysis
import config

FIG_DIR = config.FIG_DIR
FENCING = "#1f6fff"
MMA = "#b83266"
OTHER = "#b4bcc8"
INK, MUTED, GRID = "#15324b", "#5c6372", "#dce6f7"


def setup_font():
    """한글 폰트 설정 (Windows: 맑은 고딕, Mac: AppleGothic, Linux: 나눔고딕 / Noto Sans CJK)
    Noto Sans CJK JP 도 한글 글자를 모두 담고 있어, KR 이름이 안 보이는 환경의 대안으로 쓴다."""
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP"]:
        if any(name == f.name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    else:
        print("  ※ 한글 폰트를 찾지 못해 그래프의 한글이 네모로 보일 수 있습니다 (README 참고).")
    plt.rcParams.update({"axes.unicode_minus": False, "svg.fonttype": "path", "svg.hashsalt": "fencing", "font.size": 10,
                         "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    """그림을 figures/ 에 PNG(300dpi, 발표용)와 SVG(벡터, 보고서용)로 저장하고 메모리에서 닫는다.
    SVG는 글자를 도형으로 바꿔 저장하므로(svg.fonttype=path) 폰트가 없는 컴퓨터에서도 같은 모양으로 선명하게 보인다."""
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(os.path.splitext(path)[0] + ".svg", bbox_inches="tight", facecolor="white", metadata={"Date": None})
    plt.close(fig)
    print("저장:", name, "(+ .svg)")


def color_of(sport):
    """펜싱만 강조색(파랑), 나머지 종목은 회색으로 칠한다."""
    return FENCING if sport == "fencing" else OTHER


def fig1_timeline(data, games):
    """그림 1. 한국어 위키 펜싱 vs 축구 일별 관심도 (로그 축)"""
    fig, ax = plt.subplots(figsize=(7.2, 2.56))
    for _, g in games.iterrows():
        ax.axvspan(g["start"], g["end"], color=GRID, lw=0)
    football = analysis.series(data, "wikipedia", "ko", "football").rolling(7, center=True).mean()
    fencing = analysis.series(data, "wikipedia", "ko", "fencing")
    ax.plot(football.index, football.values, color=OTHER, lw=1.2)
    ax.plot(fencing.index, fencing.values, color=FENCING, lw=1.0)
    ax.set_yscale("log")
    ax.set_xlim(pd.Timestamp("2015-07-01"), pd.Timestamp("2026-10-15"))
    ax.set_ylabel("위키 전체 조회 100만 건당")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.text(pd.Timestamp("2015-08-01"), 160, "축구 (7일 평균)", color=MUTED, fontsize=9)
    ax.annotate("펜싱", (fencing.idxmax(), fencing.max()), xytext=(8, -4), textcoords="offset points",
                color=FENCING, fontsize=10, fontweight="bold")
    ax.set_title("펜싱은 대회 기간(회색 띠)에만 치솟는다 - 한국어 위키피디아 일별 관심도",
                 loc="left", color=INK, fontsize=11)
    save(fig, "fig1_timeline_ko.png")


def fig2_top3(summary):
    """그림 2. 1년 관심 중 상위 3일 비율 - 보통 해(중앙값)와 가장 몰린 해(최댓값)"""
    event_of = {("ko", "fencing"): "항저우 AG", ("ko", "football"): "카타르 WC",
                ("en", "fencing"): "파리 올림픽", ("en", "football"): "카타르 WC"}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.5))
    for ax, region, title in zip(axes, ["ko", "en"], ["한국어 위키피디아", "영어 위키피디아"]):
        s = summary.loc[region].sort_values("max")
        y = np.arange(len(s))
        colors = [color_of(k) for k in s.index]
        ax.barh(y, s["max"], color=colors, alpha=0.35, height=0.62)
        ax.barh(y, s["median"], color=colors, height=0.62)
        for i, (sport, r) in enumerate(s.iterrows()):
            label = f"{r['max']:.0f}%  {int(r['max_year'])} {event_of.get((region, sport), '')}"
            ax.text(r["max"] + 0.8, i, label.rstrip(), va="center", fontsize=8.5)
        ax.set_yticks(y, [config.NAMES[k] for k in s.index])
        ax.axvline(analysis.TOP_K / 365 * 100, color=INK, lw=0.7, ls=":")
        ax.set_xlim(0, s["max"].max() * 1.55)
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.tick_params(axis="y", length=0)
    axes[0].set_xlabel("%  (진한 막대: 보통 해, 연한 막대: 가장 몰린 해)")
    axes[1].set_xlabel("점선: 고르게 퍼졌을 때 0.8%")
    fig.suptitle("1년 관심 중 '가장 많이 본 3일'이 차지하는 비율 (2016~2025)",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout()
    save(fig, "fig2_top3.png")


def fig3_mma_vs_fencing(gt):
    """그림 3. 구글 트렌드 전 세계 평상시 관심도 - 같은 척도에서 MMA와 펜싱 비교"""
    years = [y for y in gt.index if 2004 <= y <= 2025]
    fig, ax = plt.subplots(figsize=(4.6, 2.9))          # 보고서·발표에서 반 칸 너비로 쓰므로 작게(글자가 상대적으로 커짐)
    for sport, color, lw in [("boxing", OTHER, 1.3), ("mma", MMA, 2.0), ("fencing", FENCING, 2.0)]:
        ax.plot(years, gt.loc[years, sport].values, color=color, lw=lw)
        ax.text(years[-1] + 0.3, gt.loc[years[-1], sport], config.NAMES[sport], color=color,
                va="center", fontsize=9, fontweight="normal" if sport == "boxing" else "bold")
    ax.axvline(2005, color=INK, lw=0.8, ls="--")
    ax.text(2005.3, 31, "UFC 리얼리티쇼\nTUF 첫 방송 (2005)", fontsize=9, color=INK, va="top")
    ax.set_ylabel("구글 트렌드 지수 (같은 척도)")
    ax.set_xlim(2004, 2026.5)
    ax.set_ylim(0, 32)
    ax.set_xticks(range(2004, 2026, 4))
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_title("2004년 MMA는 펜싱보다 작았다\n전 세계 평상시 검색 관심도 (대회 달 제외, 연도별 중앙값)",
                 loc="left", fontsize=10.5, color=INK)
    save(fig, "fig3_mma_vs_fencing.png")


def fig4_games_share(am):
    """그림 4. 스타 선수 관심의 몇 %가 대회 기간에 몰렸나 (한국어 위키, 2021~2026)"""
    ko = am[am["region"] == "ko"].sort_values("games_share")
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    ax.barh(ko["name"], ko["games_share"] * 100, color=[color_of(s) for s in ko["sport"]], height=0.6)
    for i, (v, sport) in enumerate(zip(ko["games_share"] * 100, ko["sport"])):
        ax.text(v + 1, i, f"{v:.0f}%  ({config.NAMES[sport]})", va="center", fontsize=9)
    even = ko["days_in_games_windows"].median() * 100
    ax.axvline(even, color=INK, lw=0.8, ls="--")
    ax.text(even + 0.8, -0.75, f"← 관심이 고르게 퍼져 있다면 {even:.0f}% (대회 기간이 전체 날짜에서 차지하는 비율)",
            fontsize=8.5, color=INK, va="center")
    ax.set_ylim(-1.2, len(ko) - 0.4)
    ax.set_xlim(0, 105)
    ax.set_xlabel("2021~2026년 위키 관심 중 올림픽·아시안게임 기간(전후 30일 포함)의 비율 (%)")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_title("펜싱 스타가 받는 관심의 대부분은 대회 기간에 몰린다 - 한국어 위키피디아",
                 loc="left", fontsize=11, color=INK)
    save(fig, "fig4_games_share.png")


def fig5_income_gap(gap):
    """그림 5. 오상욱 = 1 일 때 평상시 관심도 배수와 수입 배수 (로그 축)"""
    gap = gap.sort_values("income_x")
    y = np.arange(len(gap))
    fig, ax = plt.subplots(figsize=(7.2, 2.3))
    ax.hlines(y, gap["interest_x"], gap["income_x"], color=GRID, lw=6, zorder=1)
    ax.scatter(gap["interest_x"], y, s=70, color=OTHER, edgecolor="white", linewidth=1.5, zorder=3)
    ax.scatter(gap["income_x"], y, s=70, color=FENCING, marker="s", edgecolor="white", linewidth=1.5, zorder=3)
    for i, (_, r) in enumerate(gap.iterrows()):
        ax.text(r["interest_x"] / 1.18, i, f"{r['interest_x']:.0f}배", ha="right", va="center", fontsize=9, color=MUTED)
        ax.text(r["income_x"] * 1.18, i, f"{r['income_x']:,.0f}배", ha="left", va="center", fontsize=9, color=INK)
    ax.set_yticks(y, gap["name"])
    ax.set_xscale("log")
    ax.set_xlim(10, 20000)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}배"))
    ax.set_ylim(-0.6, len(gap) - 0.2)
    ax.text(10.5, len(gap) - 0.45, "●  평상시 관심도 배수 (영어 위키)", color=MUTED, fontsize=9, va="center")
    ax.text(400, len(gap) - 0.45, "■  연간 총수입 ÷ 펜싱 우승 상금", color=FENCING, fontsize=9, va="center")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_title("평상시 관심도와 공개 금액은 얼마나 차이가 날까?", loc="left", fontsize=11, color=INK)
    save(fig, "fig5_income_gap.png")


def fig6_match_gaps(mg):
    """그림 6. 다음 경기까지 평균 며칠 쉬는가 (로그 축)"""
    short = {"jung_cs": "정찬성 (UFC, 군 복무 포함)", "mcgregor": "맥그리거 (UFC)",
             "fury": "퓨리 (복싱)", "mma": "UFC 선수 평균", "canelo": "카넬로 (복싱)",
             "oh_su_2024": "오상욱 23/24 시즌 개인전", "oh_su_2026": "오상욱 25/26 시즌 개인전",
             "football": "레알 마드리드 (축구)", "oh_su_paris": "오상욱 파리 개인전→단체전",
             "baseball": "MLB 팀 (야구)"}
    mg = mg.iloc[::-1].reset_index(drop=True)          # 간격이 짧은 것이 아래로 가도록
    colors = [FENCING if s == "fencing" else (MMA if s in ("mma", "boxing") else OTHER) for s in mg["sport"]]
    fig, ax = plt.subplots(figsize=(4.2, 3.0))          # 보고서·발표에서 반 칸 너비로 쓰므로 작게(글자가 상대적으로 커짐)
    ax.barh(range(len(mg)), mg["mean_gap"], color=colors, height=0.6)
    for i, v in enumerate(mg["mean_gap"]):
        ax.text(v * 1.08, i, f"{v:.1f}일" if v < 10 else f"{v:.0f}일", va="center", fontsize=9)
    ax.set_yticks(range(len(mg)), [short.get(k, k) for k in mg["series"]])
    ax.set_xscale("log")
    ax.set_xlim(0.8, 900)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}일"))
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_title("선수·팀의 출전 간격 (일)\n파리 올림픽 개인전과 단체전 간격은 4일",
                 loc="left", fontsize=10.5, color=INK)
    save(fig, "fig6_match_gaps.png")


def main():
    """results/ 의 분석 결과 CSV를 읽어 그림 1~6을 차례로 만든다."""
    setup_font()
    os.makedirs(FIG_DIR, exist_ok=True)
    data, _, games = analysis.load()

    def read(name, **kw):
        return pd.read_csv(os.path.join(analysis.RESULT_DIR, name), **kw)

    fig1_timeline(data, games)
    fig2_top3(read("top3_share_summary.csv", index_col=[0, 1]))
    fig3_mma_vs_fencing(read("gtrends_yearly_world.csv", index_col=0))
    fig4_games_share(read("athlete_metrics.csv", index_col=0))
    fig5_income_gap(read("income_gap.csv", index_col=0))
    fig6_match_gaps(read("match_gaps.csv", index_col=0))


if __name__ == "__main__":
    main()
