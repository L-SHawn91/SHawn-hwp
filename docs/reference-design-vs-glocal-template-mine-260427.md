# Reference Design vs Glocal HWP/Mine Comparison 260427

working folder: `/home/mdge/github/SHawn-hwp`  
document class: `project` / design comparison

## Compared sources

### Reference design model
- `/home/mdge/Clouds/onedrive/과제/참고자료/서울바이오클러스터 계획서.pdf`
- `/home/mdge/Clouds/onedrive/과제/참고자료/항암면역 계획서.pdf`
- Extracted design profile: `docs/reference-design-style-profile-260427.md`

### Current / user documents
- Official glocal template candidate: `/home/mdge/Clouds/gdrive/2026 글로컬랩/참고자료/2026 문서/붙임2-1-2. 2026년도 글로컬랩 연구계획서_컨소시엄형(양식)_공지 2026년.hwp`
- User MG HWPX candidate: `/home/mdge/Clouds/gdrive/2026 글로컬랩/한민기 박사/붙임2-1-2. 2026년도 글로컬랩 연구계획서_컨소시엄형(양식)_MG.hwpx`
- User root Final HWP candidate: `/home/mdge/Clouds/gdrive/2026 글로컬랩/붙임2-1-2. 2026년도 글로컬랩 연구계획서_컨소시엄형_Final.hwp`

## Extracted signal matrix

| source | chars | lines | dashboard signals | technical heading signals | evidence/figure signals | instruction leftovers | image mentions | table mentions | markdown headings |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| official_template_hwp | 3,614 | 223 | 2 | 32 | 15 | 0 | 0 | 93 | 0 |
| mine_mg_hwpx | 8,551 | 163 | 9 | 9 | 73 | 1 | 51 | 6 | 42 |
| mine_root_final_hwp | 15,839 | 504 | 4 | 80 | 56 | 0 | 0 | 138 | 0 |

## High-level comparison

### 1. Reference design model
- **서울바이오클러스터형**은 첫 장부터 `대시보드형 요약 페이지`이다. 네이비 title band, 핵심목표 카드, 번호 배지, 추진전략/구성요소/기대효과 박스가 한 화면에 잡힌다.
- **항암면역형**은 dense evidence style이다. 그림과 근거 bullet을 같은 테두리 박스 안에 배치해, 과학적 근거와 해석을 동시에 읽게 만든다.
- 공통 장점은 “평가자가 구조를 먼저 보고, 세부문장을 나중에 읽는” 편집이다.

### 2. Existing official glocal template
- 공식 양식은 목차/항목/필수 구조를 제공하지만, 디자인적으로는 **채워 넣는 문서**에 가깝다.
- 네이비 dashboard, 핵심 메시지 카드, figure+interpretation box 같은 평가자 안내 장치가 거의 없다.
- 장점: 제출 항목과 순서 보존에는 안전하다.
- 약점: 그대로 채우면 긴 본문/그림/표가 나열되어, 핵심 전략과 차별성이 한눈에 들어오기 어렵다.

### 3. User MG / Final draft
- 내 작성본은 공식 양식보다 본문·그림·기관 서술·연구역량/인력/장비 신호가 훨씬 풍부하다.
- 특히 비전, BRIDGE, 난임, AI, 컨소시엄 기관, 장비/인력 등 실제 설득 재료는 이미 많이 들어 있다.
- 다만 추출 텍스트 기준으로는 `#` heading이 많고, 그림 캡션/본문/표가 섞여 있어 **시각 hierarchy를 HWP에서 재정렬할 여지**가 크다.
- 현재 상태는 “내용 재료는 충분하지만, 모범 PDF처럼 평가자용 dashboard/evidence-box 문법으로 압축·재배치되지는 않은 상태”로 판단한다.

## Section-by-section design mapping recommendation

| Glocal section | Current problem likely | Reference style to apply | Concrete HWP redesign action |
|---|---|---|---|
| 목차 / 앞부분 | 항목 나열 중심 | 서울바이오클러스터 dashboard | 1-page `핵심요약` 신설: 비전, 핵심목표 2개, 추진전략 3개, 기대효과 2개 카드화 |
| 1. 연구개발과제 필요성 | 긴 서술이 흩어질 위험 | 항암면역 evidence-box | 질병/지역/기술 필요성을 `그림 + 근거 bullet + 시사점` 박스 2~3개로 재배치 |
| 2. 목표 | 목표와 세부목표가 문장형으로 묻힐 위험 | dashboard-blue | 최종목표 1개 + 세부목표 2~3개를 흰색 rounded card / 번호 배지로 강조 |
| 4. 연구소 발전계획 | 비전/육성/지역거점/거버넌스가 길게 이어짐 | dashboard + technical body | 첫 페이지는 대시보드, 뒤 페이지는 H1/H2/H3 heading hierarchy 통일 |
| 5. 연구수행계획 | 추진전략/체계/성과활용이 복잡함 | 서울바이오클러스터 flow/grid | 추진체계를 3-column grid, 성과활용을 2-column effect box로 정리 |
| 6. 인력/장비/예산 | 정보량 많고 표가 무거움 | technical-body table style | 표 header navy, 핵심 cell light-blue, 강조 border orange; 장비/인력은 icon-like label 적용 |
| 그림 많은 페이지 | 그림 의미가 바로 안 보일 수 있음 | evidence-box | 모든 그림에 `1-line caption + 평가 포인트 bullet` 강제 |

## Design gap scorecard

| Criterion | Official template | User draft | Target reference | Gap / action |
|---|---:|---:|---:|---|
| 공식 항목 보존 | 5 | 4 | 3 | 공식 양식 골격은 유지해야 함 |
| 첫 장 임팩트 | 1 | 2 | 5 | dashboard summary page 필요 |
| 제목 hierarchy | 2 | 3 | 5 | H1 navy band / H2 blue label / H3 bold numbering 필요 |
| 그림-해석 연결 | 1 | 3 | 5 | 그림마다 해석 bullet 추가 |
| 표 가독성 | 2 | 3 | 5 | header/emphasis style 통일 |
| 평가자 skim-read | 1 | 2 | 5 | 핵심 메시지 카드와 번호 배지 필요 |
| 내용 충실도 | 1 | 4 | 4 | 내 작성본은 내용 재료가 강함 |

## Recommended redesign strategy

1. **공식 양식 구조는 유지**한다. 항목 번호/목차/제출 요구사항을 바꾸면 위험하다.
2. 각 큰 항목 첫 페이지에만 `proposal-dashboard-blue`를 적용한다. 전체 페이지를 전부 화려하게 만들 필요는 없다.
3. 과학적 근거/필요성/선행연구 페이지는 `proposal-evidence-box`로 바꾼다.
4. 일반 본문은 `proposal-technical-body`로 heading/table/bullet만 정돈한다.
5. HWP 자동화는 먼저 “스타일 제안/디자인 QA”로 시작하고, 실제 HWP 재생성은 사본에서만 한다.

## Automation tasks for SHawn-hwp

- Add design profile schema to template profile: `design_profile.preset`, `colors`, `heading_patterns`, `components`, `qa_rules`.
- Add section classifier: `dashboard`, `technical_body`, `evidence_box`, `table_heavy`, `figure_heavy`.
- Add design QA report: detect missing dashboard, dense page without box, figure without caption/interpretation, heading hierarchy inconsistency, bullet depth >2.
- Add HWPX candidate generator v1: rebuild from Markdown/JSON into reference-template HWPX using navy/blue heading and card/table blocks.
- Later: use official HWP template as protected shell and inject redesigned section blocks into safe editable regions.

## Bottom line

현재 내 작성본은 내용은 충분하지만, 모범 참고자료처럼 `평가자용 시각 구조`가 부족하다. 최적 방향은 공식 글로컬랩 양식의 항목/순서를 유지하면서, 각 주요 섹션 첫 페이지를 dashboard화하고, 근거 파트는 figure+evidence box로 재편하는 것이다.
