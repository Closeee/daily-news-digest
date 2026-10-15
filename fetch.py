# -*- coding: utf-8 -*-
"""每日新闻简报抓取脚本

抓取 sources.json 里配置的新闻源（RSS / 网页），去重后按领域分组，
生成卫报式报纸风格的 HTML 简报。只依赖 requests + bs4 + lxml。
"""
import datetime
import json
import os
import re
import sys
import time
from email.utils import parsedate_to_datetime
from html import escape

import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录，clone 到任意机器/路径都能跑
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

FIELD_ICON = {'科技': '🤖', '国际': '🌍', '财经': '💰', '安防': '🛡️'}
COLUMN_ORDER = ['国际', '财经', '科技', '安防']
MAX_PER_FIELD = 8  # 每栏目最多展示条数（用户要求控制在 5-10 条）

HEADERS = {
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def get(url, retries=2):
    """抓取页面，带重试（应对联合早报等源的间歇性 TLS 失败/限流）。"""
    for i in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r
        except Exception:
            if i == retries:
                raise
            time.sleep(2 * (i + 1))


# ---- 时间格式化 ----

def fmt_rss_time(s):
    try:
        return parsedate_to_datetime(s).strftime('%Y-%m-%d')
    except Exception:
        return ''


def fmt_zaobao_time(href):
    m = re.search(r'story(\d{8})', href)
    if m:
        d = m.group(1)
        return f'{d[:4]}-{d[4:6]}-{d[6:8]}'
    return ''


def fmt_asmag_time(url):
    m = re.search(r'/news/(\d{4})(\d{2})/', url)
    if m:
        return f'{m.group(1)}-{m.group(2)}'
    return ''


# ---- 各源解析器 ----

def _extract_img(it):
    """从 RSS item 里提取图片 URL（Wired 的 thumbnail / media:content / enclosure）。"""
    for t in it.find_all(True):
        url = t.get('url')
        if url and re.search(r'\.(jpe?g|png|webp)(\?|$)', url, re.I):
            return url
    return ''


SHOPPING_HINTS = ('coupon', 'promo code', 'discount', '% off', 'buying guide')


def _is_shopping(title, cats):
    """过滤 Wired 等外媒 RSS 里的购物/优惠券/导购内容。"""
    c = ' '.join(cats).lower()
    if 'deals' in c or 'buying guide' in c:
        return True
    t = title.lower()
    return any(h in t for h in SHOPPING_HINTS)


def parse_rss(text):
    soup = BeautifulSoup(text, 'xml')
    out = []
    for it in soup.find_all('item'):
        t = it.find('title')
        l = it.find('link')
        g = it.find('guid')
        d = it.find('pubDate')
        title = t.get_text(strip=True) if t else ''
        url = (l.get_text(strip=True) if l else '') or (g.get_text(strip=True) if g else '')
        cats = [c.get_text(strip=True) for c in it.find_all('category')]
        if title and url and not _is_shopping(title, cats):
            out.append({'title': title, 'url': url,
                        'time': fmt_rss_time(d.get_text(strip=True) if d else ''),
                        'img': _extract_img(it)})
    return out


def parse_zaobao(text):
    soup = BeautifulSoup(text, 'lxml')
    out = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/story' in href:
            title = (a.get('title') or a.get_text(strip=True)).strip()
            url = href if href.startswith('http') else 'https://www.zaobao.com' + href
            if title and url:
                out.append({'title': title, 'url': url, 'time': fmt_zaobao_time(href), 'img': ''})
    return out


def parse_asmag(text):
    soup = BeautifulSoup(text, 'lxml')
    out = []
    for h3 in soup.find_all('h3', class_='ellipsis2'):
        a = h3.find_parent('a')
        url = a.get('href') if a else ''
        title = h3.get_text(strip=True)
        if title and url:
            out.append({'title': title, 'url': url, 'time': fmt_asmag_time(url), 'img': ''})
    return out


PARSERS = {'rss': parse_rss, 'zaobao': parse_zaobao, 'asmag': parse_asmag}


# ---- HTML 样式（卫报式报纸风格）----

CSS = '''
@font-face {
  font-family: 'Douyin Sans';
  src: url('../fonts/DouyinSansBold.ttf') format('truetype');
  font-weight: 100 900;
  font-display: swap;
}
:root {
  --bg:#f6f6f4; --ink:#121212; --blue:#052962; --red:#ab0613;
  --line:#dcdcdc; --sub:#767676;
}
* { box-sizing:border-box; margin:0; padding:0; }
body { background:var(--bg); color:var(--ink); font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif; line-height:1.5; }
.masthead { background:var(--blue); color:#fff; padding:16px 32px; }
.masthead .inner { max-width:1200px; margin:0 auto; display:flex; align-items:baseline; justify-content:space-between; }
.masthead h1 { font-family:'Douyin Sans',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif; font-size:32px; font-weight:700; letter-spacing:1px; }
.masthead .date { font-family:'Douyin Sans',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif; font-size:15px; opacity:.9; }
.main { max-width:1200px; margin:0 auto; padding:24px 32px 40px; }
.stats { color:var(--sub); font-size:13px; margin-bottom:20px; }
.lead { display:grid; grid-template-columns:1.3fr 1fr; gap:24px; margin-bottom:26px; padding-bottom:24px; border-bottom:1px solid var(--line); }
.lead img { width:100%; height:100%; min-height:260px; object-fit:cover; }
.lead-body { display:flex; flex-direction:column; justify-content:center; }
.kicker { color:var(--red); font-size:13px; font-weight:700; letter-spacing:1px; margin-bottom:10px; }
.lead-title { font-family:'Douyin Sans',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif; font-size:32px; font-weight:700; line-height:1.2; color:var(--ink); text-decoration:none; }
.lead-title:hover { text-decoration:underline; }
.lead .meta { color:var(--sub); font-size:12px; margin-top:12px; }
.grid { display:grid; grid-template-columns:repeat(3,1fr); gap:32px; }
.col { border-top:3px solid var(--blue); padding-top:12px; }
.col-title { font-family:'Douyin Sans',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif; font-size:17px; font-weight:700; margin-bottom:14px; display:flex; align-items:center; gap:6px; }
.col-title .n { background:var(--blue); color:#fff; font-size:11px; border-radius:9px; padding:1px 8px; font-weight:500; }
.col-lead { display:block; font-family:'Douyin Sans',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif; font-size:20px; font-weight:700; line-height:1.35; color:var(--ink); text-decoration:none; margin-bottom:6px; }
.col-lead:hover { color:var(--blue); }
.col-lead-meta { color:var(--sub); font-size:12px; margin-bottom:14px; }
.item { display:flex; gap:10px; align-items:flex-start; padding:9px 0; border-top:1px solid var(--line); color:var(--ink); text-decoration:none; }
.item:hover .t { color:var(--blue); }
.item img { width:64px; height:44px; object-fit:cover; flex-shrink:0; border-radius:2px; background:#eee; }
.item .body { flex:1; min-width:0; }
.item .t { display:block; font-size:14px; line-height:1.45; }
.item .m { display:block; color:var(--sub); font-size:12px; margin-top:3px; }
footer { max-width:1200px; margin:0 auto; padding:0 32px 48px; color:var(--sub); font-size:12px; }
@media (max-width:900px) {
  .grid { grid-template-columns:1fr; }
  .lead { grid-template-columns:1fr; }
}
'''


def _src_time(it):
    """拼接条目的「来源 · 时间」，缺项自动省略。"""
    return ' · '.join(x for x in (it.get('source', ''), it.get('time', '')) if x)


def render_html(fields, stats, total, today, lead):
    weekday = '周' + '一二三四五六日'[today.weekday()]
    date_str = today.strftime('%Y-%m-%d')

    stat_parts = [f'{n} {c}' if isinstance(c, int) else f'{n} ⚠️' for n, c in stats]
    stat_html = ' · '.join(stat_parts)

    # 头条（取第一条有图的外媒，即 Wired 头条）
    lead_html = ''
    if lead:
        img = (f'<img src="{escape(lead["img"], quote=True)}" alt="" loading="eager">'
               if lead.get('img') else '')
        lead_html = f'''<article class="lead">
      {img}
      <div class="lead-body">
        <span class="kicker">头条 · {escape(lead["source"])}</span>
        <a class="lead-title" href="{escape(lead["url"], quote=True)}" target="_blank" rel="noopener">{escape(lead["title"])}</a>
        <div class="meta">{escape(lead["time"])}</div>
      </div>
    </article>'''

    # 分类栏
    order = COLUMN_ORDER + [k for k in fields if k not in COLUMN_ORDER]
    columns = []
    for f in order:
        items = fields.get(f)
        if not items:
            continue
        col_items = items
        # 科技栏跳过头条（头条已单独展示）
        if f == '科技' and lead and col_items and col_items[0].get('url') == lead.get('url'):
            col_items = col_items[1:]
        if not col_items:
            continue
        # 每栏控制在 MAX_PER_FIELD 条以内（取最新/最靠前的精选）
        col_items = col_items[:MAX_PER_FIELD]
        icon = FIELD_ICON.get(f, '📌')
        first = col_items[0]
        first_html = (f'<a class="col-lead" href="{escape(first["url"], quote=True)}" '
                      f'target="_blank" rel="noopener">{escape(first["title"])}</a>'
                      f'<div class="col-lead-meta">{escape(_src_time(first))}</div>')
        rest = []
        for it in col_items[1:]:
            thumb = ''
            if it.get('img'):
                thumb = (f'<img src="{escape(it["img"], quote=True)}" alt="" loading="lazy">')
            rest.append(f'<a class="item" href="{escape(it["url"], quote=True)}" '
                        f'target="_blank" rel="noopener">{thumb}'
                        f'<span class="body"><span class="t">{escape(it["title"])}</span>'
                        f'<span class="m">{escape(_src_time(it))}</span></span></a>')
        columns.append(f'<section class="col"><h3 class="col-title">{icon} {escape(f)} '
                       f'<span class="n">{len(col_items)}</span></h3>{first_html}{"".join(rest)}</section>')

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日新闻简报 · {date_str}</title>
<style>{CSS}</style>
</head>
<body>
<header class="masthead">
  <div class="inner">
    <h1>每日新闻简报</h1>
    <div class="date">{date_str} {weekday}</div>
  </div>
</header>
<div class="main">
  <p class="stats">共 {total} 条 · {stat_html}</p>
  {lead_html}
  <div class="grid">
    {''.join(columns)}
  </div>
</div>
<footer>数据抓取于 {today.strftime('%Y-%m-%d %H:%M')} · 本地生成，未推送</footer>
</body>
</html>'''


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    cfg_path = os.path.join(BASE, 'sources.json')
    cfg = json.load(open(cfg_path, encoding='utf-8'))

    all_items, stats = [], []
    for s in cfg['sources']:
        name = s['name']
        try:
            r = get(s['url'])
            items = PARSERS.get(s['type'], lambda t: [])(r.content)
            for it in items:
                it['source'] = name
                it['field'] = s['field']
            all_items.extend(items)
            stats.append((name, len(items)))
            print(f'  ✓ {name}: {len(items)} 条')
        except Exception as e:
            stats.append((name, 'fail'))
            print(f'  ✗ {name}: {type(e).__name__} {str(e)[:80]}')

    # 按标题去重
    seen, dedup = set(), []
    for it in all_items:
        k = it['title']
        if k and k not in seen:
            seen.add(k)
            dedup.append(it)

    # 按领域分组
    fields = {}
    for it in dedup:
        fields.setdefault(it['field'], []).append(it)

    # 头条：第一条带图的外媒
    lead = next((it for it in dedup if it.get('img')), None)

    today = datetime.date.today()
    html = render_html(fields, stats, len(dedup), today, lead)

    out_dir = os.path.join(BASE, 'output')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f'news-{today.isoformat()}.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n共 {len(dedup)} 条（去重后），已生成 {out}')


if __name__ == '__main__':
    main()
