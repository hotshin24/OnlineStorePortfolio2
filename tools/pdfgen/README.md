# PDF 생성 스크립트

회원·상품·주문·결제·배송 도메인 문서 PDF를 만드는 스크립트다. `build.sh`는 회원 도메인만 만들고, 상품·주문·결제·배송은 아래 "상품·주문·결제 도메인"의 명령으로 따로 만든다. HTML을 만든 뒤 Chrome headless로 A4 PDF를 출력한다 (폰트 Apple SD Gothic Neo).

## 실행

```bash
tools/pdfgen/build.sh /tmp/pdfout            # 출력 폴더에만 생성
tools/pdfgen/build.sh /tmp/pdfout --install  # docs/pdf/의 PDF 6개를 덮어씀
```

## 구성

| 폴더 | 파일 | 만드는 문서 |
|---|---|---|
| `cols/` | `data.py` 테이블·컬럼·코드 값 (단일 출처)<br>`order.py` 테이블·컬럼 그룹 순서 (규칙 8)<br>`related.py` 코드 값별 관련 정보<br>`render.py` 렌더러 | `회원_테이블이름_확정.pdf`, `회원_컬럼정의서_검토용.pdf` |
| `cmm/` | `cmm.py` (`cols/data.py`의 코드를 읽음) | `공통코드_CMM_CODE_회원도메인.pdf` (그룹 48개, 값 322개), `code_ids.json` (가상 CODE_ID) |
| `col_decision/` | `col_decision.py` 컬럼 검토 결정 C-1~C-99 (선택지·답변) | `회원_컬럼검토_결정.pdf` |
| `rules/` | `rules.py` 지시 규칙 1~8 (정렬 예시는 `cols/order.py`에서 읽음) | `DB설계_지시규칙_1-8.pdf` |
| `policy/` | `content.py` 조문 내용<br>`render.py` 렌더러<br>`prd_content.py`, `ord_content.py`, `pay_content.py`, `dlv_content.py`, `inv_content.py`와 렌더러 `render_domain.py` (상품·주문·결제·배송·재고) | `회원도메인_정책명세.pdf`, `상품도메인_정책명세.pdf`, `주문도메인_정책명세.pdf`, `결제도메인_정책명세.pdf`, `배송도메인_정책명세.pdf`, `재고도메인_정책명세.pdf` |
| `decision_change/` | `chg.py` 변경 안내 쪽<br>`merge.swift` PDF 앞에 쪽 붙이기 | 회원결정 3·8·10·12·13·17·20·21·22·25·26·27·28·30·31·32·35·39·43·47번, 선행결정 3·5·14번의 첫 쪽 |
| `erd/` | `erd.py` ERD 생성 (`cols/data.py`·`order.py`를 읽고 `prd/erd_prd.py`, `ord/erd_ord.py`, `pay/erd_pay.py`, `dlv/erd_dlv.py`를 불러 씀, `build.sh`와 별도 실행) | `docs/mmd/*.mmd` 6개, `docs/drawio/전체_ERD.drawio` |
| `prd/` | `data.py` 상품 테이블·컬럼·코드 값 (단일 출처, 확정 표시 포함)<br>`cmm.py` 공통코드 (회원 `code_ids.json` 뒤에 이어서 발번)<br>`render.py`, `col_review.py`(PC-n), `erd_prd.py` | `상품_테이블이름_검토.pdf`, `상품_컬럼정의서_검토용.pdf`, `상품_컬럼검토_결정.pdf`, `공통코드_CMM_CODE_상품도메인.pdf` |
| `prd_decision/` | `gen.py`, `data1~3.py` 상품결정 본문과 설계 패턴 | `상품결정_NN_*.pdf` 74개, `상품도메인_설계패턴_1-53.pdf` |
| `ord/` | `data.py` 주문 테이블·컬럼·코드 값 (단일 출처, `CONFIRMED_GROUPS` 확정 표시)<br>`render.py`, `col_review.py`(OC-n), `erd_ord.py` | `주문_테이블이름_검토.pdf`, `주문_컬럼정의서_검토용.pdf`, `주문_컬럼검토_결정.pdf` (공통코드 PDF는 아직 없음, `CODE_ID` 미발번) |
| `pay/` | `data.py` 결제 테이블·컬럼·코드 값 (단일 출처, 확정 표시·`CONFIRM` 포함, 원장·로그·대사의 FK 없는 값 참조는 `ref()`)<br>`render.py`(`ord/style.css`를 함께 씀, `col_review.py`의 `C`를 읽어 PYC 범위 계산), `col_review.py`(PYC-n, 새 결정은 `C` 끝에), `erd_pay.py` | `결제_테이블이름_검토.pdf`, `결제_컬럼정의서_검토용.pdf`, `결제_컬럼검토_결정.pdf` (공통코드 PDF는 아직 없음, `CODE_ID` 미발번) |
| `ord_decision/` | `gen.py`, `d1~3.py`, `md.py`, `orig/`(결정 당시 원문) 주문결정 본문과 설계 패턴. 나중에 바뀐 결정은 `gen.py`의 `CHANGES`에 변경 안내를 적는다 (지금 5-5, 9-2, 3-9, 4-6) | `주문결정_NN-NN_*.pdf` 80개, `주문도메인_설계패턴_80.pdf` |
| `pay_decision/` | `gen.py`, `fields.py`(12개 분야 이름·소개·패턴 수), `orig/`(2026-11-25 대화 원문, 패턴마다 질문과 답변, `history_1~4.md` 부록). `ord_decision/`의 `md.py`·`style.css`를 함께 쓴다. 선택지·추천·답은 원문에서 읽고, 답이 한 글자가 아니었던 2-1·7-1·12-4는 `CHOSEN`, 결정 단계 기록은 `NOTE`, 나중에 바뀐 결정의 변경 안내는 `CHANGES`(지금 4-3, 10-1)에 적는다 | `결제결정_NN-NN_*.pdf` 76개, `결제도메인_설계패턴_76.pdf` |
| `dlv/` | `data.py` 배송 테이블·컬럼·코드 값 (단일 출처, `CONFIRM`·`POLICY`·`EXTERNAL_SOURCED` 포함, 주문·클레임 ID는 `ref()`)<br>`render.py`(`pay/render.py`에서 가져옴), `col_review.py`(전제·축, T-n, DC-n 결정 77개를 대화 원문 그대로, 새 결정은 `C` 끝에), `split.py <폴더>`(결정 하나당 HTML, `names.txt`에 파일 이름), `col_record.py <출력.html>`(DC-n만 모은 컬럼 검토 결정 기록), `erd_dlv.py` | `배송_테이블이름_검토.pdf`, `배송_컬럼정의서_검토용.pdf`, `docs/pdf/결정/배송결정/배송결정_<번호>_<제목>.pdf` 77개 (공통코드 PDF는 아직 없음) |
| `inv/` | `decision.py` 재고 결정 187개(축 8개 결정 52개 + 후속 2개 + 테이블 T-1~T-11 + 컬럼 IC-1~IC-122, 재확인 질문 `RECONFIRM`)를 대화 원문 그대로 (튜플에 "무엇을 정하나"와 "설명·예시"가 따로 있음, 변경 안내 `CHANGED`, 다른 결정으로 정해진 세부 `SETTLED`), `split.py <폴더>`(결정 하나당 HTML, `names.txt`). `add_decision.py <결정.txt> [<변경안내.txt>]`(결정 원문 추가). `data.py` 테이블 7개·컬럼·코드 단일 출처(`CONFIRM`, `POLICY`, 이름 확정 `NAME_CONFIRMED`), `render.py <폴더>`(names.html, columns.html), `col_record.py <출력.html>`(IC-n 기록 → `재고_컬럼검토_결정.pdf`), `erd_inv.py`(`erd/erd.py`가 부름) | `docs/pdf/결정/재고결정/` 105개(`재고결정_<NN-NN>_<제목>.pdf`, `재고결정_T-<NN>_<제목>.pdf`, `재고결정_IC-<NN>_<제목>.pdf`), `docs/pdf/테이블_컬럼/재고/` |
| `dlv_pattern/` | `gen.py` 배송 도메인 설계 패턴 검토본 (5개 축, 세부 81개). 데이터가 스크립트 안에 있고 `ord_decision/style.css`를 함께 쓴다. 세부 개수를 assert로 검사한다 | `배송도메인_설계패턴_81.pdf` |
| `axes/` | `gen.py <pay\|ord\|prd\|mbr> <출력.html>` 결정을 마친 4개 도메인의 설계 패턴을 배송 문서 형식(큰 틀 축, 패턴 비교, 고른 안, 세부 표, 외부 정리본에서 바로잡은 점)으로 다시 묶은 문서. 축 구성은 사용자가 받은 외부 정리본(`*_N개축.pdf`)을 따른다. 고른 안은 `src.py`가 결제 `pay_decision/orig/`, 주문 `ord_decision/d1~d3.py`, 상품 `prd_decision/data1~3.py`에서 읽고, 회원은 `mbr.py`의 `DEC`에 직접 적었다. 도메인 모듈(`pay.py` 등)에 축·세부 배치·바뀐 내용(`CHG`)이 있고, 결정 번호가 빠지거나 겹치면 assert 오류 | `docs/pdf/설계패턴/{결제\|주문\|상품\|회원}도메인_설계패턴_축별_{76\|80\|53\|47}.pdf` |
| `overview/` | `gen.py` 전체 도메인 설계 패턴 개요 (진행 현황, 공통 결정, 도메인을 가로지르는 틀, 도메인별 고른 패턴, 남은 도메인의 넘어온 결정, 2026-11-20 개요와 달라진 점). 숫자는 CLAUDE.md와 맞춘다 | `docs/pdf/설계패턴/전체도메인_설계패턴_개요.pdf` |
| `screen/` | `cart.html`, `order.html`, `admin_order.html`, `admin_payment.html`, `admin_delivery.html` 화면 와이어프레임 (HTML 원본을 직접 고침) | `docs/pdf/화면/장바구니_화면.pdf`, `주문서_화면.pdf`, `관리자_주문_화면.pdf`, `관리자_결제_화면.pdf`, `관리자_배송_화면.pdf` |
| `glossary/` | `gen.py <db\|biz> <출력.html>` 용어집 (항목 데이터가 스크립트 안의 `DB`·`BIZ`에 있음, A4 가로) | `docs/pdf/용어집/DB용어집.pdf`, `업무용어집.pdf` |
| `testdata/` | `gen.py <폴더>` 테스트 데이터 엑셀. `load.py`가 네 도메인 `data.py`(회원은 `cols/order.py` 순서)에서 컬럼을 읽고, 시나리오 값은 `rows.py` | `docs/테스트데이터/테스트데이터_{회원\|상품\|주문\|결제}.xlsx` |
| `util/` | `pdf2txt.swift` PDF 텍스트 추출 (검증용)<br>`pg.swift` 쪽수 확인·쪽 PNG | |

- 실행 순서가 중요하다. `cmm.py`가 만든 `code_ids.json`을 `cols/render.py`가 읽는다.
- 코드 값을 추가하면 가상 CODE_ID가 밀릴 수 있다. 생성 후 `code_ids.json`을 이전 것과 비교한다.

## 단일 출처와 생성기 규칙

### 회원 (`cols/`)
- `cmm/cmm.py`가 공통코드 PDF와 `code_ids.json`(가상 CODE_ID)을 만들고, `cols/render.py`가 그것을 읽는다.
- `col_decision/col_decision.py`를 결정 기록 PDF와 법률검토 L10~L12 생성 스크립트(`docs/pdf/법률검토/_src/`)가 함께 읽는다.
- `cols/data.py` 컬럼 설명 끝의 `[확정 YYYY-MM-DD]`는 정의서에서 ☑ 확정 표시로 렌더링된다 (문구는 출력되지 않음). 그룹을 통째로 확정할 때는 설명에 표시를 달지 않고 `cols/order.py`의 `CONFIRMED_GROUPS`에 (테이블, 그룹명)을 넣는다 (2026-11-23 사용자 지시).
- 코드 값 행은 컬럼 이름으로 연결된다(CODE_MAP). 같은 `_CD` 컬럼을 가진 모든 테이블에 값 행이 나온다.
- `cols/related.py`의 코드 값별 관련 정보는 `{TABLE.COLUMN}` 자리표시자로 쓴다. 없는 컬럼이면 생성 때 오류가 난다.
- 컬럼이 아닌 안내 줄(참고 행)은 `cols/order.py`의 `REF_BEFORE`에 넣으면 지정한 컬럼 바로 앞에 나온다. 번호와 컬럼 수에는 들어가지 않는다. 지금은 쓰는 곳이 없다.
- 테이블 그룹·컬럼 그룹 순서(규칙 8)는 `cols/order.py`에서 정한다. 테이블 수는 `len(T)`로 계산되므로 숫자를 직접 쓰지 않는다.
- 코드 값을 중간에 추가하면 뒤 값의 CODE_ID가 밀린다. 새 값은 `cmm.py`의 `LATE` 목록(뒤에 붙일 그룹은 `LATE_GROUPS*`, 마지막은 `LATE_LAST`)에 넣어 기존 ID를 지킨다.
- 결정 하나를 바꾸면: `data.py`·`col_decision.py`(필요하면 `policy/content.py`, `chg.py`, `cmm.py`)를 고치고 → `build.sh --install` → 변경 안내 쪽 다시 붙이기(아래 "회원결정 변경 안내 쪽") → `erd.py` → (법률 결정과 같은 C-n이면) 법률검토 빌드.

### 상품·주문·결제·배송 (`prd/`, `ord/`, `pay/`, `dlv/`)
- `data.py` 하나가 단일 출처다: 테이블·컬럼(그룹 순서 = 정의서 순서)·코드 값, `TABLE_GROUPS`, `CONFIRM`(확인 필요 사항), 확정 표시 `CONFIRMED_GROUPS`(테이블, 그룹)·`CONFIRMED_TABLES`. `order.py`는 없다.
  - `CONFIRMED_TABLES`는 컬럼·코드 값·인덱스·제약·테이블 이름 행까지 ☑, `CONFIRMED_GROUPS`는 그 그룹의 컬럼과 코드 값 행만 ☑.
- `col_review.py` 튜플은 (번호, 제목, 대상, 경위, 선택지[(기호, 방식, 장점, 단점)], 추천, 이유, 선택, 답변, 반영, 바뀐 결정)이다 (배송은 마지막 항목 없음). 새 결정은 목록 끝에 붙인다 (주문은 `CSS =` 앞).
- 상품만: `data.py`에 `POLICY_GROUPS`(정책값 코드), `GROUP_NAME`(회원 코드 그룹 이름 충돌 회피)이 더 있다. `prd/cmm.py`는 회원 코드 그룹 이름과 겹치면 오류를 낸다 (예: 회원 `WITHDRAWAL_REASON` 때문에 `PRICE_WITHDRAWAL_REASON_CD`). 상품 공통코드는 회원 빌드의 `code_ids.json`을 인자로 받으므로 회원 빌드를 먼저 한다.
- 결제·배송:
  - `render.py`·`col_review.py`는 `ord/style.css`를 함께 쓴다. 배송 `render.py`는 `pay/render.py`에서 가져온다.
  - 파티션 제거(ORA-02266)를 막지 않도록 원장·로그·대사 테이블의 주문·결제 ID(배송은 주문·클레임 ID)는 `ref()`(FK 없이 인덱스만)로 둔다. ERD는 이 값 참조를 그리지 않는다.
  - Oracle 가상 컬럼은 다른 가상 컬럼을 참조할 수 없다 (결제 취소 상태는 원래 금액 컬럼으로 계산).
  - 값 행 접기: 이름이 다른 컬럼이 값 목록을 재사용하면 `REUSE`·`REUSE_NO_ROWS`(PYC-51 A), 같은 이름 코드 컬럼이 다른 테이블에 다시 나오면 `SAME_NAME_FOLD`(PYC-86 A, `render.py`가 정의서 순서로 처음 나온 곳을 `FIRST`에 기억). 둘 다 값 행 대신 노란 참조 행(`n-n-↺`)을 둔다. 배송은 다른 도메인 그룹을 재사용하는 컬럼(`REUSE`)에도 적용한다.
  - 외부에서 오는 컬럼은 번호를 굵게 표시한다: 결제 `PG_SOURCED`, 배송 `EXTERNAL_SOURCED`. 배송 공통코드 정책값은 `POLICY`.
- 결정 PDF 생성기(`prd_decision/`, `ord_decision/`, `pay_decision/`)는 컬럼 생성기와 독립이다.
  - 주문·결제는 결정 당시 대화 원문(`orig/*.md`)을 `ord_decision/md.py`로 바꾼다 (`style.css` 공유).
  - 나중에 바뀐 결정은 `ord_decision/gen.py`·`pay_decision/gen.py`의 `CHANGES`에 변경 안내를 적는다 (결정 PDF 맨 위에 나옴).
- 배송은 결정을 대화로 했으므로 `dlv/col_review.py` 하나에 질문 원문을 담고, `split.py`가 결정 하나당 PDF로(DC는 두 자리 번호), `col_record.py`가 DC-n만 모은 컬럼 검토 결정 기록을 만든다. 42개 전체 묶음은 두지 않는다 (2026-11-27 사용자 A 선택).
- 배송 패턴 검토본 `dlv_pattern/gen.py`는 세부 개수를 `assert n == 81`로 검사하므로 항목을 더하면 숫자도 고친다.
- 축별 설계 패턴(`axes/`)은 결정이 바뀌면 도메인 모듈의 `SHORT`·`CHG`를 고친다. 외부 정리본(`*_N개축.pdf`)은 사용자 파일이라 덮어쓰지 않는다.

### 재고 (`inv/`)
- `inv/decision.py` 튜플은 11개 항목이다: (번호, 제목, 대상(축), 무엇을 정하나, 설명·예시, 선택지, 추천, 이유, 선택, 답변, 반영). 배송과 달리 "무엇을 정하나"와 "설명·예시"가 따로 있고, 본문은 간단한 마크다운(문단, `- ` 목록, `1. ` 목록, `**굵게**`)으로 렌더링한다. 문자열은 Python 3.9 긴 줄 오류를 피하려고 120자 조각으로 나눠 적었으니 손으로 더할 때도 나눈다. 새 결정은 `C` 끝에 붙인다.
- 재고 ERD(`inv/erd_inv.py`, drawio 7쪽): 확보 처리 이력은 확보 아래, 스냅샷·월 마감은 한 줄 아래(Y0 기준 760)에 있고, 입고 예정 → 현재고 선은 y=1080으로 돌아간다. 사은품·운영자재 6개와 WMS 품목 마스터 2개는 오른쪽 끝(x 2200, 2700)에 있다. 보류 건은 현재고 왼쪽 위, 안전 재고 변경 이력은 왼쪽 아래(x 100)이고 현재고의 entryX=0.2로 들어간다(가운데 세로 점선과 겹치지 않게). 재고 대사 실행은 원장 위(x 1000, 위 안내문과 겹치지 않게 Y0 + 20)이고, 재고 예외의 처음·마지막 실행 FK 두 개를 컬럼 키 `ROUTE`로 따로 그린다. 같은 쌍의 FK 두 개(확보 처리 이력 → 입고 예정)는 컬럼 키 `ROUTE`로 따로 그린다.
- 재고 결정 날짜는 `inv/decision.py`의 `day()`가 번호로 정한다 (IC-30부터 2026-11-28, 나머지 2026-11-27). 다른 날 결정을 더하면 `day()`를 고친다.
- 차수 칸: `data.py`의 `PHASE`(테이블, 없으면 2차), `PHASE_COL`(1차 테이블 안의 2차 컬럼), `PHASE_ORDER`(1차 검토 순서), `PHASE_Q`(다시 물을 것의 차수). 인덱스·제약 행은 2차 컬럼만 가리키면 2차, 1차 컬럼과 섞인 CHECK는 `1차*`(2차 컬럼을 더할 때 다시 만듦)로 `render.py`가 정한다.
- `add_decision.py <결정.txt> [<변경안내.txt>]`가 결정 원문을 `decision.py`의 `C` 끝에 더하고 `CHANGED`를 고친다. 입력 형식은 스크립트 머리 주석에 있다.

### 차수 결정 (`scope/`)
- `build.py <폴더>`가 `decision.txt`(1차 범위 질문 원문, `add_decision.py`와 같은 형식)를 결정 하나당 HTML로 만든다 → Chrome PDF → `docs/pdf/결정/차수결정/`. 모양은 재고 결정 PDF와 같다.

### 정책명세 (`policy/`)
- 상품·주문·결제·배송·재고는 `policy/render_domain.py <모듈> <출력.html>`이 렌더링한다. 모듈은 조문(`P`), 다른 도메인 넘김 사항(`HANDOFF`), 미결 목록(`OPEN`)을 담는다. 조문 본문에 조 번호를 직접 쓰지 않는다 (조를 더하면 번호가 밀림).

### 화면 (`screen/`)
- `screen/*.html`을 직접 고쳐 그대로 PDF로 출력한다 (A4 가로). 쪽마다 왼쪽에 와이어프레임(동그라미 번호), 오른쪽에 "화면 요소별 저장·조회 위치" 표(No, 화면 요소, 컬럼, 근거 결정)와 짧은 주석을 둔다. 스타일은 `admin_order.html`을 복사해 쓴다 (2026-11-26 사용자 지시).

## 상품·주문·결제·배송 도메인

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
# 배송
python3 tools/pdfgen/dlv/render.py $OUT/dlv; python3 tools/pdfgen/dlv/split.py $OUT/dlv_dec      # 결정별 HTML, names.txt
python3 tools/pdfgen/dlv/col_record.py $OUT/dlv/review.html   # DC-n 컬럼 검토 결정 기록
python3 tools/pdfgen/policy/render_domain.py dlv_content $OUT/dlv_policy.html
# 재고
python3 tools/pdfgen/inv/render.py $OUT/inv      # names.html, columns.html (폴더를 먼저 만든다)
python3 tools/pdfgen/inv/split.py $OUT/inv_dec      # 결정별 HTML, names.txt → docs/pdf/결정/재고결정/
python3 tools/pdfgen/inv/col_record.py $OUT/inv/review.html   # IC-n 컬럼 검토 결정 기록
python3 tools/pdfgen/policy/render_domain.py inv_content $OUT/inv_policy.html
# 화면: tools/pdfgen/screen/*.html을 그대로 PDF로 출력 (A4 가로)
```

- PDF 복사 위치 (names → `*_테이블이름_검토`, columns → `*_컬럼정의서_검토용`, review → `*_컬럼검토_결정`):
  - 상품: `docs/pdf/테이블_컬럼/상품/`, 공통코드(cmm) → `docs/pdf/테이블_컬럼/공통/공통코드_CMM_CODE_상품도메인.pdf`, 결정·설계 패턴 → `docs/pdf/결정/상품결정/`, `docs/pdf/설계패턴/`.
  - 주문: `docs/pdf/테이블_컬럼/주문/`, 정책명세 → `docs/pdf/정책명세/주문도메인_정책명세.pdf`, 결정 → `docs/pdf/결정/주문결정/`, 설계 패턴 → `docs/pdf/설계패턴/주문도메인_설계패턴_80.pdf`.
  - 결제: `docs/pdf/테이블_컬럼/결제/`, 정책명세 → `docs/pdf/정책명세/결제도메인_정책명세.pdf`, 결정 → `docs/pdf/결정/결제결정/`, 설계 패턴 → `docs/pdf/설계패턴/결제도메인_설계패턴_76.pdf`.
  - 재고: `docs/pdf/테이블_컬럼/재고/` (names, columns, review → `재고_컬럼검토_결정`), 결정 → `docs/pdf/결정/재고결정/` (결정 하나당 PDF), 정책명세 → `docs/pdf/정책명세/재고도메인_정책명세.pdf`.
  - 배송: `docs/pdf/테이블_컬럼/배송/` (names, columns, review → `배송_컬럼검토_결정`), 결정 → `docs/pdf/결정/배송결정/` (결정 하나당 PDF), 정책명세 → `docs/pdf/정책명세/배송도메인_정책명세.pdf`, 설계 패턴 → `docs/pdf/설계패턴/배송도메인_설계패턴_81.pdf` (`python3 tools/pdfgen/dlv_pattern/gen.py <출력.html>` 뒤 Chrome으로 PDF).
- 결정 기록 범위 표기: 상품 "PC-1~PC-n"은 `prd/col_review.py`, `prd/render.py`, `prd/cmm.py`, 주문 "OC-16~OC-n"은 `ord/col_review.py`, `ord/render.py`, `policy/ord_content.py` 세 곳에 있어 함께 바꾼다. 결제 "PYC-1~PYC-n"은 `pay/render.py`가, 배송 "DC-1~DC-n"은 `dlv/render.py`가 `col_review.py`의 `C`에서 계산한다.
- Python 3.9는 한글이 든 약 1000바이트 넘는 소스 줄에서 "Non-UTF-8 code" 오류를 낸다. 긴 문자열은 나눠 쓴다 (`awk '{if (length($0)>950) print NR}'`로 확인).

## 회원결정 변경 안내 쪽

`docs/pdf/결정/회원결정/`의 3·8·10·12·13·17·20·21·22·25·26·27·28·30·31·32·35·39·43·47번에는 변경 안내 쪽이 이미 붙어 있다 (3·8·10·12·13·20·21·22·25·26·27·30·32·35·43은 컬럼 검토, 나머지는 법률 검토이고 28번에는 컬럼 검토 보완 행도 있다). 다시 만들 때는 원본(커밋 `77b85b7`의 PDF)에 붙인다. 선행결정 3·5·14번(`chgS03.pdf` 컬럼 검토 C-70·C-76, `chgS05.pdf` C-25·C-39·C-49·C-70·C-72, `chgS14.pdf` C-85)의 원본은 커밋 `2cb6480`의 `docs/pdf/선행결정/`의 해당 PDF다. 원본 커밋 당시 경로는 `docs/pdf/회원결정/`, `docs/pdf/선행결정/`이고, 2026-11-25에 `docs/pdf/결정/` 아래로 옮겼다.

`build.sh --install`은 변경 안내 쪽을 붙이지 않는다. 회원 빌드 뒤 매번 아래를 실행한다 (`$OUT`은 빌드 출력 폴더, `chg*.pdf`가 있어야 함):

```bash
M=tools/pdfgen/decision_change/merge.swift
for n in 03 08 10 12 13 17 20 21 22 25 26 27 28 30 31 32 35 39 43 47; do
  f=$(git -c core.quotepath=off ls-tree --name-only 77b85b7 "docs/pdf/회원결정/" | grep "회원결정_${n}_")
  git show 77b85b7:"$f" > $OUT/orig.pdf
  swift $M $OUT/chg$n.pdf $OUT/orig.pdf $OUT/new.pdf >/dev/null && cp $OUT/new.pdf "docs/pdf/결정/${f#docs/pdf/}" || echo FAIL $n
done
for n in 03_네이밍규칙 05_개인정보암호화해시 14_비회원주문; do
  f="docs/pdf/선행결정/선행결정_$n.pdf"; git show 2cb6480:"$f" > $OUT/orig.pdf
  swift $M $OUT/chgS${n:0:2}.pdf $OUT/orig.pdf $OUT/new.pdf >/dev/null && cp $OUT/new.pdf "docs/pdf/결정/${f#docs/pdf/}" || echo FAIL $n
done
```

- 변경 안내 쪽을 새 결정 번호에 추가하면 `chg.py`, `build.sh`, 이 문서, 이 반복문의 번호 목록을 함께 고친다.

## 검증

생성한 PDF의 텍스트를 이전 PDF와 비교한다.

```bash
swift tools/pdfgen/util/pdf2txt.swift 새.pdf 새.txt
swift tools/pdfgen/util/pdf2txt.swift 이전.pdf 이전.txt
```

## 저장소에 없는 생성 스크립트

회원결정 30·31번은 결정 당시 장단점 없이 제시해서 장단점을 보충 설명으로 추가했다. 선행결정, 회원결정 1~47번 본문, 회원 설계패턴, 후보테이블의 생성 스크립트는 없다 (상품·주문·결제 설계패턴은 `prd_decision/`, `ord_decision/`, `pay_decision/`, 배송은 `dlv_pattern/`에 있다). 지시규칙은 2026-11-22에 PDF 내용을 바탕으로 `rules/`에 새로 만들었다. 앞의 문서들은 세션 임시 폴더에서 만들었고, 그 폴더가 지워져서 최종본을 확인할 수 없다. 스크립트가 없는 문서를 고칠 때는 HTML을 세션 스크래치패드에 작성해 Chrome으로 PDF를 출력하고, 쪽수(`pg.swift`)와 쪽 이미지로 한글이 제대로 나오는지 본다.

## 법률검토 (로컬 전용, 커밋하지 않음)

`bash docs/pdf/법률검토/_src/build.sh <작업폴더>`가 도메인별 PDF 5개(`회원도메인_법률검토.pdf` L1~L12, `상품도메인_법률검토.pdf` L13~L18, `주문도메인_법률검토.pdf` 1~13절 + 세법·소비자분쟁해결기준 추가분, `결제도메인_법률검토.pdf`, `배송도메인_법률검토.pdf`)를 만든다. 원문 법령 48개는 `docs/pdf/법률/`에 있다 (역시 로컬 전용).

- 결제·배송은 따로 낸 검토 문서가 없어서 2026-11-27에 결정 원문의 "법에서 오는 조건"(결제는 여신전문금융업법 검토 기록 `pay_decision/orig/history_3.md` 포함)과 정의서·정책명세의 근거 조문을 모아 정리했다. 기록에 없는 판단은 더하지 않았다.
- 정책명세와 회원결정 17·28·31·39·47번 변경 안내 쪽이 이 경로를 참조한다.

- 회원 = L1~L9 원본 13쪽(`법률검토_L1-L9_원본.pdf`, 스크립트 없음) + L10 + L11 + L12. L10~L12 스크립트는 결정 내용을 `col_decision/col_decision.py`에서 읽는다.
- 상품 = L13~L18(`l13_gen.py`), 주문 = 원본 + 추가분(`ord_add_gen.py`), 결제 = `pay_gen.py`, 배송 = `dlv_gen.py` (렌더러 `law_doc.py`).
- 새 법률 검토는 해당 도메인 파일에 더한다 (회원이면 `build.sh`의 합치는 순서에 추가, 결제·배송이면 `pay_gen.py`·`dlv_gen.py`의 `S`에 추가).
- 회원 컬럼 검토 결정(L10~L12와 같은 C-n)이나 결제·배송의 법령 근거를 고치면 함께 다시 돌린다.

## ERD (mmd, drawio)

컬럼이 바뀌면 다시 만든다. `build.sh`에는 들어 있지 않다.

```bash
python3 tools/pdfgen/erd/erd.py
```

- mmd: 회원 컬럼 포함판 `회원_MBR_ERD.mmd`(업무 컬럼만, 공통 컬럼 생략)과 회원·상품·주문·결제·배송 관계 요약판(테이블과 관계만). 상품·주문·결제·배송 배치는 `prd/erd_prd.py`, `ord/erd_ord.py`, `pay/erd_pay.py`, `dlv/erd_dlv.py`의 `POS`에서 직접 정한다 (테이블을 추가하면 넣어야 함). 결제·배송은 결정으로 FK 없이 둔 값 참조(`ref()` 컬럼)를 그리지 않는다.
- 생성 날짜가 모든 파일에 찍혀, 한 도메인만 고쳐도 다른 도메인 파일의 날짜 줄이 바뀐다.
- drawio 1개 파일 (규칙 6: 전체 ERD 1개 파일, 도메인별 페이지): 페이지 "회원 (MBR) 관계 요약"(배치는 `summary_positions()`에서 직접 정함), "회원 (MBR)"(컬럼 포함, 그룹별 열 배치), "상품 (PRD) 관계 요약", "주문 (ORD) 관계 요약", "결제 (PAY) 관계 요약", "배송 (DLV) 관계 요약".
- 다른 도메인 FK 대상은 회색 점선 상자의 후보 이름으로만 그린다 (`EXT_NOTE`). 다른 도메인을 설계하면 페이지를 추가한다.
- 배송 `ROUTE`의 좌표는 `Y0`를 더한 절대 좌표로 적는다. FK가 아직 없는 다른 도메인 참조는 `REF`에 적는다. `POS`에 없는 테이블은 assert 오류다.
- 검증: mmd는 mermaid-cli로 렌더링해 문법을 확인한다 (전역 설치가 없어 스크래치패드에 `npm i @mermaid-js/mermaid-cli`로 설치하고 puppeteer 설정의 `executablePath`를 Chrome으로 지정). drawio는 데스크톱 앱 CLI로 PNG를 뽑아 본다 (페이지 번호는 1부터).
  ```bash
  "/Applications/draw.io.app/Contents/MacOS/draw.io" --export --format png --page-index 1 --scale 0.6 --output <출력.png> docs/drawio/전체_ERD.drawio
  ```

## 테스트 데이터

```bash
python3 tools/pdfgen/testdata/gen.py docs/테스트데이터
```

- 컬럼을 고치면 다시 돌린다. 정의서에 없는 컬럼이나 값 목록에 없는 코드를 넣으면 경고가 나온다.
- 적지 않은 NOT NULL 칸은 DDL 기본값으로 채우고, 기본값도 없으면 규칙으로 채워 회색 기울임으로 표시한다.
- openpyxl이 없어 xlsx를 zipfile로 직접 쓴다. 엑셀 잠금 파일(`~$*.xlsx`)은 커밋하지 않는다.
