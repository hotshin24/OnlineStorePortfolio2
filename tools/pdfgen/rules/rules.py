# DB 설계 지시 규칙 1~8 예시판 (docs/pdf/지시규칙/DB설계_지시규칙_1-8.pdf)
# 사용법: python3 rules.py <출력.html>
# 테이블 정렬 예시는 cols/order.py의 TABLE_GROUPS에서 읽는다.
import sys, os, html, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cols'))
from order import TABLE_GROUPS, COL_GROUPS

CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: 'Apple SD Gothic Neo', sans-serif; font-size: 9.6pt; color:#222; line-height:1.55; }
h1 { font-size: 18pt; margin:0 0 4px; border-bottom: 3px solid #1f4e79; padding-bottom:6px; color:#1f4e79; }
.meta { color:#666; font-size:8.8pt; margin-bottom:14px; }
h2 { font-size: 13.5pt; margin:20px 0 8px; color:#1f4e79; page-break-after: avoid; }
h3 { font-size: 11pt; margin:16px 0 6px; page-break-after: avoid; }
h3.new { color:#b03a00; }
h4 { font-size: 9.8pt; margin:10px 0 4px; page-break-after: avoid; }
p { margin:4px 0; }
table { border-collapse: collapse; width:100%; margin:4px 0 8px; }
tr { page-break-inside: avoid; }
th, td { border:1px solid #bbb; padding:3px 6px; vertical-align:top; text-align:left; }
th { background:#eef2f7; font-weight:600; }
td.n { white-space:nowrap; }
ul, ol { margin:3px 0 6px 0; padding-left:20px; } li { margin:1px 0; }
.box { border:1px solid #c9d6e6; background:#f6f9fc; padding:6px 12px; margin:8px 0; }
.box b.t { display:block; margin-bottom:2px; }
.new { color:#b03a00; font-weight:600; }
code { font-family: Menlo, monospace; font-size:8.8pt; background:#f1f1f1; padding:0 2px; }
pre { font-family: Menlo, monospace; font-size:8.6pt; background:#f4f4f4; padding:6px 8px; white-space:pre-wrap; margin:4px 0 8px; }
.ln small { color:#555; }
tr.grp td { background:#e9efe4; font-weight:600; }
tr.val td { background:#fbfaf3; }
.rel { border:1px solid #d9cfa6; background:#fffdf3; padding:2px 6px; margin-top:3px; font-size:8.6pt; }
"""

def il(s):
    s = html.escape(s); p = s.split('`')
    s = ''.join(f'<code>{x}</code>' if i % 2 else x for i, x in enumerate(p))
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
def ul(items): return '<ul>' + ''.join(f'<li>{il(x)}</li>' for x in items) + '</ul>'
def table(head, rows, raw=False, nw=0):
    # nw: 줄바꿈하지 않을 앞쪽 열 개수
    st = lambda i: ' style="white-space:nowrap"' if i < nw else ''
    h = '<table><tr>' + ''.join(f'<th{st(i)}>{il(x)}</th>' for i, x in enumerate(head)) + '</tr>'
    for r in rows:
        h += '<tr>' + ''.join(f'<td{st(i)}>{x if raw else il(x)}</td>' for i, x in enumerate(r)) + '</tr>'
    return h + '</table>'
def ln(ko, en): return f'<span class="ln">{il(ko)} <small>({il(en)})</small></span>'

TITLES = ['시스템 컬럼', '테이블명·컬럼명 표기 (물리명, 논리명)', '컬럼 설명', '속성값과 관련 테이블', '테이블 최소화',
          '산출물 형식', '도메인별 진행 방식', '정렬 (관련 그룹, 중요도 순)']

h = '<h1>DB 설계 지시 규칙 (1~8)</h1>'
h += ('<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE / Spring Boot + Flyway (JPA 사용 안 함) · '
      '2026-11-26 기준 (선행 결정, 회원 도메인 컬럼 검토, 법률 검토, 주문 컬럼 검토 OC-57·OC-58, 결제 컬럼 검토 PYC-80·PYC-86 반영)</div>')
h += '<h2>제목</h2><ol>' + ''.join(f'<li>{il(t)}</li>' for t in TITLES) + '</ol>'

h += '<div class="box"><b class="t">2026-11-26 변경 사항</b>' + ul([
  '규칙 4: NULL 허용 컬럼을 비교하는 CHECK는 NULL일 때 막는지 통과시키는지 적는다 (결제 컬럼 검토 PYC-80 A). 모든 도메인에 적용한다. 회원·상품·주문 CHECK는 다시 볼 때 점검한다.',
  '규칙 4: 같은 이름의 코드 컬럼이 다른 테이블에 다시 나오면 두 번째부터 값 행을 펼치지 않고 참조 행(↺)으로 처음 나온 곳을 가리킨다 (결제 컬럼 검토 PYC-86 A). 결제 정의서부터 적용했고, 회원·상품·주문 정의서는 다시 볼 때 바꾼다.']) + '</div>'
h += '<div class="box"><b class="t">2026-11-25 변경 사항</b>' + ul([
  '규칙 8: 8-C를 B(그룹 순서는 업무 흐름)에서 A(그룹도 중요도 순)로 변경하고, 합칠 수 있는 그룹은 합친다 (주문 컬럼 검토 OC-57 A, OC-58 A). 모든 도메인에 적용한다. 회원·상품 도메인은 아직 업무 흐름 순서이고, 다시 볼 때 확인 사항으로 남겼다.']) + '</div>'
h += '<div class="box"><b class="t">2026-11-23 변경 사항</b>' + ul([
  '규칙 5: 예외에 가입 유입 경로 테이블 `MBR_JOIN_ATTRIBUTION` 추가 (회원과 1:1, 컬럼 검토 C-20).']) + '</div>'
h += '<div class="box"><b class="t">2026-11-22 변경 사항</b>' + ul([
  '규칙 2: 정의서의 한글·영문 논리명을 "논리명" 한 칸으로 합쳐 `한글 논리명 (영문 논리명)`으로 표기. 예시 물리명을 네이밍 규칙(풀 영단어)에 맞춤 (`DISCOUNT_ALLOC_AMT` → `DISCOUNT_ALLOCATION_AMT`).',
  '규칙 4: 코드 컬럼에는 코드 문자열(`CODE_CD`)을 저장하고 `CMM_CODE`는 대리 PK `CODE_ID` + UK를 둔다. 정의서에는 값 목록을 코드 컬럼 바로 아래에 두고, 값마다 `CODE_ID`와 "관련 정보"를 적는다.',
  '규칙 6: 정의서 검토 방식 (확정 칸 ☑, 메모 칸) 추가.',
  '규칙 8: 8-C "업무 흐름"을 이용 흐름으로도 해석 (법률 L9 후속). 동의 컬럼을 `MBR_CONSENT`로 옮겨 회원 테이블에는 동의 그룹이 없다 (L9 후속 3). 그룹 표기 방식과 정렬 예시를 현재 회원 도메인 기준으로 갱신.',
  '용어: "묶음" 대신 "그룹"으로 쓴다.']) + '</div>'
h += '<div class="box"><b class="t">2026-11-21 변경 사항</b>' + ul([
  '규칙 1: 시스템 컬럼 4개 → 6개 (행위자 유형 컬럼 분리, 선행 결정 8-1).',
  '규칙 4: JPA 관련 내용 삭제 (JPA 사용 안 함).',
  '규칙 5: 범용 테이블 구성 변경 (선행 결정 6번), 외부 업체 마스터 예외 추가 (13-6).',
  '규칙 7: 선택지는 기호 A/B/C만 붙여 제시 (가/나는 쓰지 않음).',
  '규칙 8 추가: 테이블·컬럼을 관련 있는 것끼리 묶고 중요도 순으로 정렬 (적용 방식 8-A~8-D 사용자 선택).']) + '</div>'

h += '<h2>상세</h2>'
# 1
h += '<h3>1. 시스템 컬럼</h3><p>모든 테이블 끝에 아래 6개 컬럼을 이 순서로 넣습니다. 원장, 상태 이력, 로그 테이블도 예외가 없습니다.</p>'
h += table(['컬럼', '타입', '제약', '값'], [
  ['`CREATED_BY_TYPE_CD`', '`VARCHAR2(20)`', 'NOT NULL + CHECK', '행위자 유형: `MEMBER`, `ADMIN`, `SYSTEM`, `BATCH`, `EXTERNAL`, `GUEST`'],
  ['`CREATED_BY`', '`VARCHAR2(100)`', 'NOT NULL', '행위자 식별자: 회원·관리자 ID, 처리 이름, 배치 작업명, 업체 코드, 비회원 주문번호'],
  ['`CREATED_AT`', '`TIMESTAMP`', '`DEFAULT SYSTIMESTAMP NOT NULL`', '생성 시각'],
  ['`UPDATED_BY_TYPE_CD`', '`VARCHAR2(20)`', 'NULL 허용 + CHECK', '수정 행위자 유형. 수정 전에는 NULL'],
  ['`UPDATED_BY`', '`VARCHAR2(100)`', 'NULL 허용', '수정 행위자 식별자. 수정 전에는 NULL'],
  ['`UPDATED_AT`', '`TIMESTAMP`', 'NULL 허용', '수정 시각. 수정 전에는 NULL']])
h += ul(['논리 삭제 테이블은 `DELETED_BY_TYPE_CD`, `DELETED_BY`, `DELETED_AT`을 추가합니다.',
         '회원 가입은 시퀀스로 `MEMBER_ID`를 먼저 받아 본인 ID로 기록합니다. 관리자 대리 작업은 실제 작업자를 기록합니다.',
         '값은 애플리케이션 공통 코드가 채웁니다. Oracle 스케줄러 배치는 PL/SQL에서 직접 채웁니다.',
         '업무상 다른 행위자를 따로 남겨야 하면 같은 형식(유형 + 식별자)의 업무 컬럼을 둡니다. 예: 제재 조기 해제자 `RELEASED_BY_TYPE_CD`, `RELEASED_BY` (컬럼 검토 C-6).'])
# 2
h += '<h3>2. 테이블명·컬럼명 표기</h3>' + ul([
  '테이블과 컬럼 모두 물리명(영문), 한글 논리명, 영문 논리명을 함께 적습니다.',
  '논리명은 줄여 쓰지 않습니다. 무엇을, 어떤 기준으로, 어떤 단위로 담는지까지 알 수 있게 최대한 자세히 씁니다.',
  '물리명은 공통 결정의 네이밍 규칙(접두어 19개, 분류어 23개, 본체는 풀 영단어, 128바이트 이내)을 따릅니다.',
  '[2026-11-22] 정의서에서는 "논리명" 한 칸에 `한글 논리명 (영문 논리명)`으로 적습니다. 한 줄에 들어가면 한 줄로, 넘치면 영문을 한글 아래 줄에 괄호로 둡니다.'])
h += '<h4>테이블 표기 예시</h4>' + table(['물리명', '논리명'], [
  ['<code>ORD_ORDER_ITEM_DISCOUNT</code>', ln('주문 상품별 할인 배분 내역 (주문 상품 1건 × 할인 출처 1건)', 'Order Item Discount Allocation per Order Item and Discount Source')]], raw=True)
h += '<h4>컬럼 표기 예시</h4>' + table(['물리명', '논리명', '타입', '제약'], [
  ['<code>ORDER_ITEM_DISCOUNT_ID</code>', ln('주문 상품 할인 배분 고유 식별 번호', 'Order Item Discount Allocation Unique Identifier'), '<code>NUMBER(19,0)</code>', 'PK'],
  ['<code>DISCOUNT_ALLOCATION_AMT</code>', ln('이 할인 출처에서 주문 상품에 배분된 할인 금액 (원화)', 'Allocated Discount Amount from This Source in KRW'), '<code>NUMBER(15)</code>', 'NOT NULL'],
  ['<code>CREATED_BY_TYPE_CD</code>', ln('데이터 최초 생성 행위자 유형', 'Record Creator Actor Type Code'), '<code>VARCHAR2(20)</code>', 'NOT NULL, CHECK']], raw=True)
h += '<p><b>DDL 반영 방식</b>: <code>COMMENT</code>에 <code>한글 논리명 | 영문 논리명 | 설명</code> 형식으로 넣습니다 (정의서 표기와 달리 구분자로 나눕니다). Oracle <code>COMMENT</code>는 최대 4,000바이트입니다.</p>'
h += ('<pre>COMMENT ON TABLE ORD_ORDER_ITEM_DISCOUNT IS \'주문 상품별 할인 배분 내역 (주문 상품 1건 × 할인 출처 1건) | Order Item Discount Allocation per Order Item and Discount Source\';\n'
      'COMMENT ON COLUMN ORD_ORDER_ITEM_DISCOUNT.DISCOUNT_ALLOCATION_AMT IS \'이 할인 출처에서 주문 상품에 배분된 할인 금액 (원화) | Allocated Discount Amount from This Source in KRW | 설명...\';</pre>')
# 3
h += '<h3>3. 컬럼 설명</h3><p>컬럼마다 논리명과 별도로 설명을 한글로 씁니다. 논리명은 "무엇인지", 설명은 "어떻게 쓰는지"를 적습니다. 해당하는 항목을 아래 순서로 씁니다.</p>'
h += table(['항목', '내용'], [['업무 의미', '언제, 왜 채워지는 값인지'], ['값 규칙', '형식, 범위, 단위, NULL이 허용되는 경우'],
  ['코드값', '들어갈 수 있는 값과 각 값의 뜻'], ['계산식', '다른 컬럼에서 계산되는 값이면 그 식'],
  ['연관', '어느 테이블의 무엇을 참조하는지, 언제 변경되는지'], ['근거', '결정 번호 (예: 28-6, 선행 결정 8, 법률 L7-3)'], ['예시', '실제 값 예시']])
h += '<h4>설명 예시</h4>' + table(['물리명', '설명'], [
  ['`ITEM_STATUS_CD`', '주문 상품 1건의 현재 처리 상태. 부분 취소·반품·교환을 상품 단위로 관리하려고 주문 헤더 상태와 따로 둔다. 값 목록은 `CMM_CODE`에 두고 CHECK로 제한한다. 상태가 바뀔 때마다 주문 전용 상태 이력에 남긴다. (값은 주문 도메인에서 확정)'],
  ['`DISCOUNT_ALLOCATION_AMT`', '한 할인 출처(쿠폰, 적립금, 등급 할인 등)의 금액을 이 주문 상품에 나눠 배분한 금액. 부분 반품 때 돌려줄 할인·적립금 계산의 기준이 된다. 끝수 처리 규칙은 주문 도메인에서 정한다. 예: 15000'],
  ['`CREATED_BY_TYPE_CD` / `CREATED_BY`', '행을 처음 INSERT한 주체의 유형과 식별자. 예: `MEMBER` / `1048576`, `BATCH` / `PII_RETENTION_EXPIRED_PURGE`, `EXTERNAL` / PG 업체 코드']])
h += ul(['설명이 길어 `COMMENT` 4,000바이트를 넘는 컬럼은 코드값 목록을 공통코드나 정의서 참조로 바꿔 줄입니다.'])
# 4
h += '<h3>4. 속성값과 관련 테이블</h3><p>정해진 값 중 하나를 고르는 컬럼(상태, 유형, 사유, 컬러, 소재 등)은 들어갈 수 있는 값을 정의서에 함께 적고, 그 값을 담는 테이블을 둡니다.</p>'
h += table(['코드', '한글명', '영문명', '설명', '정렬'], [['`MEMBER`', '회원', 'Member', '로그인한 회원 본인', '1'], ['`ADMIN`', '관리자', 'Administrator', '내부 관리자 (대리 작업 포함)', '2']])
h += '<h4>값을 담는 위치</h4>' + table(['구분', '저장 위치', '예시'], [
  ['단순 코드와 작은 마스터', '`CMM_CODE_GROUP` / `CMM_CODE`. 값마다 붙는 추가 정보는 `ATTR1`~`ATTR5`', '주문 상태, 결제 수단, 회원 상태, 행위자 유형, 판매 채널, OS, 업체 종류, 개인정보 보유 사유, 컬러(HEX), 소재, 통화, 은행, 통신사'],
  ['FK로 참조해야 하는 업무 마스터', '전용 마스터 테이블', '회원 등급, 사이즈, 카테고리, 창고, 생산 협력사, 외부 업체(13-6)']])
h += '<h4>코드 저장 방식 [2026-11-22]</h4>' + table(['구분', '방식'], [
  ['업무 테이블의 코드 컬럼', '코드 문자열(`CODE_CD`)을 그대로 저장한다 (예: `MEMBER_STATUS_CD` = `ACTIVE`). `CMM_CODE`로 FK는 걸지 않는다.'],
  ['`CMM_CODE`', '대리 PK `CODE_ID` (`SEQ_CMM_CODE`, 선행 결정 1) + UK (`CODE_GROUP_ID`, `CODE_CD`). `CODE_ID`는 코드 행 관리용이며 업무 테이블은 참조하지 않는다.'],
  ['로직이 걸린 코드', '상태처럼 로직이 걸린 코드는 CHECK 제약으로 값을 제한하고, 운영자가 임의로 값을 추가하지 못하게 한다. 공통코드 값도 Flyway로 함께 배포해 CHECK 값과 어긋나지 않게 한다.']])
h += '<h4>CHECK 문장의 NULL 처리 [2026-11-26]</h4>' + ul([
  'Oracle CHECK는 조건 결과가 UNKNOWN이면 통과합니다. 비교하는 컬럼이 NULL이면 결과가 UNKNOWN입니다.',
  'NULL 허용 컬럼을 `=`, `⇔`, `IN`으로 비교하는 CHECK는 NULL일 때 막는지 통과시키는지 문장에 적습니다. 예: "`MID_PURPOSE_CD` = `BILLING` ⇔ `PAYMENT_METHOD_CD` = `ONE_CLICK`. 수단이 NULL이면 `BILLING`일 수 없다", "사유 = `AMOUNT_MISMATCH` (사유 NULL 포함)".',
  '일괄 `NVL`은 쓰지 않습니다. NULL을 통과시켜야 하는 CHECK의 뜻이 바뀌기 때문입니다 (결제 PYC-80 A).'])
h += '<h4>정의서의 값 목록 표기 [2026-11-22]</h4>'
h += ('<table><tr><th>No</th><th>물리명 / 코드</th><th>논리명</th><th>설명</th><th>메모</th></tr>'
      '<tr><td class="n">1-3</td><td><code>MEMBER_STATUS_CD</code></td><td>' + ln('회원 계정 상태 코드', 'Member Account Status Code') + '</td><td>회원 상태. 값만 CHECK로 제한 (10-1, 10-3).</td><td></td></tr>'
      '<tr class="val"><td class="n">1-3-1</td><td>└ <code>ACTIVE</code></td><td>' + ln('정상', 'Active') + '</td><td>정상 이용 중.</td><td class="n">100321</td></tr>'
      '<tr class="val"><td class="n">1-3-6</td><td>└ <code>SUSPENDED</code></td><td>' + ln('정지', 'Suspended') + '</td><td>유효한 전체 정지 제재 행의 결과.<div class="rel">관련 정보: 정지 사유·기간 <code>MBR_SANCTION</code> (<code>ACCOUNT_SUSPENSION</code> 행), 조기 해제 일시·해제자</div></td><td class="n">100326</td></tr></table>')
h += ul(['값 목록은 문서 끝이 아니라 코드 컬럼 바로 아래에 └ 행(1-3-1, 1-3-2 …)으로 둡니다.',
         '메모 칸에는 공통코드 문서와 같은 `CODE_ID`를 적어 두 문서의 번호가 항상 같게 합니다. ID 값은 설계 단계의 가상 값입니다.',
         '값마다 "그 값일 때 함께 보는 컬럼"을 관련 정보 상자로 적습니다. 마땅한 정보가 없는 값은 상자를 두지 않습니다.',
         '[2026-11-26] 같은 이름의 코드 컬럼이 다른 테이블에 다시 나오면 두 번째부터는 값 행을 펼치지 않고, 컬럼 아래에 노란 참조 행(`n-n-↺`)을 두어 처음 나온 컬럼의 번호를 가리킵니다. 이름이 다른 컬럼이 값 목록을 재사용할 때도 같은 참조 행을 씁니다 (결제 PYC-51 A, PYC-86 A). 결제 정의서부터 적용했고, 회원·상품·주문 정의서는 다시 볼 때 바꿉니다.'])
# 5
h += '<h3>5. 테이블 최소화</h3><p>테이블 수를 늘리기보다 관련 업무를 담은 컬럼을 늘리는 방향으로 설계합니다. 아래 경우에만 테이블을 따로 둡니다.</p>'
h += '<ol><li>한 행에 같은 종류의 데이터가 여러 개 달리는 경우 (1:N)</li><li>다대다 관계인 경우</li><li>거래나 원장이라 행이 계속 쌓이는 경우</li></ol>'
h += ul(['1:1 관계, 횟수가 정해진 정보, 작은 마스터는 컬럼이나 `CMM_CODE`로 흡수합니다.',
         '범용 테이블은 `SYS_STATUS_HIST`(대량 도메인 외 상태 이력), `SYS_PII_ARCHIVE`(개인정보 분리 보관), `SYS_RESERVED_KEY`(재사용 금지 값)만 둡니다. 대상별 FK 컬럼을 두고 정확히 하나만 채우도록 CHECK를 겁니다.',
         '파일·이미지, 감사 로그, 외부 연동 로그는 범용 통합 대신 도메인·용도별 테이블로 둡니다 (선행 결정 6번).',
         '**예외:** 외부 업체 마스터 테이블 (13-6, 사용자 결정). 가입 유입 경로 `MBR_JOIN_ATTRIBUTION` (회원과 1:1, 가입 때 한 번 쓰고 분석에만 읽는 값, 2026-11-23 컬럼 검토 C-20).',
         '회원 × 항목처럼 반복되는 현재 상태는 1:N 테이블로 둡니다. 예: 동의 현재 상태 `MBR_CONSENT` (회원 × 동의 항목 1행, 법률 L9 후속 3).'])
# 6
h += '<h3>6. 산출물 형식</h3>' + table(['파일', '내용'], [
  ['mmd', '도메인별 Mermaid ERD 소스'], ['drawio', '전체 ERD. 도메인별 페이지로 나누고 직접 편집할 수 있게 만듦'],
  ['pdf', '테이블 정의서 (물리명, 논리명, 타입, 제약, 설명, 속성값)와 ERD 그림']])
h += ul(['문서 3종과 DDL(.sql)은 사용자가 작성을 지시할 때만 만듭니다. 계획 승인이나 규칙 전달은 작성 지시가 아닙니다.',
         '[2026-11-22] 정의서의 모든 행에는 확정 칸과 메모 칸이 있습니다. 사용자가 확정한 행은 확정 칸에 ☑로 표시합니다. 결정 항목이 아니었던 제안은 [제안] 표시를 달고, 확정 전에는 확정으로 취급하지 않습니다.'])
# 7
h += '<h3>7. 도메인별 진행 방식</h3>' + ul([
  '사용자가 도메인을 하나 고르면 그 도메인만 다룹니다. 다른 도메인을 미리 진행하거나 여러 도메인을 묶지 않습니다.',
  '해당 도메인의 설계 패턴을 종류별로 모두 설명합니다 (방식, 장점, 단점, 적합한 상황).',
  '우리 사이트에 맞는 형식을 추천합니다. 추천은 참고용이고, 결정은 사용자가 합니다.',
  '결정이 필요한 부분은 기호 A/B/C가 붙은 선택지로 고르게 합니다. 선택지마다 방식·장점·단점과 추천 이유를 함께 보여 줍니다. 가/나 등 다른 기호는 섞지 않습니다. 패턴 검토 중에는 질문에만 답하고, 결정 단계는 사용자가 넘어가자고 할 때 시작합니다.',
  'DB 쪽 결정만 묻습니다. 선택이 이미 정한 결정이나 규칙과 충돌하면 확정 전에 알립니다.'])
# 8
h += '<h3>8. 정렬 (2026-11-21 추가)</h3>' + ul(['**8-1.** 테이블과 컬럼은 관련 있는 것끼리 묶습니다.', '**8-2.** 중요도가 높은 것부터 낮은 것 순(강 → 약)으로 정렬합니다.'])
h += '<h4>적용 방식 (사용자 선택)</h4>' + table(['번호', '항목', '선택', '내용'], [
  ['8-A', '공통 컬럼 위치', 'A', '공통 컬럼은 규칙 1대로 항상 테이블 끝에 둡니다. 순서는 개인정보 보유 4개 → 시스템 6개 → 논리 삭제 3개. 규칙 8은 업무 컬럼에만 적용합니다.'],
  ['8-B', 'PK 위치', 'A', 'PK(복합 PK 포함)는 항상 첫 컬럼입니다. 규칙 8은 PK 다음부터 적용합니다.'],
  ['8-C', '그룹과 중요도의 관계', 'A', '그룹도 중요도 순으로 놓고, 그룹 안도 중요도 순입니다. 합칠 수 있는 그룹은 합칩니다. [2026-11-25 B에서 변경, 주문 컬럼 검토 OC-57·OC-58] (변경 전 B: 그룹 순서는 업무 흐름을 따르고, 중요도 순은 그룹 안에만 적용)'],
  ['8-D', '테이블 순서와 DDL 순서', 'A', '정의서·ERD는 규칙 8 순서를 따릅니다. DDL(Flyway) 생성 순서는 참조되는 테이블부터(FK 순서) 따로 정합니다.']], nw=3)
h += '<div class="box"><b class="t">8-C 변경 [2026-11-25]</b>' + ul([
  '적용 예 (`ORD_ORDER`, 그룹 18개 → 9개): 식별 → 상태·보류 → 주문자 → 금액·세금계산서 → 배송지 → 선물하기 → 법정 확인·고지 → 주문 당시 회원 스냅샷 → 목록 표시·행 버전.',
  '회원·상품 도메인과 아래 예시는 변경 전(B, 업무 흐름 순) 배치입니다. 각 도메인을 다시 볼 때 새 기준으로 확인합니다.']) + '</div>'
h += '<div class="box"><b class="t">8-C 해석 보완 [2026-11-22, 변경 전 B 기준]</b>' + ul([
  '"업무 흐름"은 이용 흐름으로도 해석합니다. 가입 뒤에도 바뀌는 그룹은 가입 순서가 아니라 그 그룹으로 제어하는 기능 바로 앞에 둘 수 있습니다 (법률 L9 후속, 동의 그룹 위치).',
  '이후 동의 컬럼 25개를 `MBR_CONSENT`(회원 × 동의 항목 1행)로 옮겨, 회원 테이블에는 동의 그룹이 없습니다 (법률 L9 후속 3).',
  '그룹 구성과 순서는 도메인마다 사용자가 검토해 확정합니다.']) + '</div>'
h += '<h4>테이블 정렬 예시 (회원 도메인, 변경 전 B: 업무 흐름 순 그룹)</h4>'
h += table(['그룹', '테이블 (그룹 안은 중요도 순)'], [[f'{i}. {g}', ', '.join(f'`{t}`' for t in ts)] for i, (g, ts) in enumerate(TABLE_GROUPS, 1)], nw=1)
la = COL_GROUPS['MBR_LOGIN_ACCOUNT']
rows = [[str(i), g + (' (PK 첫 컬럼)' if i == 1 else ''), ', '.join(f'`{c}`' for c in cs)] for i, (g, cs) in enumerate(la, 1)]
rows.append([str(len(la) + 1), '공통 컬럼 (끝 고정)', '시스템 6개 (`CREATED_BY_TYPE_CD` … `UPDATED_AT`)'])
h += '<h4>컬럼 정렬 예시 (<code>MBR_LOGIN_ACCOUNT</code>, 변경 전 B 기준)</h4>' + table(['순서', '그룹', '컬럼 (그룹 안은 중요도 순)'], rows, nw=2)
h += '<h4>정의서의 그룹 표기 [2026-11-22]</h4>' + ul([
  '테이블 그룹: 테이블 이름 문서와 컬럼정의서 모두 그룹 이름을 표 위의 제목으로 둡니다 (예: "가입·계정" 제목 아래 테이블 1~5).',
  '컬럼 그룹: 표 안의 구분 행으로 둡니다. 구분 행은 코드 값 행과 다른 배경색으로 구분합니다.'])

out = sys.argv[1]
open(out, 'w', encoding='utf-8').write(
  f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>DB 설계 지시 규칙 1-8</title><style>{CSS}</style></head><body>{h}</body></html>')
print('ok')
