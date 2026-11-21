# 올림픽 3일의 스타, 나머지 1,458일은? — 펜싱 프로 리그의 가능성

CAS1100-01 Computer Programming 프로젝트 (2026 Fall) · 2015101013 Jangbo Ha

펜싱 세계 챔피언이 '돈 버는 스타'가 되지 못하는 이유를 5종목 3묶음
(분석 대상: 펜싱 / 결투형 프로: 복싱·MMA / 리그형: 축구·야구)의
위키피디아 조회수, 구글 트렌드, 직접 조사한 수입·경기 일정 데이터로 분석합니다.

| 연구 질문 | 사용한 지표 |
|---|---|
| Q1. 펜싱은 '올림픽 때만 보는 스포츠'인가? | 상위 3일 비율, 올림픽 배수, 평상시 관심도 |
| Q2. 펜싱 스타는 왜 '돈 버는 스타'가 되지 못하는가? | 대회 집중도, 관심도 배수 vs 수입 배수 |
| Q3. 펜싱 프로 리그는 가능한가? | MMA 기준선(2004년), 경기 간 평균 간격, FIE 대회 일정 |

### 분석 결과

- **Q1** 한국어 위키에서 펜싱의 연간 조회가 가장 많았던 3일의 비중은 2016~2025년 중앙값 기준 13.9%로 다섯 종목 중 가장 높았습니다. 영어판에서는 MMA(2.6%)가 펜싱(2.4%)보다 높았습니다.
- **Q2** 금액 배수는 타 종목 선수의 연간 총수입을 2026년 펜싱 세계선수권 개인전 우승 상금(4만 달러)으로 나눈 값입니다. 펜싱 선수의 연간 총수입은 자료에 없어 선수 간 연 소득 격차나 관심도가 소득에 미치는 효과를 추정하기 어렵습니다.
- **Q3** 파리 올림픽에서 오상욱은 개인전 4일 뒤 단체전에 출전했습니다. FIE 개인전 386건에서 연속 출전 간격의 선수별 중앙값은 구본길·김지연 28일, 김준호 32일, 오상욱 35일입니다. 주간 리그의 지속 가능성을 판단하려면 반복 출전과 시즌 운영 자료가 더 필요합니다.

## 1. 환경 설정

Python 3.9 이상에서 실행됩니다 (3.9 ~ 3.14에서 같은 결과 확인).

```bash
git clone https://github.com/ffff101fff/ff1100.git
cd ff1100
pip install -r requirements.txt
```

- git이 없으면 GitHub 페이지의 **Code → Download ZIP** 으로 받아 압축을 푼 폴더에서 실행하면 됩니다.
- Windows에서 `python` 명령이 없으면 `py` 를 쓰세요 (`py -m pip install -r requirements.txt`, `py main.py`).
- 경로는 모두 저장소 폴더 기준이므로, 다른 폴더나 IDE(VS Code 등)에서 실행해도 같은 파일을 읽고 씁니다.

그래프의 한글은 Windows는 '맑은 고딕', Mac은 'AppleGothic'으로 자동 표시됩니다.
Linux는 `sudo apt install fonts-nanum` 으로 나눔고딕을 설치하세요.

## 2. 실행 방법 (보고서·발표 결과 재현)

저장소 폴더에서 아래 한 줄을 실행하면 보고서와 발표 영상의 표·그래프가 그대로 만들어집니다.

```bash
python main.py
```

- 화면: 연구 질문별 분석 결과 표 (보고서의 숫자는 모두 이 출력에서 나왔습니다)
- `results/` : 분석 결과 CSV 10개
- `figures/` : 그래프 6개 (`fig1_timeline_ko.png` ~ `fig6_match_gaps.png`, 같은 이름의 `.svg` 벡터 그림도 함께 저장)

### 종목·선수 조회 (시연용)

```bash
python main.py --list             # 조회할 수 있는 종목·선수 이름
python main.py --sport fencing    # 종목의 상위 3일 비율, 올림픽 배수, 평상시 관심도 변화
python main.py --athlete oh_su    # 선수의 평상시 관심도, 대회 기간 하루 최고, 대회 집중도, 공개 수입
```

없는 이름을 넣으면 가능한 이름 목록을 보여 주고 종료합니다.

## 3. 입력 데이터

제안서와 함께 제출한 CSV 7개를 **변경 없이 그대로** 입력으로 사용합니다.

| 파일 | 내용 | 크기 |
|---|---|---|
| `data/processed/interest.csv` | 5종목 관심도 (위키 일별·구글 트렌드 월별, 위키는 전체 조회 100만 건당으로 보정) | 43,442행 |
| `data/processed/athletes.csv` | 스타 선수 12명의 위키 일별 관심도 | 54,741행 |
| `data/processed/events.csv` | 올림픽·아시안게임 기간, UFC 리얼리티쇼 첫 방송일 | 13행 |
| `data/star_income.csv` | 공개 금액 (Forbes 총수입 6명, 오상욱은 세계선수권 우승 상금) + 출처 URL | 7행 |
| `data/match_load.csv` | UFC 연간 경기 수, 레알 마드리드·MLB 시즌 경기 수와 기간, 펜싱 하루 경기 수 + 출처 URL | 4행 |
| `data/match_dates.csv` | 복싱·MMA 스타와 오상욱의 경기 날짜 + 출처 URL | 64행 |
| `data/fie_results.csv` | 펜싱 선수 4명의 국제펜싱연맹(FIE) 개인전 출전 날짜·순위 | 386행 |

## 4. 데이터를 원본부터 다시 만들기 (선택)

수집이 끝난 원본이 `data/raw/` 에 들어 있으므로, 아래 명령으로 통합 데이터셋 3개를 원본에서 다시 만든 뒤
분석할 수 있습니다. 만들어지는 파일은 제출한 CSV와 같습니다.

```bash
python main.py --rebuild
```

원본 자체를 새로 수집하려면:

```bash
python collect_wiki.py    # 위키피디아 일별 조회수 (Wikimedia Pageviews API, 인터넷 필요)
python load_gtrends.py    # data/raw/gtrends/ 에 내려받은 구글 트렌드 CSV를 하나로 정리
```

구글 트렌드는 공식 API가 없어 웹에서 CSV를 내려받습니다. 단어(fencing)로 검색하면 울타리 검색이,
boxing은 박싱데이 검색이 섞이므로 **'스포츠 주제' ID**로 검색하고, 종목들을 **한 화면에서** 비교해야
같은 척도가 됩니다. 아래 링크의 'Interest over time' 다운로드 버튼(↓)으로 받아 `data/raw/gtrends/` 에
저장하세요. (링크에는 처음 구성에 있던 태권도 /m/07gyv 가 함께 있으며, 같은 화면의 값이라 척도는 같고
`build_dataset.py` 가 분석 대상 종목만 남깁니다.)

| 저장할 이름 | 링크 |
|---|---|
| `world.csv` | https://trends.google.com/trends/explore?date=all&q=%2Fm%2F02y8z,%2Fm%2F07gyv,%2Fm%2F01cgz,%2Fm%2F01h7lh,%2Fm%2F018jz&hl=en |
| `korea.csv` | https://trends.google.com/trends/explore?date=all&geo=KR&q=%2Fm%2F02y8z,%2Fm%2F07gyv,%2Fm%2F01cgz,%2Fm%2F01h7lh,%2Fm%2F018jz&hl=en |

## 5. 파일 구조

| 파일 | 역할 |
|---|---|
| `main.py` | 진입점. 전체 실행, `--rebuild`, 종목·선수 조회 (입력 파일·이름 오류 처리) |
| `config.py` | 기간, 5종목 3묶음, 위키 문서·선수 목록, 구글 트렌드 주제 ID, 이벤트 달력, 파일 경로 |
| `analysis.py` | Q1 상위 3일 비율·올림픽 배수·평상시 관심도 / Q2 대회 집중도·관심도 배수 vs 수입 배수 / Q3 MMA 기준선·경기 간격·FIE 일정 |
| `figures.py` | 그래프 6개 생성 |
| `build_dataset.py` | 원본 → 통합 데이터셋 (빈 날짜 0 채우기, 전체 조회수로 나눈 실질 관심도 `value_norm`) |
| `collect_wiki.py` | 위키 종목·선수·전체 일별 조회수 수집 (리다이렉트 처리) |
| `load_gtrends.py` | 구글 트렌드 CSV 읽기 (설명 줄 제거, `<1` 처리, 한글/영어 열 이름 통일) |
| `data/raw/gtrends_keyword/`, `data/raw/archive/` | 초기 수집 자료 (단어 검색의 동음이의어 문제 증거, 이전 비교 구성) |

## 제안서 통계 검정 재현

`python proposal_checks.py`로 상위 1·3·10일 민감도, 올림픽 상대 관심도 회귀(Newey–West 7·30일), 대회 후 60~90일 잔존율, 한국어판 선수 집중도 정확 순열검정 및 Google Trends 월별 비교를 출력합니다. 입력은 제안서 제출본 CSV입니다.
