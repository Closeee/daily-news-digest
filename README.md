# 每日新闻简报

本地抓取关注的新闻源，生成《卫报》(The Guardian) 式报纸排版的 HTML 日报。桌面端优先，带头条大图 + 国际 / 财经 / 科技 / 安防四个栏目，每天自动更新。

## 特性

- 4 个源：Wired（科技，作头条）、联合早报·国际、联合早报·全球财经、安防知识网 a&s
- 卫报式排版：蓝报头 `#052962` + 头条大图 + 三栏网格
- 每栏精选 8 条（`fetch.py` 里 `MAX_PER_FIELD` 可调 5–10）
- 每条标注「来源 · 时间」
- 标题用抖音美好体（Douyin Sans），字体已随仓库，离线可用
- 英文标题保留原文（暂不翻译）

## 环境要求

- Python 3.8 及以上（Windows / macOS 均可）
- 依赖：`requests`、`beautifulsoup4`、`lxml`（一次装齐，见下）

## 快速开始

```bash
git clone https://github.com/<你的用户名>/daily-news-digest.git
cd daily-news-digest

# Windows
pip install -r requirements.txt
python fetch.py

# macOS
pip3 install -r requirements.txt
python3 fetch.py
```

生成的日报在 `output/news-YYYY-MM-DD.html`，双击用浏览器打开即可。

> macOS 若 `pip3 install` 提示 `externally-managed-environment`，改用虚拟环境：
> `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

## 每天自动运行

### Windows（任务计划程序）

```bat
schtasks /create /tn "每日新闻简报" /tr "\"C:\Python314\python.exe\" \"<脚本目录>\fetch.py\"" /sc daily /st 08:30
```

把 `<脚本目录>` 换成 `fetch.py` 所在目录；`C:\Python314\python.exe` 换成你的 Python 路径（`where python` 查看）。

### macOS（cron）

```bash
crontab -e
```

加入一行（把路径换成你的，`which python3` 查看 Python 路径）：

```
30 8 * * * /usr/bin/python3 /你的路径/daily-news-digest/fetch.py
```

## 自定义新闻源

编辑 `sources.json`，按现有格式新增即可。`type` 支持：

- `rss`：标准 RSS 源
- `zaobao`：联合早报网页
- `asmag`：安防知识网网页

字段含义：`name` 显示名、`field` 所属栏目、`type` 解析器、`url` 地址。

## 说明

- 网络直连可用性因网络环境而异（外媒站点可能需要代理）。
- 字体 `fonts/DouyinSansBold.ttf` 来自字节跳动开源（OFL 1.1 免费商用），随仓库分发。
