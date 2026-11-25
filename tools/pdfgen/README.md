# PDF 생성 스크립트

회원·상품·주문·결제 도메인 문서 PDF를 만드는 스크립트다. `build.sh`는 회원 도메인만 만들고, 상품·주문·결제는 아래 "상품·주문·결제 도메인"의 명령으로 따로 만든다. HTML을 만든 뒤 Chrome headless로 A4 PDF를 출력한다 (폰트 Apple SD Gothic Neo).

## 실행

```bash
tools/pdfgen/build.sh /tmp/pdfout            # 출력 폴더에만 생성
tools/pdfgen/build.sh /tmp/pdfout --install  # docs/pdf/의 PDF 6개를 덮어씀
```

## 구성

| 폴더 | 파일 | 만드는 문서 |
|---|---|---|
| `cols/` | `data.py` 테이블·컬럼·코드 값 (단일 출처)<br>`order.py` 테이블·컬럼 그룹 순서 (규칙 8)<br>`related.py` 코드 값별 관련 정보<br>`render.py` 렌더러 | `회원_테이블이름_확정.pdf`, `회원_컬럼정의서_검토용.pdf` |
| `cmm/` | `cmm.py` (`cols/data.py`의 코드를 읽음) | `공통코드_CMM_CODE_회원도메인.pdf`, `code_ids.json` (가상 CODE_ID) |
| `col_decision/` | `col_decision.py` 컬럼 검토 결정 C-1~C-99 (선택지·답변) | `회원_컬럼검토_결정.pdf` |
| `rules/` | `rules.py` 지시 규칙 1~8 (정렬 예시는 `cols/order.py`에서 읽음) | `DB설계_지시규칙_1-8.pdf` |
| `policy/` | `content.py` 조문 내용<br>`render.py` 렌더러<br>`prd_content.py`, `ord_content.py`, `pay_content.py`와 렌더러 `render_domain.py` (상품·주문·결제) | `회원도메인_정책명세.pdf`, `상품도메인_정책명세.pdf`, `주문도메인_정책명세.pdf`, `결제도메인_정책명세.pdf` |
| `decision_change/` | `chg.py` 변경 안내 쪽<br>`merge.swift` PDF 앞에 쪽 붙이기 | 회원결정 3·8·10·12·13·17·20·21·22·25·26·27·28·30·31·32·35·39·43·47번, 선행결정 3·5·14번의 첫 쪽 |
| `erd/` | `erd.py` ERD 생성 (`cols/data.py`·`order.py`를 읽고 `prd/erd_prd.py`, `ord/erd_ord.py`, `pay/erd_pay.py`를 불러 씀, `build.sh`와 별도 실행) | `docs/mmd/*.mmd` 5개, `docs/drawio/전체_ERD.drawio` |
| `prd/` | `data.py` 상품 테이블·컬럼·코드 값 (단일 출처, 확정 표시 포함)<br>`cmm.py` 공통코드 (회원 `code_ids.json` 뒤에 이어서 발번)<br>`render.py`, `col_review.py`(PC-n), `erd_prd.py` | `상품_테이블이름_검토.pdf`, `상품_컬럼정의서_검토용.pdf`, `상품_컬럼검토_결정.pdf`, `공통코드_CMM_CODE_상품도메인.pdf` |
| `prd_decision/` | `gen.py`, `data1~3.py` 상품결정 본문과 설계 패턴 | `상품결정_NN_*.pdf` 53개, `상품도메인_설계패턴_1-53.pdf` |
| `ord/` | `data.py` 주문 테이블·컬럼·코드 값 (단일 출처, `CONFIRMED_GROUPS` 확정 표시)<br>`render.py`, `col_review.py`(OC-n), `erd_ord.py` | `주문_테이블이름_검토.pdf`, `주문_컬럼정의서_검토용.pdf`, `주문_컬럼검토_결정.pdf` (공통코드 PDF는 아직 없음, `CODE_ID` 미발번) |
| `pay/` | `data.py` 결제 테이블·컬럼·코드 값 (단일 출처, 확정 표시·`CONFIRM` 포함, 원장·로그·대사의 FK 없는 값 참조는 `ref()`)<br>`render.py`(`ord/style.css`를 함께 씀, `col_review.py`의 `C`를 읽어 PYC 범위 계산), `col_review.py`(PYC-n, 새 결정은 `C` 끝에), `erd_pay.py` | `결제_테이블이름_검토.pdf`, `결제_컬럼정의서_검토용.pdf`, `결제_컬럼검토_결정.pdf` (공통코드 PDF는 아직 없음, `CODE_ID` 미발번) |
| `ord_decision/` | `gen.py`, `d1~3.py`, `md.py`, `orig/`(결정 당시 원문) 주문결정 본문과 설계 패턴. 나중에 바뀐 결정은 `gen.py`의 `CHANGES`에 변경 안내를 적는다 (지금 5-5, 9-2, 3-9, 4-6) | `주문결정_NN-NN_*.pdf` 80개, `주문도메인_설계패턴_80.pdf` |
| `pay_decision/` | `gen.py`, `fields.py`(12개 분야 이름·소개·패턴 수), `orig/`(2026-11-25 대화 원문, 패턴마다 질문과 답변, `history_1~4.md` 부록). `ord_decision/`의 `md.py`·`style.css`를 함께 쓴다. 선택지·추천·답은 원문에서 읽고, 답이 한 글자가 아니었던 2-1·7-1·12-4는 `CHOSEN`, 결정 단계 기록은 `NOTE`에 적는다 | `결제결정_NN-NN_*.pdf` 76개, `결제도메인_설계패턴_76.pdf` |
| `screen/` | `cart.html`, `order.html`, `admin_order.html` 화면 와이어프레임 (HTML 원본을 직접 고침) | `docs/pdf/화면/장바구니_화면.pdf`, `주문서_화면.pdf`, `관리자_주문_화면.pdf` |
| `util/` | `pdf2txt.swift` PDF 텍스트 추출 (검증용)<br>`pg.swift` 쪽수 확인·쪽 PNG | |

- 실행 순서가 중요하다. `cmm.py`가 만든 `code_ids.json`을 `cols/render.py`가 읽는다.
- 코드 값을 추가하면 가상 CODE_ID가 밀릴 수 있다. 생성 후 `code_ids.json`을 이전 것과 비교한다.

## 상품·주문·결제 도메인

HTML을 만든 뒤 Chrome headless로 PDF를 출력해 `docs/pdf/`의 해당 위치에 복사한다.

```bash
OUT=/tmp/pdfout
# 상품
python3 tools/pdfgen/prd/cmm.py $OUT/prd/cmm.html <회원 빌드 출력폴더>/code_ids.json
python3 tools/pdfgen/prd/render.py $OUT/prd; python3 tools/pdfgen/prd/col_review.py $OUT/prd/review.html
python3 tools/pdfgen/prd_decision/gen.py $OUT/prd_dec
# 주문
python3 tools/pdfgen/ord/render.py $OUT/ord; python3 tools/pdfgen/ord/col_review.py $OUT/ord/review.html
python3 tools/pdfgen/policy/render_domain.py ord_content $OUT/ord_policy.html
python3 tools/pdfgen/ord_decision/gen.py $OUT/ord_dec      # dec/*.html, patterns.html
# 결제
python3 tools/pdfgen/pay/render.py $OUT/pay; python3 tools/pdfgen/pay/col_review.py $OUT/pay/review.html
python3 tools/pdfgen/policy/render_domain.py pay_content $OUT/pay_policy.html
python3 tools/pdfgen/pay_decision/gen.py $OUT/pay_dec      # dec/*.html, patterns.html, names.txt
# 화면: tools/pdfgen/screen/*.html을 그대로 PDF로 출력 (A4 가로)
```

- PDF 복사 위치 (names → `*_테이블이름_검토`, columns → `*_컬럼정의서_검토용`, review → `*_컬럼검토_결정`):
  - 상품: `docs/pdf/테이블_컬럼/상품/`, 공통코드(cmm) → `docs/pdf/테이블_컬럼/공통/공통코드_CMM_CODE_상품도메인.pdf`, 결정·설계 패턴 → `docs/pdf/결정/상품결정/`, `docs/pdf/설계패턴/`.
  - 주문: `docs/pdf/테이블_컬럼/주문/`, 정책명세 → `docs/pdf/정책명세/주문도메인_정책명세.pdf`, 결정 → `docs/pdf/결정/주문결정/`, 설계 패턴 → `docs/pdf/설계패턴/주문도메인_설계패턴_80.pdf`.
  - 결제: `docs/pdf/테이블_컬럼/결제/`, 정책명세 → `docs/pdf/정책명세/결제도메인_정책명세.pdf`, 결정 → `docs/pdf/결정/결제결정/`, 설계 패턴 → `docs/pdf/설계패턴/결제도메인_설계패턴_76.pdf`.
- 결정 기록 범위 표기: 상품 "PC-1~PC-n"은 `prd/col_review.py`, `prd/render.py`, `prd/cmm.py`, 주문 "OC-16~OC-n"은 `ord/col_review.py`, `ord/render.py`, `policy/ord_content.py` 세 곳에 있어 함께 바꾼다. 결제 "PYC-1~PYC-n"은 `pay/render.py`가 `col_review.py`의 `C`에서 계산한다.
- Python 3.9는 한글이 든 약 1000바이트 넘는 소스 줄에서 "Non-UTF-8 code" 오류를 낸다. 긴 문자열은 나눠 쓴다 (`awk '{if (length($0)>950) print NR}'`로 확인).

## 회원결정 변경 안내 쪽

`docs/pdf/결정/회원결정/`의 3·8·10·12·13·17·20·21·22·25·26·27·28·30·31·32·35·39·43·47번에는 변경 안내 쪽이 이미 붙어 있다 (3·8·10·12·13·20·21·22·25·26·27·30·32·35·43은 컬럼 검토, 나머지는 법률 검토이고 28번에는 컬럼 검토 보완 행도 있다). 다시 만들 때는 원본(커밋 `77b85b7`의 PDF)에 붙인다. 선행결정 3·5·14번(`chgS03.pdf` 컬럼 검토 C-70·C-76, `chgS05.pdf` C-25·C-39·C-49·C-70·C-72, `chgS14.pdf` C-85)의 원본은 커밋 `2cb6480`의 `docs/pdf/선행결정/`의 해당 PDF다. 원본 커밋 당시 경로는 `docs/pdf/회원결정/`, `docs/pdf/선행결정/`이고, 2026-11-25에 `docs/pdf/결정/` 아래로 옮겼다.

```bash
git show 77b85b7:"docs/pdf/회원결정/회원결정_28_개인정보보유기간과파기.pdf" > /tmp/orig28.pdf
swift tools/pdfgen/decision_change/merge.swift /tmp/pdfout/chg28.pdf /tmp/orig28.pdf "docs/pdf/결정/회원결정/회원결정_28_개인정보보유기간과파기.pdf"
```

## 검증

생성한 PDF의 텍스트를 이전 PDF와 비교한다.

```bash
swift tools/pdfgen/util/pdf2txt.swift 새.pdf 새.txt
swift tools/pdfgen/util/pdf2txt.swift 이전.pdf 이전.txt
```

## 저장소에 없는 생성 스크립트

선행결정, 회원결정 1~47번 본문, 회원·전체 설계패턴, 후보테이블, 용어집, 법률검토 PDF의 생성 스크립트는 여기 없다 (상품·주문·결제 설계패턴은 `prd_decision/`, `ord_decision/`, `pay_decision/`에 있다). 지시규칙은 2026-11-22에 PDF 내용을 바탕으로 `rules/`에 새로 만들었다. 앞의 문서들은 세션 임시 폴더에서 만들었고, 그 폴더가 지워져서 최종본을 확인할 수 없다. 법률검토 PDF는 저장소에 올리지 않는 문서다. L10~L12는 로컬 전용 `docs/pdf/법률검토/_src/`에 생성 스크립트가 있다 (`build.sh`).

## ERD (mmd, drawio)

컬럼이 바뀌면 다시 만든다. `build.sh`에는 들어 있지 않다.

```bash
python3 tools/pdfgen/erd/erd.py
```

- mmd: 회원 컬럼 포함판(업무 컬럼만, 공통 컬럼 생략)과 회원·상품·주문·결제 관계 요약판(테이블과 관계만). 상품·주문·결제 배치는 `prd/erd_prd.py`, `ord/erd_ord.py`, `pay/erd_pay.py`의 `POS`에서 직접 정한다 (테이블을 추가하면 넣어야 함). 결제는 결정으로 FK 없이 둔 값 참조(`ref()` 컬럼)를 그리지 않는다.
- 생성 날짜가 모든 파일에 찍혀, 한 도메인만 고쳐도 다른 도메인 파일의 날짜 줄이 바뀐다.
- drawio 1개 파일 (규칙 6: 전체 ERD 1개 파일, 도메인별 페이지): 페이지 "회원 (MBR) 관계 요약"(배치는 `summary_positions()`에서 직접 정함), "회원 (MBR)"(컬럼 포함, 그룹별 열 배치), "상품 (PRD) 관계 요약", "주문 (ORD) 관계 요약", "결제 (PAY) 관계 요약".
- 다른 도메인 FK 대상은 회색 점선 상자의 후보 이름으로만 그린다 (`EXT_NOTE`). 다른 도메인을 설계하면 페이지를 추가한다.
- 검증: mmd는 mermaid-cli로 렌더링해 문법을 확인한다. drawio는 데스크톱 앱 CLI로 PNG를 뽑아 본다 (페이지 번호는 1부터).
  ```bash
  "/Applications/draw.io.app/Contents/MacOS/draw.io" --export --format png --page-index 1 --scale 0.6 --output <출력.png> docs/drawio/전체_ERD.drawio
  ```
