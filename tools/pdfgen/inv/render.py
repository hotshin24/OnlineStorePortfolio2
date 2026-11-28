# 재고 도메인 테이블 이름·컬럼 정의서 HTML (dlv/render.py에서 가져옴). 공통코드 CODE_ID는 아직 매기지 않는다.
# 사용: python3 render.py <출력폴더>
import sys, os, re, html, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import T, CODES, CONFIRM, TS, TABLE_GROUPS, REUSE, REUSE_NO_ROWS, SAME_NAME_FOLD, CONFIRMED_GROUPS, CONFIRMED_TABLES, EXTERNAL_SOURCED as PG_SOURCED, POLICY, NAME_CONFIRMED, PHASE, PHASE_COL, PHASE_ORDER, PHASE_Q
JSON_CODES = {}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decision import C as _DC
NT = sum(1 for c in _DC if c[0].startswith('T-'))
NAX = len(_DC) - NT - sum(1 for c in _DC if c[0].startswith('IC-'))
NIC = sum(1 for c in _DC if c[0].startswith('IC-'))
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
CSS += '\ntd.ph{text-align:center;font-size:7pt;color:#777}td.ph.p1{color:#0b5;font-weight:700}td.ph.pq{color:#c60;font-weight:700}\n'
def il(s):
    s = html.escape(str(s)); p = s.split('`')
    s = ''.join(f'<code>{x}</code>' if i % 2 else x for i, x in enumerate(p))
    return re.sub(r'\[(확인 필요[^\]]*)\]', r'<span class="warn">[\1]</span>', s)
def ln1(ko, en): return f'{il(ko)} <span class="en" style="display:inline-block">({il(en)})</span>'
def pn(p): return html.escape(p).replace('_', '_<wbr>')
def page(title, body): return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}{RV_CSS}</style></head><body>{body}</body></html>'
BOX = '☐'
ON = '☑'
def tphase(t): return PHASE.get(t, '2차')
def cphase(t, c): return PHASE_COL.get((t, c), tphase(t))
def phcell(p): return f'<td class="ph{" p1" if p.startswith("1차") else " pq" if p == "확인" else ""}">{p}</td>'
for _k in PHASE_COL: assert any(t['t'] == _k[0] and any(c[0] == _k[1] for c in t['cols']) for t in T), _k
for _k in PHASE_Q: assert any(a == _k for a, b, c in CONFIRM), _k
def xphase(t, x, c2):
    # 1차-6 A: FK 제약만 뒤 차수. 그 컬럼의 FK 인덱스 행은 '1차 (FK 2차)', CHECK는 1차에 만든다
    if tphase(t) == '1차' and x.startswith('IX') and any(c in x for c in c2): return '1차 (FK 2차)'
    return tphase(t)
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
PII = []  # 재고에는 개인정보 보유 테이블이 없다
def full_cols(t):
    return [(x, 'b') for x in t['cols']] + ([(x, 's') for x in PII] if t['pii'] else []) + [(x, 's') for x in SYS] + ([(x, 's') for x in DEL] if t['ldel'] else [])
CMN = '공통 컬럼 (규칙 1, 8-A: 개인정보 보유 → 시스템 → 논리 삭제)'
# ---------------- 1. 테이블 이름 (후보)
rows = ''
NHEAD = '<table style="table-layout:fixed"><colgroup><col style="width:3%"><col style="width:20%"><col style="width:22%"><col style="width:33%"><col style="width:4%"><col style="width:3.5%"><col style="width:3.5%"><col style="width:11%"></colgroup><tr><th>No</th><th>물리명</th><th>논리명 (제안)</th><th>설명 (제안)</th><th>컬럼 수</th><th>확정</th><th>차수</th><th>메모</th></tr>'
for i, t in enumerate(T, 1):
    if t['t'] in GFIRST:
        g = TGRP[t['t']]
        rows += ('</table>' if i > 1 else '') + f'<h2 class="g">{GNO[g]}. {g}</h2>' + NHEAD
    rows += (f'<tr><td class="n">{i}</td><td class="p">{pn(t["t"])}</td><td>{ln1(t["ko"], t["en"])}</td>'
             f'<td>{il(t["desc"])}<br><span class="en">근거: 재고 결정 {il(t["basis"])}</span></td><td class="n">{len(full_cols(t))}</td>' + ckcell(t['t'] in NAME_CONFIRMED) + phcell(tphase(t['t'])) + '<td class="memo"></td></tr>')
_KO = {t['t']: t['ko'].split(' (')[0] for t in T}
PBOX = ('<div class="box"><b>1차 범위 (2026-11-28 사용자 결정)</b><br>'
        '· 코드로 처음 구현할 범위부터 확정한다. 재고 1차 테이블: ' + ', '.join(f'{_KO[x]}' for x in PHASE if PHASE[x] == '1차') + ' (안전 재고 변경 이력과 월 마감은 1차-5 A로 더함).<br>'
        '· 1차에 먼저 결정할 순서: 현재고(확정) → ' + ' → '.join(f'{_KO[x]}' for x in PHASE_ORDER) + '. 나머지 테이블은 2차(보류, 입고 예정, 스냅샷, 예외·대사, 사은품·운영자재).<br>'
        '· 1차는 기초 재고로 시작하고 입고 예정·생산 입고는 2차(1차-2 A), 고객 취소·반품은 2차(1차-1 A)다. 1차 테이블 안에서 부모가 2차 테이블인 FK 컬럼은 "1차 (FK 2차)"다: 컬럼과 CHECK는 1차에 만들고 FK 제약은 부모를 만드는 차수에 건다(1차-6 A). 오픈 뒤 등록한 SKU는 1차 동안 기초 재고를 행마다 1회 받는다(1차-8 A).<br>'
        '· <b>차수</b> 칸은 <b>확정</b> 칸과 따로다. 차수 표시는 확정이 아니다.</div>')
total = sum(len(full_cols(t)) for t in T)
longest = sorted(T, key=lambda t: -len(t['t']))[:2]
META = '자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-28 · 재고 도메인 결정(축 8개 결정 %d개, 테이블 T-1~T-%d, 컬럼 IC-1~IC-%d) 기준' % (NAX, NT, NIC)
body = ('<h1>재고 도메인 테이블 이름 (검토용)</h1>'
        f'<div class="meta">{META} · 물리명 7개는 T-10 A에서 고른 안, 나머지는 후보, 논리명·설명은 제안</div>'
        f'<div class="box">재고 도메인 결정 {len(_DC)}개(축 8개 결정 {NAX}, 테이블 {NT}, 컬럼 {NIC})에서 나온 테이블 {len(T)}개다 (모두 <code>INV_</code>). 물리명 7개(현재고, 수불 원장, 재고 확보, 입고 예정, 재고 스냅샷, 재고 월 마감, 재고 예외)는 테이블 결정 T-10 A에서 골랐고, 나머지는 후보다. <b>확정</b> 칸은 컬럼 검토에서 확정할 때 표시한다(지금은 {", ".join(sorted(NAME_CONFIRMED)) or "없음"}). 고칠 논리명이나 설명은 메모 칸에 적는다.</div>' + PBOX
        + rows + f'</table><p><b>합계: 테이블 {len(T)}개, 컬럼 {total}개 (공통 컬럼 포함)</b></p>')
body += ('<h2>공통 사항</h2><ul>'
         f'<li>모든 이름은 128바이트 이내. 가장 긴 것은 ' + ', '.join(f'<code>{t["t"]}</code>({len(t["t"])}바이트)' for t in longest) + '.</li>'
         '<li>시퀀스는 <code>SEQ_{테이블}</code>. CACHE 100: 수불 원장, 재고 확보, 재고 스냅샷. CACHE 20: 현재고, 입고 예정, 월 마감, 재고 예외 (2-7 A, 4-2 A, T-11 A).</li>'
         '<li>테이블 7개: 현재고·수불 원장(1-1 A), 재고 확보(4-2 A), 입고 예정(6-1 A), 재고 스냅샷(8-1 A), 월 마감(8-2 C), 재고 예외(8-8 B, 대사 차이를 합침 8-8 후속 B).</li>'
         '<li>파티션: 수불 원장(업무 일자), 재고 확보(확보 일시), 재고 스냅샷(스냅샷 일자)만 월 INTERVAL 파티션. 이 세 테이블은 다른 테이블이 FK로 가리키지 않는다(재고 예외의 확보 ID, 정정의 원래 원장 ID는 FK 없음, T-1 A, T-6 B). '
         '입고 예정·재고 예외는 원장·확보가 가리키는 부모라 파티션 없이 기한이 지난 행을 나눠서 DELETE한다 (T-2 A, T-3 A). 현재고는 지우지 않는다 (T-4 A).</li>'
         '<li>다른 도메인 ID(주문 상품·사은품, 배송 출고·운송장·출고 요청 상품, 클레임, WMS 작업, SCM 발주 라인, 관리자)는 FK 없이 인덱스만 둔다 (2-4 A). FK는 재고 테이블끼리와 상품 SKU에만 건다. 창고·사은품·운영자재 마스터(WMS)는 FK 예정이다.</li>'
         '<li>개인정보는 없다. 논리 삭제 테이블도 없다.</li>'
         '<li>표 순서는 지시 규칙 8: 테이블을 관련 그룹으로 모으고, 그룹과 그룹 안 모두 중요도 순 (8-C A, 그룹 구성은 제안). DDL 생성 순서는 FK 순서로 따로 정한다 (8-D).</li></ul>')
open(os.path.join(OUT, 'names.html'), 'w').write(page('재고 도메인 테이블 이름', body))

# ---------------- 2. 컬럼 정의서
NOTE = ('<div class="box"><b>검토 방법</b><br>'
        '· 모든 컬럼은 <b>제안</b>이다. 확정한 컬럼은 <b>확정</b> 칸에 표시하고, 고칠 내용은 메모 칸에 적는다. 공통코드 <code>CODE_ID</code>는 아직 매기지 않았다. 테이블 물리명 7개는 T-10 A에서 골랐고, 확정 표시는 컬럼 검토 때 한다.<br>'
        '· 노란 행: 확인이 필요한 컬럼 (설명에 빨간 표시). 결정 단계에서 정할 사항은 아래 "확인이 필요한 사항"에 있고, 지금까지의 결정은 <code>docs/pdf/결정/재고결정/</code>에 결정 하나당 PDF로 있다.<br>'
        '· 회색 행: 공통 컬럼 (개인정보 보유 4개, 시스템 6개, 논리 삭제 3개). 선행 결정으로 정해져 있다. 재고에는 개인정보 보유·논리 삭제 테이블이 없어 시스템 6개만 붙는다.<br>'
        '· NULL 칸: N = NOT NULL, Y = NULL 허용. 파기 대상 개인정보 컬럼은 NULL 허용이고 필수 여부는 애플리케이션이 검증한다 (선행 7).<br>'
        '· 코드 컬럼은 바로 아래 └ 행에 값 목록을 둔다. 같은 이름의 코드 컬럼이 다른 테이블에 다시 나오면 노란 참조 행(↺)으로 처음 나온 곳을 가리킨다 (지시 규칙 4).<br>'
        '· 정렬은 지시 규칙 8 (테이블 그룹은 남색 제목, 컬럼 그룹은 초록 줄). PK는 첫 컬럼, 공통 컬럼은 끝. 그룹 구성과 순서도 제안이다.</div>')
toc = '<h2>목차</h2>'
THEAD = '<table style="table-layout:fixed"><colgroup><col style="width:5%"><col style="width:31%"><col style="width:36%"><col style="width:7%"><col style="width:7%"><col style="width:7%"><col style="width:7%"></colgroup><tr><th>No</th><th>테이블</th><th>논리명</th><th>업무 컬럼</th><th>공통 컬럼</th><th>합계</th><th>차수</th></tr>'
secs = ''; tot_b = tot_s = 0; POS = {}; FIRST = {}
for i, t in enumerate(T, 1):
    fc = full_cols(t); nb = len(t['cols']); ns = len(fc) - nb; tot_b += nb; tot_s += ns
    if t['t'] in GFIRST:
        g = TGRP[t['t']]
        toc += ('</table>' if i > 1 else '') + f'<h3>{GNO[g]}. {g}</h3>' + THEAD
        secs += f'<h2 class="g pb">{GNO[g]}. {g}</h2>'
    toc += f'<tr><td class="n">{i}</td><td class="p">{t["t"]}</td><td>{ln1(t["ko"], t["en"])}</td><td class="n">{nb}</td><td class="n">{ns}</td><td class="n">{nb+ns}</td>' + phcell(tphase(t['t'])) + '</tr>'
    secs += f'<h2{"" if t["t"] in GFIRST else " class=t"}>{i}. {t["t"]}</h2>'
    secs += '<table class="info">' + f'<tr><td>논리명</td><td>{ln1(t["ko"], t["en"])}</td></tr>' + ''.join(f'<tr><td>{a}</td><td>{il(b)}</td></tr>' for a, b in [
        ('설명', t['desc']), ('근거 결정', '재고 결정 ' + t['basis']),
        ('차수', tphase(t['t']) + (' (FK 제약만 2차: ' + ', '.join(f'`{c}`' for (tt, c) in PHASE_COL if tt == t['t']) + ')' if any(tt == t['t'] for tt, c in PHASE_COL) else '')), ('PK·시퀀스', f"{t['pk']} · CACHE {t['cache']}"), ('삭제 방식', t['delete']), ('파티션', t['part']), ('보유 기간', t['keep'])]) + '</table>'
    secs += ('<table style="table-layout:fixed"><colgroup><col style="width:4%"><col style="width:15%"><col style="width:15%"><col style="width:8%"><col style="width:3%"><col style="width:4.5%"><col style="width:7.5%"><col style="width:31%"><col style="width:3%"><col style="width:3%"><col style="width:6%"></colgroup>'
             '<tr><th>No</th><th>물리명</th><th>논리명</th><th>타입</th><th>NULL</th><th>기본값</th><th>제약</th><th>설명</th><th>확정</th><th>차수</th><th>메모</th></tr>')
    prev = None
    for k, ((p, ko, en, ty, nl, df, ck, ds), kind) in enumerate(fc, 1):
        g = t['grp_of'][p] if kind == 'b' else CMN
        if g != prev:
            secs += f'<tr class="grp"><td colspan="11">{il(g)}</td></tr>'; prev = g
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
                         + ckcell(on_) + phcell(cphase(t['t'], p)) + '<td class="memo"></td></tr>')
        if p in REUSE_NO_ROWS:
            rt, rc = REUSE_NO_ROWS[p]; nv = len(vals); vals = []
            ds = (ds + ' ' if ds else '') + '값 목록은 아래 행.'
            where = POS[(rt, rc)] + (' (이 테이블)' if rt == t['t'] else f' ({rt})')
            reuse_row = (f'<tr class="rv"><td class="n">{i}-{k}-↺</td><td class="p">↺ 값 목록 재사용</td>'
                         f'<td colspan="6">공통코드 그룹 <code>{REUSE[p]}</code> (값 {nv}개) · 값 행은 <b>{where}</b> <code>{rc}</code> 아래에 있다. '
                         f'값을 더하면 두 컬럼의 값 목록 CK를 함께 고친다.</td>' + ckcell(on_) + phcell(cphase(t['t'], p)) + '<td class="memo"></td></tr>')
        if vals: ds = (ds + ' ' if ds else '') + ('값 목록은 아래 행 (그룹 `' + REUSE[p] + '` 재사용).' if p in REUSE else 'JSON 안의 코드 값 목록은 아래 행.' if p in JSON_CODES else '값 목록은 아래 행.')
        on = t['t'] in CONFIRMED_TABLES or (kind == 'b' and (t['t'], g) in CONFIRMED_GROUPS)
        ph = cphase(t['t'], p) if kind == 'b' else tphase(t['t'])
        cls = ' class="sys"' if kind == 's' else (' class="cf"' if '[확인' in ds + ck + en else '')
        no = f'<b style="font-weight:800;color:#111">{i}-{k}</b>' if kind == 'b' and (t['t'], p) in PG_SOURCED else f'{i}-{k}'
        secs += (f'<tr{cls}><td class="n">{no}</td><td class="p">{pn(p)}</td><td>{ln1(ko, en)}</td><td class="ty">{il(ty)}</td>'
                 f'<td class="n">{nl}</td><td class="p">{il(df)}</td><td class="wr">{il(ck)}</td><td>{il(ds)}</td>' + ckcell(on) + phcell(ph) + '<td class="memo"></td></tr>')
        secs += reuse_row
        for vi, v in enumerate(vals, 1):
            _c = 'cv' + (' first' if vi == 1 else '') + (' last' if vi == len(vals) else '')
            secs += (f'<tr class="{_c}"><td class="n">{i}-{k}-{vi}</td><td class="p">└ {pn(v[0])}</td><td>{ln1(v[1], v[2])}</td>'
                     f'<td colspan="5">정렬 {v[4]}' + (f' · {il(v[3])}' if v[3] else '') + '</td>' + ckcell(on) + phcell(ph) + f'<td class="memo"><span class="ty">{code_id(p, v[0])}</span></td></tr>')
    secs += '</table>'
    if t['idx'] or t['check']:
        secs += '<h3>인덱스·제약 (제안)</h3><table><tr><th>No</th><th>내용</th><th>확정</th><th>차수</th><th>메모</th></tr>'
        _c2 = [c for (tt, c) in PHASE_COL if tt == t['t']]
        for k, x in enumerate(t['idx'] + [f'CK (테이블 수준): {c}' for c in t['check']], 1):
            secs += f'<tr{" class=cf" if "[확인" in x else ""}><td class="n">{i}-X{k}</td><td>{il(x)}</td>' + ckcell(t['t'] in CONFIRMED_TABLES) + phcell(xphase(t['t'], x, _c2)) + '<td class="memo"></td></tr>'
        secs += '</table>'
toc += f'</table><p><b>합계: 업무 컬럼 {tot_b} + 공통 컬럼 {tot_s} = {tot_b+tot_s}개</b></p>'
conf = '<h2 class="t">확인이 필요한 사항 (결정 필요)</h2><p>차수 칸이 1차인 항목을 1차 컬럼 검토 때 먼저 묻는다.</p><table><tr><th>No</th><th>항목</th><th>내용</th><th>대상</th><th>확정</th><th>차수</th><th>메모</th></tr>'
for k, (a, b, c) in enumerate(CONFIRM, 1):
    conf += f'<tr class="cf"><td class="n">Q{k}</td><td>{il(a)}</td><td>{il(b)}</td><td>{il(c)}</td><td class="ck">{BOX}</td>' + phcell(PHASE_Q.get(a, '2차')) + '<td class="memo"></td></tr>'
conf += '</table>'
conf += '<h2 class="t">공통코드에 둘 정책값</h2><table><tr><th>No</th><th>항목</th><th>내용</th><th>근거</th></tr>' + ''.join(f'<tr><td class="n">P{k}</td><td>{il(a)}</td><td>{il(b)}</td><td>{il(c)}</td></tr>' for k, (a, b, c) in enumerate(POLICY, 1)) + '</table>'
body = ('<h1>재고 도메인 컬럼 정의서 (제안)</h1>'
        f'<div class="meta">{META} · 테이블 {len(T)}개 · 컬럼 {tot_b+tot_s}개 (업무 {tot_b} + 공통 {tot_s}) · 컬럼은 모두 제안</div>'
        + NOTE + PBOX.replace('<div class="box">', '<div class="box">', 1) + toc + conf + secs)
open(os.path.join(OUT, 'columns.html'), 'w').write(page('재고 도메인 컬럼 정의서', '<div class="colspec">' + body + '</div>'))
print(len(T), tot_b, tot_s, tot_b + tot_s)
