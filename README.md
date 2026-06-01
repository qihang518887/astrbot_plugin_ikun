<div align="center">

# astrbot_plugin_ikun

_🎵 基于洛雪音乐API的点歌插件 🎵_

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)

</div>

---

## 🤝 插件介绍

`astrbot_plugin_ikun` 是一个基于 **洛雪音乐API** 的点歌插件，核心特性如下：

- 🎧 支持多平台音源（网易云、QQ音乐、酷狗、酷我）
- 🔧 可自定义洛雪音乐JS音源文件
- 🔁 多发送方式自动降级
- 📃 文本 / 单曲两种选歌模式
- 💬 支持歌词、卡片、语音、文件
- 📂 用户独立歌单（本地持久化）
- 🤖 支持 LLM Tool 自动点歌
- 🚫 无需 VIP，不绑定单一平台

---

## 📦 安装

在 AstrBot 插件市场搜索 **astrbot_plugin_ikun**，点击安装并启用。

---

## ⚙️ 配置说明

请前往 **AstrBot 插件配置面板** 进行设置。

### 🔑 洛雪音乐JS音源配置

**lx_js_url**

- 填写洛雪音乐的JS音源文件URL地址
- 支持HTTP URL或本地文件路径
- 插件会自动下载并解析其中的API配置
- 留空则使用内置默认配置

**示例：**
- URL: `https://example.com/music-source.js`
- 本地路径: `C:/path/to/music-source.js`

**JS文件格式要求：**
```javascript
const API_URL = "https://your-api-url.com"
const API_KEY = "your-api-key"
const MUSIC_QUALITY = JSON.parse('{"kg":["128k","320k","flac"],"kw":["128k","320k","flac"],"tx":["128k","320k","flac"],"wy":["128k","320k","flac"]}');
```

---

### 🎼 默认点歌平台

**default_player_name**

- 定义 `点歌` 命令默认使用的平台
- 所有平台均可通过命令显式调用

支持平台：

| 平台 | 命令 | 音源代码 |
| ---- | ---- | -------- |
| 网易云音乐 | 网易点歌 | wy |
| QQ音乐 | QQ点歌 | tx |
| 酷狗音乐 | 酷狗点歌 | kg |
| 酷我音乐 | 酷我点歌 | kw |

---

### 🎵 音质设置

**lx_quality**

设置洛雪音乐API获取音频的音质，越高音质越好但文件越大。

| 音质 | 说明 |
| ---- | ---- |
| 128k | 标准音质 |
| 320k | 高音质（推荐） |
| flac | 无损音质 |
| flac24bit | 24bit无损 |
| hires | 高解析度 |
| atmos | 空间音频 |
| atmos_plus | 增强空间音频 |
| master | 母带音质 |

> 注意：不同音源支持的音质不同，具体取决于JS音源配置。

---

### 🔍 搜索与选择

**song_limit**

- 搜索返回歌曲数量
- 当选择模式为 `single` 时强制为 1

**select_mode**

| 模式   | 行为                     |
| ------ | ------------------------ |
| text   | 文本列表，等待输入序号   |
| single | 自动选中第一首           |

---

### 📤 发送策略

**send_modes**

定义歌曲发送方式的优先级，失败自动降级：

1. card（卡片，仅QQ + 网易云）
2. record（语音）
3. file（文件）
4. text（文本链接）

> 排在前面的方式优先，发送失败将自动尝试下一种。

---

### 🧩 附加功能

| 配置项          | 说明               |
| --------------- | ------------------ |
| enable_comments | 发送后附加热评     |
| enable_lyrics   | 发送歌词图片       |
| timeout         | 选歌等待超时（秒） |
| timeout_recall  | 超时撤回选歌消息   |
| clear_cache     | 重载插件时清空缓存 |
| proxy           | 网络代理地址       |

---

## ⌨️ 使用说明

### 🎶 点歌

| 命令                    | 说明             |
| ----------------------- | ---------------- |
| `点歌 <歌名>`           | 使用默认平台点歌 |
| `<平台名>点歌 <歌名>`   | 指定平台点歌     |
| `点歌 <歌名> <序号>`    | 直接选择搜索结果 |
| `查歌词 <歌名>`         | 查询并发送歌词   |
| `<序号> <模式>`         | 选择歌曲并指定发送模式 |

**发送模式：**
- 卡片 / card / 1
- 语音 / record / 2
- 文件 / file / 3
- 文本 / text / 4

---

### 📂 歌单功能

| 命令              | 说明         |
| ----------------- | ------------ |
| `歌单收藏 <歌名>` | 收藏歌曲     |
| `歌单取藏 <歌名>` | 取消收藏     |
| `歌单列表`        | 查看个人歌单 |
| `歌单点歌 <序号>` | 播放歌单歌曲 |

- 歌单按用户独立存储
- 默认最多 100 首

---

### 🤖 AI 点歌（LLM Tool）

插件提供 LLM Tool：

当用户表达"想听某首歌"时可自动调用播放。

---

## 🔧 自定义音源说明

### 获取洛雪音乐JS音源

1. 在互联网上搜索洛雪音乐音源JS文件
2. 将JS文件的URL或本地路径填入配置项 `lx_js_url`
3. 重启插件或等待自动加载

### JS音源文件格式

JS音源文件需要包含以下配置：

```javascript
// API服务器地址
const API_URL = "https://your-api-server.com"

// API密钥
const API_KEY = "your-api-key"

// 支持的音源和音质配置
const MUSIC_QUALITY = JSON.parse('{
    "kg": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "master"],
    "kw": ["128k", "320k", "flac", "flac24bit", "hires"],
    "tx": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "atmos_plus", "master"],
    "wy": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "master"]
}');
```

### 音源代码说明

| 代码 | 平台 |
| ---- | ---- |
| kg | 酷狗音乐 |
| kw | 酷我音乐 |
| tx | QQ音乐 |
| wy | 网易云音乐 |

---

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 📌 注意事项

- 使用前请确保已配置有效的洛雪音乐JS音源
- 不同音源支持的音质可能不同
- 部分功能可能依赖特定平台支持
