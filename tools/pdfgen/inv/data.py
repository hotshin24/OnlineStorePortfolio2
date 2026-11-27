# 재고(INV) 도메인 테이블·컬럼 정의 (제안, 컬럼 검토 전)
# 근거: 재고 결정 (2026-11-27, 대화로 결정. 축 8개 결정 52개 + 후속 2개, 테이블 T-1~T-11, 컬럼 검토 IC-1~). 테이블 8개 (IC-10 B로 확보 처리 이력 추가). 결정 기록은 inv/decision.py.
# 테이블 이름은 T-10 A로 정했다. 컬럼은 모두 제안이고 컬럼 검토(IC-n)에서 정한다.
# 컬럼: (물리명, 한글 논리명, 영문 논리명, 타입, NULL(N=NOT NULL, Y=허용), 기본값, 제약, 설명)
# 테이블의 cols는 [(컬럼 그룹 이름, [컬럼...]), ...] 순서 그대로가 규칙 8 순서다 (8-C A: 그룹도 중요도 순).
ID = 'NUMBER(19,0)'
YN = 'CHAR(1)'
TS = 'TIMESTAMP'
QTY = 'NUMBER(7)'

def yn(p, ko, en, d, desc):
    return (p, ko, en, YN, 'N', f"'{d}'", 'CK (Y/N)', desc)

def fk(p, ko, en, target, null='N', extra='', desc=''):
    return (p, ko, en, ID, null, '', f'FK → `{target}`' + (', ' + extra if extra else ''), desc)

def ref(p, ko, en, null='Y', desc='', extra=''):
    # FK를 걸지 않는 식별자 (다른 도메인 ID, 파티션을 제거하는 테이블의 ID, 2-4 A)
    return (p, ko, en, ID, null, '', 'IX (FK 없음)' + (', ' + extra if extra else ''), desc)

def qty(p, ko, en, desc='', d='0', ck='CK (>= 0)', null='N'):
    return (p, ko, en, QTY, null, d, ck, desc)

def dqty(p, ko, en, desc=''):
    # 원장 증감 (부호 있음)
    return (p, ko, en, QTY, 'N', '0', '', desc)

def cd(p, ko, en, null='N', desc='', n=30, ck='CK (값 목록)'):
    return (p, ko, en, f'VARCHAR2({n})', null, '', ck, desc)

def rowver():
    return ('ROW_VER','행 버전 (낙관적 잠금)','Row Version (Optimistic Lock)','NUMBER(10)','N','0','CK (>= 0)',
            '갱신할 때마다 1 늘린다. `WHERE ROW_VER = :읽은 값`으로 갱신해 0건이면 다시 읽는다. 관리자가 상태를 바꾸는 테이블에만 둔다 (제안).')

T = []
def table(**kw):
    kw.setdefault('idx', []); kw.setdefault('check', []); kw.setdefault('pii', False); kw.setdefault('ldel', False)
    T.append(kw)

WH = 'FK 예정 → `WMS_WAREHOUSE` (후보)'
NSI = 'FK 예정 → `WMS_NON_SALE_ITEM` (후보)'
ADM = '관리자 테이블(`ADM`)은 관리자 도메인 설계 뒤 이름과 FK 여부를 정한다.'

# =========================================================== 1. 현재고
table(t='INV_STOCK', ko='현재고 (창고별 품목 수량)', en='Stock on Hand',
 desc='(창고, SKU 또는 비판매 품목)마다 1행. 판매 가능 수량의 원천이다 (1-1 A). 수량 구분 6개를 컬럼으로 갖고 (3-1 A, 3-2 A), 모든 변경은 "지금 값 ± 증감" UPDATE 한 문장으로만 한다 (2-6 A). '
      '품목을 등록할 때 창고마다 수량 0으로 만든다 (2-2 A). 지우지 않는 잔액 행이다 (T-4 A). 원장·확보·입고 예정·스냅샷·예외가 이 행 ID 하나로 창고와 품목을 가리킨다 (1-6 A).',
 basis='1-1 A, 1-2 A, 1-6 A, 2-2 A, 2-6 A, 2-7 A, 3-1 A~3-3 A, 4-12 A, 5-1 B, 5-3 A, T-4 A, T-10 A, IC-1 A~IC-4 A, IC-17 A~IC-25 A',
 pk='대리 PK `SEQ_INV_STOCK`', cache=20,
 delete='지우지 않는다. 단종돼도 수량 0 행으로 남긴다. 판매 중지는 상품 SKU의 판매 상태가 맡고, 사용 여부·삭제 컬럼을 두지 않는다 (T-4 A). 선행 4의 유형으로는 "잔액"이다',
 part='없음', keep='보존 기간 없음 (지우지 않음, T-4 A)',
 cols=[
 ('식별', [
  ('STOCK_ID','현재고 고유 식별 번호','Stock on Hand Unique Identifier',ID,'N','','PK',
   '원장·확보·입고 예정·스냅샷·예외가 이 ID를 FK로 가리킨다 (1-6 A). 한 트랜잭션에서 여러 행을 고칠 때는 이 ID 오름차순으로 UPDATE한다 (4-12 A).'),
  ('WAREHOUSE_ID','창고 식별 번호','Warehouse Identifier',ID,'N','',WH,
   'NOT NULL (1-6 A). 창고는 지금 1곳이다. WMS 창고 마스터가 생기면 FK를 건다.'),
  fk('SKU_ID','SKU 식별 번호','SKU Identifier','PRD_SKU','Y','',
     '판매 상품. 품목 둘 중 정확히 하나 (CK, 1-2 A, 선행 6). 상품 마스터라 FK를 건다.'),
  ('NON_SALE_ITEM_ID','비판매 품목 식별 번호','Non-Sale Item Identifier',ID,'Y','',NSI,
   '사은품, 포장재, 수선 부자재 (1-2 A). 비판매 품목 마스터는 WMS가 갖는다 (상품 M-12 C). 품목 둘 중 정확히 하나 (CK).'),
 ]),
 ('판매 가능', [
  ('AVAILABLE_QTY','판매 가능 수량 (가상 컬럼)','Available Quantity (Virtual)',QTY,'N','','가상 컬럼, CK (>= 0)',
   '`GENERATED ALWAYS AS (NORMAL_QTY - RESERVED_QTY - ALLOCATED_QTY) VIRTUAL` (3-3 A). CHECK >= 0이 초과 판매를 막는 마지막 방어선이다. '
   '재발송·결품 대체는 `AVAILABLE_QTY >= :수량`을 조건으로 할당을 더하는 UPDATE 한 문장이다 (5-1 B). 일반 주문은 아래 `GENERAL_ORDERABLE_QTY`를 쓴다. 예: 정상 10, 예약 2, 할당 3이면 5.'),
  ('GENERAL_ORDERABLE_QTY','일반 주문 가능 수량 (가상 컬럼)','General Orderable Quantity (Virtual)',QTY,'N','','가상 컬럼',
   '`GENERATED ALWAYS AS (GREATEST(NORMAL_QTY - RESERVED_QTY - ALLOCATED_QTY - SAFETY_STOCK_QTY, 0)) VIRTUAL` (IC-23 A). Oracle 가상 컬럼은 다른 가상 컬럼을 가리킬 수 없어 원래 컬럼으로 쓴다. '
   '일반 주문 확보는 `GENERAL_ORDERABLE_QTY >= :수량`을 조건으로 예약을 더하는 UPDATE 한 문장이다 (5-1 B). 품절 표시, "n개 남음"(5-3 A, 5-4 A), 품절 시작 일시 CK가 모두 이 값을 쓴다. '
   '예: 정상 10, 예약 2, 할당 3, 안전 재고 2이면 3. 4개 주문은 0행 갱신으로 거절된다.'),
  qty('SAFETY_STOCK_QTY','안전 재고 수량','Safety Stock Quantity',
      '일반 주문이 쓰지 못하고 남겨 두는 수량 (5-1 B). 새 행은 공통코드 정책값(등급별 기본값, IC-4 A)으로 채운다. 관리자가 고치면 수동 지정 여부가 Y가 되고, N이면 등급이 바뀔 때 새 기본값으로 바뀐다 (IC-19 A). CHECK(판매 가능 >= 0)에는 넣지 않아 재발송은 안전 재고까지 쓴다.'),
  ('SOLD_OUT_AT','품절 시작 일시','Sold Out Since',TS,'Y','','',
   '첫 생산 입고 뒤(`LAST_INBOUND_AT` NOT NULL) 일반 주문 가능 수량이 0이 되는 UPDATE에서 채우고, 양수로 돌아오면 비운다. 품절인 채로 수량만 바뀌면 처음 시각을 유지한다. 확보·출고·입고뿐 아니라 안전 재고를 고치는 UPDATE도 같다 (IC-1 A, IC-17 A). '
   '판매 개시 전(등록 뒤 첫 입고 전)은 NULL이라 품절 기간에 들어가지 않는다. 예: 11/1 등록, 12/1 첫 입고면 12/1 전은 NULL. '
   '품절 판정은 조회 때 계산 그대로이고(5-3 A) 이 값은 품절 기간·판매 기회 손실을 보는 기록이다. 품절 전환을 상품 검색 색인에 알리는 일은 상품 넘김 사항.'),
 ]),
 ('실물 수량', [
  qty('NORMAL_QTY','정상 수량','Normal (Sellable) Quantity','판매할 수 있는 실물. 예약·할당은 이 안에서 잡는다 (3-2 A).'),
  qty('INSPECTION_PENDING_QTY','검수 대기 수량','Inspection Pending Quantity','생산 입고 도착분과 반품 도착분 (6-3 B, 7-2 A). 검수를 마치면 정상·불량으로 옮긴다.'),
  qty('DEFECTIVE_QTY','불량 수량','Defective Quantity','수선해 정상으로 돌리거나 폐기·업체 반품·일괄 매각한다 (3-7 C, 7-4 A). 자사몰에서 B급으로 팔지 않는다.'),
  qty('HOLD_QTY','보류 수량','Hold Quantity','품질 확인, 촬영 대기 등으로 잠시 팔지 않는 실물 (3-6 A). 보류 사유는 원장 행에 있다.'),
  ('HOLD_SINCE_AT','보류 시작 일시','Hold Since',TS,'Y','','',
   '보류 수량이 0에서 양수가 될 때 채우고 0이 되면 비운다 (IC-2 B). 일부만 풀린 뒤 새로 들어와도 처음 값을 유지하는 근사다. 오래된 보류 감시(신호 6)는 `HOLD_SINCE_AT < 지금 − 기준 일수`로 판정한다. '
   '검수 대기에는 같은 컬럼을 두지 않고 원장의 입고 일시로 판정한다 (반품이 끊이지 않는 SKU는 늘 양수라 근사가 깨짐).'),
 ]),
 ('확보 수량', [
  qty('RESERVED_QTY','예약 수량','Reserved Quantity',
      '결제를 기다리는 주문이 잡은 정상 재고. 진행 중인 예약 상태 확보 행(입고 예정에 걸리지 않은 것)의 남은 수량 합계와 같다 (2-3 C, 8-3 A ②).'),
  qty('ALLOCATED_QTY','할당 수량','Allocated Quantity',
      '결제를 마쳤거나 주문 없이 출고 요청이 잡은 정상 재고 (4-5 A, 4-10 A). 출고하면 정상과 함께 줄어든다 (1-5 A). 할당 상태 확보 행의 남은 수량 합계와 같다.'),
 ]),
 ('재고 관리 기준', [
  ('REORDER_POINT_QTY','리오더 기준 수량','Reorder Point Quantity',QTY,'Y','','CK (>= 0)',
   'NULL이면 감시하지 않는다(시즌 한정 상품 등). 판매 가능 + Σ GREATEST(예정일이 오늘 + 입고 기간 안인 진행 중 입고 예정의 예정 − 검수 양품 − 검수 불량 − 확보, 0) <= 이 값이면 배치가 재고 예외 `LOW_STOCK`(신호 9)을 만든다 (IC-3 A, IC-8 A, IC-20 B). '
   '입고 기간은 공통코드 정책값(판매 상품, 비판매 품목). 예: 판매 가능 2, 기준 10, 60일 뒤 입고 100, 입고 기간 30일이면 2 <= 10이라 경보. '
   '이미 발주한 상품은 다시 잡히지 않는다. 포장재·사은품 같은 비판매 품목도 대상이다. 안전 재고(판매를 막는 값)와 다르다. 새 행은 등급별 기본값으로 채운다.'),
  yn('SAFETY_STOCK_MANUAL_YN','안전 재고 수동 지정 여부','Safety Stock Manually Set Flag','N',
     '관리자가 안전 재고를 고치면 Y (IC-19 A). N이면 월 등급 배치가 등급이 바뀐 행의 안전 재고를 새 등급 기본값으로 바꾼다. 예: A(10)에서 C로 떨어지면 N인 행은 C 기본값 2로 바뀐다. 기본값으로 되돌리면 N으로 돌린다.'),
  yn('REORDER_POINT_MANUAL_YN','리오더 기준 수동 지정 여부','Reorder Point Manually Set Flag','N',
     '관리자가 리오더 기준을 고치면 Y (IC-19 A). 안전 재고와 따로 다룬다.'),
  cd('STOCK_GRADE_CD','재고 등급 코드 (ABC)','Stock Grade Code (ABC)','Y',n=10,
     desc='월 마감 배치가 상품 `PRD_SALES_DAILY_STAT`의 지난 3개월 판매로 다시 매긴다 (IC-4 A). 판매 이력이 없는 새 행은 NULL. '
          '등급별 안전 재고·리오더 기준 기본값(`ATTR`)은 새 행과, 등급이 바뀐 행 중 수동 지정 여부가 N인 값에 적용한다 (5-1 B, IC-19 A). 처분 후보 추출에 쓰고, 순환 실사는 WMS가 이 등급과 WMS 실사 기록으로 뽑는다 (IC-21 B).'),
  ('STOCK_GRADE_EVAL_YM','재고 등급 산정 연월','Stock Grade Evaluation Year-Month','VARCHAR2(6)','Y','','CK (YYYYMM)',
   '등급 배치가 이 행을 산정한 연월 (IC-25 A). 산정 연월이 있는데 등급이 NULL이면 판매 이력 없음, 산정 연월이 NULL이면 아직 매기지 않은 새 행이다. 다른 행보다 오래됐으면 배치가 빠뜨린 것이다. 예: `202611`.'),
 ]),
 ('입출고·잔액 변경 시각', [
  ('LAST_INBOUND_AT','마지막 생산 입고 일시','Last Production Inbound At',TS,'Y','','',
   '생산 입고 원장과 같은 트랜잭션에서 갱신한다 (IC-1 A). 재입고 주기를 본다. 반품 입고는 넣지 않는다.'),
  ('LAST_OUTBOUND_AT','마지막 출고 일시','Last Outbound At',TS,'Y','','',
   '마지막으로 실물이 쓰이거나 나간 일시. 판매·재발송·비주문 출고와 포장재 사용·수선 사용 원장과 같은 트랜잭션에서 갱신한다 (IC-1 A, IC-22 A). 처분(폐기, 업체 반품, 매각)은 넣지 않는다. '
   '장기 체류·장기 미사용 추출, 이월·처분 판단에 쓴다. 원장(5년)이 지워져도 남는다. 예: 택배 박스는 매일 포장재 사용 배치로 갱신된다.'),
  ('BALANCE_CHANGED_AT','잔액 변경 일시','Balance Changed At',TS,'N','SYSTIMESTAMP','',
   '수량 7개(실물 4, 예약, 할당, 안전 재고) 중 하나라도 바꾸는 UPDATE에서 같은 문장으로 고친다 (IC-24 A). 일 스냅샷 대상은 그날 원장 변화가 있었거나 이 값이 그날 안인 행이다. '
   '등급·리오더 기준·수동 지정 여부만 바꾼 UPDATE는 고치지 않는다. 예: 등급 배치가 3만 행의 등급만 바꾼 날에는 스냅샷이 늘지 않는다.'),
 ]),
 ],
 idx=['UK `UK_INV_STOCK_WAREHOUSE_SKU` (함수 기반: `CASE WHEN SKU_ID IS NOT NULL THEN WAREHOUSE_ID END`, `SKU_ID`) (1-2 A)',
      'UK `UK_INV_STOCK_WAREHOUSE_NON_SALE_ITEM` (함수 기반, 비판매 품목도 같은 식) (1-2 A)',
      'IX `NON_SALE_ITEM_ID` (FK 예정). `SKU_ID`는 위 UK로 찾는다 [확인 필요: SKU만으로 찾는 조회(창고가 늘 때)용 인덱스]',
      'IX `HOLD_SINCE_AT` (오래된 보류 감시, IC-2 B), IX `LAST_OUTBOUND_AT` (장기 체류 추출, IC-1 A)'],
 check=['`SKU_ID`, `NON_SALE_ITEM_ID` 중 정확히 하나만 NOT NULL (1-2 A)',
        '`AVAILABLE_QTY >= 0` (3-3 A). 수량 컬럼 7개는 각각 >= 0 (2-6 A)',
        '`HOLD_QTY > 0`이면 `HOLD_SINCE_AT` NOT NULL, `HOLD_QTY = 0`이면 NULL (IC-2 B)',
        '`LAST_INBOUND_AT IS NOT NULL AND GENERAL_ORDERABLE_QTY = 0`이면 `SOLD_OUT_AT` NOT NULL, 아니면 NULL (IC-1 A, IC-17 A). `LAST_INBOUND_AT`이 NULL이면 조건이 거짓이라 `SOLD_OUT_AT`은 NULL이어야 한다 '
        '[확인 필요: 이 CK를 걸면 수량·안전 재고를 바꾸는 모든 UPDATE가 같은 문장에서 `SOLD_OUT_AT`을 고쳐야 한다]'])

# =========================================================== 2. 수불 원장
table(t='INV_STOCK_LEDGER', ko='수불 원장 (실물 수량 변화 1건)', en='Stock Ledger',
 desc='실물 쪽 수량(정상, 검수 대기, 불량, 보류)이 바뀐 사건 1건에 1행 (2-3 C). 예약·할당 변화는 확보 테이블이 갖는다. 현재고 UPDATE와 같은 트랜잭션에서 INSERT하고 (2-1 A), 고치거나 지우지 않는다. '
      '잘못 넣은 행은 같은 사유의 반대 행으로 정정한다 (T-6 B, 선행 4). 원천 문서는 원천마다 컬럼을 두고 사유에 맞는 하나만 채운다 (2-4 A). 수불부와 회계 구분은 사유별 합계로 낸다 (7-8 A).',
 basis='1-3 A, 1-5 A, 1-7 A, 2-1 A, 2-3 C~2-5 A, 2-7 A, 3-6 A, 3-8 A, 6-3 B, 6-5 A, 7-1 A~7-4 A, 7-7 A, 7-8 A, 8-2 C, 8-6 C, 8-8 후속 B, T-5 A, T-6 B, T-7 A, T-10 A, IC-5 A, IC-6 A',
 pk='대리 PK `SEQ_INV_STOCK_LEDGER`', cache=100,
 delete='삭제하지 않는다 (원장, 선행 4). 정정은 반대 행으로 한다 (T-6 B). 5년이 지난 파티션을 제거한다 (8-6 C)',
 part='업무 일자(`BUSINESS_DT`) 월 INTERVAL 파티션 (8-6 C). 원장을 FK로 가리키는 테이블이 없어 파티션 제거가 막히지 않는다 (정정의 원래 원장 ID는 `ref()`, T-6 B)',
 keep='업무 일자 + 5년 (8-6 C, 전표 성격) [확인 필요: 국세기본법 85조의3 장부·증빙 5년]',
 cols=[
 ('식별', [
  ('STOCK_LEDGER_ID','수불 원장 고유 식별 번호','Stock Ledger Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK','N','',
     '창고와 품목은 현재고 행에서 읽는다 (1-6 A). 수불 조회는 현재고와 조인 한 번이다.'),
  cd('STOCK_LEDGER_REASON_CD','수불 사유 코드','Stock Ledger Reason Code',
     desc='사용 17개 + 자리만 남긴 창고 이동 2개 (7-1 A, T-7 A, 1-7 A). 사유마다 채울 원천 컬럼과 버킷별 증감 방향을 테이블 수준 CK로 묶는다. 회계 구분은 코드의 `ATTR1` (7-8 A).'),
  ('LEDGER_KEY_VAL','원장 중복 방지 키','Stock Ledger Idempotency Key Value','VARCHAR2(100)','N','','UK',
   '사유별 형식: `SHIP:{출고 ID}:{현재고 ID}`, `INBOUND:{입고 ID}:{현재고 ID}`, `REVERSAL:{원래 원장 ID}` 등 (2-5 A). 같은 키로 두 번 넣으면 UK 위반으로 처리 전체가 되돌아간다. '
   '[확인 필요: 파티션 테이블의 UK라 전역 인덱스다. 파티션 제거 때 `UPDATE GLOBAL INDEXES`를 쓴다]'),
  ('BUSINESS_DT','업무 일자','Business Date','DATE','N','','파티션 키',
   '수불부·특정 날짜 수량·내부 대사 ①이 쓰는 날짜 (8-2 C). 처리 일시(`CREATED_AT`)보다 늦을 수 없다 (CK). 열린 달(또는 승인받아 재개한 달)만 넣을 수 있고 애플리케이션이 월 마감 테이블로 검사한다.'),
 ]),
 ('실물 증감', [
  dqty('NORMAL_DELTA_QTY','정상 수량 증감','Normal Quantity Delta','부호 있음. 사유별 방향은 CK (예: 판매 출고는 <= 0).'),
  dqty('INSPECTION_PENDING_DELTA_QTY','검수 대기 수량 증감','Inspection Pending Quantity Delta','생산 입고·반품 입고는 +, 입고 검수·반품 검수는 − (6-3 B, 7-2 A).'),
  dqty('DEFECTIVE_DELTA_QTY','불량 수량 증감','Defective Quantity Delta','검수·불량 전환은 +, 수선 복귀·처분은 − (7-4 A).'),
  dqty('HOLD_DELTA_QTY','보류 수량 증감','Hold Quantity Delta','보류 설정은 +, 보류 해제는 − (3-6 A).'),
 ]),
 ('원천 문서', [
  ref('SHIPMENT_ID','원천 배송 출고 식별 번호','Source Delivery Shipment Identifier',
      desc='판매 출고·재발송 출고·비주문 출고 (1-5 A). 배송 출고 행을 만드는 트랜잭션에서 넣는다. 출고 원인은 배송 출고 요청의 원인 코드에서 옮겨 사유를 고른다 (7-1 A).'),
  ref('WAYBILL_ID','원천 회수 운송장 식별 번호','Source Pickup Waybill Identifier',
      desc='반품 입고 (7-2 A). 회수 운송장 배송 완료(창고 도착) 처리와 같은 트랜잭션. 결정 원문의 "배송 패키지 ID"는 배송 DC-61 A로 운송장이 됐다.'),
  ref('CLAIM_INSPECTION_ID','원천 클레임 검수 결과 식별 번호','Source Claim Inspection Result Identifier',
      desc='반품 검수 (7-2 A). 클레임 설계 뒤 이름 확정.'),
  ref('CLAIM_REPAIR_ID','원천 클레임 수선 식별 번호','Source Claim Repair Identifier',
      desc='수선 사용 (수선에 쓴 단추·실, 3-8 A, T-7 A). 수선 건마다 1행. 클레임 설계 뒤 이름 확정.'),
  ref('RECEIPT_ID','원천 WMS 입고 식별 번호','Source WMS Receipt Identifier',
      desc='생산 입고 (도착, 6-3 B). WMS 설계 뒤 이름 확정. 계획은 아래 `INBOUND_PLAN_ID`에 따로 남는다 (T-5 A).'),
  ref('RECEIPT_INSPECTION_ID','원천 WMS 입고 검수 식별 번호','Source WMS Receipt Inspection Identifier',
      desc='입고 검수 (6-3 B). WMS 설계 뒤 이름 확정.'),
  ref('DISPOSAL_WORK_ID','원천 WMS 처분 작업 식별 번호','Source WMS Disposal Work Identifier',
      desc='수선 복귀, 폐기, 업체 반품, 일괄 매각 (7-4 A). 화물 출고는 배송을 거치지 않는다. 폐기 증빙 첨부는 WMS 넘김 사항. WMS 설계 뒤 이름 확정.'),
  ref('PACKAGING_USAGE_ID','원천 WMS 포장재 사용 집계 식별 번호','Source WMS Packaging Usage Summary Identifier',
      desc='포장재 사용. 하루 사용량을 일괄 차감한다 (T-7 A). WMS 설계 뒤 이름 확정.'),
  fk('STOCK_EXCEPTION_ID','원천 재고 예외 식별 번호','Source Stock Exception Identifier','INV_STOCK_EXCEPTION','Y','',
     '실사 조정 (7-7 A, 8-8 후속 B). 대사 차이·현장 발견 예외 행이 조정 요청 역할을 한다. 같은 INV 안이라 FK다 (2-4 A). 예외는 파티션이 없어 FK가 파티션 제거를 막지 않는다 (T-2 A).'),
  ref('STOCKTAKE_ID','관련 WMS 실사 식별 번호','Related WMS Stocktake Identifier',
      desc='실사 조정에서 실물을 센 WMS 실사 (1-3 A). 실사 조정이 아니면 NULL. [확인 필요: 원천은 예외 ID이고 이 컬럼은 선택(정확히 하나 CK에 넣지 않음)이라는 제안]'),
 ]),
 ('관련 입고 예정', [
  fk('INBOUND_PLAN_ID','관련 입고 예정 식별 번호','Related Inbound Plan Identifier','INV_INBOUND_PLAN','Y','',
     '사유가 생산 입고 또는 입고 검수이면 NOT NULL, 다른 사유이면 NULL (CK, T-5 A, IC-6 A로 입고 검수 추가). 입고 검수 원장은 이 차수의 검수 누계를 함께 고친다. 원가 경로 "입고 원장 → 입고 예정 → SCM 발주 라인" (6-5 A). 예정 없이 들어온 물건은 관리자가 입고 예정을 먼저 등록한다 (6-1 A).'),
 ]),
 ('정정', [
  ref('REVERSED_STOCK_LEDGER_ID','정정 대상 원래 원장 식별 번호','Reversed Original Stock Ledger Identifier',
      desc='NOT NULL이면 정정 행이다. 원래 행과 같은 사유를 쓰고 증감은 모두 반대다 (T-6 B). 한 행은 한 번만 정정한다 (UK). 원장 파티션 제거를 막지 않도록 FK 없이 둔다. '
           '원래 행과 같은 현재고·사유인지는 애플리케이션이 검사한다. 마감한 달의 행을 정정하면 정정 행의 업무 일자는 열린 달이나 재개한 달이다 (8-2 C).', extra='UK'),
 ]),
 ('세부 사유·승인', [
  cd('HOLD_REASON_CD','보류 사유 코드','Hold Reason Code','Y',
     desc='사유가 보류 설정이면 NOT NULL, 다른 사유이면 NULL (CK, 3-6 A, 7-1 A). 지금 보류 중인 내역은 원장에서 집계한다.'),
  cd('ADJUSTMENT_DETAIL_REASON_CD','실사 조정 세부 사유 코드','Stocktake Adjustment Detail Reason Code','Y',
     desc='사유가 실사 조정이면 NOT NULL, 다른 사유이면 NULL (CK, 7-7 A). 감모손실과 입력 오류를 나눈다.'),
  ref('APPROVED_ADMIN_ID','조정 승인 관리자 식별 번호','Adjustment Approving Administrator Identifier',
      desc='실사 조정 차이가 기준 수량(공통코드 정책값)을 넘으면 필수 (7-7 A). CHECK로 정책값을 읽을 수 없어 애플리케이션이 검사한다. ' + ADM),
  ('REASON_NOTE_CN','사유 설명','Reason Note','VARCHAR2(500)','Y','','',
   '원천 문서가 없는 사유(보류 설정, 보류 해제, 불량 전환)와 보류 사유 "기타", 정정 행이면 NOT NULL (CK, IC-5 A, IC-16 A). 정정 행에는 정정 이유를 적는다(예: "수량 입력 오류, 송장 기준 95개"). 다른 사유는 선택. 예: "고객 불만 3건으로 보풀 확인", "B-11 선반에서 오염 발견". '
   '실사 조정은 재고 예외의 처리 내용이 같은 역할이라 필수가 아니다. 길이는 바이트 기준(한글 약 160자)이고 단위는 공통 규칙(주문 OC-115)을 따른다.'),
 ]),
 ],
 idx=['IX LOCAL `STOCK_ID`, `BUSINESS_DT` (수불부 조회: 현재고 + 기간)',
      'IX `INBOUND_PLAN_ID`, `STOCK_EXCEPTION_ID` (FK, 입고 예정·예외 삭제 전 검사, T-2 A, T-3 A)',
      'IX 원천 컬럼 9개 (값 참조, 원천에서 원장을 찾는 조회와 매일 검증)',
      'UK `LEDGER_KEY_VAL`, UK `REVERSED_STOCK_LEDGER_ID` (전역 인덱스)'],
 check=['사유별 원천: 원천 컬럼 9개(`SHIPMENT_ID`~`STOCK_EXCEPTION_ID`) 중 사유에 맞는 하나만 NOT NULL, 나머지는 NULL (2-4 A). 보류 설정·보류 해제·불량 전환은 모두 NULL '
        '[확인 필요: 원천 문서 없이 관리자가 처리하는 사유. 행위자는 `CREATED_BY`]. 정정 행은 원래 행과 같은 원천 컬럼을 채운다',
        '사유별 증감 방향: 사유마다 + / − / 0인 버킷을 고정한다. `REVERSED_STOCK_LEDGER_ID`가 NOT NULL이면 방향을 모두 반대로 본다 (T-6 B)',
        '증감 4개가 모두 0인 행은 막는다',
        '사유가 생산 입고 또는 입고 검수이면 `INBOUND_PLAN_ID` NOT NULL, 아니면 NULL (T-5 A, IC-6 A)',
        '보류 설정·보류 해제·불량 전환이거나 `HOLD_REASON_CD = OTHER`이거나 정정 행(`REVERSED_STOCK_LEDGER_ID` NOT NULL)이면 `REASON_NOTE_CN` NOT NULL (IC-5 A, IC-16 A)',
        '`HOLD_REASON_CD`는 보류 설정일 때만, `ADJUSTMENT_DETAIL_REASON_CD`는 실사 조정일 때만 NOT NULL',
        '`BUSINESS_DT <= TRUNC(CREATED_AT)` (8-2 C)',
        '창고 이동 출고·입고는 자리만 남긴 값이라 CK의 허용 사유에서 뺀다 (1-7 A, 창고를 늘릴 때 연다)'])

# =========================================================== 3. 재고 확보
table(t='INV_STOCK_COMMITMENT', ko='재고 확보 (주문·출고 요청이 잡은 수량)', en='Stock Commitment',
 desc='주문 상품 1개, 주문 사은품 1개, 주문 없는 출고 요청 상품 1개마다 1행 (4-2 A, 4-10 A). 예약 → 할당 → 종결로 진행하고, 실물이 없으면 입고 예정에 걸린다 (6-2 A, 4-8 B). '
      '현재고의 예약·할당 수량의 근거다 (2-3 C). 이름은 예약·할당 두 상태를 모두 담아 COMMITMENT(약속한 재고)로 했다 (T-10 A).',
 basis='1-2 A, 1-6 A, 2-3 C, 4-2 A, 4-3 A, 4-5 A, 4-7 A~4-10 A, 4-12 A, 5-6 A, 5-9 A, 6-2 A, 6-4 B, 8-3 A, 8-9 B, 8-9 후속 A, T-1 A, T-10 A, IC-9 A, IC-10 B',
 pk='대리 PK `SEQ_INV_STOCK_COMMITMENT`', cache=100,
 delete='삭제하지 않는다 (상태로 처리). 확보 일시 기준 5년이 지난 파티션을 제거한다. 제거 전에 진행 중(종결이 아닌) 행이 0인지 검사한다 (8-9 후속 A)',
 part='확보 일시(`COMMITTED_AT`) 월 INTERVAL 파티션 (8-9 후속 A). 재고 예외는 이 테이블을 FK 없이 가리켜 파티션 제거가 막히지 않는다 (T-1 A)',
 keep='확보 일시 + 5년 (8-9 B, 8-9 후속 A)',
 cols=[
 ('식별', [
  ('STOCK_COMMITMENT_ID','재고 확보 고유 식별 번호','Stock Commitment Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK','N','','창고와 품목은 현재고 행에서 읽는다 (1-6 A).'),
  ref('ORDER_ITEM_ID','대상 주문 상품 식별 번호','Target Order Item Identifier',
      desc='판매 상품 주문. 대상 3개 중 정확히 하나 (CK, 4-2 A). 주문 쪽 ID라 FK 없음 (주문 10-10 C).'),
  ref('ORDER_FREEBIE_ID','대상 주문 사은품 식별 번호','Target Order Freebie Identifier',
      desc='사은품 (주문 4-4 A). 사은품 확보가 0행이면 주문 사은품 행을 만들지 않고 주문을 진행한다 (5-6 A).'),
  ref('SHIPMENT_REQUEST_ITEM_ID','대상 출고 요청 상품 식별 번호','Target Shipment Request Item Identifier',
      desc='주문 없는 확보: 교환·사고·반송·출고 누락·수선 재발송, 비주문 출고 (4-10 A). 출고 요청을 만들 때 바로 할당으로 잡는다. 원인은 출고 요청의 원인 코드가 갖는다.'),
  fk('INBOUND_PLAN_ID','걸린 입고 예정 식별 번호','Hung Inbound Plan Identifier','INV_INBOUND_PLAN','Y','',
     '실물이 아직 없어 입고 예정에 걸린 확보 (6-2 A). 예약 판매의 결제 대기(예약)와 결제 완료(입고 대기), 출고 때 실물이 모자라 옮긴 확보(4-8 B). '
     'NOT NULL인 확보는 현재고의 예약·할당에 넣지 않는다. 일부 출고된 확보도 걸 수 있고, 그때는 남은 수량 전부를 건다 (IC-9 A). 다음 차수로 옮기면 값을 바꾼다 (5-9 A). 실물로 옮기면(할당) NULL로 비운다. '
     '걸기·옮기기는 확보 처리 이력에 남는다 (IC-10 B).'),
 ]),
 ('상태', [
  cd('STOCK_COMMITMENT_STATUS_CD','재고 확보 상태 코드','Stock Commitment Status Code',
     desc='예약, 할당, 입고 대기, 종결 (4-3 A, 6-2 A). 예약 → 할당은 결제 완료 트랜잭션에서 (4-5 A). 상태 이력 테이블은 두지 않는다. 일반 흐름은 일시 컬럼 3개로, 해제·입고 대기 전환·차수 이동은 확보 처리 이력으로 본다 (IC-10 B).'),
 ]),
 ('수량', [
  qty('COMMITTED_QTY','확보 수량','Committed Quantity','처음 잡은 수량.',d='',ck='CK (>= 1)'),
  qty('SHIPPED_QTY','출고 수량','Shipped Quantity','배송 출고 트랜잭션에서 늘린다 (1-5 A). 현재고의 정상·할당도 함께 줄어든다.'),
  qty('RELEASED_QTY','해제 수량','Released Quantity','결제 만료, 취소, 결품 등으로 푼 수량 (4-3 A). 남은 수량 = 확보 − 출고 − 해제.'),
 ]),
 ('해제', [
  cd('RELEASE_REASON_CD','해제 사유 코드','Release Reason Code','Y',
     desc='해제 수량이 0보다 크면 NOT NULL (CK, 4-3 A, 5-9 A). 해제가 여러 번이면 마지막 사유이고, 건별 수량과 사유는 확보 처리 이력에 있다 (IC-10 B).'),
 ]),
 ('일시', [
  ('COMMITTED_AT','확보 일시','Committed At',TS,'N','SYSTIMESTAMP','파티션 키',
   '행을 만든 시각 (8-9 후속 A). 입고 대기 확보를 할당할 때 출고 기한이 같으면 이 순서로 고른다 (6-4 B).'),
  ('ALLOCATED_AT','할당 일시','Allocated At',TS,'Y','','',
   '마지막으로 할당 상태가 된 시각. 실물이 모자랄 때 가장 늦게 할당된 확보부터 입고 대기로 옮긴다 (4-8 B). 상태가 할당이면 NOT NULL (CK).'),
  ('CLOSED_AT','종결 일시','Closed At',TS,'Y','','','상태가 종결이면 NOT NULL, 아니면 NULL (CK).'),
 ]),
 ],
 idx=['IX LOCAL `STOCK_ID` (FK, 내부 대사 ②)',
      'IX `INBOUND_PLAN_ID` (FK, 내부 대사 ③, 입고 때 할당 순서, 입고 예정 삭제 전 검사)',
      'IX `ORDER_ITEM_ID`, `ORDER_FREEBIE_ID`, `SHIPMENT_REQUEST_ITEM_ID` (값 참조)',
      'UK 함수 기반: 종결이 아닐 때만 `ORDER_ITEM_ID` (주문 상품마다 진행 중 확보 1행, 4-9 A) [확인 필요: 사은품·출고 요청 상품에도 같은 UK를 둘지]',
      'IX (`STOCK_COMMITMENT_STATUS_CD`, `COMMITTED_AT`) (오래 남은 예약 감시, 신호 1)'],
 check=['대상 3개(`ORDER_ITEM_ID`, `ORDER_FREEBIE_ID`, `SHIPMENT_REQUEST_ITEM_ID`) 중 정확히 하나만 NOT NULL (4-2 A, 4-10 A)',
        '`SHIPPED_QTY + RELEASED_QTY <= COMMITTED_QTY`. 종결이면 `SHIPPED_QTY + RELEASED_QTY = COMMITTED_QTY` (4-3 A)',
        '입고 대기이면 `INBOUND_PLAN_ID` NOT NULL, 할당이면 NULL (6-2 A). 예약은 둘 다 된다 (예약 판매 결제 대기)',
        '할당이면 `ALLOCATED_AT` NOT NULL. 종결이면 `CLOSED_AT` NOT NULL, 아니면 NULL',
        '`RELEASED_QTY > 0`이면 `RELEASE_REASON_CD` NOT NULL'])

# =========================================================== 3-2. 재고 확보 처리 이력
table(t='INV_STOCK_COMMITMENT_EVENT', ko='재고 확보 처리 이력 (일반 흐름이 아닌 처리)', en='Stock Commitment Event',
 desc='확보 행에 일반 흐름(예약 → 할당 → 출고)이 아닌 처리가 있을 때마다 1행 (IC-10 B): 부분·전체 해제, 할당에서 입고 대기로 전환(4-8 B), 입고 차수 이동(5-9 A). '
      '선물 옵션 변경은 해제(사유 선물 옵션 변경) 행에 새 확보 행을 함께 적는다 (4-9 A). 확보 행 갱신과 같은 트랜잭션에서 넣고, 처리 키 UK로 같은 요청의 재시도가 두 번 반영되지 않게 막는다. '
      '일반 흐름의 경과는 확보 행의 일시 3개로 본다.',
 basis='4-3 A, 4-8 B, 4-9 A, 5-9 A, 8-9 후속 A, IC-10 B',
 pk='대리 PK `SEQ_INV_STOCK_COMMITMENT_EVENT`', cache=20,
 delete='삭제하지 않는다 (거래 기록). 확보 파티션을 제거할 때 같은 범위의 파티션이 함께 제거된다',
 part='참조 파티션 (`FK_INV_STOCK_COMMITMENT_EVENT_STOCK_COMMITMENT_ID`). 확보의 확보 일시 월 파티션을 따라간다 (IC-10 B) [확인 필요: INTERVAL 참조 파티션과 전역 UK]',
 keep='확보와 같이 확보 일시 + 5년 (8-9 B, IC-10 B)',
 cols=[
 ('식별', [
  ('STOCK_COMMITMENT_EVENT_ID','재고 확보 처리 이력 고유 식별 번호','Stock Commitment Event Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_COMMITMENT_ID','재고 확보 식별 번호','Stock Commitment Identifier','INV_STOCK_COMMITMENT','N','참조 파티션 키',
     '처리한 확보 행. 참조 파티션이라 확보 파티션과 함께 제거되어 ORA-02266에 걸리지 않는다.'),
  cd('STOCK_COMMITMENT_EVENT_TYPE_CD','확보 처리 유형 코드','Stock Commitment Event Type Code',
     desc='해제, 입고 대기 전환, 입고 차수 이동 (IC-10 B).'),
  ('EVENT_KEY_VAL','처리 키','Event Idempotency Key','VARCHAR2(100)','N','','UK (`STOCK_COMMITMENT_ID`, `EVENT_KEY_VAL`)',
   '요청한 쪽이 만든 키 (예: `CLM:클레임 ID:처리 차수`, `PAY:결제 만료 배치 실행 ID`). 같은 키로 다시 오면 UK 위반으로 확보 행 갱신까지 함께 롤백한다. '
   '상태가 할당 그대로인 부분 해제의 재시도를 상태 비교로는 가를 수 없어서 둔다 (IC-10 B).'),
 ]),
 ('수량과 사유', [
  qty('EVENT_QTY','처리 수량','Event Quantity','해제 수량, 또는 입고 대기로 옮기거나 다른 차수로 옮긴 남은 수량 (IC-9 A).',d='',ck='CK (>= 1)'),
  cd('RELEASE_REASON_CD','해제 사유 코드','Release Reason Code','Y',
     desc='해제이면 NOT NULL, 아니면 NULL (CK). 확보 행에는 마지막 사유만 남고 건별 사유는 이 행에 남는다 (IC-10 B).'),
 ]),
 ('입고 차수', [
  fk('FROM_INBOUND_PLAN_ID','처리 전 입고 예정 식별 번호','Inbound Plan Before Event Identifier','INV_INBOUND_PLAN','Y','',
     '처리 전에 걸려 있던 차수. 입고 차수 이동이면 NOT NULL, 입고 대기 전환이면 NULL (CK). 입고 대기 확보의 해제(공급 곤란)면 그 차수.'),
  fk('TO_INBOUND_PLAN_ID','처리 후 입고 예정 식별 번호','Inbound Plan After Event Identifier','INV_INBOUND_PLAN','Y','',
     '입고 대기 전환·입고 차수 이동이면 NOT NULL, 해제이면 NULL (CK).'),
 ]),
 ('대체 확보', [
  ref('REPLACEMENT_STOCK_COMMITMENT_ID','대체 재고 확보 식별 번호','Replacement Stock Commitment Identifier',
      desc='해제 사유가 선물 옵션 변경이면 NOT NULL (CK, 4-9 A). 새로 만든 확보 행. 같은 테이블 다른 파티션이라 FK 없이 둔다.'),
 ]),
 ('일시', [
  ('OCCURRED_AT','처리 일시','Event Occurred At',TS,'N','SYSTIMESTAMP','','확보 행을 고친 트랜잭션 시각.'),
 ]),
 ],
 idx=['IX LOCAL `STOCK_COMMITMENT_ID` (FK)',
      'UK (`STOCK_COMMITMENT_ID`, `EVENT_KEY_VAL`) (재시도 이중 반영 방지, 파티션 제거 때 `UPDATE GLOBAL INDEXES`)',
      'IX `FROM_INBOUND_PLAN_ID`, `TO_INBOUND_PLAN_ID` (FK, 입고 예정 삭제 전 검사)'],
 check=['해제이면 `RELEASE_REASON_CD` NOT NULL, `TO_INBOUND_PLAN_ID` NULL. 해제가 아니면 `RELEASE_REASON_CD` NULL',
        '입고 대기 전환이면 `FROM_INBOUND_PLAN_ID` NULL, `TO_INBOUND_PLAN_ID` NOT NULL',
        '입고 차수 이동이면 둘 다 NOT NULL이고 서로 다름',
        '`RELEASE_REASON_CD = GIFT_OPTION_CHANGED`이면 `REPLACEMENT_STOCK_COMMITMENT_ID` NOT NULL, 아니면 NULL'])

# =========================================================== 4. 입고 예정
table(t='INV_INBOUND_PLAN', ko='입고 예정 (품목별 입고 차수)', en='Inbound Plan',
 desc='(현재고 행, 입고 차수)마다 1행 (6-1 A). 예약 판매 한도와 예정일 고지, 실물이 모자랄 때 기다릴 수 있는지를 판단하는 근거다 (6-2 A, 4-8 B). '
      'SCM 발주가 확정되면 만들고, SCM 설계 전까지는 관리자가 직접 등록한다. 생산 입고 원장이 이 행을 가리켜 원가 경로가 이어진다 (T-5 A, 6-5 A).',
 basis='4-8 B, 5-9 A, 6-1 A~6-5 A, 8-3 A, T-3 A, T-5 A, T-9 A, T-10 A, T-11 A, IC-6 A, IC-8 A',
 pk='대리 PK `SEQ_INV_INBOUND_PLAN`', cache=20,
 delete='삭제하지 않는다 (상태로 처리). 완료·취소 + 5년이 지나고 가리키는 확보·원장·확보 처리 이력이 없는 행을 일 배치가 나눠서 DELETE한다 (T-3 A, 선행 11)',
 part='없음 (T-3 A). 확보·원장이 FK로 가리키는 부모라 파티션 제거가 ORA-02266에 걸린다',
 keep='종료 일시(`CLOSED_AT`) + 5년, 가리키는 확보·원장이 없을 때 (T-3 A)',
 cols=[
 ('식별', [
  ('INBOUND_PLAN_ID','입고 예정 고유 식별 번호','Inbound Plan Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK'),
  ('INBOUND_ROUND_NO','입고 차수','Inbound Round Number','NUMBER(3)','N','','CK (>= 1)',
   '같은 현재고 행 안에서 1부터 매긴다. (`STOCK_ID`, `INBOUND_ROUND_NO`) UK. WMS의 입고 차수(로트, 1-4 A)와는 다른 번호다 [확인 필요: WMS 입고 차수와 맞출지].'),
  ref('PURCHASE_ORDER_LINE_ID','SCM 발주 라인 식별 번호','SCM Purchase Order Line Identifier',
      desc='SCM 발주에서 만들면 채운다 (6-1 A). 관리자가 직접 등록하면 NULL. SCM 설계 뒤 이름 확정. 매입 단가는 이 경로로 SCM에서 읽는다 (6-5 A).'),
 ]),
 ('상태', [
  cd('INBOUND_PLAN_STATUS_CD','입고 예정 상태 코드','Inbound Plan Status Code',desc='예정, 일부 입고, 완료, 취소 (6-1 A).'),
 ]),
 ('일정', [
  ('PLANNED_DT','현재 입고 예정 일자','Current Planned Inbound Date','DATE','N','','',
   '고객 고지와 출고 기한 판단에 쓰는 날짜. 밀리면 고치고, 걸린 확보 전부에 지연 통지를 한다 (5-9 A).'),
  ('FIRST_PLANNED_DT','최초 입고 예정 일자','First Planned Inbound Date','DATE','N','','',
   '처음 등록한 예정일. 고치지 않는다. 지연 일수 = 현재 − 최초 (T-9 A, 배송 DC-56 A와 같은 방식).'),
  cd('DELAY_REASON_CD','입고 지연 사유 코드','Inbound Delay Reason Code','Y',
     desc='마지막 예정일 변경의 사유 (T-9 A). 현재 예정일이 최초보다 늦으면 NOT NULL (CK). 중간 변경 경로는 관리자 작업 로그로 본다.'),
 ]),
 ('수량', [
  qty('PLANNED_QTY','예정 수량','Planned Quantity','',d='',ck='CK (>= 1)'),
  qty('RECEIVED_QTY','입고 수량','Received Quantity','도착 때 늘린다 (6-3 B, 생산 입고 원장과 같은 트랜잭션).'),
  qty('COMMITTED_QTY','확보 수량','Committed Quantity',
      '이 차수에 걸린 진행 중 확보(`INBOUND_PLAN_ID`가 이 행)의 남은 수량(확보 − 출고 − 해제) 합계 (6-2 A, 내부 대사 ③, IC-9 A). 현재고처럼 증감 UPDATE 한 문장으로만 바꾼다. '
      '새 예약 판매 한도는 GREATEST(예정 − 입고 − 확보, 0)이고 애플리케이션이 검사한다. 도착했지만 검수 전인 수량은 기존 확보만 받치고 새 예약에는 열지 않는다 (IC-8 A).'),
  qty('INSPECTED_NORMAL_QTY','검수 양품 수량 (누계)','Inspected Normal Quantity (Cumulative)',
      '입고 검수 원장과 같은 트랜잭션에서 늘린다 (IC-6 A). 차수별 불량률, 업체 반품·매입 차감(SCM)의 근거. 원장(입고 검수, 이 차수)의 정상 증감 합계와 같다.'),
  qty('INSPECTED_DEFECTIVE_QTY','검수 불량 수량 (누계)','Inspected Defective Quantity (Cumulative)',
      '입고 검수 원장과 같은 트랜잭션에서 늘린다 (IC-6 A). 입고 − 양품 − 불량 = 아직 검수하지 않은 수량.'),
 ]),
 ('종료', [
  ('CLOSED_AT','종료 일시 (완료·취소)','Closed At (Completed / Canceled)',TS,'Y','','',
   '상태가 완료·취소이면 NOT NULL, 아니면 NULL (CK). 보존 기간의 기산점 (T-3 A).'),
 ]),
 ],
 idx=['UK (`STOCK_ID`, `INBOUND_ROUND_NO`)',
      'IX `PURCHASE_ORDER_LINE_ID` (값 참조)',
      'IX (`INBOUND_PLAN_STATUS_CD`, `PLANNED_DT`) (예정일 지난 미입고 감시, 신호 4)'],
 check=['`COMMITTED_QTY <= GREATEST(PLANNED_QTY - INSPECTED_NORMAL_QTY - INSPECTED_DEFECTIVE_QTY, 0)` (6-2 A, IC-8 A). 검수 양품이 확보보다 적으면 남는 확보는 5-9 A로 다음 차수에 옮기거나 해제한 뒤 검수 누계를 늘린다',
        '`PLANNED_DT > FIRST_PLANNED_DT`이면 `DELAY_REASON_CD` NOT NULL (T-9 A)',
        '`INSPECTED_NORMAL_QTY + INSPECTED_DEFECTIVE_QTY <= RECEIVED_QTY` (IC-6 A)',
        '완료·취소이면 `CLOSED_AT` NOT NULL, 아니면 NULL. 취소·완료이면 `COMMITTED_QTY = 0` (걸린 확보를 다음 차수로 옮기거나 해제한 뒤, 5-9 A)'])

# =========================================================== 5. 재고 스냅샷
table(t='INV_STOCK_SNAPSHOT', ko='재고 스냅샷 (일별·월말 수량)', en='Stock Snapshot',
 desc='매일 마감 시각에 그날 원장 변화가 있었거나 수량이 바뀐(현재고 `BALANCE_CHANGED_AT`이 그날 안) 행만, 월말에는 모든 행을 남긴다 (8-1 A, IC-14 A, IC-24 A). 예약·할당·안전 재고만 바뀐 날도 남고, 등급·기준만 바뀐 날은 남지 않는다. 그 달의 사유별 누계 수불을 함께 남겨 월말 행이 10년짜리 월 수불부가 된다 (IC-7 A). 특정 날짜 수량은 그 날 이전의 가장 가까운 스냅샷 + 그 사이 원장(업무 일자)으로 계산한다. '
      '월 마감을 재개하면 그 달 이후 스냅샷의 실물 4개와 월 누계 4개만 원장으로 다시 계산해 고치고, 예약·할당·안전 재고는 당시 값을 둔다. 그 뒤 내부 대사 ①④를 그 달부터 다시 돌린다 (8-2 C, IC-15 A). '
      '그래서 스냅샷에는 판매 가능 CHECK를 두지 않는다(정정한 실물이 당시 예약보다 적을 수 있다). Oracle 스케줄러가 만든다 (선행 11).',
 basis='8-1 A, 8-2 C, 8-3 A, 8-6 C, T-10 A, T-11 A, IC-7 A, IC-14 A, IC-15 A, IC-24 A',
 pk='대리 PK `SEQ_INV_STOCK_SNAPSHOT`', cache=100,
 delete='일 스냅샷: 5년이 지난 파티션에서 월말이 아닌 행을 나눠서 DELETE. 월말 스냅샷: 10년이 지나면 파티션 제거 (8-6 C). 재개한 달의 다시 계산은 행을 지우지 않고 실물·월 누계 컬럼만 갱신한다 (IC-15 A)',
 part='스냅샷 일자(`SNAPSHOT_DT`) 월 INTERVAL 파티션 (8-6 C)',
 keep='일 스냅샷 5년, 월말 스냅샷 10년 (8-6 C, 기말 재고 수량은 장부 성격) [확인 필요: 상법 33조 장부 10년]',
 cols=[
 ('식별', [
  ('STOCK_SNAPSHOT_ID','재고 스냅샷 고유 식별 번호','Stock Snapshot Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK'),
  ('SNAPSHOT_DT','스냅샷 일자','Snapshot Date','DATE','N','','파티션 키','마감 시각 기준 하루 (마감 시각은 공통코드 정책값). (`STOCK_ID`, `SNAPSHOT_DT`) UK.'),
  yn('MONTH_END_YN','월말 스냅샷 여부','Month-End Snapshot Flag','N','Y면 모든 현재고 행을 남긴 월말 행이고 10년 보존한다 (8-6 C).'),
 ]),
 ('실물 수량', [
  qty('NORMAL_QTY','정상 수량','Normal Quantity'),
  qty('INSPECTION_PENDING_QTY','검수 대기 수량','Inspection Pending Quantity'),
  qty('DEFECTIVE_QTY','불량 수량','Defective Quantity'),
  qty('HOLD_QTY','보류 수량','Hold Quantity'),
 ]),
 ('확보 수량', [
  qty('RESERVED_QTY','예약 수량','Reserved Quantity'),
  qty('ALLOCATED_QTY','할당 수량','Allocated Quantity'),
 ]),
 ('안전 재고', [
  qty('SAFETY_STOCK_QTY','안전 재고 수량','Safety Stock Quantity','그날의 안전 재고 (8-1 A).'),
 ]),
 ('월 누계 수불', [
  qty('MTD_INBOUND_QTY','월 누계 입고 수량','Month-to-Date Inbound Quantity',
      '그 달 1일부터 스냅샷 일자까지 생산 입고·반품 입고 합계 (IC-7 A). 월말 행에서는 그 달 전체 합계라 10년 보존되는 월 수불부가 된다. 정정 행은 원래 사유에 넣어 순액이다.'),
  qty('MTD_OUTBOUND_QTY','월 누계 출고 수량','Month-to-Date Outbound Quantity','판매·재발송·비주문 출고로 나간 수 (양수로 적음, IC-7 A).'),
  qty('MTD_DISPOSAL_QTY','월 누계 처분 수량','Month-to-Date Disposal Quantity','폐기·업체 반품·일괄 매각으로 나간 수 (양수로 적음, IC-7 A).'),
  ('MTD_ADJUST_QTY','월 누계 조정 수량','Month-to-Date Adjustment Quantity',QTY,'N','0','',
   '실사 조정, 포장재 사용, 수선 사용의 증감 합계 (부호 있음, IC-7 A). 검수·보류·불량 전환·수선 복귀 같은 상태 이동은 실물 합계를 바꾸지 않아 넣지 않는다. '
   '내부 대사 ④: 전월말 실물 합계 + 입고 − 출고 − 처분 + 조정 = 당월말 실물 합계.'),
 ]),
 ],
 idx=['UK LOCAL (`STOCK_ID`, `SNAPSHOT_DT`) (파티션 키를 포함해 로컬 인덱스로 둔다)'],
 check=['수량 7개와 월 누계 입고·출고·처분은 각각 >= 0. 월 누계 조정은 부호 있음 (IC-7 A)'])

# =========================================================== 6. 재고 월 마감
table(t='INV_MONTHLY_CLOSING', ko='재고 월 마감', en='Inventory Monthly Closing',
 desc='한 달에 1행 (회사 단위, T-11 A). 마감한 달에는 원장 업무 일자를 넣을 수 없고, 승인을 받아 재개하면 넣을 수 있다 (8-2 C). 재개하면 그 달 이후 스냅샷을 다시 계산한다. 회계 마감과 맞추는 일은 정산 넘김 사항이다.',
 basis='8-2 C, T-10 A, T-11 A',
 pk='대리 PK `SEQ_INV_MONTHLY_CLOSING` + 마감 연월 UK', cache=20,
 delete='삭제하지 않는다 (상태로 처리)', part='없음 (1년에 12행)',
 keep='[확인 필요: 보존 기간. 월말 스냅샷과 같이 10년 제안]',
 cols=[
 ('식별', [
  ('MONTHLY_CLOSING_ID','재고 월 마감 고유 식별 번호','Inventory Monthly Closing Unique Identifier',ID,'N','','PK',''),
  ('CLOSING_YM','마감 연월','Closing Year-Month','VARCHAR2(6)','N','','UK, CK (YYYYMM)','예: `202612`. 회사 단위라 창고 컬럼이 없다 (T-11 A).'),
 ]),
 ('상태', [
  cd('MONTHLY_CLOSING_STATUS_CD','월 마감 상태 코드','Monthly Closing Status Code',desc='열림, 마감, 재개 (8-2 C). 재개한 달을 다시 마감하면 마감으로 돌아간다.'),
 ]),
 ('마감', [
  ('CLOSED_AT','마감 일시','Closed At',TS,'Y','','','마지막으로 마감한 시각. 상태가 마감이면 NOT NULL (CK).'),
  ref('CLOSED_ADMIN_ID','마감 관리자 식별 번호','Closing Administrator Identifier',desc=ADM),
 ]),
 ('재개', [
  ('REOPEN_REASON_CN','재개 사유','Reopen Reason','VARCHAR2(1000)','Y','','','상태가 재개이면 NOT NULL (CK). 다시 마감해도 마지막 재개 사유를 남긴다. 이전 재개 경위는 관리자 작업 로그로 본다.'),
  ref('REOPEN_APPROVED_ADMIN_ID','재개 승인 관리자 식별 번호','Reopen Approving Administrator Identifier',desc='상태가 재개이면 NOT NULL (CK). ' + ADM),
  ('REOPENED_AT','재개 일시','Reopened At',TS,'Y','','','상태가 재개이면 NOT NULL (CK).'),
 ]),
 ('동시 갱신', [rowver()]),
 ],
 check=['마감이면 `CLOSED_AT`, `CLOSED_ADMIN_ID` NOT NULL',
        '재개이면 `REOPEN_REASON_CN`, `REOPEN_APPROVED_ADMIN_ID`, `REOPENED_AT` NOT NULL'])

# =========================================================== 7. 재고 예외
table(t='INV_STOCK_EXCEPTION', ko='재고 예외 (대사 차이·감시 신호)', en='Stock Exception',
 desc='대사 차이(INV·WMS, 내부 대사 ①②③)와 현장 발견, 감시 신호 1건마다 1행 (8-8 B, 8-8 후속 B, T-8 A). 배치가 신호마다 행을 만들고 담당자가 처리한다. 자동으로 수량을 고치지 않는다 (1-8 A, 8-3 A). '
      '대사 차이·현장 발견 행은 실사 조정의 요청 역할을 하고, 조정 원장이 이 행을 가리킨다 (7-7 A). 결정 원문의 "대사 차이 테이블"은 이 테이블에 합쳤다.',
 basis='1-8 A, 2-4 A, 2-7 A, 7-7 A, 8-3 A, 8-8 B, 8-8 후속 B, T-1 A, T-2 A, T-8 A, T-10 A, IC-3 A, IC-7 A, IC-11 A~IC-13 A',
 pk='대리 PK `SEQ_INV_STOCK_EXCEPTION`', cache=20,
 delete='삭제하지 않는다 (상태로 처리). 처리 완료 + 1년이 지나고 가리키는 원장이 없는 행을 일 배치가 나눠서 DELETE한다 (T-2 A). 조정으로 이어진 행은 원장(5년)이 지워진 뒤에야 지워진다',
 part='없음 (T-2 A). 원장이 FK로 가리키는 부모라 파티션 제거가 ORA-02266에 걸리고, 하루 수십 건이라 행 단위로 충분하다',
 keep='조정으로 이어진 행: 가리키는 원장과 같이 5년. 나머지: 처리 완료 + 1년 (T-2 A)',
 cols=[
 ('식별', [
  ('STOCK_EXCEPTION_ID','재고 예외 고유 식별 번호','Stock Exception Unique Identifier',ID,'N','','PK',''),
  cd('STOCK_EXCEPTION_TYPE_CD','재고 예외 유형 코드','Stock Exception Type Code',
     desc='대사 5개, 현장 발견, 감시 신호 6개 (T-8 A, IC-3 A, IC-7 A). 신호 3번(입고 대기 기한 위험)은 배송 출고 요청의 예외 수동 처리로, 신호 8번(반복 확보 실패)은 애플리케이션 로그로 본다. 유형마다 대상 컬럼이 정해져 있다 (`ATTR1`).'),
 ]),
 ('대상', [
  fk('STOCK_ID','대상 현재고 식별 번호','Target Stock on Hand Identifier','INV_STOCK','Y','',
     'INV·WMS 대사, 내부 대사 ①②④, 현장 발견, 검수 대기 적체, 오래된 보류, 재입고 수요, 리오더 기준 도달 (T-1 A, IC-3 A).'),
  ref('STOCK_COMMITMENT_ID','대상 재고 확보 식별 번호','Target Stock Commitment Identifier',
      desc='만료가 지났는데 남은 예약 (신호 1). 확보 파티션 제거를 막지 않도록 FK 없이 둔다 (T-1 A). 없는 ID가 들어가지 않게 애플리케이션이 막는다.'),
  fk('INBOUND_PLAN_ID','대상 입고 예정 식별 번호','Target Inbound Plan Identifier','INV_INBOUND_PLAN','Y','',
     '내부 대사 ③, 예정일이 지났는데 입고되지 않음 (신호 4) (T-1 A).'),
 ]),
 ('상태', [
  cd('STOCK_EXCEPTION_STATUS_CD','재고 예외 상태 코드','Stock Exception Status Code',
     desc='확인 중 → 조정 완료 / 조정 없음 (대사·현장 발견, 7-7 A), 확인 중 → 처리 완료 (감시 신호).'),
  ('DETECTED_AT','감지 일시','Detected At',TS,'N','SYSTIMESTAMP','','배치가 찾은 시각 (현장 발견이면 등록 시각).'),
 ]),
 ('대사 수량', [
  cd('RECONCILIATION_BUCKET_CD','대사 비교 수량 구분 코드','Reconciliation Compared Bucket Code','Y',
     desc='대사 유형만 NOT NULL (CK). INV·WMS 대사는 실물 합계(정상 + 검수 대기 + 불량 + 보류, 1-8 A, IC-12 A), 내부 대사 ①은 실물 버킷별, ②는 예약·할당, ③은 입고 예정 확보 (8-3 A), ④는 실물 합계 (IC-7 A). '
     '같은 대상의 버킷별 차이는 행이 따로다 (IC-11 A).'),
  ('RECONCILIATION_DT','대사 기준일','Reconciliation Base Date','DATE','Y','','',
   '비교한 재고의 날짜(업무 일자). 대사 유형만 NOT NULL (CK, IC-13 A). 장부 수량은 이 날짜 기준 값이다. 마감 재개 뒤 지난 날짜를 다시 대사하면 기준일과 감지 일시가 다르다(예: 기준일 11/30, 감지 12/1). UK에는 넣지 않는다.'),
  qty('BOOK_QTY','INV 장부 수량','INV Book Quantity','현재고(또는 입고 예정) 행의 그 시점 값. 대사 유형만 NOT NULL (CK).',d='',ck='CK (>= 0)',null='Y'),
  qty('COMPARED_QTY','비교 수량','Compared Quantity',
      'INV·WMS 대사는 WMS 선반 합계, 내부 대사는 스냅샷 + 원장 또는 확보 행 합계로 다시 계산한 값. 대사 유형만 NOT NULL (CK).',d='',ck='CK (>= 0)',null='Y'),
  ('DIFFERENCE_QTY','차이 수량 (가상 컬럼)','Difference Quantity (Virtual)',QTY,'Y','','가상 컬럼',
   '`COMPARED_QTY - BOOK_QTY`. 실사 조정 원장은 이 값을 보고 담당자가 실제로 센 차이로 넣는다 (2-6 A, 7-7 A). 대사 유형이 아니면 NULL.'),
 ]),
 ('처리', [
  ref('HANDLED_ADMIN_ID','처리 관리자 식별 번호','Handling Administrator Identifier',desc='처리 완료·조정 완료·조정 없음이면 NOT NULL (CK). ' + ADM),
  ('HANDLED_AT','처리 일시','Handled At',TS,'Y','','','처리를 마친 시각. 확인 중이 아니면 NOT NULL (CK). 보존 기간의 기산점 (T-2 A).'),
  ('HANDLING_CN','처리 내용','Handling Content','VARCHAR2(2000)','Y','','','확인 결과와 조치. 조정 없음이면 이유를 적는다 (7-7 A).'),
 ]),
 ('동시 갱신', [rowver()]),
 ],
 idx=['IX `STOCK_ID`, `INBOUND_PLAN_ID` (FK), `STOCK_COMMITMENT_ID` (값 참조)',
      'IX (`STOCK_EXCEPTION_STATUS_CD`, `DETECTED_AT`) (미처리 목록, 신호 5)',
      'UK 함수 기반: 확인 중일 때만 (유형, 대상 ID, 대사 비교 수량 구분) (같은 대상·유형·버킷의 확인 중 행을 하나로, 배치가 매일 다시 찾아도 새로 만들지 않음). 수량 구분이 NULL인 유형은 식 안에서 고정 값으로 바꾼다 (IC-11 A)'],
 check=['대상 3개(`STOCK_ID`, `STOCK_COMMITMENT_ID`, `INBOUND_PLAN_ID`) 중 유형에 맞는 하나만 NOT NULL (T-1 A, 선행 6). 유형-대상 조합은 CK로 고정한다',
        '대사 유형이면 `RECONCILIATION_BUCKET_CD`, `RECONCILIATION_DT`, `BOOK_QTY`, `COMPARED_QTY` NOT NULL, 아니면 모두 NULL (8-8 후속 B, IC-13 A)',
        '조정 완료·조정 없음은 대사·현장 발견 유형만, 처리 완료는 감시 신호 유형만 (7-7 A)',
        '확인 중이 아니면 `HANDLED_ADMIN_ID`, `HANDLED_AT` NOT NULL'])

TABLE_GROUPS = [
 ('수량·원장', ['INV_STOCK', 'INV_STOCK_LEDGER']),
 ('확보·입고 예정', ['INV_STOCK_COMMITMENT', 'INV_STOCK_COMMITMENT_EVENT', 'INV_INBOUND_PLAN']),
 ('마감·대사', ['INV_STOCK_SNAPSHOT', 'INV_MONTHLY_CLOSING', 'INV_STOCK_EXCEPTION']),
]

def vals(*v): return [(a, b, c, d, i) for i, (a, b, c, d) in enumerate(v, 1)]
CODES = {
 'STOCK_LEDGER_REASON_CD': vals(
   ('PRODUCTION_INBOUND','생산 입고','Production Inbound','입고. 검수 대기 +. 원천 WMS 입고, 관련 입고 예정 필수 (6-3 B, T-5 A). `ATTR1` 해당 없음'),
   ('INBOUND_INSPECTION','입고 검수','Inbound Inspection','입고. 검수 대기 −, 정상 +, 불량 +. 원천 WMS 입고 검수, 관련 입고 예정 필수 (6-3 B, IC-6 A). `ATTR1` 해당 없음'),
   ('RETURN_INBOUND','반품 입고','Return Inbound','입고. 검수 대기 +. 원천 회수 운송장 (7-2 A). `ATTR1` 해당 없음'),
   ('RETURN_INSPECTION','반품 검수','Return Inspection','입고. 검수 대기 −, 정상 +, 불량 +. 원천 클레임 검수 결과 (7-2 A). `ATTR1` 해당 없음'),
   ('SALES_SHIPMENT','판매 출고','Sales Shipment','출고. 정상 −. 원천 배송 출고 (1-5 A). `ATTR1` 매출원가'),
   ('RESHIP_SHIPMENT','재발송 출고','Reshipment','출고. 정상 −. 원천 배송 출고. 교환·사고·반송·누락·수선 재발송. `ATTR1` 클레임 귀책에 따름 (7-8 A)'),
   ('NON_ORDER_SHIPMENT','비주문 출고','Non-Order Shipment','출고. 정상 −. 원천 배송 출고. 회계 구분은 배송 `NON_ORDER_TYPE_CD`의 `ATTR` (7-8 A)'),
   ('HOLD_SET','보류 설정','Hold Set','상태 이동. 정상 −, 보류 +. 보류 사유 필수 (3-6 A). 원천 없음. `ATTR1` 해당 없음'),
   ('HOLD_RELEASE','보류 해제','Hold Release','상태 이동. 보류 −, 정상 +. 원천 없음. `ATTR1` 해당 없음'),
   ('DEFECT_TRANSFER','불량 전환','Defect Transfer','상태 이동. 정상(또는 보류) −, 불량 +. 선반에서 불량을 발견. 원천 없음. `ATTR1` 해당 없음'),
   ('REPAIR_RETURN','수선 복귀','Repair Return','상태 이동. 불량 −, 정상 +. 원천 WMS 처분 작업 (7-4 A). `ATTR1` 해당 없음'),
   ('DISPOSAL','폐기','Disposal','처분. 불량 −. 원천 WMS 처분 작업. `ATTR1` 폐기손실 [확인 필요: 재고 폐기 손금 증빙]'),
   ('VENDOR_RETURN','업체 반품','Vendor Return','처분. 불량 −. 원천 WMS 처분 작업. `ATTR1` 해당 없음 (매입 차감은 SCM·회계)'),
   ('BULK_SALE','일괄 매각','Bulk Sale','처분. 불량 −. 원천 WMS 처분 작업. `ATTR1` 매출원가'),
   ('STOCKTAKE_ADJUSTMENT','실사 조정','Stocktake Adjustment','그 밖. 버킷별 ±. 원천 재고 예외, 세부 사유 필수 (7-7 A). `ATTR1` 감모손실'),
   ('PACKAGING_USE','포장재 사용','Packaging Material Use','그 밖. 정상 −. 하루 사용량 일괄 차감. 원천 WMS 포장재 사용 집계 (T-7 A). `ATTR1` 판관비 (운반비)'),
   ('REPAIR_MATERIAL_USE','수선 사용','Repair Material Use','그 밖. 정상 −. 수선 건마다. 원천 클레임 수선 (3-8 A, T-7 A). `ATTR1` 판관비 (수선비)'),
   ('TRANSFER_OUT','창고 이동 출고','Warehouse Transfer Out','자리만 남김 (1-7 A). 창고를 늘릴 때 연다. CK 허용 값에서 뺀다'),
   ('TRANSFER_IN','창고 이동 입고','Warehouse Transfer In','자리만 남김 (1-7 A)')),
 'HOLD_REASON_CD': vals(
   ('QUALITY_CHECK','품질 확인','Quality Check',''),
   ('PHOTO_SHOOT','촬영 대기','Waiting for Photo Shoot','상품 촬영용으로 빼 둔 실물'),
   ('OTHER','기타','Other','')),
 'ADJUSTMENT_DETAIL_REASON_CD': vals(
   ('LOSS','분실','Loss',''),
   ('DAMAGE','파손','Damage',''),
   ('INPUT_ERROR','입력 오류 정정','Input Error Correction','정정 반대 행(T-6 B)으로 잡지 못한 오래된 입력 오류'),
   ('UNKNOWN','원인 불명','Unknown Cause','')),
 'STOCK_COMMITMENT_STATUS_CD': vals(
   ('RESERVED','예약','Reserved','결제 대기. 입고 예정에 걸리지 않았으면 현재고 예약 수량에 들어간다 (4-3 A, 6-2 A)'),
   ('ALLOCATED','할당','Allocated','결제 완료 또는 주문 없는 출고 요청. 현재고 할당 수량에 들어간다 (4-5 A, 4-10 A)'),
   ('WAITING_INBOUND','입고 대기','Waiting for Inbound','결제를 마쳤지만 실물이 없어 입고 예정에 걸림 (6-2 A, 4-8 B). 현재고 수량에 넣지 않는다. 입고 검수 완료 때 할당으로 (6-3 B, 6-4 B)'),
   ('CLOSED','종결','Closed','출고 + 해제 = 확보. 끝 상태')),
 'STOCK_COMMITMENT_EVENT_TYPE_CD': vals(
   ('RELEASE','해제','Release','부분·전체 해제. 해제 사유 필수 (4-3 A). 선물 옵션 변경이면 대체 확보 필수 (4-9 A)'),
   ('TO_WAITING_INBOUND','입고 대기 전환','Move to Waiting for Inbound','할당 확보를 입고 예정에 걺. 출고 때 실물 부족 (4-8 B). 일부 출고 뒤면 남은 수량 전부 (IC-9 A)'),
   ('INBOUND_PLAN_MOVE','입고 차수 이동','Inbound Plan Move','다음 차수로 옮김. 입고 지연·검수 양품 부족 (5-9 A, IC-8 A)')),
 'RELEASE_REASON_CD': vals(
   ('PAYMENT_EXPIRED','결제 만료','Payment Expired','주문 3-4 A'),
   ('PAYMENT_FAILED','결제 실패','Payment Failed',''),
   ('ORDER_CANCELED','주문 취소','Order Canceled','작업 중 취소는 WMS 작업 취소 확인 뒤 해제 (4-7 A)'),
   ('GIFT_OPTION_CHANGED','선물 옵션 변경','Gift Option Changed','선물 수락 때 옵션 변경. 새 확보 행을 만들고 원래 행을 종결 (4-9 A)'),
   ('OUT_OF_STOCK','결품','Out of Stock','출고 때 실물이 모자라고 기다릴 입고 예정이 없음 (4-8 B)'),
   ('SUPPLY_UNAVAILABLE','공급 곤란','Supply Unavailable','예약 판매의 다음 차수가 없거나 차수가 취소됨 (5-9 A)')),
 'INBOUND_PLAN_STATUS_CD': vals(
   ('PLANNED','예정','Planned',''),
   ('PARTIALLY_RECEIVED','일부 입고','Partially Received','도착 수량이 예정보다 적음. 남은 수량은 다음 차수에 합치거나 취소 (6-3 B, 5-9 A)'),
   ('COMPLETED','완료','Completed','끝 상태'),
   ('CANCELED','취소','Canceled','끝 상태. 걸린 확보는 다음 차수로 옮기거나 공급 곤란으로 해제 (5-9 A)')),
 'DELAY_REASON_CD': vals(
   ('PRODUCTION_DELAY','생산 지연','Production Delay',''),
   ('SHIPPING_DELAY','선적 지연','Shipping Delay','해외 생산'),
   ('QUALITY_ISSUE','품질 문제','Quality Issue',''),
   ('OTHER','기타','Other','')),
 'MONTHLY_CLOSING_STATUS_CD': vals(
   ('OPEN','열림','Open','업무 일자를 넣을 수 있다'),
   ('CLOSED','마감','Closed','업무 일자를 넣을 수 없다 (8-2 C)'),
   ('REOPENED','재개','Reopened','승인을 받아 다시 열었다. 다시 마감하면 마감으로 돌아가고 그 달 이후 스냅샷을 다시 계산한다')),
 'STOCK_EXCEPTION_TYPE_CD': vals(
   ('INV_WMS_RECONCILIATION','INV·WMS 대사 차이','INV-WMS Reconciliation Difference','대사. 대상 현재고. 매일 INV 실물 합계와 WMS 선반 합계 비교 (1-8 A)'),
   ('INTERNAL_RECON_PHYSICAL','내부 대사 ① 실물','Internal Reconciliation (Physical)','대사. 대상 현재고. 실물 = 전날 스냅샷 + 당일 원장 (8-3 A)'),
   ('INTERNAL_RECON_COMMITMENT','내부 대사 ② 확보','Internal Reconciliation (Commitment)','대사. 대상 현재고. 예약·할당 = 확보 행 남은 수량 합계'),
   ('INTERNAL_RECON_INBOUND_PLAN','내부 대사 ③ 입고 예정','Internal Reconciliation (Inbound Plan)','대사. 대상 입고 예정. 확보 수량 = 걸린 확보 합계'),
   ('INTERNAL_RECON_MONTHLY','내부 대사 ④ 월 수불','Internal Reconciliation (Monthly Movement)','대사. 대상 현재고. 비교 구분 실물 합계. 전월말 실물 + 월 누계 입고 − 출고 − 처분 + 조정 = 당월말 실물 (월 마감 때, IC-7 A)'),
   ('FIELD_DISCOVERY','현장 발견','Field Discovery','대상 현재고. 대사 없이 창고에서 발견한 차이를 직접 등록 (7-7 A)'),
   ('EXPIRED_RESERVATION','만료 지난 예약','Expired Reservation Remaining','신호 1. 대상 확보. 만료 배치 실패'),
   ('INSPECTION_BACKLOG','검수 대기 적체','Inspection Backlog','신호 2. 대상 현재고. 기준 일수보다 오래된 생산·반품 입고분이 아직 검수 대기 (원장 입고 일시로 판정, IC-2 B)'),
   ('OVERDUE_INBOUND_PLAN','예정일 지난 미입고','Overdue Inbound Plan','신호 4. 대상 입고 예정'),
   ('LONG_HOLD','오래된 보류','Long Hold','신호 6. 대상 현재고. `HOLD_SINCE_AT`이 기준 일수를 넘음 (IC-2 B)'),
   ('RESTOCK_DEMAND','재입고 수요','Restock Demand','신호 7. 대상 현재고. 살 수 있는 수가 0인데 재입고 신청이 기준 수 이상 (생산 판단 참고)'),
   ('LOW_STOCK','리오더 기준 도달','Reorder Point Reached','신호 9. 대상 현재고. 판매 가능 + 입고 기간 안 진행 중 입고 예정의 남은 수량(예정 − 검수 양품 − 검수 불량 − 확보, 음수면 0) <= `REORDER_POINT_QTY`. SKU·비판매 품목 모두 (IC-3 A, IC-8 A, IC-20 B)')),
 'STOCK_GRADE_CD': vals(
   ('A','A 등급 (상위 판매)','Grade A (Top Sellers)','지난 3개월 판매 상위. 기준 비율은 `ATTR1`. 등급별 안전 재고·리오더 기준 기본값은 `ATTR2`·`ATTR3`'),
   ('B','B 등급 (중간)','Grade B (Mid Sellers)',''),
   ('C','C 등급 (하위·장기 체류)','Grade C (Slow Movers)','처분 후보·장기 체류 추출 대상 (`LAST_OUTBOUND_AT`과 함께)')),
 'STOCK_EXCEPTION_STATUS_CD': vals(
   ('CHECKING','확인 중','Checking',''),
   ('ADJUSTED','조정 완료','Adjusted','대사·현장 발견. 실사 조정 원장을 넣음 (7-7 A)'),
   ('NO_ADJUSTMENT','조정 없음','No Adjustment','대사·현장 발견. 실사 결과 INV가 맞음'),
   ('RESOLVED','처리 완료','Resolved','감시 신호')),
 'RECONCILIATION_BUCKET_CD': vals(
   ('PHYSICAL_TOTAL','실물 합계','Physical Total','INV·WMS 대사, 내부 대사 ④ (정상 + 검수 대기 + 불량 + 보류, IC-12 A)'),
   ('NORMAL','정상','Normal','내부 대사 ①'),
   ('INSPECTION_PENDING','검수 대기','Inspection Pending','내부 대사 ①'),
   ('DEFECTIVE','불량','Defective','내부 대사 ①'),
   ('HOLD','보류','Hold','내부 대사 ①'),
   ('RESERVED','예약','Reserved','내부 대사 ②'),
   ('ALLOCATED','할당','Allocated','내부 대사 ②'),
   ('INBOUND_PLAN_COMMITTED','입고 예정 확보','Inbound Plan Committed','내부 대사 ③')),
}
REUSE = {}
REUSE_NO_ROWS = {}
SAME_NAME_FOLD = True

# 공통코드에 둘 정책값 (컬럼이 아니라 `CMM_CODE` 값·`ATTR`)
POLICY = [
 ('수불 사유 회계 구분', '`STOCK_LEDGER_REASON_CD`의 `ATTR1` (매출원가, 판관비, 감모손실, 폐기손실, 해당 없음, 클레임 귀책에 따름). 비주문 출고는 배송 `NON_ORDER_TYPE_CD`의 `ATTR`', '7-8 A'),
 ('안전 재고·리오더 기준 기본값', '새 현재고 행의 `SAFETY_STOCK_QTY`, `REORDER_POINT_QTY`. 등급별 값은 `STOCK_GRADE_CD`의 `ATTR2`·`ATTR3`, 등급이 없으면 공통 기본값 (예: 0, NULL). 등급이 바뀌면 수동 지정 여부가 N인 값만 새 기본값으로 바꾼다', '5-1 B, IC-3 A, IC-4 A, IC-19 A'),
 ('리오더 입고 기간', '리오더 판정에 더하는 입고 예정의 범위(오늘 + n일). 판매 상품과 비판매 품목 2개 (예: 30일, 7일)', 'IC-20 B'),
 ('재고 등급 기준', '지난 3개월 판매 순위의 등급 경계 비율 (`STOCK_GRADE_CD`의 `ATTR1`, 예: A 상위 20%, B 다음 30%)', 'IC-4 A'),
 ('남은 수량 표시 임계값', '살 수 있는 수가 이 값 이하일 때만 "n개 남음"을 보여 준다 (예: 5개)', '5-4 A'),
 ('재입고 알림 기준 수량', '살 수 있는 수가 이 값 이상이면 재입고 알림을 보낸다 (예: 3개)', '5-5 B'),
 ('실사 조정 승인 기준 수량', '차이가 이 값을 넘으면 승인 관리자 필수 (애플리케이션 검사)', '7-7 A'),
 ('재고 마감 시각', '일 스냅샷과 내부 대사를 도는 시각 (예: 0시)', '8-1 A'),
 ('감시 기준', '검수 대기 적체 일수, 오래된 보류 일수, 재입고 수요 신청 수 (예외 유형 `ATTR`)', '8-8 B, IC-2 B'),
 ('예외 유형별 대상', '`STOCK_EXCEPTION_TYPE_CD`의 `ATTR1`에 대상(현재고, 확보, 입고 예정)', 'T-1 A'),
]

NAME_CONFIRMED = {t['t'] for t in T}  # 테이블 이름은 T-10 A로 확정
CONFIRMED_GROUPS = set()
CONFIRMED_TABLES = set()
# 다른 도메인 문서에서 오는 값. 재고는 외부 업체 값이 없다.
EXTERNAL_SOURCED = set()

CONFIRM = [
 ('다른 도메인 이름', 'WMS(창고, 비판매 품목, 입고, 입고 검수, 처분 작업, 포장재 사용 집계, 실사), 클레임(검수 결과, 수선), SCM(발주 라인), 관리자 ID는 그 도메인 설계 뒤 이름과 FK 여부를 정한다. 창고·비판매 품목은 FK 예정 (1-6 A).', '원천·참조 컬럼'),
 ('원천 없는 사유', '보류 설정·보류 해제·불량 전환은 원천 문서 없이 관리자가 처리한다. 원천 컬럼은 모두 NULL이고 행위자는 `CREATED_BY`로 본다는 제안.', '`INV_STOCK_LEDGER`'),
 ('실사 조정의 WMS 실사 ID', '원천은 재고 예외 ID(필수)이고 WMS 실사 ID는 선택으로 함께 남긴다는 제안 (1-3 A, 7-7 A).', '`INV_STOCK_LEDGER.STOCKTAKE_ID`'),
 ('확보 행 동시 갱신', '행 버전 없이 상태 조건부 UPDATE(`WHERE 상태 = :읽은 상태`)로 결제 완료와 만료 배치의 경합을 막는다는 제안. 현재고는 2-6 A로 행 버전이 없다.', '`INV_STOCK_COMMITMENT`'),
 ('확보 처리 이력 파티션', 'INTERVAL 참조 파티션(12c부터)으로 확보 파티션과 함께 제거한다는 제안. 전역 UK(처리 키)는 제거 때 `UPDATE GLOBAL INDEXES` (IC-10 B).', '`INV_STOCK_COMMITMENT_EVENT`'),
 ('진행 중 확보 UK 범위', '4-9 A는 주문 상품만 정했다. 사은품·출고 요청 상품에도 같은 함수 기반 UK를 둘지.', '`INV_STOCK_COMMITMENT`'),
 ('예약 만료 시각', '만료 시각은 확보 행에 복사하지 않고 주문에서 읽는다는 제안 (신호 1 감시는 주문과 조인).', '`INV_STOCK_COMMITMENT`'),
 ('예정보다 많은 입고', '검수 누계가 예정을 넘으면 확보 상한을 0으로 보는 CK 식 (IC-8 A).', '`INV_INBOUND_PLAN`'),
 ('입고 차수 번호', 'INV 입고 차수와 WMS 입고 차수(로트, 1-4 A)를 같은 번호로 맞출지.', '`INV_INBOUND_PLAN.INBOUND_ROUND_NO`'),
 ('대사 수량의 모양', '대사 비교 수량 구분 코드 + 장부·비교 수량 + 차이(가상) 제안 (8-8 후속 B가 컬럼 검토로 넘김).', '`INV_STOCK_EXCEPTION`'),
 ('월 마감 보존 기간', '월말 스냅샷과 같이 10년 제안.', '`INV_MONTHLY_CLOSING`'),
 ('수량 타입', '수량·증감은 `NUMBER(7)` 제안 (배송은 `NUMBER(5)`). 포장재 하루 사용량(2만 개 이상)을 담는다.', '수량 컬럼 전체'),
 ('원장 UK와 파티션 제거', '중복 방지 키·정정 대상 UK는 전역 인덱스다. 파티션 제거 때 `UPDATE GLOBAL INDEXES`를 쓴다.', '`INV_STOCK_LEDGER`'),
 ('운영 DB 에디션', 'XE 데이터 12GB 한도. 원장만 5년이면 넘는다는 추정 (8-6 C) [가정].', '전체'),
]
