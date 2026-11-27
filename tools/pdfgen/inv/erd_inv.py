# 재고 도메인 관계 요약 ERD (컬럼 없이 테이블과 관계만, dlv/erd_dlv.py와 같은 구조). tools/pdfgen/erd/erd.py가 불러 mmd 파일과 draw.io 페이지를 만든다.
# 단일 출처: tools/pdfgen/inv/data.py (재고 테이블·FK). FK 예정 참조(WMS 마스터)는 REF, FK 없이 둔 참조(다른 도메인 ID 2-4 A, 예외의 확보 ID T-1 A, 정정의 원래 원장 ID T-6 B)는 그리지 않는다.
import os, re, html, importlib.util
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

O = _load('inv_data_for_erd', os.path.join(HERE, 'data.py'))
GROUPS = O.TABLE_GROUPS
BY = {t['t']: t for t in O.T}
assert sorted(n for g, ns in GROUPS for n in ns) == sorted(BY)

def _fk(c):
    m = re.search(r'FK → `([A-Z_]+)`', c[6]); return m.group(1) if m else None
def _cols(t): return [c for g, x in t['cols'] for c in x]

# 관계: (자식, FK 컬럼, 부모, 필수 여부, 1:1 여부)
RELS = []
for t in O.T:
    for c in _cols(t):
        p = _fk(c)
        # 1:1은 PK가 이 FK 하나뿐일 때(공유 PK)만. 복합 PK의 한 컬럼은 1:N이다.
        pks = [x for x in _cols(t) if re.search(r'\bPK\d*\b', x[6])]
        if p: RELS.append((t['t'], c[0], p, c[4] == 'N', len(pks) == 1 and pks[0][0] == c[0]))
# FK 미정 참조 (다른 도메인 테이블이 정해지면 FK): (자식, 컬럼, 대상 후보)
REF = [('INV_STOCK', 'WAREHOUSE_ID', 'WMS_WAREHOUSE'), ('INV_STOCK', 'NON_SALE_ITEM_ID', 'WMS_NON_SALE_ITEM')]
for ch, col, p in REF:
    assert any(c[0] == col for c in _cols(BY[ch])), (ch, col)
EXT = sorted({r[2] for r in RELS if r[2] not in BY} | {r[2] for r in REF})
CONFIRMED_EXT = {'PRD_SKU'}
DOM = {'PRD': '상품 도메인', 'WMS': '창고 도메인'}
def ext_note(n): return DOM[n.split('_')[0]] + ('' if n in CONFIRMED_EXT else ', 이름 후보')

def short_ko(n): return BY[n]['ko'].split(' (')[0]
def esc(s): return html.escape(s, quote=True)

def mmd_summary():
    L = ['---', 'title: 재고 도메인 (INV) 관계 요약', '---',
         f'%% 생성: tools/pdfgen/erd/erd.py → tools/pdfgen/inv/erd_inv.py ({TODAY}). 컬럼 없이 테이블과 관계만 그렸다. 테이블 이름은 T-10 A로 확정. FK 없이 두는 참조(다른 도메인 ID 2-4 A, 재고 예외의 확보 ID T-1 A, 정정의 원래 원장 ID T-6 B)는 그리지 않았다',
         '%% 표기: ||--o{ 필수 1:N, |o--o{ 선택(NULL 허용 FK) 1:N, |o..o{ FK 예정 참조(WMS 테이블이 정해지면 FK). 선 이름은 컬럼',
         '%% 다른 도메인 상자: 상품·창고 (창고는 후보)',
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
    for ch, col, p, req, one in RELS:
        L.append(f'    {p} {"||" if req else "|o"}--{"o|" if one else "o{"} {ch} : "{col}"')
    L.append('    %% ---- FK 예정 참조')
    for ch, col, p in REF:
        L.append(f'    {p} |o..o{{ {ch} : "{col} (FK 예정)"')
    return '\n'.join(L) + '\n'

SW, SH = 320, 58
GRP_COLOR = ['#dae8fc|#6c8ebf', '#d5e8d4|#82b366', '#fff2cc|#d6b656', '#f8cecc|#b85450', '#e1d5e7|#9673a6', '#ffe6cc|#d79b00']
Y0 = 200
POS = {k: (x, y + Y0, w, h) for k, (x, y, w, h) in {
    # 다른 도메인 (왼쪽): 현재고의 창고·품목
    'WMS_WAREHOUSE': (-260, 200, SW, SH), 'PRD_SKU': (-260, 336, SW, SH), 'WMS_NON_SALE_ITEM': (-260, 472, SW, SH),
    # 가운데: 현재고. 오른쪽 첫 줄: 현재고를 가리키는 원장·확보·스냅샷. 둘째 줄: 예외·입고 예정
    'INV_STOCK': (300, 320, 360, 90),
    'INV_STOCK_LEDGER': (900, 160, SW, SH), 'INV_STOCK_COMMITMENT': (900, 336, SW, SH), 'INV_STOCK_COMMITMENT_EVENT': (900, 560, SW, SH), 'INV_STOCK_SNAPSHOT': (900, 760, SW, SH),
    'INV_STOCK_EXCEPTION': (1500, 160, SW, SH), 'INV_INBOUND_PLAN': (1500, 336, SW, SH),
    'INV_MONTHLY_CLOSING': (1500, 760, SW, SH),
}.items()}
# 꺾는 선 (좌표는 Y0를 더한 절대 좌표): (자식, 부모[, 컬럼]) → (꺾는 점, 나가고 들어가는 위치[, 선 이름 거리]).
ROUTE = {
    ('INV_STOCK_LEDGER', 'INV_STOCK'): ([(800, 389), (800, 545)], 'exitX=0;exitY=0.5;entryX=1;entryY=0.25;'),
    ('INV_STOCK_COMMITMENT', 'INV_STOCK'): ([], 'exitX=0;exitY=0.5;entryX=1;entryY=0.5;'),
    ('INV_STOCK_SNAPSHOT', 'INV_STOCK'): ([(800, 989), (800, 590)], 'exitX=0;exitY=0.5;entryX=1;entryY=0.75;'),
    ('INV_STOCK_LEDGER', 'INV_STOCK_EXCEPTION'): ([], 'exitX=1;exitY=0.5;entryX=0;entryY=0.5;'),
    ('INV_STOCK_LEDGER', 'INV_INBOUND_PLAN'): ([(1400, 406), (1400, 551)], 'exitX=1;exitY=0.8;entryX=0;entryY=0.25;', (0.4, -10)),
    ('INV_STOCK_COMMITMENT', 'INV_INBOUND_PLAN'): ([], 'exitX=1;exitY=0.65;entryX=0;entryY=0.65;', 10),
    ('INV_STOCK_EXCEPTION', 'INV_INBOUND_PLAN'): ([], 'exitX=0.5;exitY=1;entryX=0.5;entryY=0;'),
    ('INV_STOCK_EXCEPTION', 'INV_STOCK'): ([(1660, 300), (480, 300)], 'exitX=0.5;exitY=0;entryX=0.5;entryY=0;'),
    ('INV_INBOUND_PLAN', 'INV_STOCK'): ([(1900, 565), (1900, 1080), (480, 1080)], 'exitX=1;exitY=0.5;entryX=0.5;entryY=1;', (0.6, -10)),
    ('INV_STOCK_COMMITMENT_EVENT', 'INV_STOCK_COMMITMENT'): ([], 'exitX=0.5;exitY=0;entryX=0.5;entryY=1;'),
    ('INV_STOCK_COMMITMENT_EVENT', 'INV_INBOUND_PLAN', 'FROM_INBOUND_PLAN_ID'): ([(1596, 779)], 'exitX=1;exitY=0.33;entryX=0.3;entryY=1;', (0.75, 0)),
    ('INV_STOCK_COMMITMENT_EVENT', 'INV_INBOUND_PLAN', 'TO_INBOUND_PLAN_ID'): ([(1724, 799)], 'exitX=1;exitY=0.67;entryX=0.7;entryY=1;', (0.75, 0)),
    ('INV_STOCK', 'PRD_SKU'): ([], 'exitX=0;exitY=0.5;entryX=1;entryY=0.5;'),
    ('INV_STOCK', 'WMS_WAREHOUSE'): ([(200, 545), (200, 429)], 'exitX=0;exitY=0.25;entryX=1;entryY=0.5;'),
    ('INV_STOCK', 'WMS_NON_SALE_ITEM'): ([(200, 590), (200, 701)], 'exitX=0;exitY=0.75;entryX=1;entryY=0.5;'),
}
def pts(ch, p, col=None):
    """꺾는 점, 나가고 들어가는 위치, 선 이름 위치. ROUTE 값 3번째 항목은 선 이름 거리(px, 위 -, 아래 +) 또는 (선 위 위치, 거리)."""
    r = ROUTE.get((ch, p, col)) or ROUTE.get((ch, p))
    if not r: return '', '', ''
    ps, extra = r[0], r[1]
    lab = ''
    if len(r) > 2:  # 숫자면 선에서 떨어뜨리는 거리, (x, y)면 x는 선 위 위치(-1 시작 ~ 1 끝)
        lx, ly = r[2] if isinstance(r[2], tuple) else (None, r[2])
        lab = (f' x="{lx}"' if lx is not None else '') + f' y="{ly}"'
    return ('<Array as="points">' + ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in ps) + '</Array>' if ps else ''), extra, lab

def summary_cells():
    cells, nid = [], [0]
    def new(prefix):
        nid[0] += 1; return f'p{prefix}{nid[0]}'
    missing = (set(BY) | set(EXT)) - set(POS)
    assert not missing, missing
    grp = {n: gi for gi, (g, ns) in enumerate(GROUPS) for n in ns}
    cells.append(f'<mxCell id="ptitle" value="{esc("재고 도메인 (INV) 관계 요약")}" style="text;html=1;fontSize=22;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="-260" y="140" width="900" height="40" as="geometry"/></mxCell>')
    note = (f'생성: tools/pdfgen/erd/erd.py → inv/erd_inv.py ({TODAY}) · 재고 테이블 {len(BY)}개, 이름은 T-10 A로 확정 · 컬럼 없이 테이블과 관계만 표시 · FK 없이 두는 참조(다른 도메인 ID 2-4 A, 예외의 확보 ID T-1 A, 정정의 원래 원장 ID T-6 B)는 그리지 않음 · 상자 색 = 테이블 그룹 · '
            '선 이름 = FK 컬럼 · 실선 = 필수 FK, 점선 = NULL 허용 FK · 까마귀발 = N 쪽 · 회색 점선 상자 = 다른 도메인 · 회색 가는 점선 = FK 예정 참조 (WMS 테이블이 정해지면 FK)')
    cells.append(f'<mxCell id="pnote" value="{esc(note)}" style="text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="-260" y="180" width="2200" height="30" as="geometry"/></mxCell>')
    lx = -260
    for gi, (g, ns) in enumerate(GROUPS):
        fill, stroke = GRP_COLOR[gi % len(GRP_COLOR)].split('|')
        cells.append(f'<mxCell id="{new("l")}" value="{esc(g)}" style="rounded=1;html=1;fontSize=11;fillColor={fill};strokeColor={stroke};" vertex="1" parent="1"><mxGeometry x="{lx}" y="1000" width="150" height="28" as="geometry"/></mxCell>')
        lx += 170
    vid = {}
    for n in list(BY) + EXT:
        x, y, w, h = POS[n]
        vid[n] = new('t')
        if n in BY:
            fill, stroke = GRP_COLOR[grp[n] % len(GRP_COLOR)].split('|')
            big = n in ('INV_STOCK',)
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(short_ko(n))}</span>'
            st = f'rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={14 if big else 12};' + ('strokeWidth=2;' if big else '')
        else:
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(ext_note(n))}</span>'
            st = 'rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#999999;fontColor=#555555;fontSize=12;'
        cells.append(f'<mxCell id="{vid[n]}" value="{esc(label)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    merged = {}
    for ch, col, p, req, one in RELS:  # 같은 (자식, 부모) FK는 선 하나로 합친다. ROUTE에 (자식, 부모, 컬럼) 키가 있으면 따로 그린다.
        k = (ch, p, col) if (ch, p, col) in ROUTE else (ch, p, None)
        m = merged.setdefault(k, [[], False, False]); m[0].append(col); m[1] = m[1] or req; m[2] = m[2] or one
    base = 'endFill=0;startFill=0;html=1;fontSize=9;fontColor=#444444;labelBackgroundColor=#ffffff;'
    for (ch, p, kc), (cols, req, one) in merged.items():
        end = 'ERmandOne' if req else 'ERzeroToOne'
        start = 'ERzeroToOne' if one else 'ERmany'
        st = '' if req else 'dashed=1;'
        pt, extra, lab = pts(ch, p, kc)
        cells.append(f'<mxCell id="{new("e")}" value="{esc(" / ".join(cols))}" style="endArrow={end};startArrow={start};{base}strokeColor=#666666;{st}{extra}" edge="1" parent="1" source="{vid[ch]}" target="{vid[p]}"><mxGeometry relative="1"{lab} as="geometry">{pt}</mxGeometry></mxCell>')
    for ch, col, p in REF:
        pt, extra, lab = pts(ch, p)
        cells.append(f'<mxCell id="{new("r")}" value="{esc(col + " (FK 예정)")}" style="endArrow=ERzeroToOne;startArrow=ERmany;{base}strokeColor=#aaaaaa;dashed=1;dashPattern=2 4;{extra}" edge="1" parent="1" source="{vid[ch]}" target="{vid[p]}"><mxGeometry relative="1"{lab} as="geometry">{pt}</mxGeometry></mxCell>')
    return cells
