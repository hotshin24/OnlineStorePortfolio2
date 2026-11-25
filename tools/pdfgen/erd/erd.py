# 회원 도메인 ERD와 상품·주문 도메인 관계 요약 생성 (상품은 tools/pdfgen/prd/erd_prd.py, 주문은 tools/pdfgen/ord/erd_ord.py): Mermaid(mmd, 전체 컬럼판과 관계 요약판)와 draw.io(전체 ERD 1개 파일, 도메인별 페이지: 관계 요약, 컬럼 포함)
# 사용법 (저장소 루트에서): python3 tools/pdfgen/erd/erd.py
# 단일 출처: tools/pdfgen/cols/data.py (컬럼), cols/order.py (테이블·컬럼 순서, 규칙 8)
import os, re, sys, html
from datetime import date
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'cols'))
from data import T
from order import TABLE_GROUPS, COL_GROUPS
import importlib.util
_spec = importlib.util.spec_from_file_location('erd_prd', os.path.join(HERE, '..', 'prd', 'erd_prd.py'))
PRD = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(PRD)
_spec = importlib.util.spec_from_file_location('erd_ord', os.path.join(HERE, '..', 'ord', 'erd_ord.py'))
ORD = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ORD)

TODAY = date.today().isoformat()
BY = {t['t']: t for t in T}
for t in T:  # 컬럼정의서와 같은 순서 (규칙 8)
    cm = {c[0]: c for c in t['cols']}
    t['cols'] = [cm[n] for g, ns in COL_GROUPS[t['t']] for n in ns]

EXT_NOTE = {'ADM_USER': '관리자 도메인', 'SYS_EXTERNAL_VENDOR': '시스템 도메인 (외부 업체 마스터)',
            'PRD_STYLE_COLOR': '상품 도메인', 'PRD_SKU': '상품 도메인', 'PRD_CATEGORY': '상품 도메인', 'PRM_DISCOUNT_POLICY': '프로모션 도메인'}

def keys(t, c):
    ck = c[6]
    k = []
    if re.match(r'PK\b', ck): k.append('PK')
    if 'FK →' in ck: k.append('FK')
    if re.search(r'\bUK\d*\b', ck): k.append('UK')
    return k

def fk_target(c):
    m = re.search(r'FK → `([A-Z_]+)`', c[6])
    return m.group(1) if m else None

def pk_cols(t):
    return [c[0] for c in t['cols'] if 'PK' in keys(t, c)]

# 관계: (자식 테이블, FK 컬럼, 부모 테이블, 부모 1쪽 필수 여부, 자식 쪽 1:1 여부)
RELS = []
for t in T:
    for c in t['cols']:
        p = fk_target(c)
        if not p: continue
        one2one = pk_cols(t) == [c[0]]  # 공유 PK (MBR_JOIN_ATTRIBUTION)
        RELS.append((t['t'], c[0], p, c[4] == 'N', one2one))
EXT = sorted({r[2] for r in RELS if r[2] not in BY})

ORDERED = [n for g, ns in TABLE_GROUPS for n in ns]
assert sorted(ORDERED) == sorted(BY), set(ORDERED) ^ set(BY)

def common_note(t):
    s = ['시스템 6']
    if t['pii']: s.insert(0, '개인정보 보유 4')
    if t['ldel']: s.append('논리 삭제 3')
    return ' · '.join(s)

# ---------------------------------------------------------------- Mermaid
def mtype(ty):
    m = re.match(r'NUMBER\((\d+),0\)$', ty)
    if m: return f'NUMBER({m.group(1)})'      # NUMBER(19,0) = NUMBER(19)
    if ',' in ty: return ty.split('(')[0]      # 쉼표는 Mermaid 타입에 못 씀. 전체 타입은 설명에 적는다
    return ty

def mmd():
    L = ['---', 'title: 회원 도메인 (MBR) ERD', '---',
         f'%% 생성: tools/pdfgen/erd/erd.py ({TODAY}). 단일 출처는 tools/pdfgen/cols/data.py',
         f'%% 테이블 {len(T)}개. 업무 컬럼만 그렸다. 모든 테이블 끝의 공통 컬럼(개인정보 보유 4, 시스템 6, 논리 삭제 3)은 생략했다 (규칙 1, 8-A).',
         '%% 다른 도메인 테이블(' + ', '.join(EXT) + ')은 FK 대상만 표시한 후보 이름이다.',
         '%% 표기: ||--o{ 필수 1:N, |o--o{ 선택(NULL 허용 FK) 1:N, ||--o| 1:1 (공유 PK)',
         'erDiagram']
    for g, ns in TABLE_GROUPS:
        L.append(f'    %% ---- {g}')
        for n in ns:
            t = BY[n]
            L.append(f'    {n}["{n} {t["ko"].split(" (")[0]}"] {{')
            for c in t['cols']:
                k = keys(t, c)
                cm = c[1].replace('"', "'")
                if ',' in c[3] and not re.match(r'NUMBER\(\d+,0\)$', c[3]): cm += f' · {c[3]}'
                if c[4] == 'Y': cm += ' · NULL 허용'
                L.append(f'        {mtype(c[3])} {c[0]}' + (f' {", ".join(k)}' if k else '') + f' "{cm}"')
            L.append('    }')
    L.append('    %% ---- 다른 도메인 (후보, FK 대상만)')
    for e in EXT:
        L.append(f'    {e}["{e} ({EXT_NOTE.get(e, "다른 도메인")}, 후보)"] {{')
        L.append('    }')
    L.append('    %% ---- 관계')
    for ch, col, p, req, o2o in RELS:
        left = '||' if req else '|o'
        right = 'o|' if o2o else 'o{'
        L.append(f'    {p} {left}--{right} {ch} : "{col}"')
    return '\n'.join(L) + '\n'

# ---------------------------------------------------------------- draw.io
W_KEY, W_NAME, W_TYPE, W_KO = 44, 300, 110, 250
W = W_KEY + W_NAME + W_TYPE + W_KO
RH, HEAD, GAP_Y, GAP_X = 20, 44, 60, 140
GRP_COLOR = ['#dae8fc|#6c8ebf', '#d5e8d4|#82b366', '#fff2cc|#d6b656', '#e1d5e7|#9673a6', '#f8cecc|#b85450', '#ffe6cc|#d79b00']
def esc(s): return html.escape(s, quote=True)

def drawio_page():
    cells, pkrow, rowid = [], {}, {}
    nid = [0]
    def new(prefix):
        nid[0] += 1; return f'{prefix}{nid[0]}'
    x = 40
    cells.append(f'<mxCell id="title" value="{esc("회원 도메인 (MBR) ERD")}" style="text;html=1;fontSize=22;fontStyle=1;align=left;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="40" y="0" width="900" height="40" as="geometry"/></mxCell>')
    note = (f'생성: tools/pdfgen/erd/erd.py ({TODAY}), 단일 출처 tools/pdfgen/cols/data.py · 테이블 {len(T)}개 · 업무 컬럼만 표시, '
            '공통 컬럼(개인정보 보유 4, 시스템 6, 논리 삭제 3)은 표 맨 아래 줄에 개수만 적음 · 회색 점선은 다른 도메인 후보 테이블 · '
            '선: 실선 끝 = 필수 FK, 0 표시 = NULL 허용 FK, 1:1은 공유 PK')
    cells.append(f'<mxCell id="note" value="{esc(note)}" style="text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="{6 * (W + GAP_X)}" height="36" as="geometry"/></mxCell>')
    top = 130
    for gi, (g, ns) in enumerate(TABLE_GROUPS):
        fill, stroke = GRP_COLOR[gi % len(GRP_COLOR)].split('|')
        cells.append(f'<mxCell id="{new("g")}" value="{esc(g)}" style="text;html=1;fontSize=16;fontStyle=1;align=left;fontColor={stroke};" vertex="1" parent="1"><mxGeometry x="{x}" y="{top - 40}" width="{W}" height="30" as="geometry"/></mxCell>')
        y = top
        for n in ns:
            t = BY[n]
            rows = t['cols']
            h = HEAD + RH * (len(rows) + 1)
            tid = new('t')
            label = f'<b>{esc(n)}</b><br><span style="font-weight:normal;font-size:11px">{esc(t["ko"])}</span>'
            cells.append(f'<mxCell id="{tid}" value="{esc(label)}" style="shape=table;startSize={HEAD};container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=0;align=center;resizeLast=1;html=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};fontSize=13;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{W}" height="{h}" as="geometry"/></mxCell>')
            ry = HEAD
            for c in rows + [None]:
                rid = new('r')
                if c is None:
                    vals = ['', f'+ 공통 컬럼 ({common_note(t)})', '', '']
                    styles = 'fontColor=#888888;fontStyle=2;'
                else:
                    k = keys(t, c)
                    vals = [','.join(k), c[0], c[3] + ('' if c[4] == 'N' else ' ?'), c[1]]
                    styles = 'fontStyle=1;' if 'PK' in k else ''
                    rowid[(n, c[0])] = rid
                    if 'PK' in k and n not in pkrow: pkrow[n] = rid
                bottom = '1' if c is not None and 'PK' in keys(t, c) and (rows.index(c) + 1 == len(rows) or 'PK' not in keys(t, rows[rows.index(c) + 1])) else '0'
                cells.append(f'<mxCell id="{rid}" value="" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top=0;left=0;right=0;bottom={bottom};html=1;" vertex="1" parent="{tid}"><mxGeometry y="{ry}" width="{W}" height="{RH}" as="geometry"/></mxCell>')
                cx = 0
                for i, (v, w) in enumerate(zip(vals, [W_KEY, W_NAME, W_TYPE, W_KO])):
                    al = 'center' if i == 0 else 'left'
                    fs = 10 if i < 3 else 10
                    fam = 'fontFamily=Menlo;' if i in (1, 2) else ''
                    if c is None and i == 1:  # 공통 컬럼 안내는 이름 칸에
                        pass
                    cells.append(f'<mxCell id="{new("c")}" value="{esc(v)}" style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;align={al};spacingLeft=4;overflow=hidden;html=1;whiteSpace=nowrap;fontSize={fs};{fam}{styles}" vertex="1" parent="{rid}"><mxGeometry x="{cx}" width="{w}" height="{RH}" as="geometry"><mxRectangle width="{w}" height="{RH}" as="alternateBounds"/></mxGeometry></mxCell>')
                    cx += w
                ry += RH
            y += h + GAP_Y
        x += W + GAP_X
    # 다른 도메인 후보 테이블
    y = top
    cells.append(f'<mxCell id="{new("g")}" value="{esc("다른 도메인 (후보, FK 대상)")}" style="text;html=1;fontSize=16;fontStyle=1;align=left;fontColor=#666666;" vertex="1" parent="1"><mxGeometry x="{x}" y="{top - 40}" width="360" height="30" as="geometry"/></mxCell>')
    for e in EXT:
        tid = new('t')
        label = f'<b>{esc(e)}</b><br><span style="font-size:11px">{esc(EXT_NOTE.get(e, "다른 도메인"))} · 후보 이름</span>'
        cells.append(f'<mxCell id="{tid}" value="{esc(label)}" style="rounded=0;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#999999;fontColor=#555555;fontSize=13;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="360" height="60" as="geometry"/></mxCell>')
        pkrow[e] = tid
        y += 60 + GAP_Y
    # 관계선: 자식 FK 행 → 부모 PK 행
    for ch, col, p, req, o2o in RELS:
        src, tgt = rowid[(ch, col)], pkrow[p]
        start = 'ERzeroToOne' if o2o else 'ERmany'
        end = 'ERmandOne' if req else 'ERzeroToOne'
        dash = '' if req else 'dashed=1;'
        cells.append(f'<mxCell id="{new("e")}" value="" style="edgeStyle=entityRelationEdgeStyle;fontSize=12;html=1;endArrow={end};startArrow={start};endFill=0;startFill=0;rounded=0;strokeColor=#555555;{dash}" edge="1" parent="1" source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    return cells


# ---------------------------------------------------------------- 관계 요약 (컬럼 없이 테이블과 관계선만)
def short_ko(t): return t['ko'].split(' (')[0]

def mmd_summary():
    L = ['---', 'title: 회원 도메인 (MBR) 관계 요약', '---',
         f'%% 생성: tools/pdfgen/erd/erd.py ({TODAY}). 컬럼 없이 테이블과 관계만 그렸다. 컬럼은 회원_MBR_ERD.mmd',
         '%% 표기: ||--o{ 필수 1:N, |o--o{ 선택(NULL 허용 FK) 1:N, ||--o| 1:1 (공유 PK). 선 이름은 FK 컬럼',
         'erDiagram']
    for g, ns in TABLE_GROUPS:
        L.append(f'    %% ---- {g}')
        for n in ns:
            L.append(f'    {n}["{n} {short_ko(BY[n])}"] {{')
            L.append('    }')
    L.append('    %% ---- 다른 도메인 (후보)')
    for e in EXT:
        L.append(f'    {e}["{e} ({EXT_NOTE.get(e, "다른 도메인")}, 후보)"] {{')
        L.append('    }')
    L.append('    %% ---- 관계')
    for ch, col, p, req, o2o in RELS:
        L.append(f'    {p} {"||" if req else "|o"}--{"o|" if o2o else "o{"} {ch} : "{col}"')
    return '\n'.join(L) + '\n'

SW, SH = 290, 58
def summary_positions():
    grp = {n: gi for gi, (g, ns) in enumerate(TABLE_GROUPS) for n in ns}
    left = [n for n in TABLE_GROUPS[0][1] if n != 'MBR_MEMBER'] + TABLE_GROUPS[1][1]
    right = TABLE_GROUPS[2][1] + TABLE_GROUPS[3][1]
    bottom = TABLE_GROUPS[4][1] + TABLE_GROUPS[5][1]
    pos = {'MBR_MEMBER': (1150, 600, 340, 90)}
    for i, n in enumerate(left): pos[n] = (150, 120 + i * 120, SW, SH)
    for i, n in enumerate(right): pos[n] = (2150, 120 + i * 120, SW, SH)
    for i, n in enumerate(bottom): pos[n] = (150 + i * 370, 1360, SW, SH)
    ext = {'ADM_USER': (1175, 120), 'PRD_STYLE_COLOR': (2780, 340), 'PRD_SKU': (2780, 480), 'PRD_CATEGORY': (2780, 640),
           'PRM_DISCOUNT_POLICY': (2780, 840), 'SYS_EXTERNAL_VENDOR': (-330, 240)}
    for e in EXT:
        x, y = ext.get(e, (2780, 1100 + 120 * EXT.index(e)))
        pos[e] = (x, y, SW, SH)
    return pos, grp

def drawio_summary_page():
    pos, grp = summary_positions()
    cells, nid = [], [0]
    def new(prefix):
        nid[0] += 1; return f's{prefix}{nid[0]}'
    cells.append(f'<mxCell id="stitle" value="{esc("회원 도메인 (MBR) 관계 요약")}" style="text;html=1;fontSize=22;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="150" y="0" width="900" height="40" as="geometry"/></mxCell>')
    note = (f'생성: tools/pdfgen/erd/erd.py ({TODAY}) · 컬럼 없이 테이블과 관계만 표시 (컬럼은 "회원 (MBR)" 페이지) · 상자 색 = 테이블 그룹 · '
            '선 이름 = FK 컬럼 · 실선 = 필수 FK, 점선 = NULL 허용 FK · 까마귀발 = N 쪽 · 회색 점선 상자 = 다른 도메인 후보')
    cells.append(f'<mxCell id="snote" value="{esc(note)}" style="text;html=1;fontSize=11;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="150" y="40" width="2900" height="30" as="geometry"/></mxCell>')
    # 범례: 그룹 색
    lx = 150
    for gi, (g, ns) in enumerate(TABLE_GROUPS):
        fill, stroke = GRP_COLOR[gi % len(GRP_COLOR)].split('|')
        cells.append(f'<mxCell id="{new("l")}" value="{esc(g)}" style="rounded=1;html=1;fontSize=11;fillColor={fill};strokeColor={stroke};" vertex="1" parent="1"><mxGeometry x="{lx}" y="1700" width="150" height="28" as="geometry"/></mxCell>')
        lx += 170
    vid = {}
    for n, (x, y, w, h) in pos.items():
        vid[n] = new('t')
        if n in BY:
            fill, stroke = GRP_COLOR[grp[n] % len(GRP_COLOR)].split('|')
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(short_ko(BY[n]))}</span>'
            st = f'rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={14 if n == "MBR_MEMBER" else 12};' + ('strokeWidth=2;' if n == 'MBR_MEMBER' else '')
        else:
            label = f'<b>{esc(n)}</b><br><span style="font-size:11px">{esc(EXT_NOTE.get(n, "다른 도메인"))} · 후보</span>'
            st = 'rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#999999;fontColor=#555555;fontSize=12;'
        cells.append(f'<mxCell id="{vid[n]}" value="{esc(label)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    # 같은 (자식, 부모) FK는 선 하나로 합치고, 반대 방향 쌍은 휘어서 겹치지 않게 한다
    merged = {}
    for ch, col, p, req, o2o in RELS:
        k = (ch, p)
        if k in merged:
            m = merged[k]; m[0].append(col); m[1] = m[1] or req
        else:
            merged[k] = [[col], req, o2o]
    for (ch, p), (cols, req, o2o) in merged.items():
        start = 'ERzeroToOne' if o2o else 'ERmany'
        end = 'ERmandOne' if req else 'ERzeroToOne'
        dash = '' if req else 'dashed=1;'
        pts = ''
        if p == 'SYS_EXTERNAL_VENDOR' and pos[ch][1] > 1000:  # 아래 줄에서 오는 선은 상자 밑으로 돌아간다
            x1, y1, w1, h1 = pos[ch]; x2, y2, w2, h2 = pos[p]
            pts = f'<Array as="points"><mxPoint x="{x1 + w1 / 2:.0f}" y="{y1 + h1 + 60:.0f}"/><mxPoint x="{x2 + w2 / 2:.0f}" y="{y1 + h1 + 60:.0f}"/></Array>'
            dash += 'edgeStyle=orthogonalEdgeStyle;'
        elif (p, ch) in merged and ch == 'MBR_MEMBER':  # 회원이 참조하는 쪽(기본 배송지, 최근 결제수단)을 휘게
            x1, y1, w1, h1 = pos[ch]; x2, y2, w2, h2 = pos[p]
            cx, cy = (x1 + w1 / 2 + x2 + w2 / 2) / 2, (y1 + h1 / 2 + y2 + h2 / 2) / 2
            pts = f'<Array as="points"><mxPoint x="{cx:.0f}" y="{cy - 70:.0f}"/></Array>'
            dash += 'curved=1;'
        cells.append(f'<mxCell id="{new("e")}" value="{esc(" / ".join(cols))}" style="endArrow={end};startArrow={start};endFill=0;startFill=0;html=1;fontSize=9;fontColor=#444444;labelBackgroundColor=#ffffff;strokeColor=#666666;{dash}" edge="1" parent="1" source="{vid[ch]}" target="{vid[p]}"><mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')
    return cells

def drawio():
    def diagram(did, name, cells, w, h):
        body = '\n'.join('        ' + c for c in cells)
        return (f'  <diagram id="{did}" name="{esc(name)}">\n'
                f'    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="{w}" pageHeight="{h}" math="0" shadow="0">\n'
                '      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n'
                + body + '\n      </root>\n    </mxGraphModel>\n  </diagram>\n')
    return ('<mxfile host="drawio" agent="tools/pdfgen/erd/erd.py" version="24.0.0">\n'
            + diagram('mbr-summary', '회원 (MBR) 관계 요약', drawio_summary_page(), 3200, 1800)
            + diagram('mbr', '회원 (MBR)', drawio_page(), 4800, 3600)
            + diagram('prd-summary', '상품 (PRD) 관계 요약', PRD.summary_cells(), 3200, 1600)
            + diagram('ord-summary', '주문 (ORD) 관계 요약', ORD.summary_cells(), 3200, 1600)
            + '</mxfile>\n')

if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'docs', 'mmd'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'docs', 'drawio'), exist_ok=True)
    p1 = os.path.join(ROOT, 'docs', 'mmd', '회원_MBR_ERD.mmd')
    p2 = os.path.join(ROOT, 'docs', 'drawio', '전체_ERD.drawio')
    open(p1, 'w', encoding='utf-8').write(mmd())
    p3 = os.path.join(ROOT, 'docs', 'mmd', '회원_MBR_관계요약.mmd')
    open(p2, 'w', encoding='utf-8').write(drawio())
    open(p3, 'w', encoding='utf-8').write(mmd_summary())
    p4 = os.path.join(ROOT, 'docs', 'mmd', '상품_PRD_관계요약.mmd')
    open(p4, 'w', encoding='utf-8').write(PRD.mmd_summary())
    p5 = os.path.join(ROOT, 'docs', 'mmd', '주문_ORD_관계요약.mmd')
    open(p5, 'w', encoding='utf-8').write(ORD.mmd_summary())
    print(p1); print(p3); print(p4); print(p5); print(p2)
    print(f'주문: 테이블 {len(ORD.BY)}개, 관계 {len(ORD.RELS)}개, FK 미정 참조 {len(ORD.REF)}개, 다른 도메인 {len(ORD.EXT)}개')
    print(f'상품: 테이블 {len(PRD.BY)}개, 관계 {len(PRD.RELS)}개, 다른 도메인 {len(PRD.EXT)}개')
    print(f'테이블 {len(T)}개, 관계 {len(RELS)}개, 다른 도메인 {len(EXT)}개')
