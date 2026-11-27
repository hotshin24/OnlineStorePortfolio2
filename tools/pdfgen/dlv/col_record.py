# 배송 컬럼 검토 결정 기록 (DC-n만). 다른 도메인의 *_컬럼검토_결정.pdf와 같은 자리에 둔다 (2026-11-27 사용자 지시).
# 전제·축과 T-n은 docs/pdf/결정/배송결정/의 결정별 PDF에만 있다. 데이터와 본문 렌더링은 col_review.py.
# 사용: python3 col_record.py <출력.html>  → Chrome headless로 PDF → docs/pdf/테이블_컬럼/배송/배송_컬럼검토_결정.pdf
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from col_review import C, CSS, EXTRA_CSS, il, one


def main(out):
    dc = [c for c in C if c[0].startswith('DC-')]
    done = sum(1 for c in dc if c[7])
    b = [f'<h1>배송 도메인 컬럼 검토 결정 (DC-1~DC-{len(dc)})</h1>',
         '<div class="meta">자체 브랜드 패션 온라인몰 DB 설계 · Oracle 21c XE · 2026-11-26~27 대화로 결정 · '
         f'배송 전제·축 7개와 테이블 결정 T-1~T-7, 컬럼 정의서(제안) 기준 · {done}개 결정, {len(dc) - done}개 답변 전</div>',
         '<div class="box">배송 테이블·컬럼을 설계하며 정할 사항을 질문으로 정리했다. 질문과 선택지, 추천 이유는 당시 대화 원문 그대로이고, '
         '반영은 답을 받은 뒤 알린 내용이다. 굵은 기호가 추천안, 파란 행이 고른 안이다. '
         '전제·축과 테이블 결정(T-n)은 <code>docs/pdf/결정/배송결정/</code>에 결정 하나당 PDF로 있고, 컬럼 결정도 같은 내용이 결정별 PDF로 있다.</div>',
         '<h2>목록</h2><table><tr><th style="width:56px">번호</th><th>제목</th><th style="width:56px">선택</th></tr>'
         + ''.join(f'<tr><td>{c[0]}</td><td>{il(c[1])}</td><td>{c[7] or "답변 전"}</td></tr>' for c in dc) + '</table>']
    b += [one(c) for c in dc]
    open(out, 'w', encoding='utf-8').write(
        f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>배송 도메인 컬럼 검토 결정</title>'
        f'<style>{CSS}{EXTRA_CSS}</style></head><body>{"".join(b)}</body></html>')
    print(out, len(dc))


if __name__ == '__main__':
    main(sys.argv[1])
