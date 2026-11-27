# 용어집 생성기 (2026-11-27). DB 용어집과 업무 용어집을 따로 만든다 (사용자 결정 1 C, 2 A).
# 2026-11-21 원본 1~6장과 2026-11-25 추가 7장(스크립트 없음)의 31개를 이 파일로 옮기고 주제별로 다시 묶었다.
# 사용: python3 gen.py <db|biz> <출력.html>  → Chrome headless로 PDF (A4 가로)
#   db  → docs/pdf/용어집/DB용어집.pdf,  biz → docs/pdf/용어집/업무용어집.pdf
# 항목: (용어, 한글명, 영문명, 뜻, 이 프로젝트 규칙, 예시). 근거 번호는 도메인 이름을 붙인다 (숫자만 있으면 회원 결정).
import sys, re, html

DB = [
('키와 제약조건', [
 ('PK', '기본 키', 'Primary Key',
  '테이블에서 행 하나를 유일하게 가리키는 컬럼(또는 컬럼 그룹). NULL을 허용하지 않고 값이 겹칠 수 없다. 테이블마다 1개다.',
  '컬럼 이름 `{엔티티}_ID`, 타입 `NUMBER(19,0)`. 제약 이름 `PK_{테이블}` (선행 1, 3). 항상 첫 컬럼이다 (규칙 8-B).',
  '`MBR_MEMBER.MEMBER_ID` / `PK_MBR_MEMBER`'),
 ('FK', '외래 키', 'Foreign Key',
  '다른 테이블의 PK(또는 UK) 값을 가리키는 컬럼. 가리키는 행이 없으면 값을 넣을 수 없어 테이블 사이 관계를 보장한다.',
  '컬럼 이름은 참조하는 PK와 같게 쓴다. 제약 이름 `FK_{테이블}_{FK컬럼}`. 자식이 있는 부모는 삭제할 수 없다 (선행 3, 4). 파티션 제거를 막는 곳에는 FK 대신 값 참조를 쓴다.',
  '`MBR_LOGIN_ACCOUNT.MEMBER_ID` → `MBR_MEMBER`'),
 ('UK', '고유 키 (유니크 제약)', 'Unique Key',
  'PK가 아닌 컬럼에 값이 겹치지 않도록 거는 제약. PK와 달리 NULL을 허용한다. Oracle에서 여러 행의 NULL은 서로 겹치지 않는 것으로 보지만, 복합 UK에서 일부 컬럼만 NULL이면 나머지 값이 같을 때 중복으로 본다.',
  '제약 이름 `UK_{테이블}_{컬럼}`. 재사용 금지 값(회원번호, 업무 코드)과 업무 키에 건다 (선행 1, 3, 4).',
  '`UK_MBR_MEMBER_MEMBER_NO`, `UK_MBR_MEMBER_CI_HASH`'),
 ('CK', '체크 제약', 'Check Constraint',
  '컬럼에 들어갈 수 있는 값의 조건을 DB가 검사하는 제약. 조건이 거짓이면 막고, 비교 대상이 NULL이라 결과가 UNKNOWN이면 통과시킨다. NULL을 막으려면 `IS NOT NULL`을 따로 적어야 한다.',
  '제약 이름 `CK_{테이블}_{컬럼}`. Y/N, 행위자 유형, 상태처럼 로직이 걸린 코드에 건다 (규칙 4, 선행 2, 8). NULL 허용 컬럼을 비교하는 CHECK는 NULL일 때 막는지 통과시키는지 정의서 문장에 적고, 일괄 NVL은 쓰지 않는다 (결제 PYC-80 A).',
  '`CK_MBR_MEMBER_MEMBER_STATUS_CD` (6개 상태만 허용)'),
 ('복합 PK', '복합 기본 키', 'Composite Primary Key',
  '컬럼 2개 이상을 묶어 PK로 쓰는 방식. 묶은 값 전체가 유일하다.',
  '다른 테이블이 참조하지 않는 단순 연결(매핑) 테이블에만 쓴다 (선행 1).',
  '`MBR_MEMBER_TAG` (`MEMBER_ID`, `TAG_ID`)'),
 ('대리 PK', '대리 기본 키', 'Surrogate Primary Key',
  '업무 의미가 없는 일련번호를 PK로 쓰는 방식. 업무 값이 바뀌어도 PK는 바뀌지 않는다.',
  '프로젝트 기본 방식. 테이블별 시퀀스로 채번한다. 행이 참조되거나 이력·상태·차수를 가지는 매핑도 대리 PK + 복합 UK로 둔다 (선행 1).',
  '`MBR_PREFERENCE.PREFERENCE_ID`'),
 ('업무 키', '업무 식별 키', 'Business Key',
  '업무에서 사람이 쓰는 식별 값. PK와 별도로 UK를 걸어 유일성을 보장한다.',
  '컬럼 분류어 `_NO`. 업무상 식별 가치가 있는 테이블에만 둔다 (선행 1, 3).',
  '`MEMBER_NO` (M + 숫자 10자리), `ORDER_NO`'),
 ('공유 PK', '공유 기본 키', 'Shared Primary Key',
  '1:1 자식 테이블이 부모의 PK를 자기 PK이자 FK로 그대로 쓰는 방식. 부모 1행에 자식은 최대 1행이다.',
  '테이블 최소화(규칙 5)의 예외로만 쓴다: 가입 유입 경로(회원 C-20·C-21), 주문 유입 정보(주문 3-6 B).',
  '`MBR_JOIN_ATTRIBUTION.MEMBER_ID`, `ORD_ORDER_ATTRIBUTION.ORDER_ID`'),
 ('복합 FK → 부모 UK', '복합 외래 키', 'Composite Foreign Key to Parent Unique Key',
  '부모에 (PK, 다른 컬럼) UK를 걸고, 자식의 두 컬럼이 함께 그 UK를 가리키는 FK. 자식에 복사한 값이 부모 값과 항상 같다.',
  '자식 행의 CHECK가 부모 행의 값에 따라 달라져야 할 때 쓴다 (배송 DC-5 A 후속). 회원의 기본 배송지도 복합 FK로 그 회원의 배송지만 가리킨다 (회원 C-47).',
  '요청 상품 (`SHIPMENT_REQUEST_ID`, `REQUEST_REASON_CD`) → 출고 요청 UK'),
 ('값 참조', '제약 없는 참조', 'Reference Without Constraint',
  'FK 제약 없이 다른 테이블의 ID만 컬럼에 두고 인덱스를 거는 방식. DB는 가리키는 행이 있는지 검사하지 않는다.',
  '다른 도메인의 파티션 제거(ORA-02266)를 막지 않으려고 결제의 원장·로그·대사 테이블, 배송의 주문·클레임 ID에 쓴다 (결제 11-1, 배송 5-1 B). 존재 검증은 배치가 한다. 정의서는 `ref()`로 표시하고 ERD에는 그리지 않는다.',
  '결제 원장의 `ORDER_ID`'),
]),
('인덱스', [
 ('IX', '인덱스', 'Index',
  '조회를 빠르게 하려고 컬럼 값을 정렬해 따로 저장한 구조. 제약은 아니며 값의 유일성을 보장하지 않는다 (UNIQUE 인덱스 제외).',
  '이름 `IX_{테이블}_{컬럼}`. FK 컬럼과 배치·조회 조건에 둔다 (선행 3). 조회 패턴이 정해진 것만 복합 인덱스로 만든다 (주문 10-5).',
  '`IX_MBR_MEMBER_LAST_ACTIVITY_AT` (휴면 판정 배치)'),
 ('함수 기반 인덱스', '식 인덱스', 'Function-Based Index',
  '컬럼 값 대신 식(CASE 등)의 결과로 만든 인덱스. 일반 B-tree 인덱스에는 키가 모두 NULL인 행이 들어가지 않으므로, 조건에 맞을 때만 값을 내는 식을 쓰면 그 행만 담은 작은 인덱스가 된다. UNIQUE로 만들면 조건에 맞는 행끼리만 유일성을 검사한다.',
  'UNIQUE: "회원당 기본값 1개" 같은 조건부 유일성 (회원 40-3 B). 일반: 배치·감시가 "아직 처리되지 않은 행"을 찾을 때 (주문 OC-117 서면 미교부, OC-72~75 보류, OC-70 결제 만료). 일반 IX로 NULL인 행을 찾으려 하지 않는다.',
  '`CASE WHEN DEFAULT_YN = \'Y\' THEN MEMBER_ID END`'),
 ('LOCAL 인덱스', '파티션 로컬 인덱스', 'Local Partitioned Index',
  '파티션마다 따로 만들어지는 인덱스. 파티션을 지워도 다른 파티션의 인덱스는 그대로다.',
  '파티션한 로그·이력 테이블의 기본이다.',
  '`IX_MBR_IDENTITY_VERIFICATION_LOG_MEMBER_ID` (LOCAL)'),
 ('GLOBAL 인덱스', '테이블 전체 인덱스', 'Global Index',
  '파티션과 상관없이 테이블 전체를 하나로 만든 인덱스. 파티션 키가 들어 있지 않은 UNIQUE는 GLOBAL이어야 한다. 파티션을 지우면 인덱스를 함께 갱신하지 않는 한 쓸 수 없게(UNUSABLE) 된다.',
  '파티션 키 없이 찾는 UK와 해시 검색에만 쓴다. 나머지는 LOCAL이 기본이다 (주문 OC-78). 파티션을 지울 때 `UPDATE GLOBAL INDEXES`를 붙인다 (OC-67). 주문 테이블은 14개다.',
  '`UK_ORD_ORDER_ORDER_NO`, `IX_ORD_ORDER_DELIVERY_ADDRESS_HASH`'),
]),
('채번·저장 구조·파티션', [
 ('시퀀스', '일련번호 생성기', 'Sequence',
  'Oracle이 겹치지 않는 번호를 차례로 만들어 주는 객체. 대리 PK 값을 만든다.',
  '테이블마다 1개, 이름 `SEQ_{테이블}`, `INCREMENT BY 1` (선행 1).',
  '`SEQ_MBR_MEMBER`'),
 ('CACHE', '시퀀스 캐시', 'Sequence Cache',
  '시퀀스 번호를 미리 메모리에 확보해 두는 개수. 클수록 빠르지만 DB가 재시작되면 확보한 번호가 비어 번호가 건너뛸 수 있다.',
  '고빈도 거래 테이블 100, 저빈도 테이블 20. 대상은 도메인마다 정한다 (선행 1).',
  '`CACHE 20`, 주문 `CACHE 100` (10-4)'),
 ('파티션', '테이블 분할', 'Partitioning',
  '큰 테이블을 기준값(예: 일시)에 따라 여러 조각으로 나눠 저장하는 방식. 오래된 조각을 통째로 지울 수 있다.',
  '시간순으로 만료되는 로그·이력 테이블과 주문(10년)에 쓴다 (선행 4, 11). 보존 기간이 행마다 다른 테이블은 파티션 없이 나눠서 DELETE한다 (배송 DC-28 A, 결제 12-4 A).',
  '`MBR_IDENTITY_VERIFICATION_LOG` 월 파티션'),
 ('INTERVAL 파티션', '자동 구간 파티션', 'Interval Partitioning',
  '정한 간격(예: 1개월)마다 새 파티션을 Oracle이 자동으로 만드는 방식.',
  '월 단위 로그·이력 테이블과 주문(주문 일시 월 단위, 주문 10-3 A)에 쓴다.',
  '`INTERVAL (NUMTOYMINTERVAL(1, \'MONTH\'))`'),
 ('참조 파티션', '부모 따라 분할', 'Reference Partitioning',
  '자식 테이블이 부모를 가리키는 FK를 따라 부모와 같은 파티션으로 나뉘는 방식. 자식에 파티션 키 컬럼이 없어도 되고, 부모 파티션을 지울 때 자식도 함께 지운다.',
  '주문 상품·할인 배분·상태 이력·사은품·유입 정보가 주문의 월 파티션을 따른다 (주문 10-3 A). 3단 참조 파티션(주문 → 결제 → 취소)의 제거는 21c XE에서 먼저 시험하기로 했다 (결제 11-1 A).',
  '`ORD_ORDER_ITEM` (`ORD_ORDER` 참조 파티션)'),
 ('파티션 제거', '파티션 삭제', 'Drop Partition',
  '`ALTER TABLE … DROP PARTITION`으로 오래된 조각을 통째로 지우는 것. 행마다 DELETE하는 것보다 빠르고 되돌림 기록이 적다. 이 테이블을 가리키는 활성 FK가 있으면 지우는 조각을 참조하는 행이 없어도 Oracle이 거부한다 (ORA-02266).',
  '보유 기간이 지난 로그를 이것으로 지운다 (선행 4, 11). 주문은 주문 월 + 10년에 제거하므로(주문 10-10 C) 주문을 가리키는 다른 도메인은 참조 파티션이나 값 참조를 쓴다 (OC-77 B). 21c XE에서 자기 참조 FK도 제거를 막는 것을 확인해 원주문 연결은 FK 없이 둔다.',
  '`ALTER TABLE ORD_ORDER DROP PARTITION … UPDATE GLOBAL INDEXES`'),
 ('가상 컬럼', '계산 컬럼', 'Virtual Column',
  '값을 저장하지 않고 같은 행의 다른 컬럼으로 만든 식을 조회할 때 계산하는 컬럼. 직접 값을 넣을 수 없어 원본과 어긋나지 않는다. 인덱스·CHECK·파티션 키에 쓸 수 있다. 다른 가상 컬럼을 참조할 수는 없다.',
  '다른 컬럼에서 늘 계산되는 값은 저장하지 않고 가상 컬럼으로 둔다 (주문 OC-72 보류 여부, OC-102 시도·시군구 코드, 결제 2-7 A 취소 가능 잔액, 배송 DC-3 A 적용 출고 기한). 결제 취소 상태는 다른 가상 컬럼 대신 원래 금액 컬럼으로 계산한다.',
  '`SIDO_CD AS (SUBSTR(LEGAL_DONG_CD, 1, 2))`'),
 ('네이티브 JSON 컬럼', 'JSON 타입 컬럼', 'Native JSON Column',
  'Oracle 21c의 `JSON` 타입 컬럼. 항목 구성이 행마다 다른 값을 한 칸에 담고, 형식이 맞는지 DB가 검사한다.',
  '필터·검색·통계에 쓰지 않는 값만 둔다 (선행 2). 상품은 컬럼 검토에서 1:N 테이블을 JSON으로 접었다: 혼용률(M-1 B), 세탁 기호(M-2 B), 실측(M-4 B), 태그(M-7 C). 고시 항목 값과 복종별 상세 속성도 JSON이다 (상품 6 C, 7 C).',
  '`PRD_STYLE.SIZE_MEASUREMENT_JSON`, `PRD_FABRIC.COMPOSITION_JSON`'),
 ('공통코드', '공통 값 목록', 'Common Code',
  '정해진 값 목록(상태, 유형, 사유 등)을 그룹과 값 두 테이블에 모아 두는 구조. 값마다 한글명·영문명·설명·정렬과 추가 속성을 갖는다.',
  '`CMM_CODE_GROUP`(그룹, `ATTR1`~`ATTR5`의 뜻 정의) + `CMM_CODE`(값, `CODE_ID`, `ATTR1_VAL`~`ATTR5_VAL`). 로직이 걸린 코드는 CHECK도 건다 (규칙 4). 정책값(기한 일수, 기준 금액)도 `ATTR`에 둔다. 값을 중간에 넣으면 뒤 `CODE_ID`가 밀리므로 뒤에 붙인다.',
  '`CMM_CODE.ATTR1_VAL` (시군구의 시도 코드)'),
]),
('동시성과 중복 방지', [
 ('비관적 잠금', '선점 잠금', 'Pessimistic Lock',
  '`SELECT … FOR UPDATE`로 행을 먼저 잠가, 같은 행을 쓰려는 다른 트랜잭션이 기다리게 하는 방식.',
  '합계를 읽고 판단한 뒤 쓰는 작업을 줄 세운다: 적립금·예치금 사용(결제 12-5 C, 회원 행), 미성년 월 한도(주문 9-4 A), 품번 발번(상품 M-9 B, `PRD_SEASON` 행), 결제 시도 차수 채번(결제 PYC-21 A, 주문 행).',
  '`SELECT … FROM MBR_MEMBER WHERE MEMBER_ID = :id FOR UPDATE`'),
 ('행 버전', '낙관적 잠금 번호', 'Row Version (Optimistic Lock)',
  'UPDATE할 때 읽었던 버전 번호와 비교해 같을 때만 바꾸고 번호를 1 올리는 방식. 읽은 뒤 다른 곳에서 바뀌었으면 실패한다.',
  '`ROW_VERSION_NO`. 주문 요약 상태 재계산과 고객 수정이 겹칠 때 쓴다 (주문 10-7). 비회원 주문 조회 실패 횟수·잠금을 갱신할 때는 행 버전과 `UPDATED_*`를 바꾸지 않는다 (OC-85 A).',
  '`ORD_ORDER.ROW_VERSION_NO`'),
 ('요청 키', '중복 요청 방지 키', 'Idempotency Key',
  '같은 요청이 두 번 와도 한 번만 처리되도록 요청마다 붙이는 키. UK로 두 번째 요청을 막는다.',
  '분류어 `_VAL` + UK. 주문 생성(주문 3-3 A), 결제 요청, 취소 요청에 둔다. Redis를 쓰지 않으므로 DB에 둔다 (선행 9).',
  '`UK_ORD_ORDER_ORDER_REQUEST_KEY_VAL`, `UK_PAY_PAYMENT_PAYMENT_REQUEST_KEY_VAL`'),
]),
('삭제와 보존', [
 ('논리 삭제', '논리 삭제', 'Soft Delete',
  '행을 지우지 않고 삭제 표시 컬럼에 값을 넣어 삭제된 것으로 취급하는 방식.',
  '마스터·설정 테이블에 쓴다. `DELETED_BY_TYPE_CD`, `DELETED_BY`, `DELETED_AT` 컬럼, 조회 때 `DELETED_AT IS NULL` (선행 4).',
  '`MBR_GRADE`, `MBR_TAG`'),
 ('물리 삭제', '물리 삭제', 'Hard Delete',
  '`DELETE`로 행 자체를 지우는 방식.',
  '회원 소유 목록과 단순 매핑에 쓴다 (선행 4, 회원 28-3·28-4). 보존 기간이 행마다 다른 테이블도 기간이 지나면 나눠서 지운다 (배송 DC-28 A).',
  '`MBR_DELIVERY_ADDRESS` (탈퇴 시 즉시)'),
 ('사용 중지', '사용 여부', 'In-Use Flag (`USE_YN`)',
  '삭제하지 않고 새로 쓰지 못하게만 막는 표시. 삭제와 별개다.',
  '자식이 있는 부모는 삭제 대신 `USE_YN = N`으로 중지한다 (선행 4).',
  '`MBR_GRADE.USE_YN`'),
 ('비식별화', '비식별화', 'De-identification',
  '행은 남기고 개인을 알아볼 수 있는 컬럼만 NULL로 바꾸는 처리.',
  '회원 탈퇴 처리 방식이다 (27-5 B). 탈퇴 뒤 회원 행에는 ID, 상태, 탈퇴 일시, 공개 번호, 가입일, 채널, 실적만 남는다 (28-1 B).',
  '탈퇴 회원 행 (상태 `WITHDRAWN`)'),
 ('파기', '개인정보 파기', 'Personal Information Purge',
  '보유 기간이 끝난 개인정보를 되살릴 수 없게 없애는 것.',
  'NULL 처리가 기본이라 파기 대상 컬럼은 NULL 허용이고 필수 여부는 애플리케이션이 검증한다. 이벤트 즉시 + 매일 배치로 실행하고, 파기 일시를 `PII_PURGED_AT`에 남긴다 (선행 7, 11-3).',
  '`PII_RETENTION_END_DT`가 지난 행'),
 ('개인정보 보유 공통 컬럼', '보유 컬럼 4개', 'PII Retention Columns',
  '행 단위로 파기하는 테이블에 두는 컬럼 4개: 보유 사유 코드, 기산 일자, 파기 예정 일자, 파기 일시.',
  '선행 7. 공통 컬럼 순서는 개인정보 보유 4개 → 시스템 6개 → 논리 삭제 3개 (규칙 8-A). 파기 예정일 계산식은 도메인마다 있다: 미성년 주문 max(기산일 + 5년, min(성년 도달일 + 3년, 주문일 + 10년)) (주문 10-2 A), 결제 max(이 행의 법정 기한, 주문의 파기 예정일) (결제 8-6 A). 배송은 주문 값을 복사한다 (DC-27 B).',
  '`PII_RETENTION_REASON_CD`, `PII_RETENTION_BASE_DT`, `PII_RETENTION_END_DT`, `PII_PURGED_AT`'),
]),
('개인정보 보호', [
 ('암호문 (`_ENC`)', '암호화 값', 'Ciphertext',
  '평문을 키로 암호화한 값. 키가 있어야 원래 값으로 되돌릴 수 있다.',
  'AES-256-GCM, `RAW` 타입, 길이 = 평문 + 29바이트 (키 버전 1 + IV 12 + 태그 16). 대상은 법정 필수 항목과 휴대폰, 이메일, 상세 주소다. 이름·생년월일·도로명 주소는 대상이 아니다 (선행 5, 회원 C-72·C-73).',
  '`EMAIL_ENC`'),
 ('검색 해시 (`_HASH`)', '검색용 해시', 'Search Hash',
  '값을 정규화한 뒤 HMAC-SHA256으로 만든 고정 길이 값. 원래 값으로 되돌릴 수 없지만, 같은 값이면 같은 해시가 나와 일치 검색과 UK에 쓴다.',
  '`RAW(32)` (선행 5). 비밀번호·PIN은 별도로 Argon2id를 쓴다.',
  '`EMAIL_HASH`, `CI_HASH`'),
 ('마스킹', '가림 처리', 'Masking',
  '값의 일부를 `*`로 가려 보여 주는 것.',
  '애플리케이션이 화면에서 처리한다. 외부에서 받은 마스킹 값(PG 카드번호 등)만 그대로 저장한다 (선행 5). 마스킹 카드번호에는 `*`가 반드시 있어야 한다 (결제 8-1 A, CHECK).',
  '`123-****-789`'),
 ('TDE', '투명 데이터 암호화', 'Transparent Data Encryption',
  'DB가 데이터 파일을 디스크에 쓸 때 자동으로 암호화하고 읽을 때 푸는 기능. 애플리케이션과 SQL은 평문을 본다. 디스크·백업 유출을 막는다.',
  '모든 테이블에 컬럼 암호화와 함께 쓴다 (선행 5). 이름(실명·수령인·예금주), 생년월일, 도로명·지번 주소는 컬럼 암호화 없이 평문 + TDE다 (회원 C-72·C-73, 모든 도메인).',
  '회원 실명 컬럼'),
 ('봉투 암호화', '이중 키 암호화', 'Envelope Encryption',
  '데이터는 데이터 키로 암호화하고, 데이터 키는 KMS의 마스터 키로 다시 암호화해 두는 방식. 마스터 키는 KMS 밖으로 나오지 않는다.',
  'AES-256-GCM + KMS (선행 5). 암호문 첫 바이트의 키 버전으로 어떤 데이터 키를 썼는지 안다.',
  '`_ENC` 컬럼 전체'),
 ('Argon2id', '비밀번호 해시', 'Argon2id',
  '메모리를 많이 쓰도록 만든 비밀번호 해시 함수. 무차별 대입을 느리게 한다. 같은 값도 매번 다른 해시가 나와 검색에는 못 쓴다.',
  '비밀번호와 결제 PIN에 쓴다. `VARCHAR2(255)` (선행 5, 회원 6, 41-1 D, C-70).',
  '직전 비밀번호 해시 (회원 6-2 B)'),
 ('HMAC 키 버전', '해시 키 버전', 'HMAC Key Version',
  '검색 해시를 만든 키의 버전 번호. 키를 바꿀 때 새 키로 다시 계산한 행과 아직 안 한 행을 구분한다.',
  '다시 계산할 수 있는 해시는 행에 `HASH_KEY_VER`을 두고 무중단으로 교체한다. CI 해시는 원문이 없어 CI 전용 키를 두고 교체하지 않는다. 임직원 회사 이메일 해시는 1년 재인증 때 새 키로 바뀐다 (회원 C-25, C-39).',
  '`HASH_KEY_VER`'),
 ('CI', '연계정보', 'Connecting Information',
  '본인인증 기관이 주민등록번호로 만들어 주는 사람별 고유 값. 서비스가 달라도 같은 사람이면 같다.',
  '원문은 저장하지 않고 HMAC 해시만 둔다 (회원 4-3 A). 1인 1계정 UK(4-1 C), 탈퇴 뒤 6개월 재가입 혜택 제한(39-2 B), 비회원 주문의 회원 연결 기준(주문 OC-83 A)이다.',
  '`MBR_MEMBER.CI_HASH`'),
]),
('설계 패턴', [
 ('스냅샷', '시점 복사본', 'Snapshot',
  '어떤 시점의 값을 다른 테이블에 복사해 두는 것. 원본이 나중에 바뀌어도 그 시점의 값이 남는다.',
  '주문의 상품·가격·회원 자격·배송지 사본(주문 5-1 A, 5-2 C, 5-4 B, 5-5 A), 주문·리뷰의 체형(회원 24-5 B, 선행 17), 클레임 환불 계좌(회원 43-4 C), 결제 당시 명세서 가맹점명(결제 PYC-78 A).',
  '리뷰 작성 당시의 키·몸무게'),
 ('캐시 컬럼', '계산 결과 저장 컬럼', 'Cache Column',
  '다른 테이블에서 계산할 수 있는 값을 조회 속도를 위해 미리 저장한 컬럼. 원천 데이터가 기준이다.',
  '배치나 이벤트로 갱신한다 (회원 12, 15, 상품 53 B). 적립금·예치금 잔액은 캐시를 두지 않고 원장에서 계산한다 (회원 16-1 C, 결제 12-5 C).',
  '`TOTAL_PURCHASE_CONFIRMED_AMT`, `ORDER_RESTRICTED_YN`'),
 ('원장', '거래 원장', 'Ledger',
  '금액·수량의 증감을 한 건씩 쌓는 거래 기록. 고치지 않고, 틀리면 반대 금액 행을 추가해 정정한다.',
  '적립금·예치금 원장은 결제 도메인 소속이다 (결제 1-2 A, 선행 15). 결제 취소도 취소 행을 쌓고 결제 행에는 누계만 둔다 (결제 2-7 A, 5-1 B).',
  '`PAY_POINT_LEDGER`, `PAY_DEPOSIT_LEDGER`'),
 ('로트 원장', '건별 잔액 원장', 'Lot Ledger',
  '들어온 건(적립, 입금)마다 남은 금액을 두고, 쓸 때 어느 건에서 얼마를 뺐는지 차감 기록을 남기는 원장. 소멸 순서와 부분 취소 복원이 정확하다.',
  '적립금·예치금이 이 구조다 (결제 12-1 A, 12-2 A). 잔액 컬럼은 없고 확정·기한 내 행의 남은 금액 합계로 계산하며, 동시 사용은 회원 행 잠금으로 막는다 (12-5 C).',
  '`PAY_POINT_LEDGER` + `PAY_POINT_DEDUCTION`'),
 ('이력', '변경 이력', 'History',
  '값이나 상태가 바뀔 때마다 남기는 기록. 삭제하지 않는다.',
  '테이블 이름 끝에 `_HIST` (예외 약어, 선행 6). 대량 도메인은 전용 이력, 나머지는 `SYS_STATUS_HIST`다.',
  '`MBR_CONSENT_HIST`, `ORD_ORDER_ITEM_STATUS_HIST`'),
 ('로그', '로그', 'Log',
  '외부 연동·접속 등 발생 사실을 시간순으로 쌓는 기록. 보유 기간이 지나면 파티션 단위로 제거한다.',
  '테이블 이름 끝에 `_LOG` (선행 4, 6). PG 연동은 호출 1회당 요약 행만 DB에 두고 원문은 외부 로그 도구에 둔다 (결제 7-1 C).',
  '`MBR_IDENTITY_VERIFICATION_LOG`, `DLV_COURIER_INTERFACE_LOG`'),
 ('아웃박스', '보낼 일 대기 테이블', 'Outbox',
  '외부 시스템에 알릴 변경을 업무 데이터와 같은 트랜잭션에서 테이블에 쌓고, 배치가 읽어 반영하는 방식. 업무 저장과 외부 반영이 어긋나지 않는다.',
  '상품 변경을 외부 검색 엔진 색인에 반영한다 (상품 37 D).',
  '`PRD_SEARCH_INDEX_OUTBOX`'),
 ('수신함', '받은 일 대기 테이블', 'Inbox',
  '외부에서 받은 메시지를 먼저 원문 그대로 저장하고, 처리 결과를 그 행에 남기는 테이블. 처리 실패와 중복 수신을 다시 처리할 수 있다.',
  'PG 웹훅에 쓴다. 택배사 추적 웹훅은 수신함 없이 추적 이벤트로 바로 저장하고 이벤트 ID UK로 중복을 막는다 (배송 DC-13, DC-20).',
  '`PAY_PG_WEBHOOK_INBOX`'),
 ('행위자 컬럼', '작업자 기록 컬럼', 'Actor Columns',
  '누가 행을 만들고 고치고 지웠는지 남기는 컬럼 쌍: 유형 + 식별자.',
  '유형 `VARCHAR2(20)`(`MEMBER`, `ADMIN`, `SYSTEM`, `BATCH`, `EXTERNAL`, `GUEST`, CHECK) + 식별자 `VARCHAR2(100)`. 시스템 컬럼 6개는 생성·수정 행위자와 일시다 (규칙 1, 선행 8).',
  '`CREATED_BY_TYPE_CD`, `CREATED_BY`, `CREATED_AT`'),
]),
('문서 표기', [
 ('확정 표시', '확정 표시', 'Confirmed Mark',
  '컬럼정의서에서 사용자가 확정한 행에 붙는 ☑.',
  '회원은 컬럼 설명 끝의 `[확정 YYYY-MM-DD]`와 `cols/order.py`의 `CONFIRMED_GROUPS`. 상품·주문·결제·배송은 `data.py`의 `CONFIRMED_GROUPS`(그 그룹의 컬럼·코드 값 행)와 `CONFIRMED_TABLES`(인덱스·제약·테이블 이름 행까지).',
  '☑'),
 ('값 행 접기', '참조 행', 'Folded Value Rows',
  '정의서에서 같은 코드 값 목록을 두 번째부터 다시 적지 않고, 처음 적은 곳을 가리키는 노란 참조 행으로 대신하는 표기.',
  '이름이 다른 컬럼이 같은 값 목록을 쓰면 `REUSE` (결제 PYC-51 A), 같은 이름 코드 컬럼이 다른 테이블에 다시 나오면 `SAME_NAME_FOLD` (결제 PYC-86 A, 규칙 4). 회원·주문·상품은 다시 열 때 적용한다.',
  '`n-n-↺`'),
]),
]

BIZ = [
('결제', [
 ('PG·MID', '결제대행업체·상점 아이디', 'Payment Gateway, Merchant ID',
  'PG는 카드사·은행·간편결제사와 몰 사이에서 결제를 중계하는 회사다. MID는 PG가 몰에 준 상점 아이디다.',
  'PG를 여러 곳 쓰고 결제 수단 × PG 설정으로 고른다 (선행 13, 결제 1-5 A). MID는 이 회사 명의만 쓴다 (여신전문금융업법 19조 5항). 결제 행에 실제로 쓴 PG와 MID를 남긴다 (결제 2-6 A).',
  '`PAY_PAYMENT_METHOD_PG_SETTING`, `PG_MID_VAL`'),
 ('빌링키', '정기·간편 결제 키', 'Billing Key',
  '카드를 한 번 등록하면 PG가 돌려주는 키. 다음 결제부터 카드번호 대신 이 키로 결제한다.',
  '회원 저장 결제수단에 암호문으로 둔다 (회원 40-2 B). PG마다 달라 발급한 PG로만 결제할 수 있다. 카드를 지우거나 탈퇴하면 PG 삭제 API를 부른 뒤 행을 지운다 (회원 47-1 A).',
  '`MBR_SAVED_PAYMENT_METHOD.BILLING_KEY_ENC`'),
 ('대사', '거래 맞춰 보기', 'Reconciliation',
  '우리 기록과 상대(PG 등)의 기록을 건별로 맞춰 보고 다른 것을 찾는 일.',
  '매일 PG × 거래일마다 대사 실행 행을 남기고, 불일치마다 불일치 행(유형, 양쪽 값, 해결)을 남긴다 (결제 7-3 B). 수수료·입금 대사는 정산 도메인이다 (결제 1-6 A).',
  '`PAY_RECONCILIATION_RUN`, `PAY_RECONCILIATION_MISMATCH`'),
 ('결과 불명', '결과 확인 중', 'Result Unknown',
  'PG에 승인·취소를 요청했지만 시간 초과 등으로 성공했는지 알 수 없는 상태.',
  '결제 상태 `UNKNOWN`과 발생 일시를 두고 조회·웹훅·대사로 확정한다 (결제 3-7 A). 확정한 경로를 코드로 남긴다 (3-2 C). 밀린 결과 불명 건은 감시 지표다 (7-6 B).',
  '`UNKNOWN_OCCURRED_AT`'),
 ('차지백', '카드 이의 제기 환수', 'Chargeback',
  '카드 회원이 카드사에 이의를 제기해, 카드사가 가맹점에 대금을 되돌려 달라고 청구하는 것.',
  '이의 제기마다 사건 행(결제 1 : 사건 N)에 사유, 이의 금액, 소명 기한·제출, 결과를 남긴다 (결제 9-3 A, 여신전문금융업법 16조). 인용되면 취소 행(환불 방법 차지백)을 만든다.',
  '`PAY_CHARGEBACK`'),
 ('FDS', '부정 결제 탐지', 'Fraud Detection System',
  '부정 결제가 의심되는 거래를 규칙과 점수로 걸러 내는 장치.',
  '결제 전에 자체 규칙으로 통과 / 검토 / 차단을 판정하고, 결제 행에 판정·점수·걸린 규칙과 그때의 기준값을 남긴다 (결제 9-1 A, PYC-4 A). 규칙은 공통코드에 둔다.',
  '`FDS_RULE_CD`'),
 ('결제대금예치', '에스크로', 'Escrow',
  '결제 대금을 제3자(PG·은행)가 맡아 두었다가 구매가 확정되면 판매자에게 주는 제도.',
  '가상계좌·계좌이체 결제에만 쓴다 (CHECK, 결제 PYC-80 A). 결제 행에 에스크로 그룹(배송 등록, 구매 확정)을 두고 (결제 6-9 A), 나눠 출고하면 마지막 송장을 등록한다 (배송 DC-12 B). 근거는 전자상거래법 13조 2항 10호, 24조.',
  '결제 행의 에스크로 그룹'),
]),
('배송', [
 ('영업일 달력', '영업일 기준표', 'Business Day Calendar',
  '날짜마다 영업일인지, 택배 집화가 있는지 적어 둔 기준표.',
  '법정 기한(출고 3영업일, 환급 3영업일)과 도착 예정일을 계산한다. 공휴일·대체공휴일을 등록하고 택배 집화 가능 여부를 따로 둔다 (배송 DC-26 A). 계산한 기한은 그때 값으로 저장하고, 나중에 공휴일을 등록해도 고치지 않는다 (DC-3 A).',
  '법정 출고 기한 = 대금을 받은 날 + 3영업일'),
 ('공급 기록', '재화 공급 기록', 'Supply Record',
  '재화를 언제, 어디로, 어떻게 보냈는지에 관한 기록. 전자상거래법 시행령 6조에 따라 5년 보존한다.',
  '단위는 실제로 보낸 출고다 (배송 1-1 B). 추적 이벤트를 12개월 뒤 지워도 남도록 배송 완료·집화 근거를 운송장에 복사한다 (DC-9 A, DC-14 B). 개인정보 보유는 주문 값을 복사한다 (DC-27 B).',
  '`DLV_SHIPMENT`, `DLV_WAYBILL.DELIVERED_AT`'),
]),
]

DOCS = {
    'db': ('DB 용어집', '설계 문서에 나오는 DB 약어와 용어의 뜻을 정리한다. 결제·배송 정의서의 업무 용어는 업무 용어집에 따로 있다.', DB),
    'biz': ('업무 용어집', '컬럼정의서와 정책명세를 읽는 데 필요한 결제·배송 업무 용어를 정리한다. DB 용어는 DB 용어집에 있다.', BIZ),
}

CSS = """@page { size: A4 landscape; margin: 12mm 12mm; }
body { font-family: 'Apple SD Gothic Neo', sans-serif; font-size: 8.6pt; color: #222; line-height: 1.5; }
h1 { font-size: 17pt; color: #1f4e79; border-bottom: 3px solid #1f4e79; padding-bottom: 5px; margin: 0 0 4px; }
.meta { color: #666; font-size: 8pt; margin-bottom: 8px; }
.box { border: 1px solid #c9d6e6; background: #f6f9fc; padding: 5px 9px; margin: 6px 0 10px; }
h2 { font-size: 11.5pt; color: #fff; background: #2b4c74; padding: 5px 9px; margin: 14px 0 6px; break-after: avoid; }
table { border-collapse: collapse; width: 100%; }
tr { break-inside: avoid; }
th, td { border: 1px solid #c4c4c4; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #eef2f7; }
td.t { color: #1f4e79; font-weight: 700; width: 9%; }
td.k { width: 8%; } td.e { width: 9%; } td.m { width: 26%; } td.r { width: 30%; } td.x { width: 18%; }
code { font-family: Menlo, monospace; font-size: 7.6pt; background: #f1f1f1; padding: 0 2px; word-break: break-all; }
.toc { columns: 2; margin: 0 0 6px; } .toc div { break-inside: avoid; }"""


def il(s):
    s = html.escape(s, quote=False)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', s)


def main(kind, out):
    title, note, chs = DOCS[kind]
    terms = [t for _, rows in chs for t in rows]
    names = [t[0] for t in terms]
    assert len(names) == len(set(names)), [n for n in names if names.count(n) > 1]
    b = [f'<h1>{title}</h1>',
         f'<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-27 기준 · 용어 {len(terms)}개 · 생성: tools/pdfgen/glossary/gen.py</div>',
         f'<div class="box">{il(note)} "이 프로젝트 규칙" 칸은 확정한 결정만 인용하고, 괄호 안 번호는 근거 결정이다 '
         '(숫자만 있으면 회원 도메인 결정, "C-"는 회원 컬럼 검토, "선행"은 선행 결정, "규칙"은 지시 규칙, 그 밖에는 도메인 이름을 붙였다).</div>',
         '<div class="toc">' + ''.join(f'<div><b>{i}. {il(c)}</b> ' + ', '.join(il(t[0]) for t in rows) + '</div>'
                                       for i, (c, rows) in enumerate(chs, 1)) + '</div>']
    for i, (c, rows) in enumerate(chs, 1):
        b.append(f'<h2>{i}. {il(c)}</h2><table><tr><th>용어</th><th>한글명</th><th>영문명</th><th>뜻</th><th>이 프로젝트 규칙</th><th>예시</th></tr>')
        for t, k, e, m, r, x in rows:
            b.append(f'<tr><td class="t">{il(t)}</td><td class="k">{il(k)}</td><td class="e">{il(e)}</td>'
                     f'<td class="m">{il(m)}</td><td class="r">{il(r)}</td><td class="x">{il(x)}</td></tr>')
        b.append('</table>')
    open(out, 'w', encoding='utf-8').write(
        f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{"".join(b)}</body></html>')
    print(out, len(terms))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
