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
git clone https://github.com/Closeee/daily-news-digest.git
cd daily-news-digest

# Windows
pip install -r requirements.txt
python fetch.py

# macOS（推荐：一键装依赖）
bash setup.sh

# macOS（或手动）
pip3 install -r requirements.txt
python3 fetch.py
```

生成的日报在 `output/news-YYYY-MM-DD.html`，双击用浏览器打开即可。

> macOS 若 `pip3 install` 提示 `externally-managed-environment`，改用虚拟环境：
> `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

## 每天自动运行

### Windows（任务计划程序）

仓库里自带 `run.bat`（Windows 启动器，跑完会写日志到 `output/run.log`）。

**⚠️ 不要用 `schtasks /create` 命令行注册**——如果路径含中文，命令行按 GBK 写入、任务 XML 按 UTF-16 存，任务计划程序读出来是乱码路径，会静默失败（任务"跑"了但什么都没生成，退出码 2）。**改用 PowerShell 注册**：

```powershell
# 在管理员 PowerShell 里运行（S4U 需要管理员权限）
$dir = '<脚本目录>'          # fetch.py 所在目录
$action    = New-ScheduledTaskAction -Execute "$dir\run.bat" -WorkingDirectory $dir
$trigger   = New-ScheduledTaskTrigger -Daily -At 8:30AM
$settings  = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$env:USERNAME" -LogonType S4U
Register-ScheduledTask -TaskName 'DailyNewsDigest' -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force
```

要点：

- 任务名用**英文** `DailyNewsDigest`，避免中文编码坑
- `-LogonType S4U`：锁屏、未登录也能跑，且**不需要存密码**（必须管理员权限注册）
- `-StartWhenAvailable`：8:30 没开机的话，开机后自动补跑一次
- 想确认有没有跑成功：`(Get-ScheduledTaskInfo -TaskName DailyNewsDigest).LastTaskResult`，`0` 才是成功

### 如何停止 / 卸载

双击项目目录里的 **`停止.bat`** 即可（会弹一次 UAC 请点是）。它会删除计划任务并验证结果。之后日报不再自动更新，但已生成的 HTML 都还在。

手动等价命令（管理员 PowerShell）：

```powershell
Unregister-ScheduledTask -TaskName 'DailyNewsDigest' -Confirm:$false
```

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
