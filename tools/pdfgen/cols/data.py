# 회원 도메인 컬럼 정의 (제안, 확정 전)
# 컬럼: (물리명, 한글 논리명, 영문 논리명, 타입, NULL(N=NOT NULL, Y=허용), 기본값, 제약, 설명)
ID = 'NUMBER(19,0)'
YN = 'CHAR(1)'
TS = 'TIMESTAMP'
def yn(p, ko, en, d, desc):
    return (p, ko, en, YN, 'N', f"'{d}'", 'CK (Y/N)', desc)

T = []  # (테이블, 한글, 영문, 설명, 근거, PK 방식, CACHE, 삭제 방식, 파티션, 보유, 논리삭제, PII, 컬럼, 인덱스·제약, 확인)

# ---------------------------------------------------------------- 1 MBR_GRADE
T.append(dict(
 t='MBR_GRADE', ko='회원 등급 기준 및 등급 혜택 (적용 기간별 버전)', en='Member Grade Criteria and Benefits (Versioned by Application Period)',
 desc='등급별 산정 기준(최근 12개월 구매 확정 금액)과 혜택을 담는 마스터. 기준이 바뀌면 같은 등급 코드로 새 행을 추가해 적용 기간으로 버전을 관리한다.',
 basis='14, 35-1, 35-2, 35-6', pk='대리 PK `SEQ_MBR_GRADE`', cache=20, delete='논리 삭제 (마스터). 자식(회원, 등급 이력)이 있으면 삭제 불가, `USE_YN`으로 중지', part='없음', keep='-', ldel=True, pii=False,
 cols=[
 ('GRADE_ID','회원 등급 기준 버전 고유 식별 번호','Member Grade Version Unique Identifier',ID,'N','','PK','등급 기준 한 버전(등급 코드 × 적용 기간)을 식별하는 대리 키. 회원 테이블과 등급 이력이 이 값을 FK로 참조한다.'),
 ('GRADE_CD','회원 등급 코드','Member Grade Code','VARCHAR2(30)','N','','UK1','같은 등급의 여러 버전이 공유하는 코드. 예: `BRONZE`, `SILVER`, `GOLD`, `VIP`. 값 목록은 운영 정책으로 정하고 `CMM_CODE`(등급 코드 그룹)에 둔다.'),
 ('GRADE_NM','회원 등급 화면 표시 이름','Member Grade Display Name','VARCHAR2(100)','N','','','고객 화면과 안내 메시지에 보이는 등급 이름. 예: 골드.'),
 ('GRADE_ORDER_SN','회원 등급 서열 순서 번호 (높을수록 상위 등급)','Member Grade Rank Order Sequence Number','NUMBER(3)','N','','CK (>= 1)','등급 비교와 승급 판정에 쓰는 순서. 값이 클수록 상위 등급. 강등이 없으므로(35-3) 승급 판정 때 현재 등급보다 큰 값만 적용한다.'),
 ('EVALUATION_PERIOD_MONTH_CNT','등급 산정 대상 기간 개월 수','Grade Evaluation Period Month Count','NUMBER(3)','N','12','CK (1~60)','최근 몇 개월의 구매 확정 금액으로 산정할지. 결정 14-3에 따라 12.'),
 ('MIN_PURCHASE_CONFIRMED_AMT','등급 달성 최소 구매 확정 금액 (원화)','Minimum Purchase Confirmed Amount for Grade (KRW)','NUMBER(15)','N','0','CK (>= 0)','산정 기간 동안 이 금액 이상을 구매 확정하면 이 등급이 된다. 반품·취소 금액은 제외 (14-2).'),
 ('APPLY_START_DT','등급 기준 적용 시작 일자','Grade Criteria Application Start Date','DATE','N','','UK1','이 버전이 적용되기 시작하는 날. 시각 부분은 0.'),
 ('APPLY_END_DT','등급 기준 적용 종료 일자','Grade Criteria Application End Date','DATE','Y','','CK (>= 시작 일자)','이 버전의 마지막 적용일. NULL이면 현재 적용 중. 같은 등급 코드에서 기간이 겹치지 않는지는 애플리케이션이 검증 (35-2).'),
 ('DISCOUNT_RT','등급 상품 할인율 (퍼센트)','Grade Product Discount Rate (Percent)','NUMBER(5,2)','N','0','CK (0~100)','이 등급 회원에게 주는 상품 할인율. 예: 5.00 = 5%.'),
 ('POINT_ACCUMULATION_RT','등급 적립금 적립률 (퍼센트)','Grade Point Accumulation Rate (Percent)','NUMBER(5,2)','N','0','CK (0~100)','구매 확정 금액 대비 적립률.'),
 yn('FREE_SHIPPING_YN','등급 무료 배송 혜택 여부','Grade Free Shipping Benefit Flag','N','Y면 이 등급 회원의 기본 배송비를 받지 않는다.'),
 ('BIRTHDAY_COUPON_POLICY_ID','등급 생일 쿠폰 할인 정책 식별 번호','Grade Birthday Coupon Discount Policy Identifier',ID,'Y','','FK → `PRM_DISCOUNT_POLICY` (후보)','생일에 발급할 쿠폰 정책. NULL이면 생일 쿠폰 없음. 대상 추출은 회원 생일 월일 컬럼 사용 (25-2).'),
 ('GRADE_COUPON_POLICY_ID','등급 정기 쿠폰 할인 정책 식별 번호','Grade Periodic Coupon Discount Policy Identifier',ID,'Y','','FK → `PRM_DISCOUNT_POLICY` (후보)','등급 산정 후 매월 발급할 등급 쿠폰 정책. NULL이면 없음.'),
 yn('USE_YN','등급 사용 여부','Grade In-Use Flag','Y','N이면 새 산정에 쓰지 않는다. 삭제와 따로 관리 (선행 결정 4).'),
 ('GRADE_DESC','등급 기준·혜택 설명','Grade Criteria and Benefit Description','VARCHAR2(1000)','Y','','','관리자용 설명과 고객 안내 문구.'),
 ],
 idx=['UK `UK_MBR_GRADE_GRADE_CD_APPLY_START_DT` (GRADE_CD, APPLY_START_DT)', 'IX `IX_MBR_GRADE_GRADE_CD` (GRADE_CD, APPLY_END_DT)'],
 check=[],
))

# ---------------------------------------------------------------- 2 MBR_TAG
T.append(dict(
 t='MBR_TAG', ko='회원 마케팅 분류 태그 마스터', en='Member Marketing Classification Tag Master',
 desc='마케팅 분류용 태그 목록. 관리자 화면에서 운영 중에 만들고 수정한다 (11-5 B). 혜택이 걸린 유형은 회원 유형 코드로 따로 관리한다.',
 basis='11-1 보충 B, 11-5 B', pk='대리 PK `SEQ_MBR_TAG`', cache=20, delete='논리 삭제 (마스터). 회원 매핑이 있으면 삭제 불가, `USE_YN`으로 중지', part='없음', keep='-', ldel=True, pii=False,
 cols=[
 ('TAG_ID','회원 태그 고유 식별 번호','Member Tag Unique Identifier',ID,'N','','PK','태그를 식별하는 대리 키.'),
 ('TAG_CD','회원 태그 업무 코드','Member Tag Business Code','VARCHAR2(50)','N','','UK','태그를 구분하는 영문 코드. 예: `OUTDOOR_LOVER`. 재사용 금지 값 (선행 결정 4).'),
 ('TAG_NM','회원 태그 이름','Member Tag Name','VARCHAR2(100)','N','','','관리자 화면에 보이는 이름.'),
 ('TAG_DESC','회원 태그 용도 설명','Member Tag Purpose Description','VARCHAR2(500)','Y','','','태그를 붙이는 기준과 쓰는 곳.'),
 yn('USE_YN','태그 사용 여부','Tag In-Use Flag','Y','N이면 새로 붙일 수 없다.'),
 ],
 idx=['UK `UK_MBR_TAG_TAG_CD` (TAG_CD)'], check=[],
))

# ---------------------------------------------------------------- 3 MBR_MEMBER
M = []
M += [
 ('MEMBER_ID','회원 고유 식별 번호','Member Unique Identifier',ID,'N','','PK','회원을 식별하는 대리 키. 가입할 때 시퀀스로 먼저 받아 생성자 컬럼에도 본인 ID로 기록한다 (선행 결정 8). [확정 2026-11-22]'),
 ('MEMBER_NO','고객 노출용 공개 회원 번호','Public Member Number for Customer Display','VARCHAR2(11)','N','','UK, CK (`M` + 숫자 10자리)','고객센터·영수증·URL에 쓰는 번호. `M` + 랜덤 숫자 10자리. UK 충돌 시 다시 생성 (5-2). 탈퇴 후에도 남는 재사용 금지 값 (28-1). URL에 쓸 때는 로그인한 본인의 번호인지 반드시 검사한다. 번호를 추측하기 어렵다는 것만으로는 접근 통제가 되지 않는다 (안전성 확보조치 기준 6조 3항, 법률 L7-3). [확정 2026-11-22]'),
 ('ANALYTICS_IDENTIFIER_VAL','외부 분석 도구 연계용 무작위 회원 식별 값','Random Member Identifier Value for External Analytics','VARCHAR2(36)','Y','','UK','외부 분석 도구에 보내는 무작위 값 (UUID). 내부 PK를 노출하지 않으려고 둔다 (선행 결정 12-4). 탈퇴 확정 시 NULL (법률 L1-1, 28-6 변경). 그래서 NULL 허용으로 바꿨다. 행동 분석 국외 이전에 동의하지 않은 회원도 값은 만들되 외부로 보내지 않는다 (법률 L7-1). [확정 2026-11-22]'),
 ('ANALYTICS_DATA_DELETION_REQUESTED_AT','외부 분석 도구 데이터 삭제 요청 일시','External Analytics Data Deletion Requested At',TS,'Y','','','탈퇴 확정 배치가 외부 분석 도구의 삭제 API 호출에 성공한 시각. 처리 증빙이라 탈퇴 후에도 남긴다 (법률 L1-3).'),
 ('ANALYTICS_DATA_DELETION_CONFIRMED_AT','외부 분석 도구 데이터 삭제 완료 확인 일시','External Analytics Data Deletion Confirmed At',TS,'Y','','','외부 도구에서 삭제가 끝난 것을 배치가 확인한 시각. 파기 증빙이라 탈퇴 후에도 남긴다. 맞춤형 광고 플랫폼의 요청·완료 컬럼(18-7, 18-8)과 같은 방식 (법률 L7-2, 개인정보 보호법 21조·26조 4항).'),
 ('MEMBER_STATUS_CD','회원 계정 상태 코드','Member Account Status Code','VARCHAR2(30)','N',"'ACTIVE'",'CK (값 목록)','회원 상태. 허용 전이는 애플리케이션이 관리하고 DB는 값만 제한 (10-1, 10-3). 바뀔 때마다 `SYS_STATUS_HIST`에 기록. 전체 정지 중 휴면 조건이 되면 휴면 우선: `DORMANT`로 바꾸고, 휴면 해제 때 유효한 전체 정지 행이 있으면 `ACTIVE`가 아니라 `SUSPENDED`로 되돌린다 [확정 2026-11-22].'),
 ('MEMBER_STATUS_CHANGED_AT','회원 계정 상태 최종 변경 일시','Member Account Status Last Changed At',TS,'N','SYSTIMESTAMP','','상태가 마지막으로 바뀐 시각. 휴면 전환·탈퇴 유예 계산과 화면 표시에 쓴다. [확정 2026-11-22: 제안 수용]'),
 ('JOINED_AT','회원 가입 완료 일시','Member Joined At',TS,'N','','','본인인증까지 마쳐 가입이 완료된 시각 (4-2). 시스템 컬럼 `CREATED_AT`과 분리한 업무 일시라 데이터 이관 때도 값을 유지한다. 가입 기간 통계, 가입 쿠폰, 등급 산정에 쓴다. [확정 2026-11-22]'),
]
M += [
 ('MEMBER_NAME_ENC','회원 실명 암호문','Member Legal Name Ciphertext','RAW(179)','Y','','','본인인증으로 받은 실명. AES-256-GCM 암호문 (평문 최대 150바이트 + 29). 휴면 중에는 `SYS_PII_ARCHIVE`로 옮기고 NULL (27-3). 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('EMAIL_ENC','회원 이메일 주소 암호문','Member Email Address Ciphertext','RAW(283)','Y','','','로그인 ID 겸 연락 수단 (2번). 평문 최대 254바이트. 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('EMAIL_HASH','회원 이메일 주소 검색용 해시','Member Email Address Search Hash','RAW(32)','Y','','UK','소문자·공백 제거로 정규화한 이메일의 HMAC-SHA256. 로그인과 중복 검사에 쓴다. 탈퇴 확정 시 NULL (선행 결정 4). [확정 2026-11-22]'),
 ('MOBILE_PHONE_NUMBER_ENC','회원 휴대폰 번호 암호문','Member Mobile Phone Number Ciphertext','RAW(49)','Y','','','본인인증으로 받은 휴대폰 번호. 숫자만 저장 (평문 최대 20바이트). 휴면 중 이동, 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('MOBILE_PHONE_NUMBER_HASH','회원 휴대폰 번호 검색용 해시','Member Mobile Phone Number Search Hash','RAW(32)','Y','','UK','숫자만 남긴 휴대폰 번호의 HMAC-SHA256. 비회원 주문 연결(14-6)과 중복 검사에 쓴다. 탈퇴 확정 시 NULL. [확정 2026-11-22]'),
 ('MOBILE_CARRIER_CD','휴대폰 통신사 코드','Mobile Carrier Code','VARCHAR2(20)','Y','','','본인인증 결과의 통신사. 값은 `CMM_CODE`(통신사 그룹, 알뜰폰 구분 포함). 업체 결과 값과 다르면 애플리케이션이 매핑한다. 휴대폰 번호를 바꿔 재인증하면 갱신. 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('BIRTH_DATE_ENC','회원 생년월일 암호문','Member Birth Date Ciphertext','RAW(37)','Y','','','`YYYYMMDD` 8바이트 평문의 암호문. 본인인증 결과. 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('MEMBER_NAME_BIRTH_DATE_HASH','회원 실명·생년월일 조합 검색용 해시','Member Legal Name and Birth Date Search Hash','RAW(32)','Y','','IX','관리자 회원 검색용. 공백을 없앤 실명 + `YYYYMMDD` 생년월일을 합쳐 HMAC-SHA256. 정확히 일치할 때만 검색된다. 생일이 같은 동명이인이 있을 수 있어 UK는 걸지 않는다. 휴면 중에도 그대로 두어 휴면 회원도 검색된다 (이름 원문만 분리 보관). 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('BIRTH_MONTH_DAY_VAL','생일 쿠폰 대상 추출용 생일 월일 (평문)','Birth Month and Day for Birthday Coupon (Plaintext)','VARCHAR2(4)','Y','','CK (`MMDD` 형식)','생일 쿠폰 대상을 SQL로 뽑으려고 평문으로 둔 월일 (25-2 D). 연령대와 합쳐도 정확한 생년월일은 알 수 없다. 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('AGE_GROUP_CD','5년 단위 연령대 코드','Five-Year Age Group Code','VARCHAR2(20)','Y','','','연령대 분석용 평문 코드 (25-2 D). 일 배치가 생년월일로 다시 계산. 값은 `CMM_CODE`(연령대 그룹). 예: `AGE_20_24`. 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('GENDER_CD','회원 성별 코드','Member Gender Code','VARCHAR2(10)','Y','','CK (값 목록)','본인인증 결과의 성별 (37-4 A). 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('FOREIGNER_YN','외국인 여부','Foreigner Flag','CHAR(1)','Y','','CK (Y/N)','본인인증 결과의 내외국인 구분. Y = 외국인. 파기 대상이라 NULL 허용 (선행 결정 7). 탈퇴 시 NULL. [확정 2026-11-22]'),
 ('CI_HASH','본인인증 연계 정보 해시','Identity Verification Connecting Information Hash','RAW(32)','Y','','UK','본인인증 CI의 HMAC-SHA256. 1인 1계정 보장 (4-1). 원문은 저장하지 않음 (4-3). 탈퇴 후 재가입 혜택 제한 기간(6개월) 동안 보관한 뒤 NULL (28-2, 39-2). [확정 2026-11-22]'),
 ('NICKNAME_NM','회원 닉네임','Member Nickname','VARCHAR2(60)','Y','','UK','리뷰·Q&A에 평문으로 보이는 이름 (37-2 B). 탈퇴 시 NULL이 되어 다른 회원이 바로 쓸 수 있다 (39-6). [확정 2026-11-22]'),
]
M += [
 yn('EMAIL_VERIFIED_YN','이메일 소유 인증 완료 여부','Email Ownership Verified Flag','N','이메일 인증 링크를 확인했는지 (30-7).'),
 ('EMAIL_VERIFIED_AT','이메일 소유 인증 완료 일시','Email Ownership Verified At',TS,'Y','','','이메일 인증을 마친 시각.'),
 ('LAST_IDENTITY_VERIFIED_AT','최근 본인인증 완료 일시','Last Identity Verification Completed At',TS,'Y','','','가입·복구·잠금 해제 등에서 마지막으로 본인인증한 시각 (30-7).'),
 ('LAST_LOGIN_AT','최근 로그인 일시 (전체 로그인 수단 기준)','Last Login At (All Login Methods)',TS,'Y','','','어떤 수단으로든 로그인하면 갱신 (8-2 C). 휴면 판정(27-2, 1년)에 쓴다.'),
 ('LAST_LOGIN_CHANNEL_CD','최근 로그인 판매 채널 코드','Last Login Sales Channel Code','VARCHAR2(20)','Y','','CK (PC/MOBILE_WEB/APP)','최근 로그인 채널 (선행 결정 10-1).'),
]
M += [
 ('MEMBER_TYPE_CD','회원 혜택 유형 코드','Member Benefit Type Code','VARCHAR2(30)','N',"'GENERAL'",'CK (값 목록)','혜택이 걸린 회원 유형 (11-1 보충 B, 11-3). 마케팅 분류는 태그로 따로 관리.'),
 yn('EMPLOYEE_YN','임직원 여부','Employee Flag','N','다른 유형과 겹칠 수 있어 따로 둔다 (11-2 B). Y면 임직원 할인 한도 테이블 사용.'),
 ('EMPLOYEE_VERIFIED_AT','임직원 회사 이메일 인증 완료 일시','Employee Company Email Verified At',TS,'Y','','','회사 도메인 메일 인증 시각. 회사 메일 주소는 저장하지 않음 (32-3 A).'),
 ('EMPLOYEE_REVERIFICATION_DUE_DT','임직원 자격 재인증 기한 일자','Employee Qualification Reverification Due Date','DATE','Y','','','인증일 + 1년. 지나면 일 배치가 임직원 자격을 해제 (32-4 B).'),
 ('QUALIFICATION_APPLICATION_TYPE_CD','특수 자격 신청 유형 코드','Special Qualification Application Type Code','VARCHAR2(30)','Y','','CK (값 목록)','진행 중이거나 마지막으로 신청한 특수 자격 (32-2 A).'),
 ('QUALIFICATION_APPLIED_AT','특수 자격 신청 일시','Special Qualification Applied At',TS,'Y','','',''),
 ('QUALIFICATION_APPROVAL_STATUS_CD','특수 자격 승인 상태 코드','Special Qualification Approval Status Code','VARCHAR2(20)','Y','','CK (값 목록)','신청·승인·반려·만료. 변경 이력은 `SYS_STATUS_HIST`.'),
 ('QUALIFICATION_APPROVER_ADMIN_USER_ID','특수 자격 승인 관리자 식별 번호','Special Qualification Approver Administrator Identifier',ID,'Y','','FK → `ADM_USER` (PK 이름은 관리자 도메인에서 확정)','승인·반려한 관리자.'),
 ('QUALIFICATION_APPROVED_AT','특수 자격 승인 또는 반려 처리 일시','Special Qualification Decision At',TS,'Y','','',''),
 ('QUALIFICATION_END_DT','특수 자격 만료 일자','Special Qualification Expiration Date','DATE','Y','','','지나면 일 배치가 유형을 `GENERAL`로 되돌림 (32-4 B).'),
 ('QUALIFICATION_REJECTION_REASON_DESC','특수 자격 반려 사유','Special Qualification Rejection Reason Description','VARCHAR2(1000)','Y','','',''),
]
M += [
 yn('ORDER_RESTRICTED_YN','주문 제한 중 여부 (제재 캐시)','Order Restricted Flag (Sanction Cache)','N','`MBR_SANCTION`에서 현재 유효한 주문 제한이 있으면 Y. 제재 등록·종료 때와 배치로 갱신 (12번 보충 B).'),
 yn('COUPON_POINT_RESTRICTED_YN','쿠폰·적립금 사용 제한 중 여부 (제재 캐시)','Coupon and Point Usage Restricted Flag (Sanction Cache)','N','같은 방식.'),
 yn('REVIEW_RESTRICTED_YN','리뷰 작성 제한 중 여부 (제재 캐시)','Review Writing Restricted Flag (Sanction Cache)','N','같은 방식.'),
 yn('PAYMENT_RESTRICTED_YN','결제 제한 중 여부 (제재 캐시)','Payment Restricted Flag (Sanction Cache)','N','같은 방식. 연속 결제 실패 자동 제한(46-2)도 여기 반영.'),
 yn('INQUIRY_RESTRICTED_YN','문의 작성 제한 중 여부 (제재 캐시)','Inquiry Writing Restricted Flag (Sanction Cache)','N','같은 방식.'),
 yn('SANCTION_REVIEW_TARGET_YN','반품 남용 제재 검토 대상 여부','Return Abuse Sanction Review Target Flag','N','반품률이 기준을 넘으면 배치가 Y로 표시하고 관리자가 확인 (12-4 B).'),
]
M += [
 ('GRADE_ID','현재 회원 등급 기준 버전 식별 번호','Current Member Grade Version Identifier',ID,'N','','FK → `MBR_GRADE`','현재 적용 등급 버전. 월 배치나 수동 조정으로 바뀜 (14-1).'),
 ('GRADE_APPLIED_AT','현재 회원 등급 적용 일시','Current Member Grade Applied At',TS,'N','SYSTIMESTAMP','','현재 등급이 적용된 시각. [제안: 결정 항목 아님]'),
 yn('MANUAL_GRADE_YN','관리자 수동 지정 등급 여부','Manually Assigned Grade Flag','N','Y면 월 배치가 등급을 바꾸지 않는다 (35-4 B).'),
 ('MANUAL_GRADE_REASON_DESC','수동 등급 지정 사유','Manual Grade Assignment Reason Description','VARCHAR2(500)','Y','','',''),
 ('MANUAL_GRADE_END_DT','수동 등급 만료 일자','Manual Grade Expiration Date','DATE','Y','','','지나면 다음 배치에서 산정 등급으로 돌아감.'),
]
M += [
 ('TOTAL_PURCHASE_CONFIRMED_AMT','누적 구매 확정 금액 (원화, 실적 캐시)','Total Purchase Confirmed Amount (KRW, Statistics Cache)','NUMBER(15)','N','0','CK (>= 0)','가입 이후 구매 확정 금액 합계. 일 배치 (15-3 B).'),
 ('FIRST_PURCHASE_DT','첫 구매 확정 일자','First Purchase Confirmed Date','DATE','Y','','',''),
 ('LAST_PURCHASE_DT','최근 구매 확정 일자','Last Purchase Confirmed Date','DATE','Y','','','이탈 고객 추출(R)에 쓴다.'),
 ('RETURN_RT','반품률 (퍼센트, 실적 캐시)','Return Rate (Percent, Statistics Cache)','NUMBER(5,2)','N','0','CK (0~100)','반품 남용 탐지(12-4)에 쓴다. 계산 기준(수량·금액)은 주문 도메인에서 확정.'),
 ('RECENT_TWELVE_MONTH_PURCHASE_CONFIRMED_AMT','최근 12개월 구매 확정 금액 (원화, 실적 캐시)','Recent Twelve Month Purchase Confirmed Amount (KRW)','NUMBER(15)','N','0','CK (>= 0)','등급 산정과 등급 안내에 쓴다 (14, 15-2 F).'),
 ('PURCHASE_STATISTICS_CALCULATED_AT','구매 실적 캐시 최종 계산 일시','Purchase Statistics Last Calculated At',TS,'Y','','','일 배치 계산 시각. [제안: 결정 항목 아님]'),
]
CONSENT = [
 ('MARKETING_PRIVACY_COLLECTION','마케팅 목적 개인정보 수집·이용','Marketing Purpose Personal Information Collection'),
 ('ADVERTISING_SMS','광고성 정보 SMS·LMS 수신','Advertising SMS and LMS Reception'),
 ('ADVERTISING_EMAIL','광고성 정보 이메일 수신','Advertising Email Reception'),
 ('ADVERTISING_PUSH','광고성 정보 앱 푸시 수신','Advertising App Push Reception'),
 ('NIGHT_ADVERTISING','야간(21시~8시) 광고성 정보 수신','Night-Time Advertising Reception'),
 ('BODY_INFORMATION','체형 정보 수집·이용','Body Information Collection'),
 ('ADVERTISING_PLATFORM_SHARE','맞춤형 광고를 위한 개인정보 제3자 제공','Third-Party Provision for Personalized Advertising'),
 ('ANALYTICS_OVERSEAS_TRANSFER','행동 분석 정보 국외 이전','Overseas Transfer of Behavior Analytics Data'),
 ('REFUND_ACCOUNT_STORAGE','환불 계좌 보관','Refund Account Storage'),
]
M += [
 ('TERMS_OF_SERVICE_VER','동의한 이용약관 버전','Agreed Terms of Service Version','VARCHAR2(20)','N','','','유일한 필수 동의 (법률 L9-1). 약관이 바뀌어 다시 동의하면 갱신. 이력은 `MBR_CONSENT_HIST` (17-1 C). [확정 2026-11-22]'),
 ('TERMS_OF_SERVICE_AGREED_AT','이용약관 동의 일시','Terms of Service Agreed At',TS,'N','','','[확정 2026-11-22]'),
 ('PRIVACY_NOTICE_VER','확인한 개인정보 수집·이용 고지 버전','Confirmed Personal Information Collection Notice Version','VARCHAR2(20)','N','','','동의가 아니라 고지 확인. 가입·주문에 필요한 항목은 계약 이행 근거로 동의 없이 수집하고, 동의 항목과 구분해 고지한다 (법률 L9-1, 개인정보 보호법 15조 1항 4호·22조 3항). 고지가 바뀌어 회원이 확인하면 갱신하고 `MBR_CONSENT_HIST`에 `PRIVACY_NOTICE` 행을 남긴다. 결정 때 이름은 `PRIVACY_COLLECTION_VER` (17-3 변경). [확정 2026-11-22]'),
 ('PRIVACY_NOTICE_CONFIRMED_AT','개인정보 수집·이용 고지 확인 일시','Personal Information Collection Notice Confirmed At',TS,'N','','','현재 고지 버전을 확인한 시각. 결정 때 이름은 `PRIVACY_COLLECTION_AGREED_AT` (법률 L9-1). [확정 2026-11-22]'),
]
for p, ko, en in CONSENT:
    M.append(yn(f'{p}_AGREED_YN', f'{ko} 선택 동의 여부', f'{en} Consent Flag', 'N', '선택 동의 현재 상태. 바뀔 때마다 `MBR_CONSENT_HIST`에 1행 (17-2 B).'))
    M.append((f'{p}_AGREED_AT', f'{ko} 동의 또는 철회 일시', f'{en} Consent Changed At', TS, 'Y', '', '', '현재 상태가 된 시각. 광고성 수신 동의는 2년마다 재확인 안내에 쓴다.'))
M.append(yn('PRIVACY_USAGE_NOTICE_REJECTED_YN','개인정보 이용·제공 내역 통지 거부 여부','Personal Information Usage Notice Rejected Flag','N','Y면 연 1회 개인정보 이용·제공 내역 통지에서 제외한다. 바뀔 때마다 `MBR_CONSENT_HIST`에 `PRIVACY_USAGE_NOTICE` 행 (법률 L9 후속, 개인정보 보호법 20조의2, 시행령 15조의3 2항 1호). [확정 2026-11-22]'))
M.append(('PRIVACY_USAGE_NOTICE_SENT_AT','개인정보 이용·제공 내역 최근 통지 발송 일시','Personal Information Usage Notice Last Sent At',TS,'Y','','','연 1회 이상 통지(수집·이용 목적과 항목, 제공받은 제3자와 목적·항목)의 이행 증빙. 거부하지 않았고 이 값이 1년이 지난 회원을 배치가 통지 대상으로 뽑는다 (법률 L9 후속, 시행령 15조의3 3항·4항). [확정 2026-11-22]'))
M.append(('ADVERTISING_CONSENT_RECONFIRM_NOTICE_SENT_AT','광고 수신 동의 재확인 안내 발송 일시','Advertising Consent Reconfirmation Notice Sent At',TS,'Y','','','2년마다 하는 광고 수신 동의 확인 안내를 보낸 시각. 채널별 동의일(`*_AGREED_AT`) 중 가장 이른 2년 기한 전에 한 번에 안내하고, 안내에는 전송자, 채널별 동의 사실과 날짜, 유지·철회 방법을 적는다. 회원이 응답하지 않아도 확인 의무 이행의 증빙이 되고, 같은 주기에 두 번 보내지 않게 한다 (법률 L9-3, 정보통신망법 50조 8항, 시행령 62조의3). [확정 2026-11-22]'))
M += [
 yn('RESTOCK_NOTIFICATION_YN','재입고 알림 수신 여부','Restock Notification Reception Flag','Y','정보성 주제 (18-2).'),
 yn('PRICE_DROP_NOTIFICATION_YN','위시 상품 가격 인하 알림 수신 여부','Wishlist Price Drop Notification Reception Flag','N','광고성 주제. 이 값과 광고 동의가 모두 Y일 때만 발송 (18-2).'),
 yn('REVIEW_REQUEST_NOTIFICATION_YN','리뷰 작성 요청 알림 수신 여부','Review Request Notification Reception Flag','N','광고성으로 해석될 수 있어 광고 동의와 함께 확인.'),
 yn('POINT_EXPIRATION_NOTIFICATION_YN','적립금 소멸 예정 알림 수신 여부','Point Expiration Notification Reception Flag','Y','정보성 주제.'),
 yn('GRADE_CHANGE_NOTIFICATION_YN','등급 변경 알림 수신 여부','Grade Change Notification Reception Flag','Y','정보성 주제.'),
 yn('PERSONALIZATION_REJECTED_YN','개인화 거부 여부','Personalization Rejected Flag','N','Y면 선호 추론, 개인화 정렬, 외부 광고 전송에서 제외 (38-10-2). 결정 때 이름은 `PERSONALIZATION_YN`이었으나 뜻을 분명히 하려고 바꿔 제안.'),
]
M += [
 ('JOIN_CHANNEL_CD','가입 판매 채널 코드','Join Sales Channel Code','VARCHAR2(20)','N','','CK (PC/MOBILE_WEB/APP)','선행 결정 10-1. 탈퇴 후에도 통계용으로 유지 (28-1).'),
 ('JOIN_OS_CD','가입 기기 운영체제 코드','Join Device Operating System Code','VARCHAR2(20)','Y','','','선행 결정 10-1. 값은 `CMM_CODE`(OS 그룹).'),
 ('FIRST_VISIT_UTM_SOURCE_VAL','첫 방문 UTM 유입 출처','First Visit UTM Source Value','VARCHAR2(200)','Y','','','쿠키에 저장해 둔 최초 방문 UTM (20-2 C).'),
 ('FIRST_VISIT_UTM_MEDIUM_VAL','첫 방문 UTM 유입 매체','First Visit UTM Medium Value','VARCHAR2(200)','Y','','',''),
 ('FIRST_VISIT_UTM_CAMPAIGN_VAL','첫 방문 UTM 캠페인','First Visit UTM Campaign Value','VARCHAR2(200)','Y','','',''),
 ('JOIN_UTM_SOURCE_VAL','가입 직전 방문 UTM 유입 출처','Join Session UTM Source Value','VARCHAR2(200)','Y','','','가입한 세션의 UTM (20-2 C).'),
 ('JOIN_UTM_MEDIUM_VAL','가입 직전 방문 UTM 유입 매체','Join Session UTM Medium Value','VARCHAR2(200)','Y','','',''),
 ('JOIN_UTM_CAMPAIGN_VAL','가입 직전 방문 UTM 캠페인','Join Session UTM Campaign Value','VARCHAR2(200)','Y','','',''),
 ('REFERRER_DOMAIN_VAL','가입 유입 사이트 도메인','Join Referrer Domain Value','VARCHAR2(255)','Y','','','UTM이 없는 자연 유입의 출처 도메인. 전체 URL은 저장하지 않음 (20-3 B).'),
]
M += [
 ('HEIGHT_CM_VAL','키 (센티미터, 정수)','Height in Centimeters','NUMBER(3)','Y','','CK (100~230)','정확한 수치 (24-3 A). 체형 동의 철회·탈퇴 시 NULL (24-7 C).'),
 ('WEIGHT_KG_VAL','몸무게 (킬로그램, 정수)','Weight in Kilograms','NUMBER(3)','Y','','CK (25~250)','같은 방식.'),
 ('USUAL_TOP_SIZE_CD','평소 상의 사이즈 코드','Usual Top Size Code','VARCHAR2(20)','Y','','','`CMM_CODE` 선택 (XS~XXL) (24-9-3 B).'),
 ('USUAL_BOTTOM_SIZE_CD','평소 하의 사이즈 코드','Usual Bottom Size Code','VARCHAR2(20)','Y','','',''),
 ('USUAL_WAIST_SIZE_CD','평소 허리 사이즈 코드 (인치)','Usual Waist Size Code (Inch)','VARCHAR2(20)','Y','','','24~40인치 공통코드.'),
 ('USUAL_SHOE_SIZE_CD','평소 신발 사이즈 코드 (밀리미터)','Usual Shoe Size Code (Millimeter)','VARCHAR2(20)','Y','','','220~300mm 공통코드.'),
 ('BODY_REVIEW_DISCLOSURE_CD','리뷰 체형 공개 범위 코드','Review Body Information Disclosure Code','VARCHAR2(20)','N',"'RANGE'",'CK (값 목록)','리뷰에 체형을 어떻게 보일지 회원 설정 (24-8 B).'),
 ('TOP_SIZE_ADJUSTMENT_VAL','상의 사이즈 추천 보정 값 (사이즈 단계)','Top Size Recommendation Adjustment Value','NUMBER(2)','N','0','CK (-3~3)','사이즈 피드백으로 계산한 보정값. 예: -1 = 한 사이즈 작게 (24-11-3).'),
 ('BOTTOM_SIZE_ADJUSTMENT_VAL','하의 사이즈 추천 보정 값 (사이즈 단계)','Bottom Size Recommendation Adjustment Value','NUMBER(2)','N','0','CK (-3~3)',''),
]
M += [
 ('DORMANT_AT','휴면 전환 일시','Dormant Transition At',TS,'Y','','','1년 동안 로그인이 없으면 일 배치가 전환 (27-1, 27-2).'),
 ('DORMANT_NOTICE_SENT_AT','휴면 전환 사전 안내 발송 일시','Dormant Advance Notice Sent At',TS,'Y','','','30일 전 안내를 두 번 보내지 않으려고 기록 (27-4).'),
 ('WITHDRAWAL_REQUESTED_AT','탈퇴 신청 일시','Withdrawal Requested At',TS,'Y','','','7일 유예 시작 (39-3). 신청 때 예치금 잔액이 있으면 출금 요청 행을 자동으로 만들고 계좌를 스냅샷한 뒤, 결제 관련 값을 NULL로 바꾼다 (법률 L2-1, L2-2, 47-2 B).'),
 ('WITHDRAWAL_SCHEDULED_DT','탈퇴 확정 예정 일자','Withdrawal Scheduled Date','DATE','Y','','','신청일 + 7일. 예치금 출금이 끝나지 않아도 이 날 확정한다. 미반환 건은 고객센터가 처리하고, 연락처는 `SYS_PII_ARCHIVE`에 둔다 (법률 L2-3, L2-4).'),
 ('WITHDRAWN_AT','탈퇴 확정 일시','Withdrawal Confirmed At',TS,'Y','','','비식별화가 끝난 시각 (27-5). 통계용으로 유지 (28-1).'),
 ('WITHDRAWAL_REASON_CD','탈퇴 사유 코드','Withdrawal Reason Code','VARCHAR2(30)','Y','','','탈퇴 화면에서 고른 사유. 값은 `CMM_CODE`. [제안: 결정 항목 아님]'),
 ('REJOIN_BENEFIT_RESTRICTION_END_DT','재가입 신규 혜택 제한 만료 일자','Rejoin Benefit Restriction End Date','DATE','Y','','','탈퇴 확정일 + 6개월. 이 날까지 같은 CI로 재가입하면 신규 혜택을 주지 않는다 (39-1 C, 39-2 B).'),
]
M += [
 ('PAYMENT_PIN_HASH','결제 비밀번호 해시 (Argon2id)','Payment PIN Hash (Argon2id)','VARCHAR2(255)','Y','','','6자리 PIN의 Argon2id 결과 문자열 (41-1 D). 탈퇴 신청 즉시 NULL (47-2 B). [확인 필요: `_HASH` 타입 규칙]'),
 ('PAYMENT_PIN_FAIL_CNT','결제 비밀번호 연속 실패 횟수','Payment PIN Consecutive Failure Count','NUMBER(2)','N','0','CK (>= 0)','5회면 잠금 (41-2 A). 성공하면 0.'),
 ('PAYMENT_PIN_LOCKED_AT','결제 비밀번호 잠금 일시','Payment PIN Locked At',TS,'Y','','','본인인증으로만 해제.'),
 ('LAST_PAYMENT_METHOD_TYPE_CD','최근 사용 결제수단 유형 코드','Last Used Payment Method Type Code','VARCHAR2(30)','Y','','','주문서 미리 선택용 (42-2 B). 값 목록은 결제 도메인. 탈퇴 신청 즉시 NULL.'),
 ('LAST_SAVED_PAYMENT_METHOD_ID','최근 사용 저장 결제수단 식별 번호','Last Used Saved Payment Method Identifier',ID,'Y','','FK → `MBR_SAVED_PAYMENT_METHOD` (ON DELETE SET NULL)','원클릭 카드로 결제했을 때만 채운다. [확인 필요: 순환 FK]'),
 ('CONSECUTIVE_PAYMENT_FAIL_CNT','연속 결제 실패 횟수','Consecutive Payment Failure Count','NUMBER(3)','N','0','CK (>= 0)','기준을 넘으면 자동 결제 제한 (46-1, 46-2). 성공하면 0.'),
 ('LAST_PAYMENT_FAILED_AT','최근 결제 실패 일시','Last Payment Failed At',TS,'Y','','',''),
 ('REFUND_BANK_CD','환불 계좌 은행 코드','Refund Account Bank Code','VARCHAR2(10)','Y','','','`CMM_CODE`(은행 그룹). 회원당 계좌 1개 (선행 결정 15-3-3). 탈퇴 신청 즉시 NULL.'),
 ('REFUND_ACCOUNT_NUMBER_ENC','환불 계좌 번호 암호문','Refund Account Number Ciphertext','RAW(59)','Y','','','평문 최대 30바이트.'),
 ('REFUND_ACCOUNT_HOLDER_NAME_ENC','환불 계좌 예금주 이름 암호문','Refund Account Holder Name Ciphertext','RAW(179)','Y','','',''),
 ('REFUND_ACCOUNT_VERIFIED_AT','환불 계좌 1원 인증 완료 일시','Refund Account One-Won Verification At',TS,'Y','','','43-2 C. 인증 코드는 `SYS_VERIFICATION_CODE`.'),
 ('REFUND_ACCOUNT_VERIFICATION_RESULT_CD','환불 계좌 인증 결과 코드','Refund Account Verification Result Code','VARCHAR2(20)','Y','','CK (값 목록)',''),
 ('CASH_RECEIPT_PURPOSE_CD','현금영수증 기본 발급 용도 코드','Default Cash Receipt Purpose Code','VARCHAR2(20)','Y','','CK (값 목록)','소득공제·지출증빙 (44-1 D). 탈퇴 신청 즉시 NULL.'),
 ('CASH_RECEIPT_IDENTIFIER_TYPE_CD','현금영수증 기본 식별 번호 유형 코드','Default Cash Receipt Identifier Type Code','VARCHAR2(20)','Y','','CK (값 목록)',''),
 ('CASH_RECEIPT_IDENTIFIER_NUMBER_ENC','현금영수증 기본 식별 번호 암호문','Default Cash Receipt Identifier Number Ciphertext','RAW(49)','Y','','','휴대폰·카드·사업자번호. 암호화 대상 (25-1 B).'),
]
T.append(dict(
 t='MBR_MEMBER', ko='회원 기본 정보 및 회원 단위 설정·캐시', en='Member Master with Member-Level Settings and Caches',
 desc='회원 1명당 1행. 계정 상태, 암호화 개인정보, 유형·등급, 실적·제재 캐시, 동의 현재값, 알림 설정, 유입, 체형, 휴면·탈퇴, 결제·환불 기본값을 담는다. 탈퇴하면 행은 남기고 개인정보를 NULL로 바꾼다 (27-5).',
 basis='1~47 전반', pk='대리 PK `SEQ_MBR_MEMBER` (가입 시 먼저 채번)', cache=20, delete='상태 코드 (`WITHDRAWN`) + 개인정보 NULL. 물리 삭제 없음', part='없음', keep='개인정보와 분석용 식별자는 탈퇴 시 NULL, CI 해시는 6개월 후 NULL, 통계 컬럼과 외부 분석 삭제 요청·완료 확인 일시는 계속 유지', ldel=False, pii=True,
 cols=M,
 idx=['UK `UK_MBR_MEMBER_MEMBER_NO`, `UK_MBR_MEMBER_EMAIL_HASH`, `UK_MBR_MEMBER_MOBILE_PHONE_NUMBER_HASH`, `UK_MBR_MEMBER_CI_HASH`, `UK_MBR_MEMBER_NICKNAME_NM`, `UK_MBR_MEMBER_ANALYTICS_IDENTIFIER_VAL`', 'IX `IX_MBR_MEMBER_MEMBER_NAME_BIRTH_DATE_HASH` (관리자 이름·생년월일 검색) [확정 2026-11-22]',
      'IX `IX_MBR_MEMBER_GRADE_ID`, `IX_MBR_MEMBER_LAST_LOGIN_AT` (휴면 배치), `IX_MBR_MEMBER_BIRTH_MONTH_DAY_VAL` (생일 쿠폰), `IX_MBR_MEMBER_MEMBER_STATUS_CD`, `IX_MBR_MEMBER_WITHDRAWAL_SCHEDULED_DT`'],
 check=['상태가 `WITHDRAWN`이면 `EMAIL_HASH`, `MOBILE_PHONE_NUMBER_HASH`는 NULL'],
))

# ---------------------------------------------------------------- 4 MBR_LOGIN_ACCOUNT
T.append(dict(
 t='MBR_LOGIN_ACCOUNT', ko='회원 로그인 수단 계정 (이메일·소셜)', en='Member Login Method Account (Email and Social)',
 desc='회원 1명이 가진 로그인 수단마다 1행 (1번 B). 이메일 행에만 비밀번호·재설정 토큰·로그인 실패 정보가 있다 (3-3, 6-3, 8-1). 탈퇴 확정 시 물리 삭제 (28-3).',
 basis='1, 2, 3, 6, 8, 28-3, 29, 30', pk='대리 PK `SEQ_MBR_LOGIN_ACCOUNT`', cache=20, delete='물리 삭제 (회원 소유 목록)', part='없음', keep='-', ldel=False, pii=False,
 cols=[
 ('LOGIN_ACCOUNT_ID','로그인 수단 계정 고유 식별 번호','Login Method Account Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','로그인 수단 소유 회원 식별 번호','Owner Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('LOGIN_TYPE_CD','로그인 수단 유형 코드','Login Method Type Code','VARCHAR2(20)','N','','CK (값 목록)','이메일, 카카오, 네이버, 구글, 애플 (3-2).'),
 ('EXTERNAL_ACCOUNT_IDENTIFIER_VAL','소셜 로그인 제공자 사용자 식별 값','Social Provider User Identifier Value','VARCHAR2(255)','Y','','CK (이메일 행은 NULL, 소셜 행은 필수)','소셜 제공자가 준 사용자 ID. 평문 (25-1에서 암호화 대상 아님). 이메일 행은 회원 테이블의 이메일 해시로 로그인하므로 NULL. [확인 필요: UK 방식]'),
 ('PASSWORD_HASH','로그인 비밀번호 해시 (Argon2id)','Login Password Hash (Argon2id)','VARCHAR2(255)','Y','','CK (이메일 행만)','Argon2id 결과 문자열 (솔트·파라미터 포함). [확인 필요: `_HASH` 타입 규칙]'),
 ('PREVIOUS_PASSWORD_HASH','직전 로그인 비밀번호 해시','Previous Login Password Hash','VARCHAR2(255)','Y','','','직전 비밀번호 재사용 금지용 (6-2 B).'),
 ('PASSWORD_CHANGED_AT','로그인 비밀번호 최종 변경 일시','Login Password Last Changed At',TS,'Y','','',''),
 ('PASSWORD_CHANGE_NEXT_NOTICE_DT','비밀번호 변경 권고 다음 안내 일자','Next Password Change Recommendation Notice Date','DATE','Y','','','90일 주기 안내, "다음에 하기"면 미룸 (6-1 B).'),
 ('PASSWORD_RESET_TOKEN_HASH','비밀번호 재설정 링크 토큰 해시','Password Reset Link Token Hash','RAW(32)','Y','','','토큰 원문은 저장하지 않음. 사용·만료 시 NULL (6-3 C).'),
 ('PASSWORD_RESET_TOKEN_EXPIRES_AT','비밀번호 재설정 토큰 만료 일시','Password Reset Token Expires At',TS,'Y','','',''),
 ('CONSECUTIVE_LOGIN_FAIL_CNT','비밀번호 로그인 연속 실패 횟수','Consecutive Password Login Failure Count','NUMBER(2)','N','0','CK (>= 0)','이메일 행만 사용 (8-1 B). 성공하면 0.'),
 ('LOGIN_LOCKED_AT','비밀번호 로그인 잠금 일시','Password Login Locked At',TS,'Y','','','본인인증으로만 해제 (30-3 B).'),
 ('LAST_LOGIN_AT','이 로그인 수단의 최근 로그인 일시','Last Login At via This Method',TS,'Y','','','수단별 사용 현황. [제안: 결정 항목 아님]'),
 ],
 idx=['UK `UK_MBR_LOGIN_ACCOUNT_MEMBER_ID_LOGIN_TYPE_CD` (MEMBER_ID, LOGIN_TYPE_CD): 회원당 수단별 1행',
      '함수 기반 UK: 소셜 행만 (LOGIN_TYPE_CD, EXTERNAL_ACCOUNT_IDENTIFIER_VAL) 유일. [확인 필요]', 'IX `IX_MBR_LOGIN_ACCOUNT_MEMBER_ID`'],
 check=['`LOGIN_TYPE_CD = EMAIL`이면 `EXTERNAL_ACCOUNT_IDENTIFIER_VAL` NULL, 아니면 NOT NULL', '비밀번호·토큰·실패 컬럼은 이메일 행에서만 값을 가짐'],
))

# ---------------------------------------------------------------- 5 MBR_REFRESH_TOKEN
T.append(dict(
 t='MBR_REFRESH_TOKEN', ko='회원 기기별 리프레시 토큰 (순환 발급)', en='Member Per-Device Refresh Token (Rotating)',
 desc='로그인 세션(기기)마다 리프레시 토큰을 저장한다 (7-1 B, 7-2 A). 재발급마다 새 행을 만들고 이전 행은 사용 처리하며, 이미 쓴 토큰이 다시 오면 같은 계열을 모두 폐기한다 (7-3 B).',
 basis='7, 선행 결정 9', pk='대리 PK `SEQ_MBR_REFRESH_TOKEN`', cache=100, delete='만료·폐기 행을 배치로 나눠 DELETE (선행 결정 11-5). 탈퇴 시 즉시 삭제 (28-4)', part='없음', keep='만료 후 정리 주기는 배치에서 정함', ldel=False, pii=False,
 cols=[
 ('REFRESH_TOKEN_ID','리프레시 토큰 고유 식별 번호','Refresh Token Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','토큰 소유 회원 식별 번호','Owner Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('DEVICE_ID','토큰 발급 기기 식별 번호','Issued Device Identifier',ID,'N','','FK → `MBR_DEVICE`','기기별 로그아웃에 쓴다.'),
 ('TOKEN_HASH','리프레시 토큰 해시','Refresh Token Hash','RAW(32)','N','','UK','토큰 원문은 저장하지 않음.'),
 ('TOKEN_FAMILY_IDENTIFIER_VAL','토큰 순환 계열 식별 값','Token Rotation Family Identifier Value','VARCHAR2(36)','N','','','최초 로그인 때 만든 UUID. 재발급 토큰이 같은 값을 이어받는다. 재사용 감지 시 이 값으로 일괄 폐기.'),
 ('ISSUED_AT','토큰 발급 일시','Token Issued At',TS,'N','SYSTIMESTAMP','',''),
 ('TOKEN_EXPIRES_AT','토큰 만료 일시','Token Expires At',TS,'N','','',''),
 ('ROTATED_AT','토큰 재발급(사용) 처리 일시','Token Rotated At',TS,'Y','','','새 토큰으로 바뀐 시각. 이 값이 있는 토큰이 다시 오면 재사용으로 판단.'),
 ('REVOKED_AT','토큰 폐기 일시','Token Revoked At',TS,'Y','','',''),
 ('REVOCATION_REASON_CD','토큰 폐기 사유 코드','Token Revocation Reason Code','VARCHAR2(30)','Y','','CK (값 목록)',''),
 ('ISSUED_IP','토큰 발급 요청 IP 주소','Token Issued Request IP Address','VARCHAR2(45)','Y','','','IPv6까지 45자.'),
 ],
 idx=['UK `UK_MBR_REFRESH_TOKEN_TOKEN_HASH`', 'IX `IX_MBR_REFRESH_TOKEN_TOKEN_FAMILY_IDENTIFIER_VAL`', 'IX `IX_MBR_REFRESH_TOKEN_MEMBER_ID`, `IX_MBR_REFRESH_TOKEN_DEVICE_ID`', 'IX `IX_MBR_REFRESH_TOKEN_TOKEN_EXPIRES_AT` (정리 배치)'],
 check=['`REVOKED_AT`이 있으면 `REVOCATION_REASON_CD` 필수'],
))

# ---------------------------------------------------------------- 6 MBR_DEVICE
T.append(dict(
 t='MBR_DEVICE', ko='회원 로그인 기기 및 브라우저', en='Member Login Device and Browser',
 desc='앱·PC·모바일 웹으로 로그인한 기기마다 1행 (9-1 B, 9-2 B). 앱 푸시 토큰, OS 알림 허용 여부, 앱 생체 인증 공개 키를 담는다.',
 basis='9, 41-3, 선행 결정 10', pk='대리 PK `SEQ_MBR_DEVICE`', cache=20, delete='물리 삭제 (회원 소유 목록). 오래 접속하지 않은 웹 행은 배치 정리 (기간은 배치에서 정함)', part='없음', keep='-', ldel=False, pii=False,
 cols=[
 ('DEVICE_ID','회원 기기 고유 식별 번호','Member Device Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','기기 소유 회원 식별 번호','Owner Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('DEVICE_IDENTIFIER_VAL','기기 또는 브라우저 고유 식별 값','Device or Browser Identifier Value','VARCHAR2(100)','N','','UK (회원별)','앱 설치 ID 또는 브라우저 쿠키 ID.'),
 ('CHANNEL_CD','기기 판매 채널 코드','Device Sales Channel Code','VARCHAR2(20)','N','','CK (PC/MOBILE_WEB/APP)',''),
 ('OS_CD','기기 운영체제 코드','Device Operating System Code','VARCHAR2(20)','Y','','','`CMM_CODE`(OS 그룹).'),
 ('OS_VER','기기 운영체제 버전','Device Operating System Version','VARCHAR2(30)','Y','','',''),
 ('APP_VER','설치된 앱 버전','Installed App Version','VARCHAR2(30)','Y','','','앱 행만. 최소 버전 안내는 `SYS_APP_VERSION`과 비교.'),
 ('PUSH_TOKEN_VAL','앱 푸시 발송 토큰','App Push Delivery Token','VARCHAR2(500)','Y','','','앱 행만. 웹 행은 NULL. 평문 (25-1에서 암호화 대상 아님).'),
 yn('OS_NOTIFICATION_ALLOWED_YN','기기 운영체제 알림 허용 여부','OS Notification Allowed Flag','N','실제 발송 가능 여부. 법적 광고 동의는 회원 테이블 (9-3 C).'),
 yn('BIOMETRIC_REGISTERED_YN','앱 생체 인증 등록 여부','App Biometric Authentication Registered Flag','N','41-3 B.'),
 ('BIOMETRIC_PUBLIC_KEY_VAL','앱 생체 인증 기기 공개 키','App Biometric Device Public Key','VARCHAR2(2000)','Y','','','결제 승인 요청 서명 검증용. 생체 정보 자체는 저장하지 않음.'),
 ('BIOMETRIC_REGISTERED_AT','앱 생체 인증 등록 일시','App Biometric Registered At',TS,'Y','','',''),
 ('LAST_ACCESSED_AT','기기 최근 접속 일시','Device Last Accessed At',TS,'N','SYSTIMESTAMP','',''),
 ],
 idx=['UK `UK_MBR_DEVICE_MEMBER_ID_DEVICE_IDENTIFIER_VAL`', 'IX `IX_MBR_DEVICE_LAST_ACCESSED_AT` (정리 배치)'],
 check=['`BIOMETRIC_REGISTERED_YN = Y`이면 공개 키 필수'],
))

# ---------------------------------------------------------------- 7 MBR_IDENTITY_VERIFICATION_LOG
T.append(dict(
 t='MBR_IDENTITY_VERIFICATION_LOG', ko='본인인증 외부 연동 로그', en='Identity Verification External Interface Log',
 desc='휴대폰 본인확인·간편인증 업체와 주고받은 요청·결과 (선행 결정 6-5, 13-2). 가입 전 요청도 있어 회원 ID는 비어 있을 수 있다.',
 basis='선행 결정 6-5, 13-2, 28-15', pk='대리 PK `SEQ_MBR_IDENTITY_VERIFICATION_LOG`', cache=100, delete='로그: 파티션 제거', part='월 단위 INTERVAL 파티션 (요청 일시)', keep='1년 (28-15)', ldel=False, pii=False,
 cols=[
 ('IDENTITY_VERIFICATION_LOG_ID','본인인증 로그 고유 식별 번호','Identity Verification Log Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','본인인증 대상 회원 식별 번호','Target Member Identifier',ID,'Y','','FK → `MBR_MEMBER`','가입 전·비회원 요청은 NULL.'),
 ('VERIFICATION_PURPOSE_CD','본인인증 요청 목적 코드','Verification Purpose Code','VARCHAR2(30)','N','','CK (값 목록)',''),
 ('VERIFICATION_METHOD_CD','본인인증 수단 코드','Verification Method Code','VARCHAR2(30)','N','','CK (값 목록)','휴대폰 본인확인, 간편인증 (13-2 B).'),
 ('EXTERNAL_VENDOR_ID','본인인증 업체 식별 번호','Verification Vendor Identifier',ID,'N','','FK → `SYS_EXTERNAL_VENDOR` (후보)',''),
 ('VENDOR_TRANSACTION_NO','본인인증 업체 거래 번호','Vendor Transaction Number','VARCHAR2(100)','Y','','','업체 대사용.'),
 ('VERIFICATION_RESULT_CD','본인인증 결과 코드','Verification Result Code','VARCHAR2(20)','N',"'REQUESTED'",'CK (값 목록)',''),
 ('FAIL_REASON_DESC','본인인증 실패 사유','Verification Failure Reason Description','VARCHAR2(500)','Y','','','업체가 준 실패 코드와 메시지. 개인정보는 마스킹.'),
 ('CI_HASH','인증 결과 연계 정보 해시','Verified Connecting Information Hash','RAW(32)','Y','','','성공 시 CI의 HMAC. 가입 중복 검사와 회원 대조에 쓴다.'),
 ('REQUESTED_AT','본인인증 요청 일시','Verification Requested At',TS,'N','SYSTIMESTAMP','','파티션 키.'),
 ('COMPLETED_AT','본인인증 완료 일시','Verification Completed At',TS,'Y','','',''),
 ('REQUEST_IP','본인인증 요청 IP 주소','Verification Request IP Address','VARCHAR2(45)','Y','','',''),
 ],
 idx=['IX `IX_MBR_IDENTITY_VERIFICATION_LOG_MEMBER_ID` (LOCAL)', 'IX `IX_MBR_IDENTITY_VERIFICATION_LOG_VENDOR_TRANSACTION_NO` (LOCAL)'],
 check=[],
))

# ---------------------------------------------------------------- 8 MBR_MEMBER_GRADE_CHANGE_HIST
T.append(dict(
 t='MBR_MEMBER_GRADE_CHANGE_HIST', ko='회원 등급 변경 이력 (산정 근거 포함)', en='Member Grade Change History with Evaluation Basis',
 desc='회원 등급이 바뀔 때마다 1행. 산정 월, 이전·신규 등급, 산정 금액, 변경 사유를 남긴다 (35-5 C). 대량 도메인이라 전용 이력 테이블 (선행 결정 6).',
 basis='14, 35-5', pk='대리 PK `SEQ_MBR_MEMBER_GRADE_CHANGE_HIST`', cache=100, delete='이력: 삭제하지 않음 (보유 기간은 [확인 필요])', part='월 단위 INTERVAL 파티션 (변경 일시)', keep='[확인 필요: 결정 항목 없음]', ldel=False, pii=False,
 cols=[
 ('MEMBER_GRADE_CHANGE_HIST_ID','회원 등급 변경 이력 고유 식별 번호','Member Grade Change History Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','등급이 바뀐 회원 식별 번호','Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('EVALUATION_YM','등급 산정 기준 연월','Grade Evaluation Year Month','VARCHAR2(6)','Y','','CK (`YYYYMM`)','월 배치 산정분. 수동·병합 변경은 NULL.'),
 ('PREVIOUS_GRADE_ID','변경 전 등급 기준 버전 식별 번호','Previous Grade Version Identifier',ID,'Y','','FK → `MBR_GRADE`','가입 때 첫 등급은 NULL.'),
 ('NEW_GRADE_ID','변경 후 등급 기준 버전 식별 번호','New Grade Version Identifier',ID,'N','','FK → `MBR_GRADE`',''),
 ('EVALUATED_PURCHASE_CONFIRMED_AMT','산정에 쓴 구매 확정 금액 (원화)','Evaluated Purchase Confirmed Amount (KRW)','NUMBER(15)','Y','','','배치 산정 때의 최근 12개월 금액.'),
 ('CHANGE_REASON_CD','등급 변경 사유 코드','Grade Change Reason Code','VARCHAR2(30)','N','','CK (값 목록)',''),
 ('CHANGED_AT','등급 변경 일시','Grade Changed At',TS,'N','SYSTIMESTAMP','','파티션 키.'),
 ('CHANGE_MEMO_DESC','등급 변경 메모','Grade Change Memo','VARCHAR2(500)','Y','','','수동 조정 사유 등.'),
 ],
 idx=['IX `IX_MBR_MEMBER_GRADE_CHANGE_HIST_MEMBER_ID` (LOCAL)'], check=[],
))

# ---------------------------------------------------------------- 9 MBR_MEMBER_TAG
T.append(dict(
 t='MBR_MEMBER_TAG', ko='회원과 마케팅 태그 연결', en='Member to Marketing Tag Mapping',
 desc='회원에게 붙인 마케팅 태그. 단순 연결이라 복합 PK (선행 결정 1).',
 basis='11-1 보충 B, 11-5 B', pk='복합 PK (MEMBER_ID, TAG_ID)', cache='-', delete='물리 삭제 (단순 매핑). 탈퇴 시 즉시 (28-4)', part='없음', keep='-', ldel=False, pii=False,
 cols=[
 ('MEMBER_ID','태그가 붙은 회원 식별 번호','Tagged Member Identifier',ID,'N','','PK, FK → `MBR_MEMBER`',''),
 ('TAG_ID','회원에게 붙인 태그 식별 번호','Assigned Tag Identifier',ID,'N','','PK, FK → `MBR_TAG`',''),
 ],
 idx=['IX `IX_MBR_MEMBER_TAG_TAG_ID` (태그별 회원 추출)'], check=[],
))

# ---------------------------------------------------------------- 10
T.append(dict(
 t='MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT', ko='임직원 연도별 할인 한도 및 사용액', en='Employee Annual Discount Limit and Usage',
 desc='임직원 회원의 연도별 할인 한도와 사용액 (11-4 C). 연도마다 1행.',
 basis='11-4', pk='대리 PK `SEQ_MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT` + UK', cache=20, delete='[확인 필요: 결정 항목 없음]', part='없음', keep='[확인 필요]', ldel=False, pii=False,
 cols=[
 ('EMPLOYEE_ANNUAL_DISCOUNT_LIMIT_ID','임직원 연도별 할인 한도 고유 식별 번호','Employee Annual Discount Limit Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','임직원 회원 식별 번호','Employee Member Identifier',ID,'N','','FK → `MBR_MEMBER`, UK1',''),
 ('DISCOUNT_YEAR_VAL','할인 한도 적용 연도','Discount Limit Year','NUMBER(4)','N','','UK1, CK (2020~2100)',''),
 ('ANNUAL_DISCOUNT_LIMIT_AMT','연간 임직원 할인 한도 금액 (원화)','Annual Employee Discount Limit Amount (KRW)','NUMBER(15)','N','','CK (>= 0)',''),
 ('USED_DISCOUNT_AMT','연간 임직원 할인 사용 금액 (원화)','Used Employee Discount Amount (KRW)','NUMBER(15)','N','0','CK (0 ~ 한도)','주문 때 더하고 취소·반품 때 뺀다. 상세 근거는 주문 상품 할인 배분 테이블 (15-5).'),
 ],
 idx=['UK `UK_MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT_MEMBER_ID_DISCOUNT_YEAR_VAL`'], check=['`USED_DISCOUNT_AMT <= ANNUAL_DISCOUNT_LIMIT_AMT`'],
))

# ---------------------------------------------------------------- 11 MBR_SANCTION
T.append(dict(
 t='MBR_SANCTION', ko='회원 기능별 제재', en='Member Function-Level Sanction',
 desc='제재 1건마다 1행 (12-1 C). 현재 유효한 제재는 회원 테이블 Y/N 캐시에 반영한다 (12번 보충 B). 연속 결제 실패 자동 제한은 생성자 유형 `SYSTEM`으로 기록 (46-2).',
 basis='12, 46-2', pk='대리 PK `SEQ_MBR_SANCTION`', cache=20, delete='이력: 삭제하지 않음 ([확인 필요] 보유 기간)', part='없음', keep='[확인 필요]', ldel=False, pii=False,
 cols=[
 ('SANCTION_ID','회원 제재 고유 식별 번호','Member Sanction Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','제재 대상 회원 식별 번호','Sanctioned Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('RESTRICTION_TYPE_CD','제재 제한 기능 유형 코드','Restricted Function Type Code','VARCHAR2(30)','N','','CK (값 목록)','12-2: 주문, 쿠폰·적립금, 리뷰, 결제, 문의 + 전체 정지(`ACCOUNT_SUSPENSION`). 전체 정지 행이 유효하면 회원 상태를 `SUSPENDED`로 둔다 (12-2 변경 [확정 2026-11-22]).'),
 ('SANCTION_START_AT','제재 시작 일시','Sanction Start At',TS,'N','','',''),
 ('SANCTION_END_AT','제재 종료 예정 일시','Sanction Scheduled End At',TS,'Y','','CK (>= 시작)','NULL이면 무기한.'),
 ('SANCTION_REASON_CD','제재 사유 코드','Sanction Reason Code','VARCHAR2(30)','N','','','`CMM_CODE`(제재 사유 그룹). 예: 반품 남용, 결제 연속 실패, 부정 사용.'),
 ('SANCTION_MEMO_DESC','제재 처리 메모','Sanction Processing Memo','VARCHAR2(1000)','Y','','',''),
 ('RELEASED_AT','제재 조기 해제 일시','Sanction Early Release At',TS,'Y','','','종료 예정 전에 관리자가 해제한 시각.'),
 ('RELEASED_BY_TYPE_CD','제재 조기 해제 행위자 유형 코드','Sanction Early Release Actor Type Code','VARCHAR2(20)','Y','','CK (행위자 유형 6개)','조기 해제한 주체의 유형 (선행 결정 8). 보통 `ADMIN`. `RELEASED_AT`과 함께 채운다. 해제 뒤 행을 다시 수정해도 `UPDATED_BY`와 달리 바뀌지 않는다. [확정 2026-11-22]'),
 ('RELEASED_BY','제재 조기 해제 행위자 식별자','Sanction Early Release Actor Identifier','VARCHAR2(100)','Y','','','조기 해제한 관리자 ID 등 (선행 결정 8). 정지를 건 사람은 `CREATED_BY`. [확정 2026-11-22]'),
 ('RELEASE_REASON_DESC','제재 조기 해제 사유','Sanction Early Release Reason','VARCHAR2(500)','Y','','',''),
 ],
 idx=['IX `IX_MBR_SANCTION_MEMBER_ID_SANCTION_END_AT`', 'IX `IX_MBR_SANCTION_SANCTION_END_AT` (종료 캐시 갱신 배치)'], check=['`RELEASED_AT`이 있으면 `RELEASE_REASON_DESC` 필수', '`RELEASED_AT`, `RELEASED_BY_TYPE_CD`, `RELEASED_BY`는 모두 채우거나 모두 NULL [확정 2026-11-22]'],
))

# ---------------------------------------------------------------- 12 MBR_CONSENT_HIST
T.append(dict(
 t='MBR_CONSENT_HIST', ko='회원 약관·개인정보·광고 동의 및 철회 이력', en='Member Consent and Withdrawal History',
 desc='동의·철회할 때마다 1행 (17-2 B). 현재 상태는 회원 테이블 컬럼에 있다.',
 basis='17, 28-13', pk='대리 PK `SEQ_MBR_CONSENT_HIST`', cache=100, delete='이력: 탈퇴 후 5년 뒤 나눠서 DELETE (28-13 C)', part='[확인 필요] (행별 기한이라 파티션 제거 대상 아님)', keep='탈퇴 후 5년. 요청 IP는 탈퇴 확정 시 NULL (법률 L4)', ldel=False, pii=False,
 cols=[
 ('CONSENT_HIST_ID','동의 이력 고유 식별 번호','Consent History Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','동의한 회원 식별 번호','Consenting Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('CONSENT_ITEM_CD','동의 항목 코드','Consent Item Code','VARCHAR2(40)','N','','CK (값 목록)','17-3의 12개 항목: 필수 동의 1, 고지 확인 1, 통지 설정 1, 선택 동의 9 (법률 L7-1, L9-1, L9 후속).'),
 ('AGREED_YN','동의 여부 (Y 동의, N 철회)','Agreed Flag (Y Agree, N Withdraw)',YN,'N','','CK (Y/N)','고지 확인 행(`PRIVACY_NOTICE`)은 항상 Y (법률 L9-1). 이용·제공 내역 통지 행(`PRIVACY_USAGE_NOTICE`)은 Y = 통지 받음, N = 거부 (법률 L9 후속).'),
 ('TERMS_VER','동의 당시 약관·안내 문서 버전','Terms or Notice Version at Consent','VARCHAR2(20)','Y','','',''),
 ('CONSENT_PATH_CD','동의 경로 코드','Consent Path Code','VARCHAR2(30)','N','','CK (값 목록)','가입, 마이페이지, 이벤트, 2년 재확인, 결제수단·계좌 등록, 관리자 대리.'),
 ('CHANNEL_CD','동의 판매 채널 코드','Consent Sales Channel Code','VARCHAR2(20)','Y','','CK (PC/MOBILE_WEB/APP)',''),
 ('CONSENT_CHANGED_AT','동의 또는 철회 일시','Consent Changed At',TS,'N','SYSTIMESTAMP','',''),
 ('RESULT_NOTICE_SENT_AT','광고 수신 동의·철회 처리 결과 통지 발송 일시','Advertising Consent Result Notice Sent At',TS,'Y','','CK (테이블 수준)','광고 수신 항목(`ADVERTISING_SMS`, `ADVERTISING_EMAIL`, `ADVERTISING_PUSH`, `NIGHT_ADVERTISING`) 행만 채운다. 의사 표시일부터 14일 안에 전송자, 동의·거부·철회 사실과 날짜, 처리 결과를 알리고 발송 시각을 기록한다. 일 배치가 14일 안 미발송 행을 찾는다 (법률 L9-2, 정보통신망법 50조 7항, 시행령 62조의2). [확정 2026-11-22]'),
 ('REQUEST_IP','동의 요청 IP 주소','Consent Request IP Address','VARCHAR2(45)','Y','','','증빙용. 탈퇴 확정 시 NULL로 바꾸고, 동의·철회 사실은 5년 유지한다 (법률 L4).'),
 ],
 idx=['IX `IX_MBR_CONSENT_HIST_MEMBER_ID_CONSENT_ITEM_CD`'], check=['`CK_MBR_CONSENT_HIST_RESULT_NOTICE_SENT_AT`: 광고 수신 항목(`ADVERTISING_SMS`, `ADVERTISING_EMAIL`, `ADVERTISING_PUSH`, `NIGHT_ADVERTISING`)이 아니면 `RESULT_NOTICE_SENT_AT`은 NULL (법률 L9-2)'],
))

# ---------------------------------------------------------------- 13
T.append(dict(
 t='MBR_ADVERTISING_PLATFORM_SHARE_HIST', ko='외부 광고 플랫폼 회원 정보 제공 이력', en='Advertising Platform Member Information Share History',
 desc='맞춤형 광고를 위해 외부 광고 플랫폼에 회원을 보낸 이력 (38-10-1 C). 동의를 철회하면 이 테이블로 플랫폼을 찾아 삭제를 요청한다. 회원 × 플랫폼 × 세그먼트당 1행.',
 basis='38-10, 17-3', pk='대리 PK `SEQ_MBR_ADVERTISING_PLATFORM_SHARE_HIST` + UK', cache=20, delete='[확인 필요: 결정 항목 없음]', part='없음', keep='[확인 필요]', ldel=False, pii=False,
 cols=[
 ('ADVERTISING_PLATFORM_SHARE_HIST_ID','광고 플랫폼 제공 이력 고유 식별 번호','Advertising Platform Share History Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','제공 대상 회원 식별 번호','Shared Member Identifier',ID,'N','','FK → `MBR_MEMBER`, UK1',''),
 ('EXTERNAL_VENDOR_ID','광고 플랫폼 업체 식별 번호','Advertising Platform Vendor Identifier',ID,'N','','FK → `SYS_EXTERNAL_VENDOR` (후보), UK1',''),
 ('SEGMENT_CD','제공한 마케팅 세그먼트 코드','Shared Marketing Segment Code','VARCHAR2(50)','N','','UK1',''),
 ('FIRST_SHARED_AT','최초 제공 일시','First Shared At',TS,'N','','',''),
 ('LAST_SHARED_AT','최근 제공 일시','Last Shared At',TS,'N','','',''),
 ('DELETION_REQUESTED_AT','플랫폼 삭제 요청 일시','Platform Deletion Requested At',TS,'Y','','','동의 철회·개인화 거부·탈퇴 때.'),
 ('DELETION_CONFIRMED_AT','플랫폼 삭제 완료 확인 일시','Platform Deletion Confirmed At',TS,'Y','','',''),
 ],
 idx=['UK `UK_MBR_ADVERTISING_PLATFORM_SHARE_HIST_MEMBER_ID_EXTERNAL_VENDOR_ID_SEGMENT_CD`'], check=[],
))

# ---------------------------------------------------------------- 14 MBR_DELIVERY_ADDRESS
T.append(dict(
 t='MBR_DELIVERY_ADDRESS', ko='회원 배송지 주소록', en='Member Delivery Address Book',
 desc='회원이 등록한 배송지 (21-1 B). 기본 배송지는 함수 기반 UNIQUE 인덱스로 회원당 1개 (21-2 B). 주문에는 스냅샷이 남는다.',
 basis='21, 22, 28-4', pk='대리 PK `SEQ_MBR_DELIVERY_ADDRESS`', cache=20, delete='물리 삭제 (회원 소유 목록). 탈퇴 시 즉시', part='없음', keep='-', ldel=False, pii=False,
 cols=[
 ('DELIVERY_ADDRESS_ID','배송지 고유 식별 번호','Delivery Address Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','배송지 소유 회원 식별 번호','Owner Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('ADDRESS_ALIAS_NM','배송지 별칭','Delivery Address Alias Name','VARCHAR2(60)','Y','','','예: 집, 회사.'),
 ('RECIPIENT_NAME_ENC','수령인 이름 암호문','Recipient Name Ciphertext','RAW(179)','N','','',''),
 ('RECIPIENT_MOBILE_PHONE_NUMBER_ENC','수령인 휴대폰 번호 암호문','Recipient Mobile Phone Number Ciphertext','RAW(49)','N','','',''),
 ('POSTAL_CODE_VAL','우편번호 (5자리, 평문)','Postal Code (Five Digits, Plaintext)','VARCHAR2(5)','N','','CK (숫자 5자리)','도서산간은 주문 때마다 이 값으로 판단 (22-4 B).'),
 ('ROAD_ADDRESS_ENC','도로명 주소 암호문','Road Name Address Ciphertext','RAW(329)','N','','','평문 최대 300바이트 (22-2 B).'),
 ('LOT_NUMBER_ADDRESS_ENC','지번 주소 암호문','Lot Number Address Ciphertext','RAW(329)','Y','','',''),
 ('DETAIL_ADDRESS_ENC','상세 주소 암호문','Detail Address Ciphertext','RAW(229)','Y','','','평문 최대 200바이트.'),
 ('SIDO_CD','시도 코드 (평문)','Province Code (Plaintext)','VARCHAR2(2)','N','','','행정구역 시도 코드 (22-3 A). 지역 분석용.'),
 ('SIGUNGU_CD','시군구 코드 (평문)','District Code (Plaintext)','VARCHAR2(5)','N','','',''),
 yn('DEFAULT_YN','기본 배송지 여부','Default Delivery Address Flag','N','회원당 Y는 1개 (21-2 B).'),
 ('DELIVERY_REQUEST_DESC','배송 요청 사항','Delivery Request Note','VARCHAR2(300)','Y','','','예: 문 앞에 놓아 주세요. [제안: 결정 항목 아님]'),
 ],
 idx=['함수 기반 UK `UK_MBR_DELIVERY_ADDRESS_DEFAULT_YN` (CASE WHEN DEFAULT_YN = \'Y\' THEN MEMBER_ID END)', 'IX `IX_MBR_DELIVERY_ADDRESS_MEMBER_ID`'], check=[],
))

# ---------------------------------------------------------------- 15
T.append(dict(
 t='MBR_WISHLIST_ITEM', ko='회원 위시리스트 상품 (스타일 × 컬러)', en='Member Wishlist Item (Style by Color)',
 desc='회원이 찜한 상품. 단위는 스타일 × 컬러 (23-2 B). 단순 연결이라 복합 PK.',
 basis='23, 18-2', pk='복합 PK (MEMBER_ID, STYLE_COLOR_ID)', cache='-', delete='물리 삭제 (회원 소유 목록). 탈퇴 시 즉시', part='없음', keep='-', ldel=False, pii=False,
 cols=[
 ('MEMBER_ID','위시리스트 소유 회원 식별 번호','Owner Member Identifier',ID,'N','','PK, FK → `MBR_MEMBER`',''),
 ('STYLE_COLOR_ID','찜한 스타일 컬러 식별 번호','Wishlisted Style Color Identifier',ID,'N','','PK, FK → `PRD_STYLE_COLOR` (후보)',''),
 ('WISHLISTED_SALE_PRICE_AMT','찜할 당시 판매 가격 (원화)','Sale Price When Wishlisted (KRW)','NUMBER(15)','Y','','CK (>= 0)','가격 인하 알림 판단 기준 (18-2 B). [제안: 결정 항목 아님]'),
 ],
 idx=['IX `IX_MBR_WISHLIST_ITEM_STYLE_COLOR_ID` (가격 인하·재입고 대상 추출)'], check=[],
))

# ---------------------------------------------------------------- 16
T.append(dict(
 t='MBR_RECENTLY_VIEWED_ITEM', ko='회원 최근 본 상품 (스타일 × 컬러)', en='Member Recently Viewed Item (Style by Color)',
 desc='회원이 최근 본 상품 (선행 결정 9, 23-3 C). 같은 상품을 다시 보면 시각을 갱신한다. 화면에는 최근 50개, 30일 지난 행은 배치가 나눠서 삭제.',
 basis='23, 38-8', pk='복합 PK (MEMBER_ID, STYLE_COLOR_ID)', cache='-', delete='물리 삭제: 30일 경과 행 배치, 탈퇴 시 즉시', part='없음', keep='30일', ldel=False, pii=False,
 cols=[
 ('MEMBER_ID','상품을 본 회원 식별 번호','Viewer Member Identifier',ID,'N','','PK, FK → `MBR_MEMBER`',''),
 ('STYLE_COLOR_ID','본 스타일 컬러 식별 번호','Viewed Style Color Identifier',ID,'N','','PK, FK → `PRD_STYLE_COLOR` (후보)',''),
 ('LAST_VIEWED_AT','최근 조회 일시','Last Viewed At',TS,'N','SYSTIMESTAMP','',''),
 ('VIEW_CNT','30일 안 조회 횟수','View Count Within Retention Period','NUMBER(5)','N','1','CK (>= 1)','선호 추론 가중치에 쓴다 (38-3). [제안: 결정 항목 아님]'),
 ],
 idx=['IX `IX_MBR_RECENTLY_VIEWED_ITEM_MEMBER_ID_LAST_VIEWED_AT`', 'IX `IX_MBR_RECENTLY_VIEWED_ITEM_LAST_VIEWED_AT` (정리 배치)'], check=[],
))

# ---------------------------------------------------------------- 17
T.append(dict(
 t='MBR_PREFERENCE', ko='회원 취향 선호 점수 (차원 × 대상 × 출처)', en='Member Preference Score (Dimension by Target by Source)',
 desc='회원 취향을 차원·대상·출처별 점수(0~100)로 저장 (38-4 B, 38-5 C). 행동이 있을 때마다 즉시 갱신하고 시간 감쇠를 적용 (38-8).',
 basis='38', pk='대리 PK `SEQ_MBR_PREFERENCE` + UK', cache=100, delete='물리 삭제 ([확인 필요] 28-4 목록에 없음)', part='없음', keep='-', ldel=False, pii=False,
 cols=[
 ('PREFERENCE_ID','회원 선호 고유 식별 번호','Member Preference Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','선호 보유 회원 식별 번호','Member Identifier',ID,'N','','FK → `MBR_MEMBER`, UK1',''),
 ('PREFERENCE_DIMENSION_CD','취향 차원 코드','Preference Dimension Code','VARCHAR2(30)','N','','CK (값 목록), UK1','카테고리, 스타일 무드, 핏, 가격대 (38-1).'),
 ('TARGET_CD','코드형 선호 대상 값','Code-Type Preference Target','VARCHAR2(50)','Y','','UK1','무드·핏·가격대의 `CMM_CODE` 값.'),
 ('CATEGORY_ID','카테고리형 선호 대상 식별 번호','Category-Type Preference Target Identifier',ID,'Y','','FK → `PRD_CATEGORY` (후보), UK1','결정 때 이름은 `TARGET_ID`. FK는 참조 PK와 같은 이름을 쓰는 규칙에 따라 바꿔 제안.'),
 ('PREFERENCE_SCORE_VAL','선호 점수 (0~100)','Preference Score','NUMBER(5,2)','N','0','CK (0~100)','반품 음수 가중치는 0에서 멈춤.'),
 ('PREFERENCE_SOURCE_CD','선호 출처 코드','Preference Source Code','VARCHAR2(20)','N','','CK (값 목록), UK1','고객 선택과 행동 추론을 따로 저장 (38-7 B).'),
 ('LAST_CALCULATED_AT','선호 점수 최종 계산 일시','Preference Score Last Calculated At',TS,'N','SYSTIMESTAMP','','다음 갱신 때 경과 시간만큼 감쇠 (38-8-2 B).'),
 ],
 idx=['UK `UK_MBR_PREFERENCE_MEMBER_ID_PREFERENCE_DIMENSION_CD_TARGET_CD_CATEGORY_ID_PREFERENCE_SOURCE_CD` (이름 길이 125바이트, 줄임 여부 확인 필요)', 'IX `IX_MBR_PREFERENCE_PREFERENCE_DIMENSION_CD_TARGET_CD` (세그먼트 추출)'],
 check=['`TARGET_CD`와 `CATEGORY_ID` 중 정확히 하나만 값 (38-6 B)', '차원이 `CATEGORY`면 `CATEGORY_ID`, 아니면 `TARGET_CD`'],
))

# ---------------------------------------------------------------- 18
T.append(dict(
 t='MBR_PROFILE_IMAGE', ko='회원 프로필 이미지 (검수 포함)', en='Member Profile Image with Inspection',
 desc='회원 프로필 이미지와 검수 상태 (37-3 C). 교체하면 새 행을 만들고 이전 행의 현재 사용 여부를 N으로 바꾼다.',
 basis='37-3', pk='대리 PK `SEQ_MBR_PROFILE_IMAGE`', cache=20, delete='[확인 필요: 탈퇴 시 처리 결정 없음 (28-4 목록 밖)]', part='없음', keep='[확인 필요]', ldel=False, pii=False,
 cols=[
 ('PROFILE_IMAGE_ID','프로필 이미지 고유 식별 번호','Profile Image Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','이미지 소유 회원 식별 번호','Owner Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('IMAGE_URL','이미지 저장소 경로','Image Storage URL','VARCHAR2(1000)','N','','',''),
 ('IMAGE_FILE_SIZE_VAL','이미지 파일 크기 (바이트)','Image File Size in Bytes','NUMBER(10)','N','','CK (> 0)',''),
 ('IMAGE_WIDTH_VAL','이미지 가로 픽셀','Image Width in Pixels','NUMBER(5)','Y','','',''),
 ('IMAGE_HEIGHT_VAL','이미지 세로 픽셀','Image Height in Pixels','NUMBER(5)','Y','','',''),
 ('INSPECTION_STATUS_CD','이미지 검수 상태 코드','Image Inspection Status Code','VARCHAR2(20)','N',"'PENDING'",'CK (값 목록)',''),
 ('INSPECTOR_ADMIN_USER_ID','이미지 검수 관리자 식별 번호','Inspector Administrator Identifier',ID,'Y','','FK → `ADM_USER` (PK 이름은 관리자 도메인에서 확정)',''),
 ('INSPECTED_AT','이미지 검수 일시','Image Inspected At',TS,'Y','','',''),
 ('INSPECTION_REJECTION_REASON_DESC','이미지 검수 반려 사유','Image Inspection Rejection Reason','VARCHAR2(500)','Y','','',''),
 yn('CURRENT_YN','현재 사용 중인 프로필 이미지 여부','Current Profile Image Flag','N','회원당 Y는 1개 (함수 기반 UK).'),
 ],
 idx=['함수 기반 UK (CASE WHEN CURRENT_YN = \'Y\' THEN MEMBER_ID END)', 'IX `IX_MBR_PROFILE_IMAGE_INSPECTION_STATUS_CD` (검수 대기 목록)'], check=[],
))

# ---------------------------------------------------------------- 19
T.append(dict(
 t='MBR_SAVED_PAYMENT_METHOD', ko='회원 저장 결제수단 (PG 빌링키)', en='Member Saved Payment Method (PG Billing Key)',
 desc='자사 원클릭 결제용 카드 등록 정보 (40-1 D, 40-2 B). 카드번호는 PG가 보관하고 빌링키만 암호화해 저장한다. 삭제는 PG 빌링키 삭제 API 성공 후 물리 삭제, 실패하면 삭제 대기 상태로 두고 앱 배치가 재시도 (47-1 A).',
 basis='40, 42, 47', pk='대리 PK `SEQ_MBR_SAVED_PAYMENT_METHOD`', cache=20, delete='물리 삭제 (PG API 성공 후)', part='없음', keep='-', ldel=False, pii=False,
 cols=[
 ('SAVED_PAYMENT_METHOD_ID','저장 결제수단 고유 식별 번호','Saved Payment Method Unique Identifier',ID,'N','','PK',''),
 ('MEMBER_ID','결제수단 소유 회원 식별 번호','Owner Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('PAYMENT_AGENCY_CD','빌링키 발급 결제 대행사 코드','Billing Key Issuing Payment Agency Code','VARCHAR2(30)','N','','','복수 PG (선행 결정 13-1). 값 목록은 결제 도메인.'),
 ('PAYMENT_METHOD_TYPE_CD','저장 결제수단 유형 코드','Saved Payment Method Type Code','VARCHAR2(30)','N','','','예: 신용카드, 체크카드. 값 목록은 결제 도메인.'),
 ('BILLING_KEY_ENC','PG 빌링키 암호문','PG Billing Key Ciphertext','RAW(229)','N','','','평문 최대 200바이트 (25-1 A).'),
 ('CARD_COMPANY_CD','카드사 코드','Card Company Code','VARCHAR2(10)','Y','','','`CMM_CODE`(카드사 그룹).'),
 ('MASKED_CARD_NUMBER_VAL','PG가 준 마스킹 카드 번호','PG-Provided Masked Card Number','VARCHAR2(30)','Y','','','외부에서 받은 마스킹 값을 그대로 저장 (선행 결정 5).'),
 ('PAYMENT_METHOD_ALIAS_NM','결제수단 별칭','Payment Method Alias Name','VARCHAR2(60)','Y','','',''),
 yn('DEFAULT_YN','기본 결제수단 여부','Default Payment Method Flag','N','회원당 Y는 1개 (40-3 B).'),
 ('SAVED_PAYMENT_METHOD_STATUS_CD','저장 결제수단 상태 코드','Saved Payment Method Status Code','VARCHAR2(30)','N',"'ACTIVE'",'CK (값 목록)','사용 중, 삭제 대기 (47-1 A).'),
 ('BILLING_KEY_DELETION_RETRY_CNT','빌링키 삭제 API 재시도 횟수','Billing Key Deletion Retry Count','NUMBER(3)','N','0','CK (>= 0)',''),
 ('LAST_DELETION_ATTEMPTED_AT','빌링키 삭제 최근 시도 일시','Billing Key Deletion Last Attempted At',TS,'Y','','',''),
 ],
 idx=['함수 기반 UK (CASE WHEN DEFAULT_YN = \'Y\' AND SAVED_PAYMENT_METHOD_STATUS_CD = \'ACTIVE\' THEN MEMBER_ID END)', 'IX `IX_MBR_SAVED_PAYMENT_METHOD_MEMBER_ID`', 'IX `IX_MBR_SAVED_PAYMENT_METHOD_SAVED_PAYMENT_METHOD_STATUS_CD` (재시도 배치)'], check=[],
))

# ---------------------------------------------------------------- 20
T.append(dict(
 t='MBR_ACCOUNT_MERGE_HIST', ko='회원 계정 병합 이력', en='Member Account Merge History',
 desc='중복 계정을 병합할 때마다 1행 (29-4 B). 흡수된 계정과 남는 계정, 옮긴 금액·건수를 남긴다. 처리자는 생성자 컬럼.',
 basis='29', pk='대리 PK `SEQ_MBR_ACCOUNT_MERGE_HIST`', cache=20, delete='이력: 삭제하지 않음 ([확인 필요] 보유 기간)', part='없음', keep='[확인 필요]', ldel=False, pii=False,
 cols=[
 ('ACCOUNT_MERGE_HIST_ID','계정 병합 이력 고유 식별 번호','Account Merge History Unique Identifier',ID,'N','','PK',''),
 ('SOURCE_MEMBER_ID','흡수되는 회원 식별 번호','Source (Absorbed) Member Identifier',ID,'N','','FK → `MBR_MEMBER`','병합 후 상태 `MERGED`.'),
 ('TARGET_MEMBER_ID','남는 회원 식별 번호','Target (Surviving) Member Identifier',ID,'N','','FK → `MBR_MEMBER`',''),
 ('MERGED_AT','계정 병합 일시','Account Merged At',TS,'N','SYSTIMESTAMP','',''),
 ('MOVED_POINT_AMT','이전한 적립금 (원화)','Moved Point Amount (KRW)','NUMBER(15)','N','0','CK (>= 0)','원장 이동 거래 합계 (29-2 A).'),
 ('MOVED_DEPOSIT_AMT','이전한 예치금 (원화)','Moved Deposit Amount (KRW)','NUMBER(15)','N','0','CK (>= 0)',''),
 ('MOVED_COUPON_CNT','이전한 쿠폰 수','Moved Coupon Count','NUMBER(5)','N','0','CK (>= 0)',''),
 ('MOVED_ORDER_CNT','회원 ID를 바꾼 주문 수','Reassigned Order Count','NUMBER(7)','N','0','CK (>= 0)','29-3 B.'),
 ('MOVED_REVIEW_CNT','회원 ID를 바꾼 리뷰 수','Reassigned Review Count','NUMBER(7)','N','0','CK (>= 0)',''),
 ('MERGE_REASON_DESC','계정 병합 사유','Account Merge Reason','VARCHAR2(500)','Y','','',''),
 ],
 idx=['IX `IX_MBR_ACCOUNT_MERGE_HIST_SOURCE_MEMBER_ID`, `IX_MBR_ACCOUNT_MERGE_HIST_TARGET_MEMBER_ID`'], check=['`SOURCE_MEMBER_ID <> TARGET_MEMBER_ID`'],
))

CODES = {
 'AGE_GROUP_CD': [('AGE_14_19','14~19세','Age 14 to 19','만 14세 미만은 가입 불가 (13) [확정 2026-11-22]',1),('AGE_20_24','20~24세','Age 20 to 24','[확정 2026-11-22]',2),('AGE_25_29','25~29세','Age 25 to 29','[확정 2026-11-22]',3),('AGE_30_34','30~34세','Age 30 to 34','[확정 2026-11-22]',4),('AGE_35_39','35~39세','Age 35 to 39','[확정 2026-11-22]',5),('AGE_40_44','40~44세','Age 40 to 44','[확정 2026-11-22]',6),('AGE_45_49','45~49세','Age 45 to 49','[확정 2026-11-22]',7),('AGE_50_54','50~54세','Age 50 to 54','[확정 2026-11-22]',8),('AGE_55_59','55~59세','Age 55 to 59','[확정 2026-11-22]',9),('AGE_60_64','60~64세','Age 60 to 64','[확정 2026-11-22]',10),('AGE_65_OVER','65세 이상','Age 65 and Over','[확정 2026-11-22]',11)],
 'MOBILE_CARRIER_CD': [('SKT','SK텔레콤','SK Telecom','[확정 2026-11-22]',1),('KT','KT','KT','[확정 2026-11-22]',2),('LG_UPLUS','LG유플러스','LG U+','[확정 2026-11-22]',3),('SKT_MVNO','SKT 알뜰폰','SKT MVNO','SKT 망을 빌려 쓰는 알뜰폰 [확정 2026-11-22]',4),('KT_MVNO','KT 알뜰폰','KT MVNO','KT 망을 빌려 쓰는 알뜰폰 [확정 2026-11-22]',5),('LG_UPLUS_MVNO','LG유플러스 알뜰폰','LG U+ MVNO','LG유플러스 망을 빌려 쓰는 알뜰폰 [확정 2026-11-22]',6)],
 'MEMBER_STATUS_CD': [('ACTIVE','정상','Active','정상 이용 [확정 2026-11-22]',1),('DORMANT','휴면','Dormant','1년 미접속, 이름·연락처 분리 보관. 전체 정지 중이어도 휴면이 우선 [확정 2026-11-22]',2),('WITHDRAWAL_PENDING','탈퇴 유예','Withdrawal Pending','신청 후 7일, 철회 가능 [확정 2026-11-22]',3),('WITHDRAWN','탈퇴','Withdrawn','비식별화 완료 [확정 2026-11-22]',4),('MERGED','병합됨','Merged','다른 계정에 흡수. CI 도입 전 중복·기존 회원 이관·계열몰 통합에 대비해 유지 [확정 2026-11-22]',5),('SUSPENDED','정지','Suspended','모든 기능 정지. `MBR_SANCTION`의 전체 정지(`ACCOUNT_SUSPENSION`) 행이 유효할 때의 결과 상태. 휴면 해제 때 정지가 유효하면 이 상태로 복귀 [확정 2026-11-22]',6)],
 'GENDER_CD': [('MALE','남성','Male','[확정 2026-11-22]',1),('FEMALE','여성','Female','[확정 2026-11-22]',2)],
 'MEMBER_TYPE_CD': [('GENERAL','일반','General','',1),('INFLUENCER','인플루언서·앰배서더','Influencer','협찬·전용 할인',2),('VIP_MANUAL','수동 지정 VIP','Manual VIP','등급과 별개, 관리자 지정',3)],
 'QUALIFICATION_APPLICATION_TYPE_CD': [('INFLUENCER','인플루언서 자격','Influencer','',1),('EMPLOYEE','임직원 자격','Employee','',2)],
 'QUALIFICATION_APPROVAL_STATUS_CD': [('APPLIED','신청','Applied','',1),('APPROVED','승인','Approved','',2),('REJECTED','반려','Rejected','',3),('EXPIRED','만료','Expired','',4)],
 'LAST_LOGIN_CHANNEL_CD / JOIN_CHANNEL_CD / CHANNEL_CD': [('PC','PC','PC','',1),('MOBILE_WEB','모바일 웹','Mobile Web','',2),('APP','앱','App','',3)],
 'BODY_REVIEW_DISCLOSURE_CD': [('PUBLIC','정확한 수치 공개','Public','',1),('RANGE','구간으로 공개','Range','기본값',2),('PRIVATE','비공개','Private','',3)],
 'REFUND_ACCOUNT_VERIFICATION_RESULT_CD': [('VERIFIED','인증 성공','Verified','',1),('FAILED','인증 실패','Failed','',2)],
 'CASH_RECEIPT_PURPOSE_CD': [('INCOME_DEDUCTION','소득공제','Income Deduction','',1),('EXPENSE_PROOF','지출증빙','Expense Proof','',2)],
 'CASH_RECEIPT_IDENTIFIER_TYPE_CD': [('MOBILE_PHONE','휴대폰 번호','Mobile Phone','',1),('CASH_RECEIPT_CARD','현금영수증 카드','Cash Receipt Card','',2),('BUSINESS_REGISTRATION','사업자등록번호','Business Registration','',3)],
 'LOGIN_TYPE_CD': [('EMAIL','이메일','Email','',1),('KAKAO','카카오','Kakao','',2),('NAVER','네이버','Naver','',3),('GOOGLE','구글','Google','',4),('APPLE','애플','Apple','',5)],
 'REVOCATION_REASON_CD': [('LOGOUT','로그아웃','Logout','',1),('LOGOUT_ALL','다른 기기 모두 로그아웃','Logout All','',2),('REUSE_DETECTED','재사용 감지','Reuse Detected','계열 전체 폐기',3),('PASSWORD_CHANGED','비밀번호 변경','Password Changed','',4),('WITHDRAWN','탈퇴','Withdrawn','',5),('ADMIN','관리자 강제','Admin','',6)],
 'VERIFICATION_PURPOSE_CD': [('JOIN','가입','Join','',1),('FIND_EMAIL','아이디 찾기','Find Email','',2),('RESET_PASSWORD','비밀번호 재설정','Reset Password','',3),('UNLOCK_LOGIN','로그인 잠금 해제','Unlock Login','',4),('RELEASE_DORMANT','휴면 해제','Release Dormant','',5),('RECOVER_SOCIAL','소셜 계정 복구','Recover Social','',6),('UNLOCK_PAYMENT_PIN','결제 비밀번호 잠금 해제','Unlock Payment PIN','',7),('GUEST_ORDER','비회원 주문 조회','Guest Order','선행 결정 14-3',8)],
 'VERIFICATION_METHOD_CD': [('MOBILE_PHONE','휴대폰 본인확인','Mobile Phone','',1),('SIMPLE_AUTHENTICATION','간편인증','Simple Authentication','',2)],
 'VERIFICATION_RESULT_CD': [('REQUESTED','요청','Requested','',1),('SUCCESS','성공','Success','',2),('FAIL','실패','Fail','',3),('CANCELED','고객 취소','Canceled','',4)],
 'CHANGE_REASON_CD (등급 이력)': [('JOIN','가입 첫 등급','Join','',1),('BATCH','월 배치 승급','Batch','',2),('MANUAL','관리자 수동 지정','Manual','',3),('MANUAL_EXPIRED','수동 등급 만료 복귀','Manual Expired','',4),('MERGE','계정 병합','Merge','',5)],
 'RESTRICTION_TYPE_CD': [('ORDER','주문','Order','',1),('COUPON_POINT','쿠폰·적립금 사용','Coupon and Point','',2),('REVIEW','리뷰 작성','Review','',3),('PAYMENT','결제','Payment','',4),('INQUIRY','문의 작성','Inquiry','',5),('ACCOUNT_SUSPENSION','전체 정지','Account Suspension','모든 기능 정지. 기간·사유는 이 제재 행에 두고, 회원 상태 `SUSPENDED`로 반영 [확정 2026-11-22]',6)],
 'CONSENT_ITEM_CD': [('TERMS_OF_SERVICE','이용약관','Terms of Service','필수',1),('PRIVACY_NOTICE','개인정보 수집·이용 고지 확인','Personal Information Collection Notice Confirmation','고지 확인 (동의 아님). 계약 이행 근거라 철회 대상이 아니며 동의 여부는 항상 Y. 결정 때 코드는 `PRIVACY_COLLECTION` (법률 L9-1)',2),('PRIVACY_USAGE_NOTICE','개인정보 이용·제공 내역 통지','Personal Information Usage Notice','통지 설정 (동의 아님). 동의 여부 N = 통지 거부. 개인정보 보호법 20조의2 (법률 L9 후속)',3)] + [(p, ko, en, '선택', i+4) for i, (p, ko, en) in enumerate(CONSENT)],
 'CONSENT_PATH_CD': [('JOIN','가입','Join','',1),('MY_PAGE','마이페이지','My Page','',2),('EVENT','이벤트','Event','',3),('RECONFIRMATION','2년 재확인','Reconfirmation','',4),('REGISTRATION','계좌·결제수단 등록','Registration','',5),('ADMIN_PROXY','관리자 대리','Admin Proxy','',6),('WITHDRAWAL','탈퇴 처리','Withdrawal','',7)],
 'PREFERENCE_DIMENSION_CD': [('CATEGORY','카테고리','Category','`CATEGORY_ID` 사용',1),('STYLE_MOOD','스타일 무드','Style Mood','',2),('FIT','핏','Fit','상의·하의 구분은 코드값으로',3),('PRICE_RANGE','가격대','Price Range','',4)],
 'PREFERENCE_SOURCE_CD': [('EXPLICIT','고객 선택','Explicit','고정 점수 80',1),('INFERRED','행동 추론','Inferred','',2)],
 'INSPECTION_STATUS_CD': [('PENDING','검수 대기','Pending','',1),('APPROVED','승인','Approved','',2),('REJECTED','반려','Rejected','',3)],
 'SAVED_PAYMENT_METHOD_STATUS_CD': [('ACTIVE','사용 중','Active','',1),('DELETION_PENDING','삭제 대기','Deletion Pending','PG API 재시도 중',2)],
}

CONFIRM = [
 ('이메일 변경 인증 대기값 (시스템 도메인)', '이메일 변경 시 새 주소는 인증이 끝날 때까지 `SYS_VERIFICATION_CODE`에 보관하고, 인증 후 회원 테이블 이메일을 교체한다 (2026-11-22 결정 B). 시스템 도메인을 설계할 때 이 테이블에 인증 대상 값(암호문) 컬럼을 넣어야 한다.', '`SYS_VERIFICATION_CODE` (시스템 도메인)'),
 ('비밀번호·PIN 해시 타입', '선행 결정 5에서 `_HASH`는 `RAW(32)`로 정했지만, 이는 HMAC 검색 해시 기준이다. Argon2id는 솔트·파라미터를 포함한 문자열이라 `VARCHAR2(255)`로 제안했다. 규칙 예외로 둘지, 분류어를 바꿀지 정해야 한다.', '`MBR_LOGIN_ACCOUNT.PASSWORD_HASH`, `PREVIOUS_PASSWORD_HASH`, `MBR_MEMBER.PAYMENT_PIN_HASH`'),
 ('로그인 계정 UK', '3-1은 UK (로그인 유형 + 외부 ID)였다. 이메일 행은 외부 ID가 NULL이라 Oracle에서 (EMAIL, NULL)이 서로 중복으로 처리된다. 소셜 행만 검사하는 함수 기반 UK + (회원, 유형) UK로 제안했다.', '`MBR_LOGIN_ACCOUNT`'),
 ('회원 ↔ 저장 결제수단 순환 FK', '회원이 결제수단을, 결제수단이 회원을 참조한다. 생성 순서와 삭제 처리(ON DELETE SET NULL)를 정해야 한다. FK를 걸지 않는 방법도 있다.', '`MBR_MEMBER.LAST_SAVED_PAYMENT_METHOD_ID`'),
 ('탈퇴 시 처리 미결정 테이블', '28-4 목록(즉시 물리 삭제)은 프로필 이미지·선호 정보·임직원 할인 한도·광고 제공 이력·제재·병합 이력·등급 이력이 정해지기 전이었다.', '`MBR_PROFILE_IMAGE`, `MBR_PREFERENCE` 외 5개'),
 ('보유 기간 미결정 테이블', '등급 이력, 제재, 병합 이력, 광고 제공 이력, 임직원 할인 한도의 보유 기간은 결정 항목이 없었다.', '해당 테이블'),
 ('결정에 없던 제안 컬럼', '정의서를 만들며 필요해 보여 추가한 컬럼. 각 컬럼 설명에 [제안: 결정 항목 아님] 표시.', '`GRADE_APPLIED_AT`, `PURCHASE_STATISTICS_CALCULATED_AT`, `WITHDRAWAL_REASON_CD`, `MBR_LOGIN_ACCOUNT.LAST_LOGIN_AT`, `DELIVERY_REQUEST_DESC`, `WISHLISTED_SALE_PRICE_AMT`, `VIEW_CNT`'),
 ('결정 때와 이름을 바꾼 컬럼', '`PERSONALIZATION_YN` → `PERSONALIZATION_REJECTED_YN` (뜻 명확화), `TARGET_ID` → `CATEGORY_ID` (FK 이름 규칙), `REJOIN_BLOCK_UNTIL` → `REJOIN_BENEFIT_RESTRICTION_END_DT` (분류어 규칙, 39-1 C 반영).', '`MBR_MEMBER`, `MBR_PREFERENCE`'),
 ('다른 도메인 FK 이름', '`ADM_USER`, `PRD_STYLE_COLOR`, `PRD_CATEGORY`, `PRM_DISCOUNT_POLICY`, `SYS_EXTERNAL_VENDOR`의 PK 이름은 해당 도메인에서 확정한다. 지금 FK 이름은 임시다.', '여러 테이블'),
 ('암호문 길이', '`_ENC` 길이는 평문 최대 바이트 + 29로 계산했다. 평문 최대값(이름 150, 이메일 254, 주소 300 등)은 가정이다.', '`_ENC` 컬럼 전체'),
 ('고빈도 시퀀스 (CACHE 100)', '리프레시 토큰, 본인인증 로그, 등급 이력, 동의 이력, 선호 정보를 고빈도로 제안했다. 나머지는 20.', '해당 테이블'),
 ('긴 제약 이름', '`MBR_PREFERENCE`의 5컬럼 UK 이름은 125바이트로 128바이트 한도에 가깝다. 줄이는 규칙을 둘지 정해야 한다.', '`MBR_PREFERENCE`'),
]
