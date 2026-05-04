# Reference Design Style Profile 260427

working folder: `/home/mdge/github/SHawn-hwp`  
document class: `project` / design profile

## Reference source

사용자가 모범으로 지정한 Mac 경로:

`/Users/soohyunglee/Library/CloudStorage/OneDrive-개인/과제/참고자료`

Linux mirror에서 확인한 대응 경로:

`/home/mdge/Clouds/onedrive/과제/참고자료`

확인 파일:

- `서울바이오클러스터 계획서.pdf` — 29 pages, A4, scanned PDF
- `항암면역 계획서.pdf` — 37 pages, A4, scanned PDF

원본은 수정하지 않았고, 분석용 사본/렌더링만 사용함.

## Design direction extracted from references

### 1. 서울바이오클러스터형: high-impact evaluator dashboard style

앞쪽 페이지는 “평가자가 10초 안에 구조를 잡는” 대시보드형 편집에 가깝다.

핵심 특징:

- 상단에 대분류/단위과제/기관 로고를 고정 배치
- 진한 네이비 계열의 큰 제목 바 사용
- 프로젝트명, 단위과제명, 타위과제명 등을 좁은 라벨 박스로 정리
- 핵심 목표를 흰색 rounded box로 크게 강조
- `01`, `02`, `03`, `04` 번호 원형/배지로 흐름을 분절
- 추진전략/기술사업화/구성요소/기대효과를 한 페이지 안에서 블록화
- 표, 도식, bullets가 혼합되지만 시각 계층이 명확함
- 페이지 하단 로고와 page number를 고정

HWP 적용 방향:

- 표지/요약/섹션 첫 페이지에는 일반 본문보다 “요약 카드형” 레이아웃을 적용
- 네이비 title band + 파란 section badge + 흰색 카드 박스 조합 사용
- HWP 표를 layout grid로 쓰되, 내용 표와 디자인 표를 구분
- 핵심 메시지 박스는 1페이지당 1~2개로 제한

### 2. 서울바이오클러스터형 본문: structured technical proposal style

본문 페이지는 일반 연구계획서처럼 보이지만 heading hierarchy가 강하다.

핵심 특징:

- 페이지 상단에 현재 장/과제명을 작게 반복 표시
- 대제목은 진한 네이비 horizontal band
- 중제목은 파란 박스 또는 번호형 라벨 `1.1`, `1.1.1`
- 본문은 넓은 여백 안에 bullets 중심으로 구성
- 표는 파란 header + 주황/붉은색 강조 테두리로 핵심 행/열을 강조
- 그림은 본문 오른쪽 또는 중앙에 삽입하고 캡션은 작게 둠
- bullet depth가 2단 이상이지만 들여쓰기와 기호가 안정적임

HWP 적용 방향:

- `H1`: 네이비 full-width band
- `H2`: 파란 label box + 얇은 horizontal rule
- `H3`: 번호형 bold heading
- 본문 bullet은 2depth까지만 기본 허용
- 표 header는 진한 파랑, 강조 cell은 연한 하늘색/주황 outline

### 3. 항암면역 계획서형: dense scientific evidence dossier style

이 참고문서는 디자인 화려함보다 논리 밀도와 근거 배치가 강점이다.

핵심 특징:

- A4 한 페이지에 많은 정보를 배치하되, 큰 section 번호로 시작
- 본문은 박스 테두리 안에서 그림+텍스트 2단 구성을 자주 사용
- scientific figure를 왼쪽/상단에 놓고 오른쪽/하단에 근거 bullet을 붙임
- `○`, `•` bullets를 규칙적으로 사용
- 큰 도식 아래에 바로 해석 문장을 붙여 평가자가 그림 의미를 놓치지 않게 함
- 페이지 번호는 하단 중앙 `- 5 -` 형태
- 색은 제한적이고, 도식 자체의 색을 활용함

HWP 적용 방향:

- 근거/필요성/선행연구 파트에는 “도식+근거 bullet” 2단 박스 사용
- 그림 단독 삽입 금지: 반드시 1~3줄 해석 caption 또는 implication bullet 동반
- 과도한 색보다는 얇은 회색/검정 테두리와 안정적 grid 사용
- dense page는 허용하되 section title과 box boundary를 명확히 유지

## Proposed SHawn-hwp style presets

### preset: `proposal-dashboard-blue`

용도: 표지 다음 요약, 과제 개요, 핵심 목표, 추진전략, 기대효과.

```yaml
style_id: proposal-dashboard-blue
page:
  size: A4
  margins_mm: {top: 14, bottom: 14, left: 18, right: 18}
colors:
  navy: "#071B3A"
  blue: "#0B5FA5"
  light_blue: "#EAF4FF"
  gold: "#B88A2A"
  gray_line: "#D8DEE8"
fonts:
  heading: "Pretendard/맑은 고딕 bold"
  body: "맑은 고딕"
components:
  - top_context_header
  - navy_title_band
  - key_message_card
  - numbered_badge_grid
  - two_column_effect_box
  - footer_logo_page_number
```

### preset: `proposal-technical-body`

용도: 연구개발 필요성, 목표/내용, 추진전략, 방법론.

```yaml
style_id: proposal-technical-body
heading_hierarchy:
  H1: navy_full_width_band
  H2: blue_number_label_with_rule
  H3: bold_numbered_heading
paragraph:
  body_size_pt: 10.5
  line_spacing_percent: 160
  bullet_depth_limit: 2
tables:
  header_fill: navy
  header_text: white
  emphasis_border: orange
  cell_padding_mm: 1.5
figures:
  require_caption: true
  require_interpretation_bullet: true
```

### preset: `proposal-evidence-box`

용도: 선행연구, unmet need, 연구역량, 핵심기술 설명.

```yaml
style_id: proposal-evidence-box
box:
  border_color: "#333333"
  border_width_pt: 0.6
  fill: white
layout:
  default: two_column_figure_text
  figure_max_width_percent: 45
  text_max_width_percent: 55
bullets:
  primary: "○"
  secondary: "•"
  indent_mm: [0, 5]
page_number:
  location: bottom_center
  format: "- {page} -"
```

## Automation implications for SHawn-hwp

### 1. Template profile extensions

Add design metadata in addition to structural profile:

```yaml
design_profile:
  preset: proposal-dashboard-blue | proposal-technical-body | proposal-evidence-box
  colors:
    primary: "#071B3A"
    secondary: "#0B5FA5"
    accent: "#B88A2A"
  heading_patterns:
    - level: 1
      style: navy_full_width_band
    - level: 2
      style: blue_number_label_with_rule
  components:
    - name: key_message_card
      required_fields: [title, body]
    - name: figure_evidence_box
      required_fields: [image, caption, interpretation]
  qa_rules:
    require_caption_for_images: true
    warn_if_bullet_depth_exceeds: 2
    warn_if_page_has_no_heading: true
    warn_if_dense_page_without_boxing: true
```

### 2. Proposed HWP improvement pipeline

```text
current HWP/HWPX proposal
  -> extract text/layout signals
  -> classify section type
  -> apply style preset per section
  -> rebuild candidate HWPX from reference template
  -> template/profile QA
  -> PDF visual review packet
```

### 3. What should be automated first

1. Section heading normalization
2. Navy/blue title band generation
3. Key message card generation from section summaries
4. Figure caption + interpretation enforcement
5. Table header/emphasis styling
6. Footer/page-number normalization
7. Design QA report

## Practical design rule for user's research proposals

- `요약/비전/추진체계` 페이지는 서울바이오클러스터형 대시보드 스타일 사용
- `필요성/선행연구/기술근거` 페이지는 항암면역형 evidence-box 스타일 사용
- `연구내용/추진전략/성과계획` 페이지는 두 스타일을 혼합하되, H1/H2/H3 hierarchy를 반드시 통일

This should become the design target for SHawn-hwp's future HWP/HWPX improvement route.
