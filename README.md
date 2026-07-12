<div align="center">

# astrbot_plugin_ikun

_🎵 基于洛雪音乐API的多平台点歌插件 🎵_

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)

</div>

---

## 插件介绍

`astrbot_plugin_ikun` 基于 **洛雪音乐API**，支持多音源搜索、发送模式自动降级、串行下载队列。

- 支持网易云、QQ音乐、酷狗、酷我四平台
- 自定义洛雪音乐JS音源文件
- 发送模式自动降级：语音 → 文件 → 文本
- 串行下载队列，避免并发下载导致失败
- 文本列表 / 单曲直选两种选歌模式
- LLM Tool 自动点歌
- 可配置代理、超时、缓存策略

---

## 安装

AstrBot 插件市场搜索 **astrbot_plugin_ikun**，安装并启用。

---

## 配置

前往 **AstrBot 插件配置面板** 设置。

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `lx_js_url` | 洛雪音乐JS音源URL（必填），支持远程URL或本地路径 | `""` |
| `song_limit` | 搜索返回歌曲数量 | `5` |
| `select_mode` | 选歌模式：`text` 文本列表 / `single` 单曲直选 | `text` |
| `send_modes` | 发送模式优先级，失败自动降级 | `record → file → text` |
| `record_supported` | 支持语音的平台列表 | aiocqhttp / dingtalk 等 |
| `file_supported` | 支持文件的平台列表 | aiocqhttp / discord 等 |
| `enable_comments` | 发送后附加热评 | `false` |
| `proxy` | HTTP代理地址，如 `http://127.0.0.1:7890` | `""` |
| `timeout` | 选歌等待超时（秒） | `30` |
| `timeout_recall` | 超时撤回选歌消息 | `true` |
| `clear_cache` | 重载插件时清空下载缓存 | `true` |

### 洛雪音乐JS音源

**lx_js_url** 必填。插件自动下载并解析JS文件中的 API 地址和密钥。

```javascript
const API_URL = "https://your-api-server.com"
const API_KEY = "your-api-key"
const MUSIC_QUALITY = JSON.parse('{"kg":["128k","320k","flac"],"kw":["128k","320k","flac"],"tx":["128k","320k","flac"],"wy":["128k","320k","flac"]}');
```

---

## 命令

### 点歌

| 命令 | 说明 |
|------|------|
| `wy <歌名>` | 网易云搜索 |
| `qq <歌名>` | QQ音乐搜索 |
| `kg <歌名>` | 酷狗搜索 |
| `kw <歌名>` | 酷我搜索 |
| `wy <歌名> <序号>` | 直接选择第N首 |

搜索后发送数字选择歌曲，也可附加模式：
- `2 语音` / `2 record` / `2 1` — 语音模式
- `2 文件` / `2 file` / `2 2` — 文件模式
- `2 文本` / `2 text` / `2 3` — 文本模式

文件模式自动进入下载队列，并提示：
```
已添加到下载队列，当前2/2
```

### LLM Tool

配置LLM Tool后，用户表达"想听某首歌"时自动调用播放。

---

## 音源对照

| 命令前缀 | 平台 | 音源代码 |
|----------|------|----------|
| `wy` | 网易云音乐 | `wy` |
| `qq` | QQ音乐 | `tx` |
| `kg` | 酷狗音乐 | `kg` |
| `kw` | 酷我音乐 | `kw` |

---

## 下载队列

v1.6.0 引入串行下载队列（`asyncio.Queue`）：

- 所有文件模式的下载任务排入队列，**同时只下载一个**
- 队列信息实时通知：`已添加到下载队列，当前2/2`
- 插件卸载时自动取消待处理任务
- 语音模式（record）不经队列，直接发送URL

---

## 注意事项

- `lx_js_url` 为必填项，首次使用请先配置有效的洛雪音乐JS音源
- 不同音源支持的音质不同，具体取决于JS配置
- 文件模式需下载音频，较语音模式更慢但音质更高
