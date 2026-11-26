# 회원·상품·주문·결제 data.py를 읽어 테이블별 전체 컬럼(업무 + 공통) 목록과 코드 값을 만든다.
# 정의서와 같은 순서: 규칙 8 그룹 순서 → 개인정보 보유 4 → 시스템 6 → 논리 삭제 3.
import os, sys, importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS = 'TIMESTAMP'
SYS = [('CREATED_BY_TYPE_CD', '생성 행위자 유형 코드', 'VARCHAR2(20)', 'N', '', ''), ('CREATED_BY', '생성 행위자 식별자', 'VARCHAR2(100)', 'N', '', ''),
       ('CREATED_AT', '행 생성 일시', TS, 'N', 'SYSTIMESTAMP', ''), ('UPDATED_BY_TYPE_CD', '최종 수정 행위자 유형 코드', 'VARCHAR2(20)', 'Y', '', ''),
       ('UPDATED_BY', '최종 수정 행위자 식별자', 'VARCHAR2(100)', 'Y', '', ''), ('UPDATED_AT', '행 최종 수정 일시', TS, 'Y', '', '')]
DEL = [('DELETED_BY_TYPE_CD', '삭제 행위자 유형 코드', 'VARCHAR2(20)', 'Y', '', ''), ('DELETED_BY', '삭제 행위자 식별자', 'VARCHAR2(100)', 'Y', '', ''),
       ('DELETED_AT', '논리 삭제 일시', TS, 'Y', '', '')]
PII = [('PII_RETENTION_REASON_CD', '개인정보 보유 사유 코드', 'VARCHAR2(30)', 'Y', '', ''), ('PII_RETENTION_BASE_DT', '개인정보 보유 기간 기산 일자', 'DATE', 'Y', '', ''),
       ('PII_RETENTION_END_DT', '개인정보 파기 예정 일자', 'DATE', 'Y', '', ''), ('PII_PURGED_AT', '개인정보 파기 완료 일시', TS, 'Y', '', '')]
DOMAINS = [('회원', 'cols'), ('상품', 'prd'), ('주문', 'ord'), ('결제', 'pay')]


def _mod(d, name):
    sys.path.insert(0, os.path.join(BASE, d))
    s = importlib.util.spec_from_file_location(f'{d}_{name}', os.path.join(BASE, d, name + '.py'))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    sys.path.pop(0)
    return m


def load():
    """[(도메인, 테이블 dict)] 순서대로. dict: t, ko, cols[(물리명, 한글명, 타입, NULL, 기본값, 제약, 설명, 그룹)], codes{컬럼: [(코드, 한글명)]}"""
    out, seen = [], set()
    for dom, d in DOMAINS:
        m = _mod(d, 'data')
        codes = {}
        for key, vals in m.CODES.items():
            for c in key.split(' (')[0].split('/'):
                codes[c.strip()] = [(v[0], v[1]) for v in vals]
        for c, g in getattr(m, 'REUSE', {}).items():
            src = [k for k in m.CODES if k.replace('_CD', '') == g or k == g + '_CD']
            if c not in codes and src: codes[c] = [(v[0], v[1]) for v in m.CODES[src[0]]]
        if d == 'cols':
            o = _mod(d, 'order')
            by = {t['t']: t for t in m.T}
            order = [n for g, ns in o.TABLE_GROUPS for n in ns]
            tables = []
            for n in order:
                t = dict(by[n]); cm = {c[0]: c for c in t['cols']}
                t['cols'] = [cm[c] + (g,) for g, cs in o.COL_GROUPS[n] for c in cs]
                tables.append(t)
        else:
            by = {t['t']: t for t in m.T}
            order = [n for g, ns in m.TABLE_GROUPS for n in ns]
            tables = []
            for n in order:
                t = dict(by[n]); t['cols'] = [c + (g,) for g, cs in t['cols'] for c in cs]
                tables.append(t)
        for t in tables:
            if t['t'] in seen: continue
            seen.add(t['t'])
            cols = [(c[0], c[1], c[3], c[4], c[5], c[6], c[7], c[8]) for c in t['cols']]
            if t.get('pii'): cols += [x + ('', '개인정보 보유') for x in PII]
            cols += [x + ('', '시스템') for x in SYS]
            if t.get('ldel'): cols += [x + ('', '논리 삭제') for x in DEL]
            out.append((dom, dict(t=t['t'], ko=t['ko'], cols=cols, codes={c[0]: codes[c[0]] for c in cols if c[0] in codes})))
    return out


if __name__ == '__main__':
    for dom, t in load():
        print(dom, t['t'], len(t['cols']))
