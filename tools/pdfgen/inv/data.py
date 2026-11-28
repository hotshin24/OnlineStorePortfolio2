# 재고(INV) 도메인 테이블·컬럼 정의 (제안, 컬럼 검토 전)
# 근거: 재고 결정 (2026-11-27, 대화로 결정. 축 8개 결정 52개 + 후속 2개, 테이블 T-1~T-11, 컬럼 검토 IC-1~). 테이블 14개 (IC-10 B로 확보 처리 이력, IC-43 B·IC-47 B로 사은품·운영자재 테이블 6개 추가). 결정 기록은 inv/decision.py.
# 테이블 물리명 7개는 T-10 A에서 골랐고 나머지는 후보다. 확정 칸 체크는 컬럼 검토에서 사용자가 확정한 것만 한다 (2026-11-28 사용자 지시). 컬럼은 모두 제안이고 컬럼 검토(IC-n)에서 정한다.
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

def refn(p, ko, en, null='Y', desc=''):
    # FK도 인덱스도 두지 않는 식별자 (건수가 적어 조회는 다른 인덱스로 좁힘, IC-116 A)
    return (p, ko, en, ID, null, '', 'FK 없음 (인덱스 없음)', desc)

def qty(p, ko, en, desc='', d='0', ck='CK (>= 0)', null='N', t=QTY):
    return (p, ko, en, t, null, d, ck, desc)

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
FRB = 'FK 예정 → `WMS_FREEBIE_ITEM` (후보)'
SUP = 'FK 예정 → `WMS_SUPPLY_ITEM` (후보)'
ADM = '관리자 테이블(`ADM`)은 관리자 도메인 설계 뒤 이름과 FK 여부를 정한다.'

# =========================================================== 1. 현재고
table(t='INV_STOCK', ko='현재고 (창고별 판매 상품 수량)', en='Stock on Hand',
 desc='(창고, SKU)마다 1행. 판매 상품만 센다 (IC-42 B). 사은품·운영자재는 전용 현재고에서 센다 (IC-43 B). 판매 가능 수량의 원천이다 (1-1 A). 수량 구분 6개를 컬럼으로 갖고 (3-1 A, 3-2 A), 모든 변경은 "지금 값 ± 증감" UPDATE 한 문장으로만 한다 (2-6 A). '
      'SKU를 등록할 때 창고마다 수량 0으로 만든다 (2-2 A). 지우지 않는 재고 수량 행이다 (T-4 A, IC-62 C). 원장·확보·입고 예정·스냅샷·예외가 이 행 ID 하나로 창고와 품목을 가리킨다 (1-6 A).',
 basis='1-1 A, 1-2 A, 1-6 A, 2-2 A, 2-6 A, 2-7 A, 3-1 A~3-3 A, 4-12 A, 5-1 B, 5-3 A, T-4 A, T-10 A, IC-1 A~IC-4 A, IC-17 A~IC-25 A, IC-30 B~IC-32 B, IC-41 A, IC-42 B, IC-50 A~IC-53 C, IC-56 A, IC-61 A, IC-62 C, IC-71 A~IC-77 A, IC-79 A, IC-80 A',
 pk='대리 PK `SEQ_INV_STOCK`', cache=20,
 delete='지우지 않는다. 단종돼도 수량 0 행으로 남긴다. 판매 중지는 상품 SKU의 판매 상태가 맡고, 사용 여부·삭제 컬럼을 두지 않는다 (T-4 A). 선행 4의 다섯 유형 어디에도 들지 않는 재고 수량 행이다 (IC-62 C)',
 part='없음', keep='보존 기간 없음 (지우지 않음, T-4 A)',
 cols=[
 ('식별', [
  ('STOCK_ID','현재고 고유 식별 번호','Stock on Hand Unique Identifier',ID,'N','','PK',
   '원장·확보·입고 예정·스냅샷·예외가 이 ID를 FK로 가리킨다 (1-6 A). 한 트랜잭션에서 여러 행을 고칠 때는 이 ID 오름차순으로 UPDATE한다 (4-12 A).'),
  ('WAREHOUSE_ID','창고 식별 번호','Warehouse Identifier',ID,'N','',WH,
   'NOT NULL (1-6 A). 창고는 지금 1곳이다. WMS 창고 마스터가 생기면 FK를 건다.'),
  fk('SKU_ID','SKU 식별 번호','SKU Identifier','PRD_SKU','N','',
     '판매 상품 (IC-42 B). 상품 마스터라 FK를 건다. 사은품·운영자재는 이 테이블에 없다 (IC-43 B).'),
  ('STOCK_COMPOSITION_TYPE_CD','재고 구성 유형 코드','Stock Composition Type Code','VARCHAR2(20)','N','','CK (값 목록)',
   '단품 / 세트 (IC-41 A). 기본값을 두지 않아 행을 만들 때 반드시 넘긴다. 빠뜨리면 NOT NULL 위반으로 드러난다 (IC-76 A). 묶어서 생산·입고한 상품(티셔츠 2팩, 파자마 상하의 세트)은 세트다 (상품 15 D). SKU 1개를 수량 1로 세는 것은 같다. '
   '상품 스타일에 같은 구분을 둘지는 상품 도메인에서 정하고, 그때 값과 원천을 맞춘다.'),
 ]),
 ('판매 가능·품절', [
  ('AVAILABLE_QTY','판매 가능 수량 (가상 컬럼)','Available Quantity (Virtual)',QTY,'N','','가상 컬럼, CK (>= 0)',
   '`GENERATED ALWAYS AS (NORMAL_QTY - RESERVED_QTY - ALLOCATED_QTY) VIRTUAL` (3-3 A). CHECK >= 0이 초과 판매를 막는 마지막 방어선이다. '
   '재발송·결품 대체는 `AVAILABLE_QTY >= :수량`을 조건으로 할당을 더하는 UPDATE 한 문장이다 (5-1 B). 일반 주문은 아래 `GENERAL_ORDERABLE_QTY`를 쓴다. 예: 정상 10, 예약 2, 할당 3이면 5.'),
  ('GENERAL_ORDERABLE_QTY','일반 주문 가능 수량 (가상 컬럼)','General Orderable Quantity (Virtual)',QTY,'N','','가상 컬럼',
   '`GENERATED ALWAYS AS (GREATEST(NORMAL_QTY - RESERVED_QTY - ALLOCATED_QTY - SAFETY_STOCK_QTY, 0)) VIRTUAL` (IC-23 A). Oracle 가상 컬럼은 다른 가상 컬럼을 가리킬 수 없어 원래 컬럼으로 쓴다. '
   '일반 주문 확보는 `GENERAL_ORDERABLE_QTY >= :수량`을 조건으로 예약을 더하는 UPDATE 한 문장이다 (5-1 B). 품절 표시, "n개 남음"(5-3 A, 5-4 A), 품절 시작 일시 CK가 모두 이 값을 쓴다. '
   '예: 정상 10, 예약 2, 할당 3, 안전 재고 2이면 3. 4개 주문은 0행 갱신으로 거절된다.'),
  ('SOLD_OUT_AT','품절 시작 일시','Sold Out Since',TS,'Y','','',
   '일반 주문이 처음 가능해진 뒤(`FIRST_SELLABLE_AT` NOT NULL, IC-71 A) 일반 주문 가능 수량이 0이 되는 UPDATE에서 채우고, 양수로 돌아오면 비운다. 품절인 채로 수량만 바뀌면 처음 시각을 유지한다. 확보·출고·입고뿐 아니라 안전 재고를 고치는 UPDATE도 같다 (IC-1 A, IC-17 A). '
   '일반 주문이 처음 가능해지기 전(첫 입고분이 검수 대기에 있는 동안 포함)은 NULL이라 품절 기간에 들어가지 않는다. 예: 11/1 등록, 12/1 첫 입고 100개가 검수 대기, 12/3 검수 합격이면 12/3 전은 NULL (IC-71 A). '
   '품절 판정은 조회 때 계산 그대로이고(5-3 A) 이 값은 품절 기간·판매 기회 손실을 보는 기록이다. 품절 전환을 상품 검색 색인에 알리는 일은 상품 넘김 사항. 수량을 바꾸는 UPDATE가 같은 문장에서 고친다 (IC-73 A, 품절 시작 일시 CHECK, IC-80 A).'),
  ('FIRST_SELLABLE_AT','최초 판매 가능 일시','First Sellable At',TS,'Y','','',
   '일반 주문 가능 수량이 처음 양수가 되는 UPDATE에서 한 번만 채우고 바꾸지 않는다 (IC-71 A). 재고상 일반 주문이 처음 가능해진 시각이고(상품의 판매 상태와는 별개, IC-80 A) 품절 시작 일시의 기준이다. '
   'CHECK는 NULL만 막으므로 갱신 경로가 `NVL(FIRST_SELLABLE_AT, SYSTIMESTAMP)`로만 채운다(백엔드 넘김, IC-80 A). 시스템 오픈 때 기초 재고는 이전 시스템의 판매 개시일, 없으면 오픈 시각으로 채운다 (IC-79 A). '
   '예: 12/1 첫 생산 입고(검수 대기)에는 NULL, 12/3 검수 합격으로 정상 98이 되면 12/3. 첫 입고 전 예약 판매 기간은 NULL이다.'),
 ]),
 ('실물 수량', [
  ('PHYSICAL_TOTAL_QTY','실물 합계 수량 (가상 컬럼)','Physical Total Quantity (Virtual)','NUMBER(8)','N','','가상 컬럼',
   '`GENERATED ALWAYS AS (NORMAL_QTY + INSPECTION_PENDING_QTY + DEFECTIVE_QTY + HOLD_QTY) VIRTUAL` (IC-50 A, IC-51 A). 창고에 있는 판매 상품 전부다(보유 수량). INV·WMS 대사(1-8 A, IC-12 A)와 내부 대사 ④(IC-7 A)가 이 값을 쓴다. '
   '구성 4개가 각각 `NUMBER(7)`이라 합이 7자리를 넘을 수 있어 8자리로 둔다. 구성 4개가 각각 CHECK >= 0이라 따로 CK를 두지 않는다. 예: 정상 10, 검수 대기 3, 불량 1, 보류 2이면 16.'),
  qty('NORMAL_QTY','정상 수량','Normal (Sellable) Quantity','판매할 수 있는 실물. 예약·할당은 이 안에서 잡는다 (3-2 A).'),
  qty('INSPECTION_PENDING_QTY','검수 대기 수량','Inspection Pending Quantity','생산 입고 도착분과 반품 도착분 (6-3 B, 7-2 A). 검수를 마치면 정상·불량으로 옮긴다.'),
  qty('DEFECTIVE_QTY','불량 수량','Defective Quantity','수선해 정상으로 돌리거나 폐기·업체 반품·일괄 매각한다 (3-7 C, 7-4 A). 자사몰에서 B급으로 팔지 않는다.'),
  qty('HOLD_QTY','보류 수량','Hold Quantity','품질 확인, 촬영 대기 등으로 잠시 팔지 않는 실물. 진행 중 보류 건(`INV_STOCK_HOLD`)의 남은 수량 합계와 같다 (IC-52 C, 내부 대사 ⑤). 사유, 시작 일시, 해제 예정일은 보류 건에 있다. '
      '판매 가능 수량(정상 − 예약 − 할당)까지만 보류할 수 있다. 예약·할당은 풀지 않는다 (IC-72 A, IC-28 B).'),
 ]),
 ('확보 수량', [
  qty('RESERVED_QTY','예약 수량','Reserved Quantity',
      '결제를 기다리는 주문이 잡은 정상 재고. 진행 중인 예약 상태 확보 행(입고 예정에 걸리지 않은 것)의 남은 수량 합계와 같다 (2-3 C, 8-3 A ②).'),
  qty('ALLOCATED_QTY','할당 수량','Allocated Quantity',
      '결제를 마쳤거나 주문 없이 출고 요청이 잡은 정상 재고 (4-5 A, 4-10 A). 출고하면 정상과 함께 줄어든다 (1-5 A). 할당 상태 확보 행의 남은 수량 합계와 같다.'),
  ('STOCK_QUANTITY_CHANGED_AT','재고 수량 변경 일시','Stock Quantity Changed At',TS,'N','SYSTIMESTAMP','',
   '수량 7개(실물 4, 예약, 할당, 안전 재고) 중 하나라도 바꾸는 UPDATE에서 같은 문장으로 고친다 (IC-24 A). 일 스냅샷 대상은 그날 원장 변화가 있었거나 이 값이 그날 안인 행이다. '
   '등급·리오더 기준·수동 지정 여부만 바꾼 UPDATE는 고치지 않는다. 예: 등급 배치가 3만 행의 등급만 바꾼 날에는 스냅샷이 늘지 않는다. '
   '확보 수량 그룹 끝에 두지만 실물 수량을 바꿀 때도 고친다 (IC-32 B). 이름은 금액 잔액과 헷갈리지 않게 재고 수량으로 했다 (IC-61 A).'),
 ]),
 ('재고 관리 기준', [
  qty('SAFETY_STOCK_QTY','안전 재고 수량','Safety Stock Quantity',
      '일반 주문이 쓰지 못하고 남겨 두는 수량 (5-1 B). 새 행은 공통코드 정책값(등급별 기본값, IC-4 A)으로 채운다. 관리자가 고치면 수동 지정 여부가 Y가 되고, N이면 등급이 바뀔 때 새 기본값으로 바뀐다 (IC-19 A). CHECK(판매 가능 >= 0)에는 넣지 않아 재발송은 안전 재고까지 쓴다. 이 값, 수동 지정 여부, 수동 지정 종료일이 바뀌면 같은 트랜잭션에서 안전 재고 변경 이력에 1행을 넣는다 (IC-53 C, IC-130 A). 이력의 변경 시점 판매 가능 수량은 같은 UPDATE의 `RETURNING AVAILABLE_QTY`로 받는다 (IC-123 A).'),
  yn('SAFETY_STOCK_MANUAL_YN','안전 재고 수동 지정 여부','Safety Stock Manually Set Flag','N',
     '관리자가 안전 재고를 고치면 Y (IC-19 A). N이면 월 등급 배치가 등급이 바뀐 행의 안전 재고를 새 등급 기본값으로 바꾼다. 예: A(10)에서 C로 떨어지면 N인 행은 C 기본값 2로 바뀐다. 기본값으로 되돌리면 N으로 돌린다. '
     '공통코드 기본값을 바꾸면 N인 행에도 같은 작업으로 새 기본값을 적용한다 (IC-128 A). 등급 배치와 기본값 적용의 UPDATE는 WHERE에 대상 등급과 N을 다시 걸어, 그사이 관리자가 고친 행을 건너뛴다. 같은 기본값의 일괄 적용은 한 번에 하나만 돌린다(배치 잠금, IC-132 A).'),
  ('SAFETY_STOCK_MANUAL_END_DT','안전 재고 수동 지정 종료일','Safety Stock Manual Setting End Date','DATE','Y','','',
   '행사처럼 기간을 정해 안전 재고를 올릴 때 관리자가 넣는다 (IC-129 B). 이 날이 지나면(종료일 < 오늘) 일 배치가 이력(사유 수동 지정 만료 복귀, 행위자 `BATCH`, IC-134 A)을 넣고 수동 지정 N, 종료일 NULL로 돌린다. 지난 날짜는 넣을 수 없고 같은 트랜잭션의 이력 CK가 막는다 (IC-135 A). '
   '수동 지정 N이면 NULL (CK). 예: 12/1 패딩 L을 5 → 20으로 올리며 종료일 12/31을 넣으면 1/1 배치가 5로 되돌린다. NULL이면 사람이 되돌릴 때까지 유지. 이 값이 바뀌어도 안전 재고 변경 이력에 1행을 넣는다 (IC-130 A). 자동 복귀 UPDATE는 WHERE에 수동 지정 Y와 종료일 < 오늘을 다시 걸어, 배치가 읽은 뒤 관리자가 연장한 행을 건너뛴다 (IC-132 A). '
   '2026-11-28 IC-129 B로 확정 테이블에 더한 컬럼이라 확정 칸은 비워 둔다.'),
  ('REORDER_POINT_QTY','리오더 기준 수량','Reorder Point Quantity',QTY,'Y','','CK (>= 0)',
   'NULL이면 감시하지 않는다(시즌 한정 상품 등). 판매 가능 + Σ GREATEST(예정일이 오늘 + 입고 기간 안인 진행 중 입고 예정의 예정 − 검수 양품 − 검수 불량 − 확보, 0) <= 이 값이면 배치가 재고 예외 `LOW_STOCK`(신호 9)을 만든다 (IC-3 A, IC-8 A, IC-20 B). '
   '입고 기간은 공통코드 정책값(판매 상품, 사은품·운영자재). 예: 판매 가능 2, 기준 10, 60일 뒤 입고 100, 입고 기간 30일이면 2 <= 10이라 경보. '
   '이미 발주한 상품은 다시 잡히지 않는다. 사은품·운영자재는 각 전용 현재고의 리오더 기준을 쓴다 (IC-49 C). 안전 재고(판매를 막는 값)와 다르다. 새 행은 등급별 기본값으로 채운다.'),
  yn('REORDER_POINT_MANUAL_YN','리오더 기준 수동 지정 여부','Reorder Point Manually Set Flag','N',
     '관리자가 리오더 기준을 고치면 Y (IC-19 A). 안전 재고와 따로 다룬다.'),
  cd('STOCK_GRADE_CD','재고 등급 코드 (ABC)','Stock Grade Code (ABC)','Y',n=10,
     desc='월 마감 배치가 상품 `PRD_SALES_DAILY_STAT`의 지난 3개월 판매로 다시 매긴다 (IC-4 A). 판매 이력이 없는 새 행은 NULL. '
          '등급별 안전 재고·리오더 기준 기본값(`ATTR`)은 새 행과, 등급이 바뀐 행 중 수동 지정 여부가 N인 값에 적용한다 (5-1 B, IC-19 A). 처분 후보 추출에 쓰고, 순환 실사는 WMS가 이 등급과 WMS 실사 기록으로 뽑는다 (IC-21 B). '
          '등급이 NULL(판매 이력 없음)로 바뀌면 수동 지정 여부가 N인 안전 재고는 등급 없는 행의 공통 기본값으로 바꾸고 이력 사유는 등급 없음 기본값이다 (IC-77 B).'),
  ('STOCK_GRADE_EVAL_YM','재고 등급 산정 연월','Stock Grade Evaluation Year-Month','VARCHAR2(6)','Y','','CK (YYYYMM)',
   '등급 배치가 이 행을 산정한 연월 (IC-25 A). 산정 연월이 있는데 등급이 NULL이면 판매 이력 없음, 산정 연월이 NULL이면 아직 매기지 않은 새 행이다. 다른 행보다 오래됐으면 배치가 빠뜨린 것이다. 예: `202611`.'),
 ]),
 ('입출고·사용 이력', [
  ('LAST_INBOUND_AT','마지막 생산 입고 일시','Last Production Inbound At',TS,'Y','','',
   '생산 입고 원장과 같은 트랜잭션에서 갱신한다 (IC-1 A). 재입고 주기를 본다. 반품 입고는 넣지 않는다. 품절 시작 일시의 기준은 `FIRST_SELLABLE_AT`으로 바뀌었다 (IC-71 A). 시스템 오픈 때 기초 재고는 이전 시스템의 마지막 생산 입고 일시를 옮기고, 없으면 NULL이다 (IC-79 A).'),
  ('LAST_OUTBOUND_AT','마지막 출고 일시','Last Outbound At',TS,'Y','','',
   '마지막으로 실물이 나간 일시. 판매·재발송·비주문 출고 원장과 같은 트랜잭션에서 갱신한다 (IC-1 A). 포장재 사용·수선 사용은 운영자재로 옮겨 넣지 않는다 (IC-22 A → IC-42 B). 처분(폐기, 업체 반품, 매각)은 넣지 않는다. '
   '장기 체류·장기 미사용 추출, 이월·처분 판단에 쓴다. 원장(5년)이 지워져도 남는다. 예: 3개월 동안 팔리지 않은 니트는 이 값이 3개월 전이다. '
   '출고마다 바뀌는 값이라 인덱스를 두지 않고, 월 추출 배치가 테이블 전체를 읽는다 (IC-75 A). 시스템 오픈 때 기초 재고는 이전 시스템 값을 옮기고, 없으면 NULL이다 (IC-79 A).'),
 ]),
 ],
 idx=['UK `UK_INV_STOCK_SKU_WAREHOUSE` (`SKU_ID`, `WAREHOUSE_ID`) (IC-42 B로 SKU만 남아 일반 UK). SKU만으로 찾는 조회(상품 상세의 창고 합계)와 `PRD_SKU` FK 인덱스를 이 UK가 맡는다 (IC-74 A)',
      '`LAST_OUTBOUND_AT`에는 인덱스를 두지 않는다 (IC-75 A). 오래된 보류 감시는 보류 건 테이블에서 한다 (IC-56 A)'],
 check=[        '`AVAILABLE_QTY >= 0` (3-3 A). 수량 컬럼 7개는 각각 >= 0 (2-6 A). 가상 컬럼 3개는 세지 않는다',
        '`FIRST_SELLABLE_AT IS NOT NULL AND GENERAL_ORDERABLE_QTY = 0`이면 `SOLD_OUT_AT` NOT NULL, 아니면 NULL (IC-1 A, IC-17 A, IC-71 A). `FIRST_SELLABLE_AT`이 NULL이면 조건이 거짓이라 `SOLD_OUT_AT`은 NULL이어야 한다. '
        '이 CK를 건다: 수량·안전 재고를 바꾸는 모든 UPDATE가 같은 문장에서 `SOLD_OUT_AT`, `FIRST_SELLABLE_AT`, `STOCK_QUANTITY_CHANGED_AT`을 고친다. 어디서 모아 고칠지는 백엔드 설계 때 정한다 (IC-73 A, 넘김 사항)',
        '`GENERAL_ORDERABLE_QTY > 0`이면 `FIRST_SELLABLE_AT` NOT NULL (한 번 채우면 비우지 않음, IC-71 A)',
        '`SAFETY_STOCK_MANUAL_YN = \'Y\' OR SAFETY_STOCK_MANUAL_END_DT IS NULL` (수동 지정 N이면 종료일 NULL, IC-129 B)'])

# =========================================================== 2. 수불 원장
table(t='INV_STOCK_LEDGER', ko='수불 원장 (실물 수량 변화 1건)', en='Stock Ledger',
 desc='판매 상품 현재고의 실물 쪽 수량(정상, 검수 대기, 불량, 보류)이 바뀐 사건 1건에 1행 (2-3 C). 사은품·운영자재는 전용 원장 (IC-43 B). 예약·할당 변화는 확보 테이블이 갖는다. 현재고 UPDATE와 같은 트랜잭션에서 INSERT하고 (2-1 A), 고치거나 지우지 않는다. '
      '잘못 넣은 행은 같은 사유의 반대 행으로 정정한다 (T-6 B, 선행 4). 원천 문서는 원천마다 컬럼을 두고 사유에 맞는 하나만 채운다 (2-4 A). 수불부와 회계 구분은 사유별 합계로 낸다 (7-8 A). 원천 문서는 원장 행을 만드는 처리 문서이고, 근거 문서(출고 요청, WMS 실사, 입고 예정)는 원천이 처리한 앞 단계 문서로 원장은 이 단위로 회계·누계를 센다 (IC-109 A). 1행의 단위는 (원천 1건, 현재고 1개, 사유 1개, 생산 입고·입고 검수는 입고 예정 1개, 출고 3사유는 출고 요청 1건)이고, 원천 안의 상품 줄 상세는 원천 테이블에 남는다. '
      '매일 검증은 원천 줄 합계와 원장 증감을 이 단위로 맞춰 본다. 줄 단위 원천 ID는 두지 않고, WMS·클레임 설계 때 상세 행 ID를 원천으로 바꿀지 다시 본다 (IC-101 C, IC-105 A). '
      '1차 재고는 기초 재고 사유로 들어온다 (IC-79 A, 1차-8 A, IC-82 A). 실제 사건 시각 컬럼은 두지 않는다: 날짜 귀속은 업무 일자가, '
      '검수 대기 적체 판정은 처리 시각(`CREATED_AT`)이 맡고, 실제 시각은 원천 테이블에서 읽는다 (IC-2 B, IC-90 B). '
      '변경 후 수량(보유, 보류, 불량 등)은 저장하지 않고 수불부 조회가 계산한다: 1차는 기초 재고부터의 원장 누계, 2차부터는 가장 가까운 일 스냅샷 + 그 사이 원장 (8-1 A, IC-100 A).',
 basis='1-3 A, 1-5 A, 1-7 A, 2-1 A, 2-3 C~2-5 A, 2-7 A, 3-6 A, 3-8 A, 6-3 B, 6-5 A, 7-1 A~7-4 A, 7-7 A, 7-8 A, 8-2 C, 8-6 C, 8-8 후속 B, T-5 A, T-6 B, T-10 A, IC-5 A, IC-6 A, IC-46 A, IC-82 A~IC-89 A, IC-90 B, IC-91 A~IC-93 A, IC-94 A~IC-100 A, IC-101 C, IC-102 A~IC-122 A',
 pk='대리 PK `SEQ_INV_STOCK_LEDGER`', cache=100,
 delete='삭제하지 않는다 (원장, 선행 4). 정정은 반대 행으로 한다 (T-6 B). 5년이 지난 파티션을 제거한다 (8-6 C)',
 part='업무 일자(`BUSINESS_DT`) 월 INTERVAL 파티션 (8-6 C). 원장을 FK로 가리키는 테이블이 없어 파티션 제거가 막히지 않는다 (정정의 원래 원장 ID는 `ref()`, T-6 B). '
      '전역 인덱스(UK 2개, 원천 6개, FK 3개)는 파티션 제거 때 `DROP PARTITION … UPDATE GLOBAL INDEXES` 한 번으로 정리한다 (21c는 전역 인덱스 정리를 비동기로 미룸, IC-92 A)',
 keep='업무 일자 + 5년 (8-6 C, 전표 성격) [확인 필요: 국세기본법 85조의3 장부·증빙 5년]',
 cols=[
 ('식별', [
  ('STOCK_LEDGER_ID','수불 원장 고유 식별 번호','Stock Ledger Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK','N','',
     '창고와 품목은 현재고 행에서 읽는다 (1-6 A). 수불 조회는 현재고와 조인 한 번이다.'),
  cd('STOCK_LEDGER_REASON_CD','수불 사유 코드','Stock Ledger Reason Code',
     desc='사용 20개 + 자리만 남긴 창고 이동 2개 (7-1 A, 1-7 A, 기초 재고 IC-82 A, 반송 입고·검수 IC-94 A, 불량 해제 IC-98 A, 고객 직접 반품 입고 IC-107 A). 값마다 1차에 쓸 수 있는지 차수 칸에 표시한다(원천이 1차에 없는 사유는 2차, IC-96 A). 포장재 사용·수선 사용은 운영자재 원장으로 옮겼다 (IC-46 A). 사유마다 채울 원천 컬럼과 버킷별 증감 방향을 테이블 수준 CK로 묶는다. 회계 구분은 코드의 `ATTR1` (7-8 A).'),
  ref('REVERSED_STOCK_LEDGER_ID','정정 대상 원래 원장 식별 번호','Reversed Original Stock Ledger Identifier',
      desc='NOT NULL이면 정정 행이다. 원래 행과 같은 사유를 쓰고 증감은 모두 반대다 (T-6 B). 한 행은 한 번만 정정한다 (UK, 전역 인덱스, IC-92 A). 원장 파티션 제거를 막지 않도록 FK 없이 둔다. '
           '원래 행과 같은 현재고·사유인지는 애플리케이션이 검사한다. 마감한 달의 행을 정정하면 정정 행의 업무 일자는 열린 달이나 재개한 달이다 (8-2 C). '
           '행의 뜻(방향이 모두 반대)을 바꾸고 CHECK 3개가 이 값을 보므로 사유 바로 다음에 둔다 (IC-93 A).', extra='UK'),
  ('REPOSTED_FROM_STOCK_LEDGER_ID','재기록 대상 원래 원장 식별 번호','Reposted-From Original Stock Ledger Identifier',ID,'Y','','FK 없음 (인덱스 없음)',
   'NOT NULL이면 재기록 행이다: 정정한 원래 행을 올바른 값으로 다시 넣은 행 (IC-88 A). 예: 출고 95장을 원장 9001에 −100으로 넣었다면, 정정 행 +100(키 `REVERSAL:9001`) 뒤에 '
   '재기록 행 −95(키 `REPOST:9001`)가 9001을 가리킨다. 키 UK로 잘못 넣은 행 하나에 재기록은 한 번이다. 원래 행에서 재기록 행을 찾을 때는 키 UK를 쓰므로 인덱스를 두지 않는다. '
   '정정 대상 원래 원장 ID와 함께 채울 수 없다 (CK, IC-117 A). 원래 행이 이미 정정됐는지, 같은 현재고·사유인지는 애플리케이션이 검사한다. 원천 컬럼은 원래 행과 같다. 정정 행과 같은 트랜잭션에서 넣고 현재고에는 두 행의 순증감을 한 번 반영한다 (IC-89 A). '
   '원장 파티션 제거를 막지 않도록 FK 없이 둔다.'),
  ('LEDGER_KEY_VAL','원장 중복 방지 키','Stock Ledger Idempotency Key Value','VARCHAR2(100)','N','','UK',
   '형식 (2-5 A): ① 원천 사유는 `{사유 코드}:{원천 ID}:{현재고 ID}` (IC-102 A). 출고 3사유는 출고 요청마다 1행이라 `{사유 코드}:{출고 ID}:{출고 요청 ID}:{현재고 ID}` (IC-106 A, 최대 78자). '
   '예: 주문 티셔츠와 교환 재발송 티셔츠를 한 박스(출고 5501)로 합포장하면 `SALES_SHIPMENT:5501:7001:1001`과 `RESHIP_SHIPMENT:5501:7002:1001`로 갈린다(배송 DC-24 B). '
   '② 생산 입고·입고 검수는 끝에 입고 예정 ID를 붙여 입고 예정마다 1행이다: `{사유 코드}:{원천 ID}:{현재고 ID}:{입고 예정 ID}` (IC-105 A, 최대 78자. 모든 형식 중 가장 긴 키도 78자, IC-115 A). '
   '③ 원천이 없거나 원천 하나가 여러 행을 만드는 사유(보류 설정·해제, 불량 전환, 불량 해제, 고객 직접 반품 입고)는 `{사유 코드}:{요청 키}:{현재고 ID}`. 요청 키는 관리자 요청마다 화면이 한 번 발급하는 UUID(36자)라 이중 클릭·재시도를 막는다 (IC-103 A). 고객 직접 반품 입고는 미확인 입고 하나를 여러 클레임에 다른 날 연결할 수 있어 연결 요청마다 키를 받는다(IC-119 A). '
   '한 요청으로 SKU 여러 개를 처리하면(예: 셔츠 M 3벌과 니트 L 2벌을 한 번에 불량 전환) 원장은 현재고마다 1행이라 끝에 현재고 ID를 붙인다 (IC-122 A, 최대 78자). '
   '④ 정정 `REVERSAL:{원래 원장 ID}`, 재기록 `REPOST:{원래 원장 ID}`(IC-88 A), 기초 재고 `OPENING:{현재고 ID}`(IC-82 A). '
   '같은 키로 두 번 넣으면 UK 위반으로 처리 전체가 되돌아간다. 파티션 테이블의 UK라 전역 인덱스이고, 파티션 제거 때 `UPDATE GLOBAL INDEXES`를 쓴다 (IC-92 A).'),
  ('BUSINESS_DT','업무 일자','Business Date','DATE','N','','파티션 키',
   '수불부·특정 날짜 수량·내부 대사 ①이 쓰는 날짜 (8-2 C). 처리 일시(`CREATED_AT`)보다 늦을 수 없다 (CK). 열린 달(또는 승인받아 재개한 달)만 넣을 수 있고 애플리케이션이 월 마감 테이블로 검사한다.'),
 ]),
 ('실물 증감', [
  dqty('NORMAL_DELTA_QTY','정상 수량 증감','Normal Quantity Delta','부호 있음. 사유별 방향은 CK (예: 판매 출고는 <= 0).'),
  dqty('INSPECTION_PENDING_DELTA_QTY','검수 대기 수량 증감','Inspection Pending Quantity Delta','생산 입고·반품 입고·고객 직접 반품 입고·반송 입고는 +, 입고 검수·반품 검수·반송 검수는 − (6-3 B, 7-2 A, IC-94 A).'),
  dqty('DEFECTIVE_DELTA_QTY','불량 수량 증감','Defective Quantity Delta','검수·불량 전환은 +, 수선 복귀·불량 해제·처분은 − (7-4 A, IC-98 A). 처분은 정상 ≤ 0, 불량 ≤ 0, 하나 이상 < 0 (IC-97 A, IC-104 A).'),
  dqty('HOLD_DELTA_QTY','보류 수량 증감','Hold Quantity Delta','보류 설정은 +, 보류 해제는 − (3-6 A).'),
  ('PHYSICAL_TOTAL_DELTA_QTY','실물 합계 증감 (가상 컬럼)','Physical Total Quantity Delta (Virtual)','NUMBER(8)','N','','가상 컬럼',
   '`GENERATED ALWAYS AS (NORMAL_DELTA_QTY + INSPECTION_PENDING_DELTA_QTY + DEFECTIVE_DELTA_QTY + HOLD_DELTA_QTY) VIRTUAL` (IC-87 A). 현재고 `PHYSICAL_TOTAL_QTY`의 짝이고, 증감 4개가 각각 `NUMBER(7)`이라 8자리다. '
   '상태 이동 사유(입고 검수, 반품 검수, 반송 검수, 보류 설정, 보류 해제, 불량 전환, 불량 해제, 수선 복귀)는 0이어야 한다 (CK). 예: 입고 검수에서 검수 대기 −95, 정상 +93, 불량 +1이면 −1이라 막힌다. '
   '내부 대사 ④, 스냅샷 월 누계, 수불부의 사유별 실물 합계가 이 값을 쓴다.'),
 ]),
 ('원천·근거 문서', [
  ref('SHIPMENT_ID','원천 배송 출고 식별 번호','Source Delivery Shipment Identifier',
      desc='판매 출고·재발송 출고·비주문 출고 (1-5 A). 배송 출고 행을 만드는 트랜잭션에서 넣는다. 출고 원인은 배송 출고 요청의 원인 코드에서 옮겨 사유를 고른다 (7-1 A). 합포장 출고는 출고 요청마다 행을 나눈다 (IC-106 A).'),
  ref('WAYBILL_ID','원천 운송장 식별 번호 (회수 또는 반송된 출고)','Source Waybill Identifier (Pickup or Returned Shipment)',
      desc='반품 입고는 회수 운송장(배송 완료 = 창고 도착 처리와 같은 트랜잭션, 7-2 A), 반송 입고는 수령 거절·주소 불명으로 반송 완료(`RETURNED`)된 출고 운송장(반송 완료 처리와 같은 트랜잭션, IC-94 A). 어느 운송장인지는 사유로 정해진다. 결정 원문의 "배송 패키지 ID"는 배송 DC-61 A로 운송장이 됐다.'),
  ref('CLAIM_INSPECTION_ID','원천 클레임 검수 결과 식별 번호','Source Claim Inspection Result Identifier',
      desc='반품 검수 (7-2 A). 클레임 설계 뒤 이름 확정.'),
  ref('RECEIPT_ID','원천 WMS 입고 식별 번호','Source WMS Receipt Identifier',
      desc='생산 입고 (도착, 6-3 B)와 고객 직접 반품 입고 (WMS 미확인 입고를 클레임에 연결할 때, IC-107 A). WMS 설계 뒤 이름 확정. 계획은 아래 `INBOUND_PLAN_ID`에 따로 남는다 (T-5 A).'),
  ref('RECEIPT_INSPECTION_ID','원천 WMS 입고 검수 식별 번호','Source WMS Receipt Inspection Identifier',
      desc='입고 검수 (6-3 B)와 반송 검수 (IC-94 A, 반송 박스도 WMS 입고 검수로 기록하는 것은 WMS 넘김 사항). WMS 설계 뒤 이름 확정.'),
  ref('DISPOSAL_WORK_ID','원천 WMS 처분 작업 식별 번호','Source WMS Disposal Work Identifier',
      desc='수선 복귀, 폐기, 업체 반품, 일괄 매각 (7-4 A). 화물 출고는 배송을 거치지 않는다. 폐기 증빙 첨부는 WMS 넘김 사항. WMS 설계 뒤 이름 확정.'),
  fk('STOCK_HOLD_ID','원천 보류 건 식별 번호','Source Stock Hold Case Identifier','INV_STOCK_HOLD','Y','',
     '보류 설정, 보류 해제, 보류에서의 불량 전환(보류 증감 ≠ 0) (IC-55 A, IC-86 A). 같은 INV 안이라 FK다 (2-4 A). 보류 건의 해제 누계를 같은 트랜잭션에서 고친다 (IC-54 A).'),
  fk('STOCK_EXCEPTION_ID','원천 재고 예외 식별 번호','Source Stock Exception Identifier','INV_STOCK_EXCEPTION','Y','',
     '실사 조정 (7-7 A, 8-8 후속 B). 대사 차이·현장 발견 예외 행이 조정 요청 역할을 한다. 같은 INV 안이라 FK다 (2-4 A). 예외는 파티션이 없어 FK가 파티션 제거를 막지 않는다 (T-2 A).'),
  ('SHIPMENT_REQUEST_ID','근거 출고 요청 식별 번호','Basis Shipment Request Identifier',ID,'Y','','FK 없음 (인덱스 없음)',
   '판매·재발송·비주문 출고이면 NOT NULL, 다른 사유이면 NULL (CK, IC-106 A). 합포장 출고는 출고 요청마다 행을 나눈다. 회계 구분을 정하는 값(재발송의 클레임 귀책, 비주문 유형)이 출고 요청에 있어 7-8 A가 행 단위로 작동한다. '
   '예: 교환 재발송(고객 귀책)과 사고 재발송(회사 귀책) 티셔츠가 한 박스로 나가면 원장 2행. 다른 도메인이라 FK 없이 두고, 조회는 출고 ID 전역 인덱스로 찾아 이 값으로 거른다. 원천이 아니라 근거 문서라 "원천은 정확히 하나" CK에 넣지 않는다. 정정·재기록 행은 원래 행과 같은 값. '
   '값의 출처: 출고 처리 트랜잭션이 출고 → 운송장 상품 → 출고 요청 상품을 따라 요청과 요청별·SKU별 수량을 구해 넣는다. 화면이나 호출 값으로 받지 않는다. 배송 ID라 DB 제약으로 맞는지 검사할 수 없어, 매일 검증이 (출고, 출고 요청, 현재고, 사유) 단위로 배송과 맞춰 본다 (IC-120 A).'),
  refn('STOCKTAKE_ID','근거 WMS 실사 식별 번호','Basis WMS Stocktake Identifier',
      desc='실사 조정에서 실물을 센 WMS 실사 (1-3 A). 원천은 재고 예외 ID(필수)이고 이 컬럼은 선택이라 "원천은 정확히 하나" CK에 넣지 않는다. '
           '실사가 없는 예외(대사 차이, 현장 발견)의 조정이면 NULL. 실사 조정이 아니면 NULL (CK, IC-91 A). 인덱스는 두지 않는다: 실사에서 원장으로는 재고 예외 FK 인덱스로 찾는다 (IC-116 A).'),
  fk('INBOUND_PLAN_ID','근거 입고 예정 식별 번호','Basis Inbound Plan Identifier','INV_INBOUND_PLAN','Y','',
     '사유가 생산 입고 또는 입고 검수이면 NOT NULL, 다른 사유이면 NULL (CK, T-5 A, IC-6 A로 입고 검수 추가). 입고 검수 원장은 이 차수의 검수 누계를 함께 고친다. 원가 경로 "입고 원장 → 입고 예정 → SCM 발주 라인" (6-5 A). 예정 없이 들어온 물건은 관리자가 입고 예정을 먼저 등록한다 (6-1 A). 한 입고에 같은 SKU가 입고 예정 여러 개로 들어오면 입고 예정마다 원장 1행이고 키 끝에 이 ID를 붙인다 (IC-105 A).'),
 ]),
 ('세부 사유·승인', [
  cd('ADJUSTMENT_DETAIL_REASON_CD','실사 조정 세부 사유 코드','Stocktake Adjustment Detail Reason Code','Y',
     desc='사유가 실사 조정이면 NOT NULL, 다른 사유이면 NULL (CK, 7-7 A). 감모손실과 입력 오류를 나눈다.'),
  cd('DEFECT_REASON_CD','불량 사유 코드','Defect Reason Code','Y',
     desc='불량 전환이면 NOT NULL, 아니면 NULL (CK, IC-114 A). 오염·파손·봉제·원단·인쇄·부자재·기타. 정상에서의 불량 전환은 원천 문서가 없어 원장이 유일한 기록이라, 원인별·SKU별 불량 집계와 공장 반품 근거로 쓴다. 사유 설명 필수는 그대로다(IC-5 A). WMS 입고 검수와 클레임 반품 검수도 같은 공통코드 그룹을 쓴다(넘김). 정정 행은 원래 행과 같은 값.'),
  refn('REQUESTED_ADMIN_ID','조정 요청 관리자 식별 번호','Adjustment Requesting Administrator Identifier',
      desc='실사 조정을 요청한 관리자. 사유가 실사 조정이면 NOT NULL, 아니면 NULL (CK, IC-110 A). 승인 관리자와 같으면 막는다(자기 승인 금지 CK). 승인이 필요한 조정은 승인 트랜잭션에서 원장을 넣어 `CREATED_BY`가 승인자라, 요청자는 이 컬럼에만 남는다. 정정 행은 원래 행과 같은 값. ' + ADM),
  refn('APPROVED_ADMIN_ID','조정 승인 관리자 식별 번호','Adjustment Approving Administrator Identifier',
      desc='실사 조정의 비교 수량이 적용 승인 기준 수량을 넘으면 필수 (7-7 A). 기준을 행에 복사해 CHECK가 검사한다 (IC-111 A). 요청 관리자와 같을 수 없다 (IC-110 A). 실사 조정이 아니면 NULL (CK, IC-118 A). 인덱스는 두지 않는다 (IC-116 A). 승인과 원장 반영이 같은 트랜잭션이라 승인 시각은 `CREATED_AT`이다 (IC-112 A). ' + ADM),
  qty('APPROVAL_THRESHOLD_QTY','적용 승인 기준 수량','Applied Approval Threshold Quantity',
      '원장을 넣는 순간의 실사 조정 승인 기준 수량(공통코드 정책값)을 복사하고 고치지 않는다. 사유가 실사 조정이면 NOT NULL, 아니면 NULL (CK, IC-111 A). 정책값이 10개에서 20개로 바뀌어도 당시 기준이 남는다. '
      '비교 수량(늘어난 수량 합과 줄어든 수량 합의 절대값 중 큰 값)이 이 값을 넘으면 승인 관리자 NOT NULL (CK). 예: 정상 −15, 불량 +15면 비교 수량 15, 기준 10이면 승인 필수. 금액 기준은 원가가 없어 쓰지 않는다(6-5 A). 정정 행은 원래 행과 같은 값.',d='',null='Y',t='NUMBER(7)'),
  ('REASON_NOTE_CN','사유 설명','Reason Note','VARCHAR2(500)','Y','','',
   '관리자가 처리하는 사유(보류 설정, 보류 해제, 불량 전환, 불량 해제)와 정정 행이면 NOT NULL (CK, IC-5 A, IC-16 A, IC-98 A). 보류 사유 "기타"의 메모는 보류 건으로 옮겼다 (IC-55 A). 정정 행에는 정정 이유를 적는다(예: "수량 입력 오류, 송장 기준 95개"). 다른 사유는 선택. 예: "고객 불만 3건으로 보풀 확인", "B-11 선반에서 오염 발견". '
   '실사 조정은 재고 예외의 처리 내용이 같은 역할이라 필수가 아니다. 길이는 바이트 기준(한글 약 160자)이고 단위는 공통 규칙(주문 OC-115)을 따른다.'),
 ]),
 ],
 idx=['IX LOCAL `STOCK_ID`, `BUSINESS_DT` (수불부 조회: 현재고 + 기간)',
      'IX 전역 `INBOUND_PLAN_ID`, `STOCK_EXCEPTION_ID`, `STOCK_HOLD_ID` (FK, 입고 예정·예외·보류 건 삭제 전 검사, T-2 A, T-3 A, IC-57 A, IC-92 A)',
      'IX 전역 원천 컬럼 6개 (값 참조, 원천에서 원장을 찾는 조회와 매일 검증. 업무 일자를 모르는 조회라 전역, IC-92 A)',
      'UK `LEDGER_KEY_VAL`, UK `REVERSED_STOCK_LEDGER_ID` (전역 인덱스)'],
 check=['사유별 원천: 원천 컬럼 8개(`SHIPMENT_ID`~`STOCK_EXCEPTION_ID`) 중 사유에 맞는 하나만 NOT NULL, 나머지는 NULL (2-4 A). 보류 설정·보류 해제는 `STOCK_HOLD_ID`, 불량 전환은 보류 증감 ≠ 0이면 `STOCK_HOLD_ID`이고 = 0(정상에서의 전환, 원천 없음, 행위자는 `CREATED_BY`)이면 모두 NULL '
        '(IC-55 A, IC-85 A, IC-86 A). 기초 재고와 불량 해제는 모두 NULL (IC-82 A, IC-98 A). 반송 입고는 `WAYBILL_ID`, 반송 검수는 `RECEIPT_INSPECTION_ID` (IC-94 A). 고객 직접 반품 입고는 `RECEIPT_ID` (IC-107 A). 정정 행과 재기록 행은 원래 행과 같은 원천 컬럼을 채운다 (IC-88 A)',
        '사유별 증감 방향: 사유마다 + / − / 0인 버킷을 고정한다. `REVERSED_STOCK_LEDGER_ID`가 NOT NULL이면 방향을 모두 반대로 본다 (T-6 B). 기초 재고는 정상·불량 >= 0, 검수 대기·보류 = 0 (IC-82 A). 처분 3사유(폐기, 업체 반품, 일괄 매각)는 정상 ≤ 0, 불량 ≤ 0, 둘 중 하나 이상 < 0, 검수 대기·보류 = 0이라 한 작업에 섞인 정상·불량을 한 행에 담는다 (IC-97 A, IC-104 A, 7-4 A 변경). '
        '반송 입고와 고객 직접 반품 입고는 검수 대기 +, 반송 검수는 검수 대기 −·정상 +·불량 + (IC-94 A). 불량 해제는 불량 −·정상 + (IC-98 A)',
        '증감 4개가 모두 0인 행은 막는다',
        '상태 이동 사유(입고 검수, 반품 검수, 반송 검수, 보류 설정, 보류 해제, 불량 전환, 불량 해제, 수선 복귀)는 `PHYSICAL_TOTAL_DELTA_QTY` = 0. 정정 행도 합이 0이라 같은 식으로 통과한다 (IC-87 A, IC-94 A, IC-98 A)',
        '사유가 생산 입고 또는 입고 검수이면 `INBOUND_PLAN_ID` NOT NULL, 아니면 NULL (T-5 A, IC-6 A)',
        '보류 설정·보류 해제·불량 전환·불량 해제이거나 정정 행(`REVERSED_STOCK_LEDGER_ID` NOT NULL)이면 `REASON_NOTE_CN` NOT NULL (IC-5 A, IC-16 A, IC-55 A, IC-98 A)',
        '사유가 판매·재발송·비주문 출고이면 `SHIPMENT_REQUEST_ID` NOT NULL, 아니면 NULL (IC-106 A)',
        '`REVERSED_STOCK_LEDGER_ID IS NULL OR REPOSTED_FROM_STOCK_LEDGER_ID IS NULL` (한 행이 정정 행이면서 재기록 행일 수 없다. 둘 다 채우면 방향 CHECK가 재기록 값을 반대로 읽는다. 재기록 행이 다시 틀리면 그 재기록 행을 정정한다, IC-117 A)',
        '`ADJUSTMENT_DETAIL_REASON_CD`는 실사 조정일 때만 NOT NULL. `STOCKTAKE_ID`는 실사 조정이 아니면 NULL (IC-91 A)',
        '사유가 실사 조정이면 `REQUESTED_ADMIN_ID`, `APPROVAL_THRESHOLD_QTY` NOT NULL. 실사 조정이 아니면 이 둘과 `APPROVED_ADMIN_ID`가 모두 NULL이다: 다른 사유 행에 승인자가 있으면 막는다 (IC-110 A, IC-111 A, IC-118 A)',
        '`APPROVED_ADMIN_ID IS NULL OR APPROVED_ADMIN_ID <> REQUESTED_ADMIN_ID` (자기 승인 금지, IC-110 A). 승인 관리자가 NULL(기준 이하)이면 통과한다',
        '실사 조정이고 `GREATEST(GREATEST(NORMAL_DELTA_QTY,0) + GREATEST(INSPECTION_PENDING_DELTA_QTY,0) + GREATEST(DEFECTIVE_DELTA_QTY,0) + GREATEST(HOLD_DELTA_QTY,0), -(LEAST(NORMAL_DELTA_QTY,0) + LEAST(INSPECTION_PENDING_DELTA_QTY,0) + LEAST(DEFECTIVE_DELTA_QTY,0) + LEAST(HOLD_DELTA_QTY,0))) > APPROVAL_THRESHOLD_QTY`이면 `APPROVED_ADMIN_ID` NOT NULL. 비교 수량은 늘어난 합과 줄어든 합(절대값) 중 큰 값이라 버킷 사이 이동을 한 번만 센다. 정정 행은 부호만 반대라 같은 값으로 통과한다 (IC-111 A)',
        '실사 조정 세부 사유가 분실·파손이면 `PHYSICAL_TOTAL_DELTA_QTY` < 0, 초과 발견이면 > 0. 입력 오류 정정·원인 불명은 제한 없음. 정정 행은 반대로 본다 (IC-113 A)',
        '사유가 불량 전환이면 `DEFECT_REASON_CD` NOT NULL, 아니면 NULL (IC-114 A)',
        '`BUSINESS_DT <= TRUNC(CREATED_AT)` (8-2 C)',
        '창고 이동 출고·입고는 자리만 남긴 값이라 CK의 허용 사유에서 뺀다 (1-7 A, 창고를 늘릴 때 연다)'])

# =========================================================== 2-1. 보류 건
table(t='INV_STOCK_HOLD', ko='보류 건 (판매 상품을 잠시 팔지 않는 건)', en='Stock Hold Case',
 desc='판매 상품 현재고의 보류 1건마다 1행 (IC-52 C, 3-6 A 변경). 예: 12/1 니트 L 20개를 보풀 확인으로 보류. 현재고의 `HOLD_QTY`는 진행 중 보류 건의 남은 수량 합계다(내부 대사 ⑤). '
      '일부 해제와 불량 전환은 누계 컬럼으로 남기고, 해제 하나하나의 기록은 원장 행이 이 건을 가리켜 남긴다 (IC-54 A, IC-55 A). 보류 설정·해제·불량 전환 원장, 현재고 UPDATE와 같은 트랜잭션에서 고친다. '
      '보류 수량은 그때의 판매 가능 수량(정상 − 예약 − 할당)까지다. 넘으면 판매 가능 CHECK가 막고, 예약·할당을 풀지 않는다. 예: 정상 10, 예약 8이면 2개까지 (IC-72 A).',
 basis='3-6 A, IC-5 A, IC-28 B, IC-52 C, IC-54 A, IC-55 A, IC-56 A, IC-57 A, IC-72 A',
 pk='대리 PK `SEQ_INV_STOCK_HOLD`', cache=20,
 delete='상태로 처리한다. 종결 + 5년이 지나고 가리키는 원장 행이 없는 행을 매일 배치가 나눠서 DELETE한다 (IC-57 A, 입고 예정 T-3 A와 같은 방식)',
 part='없음 (보류는 드물다)', keep='종결 + 5년, 가리키는 원장이 없을 때까지 (IC-57 A)',
 cols=[
 ('식별', [
  ('STOCK_HOLD_ID','보류 건 고유 식별 번호','Stock Hold Case Unique Identifier',ID,'N','','PK','원장의 보류 설정·해제·불량 전환 행이 이 ID를 FK로 가리킨다 (IC-55 A).'),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK','N','','보류한 판매 상품 현재고 행.'),
  cd('HOLD_REASON_CD','보류 사유 코드','Hold Reason Code',desc='품질 확인, 촬영 대기, 기타 (3-6 A). 원장에서 이 테이블로 옮겼다 (IC-55 A).'),
  cd('HOLD_STATUS_CD','보류 상태 코드','Hold Status Code',desc='진행 / 종결 (IC-54 A). 남은 수량이 0이 되는 UPDATE에서 종결로 바꾼다.'),
 ]),
 ('수량', [
  ('REMAINING_HOLD_QTY','남은 보류 수량 (가상 컬럼)','Remaining Hold Quantity (Virtual)',QTY,'N','','가상 컬럼, CK (>= 0)',
   '`GENERATED ALWAYS AS (HOLD_QTY - RELEASED_NORMAL_QTY - DEFECT_TRANSFERRED_QTY) VIRTUAL` (IC-54 A). 진행 중 건의 합이 현재고 `HOLD_QTY`와 같다(내부 대사 ⑤). 예: 20 − 18 − 2 = 0이면 종결.'),
  qty('HOLD_QTY','보류 수량','Hold Quantity','보류를 설정한 수량. 만든 뒤 바꾸지 않는다. 더 보류할 물건은 새 건으로 만든다 [확인 필요].', d='', ck='CK (> 0)'),
  qty('RELEASED_NORMAL_QTY','정상 해제 수량','Released to Normal Quantity','보류 해제(보류 −, 정상 +) 원장의 누계 (IC-54 A).'),
  qty('DEFECT_TRANSFERRED_QTY','불량 전환 수량','Transferred to Defective Quantity','보류에서의 불량 전환(보류 −, 불량 +) 원장의 누계 (IC-54 A).'),
 ]),
 ('기간', [
  ('HOLD_STARTED_AT','보류 시작 일시','Hold Started At',TS,'N','','',
   '보류 설정 원장과 같은 트랜잭션에서 채운다. 현재고의 근사값 `HOLD_SINCE_AT`(IC-2 B)을 대신한다 (IC-56 A).'),
  ('EXPECTED_RELEASE_DT','해제 예정일','Expected Release Date','DATE','Y','','',
   '지나면 오래된 보류(신호 6)로 본다. NULL이면 시작 일시 + 기준 일수(정책값)로 본다 (IC-56 A). 예: 촬영 대기 12/20.'),
  ('CLOSED_AT','종결 일시','Closed At',TS,'Y','','','상태가 종결이면 NOT NULL (CK). 보존 기간의 기준이다 (IC-57 A).'),
 ]),
 ('담당·메모', [
  ref('OWNER_ADMIN_ID','담당 관리자 식별 번호','Owner Administrator Identifier',desc='보류를 확인하고 풀 담당자 (3-6 B 안의 담당). ' + ADM),
  ('HOLD_NOTE_CN','보류 메모','Hold Note','VARCHAR2(500)','Y','','',
   '보류 사유가 기타이면 NOT NULL (CK, IC-5 A의 조건을 옮김). 해제 때의 설명은 원장의 사유 설명에 적는다. 예: "고객 불만 3건으로 보풀 확인".'),
 ]),
 ],
 idx=['IX `STOCK_ID` (FK, 현재고의 진행 중 보류 건 조회와 내부 대사 ⑤)', 'IX (`HOLD_STATUS_CD`, `EXPECTED_RELEASE_DT`) (오래된 보류 감시, IC-56 A)'],
 check=['`REMAINING_HOLD_QTY >= 0`. 수량 3개는 각각 >= 0이고 `HOLD_QTY > 0`',
        '상태가 종결이면 `REMAINING_HOLD_QTY = 0`이고 `CLOSED_AT` NOT NULL, 진행이면 `CLOSED_AT` NULL',
        '`EXPECTED_RELEASE_DT >= TRUNC(HOLD_STARTED_AT)` (해제 예정일이 NULL이면 통과)',
        '보류 사유가 기타이면 `HOLD_NOTE_CN` NOT NULL'])

# =========================================================== 2-2. 안전 재고 변경 이력
table(t='INV_SAFETY_STOCK_HIST', ko='안전 재고 변경 이력', en='Safety Stock Change History',
 desc='판매 상품 현재고의 안전 재고, 수동 지정 여부, 수동 지정 종료일 중 하나라도 바뀔 때마다 1행 (IC-53 C, IC-58 A, IC-130 A). "왜 8이 됐나"를 사유, 적용 등급, 수동 지정 여부의 변화로 답한다 (IC-59 A). "이 변경 때문에 품절이 됐나"는 변경 시점 판매 가능 수량으로(IC-123 A), "한 번의 작업으로 바뀐 행"은 변경 작업 키로(IC-124 A) 답한다. 값·수동 지정 여부·종료일이 모두 그대로인 행은 남기지 않는다 (IC-125 A, IC-130 A). '
      '현재고 UPDATE와 같은 트랜잭션에서 넣고 고치지 않는다. 변경자는 시스템 컬럼(`CREATED_BY_TYPE_CD`: 관리자 `ADMIN`, 등급 배치 `BATCH`)이 남긴다. 리오더 기준은 남기지 않는다 (IC-58 A).',
 basis='5-1 B, IC-4 A, IC-19 A, IC-53 C, IC-58 A, IC-59 A, IC-60 A, IC-77 B, IC-123 A~IC-125 A, IC-126 C, IC-127 B, IC-128 A, IC-129 B, IC-130 A~IC-132 A, IC-133 A~IC-135 A, IC-136 B, IC-137 A, IC-138 B, IC-140 B~IC-141 B, IC-142 A~IC-146 A, IC-147 B, IC-148 A, IC-149 A',
 pk='대리 PK `SEQ_INV_SAFETY_STOCK_HIST`', cache=20,
 delete='삭제하지 않는다 (이력). 5년이 지난 파티션을 제거한다 (IC-60 A)',
 part='생성 일시(`CREATED_AT`) 월 INTERVAL 파티션 (IC-60 A)', keep='생성 + 5년 (IC-60 A, 일 스냅샷과 같은 기간)',
 cols=[
 ('식별', [
  ('SAFETY_STOCK_HIST_ID','안전 재고 변경 이력 고유 식별 번호','Safety Stock Change History Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK'),
  cd('SAFETY_STOCK_CHANGE_REASON_CD','안전 재고 변경 사유 코드','Safety Stock Change Reason Code',
     desc='신규 행 기본값, 등급 기본값 적용, 등급 없음 기본값, 기본값 변경 적용, 관리자 수정, 기본값 복귀, 수동 지정 만료 복귀, 작업 원복 8개 (IC-59 A, IC-77 B, IC-128 A, IC-133 A, IC-134 A).'),
  ('CHANGE_OPERATION_KEY_VAL','변경 작업 키','Change Operation Key','VARCHAR2(50)','N','','',
   '한 번의 작업이 만든 행은 같은 값이다 (IC-124 A). 관리자 요청(단건, 일괄 수정, 기본값 변경)은 화면이 요청마다 발급하는 UUID(36자, 원장 요청 키와 같은 방식). 등급 배치는 `GRADE_BATCH:{실행 연월}:{실행 순번}`, 수동 지정 종료 배치는 `MANUAL_END_BATCH:{실행 일자}:{실행 순번}`, 신규 행 기본값은 `NEW_ROW:{SKU ID}`. '
   '예: 12/1 겨울 행사 대비 300건 일괄 상향은 모두 같은 UUID라, 같은 시간대의 단건 수정과 갈리고 그 300건만 되돌릴 수 있다. 되돌릴 때는 그 작업 뒤(생성 일시) 다른 변경 이력이 없는 현재고만 되돌린다(예: 12/5 따로 25로 고친 패딩 L은 건너뜀, IC-132 A). 원복 작업도 요청 하나가 UUID 하나이고, 되돌린 작업의 키는 원복 대상 작업 키에 남는다 (IC-133 A). 이관할 수동 값이 있으면 신규 행 기본값 + 관리자 수정 두 행으로 넣고, 관리자 수정 행의 키는 `MIGRATION:{실행 일자}`로 한다 (IC-137 A). 조회는 기간(월 파티션) + 이 값으로 하고 인덱스는 두지 않는다. 배치 키 형식은 배치 실행 이력(`BAT`)을 설계할 때 실행 ID로 바꿀 수 있다.'),
 ]),
 ('안전 재고 값', [
  qty('BEFORE_SAFETY_STOCK_QTY','이전 안전 재고 수량','Before Safety Stock Quantity','신규 행 기본값이면 NULL, 아니면 NOT NULL (CK).', d='', null='Y'),
  qty('AFTER_SAFETY_STOCK_QTY','새 안전 재고 수량','After Safety Stock Quantity','바뀐 뒤의 값. 예: 5 → 8의 8.', d=''),
  qty('AVAILABLE_QTY_AT_CHANGE','변경 시점 판매 가능 수량','Available Quantity at Change',
      '현재고 UPDATE의 `RETURNING AVAILABLE_QTY`로 받아 같은 트랜잭션에서 넣는다 (IC-123 A). 신규 행 기본값이면 0 (CK, IC-131 A: 현재고 행은 수량 0으로 만들어지므로, 기초 재고를 먼저 넣는 순서 실수를 잡는다). 변경 전후 일반 주문 가능 수량은 GREATEST(이 값 − 이전·새 안전 재고, 0)이다. '
      '예: 판매 가능 8에서 안전 재고 2 → 10이면 일반 주문 가능 6 → 0이라, 이 변경이 품절을 만들었다고 행 하나로 안다. 품절 시작 일시는 다시 입고되면 지워지므로 여기 남긴다.', d=''),
 ]),
 ('수동 지정 여부·종료일', [
  ('BEFORE_MANUAL_YN','이전 수동 지정 여부','Before Manually Set Flag',YN,'Y','','CK (Y/N)','신규 행 기본값이면 NULL. 기본값 복귀와 수동 지정 만료 복귀는 Y (IC-19 A, IC-134 A).'),
  ('AFTER_MANUAL_YN','새 수동 지정 여부','After Manually Set Flag',YN,'N','','CK (Y/N)','관리자 수정이면 Y, 등급 기본값 적용·등급 없음 기본값·기본값 변경 적용·기본값 복귀·수동 지정 만료 복귀·신규 행 기본값이면 N (IC-128 A, IC-134 A). 작업 원복은 대상 작업 행의 이전 수동 지정 여부와 같다 (IC-133 A).'),
  ('BEFORE_MANUAL_END_DT','이전 수동 지정 종료일','Before Manual Setting End Date','DATE','Y','','',
   '바뀌기 전 현재고의 안전 재고 수동 지정 종료일 (IC-130 A). 종료일이 없었거나 신규 행이면 NULL. 이전 수동 지정 여부가 N이면 NULL (CK, 현재고 CK와 같은 규칙).'),
  ('AFTER_MANUAL_END_DT','새 수동 지정 종료일','After Manual Setting End Date','DATE','Y','','',
   '바뀐 뒤의 종료일 (IC-130 A). 새 수동 지정 여부가 N이면 NULL (CK). 지난 날짜는 넣을 수 없다(`>= TRUNC(CREATED_AT)`, 오늘은 허용, CK, IC-135 A). 현재고는 오늘 날짜를 CHECK에 쓸 수 없어 같은 트랜잭션의 이 행이 대신 막는다. 관리자가 종료일만 직접 고쳐도 1행이고 사유는 관리자 수정(메모 필수)이다. 그 작업을 원복하면 작업 원복이다(예: 12/22 "12/20 연장 원복"은 1/15 → 12/31, 값 그대로, IC-133 A). '
   '예: 12/1 패딩 L 5 → 20, 종료일 12/31(이전 NULL, 새 12/31) → 12/20 종료일만 1/15로 연장(값 20 → 20, Y → Y, 12/31 → 1/15, 메모 "행사 연장") → 1/16 배치 수동 지정 만료 복귀(20 → 5, Y → N, 1/15 → NULL, IC-134 A).'),
 ]),
 ('근거', [
  cd('APPLIED_STOCK_GRADE_CD','적용 재고 등급 코드','Applied Stock Grade Code','Y',n=10,
     desc='등급 기본값 적용이면 NOT NULL (CK). 기본값 복귀, 수동 지정 만료 복귀, 수동 지정 N으로 되돌린 작업 원복, 신규 행 기본값, 기본값 변경 적용은 그때 등급이 있으면 채운다(등급 없음이면 NULL). 예: B → A로 올라 A 기본값 8을 적용.'),
  cd('BEFORE_STOCK_GRADE_CD','이전 재고 등급 코드','Before Stock Grade Code','Y',n=10,
     desc='등급 기본값 적용·등급 없음 기본값이면 현재고를 고치기 전 등급(판매 이력 없음이었으면 NULL). 다른 사유이면 NULL (CK, IC-126 C). 예: B → A면 B, C → 판매 이력 없음이면 C. '
          '안전 재고가 바뀐 행에만 남아 등급 이력으로는 불완전하다. 등급 추세는 2차 재고 스냅샷에 등급을 넣을지 그 테이블 검토 때 본다(진행메모).'),
  qty('POLICY_DEFAULT_SAFETY_STOCK_QTY','변경 당시 정책 기본 안전 재고 수량','Policy Default Safety Stock Quantity at Change',
      '넣는 순간 그 행에 적용되는 정책 기본값(등급 기본값, 등급 없으면 공통 기본값)을 복사한다 (IC-127 B). 공통코드는 이전 값이 남지 않아서다. 관리자 수정과 수동 지정 Y로 되돌린 작업 원복이 아닌 사유는 새 안전 재고 수량과 같다 (CK, IC-133 A). '
      '예: A등급 기본값 8일 때 관리자가 7 → 10으로 올리면 8이 남아 정책보다 2개 더 잡았음을 안다. 나중에 기본값을 12로 바꿔도 당시 판단이 남는다.', d=''),
  cd('ADMIN_CHANGE_REASON_CD','관리자 변경 사유 코드','Administrator Change Reason Code','Y',
     desc='관리자가 왜 바꿨나를 고르는 업무 사유 (IC-136 B). 관리자 수정·작업 원복·기본값 복귀이면 NOT NULL, 다른 사유이면 NULL (CK, IC-146 A). 메모는 관리자 수정·작업 원복에서 필수이고, 기본값 복귀는 기타를 골랐을 때만 필수다 (CK, IC-149 A). 작업 원복 행은 원래 작업의 이유가 아니라 되돌리는 이유를 고른다 (IC-145 A). '
          '예: 12/1 기획전 대비 상향 → 기획전 대비, 12/5 기획전 취소로 원복 → 운영 계획 철회, 12/3 생산 지연으로 상향 → 입고 차질 대비, 5를 50으로 잘못 넣은 것을 고침 → 입력 오류 정정, 이관 → 기타(집계 때 작업 키 `MIGRATION:`으로 뺀다, IC-147 B). 분기 말 "기획전 때문에 올린 건"을 바로 센다. '
          '특정 실물을 빼 두는 품질 확인·촬영 대기는 안전 재고가 아니라 보류(보류 사유 품질 확인, 촬영 대기)로 처리한다 (IC-148 A).'),
  ('REVERTED_OPERATION_KEY_VAL','원복 대상 작업 키','Reverted Operation Key','VARCHAR2(50)','Y','','',
   '작업 원복이 되돌린 작업의 변경 작업 키 (IC-133 A). 작업 원복이면 NOT NULL, 아니면 NULL (CK). 인덱스는 두지 않는다. 대상은 관리자 작업(관리자 수정, 기본값 복귀)만이고 자동 작업은 되돌리지 않는다(애플리케이션 검사). '
   '되돌리는 값은 대상 행의 이전 수동 지정 여부로 정한다: Y였으면 이전 값과 이전 종료일, N이었으면 지금 기본값·N·종료일 NULL. 그 작업 뒤 다른 변경이 있거나 옛 종료일이 이미 지난 현재고는 건너뛴다. '
   '예: 12/1 일괄 상향(UUID a1…)을 12/10 원복하면 패딩 L(5 → 20, N → Y)은 20 → 8(그사이 바뀐 기본값), Y → N이고 이 컬럼은 a1…이다. 니트 M(7 → 15, Y → Y)은 15 → 7, Y 유지.'),
  ('CHANGE_NOTE_CN','변경 메모','Change Note','VARCHAR2(500)','Y','','','관리자 수정·작업 원복이면 NOT NULL (CK, IC-59 A, IC-133 A). 예: "겨울 행사 대비 상향", 종료일만 바꾸면 "행사 연장, 1/15까지" (IC-130 A), 원복이면 "12/1 일괄 상향 취소".'),
 ]),
 ],
 idx=['IX LOCAL (`STOCK_ID`, `CREATED_AT`) (현재고별 변경 경위 조회)'],
 check=['신규 행 기본값이면 이전 안전 재고·이전 수동 지정 여부·이전 종료일이 NULL. 아니면 이전 안전 재고·이전 수동 지정 여부 NOT NULL(이전 종료일은 종료일이 없었으면 NULL, IC-130 A)',
        '등급 기본값 적용이면 이전·새 수동 지정 여부가 모두 N이고 `APPLIED_STOCK_GRADE_CD` NOT NULL, `CREATED_BY_TYPE_CD = \'BATCH\'` (IC-138 B)',
        '등급 없음 기본값이면 이전·새 수동 지정 여부가 모두 N이고 `APPLIED_STOCK_GRADE_CD` NULL, `CREATED_BY_TYPE_CD = \'BATCH\'` (IC-77 B, IC-138 B)',
        '관리자 수정이면 새 수동 지정 여부 Y와 `CHANGE_NOTE_CN` NOT NULL. 기본값 복귀이면 이전 Y, 새 N이고 `CREATED_BY_TYPE_CD = \'ADMIN\'` (관리자만, IC-134 A)',
        '수동 지정 만료 복귀이면 `CREATED_BY_TYPE_CD = \'BATCH\'`, 이전 Y, 새 N, `BEFORE_MANUAL_END_DT IS NOT NULL AND BEFORE_MANUAL_END_DT < TRUNC(CREATED_AT)` (종료일 전 자동 복귀를 막는다, IC-134 A)',
        '작업 원복이면 `REVERTED_OPERATION_KEY_VAL`·`CHANGE_NOTE_CN` NOT NULL이고 `CREATED_BY_TYPE_CD = \'ADMIN\'` (관리자만, IC-138 B), 아니면 `REVERTED_OPERATION_KEY_VAL` NULL (IC-133 A). 관리자 수정에는 행위자 CK를 걸지 않는다(이관 행이 `BATCH`, IC-137 A)',
        '관리자 수정·작업 원복·기본값 복귀이면 `ADMIN_CHANGE_REASON_CD` NOT NULL, 아니면 NULL (IC-136 B, IC-146 A)',
        '`ADMIN_CHANGE_REASON_CD <> \'OTHER\' OR CHANGE_NOTE_CN IS NOT NULL` (기타면 메모 필수. 사유가 NULL인 자동 사유 행은 비교가 UNKNOWN이라 통과. 실제로 걸리는 것은 메모가 선택인 기본값 복귀 + 기타, IC-149 A)',
        '`AFTER_MANUAL_END_DT IS NULL OR AFTER_MANUAL_END_DT >= TRUNC(CREATED_AT)` (지난 날짜 종료일 금지, 오늘은 허용, IC-135 A)',
        '안전 재고 수량 2개는 각각 >= 0 (이전 값이 NULL이면 통과)',
        '`BEFORE_SAFETY_STOCK_QTY IS NULL OR BEFORE_SAFETY_STOCK_QTY <> AFTER_SAFETY_STOCK_QTY OR BEFORE_MANUAL_YN <> AFTER_MANUAL_YN OR DECODE(BEFORE_MANUAL_END_DT, AFTER_MANUAL_END_DT, 0, 1) = 1` (값·수동 지정 여부·종료일이 모두 그대로인 행을 막는다. 종료일은 NULL이 될 수 있어 `<>` 대신 `DECODE`로 비교한다: NULL끼리는 같고 NULL과 날짜는 다르다. 신규 행은 이전 값이 NULL이라 통과, 기본값 복귀 5 → 5·Y → N, 값 고정 N → Y, 종료일만 연장은 통과, IC-125 A, IC-130 A)',
        '`AFTER_MANUAL_YN = \'Y\' OR AFTER_MANUAL_END_DT IS NULL`, `BEFORE_MANUAL_YN = \'Y\' OR BEFORE_MANUAL_END_DT IS NULL` (수동 지정 N이면 종료일 NULL, 현재고 CK와 같은 규칙. 이전 수동 지정 여부가 NULL인 신규 행은 이전 종료일도 NULL이라 통과, IC-130 A)',
        '신규 행 기본값이면 `AVAILABLE_QTY_AT_CHANGE = 0` (IC-131 A)',
        '신규 행 기본값이면 `AFTER_MANUAL_YN = \'N\'` (IC-125 A)',
        '기본값 변경 적용이면 이전·새 수동 지정 여부가 모두 N (IC-128 A)',
        '관리자 수정이 아니고 새 수동 지정 여부가 Y인 작업 원복도 아니면 `POLICY_DEFAULT_SAFETY_STOCK_QTY = AFTER_SAFETY_STOCK_QTY` (IC-127 B, IC-133 A: 수동 지정 N으로 되돌린 원복은 지금 기본값이어야 한다)',
        '등급 기본값 적용·등급 없음 기본값이 아니면 `BEFORE_STOCK_GRADE_CD` NULL (IC-126 C)'])

# =========================================================== 3. 재고 확보
table(t='INV_STOCK_COMMITMENT', ko='재고 확보 (주문·출고 요청이 잡은 수량)', en='Stock Commitment',
 desc='판매 상품의 주문 상품 1개, 주문 없는 출고 요청 상품 1개마다 1행 (4-2 A, 4-10 A). 사은품 확보는 사은품 현재고의 예약 수량과 주문 사은품 행으로 한다 (IC-45 C). 예약 → 할당 → 종결로 진행하고, 실물이 없으면 입고 예정에 걸린다 (6-2 A, 4-8 B). '
      '현재고의 예약·할당 수량의 근거다 (2-3 C). 이름은 예약·할당 두 상태를 모두 담아 COMMITMENT(약속한 재고)로 했다 (T-10 A).',
 basis='1-2 A, 1-6 A, 2-3 C, 4-2 A, 4-3 A, 4-5 A, 4-7 A~4-10 A, 4-12 A, 5-9 A, 6-2 A, 6-4 B, 8-3 A, 8-9 B, 8-9 후속 A, T-1 A, T-10 A, IC-9 A, IC-10 B, IC-45 C',
 pk='대리 PK `SEQ_INV_STOCK_COMMITMENT`', cache=100,
 delete='삭제하지 않는다 (상태로 처리). 확보 일시 기준 5년이 지난 파티션을 제거한다. 제거 전에 진행 중(종결이 아닌) 행이 0인지 검사한다 (8-9 후속 A)',
 part='확보 일시(`COMMITTED_AT`) 월 INTERVAL 파티션 (8-9 후속 A). 재고 예외는 이 테이블을 FK 없이 가리켜 파티션 제거가 막히지 않는다 (T-1 A)',
 keep='확보 일시 + 5년 (8-9 B, 8-9 후속 A)',
 cols=[
 ('식별', [
  ('STOCK_COMMITMENT_ID','재고 확보 고유 식별 번호','Stock Commitment Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','현재고 식별 번호','Stock on Hand Identifier','INV_STOCK','N','','창고와 품목은 현재고 행에서 읽는다 (1-6 A).'),
  ref('ORDER_ITEM_ID','대상 주문 상품 식별 번호','Target Order Item Identifier',
      desc='판매 상품 주문. 대상 2개 중 정확히 하나 (CK, 4-2 A, IC-45 C로 사은품 제외). 주문 쪽 ID라 FK 없음 (주문 10-10 C).'),
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
      'IX `ORDER_ITEM_ID`, `SHIPMENT_REQUEST_ITEM_ID` (값 참조)',
      'UK 함수 기반: 종결이 아닐 때만 `ORDER_ITEM_ID` (주문 상품마다 진행 중 확보 1행, 4-9 A) [확인 필요: 출고 요청 상품에도 같은 UK를 둘지]',
      'IX (`STOCK_COMMITMENT_STATUS_CD`, `COMMITTED_AT`) (오래 남은 예약 감시, 신호 1)'],
 check=['대상 2개(`ORDER_ITEM_ID`, `SHIPMENT_REQUEST_ITEM_ID`) 중 정확히 하나만 NOT NULL (4-2 A, 4-10 A, IC-45 C)',
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
 desc='(판매 상품·사은품·운영자재 현재고 행 중 하나, 입고 차수)마다 1행 (6-1 A, IC-49 C). 대상 현재고 3개 중 정확히 하나를 채운다. 예약 판매 한도와 예정일 고지, 실물이 모자랄 때 기다릴 수 있는지를 판단하는 근거다 (6-2 A, 4-8 B). '
      'SCM 발주가 확정되면 만들고, SCM 설계 전까지는 관리자가 직접 등록한다. 생산 입고 원장이 이 행을 가리켜 원가 경로가 이어진다 (T-5 A, 6-5 A). 예약 판매 확보와 입고 검수 누계는 판매 상품 행에만 쓴다 (CK). '
      '사은품·운영자재 행은 리오더 판정에서 오는 중인 물량을 빼는 데 쓴다 (IC-49 C).',
 basis='4-8 B, 5-9 A, 6-1 A~6-5 A, 8-3 A, T-3 A, T-5 A, T-9 A, T-10 A, T-11 A, IC-6 A, IC-8 A, IC-49 C',
 pk='대리 PK `SEQ_INV_INBOUND_PLAN`', cache=20,
 delete='삭제하지 않는다 (상태로 처리). 완료·취소 + 5년이 지나고 가리키는 확보·원장·확보 처리 이력이 없는 행을 일 배치가 나눠서 DELETE한다 (T-3 A, 선행 11)',
 part='없음 (T-3 A). 확보·원장이 FK로 가리키는 부모라 파티션 제거가 ORA-02266에 걸린다',
 keep='종료 일시(`CLOSED_AT`) + 5년, 가리키는 확보·원장이 없을 때 (T-3 A)',
 cols=[
 ('식별', [
  ('INBOUND_PLAN_ID','입고 예정 고유 식별 번호','Inbound Plan Unique Identifier',ID,'N','','PK',''),
  fk('STOCK_ID','판매 상품 현재고 식별 번호','Stock on Hand Identifier','INV_STOCK','Y','',
     '판매 상품 입고(생산). 대상 현재고 3개 중 정확히 하나 (CK, IC-49 C).'),
  fk('FREEBIE_STOCK_ID','사은품 현재고 식별 번호','Free Gift Stock Identifier','INV_FREEBIE_STOCK','Y','',
     '사은품 구매 입고 (IC-49 C).'),
  fk('SUPPLY_STOCK_ID','운영자재 현재고 식별 번호','Operating Supply Stock Identifier','INV_SUPPLY_STOCK','Y','',
     '포장재·수선 부자재 구매 입고 (IC-49 C).'),
  ('INBOUND_ROUND_NO','입고 차수','Inbound Round Number','NUMBER(3)','N','','CK (>= 1)',
   '같은 대상 현재고 행 안에서 1부터 매긴다. 대상마다 함수 기반 UK (대상 ID, 차수). WMS의 입고 차수(로트, 1-4 A)와는 다른 번호다 [확인 필요: WMS 입고 차수와 맞출지].'),
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
      '판매 상품 행만 쓴다(사은품·운영자재 행은 0, CK). 이 차수에 걸린 진행 중 확보(`INBOUND_PLAN_ID`가 이 행)의 남은 수량(확보 − 출고 − 해제) 합계 (6-2 A, 내부 대사 ③, IC-9 A). 현재고처럼 증감 UPDATE 한 문장으로만 바꾼다. '
      '새 예약 판매 한도는 GREATEST(예정 − 입고 − 확보, 0)이고 애플리케이션이 검사한다. 도착했지만 검수 전인 수량은 기존 확보만 받치고 새 예약에는 열지 않는다 (IC-8 A).'),
  qty('INSPECTED_NORMAL_QTY','검수 양품 수량 (누계)','Inspected Normal Quantity (Cumulative)',
      '판매 상품 행만 쓴다(사은품·운영자재는 구매 입고에 검수 단계가 없어 0) [확인 필요]. 입고 검수 원장과 같은 트랜잭션에서 늘린다 (IC-6 A). 차수별 불량률, 업체 반품·매입 차감(SCM)의 근거. 원장(입고 검수, 이 차수)의 정상 증감 합계와 같다.'),
  qty('INSPECTED_DEFECTIVE_QTY','검수 불량 수량 (누계)','Inspected Defective Quantity (Cumulative)',
      '입고 검수 원장과 같은 트랜잭션에서 늘린다 (IC-6 A). 입고 − 양품 − 불량 = 아직 검수하지 않은 수량.'),
 ]),
 ('종료', [
  ('CLOSED_AT','종료 일시 (완료·취소)','Closed At (Completed / Canceled)',TS,'Y','','',
   '상태가 완료·취소이면 NOT NULL, 아니면 NULL (CK). 보존 기간의 기산점 (T-3 A).'),
 ]),
 ],
 idx=['UK 함수 기반 3개: (`STOCK_ID`, `INBOUND_ROUND_NO`), (`FREEBIE_STOCK_ID`, `INBOUND_ROUND_NO`), (`SUPPLY_STOCK_ID`, `INBOUND_ROUND_NO`)를 대상 ID가 NOT NULL일 때만 (Oracle 복합 UK는 일부만 NULL인 행끼리도 중복으로 막기 때문, IC-49 C)',
      'IX `FREEBIE_STOCK_ID`, `SUPPLY_STOCK_ID` (FK)',
      'IX `PURCHASE_ORDER_LINE_ID` (값 참조)',
      'IX (`INBOUND_PLAN_STATUS_CD`, `PLANNED_DT`) (예정일 지난 미입고 감시, 신호 4)'],
 check=['대상 3개(`STOCK_ID`, `FREEBIE_STOCK_ID`, `SUPPLY_STOCK_ID`) 중 정확히 하나만 NOT NULL (IC-49 C)',
        '`STOCK_ID`가 NULL이면 `COMMITTED_QTY`, `INSPECTED_NORMAL_QTY`, `INSPECTED_DEFECTIVE_QTY`가 0 (예약 판매·입고 검수는 판매 상품만, IC-49 C)',
        '`COMMITTED_QTY <= GREATEST(PLANNED_QTY - INSPECTED_NORMAL_QTY - INSPECTED_DEFECTIVE_QTY, 0)` (6-2 A, IC-8 A). 검수 양품이 확보보다 적으면 남는 확보는 5-9 A로 다음 차수에 옮기거나 해제한 뒤 검수 누계를 늘린다',
        '`PLANNED_DT > FIRST_PLANNED_DT`이면 `DELAY_REASON_CD` NOT NULL (T-9 A)',
        '`INSPECTED_NORMAL_QTY + INSPECTED_DEFECTIVE_QTY <= RECEIVED_QTY` (IC-6 A)',
        '완료·취소이면 `CLOSED_AT` NOT NULL, 아니면 NULL. 취소·완료이면 `COMMITTED_QTY = 0` (걸린 확보를 다음 차수로 옮기거나 해제한 뒤, 5-9 A)'])

# =========================================================== 5. 재고 스냅샷
table(t='INV_STOCK_SNAPSHOT', ko='재고 스냅샷 (판매 상품 일별·월말 수량)', en='Stock Snapshot',
 desc='매일 마감 시각에 그날 원장 변화가 있었거나 수량이 바뀐(현재고 `STOCK_QUANTITY_CHANGED_AT`이 그날 0시 이후, 다음 날 포함) 행만, 월말에는 모든 행을 남긴다 (8-1 A, IC-14 A, IC-24 A, IC-78 A). '
      '배치가 마감 시각보다 늦게 돌면 실물 4개는 읽은 값에서 마감 시각 이후 원장(업무 일자가 다음 날인 행)을 빼서 마감 시각 값으로 되돌리고, 예약·할당·안전 재고는 읽은 시점 값을 남기며 읽은 시각을 `CAPTURED_AT`에 둔다 (IC-78 A). 예약·할당·안전 재고만 바뀐 날도 남고, 등급·기준만 바뀐 날은 남지 않는다. 그 달의 사유별 누계 수불을 함께 남겨 월말 행이 10년짜리 월 수불부가 된다 (IC-7 A). 특정 날짜 수량은 그 날 이전의 가장 가까운 스냅샷 + 그 사이 원장(업무 일자)으로 계산하며, 원장이 실물만 담으므로 실물 4개에만 해당한다 (IC-80 A). '
      '늦게 돈 행은 실물(마감 시각)과 예약·할당·안전 재고(`CAPTURED_AT`)의 시점이 달라 이 행에서 판매 가능을 계산하지 않는다. 예: 자정 정상 10·예약 8, 00:05 정상 15·예약 12이면 행에는 정상 10, 예약 12가 남는다 (IC-80 A). '
      '월 마감을 재개하면 그 달 이후 스냅샷의 실물 4개와 월 누계 4개만 원장으로 다시 계산해 고치고, 예약·할당·안전 재고는 당시 값을 둔다. 그 뒤 내부 대사 ①④를 그 달부터 다시 돌린다 (8-2 C, IC-15 A). '
      '그래서 스냅샷에는 판매 가능 CHECK를 두지 않는다(정정한 실물이 당시 예약보다 적을 수 있다). Oracle 스케줄러가 만든다 (선행 11). 사은품·운영자재는 월말 스냅샷 테이블을 따로 둔다 (IC-47 B).',
 basis='8-1 A, 8-2 C, 8-3 A, 8-6 C, T-10 A, T-11 A, IC-7 A, IC-14 A, IC-15 A, IC-24 A, IC-78 A',
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
  ('CAPTURED_AT','읽은 일시','Captured At',TS,'N','SYSTIMESTAMP','',
   '배치가 현재고를 실제로 읽은 시각 (IC-78 A). 예약·할당·안전 재고는 이 시각의 값이다. 예: 마감 0시, 배치 00:05이면 00:05. 실물 4개는 원장으로 마감 시각 값으로 되돌려 이 값과 상관없다.'),
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
      '그 달 1일부터 스냅샷 일자까지 생산 입고·반품 입고·고객 직접 반품 입고·반송 입고·기초 재고 합계 (IC-7 A, IC-84 A, IC-94 A, IC-107 A). 기초 재고는 1차에 입고 대신 쓰는 경로라 입고로 센다. 월말 행에서는 그 달 전체 합계라 10년 보존되는 월 수불부가 된다. 정정 행은 원래 사유에 넣어 순액이다.'),
  qty('MTD_OUTBOUND_QTY','월 누계 출고 수량','Month-to-Date Outbound Quantity','판매·재발송·비주문 출고로 나간 수 (양수로 적음, IC-7 A).'),
  qty('MTD_DISPOSAL_QTY','월 누계 처분 수량','Month-to-Date Disposal Quantity','폐기·업체 반품·일괄 매각으로 나간 수 (양수로 적음, IC-7 A).'),
  ('MTD_ADJUST_QTY','월 누계 조정 수량','Month-to-Date Adjustment Quantity',QTY,'N','0','',
   '실사 조정의 증감 합계 (부호 있음, IC-7 A). 포장재 사용·수선 사용은 운영자재 원장으로 옮겼다 (IC-46 A). 검수·보류·불량 전환·수선 복귀 같은 상태 이동은 실물 합계를 바꾸지 않아(원장 CK, IC-87 A) 넣지 않는다. '
   '내부 대사 ④: 전월말 실물 합계 + 입고 − 출고 − 처분 + 조정 = 당월말 실물 합계.'),
 ]),
 ],
 idx=['UK LOCAL (`STOCK_ID`, `SNAPSHOT_DT`) (파티션 키를 포함해 로컬 인덱스로 둔다)'],
 check=['수량 7개와 월 누계 입고·출고·처분은 각각 >= 0. 월 누계 조정은 부호 있음 (IC-7 A)'])

# =========================================================== 6. 재고 월 마감
table(t='INV_MONTHLY_CLOSING', ko='재고 월 마감', en='Inventory Monthly Closing',
 desc='한 달에 1행 (회사 단위, T-11 A). 판매 상품 수불 원장, 사은품 원장, 운영자재 원장 3개를 함께 막는다 (IC-47 B). 마감한 달에는 원장 업무 일자를 넣을 수 없고, 승인을 받아 재개하면 넣을 수 있다 (8-2 C). 재개하면 그 달 이후 스냅샷(사은품·운영자재 월말 스냅샷 포함)을 다시 계산한다. 회계 마감과 맞추는 일은 정산 넘김 사항이다.',
 basis='8-2 C, T-10 A, T-11 A, IC-47 B',
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
 desc='대사 차이(INV·WMS, 내부 대사 ①~⑤)와 현장 발견, 감시 신호 1건마다 1행 (8-8 B, 8-8 후속 B, T-8 A). 판매 상품, 사은품, 운영자재 현재고 모두 대상이다 (IC-48 A). 배치가 신호마다 행을 만들고 담당자가 처리한다. 자동으로 수량을 고치지 않는다 (1-8 A, 8-3 A). '
      '대사 차이·현장 발견 행은 실사 조정의 요청 역할을 하고, 조정 원장이 이 행을 가리킨다 (7-7 A). 결정 원문의 "대사 차이 테이블"은 이 테이블에 합쳤다. 장부·비교·차이 수량 6개는 현재고 실물 합계(`NUMBER(8)`)를 받으므로 `NUMBER(8)`이다 (IC-70 A). '
      '대사 유형 행은 처음 찾은 대사 실행과 마지막으로 찾은 대사 실행을 가리킨다. 확인 중인 같은 차이를 다음 대사가 다시 찾으면 새 행을 만들지 않고 마지막 실행 ID와 마지막 수량 2개만 고친다 (IC-66 C, IC-68 C).',
 basis='1-8 A, 2-4 A, 2-7 A, 7-7 A, 8-3 A, 8-8 B, 8-8 후속 B, T-1 A, T-2 A, T-8 A, T-10 A, IC-3 A, IC-7 A, IC-11 A~IC-13 A, IC-48 A, IC-49 C, IC-63 B, IC-66 C~IC-68 C, IC-70 A',
 pk='대리 PK `SEQ_INV_STOCK_EXCEPTION`', cache=20,
 delete='삭제하지 않는다 (상태로 처리). 처리 완료 + 1년이 지나고 가리키는 원장이 없는 행을 일 배치가 나눠서 DELETE한다 (T-2 A). 조정으로 이어진 행은 원장(5년)이 지워진 뒤에야 지워진다',
 part='없음 (T-2 A). 원장이 FK로 가리키는 부모라 파티션 제거가 ORA-02266에 걸리고, 하루 수십 건이라 행 단위로 충분하다',
 keep='조정으로 이어진 행: 가리키는 원장과 같이 5년. 나머지: 처리 완료 + 1년 (T-2 A)',
 cols=[
 ('식별', [
  ('STOCK_EXCEPTION_ID','재고 예외 고유 식별 번호','Stock Exception Unique Identifier',ID,'N','','PK',''),
  cd('STOCK_EXCEPTION_TYPE_CD','재고 예외 유형 코드','Stock Exception Type Code',
     desc='대사 6개, 현장 발견, 감시 신호 6개 (T-8 A, IC-3 A, IC-7 A, IC-52 C). 신호 3번(입고 대기 기한 위험)은 배송 출고 요청의 예외 수동 처리로, 신호 8번(반복 확보 실패)은 애플리케이션 로그로 본다. 유형마다 대상 컬럼이 정해져 있다 (`ATTR1`).'),
 ]),
 ('대상', [
  fk('STOCK_ID','대상 판매 상품 현재고 식별 번호','Target Stock on Hand Identifier','INV_STOCK','Y','',
     'INV·WMS 대사, 내부 대사 ①②④⑤, 현장 발견, 검수 대기 적체, 오래된 보류, 재입고 수요, 리오더 기준 도달 (T-1 A, IC-3 A).'),
  fk('FREEBIE_STOCK_ID','대상 사은품 현재고 식별 번호','Target Free Gift Stock Identifier','INV_FREEBIE_STOCK','Y','',
     'INV·WMS 대사, 현장 발견, 리오더 기준 도달 (IC-48 A, IC-49 C).'),
  fk('SUPPLY_STOCK_ID','대상 운영자재 현재고 식별 번호','Target Operating Supply Stock Identifier','INV_SUPPLY_STOCK','Y','',
     'INV·WMS 대사, 현장 발견, 리오더 기준 도달 (IC-48 A, IC-49 C).'),
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
 ('대사 실행', [
  fk('FIRST_RECONCILIATION_RUN_ID','처음 찾은 재고 대사 실행 식별 번호','First Detecting Reconciliation Run Identifier','INV_RECONCILIATION_RUN','Y','',
     '이 차이를 처음 찾은 대사 실행. 대사 유형만 NOT NULL (CK), 만든 뒤 바꾸지 않는다 (IC-66 C).'),
  fk('LAST_RECONCILIATION_RUN_ID','마지막으로 찾은 재고 대사 실행 식별 번호','Last Detecting Reconciliation Run Identifier','INV_RECONCILIATION_RUN','Y','',
     '확인 중인 이 차이를 마지막으로 다시 찾은 대사 실행. 대사 유형만 NOT NULL (CK). 처음에는 처음 찾은 실행과 같고, 다시 찾을 때마다 고친다. '
     '같은 대사의 최근 실행보다 오래됐으면 차이가 사라졌을 수 있다 (예: 11/28 처음, 11/29 마지막, 11/30 대사에서는 차이 없음) (IC-66 C).'),
 ]),
 ('대사 수량', [
  cd('RECONCILIATION_BUCKET_CD','대사 비교 수량 구분 코드','Reconciliation Compared Bucket Code','Y',
     desc='대사 유형만 NOT NULL (CK). INV·WMS 대사는 실물 합계(판매 상품은 `PHYSICAL_TOTAL_QTY`(IC-50 A), 사은품은 정상 + 불량, 운영자재는 정상, 1-8 A, IC-12 A, IC-48 A), 내부 대사 ①은 실물 버킷별, ②는 예약·할당, ③은 입고 예정 확보 (8-3 A), ④는 실물 합계 (IC-7 A), ⑤는 보류 (IC-52 C). '
     '같은 대상의 버킷별 차이는 행이 따로다 (IC-11 A).'),
  ('RECONCILIATION_DT','대사 기준일','Reconciliation Base Date','DATE','Y','','',
   '비교한 재고의 날짜(업무 일자). 대사 유형만 NOT NULL (CK, IC-13 A). 장부 수량은 이 날짜 기준 값이다. 마감 재개 뒤 지난 날짜를 다시 대사하면 기준일과 감지 일시가 다르다(예: 기준일 11/30, 감지 12/1). UK에는 넣지 않는다. 처음 찾은 대사 실행의 기준일과 같은 값으로 넣고 바꾸지 않는다 (같은지는 애플리케이션이 지킴, IC-67 A).'),
  qty('BOOK_QTY','INV 장부 수량','INV Book Quantity','처음 찾았을 때 현재고(또는 입고 예정) 행의 값. 대사 유형만 NOT NULL (CK). 다시 찾아도 바꾸지 않는다 (IC-68 C).',d='',ck='CK (>= 0)',null='Y',t='NUMBER(8)'),
  qty('COMPARED_QTY','비교 수량','Compared Quantity',
      '처음 찾았을 때의 비교 값. INV·WMS 대사는 WMS 선반 합계, 내부 대사는 스냅샷 + 원장 또는 확보 행 합계로 다시 계산한 값. 대사 유형만 NOT NULL (CK). 다시 찾아도 바꾸지 않는다 (IC-68 C).',d='',ck='CK (>= 0)',null='Y',t='NUMBER(8)'),
  ('DIFFERENCE_QTY','차이 수량 (가상 컬럼)','Difference Quantity (Virtual)','NUMBER(8)','Y','','가상 컬럼',
   '`COMPARED_QTY - BOOK_QTY`. 처음 찾았을 때의 차이. 실사 조정 원장은 이 값을 보고 담당자가 실제로 센 차이로 넣는다 (2-6 A, 7-7 A). 대사 유형이 아니면 NULL.'),
  qty('LAST_BOOK_QTY','마지막 INV 장부 수량','Last INV Book Quantity','마지막으로 찾은 대사 실행 때의 장부 수량. 대사 유형만 NOT NULL (CK). 처음에는 `BOOK_QTY`와 같고, 다시 찾을 때마다 고친다 (IC-68 C).',d='',ck='CK (>= 0)',null='Y',t='NUMBER(8)'),
  qty('LAST_COMPARED_QTY','마지막 비교 수량','Last Compared Quantity','마지막으로 찾은 대사 실행 때의 비교 수량. 대사 유형만 NOT NULL (CK). 예: 11/28 처음 INV 10·WMS 9, 11/29 다시 찾아 INV 15·WMS 13이면 이 값은 13 (IC-68 C).',d='',ck='CK (>= 0)',null='Y',t='NUMBER(8)'),
  ('LAST_DIFFERENCE_QTY','마지막 차이 수량 (가상 컬럼)','Last Difference Quantity (Virtual)','NUMBER(8)','Y','','가상 컬럼',
   '`LAST_COMPARED_QTY - LAST_BOOK_QTY`. 위 예에서 −2 (처음 차이는 −1). 대사 유형이 아니면 NULL (IC-68 C).'),
 ]),
 ('처리', [
  ref('HANDLED_ADMIN_ID','처리 관리자 식별 번호','Handling Administrator Identifier',desc='처리 완료·조정 완료·조정 없음이면 NOT NULL (CK). ' + ADM),
  ('HANDLED_AT','처리 일시','Handled At',TS,'Y','','','처리를 마친 시각. 확인 중이 아니면 NOT NULL (CK). 보존 기간의 기산점 (T-2 A).'),
  ('HANDLING_CN','처리 내용','Handling Content','VARCHAR2(2000)','Y','','','확인 결과와 조치. 조정 없음이면 이유를 적는다 (7-7 A).'),
 ]),
 ('동시 갱신', [rowver()]),
 ],
 idx=['IX `STOCK_ID`, `FREEBIE_STOCK_ID`, `SUPPLY_STOCK_ID`, `INBOUND_PLAN_ID`, `FIRST_RECONCILIATION_RUN_ID`, `LAST_RECONCILIATION_RUN_ID` (FK), `STOCK_COMMITMENT_ID` (값 참조)',
      'IX (`STOCK_EXCEPTION_STATUS_CD`, `DETECTED_AT`) (미처리 목록, 신호 5)',
      'UK 함수 기반: 확인 중일 때만 (유형, 대상 ID, 대사 비교 수량 구분) (같은 대상·유형·버킷의 확인 중 행을 하나로, 배치가 매일 다시 찾아도 새로 만들지 않음). 수량 구분이 NULL인 유형은 식 안에서 고정 값으로 바꾼다 (IC-11 A)'],
 check=['대상 5개(`STOCK_ID`, `FREEBIE_STOCK_ID`, `SUPPLY_STOCK_ID`, `STOCK_COMMITMENT_ID`, `INBOUND_PLAN_ID`) 중 유형에 맞는 하나만 NOT NULL (T-1 A, IC-48 A, 선행 6). 유형-대상 조합은 CK로 고정한다',
        '대사 유형이면 `FIRST_RECONCILIATION_RUN_ID`, `LAST_RECONCILIATION_RUN_ID`, `RECONCILIATION_BUCKET_CD`, `RECONCILIATION_DT`, `BOOK_QTY`, `COMPARED_QTY`, `LAST_BOOK_QTY`, `LAST_COMPARED_QTY` NOT NULL, 아니면 모두 NULL (8-8 후속 B, IC-13 A, IC-66 C, IC-68 C)',
        '조정 완료·조정 없음은 대사·현장 발견 유형만, 처리 완료는 감시 신호 유형만 (7-7 A)',
        '확인 중이 아니면 `HANDLED_ADMIN_ID`, `HANDLED_AT` NOT NULL'])

# =========================================================== 7-1. 재고 대사 실행
table(t='INV_RECONCILIATION_RUN', ko='재고 대사 실행 (대사 1회의 결과)', en='Stock Reconciliation Run',
 desc='(대사 유형, 대상 종류) 대사를 한 번 돌릴 때마다 1행 (IC-63 B, IC-64 A). INV·WMS 대사는 판매 상품·사은품·운영자재가 각각 1행이고, 내부 대사는 유형마다 1행이라 매일 밤 7행, 월말에는 ④까지 8행이다. '
      '차이 0건인 실행도 남아 "그날 대사했다"는 증빙이 되고, 비교 건수로 빈 대사(데이터를 받지 못해 0행을 비교함)를 잡는다. 같은 날 다시 돌리면 행이 따로 생긴다. '
      '차이 행은 재고 예외에 남고 처음·마지막으로 찾은 실행 ID로 이 행을 가리킨다 (IC-66 C). 기술적인 실행 성공·실패와 오류 로그는 배치 실행 이력(`BAT`, 선행 11)이 맡는다.',
 basis='1-8 A, 8-3 A, 8-8 후속 B, IC-48 A, IC-63 B~IC-66 C, IC-69 A',
 pk='대리 PK `SEQ_INV_RECONCILIATION_RUN`', cache=20,
 delete='삭제하지 않는다 (실행 기록). 기준일 + 5년이 지나고 가리키는 재고 예외가 없는 행을 일 배치가 나눠서 DELETE한다 (IC-69 A)',
 part='없음 (IC-69 A). 재고 예외가 FK로 가리키는 부모이고, 1년에 약 3,000행이다',
 keep='기준일 + 5년, 가리키는 재고 예외가 있으면 그 행이 지워질 때까지 (IC-69 A, 원장·일 스냅샷과 같은 기간)',
 cols=[
 ('식별', [
  ('RECONCILIATION_RUN_ID','재고 대사 실행 고유 식별 번호','Stock Reconciliation Run Unique Identifier',ID,'N','','PK',''),
  cd('RECONCILIATION_TYPE_CD','대사 유형 코드','Reconciliation Type Code',
     desc='재고 예외 유형 중 대사 6개(INV·WMS 대사, 내부 대사 ①~⑤)만 쓴다 (CK). 값은 `STOCK_EXCEPTION_TYPE_CD`와 같다 (IC-64 A).'),
  cd('RECONCILIATION_TARGET_CD','대사 대상 종류 코드','Reconciliation Target Kind Code',
     desc='판매 상품 현재고, 사은품 현재고, 운영자재 현재고, 입고 예정. 유형-대상 조합은 CK로 고정한다: INV·WMS 대사는 현재고 3종, 내부 대사 ①②④⑤는 판매 상품 현재고, ③은 입고 예정 (IC-64 A).', n=20),
  ('RECONCILIATION_DT','대사 기준일','Reconciliation Base Date','DATE','N','','',
   '비교한 재고의 날짜(업무 일자, IC-13 A와 같은 뜻). 마감 재개 뒤 지난 날짜를 다시 대사하면 실행 일시와 다르다. UK에 넣지 않는다 (같은 날 다시 돌린 실행은 행이 따로).'),
 ]),
 ('실행 상태', [
  cd('RECONCILIATION_RUN_STATUS_CD','대사 실행 상태 코드','Reconciliation Run Status Code',
     desc='실행 중 → 완료 / 실패 (IC-65 B). 끝난 행은 바꾸지 않는다.', n=20),
  ('STARTED_AT','시작 일시','Started At',TS,'N','SYSTIMESTAMP','','대사를 시작한 시각.'),
  ('ENDED_AT','종료 일시','Ended At',TS,'Y','','','완료·실패이면 NOT NULL (CK). 예: 21:00:00 시작, 21:03:10 종료.'),
 ]),
 ('결과 건수', [
  ('COMPARED_CNT','비교 건수','Compared Count','NUMBER(9)','Y','','CK (>= 0)',
   '비교한 대상 행 수. 완료이면 NOT NULL (CK). 0이면 빈 대사로 본다 (예: WMS 선반 데이터를 받지 못함).'),
  ('DIFFERENCE_CNT','차이 건수','Difference Count','NUMBER(9)','Y','','CK (>= 0)',
   '차이가 난 (대상, 수량 구분) 수. 새 예외와 다시 찾은 확인 중 예외를 모두 센다. 완료이면 NOT NULL (CK), 비교 건수 이하.'),
  ('NEW_EXCEPTION_CNT','새 예외 건수','New Exception Count','NUMBER(9)','Y','','CK (>= 0)',
   '차이 중 재고 예외 행을 새로 만든 수. 완료이면 NOT NULL (CK), 차이 건수 이하. 다시 찾은 건수는 차이 건수 − 새 예외 건수다. 예: 차이 3, 새 예외 1이면 2건은 확인 중 예외를 다시 찾은 것 (IC-65 B).'),
 ]),
 ('실패', [
  ('FAILURE_CN','실패 내용','Failure Content','VARCHAR2(2000)','Y','','','실패이면 NOT NULL (CK). 예: "WMS 선반 데이터 수신 없음". 오류 스택은 배치 실행 이력에 둔다.'),
 ]),
 ],
 idx=['IX (`RECONCILIATION_DT`, `RECONCILIATION_TYPE_CD`, `RECONCILIATION_TARGET_CD`) (기준일별 실행 조회, 최근 실행 찾기)'],
 check=['`RECONCILIATION_TYPE_CD`는 대사 6개 값만, 유형-대상 조합 고정',
        '실행 중이면 `ENDED_AT`, 건수 3개, `FAILURE_CN` 모두 NULL',
        '완료이면 `ENDED_AT`, 건수 3개 NOT NULL, `NEW_EXCEPTION_CNT` <= `DIFFERENCE_CNT` <= `COMPARED_CNT`',
        '실패이면 `ENDED_AT`, `FAILURE_CN` NOT NULL (건수는 NULL 허용, 일부만 돌았으면 채울 수 있음)'])

# =========================================================== 8. 사은품 현재고
table(t='INV_FREEBIE_STOCK', ko='사은품 현재고 (창고별 사은품 수량)', en='Free Gift Stock',
 desc='(창고, 사은품)마다 1행 (IC-42 B, IC-43 B). 주문 사은품으로 주는 품목(예: 에코백)을 센다. 판매 상품 현재고와 같이 "지금 값 ± 증감" UPDATE 한 문장으로만 바꾼다 (2-6 A). '
      '주문이 사은품을 잡으면 `정상 − 예약 >= 수량`을 조건으로 예약을 늘리고, 0행이면 주문 사은품 행을 만들지 않고 주문을 진행한다 (5-6 A, IC-45 C). 확보 기록은 주문 사은품 행이 맡는다.',
 basis='1-1 A, 2-6 A, 5-6 A, IC-42 B~IC-45 C, IC-48 A, IC-49 C, IC-62 C',
 pk='대리 PK `SEQ_INV_FREEBIE_STOCK`', cache=20,
 delete='지우지 않는다. 쓰지 않는 사은품도 수량 0 행으로 남긴다 (T-4 A와 같은 재고 수량 행, IC-62 C)',
 part='없음', keep='보존 기간 없음 (지우지 않음)',
 cols=[
 ('식별', [
  ('FREEBIE_STOCK_ID','사은품 현재고 고유 식별 번호','Free Gift Stock Unique Identifier',ID,'N','','PK',
   '사은품 원장·월말 스냅샷·입고 예정·재고 예외가 이 ID를 FK로 가리킨다.'),
  ('WAREHOUSE_ID','창고 식별 번호','Warehouse Identifier',ID,'N','',WH,'창고는 지금 1곳이다.'),
  ('FREEBIE_ITEM_ID','사은품 식별 번호','Free Gift Item Identifier',ID,'N','',FRB,
   '사은품 마스터는 WMS가 갖는다 (상품 M-12 C, IC-40 B). 판매 상품을 사은품으로 주는 일은 없다 (주문 4-4 A).'),
 ]),
 ('증정 가능', [
  ('AVAILABLE_QTY','증정 가능 수량 (가상 컬럼)','Available Quantity (Virtual)',QTY,'N','','가상 컬럼, CK (>= 0)',
   '`GENERATED ALWAYS AS (NORMAL_QTY - RESERVED_QTY) VIRTUAL`. 주문 사은품 확보 조건이다 (IC-45 C). 예: 정상 500, 예약 20이면 480.'),
 ]),
 ('수량', [
  qty('NORMAL_QTY','정상 수량','Normal Quantity','줄 수 있는 실물 (IC-44 B). 예약은 이 안에서 잡는다.'),
  qty('DEFECTIVE_QTY','불량 수량','Defective Quantity','반품으로 돌아온 오염품 등. 폐기·업체 반품 전까지 센다 (IC-44 B).'),
  qty('RESERVED_QTY','예약 수량','Reserved Quantity',
      '주문이 잡았지만 아직 출고하지 않은 수 (IC-45 C). 주문 때 +, 출고 때 정상과 함께 −, 취소·결제 만료 때 −. 진행 중 주문 사은품 행의 수량 합계와 같다 [확인 필요: 주문 사은품 행의 상태(주문 넘김 사항)].'),
 ]),
 ('리오더', [
  ('REORDER_POINT_QTY','리오더 기준 수량','Reorder Point Quantity',QTY,'Y','','CK (>= 0)',
   'NULL이면 감시하지 않는다. 증정 가능 + Σ 입고 기간 안 진행 중 입고 예정의 남은 수량(예정 − 입고, 음수면 0) <= 이 값이면 `LOW_STOCK` 예외 (IC-49 C, IC-20 B). 예: 정상 120, 예약 20, 기준 200이면 경보.'),
 ]),
 ],
 idx=['UK `UK_INV_FREEBIE_STOCK_WAREHOUSE_FREEBIE_ITEM` (`WAREHOUSE_ID`, `FREEBIE_ITEM_ID`)'],
 check=['`AVAILABLE_QTY >= 0` (정상 >= 예약, IC-45 C). 수량 3개는 각각 >= 0'])

# =========================================================== 9. 사은품 원장
table(t='INV_FREEBIE_LEDGER', ko='사은품 원장 (사은품 수량 변화 1건)', en='Free Gift Ledger',
 desc='사은품 현재고의 정상·불량이 바뀐 사건 1건에 1행 (IC-43 B, IC-46 A). 예약 변화는 남기지 않는다(주문 사은품 행이 기록, IC-45 C). 현재고 UPDATE와 같은 트랜잭션에서 넣고, 고치거나 지우지 않는다. '
      '규칙은 판매 상품 수불 원장과 같다: 업무 일자, 같은 사유의 반대 행 정정, 월 마감 (8-2 C, T-6 B, IC-46 A).',
 basis='2-1 A, 2-5 A, 7-7 A, 8-2 C, 8-6 C, T-6 B, IC-43 B, IC-44 B, IC-46 A, IC-48 A, IC-49 C',
 pk='대리 PK `SEQ_INV_FREEBIE_LEDGER`', cache=20,
 delete='삭제하지 않는다 (원장). 정정은 반대 행으로 한다. 5년이 지난 파티션을 제거한다 (IC-46 A)',
 part='업무 일자(`BUSINESS_DT`) 월 INTERVAL 파티션 (IC-46 A, 판매 상품 원장과 같음)',
 keep='업무 일자 + 5년 (IC-46 A) [확인 필요: 국세기본법 85조의3 장부·증빙 5년]',
 cols=[
 ('식별', [
  ('FREEBIE_LEDGER_ID','사은품 원장 고유 식별 번호','Free Gift Ledger Unique Identifier',ID,'N','','PK',''),
  fk('FREEBIE_STOCK_ID','사은품 현재고 식별 번호','Free Gift Stock Identifier','INV_FREEBIE_STOCK','N','','창고와 사은품은 현재고 행에서 읽는다.'),
  cd('FREEBIE_LEDGER_REASON_CD','사은품 수불 사유 코드','Free Gift Ledger Reason Code',
     desc='8개 (IC-46 A). 사유마다 채울 원천 컬럼과 증감 방향을 테이블 수준 CK로 묶는다. 회계 구분은 코드의 `ATTR1`.'),
  ('LEDGER_KEY_VAL','원장 중복 방지 키','Free Gift Ledger Idempotency Key Value','VARCHAR2(100)','N','','UK',
   '사유별 형식: `SHIP:{출고 ID}:{사은품 현재고 ID}` 등 (2-5 A와 같은 방식). 파티션 테이블의 전역 UK.'),
  ('BUSINESS_DT','업무 일자','Business Date','DATE','N','','파티션 키','열린 달(또는 재개한 달)만 넣을 수 있다 (8-2 C, IC-47 B).'),
 ]),
 ('실물 증감', [
  dqty('NORMAL_DELTA_QTY','정상 수량 증감','Normal Quantity Delta','부호 있음. 예: 구매 입고 +1,000, 주문 출고 −1.'),
  dqty('DEFECTIVE_DELTA_QTY','불량 수량 증감','Defective Quantity Delta','반품 입고(불량)·불량 전환은 +, 폐기·업체 반품은 −.'),
 ]),
 ('원천 문서', [
  ref('RECEIPT_ID','원천 WMS 입고 식별 번호','Source WMS Receipt Identifier',desc='구매 입고. WMS 설계 뒤 이름 확정.'),
  ref('SHIPMENT_ID','원천 배송 출고 식별 번호','Source Delivery Shipment Identifier',desc='주문 출고. 배송 출고 트랜잭션에서 넣는다 (1-5 A와 같은 방식).'),
  ref('WAYBILL_ID','원천 회수 운송장 식별 번호','Source Pickup Waybill Identifier',desc='반품 입고(정상·불량). 검수 대기 없이 검수 결과로 바로 넣는다 (IC-44 B).'),
  ref('DISPOSAL_WORK_ID','원천 WMS 처분 작업 식별 번호','Source WMS Disposal Work Identifier',desc='폐기, 업체 반품.'),
  fk('STOCK_EXCEPTION_ID','원천 재고 예외 식별 번호','Source Stock Exception Identifier','INV_STOCK_EXCEPTION','Y','','실사 조정 (7-7 A, IC-48 A).'),
 ]),
 ('근거 입고 예정', [
  fk('INBOUND_PLAN_ID','근거 입고 예정 식별 번호','Basis Inbound Plan Identifier','INV_INBOUND_PLAN','Y','',
     '구매 입고이면 NOT NULL (CK, IC-49 C, T-5 A와 같은 방식) [확인 필요]. 오는 중인 물량을 리오더 판정에서 빼고, 입고 수량을 늘린다.'),
 ]),
 ('정정', [
  ref('REVERSED_FREEBIE_LEDGER_ID','정정 대상 원래 원장 식별 번호','Reversed Original Free Gift Ledger Identifier',
      desc='NOT NULL이면 정정 행이다. 원래 행과 같은 사유, 증감은 반대 (T-6 B와 같은 방식). 한 행은 한 번만 정정한다 (UK).', extra='UK'),
 ]),
 ('세부 사유·승인', [
  cd('ADJUSTMENT_DETAIL_REASON_CD','실사 조정 세부 사유 코드','Stocktake Adjustment Detail Reason Code','Y',desc='사유가 실사 조정이면 NOT NULL (CK, 7-7 A).'),
  cd('DEFECT_REASON_CD','불량 사유 코드','Defect Reason Code','Y',desc='불량 전환이면 NOT NULL (CK, IC-114 A, 판매 상품 원장과 같은 방식).'),
  refn('REQUESTED_ADMIN_ID','조정 요청 관리자 식별 번호','Adjustment Requesting Administrator Identifier',desc='실사 조정이면 NOT NULL (CK, IC-110 A, 판매 상품 원장과 같은 방식). ' + ADM),
  refn('APPROVED_ADMIN_ID','조정 승인 관리자 식별 번호','Adjustment Approving Administrator Identifier',desc='실사 조정의 비교 수량이 적용 승인 기준 수량을 넘으면 필수, 요청 관리자와 같을 수 없다 (7-7 A, IC-110 A, IC-111 A). ' + ADM),
  qty('APPROVAL_THRESHOLD_QTY','적용 승인 기준 수량','Applied Approval Threshold Quantity','실사 조정이면 NOT NULL, 넣는 순간의 정책값 복사 (CK, IC-111 A, 판매 상품 원장과 같은 방식).',d='',null='Y',t='NUMBER(7)'),
  ('REASON_NOTE_CN','사유 설명','Reason Note','VARCHAR2(500)','Y','','','불량 전환과 정정 행이면 NOT NULL (CK, IC-5 A·IC-16 A와 같은 방식).'),
 ]),
 ],
 idx=['IX LOCAL `FREEBIE_STOCK_ID`, `BUSINESS_DT`', 'IX `INBOUND_PLAN_ID`, `STOCK_EXCEPTION_ID` (FK)', 'IX 원천 컬럼 4개 (값 참조)',
      'UK `LEDGER_KEY_VAL`, UK `REVERSED_FREEBIE_LEDGER_ID` (전역 인덱스)'],
 check=['사유별 원천: 원천 컬럼 5개 중 사유에 맞는 하나만 NOT NULL. 불량 전환은 모두 NULL', '사유별 증감 방향 고정. 정정 행은 반대', '증감 2개가 모두 0인 행은 막는다',
        '구매 입고이면 `INBOUND_PLAN_ID` NOT NULL, 아니면 NULL', '`BUSINESS_DT <= TRUNC(CREATED_AT)`',
        '실사 조정이면 `REQUESTED_ADMIN_ID`, `APPROVAL_THRESHOLD_QTY` NOT NULL. 실사 조정이 아니면 이 둘과 `APPROVED_ADMIN_ID` 모두 NULL (IC-118 A). 자기 승인 금지. 비교 수량(정상·불량의 늘어난 합과 줄어든 합 중 큰 값) > 기준이면 `APPROVED_ADMIN_ID` NOT NULL (IC-110 A, IC-111 A)',
        '세부 사유가 분실·파손이면 정상 + 불량 증감 < 0, 초과 발견이면 > 0. 정정 행(`REVERSED_FREEBIE_LEDGER_ID` NOT NULL)은 반대로 본다 (IC-113 A, IC-115 A)', '불량 전환이면 `DEFECT_REASON_CD` NOT NULL, 아니면 NULL (IC-114 A)'])

# =========================================================== 10. 사은품 월말 스냅샷
table(t='INV_FREEBIE_MONTHLY_SNAPSHOT', ko='사은품 월말 스냅샷 (월말 수량과 월 수불)', en='Free Gift Month-End Snapshot',
 desc='월 마감 때 사은품 현재고 행마다 1행 (IC-47 B). 월말 수량과 그 달의 사유별 수불을 남겨, 원장(5년)이 지워진 뒤에도 10년짜리 월 수불부가 된다 (8-6 C와 같은 기준). '
      '월 마감을 재개하면 그 달 이후 행을 원장으로 다시 계산한다 (8-2 C, IC-15 A와 같은 방식).',
 basis='8-2 C, 8-6 C, IC-7 A, IC-15 A, IC-47 B',
 pk='대리 PK `SEQ_INV_FREEBIE_MONTHLY_SNAPSHOT`', cache=20,
 delete='10년이 지난 행을 일 배치가 나눠서 DELETE한다 (행이 적어 파티션 없음)',
 part='없음 (사은품 수 × 12행/년)', keep='10년 (IC-47 B, 8-6 C의 월말 스냅샷과 같음) [확인 필요: 상법 33조 장부 10년]',
 cols=[
 ('식별', [
  ('FREEBIE_MONTHLY_SNAPSHOT_ID','사은품 월말 스냅샷 고유 식별 번호','Free Gift Month-End Snapshot Unique Identifier',ID,'N','','PK',''),
  fk('FREEBIE_STOCK_ID','사은품 현재고 식별 번호','Free Gift Stock Identifier','INV_FREEBIE_STOCK'),
  ('SNAPSHOT_YM','스냅샷 연월','Snapshot Year-Month','VARCHAR2(6)','N','','CK (YYYYMM)','마감한 달. (`FREEBIE_STOCK_ID`, `SNAPSHOT_YM`) UK.'),
 ]),
 ('월말 수량', [
  qty('NORMAL_QTY','정상 수량','Normal Quantity'),
  qty('DEFECTIVE_QTY','불량 수량','Defective Quantity'),
 ]),
 ('월 수불', [
  qty('MONTH_INBOUND_QTY','월 입고 수량','Monthly Inbound Quantity','구매 입고 + 반품 입고 (IC-7 A와 같은 방식).'),
  qty('MONTH_OUTBOUND_QTY','월 출고 수량','Monthly Outbound Quantity','주문 출고 (양수로 적음).'),
  qty('MONTH_DISPOSAL_QTY','월 처분 수량','Monthly Disposal Quantity','폐기 + 업체 반품 (양수로 적음).'),
  ('MONTH_ADJUST_QTY','월 조정 수량','Monthly Adjustment Quantity',QTY,'N','0','','실사 조정 합계 (부호 있음). 전월말 + 입고 − 출고 − 처분 + 조정 = 당월말.'),
 ]),
 ],
 idx=['UK (`FREEBIE_STOCK_ID`, `SNAPSHOT_YM`)'],
 check=['수량과 월 입고·출고·처분은 각각 >= 0. 월 조정은 부호 있음'])

# =========================================================== 11. 운영자재 현재고
table(t='INV_SUPPLY_STOCK', ko='운영자재 현재고 (창고별 포장재·수선 부자재 수량)', en='Operating Supply Stock',
 desc='(창고, 운영자재)마다 1행 (IC-42 B, IC-43 B). 포장재(택배 박스 등)와 수선 부자재(단추, 실)를 센다. 주문이 잡지 않으므로 예약 수량이 없다. '
      '줄어드는 것은 포장재 사용(하루 사용량 일괄)과 수선 사용(수선 건마다), 폐기, 실사 조정이다 (T-7 A, IC-46 A).',
 basis='1-1 A, 2-6 A, T-7 A, IC-22 A, IC-42 B~IC-44 B, IC-46 A, IC-48 A, IC-49 C',
 pk='대리 PK `SEQ_INV_SUPPLY_STOCK`', cache=20,
 delete='지우지 않는다. 쓰지 않는 자재도 수량 0 행으로 남긴다',
 part='없음', keep='보존 기간 없음 (지우지 않음)',
 cols=[
 ('식별', [
  ('SUPPLY_STOCK_ID','운영자재 현재고 고유 식별 번호','Operating Supply Stock Unique Identifier',ID,'N','','PK',
   '운영자재 원장·월말 스냅샷·입고 예정·재고 예외가 이 ID를 FK로 가리킨다.'),
  ('WAREHOUSE_ID','창고 식별 번호','Warehouse Identifier',ID,'N','',WH,'창고는 지금 1곳이다.'),
  ('SUPPLY_ITEM_ID','운영자재 식별 번호','Operating Supply Item Identifier',ID,'N','',SUP,'운영자재 마스터는 WMS가 갖는다 (IC-40 B).'),
 ]),
 ('수량', [
  qty('NORMAL_QTY','정상 수량','Normal Quantity','쓸 수 있는 수 (IC-44 B). 못 쓰는 것은 바로 폐기 원장으로 뺀다. 예: 비에 젖은 박스 50개.'),
 ]),
 ('리오더', [
  ('REORDER_POINT_QTY','리오더 기준 수량','Reorder Point Quantity',QTY,'Y','','CK (>= 0)',
   'NULL이면 감시하지 않는다. 정상 + Σ 입고 기간 안 진행 중 입고 예정의 남은 수량(예정 − 입고) <= 이 값이면 `LOW_STOCK` 예외 (IC-49 C, IC-20 B). 예: 택배 박스(소) 정상 2,000, 기준 3,000이면 경보.'),
 ]),
 ('사용 시각', [
  ('LAST_USED_AT','마지막 사용 일시','Last Used At',TS,'Y','','',
   '포장재 사용·수선 사용 원장과 같은 트랜잭션에서 갱신한다 (IC-22 A의 뜻을 옮김) [확인 필요]. 장기 미사용 자재를 뽑는다. 예: 지난 시즌 전용 박스.'),
 ]),
 ],
 idx=['UK `UK_INV_SUPPLY_STOCK_WAREHOUSE_SUPPLY_ITEM` (`WAREHOUSE_ID`, `SUPPLY_ITEM_ID`)'],
 check=['`NORMAL_QTY >= 0`'])

# =========================================================== 12. 운영자재 원장
table(t='INV_SUPPLY_LEDGER', ko='운영자재 원장 (운영자재 수량 변화 1건)', en='Operating Supply Ledger',
 desc='운영자재 현재고의 정상 수량이 바뀐 사건 1건에 1행 (IC-43 B, IC-46 A). 포장재 사용은 하루 사용량을 일괄로, 수선 사용은 수선 건마다 넣는다 (T-7 A). '
      '규칙은 판매 상품 수불 원장과 같다: 업무 일자, 같은 사유의 반대 행 정정, 월 마감 (8-2 C, T-6 B, IC-46 A).',
 basis='2-1 A, 2-5 A, 3-8 A, 7-7 A, 8-2 C, 8-6 C, T-6 B, T-7 A, IC-43 B, IC-46 A, IC-48 A, IC-49 C',
 pk='대리 PK `SEQ_INV_SUPPLY_LEDGER`', cache=20,
 delete='삭제하지 않는다 (원장). 정정은 반대 행으로 한다. 5년이 지난 파티션을 제거한다 (IC-46 A)',
 part='업무 일자(`BUSINESS_DT`) 월 INTERVAL 파티션 (IC-46 A)',
 keep='업무 일자 + 5년 (IC-46 A) [확인 필요: 국세기본법 85조의3 장부·증빙 5년]',
 cols=[
 ('식별', [
  ('SUPPLY_LEDGER_ID','운영자재 원장 고유 식별 번호','Operating Supply Ledger Unique Identifier',ID,'N','','PK',''),
  fk('SUPPLY_STOCK_ID','운영자재 현재고 식별 번호','Operating Supply Stock Identifier','INV_SUPPLY_STOCK','N','','창고와 자재는 현재고 행에서 읽는다.'),
  cd('SUPPLY_LEDGER_REASON_CD','운영자재 수불 사유 코드','Operating Supply Ledger Reason Code',
     desc='5개 (IC-46 A). 사유마다 채울 원천 컬럼과 증감 방향을 테이블 수준 CK로 묶는다. 회계 구분은 코드의 `ATTR1`.'),
  ('LEDGER_KEY_VAL','원장 중복 방지 키','Operating Supply Ledger Idempotency Key Value','VARCHAR2(100)','N','','UK',
   '사유별 형식: `PACK:{포장재 사용 집계 ID}:{운영자재 현재고 ID}`, `REPAIR:{수선 ID}:{운영자재 현재고 ID}` 등. 파티션 테이블의 전역 UK.'),
  ('BUSINESS_DT','업무 일자','Business Date','DATE','N','','파티션 키','열린 달(또는 재개한 달)만 넣을 수 있다 (8-2 C, IC-47 B).'),
 ]),
 ('실물 증감', [
  dqty('NORMAL_DELTA_QTY','정상 수량 증감','Normal Quantity Delta','부호 있음. 예: 포장재 사용 −380, 수선 사용 −2.'),
 ]),
 ('원천 문서', [
  ref('RECEIPT_ID','원천 WMS 입고 식별 번호','Source WMS Receipt Identifier',desc='구매 입고. WMS 설계 뒤 이름 확정.'),
  ref('PACKAGING_USAGE_ID','원천 WMS 포장재 사용 집계 식별 번호','Source WMS Packaging Usage Summary Identifier',desc='포장재 사용 (T-7 A). WMS 설계 뒤 이름 확정.'),
  ref('CLAIM_REPAIR_ID','원천 클레임 수선 식별 번호','Source Claim Repair Identifier',desc='수선 사용 (3-8 A, T-7 A). 클레임 설계 뒤 이름 확정.'),
  ref('DISPOSAL_WORK_ID','원천 WMS 처분 작업 식별 번호','Source WMS Disposal Work Identifier',desc='폐기.'),
  fk('STOCK_EXCEPTION_ID','원천 재고 예외 식별 번호','Source Stock Exception Identifier','INV_STOCK_EXCEPTION','Y','','실사 조정 (7-7 A, IC-48 A).'),
 ]),
 ('근거 입고 예정', [
  fk('INBOUND_PLAN_ID','근거 입고 예정 식별 번호','Basis Inbound Plan Identifier','INV_INBOUND_PLAN','Y','',
     '구매 입고이면 NOT NULL (CK, IC-49 C, T-5 A와 같은 방식) [확인 필요].'),
 ]),
 ('정정', [
  ref('REVERSED_SUPPLY_LEDGER_ID','정정 대상 원래 원장 식별 번호','Reversed Original Operating Supply Ledger Identifier',
      desc='NOT NULL이면 정정 행이다. 원래 행과 같은 사유, 증감은 반대 (T-6 B와 같은 방식). 한 행은 한 번만 정정한다 (UK).', extra='UK'),
 ]),
 ('세부 사유·승인', [
  cd('ADJUSTMENT_DETAIL_REASON_CD','실사 조정 세부 사유 코드','Stocktake Adjustment Detail Reason Code','Y',desc='사유가 실사 조정이면 NOT NULL (CK, 7-7 A).'),
  refn('REQUESTED_ADMIN_ID','조정 요청 관리자 식별 번호','Adjustment Requesting Administrator Identifier',desc='실사 조정이면 NOT NULL (CK, IC-110 A, 판매 상품 원장과 같은 방식). ' + ADM),
  refn('APPROVED_ADMIN_ID','조정 승인 관리자 식별 번호','Adjustment Approving Administrator Identifier',desc='실사 조정의 비교 수량이 적용 승인 기준 수량을 넘으면 필수, 요청 관리자와 같을 수 없다 (7-7 A, IC-110 A, IC-111 A). ' + ADM),
  qty('APPROVAL_THRESHOLD_QTY','적용 승인 기준 수량','Applied Approval Threshold Quantity','실사 조정이면 NOT NULL, 넣는 순간의 정책값 복사 (CK, IC-111 A, 판매 상품 원장과 같은 방식).',d='',null='Y',t='NUMBER(7)'),
  ('REASON_NOTE_CN','사유 설명','Reason Note','VARCHAR2(500)','Y','','','정정 행이면 NOT NULL (CK, IC-16 A와 같은 방식).'),
 ]),
 ],
 idx=['IX LOCAL `SUPPLY_STOCK_ID`, `BUSINESS_DT`', 'IX `INBOUND_PLAN_ID`, `STOCK_EXCEPTION_ID` (FK)', 'IX 원천 컬럼 4개 (값 참조)',
      'UK `LEDGER_KEY_VAL`, UK `REVERSED_SUPPLY_LEDGER_ID` (전역 인덱스)'],
 check=['사유별 원천: 원천 컬럼 5개 중 사유에 맞는 하나만 NOT NULL', '사유별 증감 방향 고정. 정정 행은 반대', '증감이 0인 행은 막는다',
        '구매 입고이면 `INBOUND_PLAN_ID` NOT NULL, 아니면 NULL', '`BUSINESS_DT <= TRUNC(CREATED_AT)`',
        '실사 조정이면 `REQUESTED_ADMIN_ID`, `APPROVAL_THRESHOLD_QTY` NOT NULL. 실사 조정이 아니면 이 둘과 `APPROVED_ADMIN_ID` 모두 NULL (IC-118 A). 자기 승인 금지. `ABS(NORMAL_DELTA_QTY)` > 기준이면 `APPROVED_ADMIN_ID` NOT NULL (IC-110 A, IC-111 A)',
        '세부 사유가 분실·파손이면 정상 증감 < 0, 초과 발견이면 > 0. 정정 행(`REVERSED_SUPPLY_LEDGER_ID` NOT NULL)은 반대로 본다 (IC-113 A, IC-115 A)'])

# =========================================================== 13. 운영자재 월말 스냅샷
table(t='INV_SUPPLY_MONTHLY_SNAPSHOT', ko='운영자재 월말 스냅샷 (월말 수량과 월 수불)', en='Operating Supply Month-End Snapshot',
 desc='월 마감 때 운영자재 현재고 행마다 1행 (IC-47 B). 월말 수량과 그 달의 사유별 수불을 남겨 10년짜리 월 수불부가 된다. 월 마감을 재개하면 그 달 이후 행을 원장으로 다시 계산한다.',
 basis='8-2 C, 8-6 C, IC-7 A, IC-15 A, IC-47 B',
 pk='대리 PK `SEQ_INV_SUPPLY_MONTHLY_SNAPSHOT`', cache=20,
 delete='10년이 지난 행을 일 배치가 나눠서 DELETE한다 (행이 적어 파티션 없음)',
 part='없음 (자재 수 × 12행/년)', keep='10년 (IC-47 B) [확인 필요: 상법 33조 장부 10년]',
 cols=[
 ('식별', [
  ('SUPPLY_MONTHLY_SNAPSHOT_ID','운영자재 월말 스냅샷 고유 식별 번호','Operating Supply Month-End Snapshot Unique Identifier',ID,'N','','PK',''),
  fk('SUPPLY_STOCK_ID','운영자재 현재고 식별 번호','Operating Supply Stock Identifier','INV_SUPPLY_STOCK'),
  ('SNAPSHOT_YM','스냅샷 연월','Snapshot Year-Month','VARCHAR2(6)','N','','CK (YYYYMM)','마감한 달. (`SUPPLY_STOCK_ID`, `SNAPSHOT_YM`) UK.'),
 ]),
 ('월말 수량', [
  qty('NORMAL_QTY','정상 수량','Normal Quantity'),
 ]),
 ('월 수불', [
  qty('MONTH_INBOUND_QTY','월 입고 수량','Monthly Inbound Quantity','구매 입고.'),
  qty('MONTH_USE_QTY','월 사용 수량','Monthly Use Quantity','포장재 사용 + 수선 사용 (양수로 적음).'),
  qty('MONTH_DISPOSAL_QTY','월 폐기 수량','Monthly Disposal Quantity','양수로 적음.'),
  ('MONTH_ADJUST_QTY','월 조정 수량','Monthly Adjustment Quantity',QTY,'N','0','','실사 조정 합계 (부호 있음). 전월말 + 입고 − 사용 − 폐기 + 조정 = 당월말.'),
 ]),
 ],
 idx=['UK (`SUPPLY_STOCK_ID`, `SNAPSHOT_YM`)'],
 check=['수량과 월 입고·사용·폐기는 각각 >= 0. 월 조정은 부호 있음'])

TABLE_GROUPS = [
 ('수량·원장', ['INV_STOCK', 'INV_STOCK_LEDGER', 'INV_STOCK_HOLD', 'INV_SAFETY_STOCK_HIST']),
 ('확보·입고 예정', ['INV_STOCK_COMMITMENT', 'INV_STOCK_COMMITMENT_EVENT', 'INV_INBOUND_PLAN']),
 ('사은품·운영자재', ['INV_FREEBIE_STOCK', 'INV_FREEBIE_LEDGER', 'INV_FREEBIE_MONTHLY_SNAPSHOT', 'INV_SUPPLY_STOCK', 'INV_SUPPLY_LEDGER', 'INV_SUPPLY_MONTHLY_SNAPSHOT']),
 ('마감·대사', ['INV_STOCK_SNAPSHOT', 'INV_MONTHLY_CLOSING', 'INV_STOCK_EXCEPTION', 'INV_RECONCILIATION_RUN']),
]

def vals(*v): return [(a, b, c, d, i) for i, (a, b, c, d) in enumerate(v, 1)]
CODES = {
 'STOCK_LEDGER_REASON_CD': vals(
   ('PRODUCTION_INBOUND','생산 입고','Production Inbound','입고. 검수 대기 +. 원천 WMS 입고, 근거 입고 예정 필수 (6-3 B, T-5 A). `ATTR1` 해당 없음'),
   ('INBOUND_INSPECTION','입고 검수','Inbound Inspection','입고. 검수 대기 −, 정상 +, 불량 +. 원천 WMS 입고 검수, 근거 입고 예정 필수 (6-3 B, IC-6 A). `ATTR1` 해당 없음'),
   ('RETURN_INBOUND','반품 입고','Return Inbound','입고. 검수 대기 +. 원천 회수 운송장 (7-2 A). `ATTR1` 해당 없음'),
   ('DIRECT_RETURN_INBOUND','고객 직접 반품 입고','Customer-Sent Return Inbound','입고. 검수 대기 +. 고객이 다른 택배로 직접 보낸 반품(배송 운송장 없음, DC-35 B)을 WMS가 미확인 입고로 받아 두었다가 클레임에 연결할 때 넣는다(7-3 A). 원천 WMS 입고. 키는 `DIRECT_RETURN_INBOUND:{연결 요청 키}:{현재고 ID}`(입고 하나를 여러 클레임에 연결할 수 있어서, IC-119 A, IC-122 A). 검수는 반품 검수. `ATTR1` 해당 없음 (IC-107 A)'),
   ('RETURN_INSPECTION','반품 검수','Return Inspection','입고. 검수 대기 −, 정상 +, 불량 +. 원천 클레임 검수 결과 (7-2 A). `ATTR1` 해당 없음'),
   ('RETURNED_INBOUND','반송 입고','Returned Parcel Inbound','입고. 검수 대기 +. 원천 반송 완료(`RETURNED`)된 출고 운송장, 반송 완료 처리와 같은 트랜잭션. 키 `RETURNED_INBOUND:{운송장 ID}:{현재고 ID}` (IC-102 A). 수령 거절·주소 불명 반송은 회수가 아니라 출고의 상태다(배송 세부 2-8). `ATTR1` 해당 없음 (IC-94 A)'),
   ('RETURNED_INSPECTION','반송 검수','Returned Parcel Inspection','입고. 검수 대기 −, 정상 +, 불량 + (실물 합계 증감 0). 원천 WMS 입고 검수. `ATTR1` 해당 없음 (IC-94 A)'),
   ('SALES_SHIPMENT','판매 출고','Sales Shipment','출고. 정상 −. 원천 배송 출고 (1-5 A). `ATTR1` 매출원가'),
   ('RESHIP_SHIPMENT','재발송 출고','Reshipment','출고. 정상 −. 원천 배송 출고. 교환·사고·반송·누락·수선 재발송. `ATTR1` 클레임 귀책에 따름 (7-8 A)'),
   ('NON_ORDER_SHIPMENT','비주문 출고','Non-Order Shipment','출고. 정상 −. 원천 배송 출고. 회계 구분은 배송 `NON_ORDER_TYPE_CD`의 `ATTR` (7-8 A)'),
   ('HOLD_SET','보류 설정','Hold Set','상태 이동. 정상 −, 보류 +. 원천 보류 건(사유는 보류 건에, IC-52 C, IC-55 A). `ATTR1` 해당 없음'),
   ('HOLD_RELEASE','보류 해제','Hold Release','상태 이동. 보류 −, 정상 +. 원천 보류 건, 정상 해제 누계를 함께 고침 (IC-54 A, IC-55 A). `ATTR1` 해당 없음'),
   ('DEFECT_TRANSFER','불량 전환','Defect Transfer','상태 이동. 정상(또는 보류) −, 불량 +. 선반에서 불량을 발견. 보류에서면 원천 보류 건(불량 전환 누계를 함께 고침), 정상에서면 원천 없음 (IC-55 A). `ATTR1` 해당 없음'),
   ('DEFECT_RELEASE','불량 해제','Defect Release','상태 이동. 불량 −, 정상 + (실물 합계 증감 0). 수선 없이 재검수로 불량 판정을 되돌림(예: 조명 탓에 오염으로 오인). 원천 없음, 사유 설명 필수, 행위자는 `CREATED_BY`. 입력 실수는 정정(T-6 B)으로 한다. `ATTR1` 해당 없음 (IC-98 A)'),
   ('REPAIR_RETURN','수선 복귀','Repair Return','상태 이동. 불량 −, 정상 +. 원천 WMS 처분 작업 (7-4 A). `ATTR1` 해당 없음'),
   ('DISPOSAL','폐기','Disposal','처분. 정상·불량 −, 한 작업에 섞이면 한 행 (IC-97 A, IC-104 A, 팔리지 않은 정상품 포함). 원천 WMS 처분 작업. `ATTR1` 폐기손실 [확인 필요: 재고 폐기 손금 증빙]'),
   ('VENDOR_RETURN','업체 반품','Vendor Return','처분. 정상·불량 −, 한 작업에 섞이면 한 행 (IC-97 A, IC-104 A, 과잉 입고분 공장 반품 포함). 원천 WMS 처분 작업. `ATTR1` 해당 없음 (매입 차감은 SCM·회계)'),
   ('BULK_SALE','일괄 매각','Bulk Sale','처분. 정상·불량 −, 한 작업에 섞이면 한 행 (IC-97 A, IC-104 A, C등급 이월 정상품 포함). 원천 WMS 처분 작업. `ATTR1` 매출원가'),
   ('STOCKTAKE_ADJUSTMENT','실사 조정','Stocktake Adjustment','그 밖. 버킷별 ±. 원천 재고 예외, 세부 사유 필수 (7-7 A). `ATTR1` 감모손실'),
   ('OPENING_STOCK','기초 재고','Opening Stock','그 밖. 정상 +, 불량 +(각 0 이상), 검수 대기·보류 0. 원천 8개와 입고 예정 모두 NULL. 시스템 오픈 때 품목마다 1행(IC-79 A), '
    '1차 동안은 원장이 한 건도 없는 현재고 행에 행마다 1회(1차-8 A, 현재고 행을 잠근 뒤 애플리케이션이 검사). 키 `OPENING:{현재고 ID}`. 재고 0인 품목은 원장 없이 현재고만 만들고, '
    '판매 이력이 있으면 적재 경로가 품절 시작 일시를 이전 품절일(없으면 오픈 시각)로 채운다(IC-83 A). 보류할 물건은 정상으로 넣고 2차에 보류 건으로 옮긴다. `ATTR1` 해당 없음 (IC-82 A)'),
   ('TRANSFER_OUT','창고 이동 출고','Warehouse Transfer Out','자리만 남김 (1-7 A). 창고를 늘릴 때 연다. CK 허용 값에서 뺀다'),
   ('TRANSFER_IN','창고 이동 입고','Warehouse Transfer In','자리만 남김 (1-7 A)')),
 'STOCK_COMPOSITION_TYPE_CD': vals(
   ('SINGLE','단품','Single','한 개 (IC-41 A). 셋업 재킷·팬츠도 각자 단품'),
   ('SET','세트','Set','묶어서 생산·입고한 상품. 티셔츠 2팩, 파자마 상하의 세트 (상품 15 D)')),
 'FREEBIE_LEDGER_REASON_CD': vals(
   ('PURCHASE_INBOUND','구매 입고','Purchase Inbound','정상 +. 원천 WMS 입고, 근거 입고 예정 필수 (IC-49 C)'),
   ('ORDER_SHIPMENT','주문 출고','Order Shipment','정상 −. 원천 배송 출고. 예약도 함께 − (IC-45 C). `ATTR1` [확인 필요: 판촉비 등]'),
   ('RETURN_INBOUND_NORMAL','반품 입고 (정상)','Return Inbound (Normal)','정상 +. 원천 회수 운송장 (IC-44 B)'),
   ('RETURN_INBOUND_DEFECTIVE','반품 입고 (불량)','Return Inbound (Defective)','불량 +. 원천 회수 운송장 (IC-44 B)'),
   ('DEFECT_TRANSFER','불량 전환','Defect Transfer','정상 −, 불량 +. 원천 없음, 사유 설명 필수'),
   ('DISPOSAL','폐기','Disposal','불량 −. 원천 WMS 처분 작업'),
   ('VENDOR_RETURN','업체 반품','Vendor Return','불량 −. 원천 WMS 처분 작업'),
   ('STOCKTAKE_ADJUSTMENT','실사 조정','Stocktake Adjustment','정상·불량 ±. 원천 재고 예외 (7-7 A, IC-48 A)')),
 'SUPPLY_LEDGER_REASON_CD': vals(
   ('PURCHASE_INBOUND','구매 입고','Purchase Inbound','정상 +. 원천 WMS 입고, 근거 입고 예정 필수 (IC-49 C)'),
   ('PACKAGING_USE','포장재 사용','Packaging Material Use','정상 −. 하루 사용량 일괄 차감. 원천 WMS 포장재 사용 집계 (T-7 A). `ATTR1` 판관비 (운반비)'),
   ('REPAIR_MATERIAL_USE','수선 사용','Repair Material Use','정상 −. 수선 건마다. 원천 클레임 수선 (3-8 A, T-7 A). `ATTR1` 판관비 (수선비)'),
   ('DISPOSAL','폐기','Disposal','정상 −. 원천 WMS 처분 작업'),
   ('STOCKTAKE_ADJUSTMENT','실사 조정','Stocktake Adjustment','정상 ±. 원천 재고 예외 (7-7 A, IC-48 A)')),
 'HOLD_STATUS_CD': vals(
   ('OPEN','진행','Open','남은 보류 수량이 있다'),
   ('CLOSED','종결','Closed','남은 보류 수량이 0 (IC-54 A)')),
 'SAFETY_STOCK_CHANGE_REASON_CD': vals(
   ('NEW_ROW_DEFAULT','신규 행 기본값','New Row Default','SKU 등록 때 현재고 행을 만들며 등급별(또는 공통) 기본값을 채움 (2-2 A, IC-4 A)'),
   ('GRADE_DEFAULT','등급 기본값 적용','Grade Default Applied','월 등급 배치(행위자 `BATCH`, CK)가 수동 지정 N인 행에 새 등급 기본값을 적용 (IC-19 A)'),
   ('NO_GRADE_DEFAULT','등급 없음 기본값','No-Grade Default Applied','월 등급 배치(행위자 `BATCH`, CK)에서 등급이 NULL(판매 이력 없음)이 된 수동 지정 N인 행에 공통 기본값을 적용. 적용 등급 NULL (IC-77 B)'),
   ('POLICY_DEFAULT_CHANGE','기본값 변경 적용','Policy Default Change Applied','관리자가 공통코드의 등급별(또는 공통) 기본값을 바꾸면, 같은 작업이 그 등급이고 수동 지정 N인 행에 새 값을 적용. 실제로 바뀐 행만 남긴다 (IC-128 A)'),
   ('ADMIN_EDIT','관리자 수정','Administrator Edit','관리자가 값이나 수동 지정 종료일을 직접 고침(종료일만 고쳐도 해당, 원복은 작업 원복, IC-130 A). 수동 지정 Y, 메모·관리자 변경 사유 필수 (IC-136 B). 특정 실물을 빼 두는 품질 확인·촬영 대기는 이 값이 아니라 보류로 (IC-148 A)'),
   ('DEFAULT_RESTORE','기본값 복귀','Default Restored','관리자가 수동 지정을 Y에서 N으로 직접 되돌리고 등급(또는 공통) 기본값을 적용. 관리자만 (CK, IC-134 A). 관리자 변경 사유 필수, 메모는 선택(사유가 기타면 필수, IC-149 A) (IC-146 A)'),
   ('MANUAL_EXPIRED','수동 지정 만료 복귀','Manual Setting Expired','수동 지정 종료일이 지나 일 배치가 Y에서 N으로 되돌리고 기본값을 적용. 행위자 `BATCH`, 작업 키 `MANUAL_END_BATCH:…` (IC-129 B, IC-134 A)'),
   ('OPERATION_REVERT','작업 원복','Operation Reverted','관리자가 지난 관리자 작업 하나를 되돌림(행위자 `ADMIN`, CK, IC-138 B). 원복 대상 작업 키, 메모, 관리자 변경 사유 필수. 그 작업 뒤 변경이 없는 현재고만 (IC-132 A, IC-133 A)')),
 'ADMIN_CHANGE_REASON_CD': vals(
   ('CS_RESERVE_ADJUSTMENT','고객 대응 확보분 조정','Customer Service Reserve Adjustment','교환·재발송·결품 대체에 쓸 확보분을 늘리거나 줄임 (5-1 B가 이 업무에 안전 재고를 쓰게 함). 신상품 출시 초기의 사이즈 교환 대비 상향도 여기다(예: 공통 기본값 2인 새 패딩 L을 6으로, IC-141 B)'),
   ('PROMOTION_PREP','기획전 대비','Promotion Preparation','기획전 대비 상향, 행사 연장·단축에 따른 종료일 변경. 기획전 취소로 되돌리는 것은 운영 계획 철회'),
   ('STAGED_RELEASE','단계 오픈 물량','Staged Release','인기 상품을 나눠 팔 때 다음 오픈분을 묶어 둠. 오픈 시각에 관리자가 직접 내린다(종료일은 날짜뿐이라 시각을 정해 풀 수 없다). 예: 패딩 L 800장 중 300장을 2차 오픈용으로 2 → 302, 12/10 20:00에 2로 (IC-143 A)'),
   ('MARKETING_RESERVE','마케팅 출고 예정분','Marketing Reserve','협찬·화보·임직원 샘플처럼 비주문 출고가 예정된 물량을 출고 요청 전에 미리 남김. 출고 요청을 만들면 바로 할당되므로(4-10 A) 그때 내린다. 예: 다음 주 협찬 30장으로 5 → 35 (IC-142 A)'),
   ('DEMAND_FORECAST_CHANGE','수요 예측 변경','Demand Forecast Change','시즌 전환이나 판매 추세 변화로 조정'),
   ('REPLENISHMENT_DISRUPTION','입고 차질 대비','Replenishment Disruption','생산·입고 날짜가 밀리거나 입고 수량이 줄어 다음 입고까지 임시 상향. 지연인지 부족인지는 생산·입고 기록이 갖는다 (IC-140 B)'),
   ('STOCK_DISCREPANCY_BUFFER','재고 불일치 대비','Stock Discrepancy Buffer','대사 차이나 현장 발견으로 장부 수량이 의심될 때, 재고 예외가 확인 중인 동안 일부를 묶어 초과 판매를 막음. 실사 조정이 끝나면 내린다. 어느 예외인지는 메모에 (IC-144 A)'),
   ('CLEARANCE_RELEASE','정리 판매 해제','Clearance Release','시즌 종료·단종을 앞두고 남은 물량을 일반 판매에 풀려고 하향'),
   ('PLAN_WITHDRAWAL','운영 계획 철회','Plan Withdrawal','올렸던 운영 계획(기획전, 협찬, 단계 오픈 등)이 취소되어 되돌림. 보통 작업 원복이나 기본값 복귀에 쓴다. 예: 12/5 기획전 취소로 12/1 상향을 원복 (IC-145 A)'),
   ('SCOPE_SELECTION_ERROR','적용 대상 선택 오류','Scope Selection Error','일괄 작업의 대상 SKU를 잘못 골라 바로잡음. 예: 겨울 패딩에만 올릴 것을 아우터 500개 전체에 올림. 대상은 맞고 수량·종료일을 잘못 넣었으면 입력 오류 정정 (IC-145 A)'),
   ('MANUAL_ENTRY_CORRECTION','입력 오류 정정','Manual Entry Correction','대상은 맞는데 수량이나 종료일을 잘못 넣은 것을 바로잡음. 예: 5를 50으로 넣은 것을 고침'),
   ('OTHER','기타','Other','위 사유에 맞지 않음(이관 포함, 집계 때 작업 키 `MIGRATION:`으로 뺀다, IC-147 B). 메모에 이유를 적는다(기본값 복귀에서도 필수, CK, IC-149 A)')),
 'HOLD_REASON_CD': vals(
   ('QUALITY_CHECK','품질 확인','Quality Check',''),
   ('PHOTO_SHOOT','촬영 대기','Waiting for Photo Shoot','상품 촬영용으로 빼 둔 실물'),
   ('OTHER','기타','Other','')),
 'ADJUSTMENT_DETAIL_REASON_CD': vals(
   ('LOSS','분실','Loss','도난·분실로 보이는 부족. 실물 합계 감소 (IC-113 A)'),
   ('DAMAGE','파손','Damage','실물이 없어진 파손만(부서져 버린 경우 등). 실물이 남아 있으면 불량 전환 뒤 폐기로 처분해 증빙을 남긴다(7-4 A, IC-113 A). 실물 합계 감소'),
   ('FOUND','초과 발견','Found Surplus','장부보다 실물이 많음(분실 처리한 물건을 다른 선반에서 찾음 등). 실물 합계 증가 (IC-113 A). 회계 처리 [확인 필요: 감모손실 환입인지 잡이익인지]'),
   ('INPUT_ERROR','입력 오류 정정','Input Error Correction','정정 반대 행(T-6 B)으로 잡지 못한 오래된 입력 오류'),
   ('UNKNOWN','원인 불명','Unknown Cause','')),
 'DEFECT_REASON_CD': vals(
   ('STAIN','오염','Stain','얼룩, 변색, 화장품·잉크 묻음'),
   ('DAMAGE','파손·찢어짐','Damage / Tear','찢어짐, 구멍, 올 나감'),
   ('SEWING','봉제 불량','Sewing Defect','박음질 풀림, 비뚤어짐'),
   ('FABRIC','원단 불량','Fabric Defect','원단 결함, 보풀, 이염'),
   ('PRINT','인쇄·자수 불량','Print / Embroidery Defect','프린트 벗겨짐, 자수 빠짐'),
   ('HARDWARE','부자재 불량','Hardware Defect','지퍼, 단추, 스냅 불량·탈락'),
   ('OTHER','기타','Other','사유 설명에 내용을 적는다')),
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
   ('INV_WMS_RECONCILIATION','INV·WMS 대사 차이','INV-WMS Reconciliation Difference','대사. 대상 판매 상품·사은품·운영자재 현재고 (IC-48 A). 매일 INV 실물 합계와 WMS 선반 합계 비교 (1-8 A)'),
   ('INTERNAL_RECON_PHYSICAL','내부 대사 ① 실물','Internal Reconciliation (Physical)','대사. 대상 현재고. 실물 = 전날 스냅샷 + 당일 원장 (8-3 A)'),
   ('INTERNAL_RECON_COMMITMENT','내부 대사 ② 확보','Internal Reconciliation (Commitment)','대사. 대상 현재고. 예약·할당 = 확보 행 남은 수량 합계'),
   ('INTERNAL_RECON_INBOUND_PLAN','내부 대사 ③ 입고 예정','Internal Reconciliation (Inbound Plan)','대사. 대상 입고 예정. 확보 수량 = 걸린 확보 합계'),
   ('INTERNAL_RECON_HOLD','내부 대사 ⑤ 보류','Internal Reconciliation (Hold)','대사. 대상 현재고. 보류 = 진행 중 보류 건의 남은 수량 합계 (IC-52 C)'),
   ('INTERNAL_RECON_MONTHLY','내부 대사 ④ 월 수불','Internal Reconciliation (Monthly Movement)','대사. 대상 현재고. 비교 구분 실물 합계. 전월말 실물 + 월 누계 입고 − 출고 − 처분 + 조정 = 당월말 실물 (월 마감 때, IC-7 A)'),
   ('FIELD_DISCOVERY','현장 발견','Field Discovery','대상 판매 상품·사은품·운영자재 현재고 (IC-48 A). 대사 없이 창고에서 발견한 차이를 직접 등록 (7-7 A)'),
   ('EXPIRED_RESERVATION','만료 지난 예약','Expired Reservation Remaining','신호 1. 대상 확보. 만료 배치 실패'),
   ('INSPECTION_BACKLOG','검수 대기 적체','Inspection Backlog','신호 2. 대상 현재고. 기준 일수보다 오래된 생산·반품(고객 직접 반품 포함)·반송 입고분이 아직 검수 대기 (원장 입고 행의 처리 시각으로 판정, IC-2 B, IC-90 B)'),
   ('OVERDUE_INBOUND_PLAN','예정일 지난 미입고','Overdue Inbound Plan','신호 4. 대상 입고 예정'),
   ('LONG_HOLD','오래된 보류','Long Hold','신호 6. 대상 현재고. 진행 중 보류 건의 해제 예정일이 지났거나, 해제 예정일이 없고 시작 일시 + 기준 일수가 지남 (IC-56 A)'),
   ('RESTOCK_DEMAND','재입고 수요','Restock Demand','신호 7. 대상 현재고. 살 수 있는 수가 0인데 재입고 신청이 기준 수 이상 (생산 판단 참고)'),
   ('LOW_STOCK','리오더 기준 도달','Reorder Point Reached','신호 9. 대상 현재고. 판매 가능 + 입고 기간 안 진행 중 입고 예정의 남은 수량(예정 − 검수 양품 − 검수 불량 − 확보, 음수면 0) <= `REORDER_POINT_QTY`. 사은품은 증정 가능, 운영자재는 정상에 남은 수량(예정 − 입고)을 더한다. 대상 판매 상품·사은품·운영자재 현재고 (IC-3 A, IC-8 A, IC-20 B, IC-49 C)')),
 'STOCK_GRADE_CD': vals(
   ('A','A 등급 (상위 판매)','Grade A (Top Sellers)','지난 3개월 판매 상위. 기준 비율은 `ATTR1`. 등급별 안전 재고·리오더 기준 기본값은 `ATTR2`·`ATTR3`'),
   ('B','B 등급 (중간)','Grade B (Mid Sellers)',''),
   ('C','C 등급 (하위·장기 체류)','Grade C (Slow Movers)','처분 후보·장기 체류 추출 대상 (`LAST_OUTBOUND_AT`과 함께)')),
 'STOCK_EXCEPTION_STATUS_CD': vals(
   ('CHECKING','확인 중','Checking',''),
   ('ADJUSTED','조정 완료','Adjusted','대사·현장 발견. 실사 조정 원장을 넣음 (7-7 A)'),
   ('NO_ADJUSTMENT','조정 없음','No Adjustment','대사·현장 발견. 실사 결과 INV가 맞음'),
   ('RESOLVED','처리 완료','Resolved','감시 신호')),
 'RECONCILIATION_TARGET_CD': vals(
   ('STOCK','판매 상품 현재고','Stock on Hand','INV·WMS 대사, 내부 대사 ①②④⑤'),
   ('FREEBIE_STOCK','사은품 현재고','Free Gift Stock','INV·WMS 대사 (IC-48 A)'),
   ('SUPPLY_STOCK','운영자재 현재고','Operating Supply Stock','INV·WMS 대사 (IC-48 A)'),
   ('INBOUND_PLAN','입고 예정','Inbound Plan','내부 대사 ③')),
 'RECONCILIATION_RUN_STATUS_CD': vals(
   ('RUNNING','실행 중','Running',''),
   ('COMPLETED','완료','Completed','건수 3개를 채움'),
   ('FAILED','실패','Failed','실패 내용을 채움')),
 'RECONCILIATION_BUCKET_CD': vals(
   ('PHYSICAL_TOTAL','실물 합계','Physical Total','INV·WMS 대사, 내부 대사 ④. 판매 상품은 `PHYSICAL_TOTAL_QTY` (IC-12 A, IC-50 A)'),
   ('NORMAL','정상','Normal','내부 대사 ①'),
   ('INSPECTION_PENDING','검수 대기','Inspection Pending','내부 대사 ①'),
   ('DEFECTIVE','불량','Defective','내부 대사 ①'),
   ('HOLD','보류','Hold','내부 대사 ①⑤'),
   ('RESERVED','예약','Reserved','내부 대사 ②'),
   ('ALLOCATED','할당','Allocated','내부 대사 ②'),
   ('INBOUND_PLAN_COMMITTED','입고 예정 확보','Inbound Plan Committed','내부 대사 ③')),
}
# 같은 등급 값을 쓰는 컬럼은 값 행을 다시 펼치지 않고 원래 컬럼을 가리킨다 (결제 PYC-86 A 방식)
CODES['APPLIED_STOCK_GRADE_CD'] = CODES['STOCK_GRADE_CD']
CODES['BEFORE_STOCK_GRADE_CD'] = CODES['STOCK_GRADE_CD']
CODES['RECONCILIATION_TYPE_CD'] = CODES['STOCK_EXCEPTION_TYPE_CD']  # 대사 6개만 CK로 씀
REUSE = {'APPLIED_STOCK_GRADE_CD': 'STOCK_GRADE', 'BEFORE_STOCK_GRADE_CD': 'STOCK_GRADE', 'RECONCILIATION_TYPE_CD': 'STOCK_EXCEPTION_TYPE'}
REUSE_NO_ROWS = {'APPLIED_STOCK_GRADE_CD': ('INV_STOCK', 'STOCK_GRADE_CD'), 'BEFORE_STOCK_GRADE_CD': ('INV_STOCK', 'STOCK_GRADE_CD'), 'RECONCILIATION_TYPE_CD': ('INV_STOCK_EXCEPTION', 'STOCK_EXCEPTION_TYPE_CD')}
SAME_NAME_FOLD = True

# 공통코드에 둘 정책값 (컬럼이 아니라 `CMM_CODE` 값·`ATTR`)
POLICY = [
 ('수불 사유 회계 구분', '`STOCK_LEDGER_REASON_CD`, `FREEBIE_LEDGER_REASON_CD`, `SUPPLY_LEDGER_REASON_CD`의 `ATTR1` (매출원가, 판관비, 감모손실, 폐기손실, 해당 없음, 클레임 귀책에 따름). 비주문 출고는 배송 `NON_ORDER_TYPE_CD`의 `ATTR`', '7-8 A, IC-46 A'),
 ('안전 재고·리오더 기준 기본값', '새 현재고 행의 `SAFETY_STOCK_QTY`, `REORDER_POINT_QTY`. 등급별 값은 `STOCK_GRADE_CD`의 `ATTR2`·`ATTR3`, 등급이 없으면 공통 기본값 (예: 0, NULL). 등급이 바뀌면 수동 지정 여부가 N인 값만 새 기본값으로 바꾼다', '5-1 B, IC-3 A, IC-4 A, IC-19 A'),
 ('리오더 입고 기간', '리오더 판정에 더하는 입고 예정의 범위(오늘 + n일). 판매 상품과 사은품·운영자재 2개 (예: 30일, 7일)', 'IC-20 B, IC-49 C'),
 ('재고 등급 기준', '지난 3개월 판매 순위의 등급 경계 비율 (`STOCK_GRADE_CD`의 `ATTR1`, 예: A 상위 20%, B 다음 30%)', 'IC-4 A'),
 ('남은 수량 표시 임계값', '살 수 있는 수가 이 값 이하일 때만 "n개 남음"을 보여 준다 (예: 5개)', '5-4 A'),
 ('재입고 알림 기준 수량', '살 수 있는 수가 이 값 이상이면 재입고 알림을 보낸다 (예: 3개)', '5-5 B'),
 ('실사 조정 승인 기준 수량', '비교 수량이 이 값을 넘으면 승인 관리자 필수. 원장에 넣을 때 적용 승인 기준 수량으로 복사해 CHECK가 검사한다', '7-7 A, IC-111 A'),
 ('재고 마감 시각', '일 스냅샷과 내부 대사를 도는 시각 (예: 0시)', '8-1 A'),
 ('감시 기준', '검수 대기 적체 일수, 오래된 보류 일수(해제 예정일이 없는 보류 건), 재입고 수요 신청 수 (예외 유형 `ATTR`)', '8-8 B, IC-2 B, IC-56 A'),
 ('예외 유형별 대상', '`STOCK_EXCEPTION_TYPE_CD`의 `ATTR1`에 대상(판매 상품·사은품·운영자재 현재고, 확보, 입고 예정)', 'T-1 A, IC-48 A'),
]

# 확정 칸은 컬럼 검토에서 사용자가 확정한 것만 넣는다. T-10 A의 선택(7개)은 결정 기록에 있다 (2026-11-28 사용자 지시)
# INV_STOCK: 2026-11-28 IC-80 뒤 사용자가 "현재고 테이블 확정 체크 해"로 이름·컬럼 전체를 확정
NAME_CONFIRMED = {'INV_STOCK', 'INV_STOCK_LEDGER', 'INV_SAFETY_STOCK_HIST'}  # 수불 원장: 2026-11-28, 안전 재고 변경 이력: 2026-11-29 사용자 확정 지시
CONFIRMED_GROUPS = set()
CONFIRMED_TABLES = {'INV_STOCK', 'INV_STOCK_LEDGER', 'INV_SAFETY_STOCK_HIST'}
# 확정 테이블에 나중에 더해 아직 확정하지 않은 컬럼과, 인덱스·제약 행을 고르는 표시 문자열 (IC-129 재확인 A)
UNCONFIRMED_COLS = {('INV_STOCK', 'SAFETY_STOCK_MANUAL_END_DT')}
UNCONFIRMED_X = {('INV_STOCK', 'IC-129 B')}
# 차수 (2026-11-28 1차 범위, 진행메모 "1차 범위"). 테이블 차수는 사용자 결정(1차-1~4 A)에서 나온 것이고,
# 1차 테이블 안의 컬럼 차수는 1차-4 A 기준을 적용한 제안이다(컬럼 검토에서 확정). 확정 칸과 따로 표시한다.
PHASE = {'INV_STOCK': '1차', 'INV_STOCK_LEDGER': '1차', 'INV_STOCK_COMMITMENT': '1차', 'INV_STOCK_COMMITMENT_EVENT': '1차',
         'INV_SAFETY_STOCK_HIST': '1차', 'INV_MONTHLY_CLOSING': '1차'}  # 나머지는 2차 (안전 재고 이력·월 마감은 1차-5 A로 더함)
# 1차 테이블에서 부모가 2차 테이블인 FK 컬럼: 컬럼은 1차에 만들고 FK 제약은 부모를 만드는 차수에 ALTER로 건다 (1차-6 A)
PHASE_COL = {('INV_STOCK_LEDGER', 'INBOUND_PLAN_ID'): '1차 생성 (2차 사용, FK 2차)', ('INV_STOCK_LEDGER', 'STOCK_HOLD_ID'): '1차 생성 (2차 사용, FK 2차)',
             ('INV_STOCK_LEDGER', 'STOCK_EXCEPTION_ID'): '1차 생성 (2차 사용, FK 2차)',
             # IC-121 A: 2차 사유만 채우는 컬럼은 1차 DDL에 컬럼·CHECK를 만들고 값은 2차부터 채운다
             ('INV_STOCK_LEDGER', 'WAYBILL_ID'): '1차 생성 (2차 사용)', ('INV_STOCK_LEDGER', 'CLAIM_INSPECTION_ID'): '1차 생성 (2차 사용)',
             ('INV_STOCK_LEDGER', 'RECEIPT_ID'): '1차 생성 (2차 사용)', ('INV_STOCK_LEDGER', 'RECEIPT_INSPECTION_ID'): '1차 생성 (2차 사용)',
             ('INV_STOCK_LEDGER', 'DISPOSAL_WORK_ID'): '1차 생성 (2차 사용)', ('INV_STOCK_LEDGER', 'STOCKTAKE_ID'): '1차 생성 (2차 사용)',
             ('INV_STOCK_LEDGER', 'ADJUSTMENT_DETAIL_REASON_CD'): '1차 생성 (2차 사용)', ('INV_STOCK_LEDGER', 'REQUESTED_ADMIN_ID'): '1차 생성 (2차 사용)',
             ('INV_STOCK_LEDGER', 'APPROVED_ADMIN_ID'): '1차 생성 (2차 사용)', ('INV_STOCK_LEDGER', 'APPROVAL_THRESHOLD_QTY'): '1차 생성 (2차 사용)', ('INV_STOCK_COMMITMENT', 'INBOUND_PLAN_ID'): '1차 (FK 2차)',
             ('INV_STOCK_COMMITMENT_EVENT', 'FROM_INBOUND_PLAN_ID'): '1차 (FK 2차)', ('INV_STOCK_COMMITMENT_EVENT', 'TO_INBOUND_PLAN_ID'): '1차 (FK 2차)'}
# 1차 컬럼 검토 순서 (현재고는 확정)
PHASE_ORDER = ['INV_STOCK_LEDGER', 'INV_MONTHLY_CLOSING', 'INV_STOCK_COMMITMENT', 'INV_STOCK_COMMITMENT_EVENT', 'INV_SAFETY_STOCK_HIST']
# 다시 물을 것(CONFIRM)의 차수. 제목으로 찾는다. 없는 제목은 2차.
# 수불 사유 값별 차수 (IC-96 A): 원천이 1차에 없는 사유(WMS, 클레임, 입고 예정, 보류 건, 재고 예외)는 2차
CODE_PHASE = {('STOCK_LEDGER_REASON_CD', v): '2차' for v in ('PRODUCTION_INBOUND', 'INBOUND_INSPECTION', 'RETURN_INBOUND', 'RETURN_INSPECTION',
              'RETURNED_INBOUND', 'RETURNED_INSPECTION', 'DIRECT_RETURN_INBOUND', 'HOLD_SET', 'HOLD_RELEASE', 'REPAIR_RETURN', 'DISPOSAL', 'VENDOR_RETURN',
              'BULK_SALE', 'STOCKTAKE_ADJUSTMENT')}
CODE_PHASE.update({('STOCK_LEDGER_REASON_CD', 'DEFECT_TRANSFER'): '1차 (보류에서는 2차)', ('STOCK_LEDGER_REASON_CD', 'TRANSFER_OUT'): '자리만',
                   ('STOCK_LEDGER_REASON_CD', 'TRANSFER_IN'): '자리만'})
PHASE_Q = {'다른 도메인 이름': '1차', '보류 건·안전 재고 이력 컬럼': '1차',
           '확보 행 동시 갱신': '1차', '확보 처리 이력 파티션': '1차', '진행 중 확보 UK 범위': '1차', '예약 만료 시각': '1차',
           '수량 타입': '1차', '운영 DB 에디션': '1차'}
# 다른 도메인 문서에서 오는 값. 재고는 외부 업체 값이 없다.
EXTERNAL_SOURCED = set()

CONFIRM = [
 ('다른 도메인 이름', 'WMS(창고, 사은품, 운영자재, 입고, 입고 검수, 처분 작업, 포장재 사용 집계, 실사), 클레임(검수 결과, 수선), SCM(발주 라인), 관리자 ID는 그 도메인 설계 뒤 이름과 FK 여부를 정한다. 창고·사은품·운영자재는 FK 예정 (1-6 A, IC-40 B).', '원천·참조 컬럼'),
 ('보류 건·안전 재고 이력 컬럼', 'IC-52 C~IC-60 A로 더한 2개 테이블의 컬럼은 결정한 구성을 바탕으로 한 제안이다 (보류 수량을 만든 뒤 바꾸지 않음, 담당 관리자, 메모 조건 등). 이름 2개도 후보.', '`INV_STOCK_HOLD`, `INV_SAFETY_STOCK_HIST`'),
 ('대사 실행 컬럼', 'IC-63 B~IC-69 A로 더한 `INV_RECONCILIATION_RUN`의 컬럼과 CHECK는 결정한 구성을 바탕으로 한 제안이다 (대사 유형은 재고 예외 유형 값을 재사용하고 대사 6개만 CK, 대상 종류 코드 4개, 실패 때 건수 NULL 허용). 이름도 후보.', '`INV_RECONCILIATION_RUN`'),
 ('예외 다시 찾기와 행 버전', '배치가 확인 중 예외를 다시 찾아 마지막 실행 ID·수량을 고칠 때도 `ROW_VER`를 1 늘린다는 제안. 그 사이 관리자가 같은 행을 처리하면 관리자 쪽이 다시 읽는다 (IC-66 C, IC-68 C).', '`INV_STOCK_EXCEPTION`'),
 ('기초 재고 사유 (사은품·운영자재)', '판매 상품 원장의 기초 재고는 IC-82 A~IC-84 A로 정했다(`OPENING_STOCK`). 사은품·운영자재 원장에도 같은 사유를 둘지는 각 원장 검토 때 정한다.', '`INV_FREEBIE_LEDGER`, `INV_SUPPLY_LEDGER`'),
 ('보류 건 갱신 순서', '보류 설정·해제는 현재고 행을 먼저 UPDATE하고 보류 건 행을 고친다는 제안(여러 품목 잠금 순서 4-12 A와 맞춤).', '`INV_STOCK_HOLD`'),
 ('확보 행 동시 갱신', '행 버전 없이 상태 조건부 UPDATE(`WHERE 상태 = :읽은 상태`)로 결제 완료와 만료 배치의 경합을 막는다는 제안. 현재고는 2-6 A로 행 버전이 없다.', '`INV_STOCK_COMMITMENT`'),
 ('확보 처리 이력 파티션', 'INTERVAL 참조 파티션(12c부터)으로 확보 파티션과 함께 제거한다는 제안. 전역 UK(처리 키)는 제거 때 `UPDATE GLOBAL INDEXES` (IC-10 B).', '`INV_STOCK_COMMITMENT_EVENT`'),
 ('진행 중 확보 UK 범위', '4-9 A는 주문 상품만 정했다. 출고 요청 상품에도 같은 함수 기반 UK를 둘지.', '`INV_STOCK_COMMITMENT`'),
 ('사은품·운영자재 테이블 컬럼', 'IC-42 B~IC-49 C로 더한 6개 테이블의 컬럼은 모두 제안이다 (판매 상품 테이블과 같은 방식으로 적음). 이름 6개도 후보.', '`INV_FREEBIE_*`, `INV_SUPPLY_*`'),
 ('사은품 확보와 잠금 순서', '주문 트랜잭션에서 판매 상품 현재고 행(ID 오름차순, 4-12 A)을 모두 고친 뒤 사은품 현재고를 고친다는 제안. 사은품은 0행이어도 되돌리지 않는다 (5-6 A).', '`INV_FREEBIE_STOCK`'),
 ('사은품 예약 대사', '사은품 예약 수량 = 진행 중 주문 사은품 행의 수량 합계를 맞춰 볼지(내부 대사 ②와 같은 방식). 주문 사은품 행에 상태가 있어야 한다 (주문 넘김 사항).', '`INV_FREEBIE_STOCK.RESERVED_QTY`'),
 ('구매 입고의 입고 예정', '사은품·운영자재 원장의 구매 입고도 입고 예정을 필수로 가리킨다는 제안 (T-5 A와 같은 방식, IC-49 C). 구매 입고는 검수 단계 없이 바로 정상.', '`INV_FREEBIE_LEDGER`, `INV_SUPPLY_LEDGER`, `INV_INBOUND_PLAN`'),
 ('운영자재 마지막 사용 일시', 'IC-22 A의 "포장재·수선 사용도 마지막 출고 일시에 넣는다"를 운영자재 현재고의 마지막 사용 일시로 옮긴다는 제안.', '`INV_SUPPLY_STOCK.LAST_USED_AT`'),
 ('예약 만료 시각', '만료 시각은 확보 행에 복사하지 않고 주문에서 읽는다는 제안 (신호 1 감시는 주문과 조인).', '`INV_STOCK_COMMITMENT`'),
 ('예정보다 많은 입고', '검수 누계가 예정을 넘으면 확보 상한을 0으로 보는 CK 식 (IC-8 A).', '`INV_INBOUND_PLAN`'),
 ('입고 차수 번호', 'INV 입고 차수와 WMS 입고 차수(로트, 1-4 A)를 같은 번호로 맞출지.', '`INV_INBOUND_PLAN.INBOUND_ROUND_NO`'),
 ('대사 수량의 모양', '대사 비교 수량 구분 코드 + 장부·비교 수량 + 차이(가상) 제안 (8-8 후속 B가 컬럼 검토로 넘김).', '`INV_STOCK_EXCEPTION`'),
 ('월 마감 보존 기간', '월말 스냅샷과 같이 10년 제안.', '`INV_MONTHLY_CLOSING`'),
 ('수량 타입', '수량·증감은 `NUMBER(7)` 제안 (배송은 `NUMBER(5)`). 포장재 하루 사용량(2만 개 이상)을 담는다.', '수량 컬럼 전체'),
 ('운영 DB 에디션', 'XE 데이터 12GB 한도. 원장만 5년이면 넘는다는 추정 (8-6 C) [가정].', '전체'),
]
