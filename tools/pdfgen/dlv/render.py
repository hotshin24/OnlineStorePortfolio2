# 배송 도메인 테이블 이름·컬럼 정의서 HTML (pay/render.py에서 가져옴). 공통코드 CODE_ID는 아직 매기지 않는다.
# 사용: python3 render.py <출력폴더>
import sys, os, re, html, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import T, CODES, CONFIRM, TS, TABLE_GROUPS, REUSE, REUSE_NO_ROWS, SAME_NAME_FOLD, CONFIRMED_GROUPS, CONFIRMED_TABLES, EXTERNAL_SOURCED as PG_SOURCED, POLICY
JSON_CODES = {}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from col_review import C as _DC
NDC = sum(1 for c in _DC if c[0].startswith('DC-'))
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
_pgm = PG_SOURCED - {(t['t'], c[0]) for t in T for c in t['cols']}
assert not _pgm, _pgm
missing = [(t['t'], c[0]) for t in T for c in t['cols'] if '값 목록' in c[6] and c[0] not in CODES]
assert not missing, missing
def code_id(col, code): return ''

RV_CSS = 'tr.rv td{background:#fff4d6;font-size:8pt;border-top:1px solid #d9a521;border-bottom:2px solid #d9a521;color:#5a4300} tr.rv td:first-child{border-left:4px solid #d9a521} tr.rv td.p{padding-left:14px;font-weight:700}'
CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ord', 'style.css'), encoding='utf-8').read()
def il(s):
    s = html.escape(str(s)); p = s.split('`')
    s = ''.join(f'<code>{x}</code>' if i % 2 else x for i, x in enumerate(p))
    return re.sub(r'\[(확인 필요[^\]]*)\]', r'<span class="warn">[\1]</span>', s)
def ln1(ko, en): return f'{il(ko)} <span class="en" style="display:inline-block">({il(en)})</span>'
def pn(p): return html.escape(p).replace('_', '_<wbr>')
def page(title, body): return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}{RV_CSS}</style></head><body>{body}</body></html>'
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
 ('PII_RETENTION_REASON_CD','개인정보 보유 사유 코드','Personal Information Retention Reason Code','VARCHAR2(30)','Y','','CK (값 목록)','`CMM_CODE` 보유 기간 코드 (선행 결정 7). 주문 값 복사 (DC-27 B).'),
 ('PII_RETENTION_BASE_DT','개인정보 보유 기간 기산 일자','Personal Information Retention Base Date','DATE','Y','','','주문의 기산일(거래 종료일)을 복사한다 (DC-27 B). 이름은 후보.'),
 ('PII_RETENTION_END_DT','개인정보 파기 예정 일자','Personal Information Retention End Date','DATE','Y','','','주문(회수·교환이면 원래 주문)의 파기 예정일을 복사한다. 합포장이면 가장 늦은 날. 지나면 일 배치가 개인정보 컬럼을 NULL로 바꾸고 행을 지운다 (DC-27 B, DC-28 A).'),
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
             f'<td>{il(t["desc"])}<br><span class="en">근거: 배송 결정 {il(t["basis"])}</span></td><td class="n">{len(full_cols(t))}</td>' + ckcell(t['t'] in CONFIRMED_TABLES) + '<td class="memo"></td></tr>')
total = sum(len(full_cols(t)) for t in T)
longest = sorted(T, key=lambda t: -len(t['t']))[:2]
META = '자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-27 · 배송 도메인 결정(전제·축 7개, 테이블 T-1~T-7, 컬럼 DC-1~DC-%d) 기준' % NDC
body = ('<h1>배송 도메인 테이블 이름 (검토용)</h1>'
        f'<div class="meta">{META} · 물리명, 논리명, 설명 모두 후보 (확인 칸으로 검토)</div>'
        f'<div class="box">배송 도메인 결정 42개(전제·축 7, 테이블 7, 컬럼 {NDC})에서 나온 테이블 {len(T)}개다 (모두 <code>DLV_</code>). 물리명도 아직 확정하지 않았다. 확정한 행은 <b>확정</b> 칸에 표시하고, 고칠 이름이나 내용은 메모 칸에 적는다.</div>'
        + rows + f'</table><p><b>합계: 테이블 {len(T)}개, 컬럼 {total}개 (공통 컬럼 포함)</b></p>')
body += ('<h2>공통 사항</h2><ul>'
         f'<li>모든 이름은 128바이트 이내. 가장 긴 것은 ' + ', '.join(f'<code>{t["t"]}</code>({len(t["t"])}바이트)' for t in longest) + '.</li>'
         '<li>시퀀스는 <code>SEQ_{테이블}</code>. 복합 PK인 패키지 상품은 시퀀스 없음. CACHE는 제안(고빈도 100, 기준 데이터·사고 20)이고 정의서 "확인이 필요한 사항"에서 정한다.</li>'
         '<li>테이블 11개: 결정으로 정해진 8개(1-1 B의 5개, 4-2 B 추적 이벤트, 선행 6 연동 로그, 주문 5-7 A 도서산간 기준표) + 상태 이력(T-1 C), 배송 사고(T-3 A), 운임표(T-5 A). 출고와 회수가 같은 테이블을 쓴다 (2-1 B).</li>'
         '<li>파티션 (DC-28 A): 핵심 6개(출고 요청, 요청 상품, 출고, 패키지, 패키지 상품, 사고)는 파티션 없이 보존 기간이 지난 행을 나눠서 DELETE. 추적 이벤트·상태 이력·연동 로그만 월 INTERVAL 파티션. 기준 데이터 2개는 마스터라 논리 삭제.</li>'
         '<li>주문·클레임 ID는 FK 없이 값으로 두고 매일 검증한다 (5-1 B). FK는 배송 테이블끼리와 마스터(상품 SKU, 외부 업체)에만 건다. 창고·비판매 품목 마스터(WMS)는 FK 예정이다.</li>'
         '<li>개인정보는 출고 한 테이블에만 있다 (DC-6 A). 공동현관 출입 방법은 두지 않는다 (DC-7 A).</li>'
         '<li>표 순서는 지시 규칙 8: 테이블을 관련 그룹으로 모으고, 그룹과 그룹 안 모두 중요도 순 (8-C A, 그룹 구성은 제안). DDL 생성 순서는 FK 순서로 따로 정한다 (8-D).</li></ul>')
open(os.path.join(OUT, 'names.html'), 'w').write(page('배송 도메인 테이블 이름', body))

# ---------------- 2. 컬럼 정의서
NOTE = ('<div class="box"><b>검토 방법</b><br>'
        '· 테이블 이름과 모든 컬럼은 <b>제안</b>이다. 확정한 컬럼은 <b>확정</b> 칸에 표시하고, 고칠 내용은 메모 칸에 적는다. 공통코드 <code>CODE_ID</code>는 아직 매기지 않았다.<br>'
        '· 노란 행: 확인이 필요한 컬럼 (설명에 빨간 표시). 결정 단계에서 정할 사항은 아래 "확인이 필요한 사항"에 있고, 지금까지의 결정은 <code>docs/pdf/결정/배송결정/</code>에 결정 하나당 PDF로 있다.<br>'
        '· 회색 행: 공통 컬럼 (개인정보 보유 4개, 시스템 6개, 논리 삭제 3개). 선행 결정으로 정해져 있다. 개인정보 보유는 출고만, 논리 삭제는 기준 데이터 2개만이다.<br>'
        '· NULL 칸: N = NOT NULL, Y = NULL 허용. 파기 대상 개인정보 컬럼은 NULL 허용이고 필수 여부는 애플리케이션이 검증한다 (선행 7).<br>'
        '· 코드 컬럼은 바로 아래 └ 행에 값 목록을 둔다. 같은 이름의 코드 컬럼이 다른 테이블에 다시 나오면 노란 참조 행(↺)으로 처음 나온 곳을 가리킨다 (지시 규칙 4).<br>'
        f'· <b>굵은 번호</b>: 택배사에서 오는 값 ({len(PG_SOURCED)}개). 택배사 API 응답·추적 웹훅으로 받거나 운임 계약서에서 옮겨 적는 값이다.<br>'
        '· 정렬은 지시 규칙 8 (테이블 그룹은 남색 제목, 컬럼 그룹은 초록 줄). PK는 첫 컬럼, 공통 컬럼은 끝. 그룹 구성과 순서도 제안이다.</div>')
toc = '<h2>목차</h2>'
THEAD = '<table style="table-layout:fixed"><colgroup><col style="width:5%"><col style="width:33%"><col style="width:38%"><col style="width:8%"><col style="width:8%"><col style="width:8%"></colgroup><tr><th>No</th><th>테이블</th><th>논리명</th><th>업무 컬럼</th><th>공통 컬럼</th><th>합계</th></tr>'
secs = ''; tot_b = tot_s = 0; POS = {}; FIRST = {}
for i, t in enumerate(T, 1):
    fc = full_cols(t); nb = len(t['cols']); ns = len(fc) - nb; tot_b += nb; tot_s += ns
    if t['t'] in GFIRST:
        g = TGRP[t['t']]
        toc += ('</table>' if i > 1 else '') + f'<h3>{GNO[g]}. {g}</h3>' + THEAD
        secs += f'<h2 class="g pb">{GNO[g]}. {g}</h2>'
    toc += f'<tr><td class="n">{i}</td><td class="p">{t["t"]}</td><td>{ln1(t["ko"], t["en"])}</td><td class="n">{nb}</td><td class="n">{ns}</td><td class="n">{nb+ns}</td></tr>'
    secs += f'<h2{"" if t["t"] in GFIRST else " class=t"}>{i}. {t["t"]}</h2>'
    secs += '<table class="info">' + f'<tr><td>논리명</td><td>{ln1(t["ko"], t["en"])}</td></tr>' + ''.join(f'<tr><td>{a}</td><td>{il(b)}</td></tr>' for a, b in [
        ('설명', t['desc']), ('근거 결정', '배송 결정 ' + t['basis']),
        ('PK·시퀀스', f"{t['pk']} · CACHE {t['cache']}"), ('삭제 방식', t['delete']), ('파티션', t['part']), ('보유 기간', t['keep'])]) + '</table>'
    secs += ('<table style="table-layout:fixed"><colgroup><col style="width:4%"><col style="width:15%"><col style="width:15%"><col style="width:8%"><col style="width:3%"><col style="width:4.5%"><col style="width:7.5%"><col style="width:34%"><col style="width:3%"><col style="width:6%"></colgroup>'
             '<tr><th>No</th><th>물리명</th><th>논리명</th><th>타입</th><th>NULL</th><th>기본값</th><th>제약</th><th>설명</th><th>확정</th><th>메모</th></tr>')
    prev = None
    for k, ((p, ko, en, ty, nl, df, ck, ds), kind) in enumerate(fc, 1):
        g = t['grp_of'][p] if kind == 'b' else CMN
        if g != prev:
            secs += f'<tr class="grp"><td colspan="10">{il(g)}</td></tr>'; prev = g
        vals = CODES.get(p, []) if ('값 목록' in ck) else []
        on_ = t['t'] in CONFIRMED_TABLES or (kind == 'b' and (t['t'], g) in CONFIRMED_GROUPS)
        POS[(t['t'], p)] = f'{i}-{k}'
        reuse_row = ''
        same = None
        if SAME_NAME_FOLD and vals and kind == 'b':
            if p in FIRST and FIRST[p] != t['t']: same = (FIRST[p], p)
            else: FIRST.setdefault(p, t['t'])
        if same:
            rt, rc = same; nv = len(vals); vals = []
            ds = (ds + ' ' if ds else '') + '값 목록은 아래 행.'
            reuse_row = (f'<tr class="rv"><td class="n">{i}-{k}-↺</td><td class="p">↺ 같은 컬럼의 값 목록</td>'
                         f'<td colspan="6">같은 이름 컬럼의 값 목록 (값 {nv}개) · 값 행은 <b>{POS[(rt, rc)]} ({rt})</b> <code>{rc}</code> 아래에 있다 (지시 규칙 4, 결제 PYC-86 A).</td>'
                         + ckcell(on_) + '<td class="memo"></td></tr>')
        if p in REUSE_NO_ROWS:
            rt, rc = REUSE_NO_ROWS[p]; nv = len(vals); vals = []
            ds = (ds + ' ' if ds else '') + '값 목록은 아래 행.'
            where = POS[(rt, rc)] + (' (이 테이블)' if rt == t['t'] else f' ({rt})')
            reuse_row = (f'<tr class="rv"><td class="n">{i}-{k}-↺</td><td class="p">↺ 값 목록 재사용</td>'
                         f'<td colspan="6">공통코드 그룹 <code>{REUSE[p]}</code> (값 {nv}개) · 값 행은 <b>{where}</b> <code>{rc}</code> 아래에 있다. '
                         f'값을 더하면 두 컬럼의 값 목록 CK를 함께 고친다.</td>' + ckcell(on_) + '<td class="memo"></td></tr>')
        if vals: ds = (ds + ' ' if ds else '') + ('값 목록은 아래 행 (그룹 `' + REUSE[p] + '` 재사용).' if p in REUSE else 'JSON 안의 코드 값 목록은 아래 행.' if p in JSON_CODES else '값 목록은 아래 행.')
        on = t['t'] in CONFIRMED_TABLES or (kind == 'b' and (t['t'], g) in CONFIRMED_GROUPS)
        cls = ' class="sys"' if kind == 's' else (' class="cf"' if '[확인' in ds + ck + en else '')
        no = f'<b style="font-weight:800;color:#111">{i}-{k}</b>' if kind == 'b' and (t['t'], p) in PG_SOURCED else f'{i}-{k}'
        secs += (f'<tr{cls}><td class="n">{no}</td><td class="p">{pn(p)}</td><td>{ln1(ko, en)}</td><td class="ty">{il(ty)}</td>'
                 f'<td class="n">{nl}</td><td class="p">{il(df)}</td><td class="wr">{il(ck)}</td><td>{il(ds)}</td>' + ckcell(on) + '<td class="memo"></td></tr>')
        secs += reuse_row
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
conf += '<h2 class="t">공통코드에 둘 정책값</h2><table><tr><th>No</th><th>항목</th><th>내용</th><th>근거</th></tr>' + ''.join(f'<tr><td class="n">P{k}</td><td>{il(a)}</td><td>{il(b)}</td><td>{il(c)}</td></tr>' for k, (a, b, c) in enumerate(POLICY, 1)) + '</table>'
body = ('<h1>배송 도메인 컬럼 정의서 (제안)</h1>'
        f'<div class="meta">{META} · 테이블 {len(T)}개 · 컬럼 {tot_b+tot_s}개 (업무 {tot_b} + 공통 {tot_s}) · 테이블 이름과 컬럼 모두 제안</div>'
        + NOTE + toc + conf + secs)
open(os.path.join(OUT, 'columns.html'), 'w').write(page('배송 도메인 컬럼 정의서', '<div class="colspec">' + body + '</div>'))
print(len(T), tot_b, tot_s, tot_b + tot_s)
