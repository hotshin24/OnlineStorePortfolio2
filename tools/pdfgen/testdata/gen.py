# 테스트 데이터 엑셀 생성: python3 tools/pdfgen/testdata/gen.py <출력 폴더>  (도메인별 파일 4개)
# rows.py의 시나리오 값 + 빈 NOT NULL 컬럼 자동 채움 (회색 기울임) → 시트마다 테이블 하나.
import os, sys, re, zipfile
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import load, rows

BASE_AT = '2026-11-20 00:00:00'


def default_of(col, row):
    name, ko, typ, null, dflt, ck = col[:6]
    d = (dflt or '').strip()
    if d == 'SYSTIMESTAMP' or d == 'SYSDATE':
        ats = sorted(v for k, v in row.items() if k.endswith('_AT') and isinstance(v, str) and v[:2] == '20')
        return ats[0] if ats else BASE_AT
    if d.startswith("'") and d.endswith("'"): return d[1:-1]
    if re.fullmatch(r'-?\d+(\.\d+)?', d): return float(d) if '.' in d else int(d)
    return None


def auto(col, row, codes):
    name, ko, typ, null, dflt, ck = col[:6]
    v = default_of(col, row)
    if v is not None: return v
    if name == 'CREATED_BY_TYPE_CD': return 'MEMBER' if row.get('MEMBER_ID') else 'ADMIN'
    if name == 'CREATED_BY': return str(row['MEMBER_ID']) if row.get('MEMBER_ID') else '7'
    if name.endswith('_YN'): return 'N'
    if name in codes: return codes[name][0][0]
    if name.endswith('_SN') or name.endswith('_VER') and typ.startswith('NUMBER'): return 1
    if typ.startswith('NUMBER'): return 0
    if name.endswith('_AT') or typ.startswith('TIMESTAMP'): return BASE_AT
    if name.endswith('_DT') or typ == 'DATE': return BASE_AT[:10]
    if name.endswith('_ENC'): return 'ENC(…)'
    if name.endswith('_HASH'): return 'HMAC(…)'
    if name.endswith('_JSON'): return '{}'
    return '(값)'


def build():
    tables = load.load()
    names = {t['t'] for _, t in tables}
    warn = [f'rows.py에 있으나 정의서에 없는 테이블: {n}' for n in rows.R if n not in names]
    out = []
    for dom, t in tables:
        cols = t['cols']; cn = [c[0] for c in cols]
        pk = cols[0][0] if 'PK' in cols[0][5] else None
        data = []
        for i, r in enumerate(rows.R.get(t['t'], []), 1):
            for k in r:
                if k not in cn: warn.append(f"{t['t']}: 없는 컬럼 {k}")
            row, autos = {}, set()
            if pk and pk not in r and cols[0][2].startswith('NUMBER'): row[pk] = i
            for c in cols:
                n = c[0]
                if n in row: continue
                if n in r and r[n] is not None:
                    row[n] = r[n]
                    if n in t['codes'] and isinstance(r[n], str) and r[n] not in [x[0] for x in t['codes'][n]]:
                        warn.append(f"{t['t']}.{n}: 값 목록에 없는 코드 {r[n]}")
                elif c[3] == 'N' and '가상 컬럼' not in c[5]:
                    d = default_of(c, {**r, **row})
                    if d is not None: row[n] = d
                    else: row[n] = auto(c, {**r, **row}, t['codes']); autos.add(n)
            data.append((row, autos))
        out.append((dom, t, data))
    return out, warn


# ---------------------------------------------------------------- xlsx
def col_letter(i):
    s = ''
    while True:
        i, r = divmod(i, 26); s = chr(65 + r) + s
        if i == 0: return s
        i -= 1


STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0"/></numFmts>
<fonts count="5"><font><sz val="10"/><name val="Apple SD Gothic Neo"/></font>
<font><b/><sz val="10"/><name val="Apple SD Gothic Neo"/></font>
<font><sz val="9"/><color rgb="FF555555"/><name val="Apple SD Gothic Neo"/></font>
<font><i/><sz val="10"/><color rgb="FF999999"/><name val="Apple SD Gothic Neo"/></font>
<font><b/><sz val="13"/><name val="Apple SD Gothic Neo"/></font></fonts>
<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFDCE6F2"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEDEDED"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/></patternFill></fill></fills>
<borders count="2"><border/><border><left style="thin"><color rgb="FFBFBFBF"/></left><right style="thin"><color rgb="FFBFBFBF"/></right>
<top style="thin"><color rgb="FFBFBFBF"/></top><bottom style="thin"><color rgb="FFBFBFBF"/></bottom></border></borders>
<cellStyleXfs count="1"><xf/></cellStyleXfs>
<cellXfs count="12">
<xf/>
<xf fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1"/>
<xf fontId="2" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1"><alignment wrapText="1" vertical="top"/></xf>
<xf fontId="1" fillId="3" borderId="1" applyFont="1" applyFill="1" applyBorder="1"/>
<xf fontId="2" fillId="3" borderId="1" applyFont="1" applyFill="1" applyBorder="1"><alignment wrapText="1" vertical="top"/></xf>
<xf borderId="1" applyBorder="1"/>
<xf numFmtId="164" borderId="1" applyNumberFormat="1" applyBorder="1"/>
<xf fontId="3" borderId="1" applyFont="1" applyBorder="1"/>
<xf fontId="3" numFmtId="164" borderId="1" applyFont="1" applyNumberFormat="1" applyBorder="1"/>
<xf fontId="4" applyFont="1"/>
<xf fontId="1" fillId="4" borderId="1" applyFont="1" applyFill="1" applyBorder="1"/>
<xf borderId="1" applyBorder="1"><alignment wrapText="1" vertical="top"/></xf>
</cellXfs></styleSheet>'''


def cell(ref, v, s=0):
    if v is None or v == '': return f'<c r="{ref}" s="{s}"/>' if s else ''
    if isinstance(v, bool): v = 'Y' if v else 'N'
    if isinstance(v, (int, float)): return f'<c r="{ref}" s="{s}"><v>{v}</v></c>'
    t = escape(str(v)).replace('\n', '&#10;')
    return f'<c r="{ref}" s="{s}" t="inlineStr"><is><t xml:space="preserve">{t}</t></is></c>'


def sheet_xml(grid, widths, freeze=None):
    x = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
         '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
    if freeze:
        x.append(f'<sheetViews><sheetView workbookViewId="0"><pane xSplit="1" ySplit="{freeze - 1}" topLeftCell="B{freeze}" '
                 'activePane="bottomRight" state="frozen"/></sheetView></sheetViews>')
    x.append('<cols>' + ''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths, 1)) + '</cols>')
    x.append('<sheetData>')
    for ri, row in enumerate(grid, 1):
        x.append(f'<row r="{ri}">' + ''.join(cell(f'{col_letter(ci)}{ri}', v, s) for ci, (v, s) in enumerate(row)) + '</row>')
    x.append('</sheetData></worksheet>')
    return ''.join(x)


def write_xlsx(path, sheets):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(1, len(sheets) + 1)) + '</Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + ''.join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, (n, _) in enumerate(sheets, 1))
                   + '</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                             f'Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1))
                   + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                   'Target="styles.xml"/></Relationships>')
        z.writestr('xl/styles.xml', STYLES)
        for i, (_, xml) in enumerate(sheets, 1):
            z.writestr(f'xl/worksheets/sheet{i}.xml', xml)


COMMON = ('개인정보 보유', '시스템', '논리 삭제')


def table_sheet(t, data):
    cols = t['cols']
    hdr = lambda c, s, s2: (c, s2 if c is not None and False else s)
    g1, g2, g3, g4 = [('No', 10)], [('한글 논리명', 10)], [('그룹', 10)], [('타입 / NULL', 10)]
    for c in cols:
        common = c[7] in COMMON
        a, b = (3, 4) if common else (1, 2)
        g1.append((c[0], a)); g2.append((c[1], b)); g3.append((c[7], b))
        extra = ' · 가상' if '가상 컬럼' in c[5] else ''
        g4.append((f"{c[2]} / {'NULL' if c[3] == 'Y' else 'NOT NULL'}{extra}", b))
    grid = [g1, g2, g3, g4]
    for i, (row, autos) in enumerate(data, 1):
        line = [(i, 5)]
        for c in cols:
            v = row.get(c[0]); a = c[0] in autos
            num = isinstance(v, (int, float)) and c[0].endswith('_AMT')
            line.append((v, (8 if num else 7) if a else (6 if num else 5)))
        grid.append(line)
    widths = [6]
    for c in cols:
        vals = [str(r.get(c[0], '')) for r, _ in data] + [c[0]]
        widths.append(min(48, max(10, max(len(v) for v in vals) * 1.1 + 2)))
    return sheet_xml(grid, widths, freeze=5)


def main(outdir):
    allout, warn = build()
    for w in warn: print('경고:', w)
    for dom, _ in load.DOMAINS:
        out = [x for x in allout if x[0] == dom]
        write_domain(os.path.join(outdir, f'테스트데이터_{dom}.xlsx'), dom, out)


def write_domain(path, dom, out):
    used, sheets, index = set(), [], []
    for dom, t, data in out:
        n = t['t'][:31]; k = 1
        while n in used: k += 1; n = t['t'][:29] + f'~{k}'
        used.add(n)
        sheets.append((n, table_sheet(t, data)))
        nauto = sum(len(a) for _, a in data)
        index.append((dom, t['t'], t['ko'], n, len(data), len(t['cols']), nauto))
    g = [[(f'{dom} 도메인 테스트 데이터 (컬럼 추가·이동 검토용). 시나리오는 회원·상품·주문·결제 파일 공통', 9)], [('기준일 2026-11-20. 정의서 단일 출처(data.py)에서 컬럼 목록을 읽어 만들었다.', 0)], [('', 0)]]
    g.append([('시나리오', 10)])
    for i, s in enumerate(rows.SCENARIO, 1): g.append([(i, 5), (s, 11)])
    g += [[('', 0)], [('표기', 10)]]
    for a, b in [('파란 머리글', '업무 컬럼 (정의서 그룹 순서)'), ('회색 머리글', '공통 컬럼: 개인정보 보유 4 → 시스템 6 → 논리 삭제 3'),
                 ('회색 기울임 값', '시나리오에서 정하지 않았고 DDL 기본값도 없는 NOT NULL 컬럼을 규칙으로 채운 값 (의미 없음). 기본값으로 채운 칸은 보통 글씨'),
                 ('빈칸', 'NULL (그 상황에서 채워지지 않는 값)'), ('ENC(평문)', '암호문 RAW (AES-256-GCM). 괄호 안은 평문 예시'),
                 ('HMAC(정규화 값)', '검색용 해시 RAW(32)'), ('ARGON2ID(…)', '비밀번호·PIN 해시'),
                 ('타입 줄의 · 가상', 'Oracle 가상 컬럼. 저장하지 않고 계산되는 값이며, 행에 적은 값은 계산 결과 예시'),
                 ('PK', '1부터 차례로 매김. 범위 밖 도메인(쿠폰, 클레임, 관리자 등) FK는 그럴듯한 번호만 넣음')]:
        g.append([(a, 5), (b, 5)])
    g += [[('', 0)], [('테이블 목록', 10)], [('도메인', 1), ('테이블', 1), ('한글명', 1), ('시트', 1), ('행', 1), ('컬럼', 1), ('자동 채움 칸', 1)]]
    for r in index: g.append([(v, 5) for v in r])
    sheets.insert(0, ('안내', sheet_xml(g, [16, 90, 30, 32, 6, 6, 12])))
    write_xlsx(path, sheets)
    print(f'시트 {len(sheets)}개, 테이블 {len(out)}개, 행 {sum(len(d) for _, _, d in out)}개 → {path}')


if __name__ == '__main__':
    main(sys.argv[1])
