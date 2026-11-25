# 주문 도메인 테이블·컬럼 정의 (제안, 확정 전)
# 근거: 주문 도메인 결정 1-1~10-11 (docs/pdf/결정/주문결정/). 테이블 이름은 모두 후보다.
# 컬럼: (물리명, 한글 논리명, 영문 논리명, 타입, NULL(N=NOT NULL, Y=허용), 기본값, 제약, 설명)
# 테이블의 cols는 [(컬럼 그룹 이름, [컬럼...]), ...] 순서 그대로가 규칙 8 순서다.
ID = 'NUMBER(19,0)'
YN = 'CHAR(1)'
TS = 'TIMESTAMP'
AMT = 'NUMBER(15)'

def yn(p, ko, en, d, desc):
    return (p, ko, en, YN, 'N', f"'{d}'", 'CK (Y/N)', desc)

def fk(p, ko, en, target, null='N', extra='', desc=''):
    return (p, ko, en, ID, null, '', f'FK → `{target}`' + (', ' + extra if extra else ''), desc)

def amt(p, ko, en, desc='', null='N', d='0', ck='CK (>= 0)'):
    return (p, ko, en, AMT, null, d, ck, desc)

T = []
def table(**kw):
    kw.setdefault('idx', []); kw.setdefault('check', []); kw.setdefault('pii', False); kw.setdefault('ldel', False)
    T.append(kw)

ITEM_STATUS = '`ORDER_ITEM_STATUS_CD` 값 목록과 같음'

# =========================================================== 장바구니
table(t='ORD_CART', ko='장바구니 상품 (SKU 단위)', en='Shopping Cart Item',
 desc='회원·비회원이 담은 상품. SKU당 1행이고 수량을 가진다. 회원 소유 목록이라 물리 삭제한다.',
 basis='2-1 A, 2-2 A, 2-3 B, 2-4 A, 2-5 A, 2-6 A, 2-7 A, 2-8 A, 선행 9·14, 컬럼 검토 OC-15 B·OC-32 B·OC-34 B·OC-35 A·OC-36 B·OC-37 B·OC-38 B·OC-44·OC-47 B·OC-48 A·OC-49 B·OC-55 B·OC-56 B', pk='대리 PK `SEQ_ORD_CART`', cache=100,
 delete='물리 삭제 (회원 소유 목록, 선행 4). 결제 완료 때 주문한 SKU 행 삭제, 보관 기간이 지나면 배치가 나눠서 삭제',
 part='없음 (10-3 A)', keep='마지막으로 담거나 바꾼 날부터 회원·비회원별 정책값 일수 (2-4 A)',
 cols=[
 ('식별·소유자', [
  ('CART_ID','장바구니 상품 고유 식별 번호','Shopping Cart Item Unique Identifier',ID,'N','','PK',''),
  fk('MEMBER_ID','장바구니 소유 회원 식별 번호','Cart Owner Member Identifier','MBR_MEMBER','Y','UK1','회원 장바구니면 채운다. 비회원 키 해시와 둘 중 정확히 하나 (선행 14).'),
  ('GUEST_CART_KEY_HASH','비회원 장바구니 키 해시','Guest Cart Key Hash','RAW(32)','Y','','UK1, IX','비회원 브라우저·앱에 발급한 무작위 키(UUID)의 SHA-256 해시. 원문은 저장하지 않는다 (선행 5 토큰 규칙, OC-15 B). 키가 충분히 무작위라 HMAC 키는 쓰지 않는다. 로그인하면 회원 행으로 옮기고 지운다 (2-2 A). 비회원 장바구니 주문이면 같은 값을 `ORD_ORDER.GUEST_CART_KEY_HASH`에 복사한다 (OC-31 B).'),
 ]),
 ('담은 상품', [
  fk('SKU_ID','담은 상품 SKU 식별 번호','Cart SKU Identifier','PRD_SKU','N','UK1','옵션을 바꾸면 UPDATE하고, 바꾼 SKU가 이미 있으면 그 행에 수량을 더한 뒤 원래 행을 지운다 (2-7 A).'),
  ('ITEM_QTY','담은 수량','Cart Item Quantity','NUMBER(2)','N','1','CK (1~99)','같은 SKU를 다시 담으면 더한다 (2-1 A). 1회 주문 한도는 주문 때 다시 검사 (8-1).'),
  amt('ADDED_SALE_PRICE_AMT','담을 때 판매가 (안내용)','Sale Price When Added (For Notice)','컬러 판매가 + SKU 추가 금액. 판매가 인하 안내용이고 주문 가격이 아니다. 옵션을 바꾸면 새 SKU의 현재 가격으로, 같은 SKU를 다시 담으면 그때 가격으로 바꾼다 (2-3 B, 2-7 A, OC-41 B).', ck='CK (>= 0, 10원 단위)'),
  amt('ADDED_DISPLAY_PRICE_AMT','담을 때 표시 가격 (즉시 할인 반영, 안내용)','Display Price When Added (For Notice)','담을 때 판매가에서 모든 고객에게 같은 즉시 할인 프로모션(타임특가 등)을 뺀 가격. 쿠폰·등급·임직원 할인과 적립금은 넣지 않는다. "담았을 때보다 n% 할인" 안내와 가격 인하 알림의 기준이다. 판매가와 바꾸는 시점이 같다 (OC-37 B, OC-41 B).', ck='CK (>= 0, <= `ADDED_SALE_PRICE_AMT`)'),
  ('ADDED_THUMBNAIL_URL','담을 때 썸네일 경로','Thumbnail Path When Added','VARCHAR2(500)','Y','','','담는 SKU 컬러의 썸네일(`PRD_STYLE_MEDIA` 유형 `THUMBNAIL`, 컬러 행이 없으면 공통 행) 저장소 상대 경로. 썸네일이 없으면 NULL. 옵션을 바꾸거나 같은 SKU를 다시 담으면 그때 썸네일로 바꾼다. 상품명·옵션명은 저장하지 않고 열 때 읽는다. 상품 쪽 파일 원본 보관(6개월, 상품 결정 44 B)보다 장바구니 보관 기간이 길면 파일이 먼저 지워질 수 있고, 그때는 화면에 "이미지 없음"으로 보인다 (OC-47 B).'),
  ('ADDED_SHIPMENT_EXPECTED_DT','담을 때 출고 예정 시작 일자','Shipment Expected Start Date When Added','DATE','Y','','','예약판매 상품이면 담을 때 상품의 `SHIPMENT_EXPECTED_DT`를 복사한다. 예약판매가 아니면 NULL. 옵션을 바꾸거나 같은 SKU를 다시 담으면 그때 값으로 바꾼다. 열 때 현재 예정일이 이 값보다 늦으면 "발송 예정일이 늦어졌어요"라고 화면에 안내한다 (알림 발송 없음). 법정 공급 시기 고지는 주문 때 한다 (3-9 A, 8-4 A, OC-55 B).'),
  ('ADDED_SHIPMENT_EXPECTED_END_DT','담을 때 출고 예정 마지막 일자','Shipment Expected End Date When Added','DATE','Y','','','"12월 2주 차부터 순차 출고" 같은 범위의 마지막 일자. 상품의 `SHIPMENT_EXPECTED_END_DT`를 복사하고, 마지막 일자만 늦어져도 안내한다. NULL이면 하루 (상품 PC-44 A, OC-56 B).'),
 ]),
 ('담은 경로', [
  ('ADDED_SOURCE_TYPE_CD','담은 경로 유형 코드','Added Source Type Code','VARCHAR2(20)','N',"'DIRECT'",'CK (값 목록)','어디에서 담았는지. 기획전별 매출과 크리에이터·제휴 수수료 정산처럼 돈이 걸린 계산에 쓴다. 검색·추천 같은 나머지 경로는 `DIRECT`로 두고 외부 분석 도구가 맡는다 (선행 12, OC-34 B, OC-35 A). 같은 SKU를 다른 경로로 다시 담으면 유형과 대상 FK를 마지막 경로로 바꾼다 (OC-44). 주문하면 주문 상품에 복사한다.'),
  ('EXHIBITION_ID','담은 기획전 식별 번호','Added Exhibition Identifier',ID,'Y','','CK (테이블 수준)','유형이 `EXHIBITION`일 때만 채운다. 기획전 테이블의 소속(전시 DSP / 프로모션 PRM)은 그 도메인을 설계할 때 정하고, 정해지면 FK를 건다 (OC-36 B, OC-45 C).'),
  ('DISPLAY_CONTENT_ID','담은 전시 콘텐츠 식별 번호','Added Display Content Identifier',ID,'Y','','CK (테이블 수준)','유형이 `CONTENT`(스냅·코디 콘텐츠)일 때만 채운다. FK는 전시 도메인 테이블이 정해지면 건다 (OC-36 B).'),
  ('AFFILIATE_ID','담은 크리에이터·제휴처 식별 번호','Added Affiliate Identifier',ID,'Y','','CK (테이블 수준)','유형이 `AFFILIATE`일 때만 채운다. 크리에이터·제휴처 마스터의 소속(SYS / STL)과 개인 크리에이터의 개인정보·원천징수는 정산 도메인을 설계할 때 정하고, 정해지면 FK를 건다 (OC-36 B, OC-46 C).'),
 ]),
 ('쿠폰 선택', [
  ('SELECTED_MEMBER_COUPON_ID','장바구니에서 고른 회원 쿠폰 식별 번호','Selected Member Coupon Identifier',ID,'Y','','UK, CK (테이블 수준)','상품 행에서 "쿠폰 사용"으로 고른 쿠폰. 고른 것을 기억할 뿐 확보가 아니고, 확보는 결제 대기 주문을 만들 때 한다 (1-4 A). 한 쿠폰을 두 행에 쓰지 못하게 단일 컬럼 UK를 건다 (NULL은 비교하지 않음). 비회원 행은 NULL. 쿠폰이 만료되거나 다른 주문에 쓰이거나 옵션을 바꾸면 NULL로 돌리고, 주문서에서 다시 검사한다. FK는 프로모션 도메인 테이블이 정해지면 건다 (OC-38 B).'),
 ]),
 ('보관 기간', [
  ('LAST_CART_ACTIVITY_AT','마지막으로 담거나 바꾼 일시','Last Cart Activity At',TS,'N','SYSTIMESTAMP','IX','보관 기간 계산 기준. 열어 보기만 한 것은 넣지 않는다 (2-4 A).'),
 ]),
 ('가격 인하 알림', [
  ('PRICE_DROP_NOTIFIED_AT','가격 인하 알림 발송 일시','Price Drop Notified At',TS,'Y','','','"담은 상품이 할인 중이에요" 알림을 보낸 시각. 광고성 정보 수신 동의(`MBR_CONSENT`, 정보통신망법 50조)가 있는 회원에게만 보낸다. 비회원 행은 보내지 않는다. 발송 기록 자체는 알림 도메인에 남는다 (OC-32 B).'),
  amt('PRICE_DROP_NOTIFIED_PRICE_AMT','가격 인하 알림 기준 표시 가격','Price Drop Notified Display Price','알림을 보낼 때의 현재 표시 가격(즉시 할인 반영). 다음 알림은 현재 표시 가격이 이 값보다 낮을 때만 보낸다. 처음 알림은 `ADDED_DISPLAY_PRICE_AMT`보다 낮을 때 보낸다. 옵션을 바꾸거나 같은 SKU를 다시 담으면 두 컬럼을 NULL로 돌린다 (OC-32 B, OC-37 B, OC-41 B).', null='Y', d=''),
 ]),
 ('재입고 알림', [
  yn('RESTOCK_REQUESTED_YN','재입고 알림 신청 여부','Restock Notification Requested Flag','N','품절 행의 "재입고 알림 신청" 버튼 표시용. 원본은 회원 도메인 `MBR_RESTOCK_NOTIFICATION_REQUEST`이고 이 값은 사본이다. 장바구니나 상품 상세에서 신청하면 같은 트랜잭션에서 Y, 신청 행이 지워지면(회원 취소, 단종, 휴면 전환, 탈퇴 확정, 발송 30일 뒤, 신청 90일 뒤) 같은 처리에서 그 회원·SKU 행을 N으로 돌린다. 옵션을 바꾸면 새 SKU로 다시 계산한다. 비회원 행은 N (신청은 회원만, 비회원이 누르면 로그인 안내, OC-49 B, OC-50 A).'),
 ]),
 ],
 idx=['UK `UK_ORD_CART_MEMBER_ID_GUEST_CART_KEY_HASH_SKU_ID` (`MEMBER_ID`, `GUEST_CART_KEY_HASH`, `SKU_ID`) (2-1 A)',
      'UK `UK_ORD_CART_SELECTED_MEMBER_COUPON_ID` (한 쿠폰은 한 행에만, OC-38 B)', 'IX `IX_ORD_CART_GUEST_CART_KEY_HASH` (비회원 조회·병합, 결제 완료 정리)', 'IX `IX_ORD_CART_LAST_CART_ACTIVITY_AT` (정리 배치, 10-5 A)', 'IX `IX_ORD_CART_SKU_ID` (FK)'],
 check=['`MEMBER_ID`와 `GUEST_CART_KEY_HASH` 중 정확히 하나만 NOT NULL (선행 14)',
        '`PRICE_DROP_NOTIFIED_AT`과 `PRICE_DROP_NOTIFIED_PRICE_AMT`는 함께 NULL이거나 함께 NOT NULL (OC-32 B)',
        '`ADDED_SOURCE_TYPE_CD`에 맞는 FK 하나만 NOT NULL: `EXHIBITION` → `EXHIBITION_ID`, `CONTENT` → `DISPLAY_CONTENT_ID`, `AFFILIATE` → `AFFILIATE_ID`, `DIRECT` → 셋 다 NULL (OC-34 B, OC-36 B)',
        '`GUEST_CART_KEY_HASH` NOT NULL이면 `SELECTED_MEMBER_COUPON_ID` IS NULL (비회원은 쿠폰 없음, OC-38 B)',
        '`GUEST_CART_KEY_HASH` NOT NULL이면 `RESTOCK_REQUESTED_YN` = N (재입고 알림은 회원만, OC-50 A)',
        '`ADDED_SHIPMENT_EXPECTED_END_DT` IS NULL 또는 `ADDED_SHIPMENT_EXPECTED_DT` NOT NULL이고 `ADDED_SHIPMENT_EXPECTED_END_DT >= ADDED_SHIPMENT_EXPECTED_DT` (OC-56 B)'])

# =========================================================== 주문
table(t='ORD_ORDER', ko='주문', en='Order',
 desc='주문 1건. "결제하기"를 누르면 결제 대기로 만들고 결제 완료·만료로 바꾼다 (3-1 A). 주문자·수령인·배송지·금액 합계·확인 기록을 둔다. 결제 뒤 금액은 바꾸지 않는다 (6-2 A).',
 basis='1-1 A, 3-1~3-9, 4-1 A, 5-4 B, 5-5 A, 5-7 A, 5-8 B, 5-10 A, 6-1 A, 6-6 A, 6-7 A, 7-1 A, 7-6 A, 7-7 A, 8-3 A, 9-1~9-5, 10-1 A, 10-6 A, 10-7 A, 10-11 A, 컬럼 검토 OC-16·OC-18~OC-20·OC-22·OC-23 A',
 pk='대리 PK `SEQ_ORD_ORDER`', cache=100,
 delete='상태 코드로 처리. 결제 만료 주문은 정책값 일수 뒤 자식 행과 함께 물리 삭제 (3-5 A). 그 밖은 주문 월 기준 10년 뒤 파티션 제거 (10-10 C). 지우기 전에 주문번호를 `SYS_RESERVED_KEY`로 옮긴다',
 part='`ORDERED_AT` 월 단위 INTERVAL (10-3 A). 자식 테이블은 참조 파티션', keep='개인정보: 거래 종료일 + 5년 (미성년 주문은 10-2 A 계산식), 행: 주문 월 + 10년', pii=True,
 cols=[
 ('식별', [
  ('ORDER_ID','주문 고유 식별 번호','Order Unique Identifier',ID,'N','','PK',''),
  ('ORDER_NO','주문번호 (고객 표시용 업무 키)','Order Number (Customer-Facing Business Key)','VARCHAR2(15)','N','','UK, CK (형식)','주문 일자 8자리 + 하이픈 + 무작위 6자리 (예: `20261124-K3F8QZ`), 하이픈 포함 15자로 저장. 무작위 부분은 영문 대문자·숫자에서 헷갈리는 글자(0, O, 1, I, L)를 뺀 31개 문자. CK 형식: `^[0-9]{8}-[2-9A-HJKMNP-Z]{6}$`. 앞 8자리는 한국 시간 기준 `ORDERED_AT`의 일자다 (OC-67 A). UK 충돌 때 다시 만든다. 재사용하지 않는다 (3-2 B, 선행 4, OC-59 A).'),
  ('ORDER_REQUEST_KEY_VAL','주문 요청 중복 방지 키','Order Request Idempotency Key Value','VARCHAR2(64)','N','','UK','주문서 화면이 발급한 무작위 값. 더블클릭·재시도로 같은 주문이 두 번 생기지 않게 한다 (3-3 A, 선행 9). 같은 키로 다시 오면 내용 해시를 비교해 같으면 기존 주문을 돌려주고 다르면 오류를 낸다 (OC-66 B).'),
  ('ORDER_REQUEST_CONTENT_HASH','주문 요청 내용 해시','Order Request Content Hash','RAW(32)','N','','','주문 요청 내용(주문 상품 SKU·수량, 선택 쿠폰, 적립금·예치금 사용액, 결제 금액)을 정해진 순서로 이어 SHA-256으로 계산한다. 서버가 다시 계산한 값이 아니라 클라이언트가 보낸 값(화면에 보인 예상 결제 금액 포함)으로 계산한다. 개인정보(배송지·연락처)는 넣지 않으므로 같은 키로 배송지만 바꾼 재시도는 기존 주문을 돌려받는다 (배송지는 결제 뒤에도 바꿀 수 있어 감수, OC-81 A). 같은 요청 키로 내용이 다른 요청을 막는 데만 쓴다 (OC-66 B).'),
  ('ORIGINAL_ORDER_ID','원주문 식별 번호','Original Order Identifier',ID,'Y','','IX (FK 없음)','가격이 다른 옵션으로 바꾸려고 부분 취소한 뒤 새로 만든 주문이면 원래 주문 ID (OC-21 A). 고객센터 연결 조회와 쿠폰·적립금 재적용 추적에 쓴다. 자기 참조 FK는 10년 파티션 제거를 막아(21c 시험: ORA-02266, 참조 행이 없어도 거부) FK 없이 둔다. 원주문이 있는지는 매일 검증 배치가 확인하고, 원주문이 파티션 제거로 지워지면 링크가 끊긴 것으로 본다 (OC-65 A → OC-77 B).'),
 ]),
 ('상태·보류', [
  ('ORDER_STATUS_CD','주문 상태 코드 (주문 상품 상태 요약)','Order Status Code (Summary of Item Statuses)','VARCHAR2(30)','N',"'PAYMENT_PENDING'",'CK (값 목록)','원천은 주문 상품 상태이고, 같은 트랜잭션에서 다시 계산한다 (7-1 A). 주문 상품 상태를 바꾸는 트랜잭션은 먼저 이 주문 행을 `SELECT … FOR UPDATE`로 잠그고, 재계산 때 `ROW_VERSION_NO`도 올린다 (OC-71 A). 값은 판정 순서(값 설명의 "판정 n") 1부터 처음 맞는 값을 쓴다. 판정 5의 진행 순서는 결제 완료 < 출고 요청 < 출고 < 배송 완료이고, 화면 정렬 번호를 판정 근거로 쓰지 않는다. 출고 요청 배치와 보류 걸기, 결제 승인 응답과 만료 배치도 이 행을 먼저 잠그고 보류 여부·상태를 다시 확인한다 (OC-71 A). 매일 검증 배치도 같은 순서로 다시 계산해 비교한다 (OC-60 C, OC-61 C, OC-62 B).'),
  ('ORDERED_AT','주문 일시','Ordered At',TS,'N','SYSTIMESTAMP','','결제 대기 주문을 만든 시각. 파티션 키 (10-3 A). 임직원 할인 연도와 구매 한도 하루의 기준 (6-9 A, 8-1 A).'),
  ('PAYMENT_DUE_AT','결제 만료 일시','Payment Due At',TS,'N','','CK (테이블 수준)','주문 일시 + 결제 수단별 기한(정책값). 가상계좌는 PG 입금 기한에 맞춘다 (3-4 A).'),
  ('PAYMENT_COMPLETED_AT','결제 완료 일시','Payment Completed At',TS,'Y','','',''),
  ('PAYMENT_EXPIRED_AT','결제 만료 처리 일시','Payment Expired At',TS,'Y','','','결제 만료 처리 일시. 기한 경과(배치), PG 승인 실패·결제 취소 확인, 같은 회원·장바구니로 새 주문을 만든 경우(이전 결제 대기 주문) 즉시 만료시킨 시각이다. 가상계좌는 실패가 확인되지 않아 기한을 기다린다. 가상계좌 주문을 새 주문으로 대체할 때는 PG에 계좌 발급 취소를 먼저 요청해 성공하면 즉시 만료시키고, 실패하면 기한까지 결제 대기로 둔다 (기한 뒤 입금은 3-4 A대로 환불, OC-80 C). 사유는 주문 상품 상태 이력의 사유 코드로 남긴다 (OC-69 B, 3-5 A). 결제 만료 주문의 보존 기산일 (10-9 B).'),
  ('HOLD_YN','주문 보류 여부 (현재)','Order Hold Flag (Current)','CHAR(1)','N','','가상 컬럼','`GENERATED ALWAYS AS (CASE WHEN HOLD_AT IS NOT NULL AND HOLD_RELEASED_AT IS NULL THEN \'Y\' ELSE \'N\' END) VIRTUAL`. 애플리케이션은 값을 쓰지 않는다 (OC-73 B). Y이면 출고하지 않는다. 상태와 따로 둔다 (7-6 A). 보류 컬럼은 마지막 보류를 남기고, 걸고 푼 기록은 모두 `ORD_ORDER_CHANGE_HIST`에 남는다 (OC-16 A, OC-72 A).'),
  ('HOLD_REASON_CD','주문 보류 사유 코드 (마지막 보류)','Order Hold Reason Code (Last Hold)','VARCHAR2(30)','Y','','CK (값 목록), CK (테이블 수준)','풀어도 지우지 않는다 (OC-72 A).'),
  ('HOLD_AT','주문 보류 일시 (마지막 보류)','Order Hold At (Last Hold)',TS,'Y','','CK (테이블 수준)','풀어도 지우지 않는다. 다시 보류하면 새 일시로 바꾼다 (OC-72 A). 보류는 출고 전 상품이 남은 주문에만 걸 수 있고, 거는 순간 애플리케이션이 검사한다 (OC-74 B).'),
  ('HOLD_RELEASED_AT','주문 보류 해제 일시 (마지막 보류)','Order Hold Released At (Last Hold)',TS,'Y','','CK (테이블 수준)','풀면 채우고, 다시 보류하면 NULL로 돌린다 (OC-72 A). 보류 중에 주문 상태가 끝 상태(완료, 전체 취소, 전체 반품, 취소·반품 종료)가 되면 같은 트랜잭션에서 자동으로 채우고 변경 이력에 사유 `ORDER_CLOSED`로 남긴다 (OC-79 A).'),
 ]),
 ('주문자', [
  fk('MEMBER_ID','주문 회원 식별 번호','Ordering Member Identifier','MBR_MEMBER','Y','IX','비회원 주문은 NULL (선행 14). 비회원 주문을 회원에 연결하면 채운다 (9-2 A). 잘못 연결된 주문은 연결 일시·방식과 함께 NULL로 되돌리고 변경 이력에 `MEMBER_UNLINK`로 남긴다. 연결된 주문에는 적립금과 등급 실적을 주지 않는다 (OC-89 A).'),
  yn('GUEST_ORDER_YN','비회원 주문 여부','Guest Order Flag','N','주문할 때 비회원이었으면 Y. 회원에 연결해도 바꾸지 않는다 (9-2 A).'),
  ('ORDERER_NM','주문자 이름','Orderer Name','VARCHAR2(150)','Y','','','평문 + TDE (선행 5, 회원 C-72). 파기·분리 보관 때 NULL.'),
  ('ORDERER_MOBILE_PHONE_NUMBER_ENC','주문자 휴대폰 번호 암호문','Orderer Mobile Phone Number Ciphertext','RAW(49)','Y','','',''),
  ('ORDERER_MOBILE_PHONE_NUMBER_HASH','주문자 휴대폰 번호 검색용 해시','Orderer Mobile Phone Number Search Hash','RAW(32)','Y','','IX','재판매 의심 합산(8-3 A). 회원 연결은 번호 재할당 때문에 CI 해시로 바꿨다 (OC-83 A). 탈퇴·파기 때 NULL로만 바꾼다 (10-11 A).'),
  ('ORDERER_EMAIL_ENC','주문자 이메일 주소 암호문','Orderer Email Address Ciphertext','RAW(283)','Y','','',''),
  ('GUEST_IDENTITY_CI_HASH','비회원 본인인증 연계 정보 해시','Guest Identity Verification CI Hash','RAW(32)','Y','','IX, CK (테이블 수준)','비회원 본인인증 CI의 HMAC-SHA256. 회원 `MBR_MEMBER.CI_HASH`와 같은 CI 전용 키를 쓰고 교체하지 않는다 (회원 C-25). '
   '회원 연결은 이 값이 회원 CI 해시와 같은 주문만 보여 준다. 번호가 바뀌거나 다른 사람에게 다시 할당돼도 정확하다. 비회원 주문이면 필수. 파기·분리 보관 때 NULL. [확인 필요: 법무, 처리방침에 이용 목적 고지] (OC-83 A).'),
  ('GUEST_IDENTITY_VERIFICATION_PROVIDER_CD','비회원 본인인증 업체 코드','Guest Identity Verification Provider Code','VARCHAR2(30)','Y','','CK (테이블 수준)','외부 업체 마스터의 업체 코드 (선행 13). 비회원 주문이면 필수 (9-1 A).'),
  ('GUEST_IDENTITY_VERIFICATION_TRANSACTION_NO','비회원 본인인증 업체 거래번호','Guest Identity Verification Transaction Number','VARCHAR2(100)','Y','','','본인인증 로그 FK가 아니다. 로그가 지워져도 업체에 다시 확인할 수 있다 (9-1 A, 회원 C-85).'),
  ('GUEST_IDENTITY_VERIFIED_AT','비회원 본인인증 완료 일시','Guest Identity Verified At',TS,'Y','','',''),
  ('GUEST_ORDER_PASSWORD_HASH','비회원 주문 조회 비밀번호 해시','Guest Order Lookup Password Hash','VARCHAR2(255)','Y','','','Argon2id (선행 14, 회원 C-70). 회원에 연결해도 그대로 둔다.'),
  ('GUEST_LOOKUP_FAIL_CNT','비회원 주문 조회 연속 실패 횟수','Guest Order Lookup Consecutive Failure Count','NUMBER(3)','N','0','CK (>= 0)','비밀번호를 틀릴 때마다 1 증가, 성공하면 0. 마지막 실패에서 정책값 초기화 시간이 지난 뒤 다시 틀리면 1부터 센다 (OC-86 A). 정책값 횟수에 이르면 잠근다 (OC-23 A, 선행 9). 이 컬럼과 마지막 실패 일시·잠금 해제 일시를 갱신할 때는 `ROW_VERSION_NO`와 `UPDATED_*`를 바꾸지 않는다 (규칙 1 예외, OC-85 A).'),
  ('GUEST_LOOKUP_LAST_FAILED_AT','비회원 주문 조회 마지막 실패 일시','Guest Order Lookup Last Failed At',TS,'Y','','','실패할 때마다 갱신한다. 이 시각에서 정책값 초기화 시간이 지나면 실패 횟수를 1부터 다시 센다. 갱신 때 행 버전·수정자를 바꾸지 않는다 (OC-86 A, OC-85 A).'),
  ('GUEST_LOOKUP_LOCKED_UNTIL_AT','비회원 주문 조회 잠금 해제 일시','Guest Order Lookup Locked Until',TS,'Y','','','이 시각 전에는 비밀번호 조회를 막고 휴대폰 인증으로만 풀 수 있다 (OC-23 A). 갱신 때 행 버전·수정자를 바꾸지 않는다 (OC-85 A).'),
  ('GUEST_PRIVACY_NOTICE_CONFIRMED_AT','비회원 개인정보 처리 고지 확인 일시','Guest Privacy Notice Confirmed At',TS,'Y','','CK (테이블 수준)','계약 이행에 필요한 개인정보라 동의가 아니라 고지다 (개인정보 보호법 15조 1항 4호, OC-20 A). 비회원 주문이면 필수. [확인 필요: 법무]'),
  ('GUEST_PRIVACY_POLICY_VER','비회원에게 고지한 개인정보 처리방침 버전','Guest Notified Privacy Policy Version','VARCHAR2(20)','Y','','CK (테이블 수준)','택배사 처리 위탁(3-7)도 이 처리방침에 공개한다.'),
  ('MEMBER_LINKED_AT','비회원 주문 회원 연결 일시','Guest Order Member Linked At',TS,'Y','','','회원 CI 해시와 비회원 CI 해시가 같은 주문만 목록에 보여 주고, 고객이 수락해야 연결한다 (9-2 A, OC-83 A로 휴대폰 해시에서 변경).'),
  ('MEMBER_LINK_METHOD_CD','비회원 주문 회원 연결 방식 코드','Guest Order Member Link Method Code','VARCHAR2(30)','Y','','CK (값 목록)','고객 수락 하나만 둔다. 번호를 바꾼 고객도 CI로 연결되므로 관리자 처리 값은 지웠다 (OC-88 B).'),
  ('GUEST_CART_KEY_HASH','비회원 장바구니 키 해시 (주문 당시)','Guest Cart Key Hash at Order','RAW(32)','Y','','','비회원이 장바구니에서 주문했을 때만 `ORD_CART.GUEST_CART_KEY_HASH`를 복사한다. 결제 완료(PG 웹훅) 때 (이 값 + 주문한 SKU)로 장바구니 행을 지운다. 회원은 `MEMBER_ID` + SKU, 바로 구매(`ORDER_ENTRY_PATH_CD` = `BUY_NOW`)는 채우지 않는다. 진입 경로가 유입 정보 테이블에 있어 채움 조건은 애플리케이션이 검사한다 (2-8 A, 2-9 A, OC-31 B). 결제 완료 때 장바구니 행을 지운 뒤, 또는 결제 만료 때 NULL로 바꾼다. 같은 브라우저의 여러 주문을 이어 볼 수 있는 값을 남기지 않는다 (OC-91 A).'),
 ]),
 ('금액·세금계산서', [
  amt('PAYMENT_AMT','최종 결제 금액','Final Payment Amount','PG 결제 금액 합계와 같다. 0원 주문은 받지 않는다 (3-8 C). 최소 결제 금액은 애플리케이션 검사. 결제 뒤에는 바꾸지 않는다 (6-2 A). 환불 합계가 이 금액을 넘지 않는지는 클레임 확정 때 주문 행을 잠그고 검사한다 (OC-95 B).', d='', ck='CK (> 0), CK (테이블 수준)'),
  amt('PRODUCT_TOTAL_AMT','상품 금액 합계','Product Amount Total','주문 상품 `PRODUCT_AMT`(단가 = 판매가 + SKU 추가 금액, × 주문 수량)의 합. 정가 기준이 아니다 (6-1 A, 6-3 A).'),
  amt('COUPON_DISCOUNT_AMT','쿠폰 할인 합계','Coupon Discount Total','출처 `COUPON` 배분 행의 합. 원천은 배분 행이고 매일 검증한다 (OC-18 A, 6-10 A).'),
  amt('PROMOTION_DISCOUNT_AMT','프로모션 할인 합계','Promotion Discount Total','출처 `PROMOTION` 배분 행의 합 (OC-18 A).'),
  amt('GRADE_DISCOUNT_AMT','등급 할인 합계','Grade Discount Total','출처 `GRADE` 배분 행의 합 (OC-18 A).'),
  amt('EMPLOYEE_DISCOUNT_AMT','임직원 할인 합계','Employee Discount Total','출처 `EMPLOYEE` 배분 행의 합. 연도 한도 행에 더한다 (6-9 A, OC-18 A).'),
  amt('POINT_USED_AMT','적립금 사용 금액','Point Used Amount','출처 `POINT_PURCHASE`·`POINT_OTHER` 배분 행의 합 (OC-18 A, OC-26 A).'),
  amt('DEPOSIT_USED_AMT','예치금 사용 금액','Deposit Used Amount','출처 `DEPOSIT` 배분 행의 합 (OC-18 A).'),
  amt('BASE_DELIVERY_FEE_AMT','기본 배송비','Base Delivery Fee','',),
  amt('REMOTE_AREA_DELIVERY_FEE_AMT','도서산간 추가 배송비','Remote Area Additional Delivery Fee'),
  amt('DELIVERY_FEE_DISCOUNT_AMT','배송비 할인 금액','Delivery Fee Discount','상품에 나누지 않는다 (6-6 A). 무료배송 기준을 넘으면 기본 배송비는 정책 금액 그대로 두고 같은 금액을 여기에 사유 `FREE_THRESHOLD`로 기록한다. 부분 반품으로 기준이 깨지면 청구할 금액이 기본 배송비에 남는다 (OC-96 A).'),
  ('DELIVERY_FEE_DISCOUNT_REASON_CD','배송비 할인 사유 코드','Delivery Fee Discount Reason Code','VARCHAR2(30)','Y','','CK (값 목록), CK (테이블 수준)','배송비 할인이 있으면 필수. 주문 하나에 출처는 하나이고, 무료배송 기준을 넘은 주문에는 무료배송 쿠폰을 쓰지 않게 애플리케이션이 막는다. 전체 취소 때 돌려줄 쿠폰, 부분 반품 때 배송비 청구 여부, 정산 부담 주체를 이 값으로 판단한다 (OC-93 A).'),
  ('DELIVERY_FEE_MEMBER_COUPON_ID','배송비 할인 회원 쿠폰 식별 번호','Delivery Fee Discount Member Coupon Identifier',ID,'Y','','CK (테이블 수준)','사유가 `COUPON`일 때만. FK는 프로모션 도메인 테이블이 정해지면 건다 (OC-10, OC-93 A).'),
  amt('FREE_DELIVERY_THRESHOLD_AMT','주문 당시 무료배송 기준 금액','Free Delivery Threshold at Order','주문 당시 무료배송 기준 (6-6 A). NULL이면 주문 당시 기준이 없었다. 비교 금액은 상품 금액 − 상품 할인(쿠폰·프로모션·등급·임직원)이고, 적립금·예치금은 결제 수단이라 빼지 않는다. 부분 반품 때도 남은 상품으로 같은 식을 쓴다 (OC-97 A).', null='Y', d=''),
  amt('RETURN_DELIVERY_FEE_AMT','주문 당시 반품 배송비 (편도)','Return Delivery Fee at Order (One Way)','주문 전에 표시한 단순 변심 반품 비용 (전자상거래법 13조, 18조 9항). 교환은 편도 × 2. 도서산간이면 `REMOTE_AREA_DELIVERY_FEE_AMT`를 더한다 [가정: 반품도 같은 추가비]. 클레임이 청구 기준으로 쓴다 (OC-94 A).'),
  amt('PG_TAXABLE_AMT','PG 요청 과세 금액 (부가세 포함)','PG Requested Taxable Amount (VAT Included)','PG 결제 요청에 보낸 과세 금액 (6-7 A). 세금 신고 기준 과세 금액이 아니다. 예치금·적립금 결제분의 과세 처리와 신고 기준 금액은 정산(`STL`)에서 계산한다 (OC-19 A). [확인 필요: 세무]'),
  amt('PG_VAT_AMT','PG 요청 부가세','PG Requested Value Added Tax Amount','PG 요청 과세 금액 × 10/110, 원 미만 버림 (6-7 A).'),
  amt('PG_TAX_EXEMPT_AMT','PG 요청 면세 금액','PG Requested Tax Exempt Amount','OC-19 A.'),
  yn('TAX_INVOICE_REQUESTED_YN','세금계산서 발급 요청 여부','Tax Invoice Requested Flag','N','사업자 고객이 사업자등록증을 제시하고 세금계산서를 요구한 주문 (부가가치세법 36조 3항, 시행령 73조 3항, OC-25 B). 소매라 원칙은 영수증이다. 카드전표·현금영수증을 이미 발급한 결제에는 발급하지 않는다 (33조 2항). 사업자등록번호·상호·대표자명, 원본·수정 발급 내역과 승인번호는 결제 도메인의 세금계산서 발급 테이블에 둔다.'),
  ('TAX_INVOICE_REQUESTED_AT','세금계산서 발급 요청 일시','Tax Invoice Requested At','TIMESTAMP','Y','','CK (테이블 수준)','요청 여부가 Y일 때만 채운다 (OC-25 B). 요청 기한(공급 시기가 속한 달의 다음 달 10일)은 공급 시기 기준을 정한 뒤 결제 도메인에서 정한다 [확인 필요: 세무].'),
 ]),
 ('배송지', [
  ('RECIPIENT_NM','수령인 이름','Recipient Name','VARCHAR2(150)','Y','','','평문 + TDE. 선물 주문은 수락 전 NULL (4-6 B). 회원 배송지를 가리키지 않고 값을 복사한다 (5-5 A). 출고 전에 바꾸면 덮어쓰고 바꾸기 전 값은 `ORD_ORDER_CHANGE_HIST`에 남긴다 (5-5 A 변경, OC-16 A).'),
  ('RECIPIENT_MOBILE_PHONE_NUMBER_ENC','수령인 휴대폰 번호 암호문','Recipient Mobile Phone Number Ciphertext','RAW(49)','Y','','',''),
  ('RECIPIENT_MOBILE_PHONE_NUMBER_HASH','수령인 휴대폰 번호 검색용 해시','Recipient Mobile Phone Number Search Hash','RAW(32)','Y','','IX','회원 배송지와 같은 정규화(숫자만)와 HMAC 키. 회원이 아닌 수령인이 열람·정정·삭제·처리정지를 요청할 때(개인정보 보호법 35~37조) 주문을 찾는 용도이고, 업무 화면 검색에는 쓰지 않는다. 선물 받는 사람 휴대폰도 수락 때 수령인으로 복사돼 함께 찾는다. 파기 때 NULL (회원 C-63 A, OC-101 A).'),
  ('POSTAL_CODE_VAL','배송지 우편번호','Delivery Postal Code','VARCHAR2(5)','Y','','CK (숫자 5자리)',''),
  ('ROAD_ADDR','배송지 도로명 주소','Delivery Road Name Address','VARCHAR2(300)','Y','','','평문 + TDE (회원 C-72).'),
  ('LOT_NUMBER_ADDR','배송지 지번 주소','Delivery Lot Number Address','VARCHAR2(300)','Y','','',''),
  ('DETAIL_ADDRESS_ENC','배송지 상세 주소 암호문','Delivery Detail Address Ciphertext','RAW(229)','Y','','',''),
  ('DELIVERY_PLACE_CD','수령 장소 코드','Delivery Place Code','VARCHAR2(20)','Y','','CK (값 목록)','회원 코드 그룹을 함께 쓴다 (5-6 A).'),
  ('ENTRANCE_ACCESS_METHOD_CD','공동현관 출입 방법 코드','Building Entrance Access Method Code','VARCHAR2(20)','Y','','CK (값 목록), CK (테이블 수준)','비밀번호 / 경비실 호출 / 자유 출입 / 기타. 비밀이 아닌 출입 방법은 암호화하지 않는다. 회원 배송지(C-59 C, 암호문 하나)도 같은 구조로 바꾼다 [회원 도메인을 다시 열 때] (OC-100 A).'),
  ('ENTRANCE_ACCESS_ENC','공동현관 출입 방법 암호문','Building Entrance Access Method Ciphertext','RAW(129)','Y','','','공동현관 비밀번호나 기타 출입 방법. 출입 방법 코드가 비밀번호·기타일 때만 채운다 (OC-100 A). 주문 상품이 모두 구매 확정되고 진행 중인 회수가 없을 때 NULL. 출고 없이 끝나면 취소·만료 때 바로 NULL (5-8 B, 회원 C-71).'),
  ('DELIVERY_REQUEST_ENC','배송 요청 사항 암호문','Delivery Request Note Ciphertext','RAW(329)','Y','','','평문 최대 300바이트. 공동현관 출입 방법 암호문과 같은 시점에 NULL로 바꾼다 (5-8 B, OC-105 A). 수령 장소가 기타이면 필수라는 검사(회원 C-60)는 일찍 지우는 값이라 애플리케이션이 한다.'),
  ('REMOTE_AREA_CD','도서산간 구분 코드 (주문 때 판단)','Remote Area Type Code (Judged at Order)','VARCHAR2(20)','Y','','CK (값 목록)','기준표는 배송 도메인. 주문에는 판단 결과만 남긴다 (5-7 A). 선물 주문은 수락 때 판단하고, 받는 사람 주소가 도서산간이면 수락을 막고 다른 주소를 안내한다 (결제 뒤 추가비를 받을 수 없음, OC-104 B). 주문 때 판단한 값으로 고정하고 출고 전 배송지를 바꿔도 고치지 않는다. 도서산간 여부가 바뀌면 차액은 결제 도메인의 추가 결제(주문 1 : 결제 N)나 부분 환불로 처리하고, 새 판단은 변경 이력과 배송 도메인 출고 기록에 남긴다 (OC-107 A, 6-2 A, OC-98 A 유지).'),
  ('LEGAL_DONG_CD','배송지 법정동 코드','Delivery Legal Dong Code','VARCHAR2(10)','Y','','CK (숫자 10자리)','주소 검색 API가 주는 법정동 코드. 시도·시군구 가상 컬럼의 원천이다 (OC-102 A).'),
  ('SIDO_CD','시도 코드 (가상)','Province Code (Virtual)','VARCHAR2(2)','Y','','가상 컬럼','`GENERATED ALWAYS AS (SUBSTR(LEGAL_DONG_CD, 1, 2)) VIRTUAL`. 지역별 매출 집계와 배송 권역에 쓴다 (5-7 A, OC-102 A). 회원 배송지는 저장형(22-3 A)이다.'),
  ('SIGUNGU_CD','시군구 코드 (가상)','District Code (Virtual)','VARCHAR2(5)','Y','','가상 컬럼','`GENERATED ALWAYS AS (SUBSTR(LEGAL_DONG_CD, 1, 5)) VIRTUAL`. 지역별 매출 집계와 배송 권역에 쓴다 (OC-102 A).'),
  ('DELIVERY_ADDRESS_HASH','정규화 배송 주소 검색용 해시','Normalized Delivery Address Search Hash','RAW(32)','Y','','IX','재판매 의심 주문 합산용 HMAC-SHA256 (8-3 A). 입력은 주소 검색 API가 준 표준 도로명 주소(건물번호까지) + 정규화한 상세 주소(공백 제거, 동·호 표기 통일). 건물관리번호는 저장하지 않는다 (회원 C-61 A, OC-99 B). 탈퇴·파기 때 NULL로만 바꾼다. [확인 필요: 처리방침 고지]'),
  ('HASH_KEY_VER','검색용 해시 계산 HMAC 키 버전','Search Hash HMAC Key Version','VARCHAR2(10)','N',"'1'",'','주문자 휴대폰 해시, 수령인 휴대폰 해시, 선물 받는 사람 휴대폰 해시, 배송 주소 해시의 HMAC 키 버전. 키를 바꾸면 네 해시를 함께 다시 계산한다. CI 해시는 교체하지 않는 전용 키라 대상이 아니다 (선행 5, 회원 C-25).'),
 ]),
 ('선물하기', [
  yn('GIFT_ORDER_YN','선물 주문 여부','Gift Order Flag','N','받는 사람이 배송지를 입력하는 주문 (4-6 B, 회원 34-3).'),
  ('GIFT_RECIPIENT_NM','선물 받는 사람 이름','Gift Recipient Name','VARCHAR2(150)','Y','','CK (테이블 수준)','보낸 사람이 입력한 이름. 평문 + TDE (회원 C-72). 선물이면 필수(파기 전). 주문 테이블에 두고 보유 기간은 주문 개인정보와 같다(거래 종료일 + 5년). 수집 근거는 보낸 사람과의 계약 이행(개인정보 보호법 15조 1항 4호)이고 출처를 통지한다 (20조 2항, OC-109 A). [확인 필요: 법무] (4-6 B 정리, OC-116 메모)'),
  ('GIFT_RECIPIENT_MOBILE_PHONE_NUMBER_ENC','선물 받는 사람 휴대폰 번호 암호문','Gift Recipient Mobile Phone Number Ciphertext','RAW(49)','Y','','CK (테이블 수준)','선물이면 필수(파기 전, OC-114 A). 수락하면 수령인 휴대폰으로 복사한다.'),
  ('GIFT_RECIPIENT_MOBILE_PHONE_NUMBER_HASH','선물 받는 사람 휴대폰 번호 검색용 해시','Gift Recipient Mobile Phone Number Search Hash','RAW(32)','Y','','IX, CK (테이블 수준)','숫자만 남기는 정규화 뒤 HMAC-SHA256 (키 버전은 `HASH_KEY_VER`). 회원 앱의 받은 선물함과 수락 전 받는 사람의 권리 요청(35~37조)에 쓴다. 파기 때 NULL (OC-110 A).'),
  ('GIFT_MESSAGE_CN','선물 메시지','Gift Message Content','VARCHAR2(200 CHAR)','Y','','','글자 단위 길이(최대 200자). 화면 안내와 같게 이 컬럼만 `CHAR` 단위로 둔다. 다른 컬럼은 바이트 단위 (OC-115 A, 공통 규칙은 확인 사항)'),
  ('GIFT_ACCEPT_TOKEN_HASH','선물 수락 링크 토큰 해시','Gift Accept Link Token Hash','RAW(32)','Y','','UK','받는 사람에게 보낸 링크의 무작위 토큰 SHA-256. 원문은 저장하지 않는다 (선행 5). 링크를 다시 보내면 덮어쓴다. 수락 전에는 배송지 입력 기한까지 유효하고, 수락 뒤에는 배송 조회만 허용한다(주소·연락처는 보여 주지 않음). 거절·기한 만료·모든 주문 상품이 끝 상태가 될 때 NULL (OC-22 A → OC-108 A).'),
  ('GIFT_ADDRESS_INPUT_DUE_AT','선물 배송지 입력 기한','Gift Address Input Due At',TS,'Y','','IX, CK (테이블 수준)','결제 완료 일시 + 정책값 일수. 링크는 결제 완료 뒤에 보낸다. 지나면 자동 취소한다 (4-6 B, OC-113 A).'),
  ('GIFT_RECIPIENT_VERIFIED_AT','선물 받는 사람 본인 확인 일시','Gift Recipient Verified At',TS,'Y','','CK (테이블 수준)','수락할 때 저장된 받는 사람 휴대폰으로 인증번호를 보내 확인한 일시 (인증 코드는 시스템 도메인 `SYS_VERIFICATION_CODE`). 수락하려면 필수 (OC-111 A).'),
  ('GIFT_ACCEPTED_AT','선물 수락 (배송지 입력) 일시','Gift Accepted At',TS,'Y','','','공급 조치 기한의 시작점 (8-4 A). 수락할 때 같은 가격의 다른 옵션으로 바꿀 수 있다 (OC-21 A 규칙, 행위자 `GUEST`, OC-116 A).'),
  ('GIFT_REJECTED_AT','선물 거절 일시','Gift Rejected At',TS,'Y','','',''),
  ('GIFT_RECIPIENT_SOURCE_NOTIFIED_AT','선물 받는 사람 개인정보 수집 출처 통지 일시','Gift Recipient Collection Source Notified At',TS,'Y','','','선물 알림에 수집 출처, 처리 목적, 처리 정지 요구권을 함께 넣어 발송에 성공한 일시. 통지 사실은 파기할 때까지 보관한다 (개인정보 보호법 20조 2항, 시행령 15조의2). [확인 필요: 법무, 의무 대상 여부와 문구] (OC-109 A)'),
  ('GIFT_LINK_SENT_CNT','선물 링크 발송 횟수','Gift Link Sent Count','NUMBER(2)','N','0','CK (>= 0)','처음 발송 포함. 정책값 최대 횟수까지만 다시 보낼 수 있다 (OC-112 A).'),
  ('GIFT_LINK_LAST_SENT_AT','선물 링크 마지막 발송 일시','Gift Link Last Sent At',TS,'Y','','','다시 보내기 최소 간격(정책값)과 기한 전 알림 일정의 기준 (OC-112 A).'),
 ]),
 ('법정 확인·고지', [
  ('ORDER_CONTENT_CONFIRMED_AT','주문 내용 확인 일시','Order Content Confirmed At',TS,'Y','','CK (테이블 수준)','결제 전 확인 절차 (전자상거래법 7조, 8조 2항). 결제 완료 이후면 NOT NULL (3-7 A).'),
  ('APPLIED_TERMS_VER','적용 이용약관 버전','Applied Terms of Service Version','VARCHAR2(20)','Y','','',''),
  ('CONTRACT_DOCUMENT_ISSUED_AT','계약 내용 서면 교부 일시','Contract Document Issued At',TS,'Y','','IX','주문 완료 메일·알림톡 발송이 성공한 시각. 청약철회 기간 시작점 (3-9 A, 전자상거래법 13조 2항, 17조 1항). 발송 기록은 `NTF`.'),
  ('CONTRACT_DOCUMENT_TEMPLATE_VER','계약 서면 양식 버전','Contract Document Template Version','VARCHAR2(20)','Y','','','서면 내용은 주문 데이터와 양식 버전으로 다시 만든다 (3-9 A).'),
  yn('MINOR_ORDER_YN','미성년 회원 주문 여부','Minor Member Order Flag','N','주문 때 생년월일로 계산. 비회원은 본인인증 결과가 만 19세 미만이면 주문할 수 없으므로(정책명세 제52조, 회원 C-85 B) 비회원 주문은 언제나 N (9-3 A).'),
  ('ADULTHOOD_DT','주문 회원 성년 도달 일자','Ordering Member Adulthood Date','DATE','Y','','CK (테이블 수준)','만 19세가 되는 날. 탈퇴 뒤에도 파기 예정일 계산에 쓴다 (9-3 A, 10-2 A).'),
  ('MINOR_CANCELLATION_RIGHT_NOTIFIED_AT','미성년자 계약 취소권 고지 일시','Minor Cancellation Right Notified At',TS,'Y','','CK (테이블 수준)','회원 C-83. 전자상거래법 13조 3항.'),
  fk('LEGAL_GUARDIAN_CONSENT_ID','근거 법정대리인 동의 식별 번호','Basis Legal Guardian Consent Identifier','MBR_LEGAL_GUARDIAN_CONSENT','Y','CK (테이블 수준)','회원 C-90.'),
  amt('GUARDIAN_MONTHLY_LIMIT_AMT','적용 법정대리인 월 구매 한도','Applied Guardian Monthly Purchase Limit','한도를 정하지 않은 동의면 NULL (9-5 B, 회원 C-95).', null='Y', d=''),
  amt('MONTH_USED_BEFORE_ORDER_AMT','이 주문 전 그 달 결제 금액 합계','Month Payment Total Before This Order','결제 대기 포함, 만료 제외, 환불 차감 (9-4 A, 9-5 B).', null='Y', d=''),
 ]),
 ('주문 당시 회원 스냅샷', [
  ('ORDER_GRADE_CD','주문 당시 회원 등급 코드','Member Grade Code at Order','VARCHAR2(30)','Y','','CK (테이블 수준)','회원 ID가 NULL이면 NULL (5-4 B).'),
  ('ORDER_MEMBER_TYPE_CD','주문 당시 회원 혜택 유형 코드','Member Benefit Type Code at Order','VARCHAR2(30)','Y','','',''),
  ('ORDER_GRADE_POINT_ACCUMULATION_RT','주문 당시 등급 기본 적립률 (퍼센트)','Grade Base Point Accumulation Rate at Order','NUMBER(5,2)','Y','','CK (0~100)',''),
  ('HEIGHT_CM_VAL','주문 당시 키 (센티미터)','Height at Order in Centimeters','NUMBER(3)','Y','','CK (100~230)','회원 체형을 주문 때 복사 (5-10 A). 탈퇴 때 NULL (회원 28-5). [확인 필요: 체형 동의 철회 때도 NULL로 바꿀지]'),
  ('WEIGHT_KG_VAL','주문 당시 몸무게 (킬로그램)','Weight at Order in Kilograms','NUMBER(3)','Y','','CK (25~250)',''),
  ('USUAL_TOP_SIZE_CD','주문 당시 평소 상의 사이즈 코드','Usual Top Size Code at Order','VARCHAR2(20)','Y','','','공통코드 `TOP_SIZE` (회원·상품 공용).'),
  ('USUAL_BOTTOM_SIZE_CD','주문 당시 평소 하의 사이즈 코드','Usual Bottom Size Code at Order','VARCHAR2(20)','Y','','','공통코드 `BOTTOM_SIZE`.'),
  ('USUAL_WAIST_SIZE_CD','주문 당시 평소 허리 사이즈 코드','Usual Waist Size Code at Order','VARCHAR2(20)','Y','','','공통코드 `WAIST_SIZE`.'),
  ('USUAL_SHOE_SIZE_CD','주문 당시 평소 신발 사이즈 코드','Usual Shoe Size Code at Order','VARCHAR2(20)','Y','','','공통코드 `SHOE_SIZE`.'),
 ]),
 ('목록 표시·행 버전', [
  ('REPRESENTATIVE_PRODUCT_NM','대표 상품명','Representative Product Name','VARCHAR2(200)','N','','','번호가 가장 빠른 주문 상품의 상품명. 취소돼도 바꾸지 않는다 (10-6 A).'),
  ('ORDER_ITEM_CNT','주문 상품 수','Order Item Count','NUMBER(3)','N','','CK (>= 1)','"외 N건" 표시용.'),
  ('REPRESENTATIVE_IMAGE_URL','대표 상품 이미지 경로','Representative Product Image Path','VARCHAR2(500)','Y','','',''),
  ('ROW_VERSION_NO','행 버전 번호','Row Version Number','NUMBER(10)','N','0','','바꿀 때마다 1 증가, `WHERE ROW_VERSION_NO = ?` 조건 (10-7 A).'),
 ]),
 ],
 idx=['UK `UK_ORD_ORDER_ORDER_NO` (GLOBAL. GLOBAL 인덱스 13개는 파티션 제거 때 `UPDATE GLOBAL INDEXES`를 붙여야 UNUSABLE이 되지 않는다, OC-67 A)', 'UK `UK_ORD_ORDER_ORDER_REQUEST_KEY_VAL` (GLOBAL)',
      'IX `IX_ORD_ORDER_MEMBER_ID_ORDERED_AT` (회원 주문 목록, LOCAL. 고객 주문 목록은 기간 선택 필수: 기본 최근 3개월, 최대 기간은 정책값, OC-90 A)', 'IX `IX_ORD_ORDER_PAYMENT_PENDING_DUE_AT` (만료 배치, 함수 기반: `CASE WHEN ORDER_STATUS_CD = \'PAYMENT_PENDING\' THEN PAYMENT_DUE_AT END`, 결제 대기 행만 담음, GLOBAL, OC-70 A, OC-78 A)',
      'IX `IX_ORD_ORDER_ORDERER_MOBILE_PHONE_NUMBER_HASH` (GLOBAL)', 'IX `IX_ORD_ORDER_DELIVERY_ADDRESS_HASH` (GLOBAL)', 'UK `UK_ORD_ORDER_GIFT_ACCEPT_TOKEN_HASH` (GLOBAL, 목록에서 빠져 있던 것을 더함)', 'IX `IX_ORD_ORDER_GIFT_RECIPIENT_MOBILE_PHONE_NUMBER_HASH` (받은 선물함, GLOBAL, OC-110 A)', 'IX `IX_ORD_ORDER_RECIPIENT_MOBILE_PHONE_NUMBER_HASH` (수령인 권리 요청, 드물어 LOCAL, OC-101 A)',
      'IX `IX_ORD_ORDER_PII_RETENTION_END_DT` (파기 배치, GLOBAL, OC-78 A)', 'IX `IX_ORD_ORDER_GIFT_PENDING_INPUT_DUE_AT` (선물 기한 배치, 함수 기반: `CASE WHEN ORDER_STATUS_CD = \'GIFT_ACCEPT_PENDING\' THEN GIFT_ADDRESS_INPUT_DUE_AT END`, OC-70 A)', 'IX `IX_ORD_ORDER_ORIGINAL_ORDER_ID` (원주문 연결 조회, FK 없음, GLOBAL, OC-77 B, OC-78 A)', 'IX `IX_ORD_ORDER_ORDER_STATUS_CD_ORDERED_AT` (관리자 상태별 목록, 기간 조건 필수, LOCAL, OC-82 A)', 'IX `IX_ORD_ORDER_HOLD_REASON_CD` (보류 목록, 함수 기반: `CASE WHEN HOLD_YN = \'Y\' THEN HOLD_REASON_CD END`, 보류 중인 행만 담음, GLOBAL, OC-75 A, OC-78 A)', 'IX `IX_ORD_ORDER_LEGAL_GUARDIAN_CONSENT_ID` (FK, GLOBAL, OC-78 A)', 'IX `IX_ORD_ORDER_GUEST_IDENTITY_CI_HASH` (회원 연결 목록, GLOBAL, OC-83 A)'],
 check=['`ORDER_STATUS_CD`가 결제 대기·결제 만료가 아니면 `ORDER_CONTENT_CONFIRMED_AT` NOT NULL (3-7 A)',
        '`GUEST_ORDER_YN` = Y이고 `PII_PURGED_AT` IS NULL이면 비회원 본인인증 3개 컬럼, `GUEST_IDENTITY_CI_HASH`, `GUEST_ORDER_PASSWORD_HASH`, 개인정보 처리 고지 2개 컬럼 NOT NULL. '
        '파기 뒤에는 NULL일 수 있다 (선행 7, 9-1 A, OC-20 A, OC-83 A, OC-84 A). [확인 필요: 분리 보관(10-11 A) 때 `PII_PURGED_AT`을 채우는지. 채우지 않으면 분리 보관 여부 조건을 더한다]',
        '`MINOR_ORDER_YN` = Y ⇔ `ADULTHOOD_DT`, `MINOR_CANCELLATION_RIGHT_NOTIFIED_AT`, `LEGAL_GUARDIAN_CONSENT_ID` NOT NULL (9-3 A)',
        '`GUARDIAN_MONTHLY_LIMIT_AMT` NOT NULL이면 `MONTH_USED_BEFORE_ORDER_AMT` NOT NULL이고 `MONTH_USED_BEFORE_ORDER_AMT + PAYMENT_AMT <= GUARDIAN_MONTHLY_LIMIT_AMT` (9-5 B)',
        '`MEMBER_ID` IS NULL이면 `ORDER_GRADE_CD`, `ORDER_MEMBER_TYPE_CD`, `ORDER_GRADE_POINT_ACCUMULATION_RT` 모두 NULL (5-4 B)',
        '`PAYMENT_AMT = PRODUCT_TOTAL_AMT − COUPON_DISCOUNT_AMT − PROMOTION_DISCOUNT_AMT − GRADE_DISCOUNT_AMT − EMPLOYEE_DISCOUNT_AMT − POINT_USED_AMT − DEPOSIT_USED_AMT + BASE_DELIVERY_FEE_AMT + REMOTE_AREA_DELIVERY_FEE_AMT − DELIVERY_FEE_DISCOUNT_AMT` (6-1 A)',
        '`DELIVERY_FEE_DISCOUNT_AMT <= BASE_DELIVERY_FEE_AMT + REMOTE_AREA_DELIVERY_FEE_AMT` (6-6 A)',
        '`COUPON_DISCOUNT_AMT + PROMOTION_DISCOUNT_AMT + GRADE_DISCOUNT_AMT + EMPLOYEE_DISCOUNT_AMT <= PRODUCT_TOTAL_AMT` (OC-98 A)',
        '`GUEST_ORDER_YN` = Y이면 `GRADE_DISCOUNT_AMT`, `EMPLOYEE_DISCOUNT_AMT`, `POINT_USED_AMT`, `DEPOSIT_USED_AMT` = 0 (주문 당시 기준, 연결과 무관, OC-98 A)',
        '`DELIVERY_FEE_DISCOUNT_AMT` > 0 ⇔ `DELIVERY_FEE_DISCOUNT_REASON_CD` NOT NULL (OC-93 A)',
        '`DELIVERY_FEE_DISCOUNT_REASON_CD` = \'COUPON\' ⇔ `DELIVERY_FEE_MEMBER_COUPON_ID` NOT NULL (OC-93 A)',
        '`DELIVERY_FEE_DISCOUNT_REASON_CD` = \'FREE_THRESHOLD\'이면 `FREE_DELIVERY_THRESHOLD_AMT` NOT NULL (OC-98 A)',
        '`REMOTE_AREA_DELIVERY_FEE_AMT` > 0 ⇔ `REMOTE_AREA_CD` NOT NULL이고 \'NONE\'이 아님 (OC-98 A)',
        '`PG_TAXABLE_AMT + PG_TAX_EXEMPT_AMT = PAYMENT_AMT` (6-7 A, OC-19 A)',
        '`PG_VAT_AMT = TRUNC(PG_TAXABLE_AMT / 11)` (10/110, 원 미만 버림, 6-7 A, OC-98 A)',
        '`HOLD_AT` NOT NULL ⇔ `HOLD_REASON_CD` NOT NULL (마지막 보류 기록, 7-6 A, OC-72 A)',
        '`HOLD_RELEASED_AT` NOT NULL이면 `HOLD_AT` NOT NULL이고 `HOLD_RELEASED_AT >= HOLD_AT` (OC-72 A). 보류 중(`HOLD_YN` = Y)이면 사유·보류 일시가 있고 해제 일시는 없다는 조건은 가상 컬럼 정의와 이 두 CHECK로 성립한다',
        '`ORDER_STATUS_CD` = \'PAYMENT_EXPIRED\' ⇔ `PAYMENT_EXPIRED_AT` NOT NULL (OC-68 A)',
        '`ORDER_STATUS_CD`가 결제 대기·결제 만료가 아니면 ⇔ `PAYMENT_COMPLETED_AT` NOT NULL (OC-68 A). 두 조건으로 결제 완료·만료 일시가 함께 채워지지 않는다',
        '`PAYMENT_DUE_AT > ORDERED_AT` (OC-68 A)',
        '`ORIGINAL_ORDER_ID <> ORDER_ID` (OC-65 A, OC-77 B)',
        '`TAX_INVOICE_REQUESTED_YN` = Y ⇔ `TAX_INVOICE_REQUESTED_AT` NOT NULL (OC-25 B)',
        '`GIFT_ORDER_YN` = N이면 선물 컬럼(받는 사람 이름·휴대폰 암호문·해시, 메시지, 토큰 해시, 기한, 본인 확인·수락·거절·통지·마지막 발송 일시) 모두 NULL, `GIFT_LINK_SENT_CNT` = 0 (OC-114 A)',
        '`GIFT_ORDER_YN` = Y이고 `PII_PURGED_AT` IS NULL이면 받는 사람 이름·휴대폰 암호문·해시 NOT NULL (4-6 B, 파기 조건 추가, OC-114 A)',
        '`GIFT_ORDER_YN` = Y이고 `PAYMENT_COMPLETED_AT` NOT NULL이면 `GIFT_ADDRESS_INPUT_DUE_AT` NOT NULL, 기한이 있으면 `GIFT_ADDRESS_INPUT_DUE_AT > PAYMENT_COMPLETED_AT` (OC-113 A)',
        '`GIFT_ACCEPTED_AT`과 `GIFT_REJECTED_AT`은 함께 NOT NULL일 수 없다 (OC-114 A)',
        '`GIFT_ACCEPTED_AT` NOT NULL이면 `GIFT_RECIPIENT_VERIFIED_AT` NOT NULL (OC-111 A)',
        '(`GIFT_ORDER_YN` = N 또는 `GIFT_ACCEPTED_AT` NOT NULL)이고 `PII_PURGED_AT` IS NULL이면 수령인 이름, 수령인 휴대폰 암호문·해시, 우편번호, 도로명 주소, 법정동 코드, 수령 장소, 도서산간 구분 NOT NULL. '
        '상세 주소는 회원 쪽도 선택이라 빼고, 공동현관·배송 요청은 일찍 지우는 값이라 뺀다 (선행 7, OC-84 A와 같은 형식, OC-103 A)',
        '`ENTRANCE_ACCESS_ENC` NOT NULL이면 `ENTRANCE_ACCESS_METHOD_CD` IN (\'PASSWORD\', \'OTHER\') (파기 뒤에는 암호문만 NULL, OC-100 A)',
        '`GUEST_ORDER_YN` = N이면 `MEMBER_ID` NOT NULL, 비회원 전용 컬럼(본인인증 3개, CI 해시, 비밀번호 해시, 고지 2개, 마지막 실패 일시, 잠금 해제 일시, 연결 일시·방식, 장바구니 키 해시) IS NULL, '
        '`GUEST_LOOKUP_FAIL_CNT` = 0 (OC-31 B, OC-84 A)',
        '`GUEST_ORDER_YN` = Y이면 `MEMBER_ID` NOT NULL ⇔ `MEMBER_LINKED_AT` NOT NULL (연결 전에는 회원 ID 없음, OC-84 A)',
        '`MEMBER_LINKED_AT`과 `MEMBER_LINK_METHOD_CD`는 함께 NULL이거나 함께 NOT NULL (9-2 A)'])

table(t='ORD_ORDER_ATTRIBUTION', ko='주문 유입 정보 (주문과 1:1)', en='Order Attribution',
 desc='주문의 판매 채널, OS, 주문 진입 경로, 요청 IP, UTM, 유입 도메인. 회원 `MBR_JOIN_ATTRIBUTION`과 같은 1:1 구조다 (주문 ID 공유 PK).',
 basis='3-6 B, 2-9 A, 선행 10·12', pk='`ORDER_ID` 공유 PK (시퀀스 없음, 10-4 A)', cache='-',
 delete='주문과 함께 처리 (결제 만료 주문 삭제, 10년 파티션 제거)', part='`ORD_ORDER` 참조 파티션 (10-3 A)', keep='주문과 같음',
 cols=[
 ('식별', [
  fk('ORDER_ID','주문 식별 번호','Order Identifier','ORD_ORDER','N','PK','주문과 1:1. [확인 필요: 규칙 5 예외 목록 추가 (결정 단계)]'),
 ]),
 ('채널·기기', [
  ('SALES_CHANNEL_CD','주문 판매 채널 코드','Order Sales Channel Code','VARCHAR2(20)','N','','CK (PC/MOBILE_WEB/APP)','선행 10.'),
  ('OS_CD','주문 기기 운영체제 코드','Order Device Operating System Code','VARCHAR2(20)','Y','','','회원 OS 코드 그룹을 함께 쓴다.'),
  ('ORDER_ENTRY_PATH_CD','주문 진입 경로 코드','Order Entry Path Code','VARCHAR2(20)','N','','CK (값 목록)','장바구니 주문 / 바로 구매 (2-9 A).'),
  ('ORDER_REQUEST_IP','주문 요청 IP 주소','Order Request IP Address','VARCHAR2(45)','Y','','','주문을 만든 요청의 IP (IPv6까지 45자). 재판매 의심 합산(8-3 A)과 결제 도용 분쟁 소명에 쓴다. 회원 도메인과 같이 평문 + TDE (선행 5). '
   '주문 일시로부터 정책값 기간(3개월)이 지나면 매일 배치가 NULL로 바꾼다 (별도 일자 컬럼 없음). [확인 필요: 법무, 보관 기간과 처리방침 고지] (OC-92 C).'),
 ]),
 ('유입', [
  ('UTM_SOURCE_VAL','주문 세션 UTM 유입 출처','Order Session UTM Source Value','VARCHAR2(200)','Y','','','선행 12.'),
  ('UTM_MEDIUM_VAL','주문 세션 UTM 유입 매체','Order Session UTM Medium Value','VARCHAR2(200)','Y','','',''),
  ('UTM_CAMPAIGN_VAL','주문 세션 UTM 캠페인','Order Session UTM Campaign Value','VARCHAR2(200)','Y','','',''),
  ('REFERRER_DOMAIN_VAL','주문 유입 사이트 도메인','Order Referrer Domain Value','VARCHAR2(255)','Y','','','전체 URL은 저장하지 않는다 (회원 20-3 B와 같음).'),
 ]),
 ])

# =========================================================== 주문 상품
table(t='ORD_ORDER_ITEM', ko='주문 상품 (SKU 단위)', en='Order Item',
 desc='주문 안의 상품. SKU당 1행과 주문 수량. 상태의 원천이고, 상품·가격 스냅샷, 결제 분담액, 클레임 수량, 공급·배송·구매 확정 시각을 둔다.',
 basis='4-2 A, 4-3 B, 1-5 A, 1-6 A, 1-7 A, 5-1 A, 5-2 C, 5-3 A, 5-9 A, 6-1 A, 6-8 A, 7-1 A, 7-2 C, 7-5 A, 7-7 A, 8-4 A, 10-7 A, 컬럼 검토 OC-18 A, OC-21 A',
 pk='대리 PK `SEQ_ORD_ORDER_ITEM`', cache=100, delete='상태 코드로 처리. 주문과 함께 삭제·파티션 제거', part='`ORD_ORDER` 참조 파티션 (10-3 A)', keep='주문과 같음',
 cols=[
 ('식별', [
  ('ORDER_ITEM_ID','주문 상품 고유 식별 번호','Order Item Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ID','주문 식별 번호','Order Identifier','ORD_ORDER','N','UK1, UK2',''),
  ('ORDER_ITEM_SN','주문 안 상품 순번','Order Item Sequence in Order','NUMBER(3)','N','','UK2, CK (>= 1)','만들 때 1부터 매기고 취소돼도 비우지 않는다 (4-3 B).'),
  ('ORDER_ITEM_NO','주문 상품 번호 (업무 키)','Order Item Number (Business Key)','VARCHAR2(18)','N','','UK','주문번호 + "-" + 순번 2자리 (예: `20261124-K3F8QZ-02`). 고객센터·창고에서 번호 하나로 찾는다 (4-3 B).'),
 ]),
 ('상품 참조', [
  fk('SKU_ID','주문 SKU 식별 번호','Ordered SKU Identifier','PRD_SKU','N','UK1','출고 요청 전에 가격이 같은 옵션으로만 바꿀 수 있다. 바꾸면 상품 스냅샷도 함께 바꾸고 바꾸기 전 값은 `ORD_ORDER_CHANGE_HIST`에 남긴다. 가격이 다르거나 바꿀 SKU가 이미 이 주문에 있으면 부분 취소 뒤 새로 주문한다 (OC-21 A).'),
  fk('STYLE_ID','주문 스타일 식별 번호','Ordered Style Identifier','PRD_STYLE','N','IX','리뷰·판매 집계용.'),
 ]),
 ('세트 묶음', [
  ('SET_GROUP_SN','세트 묶음 순번','Set Group Sequence Number','NUMBER(3)','Y','','CK (>= 1)','함께 구매 할인(상품 결정 15 D)으로 산 셋업 상품끼리 같은 번호를 준다. 같은 셋업을 2벌 사면 1, 2로 나눈다. 한 벌 단위 교환·환급(소비자분쟁해결기준 별표 2 의복류: 상하 일착은 한쪽만 이상이 있어도 일착으로 처리)과 한쪽만 반품할 때 세트 할인 환원 판단에 쓴다. 같은 번호가 2개 행 이상인지는 애플리케이션에서 검사한다 (OC-27 A).'),
 ]),
 ('담은 경로', [
  ('ADDED_SOURCE_TYPE_CD','담은 경로 유형 코드','Added Source Type Code','VARCHAR2(20)','N',"'DIRECT'",'CK (값 목록)','상품을 담은 경로. 장바구니 주문이면 장바구니 행에서 복사하고, 바로 구매면 주문 요청에서 받은 경로를 넣는다 (2-9 A). 기획전별 매출과 크리에이터·제휴 수수료 정산의 근거다 (OC-34 B, OC-35 A).'),
  ('EXHIBITION_ID','담은 기획전 식별 번호','Added Exhibition Identifier',ID,'Y','','IX, CK (테이블 수준)','유형이 `EXHIBITION`일 때만 채운다. 기획전 테이블의 소속(전시 DSP / 프로모션 PRM)은 그 도메인을 설계할 때 정하고, 정해지면 FK를 건다 (OC-36 B, OC-45 C).'),
  ('DISPLAY_CONTENT_ID','담은 전시 콘텐츠 식별 번호','Added Display Content Identifier',ID,'Y','','IX, CK (테이블 수준)','유형이 `CONTENT`(스냅·코디 콘텐츠)일 때만 채운다. FK는 전시 도메인 테이블이 정해지면 건다 (OC-36 B).'),
  ('AFFILIATE_ID','담은 크리에이터·제휴처 식별 번호','Added Affiliate Identifier',ID,'Y','','IX, CK (테이블 수준)','유형이 `AFFILIATE`일 때만 채운다. 크리에이터·제휴처 마스터의 소속(SYS / STL)과 개인 크리에이터의 개인정보·원천징수는 정산 도메인을 설계할 때 정하고, 정해지면 FK를 건다 (OC-36 B, OC-46 C).'),
 ]),
 ('상품 스냅샷', [
  ('STYLE_NO','주문 당시 품번','Style Number at Order','VARCHAR2(30)','N','','',''),
  ('STYLE_NM','주문 당시 상품명','Product Name at Order','VARCHAR2(200)','N','','',''),
  ('BRAND_NM','주문 당시 브랜드명','Brand Name at Order','VARCHAR2(100)','N','','',''),
  ('COLOR_CD','주문 당시 컬러 코드','Color Code at Order','VARCHAR2(20)','N','','',''),
  ('COLOR_DISPLAY_NM','주문 당시 컬러 표시명','Color Display Name at Order','VARCHAR2(100)','N','','',''),
  ('SIZE_CD','주문 당시 사이즈 코드','Size Code at Order','VARCHAR2(20)','N','','',''),
  ('SIZE_NM','주문 당시 사이즈 표시명','Size Display Name at Order','VARCHAR2(50)','N','','',''),
  ('SKU_CD','주문 당시 SKU 코드','SKU Code at Order','VARCHAR2(40)','N','','',''),
  ('TAXATION_TYPE_CD','주문 당시 과세 구분 코드','Taxation Type Code at Order','VARCHAR2(20)','N','','CK (값 목록)','상품 코드 그룹을 함께 쓴다.'),
  ('PRODUCT_IMAGE_URL','주문 당시 컬러 대표 이미지 경로','Color Representative Image Path at Order','VARCHAR2(500)','Y','','','5-3 A. [확인 필요: 이미지 파일 보관 (상품 도메인)]'),
  ('DISPLAY_CONTENT_HIST_ID','주문 당시 표시 내용 이력 식별 번호','Display Content History Identifier at Order',ID,'Y','','','상세 설명·고시 버전 (5-1 A, 상품 44 B). [확인 필요: FK로 걸지 참조 값으로 둘지. 표시 내용 이력은 6개월 뒤 파티션 제거]'),
 ]),
 ('청약철회 제한 고지', [
  ('WITHDRAWAL_RESTRICTION_CD','청약철회 제한 사유 코드','Withdrawal Restriction Reason Code','VARCHAR2(30)','Y','','CK (값 목록), CK (테이블 수준)','제한이 있는 상품만 (5-9 A, 상품 33 B). 상품 코드 그룹을 함께 쓴다.'),
  ('WITHDRAWAL_RESTRICTION_NOTICE_CN','청약철회 제한 고지 문구 (주문 당시 전문)','Withdrawal Restriction Notice Content at Order','VARCHAR2(2000)','Y','','CK (테이블 수준)','전자상거래법 17조 6항.'),
 ]),
 ('가격 스냅샷', [
  amt('LIST_PRICE_AMT','주문 당시 정가','List Price at Order', ck='CK (>= 0, 10원 단위)', d=''),
  amt('SALE_PRICE_AMT','주문 당시 판매가','Sale Price at Order', ck='CK (>= 0, 10원 단위)', d=''),
  amt('SKU_EXTRA_PRICE_AMT','주문 당시 SKU 추가 금액','SKU Extra Price at Order', ck='CK (>= 0, 10원 단위)'),
  fk('PRICE_HIST_ID','적용 판매가 이력 행 식별 번호','Applied Sale Price History Identifier','PRD_PRICE_HIST','N','','가격 이력은 삭제하지 않는다 (5-2 C, 상품 PC-16 A).'),
  amt('UNIT_PRICE_AMT','주문 단가','Order Unit Price','판매가 + SKU 추가 금액.', d='', ck='CK (테이블 수준)'),
 ]),
 ('수량·금액', [
  ('ORDER_QTY','주문 수량','Order Quantity','NUMBER(2)','N','','CK (1~99)',''),
  amt('PRODUCT_AMT','상품 금액','Product Amount','단가 × 수량.', d=''),
  amt('ITEM_DISCOUNT_AMT','상품 할인 배분 합계','Item Discount Allocation Total','이 상품의 배분 행 중 `POINT_PURCHASE`·`POINT_OTHER`·`DEPOSIT`을 뺀 합. 원천은 배분 행이고 매일 검증한다 (6-4 A, OC-18 A).'),
  amt('ITEM_POINT_USED_AMT','상품 적립금 사용 배분액','Item Point Used Allocation','이 상품의 `POINT_PURCHASE`·`POINT_OTHER` 배분 행의 합 (OC-18 A, OC-26 A).'),
  amt('ITEM_DEPOSIT_USED_AMT','상품 예치금 사용 배분액','Item Deposit Used Allocation','이 상품의 `DEPOSIT` 배분 행 (OC-18 A).'),
  amt('ITEM_PAYMENT_AMT','상품 결제 분담액','Item Payment Share','부분 환불 근거. 결제 뒤 바꾸지 않는다 (6-1 A, 6-2 A).', d=''),
  amt('EMPLOYEE_PURCHASE_MARKET_PRICE_AMT','임직원 구매 시가 합계','Employee Purchase Market Price Amount','임직원 할인 배분 행(`EMPLOYEE`)이 있는 상품만 주문 때 정해 저장한다. 연말 비과세 한도 = max(그해 합계 × 20%, 240만 원)이고, 취소·반품 수량만큼 빼서 계산한다 (소득세법 20조 1항 6호, 12조 3호 처목, 시행령 17조의5·38조 4항, OC-28 A). 시가는 일반 고객과의 거래 가격(법인세법 52조 2항)이다. 일반 고객도 받는 세일·프로모션을 시가에서 뺄지는 [확인 필요: 세무].', null='Y', d=''),
 ]),
 ('적립 예정', [
  ('POINT_ACCUMULATION_RT','적용 적립률 (퍼센트)','Applied Point Accumulation Rate','NUMBER(5,2)','N','0','CK (0~100)','등급 기본 + 상품별 추가 (6-8 A).'),
  amt('EXPECTED_POINT_AMT','적립 예정 금액','Expected Point Amount','결제 완료 때 원장에 "예정" 행을 만든다 (6-8 A).'),
 ]),
 ('클레임 수량', [
  ('CANCELED_QTY','취소 수량','Canceled Quantity','NUMBER(2)','N','0','CK (>= 0)','클레임 처리 트랜잭션에서 증감 (1-6 A).'),
  ('RETURNED_QTY','반품 수량','Returned Quantity','NUMBER(2)','N','0','CK (>= 0)','청약철회 반품(17조 1항·3항, 구매 확정 뒤 3개월 반품 포함)만 센다. 교환과 품질보증 기간 안 하자 환급(보증 환급)은 바꾸지 않는다 (OC-63 C, OC-64 A).'),
 ]),
 ('상태', [
  ('ORDER_ITEM_STATUS_CD','주문 상품 상태 코드','Order Item Status Code','VARCHAR2(30)','N',"'PAYMENT_PENDING'",'CK (값 목록)','정상 흐름만 둔다. 수량을 모두 채우면 끝 상태로 바꾼다 (7-2 C). [확인 필요: 값 목록 (결정 단계)]'),
  ('FINAL_STATUS_AT','끝 상태 도달 일시','Final Status Reached At',TS,'Y','','','구매 확정·취소 완료·반품 완료가 된 시각. 거래 종료일 계산 (10-9 B).'),
 ]),
 ('공급·배송', [
  ('SUPPLY_ACTION_DUE_DT','공급 조치 기한 일자','Supply Action Due Date','DATE','Y','','IX','결제 완료(선물은 수락) + 3영업일, 약정이 있으면 약정일 (8-4 A, 전자상거래법 15조 1항).'),
  ('INITIAL_PROMISED_SUPPLY_DT','최초 약정 공급 예정 일자 (예약 상품)','Initial Promised Supply Date','DATE','Y','','','예약 판매 상품만 (상품 PC-42 B).'),
  ('CURRENT_PROMISED_SUPPLY_DT','현재 약정 공급 예정 일자 (예약 상품)','Current Promised Supply Date','DATE','Y','','',''),
  ('SUPPLY_DIFFICULTY_NOTIFIED_AT','공급 곤란 통지 일시','Supply Difficulty Notified At',TS,'Y','','','전자상거래법 15조 2항. 통지 발송은 `NTF`, 환급은 클레임.'),
  ('SUPPLY_DIFFICULTY_REASON_CD','공급 곤란 사유 코드','Supply Difficulty Reason Code','VARCHAR2(30)','Y','','CK (값 목록)',''),
  ('SHIPMENT_REQUESTED_AT','출고 요청 일시','Shipment Requested At',TS,'Y','','','창고에 넘긴 시각. 공급 조치의 기록 (1-5 A).'),
  ('SHIPPED_AT','출고 일시','Shipped At',TS,'Y','','','배송 도메인이 같은 트랜잭션에서 채운다 (1-7 A).'),
  ('DELIVERED_AT','배송 완료 일시','Delivered At',TS,'Y','','','청약철회 기간·자동 구매 확정 계산 (1-7 A, 7-5 A).'),
 ]),
 ('구매 확정', [
  ('PURCHASE_CONFIRMED_AT','구매 확정 일시','Purchase Confirmed At',TS,'Y','','',''),
  ('PURCHASE_CONFIRMATION_METHOD_CD','구매 확정 방식 코드','Purchase Confirmation Method Code','VARCHAR2(20)','Y','','CK (값 목록), CK (테이블 수준)','고객 / 자동(배송 완료 + N일, 7일 이상) / 관리자 (7-5 A).'),
 ]),
 ('동시 수정 감지', [
  ('ROW_VERSION_NO','행 버전 번호','Row Version Number','NUMBER(10)','N','0','','10-7 A.'),
 ]),
 ],
 idx=['UK `UK_ORD_ORDER_ITEM_ORDER_ID_SKU_ID` (4-2 A)', 'UK `UK_ORD_ORDER_ITEM_ORDER_ID_ORDER_ITEM_SN`', 'UK `UK_ORD_ORDER_ITEM_ORDER_ITEM_NO` (GLOBAL)',
      'IX `IX_ORD_ORDER_ITEM_SUPPLY_ACTION_DUE_DT` (공급 기한 감시, 8-4 A)', 'IX `IX_ORD_ORDER_ITEM_ORDER_ITEM_STATUS_CD_DELIVERED_AT` (자동 구매 확정)',
      'IX `IX_ORD_ORDER_ITEM_SKU_ID` (FK)', 'IX `IX_ORD_ORDER_ITEM_STYLE_ID` (FK)', 'IX `IX_ORD_ORDER_ITEM_PRICE_HIST_ID` (FK)',
      'IX `IX_ORD_ORDER_ITEM_EXHIBITION_ID`, `IX_ORD_ORDER_ITEM_DISPLAY_CONTENT_ID`, `IX_ORD_ORDER_ITEM_AFFILIATE_ID` (경로별 매출·수수료 정산, FK 연결 뒤)'],
 check=['`CANCELED_QTY + RETURNED_QTY <= ORDER_QTY` (1-6 A)', '`UNIT_PRICE_AMT = SALE_PRICE_AMT + SKU_EXTRA_PRICE_AMT`, `SALE_PRICE_AMT <= LIST_PRICE_AMT` (5-2 C)',
        '`PRODUCT_AMT = UNIT_PRICE_AMT × ORDER_QTY`', '`ITEM_PAYMENT_AMT = PRODUCT_AMT − ITEM_DISCOUNT_AMT − ITEM_POINT_USED_AMT − ITEM_DEPOSIT_USED_AMT`, `ITEM_PAYMENT_AMT >= 0` (6-1 A)',
        '`WITHDRAWAL_RESTRICTION_CD`와 `WITHDRAWAL_RESTRICTION_NOTICE_CN`은 함께 NULL이거나 함께 NOT NULL (5-9 A)',
        '`PURCHASE_CONFIRMED_AT`과 `PURCHASE_CONFIRMATION_METHOD_CD`는 함께 NULL이거나 함께 NOT NULL (7-5 A)',
        '`EMPLOYEE_PURCHASE_MARKET_PRICE_AMT` NOT NULL이면 `EMPLOYEE_PURCHASE_MARKET_PRICE_AMT >= ITEM_PAYMENT_AMT` (OC-28 A)',
        '`ADDED_SOURCE_TYPE_CD`에 맞는 FK 하나만 NOT NULL: `EXHIBITION` → `EXHIBITION_ID`, `CONTENT` → `DISPLAY_CONTENT_ID`, `AFFILIATE` → `AFFILIATE_ID`, `DIRECT` → 셋 다 NULL (OC-34 B, OC-36 B)'])

table(t='ORD_ORDER_ITEM_DISCOUNT', ko='주문 상품 할인 출처별 배분', en='Order Item Discount Allocation',
 desc='주문 상품 × 할인 출처. 쿠폰·프로모션·등급·임직원 할인과 적립금·예치금 사용액을 적용 대상 상품의 금액 비율로 나눈다. 남는 금액은 금액이 가장 큰 행(같으면 번호가 빠른 행)에 더한다.',
 basis='6-4 A, 6-5 A, 선행 6·15, 컬럼 검토 OC-10, OC-18 A', pk='대리 PK `SEQ_ORD_ORDER_ITEM_DISCOUNT`', cache=100, delete='삭제하지 않음 (거래). 주문과 함께 삭제·파티션 제거', part='`ORD_ORDER_ITEM` 참조 파티션 (10-3 A)', keep='주문과 같음',
 cols=[
 ('식별', [
  ('ORDER_ITEM_DISCOUNT_ID','주문 상품 할인 배분 고유 식별 번호','Order Item Discount Allocation Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ITEM_ID','주문 상품 식별 번호','Order Item Identifier','ORD_ORDER_ITEM','N','UK1',''),
 ]),
 ('할인 출처', [
  ('DISCOUNT_SOURCE_CD','할인 출처 코드','Discount Source Code','VARCHAR2(20)','N','','UK1, CK (값 목록)','출처를 구분해 세금 계산과 부분 반품 환원에 쓴다 (6-4 A).'),
  ('MEMBER_COUPON_ID','출처 회원 쿠폰 식별 번호','Source Member Coupon Identifier',ID,'Y','','UK1, CK (테이블 수준)','출처가 `COUPON`일 때만. FK는 프로모션 도메인 테이블이 정해지면 건다 (선행 6, OC-10).'),
  ('PROMOTION_ID','출처 프로모션 식별 번호','Source Promotion Identifier',ID,'Y','','UK1, CK (테이블 수준)','출처가 `PROMOTION`일 때만. FK는 프로모션 도메인에서.'),
  fk('EMPLOYEE_ANNUAL_DISCOUNT_LIMIT_ID','출처 임직원 연도별 할인 한도 식별 번호','Source Employee Annual Discount Limit Identifier','MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT','Y','UK1, CK (테이블 수준)','출처가 `EMPLOYEE`일 때만 (6-9 A).'),
 ]),
 ('배분 금액', [
  amt('ALLOCATED_AMT','배분 금액','Allocated Amount','원 단위 (6-5 A). 주문 상품·주문의 할인·적립금·예치금 컬럼은 이 행들의 합이다 (OC-18 A).', d='', ck='CK (> 0)'),
 ]),
 ],
 idx=['UK `UK_ORD_ORDER_ITEM_DISCOUNT_SOURCE` (`ORDER_ITEM_ID`, `DISCOUNT_SOURCE_CD`, `MEMBER_COUPON_ID`, `PROMOTION_ID`, `EMPLOYEE_ANNUAL_DISCOUNT_LIMIT_ID`) (6-4 A, OC-10). Oracle은 NULL이 섞인 복합 UK도 같은 값끼리 중복으로 보므로 적립금·예치금·등급 행은 주문 상품당 1행',
      'IX `IX_ORD_ORDER_ITEM_DISCOUNT_MEMBER_COUPON_ID`', 'IX `IX_ORD_ORDER_ITEM_DISCOUNT_PROMOTION_ID`', 'IX `IX_ORD_ORDER_ITEM_DISCOUNT_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT_ID` (FK)'],
 check=['출처 코드에 맞는 FK 하나만 NOT NULL: `COUPON` → `MEMBER_COUPON_ID`, `PROMOTION` → `PROMOTION_ID`, `EMPLOYEE` → `EMPLOYEE_ANNUAL_DISCOUNT_LIMIT_ID`, `GRADE`·`POINT_PURCHASE`·`POINT_OTHER`·`DEPOSIT` → 셋 다 NULL (선행 6)'])

table(t='ORD_ORDER_ITEM_STATUS_HIST', ko='주문 상품 상태 이력', en='Order Item Status History',
 desc='주문 상품 상태가 바뀔 때마다 1행. 주문 상태 이력은 따로 두지 않는다 (7-3 C). 고치거나 지우지 않는다 (결제 만료 주문 삭제 때만 함께 삭제).',
 basis='7-3 C, 7-4 B, 선행 6·8', pk='대리 PK `SEQ_ORD_ORDER_ITEM_STATUS_HIST`', cache=100, delete='삭제하지 않음 (이력)', part='`ORD_ORDER_ITEM` 참조 파티션 (10-3 A)', keep='주문과 같음',
 cols=[
 ('식별', [
  ('ORDER_ITEM_STATUS_HIST_ID','주문 상품 상태 이력 고유 식별 번호','Order Item Status History Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ITEM_ID','주문 상품 식별 번호','Order Item Identifier','ORD_ORDER_ITEM','N','IX',''),
 ]),
 ('상태 변경', [
  ('PREVIOUS_STATUS_CD','이전 주문 상품 상태 코드','Previous Order Item Status Code','VARCHAR2(30)','Y','','CK (값 목록)','처음 만들 때 NULL. ' + ITEM_STATUS + '.'),
  ('NEW_STATUS_CD','다음 주문 상품 상태 코드','New Order Item Status Code','VARCHAR2(30)','N','','CK (값 목록)','허용되지 않은 전이는 매일 검증 배치가 찾는다 (7-4 B).'),
  ('STATUS_CHANGED_AT','상태 변경 일시','Status Changed At',TS,'N','SYSTIMESTAMP','',''),
 ]),
 ('사유', [
  ('STATUS_CHANGE_REASON_CD','상태 변경 사유 코드','Status Change Reason Code','VARCHAR2(30)','Y','','CK (값 목록)',''),
  ('STATUS_CHANGE_REASON_CN','상태 변경 상세 사유','Status Change Reason Content','VARCHAR2(1000)','Y','','',''),
  ('CLAIM_ID','관련 클레임 식별 번호','Related Claim Identifier',ID,'Y','','','클레임으로 끝 상태가 된 경우. [확인 필요: 클레임 도메인 테이블이 정해지면 FK]'),
 ]),
 ])

table(t='ORD_ORDER_FREEBIE', ko='주문 사은품', en='Order Free Gift Item',
 desc='주문 때 약속한 사은품. 비판매 품목은 재고·창고 도메인 마스터를 가리킨다. 출고 요청에 함께 넘긴다. 주문 상품 행으로 만들지 않는다.',
 basis='4-4 A, 상품 M-12 C', pk='대리 PK `SEQ_ORD_ORDER_FREEBIE`', cache=20, delete='주문과 함께 삭제·파티션 제거', part='`ORD_ORDER` 참조 파티션 (10-3 A)', keep='주문과 같음',
 cols=[
 ('식별', [
  ('ORDER_FREEBIE_ID','주문 사은품 고유 식별 번호','Order Free Gift Item Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ID','주문 식별 번호','Order Identifier','ORD_ORDER','N','IX',''),
 ]),
 ('사은품', [
  ('NON_SALE_ITEM_ID','비판매 품목 식별 번호','Non-Sale Item Identifier',ID,'N','','','[확인 필요: 재고·창고 도메인 테이블이 정해지면 FK]'),
  ('FREEBIE_QTY','사은품 수량','Free Gift Quantity','NUMBER(3)','N','1','CK (>= 1)',''),
  ('PROMOTION_ID','근거 프로모션 식별 번호','Basis Promotion Identifier',ID,'Y','','','[확인 필요: 프로모션 도메인 테이블이 정해지면 FK]'),
 ]),
 ])

# =========================================================== 주문 기록
table(t='ORD_ORDER_CHANGE_HIST', ko='주문 변경 이력 (배송지·보류·선물·회원 연결·옵션 변경)', en='Order Change History',
 desc='주문이나 주문 상품의 정보가 바뀔 때마다 1행. 상태 이력(주문 상품 상태)과 따로, 상태가 아닌 값의 변경을 남긴다. 바꾸기 전 배송지도 주문과 같은 기간 보관한다. 고치거나 지우지 않는다 (결제 만료 주문 삭제 때만 함께 삭제).',
 basis='컬럼 검토 OC-16 A (5-5 A 변경), OC-21 A, 7-6 A', pk='대리 PK `SEQ_ORD_ORDER_CHANGE_HIST`', cache=20, delete='삭제하지 않음 (이력). 개인정보는 주문과 같은 기한에 NULL', part='`ORD_ORDER` 참조 파티션 (10-3 A)', keep='개인정보: 주문과 같음, 행: 주문과 같음', pii=True,
 cols=[
 ('식별', [
  ('ORDER_CHANGE_HIST_ID','주문 변경 이력 고유 식별 번호','Order Change History Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ID','주문 식별 번호','Order Identifier','ORD_ORDER','N','IX',''),
  fk('ORDER_ITEM_ID','대상 주문 상품 식별 번호','Target Order Item Identifier','ORD_ORDER_ITEM','Y','IX, CK (테이블 수준)','옵션 변경일 때만 (OC-21 A).'),
 ]),
 ('변경 내용', [
  ('ORDER_CHANGE_TYPE_CD','주문 변경 유형 코드','Order Change Type Code','VARCHAR2(30)','N','','CK (값 목록)',''),
  ('CHANGED_AT','변경 일시','Changed At',TS,'N','SYSTIMESTAMP','',''),
  ('BEFORE_VALUE_JSON','변경 전 값 (개인정보 제외)','Before Value JSON (Excluding Personal Information)','JSON','Y','','','보류 사유 코드, 이전 SKU·사이즈·컬러 스냅샷, 연결 방식 등 개인정보가 아닌 값.'),
  ('AFTER_VALUE_JSON','변경 후 값 (개인정보 제외)','After Value JSON (Excluding Personal Information)','JSON','Y','','',''),
  ('BEFORE_PERSONAL_VALUE_ENC','변경 전 개인정보 값 암호문','Before Personal Information Value Ciphertext','RAW(1029)','Y','','','배송지 변경 때 바꾸기 전 수령인·연락처·주소·배송 요청을 JSON으로 묶어 암호화 (평문 최대 1,000바이트). 다음 값은 주문 행에 있다. 파기·분리 보관 때 NULL (10-1 A, 10-11 A).'),
 ]),
 ('사유', [
  ('CHANGE_REASON_CD','변경 사유 코드','Change Reason Code','VARCHAR2(30)','Y','','CK (값 목록)',''),
  ('CHANGE_REASON_CN','변경 상세 사유','Change Reason Content','VARCHAR2(1000)','Y','','',''),
 ]),
 ],
 check=['`ORDER_CHANGE_TYPE_CD` = `OPTION_CHANGE` ⇔ `ORDER_ITEM_ID` NOT NULL (OC-21 A)'])

table(t='ORD_ORDER_ADMIN_MEMO', ko='주문 관리자 메모', en='Order Admin Memo',
 desc='상담원·MD·창고 담당자가 주문에 남기는 내부 메모. 고객에게 보이지 않는다. 고치지 않고 새 메모로 덧붙인다.',
 basis='컬럼 검토 OC-17 A', pk='대리 PK `SEQ_ORD_ORDER_ADMIN_MEMO`', cache=20, delete='삭제하지 않음 (기록). 메모 내용은 주문과 같은 기한에 NULL', part='`ORD_ORDER` 참조 파티션 (10-3 A)', keep='개인정보: 주문과 같음, 행: 주문과 같음', pii=True,
 cols=[
 ('식별', [
  ('ORDER_ADMIN_MEMO_ID','주문 관리자 메모 고유 식별 번호','Order Admin Memo Unique Identifier',ID,'N','','PK',''),
  fk('ORDER_ID','주문 식별 번호','Order Identifier','ORD_ORDER','N','IX',''),
 ]),
 ('메모', [
  ('MEMO_CN','메모 내용','Memo Content','VARCHAR2(2000)','Y','','','고객 개인정보가 들어갈 수 있어 주문 개인정보와 같은 기한에 NULL (OC-17 A). 작성자는 시스템 컬럼 `CREATED_BY`.'),
  yn('IMPORTANT_YN','중요 메모 여부','Important Memo Flag','N','Y이면 주문 화면 위에 고정한다.'),
 ]),
 ])

table(t='ORD_GUEST_LOOKUP_FAIL_LOG', ko='비회원 주문 조회 실패 로그', en='Guest Order Lookup Failure Log',
 desc='비회원 주문 조회(주문번호 + 비밀번호)가 실패할 때마다 1행. 주문번호를 바꿔 가며 비밀번호를 시도하는 공격을 IP별로 집계해 막는다. 주문별 잠금(OC-23 A)과 함께 쓴다.',
 basis='컬럼 검토 OC-87 B, 선행 9', pk='대리 PK `SEQ_ORD_GUEST_LOOKUP_FAIL_LOG`', cache=100,
 delete='삭제하지 않음 (로그). 파티션 단위로 제거 (선행 4)', part='실패 일시 월 단위 INTERVAL 파티션. 주문을 참조하지 않는다', keep='3개월 (주문 요청 IP와 같음, OC-92 C)',
 cols=[
 ('식별', [
  ('GUEST_LOOKUP_FAIL_LOG_ID','비회원 주문 조회 실패 로그 고유 식별 번호','Guest Order Lookup Failure Log Unique Identifier',ID,'N','','PK',''),
 ]),
 ('요청', [
  ('REQUEST_IP','조회 요청 IP 주소','Lookup Request IP Address','VARCHAR2(45)','N','','IX1','IP별 실패 횟수 집계 기준. 정책값 집계 시간 안의 실패가 정책값 횟수에 이르면 그 IP의 비회원 조회를 막는다 (OC-87 B).'),
  ('FAILED_AT','조회 실패 일시','Lookup Failed At',TS,'N','SYSTIMESTAMP','IX1','파티션 키.'),
  ('LOOKUP_FAIL_REASON_CD','조회 실패 사유 코드','Lookup Failure Reason Code','VARCHAR2(30)','N','','CK (값 목록)',''),
  ('ENTERED_ORDER_NO','입력한 주문번호','Entered Order Number','VARCHAR2(30)','N','','','고객이 입력한 값 그대로 (없는 번호 포함).'),
  ('ORDER_ID','찾은 주문 식별 번호','Matched Order Identifier',ID,'Y','','','주문번호가 맞은 경우만. FK를 걸지 않는다: 주문 파티션 제거를 막지 않게 하고(OC-77 B), 이 로그가 먼저 지워진다.'),
  ('SALES_CHANNEL_CD','조회 판매 채널 코드','Lookup Sales Channel Code','VARCHAR2(20)','N','','CK (PC/MOBILE_WEB/APP)','선행 10.'),
 ]),
 ],
 idx=['IX `IX_ORD_GUEST_LOOKUP_FAIL_LOG_REQUEST_IP_FAILED_AT` (IP별 집계, LOCAL, OC-87 B)'])

TABLE_GROUPS = [
 ('장바구니', ['ORD_CART']),
 ('주문', ['ORD_ORDER', 'ORD_ORDER_ATTRIBUTION']),
 ('주문 상품', ['ORD_ORDER_ITEM', 'ORD_ORDER_ITEM_DISCOUNT', 'ORD_ORDER_ITEM_STATUS_HIST', 'ORD_ORDER_FREEBIE']),
 ('주문 기록', ['ORD_ORDER_CHANGE_HIST', 'ORD_ORDER_ADMIN_MEMO', 'ORD_GUEST_LOOKUP_FAIL_LOG']),
]

def vals(*v): return [(a, b, c, d, i) for i, (a, b, c, d) in enumerate(v, 1)]
ITEM_STATUS_VALS = vals(
 ('PAYMENT_PENDING','결제 대기','Payment Pending','재고·쿠폰·적립금 예약 중 (1-3 A, 1-4 A)'),
 ('PAYMENT_EXPIRED','결제 만료','Payment Expired','끝 상태. 예약 해제'),
 ('GIFT_ACCEPT_PENDING','선물 수락 대기','Gift Accept Pending','결제 완료, 받는 사람 배송지 입력 전 (4-6 B)'),
 ('PAID','결제 완료','Paid','출고 요청 전'),
 ('SHIPMENT_REQUESTED','출고 요청','Shipment Requested',''),
 ('SHIPPED','출고','Shipped','배송 도메인이 바꿈 (1-7 A)'),
 ('DELIVERED','배송 완료','Delivered',''),
 ('PURCHASE_CONFIRMED','구매 확정','Purchase Confirmed','끝 상태 (7-5 A). 단, 확정 뒤 표시·광고와 다른 상품의 반품(17조 3항)으로 수량이 모두 소진되면 반품 완료로 바뀐다. 품질보증 하자 환급은 상태를 바꾸지 않는다 (OC-63 C, OC-64 A)'),
 ('CANCELED','취소 완료','Canceled','끝 상태. 취소 수량 = 주문 수량 (7-2 C). 선물 거절·기한 만료 포함'),
 ('RETURNED','반품 완료','Returned','끝 상태. 취소 + 반품 수량 = 주문 수량이고 반품이 있으면 (7-2 C)'))
CODES = {
 'MEMBER_LINK_METHOD_CD': vals(('CUSTOMER_ACCEPTED','고객 수락','Customer Accepted','본인인증 CI 해시가 같은 주문 목록을 보고 수락 (9-2 A, OC-83 A)')),
 'ORDER_STATUS_CD': vals(('PAYMENT_PENDING','결제 대기','Payment Pending','판정 1: 모든 상품이 결제 대기'),
   ('PAYMENT_EXPIRED','결제 만료','Payment Expired','판정 2: 모든 상품이 결제 만료'),
   ('GIFT_ACCEPT_PENDING','선물 수락 대기','Gift Accept Pending','판정 3: 끝 상태가 아닌 상품이 모두 선물 수락 대기. 이 동안은 일부 취소를 받지 않고 전체 취소만 받는다 (OC-60 C)'),
   ('PAID','결제 완료','Paid','판정 5: 끝 상태가 아닌 상품 중 가장 덜 진행된 상품이 결제 완료'),
   ('SHIPMENT_REQUESTED','출고 준비','Shipment Requested','판정 5: 가장 덜 진행된 상품이 출고 요청'),
   ('PARTIALLY_SHIPPED','부분 배송','Partially Shipped','판정 4: 끝 상태가 아닌 상품 중 출고 전(결제 완료·출고 요청)과 출고 후(출고·배송 완료)가 섞임 (OC-61 C)'),
   ('SHIPPED','배송 중','Shipping','판정 5: 가장 덜 진행된 상품이 출고'),
   ('DELIVERED','배송 완료','Delivered','판정 5: 끝 상태가 아닌 상품이 모두 배송 완료 (구매 확정 전)'),
   ('COMPLETED','완료','Completed','판정 6: 모든 상품이 끝 상태이고 구매 확정이 하나라도 있음. 17조 3항 반품(4-41-8)으로 전체 반품·취소·반품 종료로 다시 계산될 수 있다. 거래 종료일은 10-9 B를 따른다'),
   ('ALL_CANCELED','전체 취소','All Canceled','판정 7: 모든 상품이 취소 완료 (OC-62 B)'),
   ('ALL_RETURNED','전체 반품','All Returned','판정 8: 모든 상품이 반품 완료'),
   ('CANCELED_RETURNED','취소·반품 종료','Canceled and Returned','판정 9: 나머지 (취소·반품 섞임, 구매 확정 없음)')),
 'ORDER_ITEM_STATUS_CD': ITEM_STATUS_VALS, 'PREVIOUS_STATUS_CD': ITEM_STATUS_VALS, 'NEW_STATUS_CD': ITEM_STATUS_VALS,
 'REMOTE_AREA_CD': vals(('NONE','해당 없음','None',''),('JEJU','제주','Jeju',''),('ISLAND_MOUNTAIN','도서산간 (제주 외)','Island or Mountain Area','')),
 'DELIVERY_PLACE_CD': vals(('DOOR','문 앞','Front Door','회원 코드 그룹'),('SECURITY_OFFICE','경비실','Security Office',''),('PARCEL_LOCKER','택배함','Parcel Locker',''),('IN_PERSON','직접 수령','In Person',''),('OTHER','기타','Other','배송 요청 사항 필수')),
 'HOLD_REASON_CD': vals(('RESALE_SUSPECTED','재판매 의심','Resale Suspected','8-3 A'),('PAYMENT_REVIEW','결제 확인 필요','Payment Review','PG FDS 판정 등'),('ADDRESS_CHECK','배송지 확인 필요','Address Check',''),('CUSTOMER_REQUEST','고객 요청','Customer Request',''),('OTHER','기타','Other','')),
 'SALES_CHANNEL_CD': vals(('PC','PC','PC',''),('MOBILE_WEB','모바일 웹','Mobile Web',''),('APP','앱','App','')),
 'ADDED_SOURCE_TYPE_CD': vals(('EXHIBITION','기획전','Exhibition','기획전 페이지에서 담음'),('CONTENT','스냅·코디 콘텐츠','Styling Content','전시 콘텐츠에서 담음'),('AFFILIATE','크리에이터·제휴 링크','Affiliate Link','수수료 정산 대상'),('DIRECT','직접','Direct','상품 목록·상세·검색·추천 등 나머지. 경로 분석은 외부 분석 도구 (선행 12)')),
 'LOOKUP_FAIL_REASON_CD': vals(('ORDER_NOT_FOUND','주문 없음','Order Not Found','입력한 주문번호의 비회원 주문이 없음'),('PASSWORD_MISMATCH','비밀번호 불일치','Password Mismatch',''),('LOOKUP_LOCKED','조회 잠김','Lookup Locked','주문별 잠금 중 시도 (OC-23 A)')),
 'DELIVERY_FEE_DISCOUNT_REASON_CD': vals(('FREE_THRESHOLD','무료배송 기준 충족','Free Delivery Threshold Met','기본 배송비와 같은 금액 (OC-96 A)'),('COUPON','무료배송 쿠폰','Free Delivery Coupon','쿠폰 ID 필수'),('PROMOTION','프로모션','Promotion','등급 무료배송 혜택은 프로모션 도메인에서 정하면 값 추가 (OC-93 A)')),
 'ENTRANCE_ACCESS_METHOD_CD': vals(('PASSWORD','공동현관 비밀번호','Entrance Password','암호문 필수 입력'),('CALL_SECURITY','경비실 호출','Call Security Office',''),('FREE_ACCESS','자유 출입','Free Access',''),('OTHER','기타','Other','암호문에 방법 입력')),
 'ORDER_ENTRY_PATH_CD': vals(('CART','장바구니 주문','Cart',''),('BUY_NOW','바로 구매','Buy Now','장바구니를 거치지 않음 (2-9 A)')),
 'TAXATION_TYPE_CD': vals(('TAXABLE','과세','Taxable','상품 코드 그룹'),('TAX_EXEMPT','면세','Tax Exempt','')),
 'WITHDRAWAL_RESTRICTION_CD': vals(('VALUE_DECREASE_BY_USE','사용·착용으로 가치 감소','Value Decrease by Use','상품 코드 그룹. 제한 없음(`NONE`)은 NULL로 저장')),
 'SUPPLY_DIFFICULTY_REASON_CD': vals(('OUT_OF_STOCK','재고 부족','Out of Stock',''),('PRODUCTION_DELAY','생산 지연','Production Delay','예약 상품'),('QUALITY_ISSUE','품질 문제','Quality Issue',''),('OTHER','기타','Other','')),
 'PURCHASE_CONFIRMATION_METHOD_CD': vals(('CUSTOMER','고객 확정','Customer',''),('AUTO','자동 확정','Automatic','배송 완료 + N일 (7-5 A)'),('ADMIN','관리자 확정','Admin','')),
 'DISCOUNT_SOURCE_CD': vals(('COUPON','쿠폰','Coupon',''),('PROMOTION','프로모션','Promotion',''),('GRADE','등급 할인','Grade Discount',''),('EMPLOYEE','임직원 할인','Employee Discount','6-9 A'),('POINT_PURCHASE','구매 적립 적립금 사용','Purchase-Earned Point Used','구입 실적으로 적립된 자기적립마일리지 (부가가치세법 시행령 61조 1항·2항 9호, OC-26 A)'),('POINT_OTHER','기타 적립 적립금 사용','Other-Earned Point Used','리뷰·이벤트·보상 등 구입 실적이 아닌 적립. 과세 처리는 정산에서 정한다 [확인 필요: 세무] (OC-26 A)'),('DEPOSIT','예치금 사용','Deposit Used','')),
 'STATUS_CHANGE_REASON_CD': vals(('CUSTOMER_ACTION','고객 처리','Customer Action',''),('PAYMENT_TIMEOUT','결제 기한 경과','Payment Timeout',''),('PAYMENT_FAILED','결제 실패·취소','Payment Failed or Canceled','PG 승인 실패·결제 취소 확인 즉시 만료 (OC-69 B)'),('REPLACED_BY_NEW_ORDER','새 주문으로 대체','Replaced by New Order','같은 회원·장바구니로 새 주문을 만들어 이전 결제 대기 주문 만료 (OC-69 B)'),('GIFT_TIMEOUT','선물 입력 기한 경과','Gift Timeout',''),('GIFT_REJECTED','선물 거절','Gift Rejected',''),('CLAIM_COMPLETED','클레임 완료','Claim Completed',''),('DELIVERY_UPDATE','배송 상태 반영','Delivery Update',''),('AUTO_CONFIRMATION','자동 구매 확정','Auto Confirmation',''),('ADMIN_ACTION','관리자 처리','Admin Action',''),('OTHER','기타','Other','')),
 'ORDER_CHANGE_TYPE_CD': vals(('DELIVERY_ADDRESS','배송지 변경','Delivery Address Change','출고 요청 전. 바꾸기 전 값은 암호문'),('HOLD','보류','Hold','7-6 A'),('HOLD_RELEASE','보류 해제','Hold Release',''),('GIFT_ACCEPT','선물 수락','Gift Accept','받는 사람 배송지 입력'),('GIFT_REJECT','선물 거절','Gift Reject',''),('MEMBER_LINK','비회원 주문 회원 연결','Member Link','9-2 A'),('MEMBER_UNLINK','비회원 주문 회원 연결 취소','Member Unlink','잘못 연결된 주문을 되돌림 (OC-89 A)'),('OPTION_CHANGE','옵션 변경','Option Change','출고 전, 같은 가격 (OC-21 A)')),
 'CHANGE_REASON_CD': vals(('CUSTOMER_REQUEST','고객 요청','Customer Request',''),('RESALE_SUSPECTED','재판매 의심','Resale Suspected',''),('PAYMENT_REVIEW','결제 확인','Payment Review',''),('ADDRESS_CHECK','배송지 확인','Address Check',''),('ADMIN_ACTION','관리자 처리','Admin Action',''),('OTHER','기타','Other',''),('ORDER_CLOSED','주문 종료로 자동 해제','Released on Order Close','보류 중 주문이 끝 상태가 되어 자동 해제 (OC-79 A)')),
 'PII_RETENTION_REASON_CD': vals(('ORDER_TRANSACTION','거래 기록 5년','Order Transaction Record','전자상거래법 시행령 6조 1항 2·3호, 기산일 = 거래 종료일 (10-9 B)'),('MINOR_ORDER','미성년 주문','Minor Order','10-2 A 계산식'),('EXPIRED_ORDER','결제 만료 주문','Expired Order','정책값 일수 (3-5 A)')),
}
REUSE = {'DELIVERY_PLACE_CD': 'DELIVERY_PLACE', 'TAXATION_TYPE_CD': 'TAXATION_TYPE (상품)', 'WITHDRAWAL_RESTRICTION_CD': 'WITHDRAWAL_RESTRICTION (상품)'}

CONFIRMED_GROUPS = {('ORD_CART', g) for g in ('식별·소유자', '담은 상품', '담은 경로', '쿠폰 선택', '보관 기간', '가격 인하 알림', '재입고 알림')} | {('ORD_ORDER', '식별'), ('ORD_ORDER', '상태·보류'), ('ORD_ORDER', '주문자'), ('ORD_ORDER', '금액·세금계산서'), ('ORD_ORDER', '배송지'), ('ORD_ORDER', '선물하기')}  # 2026-11-25 사용자 지시: 장바구니 컬럼 확정, 주문 식별·상태·보류·주문자·금액·세금계산서·배송지·선물하기 그룹 확정
CONFIRMED_TABLES = set()

CONFIRM = [
 ('테이블 이름', '10개 모두 후보. 상품 도메인처럼 이름 결정 질문을 거쳐 확정한다.', '전체'),
 ('결정 단계 미정 사항', '선물하기 세부(한정판 제외, 공급 시기 약정, 철회·교환 주체), 표시 내용 이력 FK, 배송 요청 문구 파기 시점, 체형 동의 철회, 상태 값 목록, 반품 수량 한도 포함 여부 등은 `주문_컬럼검토_결정.pdf`의 OC 질문으로 정한다.', 'OC 질문'),
 ('영업일 달력', '"3영업일" 계산용 영업일 달력 테이블(1-8 A)은 주문 도메인 테이블이 아니다. 소속(`SYS` / `CMM`)을 정한 뒤 그 도메인에 둔다.', 'SYS 또는 CMM'),
 ('다른 도메인 FK', '`CLAIM_ID`, `NON_SALE_ITEM_ID`, `PROMOTION_ID`(사은품·할인 배분), `MEMBER_COUPON_ID`, 주문 `DELIVERY_FEE_MEMBER_COUPON_ID`, 장바구니 `SELECTED_MEMBER_COUPON_ID`, 장바구니·주문 상품의 `EXHIBITION_ID`·`DISPLAY_CONTENT_ID`·`AFFILIATE_ID`는 해당 도메인 테이블이 정해지면 FK로 건다.', 'CLM, WMS, PRM, DSP'),
 ('기획전·제휴처 소속', '기획전 테이블의 소속(DSP / PRM)은 전시·프로모션 도메인을 설계할 때 정한다 (OC-45 C). 크리에이터·제휴처 마스터의 소속(SYS / STL)과 개인 크리에이터의 개인정보 항목·보유 기간·원천징수(세무 확인)는 정산 도메인을 설계할 때 정한다 (OC-46 C).', 'DSP, PRM, SYS, STL'),
 ('회원 배송지 다시 열 때', '공동현관 출입 방법 코드 추가(C-59 C 변경, OC-100 A). 시도·시군구 저장형(22-3 A)을 주문처럼 가상 컬럼으로 바꿀지 확인 (OC-102 A).', '회원 `MBR_DELIVERY_ADDRESS`'),
 ('도착 보장 배송', '주문 상품에 배송 서비스 유형 코드(일반 / 도착 보장)를 둔다 (OC-106 A). 주문 상품 그룹을 검토할 때 컬럼으로 정하고, 택배사 도착 보장 약정과 지연 보상은 배송 도메인에서 정한다.', '`ORD_ORDER_ITEM`, 배송 `DLV`'),
 ('재입고 알림 신청 경로', '회원 도메인 `MBR_RESTOCK_NOTIFICATION_REQUEST`에 신청 경로 코드(`PRODUCT_DETAIL` / `CART` / `WISHLIST`)를 추가하기로 했다 (OC-51 B). 다시 신청하면 마지막 경로로 바꾼다 (OC-53 A). 확정된 회원 문서는 회원 도메인을 다시 열 때 함께 고친다 (OC-52 B). 그때 신청 행 삭제 처리 6곳에 장바구니 `RESTOCK_REQUESTED_YN` 갱신도 적는다 (OC-49 B).', '회원 MBR'),
 ('세트 할인 조건', '장바구니는 세트로 담았는지 기억하지 않는다 (OC-33 A). 함께 구매 할인을 "짝이 맞으면 자동 할인"으로 정한다는 전제다. 프로모션 도메인에서 "세트로 담아야 할인"으로 정하면 OC-33을 다시 연다.', '프로모션 PRM'),
 ('`SYS_PII_ARCHIVE` 주문 대상 FK', '탈퇴 회원 주문 개인정보를 옮길 때 주문을 가리키는 대상 FK가 필요하다 (10-11 A). 시스템 도메인에서 설계한다.', '`SYS_PII_ARCHIVE`'),
 ('정책값', '장바구니 보관 일수(회원·비회원), 장바구니 행 수 상한, 결제 수단별 결제 기한, 결제 만료 주문 보관 일수, 자동 구매 확정 일수(7일 이상), 최소 결제 금액, 재판매 탐지 기준 수량·기간.', '`CMM_CODE` 주문 정책 그룹'),
 ('세금 신고 기준 금액', '주문에는 PG 요청 과세 금액만 둔다 (OC-19 A). 예치금·적립금 결제분과 쿠폰의 과세 처리, 신고 기준 금액 계산은 정산 도메인에서 세무 확인 뒤 정한다.', '정산 `STL`'),
 ('금액 일치 검증', '배분 행이 원천이다 (OC-18 A). 매일 검증: 주문 상품 할인 = 배분 행(`POINT_PURCHASE`·`POINT_OTHER`·`DEPOSIT` 제외) 합, 주문 상품 적립금·예치금 = 해당 배분 행, 주문 출처별 합계 = 해당 출처 배분 행 합, 주문 합계 = 주문 상품 합.', '6-10 검증 배치'),
 ('교환 뒤 받은 사이즈', '리뷰의 사이즈 스냅샷은 마지막으로 끝난 교환의 새 SKU, 없으면 주문 상품 SKU에서 가져온다. 클레임·리뷰 도메인에서 정한다.', 'CLM, RVW'),
 ('세금계산서 발급 테이블', '발급 내역(원본·수정 구분, 사업자등록번호, 상호, 대표자명, 받을 이메일, 승인번호, 국세청 전송 일시)은 결제 도메인에 주문 1 : 발급 N으로 둔다. 카드전표·현금영수증과 중복 발급 금지 검사도 결제 도메인에서 한다 (OC-25 B).', '결제 `PAY`'),
 ('현금영수증 의무 발행', '의복·신발·가방·의복 액세서리를 파는 전자상거래 소매업은 현금영수증 의무 발행 업종이다 (소득세법 시행령 별표 3의3 5호·6호). 건당 10만 원 이상 현금 결제는 요청이 없어도 5일 안에 발급(무기명 가능)하고, 요청하면 1원 이상 발급한다 (법인세법 117조의2, 시행령 159조의2). 미발급 가산세 20% (75조의6). 결제 도메인에 요청 유형, 식별번호 암호문, 발급 기한·일시, 승인번호, 취소 기록과 미발급 감시 배치를 둔다. 예치금 사용분을 현금 대금으로 볼지는 [확인 필요: 세무].', '결제 `PAY`'),
 ('품질보증기간과 감가', '의류 1년(별표 3 6호 기본값), 신발은 가죽 60% 이상 1년·그 외 6개월, 우산류 1개월 (소비자분쟁해결기준 별표 3). 기간 안에는 구입가 환급, 지나면 세탁업 배상비율표 내용연수로 감가한다. 상품 분류의 보증기간·내용연수 구분과 신발 가죽 비율 판단, 기산일(배송 완료 / 주문)을 정해야 한다. 산 지 2년 안의 의류는 판매자가 품질이 정상임을 입증한다 (별표 2 의복류).', '상품 `PRD`, 클레임 `CLM`'),
 ('임원 할인과 연도 기준', '임원은 특수관계인이라 저가 판매가 부당행위계산 부인(법인세법 52조) 대상인지 [확인 필요: 세무]. 회원 임직원 연도별 할인 테이블의 연도가 소득세 과세기간(1~12월)과 같은지 확인한다. 재판매 1년 금지(소득세법 시행령 17조의5 2항 3호)는 임직원 할인 약관과 재판매 탐지(8-3 A)의 근거다.', '회원 `MBR`, 관리자 `ADM`'),
 ('적립금 원장 적립 사유', '배분 때 구매 적립분과 기타 적립분을 나누려면 적립금 원장의 적립 건마다 구입 실적 적립인지 구분하는 값이 있어야 한다 (OC-26 A).', '적립금 원장 도메인'),
 ('공급 시기와 임직원 할인 과세', '공급 시기(부가가치세법 15조: 인도되는 때)로 출고 일시와 배송 완료 일시 중 무엇을 쓸지, 임직원 할인 차액의 과세 여부(10조 4항, 29조 4항)와 기타 적립분 결제의 과세 처리. [확인 필요: 세무]', '정산 `STL`'),
 ('정책값 추가', '선물 배송지 입력 기한 일수(결제 완료 기준, OC-113 A), 선물 링크 최대 발송 횟수와 최소 간격 (OC-112 A). 비회원 주문 조회 잠금 실패 횟수와 잠금 시간 (OC-23 A), 실패 횟수 초기화 시간 (OC-86 A), IP별 조회 실패 허용 횟수와 집계 시간 (OC-87 B), 주문 요청 IP 보관 기간 3개월 (OC-92 C), 고객 주문 목록 최대 조회 기간 (OC-90 A). 비회원 키당 장바구니 행 수 상한 (회원과 따로, OC-40 A).', '`CMM_CODE` 주문 정책 그룹'),
 ('재판매 탐지 고지', '정규화 주소 해시를 쓰는 목적을 개인정보 처리방침에 적을지.', '`DELIVERY_ADDRESS_HASH`'),
]
