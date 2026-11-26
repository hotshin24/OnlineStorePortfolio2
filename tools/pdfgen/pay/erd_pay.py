# 결제 도메인 관계 요약 ERD (컬럼 없이 테이블과 관계만, ord/erd_ord.py와 같은 구조). tools/pdfgen/erd/erd.py가 불러 mmd 파일과 draw.io 페이지를 만든다.
# 단일 출처: tools/pdfgen/pay/data.py (결제 테이블·FK). FK 미정 참조는 REF, 결정으로 FK 없이 둔 값 참조(원장·로그·대사의 주문·결제 ID 등, 11-1 A)는 그리지 않는다.
import os, re, html, importlib.util
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

O = _load('pay_data_for_erd', os.path.join(HERE, 'data.py'))
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
REF = [('PAY_PAYMENT', 'CLAIM_ID', 'CLM_CLAIM'), ('PAY_REFUND_REQUEST', 'CLAIM_ID', 'CLM_CLAIM'), ('PAY_PAYMENT_CANCEL', 'CLAIM_ID', 'CLM_CLAIM')]
for ch, col, p in REF:
    assert any(c[0] == col for c in _cols(BY[ch])), (ch, col)
EXT = sorted({r[2] for r in RELS if r[2] not in BY} | {r[2] for r in REF})
CONFIRMED_EXT = {'MBR_MEMBER'}
DOM = {'MBR': '회원 도메인', 'ORD': '주문 도메인', 'CLM': '클레임 도메인', 'ADM': '관리자 도메인'}
def ext_note(n): return DOM[n.split('_')[0]] + ('' if n in CONFIRMED_EXT else ', 이름 후보')

def short_ko(n): return BY[n]['ko'].split(' (')[0]
def esc(s): return html.escape(s, quote=True)

def mmd_summary():
    L = ['---', 'title: 결제 도메인 (PAY) 관계 요약', '---',
         f'%% 생성: tools/pdfgen/erd/erd.py → tools/pdfgen/pay/erd_pay.py ({TODAY}). 컬럼 없이 테이블과 관계만 그렸다. 테이블 이름은 모두 후보. FK 없이 값만 두는 참조(원장·로그·대사의 주문·결제 ID 등, 11-1 A)는 그리지 않았다',
         '%% 표기: ||--o{ 필수 1:N, |o--o{ 선택(NULL 허용 FK) 1:N, ||--o| 1:1(공유 PK), |o..o{ FK 미정 참조(다른 도메인 테이블이 정해지면 FK). 선 이름은 컬럼',
         '%% 다른 도메인 상자: 회원(확정 이름), 주문·클레임·관리자(후보)',
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
GRP_COLOR = ['#dae8fc|#6c8ebf', '#d5e8d4|#82b366', '#fff2cc|#d6b656', '#f8cecc|#b85450', '#e1d5e7|#9673a6', '#ffe6cc|#d79b00']
POS = {
    # 다른 도메인 (왼쪽·오른쪽)
    'ORD_ORDER': (-260, 420, SW, SH), 'ORD_ORDER_CHANGE_HIST': (-260, 620, SW, SH), 'CLM_CLAIM': (-260, 820, SW, SH),
    'MBR_MEMBER': (-260, 1180, SW, SH), 'ADM_USER': (2540, 720, SW, SH),
    # 결제·환불, 증빙, 분쟁
    'PAY_TAX_INVOICE': (300, 250, SW, SH), 'PAY_PAYMENT': (300, 420, 360, 90), 'PAY_REFUND_REQUEST': (300, 720, SW, SH),
    'PAY_CASH_RECEIPT': (860, 250, SW, SH), 'PAY_PAYMENT_CANCEL': (860, 560, 360, 90),
    'PAY_CHARGEBACK_EVIDENCE_FILE': (1420, 250, SW, SH), 'PAY_CHARGEBACK': (1420, 420, SW, SH),
    # 적립금·예치금
    'PAY_POINT_LEDGER': (300, 1060, SW, SH), 'PAY_POINT_DEDUCTION': (860, 1060, SW, SH),
    'PAY_DEPOSIT_LEDGER': (300, 1260, SW, SH), 'PAY_DEPOSIT_DEDUCTION': (860, 1260, SW, SH), 'PAY_DEPOSIT_WITHDRAWAL_REQUEST': (300, 1440, SW, SH),
    # 연동·대사·감시
    'PAY_PG_INCIDENT': (1980, 720, SW, SH), 'PAY_RECONCILIATION_MISMATCH': (1980, 880, SW, SH), 'PAY_RECONCILIATION_RUN': (1980, 1040, SW, SH),
    'PAY_PG_API_LOG': (1420, 880, SW, SH), 'PAY_PG_WEBHOOK_INBOX': (1420, 1040, SW, SH), 'PAY_PG_METRIC_5MIN': (1420, 1200, SW, SH),
    # 설정
    'PAY_PAYMENT_METHOD_PG_SETTING': (1980, 1260, SW, SH), 'PAY_CARD_MERCHANT_CONTRACT': (1980, 1380, SW, SH), 'PAY_PG_CODE_MAPPING': (1980, 1500, SW, SH),
}
# 꺾는 선: (자식, 부모) → (꺾는 점, 나가고 들어가는 위치). 자기 참조(원장, 현금영수증, 세금계산서)는 오른쪽 고리로 그린다.
ROUTE = {
    ('PAY_POINT_LEDGER', 'PAY_POINT_LEDGER'): ([(396, 1025), (524, 1025)], 'exitX=0.3;exitY=0;entryX=0.7;entryY=0;'),
    ('PAY_DEPOSIT_LEDGER', 'PAY_DEPOSIT_LEDGER'): ([(396, 1225), (524, 1225)], 'exitX=0.3;exitY=0;entryX=0.7;entryY=0;'),
    ('PAY_PAYMENT_CANCEL', 'CLM_CLAIM'): ([(1040, 870)], 'exitX=0.5;exitY=1;entryX=1;entryY=0.85;'),
    ('PAY_CASH_RECEIPT', 'PAY_CASH_RECEIPT'): ([(1110, 220), (1220, 220), (1220, 279)], 'exitX=0.78;exitY=0;entryX=1;entryY=0.5;'),
    ('PAY_TAX_INVOICE', 'PAY_TAX_INVOICE'): ([(550, 220), (660, 220), (660, 279)], 'exitX=0.78;exitY=0;entryX=1;entryY=0.5;'),
    ('PAY_CHARGEBACK', 'ADM_USER'): ([(1900, 449), (1900, 700), (2700, 700)], 'exitX=1;exitY=0.5;entryX=0.5;entryY=0;'),
    ('PAY_PAYMENT', 'ADM_USER'): ([(606, 395), (2800, 395)], 'exitX=0.85;exitY=0;entryX=0.8125;entryY=0;'),
    ('PAY_PAYMENT_CANCEL', 'ADM_USER'): ([(2600, 627)], 'exitX=1;exitY=0.75;entryX=0.1875;entryY=0;'),
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
    cells.append(f'<mxCell id="ptitle" value="{esc("결제 도메인 (PAY) 관계 요약")}" style="text;html=1;fontSize=22;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="-260" y="140" width="900" height="40" as="geometry"/></mxCell>')
    note = (f'생성: tools/pdfgen/erd/erd.py → pay/erd_pay.py ({TODAY}) · 결제 테이블 {len(BY)}개, 이름은 모두 후보 · 컬럼 없이 테이블과 관계만 표시 · FK 없이 값만 두는 참조(원장·로그·대사의 주문·결제 ID, 11-1 A)는 그리지 않음 · 상자 색 = 테이블 그룹 · '
            '선 이름 = FK 컬럼 · 실선 = 필수 FK, 점선 = NULL 허용 FK · 까마귀발 = N 쪽 · 회색 점선 상자 = 다른 도메인 · 회색 가는 점선 = FK 미정 참조 (다른 도메인 테이블이 정해지면 FK)')
    cells.append(f'<mxCell id="pnote" value="{esc(note)}" style="text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="-260" y="180" width="2760" height="30" as="geometry"/></mxCell>')
    lx = -260
    for gi, (g, ns) in enumerate(GROUPS):
        fill, stroke = GRP_COLOR[gi % len(GRP_COLOR)].split('|')
        cells.append(f'<mxCell id="{new("l")}" value="{esc(g)}" style="rounded=1;html=1;fontSize=11;fillColor={fill};strokeColor={stroke};" vertex="1" parent="1"><mxGeometry x="{lx}" y="1620" width="150" height="28" as="geometry"/></mxCell>')
        lx += 170
    vid = {}
    for n in list(BY) + EXT:
        x, y, w, h = POS[n]
        vid[n] = new('t')
        if n in BY:
            fill, stroke = GRP_COLOR[grp[n] % len(GRP_COLOR)].split('|')
            big = n in ('PAY_PAYMENT', 'PAY_PAYMENT_CANCEL')
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
