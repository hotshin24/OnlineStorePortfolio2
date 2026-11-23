# PDF 생성 스크립트

회원 도메인 문서 PDF를 만드는 스크립트다. HTML을 만든 뒤 Chrome headless로 A4 PDF를 출력한다 (폰트 Apple SD Gothic Neo).

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
| `policy/` | `content.py` 조문 내용<br>`render.py` 렌더러 | `회원도메인_정책명세.pdf` |
| `decision_change/` | `chg.py` 변경 안내 쪽<br>`merge.swift` PDF 앞에 쪽 붙이기 | 회원결정 3·8·10·12·13·17·20·21·22·25·26·27·28·30·31·32·35·39·43·47번, 선행결정 3·5·14번의 첫 쪽 |
| `util/` | `pdf2txt.swift` PDF 텍스트 추출 (검증용) | |

- 실행 순서가 중요하다. `cmm.py`가 만든 `code_ids.json`을 `cols/render.py`가 읽는다.
- 코드 값을 추가하면 가상 CODE_ID가 밀릴 수 있다. 생성 후 `code_ids.json`을 이전 것과 비교한다.

## 회원결정 변경 안내 쪽

`docs/pdf/회원결정/`의 3·8·10·12·13·17·20·21·22·25·26·27·28·30·31·32·35·39·43·47번에는 변경 안내 쪽이 이미 붙어 있다 (3·8·10·12·13·20·21·22·25·26·27·30·32·35·43은 컬럼 검토, 나머지는 법률 검토이고 28번에는 컬럼 검토 보완 행도 있다). 다시 만들 때는 원본(커밋 `77b85b7`의 PDF)에 붙인다. 선행결정 3·5·14번(`chgS03.pdf` 컬럼 검토 C-70·C-76, `chgS05.pdf` C-25·C-39·C-49·C-70·C-72, `chgS14.pdf` C-85)의 원본은 커밋 `2cb6480`의 `docs/pdf/선행결정/`의 해당 PDF다.

```bash
git show 77b85b7:"docs/pdf/회원결정/회원결정_28_개인정보보유기간과파기.pdf" > /tmp/orig28.pdf
swift tools/pdfgen/decision_change/merge.swift /tmp/pdfout/chg28.pdf /tmp/orig28.pdf "docs/pdf/회원결정/회원결정_28_개인정보보유기간과파기.pdf"
```

## 검증

생성한 PDF의 텍스트를 이전 PDF와 비교한다.

```bash
swift tools/pdfgen/util/pdf2txt.swift 새.pdf 새.txt
swift tools/pdfgen/util/pdf2txt.swift 이전.pdf 이전.txt
```

## 저장소에 없는 생성 스크립트

선행결정, 회원결정 1~47번 본문, 설계패턴, 후보테이블, 용어집, 법률검토 PDF의 생성 스크립트는 여기 없다. 지시규칙은 2026-11-22에 PDF 내용을 바탕으로 `rules/`에 새로 만들었다. 앞의 문서들은 세션 임시 폴더에서 만들었고, 그 폴더가 지워져서 최종본을 확인할 수 없다. 법률검토 PDF는 저장소에 올리지 않는 문서다.
