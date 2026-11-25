# 주문 도메인 테이블 이름·컬럼 정의서 HTML. 공통코드 CODE_ID는 아직 매기지 않는다.
# 사용: python3 render.py <출력폴더>
import sys, os, re, html, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import T, CODES, CONFIRM, TS, TABLE_GROUPS, REUSE, CONFIRMED_GROUPS, CONFIRMED_TABLES
JSON_CODES = {}
OUT = sys.argv[1]
_by = {t['t']: t for t in T}
_order = [n for g, ns in TABLE_GROUPS for n in ns]
assert sorted(_order) == sorted(_by), set(_by) ^ set(_order)
T[:] = [_by[n] for n in _order]
TGRP = {n: g for g, ns in TABLE_GROUPS for n in ns}
GNO = {g: k for k, (g, ns) in enumerate(TABLE_GROUPS, 1)}
GFIRST = {ns[0] for g, ns in TABLE_GROUPS}
for t in T:
    t['grp_of'] = {c[0]: g for g, cs in t['cols'] for c in cs}
    t['cols'] = [c for g, cs in t['cols'] for c in cs]
    assert len({c[0] for c in t['cols']}) == len(t['cols']), t['t']
    for c in t['cols']:
        assert len(c) == 8, (t['t'], c[0])
        assert len(c[0].encode()) <= 128
missing = [(t['t'], c[0]) for t in T for c in t['cols'] if '값 목록' in c[6] and c[0] not in CODES]
assert not missing, missing
def code_id(col, code): return ''

CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css'), encoding='utf-8').read()
def il(s):
    s = html.escape(str(s)); p = s.split('`')
    s = ''.join(f'<code>{x}</code>' if i % 2 else x for i, x in enumerate(p))
    return re.sub(r'\[(확인 필요[^\]]*)\]', r'<span class="warn">[\1]</span>', s)
def ln1(ko, en): return f'{il(ko)} <span class="en" style="display:inline-block">({il(en)})</span>'
def pn(p): return html.escape(p).replace('_', '_<wbr>')
def page(title, body): return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>'
BOX = '☐'
ON = '☑'
def ckcell(on): return f'<td class="ck on">{ON}</td>' if on else f'<td class="ck">{BOX}</td>'
for _t, _g in CONFIRMED_GROUPS: assert any(t['t'] == _t and _g in t['grp_of'].values() for t in T), (_t, _g)
assert CONFIRMED_TABLES <= {t['t'] for t in T}
SYS = [
 ('CREATED_BY_TYPE_CD','생성 행위자 유형 코드','Created By Actor Type Code','VARCHAR2(20)','N','','CK (행위자 유형 6개)','MEMBER, ADMIN, SYSTEM, BATCH, EXTERNAL, GUEST (선행 결정 8).'),
 ('CREATED_BY','생성 행위자 식별자','Created By Actor Identifier','VARCHAR2(100)','N','','','유형에 따른 회원 ID, 관리자 ID, 업체 코드 등.'),
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
 ('PII_RETENTION_REASON_CD','개인정보 보유 사유 코드','Personal Information Retention Reason Code','VARCHAR2(30)','Y','','CK (값 목록)','`CMM_CODE` 보유 기간 코드 (선행 결정 7).'),
 ('PII_RETENTION_BASE_DT','개인정보 보유 기간 기산 일자','Personal Information Retention Base Date','DATE','Y','','','거래 종료일 (주문 상품이 모두 끝 상태이고 진행 중 클레임이 없는 날). 결제 만료 주문은 만료일. 확정 뒤 클레임이 들어오면 비웠다가 다시 채운다 (10-9 B). 이름은 후보.'),
 ('PII_RETENTION_END_DT','개인정보 파기 예정 일자','Personal Information Retention End Date','DATE','Y','','','기산일 + 5년. 미성년 주문은 max(기산일 + 5년, min(성년 도달일 + 3년, 주문일 + 10년)) (10-2 A). 지나면 일 배치가 개인정보 컬럼만 NULL (10-1 A).'),
 ('PII_PURGED_AT','개인정보 파기 완료 일시','Personal Information Purged At',TS,'Y','','',''),
]
def full_cols(t):
    return [(x, 'b') for x in t['cols']] + ([(x, 's') for x in PII] if t['pii'] else []) + [(x, 's') for x in SYS] + ([(x, 's') for x in DEL] if t['ldel'] else [])
CMN = '공통 컬럼 (규칙 1, 8-A: 개인정보 보유 → 시스템 → 논리 삭제)'
# ---------------- 1. 테이블 이름 (후보)
rows = ''
NHEAD = '<table style="table-layout:fixed"><colgroup><col style="width:3%"><col style="width:20%"><col style="width:22%"><col style="width:36.5%"><col style="width:4%"><col style="width:3.5%"><col style="width:11%"></colgroup><tr><th>No</th><th>물리명 (후보)</th><th>논리명 (제안)</th><th>설명 (제안)</th><th>컬럼 수</th><th>확정</th><th>메모</th></tr>'
for i, t in enumerate(T, 1):
    if t['t'] in GFIRST:
        g = TGRP[t['t']]
        rows += ('</table>' if i > 1 else '') + f'<h2 class="g">{GNO[g]}. {g}</h2>' + NHEAD
    rows += (f'<tr><td class="n">{i}</td><td class="p">{pn(t["t"])}</td><td>{ln1(t["ko"], t["en"])}</td>'
             f'<td>{il(t["desc"])}<br><span class="en">근거: 주문 결정 {il(t["basis"])}</span></td><td class="n">{len(full_cols(t))}</td>' + ckcell(t['t'] in CONFIRMED_TABLES) + '<td class="memo"></td></tr>')
total = sum(len(full_cols(t)) for t in T)
longest = sorted(T, key=lambda t: -len(t['t']))[:2]
body = ('<h1>주문 도메인 테이블 이름 (검토용)</h1>'
        '<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-25 · 주문 도메인 결정 1-1~10-11, 컬럼 검토 OC-10·OC-15·OC-16~OC-116 기준 · 물리명, 논리명, 설명 모두 후보 (확인 칸으로 검토)</div>'
        f'<div class="box">주문 도메인 결정 1-1~10-11과 컬럼 검토에서 나온 테이블 {len(T)}개다 (모두 <code>ORD_</code>). 물리명도 아직 확정하지 않았다. 확정한 행은 <b>확정</b> 칸에 표시하고, 고칠 이름이나 내용은 메모 칸에 적는다.</div>'
        + rows + f'</table><p><b>합계: 테이블 {len(T)}개, 컬럼 {total}개 (공통 컬럼 포함)</b></p>')
body += ('<h2>공통 사항</h2><ul>'
         f'<li>모든 이름은 128바이트 이내. 가장 긴 것은 ' + ', '.join(f'<code>{t["t"]}</code>({len(t["t"])}바이트)' for t in longest) + '.</li>'
         '<li>시퀀스는 <code>SEQ_{테이블}</code>. <code>ORD_ORDER_ATTRIBUTION</code>은 주문 ID 공유 PK라 시퀀스 없음 (10-4 A).</li>'
         '<li>고빈도 시퀀스(CACHE 100): 장바구니, 주문, 주문 상품, 할인 배분, 상태 이력, 비회원 주문 조회 실패 로그(공격 때 몰림). 주문 사은품, 주문 변경 이력, 주문 관리자 메모는 CACHE 20 (10-4 A, 컬럼 검토 OC-16·OC-17).</li>'
         '<li>2026-11-25 컬럼 검토로 7개에서 9개가 되었다: 주문 변경 이력(OC-16 A, 5-5 A의 "이전 값은 감사 로그"를 바꿈), 주문 관리자 메모(OC-17 A). 같은 날 비회원 주문 조회 실패 로그(OC-87 B)를 더해 10개가 되었다. 한 주문을 여러 배송지로 보내는 기능은 운영하지 않는다 (OC-24 A).</li>'
         '<li>주문은 주문 일시 월 단위 INTERVAL 파티션, 자식 테이블은 참조 파티션. 장바구니는 파티션 없음 (10-3 A).</li>'
         '<li>주문 유입 정보(1:1)는 규칙 5 예외가 필요하다 (3-6 B, 결정 단계에서 예외 목록에 추가).</li>'
         '<li>영업일 달력(1-8 A)은 주문 도메인 테이블이 아니어서 넣지 않았다. 소속(<code>SYS</code> / <code>CMM</code>)은 결정 단계에서 정한다.</li>'
         '<li>주문 상태 이력은 두지 않고 주문 상품 상태 이력만 둔다 (7-3 C). 상태가 아닌 값(배송지, 보류, 선물, 회원 연결, 옵션)의 변경은 주문 변경 이력에 남긴다.</li>'
         '<li>표 순서는 지시 규칙 8: 테이블을 관련 그룹으로 모으고, 그룹은 업무 흐름 순, 그룹 안은 중요도 순 (그룹 구성은 제안). DDL 생성 순서는 FK 순서로 따로 정한다 (8-D).</li></ul>')
open(os.path.join(OUT, 'names.html'), 'w').write(page('주문 도메인 테이블 이름', body))

# ---------------- 2. 컬럼 정의서
NOTE = ('<div class="box"><b>검토 방법</b><br>'
        '· 테이블 이름과 모든 컬럼은 <b>제안</b>이다. 확정한 컬럼은 <b>확정</b> 칸에 표시하고, 고칠 내용은 메모 칸에 적는다. 공통코드 <code>CODE_ID</code>는 아직 매기지 않았다.<br>'
        '· 노란 행: 확인이 필요한 컬럼 (설명에 빨간 표시). 결정 단계에서 정할 사항은 <code>주문_컬럼검토_결정.pdf</code>의 OC 질문에 있다.<br>'
        '· 회색 행: 공통 컬럼 (개인정보 보유 4개, 시스템 6개). 선행 결정으로 정해져 있다. 주문 도메인 테이블은 논리 삭제 테이블이 없다.<br>'
        '· NULL 칸: N = NOT NULL, Y = NULL 허용. 파기 대상 개인정보 컬럼은 NULL 허용이고 필수 여부는 애플리케이션이 검증한다 (선행 7).<br>'
        '· 코드 컬럼은 바로 아래 └ 행에 값 목록을 둔다. 코드 컬럼에는 코드 문자열을 저장한다.<br>'
        '· 정렬은 지시 규칙 8 (테이블 그룹은 남색 제목, 컬럼 그룹은 초록 줄). PK는 첫 컬럼, 공통 컬럼은 끝. 그룹 구성과 순서도 제안이다.</div>')
toc = '<h2>목차</h2>'
THEAD = '<table style="table-layout:fixed"><colgroup><col style="width:5%"><col style="width:33%"><col style="width:38%"><col style="width:8%"><col style="width:8%"><col style="width:8%"></colgroup><tr><th>No</th><th>테이블</th><th>논리명</th><th>업무 컬럼</th><th>공통 컬럼</th><th>합계</th></tr>'
secs = ''; tot_b = tot_s = 0
for i, t in enumerate(T, 1):
    fc = full_cols(t); nb = len(t['cols']); ns = len(fc) - nb; tot_b += nb; tot_s += ns
    if t['t'] in GFIRST:
        g = TGRP[t['t']]
        toc += ('</table>' if i > 1 else '') + f'<h3>{GNO[g]}. {g}</h3>' + THEAD
        secs += f'<h2 class="g pb">{GNO[g]}. {g}</h2>'
    toc += f'<tr><td class="n">{i}</td><td class="p">{t["t"]}</td><td>{ln1(t["ko"], t["en"])}</td><td class="n">{nb}</td><td class="n">{ns}</td><td class="n">{nb+ns}</td></tr>'
    secs += f'<h2{"" if t["t"] in GFIRST else " class=t"}>{i}. {t["t"]}</h2>'
    secs += '<table class="info">' + f'<tr><td>논리명</td><td>{ln1(t["ko"], t["en"])}</td></tr>' + ''.join(f'<tr><td>{a}</td><td>{il(b)}</td></tr>' for a, b in [
        ('설명', t['desc']), ('근거 결정', '주문 결정 ' + t['basis']),
        ('PK·시퀀스', f"{t['pk']} · CACHE {t['cache']}"), ('삭제 방식', t['delete']), ('파티션', t['part']), ('보유 기간', t['keep'])]) + '</table>'
    secs += ('<table style="table-layout:fixed"><colgroup><col style="width:4%"><col style="width:15%"><col style="width:15%"><col style="width:8%"><col style="width:3%"><col style="width:4.5%"><col style="width:7.5%"><col style="width:34%"><col style="width:3%"><col style="width:6%"></colgroup>'
             '<tr><th>No</th><th>물리명</th><th>논리명</th><th>타입</th><th>NULL</th><th>기본값</th><th>제약</th><th>설명</th><th>확정</th><th>메모</th></tr>')
    prev = None
    for k, ((p, ko, en, ty, nl, df, ck, ds), kind) in enumerate(fc, 1):
        g = t['grp_of'][p] if kind == 'b' else CMN
        if g != prev:
            secs += f'<tr class="grp"><td colspan="10">{il(g)}</td></tr>'; prev = g
        vals = CODES.get(p, []) if ('값 목록' in ck) else []
        if vals: ds = (ds + ' ' if ds else '') + ('값 목록은 아래 행 (그룹 `' + REUSE[p] + '` 재사용).' if p in REUSE else 'JSON 안의 코드 값 목록은 아래 행.' if p in JSON_CODES else '값 목록은 아래 행.')
        on = t['t'] in CONFIRMED_TABLES or (kind == 'b' and (t['t'], g) in CONFIRMED_GROUPS)
        cls = ' class="sys"' if kind == 's' else (' class="cf"' if '[확인' in ds + ck + en else '')
        secs += (f'<tr{cls}><td class="n">{i}-{k}</td><td class="p">{pn(p)}</td><td>{ln1(ko, en)}</td><td class="ty">{il(ty)}</td>'
                 f'<td class="n">{nl}</td><td class="p">{il(df)}</td><td class="wr">{il(ck)}</td><td>{il(ds)}</td>' + ckcell(on) + '<td class="memo"></td></tr>')
        for vi, v in enumerate(vals, 1):
            _c = 'cv' + (' first' if vi == 1 else '') + (' last' if vi == len(vals) else '')
            secs += (f'<tr class="{_c}"><td class="n">{i}-{k}-{vi}</td><td class="p">└ {pn(v[0])}</td><td>{ln1(v[1], v[2])}</td>'
                     f'<td colspan="5">정렬 {v[4]}' + (f' · {il(v[3])}' if v[3] else '') + '</td>' + ckcell(on) + f'<td class="memo"><span class="ty">{code_id(p, v[0])}</span></td></tr>')
    secs += '</table>'
    if t['idx'] or t['check']:
        secs += '<h3>인덱스·제약 (제안)</h3><table><tr><th>No</th><th>내용</th><th>확정</th><th>메모</th></tr>'
        for k, x in enumerate(t['idx'] + [f'CK (테이블 수준): {c}' for c in t['check']], 1):
            secs += f'<tr{" class=cf" if "[확인" in x else ""}><td class="n">{i}-X{k}</td><td>{il(x)}</td>' + ckcell(t['t'] in CONFIRMED_TABLES) + '<td class="memo"></td></tr>'
        secs += '</table>'
toc += f'</table><p><b>합계: 업무 컬럼 {tot_b} + 공통 컬럼 {tot_s} = {tot_b+tot_s}개</b></p>'
conf = '<h2 class="t">확인이 필요한 사항 (결정 필요)</h2><table><tr><th>No</th><th>항목</th><th>내용</th><th>대상</th><th>확정</th><th>메모</th></tr>'
for k, (a, b, c) in enumerate(CONFIRM, 1):
    conf += f'<tr class="cf"><td class="n">Q{k}</td><td>{il(a)}</td><td>{il(b)}</td><td>{il(c)}</td><td class="ck">{BOX}</td><td class="memo"></td></tr>'
conf += '</table>'
body = ('<h1>주문 도메인 컬럼 정의서 (제안)</h1>'
        f'<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-25 · 주문 도메인 결정 1-1~10-11, 컬럼 검토 OC-10·OC-15·OC-16~OC-116 기준 · 테이블 {len(T)}개 · 컬럼 {tot_b+tot_s}개 (업무 {tot_b} + 공통 {tot_s}) · 테이블 이름과 컬럼 모두 제안</div>'
        + NOTE + toc + conf + secs)
open(os.path.join(OUT, 'columns.html'), 'w').write(page('주문 도메인 컬럼 정의서', '<div class="colspec">' + body + '</div>'))
print(len(T), tot_b, tot_s, tot_b + tot_s)
