# 결제 도메인 테이블·컬럼 정의 (제안, 확정 전)
# 근거: 결제 도메인 결정 1-1~12-5 (docs/pdf/결정/결제결정/), 컬럼 검토 PYC-1~PYC-15. 테이블 이름은 모두 후보다.
# 컬럼: (물리명, 한글 논리명, 영문 논리명, 타입, NULL(N=NOT NULL, Y=허용), 기본값, 제약, 설명)
# 테이블의 cols는 [(컬럼 그룹 이름, [컬럼...]), ...] 순서 그대로가 규칙 8 순서다 (8-C A: 그룹도 중요도 순).
ID = 'NUMBER(19,0)'
YN = 'CHAR(1)'
TS = 'TIMESTAMP'
AMT = 'NUMBER(15)'
PG = 'VARCHAR2(30)'

def yn(p, ko, en, d, desc):
    return (p, ko, en, YN, 'N', f"'{d}'", 'CK (Y/N)', desc)

def fk(p, ko, en, target, null='N', extra='', desc=''):
    return (p, ko, en, ID, null, '', f'FK → `{target}`' + (', ' + extra if extra else ''), desc)

def ref(p, ko, en, null='Y', desc=''):
    # FK를 걸지 않는 식별자 (파티션 제거·기록용 값)
    return (p, ko, en, ID, null, '', 'IX (FK 없음)', desc)

def amt(p, ko, en, desc='', null='N', d='0', ck='CK (>= 0)'):
    return (p, ko, en, AMT, null, d, ck, desc)

def cd(p, ko, en, null='N', desc='', n=20, ck='CK (값 목록)'):
    return (p, ko, en, f'VARCHAR2({n})', null, '', ck, desc)

def pgcd(p='PG_CD', ko='PG 업체 코드', en='Payment Gateway Vendor Code', null='N', desc=''):
    return (p, ko, en, PG, null, '', '', (desc + ' ' if desc else '') + '외부 업체 마스터(`SYS`)의 업체 코드. FK를 걸지는 [확인 필요: 컬럼 검토 질문, 2-6].')

T = []
def table(**kw):
    kw.setdefault('idx', []); kw.setdefault('check', []); kw.setdefault('pii', False); kw.setdefault('ldel', False)
    T.append(kw)

KEEP5 = '개인정보: 행별 파기 예정일 = max(이 행의 법정 기한, 주문의 파기 예정일) (8-6 A). 행: 주문 파티션과 함께 제거 (주문 월 + 10년, 11-1 A)'

# =========================================================== 1. 결제
table(t='PAY_PAYMENT', ko='결제 (PG 결제 시도 단위)', en='Payment',
 desc='PG 결제 시도 1건당 1행. PG를 부르기 전에 "준비" 상태로 만들고, 실패·만료도 남긴다. 수단별 상세는 컬럼 그룹으로 한 테이블에 둔다. 적립금·예치금 사용분은 담지 않는다 (주문 할인 배분).',
 basis='1-4 A, 1-5 A, 1-7 C, 2-1 A~2-8 B, 3-1 B~3-8 A, 4-1 A~4-5 A, 5-1 B, 5-4 A, 5-10 A, 6-1 C, 6-2 A, 6-7 A~6-9 A, 8-1 A~8-6 A, 9-1 A~9-5 A, 10-1 A~10-4 B, 11-1 A',
 pk='대리 PK `SEQ_PAY_PAYMENT`', cache=100,
 delete='삭제하지 않음 (거래). 결제 만료 주문을 지울 때와 주문 파티션 제거 때 함께 지운다. 지우기 전 결제번호를 `SYS_RESERVED_KEY`로 옮긴다 (2-8 B)',
 part='`ORD_ORDER` 참조 파티션 (11-1 A)', keep=KEEP5, pii=True,
 cols=[
 ('식별', [
  ('PAYMENT_ID','결제 고유 식별 번호','Payment Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ID','결제 대상 주문 식별 번호','Paid Order Identifier','ORD_ORDER','N','UK1','참조 파티션 키 (11-1 A).'),
  ('PAYMENT_SN','주문별 결제 시도 차수','Payment Attempt Number per Order','NUMBER(3)','N','','UK1, CK (1~999)','한 주문에서 결제 행을 만들 때마다 1, 2, 3…으로 붙는 번호. 재시도와 추가 결제(교환 배송비 등)도 한 번의 시도로 센다. 결제번호 끝 3자리가 이 값이다. 주문당 시도 상한(9-2 A) 검사에 쓴다 (2-8 B). 주문 행을 `FOR UPDATE`로 잠근 뒤 그 주문의 최대 차수 + 1로 채번한다 (잠금 순서 3-6 A·주문 OC-71 A, PYC-21 A).'),
  ('PAYMENT_NO','결제번호 (PG 전송용 업무 키)','Payment Number (Business Key Sent to PG)','VARCHAR2(18)','N','','UK, CK (형식)','주문번호(하이픈 포함 15자) + 결제 시도 차수 3자리 = 18자 (예: `20261124-K3F8QZ001`). PG 주문번호로 보낸다. 재사용 금지 (2-8 B). '
   'CK: `REGEXP_LIKE(PAYMENT_NO, \'^[0-9]{8}-[2-9A-HJKMNP-Z]{6}[0-9]{3}$\')` (주문번호 CK와 같은 형식, PYC-22 A). [확인 필요: 계약 PG 주문번호 허용 문자·길이 (토스는 영문·숫자·`-`·`_`, 6~64자)]'),
  cd('PAYMENT_PURPOSE_CD','결제 용도 코드','Payment Purpose Code',desc='최초 주문 결제 / 추가 결제 (2-2 C, 5-10 A).'),
  ('PAYMENT_REQUEST_KEY_VAL','결제 요청 중복 방지 키','Payment Request Idempotency Key','VARCHAR2(64)','N','','UK','클라이언트가 결제 요청마다 만드는 키. 같은 키로 다시 오면 기존 행을 돌려주고, 같은 키인데 주문 ID나 결제 용도가 다르면 오류를 낸다 (3-4 A, PYC-23 A). 길이는 주문 요청 키와 같다.'),
  ref('MEMBER_ID','결제 회원 식별 번호 (주문에서 복사)','Paying Member Identifier (Copied from Order)',desc='비회원은 NULL. 회원·카드·IP별 실패 횟수 집계에 쓴다 (9-2 A). FK 없음.'),
 ]),
 ('상태·결과', [
  cd('PAYMENT_STATUS_CD','결제 상태 코드','Payment Status Code',desc='상태 전이는 앞으로만 가는 조건부 UPDATE로 바꾼다 (3-1 B, 3-5 C). 예외 전이 2개: 만료 → 승인, 실패 → 승인. PG 조회로 승인이 확인된 뒤늦은 승인에만 허용하고, 이상 승인 여부를 Y로 바꾸며 바로 자동 취소한다. 이전 실패·만료 사유와 일시는 지우지 않는다 (3-8 A, PYC-24 A).'),
  ('PAYMENT_CANCEL_STATUS_CD','결제 취소 상태 코드 (계산)','Payment Cancellation Status Code (Derived)','VARCHAR2(20)','N','','가상 컬럼, CK (값 목록)','`GENERATED ALWAYS AS (CASE WHEN CANCELED_AMT + OUTSIDE_PG_REFUNDED_AMT = 0 THEN \'NONE\' WHEN CANCEL_PENDING_AMT = 0 AND CANCELED_AMT + OUTSIDE_PG_REFUNDED_AMT = APPROVED_AMT THEN \'FULL\' ELSE \'PARTIAL\' END) VIRTUAL` (3-1 B). 가상 컬럼은 다른 가상 컬럼(`CANCELABLE_AMT`)을 참조할 수 없어 원래 컬럼으로 쓴다. 완료된 취소 기준이다. 취소 처리 중 여부는 상태 값에 넣지 않고 `CANCEL_PENDING_AMT` > 0으로 본다 (PYC-25 B).'),
  ('PAYMENT_DISPLAY_STATUS_CD','결제 표시 상태 코드 (계산, 업무 화면용)','Payment Display Status Code (Derived, for Business Screens)','VARCHAR2(20)','N','','가상 컬럼, CK (값 목록)',
   '고객센터·관리자 결제 목록이 한 컬럼으로 보는 업무 상태. 결제 상태, 취소 처리 중 금액, 취소 누계를 합쳐 위에서부터 먼저 맞는 값을 쓴다 (PYC-32 A). '
   '`GENERATED ALWAYS AS (CASE WHEN PAYMENT_STATUS_CD IN (\'READY\', \'AUTHENTICATED\', \'WAITING_DEPOSIT\') THEN \'UNPAID\' WHEN PAYMENT_STATUS_CD = \'UNKNOWN\' THEN \'CHECKING\' '
   'WHEN PAYMENT_STATUS_CD = \'FAILED\' THEN \'FAILED\' WHEN PAYMENT_STATUS_CD = \'EXPIRED\' THEN \'EXPIRED\' WHEN CANCEL_PENDING_AMT > 0 THEN \'CANCEL_PENDING\' '
   'WHEN CANCELED_AMT + OUTSIDE_PG_REFUNDED_AMT = APPROVED_AMT THEN \'CANCELED\' WHEN CANCELED_AMT + OUTSIDE_PG_REFUNDED_AMT > 0 THEN \'PARTIALLY_CANCELED\' ELSE \'PAID\' END) VIRTUAL`. '
   '가상 컬럼은 다른 가상 컬럼(`PAYMENT_CANCEL_STATUS_CD`)을 참조할 수 없어 원래 금액 컬럼으로 다시 계산한다. 취소 처리 중을 부분 취소보다 앞에 두어 지금 처리할 일이 먼저 보이게 한다. 이미 일부 취소된 사실은 취소 상태와 금액에 남는다. 이상 승인 행(3-8 A)은 취소 처리 중을 거쳐 전체 취소로 보인다.'),
  cd('PAYMENT_FAILURE_REASON_CD','결제 실패·만료 사유 코드','Payment Failure or Expiry Reason Code','Y','실패·만료 사유. 상태가 실패·만료이거나 이상 승인이면 NOT NULL, 아니면 NULL (3-1 B, 9-1 A, 9-2 A, 9-4 A, 10-4 B, PYC-26 A, PYC-30 A). '
   '여러 사유가 함께 맞으면 주문 행을 잠근 뒤 원인 철회 → 새 시도로 대체 → 결제 행 자신의 기한(입금 기한, 승인 제한 시간, 추가 결제 기한) → 주문 만료 순으로 먼저 맞는 값을 쓴다 (PYC-39 A). '
   '`CMM_CODE`의 `ATTR1`은 쓰는 상태(`FAILED` / `EXPIRED` / `ALL`, PYC-40 A), `ATTR2`는 그룹(`CUSTOMER_ACTION` 고객 행동, `PG_DECLINE` 결제사 거절, `MERCHANT_RULE` 우리 규칙 차단, `DEADLINE` 기한 경과, `REPLACEMENT` 대체·철회, `ERROR_OTHER` 오류·기타)이고 정렬은 그룹 순이다 (PYC-42 A). '
   '값을 더하면 상태별 사유 CHECK, 우리 판정 사유 CHECK, `ATTR1`·`ATTR2`를 함께 고친다 (PYC-43 A).',30),
  ('PG_PAYMENT_STATUS_VAL','PG 결제 상태 원래 값','PG Raw Payment Status','VARCHAR2(30)','Y','','','PG가 준 결제 상태 그대로 (토스: `READY`, `IN_PROGRESS`, `WAITING_FOR_DEPOSIT`, `DONE`, `CANCELED`, `PARTIAL_CANCELED`, `ABORTED`, `EXPIRED`). '
   '승인 응답, 웹훅 뒤 조회, 결과 불명 조회 때마다 덮어쓴다. 원문은 DB에 두지 않으므로(7-1 C) PG 상태의 유일한 기록이다. 우리 상태와 어긋나면 예외 수동 처리(사유 `STATUS_MISMATCH`)로 올린다 (PYC-16 A).'),
  ('PG_RESULT_CD','PG 실패·오류 코드 (PG 원래 값)','PG Failure or Error Code (Raw)','VARCHAR2(50)','Y','','','실패·오류일 때만 PG가 준 코드 그대로 (토스 `failure.code`). 우리 공통코드가 아니다. 성공 상태는 `PG_PAYMENT_STATUS_VAL`에 둔다 (PYC-16 A).'),
  ('PG_RESULT_MESSAGE_CN','PG 실패·오류 메시지','PG Failure or Error Message','VARCHAR2(1000)','Y','','',''),
  cd('RESULT_CONFIRM_ROUTE_CD','결과 확정 경로 코드','Result Confirmation Route Code','Y','동기 응답 / 결제창 복귀 / 웹훅 뒤 조회 / 대사 뒤 조회 / PG 조회 / 우리 판정 / 수동 (3-2 C, 3-5 C, PYC-28 A, PYC-29 A, PYC-44 A). '
   '승인·실패·만료이면 NOT NULL, 그 밖의 상태이면 NULL (PYC-46 A). 이상 승인으로 다시 확정되면 새 경로로 덮어쓰고, 이전 경로는 `ABNORMAL_PREV_CONFIRM_ROUTE_CD`로 옮긴다 (PYC-47 B). 이 컬럼과 같은 코드 그룹을 쓰므로 값을 더하면 두 컬럼의 값 목록 CK를 함께 고친다 (PYC-50 A).'),
  ('RESULT_CONFIRM_REASON_CN','수동 확정 사유','Manual Confirmation Reason','VARCHAR2(500)','Y','','','확정 경로가 수동일 때 필수 (3-2 C).'),
  yn('ABNORMAL_APPROVAL_YN','이상 승인 여부','Abnormal Approval Flag','N','PG는 승인했지만 우리가 받아들이지 않아 곧바로 자동 취소한 승인 행. 두 경우다: 만료·실패 뒤에 승인이 확인됨(3-8 A), 자동 승인 수단이 요청과 다른 금액으로 승인함(사유 `AMOUNT_MISMATCH`, 3-3 A, PYC-52 A). '
   'Y이면 주문당 승인 1건 UK, 승인 금액 CHECK, 과세 분할 CHECK에서 빠진다.'),
  cd('ABNORMAL_PREV_CONFIRM_ROUTE_CD','이상 승인 전 확정 경로 코드','Result Confirmation Route Code before Abnormal Approval','Y','이상 승인으로 바뀔 때 그전의 `RESULT_CONFIRM_ROUTE_CD`를 옮겨 둔다. 만료·실패 뒤 이상 승인이면 NOT NULL, 금액 불일치 이상 승인(이전 확정이 없음)과 이상 승인이 아닌 행은 NULL (PYC-52 A). '
   'PG 호출 로그는 1년 뒤 지워지므로(11-2 A) 5년 남는 결제 행에 처음 실패·만료를 확정한 경로를 남긴다 (3-2 C 예 4, PYC-47 B).'),
  yn('MANUAL_CHECK_REQUIRED_YN','결제 예외 수동 처리 필요 여부','Payment Exception Manual Handling Required Flag','N','예외 = 자동 흐름으로 끝내지 못했거나 고객 문의로 사람이 봐야 하는 결제(돈, 상태, 외부 등록) (PYC-58 A). 켜는 경로는 사유 코드의 값 목록 (3-7 A, 4-2 A, 4-3 A, 5-7 A). 처리가 끝나도 Y로 남기고, 미처리 여부는 완료 일시가 NULL인지로 본다 (PYC-19 A).'),
  cd('MANUAL_CHECK_REASON_CD','결제 예외 수동 처리 사유 코드','Payment Exception Manual Handling Reason Code','Y','처리 필요가 Y일 때만, 그때 NOT NULL (PYC-18 A). 두 번째로 처리 대상이 되면 덮어쓰고, 이전 처리는 관리자 작업 로그(3-2 C)에 남는다. '
   '정렬은 급한 순서의 그룹 순이고 `CMM_CODE`의 `ATTR2`에 그룹(`MONEY_RISK` 돈 문제, `STATUS_UNCERTAIN` 상태 미확정·불일치, `EXTERNAL_SYNC` 외부 처리 반영, `INQUIRY_OTHER` 문의·기타)을 적는다 (PYC-56 A). 기타가 늘면 새 값으로 올린다 (PYC-43 A와 같은 기준).',30),
  ('MANUAL_CHECK_RESOLVED_AT','결제 예외 수동 처리 완료 일시','Payment Exception Manual Handling Resolved At',TS,'Y','','','PYC-19 A.'),
  fk('MANUAL_CHECK_RESOLVER_ADMIN_USER_ID','결제 예외 수동 처리 관리자 식별 번호','Payment Exception Manual Handling Resolver Administrator Identifier','ADM_USER','Y','','완료 일시와 함께 채운다. 처리 내용은 수동 확정 사유나 관리자 작업 로그에 남긴다 (PYC-19 A).'),
 ]),
 ('결제 수단', [
  cd('PAYMENT_METHOD_CD','결제 수단 코드','Payment Method Code',desc='1-4 A.'),
  cd('PAYMENT_WINDOW_TYPE_CD','결제창 호출 방식 코드','Payment Window Invocation Type Code','N','결제 행을 만들 때 정한다. PG 통합 결제창 / 카드사 바로 호출 / 간편결제 바로 호출 / 빌링(창 없음). 호출 방식별 이탈률·실패 유형 분석에 쓴다 (PYC-66 A).'),
  cd('EASY_PAY_PROVIDER_CD','간편결제사 코드','Easy Pay Provider Code','Y','수단이 간편결제일 때만. 고객이 주문서에서 고른 간편결제사가 있으면 결제 행을 만들 때 채우고, 없으면 승인 응답으로 채운다 (PYC-60 A). '
   '삼성페이·애플페이처럼 카드를 토큰으로 바꾼 결제를 PG가 카드로 돌려주면 수단은 `CARD`로 두고, 간편결제사 코드는 PG가 알려 줄 때만 채운다 (2-5 A, PYC-64 A). PG 코드 대응이 없으면 NULL이고 원래 값만 남는다 (PYC-63 A).'),
  ('PG_EASY_PAY_PROVIDER_RAW_VAL','PG가 준 간편결제사 원래 값','PG Raw Easy Pay Provider Value','VARCHAR2(30)','Y','','','PG가 준 간편결제사 값 그대로 (토스 `easyPay.provider`). 대응이 없으면 예외 수동 처리(사유 `PG_CODE_UNMAPPED`)로 올리고, 대응을 더한 뒤 코드를 채운다. 카드사 원래 값과 같은 방식 (PYC-63 A).'),
  cd('EASY_PAY_INNER_METHOD_CD','간편결제 앱에서 고른 결제 수단 코드','Payment Method Chosen in Easy Pay App Code','Y','간편결제사 서비스(앱·웹) 안에서 고객이 실제로 돈을 낸 수단 (예: 카카오페이에 등록한 카드, 카카오페이머니). 간편결제사가 알려 준다 (PYC-67 A). 승인 응답으로 채우므로 승인 전에는 NULL (2-5 A, PYC-60 A).'),
  amt('EASY_PAY_INNER_CARD_AMT','간편결제 앱에서 카드로 낸 금액','Amount Paid by Card in Easy Pay App',null='Y',d='',desc='간편결제이고 승인이면 NOT NULL. 카드로 낸 금액 + 현금성으로 낸 금액 = 승인 금액 (2-5 A, PYC-61 A). PG가 나눠 주지 않으면 앱에서 고른 수단으로 계산해 채운다 (카드면 승인 금액 전부).'),
  amt('EASY_PAY_INNER_CASH_AMT','간편결제 앱에서 현금성으로 낸 금액 (계좌·충전금·포인트)','Amount Paid by Cash-Like Means in Easy Pay App',null='Y',d='',desc='PG가 준 간편결제 현금성 금액(계좌·충전금·충전식 포인트, 토스 `easyPay.amount`). 적립 포인트 포함 여부는 [확인 필요: 세무·계약 PG] (PYC-65 B). '
   '현금영수증 대상 금액의 근거이고, 몰이 발급하는 계약일 때만 쓴다 (6-2 A).'),
  ref('SAVED_PAYMENT_METHOD_ID','사용한 저장 결제수단 식별 번호 (기록용)','Used Saved Payment Method Identifier (Record Only)',desc='원클릭일 때 `MBR_SAVED_PAYMENT_METHOD`의 ID. 결제수단이 물리 삭제되어도 남는 기록용 값이라 FK를 걸지 않는다 (8-2 B). 빌링키는 복사하지 않는다.'),
 ]),
 ('금액', [
  amt('REQUEST_AMT','결제 요청 금액','Payment Request Amount',ck='CK (> 0)',d='',desc='행을 만들 때 정한 금액. 주문 결제 금액 또는 추가 결제 금액.'),
  amt('AUTHENTICATED_AMT','인증 금액','Authenticated Amount',null='Y',d='',desc='인증 결과로 받은 금액. 승인 전에 요청 금액과 비교한다 (3-3 A).'),
  amt('APPROVED_AMT','승인 금액','Approved Amount',desc='가상계좌는 입금 확인 금액 (4-3 A).'),
  amt('CARD_ISSUER_INSTANT_DISCOUNT_AMT','카드사 부담 즉시 할인 금액','Card Issuer-Funded Instant Discount Amount',desc='PG 승인 응답의 카드사 즉시 할인 (토스 `discount.amount`). 부담 주체별 금액이라 부담 주체 코드는 두지 않는다 (10-1 A, PYC-11 A, PYC-15 A).'),
  amt('EASY_PAY_PROVIDER_INSTANT_DISCOUNT_AMT','간편결제사 부담 즉시 할인 금액','Easy Pay Provider-Funded Instant Discount Amount',desc='PG 승인 응답의 간편결제사 즉시 할인 (토스 `easyPay.discountAmount`). 카드사 할인과 함께 올 수 있다 (PYC-11 A).'),
  amt('PG_INSTANT_DISCOUNT_AMT','PG 부담 즉시 할인 금액','PG-Funded Instant Discount Amount',desc='PG가 비용을 대는 즉시 할인 (예: 계좌이체 즉시 할인) [확인 필요: 계약 PG]. 10-1 A의 부담 주체 PG를 담는다 (PYC-15 A).'),
  amt('CANCELED_AMT','PG 취소 누계','Cumulative PG Canceled Amount',desc='완료된 PG 취소 행 금액의 합 (2-7 A, 5-1 B). 취소 행과 같은 트랜잭션에서 바꾼다.'),
  amt('CANCEL_PENDING_AMT','취소 처리 중 금액','Cancellation Pending Amount',desc='요청했으나 결과가 나지 않은 취소 금액 (5-1 B).'),
  amt('OUTSIDE_PG_REFUNDED_AMT','PG 밖 환불 누계','Cumulative Refunded Amount outside PG',desc='계좌 송금, 예치금 적립, 차지백 인용으로 돌려준 금액 (5-4 A, 9-3 A).'),
  ('CANCELABLE_AMT','취소 가능 잔액 (계산)','Cancelable Remaining Amount (Derived)',AMT,'N','','가상 컬럼, CK (>= 0)','`GENERATED ALWAYS AS (APPROVED_AMT - CANCELED_AMT - CANCEL_PENDING_AMT - OUTSIDE_PG_REFUNDED_AMT) VIRTUAL` (2-7 A, 5-1 B). CK로 과다 환불을 막는다.'),
  ('PARTIAL_CANCELABLE_YN','부분 취소 가능 여부','Partial Cancellation Available Flag',YN,'Y','','CK (Y/N)','PG 승인 응답 값 (PYC-8 A). N이면 부분 환불은 PG에 보내지 않고 바로 PG 밖 환불(계좌 송금·예치금, 5-4 A)로 보낸다. 응답에 이 값이 없는 PG는 NULL이고, 취소를 보내 본 결과로 판단한다.'),
  amt('CASH_RECEIPT_TARGET_AMT','현금영수증 대상 금액','Cash Receipt Target Amount',desc='PG 결제 중 현금성 부분만. 승인할 때 정한다 (6-2 A).'),
  amt('TAXABLE_SUPPLY_AMT','과세 공급가액','Taxable Supply Amount',desc='PG로 보낸 값 그대로 (6-8 A).'),
  amt('VAT_AMT','부가가치세 금액','Value-Added Tax Amount'),
  amt('TAX_FREE_AMT','면세 금액','Tax-Free Amount'),
 ]),
 ('PG·가맹점', [
  pgcd(desc='실제로 쓴 PG. 설정 행을 FK로 가리키지 않고 값을 복사한다 (2-6 A).'),
  ('PG_MID_VAL','PG 상점 아이디 (MID)','PG Merchant Identifier (MID)','VARCHAR2(50)','N','','','결제 시점에 설정에서 복사 (2-6 A). 반드시 이 회사 명의 (여신전문금융업법 19조 5항).'),
  cd('MID_PURPOSE_CD','MID 용도 코드','MID Purpose Code',desc='일반 / 빌링. 원클릭이면 빌링 (2-6 A).'),
  cd('SETTLEMENT_METHOD_CD','정산 방식 코드','Settlement Method Code','Y','카드 결제는 승인 응답의 카드사로 `PAY_CARD_MERCHANT_CONTRACT`에서 복사한다. 카드가 아니면 PG 정산 (1-7 C, PYC-1 B).'),
  ('CARD_MERCHANT_NO','카드사 가맹점번호','Card Issuer Merchant Number','VARCHAR2(20)','Y','','','직가맹일 때만 (1-7 C).'),
  ('PG_TRANSACTION_NO','PG 거래번호','PG Transaction Number','VARCHAR2(200)','Y','','UK (함수 기반)','인증·승인 결과로 받는다. UK: `(CASE WHEN PG_TRANSACTION_NO IS NOT NULL THEN PG_CD END, PG_TRANSACTION_NO)` (2-8 B, 선행 13). 길이는 토스 `paymentKey` 최대 200자에 맞춘다 (PYC-6 A).'),
  ('PG_RECEIPT_URL','PG 매출전표 조회 URL','PG Receipt Inquiry URL','VARCHAR2(500)','Y','','','전표 자체는 저장하지 않는다 (6-7 A).'),
 ]),
 ('단계별 일시', [
  ('AUTHENTICATED_AT','인증 완료 일시','Authenticated At',TS,'Y','','','3-2 C.'),
  ('APPROVAL_REQUESTED_AT','승인 요청 선점 일시','Approval Request Claimed At',TS,'Y','','','승인 요청을 보내기 전 `WHERE APPROVAL_REQUESTED_AT IS NULL` 조건부 UPDATE로 채워 한 번만 보낸다 (3-4 A).'),
  ('APPROVED_AT','승인 일시','Approved At',TS,'Y','','','가상계좌는 입금 확인 일시. 미성년 월 한도는 이 일시의 월로 센다 (9-4 A).'),
  ('FAILED_AT','실패 일시','Failed At',TS,'Y','','',''),
  ('EXPIRED_AT','만료 일시','Expired At',TS,'Y','','',''),
  ('UNKNOWN_OCCURRED_AT','결과 불명 발생 일시','Result Unknown Occurred At',TS,'Y','','','3-7 A.'),
  ('RESULT_CONFIRMED_AT','결과 확정 일시','Result Confirmed At',TS,'Y','','','확정 경로 코드와 함께 채운다 (3-2 C).'),
 ]),
 ('결과 불명 조회', [
  ('INQUIRY_CNT','PG 조회 횟수','PG Inquiry Count','NUMBER(3)','N','0','CK (>= 0)','정책값 횟수를 넘으면 예외 수동 처리 필요 (3-7 A).'),
  ('NEXT_INQUIRY_AT','다음 조회 예정 일시','Next Inquiry Scheduled At',TS,'Y','','',''),
  ('LAST_INQUIRY_AT','마지막 조회 일시','Last Inquiry At',TS,'Y','','',''),
 ]),
 ('카드', [
  cd('CARD_COMPANY_CD','카드 발급사 코드','Card Issuer Code','Y','PG 코드를 `PAY_PG_CODE_MAPPING`으로 바꿔 저장 (2-4 A, PYC-2 B). 카드 그룹에는 간편결제 앱에서 고른 카드도 담는다 (2-5 A, PYC-62 A).'),
  cd('CARD_ACQUIRER_CD','카드 매입사 코드','Card Acquirer Code','Y',''),
  ('PG_CARD_COMPANY_RAW_VAL','PG가 준 카드사 코드 원래 값','PG Raw Card Issuer Code','VARCHAR2(20)','Y','','','대응이 없으면 우리 코드는 NULL, 이 값만 남는다. [확인 필요: 컬럼 검토 질문, PYC-2 후속]'),
  ('MASKED_CARD_NUMBER_VAL','PG가 준 마스킹 카드 번호','PG-Provided Masked Card Number','VARCHAR2(30)','Y','','CK (`*` 포함)','`REGEXP_LIKE(MASKED_CARD_NUMBER_VAL, \'\\*\')` (8-1 A). 원클릭은 저장 결제수단의 값을 복사 (8-2 B). 회원 도메인과 같은 이름.'),
  cd('CARD_TYPE_CD','카드 종류 코드','Card Type Code','Y','신용 / 체크 / 기프트.'),
  ('CARD_APPROVAL_NO','카드 승인번호','Card Approval Number','VARCHAR2(20)','Y','','',''),
  ('PG_CARD_IDENTIFIER_VAL','PG 카드 식별 값','PG Card Identifier Value','VARCHAR2(100)','Y','','IX','같은 카드 판별용 PG 토큰. 평문 + TDE (8-1 A, 8-3 B). 카드별 실패 집계 (9-2 A).'),
  cd('CARD_OWNER_TYPE_CD','카드 소유 유형 코드','Card Owner Type Code','Y','개인 / 법인 / 미확인. PG 승인 응답 값. 법인카드 결제 고객의 증빙 문의에 쓴다 (PYC-14 A).'),
  ('CARD_POINT_USED_YN','카드 포인트 사용 여부','Card Point Used Flag',YN,'Y','','CK (Y/N)','카드사 포인트로 결제했는지. PG 승인 응답 값 (PYC-14 A). 응답에 없는 PG는 NULL.'),
  ('INSTALLMENT_MONTHS_CNT','할부 개월 수','Installment Months Count','NUMBER(2)','Y','','CK (0~36)','일시불 0 (2-4 A, 10-2 A).'),
  cd('INTEREST_FREE_TYPE_CD','무이자 유형 코드','Interest-Free Type Code','Y','10-2 A.'),
  cd('INTEREST_FREE_FUNDER_CD','무이자 부담 주체 코드','Interest-Free Funder Code','Y','가맹점 부담 무이자는 정산 도메인이 수수료를 대사한다 (10-2 A).'),
  ('INTEREST_FREE_INSTALLMENT_CNT','부분 무이자 회차 수','Partial Interest-Free Installment Count','NUMBER(2)','Y','','','부분 무이자일 때만 (10-2 A).'),
 ]),
 ('본인 확인', [
  cd('IDENTITY_VERIFIER_CD','본인 확인 주체 코드','Identity Verifier Code','Y','카드사·PG / 간편결제사 / 우리 몰 (9-5 A, 여신전문금융업법 19조 2항).'),
  cd('IDENTITY_VERIFICATION_METHOD_CD','본인 확인 방식 코드','Identity Verification Method Code','Y','승인된 카드·원클릭은 NOT NULL이고 `NONE`이 아니다 (9-5 A).'),
  ('PG_AUTH_RESULT_VAL','PG 인증 결과 원래 값','PG Raw Authentication Result','VARCHAR2(50)','Y','','',''),
 ]),
 ('가상계좌', [
  cd('VIRTUAL_ACCOUNT_BANK_CD','가상계좌 은행 코드','Virtual Account Bank Code','Y','`CMM_CODE` 은행 그룹(회원 도메인) 재사용.',ck=''),
  ('VIRTUAL_ACCOUNT_NUMBER_VAL','가상계좌 번호','Virtual Account Number','VARCHAR2(30)','Y','','','회사 수납 계좌라 평문 + TDE (8-3 B). 결제 행마다 일회용 (4-1 A).'),
  ('DEPOSIT_DUE_AT','입금 기한 일시','Deposit Due At',TS,'Y','','','지나면 PG 조회로 입금이 없음을 확인한 뒤 만료 (4-2 A).'),
  ('DEPOSITOR_NM','실제 입금자명','Actual Depositor Name','VARCHAR2(150)','Y','','','PG 입금 통보로 받은 실제 입금자 이름. 발급 때 PG에 보낸 고객명은 저장하지 않고 주문의 주문자 이름으로 갈음한다 (PYC-12 B). 개인정보. 평문 + TDE (C-72 기준). 파기 대상 (8-6 A).'),
  ('VIRTUAL_ACCOUNT_WEBHOOK_SECRET_HASH','가상계좌 웹훅 검증 값 해시','Virtual Account Webhook Secret Hash','RAW(32)','Y','','','가상계좌 발급 응답의 검증 값(토스 `secret`)을 HMAC-SHA256으로 해시한 값 (PYC-7 A, 선행 5). 입금 웹훅에 실린 값을 같은 방식으로 해시해 비교하고, 결과를 웹훅 수신함 서명 검증 결과에 적는다. 입금 기한 안에서만 쓰므로 키 버전은 두지 않는다. 검증 값을 주지 않는 PG는 NULL.'),
 ]),
 ('계좌이체·휴대폰', [
  cd('TRANSFER_BANK_CD','계좌이체 은행 코드','Account Transfer Bank Code','Y','`CMM_CODE` 은행 그룹 재사용.',ck=''),
  ('MASKED_TRANSFER_ACCOUNT_NUMBER_VAL','PG가 준 마스킹 출금 계좌번호','PG-Provided Masked Transfer Account Number','VARCHAR2(30)','Y','','','2-4 A.'),
  cd('MOBILE_CARRIER_CD','휴대폰 결제 통신사 코드','Mobile Payment Carrier Code','Y',''),
  ('MOBILE_PHONE_NUMBER_ENC','휴대폰 결제 번호 암호문','Mobile Payment Phone Number Ciphertext','RAW(49)','Y','','','평문 최대 20바이트 + 29 (선행 5, 8-3 B). 파기 대상.'),
  ('MASKED_MOBILE_PHONE_NUMBER_VAL','마스킹 휴대폰 결제 번호','Masked Mobile Payment Phone Number','VARCHAR2(20)','Y','','','파기 대상.'),
 ]),
 ('현금영수증 신청', [
  yn('CASH_RECEIPT_REQUESTED_YN','현금영수증 신청 여부','Cash Receipt Requested Flag','N','주문서에서 받는다 (4-5 A, 6-1 C). N이면 정책값 일수 뒤 무기명 자진 발급 (6-3 C).'),
  cd('CASH_RECEIPT_PURPOSE_CD','현금영수증 발급 용도 코드','Cash Receipt Purpose Code','Y','회원 기본값 그룹 재사용 (회원 44-1 D).',ck=''),
  cd('CASH_RECEIPT_IDENTIFIER_TYPE_CD','현금영수증 식별 번호 유형 코드','Cash Receipt Identifier Type Code','Y','회원 그룹 재사용.',ck=''),
  ('CASH_RECEIPT_IDENTIFIER_NUMBER_ENC','현금영수증 식별 번호 암호문','Cash Receipt Identifier Number Ciphertext','RAW(49)','Y','','','휴대폰·카드·사업자번호. 회원과 같은 길이 (8-3 B). 파기 대상.'),
  ('MASKED_CASH_RECEIPT_IDENTIFIER_NUMBER_VAL','마스킹 현금영수증 식별 번호','Masked Cash Receipt Identifier Number','VARCHAR2(20)','Y','','','파기 대상.'),
  ('CASH_RECEIPT_REQUESTED_AT','현금영수증 신청 일시','Cash Receipt Requested At',TS,'Y','','','주문서 또는 입금 뒤 마이페이지 신청 (4-5 A, 6-1 C).'),
  ('CASH_RECEIPT_DUE_DT','현금영수증 발급 기한 일자','Cash Receipt Issue Due Date','DATE','Y','','IX','신청이 있으면 승인일 + 5일, 없으면 승인일 + 정책값 일수(기본 3일). 승인일 + 5일 이하 (6-1 C, 6-3 C). 미발급 감시 배치가 본다.'),
 ]),
 ('부정 결제 판정', [
  cd('FDS_DECISION_CD','FDS 판정 코드','Fraud Detection Decision Code','Y','차단이면 PG를 부르지 않고 실패, 검토면 승인 뒤 주문 보류 (9-1 A).'),
  ('FDS_SCORE_VAL','FDS 점수','Fraud Detection Score','NUMBER(5,2)','Y','','',''),
  ('FDS_MATCHED_RULE_JSON','걸린 FDS 규칙과 적용 기준값','Matched Fraud Rules with Applied Thresholds','JSON','Y','','','규칙 코드(`FDS_RULE_CD`)와 그때의 기준값 스냅샷 (PYC-4 A).'),
  ('FDS_EVALUATED_AT','FDS 판정 일시','Fraud Detection Evaluated At',TS,'Y','','',''),
  ('PG_FDS_RESULT_VAL','PG FDS 판정 원래 값','PG Raw Fraud Detection Result','VARCHAR2(50)','Y','','',''),
 ]),
 ('결제 혜택', [
  ('PG_PROMOTION_CD','PG 행사 코드 (PG 원래 값)','PG Promotion Code (Raw)','VARCHAR2(50)','Y','','','우리 공통코드가 아니다 (10-1 A).'),
  ('PG_PROMOTION_NM','PG 행사 이름','PG Promotion Name','VARCHAR2(200)','Y','','',''),
  ('MERCHANT_FUNDED_EXTERNAL_PROMOTION_CD','우리 부담 외부 적립 행사 코드','Merchant-Funded External Accrual Promotion Code','VARCHAR2(30)','Y','','','10-3 B. 값 목록 위치는 [확인 필요: 컬럼 검토 질문, 10-4 B 프로모션 마스터와 함께].'),
 ]),
 ('결제대금예치', [
  yn('ESCROW_APPLIED_YN','결제대금예치 적용 여부','Escrow Applied Flag','N','주문 1-9 A, 6-9 A.'),
  cd('ESCROW_DELIVERY_REGISTER_STATUS_CD','결제대금예치 배송 등록 상태 코드','Escrow Delivery Registration Status Code','Y','적용일 때만 (6-9 A).'),
  ('ESCROW_INVOICE_NO','결제대금예치 등록 송장번호','Escrow Registered Invoice Number','VARCHAR2(30)','Y','','','나눠서 출고하면 마지막 출고의 송장 (6-9 A).'),
  ('ESCROW_DELIVERY_REGISTERED_AT','결제대금예치 배송 등록 일시','Escrow Delivery Registered At',TS,'Y','','',''),
  ('ESCROW_REGISTER_RETRY_CNT','결제대금예치 배송 등록 재시도 횟수','Escrow Registration Retry Count','NUMBER(3)','Y','','CK (>= 0)','등록 실패 때 재시도 (6-9 A, 5-9 A와 같은 방식). 적용일 때만. 정책값 횟수를 넘으면 예외 수동 처리(사유 `ESCROW_REGISTRATION_FAILED`)로 올린다 (PYC-53 A).'),
  ('ESCROW_NEXT_RETRY_AT','결제대금예치 다음 등록 재시도 일시','Escrow Next Registration Retry At',TS,'Y','','',''),
  ('ESCROW_KEY_VAL','결제대금예치 거래 키','Escrow Transaction Key','VARCHAR2(200)','Y','','','PG가 준 결제대금예치 거래 키 (토스 `escrowKey`). 배송 등록·구매 확정 API에 PG 거래번호 대신 이 키를 쓰는 PG를 위해 둔다. 쓰지 않는 PG는 NULL (PYC-13 A). 길이는 [확인 필요: 계약 PG 연동 문서].'),
  cd('ESCROW_CONFIRM_STATUS_CD','결제대금예치 구매 확정 상태 코드','Escrow Purchase Confirmation Status Code','Y','적용일 때만 (6-9 A).'),
  ('ESCROW_CONFIRMED_AT','결제대금예치 구매 확정·거절 일시','Escrow Purchase Confirmed or Rejected At',TS,'Y','','',''),
 ]),
 ('추가 결제 원인', [
  cd('ADDITIONAL_PAYMENT_REASON_CD','추가 결제 사유 코드','Additional Payment Reason Code','Y','용도가 추가 결제일 때만 (5-10 A).',30),
  ('CLAIM_ID','추가 결제 원인 클레임 식별 번호','Additional Payment Source Claim Identifier',ID,'Y','','','[확인 필요: 클레임 도메인 테이블이 정해지면 FK]'),
  fk('ORDER_CHANGE_HIST_ID','추가 결제 원인 주문 변경 이력 식별 번호','Additional Payment Source Order Change History Identifier','ORD_ORDER_CHANGE_HIST','Y','','배송지 변경으로 도서산간 차액이 생긴 경우 등 (5-10 A).'),
 ]),
 ('미성년·요청 환경', [
  yn('MINOR_LIMIT_APPLIED_YN','미성년 월 한도 적용 여부','Minor Monthly Limit Applied Flag','N','주문의 미성년 주문 여부를 복사. 월 사용액 합산 대상 (9-4 A).'),
  ('PAYMENT_REQUEST_IP','결제 요청 IP 주소','Payment Request IP Address','VARCHAR2(45)','Y','','IX','평문 + TDE. 생성 일시부터 정책값 개월(기본 6개월)이 지나면 배치가 NULL (8-5 B, 9-3 A).'),
  ('SALES_CHANNEL_CD','결제 판매 채널 코드','Payment Sales Channel Code','VARCHAR2(20)','N','','CK (PC/MOBILE_WEB/APP)','선행 10, 8-5 B.'),
  ('OS_CD','결제 기기 운영체제 코드','Payment Device Operating System Code','VARCHAR2(20)','Y','','','회원 OS 코드 그룹을 함께 쓴다.'),
 ]),
 ],
 idx=['UK `UK_PAY_PAYMENT_ORDER_ID_PAYMENT_SN` (`ORDER_ID`, `PAYMENT_SN`) LOCAL, `UK_PAY_PAYMENT_PAYMENT_NO` GLOBAL, `UK_PAY_PAYMENT_PAYMENT_REQUEST_KEY_VAL` GLOBAL (11-1 A)',
      'UK `UK_PAY_PAYMENT_PG_TRANSACTION_NO` (함수 기반, GLOBAL): `(CASE WHEN PG_TRANSACTION_NO IS NOT NULL THEN PG_CD END, PG_TRANSACTION_NO)` (2-8 B)',
      'UK `UK_PAY_PAYMENT_ORDER_ACTIVE` (함수 기반, LOCAL): `CASE WHEN PAYMENT_PURPOSE_CD = \'ORDER\' AND PAYMENT_STATUS_CD IN (\'APPROVED\', \'UNKNOWN\', \'WAITING_DEPOSIT\') AND ABNORMAL_APPROVAL_YN = \'N\' THEN ORDER_ID END` (2-2 C, 3-7 A, 3-8 A, 4-1 A)',
      'IX `IX_PAY_PAYMENT_NEXT_INQUIRY_AT` (함수 기반: 상태 `UNKNOWN`인 행만, 3-7 A), `IX_PAY_PAYMENT_DEPOSIT_DUE_AT` (함수 기반: 상태 `WAITING_DEPOSIT`인 행만, 4-2 A)',
      'IX `IX_PAY_PAYMENT_MANUAL_CHECK_OPEN` (함수 기반: `CASE WHEN MANUAL_CHECK_REQUIRED_YN = \'Y\' AND MANUAL_CHECK_RESOLVED_AT IS NULL THEN CREATED_AT END`, 미처리 예외 목록, PYC-19 A), `IX_PAY_PAYMENT_MANUAL_CHECK_RESOLVER_ADMIN_USER_ID` (FK)',
      'IX `IX_PAY_PAYMENT_ADDITIONAL_PENDING` (함수 기반: `CASE WHEN PAYMENT_PURPOSE_CD = \'ADDITIONAL\' AND PAYMENT_STATUS_CD IN (\'READY\', \'AUTHENTICATED\') THEN CREATED_AT END`, 추가 결제 만료 배치, PYC-17 B)',
      'IX LOCAL: (`MEMBER_ID`, `CREATED_AT`), (`PAYMENT_REQUEST_IP`, `CREATED_AT`), (`PG_CARD_IDENTIFIER_VAL`, `CREATED_AT`) (9-2 A), (`MEMBER_ID`, `APPROVED_AT`) (9-4 A), (`CREATED_AT`) (대사·감시, 11-1 A). 실패 행만 세는 함수 기반으로 할지는 [확인 필요: 컬럼 검토 질문, 9-2 A]',
      'IX `IX_PAY_PAYMENT_SAVED_PAYMENT_METHOD_ID` (FK 없음, 8-2 B), `IX_PAY_PAYMENT_ORDER_CHANGE_HIST_ID` (FK), `IX_PAY_PAYMENT_PII_RETENTION_END_DT` (파기 배치)'],
 check=['상태 전이는 허용 목록 테이블이 아니라 정책명세의 전이표로 관리하고 UPDATE 조건에 넣는다 (3-5 C)',
        '`PAYMENT_STATUS_CD` = `APPROVED`이면 `APPROVED_AT`, `PG_TRANSACTION_NO` NOT NULL. 여기에 `ABNORMAL_APPROVAL_YN` = N이면 `REQUEST_AMT = APPROVED_AMT + CARD_ISSUER_INSTANT_DISCOUNT_AMT + EASY_PAY_PROVIDER_INSTANT_DISCOUNT_AMT + PG_INSTANT_DISCOUNT_AMT` (10-1 A, PYC-11 A, PYC-15 A, PYC-52 A)',
        '`PAYMENT_STATUS_CD` = `FAILED`이면 `FAILED_AT` NOT NULL',
        '`PAYMENT_FAILURE_REASON_CD` NOT NULL ⇔ 상태가 `FAILED`·`EXPIRED`이거나, 상태가 `APPROVED`이고 `ABNORMAL_APPROVAL_YN` = Y (3-8 A, PYC-24 A, PYC-30 A)',
        '`ABNORMAL_APPROVAL_YN` = Y이면 상태가 `APPROVED` (PYC-30 A)',
        '상태가 `FAILED`이면 `PAYMENT_FAILURE_REASON_CD` IN (`USER_ABORTED`, `PG_DECLINED`, `AUTHENTICATION_FAILED`, `SAVED_CARD_INVALID`, `CARRIER_LIMIT_EXCEEDED`, `AMOUNT_MISMATCH`, `FDS_BLOCKED`, `ATTEMPT_LIMIT_EXCEEDED`, `MINOR_LIMIT_EXCEEDED`, `PAYMENT_METHOD_MISMATCH`, `DUPLICATE_PAYMENT`, `PG_ERROR`, `OTHER`). '
        '상태가 `EXPIRED`이면 IN (`DEPOSIT_DEADLINE_PASSED`, `APPROVAL_TIME_LIMIT_PASSED`, `ADDITIONAL_PAYMENT_TIMEOUT`, `ORDER_EXPIRED`, `REPLACED_BY_NEW_ATTEMPT`, `ADDITIONAL_PAYMENT_CAUSE_WITHDRAWN`, `OTHER`). 이상 승인 행은 이전 사유를 두므로 제한하지 않는다 (PYC-40 A)',
        '상태가 `FAILED`·`EXPIRED`이고 사유가 우리 판정 사유(`AMOUNT_MISMATCH`, `FDS_BLOCKED`, `ATTEMPT_LIMIT_EXCEEDED`, `MINOR_LIMIT_EXCEEDED`, `PAYMENT_METHOD_MISMATCH`, `DUPLICATE_PAYMENT`, `APPROVAL_TIME_LIMIT_PASSED`, `ADDITIONAL_PAYMENT_TIMEOUT`, `REPLACED_BY_NEW_ATTEMPT`, `ADDITIONAL_PAYMENT_CAUSE_WITHDRAWN`)이면 `RESULT_CONFIRM_ROUTE_CD` = `INTERNAL_DECISION`. 반대 방향은 걸지 않는다 (PYC-41 B)',
        '`RESULT_CONFIRM_ROUTE_CD` NOT NULL ⇔ 상태가 `APPROVED`·`FAILED`·`EXPIRED` (PYC-29 A, PYC-46 A)',
        '`RESULT_CONFIRM_ROUTE_CD` = `INTERNAL_DECISION`이면 상태가 `FAILED`·`EXPIRED` (PYC-46 A)',
        '`RESULT_CONFIRM_ROUTE_CD` = `BROWSER_RETURN`이면 상태가 `FAILED`이고 `PAYMENT_FAILURE_REASON_CD` IN (`USER_ABORTED`, `PG_DECLINED`, `AUTHENTICATION_FAILED`, `SAVED_CARD_INVALID`, `CARRIER_LIMIT_EXCEEDED`, `PG_ERROR`, `OTHER`) (PYC-44 A)',
        '`ABNORMAL_PREV_CONFIRM_ROUTE_CD` NOT NULL ⇔ `ABNORMAL_APPROVAL_YN` = Y이고 `PAYMENT_FAILURE_REASON_CD` ≠ `AMOUNT_MISMATCH` (PYC-47 B, PYC-52 A)',
        '`PAYMENT_METHOD_CD` = `ONE_CLICK`이면 `SAVED_PAYMENT_METHOD_ID` NOT NULL, `MID_PURPOSE_CD` = `BILLING`, `IDENTITY_VERIFIER_CD` = `MERCHANT`, `IDENTITY_VERIFICATION_METHOD_CD` = `PAYMENT_PIN` (1-4 A, 8-2 B, 9-5 A)',
        '`PAYMENT_METHOD_CD` = `EASY_PAY`이고 승인이면 (`EASY_PAY_PROVIDER_CD` 또는 `PG_EASY_PAY_PROVIDER_RAW_VAL`), `EASY_PAY_INNER_METHOD_CD` NOT NULL이고 `IDENTITY_VERIFIER_CD` = `EASY_PAY_PROVIDER`. 승인 전에는 간편결제사만 있을 수 있다. 간편결제가 아니면 간편결제 컬럼 모두 NULL (2-5 A, PYC-60 A, PYC-63 A)',
        '`PAYMENT_METHOD_CD` = `EASY_PAY`이고 승인이면 `EASY_PAY_INNER_CARD_AMT`, `EASY_PAY_INNER_CASH_AMT` NOT NULL이고 합 = `APPROVED_AMT`. 앱에서 고른 수단이 `CARD`이면 현금성 0, `MONEY`·`POINT`·`ACCOUNT`이면 카드 0, `MIXED`이면 둘 다 > 0 (2-5 A, PYC-61 A)',
        '승인이고 (`PAYMENT_METHOD_CD` IN (`CARD`, `ONE_CLICK`)이거나 `EASY_PAY_INNER_METHOD_CD` IN (`CARD`, `MIXED`))이면 (`CARD_COMPANY_CD` 또는 `PG_CARD_COMPANY_RAW_VAL`), `MASKED_CARD_NUMBER_VAL`, `CARD_APPROVAL_NO` NOT NULL (2-5 A, PYC-62 A). 승인번호는 [확인 필요: 계약 PG]',
        '`PAYMENT_WINDOW_TYPE_CD` = `BILLING` ⇔ `PAYMENT_METHOD_CD` = `ONE_CLICK`. `DIRECT_CARD`이면 `CARD`, `DIRECT_EASY_PAY`이면 `EASY_PAY` (PYC-66 A)',
        '`PAYMENT_METHOD_CD` IN (`CARD`, `ONE_CLICK`)이고 승인이면 `IDENTITY_VERIFICATION_METHOD_CD` NOT NULL이고 `NONE`이 아님 (9-5 A)',
        '`PAYMENT_METHOD_CD` = `VIRTUAL_ACCOUNT`가 아니면 가상계좌 컬럼 모두 NULL. `MOBILE_PHONE`이 아니면 휴대폰 컬럼 모두 NULL (2-4 A)',
        '`INSTALLMENT_MONTHS_CNT` = 0이면 `INTEREST_FREE_TYPE_CD` = `NONE`. 유형이 `NONE`이 아니면 부담 주체 NOT NULL. `PARTIAL`이면 회차 수 NOT NULL이고 할부 개월보다 작음 (10-2 A)',
        '`PAYMENT_PURPOSE_CD` = `ADDITIONAL`이면 `ADDITIONAL_PAYMENT_REASON_CD` NOT NULL이고 `CLAIM_ID`, `ORDER_CHANGE_HIST_ID` 중 하나 이상 NOT NULL. `ORDER`이면 셋 다 NULL (5-10 A)',
        '`CASH_RECEIPT_REQUESTED_YN` = Y이면 용도·식별 번호 유형·신청 일시 NOT NULL (6-1 C). 승인 뒤 `CASH_RECEIPT_DUE_DT` <= 승인일 + 5일 (6-3 C)',
        '`RESULT_CONFIRM_ROUTE_CD` = `MANUAL`이면 `RESULT_CONFIRM_REASON_CN`, `MANUAL_CHECK_RESOLVED_AT` NOT NULL (3-2 C, PYC-48 A)',
        '`MANUAL_CHECK_REQUIRED_YN` = Y ⇔ `MANUAL_CHECK_REASON_CD` NOT NULL (PYC-18 A)',
        '`MANUAL_CHECK_RESOLVED_AT` NOT NULL ⇔ `MANUAL_CHECK_RESOLVER_ADMIN_USER_ID` NOT NULL. 완료 일시가 있으면 `MANUAL_CHECK_REQUIRED_YN` = Y (PYC-19 A)',
        '`ESCROW_APPLIED_YN` = Y이면 수단은 `VIRTUAL_ACCOUNT` 또는 `ACCOUNT_TRANSFER`이고 두 상태 코드 NOT NULL. N이면 결제대금예치 컬럼 모두 NULL (6-9 A)',
        '`TAXABLE_SUPPLY_AMT + VAT_AMT + TAX_FREE_AMT = APPROVED_AMT` (승인 뒤, 이상 승인 행 제외, 6-8 A, PYC-52 A)'])

table(t='PAY_REFUND_REQUEST', ko='환불 요청', en='Refund Request',
 desc='환불 1건당 1행. 클레임 도메인이 수단별 금액을 정해 요청하고, 결제 도메인이 결제 취소 행과 원장 복원 행을 만든다. 각 행은 이 요청을 가리킨다. 클레임 없는 환불(주문 변경, 자동 취소 등)도 같은 길로 처리한다 (1-3 A).',
 basis='1-3 A, 5-3 A, 선행 6', pk='대리 PK `SEQ_PAY_REFUND_REQUEST`', cache='[확인 필요: 컬럼 검토 질문, 11-3 목록에 없음]',
 delete='삭제하지 않음 (거래). 주문 파티션과 함께 제거',
 part='`ORD_ORDER` 참조 파티션 제안 [확인 필요: 컬럼 검토 질문, 11-1 A 목록에 없음]', keep='주문과 같음. 개인정보 없음',
 cols=[
 ('식별', [
  ('REFUND_REQUEST_ID','환불 요청 고유 식별 번호','Refund Request Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ID','환불 대상 주문 식별 번호','Refunded Order Identifier','ORD_ORDER','N','','참조 파티션 키.'),
 ]),
 ('근거', [
  ('CLAIM_ID','근거 클레임 식별 번호','Source Claim Identifier',ID,'Y','','','[확인 필요: 클레임 도메인 테이블이 정해지면 FK]'),
  fk('ORDER_CHANGE_HIST_ID','근거 주문 변경 이력 식별 번호','Source Order Change History Identifier','ORD_ORDER_CHANGE_HIST','Y',''),
  cd('PAYMENT_REFUND_REASON_CD','결제 자체 환불 사유 코드','Payment-Originated Refund Reason Code','Y','클레임·주문 변경이 아닌 환불 (자동 취소, 만료 뒤 입금, 차지백, PG 관리자 화면 취소 들여오기, 운영자 조정).',30),
 ]),
 ('금액·상태', [
  amt('REFUND_TOTAL_AMT','환불 총액','Refund Total Amount',ck='CK (> 0)',d=''),
  amt('PG_REFUND_AMT','PG 결제 환불 지시 금액','PG Payment Refund Amount',desc='취소 행(PG 취소·계좌 송금·예치금 적립) 합계와 같아야 한다 (5-3 A).'),
  amt('POINT_RESTORE_AMT','적립금 복원 지시 금액','Point Restore Amount'),
  amt('DEPOSIT_RESTORE_AMT','예치금 복원 지시 금액','Deposit Restore Amount'),
  cd('REFUND_REQUEST_STATUS_CD','환불 요청 상태 코드','Refund Request Status Code',desc='요청 → 처리 중 → 완료 / 일부 실패 (1-3 A).'),
  ('REQUESTED_AT','환불 요청 일시','Refund Requested At',TS,'N','SYSTIMESTAMP','',''),
  ('COMPLETED_AT','환불 완료 일시','Refund Completed At',TS,'Y','','',''),
 ]),
 ],
 idx=['IX `IX_PAY_REFUND_REQUEST_ORDER_ID` (FK, LOCAL), `IX_PAY_REFUND_REQUEST_CLAIM_ID`, `IX_PAY_REFUND_REQUEST_ORDER_CHANGE_HIST_ID` (FK)',
      'IX 처리 대상 (함수 기반: 상태 `REQUESTED`·`PROCESSING`·`PARTIALLY_FAILED`인 행만)'],
 check=['근거는 `CLAIM_ID`, `ORDER_CHANGE_HIST_ID`, `PAYMENT_REFUND_REASON_CD` 중 정확히 하나 (1-3 A, 선행 6)',
        '`PG_REFUND_AMT + POINT_RESTORE_AMT + DEPOSIT_RESTORE_AMT = REFUND_TOTAL_AMT` (5-3 A)',
        '상태 `COMPLETED`이면 `COMPLETED_AT` NOT NULL'])

table(t='PAY_PAYMENT_CANCEL', ko='결제 취소 (부분 취소·PG 밖 환불·차지백 포함)', en='Payment Cancellation',
 desc='결제 1건의 취소·환불 1회당 1행. PG 취소뿐 아니라 계좌 송금, 예치금 적립, PG 관리자 화면 취소 들여오기, 차지백 인용도 같은 행으로 남긴다.',
 basis='5-1 B~5-10 A, 3-3 A, 3-8 A, 4-4 A, 6-4 A, 6-7 A, 6-8 A, 8-3 B, 8-6 A, 9-3 A, 10-1 A, 12-3 A',
 pk='대리 PK `SEQ_PAY_PAYMENT_CANCEL`', cache=100,
 delete='삭제하지 않음 (거래). 결제와 함께 파티션 제거. 지우기 전 취소번호를 `SYS_RESERVED_KEY`로 옮긴다 (5-9 A)',
 part='`PAY_PAYMENT` 참조 파티션 (11-1 A)', keep=KEEP5, pii=True,
 cols=[
 ('식별', [
  ('PAYMENT_CANCEL_ID','결제 취소 고유 식별 번호','Payment Cancellation Unique Identifier',ID,'N','','PK',''),
  fk('PAYMENT_ID','취소 대상 결제 식별 번호','Canceled Payment Identifier','PAY_PAYMENT','N','UK1','참조 파티션 키.'),
  ('CANCEL_SN','결제 안 취소 순번','Cancellation Sequence within Payment','NUMBER(3)','N','','UK1, CK (1~999)',''),
  fk('REFUND_REQUEST_ID','환불 요청 식별 번호','Refund Request Identifier','PAY_REFUND_REQUEST','N','IX','이 취소를 만든 환불 요청 (1-3 A). 자동 취소도 결제 사유 환불 요청을 만든다.'),
  ('CANCEL_REQUEST_KEY_VAL','취소 요청 중복 방지 키','Cancellation Request Idempotency Key','VARCHAR2(64)','N','','UK','화면·호출 쪽 중복 요청을 막는다. PG 요청 중복은 취소번호가 막는다 (5-1 B, 5-9 A).'),
  ('CANCEL_NO','취소번호 (PG 취소 요청 업무 키)','Cancellation Number (Business Key Sent to PG)','VARCHAR2(23)','N','','UK','결제번호 + `-C` + 순번 3자리. 응답이 없으면 같은 번호로 조회한 뒤 재시도한다 (5-9 A).'),
 ]),
 ('원인', [
  cd('PAYMENT_CANCEL_REASON_CD','결제 취소 사유 코드','Payment Cancellation Reason Code',desc='사유에 따라 아래 원인 FK 중 필수인 것이 정해진다 (5-2 A).',n=30),
  ('MANUAL_CANCEL_MEMO_CN','운영자 수동 취소 사유 메모','Manual Cancellation Memo','VARCHAR2(1000)','Y','','','사유가 운영자 조정이면 필수 (5-2 A).'),
  ('CLAIM_ID','취소 원인 클레임 식별 번호','Cancellation Source Claim Identifier',ID,'Y','','','클레임 환불. [확인 필요: 클레임 도메인 테이블이 정해지면 FK]'),
  fk('ORDER_CHANGE_HIST_ID','취소 원인 주문 변경 이력 식별 번호','Cancellation Source Order Change History Identifier','ORD_ORDER_CHANGE_HIST','Y','','주문 변경 차액 환불 (5-2 A).'),
  fk('CHARGEBACK_ID','취소 원인 차지백 식별 번호','Cancellation Source Chargeback Identifier','PAY_CHARGEBACK','Y','','차지백 인용 (9-3 A).'),
 ]),
 ('처리 상태', [
  cd('CANCEL_PROCESS_STATUS_CD','취소 처리 상태 코드','Cancellation Process Status Code',desc='5-9 A.'),
  ('REQUESTED_AT','취소 요청 일시','Cancellation Requested At',TS,'N','SYSTIMESTAMP','',''),
  ('COMPLETED_AT','취소 완료 일시','Cancellation Completed At',TS,'Y','','',''),
  ('FAILED_AT','취소 실패 일시','Cancellation Failed At',TS,'Y','','',''),
  ('RETRY_CNT','취소 재시도 횟수','Cancellation Retry Count','NUMBER(3)','N','0','CK (>= 0)','정책값 횟수를 넘으면 예외 수동 처리 (5-9 A).'),
  ('NEXT_RETRY_AT','다음 재시도 예정 일시','Next Retry Scheduled At',TS,'Y','','',''),
  ('INQUIRY_CNT','PG 취소 조회 횟수','PG Cancellation Inquiry Count','NUMBER(3)','N','0','CK (>= 0)','응답이 없을 때 같은 취소번호로 PG 취소 내역을 조회한다 (5-9 A).'),
  ('NEXT_INQUIRY_AT','다음 조회 예정 일시','Next Inquiry Scheduled At',TS,'Y','','',''),
  ('LAST_INQUIRY_AT','마지막 조회 일시','Last Inquiry At',TS,'Y','','',''),
  yn('MANUAL_CHECK_REQUIRED_YN','취소 예외 수동 처리 필요 여부','Cancellation Exception Manual Handling Required Flag','N','예외 = 재시도로 끝내지 못했거나 기한 안에 이행하기 어려운 취소·환불 (PYC-59 A). 켜는 경로는 사유 코드의 값 목록 (4-4 A, 5-9 A). 처리가 끝나도 Y로 남긴다 (PYC-20 A).'),
  cd('CANCEL_MANUAL_CHECK_REASON_CD','취소 예외 수동 처리 사유 코드','Cancellation Exception Manual Handling Reason Code','Y','처리 필요가 Y일 때만, 그때 NOT NULL (PYC-20 A). 결제 행과 값 목록이 달라 이름을 나눴다 (코드 그룹 이름 = 컬럼 이름).',30),
  ('MANUAL_CHECK_RESOLVED_AT','취소 예외 수동 처리 완료 일시','Cancellation Exception Manual Handling Resolved At',TS,'Y','','','PYC-20 A.'),
  fk('MANUAL_CHECK_RESOLVER_ADMIN_USER_ID','취소 예외 수동 처리 관리자 식별 번호','Cancellation Exception Manual Handling Resolver Administrator Identifier','ADM_USER','Y','','완료 일시와 함께 채운다 (PYC-20 A).'),
  ('PG_CANCEL_TRANSACTION_NO','PG 취소 거래번호','PG Cancellation Transaction Number','VARCHAR2(100)','Y','','',''),
  ('PG_RESULT_CD','PG 결과 코드 (PG 원래 값)','PG Result Code (Raw)','VARCHAR2(50)','Y','','',''),
  ('PG_RESULT_MESSAGE_CN','PG 결과 메시지','PG Result Message','VARCHAR2(1000)','Y','','',''),
  cd('CANCEL_TIME_CARD_ACQUIRE_STATUS_CD','취소 시점 카드 매입 상태 코드','Card Acquisition Status at Cancellation Code','Y','카드 결제의 PG 취소일 때만. 취소 직전 PG 조회나 취소 응답에서 받은 값 (PYC-9 A). 매입 전 취소는 승인 취소라 바로 사라지고, 매입 뒤 취소는 카드사 환불이라 며칠 걸린다는 고객 안내에 쓴다. 한 번 쓰고 바꾸지 않는다.'),
 ]),
 ('금액', [
  amt('CANCEL_AMT','취소·환불 금액','Cancellation or Refund Amount',ck='CK (> 0)',d='',desc='결제 행의 취소 가능 잔액 안에서만 (2-7 A).'),
  cd('REFUND_METHOD_CD','환불 방법 코드','Refund Method Code',desc='PG 취소면 결제 행 PG 취소 누계에, 나머지는 PG 밖 환불 누계에 더한다 (5-4 A, 9-3 A).'),
  amt('CARD_ISSUER_INSTANT_DISCOUNT_CANCEL_AMT','카드사 부담 즉시 할인 취소 금액','Card Issuer-Funded Instant Discount Cancellation Amount',desc='이번 취소로 되돌아간 카드사 즉시 할인. PG·카드사 부분 취소 규칙의 결과를 받은 값 (토스 `cancels[].cardDiscountAmount`, 10-1 A, PYC-11 A).'),
  amt('EASY_PAY_PROVIDER_INSTANT_DISCOUNT_CANCEL_AMT','간편결제사 부담 즉시 할인 취소 금액','Easy Pay Provider-Funded Instant Discount Cancellation Amount',desc='토스 `cancels[].easyPayDiscountAmount` (PYC-11 A).'),
  amt('PG_INSTANT_DISCOUNT_CANCEL_AMT','PG 부담 즉시 할인 취소 금액','PG-Funded Instant Discount Cancellation Amount',desc='토스 `cancels[].transferDiscountAmount` 등 PG 부담 할인 (PYC-15 A).'),
  amt('CASH_RECEIPT_TARGET_CANCEL_AMT','현금영수증 대상 취소 금액','Cash Receipt Target Cancellation Amount',desc='6-4 A.'),
  amt('TAXABLE_SUPPLY_AMT','취소 과세 공급가액','Canceled Taxable Supply Amount',desc='마지막 취소가 남은 값을 모두 가져간다 (6-8 A).'),
  amt('VAT_AMT','취소 부가가치세 금액','Canceled Value-Added Tax Amount'),
  amt('TAX_FREE_AMT','취소 면세 금액','Canceled Tax-Free Amount'),
  amt('REFUND_DEDUCTION_AMT','환불 차감 금액','Refund Deduction Amount',desc='교환 배송비·도서산간 비용·적립금 회수 부족분처럼 환불에서 뺀 금액 (5-10 A, 12-3 A). [확인 필요: 컬럼 검토 질문, 차감이 여러 사유면 클레임 쪽 내역으로 둘지]'),
  cd('REFUND_DEDUCTION_REASON_CD','환불 차감 사유 코드','Refund Deduction Reason Code','Y','차감이 있을 때만.',30),
 ]),
 ('환불 계좌·예치금', [
  cd('REFUND_BANK_CD','환불 계좌 은행 코드','Refund Account Bank Code','Y','계좌 송금일 때만 (5-6 A). `CMM_CODE` 은행 그룹 재사용.',ck=''),
  ('REFUND_ACCOUNT_NUMBER_ENC','환불 계좌번호 암호문','Refund Account Number Ciphertext','RAW(59)','Y','','','회원과 같은 길이 (8-3 B). 파기 대상.'),
  ('MASKED_REFUND_ACCOUNT_NUMBER_VAL','마스킹 환불 계좌번호','Masked Refund Account Number','VARCHAR2(30)','Y','','','파기 대상.'),
  ('REFUND_ACCOUNT_HOLDER_NM','환불 계좌 예금주 이름','Refund Account Holder Name','VARCHAR2(150)','Y','','','평문 + TDE (C-72). 파기 대상.'),
  cd('ACCOUNT_HOLDER_VERIFY_RESULT_CD','예금주 조회 결과 코드','Account Holder Verification Result Code','Y','송금 전 예금주 조회 결과 (5-6 A).'),
  ('ACCOUNT_HOLDER_VERIFIED_AT','예금주 조회 일시','Account Holder Verified At',TS,'Y','','','송금 전 예금주 조회 (5-6 A).'),
  ('TRANSFER_FAILURE_REASON_CN','송금 실패 사유','Bank Transfer Failure Reason','VARCHAR2(500)','Y','','','실패하면 이 행을 실패로 두고 새 계좌로 새 취소 행을 만든다 (5-6 A).'),
  ('DEPOSIT_CREDIT_CONSENTED_AT','예치금 환불 동의 일시','Deposit Credit Consent At',TS,'Y','','','환불 방법이 예치금이면 NOT NULL (5-5 A, 4-4 A).'),
 ]),
 ('환불 기한', [
  ('REFUND_BASE_DT','환급 기산 일자','Refund Base Date','DATE','Y','','','법정 3영업일의 기산일 (5-8 A, 전자상거래법 18조).'),
  ('REFUND_DUE_DT','법정 환급 기한 일자','Statutory Refund Due Date','DATE','Y','','','영업일 달력으로 계산 (주문 1-8 A).'),
  ('REFUND_FULFILLED_AT','환급 이행 일시','Refund Fulfilled At',TS,'Y','','',''),
  ('REFUND_DELAY_DAYS_CNT','환급 지연 일수','Refund Delay Days Count','NUMBER(5)','Y','','CK (>= 0)','이행할 때 기록. 지연배상금은 클레임 도메인이 계산한다 (5-8 A).'),
  yn('CUSTOMER_CAUSED_DELAY_YN','고객 사유 지연 여부','Customer-Caused Delay Flag','N','[확인 필요: 법무, 고객 사유 지연의 범위]'),
  ('PG_CANCEL_RECEIPT_URL','PG 취소 전표 조회 URL','PG Cancellation Receipt Inquiry URL','VARCHAR2(500)','Y','','','6-7 A.'),
 ]),
 ],
 idx=['UK `UK_PAY_PAYMENT_CANCEL_PAYMENT_ID_CANCEL_SN` LOCAL, `UK_PAY_PAYMENT_CANCEL_CANCEL_NO` GLOBAL',
      'UK `UK_PAY_PAYMENT_CANCEL_CANCEL_REQUEST_KEY_VAL` GLOBAL (5-1 B)',
      'IX `IX_PAY_PAYMENT_CANCEL_NEXT_INQUIRY_AT` (함수 기반: `NEXT_INQUIRY_AT`이 있는 행만), `IX_PAY_PAYMENT_CANCEL_NEXT_RETRY_AT` (함수 기반: 상태 `REQUESTED`·`UNKNOWN`·`FAILED`이고 예외 수동 처리이 아닌 행만, 5-9 A), `IX_PAY_PAYMENT_CANCEL_REFUND_DUE_DT` (함수 기반: 이행 전 행만, 5-8 A)',
      'IX `IX_PAY_PAYMENT_CANCEL_CLAIM_ID`, `IX_PAY_PAYMENT_CANCEL_ORDER_CHANGE_HIST_ID`, `IX_PAY_PAYMENT_CANCEL_CHARGEBACK_ID` (FK), `IX_PAY_PAYMENT_CANCEL_PII_RETENTION_END_DT`',
      'IX `IX_PAY_PAYMENT_CANCEL_MANUAL_CHECK_OPEN` (함수 기반: 처리 필요 Y이고 완료 전인 행만 `CREATED_AT`), `IX_PAY_PAYMENT_CANCEL_MANUAL_CHECK_RESOLVER_ADMIN_USER_ID` (FK) (PYC-20 A)'],
 check=['원인 FK는 사유에 맞는 하나만: `CLAIM_REFUND` → `CLAIM_ID`, `ORDER_CHANGE_ADJUSTMENT` → `ORDER_CHANGE_HIST_ID`, `CHARGEBACK` → `CHARGEBACK_ID`, 나머지 → 셋 다 NULL (5-2 A, 9-3 A)',
        '`REFUND_METHOD_CD` = `CHARGEBACK` ⇔ 사유 `CHARGEBACK` (9-3 A)',
        '`REFUND_METHOD_CD` = `BANK_TRANSFER`이면 환불 계좌 컬럼 NOT NULL(파기 전). `DEPOSIT_CREDIT`이면 `DEPOSIT_CREDIT_CONSENTED_AT` NOT NULL (5-5 A, 5-6 A)',
        '`CANCEL_PROCESS_STATUS_CD` = `COMPLETED`이면 `COMPLETED_AT` NOT NULL. 환불 방법이 `BANK_TRANSFER`이고 완료면 `ACCOUNT_HOLDER_VERIFY_RESULT_CD` = `MATCHED` (5-6 A)',
        '사유 `MANUAL_ADJUSTMENT`이면 `MANUAL_CANCEL_MEMO_CN` NOT NULL (5-2 A)',
        '취소 행의 원인 FK와 환불 요청의 근거는 같아야 한다 (테이블이 달라 애플리케이션 검사). [확인 필요: 컬럼 검토 질문, 원인 FK를 취소 행에도 둘지 (1-3 A, 5-2 A)]',
        '`REFUND_DEDUCTION_AMT` > 0 ⇔ `REFUND_DEDUCTION_REASON_CD` NOT NULL',
        '`MANUAL_CHECK_REQUIRED_YN` = Y ⇔ `CANCEL_MANUAL_CHECK_REASON_CD` NOT NULL. `MANUAL_CHECK_RESOLVED_AT` NOT NULL ⇔ `MANUAL_CHECK_RESOLVER_ADMIN_USER_ID` NOT NULL이고, 완료 일시가 있으면 처리 필요 Y (PYC-20 A)'])

# =========================================================== 2. 적립금·예치금
table(t='PAY_POINT_LEDGER', ko='적립금 원장 (적립 행 = 적립 건)', en='Point Ledger',
 desc='적립금 증감 1건당 1행. 적립 행이 곧 적립 건이고 남은 금액과 유효기한을 가진다. 잔액 컬럼은 두지 않고 남은 금액 합계로 계산한다 (12-5 C).',
 basis='선행 15, 1-2 A, 7-4 A, 12-1 A, 12-3 A, 12-4 A(질문 2), 12-5 C, 주문 1-4 A·6-8 A·OC-26 A',
 pk='대리 PK `SEQ_PAY_POINT_LEDGER`', cache='[확인 필요: 컬럼 검토 질문, 11-3 목록에 없음]',
 delete='삭제하지 않음 (원장). 남은 금액 0이고 마지막 변동 뒤 정책값 5년이 지난 건을 차감 기록과 함께 나눠서 DELETE (12-4 A)',
 part='없음 (행별 기한, 12-4 A)', keep='마지막 변동 + 5년 (정책값). 개인정보 없음',
 cols=[
 ('식별', [
  ('POINT_LEDGER_ID','적립금 원장 고유 식별 번호','Point Ledger Unique Identifier',ID,'N','','PK',''),
  fk('MEMBER_ID','적립금 소유 회원 식별 번호','Point Owner Member Identifier','MBR_MEMBER','N','IX',''),
 ]),
 ('거래', [
  cd('POINT_TRANSACTION_TYPE_CD','적립금 거래 유형 코드','Point Transaction Type Code',desc='유형별 부호를 CHECK로 검사한다 (12-1 A, 12-3 A).',n=30),
  cd('POINT_LEDGER_STATUS_CD','적립금 원장 상태 코드','Point Ledger Status Code',desc='예정·확정·취소 (선행 15).'),
  amt('POINT_AMT','적립금 증감 금액 (부호 있음)','Signed Point Amount',ck='CK (유형별 부호)',d='',desc='적립·복원은 +, 사용·소멸·회수는 −.'),
  cd('POINT_KIND_CD','적립금 종류 코드','Point Kind Code','Y','구매 적립(자기적립마일리지) / 기타. 적립 행은 NOT NULL, 차감 행은 차감 기록으로 안다 (주문 OC-26 A).'),
  cd('POINT_ACCRUAL_REASON_CD','적립 사유 코드','Point Accrual Reason Code','Y','적립 행만. [확인 필요: 프로모션 도메인 적립 정책과 맞춤]',30),
  ('TRANSACTION_DESC','고객 표시 거래 내용','Customer-Facing Transaction Description','VARCHAR2(200)','Y','','','적립금 내역 화면 문구.'),
 ]),
 ('적립 건', [
  ('EXPIRES_DT','유효기한 일자','Expiration Date','DATE','Y','','','적립 행만 NOT NULL. 이 날까지 쓸 수 있다 (12-5 C: 조회 조건 `EXPIRES_DT >= 오늘`).'),
  amt('REMAINING_AMT','적립 건 남은 금액','Accrual Remaining Amount',null='Y',d='',ck='CK (0 ~ POINT_AMT)',desc='적립 행만. 차감·복원 때 같은 트랜잭션에서 바꾼다 (12-1 A). 매일 대사로 검증 (7-4 A).'),
  fk('RESTORED_FROM_POINT_LEDGER_ID','유예 복원 원래 적립 건 식별 번호','Restored-From Accrual Ledger Identifier','PAY_POINT_LEDGER','Y','','기한이 지난 건을 유예 기한으로 다시 준 행(`RESTORE_REISSUE`)만. 종류를 따라간다 (12-3 A).'),
  fk('ORIGINAL_POINT_LEDGER_ID','취소·회수 대상 원장 식별 번호','Original Ledger Identifier for Cancellation','PAY_POINT_LEDGER','Y','','적립 취소·회수 행이 가리키는 적립 행.'),
  ('CONFIRMED_AT','확정 일시','Confirmed At',TS,'Y','','','예정 적립이 구매 확정으로 확정된 일시 (주문 6-8 A).'),
  ('CANCELED_AT','취소 일시','Canceled At',TS,'Y','','',''),
 ]),
 ('원인', [
  ref('ORDER_ID','관련 주문 식별 번호','Related Order Identifier',desc='주문 파티션 제거를 막지 않게 FK를 걸지 않는다 (11-1 A).'),
  ref('ORDER_ITEM_ID','관련 주문 상품 식별 번호','Related Order Item Identifier',desc='상품별 적립·사용 배분과 맞춘다 (7-4 A).'),
  ref('CLAIM_ID','관련 클레임 식별 번호','Related Claim Identifier',desc='반품 복원·회수 (12-3 A). FK 없음.'),
  ref('REFUND_REQUEST_ID','복원 원인 환불 요청 식별 번호','Restoration Source Refund Request Identifier',desc='환불로 복원·회수한 행 (1-3 A). 원장은 파티션이 없어 FK를 걸면 주문 파티션 제거가 막히므로 FK 없음 (11-1 A).'),
 ]),
 ],
 idx=['IX `IX_PAY_POINT_LEDGER_MEMBER_ID_EXPIRES_DT` (함수 기반: 확정이고 남은 금액 > 0인 적립 행만, 차감·소멸·잔액 계산, 12-1 A, 12-5 C)',
      'IX `IX_PAY_POINT_LEDGER_MEMBER_ID` (FK, 내역 조회 `MEMBER_ID, CREATED_AT`), `IX_PAY_POINT_LEDGER_ORDER_ID`, `IX_PAY_POINT_LEDGER_ORDER_ITEM_ID`, `IX_PAY_POINT_LEDGER_CLAIM_ID`',
      'IX 삭제 대상 (함수 기반: 남은 금액 0인 적립 행만 `UPDATED_AT`, 12-4 A)'],
 check=['적립 행(`ACCRUAL`, `RESTORE_REISSUE`, `MOVE_IN`)만 `REMAINING_AMT`, `EXPIRES_DT`, `POINT_KIND_CD` NOT NULL. 나머지는 NULL',
        '유형별 부호: 적립·복원·이동 받음 > 0, 사용·소멸·적립 취소·회수·이동 보냄 < 0. 조정은 0이 아님'])

table(t='PAY_POINT_DEDUCTION', ko='적립금 차감 기록 (차감 행 × 적립 건)', en='Point Deduction Allocation',
 desc='사용·소멸·회수 행이 어느 적립 건에서 얼마를 뺐는지. 반품 복원은 이 기록을 따라 원래 적립 건으로 되돌린다 (12-3 A).',
 basis='선행 15, 12-1 A, 12-3 A', pk='복합 PK (`DEDUCTING_POINT_LEDGER_ID`, `ACCRUAL_POINT_LEDGER_ID`)', cache='없음 (시퀀스 없음)',
 delete='원장 행과 함께 나눠서 DELETE (12-4 A)', part='없음', keep='원장과 같음',
 cols=[
 ('식별', [
  fk('DEDUCTING_POINT_LEDGER_ID','차감한 원장 식별 번호','Deducting Ledger Identifier','PAY_POINT_LEDGER','N','PK',''),
  fk('ACCRUAL_POINT_LEDGER_ID','차감된 적립 건 식별 번호','Deducted Accrual Ledger Identifier','PAY_POINT_LEDGER','N','PK',''),
 ]),
 ('금액', [
  amt('DEDUCTED_AMT','차감 금액','Deducted Amount',ck='CK (> 0)',d=''),
  amt('RESTORED_AMT','복원 금액','Restored Amount',ck='CK (0 ~ DEDUCTED_AMT)',desc='반품으로 원래 적립 건에 되돌린 금액. [확인 필요: 컬럼 검토 질문, 복원을 이 컬럼으로 할지 음수 행으로 할지 (12-3 A)]'),
 ]),
 ],
 idx=['IX `IX_PAY_POINT_DEDUCTION_ACCRUAL_POINT_LEDGER_ID` (FK, 적립 건별 차감 합계 대사)'])

table(t='PAY_DEPOSIT_LEDGER', ko='예치금 원장 (입금 행 = 입금 건)', en='Deposit Ledger',
 desc='예치금 증감 1건당 1행. 입금 행이 곧 입금 건이고 출처와 남은 금액을 가진다. 출금은 현금성 입금 건에서만, 사용은 카드성부터 차감한다 (12-2 A).',
 basis='선행 15, 1-2 A, 4-4 A, 5-5 A, 5-7 A, 7-4 A, 12-2 A, 12-4 A, 12-5 C',
 pk='대리 PK `SEQ_PAY_DEPOSIT_LEDGER`', cache='[확인 필요: 컬럼 검토 질문, 11-3 목록에 없음]',
 delete='삭제하지 않음 (원장). 남은 금액 0이고 마지막 변동 뒤 정책값 5년이 지난 건만 나눠서 DELETE (12-4 A)',
 part='없음 (예치금은 유효기한이 없음, 12-4 A)', keep='마지막 변동 + 5년 (정책값). 개인정보 없음',
 cols=[
 ('식별', [
  ('DEPOSIT_LEDGER_ID','예치금 원장 고유 식별 번호','Deposit Ledger Unique Identifier',ID,'N','','PK',''),
  fk('MEMBER_ID','예치금 소유 회원 식별 번호','Deposit Owner Member Identifier','MBR_MEMBER','N','IX',''),
 ]),
 ('거래', [
  cd('DEPOSIT_TRANSACTION_TYPE_CD','예치금 거래 유형 코드','Deposit Transaction Type Code',desc='예치금은 들어오는 즉시 확정이라 상태 컬럼이 없다 (12-2 A).',n=30),
  amt('DEPOSIT_AMT','예치금 증감 금액 (부호 있음)','Signed Deposit Amount',ck='CK (유형별 부호)',d=''),
  cd('DEPOSIT_CREDIT_REASON_CD','예치금 입금 사유 코드','Deposit Credit Reason Code','Y','입금 행만.',30),
  ('TRANSACTION_DESC','고객 표시 거래 내용','Customer-Facing Transaction Description','VARCHAR2(200)','Y','','',''),
 ]),
 ('입금 건', [
  cd('DEPOSIT_SOURCE_TYPE_CD','예치금 입금 출처 유형 코드','Deposit Source Type Code','Y','입금 행만. 입금을 만든 취소 행의 원 결제 수단으로 정한다 (12-2 A). [확인 필요: 법무, 카드성 출금 제한]'),
  amt('REMAINING_AMT','입금 건 남은 금액','Credit Remaining Amount',null='Y',d='',ck='CK (0 ~ DEPOSIT_AMT)',desc='입금 행만.'),
  fk('ORIGINAL_DEPOSIT_LEDGER_ID','취소 대상 원장 식별 번호','Original Ledger Identifier for Cancellation','PAY_DEPOSIT_LEDGER','Y','',''),
 ]),
 ('원인', [
  ref('PAYMENT_ID','관련 결제 식별 번호','Related Payment Identifier',desc='결제 파티션 제거를 막지 않게 FK 없음 (11-1 A).'),
  ref('PAYMENT_CANCEL_ID','입금 원인 결제 취소 식별 번호','Credit Source Payment Cancellation Identifier',desc='예치금 환불(5-5 A), 과다 환불 회수(5-7 A). FK 없음.'),
  ref('ORDER_ID','관련 주문 식별 번호','Related Order Identifier'),
  ref('ORDER_ITEM_ID','관련 주문 상품 식별 번호','Related Order Item Identifier'),
  ref('CLAIM_ID','관련 클레임 식별 번호','Related Claim Identifier'),
  ref('REFUND_REQUEST_ID','복원 원인 환불 요청 식별 번호','Restoration Source Refund Request Identifier',desc='환불로 복원한 행 (1-3 A). FK 없음 (11-1 A).'),
  fk('DEPOSIT_WITHDRAWAL_REQUEST_ID','관련 출금 요청 식별 번호','Related Withdrawal Request Identifier','PAY_DEPOSIT_WITHDRAWAL_REQUEST','Y','','출금·출금 취소 행만 (12-4 A).'),
 ]),
 ],
 idx=['IX `IX_PAY_DEPOSIT_LEDGER_MEMBER_ID_SOURCE` (함수 기반: 남은 금액 > 0인 입금 행만 (`MEMBER_ID`, `DEPOSIT_SOURCE_TYPE_CD`), 12-5 C)',
      'IX `IX_PAY_DEPOSIT_LEDGER_MEMBER_ID` (FK), `IX_PAY_DEPOSIT_LEDGER_PAYMENT_CANCEL_ID`, `IX_PAY_DEPOSIT_LEDGER_ORDER_ID`, `IX_PAY_DEPOSIT_LEDGER_DEPOSIT_WITHDRAWAL_REQUEST_ID` (FK)'],
 check=['입금 행(`CREDIT`, `MOVE_IN`)만 `REMAINING_AMT`, `DEPOSIT_SOURCE_TYPE_CD`, `DEPOSIT_CREDIT_REASON_CD` NOT NULL',
        '`WITHDRAWAL`, `WITHDRAWAL_CANCEL`이면 `DEPOSIT_WITHDRAWAL_REQUEST_ID` NOT NULL', '유형별 부호 (적립금 원장과 같은 방식)'])

table(t='PAY_DEPOSIT_DEDUCTION', ko='예치금 차감 기록 (차감 행 × 입금 건)', en='Deposit Deduction Allocation',
 desc='사용·출금 행이 어느 입금 건에서 얼마를 뺐는지. 출금 실패·사용 취소는 이 기록을 따라 같은 입금 건으로 되돌린다 (12-4 A).',
 basis='선행 15, 12-2 A, 12-4 A', pk='복합 PK (`DEDUCTING_DEPOSIT_LEDGER_ID`, `CREDIT_DEPOSIT_LEDGER_ID`)', cache='없음 (시퀀스 없음)',
 delete='원장 행과 함께 나눠서 DELETE', part='없음', keep='원장과 같음',
 cols=[
 ('식별', [
  fk('DEDUCTING_DEPOSIT_LEDGER_ID','차감한 원장 식별 번호','Deducting Ledger Identifier','PAY_DEPOSIT_LEDGER','N','PK',''),
  fk('CREDIT_DEPOSIT_LEDGER_ID','차감된 입금 건 식별 번호','Deducted Credit Ledger Identifier','PAY_DEPOSIT_LEDGER','N','PK',''),
 ]),
 ('금액', [
  amt('DEDUCTED_AMT','차감 금액','Deducted Amount',ck='CK (> 0)',d=''),
  amt('RESTORED_AMT','복원 금액','Restored Amount',ck='CK (0 ~ DEDUCTED_AMT)',desc='적립금 차감 기록과 같은 방식.'),
 ]),
 ],
 idx=['IX `IX_PAY_DEPOSIT_DEDUCTION_CREDIT_DEPOSIT_LEDGER_ID` (FK)'])

table(t='PAY_DEPOSIT_WITHDRAWAL_REQUEST', ko='예치금 출금 요청', en='Deposit Withdrawal Request',
 desc='예치금을 계좌로 돌려받는 요청 1건당 1행. 요청 순간 원장에서 차감하고, 실패하면 출금 취소 행으로 되돌린다 (12-4 A). 이체 실행과 회사 계좌 내역은 정산 도메인.',
 basis='선행 15, 12-2 A, 12-4 A, 8-3 B, 8-6 A, 회원 28-7·43-2 C', pk='대리 PK `SEQ_PAY_DEPOSIT_WITHDRAWAL_REQUEST`', cache=20,
 delete='삭제하지 않음 (거래). 개인정보는 파기 예정일에 NULL, 행은 원장 보관과 같은 기준으로 삭제', part='없음',
 keep='개인정보: 완료일 + 5년 (8-6 A)', pii=True,
 cols=[
 ('식별', [
  ('DEPOSIT_WITHDRAWAL_REQUEST_ID','예치금 출금 요청 고유 식별 번호','Deposit Withdrawal Request Unique Identifier',ID,'N','','PK',''),
  fk('MEMBER_ID','출금 요청 회원 식별 번호','Requesting Member Identifier','MBR_MEMBER','N','IX',''),
  cd('WITHDRAWAL_REQUEST_TYPE_CD','출금 요청 유형 코드','Withdrawal Request Type Code',desc='고객 요청 / 탈퇴 자동 (회원 28-7).',n=30),
 ]),
 ('상태·금액', [
  cd('WITHDRAWAL_STATUS_CD','출금 처리 상태 코드','Withdrawal Status Code'),
  amt('WITHDRAWAL_AMT','출금 금액','Withdrawal Amount',ck='CK (> 0)',d='',desc='현금성 입금 건 남은 금액 합계 안에서만 (12-2 A).'),
  ('REQUESTED_AT','출금 요청 일시','Withdrawal Requested At',TS,'N','SYSTIMESTAMP','',''),
  ('TRANSFER_STARTED_AT','이체 시작 일시','Transfer Started At',TS,'Y','','',''),
  ('COMPLETED_AT','출금 완료 일시','Withdrawal Completed At',TS,'Y','','',''),
  ('FAILED_AT','출금 실패 일시','Withdrawal Failed At',TS,'Y','','',''),
  ('FAILURE_REASON_CN','출금 실패 사유','Withdrawal Failure Reason','VARCHAR2(500)','Y','','',''),
  ('RETRY_CNT','이체 재시도 횟수','Transfer Retry Count','NUMBER(3)','N','0','CK (>= 0)',''),
  ('TRANSFER_REFERENCE_NO','이체 참조 번호 (정산 도메인)','Transfer Reference Number (Settlement Domain)','VARCHAR2(50)','Y','','','출금 내역 대사(7-4 A)에 쓴다.'),
 ]),
 ('출금 계좌', [
  cd('BANK_CD','출금 계좌 은행 코드','Withdrawal Account Bank Code','Y','회원 환불 계좌에서 복사. `CMM_CODE` 은행 그룹 재사용.',ck=''),
  ('ACCOUNT_NUMBER_ENC','출금 계좌번호 암호문','Withdrawal Account Number Ciphertext','RAW(59)','Y','','','파기 대상 (8-3 B).'),
  ('MASKED_ACCOUNT_NUMBER_VAL','마스킹 출금 계좌번호','Masked Withdrawal Account Number','VARCHAR2(30)','Y','','','파기 대상.'),
  ('ACCOUNT_HOLDER_NM','출금 계좌 예금주 이름','Withdrawal Account Holder Name','VARCHAR2(150)','Y','','','평문 + TDE. 파기 대상.'),
  ('ACCOUNT_VERIFIED_AT','계좌 1원 인증 확인 일시 (복사)','Account One-Won Verification At (Copied)',TS,'Y','','','회원의 인증 완료 일시를 복사 (회원 43-2 C).'),
 ]),
 ],
 idx=['IX `IX_PAY_DEPOSIT_WITHDRAWAL_REQUEST_MEMBER_ID` (FK)', 'IX 처리 대상 (함수 기반: 상태 `REQUESTED`·`FAILED`인 행만)', 'IX `IX_PAY_DEPOSIT_WITHDRAWAL_REQUEST_PII_RETENTION_END_DT`'],
 check=['상태 `COMPLETED`이면 `COMPLETED_AT` NOT NULL, `FAILED`이면 `FAILED_AT` NOT NULL'])

# =========================================================== 3. 증빙
table(t='PAY_CASH_RECEIPT', ko='현금영수증 발급·취소', en='Cash Receipt Issuance',
 desc='현금영수증 발급 1회, 취소 1회당 1행. 신청 정보는 결제 행에 있고, 이 테이블은 실제 발급·취소 기록이다 (6-1 C).',
 basis='4-5 A, 6-1 C~6-4 A, 6-6 A, 8-3 B, 8-6 A', pk='대리 PK `SEQ_PAY_CASH_RECEIPT`', cache=100,
 delete='삭제하지 않음 (거래). 결제와 함께 파티션 제거', part='`PAY_PAYMENT` 참조 파티션 (11-1 A)',
 keep='개인정보: 국세 증빙 5년 (법정 신고 기한 기산, 8-6 A). 행: 주문 파티션과 함께', pii=True,
 cols=[
 ('식별', [
  ('CASH_RECEIPT_ID','현금영수증 발급 고유 식별 번호','Cash Receipt Issuance Unique Identifier',ID,'N','','PK',''),
  fk('PAYMENT_ID','대상 결제 식별 번호','Target Payment Identifier','PAY_PAYMENT','N','','참조 파티션 키.'),
  fk('PAYMENT_CANCEL_ID','원인 결제 취소 식별 번호','Source Payment Cancellation Identifier','PAY_PAYMENT_CANCEL','Y','','취소에 따라 취소·재발급한 경우 (6-4 A).'),
  fk('ORIGINAL_CASH_RECEIPT_ID','취소 대상 원 발급 식별 번호','Original Cash Receipt Identifier','PAY_CASH_RECEIPT','Y','','취소 행만.'),
  fk('PREVIOUS_CASH_RECEIPT_ID','재발급 직전 영수증 식별 번호','Previous Cash Receipt Identifier for Reissue','PAY_CASH_RECEIPT','Y','','전액 취소 뒤 남은 금액으로 재발급한 행이 직전 영수증을 가리킨다 (6-4 A).'),
 ]),
 ('발급', [
  cd('CASH_RECEIPT_ACTION_CD','현금영수증 처리 구분 코드','Cash Receipt Action Code',desc='발급 / 전액 취소 / 부분 취소 (6-4 A).'),
  cd('CASH_RECEIPT_ISSUE_TYPE_CD','현금영수증 발급 유형 코드','Cash Receipt Issue Type Code',desc='고객 신청 / 무기명 자진 발급 (6-3 C).'),
  cd('CASH_RECEIPT_PROCESS_STATUS_CD','현금영수증 처리 상태 코드','Cash Receipt Process Status Code'),
  cd('CASH_RECEIPT_ISSUE_ROUTE_CD','현금영수증 발급 경로 코드','Cash Receipt Issue Route Code',desc='PG 설정의 발급 주체를 복사 (6-1 C).'),
  ('NTS_APPROVAL_NO','국세청 현금영수증 승인번호','National Tax Service Cash Receipt Approval Number','VARCHAR2(30)','Y','','',''),
  ('ISSUE_DUE_DT','법정 발급 기한 일자','Statutory Issue Due Date','DATE','Y','','','현금 수령일부터 5일 (소득세법 시행령 210조의3 13항, 6-3 C).'),
  ('REQUESTED_AT','발급 요청 일시','Issue Requested At',TS,'N','SYSTIMESTAMP','',''),
  ('ISSUED_AT','발급·취소 완료 일시','Issued or Canceled At',TS,'Y','','',''),
  ('FAILED_AT','발급 실패 일시','Issue Failed At',TS,'Y','','',''),
  ('RETRY_CNT','재시도 횟수','Retry Count','NUMBER(3)','N','0','CK (>= 0)',''),
  ('NEXT_RETRY_AT','다음 재시도 예정 일시','Next Retry Scheduled At',TS,'Y','','',''),
  pgcd(desc='발급을 대행한 PG.'),
  ('PG_RESULT_CD','PG 결과 코드 (PG 원래 값)','PG Result Code (Raw)','VARCHAR2(50)','Y','','',''),
 ]),
 ('금액', [
  amt('TOTAL_AMT','발급·취소 합계 금액','Total Amount',ck='CK (> 0)',d=''),
  amt('TAXABLE_SUPPLY_AMT','과세 공급가액','Taxable Supply Amount'),
  amt('VAT_AMT','부가가치세 금액','Value-Added Tax Amount'),
  amt('TAX_FREE_AMT','면세 금액','Tax-Free Amount'),
 ]),
 ('식별 번호', [
  cd('CASH_RECEIPT_PURPOSE_CD','현금영수증 발급 용도 코드','Cash Receipt Purpose Code','Y','무기명 자진 발급은 국세청 지정 번호 (6-3 C). 회원 그룹 재사용.',ck=''),
  cd('CASH_RECEIPT_IDENTIFIER_TYPE_CD','현금영수증 식별 번호 유형 코드','Cash Receipt Identifier Type Code','Y','회원 그룹 재사용.',ck=''),
  ('CASH_RECEIPT_IDENTIFIER_NUMBER_ENC','현금영수증 식별 번호 암호문','Cash Receipt Identifier Number Ciphertext','RAW(49)','Y','','','파기 대상 (8-3 B).'),
  ('MASKED_CASH_RECEIPT_IDENTIFIER_NUMBER_VAL','마스킹 현금영수증 식별 번호','Masked Cash Receipt Identifier Number','VARCHAR2(20)','Y','','','파기 대상.'),
 ]),
 ],
 idx=['IX `IX_PAY_CASH_RECEIPT_PAYMENT_ID` (FK, LOCAL), `IX_PAY_CASH_RECEIPT_PAYMENT_CANCEL_ID`, `IX_PAY_CASH_RECEIPT_ORIGINAL_CASH_RECEIPT_ID` (FK)',
      'IX 처리 대상 (함수 기반: 상태 `REQUESTED`·`FAILED`인 행만 `NEXT_RETRY_AT`), 기한 감시 (`ISSUE_DUE_DT`, 7-6 B)', 'IX `IX_PAY_CASH_RECEIPT_PII_RETENTION_END_DT`'],
 check=['`CASH_RECEIPT_ACTION_CD`가 취소면 `ORIGINAL_CASH_RECEIPT_ID` NOT NULL, 발급이면 NULL',
        '`TAXABLE_SUPPLY_AMT + VAT_AMT + TAX_FREE_AMT = TOTAL_AMT`', '상태 `ISSUED`이면 `NTS_APPROVAL_NO`, `ISSUED_AT` NOT NULL'])

table(t='PAY_TAX_INVOICE', ko='세금계산서 발급', en='Tax Invoice Issuance',
 desc='주문 기준 세금계산서 1장당 1행. 수정 세금계산서도 새 행이다. 작성일자는 출고일 기준이고 받는 자 정보는 발급 시점 스냅샷이다 (6-5 A).',
 basis='6-5 A, 6-6 A, 8-3 B, 8-6 A, 주문 OC-25 B', pk='대리 PK `SEQ_PAY_TAX_INVOICE`', cache=20,
 delete='삭제하지 않음 (거래). 주문 파티션과 함께 제거', part='`ORD_ORDER` 참조 파티션 (11-1 A)',
 keep='개인정보: 국세 증빙 5년 (법정 신고 기한 기산, 8-6 A). 사업자번호는 같은 기간 보유', pii=True,
 cols=[
 ('식별', [
  ('TAX_INVOICE_ID','세금계산서 발급 고유 식별 번호','Tax Invoice Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ID','대상 주문 식별 번호','Target Order Identifier','ORD_ORDER','N','UK1','참조 파티션 키.'),
  ('TAX_INVOICE_SN','주문 안 세금계산서 순번','Tax Invoice Sequence within Order','NUMBER(3)','N','','UK1',''),
  cd('TAX_INVOICE_TYPE_CD','세금계산서 구분 코드','Tax Invoice Type Code',desc='당초 / 수정.'),
  fk('ORIGINAL_TAX_INVOICE_ID','당초 세금계산서 식별 번호','Original Tax Invoice Identifier','PAY_TAX_INVOICE','Y','','수정 세금계산서만.'),
  cd('TAX_INVOICE_AMENDMENT_REASON_CD','수정 사유 코드','Amendment Reason Code','Y','수정만. [확인 필요: 세무, 부가가치세법 시행령 70조 사유 목록]',30),
 ]),
 ('발급 상태', [
  cd('TAX_INVOICE_STATUS_CD','세금계산서 처리 상태 코드','Tax Invoice Status Code'),
  ('WRITE_DT','작성 일자','Write Date','DATE','N','','','출고일 기준 (6-5 A). [확인 필요: 세무, 공급 시기]'),
  ('ISSUE_DUE_DT','발급 기한 일자','Issue Due Date','DATE','Y','','','공급 시기가 속한 달의 다음 달 10일 [확인 필요: 세무].'),
  ('NTS_APPROVAL_NO','국세청 승인번호','National Tax Service Approval Number','VARCHAR2(30)','Y','','UK (NULL 제외)',''),
  ('ISSUED_AT','발급 일시','Issued At',TS,'Y','','',''),
  ('NTS_TRANSMITTED_AT','국세청 전송 일시','NTS Transmitted At',TS,'Y','','',''),
  ('ISSUING_VENDOR_CD','발행 대행 업체 코드','Issuing Vendor Code',PG,'Y','','','외부 업체 마스터 코드.'),
  ('VENDOR_RESULT_CD','발행 업체 결과 코드 (원래 값)','Issuing Vendor Result Code (Raw)','VARCHAR2(50)','Y','','',''),
 ]),
 ('금액', [
  ('REPRESENTATIVE_ITEM_NM','대표 품목명','Representative Item Name','VARCHAR2(200)','N','','','"대표 품목명 외 N건"으로 표시. 품목 줄은 저장하지 않는다 (6-5 A).'),
  ('ITEM_CNT','품목 수','Item Count','NUMBER(5)','N','1','CK (>= 1)',''),
  amt('SUPPLY_AMT','공급가액','Supply Amount',ck='CK (부호: 당초 > 0)',d='',desc='수정은 음수일 수 있다.'),
  amt('VAT_AMT','세액','Tax Amount',ck='',d=''),
  amt('TOTAL_AMT','합계 금액','Total Amount',ck='',d=''),
 ]),
 ('받는 자', [
  ('BUYER_BUSINESS_REGISTRATION_NO','받는 자 사업자등록번호','Buyer Business Registration Number','VARCHAR2(10)','N','','IX','공개 정보라 평문 + TDE (8-3 B). [확인 필요: 법무, 개인사업자 번호의 개인정보 해당 여부]'),
  ('BUYER_COMPANY_NM','받는 자 상호','Buyer Company Name','VARCHAR2(200)','N','','',''),
  ('BUYER_REPRESENTATIVE_NM','받는 자 대표자 이름','Buyer Representative Name','VARCHAR2(150)','Y','','','파기 대상 (8-6 A).'),
  ('BUYER_ADDR','받는 자 사업장 주소','Buyer Business Address','VARCHAR2(500)','Y','','',''),
  ('BUYER_BUSINESS_TYPE_VAL','받는 자 업태','Buyer Business Type','VARCHAR2(100)','Y','','',''),
  ('BUYER_BUSINESS_ITEM_VAL','받는 자 종목','Buyer Business Item','VARCHAR2(100)','Y','','',''),
  ('BUYER_EMAIL_ENC','받는 자 이메일 암호문','Buyer Email Ciphertext','RAW(349)','Y','','','이메일은 암호화 대상 (선행 5). 파기 대상.'),
 ]),
 ],
 idx=['UK `UK_PAY_TAX_INVOICE_ORDER_ID_TAX_INVOICE_SN` LOCAL', 'IX `IX_PAY_TAX_INVOICE_BUYER_BUSINESS_REGISTRATION_NO` (B2B 응대 검색)', 'IX 기한 감시 (함수 기반: 발급 전 행만 `ISSUE_DUE_DT`, 7-6 B)', 'IX `IX_PAY_TAX_INVOICE_PII_RETENTION_END_DT`'],
 check=['수정이면 `ORIGINAL_TAX_INVOICE_ID`, `TAX_INVOICE_AMENDMENT_REASON_CD` NOT NULL, 당초면 둘 다 NULL', '`SUPPLY_AMT + VAT_AMT = TOTAL_AMT`',
        '세금계산서를 요청한 주문의 결제 수단은 가상계좌·계좌이체만 (6-6 A, 테이블이 달라 애플리케이션이 주문 행을 잠그고 검사)'])

# =========================================================== 4. 분쟁
table(t='PAY_CHARGEBACK', ko='차지백 사건', en='Chargeback Case',
 desc='카드사 이의 제기 1건당 1행 (결제 1 : 사건 N). 인용되면 결제 취소 행(사유 `CHARGEBACK`)을 만들어 잔액을 줄인다 (9-3 A).',
 basis='9-3 A, 9-5 A, 여신전문금융업법 16조', pk='대리 PK `SEQ_PAY_CHARGEBACK`', cache=20,
 delete='삭제하지 않음 (사건). 결제와 함께 파티션 제거', part='`PAY_PAYMENT` 참조 파티션 (11-1 A)', keep='결제와 같음',
 cols=[
 ('식별', [
  ('CHARGEBACK_ID','차지백 사건 고유 식별 번호','Chargeback Case Unique Identifier',ID,'N','','PK',''),
  fk('PAYMENT_ID','대상 결제 식별 번호','Disputed Payment Identifier','PAY_PAYMENT','N','','참조 파티션 키.'),
  ('PG_CASE_NO','PG 사건번호','PG Case Number','VARCHAR2(50)','Y','','',''),
 ]),
 ('이의·결과', [
  cd('CHARGEBACK_REASON_CD','이의 사유 코드','Chargeback Reason Code',n=30),
  amt('DISPUTED_AMT','이의 금액','Disputed Amount',ck='CK (> 0)',d='',desc='부분 이의 가능.'),
  cd('CHARGEBACK_RESULT_CD','차지백 결과 코드','Chargeback Result Code'),
  amt('RECOVERED_AMT','회수 금액','Recovered Amount',desc='인용·일부 인용일 때. 정산 차감은 정산 도메인.'),
  ('RECEIVED_AT','접수 일시','Received At',TS,'N','','',''),
  ('RESPONSE_DUE_AT','소명 기한 일시','Response Due At',TS,'Y','','','감시 대상 (7-6 B).'),
  ('RESPONSE_SUBMITTED_AT','소명 제출 일시 (최초)','First Response Submitted At',TS,'Y','','','차수별 제출은 소명 파일 행 (PYC-5 A).'),
  ('RESULT_AT','결과 일시','Result At',TS,'Y','','',''),
 ]),
 ('담당', [
  fk('HANDLER_ADMIN_USER_ID','담당 관리자 식별 번호','Handler Administrator Identifier','ADM_USER','Y','','PK 이름은 관리자 도메인에서 확정.'),
  ('MEMO_CN','처리 메모','Handling Memo','VARCHAR2(4000)','Y','','',''),
 ]),
 ],
 idx=['IX `IX_PAY_CHARGEBACK_PAYMENT_ID` (FK, LOCAL)', 'IX 소명 기한 (함수 기반: 결과 `IN_PROGRESS`인 행만 `RESPONSE_DUE_AT`, 9-3 A)', 'IX `IX_PAY_CHARGEBACK_HANDLER_ADMIN_USER_ID` (FK)'],
 check=['결과가 인용·일부 인용이면 `RECOVERED_AMT` > 0이고 `RESULT_AT` NOT NULL', '`RECOVERED_AMT <= DISPUTED_AMT`'])

table(t='PAY_CHARGEBACK_EVIDENCE_FILE', ko='차지백 소명 자료 파일', en='Chargeback Evidence File',
 desc='차지백 소명 때 PG에 낸 파일 1개당 1행 (사건 1 : 파일 N). 파일은 저장소에 두고 메타데이터만 둔다 (PYC-5 A).',
 basis='9-3 A, PYC-5 A, 선행 6', pk='대리 PK `SEQ_PAY_CHARGEBACK_EVIDENCE_FILE`', cache=20,
 delete='개인정보 기한에 파일을 지우고 경로를 NULL. 행은 차지백과 함께 파티션 제거', part='`PAY_CHARGEBACK` 참조 파티션 (11-1 A 체인)',
 keep='개인정보: 결제 행 파기 예정일과 같음', pii=True,
 cols=[
 ('식별', [
  ('CHARGEBACK_EVIDENCE_FILE_ID','차지백 소명 파일 고유 식별 번호','Chargeback Evidence File Unique Identifier',ID,'N','','PK',''),
  fk('CHARGEBACK_ID','차지백 사건 식별 번호','Chargeback Case Identifier','PAY_CHARGEBACK','N','','참조 파티션 키.'),
  ('SUBMISSION_SN','제출 차수','Submission Sequence','NUMBER(2)','N','1','CK (>= 1)','보완 제출이면 2 이상.'),
  cd('EVIDENCE_FILE_TYPE_CD','소명 파일 종류 코드','Evidence File Type Code'),
 ]),
 ('파일', [
  ('EVIDENCE_FILE_URL','소명 파일 저장 경로','Evidence File Storage Path','VARCHAR2(500)','Y','','','파기하면 NULL.'),
  ('ORIGINAL_FILE_NM','원본 파일명','Original File Name','VARCHAR2(255)','Y','','',''),
  ('EVIDENCE_FILE_SIZE_VAL','파일 크기 (바이트)','File Size in Bytes','NUMBER(10)','Y','','',''),
  ('EVIDENCE_FILE_HASH','파일 해시 (SHA-256)','File Hash (SHA-256)','RAW(32)','N','','','제출한 파일이 바뀌지 않았음을 보이는 값.'),
  ('SUBMITTED_AT','제출 일시','Submitted At',TS,'N','','',''),
 ]),
 ],
 idx=['IX `IX_PAY_CHARGEBACK_EVIDENCE_FILE_CHARGEBACK_ID` (FK, LOCAL)', 'IX `IX_PAY_CHARGEBACK_EVIDENCE_FILE_PII_RETENTION_END_DT`'])

# =========================================================== 5. 설정
table(t='PAY_PAYMENT_METHOD_PG_SETTING', ko='결제 수단별 PG 설정', en='Payment Method PG Routing Setting',
 desc='결제 수단(간편결제는 제공사까지)마다 쓸 PG와 MID, 우선순위, 적용 기간. 장애 때 관리자가 바꾼다 (1-5 A, 7-5 A).',
 basis='1-5 A, 2-6 A, 7-5 A, 여신전문금융업법 19조 5항·7항', pk='대리 PK `SEQ_PAY_PAYMENT_METHOD_PG_SETTING`', cache=20,
 delete='논리 삭제 (설정)', part='없음', keep='논리 삭제 뒤 1년', ldel=True,
 cols=[
 ('식별', [
  ('PAYMENT_METHOD_PG_SETTING_ID','결제 수단별 PG 설정 고유 식별 번호','Payment Method PG Setting Unique Identifier',ID,'N','','PK',''),
  cd('PAYMENT_METHOD_CD','결제 수단 코드','Payment Method Code'),
  cd('EASY_PAY_PROVIDER_CD','간편결제사 코드','Easy Pay Provider Code','Y','수단이 간편결제일 때만.'),
  pgcd(),
 ]),
 ('라우팅', [
  ('PG_MID_VAL','PG 상점 아이디 (MID)','PG Merchant Identifier (MID)','VARCHAR2(50)','N','','','이 회사 명의만 (19조 5항).'),
  cd('MID_PURPOSE_CD','MID 용도 코드','MID Purpose Code'),
  ('PRIORITY_SN','우선순위','Priority','NUMBER(3)','N','1','CK (>= 1)','같은 수단에서 작은 값이 먼저.'),
  yn('USE_YN','사용 여부','Use Flag','Y','장애 때 끔 (7-5 A).'),
  ('EFFECTIVE_START_AT','적용 시작 일시','Effective Start At',TS,'N','','',''),
  ('EFFECTIVE_END_AT','적용 종료 일시','Effective End At',TS,'Y','','','NULL이면 계속.'),
  ('MERCHANT_DISPLAY_NM','카드 명세서 표시 가맹점명','Merchant Name Shown on Card Statement','VARCHAR2(100)','Y','','','PG 계약 정보. CS용 (19조 7항).'),
  ('CHANGE_REASON_CN','변경 사유','Change Reason','VARCHAR2(500)','Y','','','관리자 작업 로그에도 남는다.'),
 ]),
 ],
 idx=['IX (`PAYMENT_METHOD_CD`, `EASY_PAY_PROVIDER_CD`, `PRIORITY_SN`) (삭제되지 않고 사용 중인 행 조회)'],
 check=['`EFFECTIVE_END_AT` IS NULL OR `EFFECTIVE_END_AT` > `EFFECTIVE_START_AT`', '`PAYMENT_METHOD_CD` = `EASY_PAY` ⇔ `EASY_PAY_PROVIDER_CD` NOT NULL'])

table(t='PAY_CARD_MERCHANT_CONTRACT', ko='카드사 가맹점 계약', en='Card Issuer Merchant Contract',
 desc='카드사마다 직가맹인지(정산 방식), 가맹점번호, 적용 기간. 승인 응답의 카드사로 찾아 결제 행에 복사한다 (PYC-1 B).',
 basis='1-7 C, PYC-1 B', pk='대리 PK `SEQ_PAY_CARD_MERCHANT_CONTRACT`', cache=20,
 delete='논리 삭제 (설정)', part='없음', keep='논리 삭제 뒤 1년', ldel=True,
 cols=[
 ('식별', [
  ('CARD_MERCHANT_CONTRACT_ID','카드사 가맹점 계약 고유 식별 번호','Card Merchant Contract Unique Identifier',ID,'N','','PK',''),
  cd('CARD_COMPANY_CD','카드 발급사 코드','Card Issuer Code',desc='외부 업체 마스터 FK는 [확인 필요: 컬럼 검토 질문, 2-6].'),
 ]),
 ('계약', [
  cd('SETTLEMENT_METHOD_CD','정산 방식 코드','Settlement Method Code'),
  ('CARD_MERCHANT_NO','카드사 가맹점번호','Card Issuer Merchant Number','VARCHAR2(20)','Y','','','직가맹이면 NOT NULL.'),
  ('EFFECTIVE_START_AT','적용 시작 일시','Effective Start At',TS,'N','','',''),
  ('EFFECTIVE_END_AT','적용 종료 일시','Effective End At',TS,'Y','','',''),
  yn('USE_YN','사용 여부','Use Flag','Y',''),
  ('MEMO_CN','메모','Memo','VARCHAR2(1000)','Y','','',''),
 ]),
 ],
 idx=['IX (`CARD_COMPANY_CD`, `EFFECTIVE_START_AT`)'],
 check=['`SETTLEMENT_METHOD_CD` = `CARD_DIRECT` ⇔ `CARD_MERCHANT_NO` NOT NULL', '같은 카드사의 적용 기간은 겹치지 않음 (애플리케이션 검사)'])

table(t='PAY_PG_CODE_MAPPING', ko='PG 코드 대응', en='PG Code Mapping',
 desc='PG마다 다른 카드사·은행·통신사·간편결제사 코드를 우리 표준 코드로 바꾸는 표. 받는 방향은 (PG, 그룹, PG 코드)로, 보내는 방향은 보낼 때 쓰는 값으로 하나로 정한다 (PYC-2 B).',
 basis='2-4 A, PYC-2 B', pk='대리 PK `SEQ_PAY_PG_CODE_MAPPING`', cache=20,
 delete='논리 삭제 (설정)', part='없음', keep='논리 삭제 뒤 1년', ldel=True,
 cols=[
 ('식별', [
  ('PG_CODE_MAPPING_ID','PG 코드 대응 고유 식별 번호','PG Code Mapping Unique Identifier',ID,'N','','PK',''),
  pgcd(),
  cd('PG_CODE_GROUP_CD','대응 코드 그룹 코드','Mapped Code Group Code'),
  ('PG_CODE_VAL','PG 쪽 코드 값','PG-Side Code Value','VARCHAR2(20)','N','','',''),
 ]),
 ('대응', [
  ('STANDARD_CODE_VAL','우리 표준 코드 값','Standard Code Value','VARCHAR2(30)','N','','','그룹에 맞는 `CMM_CODE` 값.'),
  yn('OUTBOUND_USE_YN','보낼 때 쓰는 값 여부','Outbound Use Flag','Y','같은 (PG, 그룹, 표준 코드)에서 하나만 Y.'),
  yn('USE_YN','사용 여부','Use Flag','Y',''),
 ]),
 ],
 idx=['UK (`PG_CD`, `PG_CODE_GROUP_CD`, `PG_CODE_VAL`) (함수 기반: 삭제되지 않은 행만)',
      'UK 보내는 방향 (함수 기반: `OUTBOUND_USE_YN` = Y이고 삭제되지 않은 행만 (`PG_CD`, `PG_CODE_GROUP_CD`, `STANDARD_CODE_VAL`))'])

# =========================================================== 6. 연동·대사·감시
table(t='PAY_PG_API_LOG', ko='PG 호출 요약 로그', en='PG API Call Summary Log',
 desc='우리가 PG API를 부른 1회당 1행. 원문은 두지 않고 외부 로그 도구 추적 값으로 찾아간다 (7-1 C). 결제·취소 ID는 FK 없이 둔다.',
 basis='7-1 C, 7-6 B, 8-4 A, 11-2 A, PYC-3 A', pk='대리 PK `SEQ_PAY_PG_API_LOG`', cache=100,
 delete='삭제하지 않음 (로그). 파티션 단위로 제거 (선행 4)', part='`REQUESTED_AT` 월 단위 INTERVAL 파티션', keep='12개월 (정책값, 11-2 A)',
 cols=[
 ('식별', [
  ('PG_API_LOG_ID','PG 호출 로그 고유 식별 번호','PG API Log Unique Identifier',ID,'N','','PK',''),
  pgcd(),
  cd('PG_API_TYPE_CD','PG API 종류 코드','PG API Type Code',n=30),
 ]),
 ('결과', [
  cd('API_CALL_RESULT_CD','호출 결과 코드','API Call Result Code'),
  ('PG_RESULT_CD','PG 결과 코드 (PG 원래 값)','PG Result Code (Raw)','VARCHAR2(50)','Y','','',''),
  ('PG_RESULT_MESSAGE_CN','PG 결과 메시지','PG Result Message','VARCHAR2(1000)','Y','','',''),
  ('HTTP_STATUS_VAL','HTTP 상태 값','HTTP Status Value','NUMBER(3)','Y','','','시간 초과면 NULL.'),
  ('REQUESTED_AT','요청 일시','Requested At',TS,'N','','','파티션 키.'),
  ('RESPONDED_AT','응답 일시','Responded At',TS,'Y','','',''),
  ('ELAPSED_MILLISECOND_CNT','소요 시간 (밀리초)','Elapsed Milliseconds','NUMBER(10)','Y','','CK (>= 0)',''),
 ]),
 ('대상', [
  ref('PAYMENT_ID','관련 결제 식별 번호','Related Payment Identifier'),
  ref('PAYMENT_CANCEL_ID','관련 결제 취소 식별 번호','Related Payment Cancellation Identifier'),
  ref('CASH_RECEIPT_ID','관련 현금영수증 발급 식별 번호','Related Cash Receipt Identifier'),
  ('REQUEST_BUSINESS_NO_VAL','요청 업무 번호','Request Business Number','VARCHAR2(30)','Y','','IX','결제번호나 취소번호.'),
 ]),
 ('원문 추적', [
  ('EXTERNAL_LOG_TRACE_VAL','외부 로그 추적 값','External Log Trace Value','VARCHAR2(100)','Y','','','외부 로그 도구에서 원문을 찾는 키 (7-1 C).'),
  ('MASKING_RULE_VER','적용 허용 목록 버전','Applied Masking Allow-List Version','VARCHAR2(30)','Y','','','[확인 필요: 컬럼 검토 질문, PYC-3 후속]'),
 ]),
 ],
 idx=['IX LOCAL: `PAYMENT_ID`, `PAYMENT_CANCEL_ID`, `REQUEST_BUSINESS_NO_VAL`, (`PG_CD`, `REQUESTED_AT`) (성능 집계, 7-6 B)'])

table(t='PAY_PG_WEBHOOK_INBOX', ko='PG 웹훅 수신함', en='PG Webhook Inbox',
 desc='PG 웹훅 1건당 1행. 받으면 먼저 저장(커밋)하고 응답한 뒤, 처리기가 PG에 조회해 반영한다 (7-2 A, 3-5 C).',
 basis='3-5 C, 7-2 A, 11-2 A', pk='대리 PK `SEQ_PAY_PG_WEBHOOK_INBOX`', cache=100,
 delete='삭제하지 않음 (로그). 파티션 단위로 제거. 미처리 행이 있으면 제거를 미루고 알린다 (11-2 A)', part='`RECEIVED_AT` 월 단위 INTERVAL 파티션', keep='12개월 (정책값)',
 cols=[
 ('식별', [
  ('PG_WEBHOOK_INBOX_ID','웹훅 수신 고유 식별 번호','PG Webhook Inbox Unique Identifier',ID,'N','','PK',''),
  pgcd(),
  ('DEDUPLICATION_KEY_VAL','중복 방지 키','Deduplication Key','VARCHAR2(200)','N','','UK1','PG 이벤트 ID, 없으면 (PG, 종류, 거래번호, 상태, PG 시각)의 해시 (7-2 A).'),
  ('WEBHOOK_EVENT_TYPE_VAL','웹훅 이벤트 종류 (PG 원래 값)','Webhook Event Type (Raw)','VARCHAR2(50)','N','','',''),
  ('RECEIVED_AT','수신 일시','Received At',TS,'N','SYSTIMESTAMP','','파티션 키.'),
 ]),
 ('처리', [
  cd('WEBHOOK_PROCESSING_STATUS_CD','웹훅 처리 상태 코드','Webhook Processing Status Code'),
  cd('SIGNATURE_VERIFICATION_RESULT_CD','서명 검증 결과 코드','Signature Verification Result Code'),
  ('PROCESSED_AT','처리 일시','Processed At',TS,'Y','','',''),
  ('RETRY_CNT','처리 재시도 횟수','Processing Retry Count','NUMBER(3)','N','0','CK (>= 0)',''),
  ('NEXT_RETRY_AT','다음 처리 예정 일시','Next Processing Scheduled At',TS,'Y','','',''),
 ]),
 ('대상', [
  ('PAYMENT_NO','웹훅에 실린 결제번호','Payment Number in Webhook','VARCHAR2(18)','Y','','',''),
  ('PG_TRANSACTION_NO','웹훅에 실린 PG 거래번호','PG Transaction Number in Webhook','VARCHAR2(200)','Y','','',''),
  ref('MATCHED_PAYMENT_ID','찾은 결제 식별 번호','Matched Payment Identifier'),
  ('SENDER_IP','발신 IP 주소','Sender IP Address','VARCHAR2(45)','Y','','','서명 불일치 반복 감시 (7-2 A, 7-6 B).'),
  ('EXTERNAL_LOG_TRACE_VAL','외부 로그 추적 값','External Log Trace Value','VARCHAR2(100)','Y','','','원문은 외부 로그 도구.'),
 ]),
 ],
 idx=['UK `UK_PAY_PG_WEBHOOK_INBOX_DEDUPLICATION` (`PG_CD`, `DEDUPLICATION_KEY_VAL`) GLOBAL. 파티션 제거 때 `UPDATE GLOBAL INDEXES` (11-2 A)',
      'IX 처리 대상 (함수 기반: 상태 `RECEIVED`·`INQUIRY_FAILED`인 행만 `NEXT_RETRY_AT`)', 'IX LOCAL: `MATCHED_PAYMENT_ID`'])

table(t='PAY_RECONCILIATION_RUN', ko='대사 실행', en='Reconciliation Run',
 desc='대상(PG / 적립금 / 예치금) × 업체 × 거래일 × 차수당 1행. 배치 실행 이력(`BAT`)과 별개의 업무 기록이다 (7-3 B, 7-4 A).',
 basis='1-6 A, 7-3 B, 7-4 A, 11-2 A', pk='대리 PK `SEQ_PAY_RECONCILIATION_RUN`', cache=20,
 delete='실행 일자 + 5년(정책값) 뒤 불일치 행과 함께 나눠서 DELETE (11-2 A)', part='없음', keep='5년',
 cols=[
 ('식별', [
  ('RECONCILIATION_RUN_ID','대사 실행 고유 식별 번호','Reconciliation Run Unique Identifier',ID,'N','','PK',''),
  cd('RECONCILIATION_TARGET_CD','대사 대상 코드','Reconciliation Target Code',desc='7-4 A.'),
  pgcd(null='Y',desc='대상이 PG일 때만.'),
  ('TRANSACTION_DT','대사 거래 일자','Reconciled Transaction Date','DATE','N','','UK1',''),
  ('RUN_SN','실행 차수','Run Sequence','NUMBER(3)','N','1','UK1','같은 날을 다시 돌리면 증가.'),
 ]),
 ('실행', [
  cd('RECONCILIATION_RUN_STATUS_CD','대사 실행 상태 코드','Reconciliation Run Status Code'),
  ('STARTED_AT','시작 일시','Started At',TS,'N','','',''),
  ('FINISHED_AT','종료 일시','Finished At',TS,'Y','','',''),
  ('MISMATCH_CNT','불일치 건수','Mismatch Count','NUMBER(9)','N','0','CK (>= 0)',''),
 ]),
 ('원본 파일·합계', [
  ('SOURCE_FILE_NM','PG 거래 파일명','PG Transaction File Name','VARCHAR2(255)','Y','','','원본은 파일 보관소 (7-3 B).'),
  ('SOURCE_FILE_HASH','PG 거래 파일 해시 (SHA-256)','PG Transaction File Hash','RAW(32)','Y','','',''),
  ('OUR_TRANSACTION_CNT','우리 거래 건수','Our Transaction Count','NUMBER(9)','Y','','',''),
  ('PG_TRANSACTION_CNT','PG 거래 건수','PG Transaction Count','NUMBER(9)','Y','','',''),
  amt('OUR_APPROVED_TOTAL_AMT','우리 승인 합계','Our Approved Total Amount',null='Y',d='',ck=''),
  amt('OUR_CANCELED_TOTAL_AMT','우리 취소 합계','Our Canceled Total Amount',null='Y',d='',ck=''),
  amt('PG_APPROVED_TOTAL_AMT','PG 승인 합계','PG Approved Total Amount',null='Y',d='',ck=''),
  amt('PG_CANCELED_TOTAL_AMT','PG 취소 합계','PG Canceled Total Amount',null='Y',d='',ck=''),
 ]),
 ],
 idx=['UK `UK_PAY_RECONCILIATION_RUN_TARGET` (`RECONCILIATION_TARGET_CD`, `PG_CD`, `TRANSACTION_DT`, `RUN_SN`) (7-4 A)'],
 check=['`RECONCILIATION_TARGET_CD` = `PG` ⇔ `PG_CD` NOT NULL (7-4 A)'])

table(t='PAY_RECONCILIATION_MISMATCH', ko='대사 불일치', en='Reconciliation Mismatch',
 desc='대사에서 찾은 불일치 1건당 1행. 양쪽 값과 해결 상태·방법을 남긴다 (7-3 B, 7-4 A). 결제·회원·주문 ID는 FK 없이 둔다.',
 basis='5-7 A, 6-4 A, 6-8 A, 7-3 B, 7-4 A, 11-2 A, 12-5 C', pk='대리 PK `SEQ_PAY_RECONCILIATION_MISMATCH`', cache=20,
 delete='실행 행과 함께 나눠서 DELETE', part='없음', keep='5년',
 cols=[
 ('식별', [
  ('RECONCILIATION_MISMATCH_ID','대사 불일치 고유 식별 번호','Reconciliation Mismatch Unique Identifier',ID,'N','','PK',''),
  fk('RECONCILIATION_RUN_ID','대사 실행 식별 번호','Reconciliation Run Identifier','PAY_RECONCILIATION_RUN','N','IX',''),
  cd('MISMATCH_TYPE_CD','불일치 유형 코드','Mismatch Type Code',n=30),
 ]),
 ('해결', [
  cd('MISMATCH_RESOLUTION_STATUS_CD','불일치 해결 상태 코드','Mismatch Resolution Status Code'),
  cd('MISMATCH_RESOLUTION_METHOD_CD','불일치 해결 방법 코드','Mismatch Resolution Method Code','Y','',30),
  ('RESOLVED_AT','해결 일시','Resolved At',TS,'Y','','',''),
  fk('RESOLVER_ADMIN_USER_ID','해결 관리자 식별 번호','Resolver Administrator Identifier','ADM_USER','Y','','수동 해소만.'),
  ('RESOLUTION_MEMO_CN','해결 메모','Resolution Memo','VARCHAR2(2000)','Y','','',''),
 ]),
 ('대상', [
  ref('PAYMENT_ID','관련 결제 식별 번호','Related Payment Identifier'),
  ref('PAYMENT_CANCEL_ID','관련 결제 취소 식별 번호','Related Payment Cancellation Identifier'),
  ref('MEMBER_ID','관련 회원 식별 번호','Related Member Identifier',desc='적립금·예치금 대사 (7-4 A).'),
  ref('ORDER_ID','관련 주문 식별 번호','Related Order Identifier'),
  ('PG_TRANSACTION_NO','PG 거래번호','PG Transaction Number','VARCHAR2(200)','Y','','',''),
 ]),
 ('비교 값', [
  amt('OUR_AMT','우리 쪽 금액','Our Amount',null='Y',d='',ck=''),
  amt('COUNTERPART_AMT','상대 쪽 금액','Counterpart Amount',null='Y',d='',ck='',desc='PG 값, 또는 내부 대사의 비교 대상 값 (원장 합계 등).'),
  ('OUR_STATUS_VAL','우리 쪽 상태','Our Status','VARCHAR2(30)','Y','','',''),
  ('COUNTERPART_STATUS_VAL','상대 쪽 상태','Counterpart Status','VARCHAR2(30)','Y','','',''),
 ]),
 ],
 idx=['IX `IX_PAY_RECONCILIATION_MISMATCH_RECONCILIATION_RUN_ID` (FK)', 'IX 미해결 감시 (함수 기반: 미해결 행만 `CREATED_AT`, 7-3 B)', 'IX `PAYMENT_ID`, `MEMBER_ID`, `ORDER_ID`, `PG_TRANSACTION_NO`', 'IX `IX_PAY_RECONCILIATION_MISMATCH_RESOLVER_ADMIN_USER_ID` (FK)'],
 check=['해결 상태가 미해결이 아니면 `MISMATCH_RESOLUTION_METHOD_CD`, `RESOLVED_AT` NOT NULL', '`MANUALLY_RESOLVED`이면 `RESOLVER_ADMIN_USER_ID` NOT NULL'])

table(t='PAY_PG_INCIDENT', ko='PG 장애 기록', en='PG Incident Record',
 desc='PG 장애 1건당 1행. 감지는 자동, 전환은 사람이 하고 그 조치를 남긴다 (7-5 A). 영향 결제는 결제 행의 PG와 생성 일시로 조회한다.',
 basis='7-5 A', pk='대리 PK `SEQ_PAY_PG_INCIDENT`', cache=20,
 delete='논리 삭제', part='없음', keep='논리 삭제 뒤 1년', ldel=True,
 cols=[
 ('식별', [
  ('PG_INCIDENT_ID','PG 장애 고유 식별 번호','PG Incident Unique Identifier',ID,'N','','PK',''),
  pgcd(),
  cd('AFFECTED_PAYMENT_METHOD_CD','영향 결제 수단 코드','Affected Payment Method Code','Y','전체면 NULL.',ck='CK (`PAYMENT_METHOD_CD` 값 목록)'),
 ]),
 ('장애·조치', [
  ('STARTED_AT','장애 시작 일시','Incident Started At',TS,'N','','',''),
  ('ENDED_AT','장애 종료 일시','Incident Ended At',TS,'Y','','',''),
  cd('INCIDENT_DETECTION_METHOD_CD','장애 감지 방법 코드','Incident Detection Method Code'),
  cd('INCIDENT_ACTION_CD','장애 조치 코드','Incident Action Code'),
  fk('HANDLER_ADMIN_USER_ID','담당 관리자 식별 번호','Handler Administrator Identifier','ADM_USER','Y',''),
  ('MEMO_CN','메모','Memo','VARCHAR2(4000)','Y','','',''),
 ]),
 ],
 idx=['IX (`PG_CD`, `STARTED_AT`)', 'IX `IX_PAY_PG_INCIDENT_HANDLER_ADMIN_USER_ID` (FK)'],
 check=['`ENDED_AT` IS NULL OR `ENDED_AT` >= `STARTED_AT`'])

table(t='PAY_PG_METRIC_5MIN', ko='PG 성능 5분 집계', en='PG Performance 5-Minute Metric',
 desc='PG × 수단 × API 종류 × 5분당 1행. Oracle 스케줄러가 호출 로그에서 집계한다. 로그보다 오래 남겨 장기 비교에 쓴다 (7-6 B).',
 basis='7-6 B, 7-5 A, 선행 11', pk='복합 PK (`PG_CD`, `PAYMENT_METHOD_SCOPE_CD`, `PG_API_TYPE_CD`, `AGGREGATION_START_AT`)', cache='없음 (시퀀스 없음)',
 delete='삭제하지 않음 (집계). 파티션 단위로 제거', part='`AGGREGATION_START_AT` 월 단위 INTERVAL 파티션', keep='3년 (정책값)',
 cols=[
 ('식별', [
  pgcd(),
  cd('PAYMENT_METHOD_SCOPE_CD','집계 결제 수단 범위 코드','Aggregated Payment Method Scope Code',desc='결제 수단 6개 + 수단과 무관한 API용 `ALL`.'),
  cd('PG_API_TYPE_CD','PG API 종류 코드','PG API Type Code',n=30),
  ('AGGREGATION_START_AT','집계 시작 일시','Aggregation Start At',TS,'N','','PK','5분 단위.'),
 ]),
 ('지표', [
  ('CALL_CNT','호출 수','Call Count','NUMBER(9)','N','0','CK (>= 0)',''),
  ('SUCCESS_CNT','성공 수','Success Count','NUMBER(9)','N','0','CK (<= CALL_CNT)',''),
  ('TIMEOUT_CNT','시간 초과 수','Timeout Count','NUMBER(9)','N','0','CK (>= 0)',''),
  ('AVERAGE_ELAPSED_MILLISECOND_CNT','평균 응답 시간 (밀리초)','Average Elapsed Milliseconds','NUMBER(10)','Y','','',''),
  ('P95_ELAPSED_MILLISECOND_CNT','95 백분위 응답 시간 (밀리초)','95th Percentile Elapsed Milliseconds','NUMBER(10)','Y','','',''),
  ('FAILURE_CODE_COUNT_JSON','실패 코드별 건수','Failure Count by PG Result Code','JSON','Y','','','PG마다 코드가 달라 JSON 한 컬럼 (7-6 B).'),
 ]),
 ])

TABLE_GROUPS = [
 ('결제·환불', ['PAY_PAYMENT', 'PAY_REFUND_REQUEST', 'PAY_PAYMENT_CANCEL']),
 ('적립금·예치금', ['PAY_POINT_LEDGER', 'PAY_POINT_DEDUCTION', 'PAY_DEPOSIT_LEDGER', 'PAY_DEPOSIT_DEDUCTION', 'PAY_DEPOSIT_WITHDRAWAL_REQUEST']),
 ('증빙', ['PAY_CASH_RECEIPT', 'PAY_TAX_INVOICE']),
 ('분쟁', ['PAY_CHARGEBACK', 'PAY_CHARGEBACK_EVIDENCE_FILE']),
 ('설정', ['PAY_PAYMENT_METHOD_PG_SETTING', 'PAY_CARD_MERCHANT_CONTRACT', 'PAY_PG_CODE_MAPPING']),
 ('연동·대사·감시', ['PAY_PG_API_LOG', 'PAY_PG_WEBHOOK_INBOX', 'PAY_RECONCILIATION_RUN', 'PAY_RECONCILIATION_MISMATCH', 'PAY_PG_INCIDENT', 'PAY_PG_METRIC_5MIN']),
]

def vals(*v): return [(a, b, c, d, i) for i, (a, b, c, d) in enumerate(v, 1)]
METHOD = vals(('CARD','카드','Card','PG 결제창'),('ONE_CLICK','원클릭 (저장 카드)','One-Click Saved Card','빌링키 결제'),('EASY_PAY','간편결제','Easy Pay','제공사 코드 필수'),
              ('VIRTUAL_ACCOUNT','가상계좌','Virtual Account',''),('ACCOUNT_TRANSFER','계좌이체','Account Transfer',''),('MOBILE_PHONE','휴대폰 결제','Mobile Phone Payment','1-4 A'))
CARD_CO = vals(('SHINHAN','신한카드','Shinhan Card',''),('SAMSUNG','삼성카드','Samsung Card',''),('HYUNDAI','현대카드','Hyundai Card',''),('KB','KB국민카드','KB Kookmin Card',''),
               ('LOTTE','롯데카드','Lotte Card',''),('HANA','하나카드','Hana Card',''),('WOORI','우리카드','Woori Card',''),('BC','비씨카드','BC Card',''),('NH','NH농협카드','NH Nonghyup Card',''),
               ('OTHER','기타 (해외 등)','Other','[확인 필요: 계약 PG]'))
API = vals(('AUTHENTICATE','인증','Authenticate',''),('APPROVE','승인','Approve',''),('BILLING_APPROVE','빌링 승인','Billing Approve','원클릭'),('INQUIRY','조회','Inquiry','3-5 C, 3-7 A'),
           ('CANCEL','취소','Cancel',''),('VIRTUAL_ACCOUNT_ISSUE','가상계좌 발급','Virtual Account Issue',''),('CASH_RECEIPT_ISSUE','현금영수증 발급','Cash Receipt Issue',''),
           ('CASH_RECEIPT_CANCEL','현금영수증 취소','Cash Receipt Cancel',''),('ESCROW_SHIPMENT_REGISTER','에스크로 배송 등록','Escrow Shipment Register','6-9 A'),('BILLING_KEY_DELETE','빌링키 삭제','Billing Key Delete','회원 47-1 A'))
CONFIRM_ROUTE = vals(('SYNC_RESPONSE','동기 응답','Synchronous Response','우리가 승인 API(빌링 승인 포함)를 호출하고 바로 받은 응답으로 확정. 카드 승인·거절, PG 부정 결제 거절 등. 응답 시간이 넘어 결과 불명이 되면 이 값이 아니다 (3-5 C)'),
  ('BROWSER_RETURN','결제창 복귀','Browser Return','결제창이 실패 결과를 들고 브라우저를 실패 URL로 돌려보낸 것으로 확정. 고객 중단, 인증 실패, 카드사 거절. 고객이 조작할 수 있으므로 실패만 확정하고, 성공해서 돌아오면 승인 요청으로 이어져 동기 응답이 된다 (3-5 C, PYC-44 A)'),
  ('WEBHOOK','웹훅 뒤 조회','Webhook then Inquiry','웹훅을 받고 그 결제를 PG에 조회해 확정. 가상계좌 입금, 비동기 간편결제 결과 등. 웹훅 내용을 그대로 적용하지 않는다 (3-5 C, 7-2 A)'),
  ('RECONCILIATION_INQUIRY','대사 뒤 조회','Reconciliation then Inquiry','거래 대사가 찾은 건을 조회해 반영. 웹훅 유실, 상태 어긋남 등. 웹훅 유실 건을 센다 (7-3 B, PYC-28 A)'),
  ('PG_INQUIRY','PG 조회','PG Inquiry','우리가 PG에 조회해 확정. 결과 불명 조회 배치, 응답 시간 초과 뒤 바로 한 조회, 가상계좌 만료 전 조회, 이상 승인 확인 (3-7 A, 4-2 A)'),
  ('INTERNAL_DECISION','우리 판정','Internal Decision','PG를 부르지 않고 우리 규칙으로 끝냄: 금액 불일치, 부정 결제 차단, 한도 초과, 주문 만료, 승인 제한 시간, 새 시도로 대체 등. 실패·만료만 가능 (PYC-29 A, PYC-41 B, PYC-46 A)'),
  ('MANUAL','수동','Manual','운영자가 PG 문의 등으로 판단해 확정. 확정 사유와 예외 수동 처리(완료 일시, 처리 관리자)가 있어야 한다 (3-2 C, 3-7 A, PYC-48 A)'))
CODES = {
 'PAYMENT_PURPOSE_CD': vals(('ORDER','주문 결제','Order Payment','주문당 승인 1건 UK 대상 (2-2 C)'),('ADDITIONAL','추가 결제','Additional Payment','교환 배송비 등 (5-10 A)')),
 'PAYMENT_STATUS_CD': vals(('READY','준비 (미결제)','Ready (Unpaid)','PG 호출 전 (2-1 A). 업무 용어 병기 (PYC-31 A)'),('AUTHENTICATED','인증 완료 (미결제)','Authenticated (Unpaid)','3-3 A'),('WAITING_DEPOSIT','입금 대기 (미결제)','Waiting for Deposit (Unpaid)','가상계좌 (4-1 A)'),
   ('APPROVED','승인 (결제 완료)','Approved (Paid)','취소 여부는 취소 상태로 본다 (3-1 B)'),('FAILED','실패 (결제 실패)','Failed (Payment Failed)','끝 상태'),('UNKNOWN','결과 불명 (확인 중)','Unknown (Checking)','PG 조회로 확정 (3-7 A)'),('EXPIRED','만료 (결제 기한 경과)','Expired (Payment Deadline Passed)','끝 상태. 조회로 승인이 확인되면 승인으로 바꾼 뒤 자동 취소 (3-5 C, 3-8 A)')),
 'PAYMENT_DISPLAY_STATUS_CD': vals(('UNPAID','미결제','Unpaid','상태 준비·인증 완료·입금 대기'),('CHECKING','확인 중','Checking','상태 결과 불명'),('FAILED','결제 실패','Payment Failed','상태 실패'),
   ('EXPIRED','결제 기한 만료','Payment Expired','상태 만료. 환불이 없으므로 "취소"라고 부르지 않는다'),('CANCEL_PENDING','취소 처리 중','Cancellation Pending','승인이고 취소 처리 중 금액 > 0'),
   ('CANCELED','전체 취소','Fully Canceled','승인이고 PG 취소 누계 + PG 밖 환불 누계 = 승인 금액'),('PARTIALLY_CANCELED','부분 취소','Partially Canceled','승인이고 취소·환불 누계 > 0'),('PAID','결제 완료','Paid','그 밖의 승인')),
 'PAYMENT_CANCEL_STATUS_CD': vals(('NONE','취소 없음','None',''),('PARTIAL','부분 취소','Partially Canceled',''),('FULL','전액 취소','Fully Canceled','')),
 'PAYMENT_FAILURE_REASON_CD': vals(
   ('USER_ABORTED','고객 중단','User Aborted','고객이 결제창을 닫거나 결제를 그만둠 (PG가 중단 결과를 줌) · `ATTR1` FAILED · `ATTR2` CUSTOMER_ACTION'),
   ('PG_DECLINED','PG·카드사 거절','Declined','PG·카드사가 승인을 거절 (한도 초과, 잔액 부족, 정지 카드 등) · `ATTR1` FAILED · `ATTR2` PG_DECLINE'),
   ('AUTHENTICATION_FAILED','인증 실패','Authentication Failed','카드 비밀번호·본인 인증 실패 · `ATTR1` FAILED · `ATTR2` PG_DECLINE'),
   ('SAVED_CARD_INVALID','저장 카드 사용 불가','Saved Card Invalid','원클릭(빌링) 승인이 카드 해지·유효기간 만료로 거절됨. PG 실패 코드를 `PAY_PG_CODE_MAPPING`으로 바꿔 판단 (8-2 B, PYC-37 A) · `ATTR1` FAILED · `ATTR2` PG_DECLINE'),
   ('CARRIER_LIMIT_EXCEEDED','통신사 한도 초과','Carrier Limit Exceeded','휴대폰 결제가 통신사 한도를 넘어 거절됨 (9-4 A) · `ATTR1` FAILED · `ATTR2` PG_DECLINE'),
   ('AMOUNT_MISMATCH','금액 불일치','Amount Mismatch','인증 금액이 요청 금액과 달라 승인을 부르지 않음 (3-3 A) · `ATTR1` FAILED · `ATTR2` MERCHANT_RULE'),
   ('FDS_BLOCKED','부정 결제 차단','Fraud Blocked','우리 부정 결제 판정이 차단이라 PG를 부르지 않음 (9-1 A) · `ATTR1` FAILED · `ATTR2` MERCHANT_RULE'),
   ('ATTEMPT_LIMIT_EXCEEDED','시도 한도 초과','Attempt Limit Exceeded','주문당 시도 상한이나 회원·카드·IP별 실패 횟수 한도를 넘어 PG를 부르지 않음 (9-2 A) · `ATTR1` FAILED · `ATTR2` MERCHANT_RULE'),
   ('MINOR_LIMIT_EXCEEDED','미성년 월 한도 초과','Minor Monthly Limit Exceeded','미성년 회원의 그 달 사용액이 한도를 넘어 PG를 부르지 않음 (9-4 A) · `ATTR1` FAILED · `ATTR2` MERCHANT_RULE'),
   ('PAYMENT_METHOD_MISMATCH','조건 결제 수단 불일치','Payment Method Mismatch','결제 수단 조건 할인의 조건 수단과 실제 수단이 달라 승인하지 않음 (10-4 B) · `ATTR1` FAILED · `ATTR2` MERCHANT_RULE'),
   ('DUPLICATE_PAYMENT','이미 결제된 주문','Duplicate Payment','승인 전 검사에서 같은 주문의 진행 결제가 이미 있음 (2-2 C) · `ATTR1` FAILED · `ATTR2` MERCHANT_RULE'),
   ('DEPOSIT_DEADLINE_PASSED','입금 기한 경과','Deposit Deadline Passed','가상계좌 입금 기한이 지나 PG 조회로 입금이 없음을 확인 (4-2 A) · `ATTR1` EXPIRED · `ATTR2` DEADLINE'),
   ('APPROVAL_TIME_LIMIT_PASSED','승인 제한 시간 경과','Approval Time Limit Passed','인증 뒤 PG 승인 제한 시간이 지나 PG를 부르지 않고 만료 (PYC-17 B) · `ATTR1` EXPIRED · `ATTR2` DEADLINE'),
   ('ADDITIONAL_PAYMENT_TIMEOUT','추가 결제 미완료 만료','Additional Payment Timeout','생성 + 정책값 시간이 지난 추가 결제 행 (PYC-17 B) · `ATTR1` EXPIRED · `ATTR2` DEADLINE'),
   ('ORDER_EXPIRED','주문 만료','Order Expired','주문이 만료(기한 경과, 새 주문으로 대체)되어 결제 행도 함께 만료 (2-1 A, PYC-26 A) · `ATTR1` EXPIRED · `ATTR2` DEADLINE'),
   ('REPLACED_BY_NEW_ATTEMPT','새 시도로 대체','Replaced by New Attempt','같은 주문에 새 결제 행을 만들 때 준비·인증 완료 행을 만료. 입금 대기는 PG 발급 취소가 성공한 뒤 (가상계좌 은행 변경 포함, 4-1 A, PYC-34 A, PYC-35 A) · `ATTR1` EXPIRED · `ATTR2` REPLACEMENT'),
   ('ADDITIONAL_PAYMENT_CAUSE_WITHDRAWN','추가 결제 원인 철회','Additional Payment Cause Withdrawn','클레임 철회나 주문 변경 취소로 추가 결제가 필요 없어져 준비·인증 완료 행을 바로 만료 (5-10 A, PYC-38 A) · `ATTR1` EXPIRED · `ATTR2` REPLACEMENT'),
   ('PG_ERROR','PG 오류','PG Error','PG 장애·오류 응답 (응답이 아예 없으면 실패가 아니라 결과 불명) · `ATTR1` FAILED · `ATTR2` ERROR_OTHER'),
   ('OTHER','기타','Other','다른 값에 맞지 않음. 세부 원인은 PG 실패 코드·메시지에 남김. 비율을 감시해 반복되면 새 값으로 올림 (PYC-43 A) · `ATTR1` ALL · `ATTR2` ERROR_OTHER')),
 'MANUAL_CHECK_REASON_CD': vals(
   ('DEPOSIT_CORRECTION','은행 입금 정정','Bank Deposit Correction','승인된 가상계좌 입금을 은행이 정정·취소함. 돈 없이 결제 완료된 주문이 출고될 수 있어 가장 급하다. 운영자는 주문 출고를 막고 PG와 입금 사실을 확인한다 (4-2 A) · `ATTR2` MONEY_RISK'),
   ('DEPOSIT_AMOUNT_MISMATCH','설정과 다른 입금 금액','Deposit Amount Mismatch','가상계좌에 설정과 다른 금액이 들어와 승인으로 바꾸지 않음. 운영자는 고객에게 환불 계좌를 받아 돌려주고 다시 결제를 안내한다 (4-3 A) · `ATTR2` MONEY_RISK'),
   ('INQUIRY_LIMIT_EXCEEDED','조회 한도 초과','Inquiry Limit Exceeded','결과 불명을 최대 횟수까지 조회해도 확정되지 않음. 운영자는 PG에 문의해 수동 확정한다 (3-7 A, PYC-48 A) · `ATTR2` STATUS_UNCERTAIN'),
   ('STATUS_MISMATCH','PG 상태 불일치','PG Status Mismatch','`PG_PAYMENT_STATUS_VAL`과 우리 상태가 어긋남. 운영자는 PG에 다시 조회해 반영하거나 취소를 들여온다 (PYC-16 A) · `ATTR2` STATUS_UNCERTAIN'),
   ('PG_CODE_UNMAPPED','PG 코드 대응 없음','PG Code Unmapped','PG 결제 상태나 실패 코드가 PG 코드 대응 테이블에 없어 처리하지 못함. 운영자는 대응을 더한 뒤 같은 코드로 걸린 행을 다시 처리한다 (PYC-2 B, PYC-55 A) · `ATTR2` STATUS_UNCERTAIN'),
   ('PG_CONSOLE_CANCEL_CHECK_FAILED','PG 관리자 화면 취소 들여오기 CHECK 위반','PG Console Cancel Import Check Failed','대사가 찾은 PG 관리자 화면 취소를 취소 행으로 들여오다 CHECK에 걸림(잔액 초과 등). 운영자는 금액을 맞춰 들여오거나 PG 쪽을 바로잡는다 (5-7 A) · `ATTR2` EXTERNAL_SYNC'),
   ('ESCROW_REGISTRATION_FAILED','에스크로 배송 등록 실패','Escrow Delivery Registration Failed','결제대금예치 배송 등록 재시도가 정책값 횟수를 넘음. 등록하지 않으면 구매 확정과 정산이 막힌다. 운영자는 송장을 확인해 PG에 직접 등록한다 (6-9 A, PYC-53 A) · `ATTR2` EXTERNAL_SYNC'),
   ('CUSTOMER_INQUIRY','고객 문의','Customer Inquiry','고객센터 문의(예: 돈은 빠졌는데 주문이 안 됨)로 운영자가 결제 행을 확인·수동 확정함 (PYC-48 A, PYC-54 A) · `ATTR2` INQUIRY_OTHER'),
   ('OTHER','기타','Other','다른 값에 맞지 않음. 내용은 수동 확정 사유나 관리자 작업 로그에 남긴다. 늘면 새 값으로 올린다 (PYC-43 A와 같은 기준) · `ATTR2` INQUIRY_OTHER')),
 'CANCEL_MANUAL_CHECK_REASON_CD': vals(('RETRY_LIMIT_EXCEEDED','재시도 한도 초과','Retry Limit Exceeded','5-9 A'),('REFUND_DUE_APPROACHING','환급 기한 임박','Refund Due Approaching','환불 계좌를 받지 못함 (4-4 A)'),('OTHER','기타','Other','')),
 'RESULT_CONFIRM_ROUTE_CD': CONFIRM_ROUTE,
 'ABNORMAL_PREV_CONFIRM_ROUTE_CD': CONFIRM_ROUTE,
 'PAYMENT_METHOD_CD': METHOD,
 'PAYMENT_METHOD_SCOPE_CD': vals(*[(v[0], v[1], v[2], v[3]) for v in METHOD], ('ALL','전체 (수단 무관)','All','현금영수증 발급 등')),
 'EASY_PAY_PROVIDER_CD': vals(('NAVER_PAY','네이버페이','Naver Pay',''),('KAKAO_PAY','카카오페이','Kakao Pay',''),('TOSS_PAY','토스페이','Toss Pay',''),('PAYCO','페이코','PAYCO',''),('SAMSUNG_PAY','삼성페이','Samsung Pay','[확인 필요: 계약]'),('APPLE_PAY','애플페이','Apple Pay','PG가 카드로 돌려주면 수단은 `CARD`로 두고 이 값은 PG가 알려 줄 때만 (2-5 A, PYC-64 A) [확인 필요: 계약 PG 지원]')),
 'PAYMENT_WINDOW_TYPE_CD': vals(('PG_INTEGRATED','PG 통합 결제창','PG Integrated Window','PG 창에서 수단을 고름. 가상계좌·계좌이체·휴대폰 결제 포함'),('DIRECT_CARD','카드사 바로 호출','Direct Card Issuer Call','주문서의 카드사 버튼으로 카드사 결제 앱을 바로 엶. 수단 `CARD`'),
   ('DIRECT_EASY_PAY','간편결제 바로 호출','Direct Easy Pay Call','주문서의 간편결제사 버튼으로 바로 엶. 수단 `EASY_PAY`'),('BILLING','빌링 (창 없음)','Billing (No Window)','원클릭. 저장한 빌링키로 서버가 승인 (8-2 B)')),
 'EASY_PAY_INNER_METHOD_CD': vals(('CARD','카드','Card',''),('MONEY','머니 (충전금)','Stored Money','현금성'),('POINT','포인트','Point',''),('ACCOUNT','계좌','Bank Account','현금성'),('MIXED','혼합','Mixed','카드 + 현금성')),
 'MID_PURPOSE_CD': vals(('GENERAL','일반','General',''),('BILLING','빌링','Billing','원클릭')),
 'SETTLEMENT_METHOD_CD': vals(('PG_SETTLEMENT','PG 정산 (하위가맹)','PG Settlement',''),('CARD_DIRECT','카드사 직정산 (직가맹)','Card Issuer Direct','가맹점번호 필수 (1-7 C)')),
 'CARD_COMPANY_CD': CARD_CO, 'CARD_ACQUIRER_CD': CARD_CO,
 'CARD_OWNER_TYPE_CD': vals(('PERSONAL','개인','Personal',''),('CORPORATE','법인','Corporate',''),('UNKNOWN','미확인','Unknown','PG가 구분하지 못함')),
 'CANCEL_TIME_CARD_ACQUIRE_STATUS_CD': vals(('READY','매입 전','Not Yet Acquired','승인 취소. 바로 사라짐'),('REQUESTED','매입 요청','Acquisition Requested',''),('COMPLETED','매입 완료','Acquired','카드사 환불. 며칠 걸림'),('CANCEL_REQUESTED','매입 취소 요청','Acquisition Cancel Requested',''),('CANCELED','매입 취소','Acquisition Canceled','')),
 'CARD_TYPE_CD': vals(('CREDIT','신용','Credit',''),('CHECK','체크','Check (Debit)',''),('GIFT','기프트','Gift','')),
 'INTEREST_FREE_TYPE_CD': vals(('NONE','아님','None',''),('FULL','전체 무이자','Full',''),('PARTIAL','부분 무이자','Partial','')),
 'INTEREST_FREE_FUNDER_CD': vals(('CARD_ISSUER','카드사','Card Issuer',''),('MERCHANT','가맹점 (우리 몰)','Merchant','수수료 추가'),('PG','PG','PG','')),
 'IDENTITY_VERIFIER_CD': vals(('ISSUER','카드사·PG','Card Issuer or PG',''),('EASY_PAY_PROVIDER','간편결제사','Easy Pay Provider',''),('MERCHANT','우리 몰','Merchant','결제 비밀번호')),
 'IDENTITY_VERIFICATION_METHOD_CD': vals(('APP_CARD','앱카드','App Card',''),('ISP','ISP','ISP',''),('SAFE_CLICK','안심클릭','Safe Click',''),('EASY_PAY_AUTH','간편결제사 인증','Easy Pay Authentication',''),
   ('PAYMENT_PIN','결제 비밀번호','Payment PIN','원클릭 (회원 41-1 D)'),('NONE','비인증','None','[확인 필요: 계약 PG, 없으면 값에서 뺌]')),
 'MOBILE_CARRIER_CD': vals(('SKT','SK텔레콤','SK Telecom',''),('KT','KT','KT',''),('LGU','LG유플러스','LG U+',''),('MVNO','알뜰폰','MVNO','[확인 필요: 계약 PG]')),
 'FDS_DECISION_CD': vals(('PASS','통과','Pass',''),('REVIEW','검토','Review','승인 뒤 주문 보류 `PAYMENT_REVIEW`'),('BLOCK','차단','Block','PG 호출 안 함')),
 'ESCROW_DELIVERY_REGISTER_STATUS_CD': vals(('PENDING','등록 대기','Pending','마지막 출고 전'),('REGISTERED','등록 완료','Registered',''),('FAILED','등록 실패','Failed','재시도 대상')),
 'ESCROW_CONFIRM_STATUS_CD': vals(('WAITING','확정 대기','Waiting',''),('CONFIRMED','구매 확정','Confirmed',''),('REJECTED','구매 거절','Rejected',''),('AUTO_CONFIRMED','자동 확정','Auto Confirmed','PG 기한 경과')),
 'ACCOUNT_HOLDER_VERIFY_RESULT_CD': vals(('MATCHED','일치','Matched','송금 가능'),('MISMATCHED','불일치','Mismatched','계좌 다시 받음'),('ERROR','조회 오류','Error','다시 조회')),
 'CASH_RECEIPT_ISSUE_ROUTE_CD': vals(('PG_AGENT','PG 대행 발급','PG Agent',''),('MERCHANT_DIRECT','자사 직접 발급','Merchant Direct','')),
 'PAYMENT_REFUND_REASON_CD': vals(('AMOUNT_MISMATCH_AUTO_CANCEL','금액 불일치 자동 취소','Amount Mismatch Auto Cancel','3-3 A'),('ABNORMAL_APPROVAL_AUTO_CANCEL','이상 승인 자동 취소','Abnormal Approval Auto Cancel','3-8 A'),('LATE_DEPOSIT_REFUND','만료 뒤 입금 환불','Late Deposit Refund','4-4 A'),('CHARGEBACK','차지백 인용','Chargeback Accepted','9-3 A'),('PG_CONSOLE_CANCEL','PG 관리자 화면 취소 들여오기','PG Console Cancel Import','5-7 A'),('MANUAL_ADJUSTMENT','운영자 조정','Manual Adjustment','')),
 'REFUND_REQUEST_STATUS_CD': vals(('REQUESTED','요청','Requested',''),('PROCESSING','처리 중','Processing',''),('COMPLETED','완료','Completed',''),('PARTIALLY_FAILED','일부 실패','Partially Failed','예외 수동 처리')),
 'ADDITIONAL_PAYMENT_REASON_CD': vals(('EXCHANGE_SHIPPING_FEE','교환 배송비','Exchange Shipping Fee',''),('REMOTE_AREA_FEE','도서산간 추가 배송비','Remote Area Fee',''),('OVER_REFUND_RECOVERY','과다 환불 회수','Over-Refund Recovery','5-7 A')),
 'PAYMENT_CANCEL_REASON_CD': vals(('CLAIM_REFUND','클레임 환불','Claim Refund','CLAIM_ID 필수'),('ORDER_CHANGE_ADJUSTMENT','주문 변경 차액','Order Change Adjustment','ORDER_CHANGE_HIST_ID 필수'),
   ('AMOUNT_MISMATCH_AUTO_CANCEL','금액 불일치 자동 취소','Amount Mismatch Auto Cancel','3-3 A'),('ABNORMAL_APPROVAL_AUTO_CANCEL','이상 승인 자동 취소','Abnormal Approval Auto Cancel','3-8 A'),
   ('LATE_DEPOSIT_REFUND','만료 뒤 입금 환불','Late Deposit Refund','4-4 A'),('PG_CONSOLE_CANCEL','PG 관리자 화면 취소 들여오기','PG Console Cancel Import','5-7 A'),
   ('CHARGEBACK','차지백 인용','Chargeback Accepted','CHARGEBACK_ID 필수 (9-3 A)'),('FDS_REVIEW_CANCEL','FDS 검토 뒤 취소','Fraud Review Cancel','[확인 필요: 컬럼 검토 질문, 9-1 A]'),('MANUAL_ADJUSTMENT','운영자 조정','Manual Adjustment','')),
 'CANCEL_PROCESS_STATUS_CD': vals(('REQUESTED','요청','Requested',''),('COMPLETED','완료','Completed',''),('FAILED','실패','Failed','재시도 대상'),('UNKNOWN','결과 불명','Unknown','같은 취소번호로 조회 (5-9 A)')),
 'REFUND_METHOD_CD': vals(('PG_CANCEL','PG 취소','PG Cancel',''),('BANK_TRANSFER','계좌 송금','Bank Transfer','5-4 A'),('DEPOSIT_CREDIT','예치금 적립','Deposit Credit','동의 필요 (5-5 A)'),('CHARGEBACK','차지백 회수','Chargeback','9-3 A')),
 'REFUND_DEDUCTION_REASON_CD': vals(('EXCHANGE_SHIPPING_FEE','교환 배송비','Exchange Shipping Fee',''),('REMOTE_AREA_FEE','도서산간 추가 배송비','Remote Area Fee',''),('POINT_CLAWBACK_SHORTFALL','적립금 회수 부족분','Point Clawback Shortfall','12-3 A')),
 'POINT_TRANSACTION_TYPE_CD': vals(('ACCRUAL','적립','Accrual','+'),('USE','사용','Use','−'),('USE_CANCEL','사용 취소 (원래 건 복원)','Use Cancel','+ (12-3 A)'),('EXPIRATION','소멸','Expiration','−'),
   ('ACCRUAL_CANCEL','적립 취소 (예정 취소)','Accrual Cancel','−'),('ACCRUAL_CLAWBACK','확정 적립 회수','Accrual Clawback','− (12-3 A)'),('RESTORE_REISSUE','유예 기한 복원','Restore Reissue','+ (12-3 A)'),
   ('MOVE_IN','이동 받음','Move In','계정 통합 (회원 29-2 A)'),('MOVE_OUT','이동 보냄','Move Out',''),('ADJUSTMENT','운영자 조정','Adjustment','')),
 'POINT_LEDGER_STATUS_CD': vals(('SCHEDULED','예정','Scheduled','결제 완료 때 (주문 6-8 A)'),('CONFIRMED','확정','Confirmed',''),('CANCELED','취소','Canceled','')),
 'POINT_KIND_CD': vals(('PURCHASE','구매 적립','Purchase-Earned','자기적립마일리지 (주문 OC-26 A)'),('OTHER','기타 적립','Other','이벤트 등')),
 'POINT_ACCRUAL_REASON_CD': vals(('PURCHASE','구매','Purchase',''),('REVIEW','리뷰','Review',''),('EVENT','이벤트','Event',''),('ADMIN_GRANT','운영자 지급','Admin Grant',''),('RESTORE','유예 복원','Restore','12-3 A'),('MEMBER_MERGE','계정 통합','Member Merge','')),
 'DEPOSIT_TRANSACTION_TYPE_CD': vals(('CREDIT','입금','Credit','+'),('USE','사용','Use','−'),('USE_CANCEL','사용 취소','Use Cancel','+'),('WITHDRAWAL','출금','Withdrawal','− (요청 순간, 12-4 A)'),
   ('WITHDRAWAL_CANCEL','출금 취소','Withdrawal Cancel','+ (실패·취소)'),('OVER_REFUND_RECOVERY','과다 환불 회수','Over-Refund Recovery','− (5-7 A)'),('MOVE_IN','이동 받음','Move In',''),('MOVE_OUT','이동 보냄','Move Out',''),('ADJUSTMENT','운영자 조정','Adjustment','')),
 'DEPOSIT_CREDIT_REASON_CD': vals(('REFUND_CREDIT','환불 예치금 적립','Refund Credit','5-5 A'),('VIRTUAL_ACCOUNT_OVERPAYMENT','가상계좌 과오입금','Virtual Account Overpayment','4-4 A'),('ADMIN_ADJUSTMENT','운영자 조정','Admin Adjustment',''),('MEMBER_MERGE','계정 통합','Member Merge','')),
 'DEPOSIT_SOURCE_TYPE_CD': vals(('CARD_LIKE','카드성','Card-Like','카드, 원클릭, 간편결제 앱에서 고른 카드, 휴대폰 결제. 출금 불가 (12-2 A)'),('CASH_LIKE','현금성','Cash-Like','가상계좌, 계좌이체, 간편결제 앱에서 고른 머니·계좌'),('OTHER','기타','Other','운영자 조정 등')),
 'WITHDRAWAL_REQUEST_TYPE_CD': vals(('CUSTOMER_REQUEST','고객 요청','Customer Request',''),('MEMBER_WITHDRAWAL_AUTO','탈퇴 자동 출금','Member Withdrawal Auto','회원 28-7')),
 'WITHDRAWAL_STATUS_CD': vals(('REQUESTED','요청','Requested',''),('TRANSFERRING','이체 중','Transferring',''),('COMPLETED','완료','Completed',''),('FAILED','실패','Failed','출금 취소 행으로 복원'),('CANCELED','취소','Canceled','')),
 'CASH_RECEIPT_ACTION_CD': vals(('ISSUE','발급','Issue',''),('CANCEL','전액 취소','Cancel',''),('PARTIAL_CANCEL','부분 취소','Partial Cancel','PG가 지원할 때 (6-4 A)')),
 'CASH_RECEIPT_ISSUE_TYPE_CD': vals(('CUSTOMER_REQUESTED','고객 신청','Customer Requested',''),('SELF_ISSUED','무기명 자진 발급','Self-Issued','6-3 C')),
 'CASH_RECEIPT_PROCESS_STATUS_CD': vals(('REQUESTED','요청','Requested',''),('ISSUED','완료','Issued',''),('FAILED','실패','Failed','재시도')),
 'TAX_INVOICE_TYPE_CD': vals(('ORIGINAL','당초','Original',''),('AMENDED','수정','Amended','')),
 'TAX_INVOICE_AMENDMENT_REASON_CD': vals(('RETURN_OF_GOODS','환입','Return of Goods',''),('CONTRACT_CANCELLATION','계약 해제','Contract Cancellation',''),('SUPPLY_VALUE_CHANGE','공급가액 변동','Supply Value Change',''),
   ('ENTRY_ERROR_CORRECTION','기재사항 착오 정정','Entry Error Correction',''),('DUPLICATE_ISSUE','착오 이중 발급','Duplicate Issue','')),
 'TAX_INVOICE_STATUS_CD': vals(('REQUESTED','요청','Requested',''),('ISSUED','발급','Issued',''),('TRANSMITTED','국세청 전송','Transmitted',''),('FAILED','실패','Failed','')),
 'CHARGEBACK_REASON_CD': vals(('UNAUTHORIZED_USE','본인 미사용','Unauthorized Use','여신전문금융업법 16조'),('NOT_RECEIVED','상품 미수령','Not Received',''),('NOT_AS_DESCRIBED','상품 상이','Not as Described',''),
   ('DUPLICATE_BILLING','중복 청구','Duplicate Billing',''),('CANCELED_NOT_REFUNDED','취소 미환불','Canceled not Refunded',''),('OTHER','기타','Other','')),
 'CHARGEBACK_RESULT_CD': vals(('IN_PROGRESS','진행','In Progress',''),('REJECTED','기각','Rejected','변동 없음'),('ACCEPTED','인용','Accepted','취소 행 생성'),('PARTIALLY_ACCEPTED','일부 인용','Partially Accepted','')),
 'EVIDENCE_FILE_TYPE_CD': vals(('PAYMENT_SUMMARY','결제·인증 요약','Payment Summary',''),('DELIVERY_PROOF','배송 증빙','Delivery Proof',''),('CONSULTATION_RECORD','상담 기록','Consultation Record',''),('OTHER','기타','Other','')),
 'PG_CODE_GROUP_CD': vals(('CARD_COMPANY','카드사','Card Company',''),('BANK','은행','Bank',''),('MOBILE_CARRIER','통신사','Mobile Carrier',''),('EASY_PAY_PROVIDER','간편결제사','Easy Pay Provider',''),('PAYMENT_FAILURE_REASON','결제 실패 사유','Payment Failure Reason','PG 실패 코드 → 실패·만료 사유 코드. 저장 카드 사용 불가 판단에 쓴다 (PYC-37 A)')),
 'PG_API_TYPE_CD': API,
 'API_CALL_RESULT_CD': vals(('SUCCESS','성공','Success',''),('FAILURE','실패 응답','Failure',''),('TIMEOUT','시간 초과','Timeout',''),('NETWORK_ERROR','통신 오류','Network Error','')),
 'WEBHOOK_PROCESSING_STATUS_CD': vals(('RECEIVED','수신','Received','처리 대상'),('APPLIED','적용','Applied',''),('IGNORED','무시','Ignored','이미 반영 등'),('INQUIRY_FAILED','조회 실패','Inquiry Failed','재시도 대상'),('SIGNATURE_INVALID','서명 불일치','Signature Invalid','조회하지 않음')),
 'SIGNATURE_VERIFICATION_RESULT_CD': vals(('VALID','일치','Valid',''),('INVALID','불일치','Invalid',''),('NOT_APPLICABLE','해당 없음','Not Applicable','서명이나 검증 값을 주지 않는 PG. 가상계좌 입금 웹훅은 결제 행의 검증 값 해시로 검증한다 (PYC-7 A)')),
 'RECONCILIATION_TARGET_CD': vals(('PG','PG 거래','PG Transactions','7-3 B'),('POINT','적립금','Point','7-4 A'),('DEPOSIT','예치금','Deposit','7-4 A')),
 'RECONCILIATION_RUN_STATUS_CD': vals(('RUNNING','실행 중','Running',''),('COMPLETED','완료','Completed',''),('FAILED','실패','Failed','')),
 'MISMATCH_TYPE_CD': vals(('PG_ONLY','PG에만 있음','PG Only',''),('OURS_ONLY','우리에만 있음','Ours Only','날짜 경계 포함'),('AMOUNT_DIFF','금액 다름','Amount Difference',''),('STATUS_DIFF','상태 다름','Status Difference',''),
   ('TAX_SPLIT_DIFF','과세·면세 분할 다름','Tax Split Difference','6-8 A'),('INTERNAL_SUM_DIFF','취소 합계 ≠ 누계','Internal Sum Difference','2-7 A'),('CASH_RECEIPT_DIFF','현금영수증 금액 다름','Cash Receipt Difference','6-4 A'),
   ('BALANCE_DIFF','남은 금액 ≠ 적립 − 차감','Balance Difference','12-5 C로 정의 변경'),('ALLOCATION_DIFF','배분 ≠ 원장 사용','Allocation Difference','7-4 A'),('RESTORE_MISSING','복원 누락','Restore Missing','7-4 A'),('WITHDRAWAL_DIFF','출금 내역 다름','Withdrawal Difference','7-4 A')),
 'MISMATCH_RESOLUTION_STATUS_CD': vals(('UNRESOLVED','미해결','Unresolved',''),('AUTO_RESOLVED','자동 해소','Auto Resolved',''),('MANUALLY_RESOLVED','수동 해소','Manually Resolved','')),
 'MISMATCH_RESOLUTION_METHOD_CD': vals(('DATE_BOUNDARY_AUTO','날짜 경계 자동 해소','Date Boundary Auto',''),('PAYMENT_INQUIRY_APPLIED','결제 조회 반영','Payment Inquiry Applied',''),('PG_CANCEL_IMPORTED','PG 취소 들여오기','PG Cancel Imported','5-7 A'),('OPERATOR_ADJUSTMENT','운영자 조정','Operator Adjustment','')),
 'INCIDENT_DETECTION_METHOD_CD': vals(('AUTO_ALERT','자동 감지','Auto Alert','7-6 B 지표'),('PG_NOTICE','PG 공지','PG Notice',''),('MANUAL','수동','Manual','')),
 'INCIDENT_ACTION_CD': vals(('ROUTING_SWITCH','PG 전환','Routing Switch',''),('METHOD_HIDDEN','수단 숨김','Method Hidden',''),('NONE','조치 없음','None','')),
 'PII_RETENTION_REASON_CD': vals(('ECOMMERCE_PAYMENT_RECORD_5Y','대금 결제 기록 5년','E-Commerce Payment Record 5 Years','전자상거래법 시행령 6조, 기산일 = 거래일'),
   ('TAX_EVIDENCE_5Y_FROM_FILING_DUE','국세 증빙 5년','Tax Evidence 5 Years from Filing Due','국세기본법 85조의3, 기산일 = 법정 신고 기한 [확인 필요: 세무]')),
 'AFFECTED_PAYMENT_METHOD_CD': METHOD,
}
REUSE = {'CARD_ACQUIRER_CD': 'CARD_COMPANY', 'AFFECTED_PAYMENT_METHOD_CD': 'PAYMENT_METHOD', 'ABNORMAL_PREV_CONFIRM_ROUTE_CD': 'RESULT_CONFIRM_ROUTE'}
# 재사용 컬럼은 값 행을 다시 펼치지 않고, 원래 컬럼을 가리키는 참조 행 하나를 아래에 둔다 (PYC-50 A, PYC-51 A): {컬럼: (원래 테이블, 원래 컬럼)}
REUSE_NO_ROWS = {'ABNORMAL_PREV_CONFIRM_ROUTE_CD': ('PAY_PAYMENT', 'RESULT_CONFIRM_ROUTE_CD'),
                 'CARD_ACQUIRER_CD': ('PAY_PAYMENT', 'CARD_COMPANY_CD'),
                 'AFFECTED_PAYMENT_METHOD_CD': ('PAY_PAYMENT', 'PAYMENT_METHOD_CD')}

CONFIRMED_GROUPS = {('PAY_PAYMENT', '식별'), ('PAY_PAYMENT', '상태·결과'), ('PAY_PAYMENT', '결제 수단')}
CONFIRMED_TABLES = set()
# PG사(또는 PG를 거쳐 카드사·국세청)에서 받는 값과, 계약서·코드표에서 옮겨 적는 PG 값. 정의서에서 번호를 굵게 표시한다 (2026-11-26 사용자 지시).
PG_SOURCED = {(t, c) for t, cs in [
    ('PAY_PAYMENT', 'PG_PAYMENT_STATUS_VAL PG_RESULT_CD PG_RESULT_MESSAGE_CN PG_TRANSACTION_NO PG_RECEIPT_URL AUTHENTICATED_AMT APPROVED_AMT CARD_ISSUER_INSTANT_DISCOUNT_AMT EASY_PAY_PROVIDER_INSTANT_DISCOUNT_AMT PG_INSTANT_DISCOUNT_AMT '
     'AUTHENTICATED_AT APPROVED_AT EASY_PAY_INNER_METHOD_CD EASY_PAY_INNER_CARD_AMT EASY_PAY_INNER_CASH_AMT PG_EASY_PAY_PROVIDER_RAW_VAL '
     'CARD_COMPANY_CD CARD_ACQUIRER_CD PG_CARD_COMPANY_RAW_VAL MASKED_CARD_NUMBER_VAL CARD_TYPE_CD CARD_APPROVAL_NO PG_CARD_IDENTIFIER_VAL '
     'INSTALLMENT_MONTHS_CNT INTEREST_FREE_TYPE_CD INTEREST_FREE_FUNDER_CD INTEREST_FREE_INSTALLMENT_CNT '
     'PG_AUTH_RESULT_VAL IDENTITY_VERIFICATION_METHOD_CD VIRTUAL_ACCOUNT_BANK_CD VIRTUAL_ACCOUNT_NUMBER_VAL DEPOSIT_DUE_AT DEPOSITOR_NM '
     'TRANSFER_BANK_CD MASKED_TRANSFER_ACCOUNT_NUMBER_VAL MOBILE_CARRIER_CD MOBILE_PHONE_NUMBER_ENC MASKED_MOBILE_PHONE_NUMBER_VAL '
     'PG_FDS_RESULT_VAL PG_PROMOTION_CD PG_PROMOTION_NM ESCROW_CONFIRM_STATUS_CD ESCROW_CONFIRMED_AT '
     'SETTLEMENT_METHOD_CD CARD_MERCHANT_NO PG_MID_VAL PARTIAL_CANCELABLE_YN CARD_OWNER_TYPE_CD CARD_POINT_USED_YN VIRTUAL_ACCOUNT_WEBHOOK_SECRET_HASH ESCROW_KEY_VAL'),
    ('PAY_PAYMENT_CANCEL', 'PG_CANCEL_TRANSACTION_NO PG_RESULT_CD PG_RESULT_MESSAGE_CN COMPLETED_AT CARD_ISSUER_INSTANT_DISCOUNT_CANCEL_AMT EASY_PAY_PROVIDER_INSTANT_DISCOUNT_CANCEL_AMT PG_INSTANT_DISCOUNT_CANCEL_AMT '
     'PG_CANCEL_RECEIPT_URL ACCOUNT_HOLDER_VERIFY_RESULT_CD CANCEL_TIME_CARD_ACQUIRE_STATUS_CD'),
    ('PAY_CASH_RECEIPT', 'NTS_APPROVAL_NO PG_RESULT_CD ISSUED_AT'),
    ('PAY_CHARGEBACK', 'PG_CASE_NO CHARGEBACK_REASON_CD DISPUTED_AMT RECEIVED_AT RESPONSE_DUE_AT CHARGEBACK_RESULT_CD RECOVERED_AMT RESULT_AT'),
    ('PAY_PG_API_LOG', 'PG_RESULT_CD PG_RESULT_MESSAGE_CN HTTP_STATUS_VAL RESPONDED_AT'),
    ('PAY_PG_WEBHOOK_INBOX', 'DEDUPLICATION_KEY_VAL WEBHOOK_EVENT_TYPE_VAL PAYMENT_NO PG_TRANSACTION_NO SENDER_IP'),
    ('PAY_RECONCILIATION_RUN', 'SOURCE_FILE_NM PG_TRANSACTION_CNT PG_APPROVED_TOTAL_AMT PG_CANCELED_TOTAL_AMT'),
    ('PAY_PAYMENT_METHOD_PG_SETTING', 'PG_MID_VAL MERCHANT_DISPLAY_NM'),
    ('PAY_CARD_MERCHANT_CONTRACT', 'CARD_MERCHANT_NO'),
    ('PAY_PG_CODE_MAPPING', 'PG_CODE_VAL'),
] for c in cs.split()}

CONFIRM = [
 ('테이블 이름', '21개 모두 후보. 주문 도메인처럼 이름 결정 질문을 거쳐 확정한다.', '전체'),
 ('PG·카드사 코드의 외부 업체 마스터 FK', 'PG 업체 코드(`PG_CD`)와 카드사 코드에 `SYS` 외부 업체 마스터 FK를 걸지 (2-6 A, PYC-1 B에서 넘김).', '`PG_CD` 전체'),
 ('원장·환불 요청 시퀀스 CACHE', '적립금·예치금 원장과 환불 요청은 11-3 목록에 없었다. 적립금 원장은 결제와 같은 속도로 늘어난다.', '`PAY_POINT_LEDGER`, `PAY_DEPOSIT_LEDGER`, `PAY_REFUND_REQUEST`'),
 ('환불 요청 파티션', '1-3 A의 환불 요청 테이블은 11-1 A 파티션 목록에 없었다. 주문 참조 파티션을 제안한다.', '`PAY_REFUND_REQUEST`'),
 ('취소 행 원인 FK와 환불 요청 근거', '5-2 A는 취소 행에 원인 FK를, 1-3 A는 환불 요청에 근거를 둔다. 둘 다 둘지, 취소 행은 환불 요청만 가리킬지.', '`PAY_PAYMENT_CANCEL`'),
 ('PG 원래 코드 보관', '대응이 없는 PG 카드사 코드를 원래 값으로 남길지 (PYC-2 후속).', '`PG_CARD_COMPANY_RAW_VAL`'),
 ('적립금 복원 방식', '반품 복원을 차감 기록의 복원 금액으로 할지, 음수 차감 행으로 할지 (12-3 A).', '`RESTORED_AMT`'),
 ('환불 차감 내역', '환불에서 뺀 금액이 여러 사유일 때 취소 행 한 칸으로 둘지, 클레임 쪽 내역으로 둘지 (5-10 A, 12-3 A).', '`REFUND_DEDUCTION_AMT`'),
 ('FDS 검토 뒤 취소 사유', 'FDS 검토 판정 뒤 운영자가 취소할 때 전용 사유 코드를 둘지 (9-1 A).', '`PAYMENT_CANCEL_REASON_CD`'),
 ('추가 결제의 미성년 한도 복사', '추가 결제 행에 적용 한도와 결제 전 사용액을 복사하고 CHECK를 걸지 (9-4 A).', '`PAY_PAYMENT`'),
 ('실패 행 함수 기반 인덱스', '실패 횟수 집계 인덱스 3개를 실패 행만 담는 함수 기반으로 할지 (9-2 A).', '`PAY_PAYMENT` 인덱스'),
 ('외부 적립 행사 코드 값 목록', '우리 부담 외부 적립 행사 코드를 `CMM_CODE`에 둘지, 10-4 B 프로모션 마스터를 가리킬지 (10-3 B).', '`MERCHANT_FUNDED_EXTERNAL_PROMOTION_CD`'),
 ('허용 목록 버전 기록', 'PG 호출 로그에 적용한 원문 허용 목록 버전을 남길지 (PYC-3 후속).', '`MASKING_RULE_VER`'),
 ('세무·법무·계약 PG', '공급 시기와 작성일자, 수정 사유 목록, 국세 증빙 기산일, 카드성 예치금 출금 제한, 고객 사유 지연, 개인사업자 번호, 간편결제사·통신사·인증 방식 목록.', '빨간 표시 컬럼'),
 ('간편결제 포인트의 현금영수증 대상 여부', '간편결제 앱에서 현금성으로 낸 금액에 적립 포인트가 섞이는지, 계약 PG가 포인트와 충전금을 나눠 주는지. 나눠 주고 적립 포인트가 대상이 아니면 포인트로 낸 금액 컬럼을 더한다 (PYC-65 B).', '`EASY_PAY_INNER_CASH_AMT`'),
 ('카드 승인번호 수신 여부', '간편결제 앱에서 고른 카드에서도 PG가 카드 승인번호를 주는지. 주지 않으면 카드 정보 CHECK에서 승인번호를 뺀다 (PYC-62 A).', '`CARD_APPROVAL_NO`'),
]
