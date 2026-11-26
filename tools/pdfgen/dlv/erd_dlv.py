# 배송 도메인 관계 요약 ERD (컬럼 없이 테이블과 관계만, pay/erd_pay.py와 같은 구조). tools/pdfgen/erd/erd.py가 불러 mmd 파일과 draw.io 페이지를 만든다.
# 단일 출처: tools/pdfgen/dlv/data.py (배송 테이블·FK). FK 예정 참조(WMS 마스터)는 REF, 결정으로 FK 없이 둔 값 참조(주문·클레임 ID, 5-1 B)는 그리지 않는다.
import os, re, html, importlib.util
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

O = _load('dlv_data_for_erd', os.path.join(HERE, 'data.py'))
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
        if p: RELS.append((t['t'], c[0], p, c[4] == 'N', 'PK' in c[6]))
# FK 미정 참조 (다른 도메인 테이블이 정해지면 FK): (자식, 컬럼, 대상 후보)
REF = [('DLV_SHIPMENT_REQUEST', 'WAREHOUSE_ID', 'WMS_WAREHOUSE'), ('DLV_SHIPMENT', 'WAREHOUSE_ID', 'WMS_WAREHOUSE'), ('DLV_SHIPMENT_REQUEST_ITEM', 'NON_SALE_ITEM_ID', 'WMS_NON_SALE_ITEM')]
for ch, col, p in REF:
    assert any(c[0] == col for c in _cols(BY[ch])), (ch, col)
EXT = sorted({r[2] for r in RELS if r[2] not in BY} | {r[2] for r in REF})
CONFIRMED_EXT = set()
DOM = {'PRD': '상품 도메인', 'SYS': '시스템 도메인', 'WMS': '창고 도메인'}
def ext_note(n): return DOM[n.split('_')[0]] + ('' if n in CONFIRMED_EXT else ', 이름 후보')

def short_ko(n): return BY[n]['ko'].split(' (')[0]
def esc(s): return html.escape(s, quote=True)

def mmd_summary():
    L = ['---', 'title: 배송 도메인 (DLV) 관계 요약', '---',
         f'%% 생성: tools/pdfgen/erd/erd.py → tools/pdfgen/dlv/erd_dlv.py ({TODAY}). 컬럼 없이 테이블과 관계만 그렸다. 테이블 이름은 모두 후보. FK 없이 값만 두는 참조(주문·클레임 ID, 5-1 B, 로그의 출고 요청·패키지 ID, 추적 이벤트의 정정 대상)는 그리지 않았다',
         '%% 표기: ||--o{ 필수 1:N, |o--o{ 선택(NULL 허용 FK) 1:N, |o..o{ FK 예정 참조(WMS 테이블이 정해지면 FK). 선 이름은 컬럼',
         '%% 다른 도메인 상자: 상품·시스템·창고 (모두 후보)',
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
    # 다른 도메인 (왼쪽·오른쪽)
    'WMS_WAREHOUSE': (-260, 420, SW, SH), 'PRD_SKU': (-260, 620, SW, SH), 'WMS_NON_SALE_ITEM': (-260, 760, SW, SH),
    'SYS_EXTERNAL_VENDOR': (1980, 250, SW, SH),
    # 출고 요청·출고, 이력
    'DLV_STATUS_HIST': (300, 120, SW, SH), 'DLV_SHIPMENT_REQUEST': (300, 420, 360, 90), 'DLV_SHIPMENT_REQUEST_ITEM': (300, 620, SW, SH),
    'DLV_SHIPMENT': (860, 250, SW, SH),
    # 패키지·추적·사고
    'DLV_PARCEL': (860, 420, 360, 90), 'DLV_PARCEL_ITEM': (860, 620, SW, SH),
    'DLV_TRACKING_EVENT': (1420, 520, SW, SH), 'DLV_PARCEL_ACCIDENT': (1420, 680, SW, SH),
    # 기준 데이터, 연동
    'DLV_REMOTE_AREA_POSTCODE': (1420, 120, SW, SH), 'DLV_COURIER_RATE': (1420, 250, SW, SH),
    'DLV_COURIER_INTERFACE_LOG': (1980, 520, SW, SH),
}.items()}
# 꺾는 선 (좌표는 Y0를 더한 절대 좌표): (자식, 부모) → (꺾는 점, 나가고 들어가는 위치). 패키지 재발번 자기 참조는 위쪽 고리로 그린다.
ROUTE = {
    ('DLV_PARCEL', 'DLV_PARCEL'): ([(1130, 590), (1250, 590), (1250, 665)], 'exitX=0.75;exitY=0;entryX=1;entryY=0.5;'),
    ('DLV_SHIPMENT_REQUEST', 'DLV_PARCEL_ACCIDENT'): ([(250, 665), (250, 1080), (1580, 1080)], 'exitX=0;exitY=0.5;entryX=0.5;entryY=1;'),
    ('DLV_SHIPMENT', 'WMS_WAREHOUSE'): ([(-100, 479)], 'exitX=0;exitY=0.5;entryX=0.5;entryY=0;'),
}
def pts(ch, p):
    if (ch, p) not in ROUTE: return '', ''
    ps, extra = ROUTE[(ch, p)]
    return '<Array as="points">' + ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in ps) + '</Array>', extra

def summary_cells():
    cells, nid = [], [0]
    def new(prefix):
        nid[0] += 1; return f'p{prefix}{nid[0]}'
    missing = (set(BY) | set(EXT)) - set(POS)
    assert not missing, missing
    grp = {n: gi for gi, (g, ns) in enumerate(GROUPS) for n in ns}
    cells.append(f'<mxCell id="ptitle" value="{esc("배송 도메인 (DLV) 관계 요약")}" style="text;html=1;fontSize=22;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="-260" y="140" width="900" height="40" as="geometry"/></mxCell>')
    note = (f'생성: tools/pdfgen/erd/erd.py → dlv/erd_dlv.py ({TODAY}) · 배송 테이블 {len(BY)}개, 이름은 모두 후보 · 컬럼 없이 테이블과 관계만 표시 · FK 없이 값만 두는 참조(주문·클레임 ID 5-1 B, 로그·정정 이벤트 ID)는 그리지 않음 · 상자 색 = 테이블 그룹 · '
            '선 이름 = FK 컬럼 · 실선 = 필수 FK, 점선 = NULL 허용 FK · 까마귀발 = N 쪽 · 회색 점선 상자 = 다른 도메인 · 회색 가는 점선 = FK 예정 참조 (WMS 테이블이 정해지면 FK)')
    cells.append(f'<mxCell id="pnote" value="{esc(note)}" style="text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="-260" y="180" width="2760" height="30" as="geometry"/></mxCell>')
    lx = -260
    for gi, (g, ns) in enumerate(GROUPS):
        fill, stroke = GRP_COLOR[gi % len(GRP_COLOR)].split('|')
        cells.append(f'<mxCell id="{new("l")}" value="{esc(g)}" style="rounded=1;html=1;fontSize=11;fillColor={fill};strokeColor={stroke};" vertex="1" parent="1"><mxGeometry x="{lx}" y="1360" width="150" height="28" as="geometry"/></mxCell>')
        lx += 170
    vid = {}
    for n in list(BY) + EXT:
        x, y, w, h = POS[n]
        vid[n] = new('t')
        if n in BY:
            fill, stroke = GRP_COLOR[grp[n] % len(GRP_COLOR)].split('|')
            big = n in ('DLV_SHIPMENT_REQUEST', 'DLV_PARCEL')
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(short_ko(n))}</span>'
            st = f'rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={14 if big else 12};' + ('strokeWidth=2;' if big else '')
        else:
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(ext_note(n))}</span>'
            st = 'rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#999999;fontColor=#555555;fontSize=12;'
        cells.append(f'<mxCell id="{vid[n]}" value="{esc(label)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    merged = {}
    for ch, col, p, req, one in RELS:
        m = merged.setdefault((ch, p), [[], False, False]); m[0].append(col); m[1] = m[1] or req; m[2] = m[2] or one
    base = 'endFill=0;startFill=0;html=1;fontSize=9;fontColor=#444444;labelBackgroundColor=#ffffff;'
    for (ch, p), (cols, req, one) in merged.items():
        end = 'ERmandOne' if req else 'ERzeroToOne'
        start = 'ERzeroToOne' if one else 'ERmany'
        st = '' if req else 'dashed=1;'
        pt, extra = pts(ch, p)
        cells.append(f'<mxCell id="{new("e")}" value="{esc(" / ".join(cols))}" style="endArrow={end};startArrow={start};{base}strokeColor=#666666;{st}{extra}" edge="1" parent="1" source="{vid[ch]}" target="{vid[p]}"><mxGeometry relative="1" as="geometry">{pt}</mxGeometry></mxCell>')
    for ch, col, p in REF:
        pt, extra = pts(ch, p)
        cells.append(f'<mxCell id="{new("r")}" value="{esc(col + " (FK 예정)")}" style="endArrow=ERzeroToOne;startArrow=ERmany;{base}strokeColor=#aaaaaa;dashed=1;dashPattern=2 4;{extra}" edge="1" parent="1" source="{vid[ch]}" target="{vid[p]}"><mxGeometry relative="1" as="geometry">{pt}</mxGeometry></mxCell>')
    return cells
