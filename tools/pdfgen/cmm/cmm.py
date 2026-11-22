import sys, os, html, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cols'))
from data import CODES, TS, ID
OUT = sys.argv[1]

def yn(p, ko, en, d, desc): return (p, ko, en, 'CHAR(1)', 'N', f"'{d}'", 'CK (Y/N)', desc)
SYS = [
 ('CREATED_BY_TYPE_CD','생성 행위자 유형 코드','Created By Actor Type Code','VARCHAR2(20)','N','','CK (행위자 유형 6개)','규칙 1, 선행 결정 8.'),
 ('CREATED_BY','생성 행위자 식별자','Created By Actor Identifier','VARCHAR2(100)','N','','','Flyway 시드는 `BATCH` + 마이그레이션 버전 등 [확인 필요].'),
 ('CREATED_AT','행 생성 일시','Created At',TS,'N','SYSTIMESTAMP','',''),
 ('UPDATED_BY_TYPE_CD','최종 수정 행위자 유형 코드','Updated By Actor Type Code','VARCHAR2(20)','Y','','CK (행위자 유형 6개)','수정 전에는 NULL (규칙 1).'),
 ('UPDATED_BY','최종 수정 행위자 식별자','Updated By Actor Identifier','VARCHAR2(100)','Y','','','수정 전에는 NULL (규칙 1).'),
 ('UPDATED_AT','행 최종 수정 일시','Updated At',TS,'Y','','','수정 전에는 NULL (규칙 1).'),
 ('DELETED_BY_TYPE_CD','삭제 행위자 유형 코드','Deleted By Actor Type Code','VARCHAR2(20)','Y','','CK (행위자 유형 6개)','마스터 테이블이라 논리 삭제 (선행 결정 4).'),
 ('DELETED_BY','삭제 행위자 식별자','Deleted By Actor Identifier','VARCHAR2(100)','Y','','',''),
 ('DELETED_AT','논리 삭제 일시','Deleted At',TS,'Y','','','NULL이면 삭제되지 않은 행.'),
]
TABLES = [
 dict(t='CMM_CODE_GROUP', ko='공통코드 그룹', en='Common Code Group',
  desc='코드의 종류(그룹)를 정의하는 마스터. 그룹마다 1행. 그룹별로 ATTR1~5에 무엇을 담는지도 여기서 정의한다.',
  cols=[
   ('CODE_GROUP_ID','공통코드 그룹 고유 식별 번호','Common Code Group Unique Identifier',ID,'N','','PK','대리 PK `SEQ_CMM_CODE_GROUP` (선행 결정 1).'),
   ('CODE_GROUP_CD','공통코드 그룹 코드','Common Code Group Code','VARCHAR2(50)','N','','UK','그룹을 구분하는 영문 코드. 예: `MEMBER_STATUS`. 재사용 금지 값 (선행 결정 4).'),
   ('CODE_GROUP_NM','공통코드 그룹 한글 이름','Common Code Group Korean Name','VARCHAR2(100)','N','','','예: 회원 계정 상태.'),
   ('CODE_GROUP_ENGLISH_NM','공통코드 그룹 영문 이름','Common Code Group English Name','VARCHAR2(200)','N','','','예: Member Account Status.'),
   ('OWNER_DOMAIN_CD','공통코드 그룹 소유 도메인 접두어','Owner Domain Prefix Code','VARCHAR2(10)','N','','CK (도메인 접두어 19개)','이 그룹을 주로 쓰는 도메인. 예: `MBR`. 여러 도메인이 함께 쓰면 `CMM`.'),
   yn('CHECK_CONSTRAINT_YN','업무 컬럼 CHECK 제약 적용 여부','Business Column Check Constraint Flag','N','Y면 이 그룹의 값을 업무 컬럼 CHECK 제약에도 나열한다 (규칙 4). 값을 추가하면 CHECK도 함께 바꿔야 한다.'),
   ('ATTR1_NM','추가 속성 1 의미','Additional Attribute 1 Meaning','VARCHAR2(100)','Y','','','이 그룹에서 `CMM_CODE.ATTR1_VAL`이 뜻하는 것. 예: 최소 나이. NULL이면 쓰지 않음.'),
   ('ATTR2_NM','추가 속성 2 의미','Additional Attribute 2 Meaning','VARCHAR2(100)','Y','','',''),
   ('ATTR3_NM','추가 속성 3 의미','Additional Attribute 3 Meaning','VARCHAR2(100)','Y','','',''),
   ('ATTR4_NM','추가 속성 4 의미','Additional Attribute 4 Meaning','VARCHAR2(100)','Y','','',''),
   ('ATTR5_NM','추가 속성 5 의미','Additional Attribute 5 Meaning','VARCHAR2(100)','Y','','',''),
   ('CODE_GROUP_DESC','공통코드 그룹 설명','Common Code Group Description','VARCHAR2(1000)','Y','','','용도와 쓰는 컬럼.'),
   yn('USE_YN','공통코드 그룹 사용 여부','Common Code Group In-Use Flag','Y','삭제와 별개 (선행 결정 4).'),
  ] + SYS,
  idx=['UK `UK_CMM_CODE_GROUP_CODE_GROUP_CD` (CODE_GROUP_CD)']),
 dict(t='CMM_CODE', ko='공통코드 값', en='Common Code Value',
  desc='그룹별 코드 값. 업무 테이블의 `_CD` 컬럼은 이 표의 `CODE_CD` 문자열을 그대로 저장하고 FK는 걸지 않는다 (코드 저장 방식 A, 2026-11-22).',
  cols=[
   ('CODE_ID','공통코드 값 고유 식별 번호','Common Code Value Unique Identifier',ID,'N','','PK','대리 PK `SEQ_CMM_CODE` (선행 결정 1). 업무 테이블은 이 값을 참조하지 않는다.'),
   ('CODE_GROUP_ID','소속 공통코드 그룹 식별 번호','Owning Common Code Group Identifier',ID,'N','','FK → `CMM_CODE_GROUP`, UK1',''),
   ('CODE_GROUP_CD','소속 공통코드 그룹 코드 (중복 저장)','Owning Common Code Group Code (Denormalized)','VARCHAR2(50)','N','','','그룹 조인 없이 `WHERE CODE_GROUP_CD = ...`로 조회하려고 중복 저장. [확인 필요]'),
   ('CODE_CD','공통코드 값','Common Code Value','VARCHAR2(50)','N','','UK1','업무 컬럼에 저장되는 문자열. 예: `ACTIVE`. 한 번 쓴 값은 바꾸거나 재사용하지 않는다 (코드 저장 방식 A의 단점 대응).'),
   ('CODE_NM','공통코드 한글 이름','Common Code Korean Name','VARCHAR2(100)','N','','','화면 표시 이름. 예: 정상.'),
   ('CODE_ENGLISH_NM','공통코드 영문 이름','Common Code English Name','VARCHAR2(200)','N','','','예: Active.'),
   ('CODE_DESC','공통코드 설명','Common Code Description','VARCHAR2(1000)','Y','','',''),
   ('SORT_SN','공통코드 표시 정렬 순서','Common Code Display Sort Order','NUMBER(5)','N','','CK (>= 1)','그룹 안에서의 표시 순서.'),
   ('ATTR1_VAL','공통코드 추가 속성 1 값','Common Code Additional Attribute 1 Value','VARCHAR2(200)','Y','','','의미는 그룹의 `ATTR1_NM`. 숫자도 문자로 저장. 결정 때 이름은 `ATTR1`이었으나 분류어 규칙(선행 결정 3)에 맞춰 `_VAL` 제안.'),
   ('ATTR2_VAL','공통코드 추가 속성 2 값','Common Code Additional Attribute 2 Value','VARCHAR2(200)','Y','','',''),
   ('ATTR3_VAL','공통코드 추가 속성 3 값','Common Code Additional Attribute 3 Value','VARCHAR2(200)','Y','','',''),
   ('ATTR4_VAL','공통코드 추가 속성 4 값','Common Code Additional Attribute 4 Value','VARCHAR2(200)','Y','','',''),
   ('ATTR5_VAL','공통코드 추가 속성 5 값','Common Code Additional Attribute 5 Value','VARCHAR2(200)','Y','','',''),
   yn('USE_YN','공통코드 사용 여부','Common Code In-Use Flag','Y','N이면 새로 고를 수 없지만, 이미 저장된 데이터는 그대로 표시한다.'),
  ] + SYS,
  idx=['UK `UK_CMM_CODE_CODE_GROUP_ID_CODE_CD` (CODE_GROUP_ID, CODE_CD)', 'IX `IX_CMM_CODE_CODE_GROUP_CD_SORT_SN` (CODE_GROUP_CD, SORT_SN)', 'CK (테이블 수준): `CODE_GROUP_CD`는 `CODE_GROUP_ID`의 그룹 코드와 같아야 함 (애플리케이션·Flyway 시드에서 보장) [확인 필요]']),
]

# ---- 회원 도메인 코드 그룹
# (그룹 코드, 한글, 영문, 쓰는 컬럼, CHECK, ATTR 의미 [], 값 [(코드, 한글, 영문, 설명, [attr...])], 비고)
import related as _rel
def _withrel(key, code, d):
    xs = _rel.items(key, code, lambda t, col: f'`{t}.{col}`')
    return d + '\x1e' + '\x1f'.join(xs) if xs else d
def from_codes(key): return [(v[0], v[1], v[2], _withrel(key, v[0], v[3]), []) for v in CODES[key]]
G = []
def add(gc, ko, en, cols, ck, attrs, vals, note=''): G.append((gc, ko, en, cols, ck, attrs, vals, note))
add('MEMBER_STATUS','회원 계정 상태','Member Account Status','`MBR_MEMBER.MEMBER_STATUS_CD`','Y',[],from_codes('MEMBER_STATUS_CD'),'10-1, 10-2')
add('MEMBER_TYPE','회원 혜택 유형','Member Benefit Type','`MBR_MEMBER.MEMBER_TYPE_CD`','Y',[],from_codes('MEMBER_TYPE_CD'),'11-3')
add('GENDER','성별','Gender','`MBR_MEMBER.GENDER_CD`','Y',[],from_codes('GENDER_CD'),'37-4')
add('MOBILE_CARRIER','휴대폰 통신사','Mobile Carrier','`MBR_MEMBER.MOBILE_CARRIER_CD`','N',['모회선 통신사'],
    [(c0,k,e,dd,[{'SKT_MVNO':'SKT','KT_MVNO':'KT','LG_UPLUS_MVNO':'LG_UPLUS'}.get(c0,'')]) for c0,k,e,dd,_ in from_codes('MOBILE_CARRIER_CD')],
    '2026-11-22 컬럼 추가 결정. 본인인증 업체 결과 기준')
add('AGE_GROUP','5년 단위 연령대','Five-Year Age Group','`MBR_MEMBER.AGE_GROUP_CD`','N',['최소 나이','최대 나이'],
    [(c0,k,e,dd,[c0.split('_')[1], '' if c0.endswith('OVER') else c0.split('_')[2]]) for c0,k,e,dd,_ in from_codes('AGE_GROUP_CD')],'25-2. 일 배치가 생년월일로 계산')
add('SALES_CHANNEL','판매 채널','Sales Channel','`MBR_MEMBER.JOIN_CHANNEL_CD`, `LAST_LOGIN_CHANNEL_CD`, `MBR_DEVICE.CHANNEL_CD`, `MBR_CONSENT_HIST.CHANNEL_CD`','Y',[],
    from_codes('LAST_LOGIN_CHANNEL_CD / JOIN_CHANNEL_CD / CHANNEL_CD'),'선행 10. 여러 도메인 공통 (소유 `CMM`)')
add('OPERATING_SYSTEM','기기 운영체제','Device Operating System','`MBR_MEMBER.JOIN_OS_CD`, `MBR_DEVICE.OS_CD`','N',[],
    [('IOS','iOS','iOS','',[]),('ANDROID','안드로이드','Android','',[]),('WINDOWS','윈도우','Windows','',[]),('MACOS','macOS','macOS','',[]),('OTHER','기타','Other','리눅스 등',[])],'선행 10. 여러 도메인 공통 (소유 `CMM`)')
add('LOGIN_TYPE','로그인 수단 유형','Login Method Type','`MBR_LOGIN_ACCOUNT.LOGIN_TYPE_CD`','Y',[],from_codes('LOGIN_TYPE_CD'),'2, 3-2')
add('TOKEN_REVOCATION_REASON','리프레시 토큰 폐기 사유','Refresh Token Revocation Reason','`MBR_REFRESH_TOKEN.REVOCATION_REASON_CD`','Y',[],from_codes('REVOCATION_REASON_CD'),'7-3')
add('IDENTITY_VERIFICATION_PURPOSE','본인인증 요청 목적','Identity Verification Purpose','`MBR_IDENTITY_VERIFICATION_LOG.VERIFICATION_PURPOSE_CD`','Y',[],from_codes('VERIFICATION_PURPOSE_CD'),'4-2, 30')
add('IDENTITY_VERIFICATION_METHOD','본인인증 수단','Identity Verification Method','`MBR_IDENTITY_VERIFICATION_LOG.VERIFICATION_METHOD_CD`','Y',[],from_codes('VERIFICATION_METHOD_CD'),'선행 13-2')
add('IDENTITY_VERIFICATION_RESULT','본인인증 결과','Identity Verification Result','`MBR_IDENTITY_VERIFICATION_LOG.VERIFICATION_RESULT_CD`','Y',[],from_codes('VERIFICATION_RESULT_CD'),'')
add('QUALIFICATION_TYPE','특수 자격 유형','Special Qualification Type','`MBR_MEMBER.QUALIFICATION_APPLICATION_TYPE_CD`','Y',[],from_codes('QUALIFICATION_APPLICATION_TYPE_CD'),'32-2')
add('QUALIFICATION_APPROVAL_STATUS','특수 자격 승인 상태','Special Qualification Approval Status','`MBR_MEMBER.QUALIFICATION_APPROVAL_STATUS_CD`','Y',[],from_codes('QUALIFICATION_APPROVAL_STATUS_CD'),'32-2')
add('GRADE_CHANGE_REASON','등급 변경 사유','Grade Change Reason','`MBR_MEMBER_GRADE_CHANGE_HIST.CHANGE_REASON_CD`','Y',[],from_codes('CHANGE_REASON_CD (등급 이력)'),'35-4, 35-5')
add('SANCTION_RESTRICTION_TYPE','제재 제한 기능','Sanction Restricted Function','`MBR_SANCTION.RESTRICTION_TYPE_CD`','Y',['회원 캐시 컬럼'],
    [(c,k,e,d,[col]) for (c,k,e,d,_),col in zip(from_codes('RESTRICTION_TYPE_CD'),['ORDER_RESTRICTED_YN','COUPON_POINT_RESTRICTED_YN','REVIEW_RESTRICTED_YN','PAYMENT_RESTRICTED_YN','INQUIRY_RESTRICTED_YN','MEMBER_STATUS_CD'])],'12-2 (반품·교환 제외). 전체 정지 추가 [확정 2026-11-22]')
add('SANCTION_REASON','제재 사유','Sanction Reason','`MBR_SANCTION.SANCTION_REASON_CD`','N',[],
    [('RETURN_ABUSE','반품 남용','Return Abuse','12-4 후보 확정',[]),('PAYMENT_FAILURE_REPEATED','결제 연속 실패','Repeated Payment Failure','46-2 자동 제한 (처리자 SYSTEM)',[]),
     ('PAYMENT_FRAUD','부정 결제','Payment Fraud','',[]),('COUPON_POINT_ABUSE','쿠폰·적립금 부정 사용','Coupon and Point Abuse','',[]),
     ('REVIEW_ABUSE','리뷰 부정 작성','Review Abuse','광고성·허위 리뷰',[]),('ABUSIVE_INQUIRY','고객센터 악성 문의','Abusive Inquiry','',[]),('OTHER','기타','Other','메모 필수',[])],'[제안: 값은 결정 항목 아님]')
add('CONSENT_ITEM','동의 항목','Consent Item','`MBR_CONSENT_HIST.CONSENT_ITEM_CD`','Y',['필수 여부'],
    [(c,k,e,d,['Y' if d.split('\x1e')[0]=='필수' else 'N']) for c,k,e,d,_ in from_codes('CONSENT_ITEM_CD')],'17-3, 38-10, 43-3, 법률 L7-1, L9-1, L9 후속')
add('CONSENT_PATH','동의 경로','Consent Path','`MBR_CONSENT_HIST.CONSENT_PATH_CD`','Y',[],from_codes('CONSENT_PATH_CD'),'17-2')
add('BODY_REVIEW_DISCLOSURE','리뷰 체형 공개 범위','Review Body Information Disclosure','`MBR_MEMBER.BODY_REVIEW_DISCLOSURE_CD`','Y',[],from_codes('BODY_REVIEW_DISCLOSURE_CD'),'24-8')
add('TOP_SIZE','평소 상의 사이즈','Usual Top Size','`MBR_MEMBER.USUAL_TOP_SIZE_CD`','N',[],[(s,s,s,'',[]) for s in ['XS','S','M','L','XL','XXL']],'24-9-3')
add('BOTTOM_SIZE','평소 하의 사이즈','Usual Bottom Size','`MBR_MEMBER.USUAL_BOTTOM_SIZE_CD`','N',[],[(s,s,s,'',[]) for s in ['XS','S','M','L','XL','XXL']],'24-9-3')
add('WAIST_SIZE','평소 허리 사이즈 (인치)','Usual Waist Size (Inch)','`MBR_MEMBER.USUAL_WAIST_SIZE_CD`','N',['인치 값'],[(f'W{n}',f'{n}인치',f'{n} Inch','',[str(n)]) for n in range(24,41)],'24-9-3')
add('SHOE_SIZE','평소 신발 사이즈 (mm)','Usual Shoe Size (Millimeter)','`MBR_MEMBER.USUAL_SHOE_SIZE_CD`','N',['mm 값'],[(f'S{n}',f'{n}mm',f'{n} mm','',[str(n)]) for n in range(220,301,5)],'24-9-3')
add('PREFERENCE_DIMENSION','취향 차원','Preference Dimension','`MBR_PREFERENCE.PREFERENCE_DIMENSION_CD`','Y',['대상 코드 그룹'],
    [('CATEGORY','카테고리','Category','`CATEGORY_ID` 사용',['']),('STYLE_MOOD','스타일 무드','Style Mood','',['STYLE_MOOD']),('FIT','핏','Fit','',['FIT']),('PRICE_RANGE','가격대','Price Range','',['PRICE_RANGE'])],'38-1, 38-6')
G[-1] = G[-1][:6] + ([(v[0], v[1], v[2], _withrel('PREFERENCE_DIMENSION_CD', v[0], v[3]), v[4]) for v in G[-1][6]],) + G[-1][7:]
add('STYLE_MOOD','스타일 무드','Style Mood','`MBR_PREFERENCE.TARGET_CD` (차원 STYLE_MOOD)','N',[],
    [('MINIMAL','미니멀','Minimal','',[]),('CASUAL','캐주얼','Casual','',[]),('STREET','스트릿','Street','',[]),('OFFICE','오피스','Office','',[]),('CLASSIC','클래식','Classic','',[]),('SPORTY','스포티','Sporty','',[])],'38-1 예시 값 기반. 상품 도메인과 함께 확정')
add('FIT','핏','Fit','`MBR_PREFERENCE.TARGET_CD` (차원 FIT)','N',['부위'],
    [('TOP_SLIM','상의 슬림','Top Slim','',['TOP']),('TOP_REGULAR','상의 레귤러','Top Regular','',['TOP']),('TOP_OVERSIZED','상의 오버','Top Oversized','',['TOP']),
     ('BOTTOM_SLIM','하의 슬림','Bottom Slim','',['BOTTOM']),('BOTTOM_REGULAR','하의 레귤러','Bottom Regular','',['BOTTOM']),('BOTTOM_WIDE','하의 와이드','Bottom Wide','',['BOTTOM'])],'38-1 (상의·하의 따로)')
add('PRICE_RANGE','가격대','Price Range','`MBR_PREFERENCE.TARGET_CD` (차원 PRICE_RANGE)','N',['최소 금액','최대 금액'],
    [('UNDER_50000','5만 원 미만','Under 50,000 KRW','',['0','49999']),('FROM_50000_TO_99999','5만~10만 원','50,000 to 99,999 KRW','',['50000','99999']),
     ('FROM_100000_TO_199999','10만~20만 원','100,000 to 199,999 KRW','',['100000','199999']),('OVER_200000','20만 원 이상','200,000 KRW and Over','',['200000',''])],'38-1')
add('PREFERENCE_SOURCE','선호 출처','Preference Source','`MBR_PREFERENCE.PREFERENCE_SOURCE_CD`','Y',['고정 점수'],
    [('EXPLICIT','고객 선택','Explicit','',['80']),('INFERRED','행동 추론','Inferred','',[''])],'38-2, 38-7')
G[-1] = G[-1][:6] + ([(v[0], v[1], v[2], _withrel('PREFERENCE_SOURCE_CD', v[0], v[3]), v[4]) for v in G[-1][6]],) + G[-1][7:]
add('PREFERENCE_BEHAVIOR_WEIGHT','선호 추론 행동 가중치','Preference Behavior Weight','선호 추론 로직 (컬럼 없음)','N',['가중치'],
    [('VIEW','조회','View','',['1']),('WISHLIST','위시 추가','Wishlist','',['3']),('CART','장바구니 담기','Cart','',['4']),('PURCHASE_CONFIRMED','구매 확정','Purchase Confirmed','',['10']),('RETURN','반품 (사이즈 외 사유)','Return','점수는 0 아래로 내려가지 않음 (38-4)',['-5'])],'38-3. 가중치는 결정 당시 예시 값')
add('PROFILE_IMAGE_INSPECTION_STATUS','프로필 이미지 검수 상태','Profile Image Inspection Status','`MBR_PROFILE_IMAGE.INSPECTION_STATUS_CD`','Y',[],from_codes('INSPECTION_STATUS_CD'),'37-3')
add('WITHDRAWAL_REASON','탈퇴 사유','Withdrawal Reason','`MBR_MEMBER.WITHDRAWAL_REASON_CD`','N',[],
    [('LOW_USAGE','이용 빈도 낮음','Low Usage','',[]),('PRODUCT_DISSATISFACTION','상품 불만','Product Dissatisfaction','',[]),('DELIVERY_DISSATISFACTION','배송 불만','Delivery Dissatisfaction','',[]),
     ('SERVICE_DISSATISFACTION','서비스·고객센터 불만','Service Dissatisfaction','',[]),('PRIVACY_CONCERN','개인정보 우려','Privacy Concern','',[]),('TOO_MANY_NOTIFICATIONS','알림이 너무 많음','Too Many Notifications','',[]),
     ('REJOIN_PLANNED','재가입 예정','Rejoin Planned','',[]),('OTHER','기타','Other','',[])],'[제안: 컬럼과 값 모두 결정 항목 아님]')
add('SAVED_PAYMENT_METHOD_STATUS','저장 결제수단 상태','Saved Payment Method Status','`MBR_SAVED_PAYMENT_METHOD.SAVED_PAYMENT_METHOD_STATUS_CD`','Y',[],from_codes('SAVED_PAYMENT_METHOD_STATUS_CD'),'47-1')
add('BANK','은행 (금융결제원 표준 코드)','Bank (KFTC Standard Code)','`MBR_MEMBER.REFUND_BANK_CD`','N',[],
    [(c,k,e,'',[]) for c,k,e in [('002','KDB산업은행','KDB'),('003','IBK기업은행','IBK'),('004','KB국민은행','KB Kookmin'),('007','수협은행','Suhyup'),('011','NH농협은행','NH Nonghyup'),
     ('020','우리은행','Woori'),('023','SC제일은행','SC First'),('027','한국씨티은행','Citibank Korea'),('031','iM뱅크','iM Bank'),('032','부산은행','Busan'),('034','광주은행','Gwangju'),
     ('035','제주은행','Jeju'),('037','전북은행','Jeonbuk'),('039','경남은행','Kyongnam'),('045','새마을금고','MG Saemaul'),('048','신협','Shinhyup'),('071','우체국','Korea Post'),
     ('081','하나은행','Hana'),('088','신한은행','Shinhan'),('089','케이뱅크','K Bank'),('090','카카오뱅크','Kakao Bank'),('092','토스뱅크','Toss Bank')]],'43-1. 코드는 금융결제원 3자리 은행 코드 [확인 필요: 최신 목록 대조]')
add('CARD_COMPANY','카드사','Card Company','`MBR_SAVED_PAYMENT_METHOD.CARD_COMPANY_CD`','N',['PG별 카드사 코드 매핑'],
    [(c,k,e,'',['']) for c,k,e in [('SHINHAN','신한카드','Shinhan Card'),('SAMSUNG','삼성카드','Samsung Card'),('KB_KOOKMIN','KB국민카드','KB Kookmin Card'),('HYUNDAI','현대카드','Hyundai Card'),
     ('LOTTE','롯데카드','Lotte Card'),('HANA','하나카드','Hana Card'),('WOORI','우리카드','Woori Card'),('BC','BC카드','BC Card'),('NH_NONGHYUP','NH농협카드','NH Nonghyup Card'),('OTHER','기타','Other')]],'40-2. 카드사 코드는 PG마다 달라 자체 코드 + 매핑 [확인 필요: 매핑 위치는 결제 도메인]')
add('REFUND_ACCOUNT_VERIFICATION_RESULT','환불 계좌 인증 결과','Refund Account Verification Result','`MBR_MEMBER.REFUND_ACCOUNT_VERIFICATION_RESULT_CD`','Y',[],from_codes('REFUND_ACCOUNT_VERIFICATION_RESULT_CD'),'43-2')
add('CASH_RECEIPT_PURPOSE','현금영수증 발급 용도','Cash Receipt Purpose','`MBR_MEMBER.CASH_RECEIPT_PURPOSE_CD`','Y',[],from_codes('CASH_RECEIPT_PURPOSE_CD'),'44-1')
add('CASH_RECEIPT_IDENTIFIER_TYPE','현금영수증 식별번호 유형','Cash Receipt Identifier Type','`MBR_MEMBER.CASH_RECEIPT_IDENTIFIER_TYPE_CD`','Y',[],from_codes('CASH_RECEIPT_IDENTIFIER_TYPE_CD'),'44-1')
add('SIDO','시도 (행정표준코드)','Province (Administrative Standard Code)','`MBR_DELIVERY_ADDRESS.SIDO_CD`','N',[],
    [(c,k,e,'',[]) for c,k,e in [('11','서울특별시','Seoul'),('26','부산광역시','Busan'),('27','대구광역시','Daegu'),('28','인천광역시','Incheon'),('29','광주광역시','Gwangju'),('30','대전광역시','Daejeon'),
     ('31','울산광역시','Ulsan'),('36','세종특별자치시','Sejong'),('41','경기도','Gyeonggi'),('43','충청북도','Chungbuk'),('44','충청남도','Chungnam'),('46','전라남도','Jeonnam'),
     ('47','경상북도','Gyeongbuk'),('48','경상남도','Gyeongnam'),('50','제주특별자치도','Jeju'),('51','강원특별자치도','Gangwon'),('52','전북특별자치도','Jeonbuk')]],'22-3. 법정동 코드 앞 2자리 [확인 필요: 최신 행정표준코드 대조]')
add('SIGUNGU','시군구 (행정표준코드)','District (Administrative Standard Code)','`MBR_DELIVERY_ADDRESS.SIGUNGU_CD`','N',['시도 코드'],[],'22-3. 약 250개. 행정안전부 행정표준코드 파일을 Flyway 시드로 적재하고 ATTR1에 시도 코드. 값은 이 문서에 나열하지 않음')
add('PII_RETENTION_REASON','개인정보 보유 사유','Personal Information Retention Reason','모든 테이블의 `PII_RETENTION_REASON_CD` (회원은 `MBR_MEMBER`)','N',['보유 개월 수','기산 기준'],
    [('REJOIN_BENEFIT_RESTRICTION','재가입 혜택 제한','Rejoin Benefit Restriction','CI 해시',['6','탈퇴 확정일']),
     ('ORDERER_INFORMATION','주문자·수령인 정보','Orderer Information','전자상거래법',['60','주문일']),('ORDER_RECORD','주문 금액·상품·수량','Order Record','',['120','주문일']),
     ('PAYMENT_RECORD','결제 정보','Payment Record','전자상거래법 시행령 6조. 탈퇴하면 `SYS_PII_ARCHIVE`로 분리 (법률 L3)',['60','결제일']),('INQUIRY_RECORD','문의·상품 Q&A','Inquiry Record','전자상거래법 시행령 6조. 탈퇴하면 `SYS_PII_ARCHIVE`로 분리 (법률 L3)',['36','작성일']),
     ('CONSENT_HISTORY','동의 이력','Consent History','요청 IP는 탈퇴 확정 시 NULL (법률 L4)',['60','탈퇴 확정일']),('PII_ACCESS_LOG','개인정보 접속 기록','PII Access Log','',['36','기록일']),
     ('ADMIN_ACTION_LOG','관리자 작업 로그','Administrator Action Log','',['36','기록일']),('DATA_CHANGE_LOG','데이터 변경 이력','Data Change Log','',['36','기록일']),
     ('EXTERNAL_INTERFACE_LOG','외부 연동 로그','External Interface Log','본인인증 로그 포함',['12','기록일']),('SEARCH_LOG','검색어 원본 로그','Search Keyword Log','',['12','기록일']),
     ('REFUND_ACCOUNT_SNAPSHOT','클레임 환불 계좌 마스킹 값','Refund Account Masked Snapshot','',['60','환불 완료일']),
     ('UNREFUNDED_DEPOSIT_CONTACT','미반환 예치금 반환 연락처','Unrefunded Deposit Contact','반환이 끝나면 즉시 파기 (법률 L2-4)',['0','반환 완료일'])],'선행 7, 28-2, 28-8~28-16, 26-3, 43-4, 법률 L2-4. 도메인마다 추가')
add('MEMBER_POLICY','회원 정책 기준값','Member Policy Threshold','배치·애플리케이션 판단 로직 (컬럼 없음)','N',['기준값','단위'],
    [('DORMANT_AFTER_NO_LOGIN','휴면 전환 기준','Dormant After No Login','',['12','개월']),('DORMANT_ADVANCE_NOTICE','휴면 사전 안내','Dormant Advance Notice','',['30','일 전']),
     ('WITHDRAWAL_GRACE_PERIOD','탈퇴 철회 유예','Withdrawal Grace Period','',['7','일']),('PASSWORD_CHANGE_NOTICE_CYCLE','비밀번호 변경 안내 주기','Password Change Notice Cycle','',['90','일']),
     ('LOGIN_FAIL_LOCK_COUNT','로그인 잠금 실패 횟수','Login Fail Lock Count','',['5','회 [확인 필요: 결정 항목 없음]']),
     ('PAYMENT_PIN_LOCK_COUNT','결제 PIN 잠금 실패 횟수','Payment PIN Lock Count','',['5','회']),
     ('PAYMENT_FAIL_WINDOW','결제 실패 집계 시간','Payment Failure Window','',['1','시간']),('PAYMENT_FAIL_LIMIT','결제 실패 허용 횟수','Payment Failure Limit','',['5','회']),
     ('PAYMENT_RESTRICTION_PERIOD','결제 자동 제한 기간','Payment Restriction Period','',['24','시간']),
     ('RETURN_ABUSE_RATE','반품 남용 검토 반품률','Return Abuse Review Rate','',['[미정]','%']),
     ('EMPLOYEE_REVERIFICATION_CYCLE','임직원 재인증 주기','Employee Reverification Cycle','',['12','개월']),
     ('RECENTLY_VIEWED_DISPLAY_LIMIT','최근 본 상품 표시 개수','Recently Viewed Display Limit','',['50','개']),('RECENTLY_VIEWED_RETENTION','최근 본 상품 보관 기간','Recently Viewed Retention','',['30','일'])],
    '27-2, 27-4, 39-3, 6-1, 41-2, 46-2, 12-4, 32-4, 23-3')
NOT_CMM = [
 ('`MBR_GRADE.GRADE_CD`', '등급은 마스터 테이블 `MBR_GRADE`에서 관리 (35-1)'),
 ('`MBR_TAG.TAG_CD`', '태그는 마스터 테이블 `MBR_TAG`에서 관리 (11-5)'),
 ('`MBR_ADVERTISING_PLATFORM_SHARE_HIST.SEGMENT_CD`', '마케팅 세그먼트 관리 위치 미정 (프로모션·마케팅 도메인)'),
 ('`MBR_MEMBER.LAST_PAYMENT_METHOD_TYPE_CD`, `MBR_SAVED_PAYMENT_METHOD.PAYMENT_METHOD_TYPE_CD`', '결제수단 유형 코드 그룹은 결제 도메인에서 정의'),
 ('`MBR_SAVED_PAYMENT_METHOD.PAYMENT_AGENCY_CD`', '결제 대행사는 외부 업체 마스터(선행 13-6)와의 관계를 결제 도메인에서 정의'),
]
CONFIRM = [
 ('CMM 도메인 구조', '`CMM_CODE_GROUP`·`CMM_CODE`의 컬럼 구조는 공통코드 도메인 결정 사항이다. 이 문서의 구조는 회원 코드를 담아 보려고 만든 제안이다.'),
 ('`CODE_GROUP_CD` 중복 저장', '`CMM_CODE`에 그룹 ID(FK)와 그룹 코드를 함께 둘지. 함께 두면 조회가 쉽지만 두 값이 어긋날 수 있다.'),
 ('`ATTR1~5` 이름', '규칙 4의 `ATTR1`~`ATTR5`를 분류어 규칙에 맞춰 `ATTR1_VAL`~`ATTR5_VAL`로 제안. 그룹별 의미는 `CMM_CODE_GROUP.ATTR1_NM` 등에 둔다.'),
 ('정책 기준값 그룹', '휴면 기준, 결제 실패 기준 등 숫자 설정을 `MEMBER_POLICY` 코드 그룹에 담는 방식. 별도 설정 테이블로 둘지 정해야 한다.'),
 ('결정에 없던 값', '제재 사유, 탈퇴 사유, 연령대 구간, 무드·핏 값, 카드사 목록, 로그인 잠금 횟수, 반품 남용 기준값은 결정 항목이 아니었다.'),
 ('외부 표준 코드', '은행·시도 코드는 외부 표준이라 적재 전에 최신 목록과 대조해야 한다. 시군구는 파일로 적재한다.'),
 ('Flyway 시드 행위자', '시드 행의 `CREATED_BY_TYPE_CD`/`CREATED_BY` 값 (`BATCH` + 마이그레이션 버전 등).'),
]

def il(s):
    s = html.escape(str(s)); p = s.split('`')
    s = ''.join(f'<code>{x.replace("_", "_<wbr>").replace(".", ".<wbr>")}</code>' if i % 2 else x for i, x in enumerate(p))
    s = re.sub(r'\s*\[확정 [^\]]*\]', '', s)
    return re.sub(r'\[(확인 필요[^\]]*|제안[^\]]*|미정)\]', r'<span class="warn">[\1]</span>', s)
def desc_html(d):
    if '\x1e' not in d: return il(d)
    main, rel = d.split('\x1e')
    return il(main) + '<div class="rel"><div class="rh">관련 정보</div><ul>' + ''.join(f'<li>{il(x)}</li>' for x in rel.split('\x1f')) + '</ul></div>'
def ln(ko, en): return f'{il(ko)} <span class="en" style="display:inline-block">({il(en)})</span>'  # 한 줄에 들어가면 한 줄
def pn(p): return html.escape(p).replace('_', '_<wbr>')
B = '☐'; CKS = f'<td class="ck">{B}</td><td class="memo"></td>'
CSS = """@page { size: A4 landscape; margin: 12mm 10mm; }
body { font-family: 'Apple SD Gothic Neo', sans-serif; font-size: 8.4pt; color:#222; line-height:1.4; }
h1 { font-size: 16pt; margin:0 0 4px; border-bottom: 3px solid #1f4e79; padding-bottom:6px; color:#1f4e79; }
.meta { color:#666; font-size:8pt; margin-bottom:10px; }
h2 { font-size: 12pt; margin:14px 0 4px; color:#1f4e79; page-break-after: avoid; } h2.t { page-break-before: always; }
h2.g { font-size:14pt; color:#fff; background:#1f4e79; padding:4px 8px; margin:16px 0 6px; }
h3 { font-size: 10pt; margin:10px 0 4px; page-break-after: avoid; }
table { border-collapse: collapse; width:100%; margin:3px 0 8px; } tr { page-break-inside: avoid; }
th, td { border:1px solid #bbb; padding:2px 4px; vertical-align:top; text-align:left; } th { background:#eef2f7; font-weight:600; }
td.n { text-align:center; color:#666; white-space:nowrap; } td.p { font-family: Menlo, monospace; font-size:7.6pt; overflow-wrap:anywhere; }
td.ty { font-family: Menlo, monospace; font-size:7.6pt; white-space:nowrap; } td.ck { text-align:center; font-size:11pt; color:#888; }
tr.sys td { background:#f6f6f6; color:#555; } .ok { color:#1a7f37; font-weight:600; } td.ck.on { color:#1a7f37; } tr.cf td { background:#fff6e0; } .en { color:#555; } th .en { font-weight:400; font-size:7.4pt; } .pc { font-family: Menlo, monospace; font-size:7.4pt; }
.info td:first-child { width:110px; background:#f3f6fa; font-weight:600; }
code { font-family: Menlo, monospace; font-size:7.6pt; background:#f1f1f1; padding:0 2px; }
.box { border:1px solid #c9d6e6; background:#f6f9fc; padding:6px 10px; margin:6px 0; } .warn { color:#b03a00; font-weight:600; }
.gi td { background:#f3f6fa; }
.rel { margin-top:4px; border:1px solid #c5d6ea; border-left:4px solid #3d6fa8; background:#f2f7fc; border-radius:2px; padding:3px 6px 3px 7px; }
.rel .rh { font-size:7.4pt; font-weight:700; color:#3d6fa8; letter-spacing:0.5px; margin-bottom:1px; }
.rel ul { margin:0; padding-left:12px; } .rel li { margin:0; font-size:7.8pt; color:#333; }"""
body = ('<h1>공통코드 (CMM_CODE) — 회원 도메인 코드 (제안)</h1>'
        f'<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-22 · 테이블 이름 <code>CMM_CODE_GROUP</code>, <code>CMM_CODE</code>는 확정, 구조와 값은 모두 제안</div>'
        '<div class="box"><b>검토 방법</b><br>· 모든 행에 확정 칸과 메모 칸이 있다. 확정한 행은 확정 칸에 표시하고, 고칠 내용은 메모 칸에 적는다. 1장은 T 번호, 2장은 <code>CODE_GROUP_ID</code>, 3장은 <code>CODE_ID</code>로 알려 주면 된다.<br>'
        '· 코드 저장 방식 A (2026-11-22): 업무 테이블의 <code>_CD</code> 컬럼은 <code>CMM_CODE.CODE_CD</code> 문자열을 저장하고 FK는 걸지 않는다. CHECK 적용 그룹(CK=Y)은 값을 업무 컬럼 CHECK에도 나열한다.<br>'
        '· 노란 행 / 빨간 표시: 결정 항목에 없던 제안이거나 확인이 필요한 것.<br>· 정렬은 지시 규칙 8 (관련 그룹 → 중요도 순).</div>')
conf = '<h2>확인이 필요한 사항</h2><table><tr><th>No</th><th>항목</th><th>내용</th><th>확정</th><th>메모</th></tr>' + ''.join(
    f'<tr class="cf"><td class="n">Q{k}</td><td>{il(a)}</td><td>{il(b)}</td>{CKS}</tr>' for k, (a, b) in enumerate(CONFIRM, 1)) + '</table>'
body += conf
# 1. 테이블 구조
body += '<h2 class="g">1. 테이블 구조</h2>'
COLG = '<colgroup><col style="width:4%"><col style="width:17%"><col style="width:18%"><col style="width:8.5%"><col style="width:3.5%"><col style="width:7%"><col style="width:9%"><col style="width:25%"><col style="width:3%"><col style="width:5%"></colgroup>'
for ti, t in enumerate(TABLES, 1):
    body += f'<h2>1-{ti}. {t["t"]}</h2><table class="info"><tr><td>논리명</td><td>{ln(t["ko"], t["en"])}</td></tr><tr><td>설명</td><td>{il(t["desc"])}</td></tr><tr><td>PK·시퀀스</td><td>대리 PK <code>SEQ_{t["t"]}</code> · CACHE 20</td></tr><tr><td>삭제 방식</td><td>논리 삭제 (마스터). 사용 중인 코드는 삭제 대신 <code>USE_YN = N</code></td></tr></table>'
    body += f'<table style="table-layout:fixed">{COLG}<tr><th>No</th><th>물리명</th><th>논리명</th><th>타입</th><th>NULL</th><th>기본값</th><th>제약</th><th>설명</th><th>확정</th><th>메모</th></tr>'
    for k, (p, ko, en, ty, nl, df, ck, ds) in enumerate(t['cols'], 1):
        cls = ' class="sys"' if p.startswith(('CREATED', 'UPDATED', 'DELETED')) else (' class="cf"' if '[확인' in ds or '제안' in ds else '')
        body += f'<tr{cls}><td class="n">T{ti}-{k}</td><td class="p">{pn(p)}</td><td>{ln(ko, en)}</td><td class="ty">{il(ty)}</td><td class="n">{nl}</td><td class="ty">{il(df)}</td><td>{il(ck)}</td><td>{il(ds)}</td>{CKS}</tr>'
    body += '</table><h3>인덱스·제약</h3><table><tr><th>No</th><th>내용</th><th>확정</th><th>메모</th></tr>' + ''.join(
        f'<tr><td class="n">T{ti}-X{k}</td><td>{il(x)}</td>{CKS}</tr>' for k, x in enumerate(t['idx'], 1)) + '</table>'
# 2. 그룹 목록 (CMM_CODE_GROUP 행, DB 컬럼 그대로)
CMM_OWNED = {'SALES_CHANNEL','OPERATING_SYSTEM','BANK','CARD_COMPANY','SIDO','SIGUNGU','PII_RETENTION_REASON'}
# 가상 ID: V1(공통 소유 그룹) → DB 재시작으로 캐시 20 버림 → V2(회원 그룹) 순으로 적재했다고 가정
def nxt_block(last, start, cache=20): return start + ((last - start) // cache + 1) * cache
GID, CID, CODEID = {}, {}, {}
# 법률 검토(2026-11-22)로 나중에 추가한 코드: 기존 ID를 밀지 않고 V3 마이그레이션에서 끝 번호를 받는다
LATE = [('PII_RETENTION_REASON', 'UNREFUNDED_DEPOSIT_CONTACT'), ('CONSENT_ITEM', 'ANALYTICS_OVERSEAS_TRANSFER'), ('CONSENT_ITEM', 'PRIVACY_USAGE_NOTICE')]
g, c = 1001, 100001
order = [x for x in G if x[0] in CMM_OWNED] + [x for x in G if x[0] not in CMM_OWNED]
for k, x in enumerate(order):
    if k == len([y for y in G if y[0] in CMM_OWNED]):
        g = nxt_block(g - 1, 1001); c = nxt_block(c - 1, 100001)
    GID[x[0]] = g; g += 1
    CID[x[0]] = c
    if x[0] == 'SIGUNGU': c += 250; continue
    for v in x[6]:
        if (x[0], v[0]) in LATE: continue
        CODEID[(x[0], v[0])] = c; c += 1
V3_START = nxt_block(c - 1, 100001)
c = V3_START
for key in LATE:
    CODEID[key] = c; c += 1
LAST_G, LAST_C = g - 1, c - 1
def th(p, ko): return f'<th><span class="pc">{pn(p)}</span><br><span class="en">{il(ko)}</span></th>'
body += '<h2 class="g t">2. 회원 도메인 코드 그룹 (CMM_CODE_GROUP 행)</h2>'
body += ('<div class="box"><b>ID 값은 가상 값이다</b> <span class="warn">[가정]</span><br>'
  '· 시퀀스 시작값: <code>SEQ_CMM_CODE_GROUP</code> START WITH 1001, <code>SEQ_CMM_CODE</code> START WITH 100001 (START WITH는 결정 항목이 아니었다). INCREMENT BY 1, CACHE 20 (선행 결정 1).<br>'
  '· 적재 순서: Flyway V1이 여러 도메인 공통 그룹(<code>OWNER_DOMAIN_CD = CMM</code>) 7개를 먼저 넣고, V2가 회원 그룹 34개를 넣는다. 그래서 ID 순서는 문서 순서(규칙 8)와 다르다.<br>'
  f'· V1과 V2 사이에 DB를 재시작해 캐시 20개가 버려졌다고 가정해 번호가 건너뛴다 (그룹 {GID["PII_RETENTION_REASON"]} → {min(v for k, v in GID.items() if k not in CMM_OWNED)}). 시군구 약 250개도 V1에서 <code>CODE_ID</code>를 차지한다.<br>'
  f'· 법률 검토(2026-11-22)로 추가한 코드 {len(LATE)}개는 V3 마이그레이션으로 나중에 넣었다고 가정해, 기존 ID를 밀지 않고 {V3_START}부터 받는다: ' + ', '.join(f'<code>{k[1]}</code> {CODEID[k]}' for k in LATE) + '.<br>'
  f'· 결과: <code>CODE_GROUP_ID</code> 1001~{LAST_G}, <code>CODE_ID</code> 100001~{LAST_C}. 검토할 때는 이 ID로 알려 주면 된다.</div>')
body += ('<table style="table-layout:fixed"><colgroup><col style="width:5%"><col style="width:15%"><col style="width:17%"><col style="width:6%"><col style="width:7%"><col style="width:12%"><col style="width:24%"><col style="width:4%"><col style="width:3%"><col style="width:7%"></colgroup><tr>'
         + th('CODE_GROUP_ID','그룹 ID') + th('CODE_GROUP_CD','그룹 코드') + th('CODE_GROUP_NM','한글 이름 (영문 이름)') + th('OWNER_DOMAIN_CD','소유 도메인')
         + th('CHECK_CONSTRAINT_YN','CHECK 적용') + th('ATTR1~5_NM','추가 속성 의미') + th('CODE_GROUP_DESC','설명 (쓰는 컬럼)') + th('USE_YN','사용')
         + '<th>확정</th><th>메모</th></tr>')
for gi, (gc, ko, en, cols, ck, attrs, vals, note) in enumerate(G, 1):
    body += (f'<tr><td class="n">{GID[gc]}</td><td class="p">{pn(gc)}</td><td>{ln(ko, en)}</td><td class="ty">{"CMM" if gc in CMM_OWNED else "MBR"}</td><td class="n">{ck}</td>'
             f'<td>{"<br>".join(f"ATTR{i+1}_NM: {il(x)}" for i, x in enumerate(attrs))}</td><td>{il(cols)}</td><td class="n">Y</td>{CKS}</tr>')
body += '</table>'
body += '<h3>CMM_CODE로 관리하지 않는 회원 도메인 코드 컬럼</h3><table><tr><th>컬럼</th><th>이유</th></tr>' + ''.join(f'<tr><td>{il(a)}</td><td>{il(b)}</td></tr>' for a, b in NOT_CMM) + '</table>'
# 3. 값 (CMM_CODE 행, DB 컬럼 그대로)
body += '<h2 class="g t">3. 코드 값 (CMM_CODE 행)</h2>'
nv = 0
for gi, (gc, ko, en, cols, ck, attrs, vals, note) in enumerate(G, 1):
    nA = len(attrs)
    w = 37 - 8 * nA
    body += f'<div style="page-break-inside:avoid"><h3>CODE_GROUP_ID {GID[gc]} · {gc} — {il(ko)} <span style="font-weight:400;color:#666">· CHECK {ck} · 근거 {il(note)}</span></h3>'
    if not vals:
        body += f'<p>{il(note)} · <code>CODE_ID</code> {CID[gc]}~{CID[gc]+249} 차지 (가정)</p></div>'; continue
    body += ('<table style="table-layout:fixed"><colgroup><col style="width:6%"><col style="width:7%"><col style="width:16%"><col style="width:18%">' + f'<col style="width:{w}%">' + ''.join('<col style="width:8%">' for _ in attrs) +
             '<col style="width:5%"><col style="width:4%"><col style="width:3%"><col style="width:4%"></colgroup><tr>'
             + th('CODE_ID','코드 ID') + th('CODE_GROUP_ID','그룹 ID') + th('CODE_CD','코드 값') + th('CODE_NM','한글 이름 (영문 이름)') + th('CODE_DESC','설명')
             + ''.join(th(f'ATTR{i+1}_VAL', a) for i, a in enumerate(attrs)) + th('SORT_SN','정렬') + th('USE_YN','사용') + '<th>확정</th><th>메모</th></tr>')
    for vi, (c, k, e, d, av) in enumerate(vals, 1):
        nv += 1
        cf = ' class="cf"' if '[' in note and ('제안' in note or '확인' in note) else ''
        body += (f'<tr{cf}><td class="n">{CODEID[(gc, c)]}</td><td class="n">{GID[gc]}</td><td class="p">{pn(c)}</td><td>{ln(k, e)}</td><td>{desc_html(d)}</td>'
                 + ''.join(f'<td class="p">{pn(a)}</td>' if re.fullmatch(r'[A-Z_]+', a or '') else f'<td>{il(a)}</td>' for a in (av + [""] * nA)[:nA]) + f'<td class="n">{vi}</td><td class="n">Y</td>' + (f'<td class="ck on">☑</td><td class="memo"></td>' if '[확정' in d else CKS) + '</tr>')
    body += '</table></div>'
body = body.replace('<div class="box"><b>검토 방법</b>', f'<div class="box">코드 그룹 {len(G)}개 · 코드 값 {{NV}}개 (시군구 제외)</div><div class="box"><b>검토 방법</b>', 1).replace('{NV}', str(nv))
open(OUT, 'w', encoding='utf-8').write(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>CMM_CODE 회원 도메인 코드</title><style>{CSS}</style></head><body>{body}</body></html>')
print(len(G), nv)
import json
json.dump({gc: {'gid': GID[gc], 'codes': {v[0]: CODEID[(gc, v[0])] for v in vals}} for gc, ko, en, cols, ck, attrs, vals, note in G},
          open(os.path.join(os.path.dirname(OUT), 'code_ids.json'), 'w'), ensure_ascii=False)
