# 회원결정 PDF 앞에 붙이는 "변경 안내" 쪽 (2026-11-22 법률 검토)
import sys, os
import html, re
CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: 'Apple SD Gothic Neo', sans-serif; font-size: 9.4pt; color:#222; line-height:1.5; }
h1 { font-size: 17pt; margin:0 0 4px; border-bottom: 3px solid #1f4e79; padding-bottom:6px; color:#1f4e79; }
.meta { color:#666; font-size:8.6pt; margin-bottom:12px; }
h2 { font-size: 12.5pt; margin:18px 0 6px; color:#1f4e79; page-break-after: avoid; }
h3 { font-size: 10.6pt; margin:12px 0 4px; page-break-after: avoid; }
p { margin:4px 0; }
table { border-collapse: collapse; width:100%; margin:4px 0 8px; }
tr { page-break-inside: avoid; }
th, td { border:1px solid #bbb; padding:3px 6px; vertical-align:top; text-align:left; }
th { background:#eef2f7; font-weight:600; white-space:nowrap; }
tr.chosen td { background:#e3f0ff; }
td.d { font-weight:700; color:#1f4e79; white-space:nowrap; }
ul { margin:3px 0 6px 0; padding-left:18px; } li { margin:1px 0; }
.box { border:1px solid #c9d6e6; background:#f6f9fc; padding:6px 10px; margin:6px 0; }
.law { border-left:4px solid #8a6d00; background:#fbf8ec; padding:4px 10px; margin:6px 0; font-size:8.9pt; }
.ans { border-left:4px solid #1f4e79; background:#f3f6fa; padding:4px 10px; margin:8px 0 4px; font-weight:600; }
.chg { color:#b03a00; font-weight:600; }
code { font-family: Menlo, monospace; font-size:8.6pt; background:#f1f1f1; padding:0 2px; }
.risk-h { color:#b00020; font-weight:700; } .risk-m { color:#b05a00; font-weight:700; } .risk-l { color:#5a6b00; font-weight:700; }
"""
def il(s):
    s = html.escape(s); p = s.split('`')
    s = ''.join(f'<code>{x}</code>' if i % 2 else x for i, x in enumerate(p))
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    return s.replace('[변경]', '<span class="chg">[변경]</span>')
OUT = sys.argv[1]
D = {
 '28': ('개인정보 보유기간과 파기', [
   ('28-6', 'B. 분석용 식별자 유지', '탈퇴 확정 때 NULL. 외부 분석 도구에 삭제를 요청하고, 요청 일시와 삭제 완료 확인 일시를 회원 행에 기록한다. 탈퇴 회원 통계는 회원 행에 남기는 값만 쓴다.', 'L1-1 C, L1-2 C, L1-3 B, L7-2 B', '개인정보 보호법 21조 1항'),
   ('28-7', 'A. 잔여 예치금이 0이어야 탈퇴 확정', '탈퇴 신청 때 환불 계좌로 출금 요청을 자동으로 만든다. 계좌가 없으면 탈퇴 화면에서 입력받는다. 출금이 실패하면 다시 입력받고, 7일이 지나면 확정한 뒤 고객센터가 처리한다. 미반환 건 연락처는 `SYS_PII_ARCHIVE`에 두고 반환 후 파기한다.', 'L2-1 B, L2-3 C, L2-4 B', '전자상거래법 21조의2 1항 4호'),
   ('28-10', 'A. 결제 정보 5년 뒤 NULL (운영 테이블 보관)', '기간 5년은 그대로. 탈퇴하면 결제 개인정보를 `SYS_PII_ARCHIVE`로 옮기고 운영 행은 NULL로 바꾼다.', 'L3 A', '전자상거래법 시행령 6조 2항 3호, 개인정보 보호법 21조 3항'),
   ('28-11', 'A. 문의·Q&A 3년 뒤 NULL (운영 테이블 보관)', '기간 3년은 그대로. 탈퇴하면 본문과 작성자 정보를 `SYS_PII_ARCHIVE`로 옮기고 운영 행은 NULL로 바꾼다.', 'L3 A', '전자상거래법 시행령 6조 2항 3호, 개인정보 보호법 21조 3항'),
   ('28-13', 'C. 동의 이력 5년 보관', '5년은 그대로. 탈퇴 확정 때 요청 IP만 NULL로 바꾼다.', 'L4 B', '개인정보 보호법 21조 1항'),
 ]),
 '17': ('약관과 동의', [
   ('17-1', 'C. 동의 현재 상태는 회원 테이블 컬럼, 변경 기록은 동의 이력', '현재 상태를 새 테이블 `MBR_CONSENT`(회원 × 동의 항목마다 1행, 대리 PK + UK)로 옮긴다. 회원 테이블의 동의 컬럼 25개를 없애고, 발송 기록은 `NOTICE_SENT_AT` 1개(통지·광고 4개 행)로 둔다. 가입 때 12행 생성, 탈퇴 확정 때 물리 삭제.', 'L9 후속 3 C', '—'),
   ('17-3', '동의 항목 10개 (A~H + 38-10 광고 제3자 제공 + 43-3 환불 계좌 보관)', '선택 동의 "행동 분석 정보 국외 이전"을 추가해 11개 (필수 2, 선택 9). 동의하지 않은 회원의 분석용 식별자와 행동 기록은 국외 분석 도구로 보내지 않는다. 회원 테이블에 동의 여부·일시 컬럼 2개 추가.', 'L7-1 B', '개인정보 보호법 28조의8 1항 1호'),
   ('17-3', '필수 동의 2개 (이용약관, 개인정보 수집·이용)', '개인정보 수집·이용 필수 동의를 없앤다. 가입·주문에 필요한 항목은 계약 이행 근거로 수집하고 구분해 고지한다. 코드는 `PRIVACY_NOTICE`(고지 확인, 동의 여부 항상 Y)로 바꾸고, 회원 컬럼은 `PRIVACY_NOTICE_VER`, `PRIVACY_NOTICE_CONFIRMED_AT`으로 이름을 바꾼다. 필수 동의는 이용약관 1개.', 'L9-1 B', '개인정보 보호법 15조 1항 4호, 22조 3항'),
   ('17-3', '동의 항목 11개', '통지 설정 "개인정보 이용·제공 내역 통지"(`PRIVACY_USAGE_NOTICE`, 거부 가능)를 추가해 12개 (필수 1, 고지 확인 1, 통지 설정 1, 선택 9). 회원 테이블에 통지 거부 여부·최근 통지 일시 컬럼 2개 추가.', 'L9 후속 B', '개인정보 보호법 20조의2, 시행령 15조의3'),
 ]),
 '31': ('개인정보 접근 감사', [
   ('31-4', 'C. 단건이면 회원 ID, 대량이면 조건 + 건수', '단건은 그대로. 대량 조회는 조회 조건 원문과 조회 기준 시각을 더 남긴다. 엑셀 다운로드는 대상 회원 ID를 모두 상세 행으로 남긴다 (SYS 도메인 상세 테이블, 월 파티션 3년).', 'L5 B+C', '안전성 확보조치 기준 2조 (접속기록 정의)'),
 ]),
 '39': ('탈퇴 후 재가입 정책', [
   ('39-4', 'A. 유예 중 로그인하면 철회 여부를 묻고 나머지 기능은 막음', '기능을 막는 것은 그대로. 철회 여부는 첫 로그인 때 한 번만 묻고, 그 뒤에는 "탈퇴 철회" 버튼만 보여 준다.', 'L6 C', '전자상거래법 21조의2 1항 5호, 시행령 27조의2'),
   ('이미 정한 것 (28-7 A 인용)', '예치금 잔액이 0이어야 탈퇴 확정', '28-7이 바뀌었다. 탈퇴 신청 때 예치금 자동 출금 (28번 변경 안내 참고).', 'L2-1 B', '전자상거래법 21조의2 1항 4호'),
 ]),
 '47': ('결제 정보의 파기', [
   ('47-2', 'B. 탈퇴 신청 즉시 결제 관련 값 NULL', '결정은 그대로 유지한다. 다만 신청 처리 순서를 정했다: 예치금 출금 요청 행 생성 → 환불 계좌를 출금 요청 행에 스냅샷 → 회원 결제 관련 값 NULL.', 'L2-2', '(충돌 해소, 법령 근거 아님)'),
 ]),
}
for no, (title, rows) in D.items():
    h = f'<h1>회원 도메인 결정 {no}. {il(title)} — 변경 안내</h1>'
    h += '<div class="meta">2026-11-22 법률 검토 결정 반영 · 다음 쪽부터는 결정 당시 기록 그대로다 · 상세는 <code>docs/pdf/법률검토/법률검토_결정.pdf</code></div>'
    h += '<div class="box">이 결정의 아래 항목은 법률 검토(L1~L9)에서 사용자가 다시 골라 바뀌었다. 다음 쪽부터의 원래 기록과 다르면 이 쪽이 우선한다.</div>'
    h += '<table><tr><th>항목</th><th>결정 당시</th><th>변경 후</th><th>법률 검토 결정</th><th>근거 조문</th></tr>'
    for a, bfr, aft, l, law in rows:
        h += f'<tr><td class="d">{il(a)}</td><td>{il(bfr)}</td><td class="chosen-cell">{il(aft)}</td><td>{il(l)}</td><td>{il(law)}</td></tr>'
    h += '</table>'
    css = CSS + ' td.chosen-cell { background:#e3f0ff; } '
    open(os.path.join(OUT, f'chg{no}.html'), 'w', encoding='utf-8').write(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>결정 {no} 변경 안내</title><style>{css}</style></head><body>{h}</body></html>')
print('ok')
