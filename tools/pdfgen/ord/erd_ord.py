# 주문 도메인 관계 요약 ERD (컬럼 없이 테이블과 관계만). tools/pdfgen/erd/erd.py가 불러 mmd 파일과 draw.io 페이지를 만든다.
# 단일 출처: tools/pdfgen/ord/data.py (주문 테이블·FK). FK가 아직 없는 다른 도메인 참조 컬럼은 REF로 따로 적는다.
import os, re, html, importlib.util
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

O = _load('ord_data_for_erd', os.path.join(HERE, 'data.py'))
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
REF = [('ORD_ORDER_ITEM', 'DISPLAY_CONTENT_HIST_ID', 'PRD_DISPLAY_CONTENT_HIST'),
       ('ORD_ORDER_ITEM_STATUS_HIST', 'CLAIM_ID', 'CLM_CLAIM'),
       ('ORD_ORDER_FREEBIE', 'NON_SALE_ITEM_ID', 'WMS_NON_SALE_ITEM'),
       ('ORD_ORDER_FREEBIE', 'PROMOTION_ID', 'PRM_PROMOTION'),
       ('ORD_ORDER_ITEM_DISCOUNT', 'PROMOTION_ID', 'PRM_PROMOTION'),
       ('ORD_ORDER_ITEM_DISCOUNT', 'MEMBER_COUPON_ID', 'PRM_MEMBER_COUPON'),
       ('ORD_CART', 'SELECTED_MEMBER_COUPON_ID', 'PRM_MEMBER_COUPON'),
       ('ORD_CART', 'DISPLAY_CONTENT_ID', 'DSP_DISPLAY_CONTENT'),
       ('ORD_ORDER_ITEM', 'DISPLAY_CONTENT_ID', 'DSP_DISPLAY_CONTENT')]
# EXHIBITION_ID(소속 DSP / PRM 미정), AFFILIATE_ID(소속 SYS / STL 미정)는 대상 도메인이 정해지면 넣는다 (OC-36 B)
for ch, col, p in REF:
    assert any(c[0] == col for c in _cols(BY[ch])), (ch, col)
EXT = sorted({r[2] for r in RELS if r[2] not in BY} | {r[2] for r in REF})
CONFIRMED_EXT = {'MBR_MEMBER', 'MBR_LEGAL_GUARDIAN_CONSENT', 'MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT'}
DOM = {'MBR': '회원 도메인', 'PRD': '상품 도메인', 'CLM': '클레임 도메인', 'WMS': '창고 도메인', 'PRM': '프로모션 도메인', 'DSP': '전시 도메인'}
def ext_note(n): return DOM[n.split('_')[0]] + ('' if n in CONFIRMED_EXT else ', 이름 후보')

def short_ko(n): return BY[n]['ko'].split(' (')[0]
def esc(s): return html.escape(s, quote=True)

def mmd_summary():
    L = ['---', 'title: 주문 도메인 (ORD) 관계 요약', '---',
         f'%% 생성: tools/pdfgen/erd/erd.py → tools/pdfgen/ord/erd_ord.py ({TODAY}). 컬럼 없이 테이블과 관계만 그렸다. 테이블 이름은 모두 후보',
         '%% 표기: ||--o{ 필수 1:N, |o--o{ 선택(NULL 허용 FK) 1:N, ||--o| 1:1(공유 PK), |o..o{ FK 미정 참조(다른 도메인 테이블이 정해지면 FK). 선 이름은 컬럼',
         '%% 다른 도메인 상자: 회원(확정 이름), 상품(후보), 클레임·창고·프로모션·전시(후보)',
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
    L.append('    %% ---- FK 미정 참조')
    for ch, col, p in REF:
        L.append(f'    {p} |o..o{{ {ch} : "{col} (FK 미정)"')
    return '\n'.join(L) + '\n'

SW, SH = 320, 58
GRP_COLOR = ['#dae8fc|#6c8ebf', '#d5e8d4|#82b366', '#fff2cc|#d6b656', '#e1d5e7|#9673a6']
POS = {
    'ORD_ORDER': (1000, 500, 360, 90), 'ORD_ORDER_ITEM': (1000, 820, 360, 90),
    'ORD_GUEST_LOOKUP_FAIL_LOG': (1560, 160, SW, SH), 'ORD_ORDER_ATTRIBUTION': (1560, 280, SW, SH), 'ORD_ORDER_ADMIN_MEMO': (1560, 400, SW, SH), 'ORD_ORDER_FREEBIE': (1560, 520, SW, SH),
    'ORD_ORDER_CHANGE_HIST': (1560, 660, SW, SH), 'ORD_ORDER_ITEM_DISCOUNT': (1560, 840, SW, SH), 'ORD_ORDER_ITEM_STATUS_HIST': (1560, 1000, SW, SH),
    'ORD_CART': (-260, 760, SW, SH),
    'MBR_LEGAL_GUARDIAN_CONSENT': (300, 360, SW, SH), 'MBR_MEMBER': (300, 520, SW, SH),
    'PRD_STYLE': (300, 820, SW, SH), 'PRD_SKU': (300, 1000, SW, SH), 'PRD_PRICE_HIST': (300, 1140, SW, SH), 'PRD_DISPLAY_CONTENT_HIST': (300, 1280, SW, SH), 'DSP_DISPLAY_CONTENT': (1000, 1440, SW, SH),
    'WMS_NON_SALE_ITEM': (2180, 440, SW, SH), 'PRM_PROMOTION': (2180, 600, SW, SH),
    'MBR_EMPLOYEE_ANNUAL_DISCOUNT_LIMIT': (2180, 760, SW, SH), 'PRM_MEMBER_COUPON': (2180, 900, SW, SH), 'CLM_CLAIM': (2180, 1040, SW, SH),
}
# 꺾는 선: (자식, 부모) → (꺾는 점, 나가고 들어가는 위치). 장바구니의 FK 미정 참조 2개는 그림 아래로 돌려 다른 상자·선을 지나지 않게 한다.
ROUTE = {
    ('ORD_CART', 'DSP_DISPLAY_CONTENT'): ([(-164, 1469)], 'exitX=0.3;exitY=1;entryX=0;entryY=0.5;'),
    ('ORD_CART', 'PRM_MEMBER_COUPON'): ([(-36, 1540), (2560, 1540), (2560, 929)], 'exitX=0.7;exitY=1;entryX=1;entryY=0.5;'),
}
def pts(ch, p):
    if (ch, p) not in ROUTE: return '', ''
    ps, extra = ROUTE[(ch, p)]
    return '<Array as="points">' + ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in ps) + '</Array>', extra

def summary_cells():
    cells, nid = [], [0]
    def new(prefix):
        nid[0] += 1; return f'o{prefix}{nid[0]}'
    missing = (set(BY) | set(EXT)) - set(POS)
    assert not missing, missing
    grp = {n: gi for gi, (g, ns) in enumerate(GROUPS) for n in ns}
    cells.append(f'<mxCell id="otitle" value="{esc("주문 도메인 (ORD) 관계 요약")}" style="text;html=1;fontSize=22;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="-260" y="140" width="900" height="40" as="geometry"/></mxCell>')
    note = (f'생성: tools/pdfgen/erd/erd.py → ord/erd_ord.py ({TODAY}) · 주문 테이블 {len(BY)}개, 이름은 모두 후보 · 컬럼 없이 테이블과 관계만 표시 · 상자 색 = 테이블 그룹 · '
            '선 이름 = FK 컬럼 · 실선 = 필수 FK, 점선 = NULL 허용 FK · 까마귀발 = N 쪽 · 회색 점선 상자 = 다른 도메인 · 회색 가는 점선 = FK 미정 참조 (다른 도메인 테이블이 정해지면 FK)')
    cells.append(f'<mxCell id="onote" value="{esc(note)}" style="text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="-260" y="180" width="2760" height="30" as="geometry"/></mxCell>')
    lx = -260
    for gi, (g, ns) in enumerate(GROUPS):
        fill, stroke = GRP_COLOR[gi % len(GRP_COLOR)].split('|')
        cells.append(f'<mxCell id="{new("l")}" value="{esc(g)}" style="rounded=1;html=1;fontSize=11;fillColor={fill};strokeColor={stroke};" vertex="1" parent="1"><mxGeometry x="{lx}" y="1600" width="150" height="28" as="geometry"/></mxCell>')
        lx += 170
    vid = {}
    for n in list(BY) + EXT:
        x, y, w, h = POS[n]
        vid[n] = new('t')
        if n in BY:
            fill, stroke = GRP_COLOR[grp[n] % len(GRP_COLOR)].split('|')
            big = n in ('ORD_ORDER', 'ORD_ORDER_ITEM')
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
        cells.append(f'<mxCell id="{new("r")}" value="{esc(col + " (FK 미정)")}" style="endArrow=ERzeroToOne;startArrow=ERmany;{base}strokeColor=#aaaaaa;dashed=1;dashPattern=2 4;{extra}" edge="1" parent="1" source="{vid[ch]}" target="{vid[p]}"><mxGeometry relative="1" as="geometry">{pt}</mxGeometry></mxCell>')
    return cells
