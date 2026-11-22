import sys, os, re, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import T, CODES, CONFIRM, TS
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
from order import TABLE_GROUPS, COL_GROUPS
_by = {t['t']: t for t in T}
_order = [n for g, ns in TABLE_GROUPS for n in ns]
assert sorted(_order) == sorted(_by), set(_by) ^ set(_order)
TGRP = {n: g for g, ns in TABLE_GROUPS for n in ns}
GNO = {g: k for k, (g, ns) in enumerate(TABLE_GROUPS, 1)}
GFIRST = {ns[0] for g, ns in TABLE_GROUPS}
for t in T:
    cm = {c[0]: c for c in t['cols']}
    names = [n for g, ns in COL_GROUPS[t['t']] for n in ns]
    assert sorted(names) == sorted(cm), (t['t'], set(cm) ^ set(names))
    t['grp_of'] = {n: g for g, ns in COL_GROUPS[t['t']] for n in ns}
    t['cols'] = [cm[n] for n in names]
T[:] = [_by[n] for n in _order]
CODE_MAP = {}
CODE_KEY = {}
for key, vals in CODES.items():
    k = key.split(' (')[0]
    cols = [c.strip() for c in k.split('/')]
    hit = 0
    for t in T:
        for c in t['cols']:
            if c[0] in cols:
                CODE_MAP[(t['t'], c[0])] = vals; CODE_KEY[(t['t'], c[0])] = key; hit += 1
    assert hit, key
_missing = [(t['t'], c[0]) for t in T for c in t['cols'] if '값 목록' in c[6] and (t['t'], c[0]) not in CODE_MAP]
print('CK 값 목록인데 값 없음:', _missing)
print('값 목록 매핑 컬럼 수:', len(CODE_MAP), '/ 코드 그룹 수:', len(CODES))


CSS = """
@page { size: A4 landscape; margin: 12mm 10mm; }
body { font-family: 'Apple SD Gothic Neo', sans-serif; font-size: 8.4pt; color:#222; line-height:1.4; }
h1 { font-size: 16pt; margin:0 0 4px; border-bottom: 3px solid #1f4e79; padding-bottom:6px; color:#1f4e79; }
.meta { color:#666; font-size:8pt; margin-bottom:10px; }
h2 { font-size: 12pt; margin:14px 0 4px; color:#1f4e79; page-break-after: avoid; }
h2.t { page-break-before: always; }
h3 { font-size: 10pt; margin:10px 0 4px; page-break-after: avoid; }
table { border-collapse: collapse; width:100%; margin:3px 0 8px; }
tr { page-break-inside: avoid; }
th, td { border:1px solid #bbb; padding:2px 4px; vertical-align:top; text-align:left; }
th { background:#eef2f7; font-weight:600; }
td.n { text-align:center; color:#666; white-space:nowrap; }
td.p { font-family: Menlo, monospace; font-size:7.6pt; overflow-wrap:anywhere; }
.en { color:#555; } .ok { color:#1a7f37; font-weight:600; } td.ck.on { color:#1a7f37; }
td.ty { font-family: Menlo, monospace; font-size:7.6pt; white-space:nowrap; }
td.ck { text-align:center; width:26px; font-size:11pt; color:#888; }
td.memo { width:90px; }
tr.sys td { background:#f6f6f6; color:#555; }
h2.g { font-size:14pt; color:#fff; background:#1f4e79; padding:4px 8px; margin:16px 0 6px; page-break-after: avoid; }
h2.g.pb { page-break-before: always; }
tr.cv td { background:#eaf2fa; font-size:7.8pt; border-top:1px dashed #b9cde3; border-bottom:1px dashed #b9cde3; }
tr.cv td:first-child { border-left:4px solid #3d6fa8; }
tr.cv.first td { border-top:1px solid #3d6fa8; }
tr.cv.last td { border-bottom:2px solid #3d6fa8; }
tr.cv td.p { padding-left:14px; }
.rel { margin-top:4px; border:1px solid #c5d6ea; border-left:4px solid #3d6fa8; background:#fff; border-radius:2px; padding:3px 6px 3px 7px; }
.rel .rh { font-size:7.4pt; font-weight:700; color:#3d6fa8; letter-spacing:0.5px; margin-bottom:1px; }
.rel ul { margin:0; padding-left:12px; } .rel li { margin:0; font-size:7.8pt; color:#333; }
tr.grp td { background:#dde7f3; font-weight:700; color:#1f4e79; }
tr.cf td { background:#fff6e0; }
.info td:first-child { width:110px; background:#f3f6fa; font-weight:600; }
code { font-family: Menlo, monospace; font-size:7.6pt; background:#f1f1f1; padding:0 2px; }
.box { border:1px solid #c9d6e6; background:#f6f9fc; padding:6px 10px; margin:6px 0; }
.warn { color:#b03a00; font-weight:600; }
"""

def il(s):
    s = html.escape(str(s)); p = s.split('`')
    s = ''.join(f'<code>{x}</code>' if i % 2 else x for i, x in enumerate(p))
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\s*\[확정 [^\]]*\]', '', s)
    return re.sub(r'\[(확인 필요[^\]]*|제안: 결정 항목 아님)\]', r'<span class="warn">[\1]</span>', s)

BOX = '☐'
# CMM_CODE 가상 CODE_ID (공통코드 PDF와 같은 값): 값 목록이 같은 코드 그룹을 찾아 연결
import json as _json
_IDS = _json.load(open(os.path.join(OUT, 'code_ids.json'), encoding='utf-8'))  # cmm/cmm.py가 먼저 만든다
def _code_id(vals, code):
    keys = [v[0] for v in vals]
    for g in _IDS.values():
        if list(g['codes']) == keys:
            return f'<span class="ty">CODE_ID {g["codes"][code]}</span>'
    raise KeyError(keys)
def ln(ko, en):
    return f'{il(ko)}<br><span class="en">({il(en)})</span>'
def pn(p):
    return html.escape(p).replace('_', '_<wbr>')
def page(title, body):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>'

SYS = [
 ('CREATED_BY_TYPE_CD','생성 행위자 유형 코드','Created By Actor Type Code','VARCHAR2(20)','N','','CK (행위자 유형 6개)','MEMBER, ADMIN, SYSTEM, BATCH, EXTERNAL, GUEST (선행 결정 8).'),
 ('CREATED_BY','생성 행위자 식별자','Created By Actor Identifier','VARCHAR2(100)','N','','','유형에 따른 회원 ID, 관리자 ID, 업체 코드, 비회원 주문번호 등.'),
 ('CREATED_AT','행 생성 일시','Created At',TS,'N','SYSTIMESTAMP','',''),
 ('UPDATED_BY_TYPE_CD','최종 수정 행위자 유형 코드','Updated By Actor Type Code','VARCHAR2(20)','Y','','CK (행위자 유형 6개)','수정 전에는 NULL (규칙 1).'),
 ('UPDATED_BY','최종 수정 행위자 식별자','Updated By Actor Identifier','VARCHAR2(100)','Y','','','수정 전에는 NULL (규칙 1).'),
 ('UPDATED_AT','행 최종 수정 일시','Updated At',TS,'Y','','','수정 전에는 NULL (규칙 1).'),
]
DEL = [
 ('DELETED_BY_TYPE_CD','삭제 행위자 유형 코드','Deleted By Actor Type Code','VARCHAR2(20)','Y','','CK (행위자 유형 6개)','논리 삭제 테이블만 (선행 결정 4).'),
 ('DELETED_BY','삭제 행위자 식별자','Deleted By Actor Identifier','VARCHAR2(100)','Y','','',''),
 ('DELETED_AT','논리 삭제 일시','Deleted At',TS,'Y','','','NULL이면 삭제되지 않은 행. 조회 시 `DELETED_AT IS NULL`.'),
]
PII = [
 ('PII_RETENTION_REASON_CD','개인정보 보유 사유 코드','Personal Information Retention Reason Code','VARCHAR2(30)','Y','','','`CMM_CODE` 보유 기간 코드 (선행 결정 7).'),
 ('PII_RETENTION_BASE_DT','개인정보 보유 기간 기산 일자','Personal Information Retention Base Date','DATE','Y','','','탈퇴 확정일 등. 이름은 후보.'),
 ('PII_RETENTION_END_DT','개인정보 파기 예정 일자','Personal Information Retention End Date','DATE','Y','','','지나면 일 배치가 파기 (선행 결정 7, 11-3).'),
 ('PII_PURGED_AT','개인정보 파기 완료 일시','Personal Information Purged At',TS,'Y','','',''),
]

def full_cols(t):
    c = [(x, 'b') for x in t['cols']]
    if t['pii']: c += [(x, 's') for x in PII]
    c += [(x, 's') for x in SYS]
    if t['ldel']: c += [(x, 's') for x in DEL]
    return c

# ---------------- 1. 테이블 이름 PDF
rows = ''
NHEAD = '<table style="table-layout:fixed"><colgroup><col style="width:3%"><col style="width:20%"><col style="width:20%"><col style="width:35%"><col style="width:4%"><col style="width:3.5%"><col style="width:3.5%"><col style="width:11%"></colgroup><tr><th>No</th><th>물리명 (확정)</th><th>논리명 (제안)</th><th>설명 (제안)</th><th>컬럼 수</th><th>확정</th><th>수정</th><th>메모</th></tr>'
for i, t in enumerate(T, 1):
    if t['t'] in GFIRST:
        g = TGRP[t['t']]
        rows += ('</table>' if i > 1 else '') + f'<h2 class="g">{GNO[g]}. {g}</h2>' + NHEAD
    rows += (f'<tr><td class="n">{i}</td><td class="p">{pn(t["t"])}</td><td>{ln(t["ko"], t["en"])}</td>'
             f'<td>{il(t["desc"])}</td><td class="n">{len(full_cols(t))}</td><td class="ck">{BOX}</td><td class="ck">{BOX}</td><td class="memo"></td></tr>')
total = sum(len(full_cols(t)) for t in T)
body = ('<h1>회원 도메인 테이블 이름 (확정)</h1>'
        '<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-22 (법률 검토 반영) · 물리명은 B-1~B-14 결정으로 확정 · 논리명과 설명은 제안 (확인 칸으로 검토)</div>'
        '<div class="box">물리명 20개는 확정했다. 논리명(한글, 아래 괄호에 영문)과 설명은 이 문서에서 처음 제안하는 것이라 아직 후보다. '
        '오른쪽 칸에 <b>확정</b> 또는 <b>수정</b>을 표시하고, 수정할 내용은 메모 칸에 적는다.</div>'
        + rows + f'</table><p><b>합계: 테이블 20개, 컬럼 {total}개</b></p>')
B = [('B-1','로그인 계정','A','MBR_LOGIN_ACCOUNT'),('B-2','배송지','B','MBR_DELIVERY_ADDRESS'),('B-3','위시리스트','B','MBR_WISHLIST_ITEM'),
     ('B-4','최근 본 상품','B','MBR_RECENTLY_VIEWED_ITEM'),('B-5','저장 결제수단','B','MBR_SAVED_PAYMENT_METHOD'),('B-6','제재','A','MBR_SANCTION'),
     ('B-7','외부 광고 전송 이력','C (재확인 C)','MBR_ADVERTISING_PLATFORM_SHARE_HIST'),('B-8','회원-태그 매핑','A','MBR_MEMBER_TAG'),
     ('B-9','임직원 할인 한도','B','MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT'),('B-10','등급 이력','B','MBR_MEMBER_GRADE_CHANGE_HIST'),
     ('B-11','계정 병합 이력','B','MBR_ACCOUNT_MERGE_HIST'),('B-12','동의 이력','A','MBR_CONSENT_HIST'),('B-13','본인인증 로그','A','MBR_IDENTITY_VERIFICATION_LOG'),
     ('B-14','나머지 7개','A (제안대로)','MBR_MEMBER, MBR_REFRESH_TOKEN, MBR_DEVICE, MBR_GRADE, MBR_TAG, MBR_PREFERENCE, MBR_PROFILE_IMAGE')]
body += '<h2>이름 결정 기록</h2><table><tr><th>질문</th><th>대상</th><th>선택</th><th>확정 이름</th></tr>' + ''.join(
    f'<tr><td>{a}</td><td>{b}</td><td>{c}</td><td class="p">{d}</td></tr>' for a, b, c, d in B) + '</table>'
body += ('<h2>공통 사항</h2><ul><li>모든 이름은 128바이트 이내. 가장 긴 것은 <code>MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT</code>(34바이트), <code>MBR_ADVERTISING_PLATFORM_SHARE_HIST</code>(35바이트).</li>'
         '<li>시퀀스는 <code>SEQ_{테이블}</code>. 복합 PK인 <code>MBR_MEMBER_TAG</code>, <code>MBR_WISHLIST_ITEM</code>, <code>MBR_RECENTLY_VIEWED_ITEM</code>은 시퀀스 없음.</li>'
         '<li>표 순서는 지시 규칙 8: 테이블을 관련 그룹으로 모으고, 그룹은 업무 흐름 순, 그룹 안은 중요도 순 (그룹 구성은 제안). DDL 생성 순서는 FK 순서로 따로 정한다 (8-D).</li><li>B-7 C는 PK 컬럼 이름에 약어 <code>AD</code>가 들어가 재확인했고, 풀어 쓴 C로 확정.</li></ul>')
open(os.path.join(OUT, 'names.html'), 'w').write(page('회원 도메인 테이블 이름', body))

# ---------------- 2. 컬럼 정의 PDF
NOTE = ('<div class="box"><b>검토 방법</b><br>'
        '· 모든 컬럼은 <b>제안</b>이다. 컬럼마다 <b>확정</b> 또는 <b>수정</b> 칸에 표시하고, 수정 내용은 메모 칸에 적는다.<br>'
        '· 노란 행: 결정 항목에 없던 제안 컬럼이거나 확인이 필요한 컬럼 (설명에 빨간 표시).<br>'
        '· 회색 행: 공통 컬럼 (시스템 6개, 논리 삭제 3개, 개인정보 보유 4개). 선행 결정으로 정해져 있다.<br>'
        '· NULL 칸: N = NOT NULL, Y = NULL 허용. 파기 대상 개인정보 컬럼은 선행 결정 7에 따라 NULL 허용.<br>'
        '· 코드 컬럼은 바로 아래 └ 행에 값 목록(코드, 논리명, 정렬, 설명)을 둔다. 번호는 컬럼 번호 뒤에 붙는다 (예: 1-3-1). 코드 컬럼에는 코드 문자열을 저장한다 (사용자 결정 A, 2026-11-21).<br>'
        '· 정렬은 지시 규칙 8을 따른다: 테이블·컬럼을 관련 그룹으로 모으고 (테이블 그룹은 남색 제목, 컬럼 그룹은 표 안의 파란 줄), 그룹은 업무 흐름 순, 그룹 안은 중요도 순이다. PK는 첫 컬럼, 공통 컬럼은 끝. 그룹 구성과 순서도 제안이다.</div>')
toc = '<h2>목차</h2>'
THEAD = '<table style="table-layout:fixed"><colgroup><col style="width:5%"><col style="width:33%"><col style="width:38%"><col style="width:8%"><col style="width:8%"><col style="width:8%"></colgroup><tr><th>No</th><th>테이블</th><th>논리명</th><th>업무 컬럼</th><th>공통 컬럼</th><th>합계</th></tr>'
# 상태값별 관련 정보 위치 (회원 계정 상태)
_NUM = {}
for _i, _t in enumerate(T, 1):
    for _k, ((_p, *_), _kind) in enumerate(full_cols(_t), 1):
        _NUM[(_t['t'], _p)] = f'{_i}-{_k}'
_TNO = {_t['t']: _i for _i, _t in enumerate(T, 1)}
def _ref(tb, c): return f'`{c}` ({_NUM[(tb, c)]})'
_M = 'MBR_MEMBER'
import related as _rel
_rel.check(set(_NUM), CODES)
def _fmt(tb, c, cur):
    return f'`{c}` ({_NUM[(tb, c)]})' if tb == cur else f'`{tb}.{c}` ({_NUM[(tb, c)]})'
def _related(tb, col, code):
    xs = _rel.items(CODE_KEY.get((tb, col)), code, lambda t2, c2: _fmt(t2, c2, tb))
    if not xs: return ''
    return '<div class="rel"><div class="rh">관련 정보</div><ul>' + ''.join(f'<li>{il(x)}</li>' for x in xs) + '</ul></div>'
secs = ''
tot_b = tot_s = 0
for i, t in enumerate(T, 1):
    fc = full_cols(t); nb = len(t['cols']); ns = len(fc) - nb; tot_b += nb; tot_s += ns
    if t['t'] in GFIRST:
        g = TGRP[t['t']]
        toc += ('</table>' if i > 1 else '') + f'<h3>{GNO[g]}. {g}</h3>' + THEAD
        secs += f'<h2 class="g pb">{GNO[g]}. {g}</h2>'
    toc += f'<tr><td class="n">{i}</td><td class="p">{t["t"]}</td><td>{ln(t["ko"], t["en"])}</td><td class="n">{nb}</td><td class="n">{ns}</td><td class="n">{nb+ns}</td></tr>'
    secs += f'<h2{"" if t["t"] in GFIRST else " class=t"}>{i}. {t["t"]}</h2>'
    secs += '<table class="info">' + f'<tr><td>논리명</td><td>{ln(t["ko"], t["en"])}</td></tr>' + ''.join(f'<tr><td>{a}</td><td>{il(b)}</td></tr>' for a, b in [
        ('설명', t['desc']), ('근거 결정', t['basis']),
        ('PK·시퀀스', f"{t['pk']} · CACHE {t['cache']}"), ('삭제 방식', t['delete']), ('파티션', t['part']), ('보유 기간', t['keep'])]) + '</table>'
    secs += ('<table style="table-layout:fixed"><colgroup><col style="width:4%"><col style="width:19%"><col style="width:15%"><col style="width:8.5%"><col style="width:3.5%"><col style="width:7%"><col style="width:9%"><col style="width:23%"><col style="width:3%"><col style="width:3%"><col style="width:5%"></colgroup>'
             '<tr><th>No</th><th>물리명</th><th>논리명</th><th>타입</th><th>NULL</th><th>기본값</th><th>제약</th><th>설명</th>'
             '<th>확정</th><th>수정</th><th>메모</th></tr>')
    prev = None
    for k, ((p, ko, en, ty, nl, df, ck, ds), kind) in enumerate(fc, 1):
        g = t['grp_of'].get(p, '공통 컬럼 (규칙 1, 8-A: 개인정보 보유 → 시스템 → 논리 삭제)') if kind == 'b' else '공통 컬럼 (규칙 1, 8-A: 개인정보 보유 → 시스템 → 논리 삭제)'
        if g != prev:
            secs += f'<tr class="grp"><td colspan="11">{il(g)}</td></tr>'; prev = g
        if (t['t'], p) in CODE_MAP: ds = (ds + ' ' if ds else '') + '값 목록은 아래 행.'
        cls = ' class="sys"' if kind == 's' else (' class="cf"' if re.search(r'\[(확인 필요|제안: 결정)', ds + ck + en) or '[확인' in ck else '')
        secs += (f'<tr{cls}><td class="n">{i}-{k}</td><td class="p">{pn(p)}</td><td>{ln(ko, en)}</td><td class="ty">{il(ty)}</td>'
                 f'<td class="n">{nl}</td><td class="ty">{il(df)}</td><td>{il(ck)}</td><td>{il(ds)}</td>' + (f'<td class="ck on">☑</td>' if '[확정' in ds else f'<td class="ck">{BOX}</td>') + f'<td class="ck">{BOX}</td><td class="memo"></td></tr>')
        for vi, v in enumerate(CODE_MAP.get((t['t'], p), []), 1):
            _vals = CODE_MAP.get((t['t'], p), [])
            _c = 'cv' + (' first' if vi == 1 else '') + (' last' if vi == len(_vals) else '')
            secs += (f'<tr class="{_c}"><td class="n">{i}-{k}-{vi}</td><td class="p">└ {pn(v[0])}</td><td>{ln(v[1], v[2])}</td>'
                     f'<td colspan="5">정렬 {v[4]}' + (f' · {il(v[3])}' if v[3] else '') + _related(t['t'], p, v[0]) + '</td>' + ('<td class="ck on">☑</td>' if '[확정' in v[3] else f'<td class="ck">{BOX}</td>') + f'<td class="ck">{BOX}</td><td class="memo">{_code_id(_vals, v[0])}</td></tr>')
    secs += '</table>'
    if t['idx'] or t['check']:
        secs += '<h3>인덱스·제약 (제안)</h3><table><tr><th>No</th><th>내용</th><th>확정</th><th>수정</th><th>메모</th></tr>'
        for k, x in enumerate(t['idx'] + [f'CK (테이블 수준): {c}' for c in t['check']], 1):
            secs += f'<tr><td class="n">{i}-X{k}</td><td>{il(x)}</td><td class="ck">{BOX}</td><td class="ck">{BOX}</td><td class="memo"></td></tr>'
        secs += '</table>'
toc += f'</table><p><b>합계: 업무 컬럼 {tot_b} + 공통 컬럼 {tot_s} = {tot_b+tot_s}개</b></p>'

conf = '<h2 class="t">확인이 필요한 사항 (결정 필요)</h2><table><tr><th>No</th><th>항목</th><th>내용</th><th>대상</th><th>확정</th><th>수정</th><th>메모</th></tr>'
for k, (a, b, c) in enumerate(CONFIRM, 1):
    conf += f'<tr class="cf"><td class="n">Q{k}</td><td>{il(a)}</td><td>{il(b)}</td><td>{il(c)}</td><td class="ck">{BOX}</td><td class="ck">{BOX}</td><td class="memo"></td></tr>'
conf += '</table>'

codes = '<h2 class="t">코드 값 목록 (제안)</h2><p>CHECK 제약을 거는 코드와 <code>CMM_CODE</code>에 담을 값. 정렬은 표시 순서.</p>'
for k, (col, vals) in enumerate(CODES.items(), 1):
    codes += f'<h3>C{k}. {il(col)}</h3><table><tr><th>코드</th><th>한글명</th><th>영문명</th><th>설명</th><th>정렬</th><th>확정</th><th>수정</th><th>메모</th></tr>'
    for v in vals:
        codes += f'<tr><td class="p">{v[0]}</td><td>{il(v[1])}</td><td>{il(v[2])}</td><td>{il(v[3])}</td><td class="n">{v[4]}</td><td class="ck">{BOX}</td><td class="ck">{BOX}</td><td class="memo"></td></tr>'
    codes += '</table>'

body = ('<h1>회원 도메인 컬럼 정의서 (제안)</h1>'
        f'<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-22 (법률 검토 L1~L6 반영) · 테이블 20개 · 컬럼 {tot_b+tot_s}개 (업무 {tot_b} + 공통 {tot_s}) · 테이블 이름은 확정, 컬럼은 모두 제안</div>'
        + NOTE + toc + conf + secs)
open(os.path.join(OUT, 'columns.html'), 'w').write(page('회원 도메인 컬럼 정의서', body))
print(tot_b, tot_s, tot_b + tot_s)
