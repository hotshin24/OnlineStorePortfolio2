# 대화 원문(orig/*.md)을 HTML로 바꾸는 작은 마크다운 변환기. 원문에 쓰인 문법만 다룬다:
# 제목(##, ###), 표, 글머리표(-, 들여쓰기 포함), 번호 목록, 굵게, 코드, 문단.
import html, re

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    return s

def _cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]

def render(text, chosen=None, shift=1):
    """chosen: 선택지 표에서 파랗게 칠할 기호. shift: 제목 단계를 몇 칸 내릴지."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    lines = text.split('\n'); out = []; i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.strip() == '---':
            i += 1; continue
        m = re.match(r'^(#{1,4}) (.*)$', ln)
        if m:
            lv = min(len(m.group(1)) + shift, 6)
            out.append(f'<h{lv}>{inline(m.group(2))}</h{lv}>'); i += 1; continue
        if ln.lstrip().startswith('|'):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                rows.append(lines[i]); i += 1
            head = _cells(rows[0]); body = [r for r in rows[1:] if not re.match(r'^\s*\|[\s:|-]+\|\s*$', r)]
            is_opt = head and head[0] == '선택지'
            h = '<table><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr>'
            for r in body:
                cs = _cells(r)
                lab = cs[0].replace('*', '').strip() if cs else ''
                cls = ' class="sel"' if is_opt and chosen and lab == chosen else ''
                tds = []
                for j, c in enumerate(cs):
                    if is_opt and j == 0:
                        tds.append(f'<td class="lab{" rec" if c.startswith("**") else ""}">{html.escape(lab)}</td>')
                    else:
                        tds.append(f'<td>{inline(c)}</td>')
                h += f'<tr{cls}>' + ''.join(tds) + '</tr>'
            out.append(h + '</table>'); continue
        if re.match(r'^\s*(- |\d+\. )', ln):
            items = []
            while i < len(lines) and (re.match(r'^\s*(- |\d+\. )', lines[i]) or (lines[i].startswith('   ') and lines[i].strip() and items)):
                l = lines[i]; m2 = re.match(r'^(\s*)(- |\d+\. )(.*)$', l)
                if m2:
                    items.append([len(m2.group(1)), m2.group(2).strip() != '-', m2.group(3)])
                else:
                    items[-1][2] += ' ' + l.strip()
                i += 1
            out.append(_list(items)); continue
        para = [ln.strip()]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,4} |\s*\||\s*- |\s*\d+\. |---)', lines[i]):
            para.append(lines[i].strip()); i += 1
        out.append('<p>' + '<br>'.join(inline(x) for x in para) + '</p>')
    return '\n'.join(out)

def _list(items):
    # items: [들여쓰기, 번호 목록 여부, 내용]. 들여쓰기가 깊으면 앞 항목의 하위 목록이다.
    def build(k, base):
        tag = 'ol' if items[k][1] else 'ul'; h = f'<{tag}>'
        while k < len(items) and items[k][0] >= base:
            if items[k][0] > base:
                sub, k = build(k, items[k][0]); h = h[:-5] + sub + '</li>'; continue
            h += f'<li>{inline(items[k][2])}</li>'; k += 1
        return h + f'</{tag}>', k
    h, k = build(0, items[0][0])
    while k < len(items):
        more, k = build(k, items[k][0]); h += more
    return h
