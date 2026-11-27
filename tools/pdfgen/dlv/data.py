# 배송 도메인 테이블·컬럼 정의 (제안, 확정 전)
# 근거: 배송 결정 (2026-11-26, 대화로 결정. 전제·축 7개, 테이블 T-1~T-7, 컬럼 DC-1~DC-63)과 `docs/pdf/설계패턴/배송도메인_설계패턴_81.pdf`의 세부 번호.
# 결정 기록은 dlv/col_review.py. 테이블 이름은 모두 후보다.
# 컬럼: (물리명, 한글 논리명, 영문 논리명, 타입, NULL(N=NOT NULL, Y=허용), 기본값, 제약, 설명)
# 테이블의 cols는 [(컬럼 그룹 이름, [컬럼...]), ...] 순서 그대로가 규칙 8 순서다 (8-C A: 그룹도 중요도 순).
ID = 'NUMBER(19,0)'
YN = 'CHAR(1)'
TS = 'TIMESTAMP'
AMT = 'NUMBER(15)'
QTY = 'NUMBER(5)'

def yn(p, ko, en, d, desc):
    return (p, ko, en, YN, 'N', f"'{d}'", 'CK (Y/N)', desc)

def fk(p, ko, en, target, null='N', extra='', desc=''):
    return (p, ko, en, ID, null, '', f'FK → `{target}`' + (', ' + extra if extra else ''), desc)

def ref(p, ko, en, null='Y', desc=''):
    # FK를 걸지 않는 다른 도메인 식별자 (값 참조 + 매일 검증, 5-1 B)
    return (p, ko, en, ID, null, '', 'IX (FK 없음)', desc)

def amt(p, ko, en, desc='', null='N', d='0', ck='CK (>= 0)'):
    return (p, ko, en, AMT, null, d, ck, desc)

def qty(p, ko, en, desc='', d='0', ck='CK (>= 0)'):
    return (p, ko, en, QTY, 'N', d, ck, desc)

def cd(p, ko, en, null='N', desc='', n=20, ck='CK (값 목록)'):
    return (p, ko, en, f'VARCHAR2({n})', null, '', ck, desc)

def rowver():
    return ('ROW_VER','행 버전 (낙관적 잠금)','Row Version (Optimistic Lock)','NUMBER(10)','N','0','CK (>= 0)',
            '갱신할 때마다 1 늘린다. `WHERE ROW_VER = :읽은 값`으로 갱신해 0건이면 다시 읽는다 (세부 5-10).')

T = []
def table(**kw):
    kw.setdefault('idx', []); kw.setdefault('check', []); kw.setdefault('pii', False); kw.setdefault('ldel', False)
    T.append(kw)

VENDOR = 'SYS_EXTERNAL_VENDOR'
CORE_DEL = ('삭제하지 않음 (거래 기록). 보존 기간이 지난 행을 일 배치가 나눠서 DELETE한다 (DC-28 A, 선행 11). '
            '자식(운송장 상품 → 운송장 → 출고, 요청 상품 → 요청) 순서로 지운다')
CORE_PART = '없음 (DC-28 A). 배송 테이블끼리 FK가 있어 파티션 제거가 ORA-02266에 걸리므로 행 단위로 지운다'
CORE_KEEP = ('행: 이 요청이 만든 출고가 모두 지워진 뒤 지운다. 출고 없이 취소된 요청은 취소일 + 5년 '
             '[확인 필요: 출고 없는 요청의 보존 기간]')

# =========================================================== 1. 출고 요청
table(t='DLV_SHIPMENT_REQUEST', ko='출고 요청 (아직 나가지 않은 보낼 것)', en='Shipment Request',
 desc='보내야 할 것 1건. 결제 완료, 클레임 회수·교환 접수, 사고·반송·출고 누락 재발송, 수선 회수·재발송, 비주문 출고(협찬·샘플·보상품) 때 만든다. 주문 1건에 1건이 기본이고, 예약 상품과 서비스 유형이 다른 상품은 따로 만든다 (DC-23 A). '
      '출고와 회수를 출고·회수 구분 코드로 함께 담는다 (2-1 B). 주문·클레임 ID는 FK 없이 값으로 가리킨다 (5-1 B). 개인정보는 없다.',
 basis='1-1 B, 2-1 B, 3-3 C, 5-1 B, T-4 A, DC-1 B~DC-5 A, DC-22 A, DC-23 A, DC-25 A, DC-28 A, DC-29 A~DC-31 A, DC-32 C~DC-37 A, DC-39 B~DC-45 A, DC-49 A~DC-58 A, 주문 1-5 A',
 pk='대리 PK `SEQ_DLV_SHIPMENT_REQUEST`', cache=100,
 delete=CORE_DEL, part=CORE_PART, keep=CORE_KEEP,
 cols=[
 ('식별', [
  ('SHIPMENT_REQUEST_ID','출고 요청 고유 식별 번호','Shipment Request Unique Identifier',ID,'N','','PK',
   '요청에는 업무 번호를 두지 않는다. 창고와 고객센터는 출고 번호, 주문번호, 송장번호로 부른다 (DC-1 B).'),
  cd('SHIP_PICKUP_TYPE_CD','출고·회수 구분 코드','Shipment / Pickup Type Code',
     desc='출고(`SHIP`)는 창고에서 고객에게, 회수(`PICKUP`)는 고객에게서 창고로 (2-1 B). 수령 거절 등의 반송은 회수가 아니라 출고의 상태다 (세부 2-8). '
          '이름은 "배송 방향 코드"(`DIRECTION_CD`, 값 `OUTBOUND` / `RETURN`)에서 바꿨다: 논리명 DC-29 A, 물리명과 값 DC-32 C. 출고·요청 상품처럼 식별 그룹에 둔다 (DC-30 B). 요청 대상(주문·클레임·재발송 근거·비주문)도 DC-44 C로 식별 그룹에 합쳤다.'),
  cd('REQUEST_REASON_CD','출고 요청 원인 코드','Shipment Request Reason Code',n=30,
     desc='출고·회수 구분과 원인 조합은 테이블 수준 CK로 고정한다.'),
  ('SHIPMENT_REQUEST_KEY_VAL','출고 요청 생성 중복 방지 키','Shipment Request Creation Idempotency Key Value','VARCHAR2(100)','N','','UK',
   '요청을 만드는 쪽이 원인 + 원천 ID + 분할 구분으로 만든 값 (예: `ORDER:{주문 ID}:{분할 구분}`, `CLAIM:{클레임 ID}:{구분}`, `ACCIDENT:{사고 ID}`, `NON_ORDER:{발급 값}`). '
   '결제 완료 처리·클레임 접수·사고 재발송이 재시도돼도 같은 요청이 두 번 생기지 않게 한다 (DC-31 A, 주문 3-3 A와 같은 방식). '
   '반송 재발송은 `RETURNED:{운송장 ID}`, 출고 누락 재발송은 `MISSING:{운송장 ID}:{순번}`. 같은 키로 다시 오면 기존 요청을 돌려준다. [확인 필요: 분할 구분 값(기본·예약 상품·서비스 유형)과 키 형식은 애플리케이션 규칙]'),
  ref('ORDER_ID','대상 주문 식별 번호','Target Order Identifier','Y',
      '회수·교환·사고 재발송도 원래 주문을 채운다. 비주문 출고만 NULL이고 다른 원인은 NOT NULL (CK, DC-40 A). 매일 검증 배치가 주문에 없는 값을 찾는다 (5-1 B).'),
  ref('CLAIM_ID','대상 클레임 식별 번호','Target Claim Identifier',
      desc='클레임 테이블 이름은 클레임 설계 뒤 확정. 반품 회수·교환 회수·교환 재발송·수선 회수·수선 재발송이면 NOT NULL, 주문이면 NULL (CK).'),
  fk('SOURCE_WAYBILL_ACCIDENT_ID','재발송 원인 배송 사고 식별 번호','Source Delivery Accident Identifier for Reshipment','DLV_WAYBILL_ACCIDENT','Y','',
     '원인이 사고 재발송이면 NOT NULL, 다른 원인이면 NULL (CK). 배송 안의 FK라 걸 수 있다 (5-1 B).'),
  fk('SOURCE_WAYBILL_ID','재발송 원인 운송장 식별 번호 (반송·출고 누락)','Source Waybill Identifier for Reshipment (Returned / Missing Item)','DLV_WAYBILL','Y','',
     '원인이 반송 재발송·출고 누락 재발송이면 NOT NULL, 다른 원인이면 NULL (CK). 반송 재발송은 반송 완료(`RETURNED`)된 박스, 출고 누락 재발송은 상품이 빠진 박스를 가리킨다 (DC-33 A, DC-37 A, 세부 2-8). '
     '반송과 출고 누락은 택배사 사고가 아니라 사고 행을 만들지 않는다. 반송 재발송 배송비 부담은 주문·클레임이 정한다 (넘김 사항). 출고 누락의 원래 운송장 상품 `PACKED_QTY`는 당시 기록이라 고치지 않는다.'),
  fk('PRECEDING_PICKUP_REQUEST_ID','선행 회수 출고 요청 식별 번호','Preceding Pickup Shipment Request Identifier','DLV_SHIPMENT_REQUEST','Y','',
     '교환 재발송이 기다릴 교환 회수 요청 (자기 참조, DC-34 A). 회수가 창고에 도착한 뒤 출고하면 채우고, 맞교환(회수 전에 먼저 보냄)이면 NULL. '
     '원인이 교환 재발송이 아니면 NULL (CK). 가리킨 행이 같은 클레임의 교환 회수인지는 애플리케이션이 검사한다. 맞교환 여부는 클레임 정책 (세부 2-7). 수선 재발송은 수선 완료 때 만들어 쓰지 않는다 (DC-43 B).'),
  cd('NON_ORDER_TYPE_CD','비주문 출고 유형 코드','Non-Order Shipment Type Code','Y',
     desc='협찬, 임직원 샘플, 보상품, 기타. 원인이 비주문 출고이면 NOT NULL, 다른 원인이면 NULL (CK) (DC-42 A). 유형별 출고 수·비용 집계에 쓴다.'),
  ('NON_ORDER_REASON_DESC','비주문 출고 사유 설명','Non-Order Shipment Reason Description','VARCHAR2(500)','Y','','',
   '어느 캠페인, 누구의 요청으로 보내는지 (예: "12월 겨울 코트 인플루언서 협찬, 마케팅팀 요청"). 매출 없이 재고가 나가는 출고라 정산·재고 감사의 근거가 된다. '
   '원인이 비주문 출고이면 NOT NULL, 다른 원인이면 NULL (CK) (DC-45 A). 집계는 유형 코드로 하고, 받는 사람 개인정보는 적지 않는다.'),
  ref('MEMBER_ID','비주문 출고 받는 회원 식별 번호','Non-Order Shipment Recipient Member Identifier',
      desc='받는 사람이 회원이면 채운다 (인플루언서·임직원 회원, 회원 11). 원인이 비주문 출고가 아니면 NULL (CK). 주문 출고는 주문을 조인해 회원을 찾으므로 두지 않는다 (DC-31 ⑤, DC-42 A).'),
 ]),
 ('상태', [
  cd('SHIPMENT_REQUEST_STATUS_CD','출고 요청 상태 코드','Shipment Request Status Code',n=30,
     desc='창고 작업 단계(피킹·검수·포장)는 "창고 작업 중" 하나로 두고 세부는 WMS가 갖는다 (DC-2 A). 바뀔 때마다 상태 이력에 남긴다 (T-1 C).'),
  ('REQUESTED_AT','출고 요청 일시','Shipment Requested At',TS,'N','SYSTIMESTAMP','',
   '공급 조치 기록 (전자상거래법 15조 1항). 주문 출고이면 주문 상품 `SHIPMENT_REQUESTED_AT`과 같은 값을 같은 트랜잭션에서 쓴다 (주문 1-5 A).'),
  ('STATUS_CHANGED_AT','출고 요청 상태 변경 일시 (마지막)','Shipment Request Status Changed At',TS,'N','SYSTIMESTAMP','',
   '상태가 마지막으로 바뀐 시각. 상태 코드와 같은 UPDATE에서 갱신한다. "창고 작업 중 6시간 이상" 같은 정체 감시를 상태 이력 조인 없이 한다 (DC-49 A, 주문 7-7 A와 같은 방식). 같은 시각이 상태 이력에도 남는다.'),
  ('WAREHOUSE_RELEASED_AT','창고 작업 지시 일시','Warehouse Released At',TS,'Y','','',
   'WMS에 작업 지시를 넘긴 시각 (처음 "창고 작업 중"이 된 때). 출고 마감 시각(정책값) 안에 넘겼는지, 결품이 작업 지시 전인지 후인지를 가린다 (DC-49 A). '
   '구분이 출고이고 상태가 창고 작업 중·일부 출고·출고 완료이면 NOT NULL, 구분이 회수이면 NULL (CK).'),
  ('REQUEST_COMPLETED_AT','출고 요청 완료 일시 (회수면 창고 도착)','Shipment Request Completed At',TS,'Y','','',
   '상태가 출고 완료(회수면 회수 완료 = 마지막 박스 창고 도착)가 된 시각 (분할 출고면 마지막 출고). 적용 기한 `SHIP_DUE_DT`를 지켰는지 이 행 안에서 판정한다. 상태가 출고 완료 또는 회수 완료이면 NOT NULL, 그 밖에는 NULL (CK) (DC-49 A, DC-58 A). '
   '회수에도 쓰므로 `SHIP_COMPLETED_AT`이 아니라 이 이름으로 둔다 (DC-32 C의 `SHIP` / `PICKUP` 구분). 취소로 끝나면 `CANCELED_AT`이 종결 시각이다.'),
  ('DEADLINE_BASE_DT','법정 출고 기한 기산 일자','Legal Shipping Deadline Base Date','DATE','Y','','',
   '대금을 받은 날 (전자상거래법 15조 1항). 원인이 주문이면 NOT NULL, 다른 원인이면 NULL (CK) (DC-3 A). 기한·약속 컬럼은 DC-53 B로 상태 그룹에 합쳤고, 요청을 만들 때 정한 뒤 고치지 않는다(약정 공급일 제외).'),
  ('LEGAL_SHIP_DEADLINE_DT','법정 출고 기한 일자','Legal Shipping Deadline Date','DATE','Y','','',
   '기산일 + 3영업일. 요청을 만들 때 영업일 달력으로 계산해 저장하고, 나중에 공휴일을 등록해도 고치지 않는다 (DC-3 A). 원인이 주문이면 NOT NULL (CK).'),
  ('ORIGINAL_AGREED_SUPPLY_DT','최초 약정 공급 일자','Original Agreed Supply Date','DATE','Y','','',
   '처음 약속한 공급일. 약정 공급 일자와 함께 채우고 이후 고치지 않는다. 약정 공급 일자가 NOT NULL이면 NOT NULL (CK) (DC-56 A). 지연 일수를 배송 행만으로 낸다. 예약 상품은 주문 상품 `INITIAL_PROMISED_SUPPLY_DT`와 같은 값이다.'),
  ('AGREED_SUPPLY_DT','약정 공급 일자','Agreed Supply Date','DATE','Y','','',
   '예약 상품의 출고 예정일, 선물 주문은 수락일 + 3영업일 (전자상거래법 13조 2항 4호). 있으면 법정 기한 대신 적용한다. 예약 상품은 이 날까지 "출고 가능일 대기" 상태다. 바꿀 때는 주문 상품 `CURRENT_PROMISED_SUPPLY_DT`도 같은 트랜잭션에서 고친다.'),
  cd('AGREED_SUPPLY_BASIS_CD','약정 공급 근거 코드','Agreed Supply Basis Code','Y',
     desc='약정일이 법정 기한보다 우선하는 근거 (예약 상품 / 선물 수락 / 기타, 전자상거래법 13조 2항 4호). 약정 공급 일자가 NOT NULL이면 NOT NULL, NULL이면 NULL (CK) (DC-57 A). 예약·선물별 지연율을 배송만으로 센다.'),
  ('INTERNAL_SHIP_TARGET_DT','내부 목표 출고 일자 (회수면 회수 접수 목표)','Internal Shipping Target Date','DATE','Y','','',
   '법정 기한이 없는 요청(교환·사고·반송·출고 누락·수선 재발송, 회수, 비주문 출고)의 회사 목표일. 요청일 + 원인별 N영업일(원인 코드 `ATTR1` 정책값)을 만들 때 계산해 저장하고 고치지 않는다. '
   '원인이 주문이면 NULL, 다른 원인이면 NOT NULL (CK) (DC-54 A). 법정 기한과 컬럼을 나눠 15조 준수 통계에 섞이지 않게 한다.'),
  ('SHIP_DUE_DT','적용 출고 기한 일자 (가상 컬럼)','Applied Shipping Due Date (Virtual)','DATE','Y','','가상 컬럼',
   '`GENERATED ALWAYS AS (NVL(AGREED_SUPPLY_DT, NVL(LEGAL_SHIP_DEADLINE_DT, INTERNAL_SHIP_TARGET_DT))) VIRTUAL`. 기한 임박·초과 감시 인덱스에 쓴다 (DC-3 A, DC-54 A, 세부 5-9). 모든 요청이 값을 갖는다.'),
  cd('DELIVERY_SERVICE_TYPE_CD','배송 서비스 유형 코드','Delivery Service Type Code',
     desc='주문 상품 값을 복사한다 (주문 OC-106 A). 유형이 다른 상품은 요청을 나눈다 (DC-23 A). 약정 조건(주문 마감 시각, 약정 일수, 보상 방식)은 공통코드 `ATTR`에 둔다 (DC-4 A).'),
  ('GUARANTEED_ARRIVAL_DT','약정 도착 일자','Guaranteed Arrival Date','DATE','Y','','',
   '도착 보장이면 NOT NULL, 일반이면 NULL (CK). 건별 약속이라 복사해 둔다 (DC-4 A).'),
  ('GUARANTEE_SHIP_CUTOFF_AT','도착 보장 출고 마감 일시','Guaranteed Arrival Shipping Cutoff At',TS,'Y','','',
   '약정 도착일을 지키려면 이 시각까지 출고해야 하는 시각. 요청을 만들 때 그 당시 정책(`ATTR1` 마감 시각, `ATTR2` 약정 일수)으로 계산해 저장한다. '
   '도착 보장이면 NOT NULL, 일반이면 NULL (CK) (DC-55 A). "도착 보장 위험"은 이 값 < 지금이고 아직 출고 전인 요청이다. 정책이 바뀌어도 지난 건은 그대로다.'),
 ]),
 ('출고 창고', [
  ('WAREHOUSE_ID','출고 창고 식별 번호 (회수면 도착 창고)','Warehouse Identifier (Destination for Return)',ID,'N','','FK 예정 → `WMS_WAREHOUSE` (후보)',
   '지금은 값이 하나다. 창고 선택 규칙은 두지 않는다 (3-3 C). 창고 마스터는 WMS 도메인에서 만들고 그때 FK를 건다 (마스터라 파티션 문제 없음).'),
 ]),
 ('보류·취소', [
  cd('SHIPMENT_HOLD_REASON_CD','출고 보류 사유 코드 (마지막 보류)','Shipment Hold Reason Code (Last Hold)','Y',n=30,
     desc='요청을 만든 뒤 생긴 보류 (T-4 A). 풀어도 지우지 않고, 두 사유가 겹치면 마지막 값만 남는다 (이력에는 둘 다).'),
  ('HELD_AT','출고 보류 일시 (마지막 보류)','Held At (Last Hold)',TS,'Y','','','15조 기한을 넘긴 사유를 증명한다 (T-4 A).'),
  ('HOLD_RELEASED_AT','출고 보류 해제 일시','Hold Released At',TS,'Y','','','NULL이면 보류 중 (보류 일시가 있을 때).'),
  ('CANCELED_AT','출고 요청 취소 일시','Shipment Request Canceled At',TS,'Y','','','상태가 취소이면 NOT NULL (CK).'),
  cd('SHIPMENT_REQUEST_CANCEL_REASON_CD','출고 요청 취소 사유 코드','Shipment Request Cancel Reason Code','Y',n=30,
     desc='상태가 취소이면 NOT NULL (CK).'),
 ]),
 ('공급 곤란·지연 안내', [
  ('SUPPLY_DIFFICULTY_NOTIFIED_AT','공급 곤란 통지 일시','Supply Difficulty Notified At',TS,'Y','','',
   '결품 등으로 공급이 곤란함을 소비자에게 알린 시각 (전자상거래법 15조 2항). 결품 수량은 요청 상품에 둔다.'),
  ('DELAY_NOTICED_AT','출고 지연 안내 일시 (마지막)','Shipping Delay Noticed At (Last)',TS,'Y','','',
   '적용 기한을 넘길 것 같아 고객에게 진행 상황을 알린 시각 (전자상거래법 15조 3항, DC-25 A). 알림 발송 내용은 알림 도메인.'),
 ]),
 ('회수 재접수', [
  ('PICKUP_RETRY_CNT','회수 재접수 횟수','Pickup Retry Count','NUMBER(2)','N','0','CK (>= 0)',
   '회수 실패 뒤 택배사에 다시 접수한 횟수. 재접수마다 새 출고·운송장(새 송장)을 만든다. 정책값 한도를 넘으면 예외 수동 처리로 올린다 (DC-22 A). 구분이 출고이면 0 (CK). 반품·교환 회수 모두에 쓰여 `RETURN_PICKUP_RETRY_CNT`에서 이름을 바꿨다 (DC-36 A).'),
  cd('LAST_PICKUP_FAIL_REASON_CD','마지막 회수 실패 사유 코드','Last Pickup Failure Reason Code','Y',n=30,
     desc='구분이 출고이면 NULL, 상태가 회수 실패이면 NOT NULL (CK) (DC-22 A, DC-58 A). 재접수해 회수 접수 완료로 돌아가도 값은 남긴다.'),
 ]),
 ('예외 수동 처리', [
  cd('REQUEST_MANUAL_CHECK_REASON_CD','출고 요청 예외 수동 처리 사유 코드','Shipment Request Exception Manual Handling Reason Code','Y',n=30,
     desc='자동 흐름으로 끝내지 못해 사람이 봐야 하는 요청 (DC-25 A, 결제 `MANUAL_CHECK_*`와 같은 방식). 다시 대상이 되면 덮어쓰고 이전 처리는 관리자 작업 로그에 남는다. '
          '정렬은 급한 순서의 그룹 순이고 `CMM_CODE`의 `ATTR2`에 그룹(`LEGAL_DEADLINE` 법정 기한, `CUSTOMER_PROMISE` 고객 약속, `EXTERNAL_SYNC` 외부 연동, `OTHER` 기타)을 적는다.'),
  ('MANUAL_CHECK_FLAGGED_AT','예외 수동 처리 대상 표시 일시','Exception Manual Handling Flagged At',TS,'Y','','','사유 코드와 함께 채운다 (CK).'),
  ('MANUAL_CHECK_RESOLVED_AT','예외 수동 처리 완료 일시','Exception Manual Handling Resolved At',TS,'Y','','',
   'NULL이면 미처리 (표시 일시가 있을 때). 처리한 관리자와 내용은 관리자 작업 로그에 남긴다.'),
 ]),
 ('동시 갱신', [rowver()]),
 ],
 idx=['UK `SHIPMENT_REQUEST_KEY_VAL` (생성 중복 방지, DC-31 A)', 'UK (`SHIPMENT_REQUEST_ID`, `REQUEST_REASON_CD`) (요청 상품의 복합 FK 대상, DC-5 A 후속 A)',
      'IX `ORDER_ID`, `CLAIM_ID` (FK 없는 값 참조, 5-1 B), `SOURCE_WAYBILL_ACCIDENT_ID`, `SOURCE_WAYBILL_ID`, `PRECEDING_PICKUP_REQUEST_ID` (FK), `MEMBER_ID` (값 참조)',
      'IX (`SHIPMENT_REQUEST_STATUS_CD`, `SHIP_DUE_DT`) (기한 임박·초과 감시, 세부 5-9)',
      'IX (`SHIPMENT_REQUEST_STATUS_CD`, `STATUS_CHANGED_AT`) (상태 정체 감시, DC-49 A)',
      'IX `IX_DLV_SHIPMENT_REQUEST_MANUAL_CHECK_OPEN` (함수 기반: `CASE WHEN MANUAL_CHECK_FLAGGED_AT IS NOT NULL AND MANUAL_CHECK_RESOLVED_AT IS NULL THEN MANUAL_CHECK_FLAGGED_AT END`, 예외 처리함)'],
 check=['출고·회수 구분과 원인 조합: 출고 = 주문, 교환 재발송, 사고 재발송, 반송 재발송, 출고 누락 재발송, 수선 재발송, 비주문 출고 / 회수 = 반품 회수, 교환 회수, 수선 회수',
        '`CLAIM_ID`: 원인이 반품 회수·교환 회수·교환 재발송·수선 회수·수선 재발송이면 NOT NULL, 주문이면 NULL, 사고 재발송·반송 재발송·출고 누락 재발송이면 제약 없음 (NULL이면 통과). 비주문 출고이면 유형이 보상품일 때 NOT NULL, 다른 유형이면 NULL',
        '`ORDER_ID`: 원인이 비주문 출고이면 NULL, 다른 원인이면 NOT NULL (DC-40 A)',
        '`NON_ORDER_TYPE_CD`, `NON_ORDER_REASON_DESC`: 원인이 비주문 출고이면 NOT NULL, 다른 원인이면 NULL (DC-45 A). `MEMBER_ID`: 원인이 비주문 출고가 아니면 NULL (비주문이면 NULL이어도 통과) (DC-42 A)',
        '`SOURCE_WAYBILL_ACCIDENT_ID`: 원인이 사고 재발송이면 NOT NULL, 다른 원인이면 NULL',
        '`SOURCE_WAYBILL_ID`: 원인이 반송 재발송·출고 누락 재발송이면 NOT NULL, 다른 원인이면 NULL (DC-33 A, DC-37 A)',
        '`PRECEDING_PICKUP_REQUEST_ID`: 원인이 교환 재발송이 아니면 NULL (교환 재발송이면 NULL이어도 통과 = 맞교환). 상태가 회수 도착 대기이면 NOT NULL (DC-34 A). 선행 회수 요청이 회수 완료가 되면 대기를 푼다 (DC-58 A)',
        '`DEADLINE_BASE_DT`, `LEGAL_SHIP_DEADLINE_DT`: 원인이 주문이면 둘 다 NOT NULL, 구분이 회수이거나 원인이 비주문 출고이면 둘 다 NULL. 둘 다 있으면 기한 >= 기산일',
        '`GUARANTEED_ARRIVAL_DT`, `GUARANTEE_SHIP_CUTOFF_AT`: 서비스 유형이 도착 보장이면 둘 다 NOT NULL, 일반이면 둘 다 NULL (DC-4 A, DC-55 A)',
        '`INTERNAL_SHIP_TARGET_DT`: 원인이 주문이면 NULL, 다른 원인이면 NOT NULL (DC-54 A)',
        '`ORIGINAL_AGREED_SUPPLY_DT`, `AGREED_SUPPLY_BASIS_CD`: `AGREED_SUPPLY_DT`가 NOT NULL이면 둘 다 NOT NULL, NULL이면 둘 다 NULL (DC-56 A, DC-57 A)',
        '`HOLD_RELEASED_AT`이 NOT NULL이면 `HELD_AT` NOT NULL이고 해제 >= 보류. `HELD_AT`이 NULL이면 `SHIPMENT_HOLD_REASON_CD`도 NULL',
        '상태가 취소이면 `CANCELED_AT`, 취소 사유 NOT NULL. 다른 상태이면 둘 다 NULL',
        '`REQUEST_COMPLETED_AT`: 상태가 출고 완료 또는 회수 완료이면 NOT NULL이고 >= `REQUESTED_AT`, 다른 상태이면 NULL (DC-49 A, DC-58 A)',
        '`WAREHOUSE_RELEASED_AT`: 구분이 출고이고 상태가 창고 작업 중·일부 출고·출고 완료이면 NOT NULL, 구분이 회수이면 NULL (다른 출고 상태는 NULL이어도 통과) (DC-49 A)',
        '구분별 허용 상태: 출고(`SHIP`)는 출고 가능일 대기·회수 도착 대기·재고 입고 대기·출고 대기·창고 작업 중·일부 출고·출고 완료·취소, 회수(`PICKUP`)는 회수 접수 대기·회수 접수 완료·회수 실패·회수 완료·취소 (DC-51 A, DC-52 B, DC-58 A)',
        '상태가 출고 가능일 대기이면 `AGREED_SUPPLY_DT` NOT NULL (DC-51 A)',
        '구분이 출고(`SHIP`)이면 `PICKUP_RETRY_CNT` = 0이고 `LAST_PICKUP_FAIL_REASON_CD` NULL. 상태가 회수 실패이면 `LAST_PICKUP_FAIL_REASON_CD` NOT NULL (DC-58 A)',
        '예외 수동 처리: 사유와 표시 일시는 둘 다 NULL이거나 둘 다 NOT NULL. 완료 일시가 NOT NULL이면 표시 일시 NOT NULL이고 완료 >= 표시'])

# =========================================================== 2. 출고 요청 상품
table(t='DLV_SHIPMENT_REQUEST_ITEM', ko='출고 요청 상품 (요청 안의 대상과 수량)', en='Shipment Request Item',
 desc='출고 요청 1건 안의 대상 1개. 주문 상품, 주문 사은품, 클레임 상품 중 하나를 가리키고, 실물은 SKU나 비판매 품목 중 하나다 (DC-5 A). 주문 1-5 A의 "주문 상품 단위"는 이 행으로 지켜진다.',
 basis='1-1 B, DC-5 A, DC-15 A, DC-23 A, 주문 1-5 A, 주문 4-4 A, 상품 M-12 C, DC-46 A~DC-48 B',
 pk='대리 PK `SEQ_DLV_SHIPMENT_REQUEST_ITEM`', cache=100,
 delete=CORE_DEL, part=CORE_PART, keep='행: 부모 출고 요청과 함께 지운다',
 cols=[
 ('식별', [
  ('SHIPMENT_REQUEST_ITEM_ID','출고 요청 상품 고유 식별 번호','Shipment Request Item Unique Identifier',ID,'N','','PK',''),
  fk('SHIPMENT_REQUEST_ID','출고 요청 식별 번호','Shipment Request Identifier','DLV_SHIPMENT_REQUEST'),
  cd('REQUEST_REASON_CD','출고 요청 원인 코드 (부모에서 복사)','Shipment Request Reason Code (Copied from Parent)',n=30,ck='CK (값 목록), 복합 FK',
     desc='원인별 대상 조합을 이 행의 CK로 막으려고 복사한다 (DC-5 A 후속 A, 2026-11-27). 복합 FK (`SHIPMENT_REQUEST_ID`, `REQUEST_REASON_CD`) → 부모 UK (`SHIPMENT_REQUEST_ID`, `REQUEST_REASON_CD`)로 부모 값과 다를 수 없다. 원인은 바꾸지 않는다.'),
 ]),
 ('대상', [
  ref('ORDER_ITEM_ID','대상 주문 상품 식별 번호','Target Order Item Identifier',desc='원인이 주문인 판매 상품.'),
  ref('ORDER_FREEBIE_ID','대상 주문 사은품 식별 번호','Target Order Freebie Identifier',desc='원인이 주문인 사은품 (주문 4-4 A). 실물은 비판매 품목.'),
  ref('CLAIM_ITEM_ID','대상 클레임 상품 식별 번호','Target Claim Item Identifier',
      desc='반품·교환·수선 회수, 교환·수선 재발송. 원래 주문 상품은 클레임이 가리킨다. 반품 때 돌려받는 사은품도 클레임이 사은품 반환 행을 클레임 상품으로 만들어 이 컬럼으로 가리킨다 (DC-46 A). 컬럼 이름은 클레임 설계 뒤 확정 [확인 필요: 클레임 상품 테이블 이름].'),
  ('TARGET_TYPE_CD','대상 구분 코드 (가상 컬럼)','Target Type Code (Virtual)','VARCHAR2(20)','Y','','가상 컬럼',
   "`GENERATED ALWAYS AS (CASE WHEN ORDER_ITEM_ID IS NOT NULL THEN 'ORDER_ITEM' WHEN ORDER_FREEBIE_ID IS NOT NULL THEN 'ORDER_FREEBIE' "
   "WHEN CLAIM_ITEM_ID IS NOT NULL THEN 'CLAIM_ITEM' ELSE 'NONE' END) VIRTUAL`. 원인별 대상 CK를 원인 × 대상 구분으로 쓰고, 창고 화면 필터에 쓴다 (DC-48 B)."),
  ('ORIGINAL_WAYBILL_ID','원래 운송장 식별 번호 (재발송 대상이 들어 있던 박스)','Original Waybill Identifier',ID,'Y','','FK → `DLV_WAYBILL_ITEM` (복합 1)',
   '사고·반송·출고 누락 재발송이면 NOT NULL, 다른 원인이면 NULL (CK). 원래 요청 상품과 함께 복합 FK로 운송장 상품 PK를 가리켜, 그 상품이 그 박스에 실제로 담겨 있었음을 DB가 보장한다 (DC-47 B). '
   '부모 요청의 `SOURCE_WAYBILL_ID`(반송·출고 누락)나 사고의 운송장과 같은 값인지는 애플리케이션이 검사한다.'),
  ('ORIGINAL_SHIPMENT_REQUEST_ITEM_ID','원래 출고 요청 상품 식별 번호','Original Shipment Request Item Identifier',ID,'Y','','복합 FK 2 → `DLV_WAYBILL_ITEM`',
   '재발송하는 원래 상품 행. 원래 행과 같은 대상인지, 같은 원래 행의 재발송 요청 수량 합계가 원래 담긴 수량을 넘지 않는지는 애플리케이션이 검사한다 (DC-47 B). 창고 오류율을 상품 행 단위로 센다.'),
 ]),
 ('실물', [
  fk('SKU_ID','실물 SKU 식별 번호','Physical SKU Identifier','PRD_SKU','Y','','판매 상품. 실물 둘 중 정확히 하나 (CK). 상품 마스터라 FK를 건다.'),
  ('NON_SALE_ITEM_ID','실물 비판매 품목 식별 번호','Physical Non-Sale Item Identifier',ID,'Y','','FK 예정 → `WMS_NON_SALE_ITEM` (후보)',
   '사은품 등 (상품 M-12 C). 품목 마스터는 WMS 도메인에서 만들고 그때 FK를 건다.'),
 ]),
 ('수량', [
  qty('REQUEST_QTY','요청 수량','Requested Quantity',d='',ck='CK (>= 1)'),
  qty('SHIPPED_QTY','출고 수량 (회수면 회수 접수 수량)','Shipped Quantity (Return: Pickup Booked)',
      '운송장 상품 `PACKED_QTY` 합계의 캐시. 운송장 상품을 쓰는 트랜잭션에서 함께 갱신한다. 송장이 취소된 운송장의 수량은 뺀다.'),
  qty('OUT_OF_STOCK_QTY','결품 수량','Out-of-Stock Quantity','공급 곤란 통지 대상 (전자상거래법 15조 2항).'),
  qty('CANCELED_QTY','취소 수량','Canceled Quantity','출고 전 취소된 수량.'),
 ]),
 ],
 idx=['FK `FK_DLV_SHIPMENT_REQUEST_ITEM_REQUEST_REASON` (`SHIPMENT_REQUEST_ID`, `REQUEST_REASON_CD`) → `DLV_SHIPMENT_REQUEST` UK (부모 값과 같게 보장, DC-5 A 후속 A)',
      'FK `FK_DLV_SHIPMENT_REQUEST_ITEM_ORIGINAL` (`ORIGINAL_WAYBILL_ID`, `ORIGINAL_SHIPMENT_REQUEST_ITEM_ID`) → `DLV_WAYBILL_ITEM` PK (DC-47 B)', 'IX `SHIPMENT_REQUEST_ID` (FK), `SKU_ID` (FK), `ORDER_ITEM_ID`, `ORDER_FREEBIE_ID`, `CLAIM_ITEM_ID` (값 참조), (`ORIGINAL_WAYBILL_ID`, `ORIGINAL_SHIPMENT_REQUEST_ITEM_ID`) (FK)'],
 check=['대상 3개(`ORDER_ITEM_ID`, `ORDER_FREEBIE_ID`, `CLAIM_ITEM_ID`): 원인이 비주문 출고이면 셋 다 NULL, 다른 원인이면 정확히 하나만 NOT NULL (선행 6, DC-40 A)',
        '실물 2개(`SKU_ID`, `NON_SALE_ITEM_ID`) 중 정확히 하나만 NOT NULL. `ORDER_FREEBIE_ID`가 NOT NULL이면 `NON_SALE_ITEM_ID` NOT NULL',
        '`SHIPPED_QTY + OUT_OF_STOCK_QTY + CANCELED_QTY <= REQUEST_QTY`',
        '원인 × 대상 구분 `TARGET_TYPE_CD` (DC-5 A 후속 A, DC-48 B): 주문·출고 누락 재발송 = `ORDER_ITEM`·`ORDER_FREEBIE` / 반품·교환·수선 회수, 교환·수선 재발송 = `CLAIM_ITEM` / 비주문 출고 = `NONE` / 사고·반송 재발송 = `NONE`이 아님 (원래 행과 같은 구분인지는 애플리케이션이 `ORIGINAL_SHIPMENT_REQUEST_ITEM_ID`로 검사)',
        '`ORIGINAL_WAYBILL_ID`, `ORIGINAL_SHIPMENT_REQUEST_ITEM_ID`: 둘 다 NULL이거나 둘 다 NOT NULL. 원인이 사고·반송·출고 누락 재발송이면 NOT NULL, 다른 원인이면 NULL (DC-47 B)'])

# =========================================================== 3. 출고
table(t='DLV_SHIPMENT', ko='출고 (실제로 나간 단위, 공급 기록)', en='Shipment',
 desc='창고에서 실제로 나간(회수면 택배사에 접수한) 단위 1건. 보낸 곳(받는 사람, 주소)과 일시를 한 번만 둔다 (1-1 B). 요청 1건이 출고 N건으로 나뉘거나(분할), '
      '수령인·주소·출고·회수 구분·서비스 유형이 같은 요청 N건이 출고 1건으로 합쳐질 수 있다(합포장, DC-24 B). 요청과의 관계는 운송장 상품 → 요청 상품으로 이어지므로 요청 ID를 직접 두지 않는다.',
 basis='1-1 B, 2-1 B, DC-1 B, DC-6 A, DC-7 A, DC-24 B, DC-27 B, DC-28 A, DC-32 C, DC-41 A, 주문 OC-107 A, 전자상거래법 시행령 6조',
 pk='대리 PK `SEQ_DLV_SHIPMENT`', cache=100,
 delete=CORE_DEL, part=CORE_PART, pii=True,
 keep=('개인정보: 주문(회수·교환이면 원래 주문)의 보유 사유·기산일·파기 예정일을 복사해 주문과 같은 날 NULL로 바꾼다. 주문 파기 예정일이 바뀌면 같은 트랜잭션에서 고친다. '
       '합포장 출고는 묶인 주문 중 가장 늦은 날을 복사한다. 배송 요청 사항은 주문 규칙(5-8 B)처럼 먼저 지운다 (DC-27 B). 비주문 출고는 배송 완료(반송이면 반송 완료) 일자 + 1년을 파기 예정일로 둔다. 주문 출고와 합포장되면 가장 늦은 날 (DC-40 A, DC-41 A). 행: 파기 예정일이 지난 뒤 개인정보를 지우고 같은 배치에서 행을 지운다 (DC-28 A)'),
 cols=[
 ('식별', [
  ('SHIPMENT_ID','출고 고유 식별 번호','Shipment Unique Identifier',ID,'N','','PK',''),
  ('SHIPMENT_NO','출고 번호 (창고 작업 업무 키)','Shipment Number (Warehouse Business Key)','VARCHAR2(20)','N','','UK, CK (형식)',
   '창고 작업 지시서와 출고 확인에 쓰는 유일한 배송 업무 번호 (DC-1 B). 재사용 금지. 형식 제안: 출고일 8자리 + `-` + 6자리 순번 (예: `20261126-000123`) [확인 필요: 형식].'),
  cd('SHIP_PICKUP_TYPE_CD','출고·회수 구분 코드','Shipment / Pickup Type Code',
     desc='묶인 요청과 같다. 합포장은 같은 구분(출고 / 회수)끼리만 (DC-24 B).'),
 ]),
 ('상태·일시', [
  cd('SHIPMENT_STATUS_CD','출고 상태 코드 (운송장 상태 요약)','Shipment Status Code (Waybill Status Summary)',n=30,
     desc='운송장 상태로부터 정한다. 바뀔 때마다 상태 이력에 남긴다 (T-1 C). 출고·회수 구분별로 쓸 수 있는 값을 CK로 막는다.'),
  ('SHIPPED_AT','출고 일시 (창고 출발)','Shipped At (Left Warehouse)',TS,'Y','','',
   '구분이 출고이면 NOT NULL (CK). 주문 상품 `SHIPPED_AT`을 같은 트랜잭션에서 갱신한다 (주문 1-7 A).'),
  ('PICKUP_REQUESTED_AT','회수 접수 일시','Return Pickup Requested At',TS,'Y','','','구분이 회수이면 NOT NULL, 구분이 출고이면 NULL (CK).'),
  ('DELIVERED_AT','배송 완료 일시 (마지막 운송장)','Delivered At (Last Waybill)',TS,'Y','','',
   '출고의 모든 유효 운송장이 완료된 때. 주문 반영 기준이다 (세부 4-8). 구분이 회수이면 창고에 도착한 때이고, 반환받은 날은 회수 운송장의 `DELIVERED_AT`이다 (DC-21 A).'),
 ]),
 ('고객 쪽 주소', [
  ('RECIPIENT_NM','수령인 이름 (회수면 보내는 사람)','Recipient Name (Return: Sender)','VARCHAR2(150)','Y','','',
   '평문 + TDE (회원 C-72). 주문(또는 클레임)에서 출고할 때 복사한 실제 보낸 곳이다 (DC-6 A). 필수 여부는 애플리케이션이 검증한다 (파기 대상, 선행 7).'),
  ('RECIPIENT_MOBILE_PHONE_NUMBER_ENC','수령인 휴대폰 번호 암호문','Recipient Mobile Phone Number Ciphertext','RAW(49)','Y','','',
   'AES-256-GCM (선행 5). 검색용 해시는 주문에 있어 두지 않는다 (DC-6 A).'),
  ('POSTAL_CODE_VAL','배송지 우편번호','Delivery Postal Code','VARCHAR2(5)','Y','','CK (숫자 5자리)','NULL이면 통과 (파기 뒤).'),
  ('ROAD_ADDR','배송지 도로명 주소','Delivery Road Name Address','VARCHAR2(300)','Y','','','평문 + TDE (회원 C-72).'),
  ('LOT_NUMBER_ADDR','배송지 지번 주소','Delivery Lot Number Address','VARCHAR2(300)','Y','','',''),
  ('DETAIL_ADDRESS_ENC','배송지 상세 주소 암호문','Delivery Detail Address Ciphertext','RAW(229)','Y','','','평문 최대 200바이트.'),
  cd('DELIVERY_PLACE_CD','수령 장소 코드','Delivery Place Code','Y',desc='회원 코드 그룹을 함께 쓴다 (주문 5-6 A).'),
  ('DELIVERY_REQUEST_ENC','배송 요청 사항 암호문','Delivery Request Note Ciphertext','RAW(329)','Y','','',
   '평문 최대 300바이트. 주문 규칙(5-8 B)과 같은 시점(주문 상품이 모두 구매 확정되고 회수가 없을 때)에 NULL로 바꾼다 (DC-27 B). '
   '공동현관 출입 방법은 두지 않고, 택배사에 보낼 때 주문 값을 읽어 넘긴다 (DC-7 A).'),
 ]),
 ('도서산간', [
  cd('REMOTE_AREA_CD','도서산간 구분 코드 (출고 때 판단)','Remote Area Type Code (Judged at Shipment)',
     desc='출고할 때 기준표로 다시 판단한 값. 주문 값과 다를 수 있다 (주문 OC-107 A). 주문 코드 그룹을 함께 쓴다.'),
  fk('REMOTE_AREA_POSTCODE_ID','판단 근거 도서산간 기준표 식별 번호','Remote Area Postcode Basis Identifier','DLV_REMOTE_AREA_POSTCODE','Y','',
     '구분이 해당 없음이면 NULL, 제주·도서산간이면 NOT NULL (CK).'),
 ]),
 ('출고 창고', [
  ('WAREHOUSE_ID','출고 창고 식별 번호 (회수면 도착 창고)','Warehouse Identifier (Destination for Return)',ID,'N','','FK 예정 → `WMS_WAREHOUSE` (후보)',
   '묶인 요청과 같다 (3-3 C).'),
 ]),
 ('동시 갱신', [rowver()]),
 ],
 idx=['IX `REMOTE_AREA_POSTCODE_ID` (FK), (`SHIPMENT_STATUS_CD`, `SHIPPED_AT`)',
      'IX `PII_RETENTION_END_DT` (파기 배치, 선행 7)'],
 check=['구분이 출고이면 `SHIPPED_AT` NOT NULL, `PICKUP_REQUESTED_AT` NULL. 회수이면 `PICKUP_REQUESTED_AT` NOT NULL',
        '상태 값은 출고·회수 구분별로: 출고 = 출고, 배송 중, 일부 배송 완료, 배송 완료, 반송 중, 반송 완료 / 회수 = 회수 접수, 회수 실패, 배송 중, 배송 완료',
        '상태가 배송 완료이면 `DELIVERED_AT` NOT NULL',
        '`REMOTE_AREA_CD = NONE`이면 `REMOTE_AREA_POSTCODE_ID` NULL, 다른 값이면 NOT NULL'])

# =========================================================== 4. 운송장
table(t='DLV_WAYBILL', ko='운송장 (택배 박스 1개에 붙인 송장 1장)', en='Waybill',
 desc='출고 안의 택배 박스 1개에 붙인 운송장 1장. 운송장 번호(송장번호) 1개를 갖고, 택배사 추적 이벤트가 상태를 바꾼다 (T-1 C). 송장을 다시 받으면 새 행을 만든다 (DC-8 A). '
      '배송 완료의 근거와 핵심 일시를 복사해 두어, 추적 이벤트(1년)를 지운 뒤에도 공급 기록이 남는다 (DC-9 A, DC-14 B).',
 basis='1-1 B, 3-9 C, T-1 C, T-5 A, T-6 A, DC-8 A~DC-12 B, DC-14 B, DC-25 A, DC-61 A, DC-62 B, 선행 13, 택배 표준약관 12·14·15·20조',
 pk='대리 PK `SEQ_DLV_WAYBILL`', cache=100,
 delete=CORE_DEL, part=CORE_PART, keep='행: 부모 출고와 함께 지운다. 사고 행이 있으면 사고를 먼저 지운다',
 cols=[
 ('식별', [
  ('WAYBILL_ID','운송장 고유 식별 번호','Waybill Unique Identifier',ID,'N','','PK',''),
  fk('SHIPMENT_ID','출고 식별 번호','Shipment Identifier','DLV_SHIPMENT'),
  ('TRACKING_NO','운송장 번호 (송장번호)','Waybill Tracking Number','VARCHAR2(30)','N','','UK',
   '단독 UK (선행 13). 포장할 때 택배사 API로 받는다 (T-6 A). 회수 송장도 같은 UK를 쓴다 (2-1 B). 택배사가 보존 기간(5년) 안에 번호를 다시 쓰지 않는다는 전제다 [확인 필요: 택배사 계약, 3-9 C].'),
  fk('EXTERNAL_VENDOR_ID','택배사 외부 업체 식별 번호','Courier External Vendor Identifier',VENDOR,'N','',
     '외부 업체 마스터 (선행 13, 이름 후보). 택배사는 1곳이지만 행마다 남긴다.'),
 ]),
 ('상태', [
  cd('WAYBILL_STATUS_CD','운송장 상태 코드','Waybill Status Code',n=30,
     desc='추적 이벤트(택배사, 관리자 정정, 시스템)가 바꾼다. 상태 이력 테이블에는 남기지 않고 추적 이벤트가 이력이다 (T-1 C).'),
  ('STATUS_EVENT_OCCURRED_AT','현재 상태 근거 이벤트 발생 일시','Current Status Event Occurred At',TS,'Y','','',
   '늦게 온 이벤트의 발생 일시가 이 값보다 앞서면 이벤트만 쌓고 상태는 바꾸지 않는다 (DC-13 A). 추적 멈춤 감지에도 쓴다 (세부 4-10).'),
  fk('REISSUED_FROM_WAYBILL_ID','재발번 전 운송장 식별 번호','Reissued From Waybill Identifier','DLV_WAYBILL','Y','UK',
     '송장을 다시 받으면 새 행이 이전 행을 가리키고, 이전 행은 "송장 취소" 상태가 된다. 운송장 상품도 새 행으로 옮긴다 (DC-8 A). 이전 행 하나에 새 행은 하나 (UK).'),
 ]),
 ('배송 완료', [
  ('DELIVERED_AT','배송 완료 일시','Delivered At',TS,'Y','','',
   '청약철회 기간의 기산점이고 증명 책임은 판매자에게 있다 (전자상거래법 17조 5항). 회수 운송장이면 반환받은 날이다 (DC-21 A). 상태가 배송 완료이면 NOT NULL (CK).'),
  cd('RECEIPT_METHOD_CD','수령 방법 코드','Receipt Method Code','Y',
     desc='택배사가 알려 준 인도 방법 (택배 표준약관 15조, DC-9 A). 수령자 이름은 저장하지 않는다.'),
  ('DELIVERY_EVIDENCE_EVENT_CD','배송 완료 근거 이벤트 택배사 코드','Delivery Evidence Courier Event Code','VARCHAR2(30)','Y','','',
   '배송 완료로 판정한 이벤트의 택배사 원래 코드를 복사한다. 이벤트 FK는 두지 않는다 (이벤트 파티션 제거, DC-9 A).'),
  ('DELIVERY_EVIDENCE_LOCATION_NM','배송 완료 근거 이벤트 위치명','Delivery Evidence Location Name','VARCHAR2(100)','Y','','','근거 이벤트의 위치(영업소)를 복사한다 (DC-9 A).'),
 ]),
 ('일시', [
  ('INVOICE_ISSUED_AT','송장 발번 일시','Tracking Number Issued At',TS,'N','SYSTIMESTAMP','',''),
  ('PICKED_UP_AT','집화 일시','Picked Up At',TS,'Y','','','택배사 책임이 시작되는 때 (택배 표준약관 20조).'),
  ('OUT_FOR_DELIVERY_AT','배송 출발 일시','Out for Delivery At',TS,'Y','','','고객 알림 시점 (세부 4-11).'),
  ('EXPECTED_DELIVERY_DT','도착 예정 일자 (재계산)','Expected Delivery Date (Recalculated)','DATE','Y','','',
   '집화 일자 + 기본 일수(일반 2일, 도서산간 3일, 택배 표준약관 14조). 택배 집화가 없는 날은 영업일 달력의 택배 집화 가능 여부로 건너뛴다 (DC-26 A). 고객에게 약속한 날은 요청에 있다 (세부 1-24).'),
 ]),
 ('상자', [
  cd('BOX_SIZE_CD','박스 규격 코드','Box Size Code',desc='상품 코드 그룹을 함께 쓴다 (상품 34 B). 운임표 조회 조건이다.'),
  ('WEIGHT_GRAM_VAL','실측 무게 (그램)','Measured Weight (Grams)','NUMBER(7)','Y','','CK (> 0)','창고가 포장할 때 잰다. NULL이면 통과.'),
  amt('DECLARED_VALUE_AMT','신고 가액','Declared Value',
      '담긴 상품의 판매가 합계가 기준 금액(정책값, 지금 50만 원)을 넘는 박스만 채운다. 비우면 택배사 기본 한도(50만 원)로 배상받는다 (DC-10 B, 택배 표준약관 22조). '
      '300만 원을 넘으면 택배사가 수탁을 거절할 수 있어 포장을 나눈다 (약관 12조, 세부 1-7). [확인 필요: 신고 가액 할증 기준, 택배사 계약]', null='Y', d='', ck='CK (> 0)'),
 ]),
 ('운임', [
  fk('COURIER_RATE_ID','적용 택배사 운임표 식별 번호','Applied Courier Rate Identifier','DLV_COURIER_RATE','Y','',
     '포장할 때 박스 규격·지역·출고·회수 구분·서비스 유형으로 고른 행 (DC-11 A, DC-17 A). 운임표는 마스터라 FK를 건다.'),
  amt('BASE_FREIGHT_AMT','기본 운임 (택배사에 내는 금액)','Base Freight Amount (Payable to Courier)','운임표에서 복사한다. 고객이 낸 배송비는 주문에 있다 (주문 6-6 A).', null='Y', d=''),
  amt('SURCHARGE_FREIGHT_AMT','할증 운임 (제주·도서산간)','Surcharge Freight Amount (Remote Area)','운임표에서 복사한다.', null='Y', d=''),
  cd('FREIGHT_BEARER_CD','운임 부담 주체 코드','Freight Bearer Code','Y',
     desc='반품 운임을 누가 내는지 (전자상거래법 18조 9·10항). 고객에게 받은 반품 배송비 금액은 클레임에 둔다 (DC-11 A).'),
 ]),
 ('예외 수동 처리', [
  cd('WAYBILL_MANUAL_CHECK_REASON_CD','운송장 예외 수동 처리 사유 코드','Waybill Exception Manual Handling Reason Code','Y',n=30,
     desc='출고 요청과 같은 방식 (DC-25 A). 정렬은 `ATTR2` 그룹 순 (`LEGAL_DEADLINE`, `CUSTOMER_PROMISE`, `EXTERNAL_SYNC`, `OTHER`).'),
  ('MANUAL_CHECK_FLAGGED_AT','예외 수동 처리 대상 표시 일시','Exception Manual Handling Flagged At',TS,'Y','','','사유 코드와 함께 채운다 (CK).'),
  ('MANUAL_CHECK_RESOLVED_AT','예외 수동 처리 완료 일시','Exception Manual Handling Resolved At',TS,'Y','','','NULL이면 미처리 (표시 일시가 있을 때).'),
 ]),
 ('동시 갱신', [rowver()]),
 ],
 idx=['IX `SHIPMENT_ID`, `EXTERNAL_VENDOR_ID`, `COURIER_RATE_ID` (FK)',
      'IX (`WAYBILL_STATUS_CD`, `STATUS_EVENT_OCCURRED_AT`) (추적 멈춤 감지, 세부 4-10)',
      'IX `IX_DLV_WAYBILL_MANUAL_CHECK_OPEN` (함수 기반, 출고 요청과 같은 식)'],
 check=['상태가 배송 완료이면 `DELIVERED_AT` NOT NULL. `DELIVERED_AT`이 NULL이면 근거 코드·위치·수령 방법도 NULL',
        '`COURIER_RATE_ID`, `BASE_FREIGHT_AMT`, `SURCHARGE_FREIGHT_AMT`, `FREIGHT_BEARER_CD`는 모두 NULL이거나 모두 NOT NULL (포장 전에는 NULL)',
        '`REISSUED_FROM_WAYBILL_ID <> WAYBILL_ID` (NULL이면 통과)',
        '예외 수동 처리: 출고 요청과 같은 규칙'])

# =========================================================== 5. 운송장 상품
table(t='DLV_WAYBILL_ITEM', ko='운송장 상품 (어느 박스에 무엇을 몇 개)', en='Waybill Item',
 desc='박스 1개에 담은 요청 상품과 수량. 합포장이면 여러 요청의 상품이 한 박스에 들어가고, 주문별 구분은 이 행으로 남는다 (DC-24 B). 단순 연결 관계라 복합 PK다 (DC-15 A, 선행 1).',
 basis='1-1 B, DC-8 A, DC-15 A, DC-24 B, 선행 1',
 pk='복합 PK (`WAYBILL_ID`, `SHIPMENT_REQUEST_ITEM_ID`), 시퀀스 없음', cache='-',
 delete=CORE_DEL, part=CORE_PART, keep='행: 부모 운송장과 함께 지운다',
 cols=[
 ('식별', [
  fk('WAYBILL_ID','운송장 식별 번호','Waybill Identifier','DLV_WAYBILL','N','PK1'),
  fk('SHIPMENT_REQUEST_ITEM_ID','출고 요청 상품 식별 번호','Shipment Request Item Identifier','DLV_SHIPMENT_REQUEST_ITEM','N','PK2',
     '한 박스에 같은 요청 상품은 한 행이다.'),
 ]),
 ('수량', [
  qty('PACKED_QTY','담은 수량','Packed Quantity','요청 상품 `SHIPPED_QTY`는 유효 운송장의 이 값 합계다.',d='',ck='CK (>= 1)'),
 ]),
 ],
 idx=['IX `SHIPMENT_REQUEST_ITEM_ID` (FK, PK 두 번째 컬럼)'])

# =========================================================== 6. 추적 이벤트
table(t='DLV_TRACKING_EVENT', ko='배송 추적 이벤트 (운송장 상태 이력)', en='Tracking Event',
 desc='택배사가 보낸 추적 이벤트 1건, 또는 관리자 정정·시스템 이벤트 1건. 운송장 상태 이력을 겸한다 (T-1 C). 웹훅을 받으면 바로 이 테이블에 쓰고(수신함 없음), 누락은 주기 조회로 보완한다 (DC-20 B). '
      '택배사 설명 원문은 두지 않는다 (DC-16 A, DC-19 A).',
 basis='4-2 B, T-1 C, T-2 B, DC-13 A, DC-14 B, DC-16 A, DC-19 A, DC-20 B',
 pk='대리 PK `SEQ_DLV_TRACKING_EVENT`', cache=100,
 delete='삭제하지 않음 (로그). 파티션 단위로 제거 (선행 4)', part='`RECEIVED_AT` 월 단위 INTERVAL 파티션 (DC-14 B, DC-28 A)',
 keep='12개월 (DC-14 B). 배송 사고의 택배사 책임이 1년이면 소멸한다 (택배 표준약관 25조). 공급 기록은 운송장의 일시·근거 컬럼으로 남는다',
 cols=[
 ('식별', [
  ('TRACKING_EVENT_ID','추적 이벤트 고유 식별 번호','Tracking Event Unique Identifier',ID,'N','','PK',''),
  fk('WAYBILL_ID','운송장 식별 번호','Waybill Identifier','DLV_WAYBILL','N','UK1','자식 쪽 FK라 이 테이블의 파티션 제거를 막지 않는다.'),
 ]),
 ('이벤트', [
  cd('EVENT_SOURCE_CD','이벤트 출처 코드','Event Source Code',desc='관리자가 배송 완료 등을 고치면 관리자 정정 이벤트를 쓴다 (T-1 C, 세부 4-9).'),
  ('COURIER_EVENT_CD','택배사 이벤트 원래 코드','Courier Raw Event Code','VARCHAR2(30)','Y','','UK2',
   '택배사가 보낸 값 그대로. 출처가 택배사이면 NOT NULL (CK). 우리 상태와의 대응은 공통코드 그룹 하나에 값으로 두고 `ATTR1`에 우리 상태 코드를 적는다 (T-2 B).'),
  cd('WAYBILL_STATUS_CD','대응 운송장 상태 코드','Mapped Waybill Status Code','Y',n=30,
     desc='대응이 없으면 NULL로 저장하고 운송장 예외 수동 처리(택배사 코드 대응 없음)로 올린다 (DC-20 B).'),
  yn('STATUS_APPLIED_YN','운송장 상태 반영 여부','Applied to Waybill Status Flag','N',
     '늦게 온 이벤트(발생 일시가 운송장의 현재 상태 근거보다 앞섬)나 대응 없는 코드는 N (DC-13 A).'),
  ('EVENT_OCCURRED_AT','이벤트 발생 일시 (택배사 시각)','Event Occurred At (Courier Time)',TS,'N','','UK3',''),
  ('RECEIVED_AT','이벤트 수신 일시','Event Received At',TS,'N','SYSTIMESTAMP','','파티션 키.'),
  ('LOCATION_NM','이벤트 위치명 (영업소·터미널)','Event Location Name (Branch or Terminal)','VARCHAR2(100)','Y','','',''),
 ]),
 ('정정', [
  ('CORRECTED_EVENT_ID','정정 대상 추적 이벤트 식별 번호','Corrected Tracking Event Identifier',ID,'Y','','IX (FK 없음)',
   '관리자 정정이면 NOT NULL (CK). 자기 참조 FK를 걸면 이 테이블의 월 파티션 제거가 막혀(ORA-02266) 값으로만 둔다.'),
  ('CORRECTION_REASON_DESC','정정 사유','Correction Reason','VARCHAR2(500)','Y','','','관리자 정정이면 NOT NULL (CK).'),
 ]),
 ],
 idx=['UK GLOBAL (`WAYBILL_ID`, `COURIER_EVENT_CD`, `EVENT_OCCURRED_AT`) (중복 수신 방지, DC-13 A). 파티션 키가 없어 GLOBAL 인덱스이고, 파티션을 제거할 때 `UPDATE GLOBAL INDEXES`를 쓴다. '
      '관리자 정정처럼 택배사 코드가 NULL인 행도 같은 운송장·같은 시각이면 막힌다 [확인 필요: 택배사가 이벤트 ID를 주면 이벤트 ID UK로 바꿈 (DC-13 B)]',
      'IX LOCAL `CORRECTED_EVENT_ID`, (`WAYBILL_STATUS_CD`, `RECEIVED_AT`) (대응 없는 코드 감시: 상태 NULL)'],
 check=['출처가 택배사이면 `COURIER_EVENT_CD` NOT NULL. 다른 출처이면 제약 없음 (NULL이면 통과)',
        '출처가 관리자 정정이면 `CORRECTED_EVENT_ID`, `CORRECTION_REASON_DESC` NOT NULL. 다른 출처이면 둘 다 NULL',
        '`WAYBILL_STATUS_CD`가 NULL이면 `STATUS_APPLIED_YN = N`'])

# =========================================================== 7. 배송 사고
table(t='DLV_WAYBILL_ACCIDENT', ko='배송 사고 (택배사 배상 청구)', en='Delivery Accident per Waybill',
 desc='박스 1개에 생긴 사고 1건 (운송장 1 : 사고 N). 택배사와의 배상 청구 과정을 담는다. 고객 보상과 상품 단위 처리는 클레임이 맡는다 (T-3 A, DC-15 A, 세부 1-29). 배상 상계는 정산.',
 basis='T-3 A, DC-15 A, DC-63 A, 택배 표준약관 18·19·22·25조',
 pk='대리 PK `SEQ_DLV_WAYBILL_ACCIDENT`', cache=20,
 delete=CORE_DEL, part=CORE_PART, keep='행: 부모 운송장과 함께 지운다. 재발송 요청이 가리키면 그 요청을 먼저 지운다',
 cols=[
 ('식별', [
  ('WAYBILL_ACCIDENT_ID','배송 사고 고유 식별 번호','Delivery Accident Unique Identifier',ID,'N','','PK',''),
  fk('WAYBILL_ID','사고 운송장 식별 번호','Accident Waybill Identifier','DLV_WAYBILL'),
 ]),
 ('사고', [
  cd('ACCIDENT_TYPE_CD','배송 사고 유형 코드','Delivery Accident Type Code',n=30,desc='택배 표준약관 18조.'),
  cd('ACCIDENT_STATUS_CD','배송 사고 처리 상태 코드','Delivery Accident Status Code',n=30),
  cd('DETECTED_BY_CD','사고 발견 경로 코드','Accident Detected By Code'),
  ('DETECTED_AT','사고 발견 일시','Accident Detected At',TS,'N','','',''),
  ('ACCIDENT_DESC','사고 내용','Accident Description','VARCHAR2(1000)','Y','','','개인정보를 적지 않는다.'),
 ]),
 ('택배사 통지 기한', [
  ('COURIER_NOTICE_DEADLINE_DT','택배사 통지 기한 일자','Courier Notice Deadline Date','DATE','Y','','',
   '수령일 + 14일. 일부 멸실·훼손이면 NOT NULL (CK, 택배 표준약관 25조 1항). 지나면 택배사 책임이 소멸한다.'),
  ('COURIER_NOTIFIED_AT','택배사 통지 일시','Courier Notified At',TS,'Y','','',''),
  ('LIABILITY_EXPIRY_DT','택배사 책임 소멸 일자','Courier Liability Expiry Date','DATE','N','','',
   '수령일(전부 멸실이면 인도 예정일) + 1년 (택배 표준약관 25조 2항). 사고증명서 발행 기한(19조)과 같다.'),
 ]),
 ('배상', [
  amt('COMPENSATION_CLAIM_AMT','배상 청구액','Compensation Claim Amount','택배 표준약관 22조. 신고 가액이 있으면 그 금액이 한도다.', null='Y', d=''),
  ('PROOF_SUBMITTED_AT','손해 입증 서류 제출 일시','Loss Proof Submitted At',TS,'Y','','',''),
  ('COMPENSATION_DUE_DT','우선 배상 기한 일자','Priority Compensation Due Date','DATE','Y','','',
   '서류 제출일 + 30일 (택배 표준약관 22조 5항). 제출 일시가 있으면 NOT NULL (CK).'),
  amt('COMPENSATION_RECEIVED_AMT','배상 받은 금액','Compensation Received Amount','', null='Y', d=''),
  ('COMPENSATION_RECEIVED_AT','배상 받은 일시','Compensation Received At',TS,'Y','','','받은 금액과 함께 채운다 (CK).'),
  ('COMPENSATION_REJECT_REASON_DESC','배상 거절 사유','Compensation Reject Reason','VARCHAR2(500)','Y','','','상태가 배상 거절이면 NOT NULL (CK).'),
 ]),
 ('고객 쪽 연결', [
  ref('CLAIM_ID','고객 보상 클레임 식별 번호','Customer Compensation Claim Identifier',
      desc='고객 보상은 클레임이 맡는다 (세부 1-29). 재발송은 출고 요청의 `SOURCE_WAYBILL_ACCIDENT_ID`가 이 행을 가리킨다.'),
 ]),
 ],
 idx=['IX `WAYBILL_ID` (FK), `CLAIM_ID` (값 참조), (`ACCIDENT_STATUS_CD`, `COURIER_NOTICE_DEADLINE_DT`) (통지 기한 감시)'],
 check=['유형이 일부 멸실·훼손이면 `COURIER_NOTICE_DEADLINE_DT` NOT NULL. 다른 유형이면 제약 없음 (NULL이면 통과)',
        '`PROOF_SUBMITTED_AT`이 NOT NULL이면 `COMPENSATION_DUE_DT` NOT NULL',
        '`COMPENSATION_RECEIVED_AMT`와 `COMPENSATION_RECEIVED_AT`은 둘 다 NULL이거나 둘 다 NOT NULL. 상태가 배상 완료이면 둘 다 NOT NULL',
        '상태가 배상 거절이면 `COMPENSATION_REJECT_REASON_DESC` NOT NULL'])

# =========================================================== 8. 상태 이력
table(t='DLV_STATUS_HIST', ko='출고 요청·출고 상태 이력', en='Shipment Request and Shipment Status History',
 desc='출고 요청과 출고의 상태가 바뀔 때마다 1행. 운송장 상태는 추적 이벤트가 이력이라 여기 두지 않는다 (T-1 C). 누가 바꿨는지는 시스템 컬럼 `CREATED_BY_TYPE_CD`·`CREATED_BY`에 남는다 (택배사는 `EXTERNAL` + 업체 코드, 선행 8).',
 basis='T-1 C, T-4 A, DC-28 A, 선행 6, 선행 8',
 pk='대리 PK `SEQ_DLV_STATUS_HIST`', cache=100,
 delete='삭제하지 않음 (이력). 대상 행을 지우는 배치가 먼저 이 행들을 지운다', part='`CHANGED_AT` 월 단위 INTERVAL 파티션 (DC-28 A). 다 지워진 월 파티션은 제거',
 keep='대상 출고 요청·출고와 같다 (DC-28 A)',
 cols=[
 ('식별', [
  ('STATUS_HIST_ID','상태 이력 고유 식별 번호','Status History Unique Identifier',ID,'N','','PK',''),
 ]),
 ('대상', [
  fk('SHIPMENT_REQUEST_ID','대상 출고 요청 식별 번호','Target Shipment Request Identifier','DLV_SHIPMENT_REQUEST','Y','','대상 둘 중 정확히 하나 (CK, 선행 6).'),
  fk('SHIPMENT_ID','대상 출고 식별 번호','Target Shipment Identifier','DLV_SHIPMENT','Y'),
 ]),
 ('변경', [
  ('BEFORE_STATUS_CD','바뀌기 전 상태 코드','Before Status Code','VARCHAR2(30)','Y','','CK (테이블 수준)','처음 생성이면 NULL. 대상이 요청이면 출고 요청 상태, 출고이면 출고 상태의 값이다.'),
  ('AFTER_STATUS_CD','바뀐 뒤 상태 코드','After Status Code','VARCHAR2(30)','N','','CK (테이블 수준)',''),
  cd('SHIPMENT_HOLD_REASON_CD','출고 보류 사유 코드','Shipment Hold Reason Code','Y',n=30,desc='보류를 걸 때만 (T-4 A). 대상이 출고이면 NULL (CK).'),
  ('CHANGED_AT','상태 변경 일시','Status Changed At',TS,'N','SYSTIMESTAMP','','파티션 키.'),
  ('CHANGE_REASON_DESC','상태 변경 사유','Status Change Reason','VARCHAR2(500)','Y','','','관리자가 바꾸면 필수 (애플리케이션 검사).'),
 ]),
 ],
 idx=['IX LOCAL (`SHIPMENT_REQUEST_ID`, `CHANGED_AT`), (`SHIPMENT_ID`, `CHANGED_AT`) (FK)'],
 check=['`SHIPMENT_REQUEST_ID`와 `SHIPMENT_ID` 중 정확히 하나만 NOT NULL (선행 6)',
        '전·후 상태 값: 요청 대상이면 출고 요청 상태 값, 출고 대상이면 출고 상태 값 (`BEFORE_STATUS_CD`가 NULL이면 통과)'])

# =========================================================== 9. 운임표
table(t='DLV_COURIER_RATE', ko='택배사 운임표 (택배사에 내는 계약 단가)', en='Courier Rate',
 desc='택배사 계약 운임 1개 조합(출고·회수 구분 × 서비스 유형 × 박스 규격 × 지역 구분)과 적용 기간 1행. 기본 운임과 할증 운임을 한 행에 둔다 (T-5 A, DC-17 A). 고객이 낸 배송비(주문 6-6 A)와는 별개다. 택배사 청구 대사는 정산이 이 단가로 한다.',
 basis='T-5 A, DC-11 A, DC-17 A, 선행 4, DC-32 C',
 pk='대리 PK `SEQ_DLV_COURIER_RATE`', cache=20, ldel=True,
 delete='논리 삭제 (마스터, 선행 4). 운송장이 가리키면 지우지 않고 적용 종료일로 끝낸다', part='없음', keep='논리 삭제 뒤 1년 (선행 4). 운송장이 가리키는 행은 지우지 않는다',
 cols=[
 ('식별', [
  ('COURIER_RATE_ID','택배사 운임표 고유 식별 번호','Courier Rate Unique Identifier',ID,'N','','PK',''),
 ]),
 ('조건', [
  fk('EXTERNAL_VENDOR_ID','택배사 외부 업체 식별 번호','Courier External Vendor Identifier',VENDOR,'N','UK1'),
  cd('SHIP_PICKUP_TYPE_CD','출고·회수 구분 코드','Shipment / Pickup Type Code',ck='CK (값 목록), UK2'),
  cd('DELIVERY_SERVICE_TYPE_CD','배송 서비스 유형 코드','Delivery Service Type Code',ck='CK (값 목록), UK3'),
  cd('BOX_SIZE_CD','박스 규격 코드','Box Size Code',ck='CK (값 목록), UK4',desc='상품 코드 그룹을 함께 쓴다.'),
  cd('REMOTE_AREA_CD','지역 구분 코드','Remote Area Type Code',ck='CK (값 목록), UK5',desc='주문 코드 그룹을 함께 쓴다. 해당 없음 행에는 할증 운임이 0이다.'),
 ]),
 ('금액', [
  amt('BASE_FREIGHT_AMT','기본 운임','Base Freight Amount'),
  amt('SURCHARGE_FREIGHT_AMT','할증 운임 (제주·도서산간)','Surcharge Freight Amount (Remote Area)','지역 구분이 해당 없음이면 0 (CK).'),
 ]),
 ('적용 기간', [
  ('APPLY_START_DT','적용 시작 일자','Apply Start Date','DATE','N','','UK6',''),
  ('APPLY_END_DT','적용 종료 일자','Apply End Date','DATE','Y','','','NULL이면 계속 적용. 같은 조합의 기간 겹침은 애플리케이션이 검사한다.'),
 ]),
 ],
 idx=['UK (`EXTERNAL_VENDOR_ID`, `SHIP_PICKUP_TYPE_CD`, `DELIVERY_SERVICE_TYPE_CD`, `BOX_SIZE_CD`, `REMOTE_AREA_CD`, `APPLY_START_DT`)'],
 check=['`APPLY_END_DT >= APPLY_START_DT` (NULL이면 통과)', '`REMOTE_AREA_CD = NONE`이면 `SURCHARGE_FREIGHT_AMT = 0`'])

# =========================================================== 10. 도서산간 기준표
table(t='DLV_REMOTE_AREA_POSTCODE', ko='도서산간 우편번호 기준표', en='Remote Area Postcode',
 desc='제주·도서산간 우편번호 1개와 적용 기간 1행 (T-7 A). 없는 우편번호는 해당 없음이다. 주문(5-7 A)과 출고(OC-107 A)가 이 표로 판단한다. 고객에게 받는 추가 배송비 금액은 여기 두지 않고 구분 코드별로 공통코드 `ATTR`에 둔다 (DC-18 B).',
 basis='T-7 A, DC-18 B, 주문 5-7 A, 주문 OC-107 A, 회원 22-4',
 pk='대리 PK `SEQ_DLV_REMOTE_AREA_POSTCODE`', cache=20, ldel=True,
 delete='논리 삭제 (마스터, 선행 4). 출고가 가리키면 지우지 않고 적용 종료일로 끝낸다', part='없음', keep='논리 삭제 뒤 1년 (선행 4). 출고가 가리키는 행은 지우지 않는다',
 cols=[
 ('식별', [
  ('REMOTE_AREA_POSTCODE_ID','도서산간 기준표 고유 식별 번호','Remote Area Postcode Unique Identifier',ID,'N','','PK',''),
 ]),
 ('기준', [
  ('POSTAL_CODE_VAL','우편번호','Postal Code','VARCHAR2(5)','N','','UK1, CK (숫자 5자리)',''),
  cd('REMOTE_AREA_CD','도서산간 구분 코드','Remote Area Type Code',desc='주문 코드 그룹을 함께 쓰되 해당 없음은 넣지 않는다 (CK).'),
 ]),
 ('적용 기간', [
  ('APPLY_START_DT','적용 시작 일자','Apply Start Date','DATE','N','','UK2',''),
  ('APPLY_END_DT','적용 종료 일자','Apply End Date','DATE','Y','','','NULL이면 계속 적용. 같은 우편번호의 기간 겹침은 애플리케이션이 검사한다.'),
 ]),
 ('근거', [
  ('BASIS_DESC','기준 근거 (택배사 기준표 버전 등)','Basis Description (Courier Table Version etc.)','VARCHAR2(200)','Y','','',''),
 ]),
 ],
 idx=['UK (`POSTAL_CODE_VAL`, `APPLY_START_DT`)'],
 check=['`REMOTE_AREA_CD <> NONE`', '`APPLY_END_DT >= APPLY_START_DT` (NULL이면 통과)'])

# =========================================================== 11. 연동 로그
table(t='DLV_COURIER_INTERFACE_LOG', ko='택배사 연동 요약 로그', en='Courier Interface Summary Log',
 desc='택배사 API 호출 1회, 또는 추적 웹훅 수신 1회당 1행. 원문(수령인 이름·휴대폰·주소가 들어 있음)은 DB에 두지 않고 외부 로그 도구 추적 값으로 찾아간다 (DC-19 A, 결제 7-1 C와 같음). 출고 요청·운송장 ID는 FK 없이 둔다.',
 basis='DC-19 A, DC-20 B, 선행 6, 결제 7-1 C',
 pk='대리 PK `SEQ_DLV_COURIER_INTERFACE_LOG`', cache=100,
 delete='삭제하지 않음 (로그). 파티션 단위로 제거 (선행 4)', part='`REQUESTED_AT` 월 단위 INTERVAL 파티션 (DC-28 A)', keep='12개월 (정책값, 결제와 같음)',
 cols=[
 ('식별', [
  ('COURIER_INTERFACE_LOG_ID','택배사 연동 로그 고유 식별 번호','Courier Interface Log Unique Identifier',ID,'N','','PK',''),
  ('EXTERNAL_VENDOR_ID','택배사 외부 업체 식별 번호','Courier External Vendor Identifier',ID,'N','','IX (FK 없음)','로그라 FK를 걸지 않는다.'),
  cd('COURIER_API_TYPE_CD','택배사 연동 종류 코드','Courier Interface Type Code',n=30),
 ]),
 ('결과', [
  cd('API_CALL_RESULT_CD','호출 결과 코드','API Call Result Code',desc='웹훅 수신이면 우리 쪽 처리 결과.'),
  ('COURIER_RESULT_CD','택배사 결과 코드 (원래 값)','Courier Result Code (Raw)','VARCHAR2(50)','Y','','',''),
  ('COURIER_RESULT_MESSAGE_CN','택배사 결과 메시지','Courier Result Message','VARCHAR2(1000)','Y','','','개인정보가 섞이면 가린 뒤 저장한다.'),
  ('HTTP_STATUS_VAL','HTTP 상태 값','HTTP Status Value','NUMBER(3)','Y','','','시간 초과면 NULL.'),
  cd('SIGNATURE_VERIFICATION_RESULT_CD','웹훅 서명 검증 결과 코드','Webhook Signature Verification Result Code','Y',
     desc='추적 웹훅 수신만. 불일치면 이벤트를 쓰지 않고 이 행만 남는다 (DC-20 B). 호출이면 NULL.'),
  ('REQUESTED_AT','요청 일시 (웹훅이면 수신 일시)','Requested At (Webhook: Received At)',TS,'N','','','파티션 키.'),
  ('RESPONDED_AT','응답 일시','Responded At',TS,'Y','','',''),
  ('ELAPSED_MILLISECOND_CNT','소요 시간 (밀리초)','Elapsed Milliseconds','NUMBER(10)','Y','','CK (>= 0)','NULL이면 통과.'),
 ]),
 ('대상', [
  ref('SHIPMENT_REQUEST_ID','관련 출고 요청 식별 번호','Related Shipment Request Identifier',desc='로그라 FK 없음 (파티션 제거·보존 기간이 다름).'),
  ref('WAYBILL_ID','관련 운송장 식별 번호','Related Waybill Identifier'),
  ('TRACKING_NO','관련 운송장 번호 (송장번호)','Related Waybill Tracking Number','VARCHAR2(30)','Y','','IX',''),
  ('REQUEST_KEY_VAL','택배사 요청 중복 방지 키','Courier Request Idempotency Key','VARCHAR2(64)','Y','','IX',
   '접수·발번 요청을 다시 보낼 때 같은 값을 보낸다. 출고 번호와 운송장 ID로 만든다 (세부 3-10).'),
 ]),
 ('원문 추적', [
  ('EXTERNAL_LOG_TRACE_VAL','외부 로그 추적 값','External Log Trace Value','VARCHAR2(100)','Y','','','외부 로그 도구에서 원문을 찾는 키 (DC-19 A).'),
 ]),
 ],
 idx=['IX LOCAL: `SHIPMENT_REQUEST_ID`, `WAYBILL_ID`, `TRACKING_NO`, `REQUEST_KEY_VAL`, (`COURIER_API_TYPE_CD`, `API_CALL_RESULT_CD`, `REQUESTED_AT`) (연동 실패 감시)'],
 check=['연동 종류가 추적 수신이면 `SIGNATURE_VERIFICATION_RESULT_CD` NOT NULL, 다른 종류이면 NULL'])

TABLE_GROUPS = [
 ('출고 요청·출고', ['DLV_SHIPMENT_REQUEST', 'DLV_SHIPMENT_REQUEST_ITEM', 'DLV_SHIPMENT']),
 ('운송장·추적·사고', ['DLV_WAYBILL', 'DLV_WAYBILL_ITEM', 'DLV_TRACKING_EVENT', 'DLV_WAYBILL_ACCIDENT']),
 ('이력', ['DLV_STATUS_HIST']),
 ('기준 데이터', ['DLV_COURIER_RATE', 'DLV_REMOTE_AREA_POSTCODE']),
 ('연동', ['DLV_COURIER_INTERFACE_LOG']),
]

def vals(*v): return [(a, b, c, d, i) for i, (a, b, c, d) in enumerate(v, 1)]
EXC_DESC = ' · `ATTR2` '
CODES = {
 'SHIP_PICKUP_TYPE_CD': vals(('SHIP','출고 (창고 → 고객)','Shipment','주문 출고, 교환·사고·반송 재발송'),('PICKUP','회수 (고객 → 창고)','Pickup','반품·교환 회수 (2-1 B). 지정 택배 방문 회수만 (DC-35 B)')),
 'REQUEST_REASON_CD': vals(
   ('ORDER','주문 출고','Order Shipment','구분 출고. 주문 상품·주문 사은품 대상'),
   ('EXCHANGE_RESHIP','교환 재발송','Exchange Reshipment','구분 출고. 클레임 상품 대상'),
   ('ACCIDENT_RESHIP','사고 재발송','Accident Reshipment','구분 출고. 원인 사고 ID 필수'),
   ('RETURNED_RESHIP','반송 재발송','Returned Waybill Reshipment','구분 출고. 수령 거절·주소 불명으로 반송 완료된 운송장을 다시 보냄. 원인 운송장 ID 필수 (DC-33 A)'),
   ('MISSING_RESHIP','출고 누락 재발송','Missing Item Reshipment','구분 출고. 창고가 박스에 빠뜨린 주문 상품·사은품을 다시 보냄. 원인 운송장 ID 필수. 택배사 사고가 아니다 (DC-37 A)'),
   ('REPAIR_RESHIP','수선 재발송','Repair Reshipment','구분 출고. 수선을 마친 상품을 고객에게 보냄. 클레임 상품 대상. 수선 완료 때 만든다 (DC-39 B, DC-43 B)'),
   ('NON_ORDER','비주문 출고','Non-Order Shipment','구분 출고. 협찬·임직원 샘플·보상품. 주문 없이 실물(SKU·비판매 품목)만 지정 (DC-40 A)'),
   ('RETURN_PICKUP','반품 회수','Return Pickup','구분 회수'),
   ('EXCHANGE_PICKUP','교환 회수','Exchange Pickup','구분 회수'),
   ('REPAIR_PICKUP','수선 회수','Repair Pickup','구분 회수. 클레임 유형 "수선"을 따라감 (DC-39 B)')),
 'SHIPMENT_REQUEST_STATUS_CD': vals(
   ('WAITING_AVAILABLE_DATE','출고 가능일 대기','Waiting for Available Date','구분 출고. 예약 상품. 약정 공급일까지'),
   ('WAITING_PICKUP_ARRIVAL','회수 도착 대기','Waiting for Pickup Arrival','구분 출고. 교환 재발송. 선행 회수 요청이 회수 완료가 될 때까지 (DC-34 A). 회수 상태와 헷갈리지 않게 `WAITING_PICKUP`에서 이름을 바꿈 (DC-58 A)'),
   ('WAITING_STOCK','재고 입고 대기','Waiting for Stock','구분 출고. 재고 할당에 실패했지만 적용 기한 안에 입고될 예정이라 기다림. 기한이 임박하면 예외 수동 처리(기한 임박)로 올리고, 입고되지 않으면 결품으로 공급 곤란 통지 (DC-52 B). [확인 필요: 진입·해제 조건은 재고(INV) 설계 때]'),
   ('READY','출고 대기','Ready','구분 출고. 창고에 작업 지시를 넘기기 전'),
   ('WAREHOUSE_WORKING','창고 작업 중','Warehouse Working','구분 출고. 피킹·검수·포장은 WMS (DC-2 A). 고객 취소와 경합하면 WMS 작업 취소를 먼저 요청'),
   ('PARTIALLY_SHIPPED','일부 출고','Partially Shipped','구분 출고. 분할 출고'),
   ('SHIPPED','출고 완료','Shipped','구분 출고. 출고 + 결품 + 취소 수량 = 요청 수량이고 출고 수량 합계 >= 1. 하나도 나가지 않으면 출고 완료가 아니라 취소 (DC-50 A)'),
   ('PICKUP_READY','회수 접수 대기','Pickup Ready','구분 회수. 클레임이 회수를 요청했고 아직 택배사 접수 전 (DC-58 A)'),
   ('PICKUP_BOOKED','회수 접수 완료','Pickup Booked','구분 회수. 택배사에 접수됨. 기사 방문·집화·운송 중'),
   ('PICKUP_FAILED','회수 실패 (재접수 필요)','Pickup Failed','구분 회수. 고객 부재 등. 재접수하면 회수 접수 완료로 돌아가고(새 출고·운송장, DC-22 A), 한도를 넘기면 예외 수동 처리(회수 재접수 한도 초과)'),
   ('PICKUP_COMPLETED','회수 완료 (창고 도착)','Pickup Completed','구분 회수. 마지막 박스가 창고에 도착 (회수 운송장 배송 완료, DC-21 A). 끝 상태. 교환 재발송의 회수 도착 대기를 푼다'),
   ('CANCELED','취소','Canceled','공통. 회수면 클레임 철회')),
 'DELIVERY_SERVICE_TYPE_CD': vals(('STANDARD','일반 배송','Standard',''),('GUARANTEED_ARRIVAL','도착 보장','Guaranteed Arrival','약정 도착일 필수. 조건은 `ATTR1`~`ATTR3`(주문 마감 시각, 약정 일수, 보상 방식) (DC-4 A)')),
 'NON_ORDER_TYPE_CD': vals(
   ('SPONSORSHIP','협찬','Sponsorship','인플루언서 등 협찬품'),
   ('EMPLOYEE_SAMPLE','임직원 샘플','Employee Sample',''),
   ('COMPENSATION','보상품','Compensation Item','클레임 보상으로 보내는 물건. `CLAIM_ID` 필수 (CK)'),
   ('OTHER','기타','Other','사유는 관리자 작업 로그')),
 'TARGET_TYPE_CD': vals(
   ('ORDER_ITEM','주문 상품','Order Item','가상 컬럼 계산값 (DC-48 B)'),
   ('ORDER_FREEBIE','주문 사은품','Order Freebie',''),
   ('CLAIM_ITEM','클레임 상품','Claim Item','사은품 반환 행 포함 (DC-46 A)'),
   ('NONE','대상 없음','None','비주문 출고 (DC-40 A)')),
 'AGREED_SUPPLY_BASIS_CD': vals(
   ('PRE_ORDER','예약 상품','Pre-Order','출고 예정일 (상품 PC-42 B)'),
   ('GIFT','선물 수락','Gift Acceptance','수락일 + 3영업일 (주문 8-4 A)'),
   ('OTHER','기타','Other','')),
 'SHIPMENT_HOLD_REASON_CD': vals(
   ('PAYMENT_EXCEPTION','결제 예외','Payment Exception','결제 예외 수동 처리 대상 (결제 PYC-58)'),
   ('CANCEL_REQUESTED','취소 접수','Cancel Requested','고객 취소 요청 처리 중'),
   ('ADDRESS_CHANGE','배송지 변경','Address Change','출고 전 변경 (주문 5-5 A)'),
   ('ADDRESS_CHECK','배송지 확인 필요','Address Check',''),
   ('ORDER_HOLD','주문 보류','Order Hold','주문 `HOLD_REASON_CD` (재판매 의심 등)'),
   ('OTHER','기타','Other','변경 사유 필수')),
 'SHIPMENT_REQUEST_CANCEL_REASON_CD': vals(
   ('ORDER_CANCELED','주문 취소','Order Canceled',''),('CLAIM_WITHDRAWN','클레임 철회','Claim Withdrawn','회수 요청'),
   ('OUT_OF_STOCK','결품','Out of Stock','공급 곤란 통지 (15조 2항). 요청 전량이 결품이면 이 사유로 요청을 취소한다 (DC-50 A)'),('OTHER','기타','Other','')),
 'LAST_PICKUP_FAIL_REASON_CD': vals(
   ('CUSTOMER_ABSENT','고객 부재','Customer Absent',''),('ITEM_NOT_READY','상품 미준비','Item Not Ready',''),
   ('ADDRESS_ERROR','주소 오류','Address Error',''),('CUSTOMER_REFUSED','고객 거부','Customer Refused',''),
   ('COURIER_MISSED','택배사 미방문','Courier Missed',''),('OTHER','기타','Other','')),
 'REQUEST_MANUAL_CHECK_REASON_CD': vals(
   ('SHIP_DUE_EXCEEDED','출고 기한 초과','Ship Due Exceeded','적용 기한(15조 1항 3영업일 또는 약정일)을 넘김. 지연 안내와 공급 곤란 판단' + EXC_DESC + 'LEGAL_DEADLINE'),
   ('SHIP_DUE_APPROACHING','출고 기한 임박','Ship Due Approaching','정책값 시간 안에 기한이 옴' + EXC_DESC + 'LEGAL_DEADLINE'),
   ('GUARANTEE_AT_RISK','도착 보장 위험','Guarantee at Risk','도착 보장 출고 마감 일시까지 출고하지 못함 (DC-55 A)' + EXC_DESC + 'CUSTOMER_PROMISE'),
   ('INTERNAL_TARGET_EXCEEDED','내부 목표 초과','Internal Target Exceeded','재발송·회수·비주문 출고가 내부 목표 출고 일자를 넘김 (DC-54 A). 법정 기한 건과 정렬 그룹을 나눈다' + EXC_DESC + 'CUSTOMER_PROMISE'),
   ('PICKUP_RETRY_LIMIT_EXCEEDED','회수 재접수 한도 초과','Pickup Retry Limit Exceeded','DC-22 A. 반품 환급 기한과 연결' + EXC_DESC + 'CUSTOMER_PROMISE'),
   ('COURIER_INTERFACE_FAILED','택배사 연동 실패','Courier Interface Failed','발번·접수 재시도 한도 초과' + EXC_DESC + 'EXTERNAL_SYNC'),
   ('OTHER','기타','Other','내용은 관리자 작업 로그. 늘면 새 값으로 올린다' + EXC_DESC + 'OTHER')),
 'SHIPMENT_STATUS_CD': vals(
   ('SHIPPED','출고 (창고 출발)','Shipped','구분 출고'),
   ('PICKUP_REQUESTED','회수 접수','Pickup Requested','구분 회수'),
   ('PICKUP_FAILED','회수 실패','Pickup Failed','구분 회수. 재접수는 새 출고 (DC-22 A)'),
   ('IN_TRANSIT','배송 중','In Transit',''),
   ('PARTIALLY_DELIVERED','일부 배송 완료','Partially Delivered','박스 여러 개 중 일부'),
   ('DELIVERED','배송 완료 (회수면 창고 도착)','Delivered',''),
   ('RETURNING','반송 중','Returning','구분 출고. 수령 거절·주소 불명 (세부 2-8)'),
   ('RETURNED','반송 완료','Returned','구분 출고')),
 'DELIVERY_PLACE_CD': vals(('DOOR','문 앞','Front Door','회원 코드 그룹'),('SECURITY_OFFICE','경비실','Security Office',''),('PARCEL_LOCKER','택배함','Parcel Locker',''),('IN_PERSON','직접 수령','In Person',''),('OTHER','기타','Other','배송 요청 사항 필수')),
 'REMOTE_AREA_CD': vals(('NONE','해당 없음','None','주문 코드 그룹'),('JEJU','제주','Jeju',''),('ISLAND_MOUNTAIN','도서산간 (제주 외)','Island or Mountain Area','')),
 'WAYBILL_STATUS_CD': vals(
   ('INVOICE_ISSUED','송장 발번','Tracking Number Issued',''),('PICKED_UP','집화','Picked Up',''),('IN_TRANSIT','이동 중','In Transit',''),
   ('OUT_FOR_DELIVERY','배송 출발','Out for Delivery',''),('DELIVERED','배송 완료','Delivered','회수면 창고 도착 = 반환받은 날 (DC-21 A)'),
   ('DELIVERY_FAILED','배송 실패 (부재 등)','Delivery Failed','재배송 이벤트가 오면 다시 진행'),
   ('PICKUP_FAILED','회수 실패','Pickup Failed','구분 회수'),
   ('RETURNING','반송 중','Returning','구분 출고'),('RETURNED','반송 완료','Returned','구분 출고'),
   ('LOST','분실','Lost','사고 행 생성'),('INVOICE_CANCELED','송장 취소','Tracking Number Canceled','재발번 전 행 (DC-8 A)')),
 'RECEIPT_METHOD_CD': vals(('SELF','본인 수령','Recipient',''),('PROXY','대리인 수령','Proxy','택배 표준약관 15조'),('SECURITY_OFFICE','경비실','Security Office',''),
   ('PARCEL_LOCKER','택배함','Parcel Locker',''),('DOOR','문 앞','Front Door','')),
 'BOX_SIZE_CD': vals(('SMALL','소','Small','상품 코드 그룹 [확인 필요: 택배사 규격]'),('MEDIUM','중','Medium',''),('LARGE','대','Large',''),('EXTRA_LARGE','특대','Extra Large','')),
 'FREIGHT_BEARER_CD': vals(('COMPANY','회사','Company','출고, 회사 귀책 반품 (18조 10항)'),('CUSTOMER','고객','Customer','단순 변심 반품 (18조 9항). 금액은 클레임')),
 'WAYBILL_MANUAL_CHECK_REASON_CD': vals(
   ('GUARANTEE_VIOLATED','도착 보장 위반','Guarantee Violated','약정 도착일까지 배송 완료가 아님. 보상은 클레임·프로모션' + EXC_DESC + 'CUSTOMER_PROMISE'),
   ('TRACKING_STALLED','추적 멈춤','Tracking Stalled','정책값 시간 동안 새 이벤트 없음 (세부 4-10)' + EXC_DESC + 'CUSTOMER_PROMISE'),
   ('COURIER_CODE_UNMAPPED','택배사 코드 대응 없음','Courier Code Unmapped','공통코드에 대응을 더한 뒤 다시 처리 (DC-20 B)' + EXC_DESC + 'EXTERNAL_SYNC'),
   ('COURIER_INTERFACE_FAILED','택배사 연동 실패','Courier Interface Failed','운송 중지·조회 재시도 한도 초과' + EXC_DESC + 'EXTERNAL_SYNC'),
   ('COURIER_RECONCILIATION_MISMATCH','택배사 대사 불일치','Courier Reconciliation Mismatch','청구 대사는 정산 (세부 1-32)' + EXC_DESC + 'EXTERNAL_SYNC'),
   ('OTHER','기타','Other','' + EXC_DESC + 'OTHER')),
 'EVENT_SOURCE_CD': vals(('COURIER','택배사','Courier','웹훅·주기 조회 (DC-20 B)'),('ADMIN_CORRECTION','관리자 정정','Admin Correction','정정 대상·사유 필수 (세부 4-9)'),('SYSTEM','시스템','System','송장 발번·취소 등')),
 'ACCIDENT_TYPE_CD': vals(('TOTAL_LOSS','전부 멸실','Total Loss',''),('PARTIAL_LOSS','일부 멸실','Partial Loss','14일 통지 기한'),('DAMAGE','훼손','Damage','14일 통지 기한'),
   ('DELAY','연착','Delay',''),('MISDELIVERY','오배송','Misdelivery','택배사가 다른 곳에 배달. 창고가 다른 상품을 넣은 오출고는 사고가 아니라 클레임 교환(판매자 귀책) (DC-38 A)')),
 'ACCIDENT_STATUS_CD': vals(('RECEIVED','접수','Received',''),('COURIER_NOTIFIED','택배사 통지','Courier Notified',''),('COMPENSATION_CLAIMED','배상 청구','Compensation Claimed',''),
   ('COMPENSATED','배상 완료','Compensated',''),('COMPENSATION_REJECTED','배상 거절','Compensation Rejected','거절 사유 필수'),('CLOSED','종결','Closed','배상 없이 끝냄')),
 'DETECTED_BY_CD': vals(('COURIER_NOTICE','택배사 통지','Courier Notice',''),('CUSTOMER_REPORT','고객 신고','Customer Report',''),('RETURN_INSPECTION','회수 검수','Return Inspection','')),
 'COURIER_API_TYPE_CD': vals(('ISSUE_TRACKING_NO','송장 발번','Issue Tracking Number','T-6 A'),('BOOK_PICKUP','집화 접수','Book Pickup',''),('BOOK_RETURN_PICKUP','회수 접수','Book Return Pickup',''),
   ('STOP_SHIPMENT','운송 중지','Stop Shipment','출고 뒤 취소'),('CANCEL_TRACKING_NO','송장 취소','Cancel Tracking Number','DC-8 A'),('TRACKING_INQUIRY','추적 조회','Tracking Inquiry','누락 보완 주기 조회'),
   ('TRACKING_WEBHOOK','추적 수신 (웹훅)','Tracking Webhook','DC-20 B')),
 'API_CALL_RESULT_CD': vals(('SUCCESS','성공','Success',''),('FAILURE','실패 응답','Failure',''),('TIMEOUT','시간 초과','Timeout',''),('NETWORK_ERROR','통신 오류','Network Error','')),
 'SIGNATURE_VERIFICATION_RESULT_CD': vals(('VALID','일치','Valid',''),('INVALID','불일치','Invalid','이벤트를 쓰지 않음'),('NOT_APPLICABLE','해당 없음','Not Applicable','택배사가 서명을 주지 않음 [확인 필요: 택배사 API]')),
 'PII_RETENTION_REASON_CD': vals(('ORDER_TRANSACTION','거래 기록 5년 (주문 값 복사)','Order Transaction Record','전자상거래법 시행령 6조. 주문 값 복사 (DC-27 B)'),('MINOR_ORDER','미성년 주문 (주문 값 복사)','Minor Order','주문 10-2 A 계산식'),
   ('NON_ORDER_DELIVERY','비주문 출고 (배송 완료 + 1년)','Non-Order Shipment Delivery','판매 거래가 아니라 공급 기록 5년 의무가 없다는 해석. 택배사 책임 1년에 맞춤 (DC-41 A) [확인 필요: 법무]')),
}
# 다른 도메인의 코드 그룹을 그대로 쓰는 컬럼 (값 행 옆에 그룹을 적는다)
REUSE = {'DELIVERY_PLACE_CD': 'DELIVERY_PLACE (회원)', 'REMOTE_AREA_CD': 'REMOTE_AREA (주문)', 'BOX_SIZE_CD': 'BOX_SIZE (상품)'}
REUSE_NO_ROWS = {}
# 같은 이름의 코드 컬럼이 다른 테이블에 다시 나오면 두 번째부터 값 행을 접고 참조 행을 둔다 (결제 PYC-86 A, 지시 규칙 4). 재사용 그룹도 접는다.
SAME_NAME_FOLD = True

# 공통코드에 둘 정책값 (컬럼이 아니라 `CMM_CODE` 값·`ATTR`)
POLICY = [
 ('택배사 상태 코드 대응', '택배사 원래 코드를 값으로 두고 `ATTR1`에 우리 운송장 상태 코드를 적는다. 택배사가 늘면 그룹을 하나 더 만든다', 'T-2 B'),
 ('도착 보장 약정 조건', '`DELIVERY_SERVICE_TYPE_CD = GUARANTEED_ARRIVAL`의 `ATTR1` 주문 마감 시각, `ATTR2` 약정 일수, `ATTR3` 보상 방식', 'DC-4 A'),
 ('고객 도서산간 추가 배송비', '`REMOTE_AREA_CD` 값(제주, 도서산간)의 `ATTR`에 금액. 주문은 주문 때 금액을 복사한다 (주문 `REMOTE_AREA_DELIVERY_FEE_AMT`)', 'DC-18 B'),
 ('신고 가액 기준 금액', '이 금액을 넘는 박스만 신고 가액을 채운다 (지금 50만 원)', 'DC-10 B'),
 ('회수 재접수 한도', '넘으면 출고 요청 예외 수동 처리 (`PICKUP_RETRY_LIMIT_EXCEEDED`)', 'DC-22 A'),
 ('출고 마감 시각', '이 시각까지 결제된 주문을 당일 출고 대상으로 본다', '세부 1-10'),
 ('원인별 내부 목표 영업일 수', '`REQUEST_REASON_CD` 값(주문 제외)의 `ATTR1`. 요청일에 더해 `INTERNAL_SHIP_TARGET_DT`를 계산한다', 'DC-54 A'),
 ('출고 기한 임박 시간, 추적 멈춤 시간', '예외 수동 처리 사유를 켜는 기준', 'DC-25 A, 세부 4-10'),
 ('연동 로그 보관 개월', '12개월 (결제와 같음)', 'DC-19 A'),
]

CONFIRMED_GROUPS = {('DLV_SHIPMENT_REQUEST', '식별'), ('DLV_SHIPMENT_REQUEST', '상태')}
CONFIRMED_TABLES = set()
# 택배사에서 오는 값 (API 응답·웹훅·운임 계약). 정의서에서 번호를 굵게 표시한다 (결제 `PG_SOURCED`와 같은 방식).
EXTERNAL_SOURCED = {(t, c) for t, cs in [
 ('DLV_WAYBILL', 'TRACKING_NO STATUS_EVENT_OCCURRED_AT DELIVERED_AT RECEIPT_METHOD_CD DELIVERY_EVIDENCE_EVENT_CD DELIVERY_EVIDENCE_LOCATION_NM PICKED_UP_AT OUT_FOR_DELIVERY_AT'),
 ('DLV_TRACKING_EVENT', 'COURIER_EVENT_CD EVENT_OCCURRED_AT LOCATION_NM'),
 ('DLV_COURIER_RATE', 'BASE_FREIGHT_AMT SURCHARGE_FREIGHT_AMT APPLY_START_DT APPLY_END_DT'),
 ('DLV_COURIER_INTERFACE_LOG', 'COURIER_RESULT_CD COURIER_RESULT_MESSAGE_CN HTTP_STATUS_VAL'),
] for c in cs.split()}

CONFIRM = [
 ('테이블 이름', '11개 모두 후보. 다른 도메인처럼 이름 결정 질문을 거쳐 확정한다.', '전체'),
 ('송장번호 재사용', '택배사가 보존 기간(5년) 안에 송장번호를 다시 쓰지 않는지 (3-9 C). 다시 쓰면 단독 UK를 바꿔야 한다 (선행 13).', '`DLV_WAYBILL.TRACKING_NO` · 택배사 계약'),
 ('송장 API 발번', '택배사가 API 발번을 주는지 (T-6 A). 번호 대역만 주면 대역 테이블이 필요하다.', '택배사 계약'),
 ('택배사 이벤트 ID', '추적 이벤트에 택배사 이벤트 ID가 있으면 UK를 이벤트 ID로 바꾼다 (DC-13 B).', '`DLV_TRACKING_EVENT` · 택배사 API'),
 ('신고 가액 할증', '신고 가액 구간별 할증이 있는지와 기준 금액 (DC-10 B).', '`DLV_WAYBILL.DECLARED_VALUE_AMT` · 택배사 계약'),
 ('웹훅 서명', '택배사가 추적 웹훅에 서명을 주는지.', '`DLV_COURIER_INTERFACE_LOG` · 택배사 API'),
 ('출고 번호 형식', '출고일 8자리 + `-` + 6자리 순번 제안. 순번을 시퀀스로 할지 일별로 할지.', '`DLV_SHIPMENT.SHIPMENT_NO`'),
 ('출고 없는 요청의 보존 기간', '출고 없이 취소된 요청(주문 취소, 결품)을 취소일 + 5년 둘지, 주문 파기 예정일을 따를지.', '`DLV_SHIPMENT_REQUEST`'),
 ('상태 전이 (세부 4-5)', '출고 요청·출고·운송장의 허용 전이를 DB(트리거 없이 불가)로 막지 않고 애플리케이션이 검사한다는 제안. 값 목록 CK와 구분별 값 CK만 DB에 둔다.', '상태 코드 3개'),
 ('시퀀스 CACHE', '고빈도(100) 제안: 출고 요청, 요청 상품, 출고, 운송장, 추적 이벤트, 상태 이력, 연동 로그. 나머지 20.', '전체'),
 ('다른 도메인 FK', '창고·비판매 품목 마스터(WMS), 클레임·클레임 상품(CLM)은 그 도메인 설계 뒤 이름과 FK 여부를 정한다. 클레임은 값 참조(5-1 B).', '`WAREHOUSE_ID`, `NON_SALE_ITEM_ID`, `CLAIM_ID`, `CLAIM_ITEM_ID`'),
 ('택배 집화 가능 여부', '영업일 달력(시스템 도메인)에 컬럼을 더한다 (DC-26 A). 달력 소속(`SYS` / `CMM`)은 주문 1-8 A에서 미정.', '도착 예정일 계산'),
]
