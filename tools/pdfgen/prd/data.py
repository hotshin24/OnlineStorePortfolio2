# 상품 도메인 테이블·컬럼 정의 (제안, 확정 전)
# 근거: 상품 도메인 결정 1~53 (docs/pdf/상품결정/). 테이블 이름은 모두 후보다.
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

def use_yn(ko):
    return yn('USE_YN', f'{ko} 사용 여부', 'In-Use Flag', 'Y', 'N이면 새로 고를 수 없다. 삭제와 별개 (선행 결정 4).')

def sort_sn(ko, en):
    return ('SORT_SN', f'{ko} 표시 정렬 순서', f'{en} Display Sort Order', 'NUMBER(5)', 'N', '1', 'CK (>= 1)', '')

ADM = '`ADM_USER` (후보, 관리자 도메인에서 확정)'

T = []

def table(**kw):
    kw.setdefault('idx', []); kw.setdefault('check', []); kw.setdefault('pii', False)
    T.append(kw)

# =========================================================== 1. 기준 정보
table(t='PRD_BRAND', ko='상품 브랜드 마스터', en='Product Brand Master',
 desc='브랜드·라인 마스터. 품번의 브랜드 약어와 브랜드관 화면용 기본 정보를 담는다. 브랜드관 화면 편성은 전시 도메인이 맡는다.',
 basis='20 C, 2 C, 법률 검토 L16 B', pk='대리 PK `SEQ_PRD_BRAND`', cache=20, delete='논리 삭제 (마스터). 스타일이 참조하면 삭제 불가, `USE_YN`으로 중지', part='없음', keep='-', ldel=True,
 cols=[
 ('식별', [
  ('BRAND_ID','상품 브랜드 고유 식별 번호','Product Brand Unique Identifier',ID,'N','','PK',''),
  ('BRAND_CD','품번용 브랜드 약어 코드','Brand Abbreviation Code for Style Number','VARCHAR2(5)','N','','UK, CK (영문 대문자·숫자)','품번 맨 앞에 붙는 약어. 예: `MS`. 한 번 쓴 값은 바꾸거나 재사용하지 않는다 (선행 결정 4, 상품 결정 2 C).'),
  ('BRAND_NM','브랜드 한글 이름','Brand Korean Name','VARCHAR2(100)','N','','',''),
  ('BRAND_ENGLISH_NM','브랜드 영문 이름','Brand English Name','VARCHAR2(200)','N','','',''),
 ]),
 ('브랜드관 기본 정보', [
  ('BRAND_LOGO_URL','브랜드 로고 이미지 경로','Brand Logo Image Path','VARCHAR2(500)','Y','','','저장소 상대 경로 (선행 결정 6: 전용 테이블 대신 경로 컬럼).'),
  ('BRAND_INTRODUCTION_CN','브랜드 소개 문구','Brand Introduction Content','VARCHAR2(2000)','Y','','',''),
  sort_sn('브랜드', 'Brand'),
  use_yn('브랜드'),
 ]),
 ('상품정보제공고시 기본값', [
  ('QUALITY_ASSURANCE_STANDARD_CN','품질보증기준 문구','Quality Assurance Standard Content','VARCHAR2(2000)','Y','','','고시 (1)~(4) “품질보증기준”, 고시 Ⅱ-5 (보상 규정 명시). 브랜드 상품 모두에 적용하고, 스타일 고시 JSON에 값이 있으면 그 값을 우선 (법률 검토 L16 B). 바꾸면 이전 문구는 표시 내용 이력에 남긴다.'),
  ('AFTER_SERVICE_MANAGER_NM','A/S 책임자 (부서) 이름','After-Service Manager Name','VARCHAR2(100)','Y','','','고시 “A/S 책임자와 전화번호”. 개인 이름이 아닌 부서·창구 이름을 권장 (L16 B).'),
  ('AFTER_SERVICE_PHONE_NO','A/S 전화번호','After-Service Phone Number','VARCHAR2(20)','Y','','','회사 대표·고객센터 번호 (개인정보 아님, 평문).'),
 ]),
 ])

table(t='PRD_SEASON', ko='상품 시즌 마스터', en='Product Season Master',
 desc='26SS 같은 시즌 마스터. 품번의 시즌 약어, 시즌 기간, 시즌오프 일정, 출시 계획을 담는다. 컬렉션은 전시 기획전으로 처리한다 (상품 결정 10 B). 품번을 발번할 때 이 행을 `SELECT ... FOR UPDATE`로 잠근다 (컬럼 검토 M-9 B).',
 basis='10 B, 2 C, 43 B(M-9로 변경)', pk='대리 PK `SEQ_PRD_SEASON`', cache=20, delete='논리 삭제 (마스터). 스타일이 참조하면 삭제 불가', part='없음', keep='-', ldel=True,
 cols=[
 ('식별', [
  ('SEASON_ID','상품 시즌 고유 식별 번호','Product Season Unique Identifier',ID,'N','','PK',''),
  ('SEASON_CD','품번용 시즌 약어 코드','Season Abbreviation Code for Style Number','VARCHAR2(6)','N','','UK','예: `26SS`, `26FW`. 품번에 들어가는 값이라 재사용 금지.'),
  ('SEASON_NM','시즌 한글 이름','Season Korean Name','VARCHAR2(100)','N','','','예: 2026 봄여름.'),
  ('SEASON_YEAR_VAL','시즌 연도','Season Year Value','NUMBER(4)','N','','CK (2020~2099)','회사 런칭 2020년.'),
  ('SEASON_TYPE_CD','시즌 구분 코드','Season Type Code','VARCHAR2(10)','N','','CK (값 목록)',''),
 ]),
 ('기간·일정', [
  ('SEASON_START_DT','시즌 시작 일자','Season Start Date','DATE','N','','',''),
  ('SEASON_END_DT','시즌 종료 일자','Season End Date','DATE','N','','',''),
  ('SEASON_OFF_START_DT','시즌오프 시작 예정 일자','Season-Off Start Planned Date','DATE','Y','','','안내용 일정. 실제 가격 인하는 가격 이력의 예약 행으로 처리한다 (상품 결정 8 B, 32 B).'),
  ('RELEASE_PLAN_CN','시즌 출시 계획 메모','Season Release Plan Content','VARCHAR2(2000)','Y','','','생산 계획과 겹치는 정보는 생산 도메인 차례에 나눈다 [확인 필요].'),
  use_yn('시즌'),
 ]),
 ],
 check=['`SEASON_START_DT <= SEASON_END_DT`'])

table(t='PRD_CATEGORY', ko='상품 관리 분류 (대·중·소 고정 깊이)', en='Product Management Category (Fixed Three Levels)',
 desc='복종 기준 관리 분류. 어린이제품(만 13세 이하) 복종은 두지 않는다 (법률 검토 L17 A, 범위 제외). 행마다 대·중·소 분류 코드를 고정 컬럼으로 갖는다 (상품 결정 4 충돌 재선택 A). 대분류 행은 중·소 코드가 NULL. 스타일은 소분류 행을, 회원 선호(`MBR_PREFERENCE.CATEGORY_ID`)는 어느 단계든 참조한다. 고객 메뉴용 전시 카테고리는 전시 도메인에 둔다 (상품 결정 5 C).',
 basis='4 A(재선택), 5 C, 3 B, 7 C', pk='대리 PK `SEQ_PRD_CATEGORY`', cache=20, delete='논리 삭제 (마스터). 하위 분류나 스타일이 참조하면 삭제 불가', part='없음', keep='-', ldel=True,
 cols=[
 ('식별', [
  ('CATEGORY_ID','상품 관리 분류 고유 식별 번호','Product Category Unique Identifier',ID,'N','','PK','회원 선호 FK가 참조한다 (회원 결정 38-6 B).'),
  ('CATEGORY_LEVEL_VAL','관리 분류 단계 (1 대, 2 중, 3 소)','Category Level Value','NUMBER(1)','N','','CK (1~3)',''),
  ('LARGE_CATEGORY_CD','대분류 코드','Large Category Code','VARCHAR2(10)','N','','UK1','예: `TOP`.'),
  ('MIDDLE_CATEGORY_CD','중분류 코드','Middle Category Code','VARCHAR2(10)','Y','','UK1','대분류 행은 NULL.'),
  ('SMALL_CATEGORY_CD','소분류 코드','Small Category Code','VARCHAR2(10)','Y','','UK1','대·중분류 행은 NULL.'),
  ('CATEGORY_NM','관리 분류 한글 이름','Category Korean Name','VARCHAR2(100)','N','','',''),
  ('CATEGORY_ENGLISH_NM','관리 분류 영문 이름','Category English Name','VARCHAR2(200)','N','','',''),
 ]),
 ('분류가 정하는 기준', [
  ('STYLE_NO_ITEM_CD','품번용 복종 약어','Item Abbreviation for Style Number','VARCHAR2(5)','Y','','','품번의 복종 부분. 중분류 행에만 둔다 (컬럼 검토 PC-8 A). 예: 티셔츠 `TS`, 팬츠 `PT`. 품번 일련번호는 이 중분류 단위로 센다.'),
  ('ITEM_NOTICE_GROUP_CD','상품정보제공고시 품목군 코드','Product Information Notice Item Group Code','VARCHAR2(30)','Y','','CK (값 목록)','소분류 행에서 필수 (애플리케이션 검증). 스타일의 고시 JSON 항목을 정한다 (상품 결정 7 C).'),
  ('SIZE_SYSTEM_CD','사이즈 체계 코드','Size System Code','VARCHAR2(30)','Y','','CK (값 목록)','소분류 행에서 필수. 사이즈 값은 이 체계의 공통코드 그룹에서 고른다 (상품 결정 3 B).'),
  sort_sn('관리 분류', 'Category'),
  use_yn('관리 분류'),
 ]),
 ],
 check=['단계 1이면 중·소 코드 NULL, 단계 2면 중 코드 NOT NULL·소 코드 NULL, 단계 3이면 셋 다 NOT NULL', '`STYLE_NO_ITEM_CD`는 단계 2(중분류) 행에서만 NOT NULL (PC-8 A)'],
 idx=['UK `UK_PRD_CATEGORY_LARGE_CATEGORY_CD_MIDDLE_CATEGORY_CD_SMALL_CATEGORY_CD` (63바이트)'])

table(t='PRD_COLOR', ko='상품 컬러 마스터', en='Product Color Master',
 desc='브랜드 컬러 코드 마스터. SKU 코드에 들어가는 컬러 코드를 통일한다. 고객 필터는 표준 계열 코드로 한다 (상품 결정 21 D). 컬러가 없는 상품용 `NONE` 행을 둔다 (상품 결정 47 A).',
 basis='21 D, 47 A', pk='대리 PK `SEQ_PRD_COLOR`', cache=20, delete='논리 삭제 (마스터)', part='없음', keep='-', ldel=True,
 cols=[
 ('식별', [
  ('COLOR_ID','상품 컬러 고유 식별 번호','Product Color Unique Identifier',ID,'N','','PK',''),
  ('COLOR_CD','브랜드 컬러 코드','Brand Color Code','VARCHAR2(10)','N','','UK','SKU 코드에 들어가는 값. 예: `BK`. 재사용 금지.'),
  ('COLOR_NM','컬러 표준 한글 이름','Color Standard Korean Name','VARCHAR2(100)','N','','','예: 블랙. 스타일별 화면 표시명은 `PRD_STYLE_COLOR.COLOR_DISPLAY_NM`.'),
  ('COLOR_ENGLISH_NM','컬러 표준 영문 이름','Color Standard English Name','VARCHAR2(200)','N','','',''),
 ]),
 ('필터·표시', [
  ('COLOR_FAMILY_CD','표준 컬러 계열 코드','Standard Color Family Code','VARCHAR2(20)','N','','CK (값 목록)','고객 컬러 필터용.'),
  ('COLOR_HEX_VAL','컬러칩 HEX 값','Color Chip Hex Value','VARCHAR2(7)','Y','','CK (`#` + 16진수 6자리)','예: `#1A1A1A`. 멀티 컬러는 NULL.'),
  sort_sn('컬러', 'Color'),
  use_yn('컬러'),
 ]),
 ])

# =========================================================== 2. 원단
table(t='PRD_FABRIC', ko='원단 마스터', en='Fabric Master',
 desc='판매 표시 정보의 원천인 원단 마스터 (상품 결정 24 D, 24-1 A). 혼용률은 JSON 컬럼에 둔다 (컬럼 검토 M-1 B). 원단 단가·공급처는 생산 도메인이 같은 원단 ID를 참조해 따로 둔다.',
 basis='24 D(M-1로 변경), 24-1 A, 46 B', pk='대리 PK `SEQ_PRD_FABRIC`', cache=20, delete='논리 삭제 (마스터). 스타일이 참조하면 삭제 불가', part='없음', keep='-', ldel=True,
 cols=[
 ('식별', [
  ('FABRIC_ID','원단 고유 식별 번호','Fabric Unique Identifier',ID,'N','','PK',''),
  ('FABRIC_CD','원단 코드','Fabric Code','VARCHAR2(20)','N','','UK','재사용 금지.'),
  ('FABRIC_NM','원단 이름','Fabric Name','VARCHAR2(200)','N','','','예: 울 캐시미어 멜턴.'),
 ]),
 ('혼용률', [
  ('COMPOSITION_JSON','원단 혼용률 (소재 × 비율)','Fabric Fiber Composition JSON','JSON','N','','','예: `[{"fiber":"WOOL","rate":70},{"fiber":"NYLON","rate":30}]`. 소재 코드는 공통코드 `FIBER`, 비율 합계 100과 코드 검사는 애플리케이션 (컬럼 검토 M-1 B, 상품 결정 24 D 변경). 고시 소재 문구의 원천. 소재 필터는 검색 엔진.'),
 ]),
 ('원단 특성', [
  ('FABRIC_WEIGHT_VAL','원단 중량 (g/㎡)','Fabric Weight in Grams per Square Meter','NUMBER(5)','Y','','CK (> 0)',''),
  ('THICKNESS_CD','원단 두께감 코드','Fabric Thickness Code','VARCHAR2(10)','Y','','CK (값 목록)','스타일 두께감의 기본값 제안에 쓴다. 스타일 값과 같은 그룹.'),
  ('STRETCH_CD','원단 신축성 코드','Fabric Stretch Code','VARCHAR2(10)','Y','','CK (값 목록)',''),
  ('RECOMMENDED_CARE_SYMBOL_JSON','원단 권장 세탁 기호 목록','Recommended Care Symbol List','JSON','Y','','','세탁 기호 코드 배열. 스타일 등록 때 `PRD_STYLE.CARE_SYMBOL_JSON`의 기본값 제안용 (상품 결정 46 B). 코드 검사는 애플리케이션 (컬럼 검토 PC-11 A).'),
  ('FABRIC_DESC','원단 설명','Fabric Description','VARCHAR2(1000)','Y','','',''),
  use_yn('원단'),
 ]),
 ])

# =========================================================== 3. 상품 계층
table(t='PRD_STYLE', ko='상품 스타일 (디자인 단위)', en='Product Style (Design Unit)',
 desc='기획부터 판매까지 한 행으로 추적하는 상품의 기본 단위 (상품 결정 1 B, 18 C). 품번은 기획 단계에서 발번한다. 발번 뒤에는 브랜드·시즌을 바꿀 수 없고, 관리 분류는 같은 중분류(같은 품번 복종 약어) 안의 소분류로만 옮길 수 있다 (애플리케이션 검사, 컬럼 검토 PC-22 A). 원가·생산 차수는 생산 도메인에 둔다 (17 C). 세탁 기호, 안전 인증, 사이즈별 실측, 구매 수량 제한, 태그를 별도 테이블 대신 이 행에 둔다 (컬럼 검토 M-2·M-3·M-4·M-6·M-7).',
 basis='컬럼 검토 PC-20~PC-30, 1 B, 2 C, 6 C, 7 C, 8 B, 9 B, 12 C, 13 B(M-4로 변경), 17 C, 18 C, 19 C(M-5로 변경), 25 A, 27 C(M-3으로 변경), 28 B, 29 C(M-6으로 변경), 30 B, 31 C, 33 B, 34 B, 35 A(재선택), 38 B(M-7로 변경), 39 D, 40 B, 41 C, 42 B, 43 B(M-9로 변경), 46 B(M-2로 변경), 53 B',
 pk='대리 PK `SEQ_PRD_STYLE`', cache=20, delete='상태 코드로 처리 (단종). 승인 전이고 참조가 없는 행만 물리 삭제 (상품 결정 42 B)', part='없음', keep='-', ldel=False,
 cols=[
 ('식별·분류', [  # 2026-11-24 사용자 지시: 식별과 분류 그룹을 하나로
  ('STYLE_ID','상품 스타일 고유 식별 번호','Product Style Unique Identifier',ID,'N','','PK',''),
  ('STYLE_NO','품번 (브랜드 + 시즌 + 복종 + 일련)','Style Number','VARCHAR2(20)','N','','UK','예: `MS26STS001`. 시즌 행을 잠그고 같은 접두어의 최대 일련번호 + 1로 발번 (컬럼 검토 M-9 B, 상품 결정 43 B 변경). UK가 중복을 최종 차단. URL에도 쓴다 (40 B). 재사용 금지.'),
  ('STYLE_NM','스타일 상품명 (고객 화면 표시용)','Style Product Display Name','VARCHAR2(200)','N','','','고객 화면에 보이는 상품 이름. 컬러별 표시 이름은 `PRD_STYLE_COLOR.COLOR_DISPLAY_NM` (컬럼 검토 PC-23 A).'),
  fk('BRAND_ID','브랜드 식별 번호','Brand Identifier','PRD_BRAND'),
  fk('SEASON_ID','시즌 식별 번호','Season Identifier','PRD_SEASON'),
  fk('CATEGORY_ID','관리 분류(소분류) 식별 번호','Small Category Identifier','PRD_CATEGORY',desc='소분류 행만 참조 (애플리케이션 검증).'),
  ('TARGET_GENDER_CD','상품 대상 성별 코드','Target Gender Code','VARCHAR2(10)','N','','CK (값 목록)','상품 결정 25 A.'),
  ('STYLE_OPERATION_TYPE_CD','스타일 운영 구분 코드','Style Operation Type Code','VARCHAR2(20)','N',"'SEASONAL'",'CK (값 목록)','상시, 시즌, 한정, 협업. 리오더 대상, 시즌오프 할인 대상, 재고 소진 목표, 생산 계획을 이 값으로 나눈다 (컬럼 검토 PC-20 A).'),
  fk('ORIGINAL_STYLE_ID','캐리오버 첫 세대 스타일 식별 번호','Original Style Identifier (First Carry-over Generation)','PRD_STYLE',null='Y',desc='시즌을 넘는 캐리오버로 새로 만든 스타일이면 첫 세대 스타일 ID, 첫 세대 자신이면 NULL (자기 참조). 바로 앞 세대는 연관 상품 `SUCCESSOR`가 기록하고, 이 컬럼은 전 세대를 한 번에 묶는 데 쓴다. 후속 상품 연결을 기록할 때 애플리케이션이 앞 세대의 값(NULL이면 앞 세대 ID)을 함께 넣는다 (컬럼 검토 PC-21 B, 상품 결정 23 C).'),
 ]),
 ('단계·상태', [
  ('STYLE_STAGE_CD','스타일 단계 코드','Style Stage Code','VARCHAR2(30)','N',"'PLANNING'",'CK (값 목록)','기획 → 생산 → 판매 등록, 또는 최초 승인 전에 출시 전 취소로 끝난다 (상품 결정 18 C, 컬럼 검토 PC-24 A, PC-62 A). 판매 등록은 “판매 등록 작업을 시작함”을 뜻하고 생산 완료 여부와 관계없다. 그래서 생산 중인 예약 판매 상품도 판매 등록 단계다. 생산 완료는 생산 도메인의 생산 차수로 판단한다 (PC-26 A). 판매 화면은 판매 등록 단계만 조회. 단계는 앞으로만 가고 출시 전 취소는 되돌릴 수 없다 (애플리케이션, PC-27 A). 출시 전 취소 때 가격 처리: 미반영 가격 행은 철회(사유 `PLAN_CHANGED`, 취소한 관리자)하고, 작성 중·결재 대기인 가격 변경 요청은 요청 전체를 철회한다. 이미 반영된 행은 실제 종료 일시를 취소 시각으로 채우고, 가격 캐시는 마지막 가격 기록으로 그대로 둔다 (컬럼 검토 PC-78 A).'),
  ('REGISTRATION_STATUS_CD','판매 등록 검수 상태 코드','Registration Inspection Status Code','VARCHAR2(30)','N',"'DRAFT'",'CK (값 목록)','상품 결정 19 C. 검수 요청·반려·승인 기록과 반려 사유는 `SYS_STATUS_HIST`에만 남긴다 (컬럼 검토 M-5 C). `SYS_STATUS_HIST`에 사유 컬럼이 필요하다 (SYS 도메인에서 설계). 최초 승인 뒤에는 승인과 수정 검수 요청만 오가며, 수정 검수 중에도 기존 승인 내용으로 계속 판매한다 (PC-25 A).'),
  ('SALE_STATUS_CD','스타일 판매 상태 코드','Style Sale Status Code','VARCHAR2(20)','N',"'READY'",'CK (값 목록)','품절은 상태가 아니라 재고에서 계산 (상품 결정 9 B). 단종은 되돌릴 수 없다 (애플리케이션, PC-27 A). 판매 중지 사유는 `SYS_STATUS_HIST`의 사유에 둔다 (PC-29 B).'),
  ('PENDING_REVISION_JSON','수정 검수 중인 수정안','Pending Revision Content JSON','JSON','Y','','','최초 승인 뒤 판매 중 상품의 수정안 (상세 문구, 고시 등 바꿀 항목만). 승인되면 스타일 행에 반영하고 이전 내용은 `PRD_DISPLAY_CONTENT_HIST`에 남긴 뒤 NULL. 반려되면 NULL. 한 스타일에 수정 검수는 한 번에 하나다. 요청·반려 기록과 사유는 `SYS_STATUS_HIST` (컬럼 검토 PC-25-1 B).'),
  ('FIRST_REGISTRATION_APPROVED_AT','최초 판매 등록 승인 일시','First Registration Approved At',TS,'Y','','','처음 승인될 때 한 번 채우고 바꾸지 않는다. NULL이면 판매 준비만 허용 (PC-25 A, PC-28 A). 승인 전에 최초 가격(`INITIAL`) 요청이 승인·반영되어 가격 캐시가 채워져 있어야 한다 (테이블 CHECK와 애플리케이션 검사). 사전 예약과 판매는 모두 최초 승인 뒤라서, 공개·예약·판매 어느 시점에도 반영된 가격이 있다 (컬럼 검토 PC-75 A).'),
  ('FIRST_SALE_STARTED_AT','최초 판매 개시 일시 (출시일)','First Sale Started At',TS,'Y','','','처음 판매 중이 된 시각. 예약 오픈 일시(`SALE_START_AT`)와 달리 고정. 신상품 기준, 출시 후 N일 판매율, 리오더 판단에 쓴다 (PC-28 A).'),
  ('DISCONTINUED_AT','단종 일시','Discontinued At',TS,'Y','','','판매 상태가 단종일 때만 채운다 (PC-28 A).'),
  ('DISCONTINUATION_REASON_CD','단종 사유 코드','Discontinuation Reason Code','VARCHAR2(30)','Y','','CK (값 목록)','단종일 때만 채운다. 단종은 한 번만 일어나 스타일 컬럼에 둔다. 후속 상품 대체이면 연관 상품 `SUCCESSOR`가 있어야 한다 (애플리케이션 검사, PC-29 B).'),
  ('PRE_LAUNCH_DROPPED_AT','출시 전 취소 일시','Pre-Launch Dropped At',TS,'Y','','','단계가 출시 전 취소일 때만 채운다 (PC-24 A, PC-28 A). 최초 승인 전이면 판매 등록 단계에서도 취소할 수 있어 “기획 취소”에서 이름을 바꿨다 (컬럼 검토 PC-62 A). 취소 때 가격 행 처리는 `STYLE_STAGE_CD` 설명 (PC-78 A).'),
  ('PRE_LAUNCH_DROP_REASON_CD','출시 전 취소 사유 코드','Pre-Launch Drop Reason Code','VARCHAR2(30)','Y','','CK (값 목록)','출시 전 취소일 때만 채운다. 기획 대비 출시 전환율, 취소 사유별 통계의 근거 (PC-29 B, PC-62 A).'),
 ]),
 ('가격', [
  ('LIST_PRICE_AMT','현재 정가 캐시 (원화)','Current List Price Cache Amount (KRW)',AMT,'Y','','CK (> 0, 10원 단위)','기획·생산 단계와 판매 등록 작업 중에는 NULL일 수 있다. 최초 승인되었으면 필수 (테이블 CHECK, 컬럼 검토 PC-75 A). 최초 가격 행(`INITIAL`)은 판매 등록 때 처음 쓴다. 기획·생산 단계의 잠정 가격을 원장에 남기지 않기 위해서다 (컬럼 검토 PC-59 A, 문구 PC-82 A). 원천은 `PRD_PRICE_HIST`. 정가 변경도 이력 행으로 예약하고, 반영 때 스케줄러가 같은 트랜잭션에서 판매가 캐시와 함께 갱신한다 (PC-77 A) (상품 결정 8 B, 컬럼 검토 PC-32 A). 10원 단위 (PC-39 A).'),
  ('CURRENT_SALE_PRICE_AMT','현재 판매가 캐시 (원화)','Current Sale Price Cache Amount (KRW)',AMT,'Y','','CK (> 0, 10원 단위)','스타일 전체 판매가 행(`CURRENT_PRICE_HIST_ID`)의 판매가. 그 행과 금액이 항상 일치해 캐시를 검증할 수 있다. 예약 시각에 스케줄러가 갱신 (상품 결정 32 B). 컬러 특가는 들어가지 않는다. 목록 표시용 최저가는 `LOWEST_SALE_PRICE_AMT`, 컬러마다 실제 판매가는 `PRD_STYLE_COLOR.CURRENT_SALE_PRICE_AMT` (컬럼 검토 PC-76 A, PC-65 A의 “컬러 중 최저가”에서 변경).'),
  ('CURRENT_DISCOUNT_RT','현재 정가 대비 할인율 캐시 (%)','Current Discount Rate Cache','NUMBER(3)','Y','','CK (0~99)','최초 승인 전에는 NULL일 수 있다 (PC-75 A). 스타일 전체 판매가 기준 (PC-76 A). (1 − 현재 판매가 ÷ 현재 정가) × 100, 소수점 이하 내림 [제안: 반올림 규칙]. 가격 캐시를 갱신할 때 함께 계산한다 (컬럼 검토 PC-34 B). 표시용 값이라 한도 검사에는 쓰지 않는다 (PC-81 A).'),
  ('LOWEST_SALE_PRICE_AMT','최저 판매가 캐시 (원화)','Lowest Sale Price Cache Amount (KRW)',AMT,'Y','','CK (> 0, 10원 단위)','컬러별 현재 판매가(`PRD_STYLE_COLOR.CURRENT_SALE_PRICE_AMT`) 중 가장 낮은 값. 컬러 판매가 행이 없으면 스타일 현재 판매가와 같다. 컬러 판매가가 스타일 전체 판매가보다 높을 수 있어 현재 판매가보다 클 수도 있다 (PC-80 A). 목록의 “39,000원~” 표시, 가격 정렬, 가격 필터용. 컬러 캐시를 갱신할 때 함께 갱신 (컬럼 검토 PC-76 A).'),
  ('LOWEST_PRICE_DISCOUNT_RT','최저가 기준 할인율 캐시 (%)','Lowest Price Discount Rate Cache','NUMBER(3)','Y','','CK (0~99)','(1 − 최저 판매가 ÷ 현재 정가) × 100. 목록의 “최대 N%” 표시용. 계산 규칙은 `CURRENT_DISCOUNT_RT`와 같다. 최대 허용 할인율 한도(`MAX_DISCOUNT_RT`)와는 다른 값이다 (PC-76 A).'),
  fk('CURRENT_PRICE_HIST_ID','현재 적용 가격 이력 식별 번호','Current Applied Price History Identifier','PRD_PRICE_HIST',null='Y',desc='스타일 전체 판매가 행(`STYLE_COLOR_ID` NULL) 중 현재 적용 행. 컬러별 판매가 행은 `PRD_STYLE_COLOR.CURRENT_PRICE_HIST_ID`가 가리킨다 (PC-65 A). 현재 판매가 캐시가 어느 판매가 행에서 왔는지 (정가 캐시는 가장 최근 반영된 정가 행으로 검증, PC-60 재확인 A). 예약 배치 실패·중복 실행 때 캐시 검증 근거. 출시 전 취소면 그 행에 실제 종료 일시가 채워져도 마지막 반영 행을 그대로 가리킨다 (PC-78 A, PC-82 A). 주문 스냅샷에 남길지는 주문 도메인에서 정한다. 스타일과 이력이 서로 참조해 DDL에서 이 FK는 두 테이블을 만든 뒤 추가한다 (PC-33 A).'),
  ('CURRENT_PRICE_APPLY_END_AT','현재가 적용 종료 일시 캐시','Current Price Apply End At Cache',TS,'Y','','','현재 적용 스타일 전체 판매가 행의 종료 일시. NULL이면 다음 판매가 행까지. “할인 종료까지” 표시용 (PC-33 A). 반영 때와, 적용 중인 행의 종료 시각을 바꿀 때(PC-66 A, PC-71 A) 같은 트랜잭션에서 갱신한다 (컬럼 검토 PC-82 A).'),
  ('NEXT_SALE_PRICE_AMT','다음 예약 판매가 캐시 (원화)','Next Reserved Sale Price Cache Amount (KRW)',AMT,'Y','','CK (> 0, 10원 단위)','철회되지 않았고 작성 중·결재 대기가 아닌 요청의 가장 가까운 미래 스타일 전체 판매가 행의 판매가 (PC-63 A, PC-65 A, PC-69 A). 요청 완료, 승인, 철회, 반영, 종료 시각 변경(복귀 행을 다시 만듦) 때 갱신 (PC-36 A, 컬럼 검토 PC-82 A). 스타일 전체 판매가 행만 본다. 컬러 특가 예약은 들어가지 않으므로, 관리자 목록의 예약 여부는 가격 이력에서 조회한다 (컬럼 검토 PC-79 A).'),
  ('NEXT_PRICE_APPLY_START_AT','다음 예약 적용 시작 일시 캐시','Next Reserved Price Apply Start At Cache',TS,'Y','','','예약이 없으면 NULL (PC-36 A).'),
  ('MAX_DISCOUNT_RT','최대 허용 할인율 (%)','Maximum Allowed Discount Rate','NUMBER(3)','Y','','CK (0~99)','NULL이면 공통코드 정책값 `PRODUCT_POLICY.MAX_DISCOUNT_RATE_DEFAULT`. 이보다 큰 할인 예약이 있는 가격 변경 요청은 결재 대기가 되고 승인 뒤에 반영된다 (`PRD_PRICE_CHANGE_REQUEST`, PC-48 재확인 A로 PC-35 A의 “저장 거부” 변경). 한도 값은 권한 있는 관리자만 바꾸고 데이터 변경 이력에 남는다 (상품 결정 19, 컬럼 검토 PC-35 A). 한도 검사는 내림하지 않은 정확한 값으로 한다: 판매가 < 그 시점 정가 × (1 − 한도 ÷ 100)이면 한도 초과. 50% 한도에서 50.9% 할인은 초과다. 표시용 할인율 캐시(내림)는 검사에 쓰지 않는다 (컬럼 검토 PC-81 A).'),
  ('TAXATION_TYPE_CD','과세 구분 코드','Taxation Type Code','VARCHAR2(20)','N',"'TAXABLE'",'CK (값 목록)','PG·현금영수증·정산 연동용. 의류는 과세 (PC-38 B).'),
  ('PRICE_CACHE_UPDATED_AT','가격 캐시 갱신 일시','Price Cache Updated At',TS,'Y','','','스타일 정가·판매가·할인율·최저가·다음 예약 캐시를 마지막으로 갱신한 트랜잭션의 시각. 같은 적용 시작의 가격 행은 한 트랜잭션에서 반영하고 캐시를 마지막에 한 번 갱신하므로 반영 한 번에 한 번 바뀐다 (PC-77 A). 적용 시작이 지났는데 이 값이 그보다 이르면 반영 지연으로 감시한다 (컬럼 검토 PC-82 A).'),
 ]),
 ('판매 기간·공개', [
  ('SALE_START_AT','판매 시작 일시','Sale Start At',TS,'Y','','','발매일 예약 오픈 (상품 결정 28 B). 이 시각에 스케줄러가 판매 상태를 판매 준비 → 판매 중으로 바꾸고, 처음이면 `FIRST_SALE_STARTED_AT`을 기록한다 (컬럼 검토 PC-45 A).'),
  ('SALE_END_AT','판매 종료 일시','Sale End At',TS,'Y','','','지나도 판매 상태는 바꾸지 않는다. 구매 가능 여부는 기간으로 계산해 “판매 종료”로 표시하고, 상품 페이지·리뷰·검색은 유지한다 (PC-45 A).'),
  ('DISPLAY_START_AT','상품 페이지 공개 시작 일시','Product Page Display Start At',TS,'Y','','','발매 전 “Coming Soon” 공개. NULL이면 판매 시작 일시와 같다. 상세 URL 접근 제어 기준이고, 메뉴·기획전 편성은 전시 도메인 (PC-43 A).'),
 ]),
 ('구매 조건·혜택 제외', [
  ('PURCHASE_TARGET_CD','구매 대상 코드','Purchase Target Code','VARCHAR2(20)','N',"'ALL'",'CK (값 목록)','상품 결정 30 B. 임직원 전용은 일반 목록에서 이 값으로 거른다.'),
  ('MIN_PURCHASE_GRADE_CD','구매 가능 최소 회원 등급 코드','Minimum Purchase Grade Code','VARCHAR2(30)','Y','','','`MBR_GRADE.GRADE_CD` 문자열. 비교할 때 현재 적용 버전의 등급 서열을 조회한다. FK가 없어 코드 존재는 애플리케이션이 검사 (컬럼 검토 PC-1 B, 상품 결정 30 B의 “최소 등급 FK” 변경: `MBR_GRADE`가 적용 기간별 버전 행이라).'),
  ('PER_ORDER_LIMIT_QTY','1회 주문 구매 한도 수량','Per-Order Purchase Limit Quantity','NUMBER(5)','Y','','CK (>= 1)','NULL이면 제한 없음. 스타일 단위 (컬럼 검토 M-6 B, 상품 결정 29 C 변경).'),
  ('DAILY_LIMIT_QTY','1인 1일 구매 한도 수량','Per-Member Daily Purchase Limit Quantity','NUMBER(5)','Y','','CK (>= 1)','검사는 주문 도메인.'),
  ('PER_MEMBER_TOTAL_LIMIT_QTY','1인 누적 구매 한도 수량','Per-Member Total Purchase Limit Quantity','NUMBER(5)','Y','','CK (>= 1)','판매 기간 전체 누적. 회원 전용 상품만 (테이블 CHECK).'),
  yn('COUPON_EXCLUDED_YN','쿠폰 적용 제외 여부','Coupon Excluded Flag','N','Y면 어떤 쿠폰 설정보다 우선한다 (상품 결정 31 C).'),
  yn('POINT_USE_EXCLUDED_YN','적립금 사용 제외 여부','Point Use Excluded Flag','N',''),
  yn('POINT_EARN_EXCLUDED_YN','적립금 적립 제외 여부','Point Earn Excluded Flag','N',''),
  yn('EMPLOYEE_DISCOUNT_EXCLUDED_YN','임직원 할인 제외 여부','Employee Discount Excluded Flag','N','Y면 `MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT` 계산에서도 뺀다.'),
  yn('GRADE_DISCOUNT_EXCLUDED_YN','등급 할인 제외 여부','Grade Discount Excluded Flag','N',''),
 ]),
 ('채널 노출', [
  yn('PC_EXPOSURE_YN','PC 노출 여부','PC Exposure Flag','Y','상품 결정 35 A(재선택). 가격·혜택은 모든 채널 공통.'),
  yn('MOBILE_WEB_EXPOSURE_YN','모바일 웹 노출 여부','Mobile Web Exposure Flag','Y',''),
  yn('APP_EXPOSURE_YN','앱 노출 여부','App Exposure Flag','Y',''),
 ]),
 ('청약철회 제한', [
  ('WITHDRAWAL_RESTRICTION_CD','청약철회 제한 사유 코드','Withdrawal Restriction Reason Code','VARCHAR2(30)','N',"'NONE'",'CK (값 목록)','전자상거래법 17조 2항 사유 (상품 결정 33 B). 주문 때 스냅샷.'),
  ('WITHDRAWAL_RESTRICTION_NOTICE_CN','청약철회 제한 고지 문구','Withdrawal Restriction Notice Content','VARCHAR2(1000)','Y','','','17조 6항 사전 고지. 바뀌면 이전 문구는 `PRD_DISPLAY_CONTENT_HIST` (44 B).'),
 ]),
 ('배송', [
  ('DELIVERY_TYPE_CD','배송 유형 코드','Delivery Type Code','VARCHAR2(20)','N',"'NORMAL'",'CK (값 목록)','상품 결정 34 B.'),
  yn('BUNDLE_DELIVERY_YN','묶음 배송 가능 여부','Bundle Delivery Allowed Flag','Y',''),
  ('BOX_SIZE_CD','박스 규격 코드','Box Size Code','VARCHAR2(20)','Y','','CK (값 목록)','실측 무게·치수는 창고 도메인.'),
 ]),
 ('상품 속성 (필터)', [
  ('FIT_CD','핏 코드','Fit Code','VARCHAR2(30)','Y','','CK (값 목록)','회원 선호 핏과 같은 공통코드 그룹 `FIT` (상품 결정 6 C).'),
  ('THICKNESS_CD','두께감 코드','Thickness Code','VARCHAR2(10)','Y','','CK (값 목록)',''),
  ('STRETCH_CD','신축성 코드','Stretch Code','VARCHAR2(10)','Y','','CK (값 목록)',''),
  ('SHEERNESS_CD','비침 코드','Sheerness Code','VARCHAR2(10)','Y','','CK (값 목록)',''),
  ('LINING_CD','안감 코드','Lining Code','VARCHAR2(10)','Y','','CK (값 목록)',''),
  yn('SPRING_FALL_WEARING_YN','봄·가을 착용 여부','Spring and Fall Wearing Flag','N','계절별 Y/N로 여러 계절을 함께 표시한다 (컬럼 검토 PC-6 B). 셋 다 Y면 사계절.'),
  yn('SUMMER_WEARING_YN','여름 착용 여부','Summer Wearing Flag','N',''),
  yn('WINTER_WEARING_YN','겨울 착용 여부','Winter Wearing Flag','N',''),
  ('DETAIL_ATTRIBUTE_JSON','상세 표시 속성 (복종별)','Detail Attribute JSON','JSON','Y','','','넥라인, 포켓 수, 단추 종류 등. 값 목록 검증은 애플리케이션 (상품 결정 6 C).'),
 ]),
 ('상품정보제공고시·표시 정보', [
  ('MANUFACTURER_NM','제조자 이름','Manufacturer Name','VARCHAR2(200)','Y','','','판매 등록 전 필수 (애플리케이션 검증).'),
  ('IMPORTER_NM','수입자 이름','Importer Name','VARCHAR2(200)','Y','','','고시 (1)~(4) “수입품의 경우 수입자를 함께 표기”. 제조국에 `KR`이 아닌 나라가 있으면 필수 (애플리케이션 검사, 법률 검토 L14 B).'),
  ('MANUFACTURING_COUNTRY_JSON','제조국 목록 (ISO 3166-1 alpha-2)','Manufacturing Country List JSON','JSON','Y','','','예: `["CN","VN"]`. 생산 차수마다 제조국이 다를 수 있어 목록으로 두고 화면에는 “중국, 베트남 (입고 시기에 따라 다름)”처럼 표시 (대외무역법 33조④1호 오인 표시 금지, 법률 검토 L13 B). 값은 공통코드 `COUNTRY`(소유 `CMM`, 파일 적재, 컬럼 검토 PC-15 A). 코드 검사는 애플리케이션. 판매 등록 전 필수.'),
  ('EARLIEST_STOCK_MANUFACTURED_YM','보유 재고 중 가장 빠른 제조연월 캐시','Earliest Stock Manufactured Year-Month Cache','VARCHAR2(6)','Y','','CK (YYYYMM)','고시 (1) 의류 “제조연월”을 고시 Ⅱ-4 가(보유한 동일 상품 중 가장 빠른 날짜) 방식으로 표시. 재고 입고 차수의 제조연월에서 배치로 계산 (법률 검토 L15 B). 입고 차수별 제조연월은 재고·창고 도메인에서 설계.'),
  ('ITEM_NOTICE_JSON','고시 항목 값','Product Information Notice Item JSON','JSON','Y','','','품목군(관리 분류)별 항목. 소재는 원단, 세탁 방법은 세탁 기호에서 만들 수 있다 (상품 결정 7 C).'),
  ('CARE_SYMBOL_JSON','세탁·취급 표시 기호 목록','Care Label Symbol List JSON','JSON','Y','','','세탁 기호 코드 배열, 배열 순서가 표시 순서. 코드는 공통코드 `CARE_SYMBOL` (컬럼 검토 M-2 B, 상품 결정 46 B 변경). 판매 등록 전 필수.'),
  ('SIZE_MEASUREMENT_JSON','사이즈별 실측 (cm)','Size Measurement JSON','JSON','Y','','','예: `{"M":{"TOTAL_LENGTH":70,"CHEST_WIDTH":56},…}`. 키는 사이즈 코드와 측정 부위 코드 (공통코드 `MEASUREMENT_PART`). 사이즈 추천은 회원 체형과 이 값으로 화면에서 계산 (컬럼 검토 M-4 B·M-13 B, 상품 결정 13 B·51 B 변경).'),
  ('CERTIFICATION_TYPE_CD','안전 인증 유형 코드','Safety Certification Type Code','VARCHAR2(30)','Y','','CK (값 목록)','인증 대상이 아니면 NULL. 인증은 스타일당 1개 (컬럼 검토 M-3 B, 상품 결정 27 C 변경).'),
  ('CERTIFICATION_NO','안전 인증 번호','Safety Certification Number','VARCHAR2(50)','Y','','',''),
  ('CERTIFICATION_VALID_END_DT','안전 인증 유효 종료 일자','Safety Certification Valid End Date','DATE','Y','','','공급자적합성확인처럼 기간이 없으면 NULL.'),
 ]),
 ('상세 문구·검색 노출', [
  ('SUMMARY_DESC','상품 요약 설명','Style Summary Description','VARCHAR2(1000)','Y','','','상품 결정 12 C.'),
  ('DESIGNER_NOTE_CN','디자이너 노트','Designer Note Content','VARCHAR2(2000)','Y','','',''),
  ('STYLING_TIP_CN','스타일링 팁','Styling Tip Content','VARCHAR2(2000)','Y','','',''),
  ('TAG_JSON','상품 태그 목록','Style Tag List JSON','JSON','Y','','','태그 이름 배열 (`#` 없이). 태그 검색·모아 보기는 검색 엔진, 표기 통일은 관리 화면 자동 완성 (컬럼 검토 M-7 C, 상품 결정 38 B 변경).'),
  ('META_TITLE_NM','검색 노출 제목 (덮어쓰기)','Meta Title Override','VARCHAR2(200)','Y','','','NULL이면 상품명으로 자동 생성 (상품 결정 40 B).'),
  ('META_DESC','검색 노출 설명 (덮어쓰기)','Meta Description Override','VARCHAR2(500)','Y','','','NULL이면 요약 설명으로 자동 생성.'),
 ]),
 ('담당', [
  ('RESPONSIBLE_MD_ADMIN_ID','담당 MD 관리자 식별 번호','Responsible MD Administrator Identifier',ID,'Y','',f'FK → {ADM}','책임자 표시용. 수정 권한은 관리자 담당 범위로 판단 (상품 결정 41 C). 범위 밖 MD 지정은 애플리케이션이 막는다. 이름은 역할 + 관리자 PK 이름이고, 관리자 PK 이름이 정해지면 뒷부분을 맞춘다 (컬럼 검토 PC-2 A).'),
 ]),
 ('판매·고객 반응 캐시', [
  ('RECENT_7_DAY_SALES_QTY','최근 7일 판매 수량 캐시','Recent 7-Day Sales Quantity Cache','NUMBER(9)','N','0','CK (>= 0)','`PRD_SALES_DAILY_STAT`에서 배치 계산 (상품 결정 39 D).'),
  ('RECENT_30_DAY_SALES_QTY','최근 30일 판매 수량 캐시','Recent 30-Day Sales Quantity Cache','NUMBER(9)','N','0','CK (>= 0)',''),
  ('REVIEW_CNT','리뷰 수 캐시','Review Count Cache','NUMBER(9)','N','0','CK (>= 0)','리뷰 도메인 원천, 배치 갱신 (상품 결정 53 B).'),
  ('REVIEW_AVERAGE_RATING_VAL','리뷰 평균 평점 캐시','Review Average Rating Cache','NUMBER(2,1)','Y','','CK (1.0~5.0)','리뷰가 없으면 NULL.'),
  ('SIZE_FEEDBACK_SMALL_CNT','사이즈 체감 “작아요” 수','Size Feedback Small Count','NUMBER(9)','N','0','CK (>= 0)','받는 방식은 리뷰 도메인에서 정한다.'),
  ('SIZE_FEEDBACK_TRUE_CNT','사이즈 체감 “정사이즈” 수','Size Feedback True-to-Size Count','NUMBER(9)','N','0','CK (>= 0)',''),
  ('SIZE_FEEDBACK_LARGE_CNT','사이즈 체감 “커요” 수','Size Feedback Large Count','NUMBER(9)','N','0','CK (>= 0)',''),
  ('VIEW_CNT','조회수 캐시 (외부 분석 도구)','View Count Cache','NUMBER(12)','N','0','CK (>= 0)','외부 도구에서 일 배치로 받는다 (선행 결정 12).'),
  ('CACHE_UPDATED_AT','캐시 컬럼 갱신 일시','Cache Updated At',TS,'Y','','','판매·고객 반응 캐시 배치의 마지막 실행.'),
 ]),
 ('동시 수정 감지', [
  ('ROW_VERSION_NO','스타일 행 수정 버전 번호','Style Row Version Number','NUMBER(10)','N','0','CK (>= 0)','MD, 검수자, 가격 배치가 같은 행을 동시에 고칠 때 덮어쓰기를 막는다. 수정할 때 `WHERE ROW_VERSION_NO = 읽은 값`으로 확인하고 1 올린다. 다른 테이블로 넓힐지는 공통 결정으로 따로 정한다 (컬럼 검토 PC-30 A).'),
 ]),
 ],
 check=['`ORIGINAL_STYLE_ID <> STYLE_ID` (자기 자신을 첫 세대로 가리키지 않음, PC-21 B)', '`CURRENT_SALE_PRICE_AMT <= LIST_PRICE_AMT` (PC-39 A, PC-5 A와 같은 규칙)', '`LOWEST_SALE_PRICE_AMT <= LIST_PRICE_AMT` (컬러 판매가는 스타일 전체 판매가보다 높을 수 있어 현재 판매가가 아니라 정가와 비교, PC-80 A로 PC-76 A의 CHECK 변경)', '`FIRST_REGISTRATION_APPROVED_AT` NOT NULL이면 `LIST_PRICE_AMT`, `CURRENT_SALE_PRICE_AMT`, `CURRENT_DISCOUNT_RT`, `LOWEST_SALE_PRICE_AMT`, `LOWEST_PRICE_DISCOUNT_RT` NOT NULL (PC-75 A, PC-59 A의 “판매 등록 단계이면”에서 변경. 판매 등록 단계로 바뀌는 순간에는 아직 가격 행이 없어 단계를 바꿀 수 없었다)', '`MOD(LIST_PRICE_AMT, 10) = 0`, `MOD(CURRENT_SALE_PRICE_AMT, 10) = 0`, `MOD(NEXT_SALE_PRICE_AMT, 10) = 0`, `MOD(LOWEST_SALE_PRICE_AMT, 10) = 0` (10원 단위, PC-39 A, PC-76 A)', '`NEXT_SALE_PRICE_AMT`와 `NEXT_PRICE_APPLY_START_AT`은 함께 NULL이거나 함께 NOT NULL (PC-36 A)', '`FIRST_REGISTRATION_APPROVED_AT IS NULL`이면 `SALE_STATUS_CD = \'READY\'` (최초 승인 전 판매 불가, PC-25 A로 변경)', '`STYLE_STAGE_CD IN (\'PLANNING\', \'PRODUCTION\')`이면 `REGISTRATION_STATUS_CD = \'DRAFT\'`, `SALE_STATUS_CD = \'READY\'`, `FIRST_REGISTRATION_APPROVED_AT IS NULL` (PC-27 A)', '`STYLE_STAGE_CD = \'DROPPED\'`이면 `REGISTRATION_STATUS_CD IN (\'DRAFT\', \'INSPECTION_REQUESTED\', \'REJECTED\')`, `SALE_STATUS_CD = \'READY\'`, `FIRST_REGISTRATION_APPROVED_AT IS NULL` (PC-62 A)', '`FIRST_REGISTRATION_APPROVED_AT` NOT NULL이면 `REGISTRATION_STATUS_CD IN (\'APPROVED\', \'MODIFICATION_REQUESTED\')`, NULL이면 `REGISTRATION_STATUS_CD <> \'MODIFICATION_REQUESTED\'` (PC-27 A)', '`SALE_STATUS_CD IN (\'ON_SALE\', \'SUSPENDED\')`이면 `FIRST_SALE_STARTED_AT` NOT NULL (PC-28 A)', '`REGISTRATION_STATUS_CD = \'MODIFICATION_REQUESTED\'` ⇔ `PENDING_REVISION_JSON` NOT NULL (PC-25-1 B)', '`SALE_STATUS_CD = \'DISCONTINUED\'` ⇔ `DISCONTINUED_AT`, `DISCONTINUATION_REASON_CD` NOT NULL (PC-29 B)', '`STYLE_STAGE_CD = \'DROPPED\'` ⇔ `PRE_LAUNCH_DROPPED_AT`, `PRE_LAUNCH_DROP_REASON_CD` NOT NULL (PC-29 B)',
        '`PURCHASE_TARGET_CD = \'GRADE_OR_ABOVE\'` ⇔ `MIN_PURCHASE_GRADE_CD` NOT NULL',
        '세 채널 노출 여부 중 하나 이상 Y (상품 결정 35)',
        '`WITHDRAWAL_RESTRICTION_CD <> \'NONE\'`이면 고지 문구 NOT NULL',
        '`SALE_START_AT <= SALE_END_AT`, `DISPLAY_START_AT <= SALE_START_AT` (PC-46 A)',
        '`PER_MEMBER_TOTAL_LIMIT_QTY` NOT NULL이면 `PURCHASE_TARGET_CD <> \'ALL\'` (1인 누적 한도는 회원 전용, 상품 결정 29)',
        '`CERTIFICATION_TYPE_CD`와 `CERTIFICATION_NO`는 함께 NULL이거나 함께 NOT NULL'],
 idx=['IX `IX_PRD_STYLE_BRAND_ID`, `IX_PRD_STYLE_SEASON_ID`, `IX_PRD_STYLE_CATEGORY_ID`, `IX_PRD_STYLE_ORIGINAL_STYLE_ID` (FK)', '목록 정렬 인덱스는 두지 않는다. 고객 목록은 검색 엔진, 관리자 목록 인덱스는 조회 패턴이 생기면 추가 (컬럼 검토 PC-12 B)'])

table(t='PRD_STYLE_COLOR', ko='상품 스타일 컬러', en='Product Style Color',
 desc='스타일 × 컬러. 컬러별 사진·판매 상태·착용 정보의 단위이고, 회원 위시리스트·최근 본 상품이 이 행을 참조한다 (상품 결정 1 B).',
 basis='1 B, 9 B, 21 D, 26 B, 53 B', pk='대리 PK `SEQ_PRD_STYLE_COLOR`', cache=20, delete='상태 코드로 처리 (단종). 단종 때 위시리스트 행 물리 삭제 (상품 결정 42 세부 B)', part='없음', keep='-', ldel=False,
 cols=[
 ('식별', [
  ('STYLE_COLOR_ID','상품 스타일 컬러 고유 식별 번호','Product Style Color Unique Identifier',ID,'N','','PK','회원 도메인 FK 대상 (`MBR_WISHLIST_ITEM`, `MBR_RECENTLY_VIEWED_ITEM`).'),
  fk('STYLE_ID','스타일 식별 번호','Style Identifier','PRD_STYLE',extra='UK1'),
  fk('COLOR_ID','컬러 식별 번호','Color Identifier','PRD_COLOR',extra='UK1'),
  ('COLOR_DISPLAY_NM','컬러 화면 표시 이름','Color Display Name','VARCHAR2(100)','N','','','예: 차콜 멜란지. 리뷰 스냅샷의 컬러명 (선행 결정 17).'),
 ]),
 ('상태·표시', [
  ('SALE_STATUS_CD','컬러 판매 상태 코드','Color Sale Status Code','VARCHAR2(20)','N',"'READY'",'CK (값 목록)','상위(스타일)가 중지면 판매하지 않는다.'),
  sort_sn('컬러', 'Color'),
 ]),
 ('예약 판매', [
  yn('PREORDER_YN','예약 판매 여부','Preorder Flag','N','컬러 단위 예약 판매 (컬럼 검토 PC-40 B). 예약 중인 컬러라도 재고가 있는 사이즈는 일반 판매로 처리한다 (주문 로직). 예약 한도는 상품에 두지 않고 재고 도메인에서 SKU별 “입고 예정 수량 − 예약 주문 수량”으로 계산한다 (PC-41 C). 판매 시작 전 사전 예약: 스타일이 판매 준비 상태라도 최초 승인되었고 컬러가 예약 판매 기간 안이면 구매할 수 있다. 출시일(`FIRST_SALE_STARTED_AT`)은 판매 시작 일시 기준으로 두어 사전 예약 때문에 앞당기지 않는다. 예약 시작은 공개 시작 이후여야 한다 (테이블이 달라 애플리케이션 검사, 컬럼 검토 PC-61 A).'),
  ('PREORDER_START_AT','예약 판매 시작 일시','Preorder Start At',TS,'Y','','','판매 시작 일시보다 앞서도 된다 (발매 전 사전 예약, PC-46 A).'),
  ('PREORDER_END_AT','예약 판매 종료 일시','Preorder End At',TS,'Y','','','출고 예정일과의 순서는 제한하지 않는다 (순차 출고, PC-46 A).'),
  ('SHIPMENT_EXPECTED_DT','출고 예정 시작 일자','Shipment Expected Start Date','DATE','Y','','','전자상거래법 15조 1항 단서의 공급 시기 약정. 바꾸면 이전 값을 `PRD_DISPLAY_CONTENT_HIST`(유형 `SHIPMENT_SCHEDULE`)에 남긴다. 주문별 약속 출고일은 주문 스냅샷, 지연 통지(15조 2항)는 주문 도메인 (PC-42 B).'),
  ('SHIPMENT_EXPECTED_END_DT','출고 예정 마지막 일자','Shipment Expected End Date','DATE','Y','','','“12월 2주 차부터 순차 출고” 같은 범위 고지. NULL이거나 시작 일자와 같으면 하루 (PC-44 A).'),
 ]),
 ('가격 캐시', [
  ('CURRENT_SALE_PRICE_AMT','컬러 현재 판매가 캐시 (원화)','Color Current Sale Price Cache Amount (KRW)',AMT,'Y','','CK (> 0, 10원 단위)','이 컬러에 실제 적용되는 판매가. 컬러 판매가 행이 있으면 그 값, 없으면 스타일 전체 판매가. 기획·생산 단계에서는 NULL. 주문 가격 = 이 값 + SKU 추가 금액 (컬럼 검토 PC-65 A). 컬러 중 최저값은 `PRD_STYLE.LOWEST_SALE_PRICE_AMT`로 캐시한다 (PC-76 A).'),
  fk('CURRENT_PRICE_HIST_ID','컬러 현재 적용 판매가 이력 식별 번호','Color Current Applied Price History Identifier','PRD_PRICE_HIST',null='Y',desc='이 컬러에 지금 적용되는 판매가 행 (컬러 행 또는 스타일 전체 행). 컬러별 마크다운 차수(PC-37 B)를 이 행으로 읽는다. 컬러와 이력이 서로 참조해 DDL에서 이 FK는 두 테이블을 만든 뒤 추가한다 (PC-65 A).'),
 ]),
 ('모델 착용 정보', [
  ('FITTING_MODEL_HEIGHT_CM_VAL','착용 모델 키 (cm)','Fitting Model Height in Centimeters','NUMBER(3)','Y','','CK (100~230)','모델 개인은 식별하지 않는다 (상품 결정 26 B).'),
  ('FITTING_MODEL_WEIGHT_KG_VAL','착용 모델 몸무게 (kg)','Fitting Model Weight in Kilograms','NUMBER(3)','Y','','CK (20~200)','신체 수치는 키·몸무게·착용 사이즈만 둔다 (컬럼 검토 PC-7 A).'),
  ('FITTING_SIZE_CD','모델 착용 사이즈 코드','Fitting Size Code','VARCHAR2(20)','Y','','','스타일 관리 분류의 사이즈 체계 그룹 값.'),
 ]),
 ('고객 반응 캐시', [
  ('WISHLIST_CNT','찜 수 캐시','Wishlist Count Cache','NUMBER(9)','N','0','CK (>= 0)','`MBR_WISHLIST_ITEM`에서 배치 갱신 (상품 결정 53 B).'),
 ]),
 ],
 check=['`PREORDER_YN = \'Y\'`이면 예약 시작·종료 일시와 `SHIPMENT_EXPECTED_DT` NOT NULL',
        '`PREORDER_START_AT <= PREORDER_END_AT`, `SHIPMENT_EXPECTED_DT <= SHIPMENT_EXPECTED_END_DT` (PC-46 A)',
        '`SHIPMENT_EXPECTED_END_DT` NOT NULL이면 `SHIPMENT_EXPECTED_DT` NOT NULL',
        '스타일 판매 기간과의 비교는 테이블이 달라 애플리케이션이 검사한다 (PC-46 A)'],
 idx=['UK `UK_PRD_STYLE_COLOR_STYLE_ID_COLOR_ID`', 'IX `IX_PRD_STYLE_COLOR_COLOR_ID` (FK)'])

table(t='PRD_SKU', ko='상품 SKU (컬러 × 사이즈, 재고 단위)', en='Product SKU (Color by Size, Stock Unit)',
 desc='재고 단위. 실제 생산하는 조합만 만든다 (상품 결정 22 B). 사이즈가 없는 상품은 `FREE` (47 A). 판매 상품만 담는다. 사은품·포장재·부자재는 재고·창고(WMS) 도메인에 둔다 (컬럼 검토 M-12 C).',
 basis='1 B, 2 C, 3 B, 8 B, 9 B, 22 B, 47 A, 52 C', pk='대리 PK `SEQ_PRD_SKU`', cache=20, delete='상태 코드로 처리. 단종 때 재입고 알림 신청 물리 삭제 (상품 결정 42)', part='없음', keep='-', ldel=False,
 cols=[
 ('식별', [
  ('SKU_ID','상품 SKU 고유 식별 번호','Product SKU Unique Identifier',ID,'N','','PK',''),
  fk('STYLE_COLOR_ID','스타일 컬러 식별 번호','Style Color Identifier','PRD_STYLE_COLOR',extra='UK1'),
  ('SIZE_CD','사이즈 코드','Size Code','VARCHAR2(20)','N','','UK1','관리 분류의 사이즈 체계 공통코드 그룹 값 (상품 결정 3 B). 그룹이 분류마다 달라 CHECK 대신 애플리케이션이 검증.'),
  ('SKU_NO','SKU 코드 (품번-컬러-사이즈)','SKU Code','VARCHAR2(40)','N','','UK','예: `MS26STS001-BK-L`. 재사용 금지.'),
  ('BARCODE_NO','GS1 바코드 (EAN-13)','GS1 Barcode (EAN-13)','VARCHAR2(13)','Y','','UK, CK (숫자 13자리)','상품 결정 2 C. 업체 코드 발급 전에는 NULL.'),
 ]),
 ('가격·상태', [
  ('EXTRA_PRICE_AMT','SKU 추가 금액 (원화)','SKU Extra Price Amount (KRW)',AMT,'N','0','CK (>= 0, 10원 단위)','빅사이즈 추가 금액 캐시. 원천은 `PRD_PRICE_HIST`의 SKU 추가 금액 행이고 적용 시각에 스케줄러가 갱신한다 (PC-47 A). 최종가 = 컬러 현재 판매가 + 이 값 (상품 결정 8 B, PC-65 A). 10원 단위 (`MOD(EXTRA_PRICE_AMT, 10) = 0`, PC-39 A).'),
  ('SALE_STATUS_CD','SKU 판매 상태 코드','SKU Sale Status Code','VARCHAR2(20)','N',"'READY'",'CK (값 목록)','사이즈 단위 수동 판매 중지 (상품 결정 9 B).'),
  sort_sn('사이즈', 'Size'),
 ]),
 ('외부 코드', [
  ('ADVERTISING_FEED_ITEM_NO','광고·가격비교 피드 상품 번호','Advertising Feed Item Number','VARCHAR2(50)','Y','','','광고·가격비교 피드에 보내는 상품 식별 번호 (상품 결정 52 C, 컬럼 검토 PC-4 C). 생산 협력사 품번은 생산·소싱 도메인에 둔다.'),
 ]),
 ],
 idx=['UK `UK_PRD_SKU_STYLE_COLOR_ID_SIZE_CD`', 'UK `UK_PRD_SKU_SKU_NO`', 'UK `UK_PRD_SKU_BARCODE_NO`'])

# =========================================================== 4. 상품 구성 정보
table(t='PRD_STYLE_FABRIC', ko='스타일 사용 원단', en='Style Fabric Usage',
 desc='스타일 × 부위 × 원단 (상품 결정 24 D).',
 basis='24 D', pk='복합 PK (STYLE_ID, FABRIC_PART_CD, FABRIC_ID)', cache='-', delete='물리 삭제 (단순 매핑)', part='없음', keep='-', ldel=False,
 cols=[
 ('식별', [
  fk('STYLE_ID','스타일 식별 번호','Style Identifier','PRD_STYLE',extra='PK'),
  ('FABRIC_PART_CD','원단 사용 부위 코드','Fabric Part Code','VARCHAR2(20)','N','','PK, CK (값 목록)',''),
  fk('FABRIC_ID','원단 식별 번호','Fabric Identifier','PRD_FABRIC',extra='PK'),
 ]),
 ('표시', [sort_sn('원단', 'Fabric')]),
 ],
 idx=['IX `IX_PRD_STYLE_FABRIC_FABRIC_ID` (원단별 스타일 조회)'])

table(t='PRD_STYLE_MEDIA', ko='스타일 이미지·영상', en='Style Image and Video Media',
 desc='스타일 단위 미디어. 컬러 FK가 NULL이면 모든 컬러 공통 (상품 결정 11 C). 이미지형 상세는 유형 `DETAIL` (12 C).',
 basis='11 C, 12 C, 44 B', pk='대리 PK `SEQ_PRD_STYLE_MEDIA`', cache=20, delete='논리 삭제 (설정). 파일 원본은 6개월 안에 지우지 않는다 (상품 결정 44 B)', part='없음', keep='-', ldel=True,
 cols=[
 ('식별', [
  ('STYLE_MEDIA_ID','스타일 미디어 고유 식별 번호','Style Media Unique Identifier',ID,'N','','PK',''),
  fk('STYLE_ID','스타일 식별 번호','Style Identifier','PRD_STYLE'),
  fk('STYLE_COLOR_ID','컬러 식별 번호 (NULL = 공통)','Style Color Identifier','PRD_STYLE_COLOR',null='Y',desc='같은 스타일의 컬러여야 한다 (애플리케이션 검증).'),
  ('MEDIA_TYPE_CD','미디어 유형 코드','Media Type Code','VARCHAR2(20)','N','','CK (값 목록)',''),
 ]),
 ('파일', [
  ('MEDIA_URL','미디어 파일 경로','Media File Path','VARCHAR2(500)','N','','','저장소 상대 경로.'),
  ('ALTERNATIVE_TEXT_CN','대체 텍스트','Alternative Text Content','VARCHAR2(500)','Y','','','이미지형 상세는 필수 (애플리케이션 검증, 상품 결정 12 C).'),
  ('VIDEO_PLAY_SECOND_VAL','영상 재생 시간 (초)','Video Play Time in Seconds','NUMBER(5)','Y','','CK (> 0)','영상만.'),
  ('VIDEO_THUMBNAIL_URL','영상 썸네일 경로','Video Thumbnail Path','VARCHAR2(500)','Y','','','영상만.'),
  sort_sn('미디어', 'Media'),
 ]),
 ],
 check=['`MEDIA_TYPE_CD = \'VIDEO\'` ⇔ `VIDEO_PLAY_SECOND_VAL` NOT NULL'],
 idx=['IX `IX_PRD_STYLE_MEDIA_STYLE_ID_STYLE_COLOR_ID_SORT_SN` (상세 조회)'])

# =========================================================== 6. 가격·판매 조건
table(t='PRD_PRICE_CHANGE_REQUEST', ko='상품 가격 변경 요청 (스타일 1개부터 여러 스타일·SKU까지, 요청·결재·철회 단위)', en='Product Price Change Request (From One Style to Many Styles and SKUs, Unit of Request, Approval and Withdrawal)',
 desc='가격 변경 요청 1건 = 1행. 스타일 1개짜리 단건 변경이든 340개짜리 대량 변경이든 모두 요청 1건이고, 요청으로 생긴 가격 행은 `PRD_PRICE_HIST`에 있다 (요청은 이 테이블, 가격은 가격 이력). 단건·대량 여부는 대상 스타일 수(`TARGET_STYLE_CNT`)로 안다 (컬럼 검토 PC-55 재확인 A, PC-83 A). 예: “24 FW 시즌오프 1차 마크다운, 스타일 340개” 1행, “스타일 A 오류 정정” 1행. 최대 할인율을 넘는 행이 있는 요청만 결재를 거치고, 승인 전에는 스케줄러가 반영하지 않는다 (PC-48 재확인 A). 신규 스타일의 최초 가격(`INITIAL`)도 요청 1건이고 판매 등록 검수 승인과 별개다. 출시 할인으로 한도를 넘으면 결재 대상이다 (컬럼 검토 PC-74 A). 최초 가격 요청은 판매 등록 검수 승인 전에 승인·반영되어야 한다 (PC-75 A). 요청한 뒤에는 가격 행의 금액·시작 시각을 고칠 수 없고 철회만 할 수 있다. 바꾸려면 철회하고 새 요청을 만든다. 종료 시각 변경도 새 요청으로 하며, 새 종료 기준으로 한도를 다시 검사해 넘으면 결재를 받는다 (PC-71 A).',
 basis='32 B, 컬럼 검토 PC-48 B·재확인 A', pk='대리 PK `SEQ_PRD_PRICE_CHANGE_REQUEST`', cache=20, delete='삭제하지 않음 (원장 헤더). 요청 전체 철회는 철회 일시로 표시', part='없음', keep='삭제하지 않음 (가격 이력과 같음, PC-16 A)', ldel=False,
 cols=[
 ('식별', [
  ('PRICE_CHANGE_REQUEST_ID','가격 변경 요청 고유 식별 번호','Price Change Request Unique Identifier',ID,'N','','PK',''),
  ('PRICE_CHANGE_REQUEST_NO','가격 변경 요청 번호','Price Change Request Number','VARCHAR2(30)','N','','UK','업무 키. 화면·문의에서 쓰는 번호 (상품 결정 32 B).'),
 ]),
 ('변경 내용', [
  ('PRICE_CHANGE_TITLE_NM','가격 변경 요청 제목','Price Change Request Title','VARCHAR2(200)','N','','','예: 24 FW 시즌오프 1차.'),
  ('PRICE_CHANGE_DESC','가격 변경 요청 설명','Price Change Request Description','VARCHAR2(2000)','Y','','','맥락 설명 (재고 소진 특가, 기획전 연계 등). 변경 사유는 헤더에 두지 않고 이력 행에만 둔다. 요청 목록을 사유로 거를 때는 이력 행을 조회한다 (컬럼 검토 PC-54 A).'),
  ('TARGET_STYLE_CNT','가격 변경 요청 대상 스타일 수','Price Change Request Target Style Count','NUMBER(7)','N','0','CK (>= 0)','이 요청의 가격 이력 행에 들어 있는 서로 다른 스타일 수. 1이면 단건, 2 이상이면 대량 변경이다. 요청 목록의 단건·대량 필터와 결재 화면의 영향 규모 표시에 쓴다. 작성 중에는 저장 때마다 다시 계산하고 요청 완료 때 확정한다 (컬럼 검토 PC-83 A).'),
  ('TARGET_PRICE_ROW_CNT','가격 변경 요청 대상 가격 이력 행 수','Price Change Request Target Price History Row Count','NUMBER(7)','N','0','CK (>= 0)','이 요청의 가격 이력 행 수 (정가·판매가·컬러·SKU 추가 금액·복귀 행 모두). 스타일 1개짜리 변경도 여러 행이 될 수 있어(기간 한정 할인 = 판매가 행 + 복귀 행) 단건·대량 구분에는 쓰지 않는다. 계산 시점은 `TARGET_STYLE_CNT`와 같다 (PC-83 A로 `TARGET_CNT`에서 이름 변경).'),
 ]),
 ('요청', [
  ('REQUESTED_BY_ADMIN_ID','가격 변경 요청 관리자 식별 번호','Price Change Requesting Administrator Identifier',ID,'N','',f'FK → {ADM}',''),
  ('PRICE_CHANGE_REQUEST_STATUS_CD','가격 변경 요청 진행 상태 코드','Price Change Request Progress Status Code','VARCHAR2(20)','N',"'DRAFT'",'CK (값 목록)','작성 중이면 가격 행을 나눠 만들 수 있다. 작성 중인 요청의 가격 행은 반영·기간 겹침 검사(PC-58)·캐시에서 빼고, 요청 완료로 바꿀 때 겹침 검사와 결재 필요 여부 계산을 한다 (컬럼 검토 PC-69 A).'),
  ('REQUESTED_AT','가격 변경 요청 일시','Price Change Request Requested At',TS,'Y','','','요청 완료로 바꾼 시각. 작성 중이면 NULL (PC-69 A).'),
 ]),
 ('결재 근거', [
  ('MAX_REQUESTED_DISCOUNT_RT','요청 안 최대 할인율 (%)','Maximum Requested Discount Rate','NUMBER(3)','Y','','CK (0~99)','요청 완료 때 계산. 이 요청의 판매가 행 중 그 시점 정가 대비 가장 큰 할인율 (컬럼 검토 PC-70 A). 소수점 이하 올림으로 저장해 한도 초과 사실이 값에 드러나게 한다 (50.1% → 51). 결재 필요 여부는 이 값이 아니라 정확한 값으로 판단한다 (PC-81 A).'),
  ('OVER_LIMIT_STYLE_CNT','할인 한도 초과 스타일 수','Discount Limit Exceeded Style Count','NUMBER(7)','Y','','CK (>= 0)','요청 완료 때 계산. 이 요청의 판매가 행(스타일 전체, 컬러) 중 하나라도 스타일별 할인 한도(없으면 기본 한도)를 넘는 스타일 수. 대상 스타일 수(`TARGET_STYLE_CNT`)와 단위가 같아 결재 화면에 “340개 중 12개 한도 초과”처럼 보인다. 한 스타일 안에서 몇 개 컬러가 넘었는지는 가격 이력 행을 조회한다 (PC-70 A, 컬럼 검토 PC-86 A로 `OVER_LIMIT_ROW_CNT` 판매가 행 수에서 변경). 초과 판단은 정확한 값 기준 (`PRD_STYLE.MAX_DISCOUNT_RT` 설명, PC-81 A).'),
  ('REQUEST_DEFAULT_MAX_DISCOUNT_RT','요청 당시 기본 최대 할인율 (%)','Default Maximum Discount Rate at Request','NUMBER(3)','Y','','CK (0~99)','요청 완료 때 정책값 `PRODUCT_POLICY.MAX_DISCOUNT_RATE_DEFAULT`를 복사. 한도가 나중에 바뀌어도 결재가 필요했던 근거가 남는다 (PC-70 A).'),
 ]),
 ('결재', [
  yn('APPROVAL_REQUIRED_YN','가격 변경 요청 결재 필요 여부','Price Change Request Approval Required Flag','N','이 요청에 최대 허용 할인율(`PRD_STYLE.MAX_DISCOUNT_RT`, NULL이면 정책값)을 넘는 행이 하나라도 있으면 Y. 저장 때 애플리케이션이 계산한다 (PC-48 재확인 A, PC-35 A 변경).'),
  ('PRICE_CHANGE_APPROVAL_STATUS_CD','가격 변경 요청 결재 상태 코드','Price Change Request Approval Status Code','VARCHAR2(20)','N',"'NOT_REQUIRED'",'CK (값 목록)','결재 대기·반려·기한 경과 건의 행은 스케줄러가 반영하지 않는다. 반려하면 그 요청의 모든 미반영 행(복귀 행 포함)에 철회 정보를 채운다 (사유 `APPROVAL_REJECTED`, 철회 관리자 = 결재자). 결재 대기 중 가장 이른 적용 시작이 지나면 승인할 수 없고, 배치가 상태를 기한 경과(`EXPIRED`)로 바꾸고 행을 철회한다 (사유 `APPROVAL_EXPIRED`, 철회 관리자 NULL) (컬럼 검토 PC-63 A).'),
  ('APPROVED_BY_ADMIN_ID','가격 변경 요청 결재 관리자 식별 번호','Price Change Request Approving Administrator Identifier',ID,'Y','',f'FK → {ADM}','승인 또는 반려한 관리자. 요청자와 달라야 한다 (CHECK). 결재 권한은 관리자 도메인 RBAC.'),
  ('APPROVAL_DECIDED_AT','가격 변경 요청 결재 처리 일시','Price Change Request Approval Decided At',TS,'Y','','',''),
  ('APPROVAL_COMMENT_CN','가격 변경 요청 결재 의견','Price Change Request Approval Comment','VARCHAR2(1000)','Y','','','반려면 필수(반려 사유), 승인이면 선택(조건부 승인 의견 등) (컬럼 검토 PC-72 A).'),
 ]),
 ('업로드 원본', [
  ('UPLOAD_FILE_URL','엑셀 업로드 원본 파일 경로','Upload Source File Path','VARCHAR2(500)','Y','','','엑셀로 올린 요청이면 원본 파일의 저장소 상대 경로. NULL이면 화면 입력 또는 시스템. 오입력 사고 때 원본 확인용 (컬럼 검토 PC-73 A). 상품 미디어(`PRD_STYLE_MEDIA.MEDIA_URL`)와 같은 파일 저장소에 두고 분류어도 맞췄다 (PC-84 A로 `UPLOAD_FILE_PATH_VAL`에서 이름 변경). 파일은 가격 이력처럼 지우지 않는다. 개인정보가 없어 파기 의무가 없고, 가격 이력 행이 어떻게 만들어졌는지 보여 주는 보조 증빙이다 (PC-85 A).'),
  ('UPLOAD_FILE_HASH','엑셀 업로드 원본 파일 해시','Upload Source File Hash','RAW(32)','Y','','','SHA-256. 파일 위변조 확인 (PC-73 A).'),
 ]),
 ('철회', [
  ('WITHDRAWN_AT','가격 변경 요청 전체 적용 전 철회 일시','Price Change Request Withdrawn Before Application At',TS,'Y','','','요청 전체를 거둬들인 사실. 아직 반영되지 않은 행만 철회되고, 각 행에 같은 철회 정보를 복사한다. 일부 행만 철회하면 이 컬럼은 바뀌지 않는다 (컬럼 검토 PC-57 D). “예약 취소”는 고객 예약 판매와 헷갈려 “적용 전 철회”로 바꿨다 (PC-57-1 A).'),
  ('WITHDRAWN_BY_ADMIN_ID','가격 변경 요청 전체 철회 관리자 식별 번호','Price Change Request Withdrawing Administrator Identifier',ID,'Y','',f'FK → {ADM}',''),
  ('PRICE_WITHDRAWAL_REASON_CD','가격 변경 요청 전체 철회 사유 코드','Price Change Request Withdrawal Reason Code','VARCHAR2(30)','Y','','CK (값 목록)','회원 탈퇴 사유(`WITHDRAWAL_REASON`)와 구분하려고 `PRICE_`를 붙였다.'),
  ('PRICE_WITHDRAWAL_REASON_CN','가격 변경 요청 전체 철회 상세 사유','Price Change Request Withdrawal Reason Detail','VARCHAR2(1000)','Y','','','사유 코드가 기타(`OTHER`)이면 필수.'),
 ]),
 ],
 check=['`APPROVAL_REQUIRED_YN = \'N\'` ⇔ `PRICE_CHANGE_APPROVAL_STATUS_CD = \'NOT_REQUIRED\'`',
        '상태가 `APPROVED`, `REJECTED`이면 `APPROVED_BY_ADMIN_ID`, `APPROVAL_DECIDED_AT` NOT NULL. `EXPIRED`이면 `APPROVED_BY_ADMIN_ID` NULL, `APPROVAL_DECIDED_AT` NOT NULL (배치 처리 시각). 그 밖에는 둘 다 NULL (PC-63 A)',
        '`PRICE_CHANGE_APPROVAL_STATUS_CD = \'REJECTED\'`이면 `APPROVAL_COMMENT_CN` NOT NULL (PC-72 A)',
        '`PRICE_CHANGE_REQUEST_STATUS_CD = \'REQUESTED\'` ⇔ `REQUESTED_AT` NOT NULL. 작성 중이면 `APPROVAL_REQUIRED_YN = \'N\'`, 결재 상태 `NOT_REQUIRED` (PC-69 A)',
        '요청 완료면 `MAX_REQUESTED_DISCOUNT_RT`, `OVER_LIMIT_STYLE_CNT`, `REQUEST_DEFAULT_MAX_DISCOUNT_RT` NOT NULL. `APPROVAL_REQUIRED_YN = \'Y\'` ⇔ `OVER_LIMIT_STYLE_CNT > 0` (작성 중 제외) (PC-70 A, PC-86 A)', '`OVER_LIMIT_STYLE_CNT <= TARGET_STYLE_CNT` (PC-86 A)',
        '`UPLOAD_FILE_URL`과 `UPLOAD_FILE_HASH`는 함께 NULL이거나 함께 NOT NULL (PC-73 A)',
        '`TARGET_STYLE_CNT <= TARGET_PRICE_ROW_CNT`. 요청 완료면 `TARGET_STYLE_CNT >= 1` (PC-83 A)',
        '`APPROVED_BY_ADMIN_ID <> REQUESTED_BY_ADMIN_ID` (자기 결재 금지)',
        '`WITHDRAWN_AT`과 `PRICE_WITHDRAWAL_REASON_CD`는 함께 NULL이거나 함께 NOT NULL. 철회되었으면 사유가 `APPROVAL_EXPIRED`일 때만 `WITHDRAWN_BY_ADMIN_ID` NULL, 그 밖에는 NOT NULL (PC-57-1 A, PC-63 A)', '`PRICE_WITHDRAWAL_REASON_CD = \'OTHER\'`이면 `PRICE_WITHDRAWAL_REASON_CN` NOT NULL'],
 idx=['UK `UK_PRD_PRICE_CHANGE_REQUEST_PRICE_CHANGE_REQUEST_NO`', 'IX `IX_PRD_PRICE_CHANGE_REQUEST_PRICE_CHANGE_APPROVAL_STATUS_CD` (결재 대기 목록)', 'IX `IX_PRD_PRICE_CHANGE_REQUEST_PRICE_CHANGE_REQUEST_STATUS_CD` (작성 중 목록)', 'IX `IX_PRD_PRICE_CHANGE_REQUEST_REQUESTED_BY_ADMIN_ID`, `IX_PRD_PRICE_CHANGE_REQUEST_APPROVED_BY_ADMIN_ID`, `IX_PRD_PRICE_CHANGE_REQUEST_WITHDRAWN_BY_ADMIN_ID` (FK)'])

table(t='PRD_PRICE_HIST', ko='상품 가격 이력 (정가·판매가·SKU 추가 금액, 예약 포함)', en='Product Price History (List, Sale and SKU Extra Price, Including Reservations)',
 desc='가격 원장. 정가 행, 판매가 행, SKU 추가 금액 행 세 종류를 `PRICE_ROW_TYPE_CD`로 나눠 담는다 (컬럼 검토 PC-47 A, PC-60 D·재확인 A). 시점 가격은 실제 반영 시각(`APPLIED_AT`~`ENDED_AT`) 기준이다 (PC-67 C). 정가와 판매가를 다른 행으로 둬서, 따로 잡은 예약이 예약 당시의 정가를 복사해 나중에 정가를 되돌리는 일이 없다. 미래 적용 시작 일시로 예약하고, 시작 시각에 스케줄러가 스타일(정가, 판매가, 할인율, 최저가, 다음 예약)·컬러·SKU 캐시를 갱신한다 (상품 결정 8 B, 32 B, 컬럼 검토 PC-65 A, PC-76 A, PC-82 A). 할인 전 가격 표시와 표시·광고 기록의 근거라 모든 시점의 가격이 행으로 남도록 기간 공백을 두지 않는다 (PC-49 A). 같은 스타일에서 같은 적용 시작인 행(정가, 판매가, 컬러, SKU 추가 금액, 복귀 행)은 한 트랜잭션에서 함께 반영하고, 스타일·컬러·SKU 캐시는 마지막에 한 번 갱신한다. 따로 반영하면 중간에 “판매가 ≤ 정가” CHECK에 걸린다 (컬럼 검토 PC-77 A). 스타일을 출시 전 취소하면 미반영 행은 철회(사유 `PLAN_CHANGED`, 취소한 관리자)하고 이미 반영된 행은 `ENDED_AT`을 취소 시각으로 채운다 (PC-78 A).',
 basis='8 B, 32 B, 44 B, 컬럼 검토 PC-47~PC-53', pk='대리 PK `SEQ_PRD_PRICE_HIST`', cache=20, delete='삭제하지 않음 (원장). 시작 전 예약은 취소 일시로 표시', part='없음', keep='삭제하지 않음 (컬럼 검토 PC-16 A)', ldel=False,
 cols=[
 ('식별', [
  ('PRICE_HIST_ID','가격 이력 고유 식별 번호','Price History Unique Identifier',ID,'N','','PK',''),
  fk('PRICE_CHANGE_REQUEST_ID','가격 변경 요청 식별 번호','Price Change Request Identifier','PRD_PRICE_CHANGE_REQUEST',extra='UK1',desc='이 행을 만든 요청. 단건이든 대량이든 모든 행은 요청 하나에 속한다 (PC-48 B, PC-55 재확인 A).'),
  fk('STYLE_ID','스타일 식별 번호','Style Identifier','PRD_STYLE',extra='UK1',desc='컬러 판매가 행과 SKU 추가 금액 행도 그 스타일을 넣는다 (건·스타일 단위 조회와 잠금용).'),
  fk('STYLE_COLOR_ID','스타일 컬러 식별 번호','Style Color Identifier','PRD_STYLE_COLOR',null='Y',extra='UK1',desc='판매가 행에서만 쓸 수 있다. NULL이면 스타일 전체 판매가, 값이 있으면 그 컬러만의 판매가로 스타일 판매가보다 우선한다. 컬러 판매가 행이 종료되면 스타일 전체 판매가로 돌아가므로 복귀 행이 필요 없다. 정가는 스타일 단위다 (컬럼 검토 PC-65 A). 스타일 전체 판매가를 바꿀 때 그 기간에 컬러 판매가 행이 있으면 저장 전에 목록을 보여 주고 MD가 컬러마다 “유지” 또는 “종료·철회”를 고른다. 실수로 한 컬러만 덜 할인되는 일을 막는다 (컬럼 검토 PC-68 A).'),
  fk('SKU_ID','SKU 식별 번호','SKU Identifier','PRD_SKU',null='Y',extra='UK1',desc='SKU 추가 금액 행에서만 채운다 (PC-47 A).'),
  ('PRICE_ROW_TYPE_CD','가격 이력 행 종류 코드','Price History Row Type Code','VARCHAR2(20)','N','','UK1, CK (값 목록)','정가 행, 판매가 행, SKU 추가 금액 행. 종류별 필수 금액은 CHECK로 나눈다. 기간 겹침·공백 검사도 종류별로 따로 한다 (PC-60 재확인 A).'),
 ]),
 ('가격·기간', [
  ('LIST_PRICE_AMT','적용 정가 (원화)','List Price at Application (KRW)',AMT,'Y','','CK (> 0, 10원 단위)','정가 행에서만 필수 (CHECK). 정가의 원천이고, 정가 변경도 이 행으로 예약한다 (PC-32 A). 할인 전 가격 증빙. 정가를 올릴 때 판매가도 함께 올리려면 같은 건에 판매가 행을 함께 만든다. 판매가 행이 없으면 오른 정가 대비 할인으로 표시되므로 저장 전에 애플리케이션이 알린다. 최초 등록(`INITIAL`)은 정가 행과 판매가 행을 함께 만든다 (PC-60 재확인 A).'),
  ('SALE_PRICE_AMT','판매가 (원화)','Sale Price Amount (KRW)',AMT,'Y','','CK (> 0, 10원 단위)','판매가 행에서만 필수 (CHECK). “판매가 ≤ 그 시점 정가”는 행이 달라 CHECK로 걸 수 없어 저장 때 애플리케이션이 검사한다. 정가를 내리는 예약을 저장할 때도 그 뒤 판매가 행이 새 정가보다 높으면 거부한다 (PC-5 A 변경, PC-60 재확인 A).'),
  ('EXTRA_PRICE_AMT','SKU 추가 금액 (원화)','SKU Extra Price Amount (KRW)',AMT,'Y','','CK (>= 0, 10원 단위)','SKU 추가 금액 행에서만 필수 (CHECK). 적용 시각에 `PRD_SKU.EXTRA_PRICE_AMT` 캐시를 갱신한다 (PC-47 A).'),
  ('APPLY_START_AT','적용 시작 일시','Apply Start At',TS,'N','','UK1','미래 값이면 예약.'),
  ('APPLY_END_AT','적용 종료 일시','Apply End At',TS,'Y','','','NULL이면 같은 종류의 다음 행까지. 판매가 행에만 넣을 수 있다 (정가 행은 기간 한정이 없다, CHECK). 값을 넣으면 그 시각부터 시작하는 판매가 복귀 행(사유 `RESTORE`)을 같은 저장에서 함께 만들고, 공백이 생기면 저장을 거부한다 (PC-49 A). 기간 겹침과 공백은 행 종류별로, 대상 단위(스타일 전체, 컬러, SKU)마다 스타일 행을 잠그고 검사한다. 컬러 판매가 행은 종료 뒤 스타일 전체 판매가로 돌아가므로 공백 검사 대상이 아니다 (PC-65 A) (인덱스로는 막을 수 없음, PC-60 재확인 A). 아직 끝나지 않은 판매가 행은 이 값만 바꿀 수 있다 (할인 연장·조기 종료, 컬러 예외 조기 종료). 원장 원칙의 유일한 예외이고, 처음 고지한 값은 `ORIGINAL_APPLY_END_AT`에, 변경 요청은 `APPLY_END_CHANGE_REQUEST_ID`에 남긴다. 변경은 새 가격 변경 요청으로 하고 한도를 넘으면 결재를 받는다 (PC-71 A). 복귀 행은 기존 것을 철회하고 새 종료 시각으로 같은 저장에서 다시 만든다 (PC-66 A).'),
  ('ORIGINAL_APPLY_END_AT','처음 고지한 적용 종료 일시','Originally Announced Apply End At',TS,'Y','','','종료 시각을 처음 바꿀 때 바꾸기 전 값을 복사한다. 여러 번 바꿔도 처음 값만 둔다 (중간 값은 데이터 변경 감사 로그). NULL이면 처음에는 종료 없이 고지했거나 바꾼 적이 없다. “12/7까지 고지 → 12/14로 연장” 같은 표시·광고 증빙 (PC-66 A).'),
  fk('APPLY_END_CHANGE_REQUEST_ID','종료 변경 근거 가격 변경 요청 식별 번호','Apply End Change Request Identifier','PRD_PRICE_CHANGE_REQUEST',null='Y',desc='마지막으로 종료 시각을 바꾼 요청. 변경 일시·요청자·결재는 그 요청에 있다. 그 요청이 만든 새 복귀 행도 같은 요청에 속한다. 결재가 필요한 종료 변경은 승인 뒤에 이 행에 반영한다 (컬럼 검토 PC-71 A, PC-66 A의 변경 일시·변경 관리자 컬럼을 대체).'),
  ('APPLY_END_CHANGED_AT','적용 종료 일시 변경 일시','Apply End Changed At',TS,'Y','','','종료 시각을 실제로 바꾼 시각 (결재가 필요하면 승인 뒤 반영한 시각). 여러 번 바꾸면 마지막 값. 변경 관리자는 근거 요청의 요청 관리자로 읽는다 (컬럼 검토 PC-71-1 A).'),
 ]),
 ('변경 정보', [
  ('PRICE_CHANGE_REASON_CD','가격 변경 사유 코드','Price Change Reason Code','VARCHAR2(30)','N','','CK (값 목록)','사유의 원천. 한 건 안에서도 행마다 다를 수 있다 (마크다운 건의 복귀 행 등). 사유에 걸린 CHECK 때문에 행에 둔다 (PC-54 A).'),
  ('MARKDOWN_ROUND_SN','마크다운 차수','Markdown Round Sequence Number','NUMBER(2)','N','0','CK (>= 0)','0 = 마크다운 아님, 1 = 1차, 2 = 2차. 이 변경의 사실로 기록하고 스타일에서는 현재 적용 행으로 읽는다. 원래 가격으로 되돌리면 0인 행이 된다 (PC-37 B).'),
  fk('CORRECTED_PRICE_HIST_ID','정정 대상 가격 이력 식별 번호','Corrected Price History Identifier','PRD_PRICE_HIST',null='Y',desc='사유가 오류 정정(`CORRECTION`)이면 잘못 입력된 행. 오입력 기간을 할인 전 가격 계산과 손실 집계에서 뺄 때 쓴다 (PC-51 B).'),
  fk('PREVIOUS_PRICE_HIST_ID','복귀 기준 가격 이력 식별 번호','Previous Price History Identifier','PRD_PRICE_HIST',null='Y',desc='사유가 이전 가격 복귀(`RESTORE`)이면 돌아가는 기준 행. “할인 직전 가격” 증빙 (PC-51 B).'),
 ]),
 ('반영·종료·철회', [
  ('APPLIED_AT','캐시 반영 일시','Cache Applied At',TS,'Y','','','스케줄러가 실제로 캐시에 반영한 시각. 적용 시작이 지났는데 NULL이고 철회되지 않았으며 작성 중·결재 대기가 아닌 요청의 행은 반영 실패로 감시한다 (PC-63 A, PC-69 A, 문구 PC-82 A). 실제 화면 반영 시각 증빙 (PC-50 A). 시점 가격은 예정 시각이 아니라 이 실제 반영 시각 기준이다 (PC-67).'),
  ('ENDED_AT','실제 종료 일시','Actually Ended At',TS,'Y','','','이 행이 실제로 끝난 시각. 같은 대상·같은 종류의 다음 행이 반영될 때 그 반영 시각으로 채운다. 컬러 판매가 행이 종료 시각에 이르러 스타일 전체 판매가로 돌아갈 때는 스케줄러가 그 시각에 채운다. NULL이면 아직 적용 중이거나 반영 전. 시점 가격 조회: `APPLIED_AT <= t AND (ENDED_AT IS NULL OR t < ENDED_AT)` (컬럼 검토 PC-67 C).'),
  ('WITHDRAWN_AT','적용 전 철회 일시','Withdrawn Before Application At',TS,'Y','','','관리자가 반영 전에 이 행을 거둬들인 시각 (입력 오류, 계획 변경, 할인 연장 때 복귀 행만 철회 등). 원장이라 지우지 않고 표시한다. 가격 변경 요청 전체 철회면 그 요청의 철회 정보를 복사한다 (PC-57 D, PC-57-1 A).'),
  ('WITHDRAWN_BY_ADMIN_ID','철회 관리자 식별 번호','Withdrawing Administrator Identifier',ID,'Y','',f'FK → {ADM}','시스템 수정자 컬럼은 다음 수정 때 덮어쓰이므로 원장에 따로 남긴다 (PC-52 A).'),
  ('PRICE_WITHDRAWAL_REASON_CD','철회 사유 코드','Withdrawal Reason Code','VARCHAR2(30)','Y','','CK (값 목록)',''),
  ('PRICE_WITHDRAWAL_REASON_CN','철회 상세 사유','Withdrawal Reason Detail','VARCHAR2(1000)','Y','','','사유 코드가 기타(`OTHER`)이면 필수.'),
  fk('SUPERSEDED_BY_PRICE_HIST_ID','대체한 가격 이력 식별 번호','Superseding Price History Identifier','PRD_PRICE_HIST',null='Y',desc='다른 요청과 기간이 겹쳐 “기존 예약 철회”를 골랐을 때, 이 행을 대체한 새 행. 저장 전에 겹치는 스타일 목록을 보여 주고 MD가 스타일마다 “이번 요청에서 제외” 또는 “기존 예약 철회”를 고른다. 겹침 검사에는 결재 대기 행도 포함한다 (PC-58 A).'),
 ]),
 ],
 check=['행 종류 (PC-47 A, PC-60 재확인 A): `LIST_PRICE`이면 `LIST_PRICE_AMT`만 NOT NULL이고 `SKU_ID`, `APPLY_END_AT` NULL. `SALE_PRICE`이면 `SALE_PRICE_AMT`만 NOT NULL이고 `SKU_ID` NULL. `STYLE_COLOR_ID`는 `SALE_PRICE` 행에서만 NOT NULL 가능 (PC-65 A). `SKU_EXTRA_PRICE`이면 `SKU_ID`, `EXTRA_PRICE_AMT`만 NOT NULL (나머지 금액 NULL)',
        '사유 `MARKDOWN`, `RESTORE`는 `SALE_PRICE` 행에만',
        '`APPLY_START_AT < APPLY_END_AT`. 판매가 ≤ 정가는 행이 달라 애플리케이션 검사 (PC-5 A 변경, PC-60 재확인 A)',
        '`MOD(LIST_PRICE_AMT, 10) = 0`, `MOD(SALE_PRICE_AMT, 10) = 0`, `MOD(EXTRA_PRICE_AMT, 10) = 0` (PC-39 A)',
        '`PRICE_CHANGE_REASON_CD = \'MARKDOWN\'`이면 `MARKDOWN_ROUND_SN >= 1` (PC-37 B)',
        '`PRICE_CHANGE_REASON_CD = \'CORRECTION\'` ⇔ `CORRECTED_PRICE_HIST_ID` NOT NULL, `PRICE_CHANGE_REASON_CD = \'RESTORE\'` ⇔ `PREVIOUS_PRICE_HIST_ID` NOT NULL (PC-51 B)',
        '`CORRECTED_PRICE_HIST_ID <> PRICE_HIST_ID`, `PREVIOUS_PRICE_HIST_ID <> PRICE_HIST_ID`',
        '`WITHDRAWN_AT`과 `PRICE_WITHDRAWAL_REASON_CD`는 함께 NULL이거나 함께 NOT NULL. 철회되었으면 사유가 `APPROVAL_EXPIRED`일 때만 `WITHDRAWN_BY_ADMIN_ID` NULL, 그 밖에는 NOT NULL (PC-52 A, PC-57-1 A, PC-63 A)',
        '`PRICE_WITHDRAWAL_REASON_CD = \'OTHER\'`이면 `PRICE_WITHDRAWAL_REASON_CN` NOT NULL',
        '`PRICE_WITHDRAWAL_REASON_CD = \'SUPERSEDED\'` ⇔ `SUPERSEDED_BY_PRICE_HIST_ID` NOT NULL, `SUPERSEDED_BY_PRICE_HIST_ID <> PRICE_HIST_ID` (PC-58 A)',
        '`APPLIED_AT`과 `WITHDRAWN_AT`은 동시에 NOT NULL일 수 없다 (반영된 행은 철회 불가)',
        '`ENDED_AT` NOT NULL이면 `APPLIED_AT` NOT NULL이고 `APPLIED_AT <= ENDED_AT` (PC-67 C)',
        '`APPLY_END_CHANGE_REQUEST_ID`와 `APPLY_END_CHANGED_AT`은 함께 NULL이거나 함께 NOT NULL (PC-71-1 A). `APPLY_END_CHANGE_REQUEST_ID` NOT NULL이면 `PRICE_ROW_TYPE_CD = \'SALE_PRICE\'`. `ORIGINAL_APPLY_END_AT` NOT NULL이면 `APPLY_END_CHANGE_REQUEST_ID` NOT NULL (처음에 종료 없이 고지했다가 종료를 정하면 처음 값이 NULL이라 한 방향만, PC-66 A, PC-71 A)'],
 idx=['UK `UK_PRD_PRICE_HIST_PRICE_CHANGE_REQUEST_ID_STYLE_ID_STYLE_COLOR_ID_SKU_ID_PRICE_ROW_TYPE_CD_APPLY_START_AT` (같은 건 안 중복 차단. 정가 행과 판매가 행이 같은 시각에 함께 생기므로 행 종류 포함 (PC-60 재확인 A). 같은 저장에서 만드는 복귀 행이 있어 적용 시작 일시를 포함, PC-53 A·PC-49 A)',
      'IX `IX_PRD_PRICE_HIST_APPLY_START_AT_APPLIED_AT` (스케줄러가 전체에서 반영할 행 조회, PC-53 A)',
      'IX `IX_PRD_PRICE_HIST_STYLE_ID_PRICE_ROW_TYPE_CD_APPLIED_AT_ENDED_AT` (시점 가격 조회, PC-67 C)', 'IX `IX_PRD_PRICE_HIST_APPLY_END_CHANGE_REQUEST_ID` (FK)',
      'IX `IX_PRD_PRICE_HIST_STYLE_ID_PRICE_ROW_TYPE_CD_APPLY_START_AT`, `IX_PRD_PRICE_HIST_STYLE_COLOR_ID_APPLY_START_AT`, `IX_PRD_PRICE_HIST_SKU_ID_APPLY_START_AT` (종류별 기간 조회·겹침 검사, “그 시점 정가·판매가” 조회)',
      'IX `IX_PRD_PRICE_HIST_CORRECTED_PRICE_HIST_ID`, `IX_PRD_PRICE_HIST_PREVIOUS_PRICE_HIST_ID`, `IX_PRD_PRICE_HIST_WITHDRAWN_BY_ADMIN_ID`, `IX_PRD_PRICE_HIST_SUPERSEDED_BY_PRICE_HIST_ID` (FK)'])

# =========================================================== 7. 관계·검색
table(t='PRD_STYLE_FUNCTIONAL_CLAIM', ko='스타일 기능성 표시와 실증자료', en='Style Functional Claim and Substantiation',
 desc='“방수”, “냉감”처럼 사실에 관한 기능성 표시와 그 실증자료(시험성적서). 표시광고법 5조(실증 책임, 요청 시 제출), 고시 (1) 의류 1번 “기능성인 경우 성적서 또는 허가서” (법률 검토 L18 C). 성적서 파일은 상세 화면에 게시한다.',
 basis='법률 검토 L18 C', pk='대리 PK `SEQ_PRD_STYLE_FUNCTIONAL_CLAIM`', cache=20, delete='논리 삭제 (설정). 표시를 내려도 실증 근거로 행을 남긴다', part='없음', keep='[확인 필요: 실증자료 보관 기간]', ldel=True,
 cols=[
 ('식별', [
  ('STYLE_FUNCTIONAL_CLAIM_ID','스타일 기능성 표시 고유 식별 번호','Style Functional Claim Unique Identifier',ID,'N','','PK',''),
  fk('STYLE_ID','스타일 식별 번호','Style Identifier','PRD_STYLE',extra='UK1'),
  ('FUNCTIONAL_CLAIM_CD','기능성 표시 유형 코드','Functional Claim Type Code','VARCHAR2(30)','N','','UK1, CK (값 목록)',''),
 ]),
 ('표시', [
  ('CLAIM_TEXT_CN','기능성 표시 문구','Functional Claim Text Content','VARCHAR2(500)','N','','','화면에 보이는 문구. 바꾸면 이전 문구는 표시 내용 이력에 남긴다 (상품 결정 44 B).'),
  sort_sn('기능성 표시', 'Functional Claim'),
 ]),
 ('실증자료', [
  ('TEST_REPORT_FILE_URL','시험성적서 파일 경로','Test Report File Path','VARCHAR2(500)','N','','','저장소 상대 경로. 고시 Ⅳ-2에 따라 문자로 읽을 수 있는 파일을 게시.'),
  ('TEST_AGENCY_NM','시험 기관 이름','Test Agency Name','VARCHAR2(200)','N','','','표시광고법 시행령 4조 (객관적 시험 방법).'),
  ('TEST_REPORT_NO','시험성적서 번호','Test Report Number','VARCHAR2(50)','Y','','',''),
  ('TEST_ISSUED_DT','시험성적서 발급 일자','Test Report Issued Date','DATE','N','','',''),
  ('TEST_TARGET_CD','시험 대상 구분 코드','Test Target Code','VARCHAR2(20)','N',"'FINISHED_GOODS'",'CK (값 목록)','완제품 시험인지 원단 시험인지.'),
 ]),
 ],
 idx=['UK `UK_PRD_STYLE_FUNCTIONAL_CLAIM_STYLE_ID_FUNCTIONAL_CLAIM_CD`'])

table(t='PRD_STYLE_RELATION', ko='스타일 연관 상품', en='Style Relation',
 desc='스타일 ↔ 스타일 관계 (코디, 셋업 짝, 대체, 후속). 관계 유형별 양방향 노출 규칙은 공통코드 `ATTR1` (상품 결정 14 B, 23 C).',
 basis='14 B, 23 C', pk='복합 PK (STYLE_ID, RELATED_STYLE_ID, RELATION_TYPE_CD)', cache='-', delete='물리 삭제 (단순 매핑)', part='없음', keep='-', ldel=False,
 cols=[
 ('식별', [
  fk('STYLE_ID','기준 스타일 식별 번호','Base Style Identifier','PRD_STYLE',extra='PK'),
  ('RELATED_STYLE_ID','연관 스타일 식별 번호','Related Style Identifier',ID,'N','','PK, FK → `PRD_STYLE`','역할 이름 FK (같은 테이블 두 번 참조).'),
  ('RELATION_TYPE_CD','연관 관계 유형 코드','Relation Type Code','VARCHAR2(20)','N','','PK, CK (값 목록)',''),
 ]),
 ('표시', [sort_sn('연관 상품', 'Related Style')]),
 ],
 check=['`STYLE_ID <> RELATED_STYLE_ID`'],
 idx=['IX `IX_PRD_STYLE_RELATION_RELATED_STYLE_ID` (역방향 조회)'])

table(t='PRD_SEARCH_INDEX_OUTBOX', ko='상품 검색 색인 아웃박스', en='Product Search Index Outbox',
 desc='상품 변경 이벤트를 쌓고 배치가 외부 검색 엔진에 반영한다 (상품 결정 37 D, 37-1 A). 승인 전 스타일의 물리 삭제도 이벤트로 남긴다. 태그는 스타일 행의 JSON이라 스타일 수정 이벤트로 반영된다 (M-7 C). 동의어는 검색 엔진이 직접 관리한다 (M-8 B).',
 basis='37 D, 37-1 A, 37-2 B(M-8로 변경)', pk='대리 PK `SEQ_PRD_SEARCH_INDEX_OUTBOX`', cache=100, delete='로그: 파티션 제거 (선행 결정 4)', part='`CREATED_AT` 월 단위 INTERVAL', keep='처리 완료 후 3개월 (컬럼 검토 PC-19 C)', ldel=False,
 cols=[
 ('식별', [
  ('SEARCH_INDEX_OUTBOX_ID','검색 색인 이벤트 고유 식별 번호','Search Index Outbox Unique Identifier',ID,'N','','PK',''),
  ('STYLE_ID','대상 스타일 식별 번호','Target Style Identifier',ID,'N','','','FK 없음: 물리 삭제된 스타일의 삭제 이벤트도 남겨야 한다.'),
  ('SEARCH_INDEX_EVENT_TYPE_CD','색인 이벤트 유형 코드','Search Index Event Type Code','VARCHAR2(10)','N','','CK (값 목록)',''),
 ]),
 ('처리', [
  ('OUTBOX_PROCESS_STATUS_CD','아웃박스 처리 상태 코드','Outbox Process Status Code','VARCHAR2(20)','N',"'PENDING'",'CK (값 목록)',''),
  ('RETRY_CNT','재시도 횟수','Retry Count','NUMBER(3)','N','0','CK (>= 0)',''),
  ('PROCESSED_AT','처리 완료 일시','Processed At',TS,'Y','','',''),
  ('LAST_ERROR_CN','마지막 오류 내용','Last Error Content','VARCHAR2(2000)','Y','','',''),
 ]),
 ],
 idx=['IX `IX_PRD_SEARCH_INDEX_OUTBOX_OUTBOX_PROCESS_STATUS_CD_CREATED_AT` (미처리 추출)'])

# =========================================================== 8. 표시 기록·집계
table(t='PRD_DISPLAY_CONTENT_HIST', ko='상품 표시 내용 버전 이력 (표시·광고 기록)', en='Product Display Content Version History',
 desc='전자상거래법 6조·시행령 6조의 표시·광고 기록 6개월 보존. 상세 문구, 고시, 철회 제한 고지, 대표 이미지 경로를 바꿀 때 이전 버전을 남긴다 (상품 결정 44 B). 공용 변경 로그에는 변경 사실만 남긴다 (16 B).',
 basis='44 B, 16 B', pk='대리 PK `SEQ_PRD_DISPLAY_CONTENT_HIST`', cache=20, delete='로그: 파티션 제거', part='`DISPLAY_END_AT` 월 단위 INTERVAL', keep='표시 종료 후 6개월', ldel=False,
 cols=[
 ('식별', [
  ('DISPLAY_CONTENT_HIST_ID','표시 내용 이력 고유 식별 번호','Display Content History Unique Identifier',ID,'N','','PK',''),
  fk('STYLE_ID','스타일 식별 번호','Style Identifier','PRD_STYLE',desc='컬럼 검토 PC-9 A. 승인 전 물리 삭제 스타일은 표시된 적이 없어 이력이 없으므로 FK와 충돌하지 않는다.'),
  ('STYLE_COLOR_ID','컬러 식별 번호','Style Color Identifier',ID,'Y','','','대표 이미지가 컬러별일 때.'),
  ('DISPLAY_CONTENT_TYPE_CD','표시 내용 유형 코드','Display Content Type Code','VARCHAR2(30)','N','','CK (값 목록)',''),
 ]),
 ('이전 버전', [
  ('CONTENT_JSON','이전 표시 내용','Previous Display Content JSON','JSON','N','','','유형별 구조. 이미지는 경로만.'),
  ('DISPLAY_START_AT','이 버전 표시 시작 일시','Display Start At',TS,'N','','',''),
  ('DISPLAY_END_AT','이 버전 표시 종료 일시','Display End At',TS,'N','','','파티션 키.'),
 ]),
 ],
 idx=['IX `IX_PRD_DISPLAY_CONTENT_HIST_STYLE_ID_DISPLAY_START_AT` (LOCAL)'])

table(t='PRD_SALES_DAILY_STAT', ko='SKU 일별 판매 집계', en='SKU Daily Sales Statistics',
 desc='주문 기반 SKU × 일자 집계. 랭킹과 스타일 판매 캐시, 리오더 사이즈 배분에 쓴다 (상품 결정 39 D, 39-1 A). Oracle 스케줄러가 채운다.',
 basis='39 D, 39-1 A', pk='복합 PK (SALES_DT, SKU_ID)', cache='-', delete='삭제하지 않음 (집계)', part='`SALES_DT` 월 단위 INTERVAL (조회 성능용)', keep='삭제하지 않음 (컬럼 검토 PC-18 C)', ldel=False,
 cols=[
 ('식별', [
  ('SALES_DT','판매 일자','Sales Date','DATE','N','','PK',''),
  fk('SKU_ID','SKU 식별 번호','SKU Identifier','PRD_SKU',extra='PK'),
  ('STYLE_ID','스타일 식별 번호 (중복 저장)','Style Identifier (Denormalized)',ID,'N','','','스타일 단위 집계용.'),
  ('STYLE_COLOR_ID','컬러 식별 번호 (중복 저장)','Style Color Identifier (Denormalized)',ID,'N','','',''),
 ]),
 ('수량·금액', [
  ('ORDER_QTY','주문 수량','Order Quantity','NUMBER(9)','N','0','CK (>= 0)',''),
  ('ORDER_AMT','주문 금액 (원화)','Order Amount (KRW)',AMT,'N','0','CK (>= 0)',''),
  ('CANCEL_QTY','취소 수량','Cancel Quantity','NUMBER(9)','N','0','CK (>= 0)',''),
  ('CANCEL_AMT','취소 금액 (원화)','Cancel Amount (KRW)',AMT,'N','0','CK (>= 0)',''),
  ('RETURN_QTY','반품 수량','Return Quantity','NUMBER(9)','N','0','CK (>= 0)',''),
  ('RETURN_AMT','반품 금액 (원화)','Return Amount (KRW)',AMT,'N','0','CK (>= 0)',''),
  ('AGGREGATED_AT','집계 일시','Aggregated At',TS,'N','','',''),
 ]),
 ],
 idx=['IX `IX_PRD_SALES_DAILY_STAT_STYLE_ID_SALES_DT` (LOCAL)'])

# =========================================================== 10. 회원 도메인 추가 예정
table(t='MBR_RESTOCK_NOTIFICATION_REQUEST', ko='회원 재입고 알림 신청 (SKU 단위)', en='Member Restock Notification Request (SKU Level)',
 desc='회원 × SKU 신청 (상품 결정 36 B, 36-1 `MBR`). 회원 소유 목록: 회원 취소, 단종, 휴면 전환(R-6 A), 탈퇴 확정 때 물리 삭제하고, 발송한 행은 발송 뒤 30일(R-1 B), 발송하지 않은 행은 신청 뒤 90일(R-3 B)이 지나면 매일 배치로 물리 삭제한다. 발송은 `MBR_MEMBER.RESTOCK_NOTIFICATION_YN` = Y인 회원에게만 하고, 수신이 꺼져 있어도 신청은 남긴다 (R-2 B). 입고 수량 × 5배까지 신청 순서대로 보내고 나머지는 다음 입고 때 이어서 보낸다 (R-5 B). 회원당 신청은 50개까지 (애플리케이션 검사, R-4 B). 일수·상한·배수는 공통코드 정책값이다 (R-9 B). 회원 도메인 문서(컬럼정의서, ERD, 정책명세)에 2026-11-24 반영했다. 사이즈 추천 결과 테이블은 두지 않는다 (컬럼 검토 M-13 B).',
 basis='상품 36 B, 36-1, 42 세부 B, 컬럼 검토 R-1~R-9', pk='복합 PK (MEMBER_ID, SKU_ID)', cache='-', delete='물리 삭제 (회원 소유 목록)', part='없음', keep='발송 뒤 30일, 미발송 신청은 신청 뒤 90일 (R-1 B, R-3 B)', ldel=False,
 cols=[
 ('식별', [
  fk('MEMBER_ID','신청 회원 식별 번호','Requesting Member Identifier','MBR_MEMBER',extra='PK'),
  fk('SKU_ID','신청 SKU 식별 번호','Requested SKU Identifier','PRD_SKU',extra='PK'),
 ]),
 ('신청·발송', [
  ('REQUESTED_AT','신청 일시','Requested At',TS,'N','','','발송 순서(R-5 B)와 유효 기간(R-3 B)의 기준. 발송 뒤 다시 신청하면 지금 시각으로 갱신한다 (R-8 A).'),
  ('NOTIFICATION_SENT_AT','알림 발송 일시','Notification Sent At',TS,'Y','','','NULL = 발송 대기. 발송 배치가 기록하고 30일 뒤 행을 지운다 (R-1 B). 같은 SKU를 다시 신청하면 NULL로 되돌린다 (R-8 A). 발송 기록 원본은 알림 도메인 통합 발송 이력.'),
 ]),
 ],
 idx=['IX `IX_MBR_RESTOCK_NOTIFICATION_REQUEST_SKU_ID_REQUESTED_AT` (입고 때 신청 순서대로 대상 추출, R-5 B)'])

TABLE_GROUPS = [  # 컬럼 검토 G-1 A (2026-11-24)
 ('상품 계층', ['PRD_STYLE', 'PRD_STYLE_COLOR', 'PRD_SKU']),
 ('상품 상세 정보', ['PRD_STYLE_MEDIA', 'PRD_STYLE_FABRIC', 'PRD_STYLE_FUNCTIONAL_CLAIM']),
 ('가격', ['PRD_PRICE_HIST', 'PRD_PRICE_CHANGE_REQUEST']),
 ('연관·검색', ['PRD_STYLE_RELATION', 'PRD_SEARCH_INDEX_OUTBOX']),
 ('표시 기록·집계', ['PRD_DISPLAY_CONTENT_HIST', 'PRD_SALES_DAILY_STAT']),
 ('기준 정보', ['PRD_CATEGORY', 'PRD_BRAND', 'PRD_SEASON', 'PRD_COLOR', 'PRD_FABRIC']),
 ('회원 도메인 추가 예정 (상품 결정 36)', ['MBR_RESTOCK_NOTIFICATION_REQUEST']),
]

# ---------------------------------------------------------------- 코드 값 (CHECK + CMM_CODE)
# 컬럼 이름 → [(코드, 한글, 영문, 설명, 정렬)]. 회원 도메인 그룹을 그대로 쓰는 것은 REUSE에 적는다.
def vals(*xs):
    return [(c, k, e, d, i) for i, (c, k, e, d) in enumerate(xs, 1)]

LEVEL3 = lambda a, b, c: vals(*a)
CODES = {
 'SEASON_TYPE_CD': vals(('SS','봄여름','Spring/Summer',''),('FW','가을겨울','Fall/Winter','')),
 'ITEM_NOTICE_GROUP_CD': vals(('CLOTHING','의류','Clothing','고시 품목 1'),('SHOES','구두·신발','Shoes',''),('BAG','가방','Bag',''),('FASHION_ACCESSORY','패션잡화 (모자, 벨트, 액세서리)','Fashion Accessory','')),
 'SIZE_SYSTEM_CD': vals(('TOP_SIZE','상의 알파벳 사이즈','Top Alpha Size','회원 그룹 `TOP_SIZE` 값 사용'),('BOTTOM_SIZE','하의 알파벳 사이즈','Bottom Alpha Size','회원 그룹 `BOTTOM_SIZE`'),('WAIST_SIZE','허리 인치 사이즈','Waist Inch Size','회원 그룹 `WAIST_SIZE`'),('SHOE_SIZE','신발 mm 사이즈','Shoe Millimeter Size','회원 그룹 `SHOE_SIZE`'),('FREE_SIZE','프리 사이즈','Free Size','새 그룹 `FREE_SIZE` (값 `FREE`, 상품 결정 47 A)')),
 'COLOR_FAMILY_CD': vals(('BLACK','블랙 계열','Black',''),('WHITE','화이트 계열','White',''),('GRAY','그레이 계열','Gray',''),('BEIGE','베이지 계열','Beige',''),('BROWN','브라운 계열','Brown',''),('NAVY','네이비 계열','Navy',''),('BLUE','블루 계열','Blue',''),('GREEN','그린 계열','Green',''),('KHAKI','카키 계열','Khaki',''),('RED','레드 계열','Red',''),('PINK','핑크 계열','Pink',''),('PURPLE','퍼플 계열','Purple',''),('YELLOW','옐로 계열','Yellow',''),('ORANGE','오렌지 계열','Orange',''),('MULTI','멀티','Multi','패턴·배색'),('NONE','컬러 없음','None','가상 컬러 `NONE` 행 전용 (상품 결정 47 A)')),
 'THICKNESS_CD': vals(('THIN','얇음','Thin',''),('MEDIUM','보통','Medium',''),('THICK','두꺼움','Thick','')),
 'STRETCH_CD': vals(('NONE','신축성 없음','None',''),('LOW','약간 있음','Low',''),('HIGH','좋음','High','')),
 'FIBER_CD': vals(('COTTON','면','Cotton',''),('LINEN','마 (린넨)','Linen',''),('WOOL','울','Wool',''),('CASHMERE','캐시미어','Cashmere',''),('SILK','실크','Silk',''),('POLYESTER','폴리에스터','Polyester',''),('NYLON','나일론','Nylon',''),('ACRYLIC','아크릴','Acrylic',''),('RAYON','레이온','Rayon',''),('POLYURETHANE','폴리우레탄 (스판덱스)','Polyurethane',''),('LEATHER','천연 가죽','Leather',''),('DOWN','솜털','Down','충전재'),('FEATHER','깃털','Feather','충전재'),('OTHER','기타 섬유','Other','[확인 필요]')),
 'FUNCTIONAL_CLAIM_CD': vals(('WATERPROOF','방수','Waterproof',''),('WATER_REPELLENT','발수','Water Repellent',''),('WINDPROOF','방풍','Windproof',''),('COOLING','냉감','Cooling',''),('HEAT_RETENTION','보온·발열','Heat Retention',''),('MOISTURE_WICKING','흡습속건','Moisture Wicking',''),('UV_PROTECTION','자외선 차단','UV Protection',''),('ANTIBACTERIAL','항균·방취','Antibacterial',''),('OTHER','기타 기능성','Other','표시 문구로 구체화')),
 'TEST_TARGET_CD': vals(('FINISHED_GOODS','완제품','Finished Goods',''),('FABRIC','원단','Fabric','')),
 'STYLE_OPERATION_TYPE_CD': vals(('CORE','상시','Core','시즌을 넘어 계속 판매. 시즌마다 캐리오버 새 스타일 (상품 결정 23 C)'),('SEASONAL','시즌','Seasonal','한 시즌 판매'),('LIMITED','한정','Limited','수량·기간 한정'),('COLLABORATION','협업','Collaboration','다른 브랜드·작가와 협업')),
 'PRICE_CHANGE_APPROVAL_STATUS_CD': vals(('NOT_REQUIRED','결재 불필요','Not Required','한도 안의 변경. 바로 예약 효력'),('PENDING','결재 대기','Pending','스케줄러가 반영하지 않음'),('APPROVED','승인','Approved',''),('REJECTED','반려','Rejected','미반영 행 모두 철회 (PC-63 A)'),('EXPIRED','결재 기한 경과','Expired','결재 대기 중 적용 시작이 지남. 배치가 처리 (PC-63 A)')),
 'PRICE_WITHDRAWAL_REASON_CD': vals(('INPUT_ERROR','입력 오류','Input Error','적용 전에 오입력 발견'),('PLAN_CHANGED','계획 변경','Plan Changed',''),('DISCOUNT_EXTENDED','할인 연장','Discount Extended','복귀 행만 철회'),('SUPERSEDED','다른 변경으로 대체','Superseded','`SUPERSEDED_BY_PRICE_HIST_ID` 필수 (PC-58 A)'),('APPROVAL_REJECTED','결재 반려','Approval Rejected','가격 변경 요청 반려 때 자동 (PC-63 A)'),('APPROVAL_EXPIRED','결재 기한 경과','Approval Expired','배치 처리, 철회 관리자 NULL (PC-63 A)'),('OTHER','기타','Other','상세 사유 필수')),
 'PRICE_ROW_TYPE_CD': vals(('LIST_PRICE','정가 행','List Price Row','`LIST_PRICE_AMT`만, 종료 일시 없음'),('SALE_PRICE','판매가 행','Sale Price Row','`SALE_PRICE_AMT`만. 마크다운·복귀는 이 행'),('SKU_EXTRA_PRICE','SKU 추가 금액 행','SKU Extra Price Row','`SKU_ID`, `EXTRA_PRICE_AMT`만')),
 'PRICE_CHANGE_REQUEST_STATUS_CD': vals(('DRAFT','작성 중','Draft','가격 행은 반영·겹침 검사·캐시에서 제외'),('REQUESTED','요청 완료','Requested','겹침 검사·결재 필요 여부 계산 완료. 결재 상태로 다음 단계 판단')),
 'TAXATION_TYPE_CD': vals(('TAXABLE','과세','Taxable','의류·잡화'),('TAX_EXEMPT','면세','Tax Exempt','면세 상품이 생길 때')),
 'TARGET_GENDER_CD': vals(('MALE','남성','Male',''),('FEMALE','여성','Female',''),('UNISEX','공용','Unisex','')),
 'STYLE_STAGE_CD': vals(('PLANNING','기획','Planning','품번 발번'),('PRODUCTION','생산','Production','생산 발주 이후'),('SALES_REGISTRATION','판매 등록','Sales Registration','판매 등록 작업 시작. 판매 화면 조회 대상 (PC-26 A)'),('DROPPED','출시 전 취소','Dropped Before Launch','기획·생산, 또는 최초 승인 전의 판매 등록에서 갈 수 있는 종료 값 (PC-24 A, PC-62 A)')),
 'REGISTRATION_STATUS_CD': vals(('DRAFT','작성 중','Draft',''),('INSPECTION_REQUESTED','검수 요청','Inspection Requested',''),('REJECTED','반려','Rejected',''),('APPROVED','승인','Approved','최초 승인 뒤에만 판매 중으로 바꿀 수 있다'),('MODIFICATION_REQUESTED','수정 검수 요청','Modification Requested','최초 승인 뒤 수정 검수 중. 기존 승인 내용으로 계속 판매 (PC-25 A)')),
 'DISCONTINUATION_REASON_CD': vals(('SEASON_END','시즌 종료','Season End',''),('LOW_SALES','판매 부진','Low Sales',''),('QUALITY_ISSUE','품질 문제','Quality Issue',''),('MATERIAL_UNAVAILABLE','원부자재 단종','Material Unavailable',''),('REPLACED','후속 상품 대체','Replaced by Successor','연관 상품 `SUCCESSOR` 필수 (애플리케이션)')),
 'PRE_LAUNCH_DROP_REASON_CD': vals(('COST_OVER','원가 초과','Cost Over',''),('SAMPLE_REJECTED','샘플 불합격','Sample Rejected',''),('FACTORY_UNAVAILABLE','공장 확보 실패','Factory Unavailable',''),('PLAN_CHANGED','기획 변경','Plan Changed','')),
 'SALE_STATUS_CD': vals(('READY','판매 준비','Ready',''),('ON_SALE','판매 중','On Sale','품절은 재고에서 계산'),('SUSPENDED','판매 중지','Suspended',''),('DISCONTINUED','단종','Discontinued','재입고 알림 신청·위시리스트 물리 삭제 (상품 결정 42)')),
 'PURCHASE_TARGET_CD': vals(('ALL','전체','All','비회원 포함'),('MEMBER','회원 전용','Member Only',''),('EMPLOYEE','임직원 전용','Employee Only','회원 C-39 임직원 자격'),('GRADE_OR_ABOVE','등급 이상 전용','Grade or Above','`MIN_PURCHASE_GRADE_CD` 필수')),
 'WITHDRAWAL_RESTRICTION_CD': vals(('NONE','제한 없음','None',''),('VALUE_DECREASE_BY_USE','사용·착용으로 가치 감소','Value Decrease by Use','전자상거래법 17조 2항 2호 (속옷·수영복 등)')),
 'DELIVERY_TYPE_CD': vals(('NORMAL','일반 배송','Normal',''),('SEPARATE','단독 배송','Separate','묶음 배송 불가')),
 'BOX_SIZE_CD': vals(('SMALL','소','Small','[확인 필요: 택배사 규격]'),('MEDIUM','중','Medium',''),('LARGE','대','Large',''),('EXTRA_LARGE','특대','Extra Large','')),
 'SHEERNESS_CD': vals(('NONE','비침 없음','None',''),('SLIGHT','약간 비침','Slight',''),('HIGH','비침 있음','High','')),
 'LINING_CD': vals(('NONE','안감 없음','None',''),('PARTIAL','부분 안감','Partial',''),('FULL','전체 안감','Full','')),
 'FABRIC_PART_CD': vals(('SHELL','겉감','Shell',''),('LINING','안감','Lining',''),('FILLING','충전재','Filling',''),('TRIM','배색·부속','Trim','')),
 'CARE_SYMBOL_CD': vals(('WASH_30','물세탁 30도','Wash 30',''),('WASH_40','물세탁 40도','Wash 40',''),('HAND_WASH','손세탁','Hand Wash',''),('DO_NOT_WASH','물세탁 불가','Do Not Wash',''),('BLEACH_ALLOWED','표백 가능','Bleach Allowed',''),('DO_NOT_BLEACH','표백 불가','Do Not Bleach',''),('TUMBLE_DRY_LOW','기계 건조 저온','Tumble Dry Low',''),('DO_NOT_TUMBLE_DRY','기계 건조 불가','Do Not Tumble Dry',''),('LINE_DRY','옷걸이 건조','Line Dry',''),('FLAT_DRY','뉘어서 건조','Flat Dry',''),('IRON_LOW','다림질 저온','Iron Low',''),('IRON_MEDIUM','다림질 중온','Iron Medium',''),('DO_NOT_IRON','다림질 불가','Do Not Iron',''),('DRY_CLEAN','드라이클리닝','Dry Clean',''),('DO_NOT_DRY_CLEAN','드라이클리닝 불가','Do Not Dry Clean','전체 목록은 KS K ISO 3758에서 확정 [확인 필요]')),
 'CERTIFICATION_TYPE_CD': vals(('SAFETY_CERTIFICATION','안전인증','Safety Certification',''),('SAFETY_CONFIRMATION','안전확인','Safety Confirmation',''),('SUPPLIER_CONFORMITY','공급자적합성확인','Supplier Conformity','')),
 'MEASUREMENT_PART_CD': vals(('TOTAL_LENGTH','총장','Total Length',''),('SHOULDER_WIDTH','어깨너비','Shoulder Width',''),('CHEST_WIDTH','가슴단면','Chest Width',''),('SLEEVE_LENGTH','소매길이','Sleeve Length',''),('WAIST_WIDTH','허리단면','Waist Width',''),('HIP_WIDTH','엉덩이단면','Hip Width',''),('THIGH_WIDTH','허벅지단면','Thigh Width',''),('RISE','밑위','Rise',''),('HEM_WIDTH','밑단단면','Hem Width',''),('FOOT_LENGTH','발길이','Foot Length','신발'),('HEEL_HEIGHT','굽 높이','Heel Height','신발')),
 'MEDIA_TYPE_CD': vals(('THUMBNAIL','썸네일','Thumbnail',''),('MAIN','메인','Main',''),('WEARING','착용','Wearing',''),('DETAIL','상세','Detail','이미지형 상세 (상품 결정 12 C)'),('FABRIC_CLOSEUP','소재 확대','Fabric Close-up',''),('VIDEO','영상','Video','')),
 'PRICE_CHANGE_REASON_CD': vals(('INITIAL','최초 등록','Initial',''),('MARKDOWN','마크다운','Markdown','시즌오프 등'),('PRICE_INCREASE','가격 인상','Price Increase','정가·판매가'),('LIST_PRICE_DECREASE','정가 인하','List Price Decrease','정가 행. 할인(마크다운)과 구분 (PC-60 재확인 A)'),('RESTORE','이전 가격 복귀','Restore',''),('CORRECTION','오류 정정','Correction','')),
 'RELATION_TYPE_CD': vals(('COORDINATION','코디 추천','Coordination',''),('SETUP_PAIR','셋업 짝','Setup Pair','양방향'),('SUBSTITUTE','품절 시 대체','Substitute',''),('SUCCESSOR','후속 상품','Successor','캐리오버 연결 (상품 결정 23 C)')),
 'SEARCH_INDEX_EVENT_TYPE_CD': vals(('UPSERT','등록·수정','Upsert',''),('DELETE','삭제','Delete','')),
 'OUTBOX_PROCESS_STATUS_CD': vals(('PENDING','대기','Pending',''),('COMPLETED','완료','Completed',''),('FAILED','실패','Failed','재시도 대상')),
 'DISPLAY_CONTENT_TYPE_CD': vals(('DETAIL_TEXT','상세 문구','Detail Text',''),('ITEM_NOTICE','상품정보제공고시','Item Notice',''),('WITHDRAWAL_NOTICE','청약철회 제한 고지','Withdrawal Notice',''),('MAIN_IMAGE','대표 이미지','Main Image','경로만'),('SHIPMENT_SCHEDULE','출고 예정일 고지','Shipment Schedule Notice','컬러별 예약 판매 출고 예정일 (PC-42 B)')),
}
# 회원 도메인 공통코드 그룹을 그대로 쓰는 컬럼 (값 행은 회원 그룹 ID로 표시)
REUSE = {'FIT_CD': 'FIT'}
# 새 그룹 이름 (컬럼 → CMM_CODE_GROUP 코드). 지정이 없으면 컬럼 이름에서 `_CD`를 뺀 이름.
GROUP_NAME = {'THICKNESS_CD': 'THICKNESS', 'STRETCH_CD': 'STRETCH', 'SALE_STATUS_CD': 'PRODUCT_SALE_STATUS'}
NEW_GROUPS_EXTRA = [('FREE_SIZE', '프리 사이즈', 'Free Size', '사이즈 체계 `FREE_SIZE`의 값 (상품 결정 47 A)', vals(('FREE','프리','Free','')))]

# 확정 표시 (2026-11-24 사용자 지시). 그룹 단위: (테이블, 컬럼 그룹), 테이블 전체: 테이블 이름 (컬럼, 코드 값, 인덱스·제약, 테이블 이름 행 모두 ☑)
CONFIRMED_GROUPS = {('PRD_STYLE', '식별·분류'), ('PRD_STYLE', '단계·상태'), ('PRD_STYLE', '가격')}
CONFIRMED_TABLES = {'PRD_PRICE_CHANGE_REQUEST', 'PRD_PRICE_HIST'}

CONFIRM = [
 ('테이블 이름', '18개 모두 후보. 회원 도메인처럼 이름 결정 질문을 거쳐 확정한다.', '전체'),
 ('컬럼 검토 질문', '착용 계절감, 모델 신체 수치, 품번 약어 단계, 보관 기간 등은 `상품_컬럼검토_결정.pdf`의 PC 질문으로 정한다.', 'PC 질문'),
 ('`SYS_STATUS_HIST` 사유 컬럼', '검수 반려 사유를 상태 이력에만 남기기로 해서(M-5 C) 상태 이력에 사유 컬럼이 필요하다. SYS 도메인에서 설계한다.', '`SYS_STATUS_HIST`'),
 ('비판매 품목', '사은품·포장재·부자재는 재고·창고(WMS) 도메인에서 설계한다 (M-12 C). 재고가 SKU와 비판매 품목을 함께 참조하는 방식도 그때 정한다.', 'WMS 도메인'),
 ('제조연월 원천', '`EARLIEST_STOCK_MANUFACTURED_YM`은 재고 입고 차수별 제조연월에서 계산한다 (L15 B). 재고·창고 도메인에서 입고 차수에 제조연월을 받아야 한다.', 'WMS 도메인'),
 ('실증자료 보관 기간', '기능성 표시를 내린 뒤 실증자료 행을 얼마나 보관할지 (L18 C).', '`PRD_STYLE_FUNCTIONAL_CLAIM`'),
 ('판매 중지 사유', '판매 중지 사유는 `SYS_STATUS_HIST`의 사유 컬럼에 둔다 (PC-29 B). 값 후보: 품질, 가격 오류, 표시 정보 오류, 법적 문제(리콜 포함), 재고, 기타. 코드 그룹은 SYS 도메인에서 사유 컬럼과 함께 정한다.', '`SYS_STATUS_HIST`'),
 ('예약 판매 한도', '예약 가능 수량은 재고 도메인에서 SKU별로 “입고 예정 수량 − 예약 주문 수량”으로 계산한다 (PC-41 C).', 'INV·SCM 도메인'),
 ('예약 판매 출고 지연', '주문별 약속 출고일 스냅샷, 지연 통지 일시, 15조 2항의 3영업일 환급 기한 계산은 주문 도메인에서 정한다 (PC-42 B).', '주문 도메인'),
 ('발매 알림 신청', '발매 전 공개 상품의 알림 신청 테이블(재입고 알림 신청과 같은 방식)은 회원 도메인에서 정한다 (PC-43 A).', '회원 도메인'),
 ('수정 검수 반려 기록', '수정 검수가 반려되면 검수 상태가 승인으로 돌아가 상태 이력에 “수정 검수 요청 → 승인”으로 찍힌다. 승인된 수정과 구분하려면 `SYS_STATUS_HIST`에 결과 구분(승인·반려)을 두거나 반려를 두 단계로 기록해야 한다 (2026-11-24 외부 검토).', '`SYS_STATUS_HIST`'),
 ('가격 행 동시 반영', '같은 스타일·같은 적용 시작의 가격 행을 한 트랜잭션에서 반영하고 캐시를 마지막에 한 번 갱신하는 배치 구현 (PC-77 A).', '배치 도메인 (`BAT`), `PRD_PRICE_HIST`'),
 ('JSON 코드 검사', '혼용률, 세탁 기호, 실측 JSON 안의 코드 값은 애플리케이션이 검사한다 (M-1·M-2·M-4).', '`COMPOSITION_JSON`, `CARE_SYMBOL_JSON`, `SIZE_MEASUREMENT_JSON`'),
 ('회원 도메인 반영', '`MBR_RESTOCK_NOTIFICATION_REQUEST`는 2026-11-24 회원 컬럼정의서·ERD·정책명세에 반영했다. 이 문서의 정의는 참고용이고 기준은 회원 컬럼정의서다. 테이블 이름은 후보.', '`MBR_RESTOCK_NOTIFICATION_REQUEST`'),
]

# 회원 도메인 그룹 값 (재사용). 코드 ID는 회원 code_ids.json에서 읽는다.
REUSE_VALS = {
 'FIT': vals(('TOP_SLIM','상의 슬림','Top Slim','ATTR1 부위 TOP'),('TOP_REGULAR','상의 레귤러','Top Regular',''),('TOP_OVERSIZED','상의 오버','Top Oversized',''),
             ('BOTTOM_SLIM','하의 슬림','Bottom Slim','ATTR1 부위 BOTTOM'),('BOTTOM_REGULAR','하의 레귤러','Bottom Regular',''),('BOTTOM_WIDE','하의 와이드','Bottom Wide','')),
}
for _c, _g in REUSE.items():
    CODES[_c] = REUSE_VALS[_g]
# 그룹별 추가 속성 (ATTR 의미, {코드: [값...]}) — 모두 제안
ATTRS = {
 'SIZE_SYSTEM_CD': (['값 공통코드 그룹'], {c: [c] for c in ['TOP_SIZE','BOTTOM_SIZE','WAIST_SIZE','SHOE_SIZE','FREE_SIZE']}),
 'RELATION_TYPE_CD': (['양방향 노출 여부'], {'COORDINATION': ['N'], 'SETUP_PAIR': ['Y'], 'SUBSTITUTE': ['N'], 'SUCCESSOR': ['N']}),
 'MEASUREMENT_PART_CD': (['쓰는 사이즈 체계'], {'TOTAL_LENGTH': ['TOP_SIZE,BOTTOM_SIZE,WAIST_SIZE'], 'SHOULDER_WIDTH': ['TOP_SIZE'], 'CHEST_WIDTH': ['TOP_SIZE'], 'SLEEVE_LENGTH': ['TOP_SIZE'],
     'WAIST_WIDTH': ['BOTTOM_SIZE,WAIST_SIZE'], 'HIP_WIDTH': ['BOTTOM_SIZE,WAIST_SIZE'], 'THIGH_WIDTH': ['BOTTOM_SIZE,WAIST_SIZE'], 'RISE': ['BOTTOM_SIZE,WAIST_SIZE'], 'HEM_WIDTH': ['BOTTOM_SIZE,WAIST_SIZE'],
     'FOOT_LENGTH': ['SHOE_SIZE'], 'HEEL_HEIGHT': ['SHOE_SIZE']}),
}

# JSON 안에 들어가는 코드 값 (CHECK 없음, 애플리케이션 검사). JSON 컬럼 → 코드 키
JSON_CODES = {'COMPOSITION_JSON': 'FIBER_CD', 'CARE_SYMBOL_JSON': 'CARE_SYMBOL_CD', 'SIZE_MEASUREMENT_JSON': 'MEASUREMENT_PART_CD'}
# 파일로 적재하는 공통코드 그룹 (값을 문서에 나열하지 않음). 컬럼 → (그룹 코드, 한글, 영문, 예상 값 수, 소유 도메인)
# 컬럼 없는 정책값 그룹 (그룹 코드, 한글, 영문, 쓰는 곳, ATTR 의미, 값)
POLICY_GROUPS = [('PRODUCT_POLICY', '상품 정책 기준값', 'Product Policy Threshold', '애플리케이션 판단 로직 (컬럼 없음)', ['기준값', '단위'],
  [('MAX_DISCOUNT_RATE_DEFAULT', '기본 최대 할인율', 'Default Maximum Discount Rate', '`PRD_STYLE.MAX_DISCOUNT_RT`가 NULL일 때. 넘는 변경은 결재 대상 (PC-35 A, PC-48 재확인 A)', ['[확인 필요: 값]', '%'])])]
FILE_CODES = {'MANUFACTURING_COUNTRY_JSON': ('COUNTRY', '국가 (ISO 3166-1 alpha-2)', 'Country (ISO 3166-1 alpha-2)', 250, 'CMM')}
