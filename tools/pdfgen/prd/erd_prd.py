# 상품 도메인 관계 요약 ERD (컬럼 없이 테이블과 관계만). tools/pdfgen/erd/erd.py가 불러 mmd 파일과 draw.io 페이지를 만든다.
# 단일 출처: tools/pdfgen/prd/data.py (상품 테이블·FK), tools/pdfgen/cols/data.py (상품을 참조하는 회원 테이블의 FK)
import os, re, html, importlib.util
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

P = _load('prd_data_for_erd', os.path.join(HERE, 'data.py'))
M = _load('mbr_data_for_erd', os.path.join(HERE, '..', 'cols', 'data.py'))

# 상품 테이블 (회원 도메인으로 옮긴 재입고 알림 신청은 회원 쪽 다른 도메인 상자로 그린다)
GROUPS = [(g, ns) for g, ns in P.TABLE_GROUPS if all(n.startswith('PRD_') for n in ns)]
BY = {t['t']: t for t in P.T if t['t'].startswith('PRD_')}
assert sorted(n for g, ns in GROUPS for n in ns) == sorted(BY)

def _fk(c):
    m = re.search(r'FK → `([A-Z_]+)`', c[6]); return m.group(1) if m else None

def _cols(t):
    cs = t['cols']
    return [c for g, x in cs for c in x] if cs and isinstance(cs[0][1], list) else cs

# 관계: (자식, FK 컬럼, 부모, 필수 여부)
RELS = []
for t in P.T:
    if not t['t'].startswith('PRD_'): continue
    for c in _cols(t):
        p = _fk(c)
        if p: RELS.append((t['t'], c[0], p, c[4] == 'N'))
for t in M.T:  # 상품 테이블을 참조하는 회원 테이블
    for c in _cols(t):
        p = _fk(c)
        if p in BY: RELS.append((t['t'], c[0], p, c[4] == 'N'))
EXT = sorted({x for r in RELS for x in (r[0], r[2]) if x not in BY})
EXT_NOTE = {'ADM_USER': '관리자 도메인'}
def ext_note(n): return EXT_NOTE.get(n, '회원 도메인' if n.startswith('MBR_') else '다른 도메인')
NO_FK = {'PRD_SEARCH_INDEX_OUTBOX': 'STYLE_ID는 FK 없음 (이벤트 로그)'}

def short_ko(n): return BY[n]['ko'].split(' (')[0]
def esc(s): return html.escape(s, quote=True)

def mmd_summary():
    L = ['---', 'title: 상품 도메인 (PRD) 관계 요약', '---',
         f'%% 생성: tools/pdfgen/erd/erd.py → tools/pdfgen/prd/erd_prd.py ({TODAY}). 컬럼 없이 테이블과 관계만 그렸다. 테이블 이름은 모두 후보',
         '%% 표기: ||--o{ 필수 1:N, |o--o{ 선택(NULL 허용 FK) 1:N. 선 이름은 FK 컬럼',
         '%% 다른 도메인 상자: 상품을 참조하는 회원 테이블(확정 이름, 재입고 알림 신청은 후보)과 관리자 도메인(후보)',
         'erDiagram']
    for g, ns in GROUPS:
        L.append(f'    %% ---- {g}')
        for n in ns:
            L.append(f'    {n}["{n} {short_ko(n)}"] {{')
            L.append('    }')
    L.append('    %% ---- 다른 도메인')
    for e in EXT:
        L.append(f'    {e}["{e} ({ext_note(e)})"] {{')
        L.append('    }')
    L.append('    %% ---- 관계')
    for ch, col, p, req in RELS:
        L.append(f'    {p} {"||" if req else "|o"}--o{{ {ch} : "{col}"')
    for n, why in NO_FK.items():
        L.append(f'    %% {n}: {why}')
    return '\n'.join(L) + '\n'

SW, SH = 300, 58
GRP_COLOR = ['#dae8fc|#6c8ebf', '#d5e8d4|#82b366', '#fff2cc|#d6b656', '#e1d5e7|#9673a6', '#f8cecc|#b85450', '#ffe6cc|#d79b00']
POS = {
    'PRD_STYLE': (1100, 560, 340, 90), 'PRD_STYLE_COLOR': (1120, 860, SW, SH), 'PRD_SKU': (1120, 1120, SW, SH),
    'PRD_BRAND': (450, 380, SW, SH), 'PRD_SEASON': (450, 520, SW, SH), 'PRD_CATEGORY': (450, 660, SW, SH), 'PRD_COLOR': (450, 860, SW, SH),
    'PRD_STYLE_FABRIC': (1850, 180, SW, SH), 'PRD_STYLE_FUNCTIONAL_CLAIM': (1850, 320, SW, SH), 'PRD_PRICE_HIST': (1850, 460, SW, SH), 'PRD_PRICE_CHANGE_REQUEST': (2450, 460, SW, SH),
    'PRD_STYLE_RELATION': (1850, 600, SW, SH), 'PRD_DISPLAY_CONTENT_HIST': (1850, 740, SW, SH), 'PRD_STYLE_MEDIA': (1850, 900, SW, SH),
    'PRD_FABRIC': (2450, 180, SW, SH), 'PRD_SALES_DAILY_STAT': (1850, 1120, SW, SH), 'PRD_SEARCH_INDEX_OUTBOX': (1850, 1300, SW, 70),
    'ADM_USER': (2450, 320, SW, SH), 'MBR_PREFERENCE': (-150, 660, SW, SH),
    'MBR_WISHLIST_ITEM': (450, 1010, SW, SH), 'MBR_RECENTLY_VIEWED_ITEM': (450, 1150, SW, SH),
    'MBR_RESTOCK_NOTIFICATION_REQUEST': (450, 1290, SW, SH)
}

# 다른 선을 가로지르지 않게 꺾어 그리는 관계: (자식, 부모) → (꺾는 점, 추가 스타일)
ROUTE = {
    ('PRD_STYLE', 'ADM_USER'): ([(1270, 100), (2820, 100), (2820, 349)], 'exitX=0.5;exitY=0;entryX=1;entryY=0.5;'),
    ('PRD_PRICE_HIST', 'PRD_SKU'): ([(2300, 489), (2300, 1060), (1380, 1060)], 'exitX=1;exitY=0.5;entryX=0.867;entryY=0;'),
}

def summary_cells():
    cells, nid = [], [0]
    def new(prefix):
        nid[0] += 1; return f'p{prefix}{nid[0]}'
    missing = (set(BY) | set(EXT)) - set(POS)
    assert not missing, missing
    grp = {n: gi for gi, (g, ns) in enumerate(GROUPS) for n in ns}
    cells.append(f'<mxCell id="ptitle" value="{esc("상품 도메인 (PRD) 관계 요약")}" style="text;html=1;fontSize=22;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="-150" y="0" width="900" height="40" as="geometry"/></mxCell>')
    note = (f'생성: tools/pdfgen/erd/erd.py → prd/erd_prd.py ({TODAY}) · 상품 테이블 {len(BY)}개, 이름은 모두 후보 · 컬럼 없이 테이블과 관계만 표시 · 상자 색 = 테이블 그룹 · '
            '선 이름 = FK 컬럼 · 실선 = 필수 FK, 점선 = NULL 허용 FK · 까마귀발 = N 쪽 · 회색 점선 상자 = 다른 도메인')
    cells.append(f'<mxCell id="pnote" value="{esc(note)}" style="text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="-150" y="40" width="2900" height="30" as="geometry"/></mxCell>')
    lx = -150
    for gi, (g, ns) in enumerate(GROUPS):
        fill, stroke = GRP_COLOR[gi % len(GRP_COLOR)].split('|')
        cells.append(f'<mxCell id="{new("l")}" value="{esc(g)}" style="rounded=1;html=1;fontSize=11;fillColor={fill};strokeColor={stroke};" vertex="1" parent="1"><mxGeometry x="{lx}" y="1480" width="150" height="28" as="geometry"/></mxCell>')
        lx += 170
    vid = {}
    for n in list(BY) + EXT:
        x, y, w, h = POS[n]
        vid[n] = new('t')
        if n in BY:
            fill, stroke = GRP_COLOR[grp[n] % len(GRP_COLOR)].split('|')
            sub = short_ko(n) + (f'<br><i>{esc(NO_FK[n])}</i>' if n in NO_FK else '')
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(short_ko(n)) if n not in NO_FK else sub}</span>'
            st = f'rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={14 if n == "PRD_STYLE" else 12};' + ('strokeWidth=2;' if n == 'PRD_STYLE' else '')
        else:
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(ext_note(n))}</span>'
            st = 'rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#999999;fontColor=#555555;fontSize=12;'
        cells.append(f'<mxCell id="{vid[n]}" value="{esc(label)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    merged = {}
    for ch, col, p, req in RELS:
        m = merged.setdefault((ch, p), [[], False]); m[0].append(col); m[1] = m[1] or req
    for (ch, p), (cols, req) in merged.items():
        end = 'ERmandOne' if req else 'ERzeroToOne'
        st = '' if req else 'dashed=1;'
        pts = ''
        if ch == p:  # 자기 참조 (첫 세대 스타일)
            x, y, w, h = POS[ch]
            pts = f'<Array as="points"><mxPoint x="{x + w + 60}" y="{y + h / 2:.0f}"/><mxPoint x="{x + w + 60}" y="{y - 50}"/><mxPoint x="{x + w - 60}" y="{y - 50}"/></Array>'
            st += 'edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.5;entryX=0.8;entryY=0;'
        elif (ch, p) in ROUTE:
            ps, extra = ROUTE[(ch, p)]
            pts = '<Array as="points">' + ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in ps) + '</Array>'
            st += extra
        elif (p, ch) in merged and ch in ('PRD_STYLE', 'PRD_STYLE_COLOR'):  # 스타일이 참조하는 쪽(현재 적용 가격 행)은 휘게
            x1, y1, w1, h1 = POS[ch]; x2, y2, w2, h2 = POS[p]
            cx, cy = (x1 + w1 / 2 + x2 + w2 / 2) / 2, (y1 + h1 / 2 + y2 + h2 / 2) / 2
            pts = f'<Array as="points"><mxPoint x="{cx:.0f}" y="{cy - 70:.0f}"/></Array>'
            st += 'curved=1;'
        cells.append(f'<mxCell id="{new("e")}" value="{esc(" / ".join(cols))}" style="endArrow={end};startArrow=ERmany;endFill=0;startFill=0;html=1;fontSize=9;fontColor=#444444;labelBackgroundColor=#ffffff;strokeColor=#666666;{st}" edge="1" parent="1" source="{vid[ch]}" target="{vid[p]}"><mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')
    return cells
