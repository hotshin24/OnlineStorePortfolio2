# 상품 도메인 공통코드 (CMM_CODE) PDF용 HTML과 code_ids_prd.json을 만든다.
# 사용: python3 cmm.py <출력.html> <회원 code_ids.json>
import sys, os, re, html, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import T, CODES, REUSE, GROUP_NAME, NEW_GROUPS_EXTRA, ATTRS, TABLE_GROUPS, JSON_CODES, FILE_CODES, POLICY_GROUPS
OUT, MBR_IDS = sys.argv[1], json.load(open(sys.argv[2], encoding='utf-8'))

_by = {t['t']: t for t in T}
ORDER = [_by[n] for g, ns in TABLE_GROUPS for n in ns]
USES = {}
for t in ORDER:
    for g, cs in t['cols']:
        for c in cs:
            if c[0] in CODES: USES.setdefault(c[0], []).append((t['t'], c))
            if c[0] in JSON_CODES: USES.setdefault(JSON_CODES[c[0]], []).append((t['t'], c))
            if c[0] in FILE_CODES: USES.setdefault(c[0], []).append((t['t'], c))
JSON_NAME = {'FIBER_CD': ('섬유 소재', 'Fiber Material'), 'CARE_SYMBOL_CD': ('세탁·취급 기호', 'Care Symbol'), 'MEASUREMENT_PART_CD': ('측정 부위', 'Measurement Part')}
# 새 그룹 (문서 순서 = 컬럼이 처음 나오는 순서)
G = []
for col, uses in USES.items():
    if col in REUSE: continue
    if col in FILE_CODES:
        fg = FILE_CODES[col]
        G.append((fg[0], fg[1], fg[2], ', '.join(f'`{t}.{c[0]}`' for t, c in uses) + ' 외 생산·소싱 도메인', 'N', [], [])); continue
    gc = GROUP_NAME.get(col, col[:-3])
    ko = re.sub(r'\s*코드$', '', uses[0][1][1]); en = re.sub(r'\s*Code$', '', uses[0][1][2])
    if col in JSON_NAME and not any(c[0] == col for _, c in uses): ko, en = JSON_NAME[col]
    at, av = ATTRS.get(col, ([], {}))
    vals = [(v[0], v[1], v[2], v[3], av.get(v[0], [''] * len(at))) for v in CODES[col]]
    G.append((gc, ko, en, ', '.join(f'`{t}.{c[0]}`' + (' (JSON 안의 값)' if c[0] in JSON_CODES else '') for t, c in uses), 'N' if all(c[0] in JSON_CODES for _, c in uses) else 'Y', at, vals))
    if col == 'SIZE_SYSTEM_CD':
        for gc2, ko2, en2, d2, vs in NEW_GROUPS_EXTRA:
            G.append((gc2, ko2, en2, d2 + ' · `PRD_SKU.SIZE_CD` 등', 'N', [], [(v[0], v[1], v[2], v[3], []) for v in vs]))
for gc2, ko2, en2, d2, at2, vs in POLICY_GROUPS:
    G.append((gc2, ko2, en2, d2, 'N', at2, [(v[0], v[1], v[2], v[3], v[4]) for v in vs]))
assert len({x[0] for x in G}) == len(G)
assert not ({x[0] for x in G} & set(MBR_IDS)), {x[0] for x in G} & set(MBR_IDS)
# 가상 ID: 회원 도메인 마지막 번호 다음 CACHE 20 블록부터 (V4 마이그레이션 가정)
def nxt_block(last, start, cache=20): return start + ((last - start) // cache + 1) * cache
MG = max(v['gid'] for v in MBR_IDS.values()); MC = max(max(v['codes'].values()) for v in MBR_IDS.values() if v['codes'])
g, c = nxt_block(MG, 1001), nxt_block(MC, 100001)
G0, C0 = g, c
GID, CODEID, FSTART = {}, {}, {}
for x in G:
    GID[x[0]] = g; g += 1
    if not x[6]:
        n = next(f[3] for f in FILE_CODES.values() if f[0] == x[0]); FSTART[x[0]] = c; c += n; continue
    for v in x[6]: CODEID[(x[0], v[0])] = c; c += 1
LG, LC = g - 1, c - 1
REUSED = [(gname, [col for col, gg in REUSE.items() if gg == gname]) for gname in sorted(set(REUSE.values()))]
SIZE_REUSE = ['TOP_SIZE', 'BOTTOM_SIZE', 'WAIST_SIZE', 'SHOE_SIZE']

def il(s):
    s = html.escape(str(s)); p = s.split('`')
    s = ''.join(f'<code>{x.replace("_", "_<wbr>").replace(".", ".<wbr>")}</code>' if i % 2 else x for i, x in enumerate(p))
    return re.sub(r'\[(확인 필요[^\]]*|제안[^\]]*|미정|가정)\]', r'<span class="warn">[\1]</span>', s)
def ln(ko, en): return f'{il(ko)} <span class="en" style="display:inline-block">({il(en)})</span>'
def pn(p): return html.escape(p).replace('_', '_<wbr>')
def th(p, ko): return f'<th><span class="pc">{pn(p)}</span><br><span class="en">{il(ko)}</span></th>'
CKS = '<td class="ck">☐</td><td class="memo"></td>'
CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css'), encoding='utf-8').read()

CONFIRM = [
 ('코드 그룹 이름', '새 그룹 이름은 컬럼 이름에서 `_CD`를 뺀 것이다. 판매 상태만 회원·주문 상태와 구분하려고 `PRODUCT_SALE_STATUS`로 했다.'),
 ('회원 문서 수정', '컬럼 검토 PC-14 A로 `FIT`, `TOP_SIZE`, `BOTTOM_SIZE`, `WAIST_SIZE`, `SHOE_SIZE`를 함께 쓴다. 회원 공통코드 문서에서 소유 도메인 `MBR` → `CMM`, 그룹 이름의 “평소” 삭제, 설명에 상품 컬럼 추가, `FIT` CHECK 적용 Y를 반영해야 한다 (지시 때).'),
 ('사이즈 값 범위', '회원 사이즈 그룹은 회원이 고르는 값 범위다. 상품 사이즈(예: XXS, 3XL, 빅사이즈)가 더 넓으면 값을 추가해야 한다.'),
 ('결정에 없던 값', '컬러 계열, 섬유 소재, 세탁 기호, 측정 부위, 박스 규격, 두께감·신축성·비침·안감 단계, 가격 변경 사유 값은 결정 항목이 아니었다.'),
 ('세탁 기호 목록', 'KS K ISO 3758 기호 전체와 대조해 확정해야 한다.'),
 ('추가 속성', '관계 유형의 양방향 여부, 측정 부위별 사이즈 체계, 사이즈 체계의 값 그룹을 `ATTR1`에 담는 방식.'),
]
body = ('<h1>공통코드 (CMM_CODE) — 상품 도메인 코드 (제안)</h1>'
        '<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-24 · 상품 도메인 결정 1~53, 컬럼 검토 G-1·M-1~M-13·PC-1~PC-86, 법률 검토 L13~L18 기준 · 테이블 구조는 회원 도메인 문서와 같다 (<code>공통코드_CMM_CODE_회원도메인.pdf</code> 1장) · 그룹과 값은 모두 제안</div>'
        f'<div class="box">새 코드 그룹 {len(G)}개 · 새 코드 값 {LC - C0 + 1 - sum(f[3] for f in FILE_CODES.values())}개 (국가 코드 파일 적재 제외) · 회원 도메인 그룹 재사용 {len(REUSED) + len(SIZE_REUSE)}개</div>'
        '<div class="box"><b>검토 방법</b><br>· 확정한 행은 확정 칸에 표시하고, 고칠 내용은 메모 칸에 적는다. 그룹은 <code>CODE_GROUP_ID</code>, 값은 <code>CODE_ID</code>로 알려 주면 된다.<br>'
        '· 코드 저장 방식 A (2026-11-22): 업무 테이블의 <code>_CD</code> 컬럼은 코드 문자열을 저장하고 FK는 걸지 않는다. CHECK 적용(Y) 그룹은 값을 업무 컬럼 CHECK에도 나열한다.<br>'
        '· 노란 행 / 빨간 표시: 결정 항목에 없던 제안이거나 확인이 필요한 것.<br>· 그룹 순서는 컬럼정의서의 테이블·컬럼 순서(지시 규칙 8)를 따른다.</div>')
body += '<h2>확인이 필요한 사항</h2><table><tr><th>No</th><th>항목</th><th>내용</th><th>확정</th><th>메모</th></tr>' + ''.join(
    f'<tr class="cf"><td class="n">Q{k}</td><td>{il(a)}</td><td>{il(b)}</td>{CKS}</tr>' for k, (a, b) in enumerate(CONFIRM, 1)) + '</table>'
# 1. 그룹
body += '<h2 class="g t">1. 상품 도메인 코드 그룹 (CMM_CODE_GROUP 행)</h2>'
body += ('<div class="box"><b>ID 값은 가상 값이다</b> <span class="warn">[가정]</span><br>'
         f'· 회원 도메인 코드(그룹 1001~{MG}, 값 100001~{MC})를 넣은 뒤, 상품 도메인 마이그레이션(V4 가정)이 DB 재시작 뒤 새 캐시 블록(CACHE 20)에서 번호를 받는다고 가정했다.<br>'
         f'· 결과: <code>CODE_GROUP_ID</code> {G0}~{LG}, <code>CODE_ID</code> {C0}~{LC}.</div>')
body += ('<table style="table-layout:fixed"><colgroup><col style="width:5%"><col style="width:16%"><col style="width:18%"><col style="width:6%"><col style="width:6%"><col style="width:11%"><col style="width:25%"><col style="width:4%"><col style="width:3%"><col style="width:6%"></colgroup><tr>'
         + th('CODE_GROUP_ID','그룹 ID') + th('CODE_GROUP_CD','그룹 코드') + th('CODE_GROUP_NM','한글 이름 (영문 이름)') + th('OWNER_DOMAIN_CD','소유 도메인')
         + th('CHECK_CONSTRAINT_YN','CHECK 적용') + th('ATTR1~5_NM','추가 속성 의미') + th('CODE_GROUP_DESC','설명 (쓰는 컬럼)') + th('USE_YN','사용') + '<th>확정</th><th>메모</th></tr>')
for gc, ko, en, cols, ck, attrs, vals in G:
    body += (f'<tr><td class="n">{GID[gc]}</td><td class="p">{pn(gc)}</td><td>{ln(ko, en)}</td><td class="ty">{next((f[4] for f in FILE_CODES.values() if f[0] == gc), None) or ("MBR" if all(u.startswith("`MBR_") for u in cols.split(", ")) else "PRD")}</td><td class="n">{ck}</td>'
             f'<td>{"<br>".join(f"ATTR{i+1}_NM: {il(x)}" for i, x in enumerate(attrs))}</td><td>{il(cols)}</td><td class="n">Y</td>{CKS}</tr>')
body += '</table>'
# 2. 재사용
body += '<div style="page-break-inside:avoid"><h2>2. 회원 도메인 그룹 재사용 (새 행 없음)</h2><table style="table-layout:fixed"><colgroup><col style="width:6%"><col style="width:12%"><col style="width:44%"><col style="width:27%"><col style="width:4%"><col style="width:7%"></colgroup><tr><th>그룹 ID</th><th>그룹 코드</th><th>상품 도메인에서 쓰는 곳</th><th>회원 문서에서 바꾼 것</th><th>확정</th><th>메모</th></tr>'
for gname, cols in REUSED:
    body += f'<tr class="cf"><td class="n">{MBR_IDS[gname]["gid"]}</td><td class="p">{gname}</td><td>{il(", ".join(f"`PRD_STYLE.{c}`" for c in cols))}</td><td>소유 도메인 <code>CMM</code>, CHECK 적용 Y (PC-14 A, 2026-11-24 회원 공통코드 문서에 반영)</td>{CKS}</tr>'
for gname in SIZE_REUSE:
    body += f'<tr class="cf"><td class="n">{MBR_IDS[gname]["gid"]}</td><td class="p">{gname}</td><td>사이즈 체계 <code>{gname}</code>인 분류의 <code>PRD_SKU.SIZE_CD</code>, <code>PRD_STYLE_COLOR.FITTING_SIZE_CD</code>, <code>PRD_STYLE.SIZE_MEASUREMENT_JSON</code>의 사이즈 키</td><td>소유 도메인 <code>CMM</code>, 그룹 이름에서 “평소” 삭제 (PC-14 A). 값을 넓히고(상의·하의 XXS·3XL, 허리 41~44인치, 신발 210·215·305·310mm) “회원 선택 가능 여부” 속성(상의·하의 ATTR1, 허리·신발 ATTR2)으로 회원 화면 노출을 구분 (R-7 C). 2026-11-24 회원 공통코드 문서에 반영</td>{CKS}</tr>'
body += '</table></div>'
# 3. 값
body += '<h2 class="g t">3. 코드 값 (CMM_CODE 행)</h2>'
for gc, ko, en, cols, ck, attrs, vals in G:
    nA = len(attrs); w = 37 - 8 * nA
    if gc in FSTART:
        body += f'<div><h3>CODE_GROUP_ID {GID[gc]} · {gc} — {il(ko)} <span style="font-weight:400;color:#666">· CHECK {ck}</span></h3><p>ISO 3166-1 alpha-2 국가 코드를 파일로 적재한다 (컬럼 검토 PC-15 A). 값은 문서에 나열하지 않는다. <code>CODE_ID</code> {FSTART[gc]}~{FSTART[gc]+249} 차지 <span class="warn">[가정]</span>.</p></div>'; continue
    body += f'<div style="page-break-inside:avoid"><h3>CODE_GROUP_ID {GID[gc]} · {gc} — {il(ko)} <span style="font-weight:400;color:#666">· CHECK {ck}</span></h3>'
    body += ('<table style="table-layout:fixed"><colgroup><col style="width:6%"><col style="width:7%"><col style="width:16%"><col style="width:18%">' + f'<col style="width:{w}%">' + ''.join('<col style="width:8%">' for _ in attrs) +
             '<col style="width:5%"><col style="width:4%"><col style="width:3%"><col style="width:4%"></colgroup><tr>'
             + th('CODE_ID','코드 ID') + th('CODE_GROUP_ID','그룹 ID') + th('CODE_CD','코드 값') + th('CODE_NM','한글 이름 (영문 이름)') + th('CODE_DESC','설명')
             + ''.join(th(f'ATTR{i+1}_VAL', a) for i, a in enumerate(attrs)) + th('SORT_SN','정렬') + th('USE_YN','사용') + '<th>확정</th><th>메모</th></tr>')
    for vi, (cd, k, e, d, av) in enumerate(vals, 1):
        cf = ' class="cf"' if '[확인' in d else ''
        body += (f'<tr{cf}><td class="n">{CODEID[(gc, cd)]}</td><td class="n">{GID[gc]}</td><td class="p">{pn(cd)}</td><td>{ln(k, e)}</td><td>{il(d)}</td>'
                 + ''.join(f'<td class="p">{pn(a)}</td>' for a in av) + f'<td class="n">{vi}</td><td class="n">Y</td>{CKS}</tr>')
    body += '</table></div>'
open(OUT, 'w', encoding='utf-8').write(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>CMM_CODE 상품 도메인 코드</title><style>{CSS}</style></head><body>{body}</body></html>')
ids = {gc: {'gid': GID[gc], 'codes': {v[0]: CODEID[(gc, v[0])] for v in vals}} for gc, ko, en, cols, ck, attrs, vals in G if gc not in FSTART}
for gname, _ in REUSED: ids[gname] = MBR_IDS[gname]
json.dump({'groups': ids, 'col_group': {col: (REUSE.get(col) or GROUP_NAME.get(col, col[:-3])) for col in CODES}},
          open(os.path.join(os.path.dirname(os.path.abspath(OUT)), 'code_ids_prd.json'), 'w'), ensure_ascii=False)
print('groups', len(G), 'values', LC - C0 + 1, 'gid', G0, LG, 'cid', C0, LC)
